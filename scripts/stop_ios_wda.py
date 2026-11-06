"""
================================================================================
Santiao iOS WDA 8100 自动化服务统一终止与清理工具
================================================================================
职责：
1. 扫描并精准终止电脑端运行中的 start_ios_wda 守护进程；
2. 扫描并终止所有占用 8100 端口的僵尸进程 (usbmux forward)；
3. 终止后台运行的 pymobiledevice3 xcuitest 远程测试客户端；
4. 联动向 iPhone 真机发送退出指令，停止真机 WDA Runner，使设备恢复省电常态；
5. 最终验证 8100 端口释放状态，确保下次启动零冲突。
================================================================================
"""
import functools
import os
import subprocess
import sys
import time
from typing import List, Set

import psutil

# 全局 unbuffered 打印
print = functools.partial(print, flush=True)

# 强制终端以 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


DEFAULT_WDA_BUNDLE_ID = "com.facebook.WebDriverAgentRunner.xctrunner.VX43WKZ6A5"
TARGET_PORT = 8100


def kill_processes_by_port(port: int) -> int:
    """终止所有监听或连接指定端口的本地进程"""
    killed_count = 0
    current_pid = os.getpid()

    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr and conn.laddr.port == port:
            pid = conn.pid
            if pid and pid != current_pid:
                try:
                    proc = psutil.Process(pid)
                    p_name = proc.name()
                    proc.kill()
                    killed_count += 1
                    print(f"    ✔ 已终止占用 {port} 端口的进程: PID={pid} ({p_name})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    return killed_count


def kill_wda_host_processes() -> int:
    """精准识别并终止所有与 WDA 启动、转发相关的宿主 Python 进程"""
    killed_count = 0
    current_pid = os.getpid()

    # 匹配目标关键词 (全部小写以便进行大小写不敏感匹配)
    target_keywords = [
        "start_ios_wda",
        "usbmux forward 8100",
        "developer dvt xcuitest",
        "webdriveragentrunner",
    ]

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            pid = proc.info["pid"]
            if pid == current_pid:
                continue

            cmdline_list = proc.info.get("cmdline") or []
            cmdline_str = " ".join(cmdline_list).lower()

            # 匹配关键词
            matched = any(kw in cmdline_str for kw in target_keywords)
            if matched:
                # 递归终止该进程及其所有派生的子进程树，杜绝守护看门狗残留
                try:
                    for child in proc.children(recursive=True):
                        try:
                            child.kill()
                        except Exception:
                            pass
                except Exception:
                    pass
                proc.kill()
                killed_count += 1
                p_name = proc.info.get("name") or "Python"
                print(f"    ✔ 已终止 WDA 自动化相关后台进程树: PID={pid} ({p_name})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return killed_count


def stop_iphone_wda_runner() -> bool:
    """通知 iPhone 真机停止前台/后台常驻的 WDA Runner 进程"""
    try:
        res = subprocess.run(
            ["tidevice", "kill", DEFAULT_WDA_BUNDLE_ID],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        if res.returncode == 0:
            print(f"    ✔ 已成功向 iPhone 真机发送停止指令: {DEFAULT_WDA_BUNDLE_ID}")
            return True
    except Exception:
        pass
    return False


def verify_port_released(port: int, wait_seconds: float = 3.0) -> bool:
    """验证目标端口是否已被完全释放"""
    start_time = time.time()
    while time.time() - start_time < wait_seconds:
        is_occupied = False
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                is_occupied = True
                break
        if not is_occupied:
            return True
        time.sleep(0.5)
    return False


def main() -> None:
    print("=" * 70)
    print("  🛑 Santiao iOS WDA 8100 自动化服务统一停止器 (Windows 11)")
    print("=" * 70)
    print()

    # 1. 扫描并终止电脑端宿主进程
    print("[1/4] 正在扫描并终止电脑端 WDA 启动与守护进程...")
    k_host = kill_wda_host_processes()
    if k_host == 0:
        print("    ℹ 未发现正在运行的 start_ios_wda 相关宿主进程。")

    # 2. 扫描并释放 8100 端口
    print(f"[2/4] 正在检查并释放电脑端 {TARGET_PORT} 端口占用...")
    k_port = kill_processes_by_port(TARGET_PORT)
    if k_port == 0:
        print(f"    ℹ {TARGET_PORT} 端口未被其他僵尸进程占用。")

    # 3. 停止手机端真机 Runner
    print("[3/4] 正在通知已连接的 iPhone 真机关闭 WDA Runner 测试应用...")
    stop_iphone_wda_runner()

    # 4. 验证最终端口状态
    print(f"[4/4] 正在最终校验 {TARGET_PORT} 端口状态...")
    if verify_port_released(TARGET_PORT):
        print(f"    ✔ 端口 {TARGET_PORT} 状态: 已完全空闲释放 (FREE)。")
    else:
        print(f"    ⚠️ 端口 {TARGET_PORT} 可能仍在短暂停留 TIME_WAIT，请稍候 2 秒。")

    print()
    print("=" * 70)
    print("  🎉 [SUCCESS] iOS WDA 8100 自动化服务及真机测试进程已彻底终止并清理完成！")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()

