# -*- coding: utf-8 -*-
"""
三端平台引擎公共基础工具：
1. 坐标边界解析 (parse_bounds_wh)；
2. 活跃 Appium Server 会话探测 (fetch_active_appium_source，兼容 Appium 2.x /appium/sessions 与 1.x /sessions)；
3. 截屏超时占位图生成 (create_placeholder_screenshot)。
"""
import json
import re
import socket
import urllib.request
from typing import Callable, Iterable, Optional, Tuple

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen


def parse_bounds_wh(bounds_str: str) -> Tuple[int, int, int, int]:
    """解析 '[l,t][r,b]' 为 (left, top, width, height)"""
    m = re.match(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", str(bounds_str or ""))
    if not m:
        return 0, 0, 0, 0
    left, top, right, bottom = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return left, top, max(0, right - left), max(0, bottom - top)


def fetch_active_appium_source(
    ports: Iterable[int],
    udid: str,
    platform_filter: Optional[str] = None,
    source_validator: Optional[Callable[[str], bool]] = None,
    source_timeout: float = 3.0,
) -> Optional[Tuple[str, int, str]]:
    """
    探测本地活跃的 Appium Server 会话并拉取 /source（兼容 Appium 2.x 与 1.x 路径）。
    命中时返回 (xml_source, port, session_id)，未命中返回 None。
    """
    endpoints = (
        ("", "/appium/sessions"),
        ("/wd/hub", "/appium/sessions"),
        ("", "/sessions"),
        ("/wd/hub", "/sessions"),
    )
    want_plat = (platform_filter or "").strip().lower()

    for port in ports:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.05):
                pass
        except Exception:
            continue

        for base_prefix, list_ep in endpoints:
            base_url = f"http://127.0.0.1:{port}{base_prefix}"
            try:
                req = urllib.request.Request(f"{base_url}{list_ep}")
                with urllib.request.urlopen(req, timeout=0.4) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                sessions = data.get("value") or []
                if not isinstance(sessions, list):
                    continue

                for sess in sessions:
                    if not isinstance(sess, dict):
                        continue
                    sid = str(sess.get("id") or "")
                    if not sid:
                        continue
                    caps = sess.get("capabilities") or {}
                    sess_plat = str(caps.get("platformName") or "").strip().lower()
                    sess_udid = str(
                        caps.get("deviceUDID")
                        or caps.get("udid")
                        or caps.get("deviceName")
                        or ""
                    )

                    if want_plat and sess_plat and sess_plat != want_plat and len(sessions) > 1:
                        continue
                    if udid and sess_udid and (udid not in sess_udid) and len(sessions) > 1:
                        continue

                    src_req = urllib.request.Request(f"{base_url}/session/{sid}/source")
                    with urllib.request.urlopen(src_req, timeout=source_timeout) as src_resp:
                        src_data = json.loads(src_resp.read().decode("utf-8", errors="ignore"))
                    xml_str = src_data.get("value") or ""
                    if not isinstance(xml_str, str) or len(xml_str) <= 100:
                        continue
                    if source_validator is None or source_validator(xml_str):
                        return xml_str, port, sid
            except Exception:
                continue

    return None


def create_placeholder_screenshot(
    dest_path: str,
    width: int,
    height: int,
    title: str,
    subtitle: str,
) -> bool:
    """当 DOM 已抓取成功但截屏临时超时时，生成轻量占位图确保审查链路不中断"""
    try:
        qimg = QImage(width, height, QImage.Format.Format_RGB32)
        qimg.fill(QColor("#f8fafc"))
        painter = QPainter(qimg)
        painter.setPen(QPen(QColor("#cbd5e1"), 2))
        painter.drawRect(20, 20, max(10, width - 40), max(10, height - 40))
        painter.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        painter.setPen(QColor("#64748b"))
        painter.drawText(QRect(40, int(height * 0.42), max(10, width - 80), 100), Qt.AlignmentFlag.AlignCenter, title)
        painter.setFont(QFont("Microsoft YaHei", 14))
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(QRect(40, int(height * 0.47), max(10, width - 80), 80), Qt.AlignmentFlag.AlignCenter, subtitle)
        painter.end()
        return qimg.save(dest_path, "PNG")
    except Exception:
        return False
