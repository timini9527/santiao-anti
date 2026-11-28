# -*- coding: utf-8 -*-
"""
iOS WDA 服务管理、设备探测与动作控制模块：
1. IosWdaManager：8100/8200 端口探活、设备版本查询与孤儿 relay 端口回收；
2. check_ios_wda_services：WDA Runner + 8100 转发双服务巡检；
3. IosServiceActionWorker：兼容源码态与 Mac .dmg / Win .exe 打包态 (--internal-wda) 的异步启停守护线程；
4. scan_ios_devices：usbmux / tidevice / Win32 PnP / 本地 WDA 四级探测；
5. run_ios_action：CoreDevice HID 优先 + WDA HTTP 降级动作派发。
"""
import asyncio
import contextlib
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import psutil
from PyQt6.QtCore import QThread, pyqtSignal

from desktop_app.core.path_resolver import SmartPathResolver
from desktop_app.core.paths import LOGS_DIR, WRITABLE_ROOT

logger = logging.getLogger("Inspector")

# 由 ScreenCastWorker 在初始化时注册的 iOS 原生 HID 派发钩子，避免循环依赖
_IOS_HID_DISPATCHER: Optional[Callable[..., bool]] = None


def register_ios_hid_dispatcher(fn: Callable[..., bool]) -> None:
    """注册活跃 iOS CoreDevice HID 派发器回调"""
    global _IOS_HID_DISPATCHER
    _IOS_HID_DISPATCHER = fn


def _resolve_tidevice_cmd(udid: str, *extra_args: str) -> Optional[List[str]]:
    """构造 tidevice 命令（优先打包态 --internal-tidevice，其次外部 tidevice CLI）"""
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "--internal-tidevice"]
        if udid:
            cmd.extend(["-u", udid])
        cmd.extend(extra_args)
        return cmd
    tidevice_bin = shutil.which("tidevice")
    if not tidevice_bin:
        candidate_td = os.path.join(os.path.dirname(sys.executable), "Scripts", "tidevice.exe")
        if os.path.isfile(candidate_td):
            tidevice_bin = candidate_td
    if not tidevice_bin:
        return None
    cmd = [tidevice_bin]
    if udid:
        cmd.extend(["-u", udid])
    cmd.extend(extra_args)
    return cmd


class IosWdaManager:
    """iOS WebDriverAgent (WDA) 端口探活、设备版本查询与中继管理器"""

    _relay_proc: Optional[subprocess.Popen] = None
    _relay_udid: str = ""
    _active_wda_url: str = "http://127.0.0.1:8100"
    _version_cache: Dict[str, str] = {}

    @classmethod
    def kill_relays(cls, ports: Tuple[int, ...] = (9100,)) -> None:
        """终结孤儿 relay 进程并回收指定端口，防止切换 iPhone 时发生端口冲突"""
        if cls._relay_proc is not None:
            try:
                cls._relay_proc.terminate()
                cls._relay_proc.wait(timeout=0.6)
            except Exception:
                try:
                    cls._relay_proc.kill()
                except Exception:
                    pass
            cls._relay_proc = None
        cls._relay_udid = ""

        my_pid = os.getpid()
        if sys.platform == "win32":
            creationflags = 0x08000000
            for port in ports:
                try:
                    out = subprocess.check_output(
                        f'netstat -ano | findstr ":{port} "',
                        shell=True,
                        text=True,
                        errors="ignore",
                        creationflags=creationflags,
                    )
                    for line in out.splitlines():
                        parts = line.strip().split()
                        if len(parts) >= 5 and "LISTENING" in line:
                            pid_str = parts[-1]
                            if pid_str.isdigit():
                                pid = int(pid_str)
                                if pid != my_pid and pid > 4:
                                    subprocess.run(
                                        f"taskkill /F /PID {pid}",
                                        shell=True,
                                        capture_output=True,
                                        creationflags=creationflags,
                                    )
                except Exception:
                    pass
        else:
            port_strs = tuple(str(p) for p in ports)
            for p in psutil.process_iter(["pid", "cmdline"]):
                try:
                    if p.info["pid"] == my_pid:
                        continue
                    cmdline = " ".join(p.info.get("cmdline") or []).lower()
                    if not cmdline:
                        continue
                    if any(
                        f"relay {ps}" in cmdline or f"forward {ps}" in cmdline or f"iproxy {ps}" in cmdline
                        for ps in port_strs
                    ):
                        p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

    @classmethod
    def get_device_product_version(cls, udid: str) -> Optional[str]:
        """高速查询目标 iOS 设备的系统版本（优先内存缓存）"""
        if not udid or udid.startswith("wda_localhost"):
            return None
        cached = cls._version_cache.get(udid)
        if cached:
            return cached
        try:
            from pymobiledevice3.lockdown import create_using_usbmux

            async def _query() -> str:
                ld = await create_using_usbmux(serial=udid, autopair=False, connection_type="USB")
                try:
                    ver = str(getattr(ld, "product_version", "") or "")
                    if ver:
                        cls._version_cache[udid] = ver
                    return ver
                finally:
                    await ld.close()

            return asyncio.run(asyncio.wait_for(_query(), timeout=1.0))
        except Exception:
            return None

    @classmethod
    def test_wda_status(cls, url: str, timeout: float = 1.2) -> bool:
        """测试指定 URL 的 WDA 是否正常响应（前置 40ms 极速 TCP 探活）"""
        try:
            parsed = urlparse(url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 8100
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.04)
                if s.connect_ex((host, port)) != 0:
                    return False
            req = urllib.request.Request(f"{url.rstrip('/')}/status")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    raw = resp.read().decode("utf-8", errors="ignore")
                    data = json.loads(raw)
                    return isinstance(data, dict) and ("value" in data or "sessionId" in data)
        except Exception:
            pass
        return False

    @classmethod
    def get_wda_url(cls, udid: str = "", allow_spawn: bool = False) -> Tuple[Optional[str], str]:
        """获取当前可用的 WDA 服务地址，按需拉起 8100 usbmux 端口转发"""
        for port in (8100, 8200):
            test_url = f"http://127.0.0.1:{port}"
            if cls.test_wda_status(test_url, timeout=0.6):
                cls._active_wda_url = test_url
                return test_url, f"WDA 服务已连通 ({test_url})"

        if allow_spawn and udid and not udid.startswith("wda_localhost"):
            relay_cmd = _resolve_tidevice_cmd(udid, "relay", "8100", "8100")
            if relay_cmd:
                try:
                    if cls._relay_udid and cls._relay_udid != udid:
                        cls.kill_relays((8100,))

                    creationflags = 0x08000000 if sys.platform == "win32" else 0
                    if cls._relay_proc is None or cls._relay_proc.poll() is not None:
                        cls.kill_relays((8100,))
                        cls._relay_proc = subprocess.Popen(
                            relay_cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=creationflags,
                        )
                        cls._relay_udid = udid
                        time.sleep(0.35)
                    if cls.test_wda_status("http://127.0.0.1:8100", timeout=0.8):
                        cls._active_wda_url = "http://127.0.0.1:8100"
                        return "http://127.0.0.1:8100", "已通过 tidevice relay 映射 8100 端口"
                except Exception:
                    pass

        return None, "未检测到本地活跃 WDA 端口 (8100/8200)"


def check_ios_wda_services() -> Tuple[bool, bool]:
    """
    检查 iOS WDA 8100 双核心服务状态：
    返回 (is_xcuitest_running, is_forward_running)。
    """
    try:
        if IosWdaManager.test_wda_status("http://127.0.0.1:8100", timeout=0.35):
            return True, True
    except Exception:
        pass

    is_xcuitest = False
    is_forward = False

    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                if not cmdline:
                    continue
                cmdline_str = " ".join(cmdline).lower()

                if (
                    ("dvt" in cmdline_str and "xcuitest" in cmdline_str)
                    or ("webdriveragentrunner" in cmdline_str and "pymobiledevice3" in cmdline_str)
                    or ("tidevice" in cmdline_str and "wdaproxy" in cmdline_str)
                ):
                    is_xcuitest = True

                if "8100" in cmdline_str and (
                    ("usbmux" in cmdline_str and "forward" in cmdline_str)
                    or ("tidevice" in cmdline_str and ("relay" in cmdline_str or "wdaproxy" in cmdline_str))
                    or "iproxy" in cmdline_str
                ):
                    try:
                        with socket.create_connection(("127.0.0.1", 8100), timeout=0.35):
                            is_forward = True
                    except Exception:
                        is_forward = False

                if is_xcuitest and is_forward:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logger.debug(f"[IosService] 扫描服务进程异常: {e}")

    return is_xcuitest, is_forward


def _wda_log_path() -> str:
    """获取 iOS WDA 守护日志路径（统一收敛至项目可写日志目录 LOGS_DIR）。"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, "santiao_ios_wda.log")


def _read_wda_failure_hint(log_file: str) -> str:
    """从守护日志尾部提取一条最关键的失败原因，便于在 Mac/Win 打包版界面直接提示"""
    if not os.path.isfile(log_file):
        return ""
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = [ln.strip() for ln in f.readlines()[-25:] if ln.strip()]
        for ln in reversed(lines):
            if any(tag in ln for tag in ("❌", "DTXNsError", "未检测到 USB", "Failed to launch", "ERROR", "异常")):
                return ln[:140]
        return lines[-1][:140] if lines else ""
    except Exception:
        return ""


class IosServiceActionWorker(QThread):
    """
    iOS WDA 自动化服务异步控制线程：
    同时原生支持源码开发态 (start_ios_wda.py) 与 Mac .dmg / Win .exe 打包冻结态 ([sys.executable, "--internal-wda"])，
    支持进程树彻底清理、独立会话守护与提前异常退出快速失败提示。
    """

    finished_sig = pyqtSignal(bool, str, str)

    def __init__(self, action: str, parent: Any = None) -> None:
        super().__init__(parent)
        self.action = action
        self._last_wda_err: str = ""

        project_root = SmartPathResolver.get_project_root()
        if not project_root or not os.path.isdir(os.path.join(project_root, "scripts")):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(base_dir, "..", "..", "..", ".."))
        self.stop_bat = os.path.join(project_root, "scripts", "stop_ios_wda.bat")
        self.start_bat = os.path.join(project_root, "scripts", "start_ios_wda.bat")

    def _get_python_exe(self) -> str:
        """获取真实 Python 解释器路径，严禁在打包态将 GUI 主程序当作 python 执行脚本"""
        if not getattr(sys, "frozen", False) and sys.executable and "python" in os.path.basename(sys.executable).lower():
            return sys.executable
        try:
            py_info = SmartPathResolver.discover_python_runtime()
            if py_info and py_info.get("executable"):
                return str(py_info["executable"])
        except Exception:
            pass
        return shutil.which("python") or shutil.which("python3") or "python"

    def _execute_stop_bat(self) -> bool:
        """静默执行停止脚本并回收 --internal-wda / start_ios_wda / relay 8100 关联进程树"""
        is_frozen = bool(getattr(sys, "frozen", False))
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        if not is_frozen:
            stop_py = os.path.join(os.path.dirname(self.stop_bat), "stop_ios_wda.py")
            py_exe = self._get_python_exe()
            try:
                if os.path.exists(stop_py) and py_exe:
                    subprocess.run(
                        [py_exe, "-u", stop_py],
                        capture_output=True,
                        timeout=8,
                        creationflags=creationflags,
                        cwd=os.path.dirname(stop_py),
                    )
                elif os.path.exists(self.stop_bat) and sys.platform == "win32":
                    proc = subprocess.Popen(
                        ["cmd.exe", "/c", self.stop_bat],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=creationflags,
                        cwd=os.path.dirname(self.stop_bat),
                    )
                    try:
                        proc.communicate(input=b"\r\n", timeout=8)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
            except Exception as e:
                logger.debug(f"[IosService] 停止脚本执行异常: {e}")

        target_kws = (
            "--internal-wda",
            "start_ios_wda",
            "usbmux forward 8100",
            "relay 8100",
            "developer dvt xcuitest",
            "webdriveragentrunner",
        )
        my_pid = os.getpid()
        for p in psutil.process_iter(["pid", "cmdline"]):
            try:
                if p.info["pid"] == my_pid:
                    continue
                cmdline = " ".join(p.info.get("cmdline") or []).lower()
                if not cmdline:
                    continue
                if any(kw in cmdline for kw in target_kws):
                    try:
                        for child in p.children(recursive=True):
                            if child.pid == my_pid:
                                continue
                            try:
                                child.kill()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        for _ in range(10):
            is_xcuitest, is_forward = check_ios_wda_services()
            if not is_xcuitest and not is_forward:
                break
            time.sleep(0.3)

        return True

    def _execute_start_bat(self) -> bool:
        """启动 WDA 守护进程（打包态走 --internal-wda，开发态走 start_ios_wda.py）并轮询等待双服务就绪"""
        self._last_wda_err = ""
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        is_frozen = bool(getattr(sys, "frozen", False))
        log_file = _wda_log_path()

        proc: Optional[subprocess.Popen] = None
        log_fp = None
        try:
            if is_frozen:
                work_dir = os.path.dirname(self.start_bat)
                if not os.path.isdir(work_dir):
                    work_dir = WRITABLE_ROOT
                try:
                    log_fp = open(log_file, "w", encoding="utf-8", errors="replace")
                except Exception:
                    log_fp = None

                popen_kwargs: Dict[str, Any] = {
                    "stdin": subprocess.DEVNULL,
                    "stdout": log_fp if log_fp is not None else subprocess.DEVNULL,
                    "stderr": subprocess.STDOUT if log_fp is not None else subprocess.DEVNULL,
                    "creationflags": creationflags,
                    "cwd": work_dir,
                }
                if sys.platform != "win32":
                    popen_kwargs["start_new_session"] = True
                proc = subprocess.Popen([sys.executable, "--internal-wda"], **popen_kwargs)
            else:
                start_py = os.path.join(os.path.dirname(self.start_bat), "start_ios_wda.py")
                if not os.path.exists(start_py) and not os.path.exists(self.start_bat):
                    self._last_wda_err = f"未找到启动脚本: {self.start_bat}"
                    logger.warning(f"[IosService] {self._last_wda_err}")
                    return False

                py_exe = self._get_python_exe()
                if os.path.exists(start_py) and py_exe:
                    try:
                        log_fp = open(log_file, "w", encoding="utf-8", errors="replace")
                    except Exception:
                        log_fp = None
                    popen_kwargs = {
                        "stdin": subprocess.DEVNULL,
                        "stdout": log_fp if log_fp is not None else subprocess.DEVNULL,
                        "stderr": subprocess.STDOUT if log_fp is not None else subprocess.DEVNULL,
                        "creationflags": creationflags,
                        "cwd": os.path.dirname(start_py),
                    }
                    if sys.platform != "win32":
                        popen_kwargs["start_new_session"] = True
                    proc = subprocess.Popen([py_exe, "-u", start_py], **popen_kwargs)
                else:
                    proc = subprocess.Popen(
                        ["cmd.exe", "/c", self.start_bat],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags,
                        cwd=os.path.dirname(self.start_bat),
                    )
        except Exception as e:
            self._last_wda_err = str(e)
            logger.error(f"[IosService] 执行启动脚本异常: {e}")
            return False
        finally:
            if log_fp is not None:
                try:
                    log_fp.close()
                except Exception:
                    pass

        stable_ticks = 0
        for _ in range(60):
            time.sleep(0.5)
            is_xcuitest, is_forward = check_ios_wda_services()
            if is_xcuitest and is_forward:
                stable_ticks += 1
                if stable_ticks >= 3:
                    return True
            else:
                stable_ticks = 0
                if proc is not None and proc.poll() is not None:
                    self._last_wda_err = _read_wda_failure_hint(log_file)
                    return False

        self._last_wda_err = _read_wda_failure_hint(log_file)
        return False

    def run(self) -> None:
        if self.action == "stop":
            self._execute_stop_bat()
            self.finished_sig.emit(True, "服务已停止", "stop")
        else:
            self._execute_stop_bat()
            ok = self._execute_start_bat()
            if ok:
                self.finished_sig.emit(True, "服务已启动", "start_or_restart")
            else:
                hint = self._last_wda_err.strip()
                msg = f"服务启动未完全就绪: {hint}" if hint else "服务启动未完全就绪"
                self.finished_sig.emit(False, msg, "start_or_restart")


def scan_ios_devices(seen_udids: Set[str]) -> List[Dict[str, Any]]:
    """探测当前在线的 iOS 设备（usbmux 直连 -> tidevice -> Win32 PnP -> 本地 WDA 端口）"""
    devices: List[Dict[str, Any]] = []
    creationflags = 0x08000000 if sys.platform == "win32" else 0

    try:
        from pymobiledevice3.lockdown import create_using_usbmux as pmd_create_lockdown
        from pymobiledevice3.usbmux import list_devices as pmd_list_devices

        async def _scan_ios_usbmux() -> List[Dict[str, Any]]:
            found_ios: List[Dict[str, Any]] = []
            mux_devs = await asyncio.wait_for(pmd_list_devices(), timeout=1.5)
            for mdev in mux_devs or []:
                udid = str(getattr(mdev, "serial", "") or "").strip()
                if not udid or udid in seen_udids:
                    continue
                model_desc = "iPhone"
                with contextlib.suppress(Exception):
                    ld = await asyncio.wait_for(
                        pmd_create_lockdown(serial=udid, autopair=False, connection_type="USB"),
                        timeout=1.2,
                    )
                    try:
                        m_name = getattr(ld, "display_name", None) or getattr(ld, "short_product_type", None) or ""
                        d_name = getattr(ld, "device_name", None) or ""
                        p_ver = str(getattr(ld, "product_version", "") or "")
                        if p_ver:
                            IosWdaManager._version_cache[udid] = p_ver
                        if m_name and d_name and d_name != m_name:
                            model_desc = f"{m_name} · {d_name}"
                        elif m_name or d_name:
                            model_desc = str(m_name or d_name)
                    finally:
                        with contextlib.suppress(Exception):
                            await ld.close()
                seen_udids.add(udid)
                found_ios.append({
                    "udid": udid,
                    "platform": "ios",
                    "name": f"苹果真机 ({model_desc}): {udid}",
                    "is_real": True,
                })
            return found_ios

        ios_list = asyncio.run(_scan_ios_usbmux())
        if ios_list:
            devices.extend(ios_list)
    except Exception:
        pass

    td_cmd = _resolve_tidevice_cmd("", "list")
    if td_cmd:
        try:
            out = subprocess.check_output(
                td_cmd,
                text=True,
                errors="ignore",
                timeout=3.5,
                creationflags=creationflags,
            ).strip()
            for line in out.splitlines():
                parts = line.strip().split()
                if parts and "udid" not in parts[0].lower():
                    udid = parts[0]
                    if udid and udid not in seen_udids and len(udid) >= 20:
                        seen_udids.add(udid)
                        model = " ".join(parts[2:]) if len(parts) > 2 else (parts[1] if len(parts) > 1 else "iPhone")
                        devices.append({
                            "udid": udid,
                            "platform": "ios",
                            "name": f"苹果真机 ({model}): {udid}",
                            "is_real": True,
                        })
        except Exception:
            pass

    if sys.platform == "win32":
        try:
            import ctypes
            import winreg
            from ctypes import wintypes

            cfgmgr32 = ctypes.windll.cfgmgr32
            base_key = r"SYSTEM\CurrentControlSet\Enum\USB\VID_05AC" + "&PID_12A8"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key) as k:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(k, i)
                        i += 1
                        raw_id = sub.strip()
                        devnode = wintypes.DWORD()
                        status = wintypes.DWORD()
                        problem = wintypes.DWORD()
                        dev_inst = "USB\\VID_05AC" + "&PID_12A8\\" + raw_id
                        if cfgmgr32.CM_Locate_DevNodeW(ctypes.byref(devnode), dev_inst, 0) == 0:
                            if cfgmgr32.CM_Get_DevNode_Status(ctypes.byref(status), ctypes.byref(problem), devnode, 0) == 0:
                                udid = f"{raw_id[:8]}-{raw_id[8:]}" if (len(raw_id) == 24 and "-" not in raw_id) else raw_id
                                if udid and udid not in seen_udids:
                                    seen_udids.add(udid)
                                    devices.append({
                                        "udid": udid,
                                        "platform": "ios",
                                        "name": f"苹果真机 (iPhone): {udid}",
                                        "is_real": True,
                                    })
                    except OSError:
                        break
        except Exception:
            pass

    for p in (8100, 8200):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.04)
                if s.connect_ex(("127.0.0.1", p)) == 0:
                    tag = f"wda_localhost_{p}"
                    if tag not in seen_udids:
                        seen_udids.add(tag)
                        devices.append({
                            "udid": tag,
                            "platform": "ios",
                            "name": f"iOS设备 (WDA {p} 在线)",
                            "is_real": True,
                        })
        except Exception:
            pass

    return devices


def run_ios_action(action: str, udid: str = "", **kwargs: Any) -> bool:
    """执行 iOS 动作（优先 CoreDevice HID 通道，降级 WDA HTTP）"""
    if _IOS_HID_DISPATCHER is not None and _IOS_HID_DISPATCHER(action, **kwargs):
        return True

    wda_url, _ = IosWdaManager.get_wda_url(udid, allow_spawn=False)
    if not wda_url:
        return False
    try:
        if action == "tap":
            x, y = kwargs.get("x", 0), kwargs.get("y", 0)
            data = json.dumps({"x": x, "y": y}).encode("utf-8")
            req = urllib.request.Request(f"{wda_url}/wda/tap/0", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status == 200
        if action == "swipe":
            data = json.dumps({
                "fromX": kwargs.get("x1", 0),
                "fromY": kwargs.get("y1", 0),
                "toX": kwargs.get("x2", 0),
                "toY": kwargs.get("y2", 0),
                "duration": kwargs.get("duration", 0.3),
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{wda_url}/wda/dragfromtoforduration",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                return resp.status == 200
        if action == "home":
            req = urllib.request.Request(f"{wda_url}/wda/homescreen", data=b"{}", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status == 200
        if action == "keys":
            text = kwargs.get("text", "")
            data = json.dumps({"value": list(text)}).encode("utf-8")
            req = urllib.request.Request(f"{wda_url}/wda/keys", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                return resp.status == 200
        if action == "clear":
            req = urllib.request.Request(f"{wda_url}/wda/element/active", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    el_id = json.loads(resp.read().decode("utf-8")).get("value", {}).get("ELEMENT")
                    if el_id:
                        del_req = urllib.request.Request(
                            f"{wda_url}/element/{el_id}/clear",
                            data=b"{}",
                            headers={"Content-Type": "application/json"},
                        )
                        with urllib.request.urlopen(del_req, timeout=1.5):
                            return True
    except Exception:
        pass
    return False
