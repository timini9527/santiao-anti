# -*- coding: utf-8 -*-
"""
三端设备发现聚合与跨平台动作分发中枢：
1. get_connected_devices / DeviceScanWorker：聚合鸿蒙、安卓、iOS 在线设备列表；
2. DeviceController：统一按平台路由点击、滑动、输入与清空动作。
"""
from typing import Any, Dict, List, Set

from PyQt6.QtCore import QThread, pyqtSignal

from desktop_app.ui.inspector.platforms.android import (
    android_clear_text,
    android_input_text,
    android_swipe,
    android_tap,
    scan_android_devices,
)
from desktop_app.ui.inspector.platforms.harmony import (
    harmony_clear_text,
    harmony_input_text,
    harmony_swipe,
    harmony_tap,
    scan_harmony_devices,
)
from desktop_app.ui.inspector.platforms.ios_service import run_ios_action, scan_ios_devices


def get_connected_devices() -> List[Dict[str, Any]]:
    """全自动探测 HarmonyOS / Android / iOS 当前在线设备列表"""
    devices: List[Dict[str, Any]] = []
    seen_udids: Set[str] = set()
    devices.extend(scan_harmony_devices(seen_udids))
    devices.extend(scan_android_devices(seen_udids))
    devices.extend(scan_ios_devices(seen_udids))
    return devices


class DeviceScanWorker(QThread):
    """后台异步设备探测线程，保障 UI 主线程零阻塞"""

    devices_ready = pyqtSignal(list)

    def run(self) -> None:
        try:
            self.devices_ready.emit(get_connected_devices())
        except Exception:
            self.devices_ready.emit([])


class DeviceController:
    """跨平台设备统一动作控制中枢"""

    @staticmethod
    def tap(platform: str, udid: str, x: int, y: int) -> None:
        if platform == "harmony":
            harmony_tap(udid, x, y)
        elif platform == "android":
            android_tap(udid, x, y)
        elif platform == "ios":
            run_ios_action("tap", udid, x=x, y=y)

    @staticmethod
    def swipe(
        platform: str,
        udid: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_ms: int = 300,
    ) -> None:
        if platform == "harmony":
            harmony_swipe(udid, x1, y1, x2, y2, duration_ms)
        elif platform == "android":
            android_swipe(udid, x1, y1, x2, y2, duration_ms)
        elif platform == "ios":
            run_ios_action("swipe", udid, x1=x1, y1=y1, x2=x2, y2=y2, duration=duration_ms / 1000.0)

    @staticmethod
    def input_text(platform: str, udid: str, text: str, cx: int = 0, cy: int = 0) -> None:
        if platform == "harmony":
            harmony_input_text(udid, text, cx, cy)
        elif platform == "android":
            android_input_text(udid, text, cx, cy)
        elif platform == "ios":
            if cx and cy:
                run_ios_action("tap", udid, x=cx, y=cy)
            run_ios_action("keys", udid, text=text)

    @staticmethod
    def clear_text(platform: str, udid: str, cx: int = 0, cy: int = 0) -> None:
        if platform == "harmony":
            harmony_clear_text(udid, cx, cy)
        elif platform == "android":
            android_clear_text(udid, cx, cy)
        elif platform == "ios":
            if cx and cy:
                run_ios_action("tap", udid, x=cx, y=cy)
            run_ios_action("clear", udid)
