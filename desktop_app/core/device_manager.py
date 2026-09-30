# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 设备与端口管理
=======================================================
"""
import os
import sys
import socket
import urllib.request
from typing import Dict, Any, List, Tuple

from desktop_app.config import PROJECT_ROOT

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web_platform.backend.devices import (
    get_local_ip,
    detect_appium_status,
    detect_device_details,
    get_configured_devices
)

class DeviceManager:
    """管理设备连接、端口检测与 Appium 状态"""

    @staticmethod
    def get_local_machine_ip() -> str:
        return get_local_ip()

    @staticmethod
    def check_appium(port: int = 4723) -> Tuple[bool, str]:
        """检测指定端口的 Appium 服务是否存活"""
        url = detect_appium_status(port)
        if url:
            return True, url
        return False, ""

    @staticmethod
    def scan_connected_devices() -> Dict[str, Any]:
        """探测当前物理连接的 USB 设备与默认机型"""
        return detect_device_details()

    @staticmethod
    def get_default_configured_devices() -> Tuple[str, str]:
        """获取系统默认绑定的发送端和接收端手机号"""
        return get_configured_devices()
