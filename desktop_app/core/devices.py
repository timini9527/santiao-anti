# -*- coding: utf-8 -*-
"""桌面端跨平台设备探测与 Appium 服务管理模块。"""
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.request
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("desktop_app")


def get_local_ip() -> str:
    """动态获取本机当前局域网有效 IP（自适应 192.168.*、10.*、172.* 等网段）。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    # 备用方案：通过 socket 获取本机 IP 列表进行过滤
    try:
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        for ip in ip_list:
            if not ip.startswith("127.") and not ip.startswith("169.254.") and not ip.endswith(".1"):
                return ip
    except Exception:
        pass

    return "127.0.0.1"


def detect_appium_status(port: int = 4723) -> str:
    """探测本地 Appium 服务是否可用，成功返回 `{local_ip}:{port}`，失败返回空字符串。"""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/status")
        with urllib.request.urlopen(req, timeout=1) as response:
            if response.status == 200:
                local_ip = get_local_ip()
                return f"{local_ip}:{port}"
    except Exception:
        pass
    return ""


def get_configured_devices() -> Tuple[str, str]:
    """返回控制台默认绑定的双机设备 UDID（发送端, 接收端）。"""
    return "QFF0219A11009305", "20a5fa17"


def detect_raw_connected_devices() -> List[Tuple[str, str, bool]]:
    """探测当前连接的移动设备（Android ADB / HarmonyOS HDC / iOS），返回 [(udid, platform, is_real)]。"""
    raw_devices: List[Tuple[str, str, bool]] = []
    no_window = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    # 动态感知系统或 SDK 安装目录中的 adb / hdc / ios 工具链
    toolchain: Dict[str, Any] = {}
    try:
        from desktop_app.core.path_resolver import SmartPathResolver

        toolchain = SmartPathResolver.discover_mobile_toolchain()
    except Exception:
        pass
    adb_bin = toolchain.get("adb") or shutil.which("adb") or "adb"
    hdc_bin = toolchain.get("hdc") or shutil.which("hdc") or "hdc"

    # 1. 使用 adb 探测安卓设备
    try:
        out = subprocess.check_output([adb_bin, "devices"], timeout=4, creationflags=no_window).decode(
            "utf-8", errors="ignore"
        )
        for line in out.strip().split("\n")[1:]:
            if "\tdevice" in line:
                udid = line.split("\t")[0].strip()
                if udid:
                    is_real = not (udid.startswith("emulator-") or "127.0.0.1" in udid or "localhost" in udid)
                    raw_devices.append((udid, "Android", is_real))
    except Exception as e:
        logger.warning(f"ADB 设备探测异常: {e}")

    # 2. 使用 hdc 探测鸿蒙设备
    try:
        out = subprocess.check_output([hdc_bin, "list", "targets"], timeout=5, creationflags=no_window).decode(
            "utf-8", errors="ignore"
        )
        for line in out.strip().split("\n"):
            line_str = line.strip()
            if (
                line_str
                and "Empty" not in line_str
                and "Error" not in line_str
                and "not found" not in line_str
                and "fail" not in line_str.lower()
            ):
                raw_devices.append((line_str, "HarmonyOS", True))
    except Exception as e:
        logger.warning(f"HDC 设备探测异常: {e}")

    # 3. 探测 iOS 设备（内嵌 tidevice -> 内嵌 pymobiledevice3 -> 外部 CLI -> macOS 原生 USB 总线 -> xcrun）
    ios_udids_seen = set()

    # 3.1 首选：内嵌 tidevice._usbmux 直连 usbmuxd 探测
    try:
        from tidevice._usbmux import Usbmux

        for dev in Usbmux().device_list():
            udid = getattr(dev, "udid", "").strip()
            if udid and udid not in ios_udids_seen:
                ios_udids_seen.add(udid)
                raw_devices.append((udid, "iOS", True))
    except Exception as e:
        logger.warning(f"内嵌 tidevice.Usbmux iOS 设备探测异常: {e}")

    # 3.2 次选：内嵌 pymobiledevice3.usbmux 探测
    if not ios_udids_seen:
        try:
            from pymobiledevice3 import usbmux as pmd_usbmux

            for dev in pmd_usbmux.list_devices():
                udid = getattr(dev, "serial", "").strip()
                if udid and udid not in ios_udids_seen:
                    ios_udids_seen.add(udid)
                    raw_devices.append((udid, "iOS", True))
        except Exception as e:
            logger.warning(f"内嵌 pymobiledevice3 iOS 设备探测异常: {e}")

    # 3.3 备选：外部 tidevice / idevice_id CLI 探测
    if not ios_udids_seen:
        tidevice_bin = toolchain.get("tidevice") or shutil.which("tidevice")
        if tidevice_bin:
            try:
                out = subprocess.check_output([tidevice_bin, "list"], timeout=4, creationflags=no_window).decode(
                    "utf-8", errors="ignore"
                )
                for line in out.strip().split("\n")[1:]:
                    parts = line.split()
                    if parts:
                        udid = parts[0].strip()
                        if (
                            len(udid) >= 24
                            and all(c in "0123456789abcdefABCDEF-" for c in udid)
                            and udid not in ios_udids_seen
                        ):
                            ios_udids_seen.add(udid)
                            raw_devices.append((udid, "iOS", True))
            except Exception as e:
                logger.warning(f"tidevice CLI iOS 设备探测异常: {e}")

    if not ios_udids_seen:
        idevice_bin = toolchain.get("idevice_id") or shutil.which("idevice_id")
        if idevice_bin:
            try:
                out = subprocess.check_output([idevice_bin, "-l"], timeout=4, creationflags=no_window).decode(
                    "utf-8", errors="ignore"
                )
                for line in out.strip().splitlines():
                    udid = line.strip()
                    if (
                        len(udid) >= 24
                        and all(c in "0123456789abcdefABCDEF-" for c in udid)
                        and udid not in ios_udids_seen
                    ):
                        ios_udids_seen.add(udid)
                        raw_devices.append((udid, "iOS", True))
            except Exception as e:
                logger.warning(f"idevice_id iOS 设备探测异常: {e}")

    # 3.4 macOS 原生兜底：system_profiler SPUSBDataType
    if not ios_udids_seen and sys.platform == "darwin":
        try:
            out = subprocess.check_output(["system_profiler", "SPUSBDataType"], timeout=5).decode(
                "utf-8", errors="ignore"
            )
            current_is_ios = False
            for line in out.splitlines():
                stripped = line.strip()
                if stripped.startswith(("iPhone:", "iPad:")):
                    current_is_ios = True
                elif stripped.endswith(":") and not stripped.startswith(
                    ("Serial Number:", "Vendor ID:", "Product ID:")
                ):
                    if "Apple" not in stripped:
                        current_is_ios = False
                elif current_is_ios and stripped.startswith("Serial Number:"):
                    serial = stripped.split(":", 1)[1].strip()
                    if len(serial) == 24 and all(c in "0123456789abcdefABCDEF" for c in serial):
                        udid = f"{serial[:8]}-{serial[8:]}"
                    elif len(serial) >= 24 and all(c in "0123456789abcdefABCDEF-" for c in serial):
                        udid = serial
                    else:
                        udid = ""
                    if udid and udid not in ios_udids_seen:
                        ios_udids_seen.add(udid)
                        raw_devices.append((udid, "iOS", True))
                    current_is_ios = False
        except Exception as e:
            logger.warning(f"system_profiler iOS 设备探测异常: {e}")

    # 3.5 macOS 最终兜底：xcrun xctrace list devices
    if not ios_udids_seen and sys.platform == "darwin":
        xcrun_bin = toolchain.get("xcrun") or shutil.which("xcrun")
        if xcrun_bin:
            try:
                out = subprocess.check_output([xcrun_bin, "xctrace", "list", "devices"], timeout=12).decode(
                    "utf-8", errors="ignore"
                )
                in_devices_section = False
                for line in out.splitlines():
                    if "== Devices ==" in line:
                        in_devices_section = True
                        continue
                    if "== Simulators ==" in line:
                        break
                    if in_devices_section and "(" in line and ")" in line:
                        match = re.search(r"\(([0-9a-fA-F\-]{24,})\)", line)
                        if match:
                            udid = match.group(1).strip()
                            if udid not in ios_udids_seen:
                                ios_udids_seen.add(udid)
                                raw_devices.append((udid, "iOS", True))
            except Exception as e:
                logger.warning(f"xcrun iOS 设备探测异常: {e}")

    return raw_devices


def detect_device_details() -> Dict[str, Any]:
    """获取详细的设备列表及 USB 物理真机/模拟器分类信息。"""
    raw_devices = detect_raw_connected_devices()
    default_sender, default_receiver = get_configured_devices()

    real_devices: List[str] = []
    emulator_devices: List[str] = []
    all_devices: List[str] = []
    device_items: List[Dict[str, Any]] = []
    legacy_devices: List[str] = []

    for udid, platform, is_real in raw_devices:
        all_devices.append(udid)
        if is_real:
            real_devices.append(udid)
            desc = f"USB真机 ({platform})"
        else:
            emulator_devices.append(udid)
            desc = f"模拟器 ({platform})"

        device_items.append(
            {
                "udid": udid,
                "desc": desc,
                "is_real": is_real,
                "platform": platform,
            }
        )
        legacy_devices.append(f"{udid} ({'USB真机' if is_real else '模拟器'})")

    return {
        "real_devices": real_devices,
        "emulator_devices": emulator_devices,
        "all_devices": all_devices,
        "device_items": device_items,
        "legacy_devices": legacy_devices,
        "sender_default": default_sender,
        "receiver_default": default_receiver,
    }


def detect_connected_devices() -> List[str]:
    """返回格式化后的设备描述列表，物理真机优先排列。"""
    details = detect_device_details()
    return details["legacy_devices"]


def start_appium_server(os_type: str = "windows", port: int = 4723) -> bool:
    """在后台拉起 Appium 服务并监听 0.0.0.0。"""
    try:
        if os_type == "windows":
            if port == 4723:
                subprocess.Popen(["cmd.exe", "/c", "start", "appium", "-a", "0.0.0.0"])
            else:
                subprocess.Popen(["cmd.exe", "/c", "start", "appium", "-p", str(port), "-a", "0.0.0.0"])
        elif os_type == "mac":
            if port == 4723:
                subprocess.Popen(["osascript", "-e", 'tell application "Terminal" to do script "appium -a 0.0.0.0"'])
            else:
                subprocess.Popen(
                    ["osascript", "-e", f'tell application "Terminal" to do script "appium -p {port} -a 0.0.0.0"']
                )
        else:
            if port == 4723:
                subprocess.Popen(
                    ["appium", "-a", "0.0.0.0"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            else:
                subprocess.Popen(
                    ["appium", "-p", str(port), "-a", "0.0.0.0"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
        return True
    except Exception as e:
        logger.error(f"启动 Appium 服务失败: {e}")
        return False
