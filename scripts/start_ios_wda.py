"""
================================================================================
Santiao iOS WDA 8100 自动化服务统一启动器 (工业级守护版)
================================================================================
职责：
1. 自动检测 iPhone 设备连接状态与 WDA 安装签名；
2. 工业级双重看门狗守护 (Watchdog)：
   - 自动拉起并守护 8100 端口透传 (usbmux forward)，断线自愈；
   - 自动拉起并守护真机 WDA 守护进程 (iOS 17+ userspace 模式)，崩溃自愈；
3. 环形日志缓存与关键生命周期智能过滤；
4. 实时轮询健康状态，就绪后输出标准直连凭证与 Appium 引导；
5. 进程安全联动：Ctrl+C 退出时全自动回收全部子进程，杜绝端口僵尸占用。
================================================================================
"""
import collections
import functools
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from typing import Deque, Optional

# 全局 unbuffered 打印
print = functools.partial(print, flush=True)

# 强制终端以 UTF-8 输出，消除 Windows 控制台乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


DEFAULT_WDA_BUNDLE_ID = "com.facebook.WebDriverAgentRunner.xctrunner.VX43WKZ6A5"
WDA_STATUS_URL = "http://127.0.0.1:8100/status"


def _build_pmd3_cmd(*args: str) -> list[str]:
    """构建跨态 pymobiledevice3 命令 (自动兼容打包内置自举模式与源码模式)"""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--internal-pmd3", *args]
    return [sys.executable, "-u", "-m", "pymobiledevice3", *args]


def _build_tidevice_cmd(*args: str) -> list[str]:
    """构建跨态 tidevice 命令 (自动兼容打包内置自举模式与源码模式)"""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--internal-tidevice", *args]
    return ["tidevice", *args]


def get_connected_device() -> Optional[str]:
    """检查当前是否连接了 iPhone 真机 (优先 tidevice，兜底 pymobiledevice3 usbmux list)"""
    try:
        res = subprocess.run(
            _build_tidevice_cmd("list"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        for line in lines:
            if "iPhone" in line or "ConnectionType.USB" in line:
                return line
    except Exception:
        pass
    try:
        res = subprocess.run(
            _build_pmd3_cmd("usbmux", "list"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=6,
        )
        if "Identifier" in res.stdout or "DeviceName" in res.stdout:
            return "iPhone (USB Connected)"
    except Exception:
        pass
    return None


def ensure_developer_disk_mounted(force: bool = False) -> bool:
    """
    检查并自动挂载 iOS DeveloperDiskImage (PersonalizedImage)。
    当 iPhone 重启或重连后，iOS 会卸载开发者镜像，导致 developer dvt xcuitest 立即以
    'ERROR Failed to start service' 退出；必须在拉起 xcuitest 前确保镜像已挂载。
    """
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    if not force:
        try:
            chk = subprocess.run(
                _build_pmd3_cmd("mounter", "lookup", "Personalized"),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=6,
                creationflags=creationflags,
            )
            combined_out = f"{chk.stdout}\n{chk.stderr}".lower()
            if chk.returncode == 0 and "not mounted" not in combined_out and "error" not in combined_out:
                print("    ✔ 开发者镜像 (PersonalizedImage) 已处于挂载状态")
                return True
        except Exception:
            pass

    print("    ➜ 检测到开发者镜像未挂载，正在自动挂载 DeveloperDiskImage (auto-mount)...")
    try:
        mnt = subprocess.run(
            _build_pmd3_cmd("mounter", "auto-mount"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=25,
            creationflags=creationflags,
        )
        combined_mnt = f"{mnt.stdout}\n{mnt.stderr}"
        if "mounted successfully" in combined_mnt.lower() or "already mounted" in combined_mnt.lower() or mnt.returncode == 0:
            print("    ✔ 开发者镜像 (DeveloperDiskImage) 挂载成功")
            return True
        print(f"    ⚠️ 自动挂载返回提示: {combined_mnt.strip()[-200:]}")
    except Exception as e:
        print(f"    ⚠️ 自动挂载执行异常: {e}")
    return False


def get_wda_bundle_id() -> str:
    """自动获取真机已安装的 WDA Bundle ID，获取不到时使用默认值"""
    try:
        res = subprocess.run(
            _build_tidevice_cmd("applist"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=6,
        )
        for line in res.stdout.splitlines():
            if "WebDriverAgentRunner.xctrunner" in line:
                parts = line.strip().split()
                if parts:
                    return parts[0]
    except Exception:
        pass
    return DEFAULT_WDA_BUNDLE_ID


def check_wda_ready() -> bool:
    """检测 8100 端口上的 WDA HTTP 服务是否返回就绪状态"""
    try:
        req = urllib.request.Request(WDA_STATUS_URL, method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                value = data.get("value", {})
                if value.get("ready") is True or value.get("state") == "success":
                    return True
    except Exception:
        return False
    return False


def main() -> None:
    print("=" * 70)
    print("  🚀 Santiao iOS WDA 8100 自动化服务启动器 (Windows 11 守护版)")
    print("=" * 70)
    print()

    # 1. 检查真机连接
    print("[1/4] 正在检测已连接的 iPhone 真机...")
    device_info = get_connected_device()
    if not device_info:
        print("\n❌ [错误] 未检测到 USB 连接的 iPhone！")
        print("    请排查：")
        print("    1. 数据线是否牢固连接电脑；")
        print("    2. 手机是否处于解锁亮屏状态；")
        print("    3. 手机是否在'要信任此电脑吗'弹窗中点击了【信任】。\n")
        sys.exit(1)
    print(f"    ✔ 已识别设备: {device_info}")

    # 2. 匹配 Bundle ID
    print("[2/4] 正在检索已安装的 WDA Bundle ID...")
    bundle_id = get_wda_bundle_id()
    print(f"    ✔ 目标 Bundle ID: {bundle_id}")

    # 全局退出标记与子进程句柄
    is_terminating = False
    forwarder_proc: Optional[subprocess.Popen] = None
    wda_proc: Optional[subprocess.Popen] = None

    def _cleanup_all(*_args) -> None:
        """安全回收所有子进程"""
        nonlocal is_terminating
        if is_terminating:
            return
        is_terminating = True
        print("\n[STOP] 正在停止 WDA 守护进程与 8100 端口转发...")
        for proc in (wda_proc, forwarder_proc):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        print("[STOP] 8100 自动化服务已安全退出。")
        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup_all)
    signal.signal(signal.SIGTERM, _cleanup_all)

    # 3. 启动电脑端 8100 端口透传子进程（带自动守护重试）
    print("[3/5] 正在开辟电脑 8100 端口透传隧道 (127.0.0.1:8100 -> iPhone:8100)...")
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    use_tidevice_relay = True

    def _ensure_forwarder() -> None:
        nonlocal forwarder_proc, use_tidevice_relay
        if forwarder_proc is None or forwarder_proc.poll() is not None:
            if forwarder_proc is not None and forwarder_proc.poll() is not None:
                # 转发器异常退出时输出原因并切换备用通道
                err_out = ""
                try:
                    if forwarder_proc.stderr:
                        err_out = forwarder_proc.stderr.read().strip()
                except Exception:
                    pass
                print(f"    ⚠️ 8100 端口转发进程已退出 (code={forwarder_proc.returncode}) {err_out}，正在切换通道重启...")
                use_tidevice_relay = not use_tidevice_relay

            fwd_cmd = (
                _build_tidevice_cmd("relay", "8100", "8100")
                if use_tidevice_relay
                else _build_pmd3_cmd("usbmux", "forward", "8100", "8100")
            )
            print(f"    ➜ 启动 8100 端口转发通道: {' '.join(fwd_cmd)}")
            forwarder_proc = subprocess.Popen(
                fwd_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
            )

    _ensure_forwarder()

    # 4. 检查并自动挂载 DeveloperDiskImage (PersonalizedImage)，防止手机重启后 xcuitest 立即崩溃
    print("[4/5] 正在校验并挂载真机开发者镜像 (DeveloperDiskImage / PersonalizedImage)...")
    ensure_developer_disk_mounted(force=False)

    # 5. 看门狗主循环：拉起并守护真机 WDA 进程
    print("[5/5] 正在拉起真机 WDA 自动化守护服务 (iOS 17+ userspace 模式)...")
    print("  💡 重要提示: 请保持 iPhone 屏幕处于解锁亮屏状态 (建议设置中关闭自动锁定)")

    recent_logs: Deque[str] = collections.deque(maxlen=20)
    has_shown_ready = False

    while not is_terminating:
        _ensure_forwarder()

        # macOS 不强锁 --userspace，允许 pymobiledevice3 自动在 userspace 与 native_tunnel (免 root) 间容灾切换
        xcuitest_cmd = (
            _build_pmd3_cmd("developer", "dvt", "xcuitest", "--userspace", bundle_id)
            if sys.platform == "win32"
            else _build_pmd3_cmd("developer", "dvt", "xcuitest", bundle_id)
        )
        wda_proc = subprocess.Popen(
            xcuitest_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
        )

        ready_event = threading.Event()

        def _poll_status() -> None:
            """后台轮询 8100 服务就绪状态"""
            nonlocal has_shown_ready
            for _ in range(60):
                if is_terminating or (wda_proc and wda_proc.poll() is not None):
                    break
                if check_wda_ready():
                    ready_event.set()
                    if not has_shown_ready:
                        has_shown_ready = True
                        print()
                        print("=" * 70)
                        print("  🎉 [SUCCESS] WebDriverAgent 8100 自动化服务已成功就绪！")
                        print("=" * 70)
                        print("  🌐 验证地址: http://127.0.0.1:8100/status")
                        print("  📱 设备地址: http://127.0.0.1:8100")
                        print("  ⚙️ Appium 配置: appium:webDriverAgentUrl = \"http://127.0.0.1:8100\"")
                        print("=" * 70)
                        print("  💡 提示: 自动化测试期间请保持当前窗口常开 (按 Ctrl+C 可安全退出)")
                        print("=" * 70)
                        print()
                    else:
                        print("  ➜ [Watchdog] WDA 会话已恢复并就绪。")
                    return
                time.sleep(1.0)

        threading.Thread(target=_poll_status, daemon=True).start()

        try:
            while not is_terminating:
                if wda_proc.stdout is None:
                    break
                line = wda_proc.stdout.readline()
                if not line:
                    if wda_proc.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue

                cleaned = line.strip()
                if not cleaned:
                    continue

                # 记录环形最新日志以供异常诊断
                recent_logs.append(cleaned)

                # 过滤 RemoteXPC 底层杂音
                if "WARNING No channel registered for code -1" in cleaned:
                    continue
                if "Creating future for 'requesting test configuration'" in cleaned:
                    continue

                # 关键生命周期输出
                if "didBeginExecutingTestPlan" in cleaned:
                    print("  ➜ 测试计划已挂载，正在启动真机 Runner...")
                elif "testCaseDidStart: UITestingUITests/testRunner" in cleaned:
                    print("  ➜ 真机 Runner 已进入就绪监听循环 (Listening)...")
                elif not ready_event.is_set():
                    if "ERROR" in cleaned or "Exception" in cleaned or "failed" in cleaned:
                        print(f"  [WDA 日志] {cleaned}")

        except KeyboardInterrupt:
            _cleanup_all()
            break

        if is_terminating:
            break

        exit_code = wda_proc.poll()
        if exit_code not in (0, None):
            joined_recent = "\n".join(recent_logs)
            if "Failed to start service" in joined_recent or "mounter auto-mount" in joined_recent:
                print("\n⚠️  [自愈] 检测到真机 DeveloperDiskImage 未挂载导致服务启动失败，正在执行自动挂载修复...")
                ensure_developer_disk_mounted(force=True)
            elif "DTXNsError" in joined_recent or "Failed to launch process" in joined_recent:
                print("\n❌ [签名/信任异常] iOS 拒绝启动 WebDriverAgentRunner (code 2 / Security)：")
                print("    1. 个人免费 Apple ID 签名的 WDA 证书已满 7 天过期，请重新签名安装 WDA IPA；")
                print("    2. 或前往 iPhone【设置 -> 通用 -> VPN 与设备管理】点击开发者证书并【信任/验证应用】；")
                print("    3. 请确认 iPhone 屏幕处于解锁亮屏状态。")
            else:
                print(f"\n⚠️  [警告] WDA 守护进程退出 (退出码: {exit_code})，可能原因：")
                print("    1. 手机屏幕自动锁定/休眠（导致 iOS 系统杀死调试 Runner）；")
                print("    2. USB 数据线连接出现瞬时断开或供电不足。")
                if recent_logs:
                    print("    --- 诊断详情 (最后几行日志) ---")
                    for err_line in list(recent_logs)[-3:]:
                        print(f"    | {err_line}")
                    print("    -----------------------------")
            recent_logs.clear()
            print("  🔄 [Watchdog] 看门狗正在 2 秒后自动重新拉起 WDA 守护进程...\n")
            time.sleep(2.0)


if __name__ == "__main__":
    main()

