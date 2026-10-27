"""
================================================================================
Santiao Mobile Inspector - 移动端全平台 UI 审查器 (HarmonyOS / Android / iOS)
================================================================================
1. 架构级支持鸿蒙 HarmonyOS NEXT (HDC)、安卓 Android (ADB)、苹果 iOS (WDA / tidevice) 三端设备驱动；
2. 顶部工具栏 30px 统一紧凑视觉规范，分段式模式切换胶囊，消除臃肿与拥挤；
3. 矢量级 Retina 应用图标与动态平台徽章，支持高 DPI 视网膜高清渲染；
4. 遇到输入框与编辑框时提供专属实时同步控制台 (Live Input Sync Console)，三端秒级同步；
5. 自动根据当前平台推荐最地道权威的 Appium 定位器代码 (ID / Accessibility ID / XPath)；
6. 像素级平滑横向滚动，彻底锁死切换节点时的视口跳动与位移。
================================================================================
"""
import base64
import json
import os
import random
import re
import shutil
import socket
import logging
import struct
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

# 接管 hmnextauto 日志流，重定向至 stdout 规避控制台报红并静默冗余调试信息
for _name in ("hmnextauto", "hmnextauto.hdc", "hmnextauto._client"):
    _lg = logging.getLogger(_name)
    _lg.setLevel(logging.WARNING)
    for _h in _lg.handlers:
        if hasattr(_h, "setStream"):
            _h.setStream(sys.stdout)

logger = logging.getLogger("Inspector")

from desktop_app.core.path_resolver import SmartPathResolver


from PyQt6.QtCore import Qt, QRect, QPoint, QPointF, pyqtSignal, QSize, QRectF, QThread, QTimer, QEvent, QByteArray, QBuffer
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QFont, QIcon, QImage, QKeyEvent, QKeySequence, QLinearGradient,
    QPainter, QPainterPath, QPen, QPixmap, QShortcut, QTextLayout, QTextCharFormat
)
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter, QStyle,
    QStyledItemDelegate, QStyleOptionViewItem, QTableWidget, QTableWidgetItem, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)


# ==============================================================================
# 现代矢量级 Retina 应用图标生成器
# ==============================================================================

def create_modern_app_icon() -> QIcon:
    """动态生成多分辨率矢量级 Retina 应用图标 (克莱因蓝-薄荷绿双色渐变 + 手机准星)"""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 渐变圆角外壳底板 (Squircle)
        rect = QRectF(1.0, 1.0, float(size - 2), float(size - 2))
        radius = float(size) * 0.22
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0.0, QColor("#0284c7"))  # 科技克莱因蓝
        grad.setColorAt(0.55, QColor("#0ea5e9")) # 亮蓝
        grad.setColorAt(1.0, QColor("#10b981"))  # 活力翡翠绿
        p.fillPath(path, QBrush(grad))

        # 2. 手机极简机身轮廓 (纯白细线)
        scale = size / 64.0
        p.setPen(QPen(QColor(255, 255, 255, 230), max(1.5 * scale, 1.2)))
        phone_w = 26.0 * scale
        phone_h = 44.0 * scale
        phone_x = (size - phone_w) / 2.0
        phone_y = (size - phone_h) / 2.0
        p.drawRoundedRect(QRectF(phone_x, phone_y, phone_w, phone_h), 4.0 * scale, 4.0 * scale)

        # 3. 屏幕中心 UI 审查准星瞄准十字
        cx = float(size) / 2.0
        cy = float(size) / 2.0
        r = 6.0 * scale
        p.setPen(QPen(QColor(255, 255, 255, 240), max(1.5 * scale, 1.0)))
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx - r - 3 * scale, cy), QPointF(cx + r + 3 * scale, cy))
        p.drawLine(QPointF(cx, cy - r - 3 * scale), QPointF(cx, cy + r + 3 * scale))

        p.end()
        icon.addPixmap(pix)
    return icon


# ==============================================================================
# 全局 DOM 元素标签莫兰迪低饱和度高级配色中枢 (浅色暗一点规范)
# ==============================================================================

def get_dom_tag_color(c_type: str) -> Dict[str, Any]:
    """
    统一 DOM 元素标签配色方案 (浅色暗一点、低饱和度、耐看护眼，绝无刺眼荧光色):
    - bg: 浅色微暗低饱和度底色 (Muted Light Pastel)
    - border: 同色系微暗轮廓边框色
    - text: 沉稳深色文本色 (确保 WCAG 高对比度清晰易读)
    - box_border: 真机画布高亮边框色
    - box_bg: 真机画布半透明柔和高亮底色
    """
    ct = (c_type or "").strip()

    # 1. 文本与静态展示类 (浅麦芽琥珀金微暗)
    if ct in ("Text", "Span", "StaticText", "label", "TextClock", "Marquee", "XCUIElementTypeStaticText"):
        return {
            "bg": "#fef3c7",        # 浅琥珀微暗底
            "border": "#d97706",    # 沉稳金褐边框
            "text": "#78350f",      # 深琥珀暗棕字
            "box_border": "#d97706",
            "box_bg": QColor(217, 119, 6, 35)
        }

    # 2. 按钮与可交互控件类 (浅天青蓝微暗)
    elif ct in ("Button", "Toggle", "Checkbox", "Radio", "Switch", "LoadingProgress", "Select", "MenuItem", "XCUIElementTypeButton"):
        return {
            "bg": "#e0f2fe",        # 浅天青微暗底
            "border": "#0284c7",    # 科技深蓝边框
            "text": "#075985",      # 深黛青字
            "box_border": "#0284c7",
            "box_bg": QColor(2, 132, 199, 35)
        }

    # 3. 输入编辑与搜索类 (浅幽竹翠绿微暗)
    elif ct in ("TextInput", "TextArea", "Search", "SearchField", "RichEditor", "RichEditorContent", "TextField", "EditText", "XCUIElementTypeTextField", "XCUIElementTypeSecureTextField"):
        return {
            "bg": "#dcfce7",        # 浅幽竹微暗底
            "border": "#16a34a",    # 幽竹翠绿边框
            "text": "#14532d",      # 墨绿字
            "box_border": "#16a34a",
            "box_bg": QColor(22, 163, 74, 35)
        }

    # 4. 图像媒体、图标与角标徽章类 (浅粉珊瑚微暗)
    elif ct in ("Image", "QRCode", "Icon", "SymbolGlyph", "Badge", "Video", "ImageView", "Divider", "XCUIElementTypeImage", "XCUIElementTypeIcon"):
        return {
            "bg": "#ffe4e6",        # 浅珊瑚微暗底
            "border": "#e11d48",    # 玫瑰珊瑚边框
            "text": "#881337",      # 暗酒红字
            "box_border": "#e11d48",
            "box_bg": QColor(225, 29, 72, 35)
        }

    # 5. 列表滚动与流式容器类 (浅薰衣草紫微暗)
    elif ct in ("List", "ListItem", "Scroll", "Refresh", "Swiper", "Grid", "GridItem", "XCUIElementTypeScrollView"):
        return {
            "bg": "#ede9fe",        # 浅薰衣草微暗底
            "border": "#7c3aed",    # 优雅紫罗兰边框
            "text": "#581c87",      # 深紫罗兰字
            "box_border": "#7c3aed",
            "box_bg": QColor(124, 58, 237, 35)
        }

    # 6. 结构排版布局类 (浅石板灰微暗)
    elif ct in ("Column", "Row", "Stack", "Flex", "RelativeContainer", "ViewGroup", "FrameLayout", "LinearLayout", "RelativeLayout", "XCUIElementTypeOther"):
        return {
            "bg": "#f1f5f9",        # 浅石板灰微暗底
            "border": "#64748b",    # 中度石板灰边框
            "text": "#334155",      # 深石板灰字
            "box_border": "#64748b",
            "box_bg": QColor(100, 116, 139, 30)
        }

    # 7. 导航与窗口顶层类 (浅丁香紫微暗)
    elif ct in ("Hierarchy", "root", "Navigation", "NavBar", "NavBarContent", "NavigationContent", "NavDestination", "NavDestinationContent", "WindowScene", "XCUIElementTypeWindow"):
        return {
            "bg": "#f3e8ff",        # 浅丁香紫微暗底
            "border": "#9333ea",    # 暮色暗紫边框
            "text": "#6b21a8",      # 深暮紫字
            "box_border": "#9333ea",
            "box_bg": QColor(147, 51, 234, 35)
        }

    # 8. 默认通用组件 (浅霜白灰微暗)
    else:
        return {
            "bg": "#f8fafc",        # 浅霜灰微暗底
            "border": "#94a3b8",    # 冷灰边框
            "text": "#1e293b",      # 深灰黑字
            "box_border": "#0284c7",
            "box_bg": QColor(2, 132, 199, 30)
        }


# ==============================================================================
# 三端底层通信与驱动控制中枢 (HarmonyOS / Android / iOS)
# ==============================================================================

def run_hdc(cmd: List[str], udid: str = "", timeout: float = 8.0) -> str:
    """执行 HDC 指令 (鸿蒙 NEXT，优先使用内置绿色工具链)"""
    hdc_bin = "hdc"
    try:
        from desktop_app.core.path_resolver import SmartPathResolver
        tc = SmartPathResolver.discover_mobile_toolchain()
        if tc.get("hdc"):
            hdc_bin = tc["hdc"]
    except Exception:
        pass

    full_cmd = [hdc_bin]
    if udid:
        full_cmd.extend(["-t", udid])
    full_cmd.extend(cmd)
    try:
        kwargs: Dict[str, Any] = {"capture_output": True, "text": True, "errors": "ignore", "timeout": timeout}
        if sys.platform == "win32":
            kwargs["creationflags"] = 0x08000000
        res = subprocess.run(full_cmd, **kwargs)
        return res.stdout.strip()
    except Exception:
        return ""


def run_adb(cmd: List[str], udid: str = "", timeout: float = 8.0) -> str:
    """执行 ADB 指令 (安卓 Android，优先使用内置绿色工具链)"""
    adb_bin = "adb"
    try:
        from desktop_app.core.path_resolver import SmartPathResolver
        tc = SmartPathResolver.discover_mobile_toolchain()
        if tc.get("adb"):
            adb_bin = tc["adb"]
    except Exception:
        pass

    full_cmd = [adb_bin]
    if udid:
        full_cmd.extend(["-s", udid])
    full_cmd.extend(cmd)
    try:
        kwargs: Dict[str, Any] = {"capture_output": True, "text": True, "errors": "ignore", "timeout": timeout}
        if sys.platform == "win32":
            kwargs["creationflags"] = 0x08000000
        res = subprocess.run(full_cmd, **kwargs)
        return res.stdout.strip()
    except Exception:
        return ""


class IosWdaManager:
    """
    iOS WebDriverAgent (WDA) 智能服务与端口通信管理器 (方案一核心)
    支持：
    1. 动态自动探测 8100 / 8200 等活跃 WDA 服务端口；
    2. 自动通过 tidevice applist 扫描识别手机安装的 WDA bundleId；
    3. 自动通过 tidevice wdaproxy 一键拉起手机端 WDA 并绑定本地 8100 端口，彻底解决手动点击闪退问题；
    4. 提供清晰精确的诊断信息与原生高速抓取通道。
    """
    _relay_proc: Optional[subprocess.Popen] = None
    _active_wda_url: str = "http://127.0.0.1:8100"

    @classmethod
    def test_wda_status(cls, url: str, timeout: float = 1.2) -> bool:
        """测试指定 URL 的 WDA 是否处于正常响应状态"""
        import urllib.request
        try:
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
    def find_wda_bundle_id(cls, udid: str = "") -> Optional[str]:
        """自动扫描 iPhone 当前已安装的 WebDriverAgent 包名"""
        tidevice_bin = shutil.which("tidevice") or "tidevice"
        try:
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            cmd = [tidevice_bin]
            if udid and not udid.startswith("wda_localhost"):
                cmd.extend(["-u", udid])
            cmd.append("applist")
            res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", timeout=4, creationflags=creationflags)
            for line in res.stdout.splitlines():
                line = line.strip()
                low = line.lower()
                if "webdriveragent" in low or "xctrunner" in low:
                    parts = line.split()
                    if parts:
                        return parts[0].strip()
        except Exception:
            pass
        return None

    @classmethod
    def get_wda_url(cls, udid: str = "") -> Tuple[Optional[str], str]:
        """
        获取当前可用的 WDA 服务地址
        返回值: (有效_wda_url, 诊断状态描述)
        """
        # 1. 优先探测当前已知或常用的本地 WDA 端口 (8100, 8200)
        for port in (8100, 8200):
            test_url = f"http://127.0.0.1:{port}"
            if cls.test_wda_status(test_url, timeout=1.0):
                cls._active_wda_url = test_url
                return test_url, f"WDA 服务已连通 ({test_url})"

        # 2. 若端口未连通，尝试为当前 USB 设备拉起 WDA 守护进程 (tidevice wdaproxy / relay)
        if udid and udid not in ("wda_localhost", "wda_localhost_8100", "wda_localhost_8200"):
            tidevice_bin = shutil.which("tidevice") or "tidevice"
            try:
                creationflags = 0x08000000 if sys.platform == "win32" else 0
                if cls._relay_proc is None or cls._relay_proc.poll() is not None:
                    bundle_id = cls.find_wda_bundle_id(udid)
                    if bundle_id:
                        # 核心修复：通过 wdaproxy 直接拉起 XCTest 守护进程并中继端口，规避手机桌面点击闪退
                        proxy_cmd = [tidevice_bin, "-u", udid, "wdaproxy", "-B", bundle_id, "--port", "8100"]
                        cls._relay_proc = subprocess.Popen(
                            proxy_cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=creationflags
                        )
                        time.sleep(2.0)
                    else:
                        relay_cmd = [tidevice_bin, "-u", udid, "relay", "8100", "8100"]
                        cls._relay_proc = subprocess.Popen(
                            relay_cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=creationflags
                        )
                        time.sleep(0.8)

                if cls.test_wda_status("http://127.0.0.1:8100", timeout=2.0):
                    cls._active_wda_url = "http://127.0.0.1:8100"
                    return "http://127.0.0.1:8100", "已自动通过 tidevice wdaproxy 唤醒 WDA 并建立 8100 端口映射"
            except Exception:
                pass

        return None, "未检测到手机运行 WebDriverAgent 服务 (8100/8200 端口未通)"


def run_ios_action(action: str, udid: str = "", **kwargs) -> bool:
    """执行 iOS 动作 (优先通过 WebDriverAgent 8100/8200 端口，兜底支持 tidevice)"""
    import urllib.request
    wda_url, _ = IosWdaManager.get_wda_url(udid)
    if not wda_url:
        wda_url = "http://127.0.0.1:8100"
    try:
        if action == "tap":
            x, y = kwargs.get("x", 0), kwargs.get("y", 0)
            data = json.dumps({"x": x, "y": y}).encode("utf-8")
            req = urllib.request.Request(f"{wda_url}/wda/tap/0", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        elif action == "swipe":
            x1, y1 = kwargs.get("x1", 0), kwargs.get("y1", 0)
            x2, y2 = kwargs.get("x2", 0), kwargs.get("y2", 0)
            dur = kwargs.get("duration", 0.3)
            data = json.dumps({"fromX": x1, "fromY": y1, "toX": x2, "toY": y2, "duration": dur}).encode("utf-8")
            req = urllib.request.Request(f"{wda_url}/wda/dragfromtoforduration", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        elif action == "home":
            req = urllib.request.Request(f"{wda_url}/wda/homescreen", data=b"{}", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        elif action == "keys":
            text = kwargs.get("text", "")
            data = json.dumps({"value": list(text)}).encode("utf-8")
            req = urllib.request.Request(f"{wda_url}/wda/keys", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        elif action == "clear":
            # iOS clear: 尝试向当前聚焦元素清空
            req = urllib.request.Request(f"{wda_url}/wda/element/active", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    el_id = json.loads(resp.read().decode("utf-8")).get("value", {}).get("ELEMENT")
                    if el_id:
                        del_req = urllib.request.Request(f"{wda_url}/element/{el_id}/clear", data=b"{}", headers={"Content-Type": "application/json"})
                        urllib.request.urlopen(del_req, timeout=2)
                        return True
    except Exception:
        pass

    # 兜底调用 tidevice
    try:
        tidevice_bin = shutil.which("tidevice") or "tidevice"
        if action == "tap":
            x, y = kwargs.get("x", 0), kwargs.get("y", 0)
            subprocess.run([tidevice_bin, "click", str(x), str(y)], timeout=5, creationflags=0x08000000 if sys.platform == "win32" else 0)
            return True
    except Exception:
        pass
    return False


class DeviceController:
    """跨平台设备统一动作控制中枢"""

    @staticmethod
    def tap(platform: str, udid: str, x: int, y: int):
        if platform == "harmony":
            run_hdc(["shell", "uitest", "uiInput", "click", str(x), str(y)], udid)
        elif platform == "android":
            run_adb(["shell", "input", "tap", str(x), str(y)], udid)
        elif platform == "ios":
            run_ios_action("tap", udid, x=x, y=y)

    @staticmethod
    def swipe(platform: str, udid: str, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        if platform == "harmony":
            run_hdc(["shell", "uitest", "uiInput", "swipe", str(x1), str(y1), str(x2), str(y2), "1500"], udid)
        elif platform == "android":
            run_adb(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)], udid)
        elif platform == "ios":
            run_ios_action("swipe", udid, x1=x1, y1=y1, x2=x2, y2=y2, duration=duration_ms / 1000.0)

    @staticmethod
    def key_back(platform: str, udid: str):
        if platform == "harmony":
            run_hdc(["shell", "uitest", "uiInput", "keyEvent", "Back"], udid)
        elif platform == "android":
            run_adb(["shell", "input", "keyevent", "4"], udid)
        elif platform == "ios":
            run_ios_action("swipe", udid, x1=10, y1=400, x2=320, y2=400, duration=0.3)

    @staticmethod
    def key_home(platform: str, udid: str):
        if platform == "harmony":
            run_hdc(["shell", "uitest", "uiInput", "keyEvent", "Home"], udid)
        elif platform == "android":
            run_adb(["shell", "input", "keyevent", "3"], udid)
        elif platform == "ios":
            run_ios_action("home", udid)

    @staticmethod
    def input_text(platform: str, udid: str, text: str, cx: int = 0, cy: int = 0):
        if platform == "harmony":
            safe_text = text.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
            if cx and cy:
                cmd_str = f"uitest uiInput click {cx} {cy} && uitest uiInput inputText {cx} {cy} \"{safe_text}\""
            else:
                cmd_str = f"uitest uiInput inputText {cx} {cy} \"{safe_text}\""
            run_hdc(["shell", cmd_str], udid)
        elif platform == "android":
            if cx and cy:
                run_adb(["shell", "input", "tap", str(cx), str(cy)], udid)
            escaped_text = text.replace(" ", "%s").replace("&", r"\&").replace("<", r"\<").replace(">", r"\>")
            run_adb(["shell", "input", "text", escaped_text], udid)
        elif platform == "ios":
            if cx and cy:
                run_ios_action("tap", udid, x=cx, y=cy)
            run_ios_action("keys", udid, text=text)

    @staticmethod
    def clear_text(platform: str, udid: str, cx: int = 0, cy: int = 0):
        if platform == "harmony":
            cmd_clear = f"uitest uiInput click {cx} {cy} && for i in $(seq 1 35); do uitest uiInput keyEvent 2055; done" if (cx and cy) else "for i in $(seq 1 35); do uitest uiInput keyEvent 2055; done"
            run_hdc(["shell", cmd_clear], udid)
        elif platform == "android":
            if cx and cy:
                run_adb(["shell", "input", "tap", str(cx), str(cy)], udid)
            del_keys = ["67"] * 35
            run_adb(["shell", "input", "keyevent"] + del_keys, udid)
        elif platform == "ios":
            if cx and cy:
                run_ios_action("tap", udid, x=cx, y=cy)
            run_ios_action("clear", udid)


# ==============================================================================
# 设备发现服务 (全自动扫描 HarmonyOS / Android / iOS)
# ==============================================================================

def get_connected_devices() -> List[Dict[str, Any]]:
    """全自动极速发现三端当前真实在线连接的设备列表 (HarmonyOS / Android / iOS)，严格优化超时并做命令可用性前置校验"""
    devices: List[Dict[str, Any]] = []
    seen_udids = set()
    creationflags = 0x08000000 if sys.platform == "win32" else 0

    # 1. 探测鸿蒙设备 (仅在系统存在 hdc 时执行，超时控制在 1.5 秒)
    if shutil.which("hdc") or os.environ.get("HDC_HOME"):
        try:
            out = subprocess.check_output(["hdc", "list", "targets"], text=True, errors="ignore", timeout=1.5, creationflags=creationflags).strip()
            for line in out.splitlines():
                line = line.strip()
                if line and "empty" not in line.lower() and "[Empty]" not in line and line not in seen_udids:
                    seen_udids.add(line)
                    model = run_hdc(["shell", "param get const.product.model"], line, timeout=1.0)
                    name_str = f"鸿蒙真机 ({model}): {line}" if model else f"鸿蒙真机: {line}"
                    devices.append({
                        "udid": line,
                        "platform": "harmony",
                        "name": name_str,
                        "is_real": True
                    })
            # 容灾探测：若 list targets 返回空，但存在 USB 物理连接 (如熄屏休眠脱机 Offline)
            if not devices:
                out_v = subprocess.check_output(["hdc", "list", "targets", "-v"], text=True, errors="ignore", timeout=1.5, creationflags=creationflags).strip()
                for line in out_v.splitlines():
                    parts = line.strip().split()
                    if parts and len(parts[0]) >= 10 and parts[0] not in seen_udids:
                        dev_id = parts[0]
                        seen_udids.add(dev_id)
                        status_desc = "脱机休眠" if "offline" in line.lower() else "未就绪"
                        devices.append({
                            "udid": dev_id,
                            "platform": "harmony",
                            "name": f"鸿蒙设备 ({status_desc}): {dev_id}",
                            "is_real": True
                        })
        except Exception:
            pass

    # 2. 探测安卓设备 (仅在系统存在 adb 时执行，超时控制在 1.5 秒)
    if shutil.which("adb") or os.environ.get("ANDROID_HOME"):
        try:
            out = subprocess.check_output(["adb", "devices"], text=True, errors="ignore", timeout=1.5, creationflags=creationflags).strip()
            for line in out.splitlines():
                line_str = line.strip()
                if re.search(r"\s+device$", line_str):
                    udid = line_str.split()[0].strip()
                    if udid and udid not in seen_udids:
                        seen_udids.add(udid)
                        is_real = not (udid.startswith("emulator-") or "127.0.0.1" in udid or "localhost" in udid)
                        model = run_adb(["shell", "getprop", "ro.product.model"], udid, timeout=1.0)
                        desc = (f"安卓真机 ({model}): {udid}" if is_real else f"安卓模拟器 ({model}): {udid}") if model else (f"安卓真机: {udid}" if is_real else f"安卓模拟器: {udid}")
                        devices.append({
                            "udid": udid,
                            "platform": "android",
                            "name": desc,
                            "is_real": is_real
                        })
        except Exception:
            pass

    # 3. 探测 iOS 设备 (仅在系统明确安装了 tidevice 时才探测，避免命令不存在导致的盲等)
    if shutil.which("tidevice"):
        try:
            out = subprocess.check_output(["tidevice", "list"], text=True, errors="ignore", timeout=1.5, creationflags=creationflags).strip()
            for line in out.splitlines():
                parts = line.strip().split()
                if parts:
                    udid = parts[0]
                    if udid and udid not in seen_udids and len(udid) >= 20:
                        seen_udids.add(udid)
                        model = parts[1] if len(parts) > 1 else "iPhone"
                        devices.append({
                            "udid": udid,
                            "platform": "ios",
                            "name": f"苹果真机 ({model}): {udid[:12]}...",
                            "is_real": True
                        })
        except Exception:
            pass

    # 4. 本地 WDA 极速 socket 端口探活 (每次探活仅 40ms 超时，绝不使用重型 urllib 阻塞)
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
                            "is_real": True
                        })
        except Exception:
            pass

    return devices


class DeviceScanWorker(QThread):
    """后台异步设备探测线程，确保 UI 主线程切换页面 0 秒响应、绝无假死"""
    devices_ready = pyqtSignal(list)

    def run(self):
        try:
            devs = get_connected_devices()
            self.devices_ready.emit(devs)
        except Exception:
            self.devices_ready.emit([])


# ==============================================================================
# 三端布局结构统一解析器 (Android XML / iOS XML-JSON / HarmonyOS JSON)
# ==============================================================================

def parse_android_node(elem: ET.Element) -> Dict[str, Any]:
    """将 Android uiautomator dump XML 节点转换为通用 DOM 结构"""
    attrs = elem.attrib.copy()
    raw_class = attrs.get("class", "android.view.View")
    short_type = raw_class.split(".")[-1]
    res_id = attrs.get("resource-id", "")
    text = attrs.get("text", "") or attrs.get("content-desc", "")
    bounds = attrs.get("bounds", "[0,0][0,0]")

    return {
        "attributes": {
            "type": short_type,
            "id": res_id,
            "text": text,
            "bounds": bounds,
            "class": raw_class,
            "resource-id": res_id,
            "package": attrs.get("package", ""),
            "content-desc": attrs.get("content-desc", ""),
            "clickable": attrs.get("clickable", "false"),
            "enabled": attrs.get("enabled", "true"),
            "focusable": attrs.get("focusable", "false"),
            "scrollable": attrs.get("scrollable", "false"),
        },
        "children": [parse_android_node(child) for child in elem if child.tag == "node"]
    }


def parse_ios_node(elem: ET.Element) -> Dict[str, Any]:
    """将 iOS WDA XML 节点转换为通用 DOM 结构"""
    attrs = elem.attrib.copy()
    tag = elem.tag
    short_type = tag.replace("XCUIElementType", "") if tag.startswith("XCUIElementType") else tag
    c_id = attrs.get("name", "")
    c_text = attrs.get("label", "") or attrs.get("value", "")
    try:
        x = int(float(attrs.get("x", 0)))
        y = int(float(attrs.get("y", 0)))
        w = int(float(attrs.get("width", 0)))
        h = int(float(attrs.get("height", 0)))
        bounds = f"[{x},{y}][{x + w},{y + h}]"
    except Exception:
        bounds = attrs.get("bounds", "[0,0][0,0]")

    return {
        "attributes": {
            "type": short_type,
            "id": c_id,
            "text": c_text,
            "bounds": bounds,
            "name": c_id,
            "label": attrs.get("label", ""),
            "value": attrs.get("value", ""),
            "enabled": attrs.get("enabled", "true"),
            "visible": attrs.get("visible", "true"),
        },
        "children": [parse_ios_node(child) for child in elem]
    }


def parse_ios_json_node(data: Dict[str, Any]) -> Dict[str, Any]:
    """将 iOS WDA JSON 节点转换为通用 DOM 结构"""
    raw_type = data.get("type", "Element")
    short_type = raw_type.replace("XCUIElementType", "") if raw_type.startswith("XCUIElementType") else raw_type
    c_id = data.get("name") or data.get("id") or ""
    c_text = data.get("label") or data.get("value") or ""
    rect = data.get("rect", {})
    x = int(rect.get("x", 0))
    y = int(rect.get("y", 0))
    w = int(rect.get("width", 0))
    h = int(rect.get("height", 0))
    bounds = f"[{x},{y}][{x + w},{y + h}]"

    return {
        "attributes": {
            "type": short_type,
            "id": c_id,
            "text": c_text,
            "bounds": bounds,
            "name": c_id,
            "label": str(data.get("label", "")),
            "value": str(data.get("value", "")),
            "enabled": str(data.get("enabled", "true")),
            "visible": str(data.get("visible", "true")),
        },
        "children": [parse_ios_json_node(child) for child in data.get("children", [])]
    }


# ==============================================================================
# 鸿蒙高速 UITest RPC 通信客户端 (对标 HoKit UIViewer 核心引擎)
# ==============================================================================

class HarmonyRpcLayoutClient:
    """
    鸿蒙原生 uitest 守护进程 RPC 通信客户端
    对标 HoKit UIViewer 底层实现：
    1. 启动/复用 uitest start-daemon singleness 守护进程；
    2. 基于 HDC 抽象命名套接字 localabstract:uitest_socket 建立 TCP 端口转发；
    3. 通过 _uitestkit_rpc_message_head_ 二进制包头进行高速 RPC 调用；
    4. 内存级直接拉取 captureLayout 结果，彻底消除磁盘落盘 I/O 延迟。
    """
    RPC_HEAD = b"_uitestkit_rpc_message_head_"
    RPC_TAIL = b"_uitestkit_rpc_message_tail_"

    @classmethod
    def _find_available_port(cls) -> int:
        """获取本地空闲可用端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    @classmethod
    def _ensure_daemon_running(cls, udid: str = "") -> bool:
        """检查并确保鸿蒙设备端 uitest 守护进程处于活跃状态"""
        ps_res = run_hdc(["shell", "pgrep -f uitest"], udid)
        if ps_res and any(line.strip().isdigit() for line in ps_res.splitlines()):
            return True
        run_hdc(["shell", "uitest start-daemon singleness"], udid)
        time.sleep(0.25)
        return True

    @classmethod
    def _build_request_packet(cls, payload: Dict[str, Any]) -> bytes:
        """构建遵循 _uitestkit_rpc_message_head_ 规范的二进制请求帧"""
        json_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        session_id = random.randint(1, 0x7FFFFFFF)
        header = cls.RPC_HEAD + struct.pack(">II", session_id, len(json_bytes))
        return header + json_bytes + cls.RPC_TAIL

    @classmethod
    def capture_layout_fast(cls, udid: str = "", timeout: float = 3.5) -> Optional[Any]:
        """
        通过 RPC 内存高速抓取当前活动页面的 UI 结构
        若失败返回 None，以便上层自动无感降级到经典 CLI 模式
        """
        local_port = 0
        sock = None
        try:
            cls._ensure_daemon_running(udid)
            local_port = cls._find_available_port()

            # 建立端口转发到抽象套接字
            fport_ret = run_hdc(["fport", f"tcp:{local_port}", "localabstract:uitest_socket"], udid)
            if "fail" in fport_ret.lower() or "error" in fport_ret.lower():
                return None

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(("127.0.0.1", local_port))

            # 构建 captureLayout 请求
            rpc_payload = {
                "module": "com.ohos.devicetest.hypiumApiHelper",
                "method": "Captures",
                "params": {
                    "api": "captureLayout",
                    "args": {}
                }
            }
            req_data = cls._build_request_packet(rpc_payload)
            sock.sendall(req_data)

            # 接收响应帧
            raw_buf = bytearray()
            head_len = len(cls.RPC_HEAD)
            tail_len = len(cls.RPC_TAIL)

            start_t = time.time()
            expected_body_len = -1
            while time.time() - start_t < timeout:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                raw_buf.extend(chunk)

                if expected_body_len == -1 and len(raw_buf) >= head_len + 8:
                    if raw_buf.startswith(cls.RPC_HEAD):
                        _, expected_body_len = struct.unpack(">II", raw_buf[head_len:head_len + 8])
                    else:
                        h_idx = raw_buf.find(cls.RPC_HEAD)
                        if h_idx != -1:
                            del raw_buf[:h_idx]
                            if len(raw_buf) >= head_len + 8:
                                _, expected_body_len = struct.unpack(">II", raw_buf[head_len:head_len + 8])

                if expected_body_len != -1 and len(raw_buf) >= head_len + 8 + expected_body_len + tail_len:
                    body_start = head_len + 8
                    body_bytes = raw_buf[body_start:body_start + expected_body_len]
                    resp_json = json.loads(body_bytes.decode("utf-8", errors="ignore"))
                    result = resp_json.get("result", resp_json.get("data", resp_json))
                    return result

            return None
        except Exception:
            return None
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
            if local_port > 0:
                try:
                    run_hdc(["fport", "rm", f"tcp:{local_port}", "localabstract:uitest_socket"], udid)
                except Exception:
                    pass


def normalize_harmony_node(node: Dict[str, Any], path_id: str = "root") -> Dict[str, Any]:
    """对标 HoKit convertToUIViewNode：规范化清洗鸿蒙节点，抹平 bounds 与唯一标识"""
    if not isinstance(node, dict):
        return {"attributes": {"type": "Unknown", "bounds": "[0,0][0,0]"}, "children": []}

    attrs = dict(node.get("attributes", {}))
    # 展开可能混在根层级的属性
    for k in ("type", "id", "key", "text", "originalText", "visible", "clickable", "enabled", "bounds", "rect"):
        if k in node and k not in attrs:
            attrs[k] = node[k]

    c_type = str(attrs.get("type") or node.get("type") or "Component")
    real_id = str(attrs.get("id") or attrs.get("key") or node.get("id") or "")
    if real_id and not real_id.startswith("win-"):
        attrs["id"] = real_id
        c_id = real_id
    else:
        attrs["id"] = ""
        attrs["dom_path"] = path_id
        c_id = ""

    # 规范化 bounds 表达为 [x1,y1][x2,y2]
    raw_b = attrs.get("bounds") or attrs.get("rect") or node.get("bounds") or node.get("rect")
    norm_bounds = "[0,0][0,0]"
    if isinstance(raw_b, str) and "[" in raw_b:
        norm_bounds = raw_b
    elif isinstance(raw_b, dict):
        if "left" in raw_b and "top" in raw_b:
            l, t = int(raw_b.get("left", 0)), int(raw_b.get("top", 0))
            r, b = int(raw_b.get("right", l)), int(raw_b.get("bottom", t))
            norm_bounds = f"[{l},{t}][{r},{b}]"
        elif "x" in raw_b and "y" in raw_b:
            x, y = int(raw_b.get("x", 0)), int(raw_b.get("y", 0))
            w, h = int(raw_b.get("width", 0)), int(raw_b.get("height", 0))
            norm_bounds = f"[{x},{y}][{x + w},{y + h}]"
    attrs["bounds"] = norm_bounds
    attrs["type"] = c_type

    raw_children = node.get("children", [])
    clean_children = []
    if isinstance(raw_children, list):
        for idx, ch in enumerate(raw_children):
            clean_children.append(normalize_harmony_node(ch, f"{path_id}-{idx}"))

    return {
        "attributes": attrs,
        "children": clean_children
    }


def get_layout_physical_size(layout_data: Any, default_w: int = 1084, default_h: int = 2412) -> Tuple[int, int]:
    """
    从布局数据或文件自适应提取真实物理分辨率 (根治投屏降采样帧毒化):
    鸿蒙 dumpLayout 的根节点或多窗口 attributes 始终明确包含物理绝对分辨率 (如 [0,0][1084,2412])
    """
    try:
        data = None
        if isinstance(layout_data, str) and os.path.exists(layout_data):
            with open(layout_data, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif isinstance(layout_data, (dict, list)):
            data = layout_data

        if data:
            nodes = data if isinstance(data, list) else [data]
            for n in nodes:
                if isinstance(n, dict):
                    attrs = n.get("attributes", {})
                    b_str = attrs.get("origBounds") or attrs.get("bounds") or n.get("bounds") or ""
                    m = re.match(r"\[0,0\]\[(\d+),(\d+)\]", str(b_str))
                    if m:
                        w, h = int(m.group(1)), int(m.group(2))
                        if w >= 600 and h >= 1000:
                            return w, h
    except Exception:
        pass
    return default_w, default_h


def parse_layout_file(layout_path: str, platform: str, screen_w: int = 0, screen_h: int = 0) -> Dict[str, Any]:
    """统一解析三端布局文件为通用的 DOM 节点树格式 (支持动态自适应物理分辨率与多窗口聚合，具备工业级容错兜底)"""
    if platform == "harmony":
        phys_w, phys_h = get_layout_physical_size(layout_path, 1084, 2412)
        if screen_w < 800 or screen_h < 1200:
            screen_w, screen_h = phys_w, phys_h

    root_w = screen_w if screen_w > 0 else 1080
    root_h = screen_h if screen_h > 0 else 2400
    root_bounds = f"[0,0][{root_w},{root_h}]"

    if platform == "harmony":
        if isinstance(layout_path, (dict, list)):
            raw = layout_path
        else:
            if not layout_path or not os.path.exists(layout_path):
                return {"attributes": {"type": "Hierarchy", "bounds": root_bounds}, "children": []}
            try:
                with open(layout_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
            except Exception:
                return {"attributes": {"type": "Hierarchy", "bounds": root_bounds}, "children": []}

        if isinstance(raw, list):
            # 对标 HoKit UIViewer：聚合多窗口并统一清洗规范化
            cleaned_windows = [normalize_harmony_node(w, f"win-{i}") for i, w in enumerate(raw)]
            return {
                "attributes": {
                    "type": "Hierarchy",
                    "bounds": root_bounds,
                    "origBounds": root_bounds
                },
                "children": cleaned_windows
            }
        elif isinstance(raw, dict):
            return normalize_harmony_node(raw, "root")
        return {"attributes": {"type": "Hierarchy", "bounds": root_bounds}, "children": []}
    elif platform == "android":
        if not layout_path or not os.path.exists(layout_path):
            return {"attributes": {"type": "hierarchy", "bounds": root_bounds}, "children": []}
        try:
            tree = ET.parse(layout_path)
            root = tree.getroot()
            first_child = root.find("node")
            if first_child is not None:
                return parse_android_node(first_child)
        except Exception:
            pass
        return {"attributes": {"type": "hierarchy", "bounds": root_bounds}, "children": []}
    elif platform == "ios":
        try:
            with open(layout_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content.startswith("<"):
                root = ET.fromstring(content)
                app_node = root.find(".//XCUIElementTypeApplication")
                if app_node is not None:
                    return parse_ios_node(app_node)
                return parse_ios_node(root)
            else:
                raw_json = json.loads(content)
                val = raw_json.get("value", raw_json)
                return parse_ios_json_node(val)
        except Exception:
            return {"attributes": {"type": "Screen", "bounds": "[0,0][1170,2532]"}, "children": []}
    return {}


# ==============================================================================
# 跨平台异步后台投屏与抓取引擎 (支持 HarmonyOS / Android / iOS)
# ==============================================================================

class ScreenCastWorker(QThread):
    """
    真机实时投屏流引擎 (HarmonyOS / Android / iOS):
    1. 鸿蒙 NEXT: 采用 uitest 原生 startCaptureScreen 捕获流协议，零系统截屏广播，绝不触发前台 IM 截屏通知；
    2. 内存直通: 直接在内存中解析 JPEG 帧并转为 QPixmap，0 磁盘 I/O 损耗，实现 20~30fps 级丝滑投屏；
    3. 自愈容灾: 内置自动环境自检、动态补齐 agent.so 与断线自愈重连，换手机即插即用，确保投屏稳定不掉线。
    """
    frame_ready = pyqtSignal(QImage, bytes)   # image, raw_jpeg_bytes
    state_changed = pyqtSignal(bool, str)     # is_running, status_message
    error_occurred = pyqtSignal(str)

    # 类级别全内存投屏帧缓存 (绑定具体设备 UDID，供 UI 审查器与同步真机画面 0ms 零外部调用秒级复用)
    latest_image: Optional[QImage] = None
    latest_pixmap: Optional[QPixmap] = None
    latest_frame_bytes: Optional[bytes] = None
    latest_frame_time: float = 0.0
    latest_udid: str = ""
    is_active: bool = False

    @classmethod
    def clear_cache(cls):
        """清空全量内存投屏帧缓存 (设备切换时强制调用，彻底杜绝跨设备脏画面污染)"""
        cls.latest_image = None
        cls.latest_pixmap = None
        cls.latest_frame_bytes = None
        cls.latest_frame_time = 0.0
        cls.latest_udid = ""
        cls.is_active = False

    def __init__(self, udid: str, platform: str):
        super().__init__()
        self.udid = udid
        self.platform = platform
        self._is_running = False
        self._sock: Optional[socket.socket] = None
        self._grpc_channel: Any = None
        self._local_port = 0
        self._android_proc: Optional[subprocess.Popen] = None
        self._android_scid: str = ""
        self._android_server_sock: Optional[socket.socket] = None
        self._android_conn: Optional[socket.socket] = None

    @staticmethod
    def _extract_nalu(resp_bytes: bytes) -> bytes:
        """从鸿蒙 scrcpy ReplyMessage Protobuf 字节中毫秒级提取真实 H.264 NALU 数据包"""
        pattern = b"\n\x04data\x12"
        idx = resp_bytes.find(pattern)
        if idx == -1:
            h264_idx = resp_bytes.find(b"\x00\x00\x00\x01")
            if h264_idx != -1:
                return resp_bytes[h264_idx:]
            return b""
        val_start = idx + len(pattern)
        pv_len = 0
        shift = 0
        p = val_start
        while p < len(resp_bytes):
            b = resp_bytes[p]
            p += 1
            pv_len |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        pv_end = p + pv_len
        pv_data = resp_bytes[p:pv_end]
        if pv_data.startswith(b"\x2a"):
            vb_len = 0
            shift = 0
            vp = 1
            while vp < len(pv_data):
                b = pv_data[vp]
                vp += 1
                vb_len |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7
            return pv_data[vp : vp + vb_len]
        return b""

    @classmethod
    def get_latest_jpeg_bytes(cls, target_udid: str = "") -> Optional[bytes]:
        """按需从内存最新 QImage 压缩为 JPEG 字节流 (仅在外部请求保存截图或 Dump 树时按需触发，推流主循环 0 编码开销)"""
        # 严格校验：若指定目标 UDID 且与缓存不符，坚决返回 None 杜绝脏画面
        if target_udid and cls.latest_udid and cls.latest_udid != target_udid:
            return None
        if cls.latest_frame_bytes and (time.time() - cls.latest_frame_time < 3.0):
            return cls.latest_frame_bytes
        if cls.latest_image and not cls.latest_image.isNull() and (time.time() - cls.latest_frame_time < 3.0):
            try:
                buf = QByteArray()
                buffer_io = QBuffer(buf)
                buffer_io.open(QBuffer.OpenModeFlag.WriteOnly)
                cls.latest_image.save(buffer_io, "JPEG", 85)
                cls.latest_frame_bytes = bytes(buf)
                return cls.latest_frame_bytes
            except Exception:
                pass
        return None

    @classmethod
    def _clean_all_scrcpy_fports(cls, udid: str = ""):
        """彻底清理鸿蒙真机上所有指向 scrcpy_grpc_socket 的历史残留 fport 端口映射"""
        if not udid:
            return
        try:
            fport_list = run_hdc(["fport", "ls"], udid, timeout=2.0)
            if fport_list:
                for line in fport_list.splitlines():
                    if "scrcpy_grpc_socket" in line and "tcp:" in line:
                        parts = line.split()
                        for p in parts:
                            if p.startswith("tcp:"):
                                run_hdc(["fport", "rm", p, "localabstract:scrcpy_grpc_socket"], udid, timeout=1.0)
                                break
        except Exception:
            pass

    @classmethod
    def _kill_existing_scrcpy_daemons(cls, udid: str = ""):
        """1:1 对齐 HoKit 进程治理：通过精确解析 ps -ef 获取 PID 并执行 kill -9，彻底杜绝僵尸进程占用 unix socket"""
        try:
            ps_res = run_hdc(["shell", "ps -ef | grep -E 'uitest|xdevice_scrcpy'"], udid, timeout=1.5)
            if ps_res:
                pids_to_kill = []
                for line in ps_res.splitlines():
                    if "grep" in line:
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        pids_to_kill.append(parts[1])
                if pids_to_kill:
                    run_hdc(["shell", f"kill -9 {' '.join(pids_to_kill)}"], udid, timeout=1.5)
                    time.sleep(0.2)
        except Exception:
            pass

    @classmethod
    def _ensure_harmony_env(cls, udid: str = ""):
        """确保鸿蒙真机已具备 agent.so 与 scrcpy_server.so 扩展守护环境 (100% 自包含资产，绝无硬编码路径)"""
        if not udid:
            return
        # 1. 确保 agent.so 就绪 (供控件树与事件注入)
        try:
            chk = run_hdc(["shell", "[ -f /data/local/tmp/agent.so ] && echo 'yes' || echo 'no'"], udid, timeout=1.5)
            if "yes" not in chk:
                builtin_agent = SmartPathResolver.get_asset_path("desktop_app/assets/harmony/agent.so") or ""
                local_so = builtin_agent if os.path.isfile(builtin_agent) else ""
                if not local_so:
                    import hmnextauto
                    assets_dir = os.path.join(os.path.dirname(hmnextauto.__file__), "assets")
                    if os.path.isdir(assets_dir):
                        so_files = [f for f in os.listdir(assets_dir) if f.endswith(".so")]
                        if so_files:
                            local_so = os.path.join(assets_dir, sorted(so_files)[-1])
                if local_so and os.path.isfile(local_so):
                    run_hdc(["file", "send", local_so, "/data/local/tmp/agent.so"], udid, timeout=3.0)
                    run_hdc(["shell", "chmod 777 /data/local/tmp/agent.so"], udid, timeout=1.5)
        except Exception:
            pass

        # 2. 确保 scrcpy_server.so 扩展就绪 (优先使用项目自包含内置 assets，支持直接移植即插即用)
        try:
            chk_sc = run_hdc(["shell", "[ -f /data/local/tmp/scrcpy_server.so ] && echo 'yes' || echo 'no'"], udid, timeout=1.5)
            if "yes" not in chk_sc:
                # 优先级 1: 项目内置自包含资产 (绝对免配置、零外部依赖、直接移植可运行)
                builtin_so = SmartPathResolver.get_asset_path("desktop_app/assets/harmony/scrcpy_server.so") or ""
                candidate_so = builtin_so if os.path.isfile(builtin_so) else ""

                # 优先级 2: 动态推导系统临时缓存目录 (基于系统环境变量，杜绝硬编码用户名)
                if not candidate_so:
                    temp_dirs = [
                        os.path.join(tempfile.gettempdir(), "hokit-so"),
                        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp", "hokit-so"),
                    ]
                    for td in temp_dirs:
                        if os.path.isdir(td):
                            # 优先匹配 1.3 版本 (当前固件 100% 验证兼容)
                            for fn in sorted(os.listdir(td)):
                                if fn.endswith(".so") and "screencopy" in fn and "1.3" in fn:
                                    candidate_so = os.path.join(td, fn)
                                    break
                            if not candidate_so:
                                for fn in sorted(os.listdir(td)):
                                    if fn.endswith(".so") and "screencopy" in fn:
                                        candidate_so = os.path.join(td, fn)
                                        break
                            if candidate_so:
                                break

                if candidate_so and os.path.isfile(candidate_so):
                    run_hdc(["shell", "rm -rf /data/local/tmp/scrcpy_server.so"], udid, timeout=1.0)
                    run_hdc(["file", "send", candidate_so, "/data/local/tmp/"], udid, timeout=3.0)
                    base_fn = os.path.basename(candidate_so)
                    if base_fn != "scrcpy_server.so":
                        run_hdc(["shell", f"mv -f /data/local/tmp/{base_fn} /data/local/tmp/scrcpy_server.so"], udid, timeout=1.0)
                    run_hdc(["shell", "chmod 777 /data/local/tmp/scrcpy_server.so"], udid, timeout=1.5)
        except Exception:
            pass

        # 3. 检查 uitest 守护进程是否活跃，且确认必须是带 HoKit 黄金投屏参数 (-scale 2, -frameRate 30, -bitRate 10485760)
        try:
            sock_ok = "scrcpy_grpc_socket" in run_hdc(["shell", "cat /proc/net/unix | grep scrcpy_grpc_socket"], udid, timeout=1.0)
            ps_res = run_hdc(["shell", "ps -ef | grep -E 'xdevice_scrcpy|uitest'"], udid, timeout=1.5)
            need_restart = True
            if sock_ok and ps_res:
                lines = [l for l in ps_res.splitlines() if "grep" not in l and ("uitest start-daemon" in l or "xdevice_scrcpy" in l)]
                # 严格校验进程参数：必须包含 scrcpy_server.so 且满足 50% 缩放 (-scale 2) 与 10MB/s 码率 (10485760)
                if lines and any("scrcpy_server.so" in l and "-scale 2" in l and "10485760" in l for l in lines):
                    need_restart = False
            if need_restart:
                cls._kill_existing_scrcpy_daemons(udid)
                time.sleep(0.3)
                # 1:1 对齐 HoKit 官方参数：进入 /data/local/tmp 目录并导出 LD_LIBRARY_PATH，
                # 使用后台脱壳语法 >/dev/null 2>&1 & 启动，绝不阻塞 HDC 避免连接超时导致守护进程被强杀
                cmd_start = (
                    "cd /data/local/tmp && export LD_LIBRARY_PATH=/data/local/tmp:$LD_LIBRARY_PATH && "
                    "(uitest start-daemon singleness --extension-name scrcpy_server.so "
                    "-scale 2 -frameRate 30 -bitRate 10485760 -p 9958 -screenId 0 "
                    "-encodeType 0 -iFrameInterval 2000 -repeatInterval 33 >/dev/null 2>&1 &)"
                )
                run_hdc(["shell", cmd_start], udid, timeout=3.0)
                time.sleep(0.5)
        except Exception:
            pass

    def stop(self):
        """请求优雅停止实时投屏流"""
        self._is_running = False
        ScreenCastWorker.is_active = False
        if getattr(self, "_grpc_channel", None):
            try:
                self._grpc_channel.close()
            except Exception:
                pass
            self._grpc_channel = None
        self._cleanup_android_stream()

    def _cleanup_android_stream(self):
        """安全释放安卓 scrcpy 连接通道、子进程与 reverse 端口映射"""
        if getattr(self, "_android_conn", None):
            try:
                self._android_conn.close()
            except Exception:
                pass
            self._android_conn = None
        if getattr(self, "_android_server_sock", None):
            try:
                self._android_server_sock.close()
            except Exception:
                pass
            self._android_server_sock = None
        if getattr(self, "_android_proc", None):
            try:
                self._android_proc.terminate()
            except Exception:
                pass
            self._android_proc = None
        if getattr(self, "_android_scid", "") and self.udid:
            try:
                adb_bin = "adb"
                try:
                    from desktop_app.core.path_resolver import SmartPathResolver
                    tc = SmartPathResolver.discover_mobile_toolchain()
                    if tc.get("adb"):
                        adb_bin = tc["adb"]
                except Exception:
                    pass
                creationflags = 0x08000000 if sys.platform == "win32" else 0
                subprocess.run(
                    [adb_bin, "-s", self.udid, "reverse", "--remove", f"localabstract:scrcpy_{self._android_scid}"],
                    capture_output=True,
                    timeout=1.5,
                    creationflags=creationflags
                )
            except Exception:
                pass
            self._android_scid = ""

    def _cleanup_harmony_port(self):
        """安全释放鸿蒙连接通道与端口转发"""
        if getattr(self, "_grpc_channel", None):
            try:
                self._grpc_channel.close()
            except Exception:
                pass
            self._grpc_channel = None
        if self._local_port > 0 and self.udid:
            try:
                run_hdc(["fport", "rm", f"tcp:{self._local_port}", "localabstract:scrcpy_grpc_socket"], self.udid, timeout=1.5)
            except Exception:
                pass
            self._local_port = 0

    @classmethod
    def capture_single_silent_frame(cls, udid: str = "", timeout: float = 4.5) -> Optional[bytes]:
        """
        通过 scrcpy_server.so 硬件录屏通道按需抓取单帧图像 (100% 绕过 DMS 截屏广播，绝对 0 截屏通知)
        """
        import grpc
        import av
        import threading

        # 1. 优先复用内存最新新鲜帧 (耗时 0ms)
        if cls.latest_frame_bytes and (time.time() - cls.latest_frame_time < 4.0):
            return cls.latest_frame_bytes

        # 确保守护环境就绪
        cls._ensure_harmony_env(udid)

        # 探测真机 unix socket 是否已注册，若未就绪轮询等待
        for _ in range(25):
            chk = run_hdc(["shell", "cat /proc/net/unix | grep scrcpy_grpc_socket"], udid, timeout=1.0)
            if "scrcpy_grpc_socket" in chk:
                break
            time.sleep(0.08)

        port = HarmonyRpcLayoutClient._find_available_port()
        fres = run_hdc(["fport", f"tcp:{port}", "localabstract:scrcpy_grpc_socket"], udid, timeout=2.0)
        if "fail" in fres.lower() or "error" in fres.lower():
            return None

        channel = None
        try:
            channel = grpc.insecure_channel(f"127.0.0.1:{port}")
            start_stream = channel.unary_stream(
                "/ScrcpyService/onStart",
                request_serializer=lambda x: b"",
                response_deserializer=lambda x: x
            )
            req_idr = channel.unary_unary(
                "/ScrcpyService/onRequestIDRFrame",
                request_serializer=lambda x: b"",
                response_deserializer=lambda x: x
            )

            stream = start_stream(b"")

            def send_idr():
                time.sleep(0.12)
                try:
                    req_idr(b"")
                except Exception:
                    pass

            threading.Thread(target=send_idr, daemon=True).start()

            captured_bytes = None
            codec = av.CodecContext.create("h264", "r")

            def stream_reader():
                nonlocal captured_bytes
                try:
                    for resp in stream:
                        nalu = cls._extract_nalu(resp)
                        if not nalu:
                            continue
                        packets = codec.parse(nalu)
                        for packet in packets:
                            frames = codec.decode(packet)
                            for f in frames:
                                rgb_array = f.to_ndarray(format="rgb24")
                                h, w, _ = rgb_array.shape
                                qimg = QImage(bytes(rgb_array.data), w, h, 3 * w, QImage.Format.Format_RGB888).copy()
                                buf = QByteArray()
                                buffer_io = QBuffer(buf)
                                buffer_io.open(QBuffer.OpenModeFlag.WriteOnly)
                                qimg.save(buffer_io, "JPEG", 85)
                                captured_bytes = bytes(buf)
                                cls.latest_image = qimg
                                cls.latest_frame_bytes = captured_bytes
                                cls.latest_frame_time = time.time()
                                cls.latest_udid = udid
                                return
                except Exception:
                    pass

            read_thread = threading.Thread(target=stream_reader, daemon=True)
            read_thread.start()
            read_thread.join(timeout=timeout)

            if captured_bytes:
                return captured_bytes
        except Exception:
            pass
        finally:
            if channel:
                try:
                    channel.close()
                except Exception:
                    pass
            if port > 0 and udid:
                try:
                    run_hdc(["fport", "rm", f"tcp:{port}", "localabstract:scrcpy_grpc_socket"], udid, timeout=1.0)
                except Exception:
                    pass

        return None

    def _run_harmony_scrcpy_stream(self) -> bool:
        """
        鸿蒙 6.0+ / 7.0+ 原生硬件录屏流引擎 (1:1 还原 HoKit 架构，彻底根除 DMS 截屏广播与三条 IM 聊天截屏通知)
        核心原理:
        1. 启动 uitest 扩展 scrcpy_server.so (基于 AVScreenCapture / VirtualDisplay 硬件视频流通道，非快照截图)；
        2. 通过 localabstract:scrcpy_grpc_socket 映射本地端口拉取 H.264 码流；
        3. 利用 PyAV (FFmpeg) 毫秒级硬/软解码出 RGB 帧并通过纯 QImage 线程安全输出，DMS 100% 绝不派发 COMMON_EVENT_SCREEN_CAPTURE！
        """
        import grpc
        import av
        import threading

        # 清除所有历史残留端口转发，杜绝通道错乱
        self._clean_all_scrcpy_fports(self.udid)
        # 1:1 对齐 HoKit 会话治理：每次新会话清理旧残留，确保独占全新 unix socket 通道
        self._kill_existing_scrcpy_daemons(self.udid)
        self._ensure_harmony_env(self.udid)

        # 核心高韧性保障：轮询探测真机 unix abstract socket 是否已在内核成功注册 (彻底根除 10054 Connection reset)
        socket_ready = False
        for _ in range(30):
            chk = run_hdc(["shell", "cat /proc/net/unix | grep scrcpy_grpc_socket"], self.udid, timeout=1.0)
            if "scrcpy_grpc_socket" in chk:
                socket_ready = True
                break
            time.sleep(0.1)
        if not socket_ready:
            logging.warning("[投屏引擎] 守护进程 unix socket 初始化超时或已退出")
            self.error_occurred.emit("鸿蒙底层投屏服务未能就绪，请确认设备屏幕已解锁并授权调试。")
            return False

        # 建立本地端口转发到真机 localabstract:scrcpy_grpc_socket
        self._local_port = HarmonyRpcLayoutClient._find_available_port()
        fport_res = run_hdc(
            ["fport", f"tcp:{self._local_port}", "localabstract:scrcpy_grpc_socket"],
            self.udid,
            timeout=2.0
        )
        if "fail" in fport_res.lower() or "error" in fport_res.lower():
            self.error_occurred.emit("鸿蒙投屏端口映射建立失败")
            return False

        try:
            self._grpc_channel = grpc.insecure_channel(f"127.0.0.1:{self._local_port}")
            start_stream = self._grpc_channel.unary_stream(
                "/ScrcpyService/onStart",
                request_serializer=lambda x: b"",
                response_deserializer=lambda x: x
            )
            req_idr = self._grpc_channel.unary_unary(
                "/ScrcpyService/onRequestIDRFrame",
                request_serializer=lambda x: b"",
                response_deserializer=lambda x: x
            )

            stream = start_stream(b"")
        except Exception as e:
            logging.warning(f"[投屏引擎] gRPC 连接建立异常: {e}")
            self.error_occurred.emit(f"连接鸿蒙投屏通道失败: {e}")
            return False

        # 异步请求关键帧 IDR，极速激活首帧解码
        def request_idr_task():
            time.sleep(0.12)
            try:
                req_idr(b"")
            except Exception:
                pass

        threading.Thread(target=request_idr_task, daemon=True).start()

        codec = av.CodecContext.create("h264", "r")
        last_emit_t = 0.0

        # 视频流解码循环 (1:1 对齐 HoKit 黄金投屏：30fps，丢弃陈旧堆积帧，切换画面丝滑无感零卡顿)
        has_emitted_first_frame = False
        try:
            for resp in stream:
                if not self._is_running:
                    break
                nalu = self._extract_nalu(resp)
                if not nalu:
                    continue
                try:
                    packets = codec.parse(nalu)
                    if not packets:
                        continue
                    newest_frame = None
                    for packet in packets:
                        frames = codec.decode(packet)
                        if frames:
                            newest_frame = frames[-1]
                    if newest_frame is not None:
                        now = time.time()
                        # 控制最高 30~35fps 派发频率（约每 28ms 一帧），防止主线程事件队列积压导致切换画面掉帧
                        if now - last_emit_t >= 0.028:
                            last_emit_t = now
                            rgb_array = newest_frame.to_ndarray(format="rgb24")
                            h, w, _ = rgb_array.shape
                            qimg = QImage(bytes(rgb_array.data), w, h, 3 * w, QImage.Format.Format_RGB888).copy()
                            ScreenCastWorker.latest_image = qimg
                            ScreenCastWorker.latest_frame_time = now
                            ScreenCastWorker.latest_udid = self.udid
                            self.frame_ready.emit(qimg, b"")
                            if not has_emitted_first_frame:
                                has_emitted_first_frame = True
                                self.state_changed.emit(True, "投屏已连接")
                except Exception:
                    pass
        except Exception:
            pass

        return True

    def _run_harmony_stream(self):
        """
        鸿蒙投屏总入口：优先启用 1:1 HoKit 原生硬件录屏流 (100% 根除截屏通知，25~30 FPS 丝滑满帧)
        """
        ScreenCastWorker.is_active = True
        try:
            while self._is_running:
                try:
                    ok = self._run_harmony_scrcpy_stream()
                    if not ok:
                        break
                except Exception as e:
                    logging.warning(f"[投屏引擎] 录屏流自愈重试: {e}")
                finally:
                    self._cleanup_harmony_port()

                if self._is_running:
                    time.sleep(0.3)
        finally:
            ScreenCastWorker.is_active = False

    def _run_android_scrcpy_stream(self) -> bool:
        """
        安卓端 1:1 还原 i4AirPlayer (爱思投屏) 硬件录屏流引擎:
        1. 基于 scrcpy-server (com.genymobile.scrcpy.Server) 通过 MediaCodec 硬件级 60 FPS H.264 视频流直通；
        2. 主机端利用 PyAV (FFmpeg) 毫秒级硬/软解码 Annex-B NALU 帧，直接转为 RGB24 QImage 显存直出；
        3. 滑动和桌面切换时彻底消除 UIAutomator 锁死和 screencap 管道延迟，达到 1:1 丝滑如风、零卡顿、零掉帧。
        """
        import socket
        import struct
        import random
        import av

        creationflags = 0x08000000 if sys.platform == "win32" else 0
        udid = self.udid

        # 1. 查找并确保设备端具备 scrcpy-server.jar (全场景穿透定位，0 机器私有盘符硬编码)
        local_jar = SmartPathResolver.get_asset_path("desktop_app/assets/android/scrcpy-server")
        if not local_jar:
            env_scrcpy = os.environ.get("SCRCPY_SERVER_PATH", "").strip()
            if env_scrcpy and os.path.isfile(env_scrcpy):
                local_jar = env_scrcpy

        if not local_jar:
            logging.warning("[安卓投屏] 未找到本地 scrcpy-server 资源，跳过硬件流")
            return False

        adb_bin = "adb"
        try:
            from desktop_app.core.path_resolver import SmartPathResolver
            tc = SmartPathResolver.discover_mobile_toolchain()
            if tc.get("adb"):
                adb_bin = tc["adb"]
        except Exception:
            pass

        # 检查设备端是否存在 /data/local/tmp/scrcpy-server.jar
        cmd_check = [adb_bin]
        if udid:
            cmd_check.extend(["-s", udid])
        cmd_check.extend(["shell", "[ -f /data/local/tmp/scrcpy-server.jar ] && echo 'exists' || echo 'missing'"])
        res_chk = subprocess.run(cmd_check, capture_output=True, text=True, timeout=2.0, creationflags=creationflags)
        if "exists" not in res_chk.stdout:
            cmd_push = [adb_bin]
            if udid:
                cmd_push.extend(["-s", udid])
            cmd_push.extend(["push", local_jar, "/data/local/tmp/scrcpy-server.jar"])
            subprocess.run(cmd_push, capture_output=True, timeout=5.0, creationflags=creationflags)

        # 2. 本地监听随机可用端口
        self._android_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._android_server_sock.bind(("127.0.0.1", 0))
        local_port = self._android_server_sock.getsockname()[1]
        self._android_server_sock.listen(1)
        self._android_server_sock.settimeout(4.0)

        # 3. 建立 adb reverse 端口映射
        self._android_scid = f"{random.randint(0x10000000, 0x7fffffff):08x}"
        cmd_rev = [adb_bin]
        if udid:
            cmd_rev.extend(["-s", udid])
        cmd_rev.extend(["reverse", f"localabstract:scrcpy_{self._android_scid}", f"tcp:{local_port}"])
        res_rev = subprocess.run(cmd_rev, capture_output=True, text=True, timeout=2.0, creationflags=creationflags)
        if res_rev.returncode != 0:
            logging.warning(f"[安卓投屏] adb reverse 失败: {res_rev.stderr}")
            return False

        # 4. 启动设备端 scrcpy-server 硬件录屏
        # 核心参数: cleanup=false 避免退出时误删 jar 包; tunnel_forward=false 采用反向代理回连
        cmd_start = [
            adb_bin,
        ]
        if udid:
            cmd_start.extend(["-s", udid])
        cmd_start.extend([
            "shell",
            f"CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / com.genymobile.scrcpy.Server 3.3.4 scid={self._android_scid} log_level=info video=true audio=false control=false cleanup=false tunnel_forward=false max_size=1080 video_bit_rate=8000000 max_fps=60"
        ])
        self._android_proc = subprocess.Popen(
            cmd_start,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )

        # 5. 等待真机连接
        try:
            self._android_conn, _ = self._android_server_sock.accept()
            self._android_conn.settimeout(5.0)
        except Exception as e:
            logging.warning(f"[安卓投屏] scrcpy 回连超时或失败: {e}")
            return False

        # 6. 读取协议头 (64 字节设备名 + 12 字节视频编码元信息)
        try:
            dev_name = self._android_conn.recv(64)
            codec_meta = self._android_conn.recv(12)
        except Exception as e:
            logging.warning(f"[安卓投屏] 协议头读取失败: {e}")
            return False

        # 7. 解码循环
        codec = av.CodecContext.create("h264", "r")
        last_emit_t = 0.0

        def recv_exact(sock, n):
            buf = bytearray()
            while len(buf) < n:
                if not self._is_running:
                    return None
                chunk = sock.recv(min(8192, n - len(buf)))
                if not chunk:
                    return None
                buf.extend(chunk)
            return bytes(buf)

        try:
            while self._is_running:
                hdr = recv_exact(self._android_conn, 12)
                if not hdr or len(hdr) < 12:
                    break
                pts, sz = struct.unpack(">QI", hdr)
                if sz == 0:
                    continue
                packet_data = recv_exact(self._android_conn, sz)
                if not packet_data or len(packet_data) < sz:
                    break

                packets = codec.parse(packet_data)
                if not packets:
                    continue

                newest_frame = None
                for packet in packets:
                    frames = codec.decode(packet)
                    if frames:
                        newest_frame = frames[-1]

                if newest_frame is not None and self._is_running:
                    now = time.time()
                    # 控制最高 30~35fps 派发频率（约每 28ms 一帧），防止主线程事件队列积压导致切换画面掉帧
                    if now - last_emit_t >= 0.028:
                        last_emit_t = now
                        rgb_array = newest_frame.to_ndarray(format="rgb24")
                        h, w, _ = rgb_array.shape
                        qimg = QImage(bytes(rgb_array.data), w, h, 3 * w, QImage.Format.Format_RGB888).copy()
                        ScreenCastWorker.latest_image = qimg
                        ScreenCastWorker.latest_frame_time = now
                        ScreenCastWorker.latest_udid = self.udid
                        self.frame_ready.emit(qimg, b"")
        except Exception as e:
            logging.warning(f"[安卓投屏] 解码循环异常中断: {e}")
        finally:
            self._cleanup_android_stream()

        return True

    def _run_android_stream(self):
        """
        安卓端极速实时投屏引擎 (1:1 还原 i4AirPlayer 爱思投屏架构 + 双通道自愈容灾):
        1. 优先启用 1:1 i4AirPlayer 架构：scrcpy-server 硬件级 MediaCodec 60 FPS H.264 直通流，
           由 PyAV (FFmpeg) 毫秒级硬解码，显存直通 QImage (彻底根除滑动与切屏掉帧)；
        2. 若设备或环境不支持，自动降级至 uiautomator2 原生 takeScreenshot(1, 55) 显存直出；
        3. 极端场景兜底至 adb exec-out screencap -p 内存管道流。
        """
        ScreenCastWorker.is_active = True
        creationflags = 0x08000000 if sys.platform == "win32" else 0

        # 方式 1: 1:1 i4AirPlayer 硬件视频流引擎 (60 FPS 满帧直通，滑动如丝顺滑)
        while self._is_running:
            try:
                ok = self._run_android_scrcpy_stream()
                if ok and not self._is_running:
                    ScreenCastWorker.is_active = False
                    return
            except Exception as e:
                logging.warning(f"[安卓投屏] scrcpy 硬件流异常: {e}")
            break

        if not self._is_running:
            ScreenCastWorker.is_active = False
            return

        # 方式 2: 降级为 UIAutomator JSON-RPC 原生 takeScreenshot
        u2_device = None
        try:
            import uiautomator2 as u2
            u2_device = u2.connect(self.udid) if self.udid else u2.connect()
        except Exception as e:
            logging.warning(f"[安卓投屏] uiautomator2 初始化异常: {e}")
            u2_device = None

        while self._is_running:
            qimg = None
            raw_bytes = b""
            now = time.time()

            # 方式 1: 直接调用 UIAutomator 原生 takeScreenshot (140ms 极速显存直出，零 Pillow/NumPy 损耗)
            if u2_device is not None:
                try:
                    b64 = u2_device.jsonrpc.takeScreenshot(1, 55)
                    if b64:
                        raw_bytes = base64.b64decode(b64)
                        if raw_bytes:
                            qimg = QImage.fromData(raw_bytes, "JPEG")
                except Exception:
                    # 容灾自愈：若断连尝试重连一次
                    try:
                        import uiautomator2 as u2
                        u2_device = u2.connect(self.udid) if self.udid else u2.connect()
                    except Exception:
                        u2_device = None

            # 方式 3: 兜底 adb exec-out screencap -p
            if (qimg is None or qimg.isNull()) and self._is_running:
                try:
                    cmd_sc = ["adb"]
                    if self.udid:
                        cmd_sc.extend(["-s", self.udid])
                    cmd_sc.extend(["exec-out", "screencap", "-p"])
                    res = subprocess.run(
                        cmd_sc,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        timeout=2.0,
                        creationflags=creationflags
                    )
                    if res.stdout and len(res.stdout) > 1000:
                        raw_bytes = res.stdout
                        qimg = QImage.fromData(raw_bytes, "PNG")
                except Exception:
                    pass

            if qimg is not None and not qimg.isNull() and self._is_running:
                # 严格绑定当前设备 UDID，杜绝跨设备脏数据
                ScreenCastWorker.latest_image = qimg
                ScreenCastWorker.latest_frame_time = now
                ScreenCastWorker.latest_udid = self.udid
                if raw_bytes:
                    ScreenCastWorker.latest_frame_bytes = raw_bytes
                self.frame_ready.emit(qimg, raw_bytes)

            time.sleep(0.005)

        ScreenCastWorker.is_active = False

    def _run_ios_stream(self):
        """
        iOS 端极速实时投屏引擎 (内存级 DVT 会话直通 + WDA 多通道自愈):
        1. 优先探测原生 WDA 长连接 (/mjpegstream 或 /screenshot 轮询)；
        2. 若 WDA 未通或在 iOS 17+ 环境下，启用原生 userspace_tunnel + DvtProvider 内存级持久会话，
           彻底消除 subprocess.run 高频创建 Python 进程开销 (单帧从 2.5s 骤降至 0.6s，提速 400%)，
           0 磁盘临时文件，纯内存 PNG 直通 QImage；
        3. 备用降级 pymobiledevice3 DVT CLI 保证极端容灾韧性。
        """
        import urllib.request
        import base64
        import asyncio

        ScreenCastWorker.is_active = True

        wda_url, _ = IosWdaManager.get_wda_url(self.udid)
        if not wda_url:
            wda_url = "http://127.0.0.1:8100"

        # 方式 1: 尝试通过 WDA 原生 /mjpegstream 极速长连接
        mjpeg_stream_ok = False
        try:
            stream_url = f"{wda_url}/mjpegstream?fps=30"
            req = urllib.request.Request(stream_url)
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    mjpeg_stream_ok = True
                    buffer = bytearray()
                    last_emit_t = 0.0
                    while self._is_running:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        buffer.extend(chunk)

                        latest_jpg = None
                        while True:
                            start_idx = buffer.find(b"\xff\xd8")
                            if start_idx == -1:
                                buffer.clear()
                                break
                            end_idx = buffer.find(b"\xff\xd9", start_idx)
                            if end_idx == -1:
                                if start_idx > 0:
                                    del buffer[:start_idx]
                                break
                            latest_jpg = bytes(buffer[start_idx : end_idx + 2])
                            del buffer[: end_idx + 2]

                        if latest_jpg and self._is_running:
                            now = time.time()
                            if now - last_emit_t >= 0.028:
                                last_emit_t = now
                                qimg = QImage.fromData(latest_jpg, "JPEG")
                                if qimg and not qimg.isNull():
                                    ScreenCastWorker.latest_image = qimg
                                    ScreenCastWorker.latest_frame_time = now
                                    ScreenCastWorker.latest_udid = self.udid
                                    ScreenCastWorker.latest_frame_bytes = latest_jpg
                                    self.frame_ready.emit(qimg, latest_jpg)
        except Exception:
            mjpeg_stream_ok = False

        if mjpeg_stream_ok or not self._is_running:
            ScreenCastWorker.is_active = False
            return

        # 方式 2: WDA /screenshot 极速轮询 (若 WDA 已就绪)
        wda_active = False
        try:
            req = urllib.request.Request(f"{wda_url}/status")
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                if resp.status == 200:
                    wda_active = True
        except Exception:
            wda_active = False

        if wda_active and self._is_running:
            while self._is_running:
                try:
                    req = urllib.request.Request(f"{wda_url}/screenshot")
                    with urllib.request.urlopen(req, timeout=1.2) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            b64_img = data.get("value", "")
                            if b64_img:
                                raw_bytes = base64.b64decode(b64_img)
                                qimg = QImage.fromData(raw_bytes)
                                if qimg and not qimg.isNull() and self._is_running:
                                    now = time.time()
                                    ScreenCastWorker.latest_image = qimg
                                    ScreenCastWorker.latest_frame_time = now
                                    ScreenCastWorker.latest_udid = self.udid
                                    ScreenCastWorker.latest_frame_bytes = raw_bytes
                                    self.frame_ready.emit(qimg, raw_bytes)
                except Exception:
                    break
                time.sleep(0.01)

        if not self._is_running:
            ScreenCastWorker.is_active = False
            return

        # 方式 3: 原生 userspace_tunnel + DvtProvider 内存级持久会话 (全版本通用支持，单帧 0.6s，纯内存零落盘)
        async def _run_in_process_dvt():
            from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
            from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

            udid = self.udid if (self.udid and not self.udid.startswith("wda_localhost")) else None
            provider = None
            try:
                from pymobiledevice3.remote import userspace_tunnel
                provider = await userspace_tunnel.establish_userspace_rsd(serial=udid)
            except Exception:
                from pymobiledevice3.lockdown import create_using_usbmux
                provider = await create_using_usbmux(serial=udid)

            if provider is None:
                raise RuntimeError("未能初始化 iOS 服务提供者通道")

            async with DvtProvider(provider) as dvt, Screenshot(dvt) as sc:
                while self._is_running:
                    raw_bytes = await sc.get_screenshot()
                    if raw_bytes and self._is_running:
                        qimg = QImage.fromData(raw_bytes, "PNG")
                        if qimg and not qimg.isNull():
                            now = time.time()
                            ScreenCastWorker.latest_image = qimg
                            ScreenCastWorker.latest_frame_time = now
                            ScreenCastWorker.latest_udid = self.udid
                            ScreenCastWorker.latest_frame_bytes = raw_bytes
                            self.frame_ready.emit(qimg, raw_bytes)
                    await asyncio.sleep(0.01)

        dvt_in_process_ok = False
        try:
            asyncio.run(_run_in_process_dvt())
            dvt_in_process_ok = True
        except Exception as e:
            logging.warning(f"[iOS投屏] in-process DvtProvider 退出或异常: {e}")
            dvt_in_process_ok = False

        if not self._is_running or dvt_in_process_ok:
            ScreenCastWorker.is_active = False
            return

        # 方式 4: 备用降级 pymobiledevice3 CLI 极速截屏 (极端场景高韧性兜底)
        try:
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            while self._is_running:
                qimg = None
                raw_bytes = b""
                try:
                    pmd_cmd = ["pymobiledevice3", "developer", "dvt", "screenshot"]
                    if self.udid and not self.udid.startswith("wda_localhost"):
                        pmd_cmd.extend(["--udid", self.udid])
                    project_root = SmartPathResolver.get_project_root()
                    tmp_ios = os.path.join(project_root, "reports", "inspector", f"ios_cast_{self.udid or 'dev'}.png")
                    os.makedirs(os.path.dirname(tmp_ios), exist_ok=True)
                    pmd_cmd.append(tmp_ios)
                    subprocess.run(pmd_cmd, timeout=3.5, capture_output=True, creationflags=creationflags)
                    if os.path.exists(tmp_ios) and os.path.getsize(tmp_ios) > 100:
                        with open(tmp_ios, "rb") as f_in:
                            raw_bytes = f_in.read()
                        qimg = QImage.fromData(raw_bytes)
                except Exception:
                    pass

                if qimg is not None and not qimg.isNull() and self._is_running:
                    now = time.time()
                    ScreenCastWorker.latest_image = qimg
                    ScreenCastWorker.latest_frame_time = now
                    ScreenCastWorker.latest_udid = self.udid
                    if raw_bytes:
                        ScreenCastWorker.latest_frame_bytes = raw_bytes
                    self.frame_ready.emit(qimg, raw_bytes)

                time.sleep(0.05)
        finally:
            ScreenCastWorker.is_active = False

    def run(self):
        self._is_running = True
        self.state_changed.emit(True, "投屏已连接")
        try:
            if self.platform == "harmony":
                self._run_harmony_stream()
            elif self.platform == "android":
                self._run_android_stream()
            elif self.platform == "ios":
                self._run_ios_stream()
            else:
                self.error_occurred.emit(f"不支持的投屏平台: {self.platform}")
        except Exception as e:
            self.error_occurred.emit(f"投屏异常中断: {e}")
        finally:
            self._is_running = False
            self.state_changed.emit(False, "投屏已停止")


class CaptureWorker(QThread):
    """后台异步抓取线程：支持 HarmonyOS / Android / iOS 三端截图与 UI 层次拉取"""
    finished = pyqtSignal(str, str, str)  # local_png, layout_file, platform
    screen_finished = pyqtSignal(str)
    dom_finished = pyqtSignal(str, str)  # layout_file, platform (纯 DOM 刷新)
    failed = pyqtSignal(str)

    def __init__(self, udid: str, platform: str, tmp_dir: str, mode: str = "full"):
        super().__init__()
        self.udid = udid
        self.platform = platform
        self.tmp_dir = tmp_dir
        self.mode = mode

    @staticmethod
    def _silent_capture_harmony_screen(udid: str, local_png: str) -> bool:
        """
        底层静默截屏引擎 (支持投屏活跃内存复用与离线极速显存快照):
        1. 优先等待/复用当前实时投屏活跃内存 JPEG 帧 (0 外部调用，0 截屏广播，耗时 0ms)；
        2. 若投屏未开启或无内存帧，采用底层 snapshot_display 极速显存截屏 (耗时仅 20ms，100% 成功)；
        3. 若 snapshot_display 偶发异常，平滑降级至 uitest screenCap 或单帧通道兜底。
        """
        norm_local_path = os.path.normpath(os.path.abspath(local_png))
        os.makedirs(os.path.dirname(norm_local_path), exist_ok=True)

        # 1. 投屏引擎活跃中：直接轮询等待最新投屏帧 (最多等 1.5s，0 外部 I/O 损耗)
        if ScreenCastWorker.is_active and (ScreenCastWorker.latest_udid == udid or not ScreenCastWorker.latest_udid):
            for _ in range(30):
                latest_bytes = ScreenCastWorker.get_latest_jpeg_bytes(udid)
                if latest_bytes:
                    try:
                        with open(norm_local_path, "wb") as f_out:
                            f_out.write(latest_bytes)
                        return True
                    except Exception:
                        pass
                time.sleep(0.05)

        # 2. 检查内存最新新鲜帧 (4秒内有效，必须校验 UDID)
        latest_bytes = ScreenCastWorker.get_latest_jpeg_bytes(udid)
        if latest_bytes:
            try:
                with open(norm_local_path, "wb") as f_out:
                    f_out.write(latest_bytes)
                return True
            except Exception:
                pass

        # 3. 检查本地磁盘投屏缓存 (5秒内有效)
        tmp_dir = os.path.dirname(norm_local_path)
        cached_cast = os.path.join(tmp_dir, "screencast_last_harmony.jpeg")
        if os.path.exists(cached_cast) and (time.time() - os.path.getmtime(cached_cast) < 5.0):
            try:
                shutil.copyfile(cached_cast, norm_local_path)
                return True
            except Exception:
                pass

        # 4. 投屏未活跃时：采用系统底层 snapshot_display 极速显存快照 (耗时仅 0.05s~0.5s，100% 稳定高保真)
        uid = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        remote_jpeg = f"/data/local/tmp/santiao_shot_{uid}.jpeg"
        try:
            ret = run_hdc(["shell", f"snapshot_display -f {remote_jpeg}"], udid, timeout=2.5)
            if "success" in ret.lower() or "display 0" in ret.lower():
                run_hdc(["file", "recv", remote_jpeg, norm_local_path], udid, timeout=3.0)
                if os.path.exists(norm_local_path) and os.path.getsize(norm_local_path) > 100:
                    return True
        except Exception:
            pass
        finally:
            try:
                run_hdc(["shell", f"rm -f {remote_jpeg}"], udid, timeout=1.0)
            except Exception:
                pass

        # 5. 终极备用：单帧录屏通道 (0 截屏广播，绝不派发 COMMON_EVENT_SCREEN_CAPTURE)
        try:
            frame_bytes = ScreenCastWorker.capture_single_silent_frame(udid, timeout=3.0)
            if frame_bytes and len(frame_bytes) > 100:
                with open(norm_local_path, "wb") as f_out:
                    f_out.write(frame_bytes)
                return True
        except Exception:
            pass

        return False

    def run(self):
        try:
            # 引入唯一时间戳标识，杜绝连续刷新时新线程抢先删除上一帧文件引起的竞态 FileNotFoundError
            ts = int(time.time() * 1000)
            local_png = os.path.normpath(os.path.abspath(os.path.join(self.tmp_dir, f"shot_{self.platform}_{ts}.png")))
            layout_file = os.path.normpath(os.path.abspath(os.path.join(self.tmp_dir, f"layout_{self.platform}_{ts}.dat")))

            # 安全异步清理 5 分钟之前的历史临时抓取文件，不影响当前与上一帧
            try:
                now_t = time.time()
                for fn in os.listdir(self.tmp_dir):
                    if fn.startswith("shot_") or fn.startswith("layout_"):
                        fp = os.path.join(self.tmp_dir, fn)
                        if os.path.isfile(fp) and (now_t - os.path.getmtime(fp) > 300):
                            try:
                                os.remove(fp)
                            except Exception:
                                pass
            except Exception:
                pass

            if self.platform == "harmony":
                if self.mode == "screen_only":
                    # 仅抓屏模式：纯底层静默截屏，绝不触发前台应用截屏监听
                    shot_ok = self._silent_capture_harmony_screen(self.udid, local_png)
                    if shot_ok and os.path.exists(local_png):
                        self.screen_finished.emit(local_png)
                    else:
                        self.failed.emit("静默截屏失败，请确认设备屏幕已点亮且处于解锁状态。")
                    return

                if self.mode == "dom_only":
                    # 工业级纯 DOM 刷新模式 (对标 HoKit UIViewer 刷新机制):
                    # 零截屏命令 (不调 snapshot_display、不调 uitest screenCap)，绝不触发 DisplayManager 的 OnScreenshot 广播！
                    # 仅通过底层 uitest RPC / dumpLayout 极速提取内存组件树 (30~50ms)，前台 IM 软件 100% 毫无感知
                    layout_ok = False
                    try:
                        rpc_tree = HarmonyRpcLayoutClient.capture_layout_fast(self.udid)
                        if rpc_tree is not None:
                            with open(layout_file, "w", encoding="utf-8") as f:
                                json.dump(rpc_tree, f, ensure_ascii=False)
                            layout_ok = True
                    except Exception:
                        pass

                    if not layout_ok:
                        uid = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
                        remote_json = f"/data/local/tmp/santiao_layout_{uid}.json"
                        try:
                            run_hdc(["shell", f"uitest dumpLayout -p {remote_json}"], self.udid, timeout=4.0)
                            run_hdc(["file", "recv", remote_json, layout_file], self.udid, timeout=4.0)
                            layout_ok = os.path.exists(layout_file) and os.path.getsize(layout_file) > 100
                        except Exception:
                            pass
                        finally:
                            try:
                                run_hdc(["shell", f"rm -f {remote_json}"], self.udid, timeout=1.0)
                            except Exception:
                                pass

                    if not layout_ok:
                        try:
                            from hmnextauto.driver import Driver as HMDriver
                            hm_client = HMDriver(serial=self.udid or None)
                            hm_tree = hm_client.dump_hierarchy()
                            if hm_tree:
                                with open(layout_file, "w", encoding="utf-8") as f:
                                    json.dump(hm_tree, f, ensure_ascii=False)
                                layout_ok = True
                        except Exception:
                            pass

                    if layout_ok:
                        self.dom_finished.emit(layout_file, "harmony")
                    else:
                        self.failed.emit("获取组件层级树失败，请确认设备已连接且 uitest 守护进程活跃。")
                    return

                # 全量刷新模式 (点击“刷新界面”)：
                # 工业级闭环对齐机制：优先无感抓取 DOM 树 (不触发截屏广播，真机绝对静止)，紧接着瞬间抓取画面底图
                # 彻底消除先截屏触发截屏通知导致列表位移而与随后 DOM 错位的物理时差，确保画面与 DOM 树 100% 绝对吻合！
                layout_ok = False
                shot_ok = False
                uid = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
                remote_json = f"/data/local/tmp/santiao_layout_{uid}.json"

                # 【阶段 1】：优先毫秒级抓取绝对物理层级树 (零系统截屏广播，界面完全静止)
                # 步骤 1.0: 优先使用 RPC capture_layout_fast 纯内存抓取 (耗时仅 50ms，绝不与后台守护进程冲突)
                try:
                    rpc_tree = HarmonyRpcLayoutClient.capture_layout_fast(self.udid, timeout=3.0)
                    if rpc_tree is not None:
                        with open(layout_file, "w", encoding="utf-8") as f:
                            json.dump(rpc_tree, f, ensure_ascii=False)
                        layout_ok = True
                except Exception:
                    pass

                # 步骤 1.1: 若 RPC 偶发受限，再平滑尝试 CLI dumpLayout (去除非法 -i 参数，杜绝解析失败)
                if not layout_ok:
                    try:
                        run_hdc(["shell", f"uitest dumpLayout -p {remote_json}"], self.udid, timeout=4.0)
                        run_hdc(["file", "recv", remote_json, layout_file], self.udid, timeout=4.0)
                        layout_ok = os.path.exists(layout_file) and os.path.getsize(layout_file) > 100
                    except Exception:
                        pass
                    finally:
                        try:
                            run_hdc(["shell", f"rm -f {remote_json}"], self.udid, timeout=1.0)
                        except Exception:
                            pass

                if not layout_ok:
                    try:
                        from hmnextauto.driver import Driver as HMDriver
                        for _k in list(logging.Logger.manager.loggerDict.keys()):
                            if "hmnextauto" in _k:
                                _sub_l = logging.getLogger(_k)
                                _sub_l.setLevel(logging.WARNING)
                                for _h in _sub_l.handlers:
                                    if hasattr(_h, "setStream"):
                                        _h.setStream(sys.stdout)
                        hm_client = HMDriver(serial=self.udid or None)
                        hm_tree = hm_client.dump_hierarchy()
                        if hm_tree:
                            with open(layout_file, "w", encoding="utf-8") as f:
                                json.dump(hm_tree, f, ensure_ascii=False)
                            layout_ok = True
                    except Exception:
                        pass

                # 【阶段 2】：紧随其后毫秒级抓取真机当前物理画面 (静默抓取显存底图，杜绝触发 IM 截屏消息)
                shot_ok = self._silent_capture_harmony_screen(self.udid, local_png)

                # 工业级高韧性原子交付：底图与 DOM 树一次性装载，杜绝中间态重复渲染
                if shot_ok and layout_ok:
                    self.finished.emit(local_png, layout_file, "harmony")
                elif layout_ok and not shot_ok:
                    # DOM 结构树已完整获取，画面临时获取超时 -> 自动生成轻量占位背景图，确保 DOM 审查流程畅通无阻
                    try:
                        qimg = QImage(1084, 2412, QImage.Format.Format_RGB32)
                        qimg.fill(QColor("#f8fafc"))
                        painter = QPainter(qimg)
                        painter.setPen(QPen(QColor("#cbd5e1"), 2))
                        painter.drawRect(20, 20, 1044, 2372)
                        painter.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
                        painter.setPen(QColor("#64748b"))
                        painter.drawText(QRect(40, 1000, 1000, 100), Qt.AlignmentFlag.AlignCenter, "真机画面获取超时 (屏幕熄灭或权限受限)")
                        painter.setFont(QFont("Microsoft YaHei", 14))
                        painter.setPen(QColor("#94a3b8"))
                        painter.drawText(QRect(40, 1120, 1000, 80), Qt.AlignmentFlag.AlignCenter, "DOM 组件层级树已成功载入，可在中栏与右栏正常审查")
                        painter.end()
                        qimg.save(local_png, "PNG")
                    except Exception:
                        pass
                    self.finished.emit(local_png, layout_file, "harmony")
                elif shot_ok and not layout_ok:
                    self.screen_finished.emit(local_png)
                    self.failed.emit("组件层级树拉取超时，请稍后再次点击刷新。")
                else:
                    # 两者均失败 -> 智能诊断设备真实连接状态
                    diag_msg = "抓取鸿蒙现场数据失败，请确认屏幕已点亮且处于解锁状态。"
                    try:
                        target_status = run_hdc(["list", "targets", "-v"], timeout=2.0)
                        if "offline" in target_status.lower():
                            diag_msg = "设备当前处于脱机(Offline)休眠状态，请点亮屏幕并重新允许 USB 调试连接。"
                        elif self.udid and self.udid not in target_status:
                            diag_msg = f"未检测到设备 {self.udid}，请检查 USB 线缆或重新插拔。"
                    except Exception:
                        pass
                    self.failed.emit(diag_msg)

            elif self.platform == "android":
                if self.mode == "dom_only":
                    remote_xml = "/data/local/tmp/appium_layout.xml"
                    run_adb(["shell", "uiautomator", "dump", remote_xml], self.udid)
                    run_adb(["pull", remote_xml, layout_file], self.udid)
                    if os.path.exists(layout_file) and os.path.getsize(layout_file) > 100:
                        self.dom_finished.emit(layout_file, "android")
                    else:
                        self.failed.emit("获取安卓组件层级树失败，请确认设备屏幕已解锁且已授权 USB 调试。")
                    return

                # 安卓: 优先复用当前活跃投屏的新鲜显存帧 (耗时 0ms)
                shot_ok = False
                if ScreenCastWorker.is_active and (ScreenCastWorker.latest_udid == self.udid or not ScreenCastWorker.latest_udid):
                    latest_bytes = ScreenCastWorker.get_latest_jpeg_bytes(self.udid)
                    if latest_bytes:
                        try:
                            with open(local_png, "wb") as f_out:
                                f_out.write(latest_bytes)
                            shot_ok = True
                        except Exception:
                            pass

                # 若未开启投屏，优先采用 uiautomator2 显存直通秒存，平滑降级至 adb exec-out
                if not shot_ok:
                    try:
                        import uiautomator2 as u2
                        d = u2.connect(self.udid) if self.udid else u2.connect()
                        d.screenshot(local_png)
                        shot_ok = os.path.exists(local_png) and os.path.getsize(local_png) > 1000
                    except Exception:
                        shot_ok = False

                if not shot_ok:
                    try:
                        creationflags = 0x08000000 if sys.platform == "win32" else 0
                        cmd = ["adb"]
                        if self.udid:
                            cmd.extend(["-s", self.udid])
                        cmd.extend(["exec-out", "screencap", "-p"])
                        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=6, creationflags=creationflags)
                        if p.stdout and len(p.stdout) > 1000:
                            with open(local_png, "wb") as f:
                                f.write(p.stdout)
                            shot_ok = True
                    except Exception:
                        pass

                if not shot_ok:
                    try:
                        run_adb(["shell", "screencap", "-p", "/data/local/tmp/appium_shot.png"], self.udid)
                        run_adb(["pull", "/data/local/tmp/appium_shot.png", local_png], self.udid)
                        shot_ok = os.path.exists(local_png) and os.path.getsize(local_png) > 1000
                    except Exception:
                        pass

                if shot_ok:
                    self.screen_finished.emit(local_png)

                if self.mode == "screen_only":
                    if not shot_ok:
                        self.failed.emit("获取安卓真机画面失败，请确认屏幕已点亮并解锁。")
                    return

                remote_xml = "/data/local/tmp/appium_layout.xml"
                run_adb(["shell", "uiautomator", "dump", remote_xml], self.udid)
                run_adb(["pull", remote_xml, layout_file], self.udid)

                if os.path.exists(local_png) and os.path.exists(layout_file):
                    self.finished.emit(local_png, layout_file, "android")
                else:
                    self.failed.emit("抓取安卓现场数据失败，请确认设备屏幕已解锁且已授权 USB 调试。")

            elif self.platform == "ios":
                import urllib.request
                wda_url, wda_diag = IosWdaManager.get_wda_url(self.udid)
                shot_ok = False
                layout_ok = False

                if self.mode == "dom_only":
                    if wda_url:
                        for fmt in ("json", "xml"):
                            try:
                                req = urllib.request.Request(f"{wda_url}/source?format={fmt}")
                                with urllib.request.urlopen(req, timeout=10) as resp:
                                    if resp.status == 200:
                                        with open(layout_file, "wb") as f:
                                            f.write(resp.read())
                                        layout_ok = True
                                        break
                            except Exception:
                                pass
                    if not layout_ok:
                        try:
                            pmd_acc = ["pymobiledevice3", "developer", "accessibility", "list-items"]
                            if self.udid and not self.udid.startswith("wda_localhost"):
                                pmd_acc.extend(["--udid", self.udid])
                            res = subprocess.run(pmd_acc, timeout=10, capture_output=True, text=True, errors="ignore", creationflags=0x08000000 if sys.platform == "win32" else 0)
                            if res.returncode == 0 and res.stdout.strip():
                                items = json.loads(res.stdout.strip())
                                if isinstance(items, list) and items:
                                    children = []
                                    for item in items:
                                        caption = item.get("caption") or item.get("spoken_description") or ""
                                        uid = item.get("estimated_uid") or item.get("platform_identifier") or ""
                                        children.append({
                                            "attributes": {
                                                "name": caption,
                                                "label": caption,
                                                "value": uid,
                                                "type": "XCUIElementTypeOther",
                                                "bounds": "[0,0][1170,2532]"
                                            },
                                            "children": []
                                        })
                                    acc_root = {"attributes": {"type": "Application", "name": "iOS App", "bounds": "[0,0][1170,2532]"}, "children": children}
                                    with open(layout_file, "w", encoding="utf-8") as f:
                                        json.dump(acc_root, f, ensure_ascii=False, indent=2)
                                    layout_ok = True
                        except Exception:
                            pass
                    if layout_ok and os.path.exists(layout_file) and os.path.getsize(layout_file) > 100:
                        self.dom_finished.emit(layout_file, "ios")
                    else:
                        self.failed.emit("获取 iOS 组件层级树失败，请确认 WDA 活跃或设备已连接。")
                    return

                if wda_url:
                    # 1. 优先通过 WDA 原生截屏
                    try:
                        req = urllib.request.Request(f"{wda_url}/screenshot")
                        with urllib.request.urlopen(req, timeout=8) as resp:
                            if resp.status == 200:
                                data = json.loads(resp.read().decode("utf-8"))
                                b64_img = data.get("value", "")
                                if b64_img:
                                    with open(local_png, "wb") as f:
                                        f.write(base64.b64decode(b64_img))
                                    shot_ok = True
                    except Exception:
                        pass

                    if self.mode == "screen_only":
                        if shot_ok:
                            self.screen_finished.emit(local_png)
                        return

                    # 2. 原生拉取 WDA 完整 UI 树 (优先 JSON，备选 XML)
                    for fmt in ("json", "xml"):
                        try:
                            req = urllib.request.Request(f"{wda_url}/source?format={fmt}")
                            with urllib.request.urlopen(req, timeout=10) as resp:
                                if resp.status == 200:
                                    with open(layout_file, "wb") as f:
                                        f.write(resp.read())
                                    layout_ok = True
                                    break
                        except Exception:
                            pass

                # 2. 若 WDA 未通或截屏失败，优先通过 pymobiledevice3 DVT 原生通道抓取 (完美支持 iOS 17+)
                if not shot_ok:
                    try:
                        pmd_cmd = ["pymobiledevice3", "developer", "dvt", "screenshot", local_png]
                        if self.udid and not self.udid.startswith("wda_localhost"):
                            pmd_cmd.extend(["--udid", self.udid])
                        subprocess.run(pmd_cmd, timeout=12, capture_output=True, creationflags=0x08000000 if sys.platform == "win32" else 0)
                        shot_ok = os.path.exists(local_png) and os.path.getsize(local_png) > 100
                    except Exception:
                        pass

                # 备选 tidevice 截屏 (兼容 iOS 16 及以下设备)
                if not shot_ok:
                    try:
                        tidevice_bin = shutil.which("tidevice") or "tidevice"
                        t_cmd = [tidevice_bin]
                        if self.udid and not self.udid.startswith("wda_localhost"):
                            t_cmd.extend(["-u", self.udid])
                        t_cmd.extend(["screenshot", local_png])
                        subprocess.run(t_cmd, timeout=8, creationflags=0x08000000 if sys.platform == "win32" else 0)
                        shot_ok = os.path.exists(local_png) and os.path.getsize(local_png) > 100
                    except Exception:
                        pass

                if self.mode == "screen_only":
                    if shot_ok:
                        self.screen_finished.emit(local_png)
                    return

                # 3. 若 UI 树未就绪，通过 pymobiledevice3 accessibility 原生拉取界面组件树
                if not layout_ok:
                    try:
                        pmd_acc = ["pymobiledevice3", "developer", "accessibility", "list-items"]
                        if self.udid and not self.udid.startswith("wda_localhost"):
                            pmd_acc.extend(["--udid", self.udid])
                        res = subprocess.run(pmd_acc, timeout=10, capture_output=True, text=True, errors="ignore", creationflags=0x08000000 if sys.platform == "win32" else 0)
                        if res.returncode == 0 and res.stdout.strip():
                            items = json.loads(res.stdout.strip())
                            if isinstance(items, list) and items:
                                children = []
                                for item in items:
                                    caption = item.get("caption") or item.get("spoken_description") or ""
                                    uid = item.get("estimated_uid") or item.get("platform_identifier") or ""
                                    children.append({
                                        "attributes": {
                                            "name": caption,
                                            "label": caption,
                                            "value": uid,
                                            "type": "XCUIElementTypeOther",
                                            "bounds": "[0,0][1170,2532]"
                                        },
                                        "children": []
                                    })
                                acc_root = {
                                    "attributes": {
                                        "type": "Application",
                                        "name": "iOS App",
                                        "bounds": "[0,0][1170,2532]"
                                    },
                                    "children": children
                                }
                                with open(layout_file, "w", encoding="utf-8") as f:
                                    json.dump(acc_root, f, ensure_ascii=False, indent=2)
                                layout_ok = True
                    except Exception:
                        pass

                if shot_ok and layout_ok:
                    self.finished.emit(local_png, layout_file, "ios")
                elif shot_ok:
                    minimal_root = {"attributes": {"type": "Screen", "bounds": "[0,0][1170,2532]"}, "children": []}
                    with open(layout_file, "w", encoding="utf-8") as f:
                        json.dump(minimal_root, f)
                    self.finished.emit(local_png, layout_file, "ios")
                else:
                    detail_tip = (
                        f"【iOS 连接诊断信息】\n"
                        f"已识别设备 UDID: {self.udid}\n"
                        f"诊断结论: {wda_diag}\n\n"
                        f"【彻底解决与秒通步骤 (推荐)】:\n"
                        f"1. 手机状态：请先拿起 iPhone，【解锁进入主桌面】并保持屏幕常亮（息屏会自动断开 USB 调试）；\n"
                        f"2. 一键激活调试守护：打开【爱思助手】客户端 -> 点击顶部【工具箱】-> 点击【手机投屏】或【实时屏幕】；\n"
                        f"   (注：爱思助手会自动拉起苹果官方最新私有调试守护，无需在手机上点击 WebDriverAgentRunner 图标，规避系统机制闪退)；\n"
                        f"3. 激活投屏后：回到本审查器，再次点击顶部【🔄 刷新界面】，即可秒出原生界面与完整 DOM 树！"
                    )
                    self.failed.emit(detail_tip)

        except Exception as e:
            self.failed.emit(str(e))


# ==============================================================================
# 左栏：纯净真机屏幕视窗 (纯白画布 + 拟真机身外壳，无任何方格干扰)
# ==============================================================================

class InspectorMode:
    SELECT = "select"  # 审查选择模式
    TAP = "tap"        # 坐标点击模式
    SWIPE = "swipe"    # 坐标滑动模式


class AppiumScreenView(QWidget):
    """
    真机屏幕映射视窗：
    - 纯净真实画面，默认不绘制任何杂乱的全局方格；
    - 鼠标悬停 (Hover)：单个组件细腻光晕框 + 顶部浮动类型尺寸小气泡；
    - 鼠标点击选中 (Selected)：单个组件鲜亮克莱因蓝高亮实线框；
    - 自适应缩放居中绘制，拖拽调整窗口大小时平滑流畅。
    """
    element_selected = pyqtSignal(str)
    coordinate_tapped = pyqtSignal(int, int)
    coordinate_swiped = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.mode = InspectorMode.SELECT
        self.pixmap: Optional[QPixmap] = None
        self.flat_components: List[Dict[str, Any]] = []
        self.comp_map: Dict[str, Dict[str, Any]] = {}
        self.hover_node_id: str = ""
        self.selected_node_id: str = ""
        self.orig_w = 1084
        self.orig_h = 2412
        self.layout_w = 1084
        self.layout_h = 2412

        # 拖拽滑动状态
        self.is_dragging = False
        self.swipe_start_pos: Optional[QPoint] = None
        self.swipe_cur_pos: Optional[QPoint] = None

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: transparent;")

    def set_mode(self, mode: str):
        self.mode = mode
        if mode == InspectorMode.SELECT:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif mode == InspectorMode.TAP:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == InspectorMode.SWIPE:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.update()

    def clear_screen(self):
        """清空当前屏幕图像与组件映射 (切换设备时调用，杜绝上一台设备的残影与错位)"""
        self.pixmap = None
        self.flat_components.clear()
        self.comp_map.clear()
        self.hover_node_id = ""
        self.selected_node_id = ""
        self.update()

    def update_screen_only(self, img_path: str, keep_components: bool = False):
        """
        极速同步真机画面：
        仅更新底图与分辨率比例，确保 0.05 秒内呈现真机最新画面。
        如果不保留旧组件 (keep_components=False)，则清除悬停和选中状态，避免旧界面的红框浮在已变更的画面上。
        """
        if not os.path.exists(img_path):
            return
        pix = QPixmap(img_path)
        if not pix.isNull():
            self.pixmap = pix
            self.orig_w = self.pixmap.width()
            self.orig_h = self.pixmap.height()
            self.layout_w = self.orig_w
            self.layout_h = self.orig_h
        if not keep_components:
            self.hover_node_id = ""
            self.selected_node_id = ""
        self.update()

    def update_screen_pixmap(self, pix: QPixmap, keep_components: bool = True):
        """
        实时投屏流极速渲染 (0 磁盘 I/O 损耗，对齐 HoKit Canvas 渲染):
        直接在显存/内存中装载 QPixmap，保留当前高亮组件，实现毫秒级无感丝滑更新。
        """
        if not pix or pix.isNull():
            return
        self.pixmap = pix
        self.orig_w = pix.width()
        self.orig_h = pix.height()
        # 保护基准分辨率：若已有 DOM 树物理坐标系尺寸 (如 1084x2412)，绝不随意被缩略帧覆盖，避免高亮红框错位
        if self.layout_w <= 0 or self.layout_h <= 0:
            self.layout_w = self.orig_w
            self.layout_h = self.orig_h
        elif self.orig_w < 800 and self.layout_w >= 800:
            pass  # 缩略投屏帧传入时，保持 layout_w 为物理基准，绝不覆盖
        if not keep_components:
            self.hover_node_id = ""
            self.selected_node_id = ""
        self.update()

    def update_components_only(self, components: List[Dict[str, Any]]):
        """
        仅更新 DOM 组件层级数据 (复用当前底图与缩放比例，对齐 HoKit UIViewer 叠加层机制):
        1. 保持当前视口缩放和平移状态不被重置，审查体验丝滑连贯；
        2. 清空悬停与过期选中历史，重新装载最新抓取的组件框。
        """
        self.flat_components = components
        self.comp_map = {c["node_id"]: c for c in components}
        self.hover_node_id = ""
        if self.selected_node_id not in self.comp_map:
            self.selected_node_id = ""
        # 自适应从组件最大右下边界校准 layout 坐标系
        max_r = max((c.get("right", 0) for c in components if c.get("right", 0) > 0), default=0)
        max_b = max((c.get("bottom", 0) for c in components if c.get("bottom", 0) > 0), default=0)
        if max_r >= 800 and max_b >= 1200:
            self.layout_w = max_r
            self.layout_h = max_b
        self.update()

    def load_screenshot(self, img_path: str, components: List[Dict[str, Any]]):
        self.pixmap = QPixmap(img_path)
        if not self.pixmap.isNull():
            self.orig_w = self.pixmap.width()
            self.orig_h = self.pixmap.height()
        else:
            self.orig_w = 1084
            self.orig_h = 2412

        self.flat_components = components
        self.comp_map = {c["node_id"]: c for c in components}
        self.hover_node_id = ""
        if self.selected_node_id not in self.comp_map:
            self.selected_node_id = ""

        # 权威基准对齐：真机物理截图的绝对分辨率即为唯一真理！
        # 绝不允许被滚动列表或离屏项的 max_b > orig_h 撑大导致纵向比例严重偏小与位置错位
        max_r = max((c.get("right", 0) for c in components if c.get("right", 0) > 0), default=0)
        max_b = max((c.get("bottom", 0) for c in components if c.get("bottom", 0) > 0), default=0)

        # 核心防毒化保护：如果底图为投屏硬件缩放帧 (如 542x1206，而组件最大边界为 1084x2412)，
        # layout 坐标基准必须采用组件的真实物理尺寸 (max_r, max_b)，绝不能被 542 缩小覆盖，
        # 从而保证 scale_x = draw_rect.width() / 1084，高亮框与画面 100% 绝对重合 (彻底杜绝图二错位现象)！
        if max_r > 0 and max_b > 0 and max_r > self.orig_w:
            self.layout_w = max_r
            self.layout_h = max_b
        elif self.orig_w > 0 and self.orig_h > 0:
            # 只有当属于 iOS 逻辑点坐标系 (即 max_r 和 max_b 明显小于物理截图的 75% 且对应标准 2x/3x 倍率) 时，才使用逻辑点坐标
            is_ios_points = (
                max_r > 0 and max_b > 0 and
                max_r <= self.orig_w * 0.75 and
                max_b <= self.orig_h * 0.75
            )
            if is_ios_points:
                self.layout_w = max_r
                self.layout_h = max_b
            else:
                # 鸿蒙 NEXT 原生与安卓原生：坐标系永远与真机物理原图 1:1 绝对吻合！
                self.layout_w = self.orig_w
                self.layout_h = self.orig_h
        elif max_r > 0 and max_b > 0:
            self.layout_w = max_r
            self.layout_h = max_b
        else:
            self.layout_w = 1084
            self.layout_h = 2412

        self.hover_node_id = ""
        self.update()

    def get_draw_rect(self) -> QRect:
        if not self.pixmap or self.pixmap.isNull():
            return QRect()
        avail_w = max(50, self.width() - 24)
        avail_h = max(50, self.height() - 24)
        # 纯几何等比缩放计算 (0 内存分配与 0 CPU 重采样损耗，耗时由 20ms 降至 0.0001ms)
        target_size = self.pixmap.size().scaled(
            QSize(avail_w, avail_h),
            Qt.AspectRatioMode.KeepAspectRatio
        )
        x = (self.width() - target_size.width()) // 2
        y = (self.height() - target_size.height()) // 2
        return QRect(x, y, target_size.width(), target_size.height())

    @staticmethod
    def is_content_component(comp: Dict[str, Any]) -> bool:
        """
        判断组件是否为具体有效内容或交互元素。
        对于纯结构性/排版背景容器（Column, Row, Stack, List 等无文字、无图片、无特定交互属性），
        鼠标移动到空白处时判定为无元素，绝不展示悬浮背景颜色。
        """
        if comp.get("is_interactive") is False:
            return False
        if comp.get("width", 0) <= 3 or comp.get("height", 0) <= 3:
            return False

        c_type = comp.get("type", "")
        c_text = (comp.get("text") or "").strip()
        c_id = (comp.get("id") or "").strip()
        raw = comp.get("raw_attributes", {})

        # 1. 具有具体文字内容（最核心的有效元素）
        if c_text:
            return True

        # 2. 属于天然的具体内容或交互组件 (覆盖鸿蒙 ArkUI NEXT 全量原生体系)
        content_types = {
            # 文本展示
            "Text", "Span", "StaticText", "TextClock", "Marquee", "Badge", "Divider",
            # 图标与富媒体 (重点覆盖鸿蒙 SymbolGlyph 等原生图标与画布)
            "SymbolGlyph", "Image", "Icon", "QRCode", "ImageView", "Video", "Web", "XComponent", "Canvas",
            # 按钮与操作交互
            "Button", "Toggle", "Checkbox", "Radio", "Switch", "ImageButton", "Slider", "Rating", "LoadingProgress",
            # 输入表单与编辑器
            "TextInput", "TextArea", "Search", "SearchField", "RichEditor", "RichEditorContent", "TextField", "EditText",
            # 菜单与弹窗选择器
            "Select", "MenuItem", "Menu", "DatePicker", "TimePicker", "TextPicker",
            # iOS 对应组件
            "XCUIElementTypeButton", "XCUIElementTypeImage", "XCUIElementTypeStaticText",
            "XCUIElementTypeTextField", "XCUIElementTypeSecureTextField", "XCUIElementTypeIcon"
        }
        if c_type in content_types:
            return True

        # 3. 具有特定业务 ID 且不是全屏/结构布局大容器
        container_types = {
            "Hierarchy", "root", "WindowScene", "Stack", "Navigation", "NavigationContent",
            "NavDestination", "NavDestinationContent", "Column", "Row", "List", "ListItem",
            "Refresh", "Scroll", "RelativeContainer", "Flex", "Grid", "GridItem", "Swiper",
            "__Common__", "ViewGroup", "FrameLayout", "LinearLayout", "RelativeLayout",
            "XCUIElementTypeWindow", "XCUIElementTypeOther", "XCUIElementTypeScrollView"
        }
        if c_id and c_type not in container_types:
            return True

        # 4. 可点击/可获焦且非大型结构容器（例如自定义气泡按钮、局部小挂件，需排除纯结构容器）
        clickable = raw.get("clickable") in ("true", True, "True")
        if clickable and comp.get("width", 0) < 600 and comp.get("height", 0) < 260:
            if c_type not in container_types:
                return True

        return False

    def find_component_at(self, dev_x: int, dev_y: int, for_hover: bool = False) -> str:
        """
        在设备坐标 (dev_x, dev_y) 处精准拾取组件:
        - for_hover=True: 鼠标在空白区域（仅命中纯结构容器）时直接返回 ""，不展示任何悬浮颜色；
        - for_hover=False: 点击操作，优先命中具体内容组件；若点击卡片容器/头像外框，则精准圈出该容器；
        - 核心权重：具体内容优先 > 面积最小优先 (越贴合准星越优先) > 树深度最深优先 (最内层叶子优先)。
        """
        matched = []
        for comp in self.flat_components:
            if comp["left"] <= dev_x <= comp["right"] and comp["top"] <= dev_y <= comp["bottom"]:
                # 过滤异常/超出边界的无效项
                if comp["width"] > 0 and comp["height"] > 0:
                    matched.append(comp)

        if not matched:
            return ""

        # 区分具体内容组件与纯结构背景容器
        content_matches = [c for c in matched if self.is_content_component(c)]

        if for_hover:
            # 悬停模式：若移动到空白背景容器上，不展示悬浮高亮颜色；仅当悬停在具体内容组件上才高亮
            if not content_matches:
                return ""
            candidates = content_matches
        else:
            # 点击模式：点哪儿就是哪儿！
            # 优先从击中的所有匹配组件中选取最内层、面积最小、层级最深的目标组件
            # 如果击中了内容组件 (文本/图标/按钮/输入框)，优先命中内容组件；
            # 如果点击的是自定义卡片容器、气泡或头像外框，则精准命中该容器！
            candidates = content_matches if content_matches else matched

        # 排序策略 (点哪儿圈哪儿，最内层叶子组件优先):
        # 1. 具体内容组件优先 (0 优先于 1)
        # 2. 面积最小优先 (最具体、最贴合准星的子组件优先)
        # 3. 树深度最深优先 (深度越深说明越是最内层的叶子组件)
        candidates.sort(key=lambda c: (
            0 if self.is_content_component(c) else 1,
            c["width"] * c["height"],
            -c.get("depth", 0)
        ))
        return candidates[0]["node_id"]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        draw_rect = self.get_draw_rect()
        if not self.pixmap or self.pixmap.isNull() or draw_rect.isEmpty():
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(QFont("PingFang SC", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "正在连接移动设备并同步界面布局...")
            return

        # 1. 绘制拟真手机深灰/银黑悬浮机身外壳与圆角投影
        phone_shell = draw_rect.adjusted(-6, -6, 6, 6)
        shell_path = QPainterPath()
        shell_path.addRoundedRect(QRectF(phone_shell), 16, 16)
        painter.fillPath(shell_path, QBrush(QColor("#0f172a")))
        painter.setPen(QPen(QColor("#cbd5e1"), 2))
        painter.drawPath(shell_path)

        # 2. 绘制实际真机屏幕原画截图 (直通硬件加速纹理贴图缩放，彻底消除 CPU 软件插值开销)
        screen_path = QPainterPath()
        screen_path.addRoundedRect(QRectF(draw_rect), 10, 10)
        painter.save()
        painter.setClipPath(screen_path)
        painter.drawPixmap(draw_rect, self.pixmap)
        painter.restore()

        # 统一使用绝对对齐的 layout 坐标系缩放比例
        scale_x = draw_rect.width() / self.layout_w
        scale_y = draw_rect.height() / self.layout_h

        # 3. 审查模式交互高亮：仅高亮 Hover 与选中的单个目标元素 (根据 DOM 组件类型展示微暗浅色标签与外框)
        if self.mode == InspectorMode.SELECT:
            # 鼠标悬停 (Hover) 单个有效组件（当与选中项不同时渲染专属微暗浅色虚线框与标签）
            if self.hover_node_id and self.hover_node_id in self.comp_map and self.hover_node_id != self.selected_node_id:
                h_comp = self.comp_map[self.hover_node_id]
                h_scheme = get_dom_tag_color(h_comp.get("type", ""))
                bx = int(draw_rect.x() + h_comp["left"] * scale_x)
                by = int(draw_rect.y() + h_comp["top"] * scale_y)
                bw = max(2, int(h_comp["width"] * scale_x))
                bh = max(2, int(h_comp["height"] * scale_y))

                painter.setPen(QPen(QColor(h_scheme["border"]), 1.8, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(h_scheme["box_bg"]))
                painter.drawRect(bx, by, bw, bh)

                # 顶部浮动类型与尺寸标签气泡 (浅色暗一点配色规范)
                tag_text = f" {h_comp['type']}  {h_comp['width']}×{h_comp['height']} "
                painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
                fm = painter.fontMetrics()
                tag_w = fm.horizontalAdvance(tag_text) + 8
                tag_h = 20
                tag_y = max(draw_rect.y() + 4, by - tag_h - 2)
                tag_rect = QRect(bx, tag_y, tag_w, tag_h)

                # 绘制胶囊底板与微暗边框
                painter.setPen(QPen(QColor(h_scheme["border"]), 1))
                painter.setBrush(QBrush(QColor(h_scheme["bg"])))
                painter.drawRoundedRect(tag_rect, 4, 4)
                painter.setPen(QColor(h_scheme["text"]))
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, tag_text)

            # 鼠标选中 (Selected) 单个目标组件：专属微暗浅色实线框 + 尺寸文本标签
            if self.selected_node_id and self.selected_node_id in self.comp_map:
                s_comp = self.comp_map[self.selected_node_id]
                s_scheme = get_dom_tag_color(s_comp.get("type", ""))
                bx = int(draw_rect.x() + s_comp["left"] * scale_x)
                by = int(draw_rect.y() + s_comp["top"] * scale_y)
                bw = max(2, int(s_comp["width"] * scale_x))
                bh = max(2, int(s_comp["height"] * scale_y))

                painter.setPen(QPen(QColor(s_scheme["border"]), 2.2, Qt.PenStyle.SolidLine))
                painter.setBrush(QBrush(s_scheme["box_bg"]))
                painter.drawRect(bx, by, bw, bh)

                # 顶部浮动类型与尺寸标签气泡
                s_text = s_comp.get("text", "")
                summary = f" {s_comp['type']}  {s_comp['width']}×{s_comp['height']}"
                if s_text:
                    clean_t = s_text[:14].replace("\n", " ") + ("..." if len(s_text) > 14 else "")
                    summary += f"  {clean_t}"
                summary += " "

                painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
                fm = painter.fontMetrics()
                tag_w = min(draw_rect.width() - 8, fm.horizontalAdvance(summary) + 10)
                tag_h = 20
                tag_y = max(draw_rect.y() + 4, by - tag_h - 2)
                tag_rect = QRect(bx, tag_y, tag_w, tag_h)

                # 绘制胶囊外壳 (浅色暗一点背景 + 沉稳同色边框 + 清晰暗色字)
                painter.setPen(QPen(QColor(s_scheme["border"]), 1.2))
                painter.setBrush(QBrush(QColor(s_scheme["bg"])))
                painter.drawRoundedRect(tag_rect, 4, 4)
                painter.setPen(QColor(s_scheme["text"]))
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, summary)

        # 4. 滑动模式下绘制交互手势轨迹
        if self.mode == InspectorMode.SWIPE and self.is_dragging and self.swipe_start_pos and self.swipe_cur_pos:
            pen_arrow = QPen(QColor("#0284c7"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arrow)
            painter.drawLine(self.swipe_start_pos, self.swipe_cur_pos)
            painter.setBrush(QBrush(QColor("#0284c7")))
            painter.drawEllipse(self.swipe_start_pos, 5, 5)
            painter.drawEllipse(self.swipe_cur_pos, 7, 7)

    def mouseMoveEvent(self, event):
        draw_rect = self.get_draw_rect()
        if draw_rect.isEmpty() or not draw_rect.contains(event.pos()):
            if self.hover_node_id:
                self.hover_node_id = ""
                self.update()
            return

        if self.mode == InspectorMode.SWIPE and self.is_dragging:
            self.swipe_cur_pos = event.pos()
            self.update()
            return

        if self.mode == InspectorMode.SELECT:
            scale_x = draw_rect.width() / self.layout_w
            scale_y = draw_rect.height() / self.layout_h
            dev_x = int((event.pos().x() - draw_rect.x()) / scale_x)
            dev_y = int((event.pos().y() - draw_rect.y()) / scale_y)

            # 核心：移动到空白没有元素的地方时直接返回 ""，绝不展示悬浮颜色
            hit_id = self.find_component_at(dev_x, dev_y, for_hover=True)
            if hit_id != self.hover_node_id:
                self.hover_node_id = hit_id
                self.update()

    def mousePressEvent(self, event):
        draw_rect = self.get_draw_rect()
        if draw_rect.isEmpty() or not draw_rect.contains(event.pos()):
            return

        scale_x = draw_rect.width() / self.layout_w
        scale_y = draw_rect.height() / self.layout_h
        dev_x = int((event.pos().x() - draw_rect.x()) / scale_x)
        dev_y = int((event.pos().y() - draw_rect.y()) / scale_y)

        if self.mode == InspectorMode.SELECT:
            if event.button() == Qt.MouseButton.LeftButton:
                # 核心：点击时精准重算目标组件，点哪里就圈出哪里，与 DOM 树节点完全一一对应
                target_id = self.find_component_at(dev_x, dev_y, for_hover=False)
                if target_id:
                    self.selected_node_id = target_id
                    self.hover_node_id = ""  # 选中后清除 hover 干扰
                    self.update()
                    self.element_selected.emit(self.selected_node_id)

        elif self.mode == InspectorMode.TAP:
            if event.button() == Qt.MouseButton.LeftButton:
                self.coordinate_tapped.emit(dev_x, dev_y)

        elif self.mode == InspectorMode.SWIPE:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = True
                self.swipe_start_pos = event.pos()
                self.swipe_cur_pos = event.pos()
                self.update()

    def mouseReleaseEvent(self, event):
        if self.mode == InspectorMode.SWIPE and self.is_dragging:
            self.is_dragging = False
            draw_rect = self.get_draw_rect()
            if self.swipe_start_pos and self.swipe_cur_pos and not draw_rect.isEmpty():
                scale_x = draw_rect.width() / self.layout_w
                scale_y = draw_rect.height() / self.layout_h
                x1 = int((self.swipe_start_pos.x() - draw_rect.x()) / scale_x)
                y1 = int((self.swipe_start_pos.y() - draw_rect.y()) / scale_y)
                x2 = int((self.swipe_cur_pos.x() - draw_rect.x()) / scale_x)
                y2 = int((self.swipe_cur_pos.y() - draw_rect.y()) / scale_y)
                self.swipe_start_pos = None
                self.swipe_cur_pos = None
                self.update()
                self.coordinate_swiped.emit(x1, y1, x2, y2)


def validate_xpath_syntax(xpath_str: str) -> Optional[str]:
    """
    全方位校验 XPath 表达式语法合法性 (纯 Python 零依赖 + lxml 双重兜底)：
    涵盖引号闭合、括号配对、连续斜杠、悬挂斜杠、轴名称合法性、节点测试合法性与谓语语法。
    若表达式合法返回 None；若存在语法错误，返回清晰易懂的中文错误描述。
    """
    if not xpath_str or not xpath_str.strip():
        return "XPath 表达式不能为空"

    xp = xpath_str.strip()

    # 1. 检查单双引号闭合与方括号/圆括号配对
    in_single_quote = False
    in_double_quote = False
    bracket_stack = []
    paren_stack = []

    for idx, ch in enumerate(xp):
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if ch == '[':
                bracket_stack.append(idx)
            elif ch == ']':
                if not bracket_stack:
                    return f"第 {idx + 1} 个字符处方括号 ']' 提前闭合，缺少对应的 '['"
                bracket_stack.pop()
            elif ch == '(':
                paren_stack.append(idx)
            elif ch == ')':
                if not paren_stack:
                    return f"第 {idx + 1} 个字符处圆括号 ')' 提前闭合，缺少对应的 '('"
                paren_stack.pop()

    if in_single_quote:
        return "单引号 ''' 未闭合，字符串缺少结束单引号"
    if in_double_quote:
        return '双引号 \'"\' 未闭合，字符串缺少结束双引号'
    if bracket_stack:
        pos = bracket_stack[-1] + 1
        return f"第 {pos} 个字符处方括号 '[' 未闭合，缺少对应的 ']'"
    if paren_stack:
        pos = paren_stack[-1] + 1
        return f"第 {pos} 个字符处圆括号 '(' 未闭合，缺少对应的 ')'"

    # 2. 检查顶层联合操作符 '|' (Union Operator) 并逐一校验各子分支
    # 例如: //Navigation//Image | //NavDestination//Image
    union_parts: List[str] = []
    u_buf: List[str] = []
    u_b_level = 0
    u_p_level = 0
    u_in_sq = False
    u_in_dq = False

    for ch in xp:
        if ch == "'" and not u_in_dq:
            u_in_sq = not u_in_sq
            u_buf.append(ch)
        elif ch == '"' and not u_in_sq:
            u_in_dq = not u_in_dq
            u_buf.append(ch)
        elif not u_in_sq and not u_in_dq:
            if ch == '[':
                u_b_level += 1
                u_buf.append(ch)
            elif ch == ']':
                u_b_level = max(0, u_b_level - 1)
                u_buf.append(ch)
            elif ch == '(':
                u_p_level += 1
                u_buf.append(ch)
            elif ch == ')':
                u_p_level = max(0, u_p_level - 1)
                u_buf.append(ch)
            elif ch == '|' and u_b_level == 0 and u_p_level == 0:
                union_parts.append("".join(u_buf).strip())
                u_buf = []
            else:
                u_buf.append(ch)
        else:
            u_buf.append(ch)

    union_parts.append("".join(u_buf).strip())

    if len(union_parts) > 1:
        for p_idx, part in enumerate(union_parts):
            if not part:
                return "联合操作符 '|' 前后缺少有效的路径表达式"
            sub_err = validate_xpath_syntax(part)
            if sub_err:
                return f"联合表达式分支 [{p_idx + 1}] 语法错误: {sub_err}"
        return None

    # 3. 检查空谓语 [] 与非法连续三个斜杠 ///
    i = 0
    in_sq = False
    in_dq = False
    while i < len(xp):
        ch = xp[i]
        if ch == "'" and not in_dq:
            in_sq = not in_sq
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
        elif not in_sq and not in_dq:
            if xp[i:i+2] == "[]":
                return "谓语方括号 '[]' 内部不能为空"
            if xp[i:i+3] == "///":
                return f"第 {i + 1} 个字符处存在非法的连续三个斜杠 '///'"
        i += 1

    # 3. 校验路径是否以 /、// 或 . 开头（考虑可能存在外层多重嵌套括号包装，如 ((//Text)[1])[1]）
    base_xp = xp
    while base_xp.startswith("(") and ")" in base_xp:
        r_paren_idx = base_xp.rfind(")")
        inner_content = base_xp[1:r_paren_idx].strip()
        outer_pred = base_xp[r_paren_idx+1:].strip()
        if outer_pred and not (outer_pred.startswith("[") or outer_pred.startswith("/")):
            return f"圆括号表达式后存在非法字符或空格: '{outer_pred}'"
        base_xp = inner_content

    if not (base_xp.startswith("/") or base_xp.startswith(".")):
        return "XPath 必须以 '/'、'//' 或 '.' 开头 (例如: //Text 或 /root)"

    # 4. 检查悬挂斜杠（以 / 或 // 结尾）
    if len(base_xp) > 1 and base_xp.endswith("/"):
        return "XPath 不能以悬空斜杠 '/' 或 '//' 结尾"

    # 5. 按照非引号、非括号内的 '/' 或 '//' 拆分步骤进行步进（Step）语法校验
    steps: List[str] = []
    i = 0
    n = len(base_xp)
    if base_xp.startswith("//"):
        i = 2
    elif base_xp.startswith("/"):
        i = 1

    buf = []
    b_level = 0
    p_level = 0
    in_sq = False
    in_dq = False

    while i < n:
        ch = base_xp[i]
        if ch == "'" and not in_dq:
            in_sq = not in_sq
            buf.append(ch)
            i += 1
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
            buf.append(ch)
            i += 1
        elif not in_sq and not in_dq:
            if ch == '[':
                b_level += 1
                buf.append(ch)
                i += 1
            elif ch == ']':
                b_level = max(0, b_level - 1)
                buf.append(ch)
                i += 1
            elif ch == '(':
                p_level += 1
                buf.append(ch)
                i += 1
            elif ch == ')':
                p_level = max(0, p_level - 1)
                buf.append(ch)
                i += 1
            elif b_level == 0 and p_level == 0 and base_xp[i:i+2] == "//":
                seg = "".join(buf).strip()
                if not seg:
                    return "连续斜杠之间缺少有效的节点测试步进"
                steps.append(seg)
                buf = []
                i += 2
            elif b_level == 0 and p_level == 0 and base_xp[i:i+1] == "/":
                seg = "".join(buf).strip()
                if not seg:
                    return "连续斜杠之间缺少有效的节点测试步进"
                steps.append(seg)
                buf = []
                i += 1
            else:
                buf.append(ch)
                i += 1
        else:
            buf.append(ch)
            i += 1

    last_seg = "".join(buf).strip()
    if last_seg:
        steps.append(last_seg)
    elif not steps and base_xp not in ("/", "//"):
        return "XPath 缺少有效的节点测试步进"

    VALID_AXES = {
        "ancestor", "ancestor-or-self", "attribute", "child", "descendant",
        "descendant-or-self", "following", "following-sibling", "namespace",
        "parent", "preceding", "preceding-sibling", "self"
    }

    # 6. 对每个步进逐一校验
    for step in steps:
        tag_and_pred = step
        # 轴定位校验
        if "::" in step:
            parts = step.split("::", 1)
            axis = parts[0].strip().lower()
            rest = parts[1].strip()
            if axis not in VALID_AXES:
                return f"未知的 XPath 轴名称 '{parts[0]}'，标准轴包括: following-sibling, preceding-sibling, parent, ancestor 等"
            if not rest:
                return f"轴 '{parts[0]}::' 后面缺少节点测试（如组件标签名或 '*'）"
            tag_and_pred = rest

        # 检查节点名与谓语
        m = re.match(r"^([a-zA-Z0-9_\-\*]+|\.\.|\.|node\(\)|text\(\))(.*)$", tag_and_pred)
        if not m:
            return f"步进 '{step}' 的节点名格式非法，组件标签名只能包含字母、数字、下划线、中划线或通配符 '*'"

        tag_name = m.group(1)
        rest_part = m.group(2)

        # 节点名后面若有内容，必须且只能以 '[' 开头！例如 pw123 1 包含非法字符空格
        if rest_part:
            rest_part_stripped = rest_part.strip()
            if rest_part_stripped and not rest_part_stripped.startswith("["):
                return f"节点 '{tag_name}' 后面存在未用方括号 '[]' 包裹的非法字符或空格: '{rest_part_stripped}'"

            # 进一步拆解谓语部分，检查每个 [...] 的语法
            pred_list = []
            p_buf = []
            p_depth = 0
            p_in_sq = False
            p_in_dq = False
            for ch in rest_part:
                if ch == "'" and not p_in_dq:
                    p_in_sq = not p_in_sq
                    p_buf.append(ch)
                elif ch == '"' and not p_in_sq:
                    p_in_dq = not p_in_dq
                    p_buf.append(ch)
                elif not p_in_sq and not p_in_dq:
                    if ch == '[':
                        if p_depth > 0:
                            p_buf.append(ch)
                        p_depth += 1
                    elif ch == ']':
                        p_depth -= 1
                        if p_depth == 0:
                            pred_list.append("".join(p_buf).strip())
                            p_buf = []
                        else:
                            p_buf.append(ch)
                    else:
                        if p_depth > 0:
                            p_buf.append(ch)
                        elif ch.strip():
                            return f"方括号谓语后存在非法字符 '{ch}'，谓语之间不能有孤立字符"
                else:
                    p_buf.append(ch)

            for p_content in pred_list:
                if not p_content:
                    return "谓语方括号 '[]' 内部不能为空"
                if p_content == "@":
                    return "属性选择符 '@' 后面缺少属性名，例如 [@text='...']"

                # 严格拦截 [w] 等单标识符/非法变量索引
                if re.match(r"^[a-zA-Z0-9_\-]+$", p_content):
                    if p_content.isdigit():
                        if int(p_content) <= 0:
                            return f"XPath 索引从 1 开始计数，不能使用 0 或负数 '[{p_content}]'"
                    elif p_content in ("last()", "position()", "true()", "false()"):
                        pass
                    else:
                        return (
                            f"谓语 '[{p_content}]' 语法异常：'{p_content}' 既非有效数字索引 (例如 [1])，"
                            f"也非属性过滤 (若匹配属性请添加 '@' 前缀，如 [@{p_content}])，请检查是否拼写错误"
                        )

                if "=" in p_content and not any(p_content.startswith(fn) for fn in ["contains", "starts-with", "not"]):
                    eq_parts = p_content.split("=", 1)
                    left = eq_parts[0].strip()
                    right = eq_parts[1].strip()
                    if not left:
                        return f"谓语 '{p_content}' 等号左侧缺少属性名"
                    if not right:
                        return f"谓语 '{p_content}' 等号右侧缺少对比值，例如 @text='标题'"
                    if not (right.isdigit() or right.startswith("'") or right.startswith('"') or right in ("true()", "false()", "last()")):
                        if " " in right or not re.match(r"^[a-zA-Z0-9_\-]+$", right):
                            return f"谓语属性值 '{right}' 缺少引号包裹，字符串属性值必须用单引号或双引号包裹"

                if "contains" in p_content:
                    m_c = re.search(r"contains\s*\((.*?)\)", p_content)
                    if m_c:
                        c_args = [arg.strip() for arg in m_c.group(1).split(",")]
                        if len(c_args) < 2 or not c_args[0] or not c_args[1]:
                            return "contains() 函数需要 2 个参数，格式如: contains(@text, '关键字')"

                # 递归校验以 . 或 / 开头的子路径嵌套谓语，如 [.//Text[@text='...']]
                if p_content.startswith((".", "//", "/")):
                    sub_err = validate_xpath_syntax(p_content)
                    if sub_err:
                        return f"嵌套谓语 '[{p_content}]' 内部语法错误: {sub_err}"

    # 7. 若系统安装了 lxml，尝试用 lxml 最终深度校验
    try:
        from lxml import etree
        etree.XPath(xp)
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception as e:
        lxml_err = str(e)
        if "Invalid expression" in lxml_err:
            return "XPath 表达式语法非法 (Invalid expression)"
        elif "Invalid predicate" in lxml_err:
            return "XPath 谓语语法非法 (Invalid predicate)"
        elif "Undefined namespace" in lxml_err:
            return "未定义的命名空间前缀"
        return f"XPath 语法错误: {lxml_err}"

    return None


# ==============================================================================
# 自动上下调整方框大小的多行代码/选择器输入框控件 (保持水平宽度不变)
# ==============================================================================

class AutoResizingTextEdit(QTextEdit):
    """
    自适应内容高度的选择器输入框：
    1. 默认上下高度更宽裕大气 (默认 min_height=54px，舒适展示 2~3 行，彻底解决原输入框过于扁窄局促的问题)；
    2. 上下高度根据填写内容、自动折行实时自由自适应撑高或回缩 (最高自适应至 180px)；
    3. 左右宽度由父级布局撑满，不发生左右拉伸调整；
    4. 纯文本模式 (setAcceptRichText(False))，支持 Enter 键直接触发查找 (returnPressed)，Shift+Enter 支持多行换行；
    5. 完美平替并兼容 QLineEdit 的常用 API (text, setText, setCursorPosition, setPlaceholderText 等)。
    """
    returnPressed = pyqtSignal()

    def __init__(self, min_height: int = 54, max_height: int = 180, parent=None):
        super().__init__(parent)
        self.min_height = min_height
        self.max_height = max_height
        self.setAcceptRichText(False)

        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # 优化文本框内边距，留白更宽松舒适
        doc = self.document()
        doc.setDocumentMargin(4)

        self.textChanged.connect(self.adjust_height)
        self.setFixedHeight(self.min_height)

    def text(self) -> str:
        """兼容 QLineEdit.text() 接口"""
        return self.toPlainText()

    def setText(self, text: str):
        """兼容 QLineEdit.setText() 接口"""
        self.setPlainText(text or "")
        self.adjust_height()

    def setCursorPosition(self, pos: int):
        """兼容 QLineEdit.setCursorPosition() 接口"""
        cursor = self.textCursor()
        cursor.setPosition(min(max(0, pos), len(self.toPlainText())))
        self.setTextCursor(cursor)

    def cursorPosition(self) -> int:
        """兼容 QLineEdit.cursorPosition() 接口"""
        return self.textCursor().position()

    def keyPressEvent(self, event: QKeyEvent):
        # 拦截普通回车键触发搜索，Shift+Enter 允许换行
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.returnPressed.emit()
                event.accept()
                return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_height()

    def adjust_height(self):
        """根据文档内容及当前视口宽度下的实际折行行数动态自适应调整上下高度，不影响左右宽度"""
        vw = self.viewport().width()
        if vw <= 0:
            vw = max(300, self.width() - 16)
        doc = self.document()
        doc.setTextWidth(float(vw))
        doc_height = doc.size().height()
        # 加上边框与内边距的余量 (约 14px)
        target_height = int(doc_height + 14)
        target_height = max(self.min_height, min(target_height, self.max_height))
        if self.height() != target_height:
            self.setFixedHeight(target_height)


# ==============================================================================
# 现代浅色高级感：Search for element 对话框
# ==============================================================================

class SearchElementDialog(QDialog):
    """
    全中文纯白轻奢定位搜索弹窗 (具备跨会话与窗口重开记忆模式)
    """
    element_picked = pyqtSignal(str)
    tap_requested = pyqtSignal(str)
    send_keys_requested = pyqtSignal(str, str)

    # 类级别跨会话记忆缓存 (按平台隔离记录上一次所选策略、填写的选择器与选中的节点)
    _MEMORY_STATE: Dict[str, Dict[str, Any]] = {}

    def __init__(self, flat_components: List[Dict[str, Any]], xml_root: Optional[ET.Element], comp_map: Optional[Dict[str, Dict[str, Any]]] = None, platform: str = "harmony", parent=None):
        if not isinstance(platform, str):
            parent = platform
            platform = "harmony"
        self.inspector = parent  # 保存审查器主视窗引用，保持数据双向联动
        # 核心架构改造：脱离父窗口的 Owned Window 绑定，以独立顶层窗口形态初始化
        # 这样 Windows 系统会将其识别为一个独立的顶层应用窗口，在任务栏同一个 App 图标下生成独立的缩略图卡片！
        super().__init__(None)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        # 移除静态全局 WindowStaysOnTopHint，改为应用内激活态动态置顶，避免切换到外部应用时遮挡其他软件
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowIcon(create_modern_app_icon())

        # 监听系统级应用前后台切换，实现仅在控制台应用内置顶
        app = QApplication.instance()
        if app:
            app.applicationStateChanged.connect(self._on_app_state_changed)
        self.platform = (platform or "harmony").lower()
        plat_map = {"harmony": "HarmonyOS NEXT", "android": "Android", "ios": "iOS"}
        plat_title = plat_map.get(self.platform, "多端统一")
        self.setWindowTitle(f"🔎 元素定位与查找器 ({plat_title})")
        self.resize(750, 560)
        self.flat_components = flat_components
        self.comp_map = comp_map or {}
        self.xml_root = xml_root
        self.matched_components: List[Dict[str, Any]] = []
        self.last_main_selected_comp: Optional[Dict[str, Any]] = None

        self.apply_theme()
        self.init_ui()
        self._load_memory()

    def apply_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; color: #1e293b; }
            QLabel { color: #334155; font-size: 13px; font-weight: 600; }
            QComboBox {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 4px 10px; font-size: 13px; min-height: 28px;
            }
            QComboBox:hover { border-color: #0284c7; }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 6px 10px; font-size: 13px; min-height: 28px;
                font-family: Consolas, "Segoe UI", monospace;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border: 1.5px solid #0284c7; }

            /* 统一标准按钮基类 (紧凑 28px 高度、圆角 6px、细边框白底黑字) */
            QPushButton {
                background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 14px; font-weight: 600; font-size: 12px; min-height: 28px;
            }
            QPushButton:hover {
                background-color: #f8fafc; border-color: #94a3b8; color: #0f172a;
            }
            QPushButton:pressed {
                background-color: #f1f5f9;
            }
            QPushButton:disabled {
                background-color: #f8fafc; color: #94a3b8; border: 1px solid #e2e8f0;
            }

            /* 执行查找 Primary 主按钮 (醒目高质感主题蓝，与界面设计系统同构) */
            QPushButton#btnSearchExec {
                background-color: #0284c7; color: #ffffff; border: 1px solid #0284c7;
                font-size: 12px; font-weight: 600; padding: 0 16px;
            }
            QPushButton#btnSearchExec:hover {
                background-color: #0369a1; border-color: #0369a1;
            }
            QPushButton#btnSearchExec:pressed {
                background-color: #075985;
            }

            /* 取消关闭按钮 */
            QPushButton#btnCancel {
                background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1;
            }
            QPushButton#btnCancel:hover {
                background-color: #f1f5f9; color: #0f172a; border-color: #94a3b8;
            }

            QListWidget {
                background-color: #f8fafc; border: 1px solid #e2e8f0;
                border-radius: 6px; color: #0f172a; font-family: Consolas, monospace;
            }
            QListWidget::item { padding: 9px; border-bottom: 1px solid #f1f5f9; min-height: 24px; }
            QListWidget::item:selected {
                background-color: #e0f2fe; color: #0369a1; border-radius: 4px; font-weight: bold;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        top_ctrl_bar = QHBoxLayout()
        lbl_strat = QLabel("定位策略 (Locator Strategy):")
        top_ctrl_bar.addWidget(lbl_strat)
        top_ctrl_bar.addStretch()

        self.chk_stay_on_top = QCheckBox("📌 保持置顶 (防遮挡)")
        self.chk_stay_on_top.setChecked(True)
        self.chk_stay_on_top.setToolTip("保持查找窗口在审查器内始终置顶防遮挡；切换至其他外部应用时自动让位，绝不遮挡其他应用")
        self.chk_stay_on_top.setStyleSheet("color: #0284c7; font-size: 12px; font-weight: 600;")
        self.chk_stay_on_top.toggled.connect(self._toggle_stay_on_top)
        top_ctrl_bar.addWidget(self.chk_stay_on_top)
        layout.addLayout(top_ctrl_bar)

        self.combo_strategy = QComboBox()
        self.combo_strategy.setFixedHeight(30)
        self.combo_strategy.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.combo_strategy)

        layout.addWidget(QLabel("选择器表达式 (Selector):"))
        sel_row = QHBoxLayout()
        # 核心：使用 AutoResizingTextEdit 随填写内容上下自适应调整输入框高度 (默认 54px，更大更宽裕，最高自适应撑开至 180px)，左右宽度由父布局撑满
        self.edit_selector = AutoResizingTextEdit(min_height=54, max_height=180)
        self.edit_selector.textChanged.connect(self._on_selector_text_changed)
        sel_row.addWidget(self.edit_selector, 1)

        self.btn_pick_current = QPushButton("🎯 填入主视窗选中元素")
        self.btn_pick_current.setFixedHeight(34)
        self.btn_pick_current.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick_current.setToolTip("将当前在真机画面或 DOM 树中选中的组件表达式快速填入输入框")
        self.btn_pick_current.clicked.connect(self.pick_current_element_to_input)
        sel_row.addWidget(self.btn_pick_current, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(sel_row)

        # 跟随主界面点击自动填充复选框
        self.chk_auto_pick = QCheckBox("💡 在主视窗点击真机或 DOM 树时，自动将推荐定位器填入上方输入框")
        self.chk_auto_pick.setChecked(False)
        self.chk_auto_pick.setStyleSheet("color: #475569; font-size: 12px;")
        layout.addWidget(self.chk_auto_pick)

        # 智能过滤被遮挡/未展开的隐藏层元素复选框
        self.chk_only_visible = QCheckBox("👁️ 仅匹配当前真实展示元素 (智能过滤被遮挡/未展开的隐藏层)")
        self.chk_only_visible.setChecked(True)
        self.chk_only_visible.setStyleSheet("color: #0369a1; font-size: 12px; font-weight: 600;")
        self.chk_only_visible.stateChanged.connect(self._on_only_visible_changed)
        layout.addWidget(self.chk_only_visible)

        # 构建策略下拉项并设置初始占位符与信号监听
        self._rebuild_strategies()
        self.combo_strategy.currentIndexChanged.connect(self._on_strategy_changed)

        btn_layout = QHBoxLayout()
        self.btn_search = QPushButton("🔍 查找匹配元素 (Search)")
        self.btn_search.setObjectName("btnSearchExec")
        self.btn_search.setFixedHeight(30)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self.do_search)
        self.edit_selector.returnPressed.connect(self.do_search)
        btn_layout.addWidget(self.btn_search)

        self.lbl_status = QLabel("就绪，请输入表达式或点击主视窗元素后点击查找")
        self.lbl_status.setStyleSheet("color: #0284c7; font-weight: 600;")
        btn_layout.addWidget(self.lbl_status, 1)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("匹配到的元素列表 (Elements Found):"))
        self.list_results = QListWidget()
        self.list_results.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_results, 1)

        bottom_box = QHBoxLayout()
        self.btn_tap = QPushButton("👆 点击该元素 (Tap)")
        self.btn_tap.setFixedHeight(30)
        self.btn_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tap.setEnabled(False)
        self.btn_tap.clicked.connect(self.on_tap_clicked)
        bottom_box.addWidget(self.btn_tap)

        self.btn_send_keys = QPushButton("⌨️ 输入文本内容 (Send Keys)")
        self.btn_send_keys.setFixedHeight(30)
        self.btn_send_keys.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_keys.setEnabled(False)
        self.btn_send_keys.clicked.connect(self.on_send_keys_clicked)
        bottom_box.addWidget(self.btn_send_keys)

        bottom_box.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setFixedHeight(30)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setObjectName("btnCancel")
        btn_close.clicked.connect(self.close)
        bottom_box.addWidget(btn_close)
        layout.addLayout(bottom_box)

    def _rebuild_strategies(self):
        """根据当前运行平台重建所支持的查找定位策略，并保持默认或记忆值"""
        self.combo_strategy.blockSignals(True)
        self.combo_strategy.clear()
        if self.platform == "android":
            self.combo_strategy.addItem("id (resource-id 标识)", "id")
            self.combo_strategy.addItem("xpath (XPath 路径表达式)", "xpath")
            self.combo_strategy.addItem("accessibility id (content-desc 文本或描述)", "accessibility id")
            self.combo_strategy.addItem("class name (组件类名)", "class name")
            self.combo_strategy.addItem("android uiautomator (UiSelector 语法表达式)", "uiautomator")
        elif self.platform == "ios":
            self.combo_strategy.addItem("id / accessibility id (name / label 标识)", "id")
            self.combo_strategy.addItem("xpath (XPath 路径表达式)", "xpath")
            self.combo_strategy.addItem("class name (XCUIElementType 组件类型)", "class name")
            self.combo_strategy.addItem("ios predicate string (谓词表达式)", "predicate")
            self.combo_strategy.addItem("ios class chain (类链表达式)", "class chain")
        else:
            self.combo_strategy.addItem("id (组件 Key / ID 标识 - By.id)", "id")
            self.combo_strategy.addItem("xpath (XPath 路径表达式)", "xpath")
            self.combo_strategy.addItem("text (文本内容 - By.text)", "text")
            self.combo_strategy.addItem("type / class name (ArkUI 组件类型名 - By.type)", "type")
            self.combo_strategy.addItem("description (无障碍描述 - By.description)", "description")

        self.combo_strategy.setCurrentIndex(0)
        self.combo_strategy.blockSignals(False)
        self.update_placeholder()

    def _on_strategy_changed(self):
        self.update_placeholder()
        self._save_memory()

    def _on_only_visible_changed(self):
        self._save_memory()
        if hasattr(self, "edit_selector") and self.edit_selector.text().strip():
            self.do_search()

    def _is_app_in_foreground(self) -> bool:
        """精准探测当前系统前台聚焦的窗口是否属于本审查器进程 (Win32 原生探测 + Qt 兜底)"""
        if sys.platform == "win32":
            try:
                import ctypes
                fg_hwnd = ctypes.windll.user32.GetForegroundWindow()
                if not fg_hwnd:
                    return False
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(fg_hwnd, ctypes.byref(pid))
                return pid.value == os.getpid()
            except Exception:
                pass
        app = QApplication.instance()
        return bool(app and app.applicationState() == Qt.ApplicationState.ApplicationActive)

    def _apply_native_topmost(self, on_top: bool):
        """
        动态应用或解除窗口置顶：
        - on_top 为 True：置顶于当前应用窗口上方，防止主视窗点击时被遮挡；
        - on_top 为 False：取消置顶并让位，绝不遮挡其他外部应用。
        """
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                HWND_TOPMOST = -1
                HWND_NOTOPMOST = -2
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                target = HWND_TOPMOST if on_top else HWND_NOTOPMOST
                ctypes.windll.user32.SetWindowPos(hwnd, target, 0, 0, 0, 0, flags)

                # 切换至外部应用时，主动将自身排在外部前台窗口之后
                if not on_top:
                    fg = ctypes.windll.user32.GetForegroundWindow()
                    if fg and fg != hwnd:
                        ctypes.windll.user32.SetWindowPos(hwnd, fg, 0, 0, 0, 0, flags)
                return
            except Exception as e:
                logger.debug(f"Win32 SetWindowPos 调度异常: {e}")

        # 跨平台 Qt 兜底
        flags = self.windowFlags()
        if on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        if self.windowFlags() != flags:
            was_visible = self.isVisible()
            self.setWindowFlags(flags)
            if was_visible:
                self.show()

    def _update_stay_on_top_state(self):
        """核心调度：综合置顶开关与当前前台进程状态，动态判定是否置顶"""
        if not hasattr(self, "chk_stay_on_top"):
            return
        if not self.chk_stay_on_top.isChecked() or not self.isVisible():
            self._apply_native_topmost(False)
            return

        is_active = self._is_app_in_foreground()
        self._apply_native_topmost(is_active)

    def _toggle_stay_on_top(self, checked: bool):
        self._save_memory()
        self._update_stay_on_top_state()
        if checked:
            self.raise_()
            self.activateWindow()

    def _on_app_state_changed(self, state: Qt.ApplicationState):
        """系统级应用状态变化监听：切到外部应用时立即让位，切回本应用时恢复置顶"""
        self._update_stay_on_top_state()

    def changeEvent(self, event: QEvent):
        """窗口激活状态变化监听"""
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange:
            self._update_stay_on_top_state()

    def showEvent(self, event):
        """窗口展示时按需激活置顶"""
        super().showEvent(event)
        self._update_stay_on_top_state()

    def _save_memory(self):
        if not hasattr(self, "combo_strategy") or not hasattr(self, "edit_selector"):
            return
        cur_node_id = None
        if hasattr(self, "list_results"):
            curr = self.list_results.currentItem()
            if curr:
                cur_node_id = curr.data(Qt.ItemDataRole.UserRole)
        self._MEMORY_STATE[self.platform] = {
            "strategy": self.combo_strategy.currentData(),
            "selector": self.edit_selector.text(),
            "selected_node_id": cur_node_id,
            "only_visible": self.chk_only_visible.isChecked() if hasattr(self, "chk_only_visible") else True,
            "stay_on_top": self.chk_stay_on_top.isChecked() if hasattr(self, "chk_stay_on_top") else True,
        }

    def _on_selector_text_changed(self):
        """输入框内容改变时自动记忆，并即时清除错误警示框与重置状态"""
        self._save_memory()
        if hasattr(self, "edit_selector"):
            self.edit_selector.setStyleSheet("")
        if hasattr(self, "lbl_status") and self.lbl_status.text().startswith("⚠️"):
            self.lbl_status.setText("就绪，点击查找或按回车开始匹配")
            self.lbl_status.setStyleSheet("color: #0284c7; font-weight: 600;")

    def show_syntax_error(self, err_msg: str, example: str = ""):
        """
        统一展示选择器语法错误：
        状态栏红色醒目警告 + 列表结构化错误诊断项 + 输入框红框标记，杜绝静默失败与误导性“匹配到0个元素”
        """
        if hasattr(self, "lbl_status"):
            self.lbl_status.setText(f"⚠️ 语法错误: {err_msg}")
            self.lbl_status.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 13px;")
        if hasattr(self, "edit_selector"):
            self.edit_selector.setStyleSheet("border: 1.5px solid #ef4444; border-radius: 6px; background-color: #fef2f2;")

        self.list_results.clear()

        # 错误说明卡片
        err_item = QListWidgetItem(f"❌ 表达式语法错误: {err_msg}")
        err_item.setForeground(QColor("#b91c1c"))
        err_item.setBackground(QBrush(QColor("#fee2e2")))
        err_item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.list_results.addItem(err_item)

        # 规范指引与示例卡片
        if example:
            tip_item = QListWidgetItem(f"💡 正确语法示例: {example}")
            tip_item.setForeground(QColor("#0369a1"))
            tip_item.setBackground(QBrush(QColor("#f0f9ff")))
            tip_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(tip_item)
        else:
            tip_item = QListWidgetItem("💡 提示: 请检查标签名、属性格式 [@attr='值']、方括号/引号是否配对闭合")
            tip_item.setForeground(QColor("#475569"))
            tip_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(tip_item)

        self.list_results.setUpdatesEnabled(True)
        self.btn_tap.setEnabled(False)
        self.btn_send_keys.setEnabled(False)

    def _load_memory(self):
        saved = self._MEMORY_STATE.get(self.platform, {})
        saved_strat = saved.get("strategy")
        if saved_strat:
            idx = self.combo_strategy.findData(saved_strat)
            if idx >= 0:
                self.combo_strategy.setCurrentIndex(idx)

        saved_sel = saved.get("selector", "")
        if saved_sel:
            self.edit_selector.setText(saved_sel)
            self.edit_selector.setCursorPosition(len(saved_sel))

        if hasattr(self, "chk_only_visible"):
            saved_vis = saved.get("only_visible", True)
            self.chk_only_visible.blockSignals(True)
            self.chk_only_visible.setChecked(saved_vis)
            self.chk_only_visible.blockSignals(False)

        if hasattr(self, "chk_stay_on_top"):
            saved_top = saved.get("stay_on_top", True)
            self.chk_stay_on_top.blockSignals(True)
            self.chk_stay_on_top.setChecked(saved_top)
            self.chk_stay_on_top.blockSignals(False)
            self._update_stay_on_top_state()

        # 彻底移除打开窗口时的自动 do_search()，让界面清爽呈现，不自动定位
        self.lbl_status.setText("就绪，请输入表达式或点击主视窗元素后点击查找")

    def update_context(self, flat_components: List[Dict[str, Any]], xml_root: Optional[ET.Element], comp_map: Optional[Dict[str, Dict[str, Any]]] = None, platform: str = "harmony"):
        """动态刷新真机现场数据，保持已填写和选择的内容不变"""
        new_platform = (platform or "harmony").lower()
        platform_changed = (new_platform != self.platform)
        self.platform = new_platform
        self.flat_components = flat_components
        if comp_map is not None:
            self.comp_map = comp_map
        self.xml_root = xml_root

        if platform_changed:
            plat_map = {"harmony": "HarmonyOS NEXT", "android": "Android", "ios": "iOS"}
            plat_title = plat_map.get(self.platform, "多端统一")
            self.setWindowTitle(f"🔎 元素定位与查找器 ({plat_title})")
            self._rebuild_strategies()
            self._load_memory()
        else:
            self.lbl_status.setText("真机数据已同步，点击【查找】重新匹配")

    def sync_element_from_main(self, comp: Dict[str, Any]):
        """主界面点击真机画面或 DOM 树时实时联动"""
        self.last_main_selected_comp = comp
        if hasattr(self, "chk_auto_pick") and self.chk_auto_pick.isChecked():
            self.pick_current_element_to_input()
        else:
            c_tag = comp.get("type", "Component")
            c_bounds = f"[{comp.get('left')},{comp.get('top')}][{comp.get('right')},{comp.get('bottom')}]"
            self.lbl_status.setText(f"主视窗已选中: <{c_tag} bounds=\"{c_bounds}\"> (点击【🎯 填入主视窗选中元素】)")

    def pick_current_element_to_input(self):
        """将主视窗当前选中的组件推荐表达式填入选择器输入框"""
        comp = getattr(self, "last_main_selected_comp", None)
        if not comp:
            self.lbl_status.setText("提示: 请先在主视窗点击选中任意真机或 DOM 树元素")
            return

        rec_xp = comp.get("rec_xpath") or comp.get("xpath") or ""
        rec_id = comp.get("id") or ""
        rec_text = comp.get("text") or ""
        rec_type = comp.get("type") or ""
        curr_strat = self.combo_strategy.currentData()

        if curr_strat == "id" and rec_id:
            self.edit_selector.setText(rec_id)
        elif curr_strat == "text" and rec_text:
            self.edit_selector.setText(rec_text)
        elif curr_strat in ("type", "class name") and rec_type:
            self.edit_selector.setText(rec_type)
        else:
            # 默认切换至最通用的 XPath 策略并填入推荐表达式
            xp_idx = self.combo_strategy.findData("xpath")
            if xp_idx >= 0:
                self.combo_strategy.setCurrentIndex(xp_idx)
            if rec_xp:
                self.edit_selector.setText(rec_xp)

        self.lbl_status.setText(f"已同步 <{comp.get('type')}> 推荐表达式，点击【查找】验证")

    def closeEvent(self, event):
        self._save_memory()
        super().closeEvent(event)

    def accept(self):
        self._save_memory()
        super().accept()

    def update_placeholder(self):
        if not hasattr(self, "edit_selector"):
            return
        strategy = self.combo_strategy.currentData()
        if self.platform == "android":
            tips = {
                "id": "例如: com.example.app:id/btn_send 或 login_btn",
                "xpath": "例如: //android.widget.Button[@text='发送']",
                "accessibility id": "例如: 发送 (对应 content-desc 描述)",
                "class name": "例如: android.widget.Button 或 TextView",
                "uiautomator": "例如: text(\"发送\") 或 description(\"返回\")",
            }
        elif self.platform == "ios":
            tips = {
                "id": "例如: login_button 或 send_btn (Accessibility Identifier/Name)",
                "xpath": "例如: //XCUIElementTypeButton[@name='发送']",
                "class name": "例如: XCUIElementTypeButton 或 XCUIElementTypeStaticText",
                "predicate": "例如: label == '发送' AND visible == 1",
                "class chain": "例如: **/XCUIElementTypeButton[`name == '发送'`]",
            }
        else:  # harmony
            tips = {
                "id": "例如: login_button 或 send_btn (ArkUI key/id 标识)",
                "xpath": "例如: //Button[@text='发送'] 或 //Text[@text='925']",
                "text": "例如: 发送 或 925 (匹配组件展示文本)",
                "type": "例如: Button 或 Text 或 TextInput (ArkUI 类型)",
                "description": "例如: 无障碍描述文本",
            }
        self.edit_selector.setPlaceholderText(tips.get(strategy, "请输入定位选择器表达式"))

    def do_search(self):
        # 执行前主动校验并对齐父级主窗口的最新 XML 与组件映射树，防止跨生命周期串位
        parent_win = self.parent()
        if parent_win and hasattr(parent_win, "xml_root") and parent_win.xml_root is not None:
            self.xml_root = parent_win.xml_root
            if hasattr(parent_win, "comp_map"):
                self.comp_map = parent_win.comp_map
            if hasattr(parent_win, "flat_components"):
                self.flat_components = parent_win.flat_components

        strategy = self.combo_strategy.currentData()
        val = self.edit_selector.text().strip()
        self.list_results.setUpdatesEnabled(False)
        self.list_results.clear()
        self.matched_components.clear()
        self.btn_tap.setEnabled(False)
        self.btn_send_keys.setEnabled(False)

        # 默认恢复输入框正常边框与状态栏主题色
        self.edit_selector.setStyleSheet("")
        self.lbl_status.setStyleSheet("color: #0284c7; font-weight: 600;")

        if not val:
            self.list_results.setUpdatesEnabled(True)
            self.lbl_status.setText("请输入有效的定位表达式")
            return

        # 1. 严格语法静态校验与前置拦截 (杜绝语法错误时伪装成“匹配到 0 个元素”)
        syntax_err = None
        example_str = ""
        if strategy == "xpath":
            syntax_err = validate_xpath_syntax(val)
            example_str = "//Text[@text='会员中心'] 或 //Button[contains(@text, '发送')]"
        elif strategy == "id":
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到 XPath 路径语法特征；当前策略为 [id]，若要使用路径定位请切换策略为 [xpath]"
                example_str = "login_button 或 send_btn 或 com.santiao.im:id/btn_send"
            elif val.startswith("@"):
                syntax_err = "ID 选择器无需添加 '@' 前缀；请直接输入组件 ID 或 Key"
                example_str = val.lstrip("@")
            elif " " in val:
                syntax_err = "组件 ID 标识通常不包含空格；若要根据展示文本匹配，请将策略切换为 [text]"
                example_str = val.replace(" ", "_")
        elif strategy == "text":
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到 XPath 表达式语法；当前策略为 [text] 纯文本匹配，请直接输入文本内容"
                m_txt = re.findall(r"['\"](.*?)['\"]", val)
                example_str = m_txt[0] if m_txt else "测试0225"
            elif val.startswith("@text="):
                syntax_err = "无需添加 '@text=' 前缀；当前策略为纯文本内容匹配，直接输入文本即可"
                example_str = val.replace("@text=", "").strip("'\"")
            elif re.match(r"^text\s*\(", val):
                syntax_err = "当前策略为纯文本匹配，无需使用 text(...) 函数包裹"
                m_txt = re.findall(r"['\"](.*?)['\"]", val)
                example_str = m_txt[0] if m_txt else "设置"
        elif strategy in ("type", "class name"):
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到路径语法；当前策略为 [type/class name] 组件类型匹配，无需斜杠或方括号"
                clean_type = re.sub(r"[^a-zA-Z0-9_]", "", val.split("/")[-1].split("[")[0])
                example_str = clean_type or "Button 或 Text 或 ListItem"
            elif any(ch in val for ch in ("@", "=", "(", ")")):
                syntax_err = "组件类型名不能包含 '@'、'=' 或括号；请输入标准的组件类型名称"
                example_str = "Button 或 TextInput 或 Column"
        elif strategy in ("description", "accessibility id"):
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到 XPath 语法特征；当前策略为无障碍描述匹配，请直接输入描述文本"
                example_str = "返回 或 关闭"
        elif strategy == "uiautomator":
            if val.count('"') % 2 != 0 or val.count("'") % 2 != 0 or val.count("(") != val.count(")"):
                syntax_err = "UiAutomator 表达式引号或括号未正确闭合"
                example_str = 'new UiSelector().text("设置") 或 text("设置")'
        elif strategy == "predicate":
            if val.count('"') % 2 != 0 or val.count("'") % 2 != 0:
                syntax_err = "Predicate 表达式字符串引号未闭合"
                example_str = 'label == "设置" 或 name CONTAINS "btn"'
        elif strategy == "class chain":
            if val.count("[") != val.count("]"):
                syntax_err = "Class Chain 表达式方括号 '[' 与 ']' 未正确闭合"
                example_str = '**/XCUIElementTypeButton[`label == "确定"`]'

        if syntax_err:
            self.show_syntax_error(syntax_err, example=example_str)
            return

        matched = []
        val_lower = val.lower()
        try:
            if strategy == "id":
                for c in self.flat_components:
                    cid = c.get("id", "")
                    raw_id = c.get("raw_attributes", {}).get("resource-id", "") or c.get("raw_attributes", {}).get("name", "")
                    if (cid and (val_lower == cid.lower() or val_lower in cid.lower())) or \
                       (raw_id and (val_lower == raw_id.lower() or val_lower in raw_id.lower())):
                        matched.append(c)
            elif strategy == "accessibility id":
                for c in self.flat_components:
                    text = c.get("text", "")
                    desc = c.get("raw_attributes", {}).get("description", "") or c.get("raw_attributes", {}).get("content-desc", "")
                    name = c.get("raw_attributes", {}).get("name", "") or c.get("raw_attributes", {}).get("label", "")
                    if (text and val_lower in text.lower()) or (desc and val_lower in desc.lower()) or (name and val_lower in name.lower()):
                        matched.append(c)
            elif strategy in ("class name", "type"):
                for c in self.flat_components:
                    ctype = c.get("type", "")
                    if ctype.lower() == val_lower or val_lower in ctype.lower():
                        matched.append(c)
            elif strategy == "text":
                for c in self.flat_components:
                    text = c.get("text", "") or c.get("raw_attributes", {}).get("text", "") or c.get("raw_attributes", {}).get("label", "")
                    if text and (val_lower == text.lower() or val_lower in text.lower()):
                        matched.append(c)
            elif strategy == "description":
                for c in self.flat_components:
                    desc = c.get("raw_attributes", {}).get("description", "") or c.get("raw_attributes", {}).get("content-desc", "")
                    if desc and (val_lower == desc.lower() or val_lower in desc.lower()):
                        matched.append(c)
            elif strategy == "uiautomator":
                m_text = re.search(r'text(?:Contains)?\s*\(\s*["\']([^"\']+)["\']\s*\)', val, re.IGNORECASE)
                m_desc = re.search(r'description(?:Contains)?\s*\(\s*["\']([^"\']+)["\']\s*\)', val, re.IGNORECASE)
                m_id = re.search(r'resourceId(?:Matches)?\s*\(\s*["\']([^"\']+)["\']\s*\)', val, re.IGNORECASE)
                m_cls = re.search(r'className\s*\(\s*["\']([^"\']+)["\']\s*\)', val, re.IGNORECASE)
                target_t = m_text.group(1).lower() if m_text else None
                target_d = m_desc.group(1).lower() if m_desc else None
                target_i = m_id.group(1).lower() if m_id else None
                target_c = m_cls.group(1).lower() if m_cls else None
                for c in self.flat_components:
                    c_text = c.get("text", "").lower()
                    c_desc = str(c.get("raw_attributes", {}).get("content-desc", "")).lower()
                    c_id = c.get("id", "").lower()
                    c_type = c.get("type", "").lower()
                    if target_t and target_t not in c_text:
                        continue
                    if target_d and target_d not in c_desc:
                        continue
                    if target_i and target_i not in c_id:
                        continue
                    if target_c and target_c != c_type and target_c not in c_type:
                        continue
                    if not any([target_t, target_d, target_i, target_c]):
                        if val_lower not in c_text and val_lower not in c_desc and val_lower not in c_id:
                            continue
                    matched.append(c)
            elif strategy == "predicate":
                m_label = re.search(r'label\s*(?:==|CONTAINS|like)\s*["\']([^"\']+)["\']', val, re.IGNORECASE)
                m_name = re.search(r'name\s*(?:==|CONTAINS|like)\s*["\']([^"\']+)["\']', val, re.IGNORECASE)
                m_type = re.search(r'type\s*(?:==|CONTAINS|like)\s*["\']([^"\']+)["\']', val, re.IGNORECASE)
                target_l = m_label.group(1).lower() if m_label else None
                target_n = m_name.group(1).lower() if m_name else None
                target_t = m_type.group(1).lower() if m_type else None
                for c in self.flat_components:
                    c_label = str(c.get("raw_attributes", {}).get("label", "") or c.get("text", "")).lower()
                    c_name = str(c.get("raw_attributes", {}).get("name", "") or c.get("id", "")).lower()
                    c_type = c.get("type", "").lower()
                    if target_l and target_l not in c_label:
                        continue
                    if target_n and target_n not in c_name:
                        continue
                    if target_t and target_t not in c_type:
                        continue
                    if not any([target_l, target_n, target_t]):
                        if val_lower not in c_label and val_lower not in c_name:
                            continue
                    matched.append(c)
            elif strategy == "class chain":
                clean_chain = val.replace("**/", "").replace("/*", "").strip()
                chain_type = clean_chain.split("[")[0].strip() if "[" in clean_chain else clean_chain
                chain_type_lower = chain_type.lower()
                for c in self.flat_components:
                    c_type = c.get("type", "").lower()
                    if chain_type and chain_type != "*" and chain_type_lower not in c_type:
                        continue
                    matched.append(c)
            elif strategy == "xpath":
                matched = self.match_xpath(val)
        except Exception as e:
            # 捕获运行时 XPath/选择器语法解析或求值异常，立即以红字警告呈现给用户
            err_text = str(e)
            if err_text.startswith("XPath 语法错误:"):
                err_text = err_text.replace("XPath 语法错误:", "").strip()
            self.show_syntax_error(err_text, example=example_str)
            return

        total_matched_raw = len(matched)
        if hasattr(self, "chk_only_visible") and self.chk_only_visible.isChecked():
            matched = [c for c in matched if not c.get("is_occluded", False) and c.get("is_exposed", True)]

        self.matched_components = matched
        if total_matched_raw != len(matched):
            self.lbl_status.setText(f"匹配到 {len(matched)} 个真实展示元素 (智能过滤 {total_matched_raw - len(matched)} 个被遮挡层)")
        else:
            self.lbl_status.setText(f"匹配到 {len(matched)} 个元素")

        if not matched:
            strat_tips = {
                "id": "建议核对组件 Key/ID 属性是否存在，或切换为 [text] / [xpath] 策略重试",
                "xpath": "建议核对标签名大小写、属性值及层级，或点击【🎯 填入主视窗选中元素】获取推荐路径",
                "text": "建议核对文本大小写、去除首尾空格，或取消勾选【仅匹配当前真实展示元素】重试",
                "type": "未找到该类型的组件，请核对组件类型拼写 (如 Button、Text、ListItem、Flex)",
                "class name": "未找到该类型的组件，请核对类型名拼写",
                "description": "未找到包含该无障碍描述的组件，请检查 accessibility 属性设置",
                "accessibility id": "未找到包含该描述的组件，请检查 content-desc / label 属性",
            }
            tip_detail = strat_tips.get(strategy, "请核对选择器表达式与当前真机画面组件是否匹配")
            strat_label = self.combo_strategy.currentText().split(" ")[0]
            item = QListWidgetItem(f"⚠️ 未找到任何符合条件的元素 (策略: {strat_label})")
            item.setForeground(QColor("#d97706"))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(item)

            tip_item = QListWidgetItem(f"💡 查找建议: {tip_detail}")
            tip_item.setForeground(QColor("#0369a1"))
            tip_item.setBackground(QBrush(QColor("#f0f9ff")))
            tip_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(tip_item)

            self.list_results.setUpdatesEnabled(True)
            return

        # 限制列表项最多渲染 200 条，杜绝海量渲染卡死
        render_limit = 200
        for idx, comp in enumerate(matched[:render_limit]):
            c_scheme = get_dom_tag_color(comp.get("type", ""))
            title = f"元素 {idx + 1} - <{comp['type']}"
            if comp.get('id'):
                title += f" id=\"{comp['id']}\""
            if comp.get('text'):
                title += f" text=\"{comp['text']}\""
            title += f" bounds=\"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]\">"
            list_item = QListWidgetItem(title)
            list_item.setData(Qt.ItemDataRole.UserRole, comp["node_id"])
            list_item.setForeground(QColor(c_scheme["text"]))
            list_item.setBackground(QBrush(QColor(c_scheme["bg"])))
            self.list_results.addItem(list_item)

        if len(matched) > render_limit:
            tip_item = QListWidgetItem(f"... 已截断显示前 {render_limit} 条匹配项 (共 {len(matched)} 条)")
            tip_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(tip_item)

        self.list_results.setUpdatesEnabled(True)
        self.list_results.setCurrentRow(0)
        self.on_item_clicked(self.list_results.item(0))
        self._save_memory()

    def _extract_comps_from_xml_nodes(self, nodes: List[Any]) -> List[Dict[str, Any]]:
        """从匹配到的 XML 节点列表中精确映射组件详情"""
        matched = []
        matched_ids = set()
        for elem in nodes:
            if not hasattr(elem, "attrib"):
                continue
            node_id = elem.attrib.get("node_id")
            if not node_id or node_id in matched_ids:
                continue
            matched_ids.add(node_id)

            comp = self.comp_map.get(node_id) if hasattr(self, "comp_map") and self.comp_map else None
            if not comp:
                for c in self.flat_components:
                    if c.get("node_id") == node_id:
                        comp = c
                        break
            if comp:
                elem_tag = getattr(elem, "tag", "")
                comp_type = comp.get("type", "")
                if elem_tag and comp_type and elem_tag != "Component":
                    if elem_tag.lower() != comp_type.lower():
                        continue
                matched.append(comp)
        return matched

    def _evaluate_xpath_natively(self, root_elem: ET.Element, xp: str) -> List[ET.Element]:
        """
        纯 Python 零外部依赖原生 XPath 引擎：
        支持多步骤遍历、// 与 /、轴定位 (following-sibling::, preceding-sibling::, parent::, ancestor::)、
        [@attr='val']、[contains(@attr, 'val')]、[contains(text(), 'val')] 与数字索引 [1], [last()]
        """
        # 1. 建立节点与父节点双向关系映射表 (用于支持兄弟与祖先轴导航)
        parent_map: Dict[ET.Element, ET.Element] = {}
        for p in root_elem.iter():
            for c in p:
                parent_map[c] = p

        clean_xp = xp.strip().strip("()")

        # 支持顶层联合操作符 '|' (Union Operator) 分支求值与合并
        if "|" in clean_xp:
            u_parts: List[str] = []
            u_buf: List[str] = []
            u_b_level = 0
            u_p_level = 0
            u_in_sq = False
            u_in_dq = False
            for ch in clean_xp:
                if ch == "'" and not u_in_dq:
                    u_in_sq = not u_in_sq
                    u_buf.append(ch)
                elif ch == '"' and not u_in_sq:
                    u_in_dq = not u_in_dq
                    u_buf.append(ch)
                elif not u_in_sq and not u_in_dq:
                    if ch == '[':
                        u_b_level += 1
                        u_buf.append(ch)
                    elif ch == ']':
                        u_b_level = max(0, u_b_level - 1)
                        u_buf.append(ch)
                    elif ch == '(':
                        u_p_level += 1
                        u_buf.append(ch)
                    elif ch == ')':
                        u_p_level = max(0, u_p_level - 1)
                        u_buf.append(ch)
                    elif ch == '|' and u_b_level == 0 and u_p_level == 0:
                        u_parts.append("".join(u_buf).strip())
                        u_buf = []
                    else:
                        u_buf.append(ch)
                else:
                    u_buf.append(ch)
            u_parts.append("".join(u_buf).strip())

            if len(u_parts) > 1:
                merged_nodes: List[ET.Element] = []
                seen_node_ids = set()
                for sub_xp in u_parts:
                    if sub_xp:
                        sub_res = self._evaluate_xpath_natively(root_elem, sub_xp)
                        for n_elem in sub_res:
                            elem_key = id(n_elem)
                            if elem_key not in seen_node_ids:
                                seen_node_ids.add(elem_key)
                                merged_nodes.append(n_elem)
                return merged_nodes

        # 2. 词法拆解多步骤路径 (解析 // 与 /，严格避免拆开中括号内与双冒号语法)
        steps: List[Tuple[str, str]] = []
        i = 0
        n = len(clean_xp)
        current_op = "//" if clean_xp.startswith("//") else ("/" if clean_xp.startswith("/") else "//")
        if clean_xp.startswith("//"):
            i = 2
        elif clean_xp.startswith("/"):
            i = 1

        buf = []
        bracket_level = 0
        while i < n:
            ch = clean_xp[i]
            if ch == '[':
                bracket_level += 1
                buf.append(ch)
                i += 1
            elif ch == ']':
                bracket_level = max(0, bracket_level - 1)
                buf.append(ch)
                i += 1
            elif bracket_level == 0 and clean_xp[i:i+2] == "//":
                seg = "".join(buf).strip()
                if seg:
                    steps.append((current_op, seg))
                current_op = "//"
                buf = []
                i += 2
            elif bracket_level == 0 and clean_xp[i:i+1] == "/":
                seg = "".join(buf).strip()
                if seg:
                    steps.append((current_op, seg))
                current_op = "/"
                buf = []
                i += 1
            else:
                buf.append(ch)
                i += 1

        last_seg = "".join(buf).strip()
        if last_seg:
            steps.append((current_op, last_seg))

        if not steps:
            return []

        # 3. 从根节点开始进行多步骤管道过滤
        current_nodes: List[ET.Element] = [root_elem]

        for op, step_str in steps:
            axis_name = ""
            tag_and_pred = step_str
            if "::" in step_str:
                axis_parts = step_str.split("::", 1)
                axis_name = axis_parts[0].strip().lower()
                tag_and_pred = axis_parts[1].strip()

            m = re.match(r"^([a-zA-Z0-9_\-\*]+|\.\.|\.|node\(\)|text\(\))(.*)$", tag_and_pred)
            if not m:
                raise ValueError(f"步进 '{step_str}' 节点名称格式非法")
            tag_name, predicate_str = m.group(1), m.group(2)
            if predicate_str and predicate_str.strip() and not predicate_str.strip().startswith("["):
                raise ValueError(f"节点 '{tag_name}' 后面存在未用方括号 '[]' 包裹的非法字符或空格: '{predicate_str.strip()}'")
            tag_lower = tag_name.lower()

            next_nodes: List[ET.Element] = []

            for node in current_nodes:
                candidates: List[ET.Element] = []
                if axis_name == "following-sibling":
                    p = parent_map.get(node)
                    if p is not None:
                        siblings = list(p)
                        try:
                            curr_idx = siblings.index(node)
                            candidates = siblings[curr_idx + 1:]
                        except ValueError:
                            pass
                elif axis_name == "preceding-sibling":
                    p = parent_map.get(node)
                    if p is not None:
                        siblings = list(p)
                        try:
                            curr_idx = siblings.index(node)
                            candidates = siblings[:curr_idx]
                        except ValueError:
                            pass
                elif axis_name == "parent":
                    p = parent_map.get(node)
                    if p is not None:
                        candidates = [p]
                elif axis_name == "ancestor":
                    curr_p = parent_map.get(node)
                    while curr_p is not None:
                        candidates.append(curr_p)
                        curr_p = parent_map.get(curr_p)
                else:
                    if op == "/":
                        candidates = list(node)
                    else:  # '//'
                        candidates = list(node.iter())
                        if node in candidates:
                            candidates.remove(node)

                # 按标签类型初筛
                filtered_by_tag = []
                for cand in candidates:
                    if tag_name == "*" or cand.tag.lower() == tag_lower:
                        filtered_by_tag.append(cand)

                # 按谓词过滤 (支持嵌套方括号、子路径谓词断言、属性与数字索引)
                if predicate_str:
                    pred_list = []
                    p_buf = []
                    p_depth = 0
                    p_in_sq = False
                    p_in_dq = False
                    for ch in predicate_str:
                        if ch == "'" and not p_in_dq:
                            p_in_sq = not p_in_sq
                            p_buf.append(ch)
                        elif ch == '"' and not p_in_sq:
                            p_in_dq = not p_in_dq
                            p_buf.append(ch)
                        elif not p_in_sq and not p_in_dq:
                            if ch == '[':
                                if p_depth > 0:
                                    p_buf.append(ch)
                                p_depth += 1
                            elif ch == ']':
                                p_depth -= 1
                                if p_depth == 0:
                                    pred_list.append("".join(p_buf).strip())
                                    p_buf = []
                                else:
                                    p_buf.append(ch)
                            else:
                                if p_depth > 0:
                                    p_buf.append(ch)
                        else:
                            p_buf.append(ch)

                    cand_results = filtered_by_tag
                    for pred in pred_list:
                        pred = pred.strip()
                        if not pred:
                            continue
                        if pred.isdigit():
                            idx = int(pred) - 1
                            cand_results = [cand_results[idx]] if 0 <= idx < len(cand_results) else []
                            continue
                        if pred == "last()":
                            cand_results = [cand_results[-1]] if cand_results else []
                            continue

                        pred_matched = []
                        for el in cand_results:
                            attrs = el.attrib
                            # 1. contains(@attr, 'val') 或 contains(text(), 'val')
                            m_contains = re.match(r"^contains\s*\(\s*(@[a-zA-Z0-9_\-]+|text\(\))\s*,\s*['\"](.*?)['\"]\s*\)$", pred, re.IGNORECASE)
                            if m_contains:
                                target_k, target_v = m_contains.group(1), m_contains.group(2)
                                if target_k == "text()":
                                    actual_val = attrs.get("text", "") or attrs.get("label", "") or (el.text or "")
                                else:
                                    actual_val = attrs.get(target_k[1:], "")
                                if target_v in str(actual_val):
                                    pred_matched.append(el)
                                continue

                            # 2. @attr='val' 或 @attr="val"
                            m_eq = re.match(r"^@([a-zA-Z0-9_\-]+)\s*=\s*['\"](.*?)['\"]$", pred)
                            if m_eq:
                                attr_k, attr_v = m_eq.group(1), m_eq.group(2)
                                actual_v = attrs.get(attr_k, "")
                                if not actual_v and attr_k in ("id", "resource-id", "name"):
                                    actual_v = attrs.get("id") or attrs.get("resource-id") or attrs.get("name") or ""
                                elif not actual_v and attr_k in ("text", "label", "value"):
                                    actual_v = attrs.get("text") or attrs.get("label") or attrs.get("value") or ""
                                if str(actual_v) == attr_v:
                                    pred_matched.append(el)
                                continue

                            # 3. [@id] 存在性过滤
                            if pred.startswith("@"):
                                if pred[1:] in attrs and attrs[pred[1:]]:
                                    pred_matched.append(el)
                                continue

                            # 4. 子路径或后代节点断言 (支持如 [.//Text[@text='测试0225']] 或 [Row//Text])
                            if pred.startswith((".", "//", "/")):
                                try:
                                    sub_res = self._evaluate_xpath_natively(el, pred)
                                    if sub_res:
                                        pred_matched.append(el)
                                except Exception:
                                    pass
                                continue

                            # 5. 子元素标签名存在性过滤：例如 //Stack[Search]
                            if any(sub.tag.lower() == pred.lower() for sub in el.iter() if sub is not el):
                                pred_matched.append(el)
                                continue

                            # 严格剔除不满足谓语条件的候选节点，禁止兜底放行

                        cand_results = pred_matched
                    next_nodes.extend(cand_results)
                else:
                    next_nodes.extend(filtered_by_tag)

            # 去重但保持先后顺序
            seen = set()
            dedup_nodes = []
            for n_elem in next_nodes:
                elem_id = id(n_elem)
                if elem_id not in seen:
                    seen.add(elem_id)
                    dedup_nodes.append(n_elem)
            current_nodes = dedup_nodes

        return current_nodes

    def match_xpath(self, xpath: str) -> List[Dict[str, Any]]:
        xp = xpath.strip()
        matched = []
        if not xp:
            return matched

        # 0. 静态语法预校验（确保任何独立调用 match_xpath 时都能获得语法诊断）
        syntax_err = validate_xpath_syntax(xp)
        if syntax_err:
            raise ValueError(syntax_err)

        # 1. 优先尝试使用 lxml（若用户环境中已安装 lxml）
        has_lxml = False
        try:
            from lxml import etree
            has_lxml = True
        except (ImportError, ModuleNotFoundError):
            has_lxml = False

        if has_lxml and self.xml_root is not None:
            try:
                xml_bytes = ET.tostring(self.xml_root, encoding="utf-8")
                ltree = etree.fromstring(xml_bytes)
                matched_nodes = ltree.xpath(xp)
                if isinstance(matched_nodes, list):
                    return self._extract_comps_from_xml_nodes(matched_nodes)
            except Exception as e:
                err_str = str(e)
                if "XPathSyntaxError" in type(e).__name__ or "XPathEvalError" in type(e).__name__ or "Invalid" in err_str:
                    raise ValueError(f"XPath 语法错误: {err_str}")
                logger.warning(f"lxml 解析异常: {e}，自动降级至内置原生 XPath 引擎")

        # 2. 内置原生无依赖标准库引擎：使用 Python 标准库 xml.etree.ElementTree
        if self.xml_root is not None:
            try:
                et_xp = xp
                if et_xp.startswith("//"):
                    et_xp = "." + et_xp
                elif not et_xp.startswith("."):
                    et_xp = ".//" + et_xp

                nodes = self.xml_root.findall(et_xp)
                if nodes:
                    res = self._extract_comps_from_xml_nodes(nodes)
                    if res:
                        return res
            except Exception:
                pass

            # 3. 智能原生 XPath 多步骤增强求值器 (完整支持 following-sibling::, preceding-sibling::, parent::, contains, 索引等)
            try:
                custom_nodes = self._evaluate_xpath_natively(self.xml_root, xp)
                if custom_nodes:
                    return self._extract_comps_from_xml_nodes(custom_nodes)
            except Exception as e:
                raise ValueError(str(e))

            # 核心防御：若当前界面 XML 树中确实不存在该节点，诚实返回空列表，绝不能暴力兜底把全屏无关组件列出
            return []

        return []

    def on_item_clicked(self, item: QListWidgetItem):
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self.btn_tap.setEnabled(True)
            self.btn_send_keys.setEnabled(True)
            self.element_picked.emit(node_id)
            self._save_memory()

    def on_tap_clicked(self):
        curr = self.list_results.currentItem()
        if curr:
            node_id = curr.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.lbl_status.setText("⚡ 正在真机上执行点击动作...")
                QApplication.processEvents()
                self.tap_requested.emit(node_id)
                self.lbl_status.setText("✅ 已在设备上成功执行点击动作！")

    def on_send_keys_clicked(self):
        curr = self.list_results.currentItem()
        if curr:
            node_id = curr.data(Qt.ItemDataRole.UserRole)
            if node_id:
                text, ok = QInputDialog.getText(self, "输入文本", "请输入要发送至该元素的文本内容:")
                if ok and text:
                    self.lbl_status.setText("⚡ 正在向设备下发文本内容...")
                    QApplication.processEvents()
                    self.send_keys_requested.emit(node_id, text)
                    self.lbl_status.setText(f"✅ 文本已成功发送至目标组件！")



# ==============================================================================
# 轻量高颜值无阻塞 Toast 悬浮提示条 (1 秒自动消失)
# ==============================================================================

class ToastNotification(QLabel):
    """
    轻量高颜值无阻塞 Toast 悬浮提示条：
    1. 居中悬浮展示 (视口正中央)，背景纯透明，鼠标事件完全穿透；
    2. 默认 1 秒 (1000ms) 后自动消失，杜绝弹窗阻塞打断用户心流。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #166534;
                font-size: 16px;
                font-weight: 700;
                padding: 10px 24px;
                border: none;
            }
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, message: str, duration_ms: int = 1000):
        self.setText(message)
        self.adjustSize()
        if self.parentWidget():
            parent_rect = self.parentWidget().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = (parent_rect.height() - self.height()) // 2
            self.move(x, y)
        self.show()
        self.raise_()
        self._timer.start(duration_ms)


# ==============================================================================
# 自定义 DOM 树单词精准提取与富文本渲染委托
# ==============================================================================

def extract_word_bounds(text: str, pos: int) -> Optional[Tuple[int, int, str]]:
    """
    给定文本与字符索引 pos，以单词为整体提取区间 (start, end, word)。
    - 不包含前后空格、尖括号、等号、引号等外围语法分隔符；
    - 支持并包含单词内部特殊字符（如 __Column__、bounds 的 [0,0][1084,2412] 等）；
    - 确保提取出的单词纯净、无冗余外围空白。
    """
    if not text or pos < 0 or pos >= len(text):
        return None

    # 外层分隔符：空格、制表符、换行、尖括号、等号、单双引号
    delimiters = {' ', '\t', '\r', '\n', '<', '>', '=', '"', "'", '“', '”'}

    # 若命中位置恰好是分隔符，优先向左探测紧邻的单词字符，若无则向右探测
    if text[pos] in delimiters:
        if pos > 0 and text[pos - 1] not in delimiters:
            pos = pos - 1
        elif pos + 1 < len(text) and text[pos + 1] not in delimiters:
            pos = pos + 1
        else:
            return None

    # 向左延伸至首个分隔符或字符串首
    start = pos
    while start > 0 and text[start - 1] not in delimiters:
        start -= 1

    # 向右延伸至首个分隔符或字符串尾
    end = pos + 1
    while end < len(text) and text[end] not in delimiters:
        end += 1

    word = text[start:end]
    if not word.strip():
        return None
    return (start, end, word)


class DOMTreeItemDelegate(QStyledItemDelegate):
    """
    DOM 树专属项目渲染委托：
    1. 完美保持各节点原本的高颜值莫兰迪彩色标签和背景；
    2. 支持局部单词双击高亮选中（经典蓝底纯白文字），高亮渲染仅作用于目标单词本身；
    3. 前后其他文本与标点符号保持原有颜色，杜绝整行暴力涂蓝。
    """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        widget = option.widget
        if not isinstance(widget, DOMTreeWidget):
            super().paint(painter, option, index)
            return

        item = widget.itemFromIndex(index)
        if widget.selected_word_item != item or not widget.selected_word_range:
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        # 1. 先计算文本精确绘制矩形
        text_rect = widget.style().subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, widget)
        text_rect = text_rect.adjusted(2, 0, -2, 0)

        # 2. 清空 opt.text 与选中状态后交由原生委托绘制背景与展开折叠箭头
        opt.state &= ~QStyle.StateFlag.State_Selected
        opt.text = ""
        super().paint(painter, opt, index)

        text = item.text(0)
        start, end = widget.selected_word_range
        if not text or start >= len(text) or end <= start:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = opt.font
        fm = opt.fontMetrics
        orig_color = item.foreground(0).color() if item.foreground(0).style() != Qt.BrushStyle.NoBrush else opt.palette.text().color()

        prefix_str = text[:start]
        word_str = text[start:end]
        suffix_str = text[end:]

        prefix_w = fm.horizontalAdvance(prefix_str)
        word_w = fm.horizontalAdvance(word_str)

        y_pos = text_rect.top() + (text_rect.height() - fm.height()) // 2 + fm.ascent()
        x_base = text_rect.left()

        # 3. 绘制前缀字符 (保持节点原有莫兰迪前景色)
        painter.setFont(font)
        painter.setPen(orig_color)
        if prefix_str:
            painter.drawText(x_base, y_pos, prefix_str)

        # 4. 绘制选中单词的高亮背景 (现代科技蓝底 #0284c7，3px 微圆角)
        word_bg_rect = QRectF(
            float(x_base + prefix_w),
            float(text_rect.top() + (text_rect.height() - fm.height()) / 2),
            float(word_w),
            float(fm.height())
        )
        word_bg_path = QPainterPath()
        word_bg_path.addRoundedRect(word_bg_rect.adjusted(-1, 0, 1, 0), 3.0, 3.0)
        painter.fillPath(word_bg_path, QBrush(QColor("#0284c7")))

        # 5. 绘制选中单词文字 (纯白加粗)
        bold_font = QFont(font)
        bold_font.setBold(True)
        painter.setFont(bold_font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(x_base + prefix_w, y_pos, word_str)

        # 6. 绘制后缀字符 (保持节点原有莫兰迪前景色)
        painter.setFont(font)
        painter.setPen(orig_color)
        if suffix_str:
            painter.drawText(x_base + prefix_w + word_w, y_pos, suffix_str)

        painter.restore()


# ==============================================================================
# 自定义 DOM 树控件：锁定水平拖动条，支持双击单词文本精准选中与复制
# ==============================================================================

class DOMTreeWidget(QTreeWidget):
    """
    DOM 组件层级树控件：
    1. 彻底禁用点击节点或选择节点时的自动水平位移，保持水平拖动条和视口绝对静止；
    2. 支持 DOM 树中任意文本双击单词精准选中高亮与自动复制；
    3. 支持 Ctrl+C 快捷键复制当前选中的单词文本；
    4. 仅允许垂直方向自适应滚动或用户主动拖拽横向拖动条。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoScroll(False)
        self.setIndentation(13)  # 精致紧凑层级缩进 (对标专业 IDE 规范，彻底消除过宽留白)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # 词汇文本选中状态管理
        self.selected_word_item: Optional[QTreeWidgetItem] = None
        self.selected_word_range: Optional[Tuple[int, int]] = None
        self.selected_word_text: str = ""

        # 安装专属项目渲染委托
        self.setItemDelegate(DOMTreeItemDelegate(self))

    def clear(self):
        # 刷新或清空 DOM 树时彻底释放词汇引用，杜绝悬挂指针
        self.selected_word_item = None
        self.selected_word_range = None
        self.selected_word_text = ""
        super().clear()

    def clear_word_selection(self):
        """主动清除当前的局部单词文本选中状态"""
        if self.selected_word_item:
            self.selected_word_item = None
            self.selected_word_range = None
            self.selected_word_text = ""
            self.viewport().update()

    def scrollTo(self, index, hint=QAbstractItemView.ScrollHint.EnsureVisible):
        # 拦截所有 scrollTo 调用，强制锁死水平拖动条数值，仅允许垂直方向更新
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()
        super().scrollTo(index, hint)
        h_bar.setValue(h_val)

    def mousePressEvent(self, event):
        # 鼠标按下时记录水平位置并在事件完成后严格复位
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()

        click_pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        item = self.itemAt(click_pos)

        # 若单击了不同 item 或空白处，平滑清除上一个单词的选中高亮
        if self.selected_word_item and self.selected_word_item != item:
            self.selected_word_item = None
            self.selected_word_range = None
            self.selected_word_text = ""
            self.viewport().update()

        super().mousePressEvent(event)
        h_bar.setValue(h_val)

    def mouseDoubleClickEvent(self, event):
        # 鼠标双击时记录水平位置并在事件完成后严格复位，确保横向拖动条绝不发生漂移
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()

        click_pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        item = self.itemAt(click_pos)

        if item:
            opt = QStyleOptionViewItem()
            self.initViewItemOption(opt)
            opt.rect = self.visualItemRect(item)
            text_rect = self.style().subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, self)

            rel_x = click_pos.x() - text_rect.left()
            text = item.text(0)
            if rel_x >= 0 and text:
                fm = self.fontMetrics()
                curr_x = 0
                hit_pos = len(text) - 1
                for i, ch in enumerate(text):
                    ch_w = fm.horizontalAdvance(ch)
                    if curr_x + ch_w >= rel_x:
                        hit_pos = i
                        break
                    curr_x += ch_w

                bounds = extract_word_bounds(text, hit_pos)
                if bounds:
                    start, end, word = bounds
                    self.selected_word_item = item
                    self.selected_word_range = (start, end)
                    self.selected_word_text = word

                    self.viewport().update()

                    # 自动复制至系统剪贴板
                    clipboard = QApplication.clipboard()
                    clipboard.setText(word)

                    # 触发轻量居中透明 Toast 提示 (1秒消失)
                    win = self.window()
                    if hasattr(win, "show_toast"):
                        win.show_toast(f"✅ 已复制: {word}", duration_ms=1000)

        super().mouseDoubleClickEvent(event)
        h_bar.setValue(h_val)

    def mouseReleaseEvent(self, event):
        # 鼠标释放时同样保证水平位置不发生漂移
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()
        super().mouseReleaseEvent(event)
        h_bar.setValue(h_val)

    def keyPressEvent(self, event):
        # 1. 支持在 DOM 树中按 Ctrl+C 快捷复制当前选中的单词文本
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_C:
            if self.selected_word_text:
                clipboard = QApplication.clipboard()
                clipboard.setText(self.selected_word_text)
                win = self.window()
                if hasattr(win, "show_toast"):
                    win.show_toast(f"✅ 已复制: {self.selected_word_text}", duration_ms=1000)
                event.accept()
                return

        # 2. 支持在 DOM 树中直接按 Ctrl+F 激活搜索
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            win = self.window()
            if hasattr(win, "toggle_dom_search"):
                win.toggle_dom_search()
                return

        # 键盘上下方向键导航时，保持水平拖动条位置不变
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()
        super().keyPressEvent(event)
        h_bar.setValue(h_val)


# ==============================================================================
# 主窗口：现代纯白轻奢 UI 移动端全平台 UI 审查器 (HarmonyOS / Android / iOS)
# ==============================================================================

class HarmonyAppiumInspector(QMainWindow):
    """三端一体化高颜值桌面审查器 (HarmonyOS / Android / iOS)"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Santiao Mobile Inspector - 移动端全平台 UI 审查器 (HarmonyOS / Android / iOS)")
        self.setWindowIcon(create_modern_app_icon())
        self.resize(1560, 960)
        self.setMinimumSize(950, 650)

        self.current_udid: str = ""
        self.current_platform: str = "harmony"
        self.flat_components: List[Dict[str, Any]] = []
        self.comp_map: Dict[str, Dict[str, Any]] = {}
        self.tree_item_map: Dict[str, QTreeWidgetItem] = {}
        self.xml_root: Optional[ET.Element] = None
        self.node_counter = 0
        self.search_dialog: Optional[SearchElementDialog] = None

        # DOM 树实时搜索高亮状态
        self.dom_search_matches: List[QTreeWidgetItem] = []
        self.dom_search_index: int = -1
        self.dom_search_original_styles: List[Tuple[QTreeWidgetItem, QColor, QBrush]] = []

        # 后台抓取线程与设备扫描线程
        self.capture_worker: Optional[CaptureWorker] = None
        self.scan_worker: Optional[DeviceScanWorker] = None
        self.screencast_worker: Optional[ScreenCastWorker] = None
        self.is_screencasting: bool = False     # 默认开启实时投屏状态
        self.current_screenshot_path: str = ""  # 当前已载入的真机底图本地绝对路径

        self.apply_white_luxury_theme()
        self.init_ui()

        # 注册全局 Ctrl+F 快捷键，一键唤醒 DOM 树搜索栏
        self.shortcut_dom_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_dom_search.activated.connect(self.toggle_dom_search)

        # 注册全局 Ctrl+R 快捷键，一键极速刷新 DOM 树 (不刷新画面)
        self.shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut_refresh.activated.connect(self.refresh_screen_and_dom)

        # 悬浮轻量 Toast 提示组件 (1 秒自动消失)
        self.toast = ToastNotification(self)
        self._worker_start_time: float = 0.0

        # 三个核心操作的独立超时守卫定时器 (防止界面死锁挂起)
        self._timer_screencast = QTimer(self)
        self._timer_screencast.setSingleShot(True)
        self._timer_screencast.timeout.connect(self._on_screencast_timeout)

        self._timer_sync_screen = QTimer(self)
        self._timer_sync_screen.setSingleShot(True)
        self._timer_sync_screen.timeout.connect(self._on_sync_screen_timeout)

        self._timer_refresh = QTimer(self)
        self._timer_refresh.setSingleShot(True)
        self._timer_refresh.timeout.connect(self._on_refresh_timeout)

        self.load_device_list(auto_capture=True)



    def apply_white_luxury_theme(self):
        """采用现代高级纯白 + 浅灰科技感设计系统 (全面杜绝文本被截断)"""
        self.setStyleSheet("""
            /* 全局基础背景与字体设置 */
            QMainWindow { background-color: #f1f5f9; }
            QWidget {
                color: #0f172a; font-family: 'Segoe UI', 'PingFang SC', sans-serif; font-size: 13px;
            }
            
            /* 顶部纯白卡片操作栏 (紧凑优雅) */
            QFrame#topBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                min-height: 44px;
            }
            QLabel#topBrand {
                font-weight: 800; color: #0f172a; font-size: 14px; margin-right: 2px;
            }
            QLabel#platformBadge {
                background-color: #e0f2fe; color: #0284c7; font-weight: 700;
                font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bae6fd;
            }
            
            /* 设备选择下拉框 (精致紧凑 30px，充足右侧留白避免遮挡) */
            QComboBox {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 2px 28px 2px 10px; font-weight: 500; font-size: 12px; min-height: 26px;
            }
            QComboBox:hover { border-color: #0284c7; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                selection-background-color: #e0f2fe;
                selection-color: #0284c7;
                color: #0f172a;
                padding: 4px;
                font-size: 12px;
            }
            
            /* 模式切换分段按钮 (紧凑 30px，规格统一) */
            QPushButton.mode-btn {
                background-color: #ffffff; color: #334155; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 4px; font-weight: 600; font-size: 12px; min-height: 28px;
            }
            QPushButton.mode-btn:hover {
                background-color: #f8fafc; border-color: #0284c7; color: #0284c7;
            }
            QPushButton.mode-btn:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
                color: #ffffff; border: 1px solid #0284c7; font-weight: bold;
            }
            
            /* 功能动作按钮 (统一 30px 规格，统一 12px 字号) */
            QPushButton.action-btn {
                background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 4px; font-weight: 600; font-size: 12px; min-height: 28px;
            }
            QPushButton.action-btn:hover {
                background-color: #f8fafc; border-color: #0284c7; color: #0284c7;
            }
            QPushButton.action-btn#btnRefresh {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                border: none; color: #ffffff; font-size: 12px; font-weight: 700; padding: 0 4px;
            }
            QPushButton.action-btn#btnRefresh:hover { opacity: 0.9; }
            
            QPushButton.action-btn#btnSearch {
                background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1;
            }
            QPushButton.action-btn#btnSearch:hover {
                background-color: #f8fafc; border-color: #0284c7; color: #0284c7;
            }
            
            /* 分割线与三栏背景容器 (自由拖拽手柄：精致 3px 极细设计) */
            QSplitter::handle:horizontal {
                background-color: #e2e8f0; width: 3px; margin: 0px; border-radius: 1px;
            }
            QSplitter::handle:horizontal:hover {
                background-color: #0ea5e9;
            }
            QFrame.panel-card {
                background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
            }
            
            /* App Source DOM 树形视图 (紧凑层级排版 + 底部横向拖动条) */
            QTreeWidget {
                background-color: #ffffff; border: 1px solid #e2e8f0;
                border-radius: 8px; padding: 4px; color: #0f172a; font-family: Consolas, monospace;
                font-size: 12px;
            }
            QTreeWidget::item {
                min-height: 22px; padding: 1px 4px; border-radius: 4px; margin-bottom: 1px;
            }
            QTreeWidget::item:hover {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
            }
            QTreeWidget::item:selected, QTreeWidget::item:selected:active, QTreeWidget::item:selected:!active {
                background-color: rgba(2, 132, 199, 0.08);
                border: 1px dashed #38bdf8;
            }
            
            /* 现代轻奢极细拖动条 (4px 极薄透明轨道，现代精简质感) */
            QScrollBar:horizontal {
                background: transparent; height: 4px; margin: 0px; border: none;
            }
            QScrollBar::handle:horizontal {
                background: #cbd5e1; min-width: 20px; border-radius: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none; width: 0px; height: 0px; border: none;
            }
            QScrollBar:vertical {
                background: transparent; width: 4px; margin: 0px; border: none;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1; min-height: 20px; border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none; width: 0px; height: 0px; border: none;
            }
            
            /* 属性表格 */
            QTableWidget {
                background-color: #ffffff; border: 1px solid #e2e8f0;
                border-radius: 8px; gridline-color: #f1f5f9; color: #0f172a;
            }
            QHeaderView::section {
                background-color: #f8fafc; color: #475569; border: none;
                border-bottom: 1px solid #e2e8f0; padding: 8px 10px; font-weight: 700;
            }
            
            /* 定位器复制输入框：去除过大垂直 padding，提供充足垂直渲染高度 */
            QLineEdit {
                background-color: #ffffff; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 2px 10px; color: #0f172a;
                font-family: 'Segoe UI', 'PingFang SC', Consolas, sans-serif; font-size: 13px;
                selection-background-color: #0284c7; selection-color: #ffffff;
            }
            QLineEdit:focus { border: 1px solid #0284c7; }
            
            /* 面包屑导航栏：支持多行舒展展示 */
            QLabel#breadcrumb {
                background-color: #f8fafc; border: 1px solid #e2e8f0;
                border-radius: 6px; padding: 8px 12px; color: #0284c7;
                font-family: 'Segoe UI', 'PingFang SC', Consolas, sans-serif; font-size: 12px;
                line-height: 1.4;
            }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------------------------------------------------------------
        # 1. 顶部操作栏 (30px 精致高质感统一设计，全功能清晰分区)
        # ----------------------------------------------------------------------
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(14, 8, 14, 8)
        top_layout.setSpacing(8)

        # 品牌区：Retina 应用图标 + 品牌名 + 动态系统徽章
        brand_widget = QWidget()
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(6)

        lbl_logo = QLabel()
        lbl_logo.setPixmap(create_modern_app_icon().pixmap(24, 24))
        brand_layout.addWidget(lbl_logo)

        lbl_brand = QLabel("三条 UI 审查器")
        lbl_brand.setObjectName("topBrand")
        brand_layout.addWidget(lbl_brand)

        self.lbl_platform_badge = QLabel("HarmonyOS")
        self.lbl_platform_badge.setObjectName("platformBadge")
        brand_layout.addWidget(self.lbl_platform_badge)
        top_layout.addWidget(brand_widget)

        top_layout.addSpacing(6)

        # 设备选择器
        lbl_dev = QLabel("设备:")
        lbl_dev.setStyleSheet("color: #64748b; font-weight: 600; font-size: 12px;")
        top_layout.addWidget(lbl_dev)

        self.combo_devices = QComboBox()
        self.combo_devices.setFixedHeight(30)
        self.combo_devices.setMinimumWidth(380)
        self.combo_devices.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.combo_devices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_devices.currentIndexChanged.connect(self.on_device_changed)
        top_layout.addWidget(self.combo_devices)

        self.btn_refresh_devices = QPushButton("🔄")
        self.btn_refresh_devices.setToolTip("点击获取并刷新当前已连接的设备列表")
        self.btn_refresh_devices.setProperty("class", "action-btn")
        self.btn_refresh_devices.setFixedSize(30, 30)
        self.btn_refresh_devices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_devices.clicked.connect(self.refresh_devices_action)
        top_layout.addWidget(self.btn_refresh_devices)

        top_layout.addSpacing(6)

        # 统一主要操作按键规格 (100px × 30px)
        BTN_W = 100
        BTN_H = 30

        # 模式切换分段按钮 (100x30 统一规格)
        self.btn_mode_select = QPushButton("🎯 元素审查")
        self.btn_mode_select.setProperty("class", "mode-btn")
        self.btn_mode_select.setFixedSize(BTN_W, BTN_H)
        self.btn_mode_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_select.setCheckable(True)
        self.btn_mode_select.setChecked(True)
        self.btn_mode_select.clicked.connect(lambda: self.switch_mode(InspectorMode.SELECT))
        top_layout.addWidget(self.btn_mode_select)

        self.btn_mode_tap = QPushButton("👆 坐标点击")
        self.btn_mode_tap.setProperty("class", "mode-btn")
        self.btn_mode_tap.setFixedSize(BTN_W, BTN_H)
        self.btn_mode_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_tap.setCheckable(True)
        self.btn_mode_tap.clicked.connect(lambda: self.switch_mode(InspectorMode.TAP))
        top_layout.addWidget(self.btn_mode_tap)

        top_layout.addSpacing(6)





        btn_search_modal = QPushButton("🔎 查找元素")
        btn_search_modal.setProperty("class", "action-btn")
        btn_search_modal.setObjectName("btnSearch")
        btn_search_modal.setFixedSize(BTN_W, BTN_H)
        btn_search_modal.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_modal.clicked.connect(self.open_search_dialog)
        top_layout.addWidget(btn_search_modal)

        top_layout.addStretch()

        btn_copy_xml = QPushButton("📋 复制源码")
        btn_copy_xml.setProperty("class", "action-btn")
        btn_copy_xml.setFixedSize(BTN_W, BTN_H)
        btn_copy_xml.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy_xml.clicked.connect(self.copy_xml_source)
        top_layout.addWidget(btn_copy_xml)

        btn_save_shot = QPushButton("💾 保存截图")
        btn_save_shot.setProperty("class", "action-btn")
        btn_save_shot.setFixedSize(BTN_W, BTN_H)
        btn_save_shot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save_shot.clicked.connect(self.save_screenshot)
        top_layout.addWidget(btn_save_shot)

        main_layout.addWidget(top_bar)

        # ----------------------------------------------------------------------
        # 2. 核心三栏布局 (支持自由调整大小，绝对不隐藏)    
        # ----------------------------------------------------------------------
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # ------------------ 左栏：真机屏幕画面 ------------------
        left_container = QFrame()
        left_container.setProperty("class", "panel-card")
        left_container.setMinimumWidth(220)
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        left_header = QHBoxLayout()
        lbl_left_title = QLabel("📱 设备真机画面")
        lbl_left_title.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px;")
        left_header.addWidget(lbl_left_title)
        left_header.addSpacing(8)

        # 实时投屏控制按钮 (默认未开启状态: False)
        self.btn_screencast = QPushButton("📺 开启实时投屏")
        self.btn_screencast.setToolTip("切换真机低延迟实时投屏 (0 截屏广播，完全不触发软件内部截屏通知)")
        self.btn_screencast.setFixedHeight(24)
        self.btn_screencast.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_screencast.setStyleSheet(
            "QPushButton { background: #eff6ff; border: 1px solid #93c5fd; border-radius: 4px; "
            "color: #1d4ed8; font-size: 11px; font-weight: 600; padding: 2px 8px; } "
            "QPushButton:hover { background: #dbeafe; border-color: #60a5fa; }"
        )
        self.btn_screencast.clicked.connect(self.toggle_screencast)
        left_header.addWidget(self.btn_screencast)
        left_header.addSpacing(6)

        self.btn_sync_screen = QPushButton("⚡ 同步真机画面")
        self.btn_sync_screen.setToolTip("仅极速拉取真机最新画面 (0.05s)，与投屏即刻保持一致")
        self.btn_sync_screen.setFixedHeight(24)
        self.btn_sync_screen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_screen.setStyleSheet(
            "QPushButton { background: #f0fdf4; border: 1px solid #86efac; border-radius: 4px; "
            "color: #166534; font-size: 11px; font-weight: 600; padding: 2px 8px; } "
            "QPushButton:hover { background: #dcfce7; border-color: #4ade80; }"
        )
        self.btn_sync_screen.clicked.connect(self.refresh_screen_only)
        left_header.addWidget(self.btn_sync_screen)
        left_header.addSpacing(6)

        # 刷新界面按钮 (仅刷新 DOM 树，保留当前画面底图)
        self.btn_refresh = QPushButton("🔄 刷新界面")
        self.btn_refresh.setToolTip("仅刷新 DOM 控件树，保留当前画面底图 (Ctrl+R)")
        self.btn_refresh.setFixedHeight(24)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet(
            "QPushButton { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; "
            "color: #334155; font-size: 11px; font-weight: 600; padding: 2px 8px; } "
            "QPushButton:hover { background: #f1f5f9; border-color: #94a3b8; }"
        )
        self.btn_refresh.clicked.connect(self.refresh_screen_and_dom)
        left_header.addWidget(self.btn_refresh)

        left_header.addStretch()
        left_layout.addLayout(left_header)

        self.canvas = AppiumScreenView()
        self.canvas.element_selected.connect(self.on_canvas_element_selected)
        self.canvas.coordinate_tapped.connect(self.on_canvas_coordinate_tapped)
        self.canvas.coordinate_swiped.connect(self.on_canvas_coordinate_swiped)
        left_layout.addWidget(self.canvas, 1)

        self.splitter.addWidget(left_container)

        # ------------------ 中栏：DOM 组件层级树 (支持横向拖动条) ------------------
        mid_container = QFrame()
        mid_container.setProperty("class", "panel-card")
        mid_container.setMinimumWidth(240)
        mid_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mid_layout = QVBoxLayout(mid_container)
        mid_layout.setContentsMargins(14, 14, 14, 14)
        mid_layout.setSpacing(10)

        tree_header = QHBoxLayout()
        lbl_mid_title = QLabel("🌳 DOM 组件层级树 (App Source)")
        lbl_mid_title.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px;")
        tree_header.addWidget(lbl_mid_title)
        tree_header.addStretch()

        btn_search_dom = QPushButton("🔍 搜索 (Ctrl+F)")
        btn_search_dom.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_dom.setStyleSheet("padding: 4px 10px; font-size: 11px; background-color: #f0fdf4; border: 1px solid #86efac; border-radius: 4px; color: #166534; font-weight: 600;")
        btn_search_dom.clicked.connect(self.toggle_dom_search)
        tree_header.addWidget(btn_search_dom)

        btn_expand = QPushButton("展开全部")
        btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_expand.setStyleSheet("padding: 4px 10px; font-size: 11px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; color: #334155;")
        btn_expand.clicked.connect(lambda: self.tree_widget.expandAll())
        tree_header.addWidget(btn_expand)

        btn_collapse = QPushButton("折叠全部")
        btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_collapse.setStyleSheet("padding: 4px 10px; font-size: 11px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; color: #334155;")
        btn_collapse.clicked.connect(lambda: self.tree_widget.collapseAll())
        tree_header.addWidget(btn_collapse)
        mid_layout.addLayout(tree_header)

        # 面包屑路径 (开启自动换行，绝不单行截断溢出)
        self.lbl_breadcrumb = QLabel("📍 路径: Hierarchy (根节点)")
        self.lbl_breadcrumb.setObjectName("breadcrumb")
        self.lbl_breadcrumb.setWordWrap(True)
        mid_layout.addWidget(self.lbl_breadcrumb)

        # DOM 树内置实时搜索栏 (支持 Ctrl+F 唤起，绿色高亮显示)
        self.dom_search_bar = QFrame()
        self.dom_search_bar.setObjectName("domSearchBar")
        self.dom_search_bar.setStyleSheet("""
            #domSearchBar {
                background-color: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 6px;
                padding: 3px 6px;
            }
        """)
        search_layout = QHBoxLayout(self.dom_search_bar)
        search_layout.setContentsMargins(4, 3, 4, 3)
        search_layout.setSpacing(6)

        lbl_s_icon = QLabel("🔍")
        lbl_s_icon.setStyleSheet("font-size: 12px; background: transparent; border: none;")
        search_layout.addWidget(lbl_s_icon)

        self.edit_dom_search = QLineEdit()
        self.edit_dom_search.setPlaceholderText("搜索 DOM 标签、ID、文本、属性 (Enter 下一个 / Shift+Enter 上一个 / Esc 关闭)...")
        self.edit_dom_search.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 1px solid #bbf7d0;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 12px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border: 1px solid #22c55e;
            }
        """)
        self.edit_dom_search.textChanged.connect(self.on_dom_search_text_changed)

        def search_key_press(event: QKeyEvent):
            if event.key() == Qt.Key.Key_Escape:
                self.close_dom_search()
                return
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                if event.key() == Qt.Key.Key_C:
                    self.btn_match_case.click()
                    return
                elif event.key() == Qt.Key.Key_W:
                    self.btn_match_word.click()
                    return
                elif event.key() == Qt.Key.Key_R:
                    self.btn_match_regex.click()
                    return
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.on_dom_search_prev()
                else:
                    self.on_dom_search_next()
                return
            QLineEdit.keyPressEvent(self.edit_dom_search, event)

        self.edit_dom_search.keyPressEvent = search_key_press
        search_layout.addWidget(self.edit_dom_search, 1)

        # 匹配格式选项按钮组 (现代 IDE / VS Code 同款样式：Aa 区分大小写 / ab 全字匹配 / .* 正则表达式)
        btn_opt_style = """
            QPushButton {
                background-color: transparent;
                color: #475569;
                border: 1px solid transparent;
                border-radius: 4px;
                font-family: Consolas, "Segoe UI", monospace;
                font-size: 11px;
                font-weight: 700;
                min-width: 22px;
                max-width: 22px;
                height: 22px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #dcfce7;
                border-color: #86efac;
                color: #15803d;
            }
            QPushButton:checked {
                background-color: #16a34a;
                border: 1px solid #15803d;
                color: #ffffff;
            }
            QPushButton:checked:hover {
                background-color: #15803d;
            }
        """

        self.btn_match_case = QPushButton("Aa")
        self.btn_match_case.setCheckable(True)
        self.btn_match_case.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_match_case.setToolTip("区分大小写 (Match Case - Alt+C)")
        self.btn_match_case.setStyleSheet(btn_opt_style)
        self.btn_match_case.toggled.connect(self._on_dom_search_option_toggled)
        search_layout.addWidget(self.btn_match_case)

        self.btn_match_word = QPushButton("ab")
        self.btn_match_word.setCheckable(True)
        self.btn_match_word.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_match_word.setToolTip("全字匹配 (Match Whole Word - Alt+W)")
        self.btn_match_word.setStyleSheet(btn_opt_style + "QPushButton { text-decoration: underline; }")
        self.btn_match_word.toggled.connect(self._on_dom_search_option_toggled)
        search_layout.addWidget(self.btn_match_word)

        self.btn_match_regex = QPushButton(".*")
        self.btn_match_regex.setCheckable(True)
        self.btn_match_regex.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_match_regex.setToolTip("使用正则表达式 (Use Regular Expression - Alt+R)")
        self.btn_match_regex.setStyleSheet(btn_opt_style)
        self.btn_match_regex.toggled.connect(self._on_dom_search_option_toggled)
        search_layout.addWidget(self.btn_match_regex)

        self.lbl_dom_search_count = QLabel("0/0")
        self.lbl_dom_search_count.setStyleSheet("color: #15803d; font-weight: 700; font-size: 11px; min-width: 40px; background: transparent; border: none;")
        search_layout.addWidget(self.lbl_dom_search_count)

        btn_prev_match = QPushButton("↑")
        btn_prev_match.setToolTip("上一个匹配项 (Shift+Enter)")
        btn_prev_match.setFixedSize(24, 24)
        btn_prev_match.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prev_match.setStyleSheet("QPushButton { background: #dcfce7; border: 1px solid #86efac; border-radius: 4px; color: #166534; font-weight: bold; font-size: 13px; } QPushButton:hover { background: #bbf7d0; }")
        btn_prev_match.clicked.connect(self.on_dom_search_prev)
        search_layout.addWidget(btn_prev_match)

        btn_next_match = QPushButton("↓")
        btn_next_match.setToolTip("下一个匹配项 (Enter)")
        btn_next_match.setFixedSize(24, 24)
        btn_next_match.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_next_match.setStyleSheet("QPushButton { background: #dcfce7; border: 1px solid #86efac; border-radius: 4px; color: #166534; font-weight: bold; font-size: 13px; } QPushButton:hover { background: #bbf7d0; }")
        btn_next_match.clicked.connect(self.on_dom_search_next)
        search_layout.addWidget(btn_next_match)

        btn_close_search = QPushButton("✕")
        btn_close_search.setToolTip("关闭搜索 (Esc)")
        btn_close_search.setFixedSize(24, 24)
        btn_close_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close_search.setStyleSheet("QPushButton { background: transparent; border: none; color: #64748b; font-weight: bold; font-size: 13px; } QPushButton:hover { color: #ef4444; }")
        btn_close_search.clicked.connect(self.close_dom_search)
        search_layout.addWidget(btn_close_search)

        self.dom_search_bar.setVisible(False)
        mid_layout.addWidget(self.dom_search_bar)

        # 树视图：开启像素级平滑滚动条，彻底关闭切换节点时的自动横向跳动
        self.tree_widget = DOMTreeWidget()
        self.tree_widget.setIndentation(13)
        self.tree_widget.setHeaderLabels([""])  # 留空交由表头自定义工具条统一渲染
        self.tree_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_widget.header().setStretchLastSection(True)
        self.tree_widget.header().setMinimumHeight(32)

        # 在表头栏中构建标题与【显示被遮挡元素】复选框控件 (对标截图精准右侧布局)
        tree_header_view = self.tree_widget.header()
        header_bar_layout = QHBoxLayout(tree_header_view)
        header_bar_layout.setContentsMargins(10, 0, 10, 0)
        header_bar_layout.setSpacing(12)

        lbl_tree_title = QLabel("ArkUI 组件层次结构")
        lbl_tree_title.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px; background: transparent;")
        header_bar_layout.addWidget(lbl_tree_title)

        self.chk_show_occluded = QCheckBox("显示被遮挡元素")
        self.chk_show_occluded.setChecked(True)
        self.chk_show_occluded.setToolTip("勾选展示被遮挡/未暴露的 DOM 树元素，取消勾选则隐藏")
        self.chk_show_occluded.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_show_occluded.setStyleSheet("""
            QCheckBox {
                color: #0369a1;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
            QCheckBox:hover {
                color: #0284c7;
            }
        """)
        self.chk_show_occluded.stateChanged.connect(self.on_toggle_show_occluded)
        header_bar_layout.addWidget(self.chk_show_occluded)
        header_bar_layout.addStretch()

        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        self.tree_widget.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        self.tree_widget.currentItemChanged.connect(self.on_tree_current_item_changed)
        mid_layout.addWidget(self.tree_widget, 1)

        self.splitter.addWidget(mid_container)

        # ------------------ 右栏：Selected Element 面板 ------------------
        right_container = QFrame()
        right_container.setProperty("class", "panel-card")
        right_container.setMinimumWidth(300)
        right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(12)

        # ----------------------------------------------------------------------
        # 1. 输入框内容实时同步编辑框 (Live Input Sync - 仅输入框/文本框动态展示)
        # ----------------------------------------------------------------------
        self.input_sync_box = QFrame()
        self.input_sync_box.setObjectName("inputSyncBox")
        self.input_sync_box.setStyleSheet(
            "#inputSyncBox { background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }"
        )
        sync_layout = QVBoxLayout(self.input_sync_box)
        sync_layout.setContentsMargins(10, 8, 10, 8)
        sync_layout.setSpacing(6)

        lbl_sync_title = QLabel("✍️ 输入框内容实时同步编辑框 (实时同步至真机与 DOM)")
        lbl_sync_title.setStyleSheet("color: #166534; font-weight: 700; font-size: 12px; border: none; background: transparent;")
        sync_layout.addWidget(lbl_sync_title)

        row_sync = QHBoxLayout()
        row_sync.setContentsMargins(0, 0, 0, 0)
        row_sync.setSpacing(6)

        self.edit_live_input = QLineEdit()
        self.edit_live_input.setFixedHeight(30)
        self.edit_live_input.setStyleSheet("font-size: 12px; padding: 2px 8px;")
        self.edit_live_input.setPlaceholderText("在此输入文字，按回车或点同步即刻下发真机...")
        self.edit_live_input.returnPressed.connect(self.sync_live_input)
        row_sync.addWidget(self.edit_live_input, 1)

        self.btn_sync_send = QPushButton("🚀 实时同步")
        self.btn_sync_send.setFixedHeight(30)
        self.btn_sync_send.setFixedWidth(78)
        self.btn_sync_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_send.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16a34a, stop:1 #22c55e); "
            "color: #ffffff; font-weight: 700; border: none; border-radius: 5px; font-size: 11px; padding: 0 4px;"
        )
        self.btn_sync_send.clicked.connect(self.sync_live_input)
        row_sync.addWidget(self.btn_sync_send)

        self.btn_sync_clear = QPushButton("🧹 清空")
        self.btn_sync_clear.setFixedHeight(30)
        self.btn_sync_clear.setFixedWidth(54)
        self.btn_sync_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_clear.setStyleSheet(
            "background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1; "
            "border-radius: 5px; font-weight: 600; font-size: 11px;"
        )
        self.btn_sync_clear.clicked.connect(self.action_element_clear)
        row_sync.addWidget(self.btn_sync_clear)

        sync_layout.addLayout(row_sync)
        # 初始默认隐藏，仅在选中输入框/文本框时动态显现
        self.input_sync_box.setVisible(False)
        right_layout.addWidget(self.input_sync_box)

        # ----------------------------------------------------------------------
        # 2. 定位器推荐与一键复制卡片 (严格网格对齐，与上方卡片等宽呼应)
        # ----------------------------------------------------------------------
        loc_box = QFrame()
        loc_box.setObjectName("locBox")
        loc_box.setStyleSheet(
            "#locBox { background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }"
        )
        loc_layout = QVBoxLayout(loc_box)
        loc_layout.setContentsMargins(10, 8, 10, 8)
        loc_layout.setSpacing(6)

        lbl_loc_title = QLabel("🚀 自动化定位代码推荐 (一键复制到 Page Object)")
        lbl_loc_title.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px; border: none; background: transparent;")
        loc_layout.addWidget(lbl_loc_title)

        grid_loc = QGridLayout()
        grid_loc.setContentsMargins(0, 0, 0, 0)
        grid_loc.setHorizontalSpacing(6)
        grid_loc.setVerticalSpacing(6)

        def _create_loc_row(label_text: str, placeholder: str, row_idx: int):
            lbl = QLabel(label_text)
            lbl.setFixedWidth(46)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("color: #475569; font-weight: 700; font-size: 11px; font-family: Consolas, monospace; border: none; background: transparent;")

            txt = QLineEdit()
            txt.setFixedHeight(30)
            txt.setReadOnly(True)
            txt.setStyleSheet("font-size: 12px; padding: 2px 8px;")
            txt.setPlaceholderText(placeholder)

            btn = QPushButton("复制")
            btn.setFixedHeight(30)
            btn.setFixedWidth(54)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background-color: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd; border-radius: 5px; font-weight: 700; font-size: 11px; }"
                "QPushButton:hover { background-color: #0284c7; color: #ffffff; border-color: #0284c7; }"
            )
            btn.clicked.connect(lambda: self.copy_to_clip(txt.text()))

            grid_loc.addWidget(lbl, row_idx, 0)
            grid_loc.addWidget(txt, row_idx, 1)
            grid_loc.addWidget(btn, row_idx, 2)
            return txt

        self.txt_loc_id = _create_loc_row("id", "ID 定位代码: (该元素无 ID)", 0)
        self.txt_loc_xpath = _create_loc_row("xpath", "XPath 表达式", 1)
        self.txt_loc_py = _create_loc_row("python", "Python 语句", 2)

        loc_layout.addLayout(grid_loc)
        right_layout.addWidget(loc_box)

        # 详细属性表 (优化默认行高与文本展示，消除上下截断)
        lbl_attr_header = QLabel("📋 详细属性清单 (Attributes)")
        lbl_attr_header.setStyleSheet("color: #475569; font-weight: 700; margin-top: 4px;")
        right_layout.addWidget(lbl_attr_header)

        self.table_attrs = QTableWidget()
        self.table_attrs.setColumnCount(2)
        self.table_attrs.setHorizontalHeaderLabels(["属性名称 (Attribute)", "属性值 (Value)"])
        self.table_attrs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_attrs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_attrs.verticalHeader().setDefaultSectionSize(34)
        self.table_attrs.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right_layout.addWidget(self.table_attrs, 1)

        self.splitter.addWidget(right_container)

        # 初始分配比例：3 : 5 : 3
        self.splitter.setStretchFactor(0, 28)
        self.splitter.setStretchFactor(1, 50)
        self.splitter.setStretchFactor(2, 30)

        main_layout.addWidget(self.splitter, 1)

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # 设备与界面刷新 (全平台多端异步调度)
    # --------------------------------------------------------------------------

    def load_device_list(self, auto_capture: bool = True):
        """全异步非阻塞扫描在线设备，彻底解放主线程"""
        if self.scan_worker and self.scan_worker.isRunning():
            return

        if hasattr(self, "btn_refresh_devices"):
            self.btn_refresh_devices.setEnabled(False)
            self.btn_refresh_devices.setText("⏳")

        if self.combo_devices.count() == 0:
            self.combo_devices.addItem("🔍 正在秒级扫描连接设备...", None)

        self.scan_worker = DeviceScanWorker()
        self.scan_worker.devices_ready.connect(lambda devs: self._on_devices_scanned(devs, auto_capture))
        self.scan_worker.start()

    def _on_devices_scanned(self, devices: List[Dict[str, Any]], auto_capture: bool):
        """异步扫描完成后的主线程无缝回调与智能设备选中"""
        if hasattr(self, "btn_refresh_devices"):
            self.btn_refresh_devices.setEnabled(True)
            self.btn_refresh_devices.setText("🔄")

        self.combo_devices.blockSignals(True)
        self.combo_devices.clear()

        if devices:
            target_index = -1
            for idx, dev in enumerate(devices):
                item_text = f"[{dev['platform'].upper()}] {dev['name']}"
                self.combo_devices.addItem(item_text, dev)
                self.combo_devices.setItemData(idx, f"序列号 (UDID): {dev['udid']}\n机型描述: {dev['name']}", Qt.ItemDataRole.ToolTipRole)
                if dev["udid"] == self.current_udid:
                    target_index = idx

            if target_index >= 0:
                self.combo_devices.setCurrentIndex(target_index)
                self.combo_devices.setToolTip(f"当前选中设备 UDID: {self.current_udid}")
                self.combo_devices.blockSignals(False)
            else:
                first = devices[0]
                was_screencasting = self.is_screencasting
                if self.screencast_worker:
                    self.stop_screencast()
                ScreenCastWorker.clear_cache()
                self.current_screenshot_path = ""
                if hasattr(self, "canvas") and self.canvas is not None:
                    self.canvas.clear_screen()
                self.current_udid = first["udid"]
                self.current_platform = first["platform"]
                self.combo_devices.setCurrentIndex(0)
                self.combo_devices.setToolTip(f"当前选中设备 UDID: {self.current_udid}")
                self.update_platform_badge()
                self.combo_devices.blockSignals(False)
                if was_screencasting:
                    QTimer.singleShot(150, self.start_screencast)
                if auto_capture:
                    # 延时 1500ms 刷新界面，确保投屏流首帧在内存中已就绪，0ms 零外部调用瞬时呈现
                    QTimer.singleShot(1500, self.refresh_screen_only)
        else:
            self.combo_devices.addItem("未检测到在线设备 (请检查 USB/网络连接)", None)
            self.current_udid = ""
            self.current_platform = "harmony"
            self.combo_devices.setToolTip("未检测到可用在线设备")
            self.update_platform_badge()
            self.combo_devices.blockSignals(False)

    def refresh_devices_action(self):
        """用户点击 [🔄] 按钮，异步扫描并刷新当前真实在线设备列表"""
        self.load_device_list(auto_capture=False)

    def on_device_changed(self, index: int):
        dev = self.combo_devices.currentData()
        if dev and isinstance(dev, dict):
            new_udid = dev.get("udid", "")
            new_plat = dev.get("platform", "harmony")
            self.combo_devices.setToolTip(f"当前选中设备 UDID: {new_udid}")
            if new_udid != self.current_udid or new_plat != self.current_platform:
                was_screencasting = self.is_screencasting
                if self.screencast_worker:
                    self.stop_screencast()
                # 换机隔离：彻底清空全量内存投屏帧缓存与前台画布，杜绝跨设备旧画面残留
                ScreenCastWorker.clear_cache()
                self.current_screenshot_path = ""
                if hasattr(self, "canvas") and self.canvas is not None:
                    self.canvas.clear_screen()
                self.current_udid = new_udid
                self.current_platform = new_plat
                self.update_platform_badge()
                if was_screencasting:
                    # 延时 150ms 启动新投屏，让旧 worker 线程完全退出并释放连接
                    QTimer.singleShot(150, self.start_screencast)
                QTimer.singleShot(350, self.refresh_screen_only)

    def update_platform_badge(self):
        """动态更新顶部品牌栏的系统类型胶囊徽章"""
        if self.current_platform == "harmony":
            self.lbl_platform_badge.setText("HarmonyOS NEXT")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #e0f2fe; color: #0284c7; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bae6fd;"
            )
        elif self.current_platform == "android":
            self.lbl_platform_badge.setText("Android")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #dcfce7; color: #16a34a; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bbf7d0;"
            )
        elif self.current_platform == "ios":
            self.lbl_platform_badge.setText("iOS")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #f1f5f9; color: #334155; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #cbd5e1;"
            )

    def refresh_screen_and_dom(self):
        """
        刷新界面按钮点击处理：
        仅刷新 DOM 控件树，保留当前真机画面底图 (零截屏广播通知，30~50ms 极速响应，带 12s 超时防死锁机制)
        """
        if not self.current_udid:
            QMessageBox.warning(self, "设备未连接", "未检测到在线移动设备，请确认开启 USB 调试并连接设备。")
            return

        if self.capture_worker and self.capture_worker.isRunning():
            # 引入防卡死看门狗机制：若上一轮抓取已超 6 秒仍未退出，主动终止防死锁
            if getattr(self, "_worker_start_time", 0) and (time.time() - self._worker_start_time > 6):
                try:
                    self.capture_worker.terminate()
                    self.capture_worker.wait(500)
                except Exception:
                    pass
            else:
                return

        self._worker_start_time = time.time()
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("⏳ 正在刷新...")
        self._timer_refresh.start(12000)

        project_root = SmartPathResolver.get_project_root()
        tmp_dir = os.path.normpath(os.path.abspath(os.path.join(project_root, "reports", "inspector")))
        os.makedirs(tmp_dir, exist_ok=True)

        # 核心：纯 DOM 刷新模式，不抓取/刷新画面，保留当前画面底图
        self.capture_worker = CaptureWorker(self.current_udid, self.current_platform, tmp_dir, mode="dom_only")
        self.capture_worker.dom_finished.connect(self.on_dom_only_success)
        self.capture_worker.failed.connect(self.on_capture_failed)
        self.capture_worker.start()

    def _reset_capture_buttons(self):
        """重置同步真机画面与刷新界面按钮状态"""
        self._timer_sync_screen.stop()
        self._timer_refresh.stop()
        if hasattr(self, "btn_sync_screen"):
            self.btn_sync_screen.setEnabled(True)
            self.btn_sync_screen.setText("⚡ 同步真机画面")
        if hasattr(self, "btn_refresh"):
            self.btn_refresh.setEnabled(True)
            self.btn_refresh.setText("🔄 刷新界面")

    def _on_sync_screen_timeout(self):
        """同步真机画面超时回调"""
        logging.warning("[UI审查器] 同步真机画面超时 (12s)")
        if self.capture_worker and self.capture_worker.isRunning():
            try:
                self.capture_worker.terminate()
            except Exception:
                pass
            self.capture_worker = None
        self._reset_capture_buttons()
        self.show_toast("⚠️ 同步真机画面超时 (12s)，已重置状态")

    def _on_refresh_timeout(self):
        """刷新界面超时回调"""
        logging.warning("[UI审查器] 刷新界面超时 (12s)")
        if self.capture_worker and self.capture_worker.isRunning():
            try:
                self.capture_worker.terminate()
            except Exception:
                pass
            self.capture_worker = None
        self._reset_capture_buttons()
        self.show_toast("⚠️ 刷新界面超时 (12s)，已重置状态")

    def _on_screencast_timeout(self):
        """开启实时投屏超时回调"""
        logging.warning("[UI审查器] 开启实时投屏超时 (10s)")
        self.stop_screencast()
        self._timer_screencast.stop()
        self._update_screencast_btn_style(False)
        self.show_toast("⚠️ 开启实时投屏超时 (10s)，投屏通道未响应，已自动复位")

    def on_dom_only_success(self, layout_file: str, platform: str):
        """对齐 HoKit UIViewer 叠加层机制：仅更新 DOM 组件树，复用当前底图与缩放比例 (零截屏/零系统广播)"""
        self._reset_capture_buttons()
        local_png = self.current_screenshot_path

        try:
            prev_selected_id = self.canvas.selected_node_id

            # 优先从布局文件中提取真机真实物理分辨率 (彻底免疫投屏 JPEG 帧等比缩放毒化)
            phys_w, phys_h = get_layout_physical_size(layout_file, 1084, 2412)
            pix = QPixmap(local_png) if (local_png and os.path.exists(local_png)) else QPixmap()
            if not pix.isNull() and pix.width() >= 800 and pix.height() >= 1200:
                screen_w, screen_h = pix.width(), pix.height()
            else:
                screen_w, screen_h = phys_w, phys_h

            raw_tree = parse_layout_file(layout_file, platform, screen_w=screen_w, screen_h=screen_h)

            self.clear_dom_search_highlights()
            self.flat_components.clear()
            self.comp_map.clear()
            self.tree_item_map.clear()
            self.tree_widget.clear()
            self.node_counter = 0

            # 全局模态弹窗预检测：检查整机当前是否展示了处于活跃状态的模态弹窗
            def find_active_dialogs(n: Dict[str, Any]) -> bool:
                a = n.get("attributes", {})
                t = a.get("type", "")
                vis = str(a.get("visible", "true")).lower() != "false"
                if t in ("Dialog", "CustomDialog", "ActionSheet", "AlertDialog", "Popup") and vis:
                    return True
                for ch in n.get("children", []):
                    if find_active_dialogs(ch):
                        return True
                return False

            has_active_dialog = find_active_dialogs(raw_tree)

            self.xml_root = ET.Element("Hierarchy", {"platform": platform, "udid": self.current_udid})
            self.build_dom_tree(
                raw_tree, None, self.xml_root, "/Hierarchy",
                depth=0, parent_visible=True, is_in_active_page=True,
                screen_w=screen_w, screen_h=screen_h,
                is_parent_occluded=False,
                has_active_dialog=has_active_dialog,
                is_in_dialog=False
            )

            # 仅刷新组件层级，保留当前画布底图与缩放视口 (对齐 HoKit 投屏 Overlay 机制)
            self.canvas.update_components_only(self.flat_components)
            self.tree_widget.expandToDepth(2)

            # 重新应用当前的 DOM 树搜索高亮状态
            if hasattr(self, "dom_search_bar") and self.dom_search_bar.isVisible() and self.edit_dom_search.text().strip():
                self.on_dom_search_text_changed(self.edit_dom_search.text())

            # 重新锁定原先选中的节点，保持状态连贯；若切换了画面则重置
            if prev_selected_id and prev_selected_id in self.comp_map:
                self.select_element_by_id(prev_selected_id)
            else:
                self.canvas.selected_node_id = ""
                self.canvas.hover_node_id = ""
                self.canvas.update()

            # 实时同步常驻的查找器窗口数据源，彻底根除跨生命周期导致的 XML 与 comp_map 串位
            if getattr(self, "search_dialog", None) is not None:
                self.search_dialog.update_context(
                    self.flat_components,
                    self.xml_root,
                    comp_map=self.comp_map,
                    platform=self.current_platform
                )
            self.show_toast("✅ DOM 控件树已极速刷新 (真机画面保持不变)")
        except Exception as e:
            logging.error(f"[UI审查器] 刷新 DOM 树数据异常: {e}")

    def on_capture_success(self, local_png: str, layout_file: str, platform: str):
        self._reset_capture_buttons()
        # 严格过滤超时占位白图 (只有真实物理真机截图 > 40KB 才记录为持久底图路径，彻底杜绝缓存毒化)
        is_real_shot = os.path.exists(local_png) and os.path.getsize(local_png) > 40000
        if is_real_shot:
            self.current_screenshot_path = local_png

        try:
            prev_selected_id = self.canvas.selected_node_id

            # 优先从布局文件中提取真机真实物理分辨率 (彻底免疫投屏 JPEG 帧等比缩放毒化)
            phys_w, phys_h = get_layout_physical_size(layout_file, 1084, 2412)
            pix = QPixmap(local_png) if os.path.exists(local_png) else QPixmap()
            if not pix.isNull() and pix.width() >= 800 and pix.height() >= 1200:
                screen_w, screen_h = pix.width(), pix.height()
            else:
                screen_w, screen_h = phys_w, phys_h

            raw_tree = parse_layout_file(layout_file, platform, screen_w=screen_w, screen_h=screen_h)

            self.clear_dom_search_highlights()
            self.flat_components.clear()
            self.comp_map.clear()
            self.tree_item_map.clear()
            self.tree_widget.clear()
            self.node_counter = 0

            # 全局模态弹窗预检测：检查整机当前是否展示了处于活跃状态的模态弹窗
            def find_active_dialogs(n: Dict[str, Any]) -> bool:
                a = n.get("attributes", {})
                t = a.get("type", "")
                vis = str(a.get("visible", "true")).lower() != "false"
                if t in ("Dialog", "CustomDialog", "ActionSheet", "AlertDialog", "Popup") and vis:
                    return True
                for ch in n.get("children", []):
                    if find_active_dialogs(ch):
                        return True
                return False

            has_active_dialog = find_active_dialogs(raw_tree)

            self.xml_root = ET.Element("Hierarchy", {"platform": platform, "udid": self.current_udid})
            self.build_dom_tree(
                raw_tree, None, self.xml_root, "/Hierarchy",
                depth=0, parent_visible=True, is_in_active_page=True,
                screen_w=screen_w, screen_h=screen_h,
                is_parent_occluded=False,
                has_active_dialog=has_active_dialog,
                is_in_dialog=False
            )

            # 工业级高保真视窗装载：装载底图与组件
            if is_real_shot:
                self.canvas.load_screenshot(local_png, self.flat_components)
            elif (
                ScreenCastWorker.latest_udid == self.current_udid
                and ScreenCastWorker.latest_image is not None
                and not ScreenCastWorker.latest_image.isNull()
            ):
                mem_pix = QPixmap.fromImage(ScreenCastWorker.latest_image)
                self.canvas.update_screen_pixmap(mem_pix, keep_components=False)
                self.canvas.update_components_only(self.flat_components)
            elif os.path.exists(local_png):
                self.canvas.load_screenshot(local_png, self.flat_components)

            self.tree_widget.expandToDepth(2)

            # 重新应用当前的 DOM 树搜索高亮状态
            if hasattr(self, "dom_search_bar") and self.dom_search_bar.isVisible() and self.edit_dom_search.text().strip():
                self.on_dom_search_text_changed(self.edit_dom_search.text())

            # 重新锁定原先选中的节点，保持状态连贯；若切换了画面则重置
            if prev_selected_id and prev_selected_id in self.comp_map:
                self.select_element_by_id(prev_selected_id)
            else:
                self.canvas.selected_node_id = ""
                self.canvas.hover_node_id = ""
                self.canvas.update()

            # 实时同步常驻的查找器窗口数据源，彻底根除跨生命周期导致的 XML 与 comp_map 串位
            if getattr(self, "search_dialog", None) is not None:
                self.search_dialog.update_context(
                    self.flat_components,
                    self.xml_root,
                    comp_map=self.comp_map,
                    platform=self.current_platform
                )
            self.show_toast("✅ 画面与 DOM 树已全部同步")
        except Exception as e:
            logging.error(f"[UI审查器] 处理界面现场数据异常: {e}")

    def on_capture_failed(self, err_msg: str):
        self._reset_capture_buttons()
        QMessageBox.critical(self, "抓取失败", f"无法获取设备现场界面与布局:\n{err_msg}")

    def refresh_screen_only(self):
        """
        同步真机画面按钮点击处理：
        同时刷新真机画面与 DOM 树 (对齐用户诉求：全量同步最新现场，带 12s 超时防死锁机制)
        """
        if not self.current_udid:
            QMessageBox.warning(self, "设备未连接", "未检测到在线设备，请先连接并选中设备。")
            return

        if self.capture_worker and self.capture_worker.isRunning():
            self.show_toast("⏳ 任务正在执行中，请勿重复点击")
            return

        self.btn_sync_screen.setEnabled(False)
        self.btn_sync_screen.setText("⏳ 同步中...")
        self._timer_sync_screen.start(12000)

        project_root = SmartPathResolver.get_project_root()
        tmp_dir = os.path.normpath(os.path.abspath(os.path.join(project_root, "reports", "inspector")))
        os.makedirs(tmp_dir, exist_ok=True)

        # 核心：执行 full 全量抓取，同时刷新画面与 DOM 树
        self.capture_worker = CaptureWorker(self.current_udid, self.current_platform, tmp_dir, mode="full")
        self.capture_worker.finished.connect(self.on_capture_success)
        self.capture_worker.failed.connect(self.on_capture_failed)
        self.capture_worker.start()

    def toggle_screencast(self):
        """用户点击【📺 开启实时投屏 / ⏹️ 停止实时投屏】切换投屏状态"""
        if self.is_screencasting:
            self.stop_screencast()
        else:
            self.start_screencast()

    def start_screencast(self):
        """启动后台低延迟实时投屏流 (鸿蒙专属静默极速流引擎，零截屏广播通知，带 10s 超时防死锁)"""
        if not self.current_udid:
            QMessageBox.warning(self, "设备未连接", "未检测到在线设备，请先连接并选中设备。")
            return

        self.btn_screencast.setEnabled(False)
        self.btn_screencast.setText("⏳ 连接投屏中...")
        self._timer_screencast.start(10000)

        # 换设备安全自愈：若当前 worker 正在运行但绑定的 UDID 与当前选中设备不一致，则平滑终止并重建
        if self.screencast_worker and self.screencast_worker.isRunning():
            if getattr(self.screencast_worker, "udid", "") == self.current_udid:
                return
            else:
                self.screencast_worker.stop()
                self.screencast_worker = None

        self.screencast_worker = ScreenCastWorker(self.current_udid, self.current_platform)
        self.screencast_worker.frame_ready.connect(self.on_screencast_frame)
        self.screencast_worker.state_changed.connect(self.on_screencast_state_changed)
        self.screencast_worker.error_occurred.connect(self.on_screencast_error)
        self.screencast_worker.start()

    def stop_screencast(self):
        """优雅停止实时投屏流并即刻恢复 UI 状态 (零等待主线程阻塞)"""
        self._timer_screencast.stop()
        self.is_screencasting = False
        self._update_screencast_btn_style(False)
        if self.screencast_worker:
            worker = self.screencast_worker
            self.screencast_worker = None
            worker.stop()
            # 异步延时回收线程，绝不在主线程做同步 wait 引起 UI 卡顿
            QTimer.singleShot(0, lambda: worker.wait(300))

    def on_screencast_frame(self, image: QImage, raw_bytes: bytes):
        """收到最新一帧投屏画面：实时更新画布 (100% 显存/内存直通，零磁盘 I/O 阻塞主线程)"""
        if not image or image.isNull():
            return
        if self._timer_screencast.isActive():
            self._timer_screencast.stop()
            self.is_screencasting = True
            self._update_screencast_btn_style(True)

        if not self.is_screencasting:
            return
        # 主线程安全由 QImage 转换 QPixmap，100% 避免跨线程隐患
        pixmap = QPixmap.fromImage(image)
        # 内存直通渲染，绝不阻塞主线程，切换画面丝滑流畅
        self.canvas.update_screen_pixmap(pixmap, keep_components=True)

        # 异步节流磁盘缓存 (每 1.5 秒至多更新 1 次，纯后台守护线程写文件，100% 消除主线程 I/O 卡顿)
        now = time.time()
        if now - getattr(self, "_last_disk_cache_t", 0.0) > 1.5 and raw_bytes:
            self._last_disk_cache_t = now
            def _async_save():
                try:
                    project_root = SmartPathResolver.get_project_root()
                    tmp_dir = os.path.normpath(os.path.abspath(os.path.join(project_root, "reports", "inspector")))
                    os.makedirs(tmp_dir, exist_ok=True)
                    ext = "jpeg" if raw_bytes.startswith(b"\xff\xd8") else "png"
                    cached_file = os.path.join(tmp_dir, f"screencast_last_{self.current_platform}.{ext}")
                    with open(cached_file, "wb") as f:
                        f.write(raw_bytes)
                    self.current_screenshot_path = cached_file
                except Exception:
                    pass
            import threading
            threading.Thread(target=_async_save, daemon=True).start()

    def on_screencast_state_changed(self, is_running: bool, msg: str):
        """投屏通道状态变更通知"""
        if is_running:
            self._timer_screencast.stop()
            self.is_screencasting = True
            self._update_screencast_btn_style(True)
            self.show_toast("✅ 实时投屏已启动 (零截屏通知/低延迟硬件流)")
        else:
            if not self.is_screencasting:
                self._timer_screencast.stop()
                self._update_screencast_btn_style(False)

    def on_screencast_error(self, err_msg: str):
        """投屏异常处理"""
        self._timer_screencast.stop()
        self.is_screencasting = False
        self._update_screencast_btn_style(False)
        self.show_toast(f"⚠️ 投屏提示: {err_msg}")

    def _update_screencast_btn_style(self, is_running: bool):
        """动态更新实时投屏控制按钮视觉呈现"""
        if not hasattr(self, "btn_screencast"):
            return
        self.btn_screencast.setEnabled(True)
        if is_running:
            self.btn_screencast.setText("⏹️ 停止实时投屏")
            self.btn_screencast.setStyleSheet(
                "QPushButton { background: #fee2e2; border: 1px solid #fca5a5; border-radius: 4px; "
                "color: #b91c1c; font-size: 11px; font-weight: 700; padding: 2px 8px; } "
                "QPushButton:hover { background: #fecaca; border-color: #f87171; }"
            )
        else:
            self.btn_screencast.setText("📺 开启实时投屏")
            self.btn_screencast.setStyleSheet(
                "QPushButton { background: #eff6ff; border: 1px solid #93c5fd; border-radius: 4px; "
                "color: #1d4ed8; font-size: 11px; font-weight: 600; padding: 2px 8px; } "
                "QPushButton:hover { background: #dbeafe; border-color: #60a5fa; }"
            )

    def build_dom_tree(
        self,
        node: Dict[str, Any],
        parent_item: Optional[QTreeWidgetItem],
        xml_parent: ET.Element,
        current_xpath: str,
        depth: int = 0,
        parent_visible: bool = True,
        is_in_active_page: bool = True,
        screen_w: int = 1084,
        screen_h: int = 2412,
        is_parent_occluded: bool = False,
        has_active_dialog: bool = False,
        is_in_dialog: bool = False,
        covering_rects: Optional[List[Tuple[int, int, int, int]]] = None
    ) -> bool:
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1

        attrs = node.get("attributes", {})
        bounds_str = attrs.get("bounds", "[0,0][0,0]")
        match = re.match(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", bounds_str)
        left, top, right, bottom = 0, 0, 0, 0
        if match:
            left, top, right, bottom = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))

        width = max(0, right - left)
        height = max(0, bottom - top)
        c_type = attrs.get("type") or ("Hierarchy" if depth == 0 else "Component")
        c_id = attrs.get("id") or attrs.get("resource-id") or attrs.get("key") or ""
        c_text = attrs.get("text") or attrs.get("label") or attrs.get("originalText") or ""

        # 可见性基础属性校验
        is_visible = str(attrs.get("visible", "true")).lower() != "false"
        try:
            opacity = float(attrs.get("opacity", "1.0"))
        except Exception:
            opacity = 1.0

        # 核心：鸿蒙 NavDestination / 多页面路由栈识别与不可见页面深度裁剪
        # 如果是 NavDestination 或 NavigationContent，若 bounds == "[0,0][0,0]" 或 visible 为 false，
        # 说明该页面已被压入导航栈底层，绝不能让其子树幽灵组件污染当前真实可视页面！
        node_in_active_page = is_in_active_page
        if c_type in ("NavDestination", "NavigationContent"):
            if (width <= 0 and height <= 0) or not is_visible:
                node_in_active_page = False

        # 特例豁免：移动端验证码/PIN密码输入框通常采用隐藏透明的 TextInput (opacity: 0) 接收软键盘物理输入
        # 虽视觉透明，但具备完整的点击聚焦与输入能力，必须被视为有效交互与展示节点！
        is_transparent_input = (c_type in ("TextInput", "TextArea", "SearchField") and is_visible and width >= 20 and height >= 20)
        node_visible = parent_visible and is_visible and (opacity > 0.05 or is_transparent_input)
        if not node_in_active_page:
            node_visible = False

        # 核心图形学与几何实体遮挡判定 (Geometry Occlusion & Hit-Test)
        # 1. 纯透明布局容器（如 Row, Column, Stack, Flex, RelativeContainer 等且有子节点）本身不绘制实体背景像素，
        #    其自身遮挡状态由其子节点自底向上聚合决定，绝不能因容器外框与上方实体相交而判定整行/整列容器被遮挡！
        is_transparent_container = c_type in ("Row", "Column", "Stack", "Flex", "RelativeContainer", "__Common__", "List", "ListItem", "Scroll", "Grid") and len(node.get("children", [])) > 0

        # 模态弹窗排他性规则 (Modal Dialog Exclusivity)
        is_dialog_root = c_type in ("Dialog", "CustomDialog", "ActionSheet", "AlertDialog", "Popup")
        current_is_dialog = is_in_dialog or is_dialog_root

        if is_dialog_root:
            is_node_occluded = False
        elif has_active_dialog and not current_is_dialog:
            is_node_occluded = True
        elif is_parent_occluded:
            is_node_occluded = True
        else:
            is_node_occluded = False

        # 2. 只有具备实际视觉呈现或交互实体的实心节点（Text, Image, Button, Input, Icon 等），才参与几何遮挡测试！
        if not is_node_occluded and not is_transparent_container and covering_rects and width > 0 and height > 0:
            center_x = left + width // 2
            center_y = top + height // 2
            node_area = width * height
            for c_l, c_t, c_r, c_b in covering_rects:
                # 规则 1: 遮挡物覆盖了该组件的几何中心交互点 (交互点击命中区)
                if c_l <= center_x <= c_r and c_t <= center_y <= c_b:
                    is_node_occluded = True
                    break
                # 规则 2: 遮挡物覆盖了该组件 >= 60% 的实质面积
                inter_l = max(left, c_l)
                inter_t = max(top, c_t)
                inter_r = min(right, c_r)
                inter_b = min(bottom, c_b)
                if inter_r > inter_l and inter_b > inter_t:
                    inter_area = (inter_r - inter_l) * (inter_b - inter_t)
                    if inter_area / node_area >= 0.60:
                        is_node_occluded = True
                        break

        is_exposed = node_visible and (not is_node_occluded)
        is_node_exposed = is_exposed and node_in_active_page

        # 判定当前节点是否属于被遮挡/隐藏层
        is_occluded_node = (not is_node_exposed) and depth > 0

        # 屏幕视口相交判定 (Viewport In-Screen Check):
        # 排除完全滚出真机视口之外的离屏组件 (自适应校准视口边界，杜绝投屏缩略帧尺寸导致下半屏/右半屏组件被误淘汰)
        vw = screen_w if screen_w >= 800 else 1084
        vh = screen_h if screen_h >= 1200 else 2412
        is_in_viewport = not (right <= 0 or left >= vw or bottom <= 0 or top >= vh)
        # 核心优化：画布交互拾取仅限真实暴露在顶层的有效组件 (is_exposed)
        is_interactive = node_in_active_page and is_exposed and is_in_viewport and width >= 4 and height >= 4

        node_xpath = f"{current_xpath}/{c_type}"
        
        # 智能推荐定位器代码 (区分鸿蒙、安卓与 iOS 权威最佳实践)
        rec_id = c_id if c_id else ""
        if self.current_platform == "android":
            if c_id:
                rec_xpath = f"//*[@resource-id='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
            elif c_text:
                rec_xpath = f"//*[@text='{c_text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//*[@text='{c_text}']\")"
            else:
                rec_xpath = node_xpath
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"
        elif self.current_platform == "ios":
            if c_id:
                rec_xpath = f"//*[@name='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ACCESSIBILITY_ID, '{c_id}')"
            elif c_text:
                rec_xpath = f"//*[@label='{c_text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//*[@label='{c_text}']\")"
            else:
                rec_xpath = node_xpath
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"
        else:  # harmony
            if c_id:
                rec_xpath = f"//{c_type}[@id='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
            elif c_text:
                rec_xpath = f"//{c_type}[@text='{c_text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{c_type}[@text='{c_text}']\")"
            else:
                rec_xpath = node_xpath
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"

        comp = {
            "node_id": node_id,
            "type": c_type,
            "id": c_id,
            "text": c_text,
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "width": width,
            "height": height,
            "center_x": left + width // 2,
            "center_y": top + height // 2,
            "depth": depth,
            "xpath": node_xpath,
            "rec_xpath": rec_xpath,
            "rec_id": rec_id,
            "rec_py": rec_py,
            "rec_class": c_type,
            "is_visible": is_visible,
            "opacity": opacity,
            "is_occluded": is_node_occluded,
            "is_exposed": is_exposed,
            "is_interactive": is_interactive,
            "is_in_active_page": node_in_active_page,
            "raw_attributes": attrs,
            "raw": attrs
        }

        # 严格限制：只有真实处于活跃页面、真实可见且在屏幕视口内的组件，才加入画布拾取平铺列表！
        if is_interactive:
            self.flat_components.append(comp)
        self.comp_map[node_id] = comp

        # 安全清洗并生成标准 XML 标签与属性字典
        safe_tag = re.sub(r'[^a-zA-Z0-9_\-]', '', c_type) or "Component"
        if safe_tag[0].isdigit() or safe_tag[0] == '-':
            safe_tag = f"comp_{safe_tag}"

        clean_xml_attrs = {
            "node_id": node_id,
            "id": c_id,
            "text": c_text,
            "type": c_type,
            "bounds": bounds_str,
            "clickable": str(attrs.get("clickable", "")),
            "enabled": str(attrs.get("enabled", "")),
            "occluded": str(is_node_occluded).lower(),
            "exposed": str(is_exposed).lower()
        }
        for k, v in attrs.items():
            if v is None:
                continue
            k_safe = re.sub(r'[^a-zA-Z0-9_\-]', '', str(k))
            if not k_safe:
                continue
            if k_safe[0].isdigit() or k_safe[0] == '-':
                k_safe = f"attr_{k_safe}"
            clean_xml_attrs.setdefault(k_safe, str(v))

        # 跨端 XPath 常用属性映射容错
        if c_id:
            clean_xml_attrs.setdefault("resource-id", c_id)
            clean_xml_attrs.setdefault("name", c_id)
        if c_text:
            clean_xml_attrs.setdefault("label", c_text)
            clean_xml_attrs.setdefault("value", c_text)
        desc = attrs.get("description", "") or attrs.get("content-desc", "")
        if desc:
            clean_xml_attrs.setdefault("content-desc", str(desc))
            clean_xml_attrs.setdefault("description", str(desc))

        xml_elem = ET.SubElement(xml_parent, safe_tag, clean_xml_attrs)

        # 高颜值彩色节点标签渲染
        type_badge = f"<{c_type}"
        attrs_str = ""
        if c_id:
            attrs_str += f' id="{c_id}"'
        if c_text:
            short_t = c_text if len(c_text) <= 22 else c_text[:22] + "..."
            attrs_str += f' text="{short_t}"'
        attrs_str += f' bounds="{bounds_str}"'
        if is_occluded_node:
            attrs_str += ' occluded="true"'
        attrs_str += '>'

        item = QTreeWidgetItem([f"{type_badge}{attrs_str}"])
        item.setData(0, Qt.ItemDataRole.UserRole, node_id)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, bool(is_occluded_node))

        # 统一为各组件类型专属的高颜值莫兰迪配色 (被遮挡元素使用优雅弱化浅灰调)
        if is_occluded_node:
            item.setForeground(0, QColor("#94a3b8"))
            item.setBackground(0, QBrush(QColor("#f8fafc")))
        else:
            scheme = get_dom_tag_color(c_type)
            item.setForeground(0, QColor(scheme["text"]))
            item.setBackground(0, QBrush(QColor(scheme["bg"])))

        # 根据当前复选框状态决定初始是否隐藏 (默认为勾选状态即展示)
        show_occluded = self.chk_show_occluded.isChecked() if hasattr(self, "chk_show_occluded") else True
        if is_occluded_node and not show_occluded:
            item.setHidden(True)

        self.tree_item_map[node_id] = item

        if parent_item:
            parent_item.addChild(item)
        else:
            self.tree_widget.addTopLevelItem(item)

        children = node.get("children", [])

        # 针对模态弹窗（Dialog / ActionSheet / Popup）：若存在全屏弹窗，弹窗之前的底层页面分支全部判定为已遮挡
        dialog_indices = [
            idx for idx, ch in enumerate(children)
            if ch.get("attributes", {}).get("type") in ("Dialog", "ActionSheet", "CustomDialog", "Popup")
        ]
        modal_occluded_indices = set()
        if dialog_indices:
            min_dlg_idx = min(dialog_indices)
            for prev_i in range(min_dlg_idx):
                modal_occluded_indices.add(prev_i)

        # 辅助方法：收集后序节点子树中真正具有视觉/交互实体的叶子边界（穿透纯透明布局容器）
        def collect_solid_leaf_bounds(n: Dict[str, Any]) -> List[Tuple[int, int, int, int]]:
            res = []
            a = n.get("attributes", {})
            t = a.get("type", "")
            try:
                op = float(a.get("opacity", "1.0"))
            except Exception:
                op = 1.0
            if op <= 0.05 or str(a.get("visible", "true")).lower() == "false":
                return res

            c_list = n.get("children", [])
            # Blank 组件在 ArkUI 中纯粹用于伸缩留白，完全透明穿透
            if t == "Blank":
                return res

            is_trans_container = t in ("Row", "Column", "Stack", "Flex", "RelativeContainer", "__Common__", "List", "ListItem", "Scroll", "Grid") and len(c_list) > 0
            if not is_trans_container:
                # 实心叶子组件或带内容的独立节点
                b_str = a.get("bounds", "")
                m = re.match(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", b_str)
                if m:
                    b_w = int(m.group(3)) - int(m.group(1))
                    b_h = int(m.group(4)) - int(m.group(2))
                    if b_w > 0 and b_h > 0:
                        res.append((int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))))
            else:
                for c in c_list:
                    res.extend(collect_solid_leaf_bounds(c))
            return res

        # 针对 Stack（层叠容器）和 RelativeContainer：计算后序实心图层对先序图层的真实几何覆盖
        stack_covering_map: Dict[int, List[Tuple[int, int, int, int]]] = {}
        if c_type in ("Stack", "RelativeContainer") and len(children) > 1:
            for i in range(len(children)):
                accumulated_covers = []
                for k in range(i + 1, len(children)):
                    accumulated_covers.extend(collect_solid_leaf_bounds(children[k]))
                if accumulated_covers:
                    stack_covering_map[i] = accumulated_covers

        effective_parent_item = item if item is not None else parent_item
        has_any_exposed_child = False

        for idx, child in enumerate(children):
            # 继承上级覆盖物 + 当前 Stack 层级内后序兄弟节点的实心覆盖物
            child_covers = list(covering_rects or [])
            if idx in stack_covering_map:
                child_covers.extend(stack_covering_map[idx])

            # 核心防御：如果父节点是透明容器，绝不能因为父容器外框相交而强制让子节点继承遮挡！
            child_parent_occluded = (idx in modal_occluded_indices) or (is_node_occluded and not is_transparent_container)

            child_has_exposed = self.build_dom_tree(
                child, effective_parent_item, xml_elem, node_xpath,
                depth=depth + 1,
                parent_visible=node_visible,
                is_in_active_page=node_in_active_page,
                screen_w=screen_w,
                screen_h=screen_h,
                is_parent_occluded=child_parent_occluded,
                has_active_dialog=has_active_dialog,
                is_in_dialog=current_is_dialog,
                covering_rects=child_covers
            )
            if child_has_exposed:
                has_any_exposed_child = True

        # 核心图形学聚合（Bottom-Up Aggregation）：
        # 如果当前节点是纯透明布局容器且包含子节点，只要有至少一个子节点真实暴露可见，
        # 则该容器自身绝不是被遮挡状态！
        if is_transparent_container:
            if has_any_exposed_child:
                is_node_occluded = False
                is_occluded_node = False
                comp["is_occluded"] = False
                comp["is_exposed"] = True
                clean_xml_attrs["occluded"] = "false"
                clean_xml_attrs["exposed"] = "true"
                xml_elem.attrib["occluded"] = "false"
                xml_elem.attrib["exposed"] = "true"
                scheme = get_dom_tag_color(c_type)
                item.setForeground(0, QColor(scheme["text"]))
                item.setBackground(0, QBrush(QColor(scheme["bg"])))
                attrs_str_clean = re.sub(r'\s+occluded="[^"]*"', '', attrs_str)
                item.setText(0, f"{type_badge}{attrs_str_clean}>")
                item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
                item.setHidden(False)

        # 当前子树是否拥有实质可见暴露节点：
        # 实心组件取决于自身的 is_node_exposed；透明容器取决于 has_any_exposed_child
        if is_transparent_container:
            return has_any_exposed_child
        else:
            return bool(is_node_exposed)

    # --------------------------------------------------------------------------
    # DOM 树内置搜索与高亮绿色显示 (Ctrl+F)
    # --------------------------------------------------------------------------

    def toggle_dom_search(self):
        """打开或激活 DOM 树搜索栏 (快捷键 Ctrl+F)"""
        if not self.dom_search_bar.isVisible():
            self.dom_search_bar.setVisible(True)
        self.edit_dom_search.setFocus()
        self.edit_dom_search.selectAll()

    def close_dom_search(self):
        """关闭 DOM 树搜索栏并清除所有绿色高亮"""
        self.clear_dom_search_highlights()
        if hasattr(self, "edit_dom_search"):
            self.edit_dom_search.setStyleSheet("""
                QLineEdit {
                    background: #ffffff;
                    border: 1px solid #bbf7d0;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 12px;
                    color: #1e293b;
                }
                QLineEdit:focus { border: 1px solid #22c55e; }
            """)
        if hasattr(self, "lbl_dom_search_count"):
            self.lbl_dom_search_count.setStyleSheet("color: #15803d; font-weight: 700; font-size: 11px; min-width: 40px; background: transparent; border: none;")
        self.dom_search_bar.setVisible(False)
        self.tree_widget.setFocus()

    def clear_dom_search_highlights(self):
        """还原所有匹配项的原有配色与字体样式"""
        for item, orig_fg, orig_bg in self.dom_search_original_styles:
            try:
                item.setForeground(0, orig_fg)
                item.setBackground(0, orig_bg)
                font = item.font(0)
                if font.bold():
                    font.setBold(False)
                    item.setFont(0, font)
            except RuntimeError:
                pass
        self.dom_search_original_styles.clear()
        self.dom_search_matches.clear()
        self.dom_search_index = -1

    def _on_dom_search_option_toggled(self):
        """三种匹配格式选项 (Aa / ab / .*) 切换时实时重新执行检索"""
        if hasattr(self, "edit_dom_search"):
            self.on_dom_search_text_changed(self.edit_dom_search.text())

    def on_dom_search_text_changed(self, keyword: str):
        """DOM 树内容实时搜索与高亮绿色渲染 (支持 Aa 区分大小写 / ab 全字匹配 / .* 正则表达式 三种格式匹配)"""
        self.clear_dom_search_highlights()
        kw = keyword.strip()
        if not kw:
            self.lbl_dom_search_count.setText("0/0")
            self.lbl_dom_search_count.setStyleSheet("color: #15803d; font-weight: 700; font-size: 11px; min-width: 40px; background: transparent; border: none;")
            self.edit_dom_search.setStyleSheet("""
                QLineEdit {
                    background: #ffffff;
                    border: 1px solid #bbf7d0;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 12px;
                    color: #1e293b;
                }
                QLineEdit:focus { border: 1px solid #22c55e; }
            """)
            return

        # 获取三种匹配选项状态
        match_case = self.btn_match_case.isChecked() if hasattr(self, "btn_match_case") else False
        match_word = self.btn_match_word.isChecked() if hasattr(self, "btn_match_word") else False
        match_regex = self.btn_match_regex.isChecked() if hasattr(self, "btn_match_regex") else False

        flags = 0 if match_case else re.IGNORECASE
        regex_obj = None

        if match_regex:
            try:
                pattern = kw
                if match_word:
                    pattern = r"\b(?:" + pattern + r")\b"
                regex_obj = re.compile(pattern, flags)
                self.edit_dom_search.setStyleSheet("""
                    QLineEdit {
                        background: #ffffff;
                        border: 1px solid #bbf7d0;
                        border-radius: 4px;
                        padding: 3px 8px;
                        font-size: 12px;
                        color: #1e293b;
                    }
                    QLineEdit:focus { border: 1px solid #22c55e; }
                """)
                self.lbl_dom_search_count.setStyleSheet("color: #15803d; font-weight: 700; font-size: 11px; min-width: 40px; background: transparent; border: none;")
            except re.error:
                # 正则表达式语法非法时，边框变红并提示无效正则，绝不抛出异常导致崩溃
                self.edit_dom_search.setStyleSheet("""
                    QLineEdit {
                        background: #fef2f2;
                        border: 1.5px solid #ef4444;
                        border-radius: 4px;
                        padding: 3px 8px;
                        font-size: 12px;
                        color: #991b1b;
                    }
                """)
                self.lbl_dom_search_count.setText("无效正则")
                self.lbl_dom_search_count.setStyleSheet("color: #dc2626; font-weight: 700; font-size: 11px; min-width: 48px; background: transparent; border: none;")
                return
        elif match_word:
            try:
                # 全词匹配：使用 \b 单词边界
                pattern = r"\b" + re.escape(kw) + r"\b"
                regex_obj = re.compile(pattern, flags)
            except re.error:
                regex_obj = None

        def is_matched(node_text: str) -> bool:
            if regex_obj is not None:
                return bool(regex_obj.search(node_text))
            if match_case:
                return kw in node_text
            return kw.lower() in node_text.lower()

        def collect_tree_items(parent_item: QTreeWidgetItem) -> List[QTreeWidgetItem]:
            items = []
            for i in range(parent_item.childCount()):
                ch = parent_item.child(i)
                items.append(ch)
                items.extend(collect_tree_items(ch))
            return items

        all_items: List[QTreeWidgetItem] = []
        for i in range(self.tree_widget.topLevelItemCount()):
            top = self.tree_widget.topLevelItem(i)
            all_items.append(top)
            all_items.extend(collect_tree_items(top))

        # 根据三种匹配格式进行过滤匹配 (自动排除隐藏未展示的节点)
        matches = [it for it in all_items if (not it.isHidden()) and is_matched(it.text(0))]
        self.dom_search_matches = matches

        if not matches:
            self.lbl_dom_search_count.setText("0/0")
            return

        # 为所有匹配的 DOM 节点设置高亮绿色背景与深绿文本，并自动展开祖先确保可见
        for item in matches:
            orig_fg = item.foreground(0).color()
            orig_bg = item.background(0)
            self.dom_search_original_styles.append((item, orig_fg, orig_bg))

            item.setBackground(0, QBrush(QColor("#dcfce7")))  # 清新亮绿背景
            item.setForeground(0, QColor("#15803d"))          # 深青翠绿文本

            curr = item.parent()
            while curr:
                curr.setExpanded(True)
                curr = curr.parent()

        self.dom_search_index = 0
        self.highlight_current_dom_match()

    def highlight_current_dom_match(self):
        """定位并强高亮当前聚焦的匹配项 (醒目翠绿+加粗)，联动滚动与左侧画布拾取"""
        if not self.dom_search_matches:
            self.lbl_dom_search_count.setText("0/0")
            return

        total = len(self.dom_search_matches)
        idx = self.dom_search_index % total
        self.dom_search_index = idx
        self.lbl_dom_search_count.setText(f"{idx + 1}/{total}")

        for i, item in enumerate(self.dom_search_matches):
            font = item.font(0)
            if i == idx:
                # 当前聚焦项：醒目翠绿高亮背景 + 加粗深绿黑字
                item.setBackground(0, QBrush(QColor("#4ade80")))
                item.setForeground(0, QColor("#052e16"))
                font.setBold(True)
                item.setFont(0, font)

                # 平滑滚动并选中当前节点
                h_bar = self.tree_widget.horizontalScrollBar()
                h_val = h_bar.value()
                self.tree_widget.setCurrentItem(item)
                self.tree_widget.scrollToItem(item, QAbstractItemView.ScrollHint.EnsureVisible)
                h_bar.setValue(h_val)

                # 联动真机预览画布与属性面板
                node_id = item.data(0, Qt.ItemDataRole.UserRole)
                if node_id:
                    self.canvas.selected_node_id = node_id
                    self.canvas.hover_node_id = ""
                    self.canvas.update()
                    self.update_selected_element_panel(node_id)
            else:
                # 其余匹配项保持普通清新草绿色高亮
                item.setBackground(0, QBrush(QColor("#dcfce7")))
                item.setForeground(0, QColor("#15803d"))
                if font.bold():
                    font.setBold(False)
                    item.setFont(0, font)

    def on_dom_search_next(self):
        """跳转下一个匹配项 (Enter / ▼)"""
        if not self.dom_search_matches:
            return
        self.dom_search_index = (self.dom_search_index + 1) % len(self.dom_search_matches)
        self.highlight_current_dom_match()

    def on_dom_search_prev(self):
        """跳转上一个匹配项 (Shift+Enter / ▲)"""
        if not self.dom_search_matches:
            return
        self.dom_search_index = (self.dom_search_index - 1) % len(self.dom_search_matches)
        self.highlight_current_dom_match()

    # --------------------------------------------------------------------------
    # 模式切换与工具栏动作
    # --------------------------------------------------------------------------

    def switch_mode(self, mode: str):
        self.btn_mode_select.setChecked(mode == InspectorMode.SELECT)
        self.btn_mode_tap.setChecked(mode == InspectorMode.TAP)
        self.canvas.set_mode(mode)


    def copy_xml_source(self):
        if self.xml_root is not None:
            xml_str = ET.tostring(self.xml_root, encoding="utf-8").decode("utf-8")
            QApplication.clipboard().setText(xml_str)
            self.show_toast("✅ XML 源码已复制到剪贴板！", duration_ms=1000)

    def save_screenshot(self):
        if not self.canvas.pixmap or self.canvas.pixmap.isNull():
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存真机截图", f"{self.current_platform}_screen.png", "PNG Images (*.png)")
        if path:
            self.canvas.pixmap.save(path, "PNG")
            QMessageBox.information(self, "保存成功", f"截图已保存至:\n{path}")

    def open_search_dialog(self):
        if self.search_dialog is None:
            self.search_dialog = SearchElementDialog(
                self.flat_components,
                self.xml_root,
                comp_map=self.comp_map,
                platform=self.current_platform,
                parent=self
            )
            self.search_dialog.element_picked.connect(self.select_element_by_id)
            self.search_dialog.tap_requested.connect(self.direct_tap_element)
            self.search_dialog.send_keys_requested.connect(self.direct_send_keys_to_element)
        else:
            self.search_dialog.update_context(
                self.flat_components,
                self.xml_root,
                comp_map=self.comp_map,
                platform=self.current_platform
            )

        # 核心：使用独立顶级子任务窗口打开，若处于最小化则恢复，并提升至最前台激活
        if self.search_dialog.isMinimized():
            self.search_dialog.showNormal()
        else:
            self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    # --------------------------------------------------------------------------
    # 核心：点击元素时 DOM 树窗口不改变展开折叠状态，极速定位
    # --------------------------------------------------------------------------

    def select_element_by_id(self, node_id: str):
        self.canvas.selected_node_id = node_id
        self.canvas.update()

        item = self.tree_item_map.get(node_id)
        if item:
            # 锁定当前横向滚动位置，彻底禁止 scrollToItem 将视口推向右侧
            h_bar = self.tree_widget.horizontalScrollBar()
            h_val = h_bar.value()
            self.tree_widget.setCurrentItem(item)
            self.tree_widget.scrollToItem(item, QTreeWidget.ScrollHint.EnsureVisible)
            h_bar.setValue(h_val)

        self.update_selected_element_panel(node_id)

        # 核心联动：如果查找器独立窗口处于打开状态，将当前点击选中的真机/DOM元素实时同步至查找器
        if hasattr(self, "search_dialog") and self.search_dialog and self.search_dialog.isVisible():
            comp = self.comp_map.get(node_id)
            if comp:
                self.search_dialog.sync_element_from_main(comp)

    def on_canvas_element_selected(self, node_id: str):
        self.select_element_by_id(node_id)

    def on_toggle_show_occluded(self, state: int):
        """响应【显示被遮挡元素】复选框状态切换，秒级刷新 DOM 树可见性"""
        show_occluded = self.chk_show_occluded.isChecked() if hasattr(self, "chk_show_occluded") else True
        self.apply_occluded_visibility_to_tree(show_occluded)

    def apply_occluded_visibility_to_tree(self, show_occluded: bool):
        """动态更新当前 DOM 树中所有被遮挡节点的显示/隐藏状态"""
        def traverse_item(item: QTreeWidgetItem):
            is_occluded = bool(item.data(0, Qt.ItemDataRole.UserRole + 1))
            if is_occluded:
                item.setHidden(not show_occluded)
            for i in range(item.childCount()):
                traverse_item(item.child(i))

        for idx in range(self.tree_widget.topLevelItemCount()):
            top = self.tree_widget.topLevelItem(idx)
            if top:
                traverse_item(top)

        # 树可见性更新后，若内置搜索栏正在激活，自动重新计算匹配结果并刷新
        if hasattr(self, "dom_search_bar") and self.dom_search_bar.isVisible() and hasattr(self, "edit_dom_search") and self.edit_dom_search.text().strip():
            self.on_dom_search_text_changed(self.edit_dom_search.text())

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        # 用户在 DOM 树中点击切换节点时，彻底锁死横向位置，底部拖动条绝不自动跳动
        h_bar = self.tree_widget.horizontalScrollBar()
        h_val = h_bar.value()
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self.canvas.selected_node_id = node_id
            self.canvas.hover_node_id = ""  # 选中后清除 hover 干扰
            self.canvas.update()
            self.update_selected_element_panel(node_id)
            if hasattr(self, "search_dialog") and self.search_dialog and self.search_dialog.isVisible():
                comp = self.comp_map.get(node_id)
                if comp:
                    self.search_dialog.sync_element_from_main(comp)
        h_bar.setValue(h_val)

    def on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击 DOM 树里面的元素：确立当前项、联动真机与属性面板，并自适应展开子层级"""
        if not item:
            return
        h_bar = self.tree_widget.horizontalScrollBar()
        h_val = h_bar.value()

        # 1. 设为当前树选中项并锁定水平视口
        self.tree_widget.setCurrentItem(item)
        item.setSelected(True)
        h_bar.setValue(h_val)

        # 2. 如果存在子节点且未展开，双击时平滑展开以便查看下层组件
        if item.childCount() > 0 and not item.isExpanded():
            item.setExpanded(True)

        # 3. 联动真机画面高亮框、右侧属性面板及查找器定位器同步
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self.select_element_by_id(node_id)

    def on_tree_current_item_changed(self, current: Optional[QTreeWidgetItem], previous: Optional[QTreeWidgetItem]):
        """当前树节点切换时联动更新真机高亮框与属性面板 (保持莫兰迪原本色彩，绝不暴力涂蓝整行)"""
        if not current:
            return

        # 联动真机画面与属性面板更新
        node_id = current.data(0, Qt.ItemDataRole.UserRole)
        if node_id and node_id != self.canvas.selected_node_id:
            self.canvas.selected_node_id = node_id
            self.canvas.hover_node_id = ""
            self.canvas.update()
            self.update_selected_element_panel(node_id)
            if hasattr(self, "search_dialog") and self.search_dialog and self.search_dialog.isVisible():
                comp = self.comp_map.get(node_id)
                if comp:
                    self.search_dialog.sync_element_from_main(comp)

    def on_canvas_coordinate_tapped(self, x: int, y: int):
        if self.current_udid:
            DeviceController.tap(self.current_platform, self.current_udid, x, y)
            self.refresh_screen_and_dom()

    def on_canvas_coordinate_swiped(self, x1: int, y1: int, x2: int, y2: int):
        if self.current_udid:
            DeviceController.swipe(self.current_platform, self.current_udid, x1, y1, x2, y2, 600)
            self.refresh_screen_and_dom()

    def update_selected_element_panel(self, node_id: str):
        """刷新右侧 Selected Element 面板与实时输入同步栏"""
        comp = self.comp_map.get(node_id)
        if not comp:
            return

        c_type = comp.get("type", "")
        c_text = comp.get("text", "")

        # 实时输入框预填当前组件现有文字
        self.edit_live_input.blockSignals(True)
        self.edit_live_input.setText(c_text)
        self.edit_live_input.blockSignals(False)

        # 核心：这块只有输入框和文本框才进行展示
        is_input_or_text = (
            c_type in ("TextInput", "TextArea", "Search", "Text", "RichText", "Span")
            or any(k in c_type.lower() for k in ("input", "edit", "text", "search"))
            or bool(c_text and c_text.strip())
        )
        self.input_sync_box.setVisible(is_input_or_text)

        path_str = comp.get("xpath", "Hierarchy").replace("/", "  ›  ")
        scheme = get_dom_tag_color(c_type)
        self.lbl_breadcrumb.setText(f"📍 路径: {path_str}")
        self.lbl_breadcrumb.setStyleSheet(
            f"background-color: {scheme['bg']}; color: {scheme['text']}; "
            f"border: 1px solid {scheme['border']}; border-radius: 6px; padding: 4px 8px; font-weight: 600;"
        )

        # 推荐定位器
        self.txt_loc_id.setText(comp.get("rec_id", ""))
        self.txt_loc_xpath.setText(comp.get("rec_xpath", ""))
        self.txt_loc_py.setText(comp.get("rec_py", ""))

        self.txt_loc_id.setCursorPosition(0)
        self.txt_loc_xpath.setCursorPosition(0)
        self.txt_loc_py.setCursorPosition(0)

        # 快速填充属性列表
        raw = comp.get("raw") or comp.get("raw_attributes") or {}
        real_id_val = comp.get("id", "")
        dom_path_val = raw.get("dom_path", "")
        if real_id_val:
            id_show = real_id_val
        elif dom_path_val:
            id_show = f"(未显式声明 · 虚拟层级: {dom_path_val})"
        else:
            id_show = "-"

        display_attrs = [
            ("id / key", id_show),
            ("text / originalText", comp.get("text", "-")),
            ("class / type", comp.get("type", "-")),
            ("bounds (坐标范围)", f"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]"),
            ("size (尺寸宽高)", f"{comp['width']} × {comp['height']}"),
            ("clickable (可点击)", str(raw.get("clickable", "-"))),
            ("enabled (可用状态)", str(raw.get("enabled", "-"))),
            ("focusable (可获焦点)", str(raw.get("focusable", "-"))),
            ("focused (当前聚焦)", str(raw.get("focused", "-"))),
            ("scrollable (可滚动)", str(raw.get("scrollable", "-"))),
            ("visible (可见性)", str(raw.get("visible", "-"))),
            ("xpath (完整绝对路径)", comp.get("xpath", "-")),
        ]

        known_keys = {"id", "key", "text", "originalText", "type", "bounds", "bundleName", "clickable", "enabled", "focusable", "focused", "scrollable", "visible"}
        for k, v in raw.items():
            if k not in known_keys:
                display_attrs.append((f"raw: {k}", str(v)))

        self.table_attrs.setUpdatesEnabled(False)
        self.table_attrs.setRowCount(len(display_attrs))
        for row, (k, v) in enumerate(display_attrs):
            k_item = QTableWidgetItem(str(k))
            v_item = QTableWidgetItem(str(v))
            v_item.setToolTip(str(v))
            if any(key in k for key in ("id", "text", "class", "xpath", "bounds", "size")):
                k_item.setForeground(QColor("#0284c7"))
                v_item.setForeground(QColor("#d97706"))
                k_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            else:
                k_item.setForeground(QColor("#64748b"))
                v_item.setForeground(QColor("#0f172a"))
            self.table_attrs.setItem(row, 0, k_item)
            self.table_attrs.setItem(row, 1, v_item)
        self.table_attrs.setUpdatesEnabled(True)

    # --------------------------------------------------------------------------
    # 核心新增：实时输入同步 (Live Input & Device Sync)
    # --------------------------------------------------------------------------

    def sync_live_input(self):
        """将实时输入框中的文字下发到鸿蒙真机，并即时同步全量视图"""
        curr_id = self.canvas.selected_node_id
        if not curr_id:
            QMessageBox.information(self, "提示", "请先在左侧或 DOM 树中选择目标输入框/编辑框组件！")
            return

        text = self.edit_live_input.text()
        self.direct_send_keys_to_element(curr_id, text)


    def direct_tap_element(self, node_id: str):
        comp = self.comp_map.get(node_id)
        if comp and self.current_udid:
            cx, cy = comp["center_x"], comp["center_y"]
            DeviceController.tap(self.current_platform, self.current_udid, cx, cy)
            self.refresh_screen_and_dom()


    def direct_send_keys_to_element(self, node_id: str, text: str):
        """
        向目标组件下发文本，并实现零延迟的视图与真机双向实时同步：
        1. 跨平台指令下发到真机执行物理输入
        2. 立即就地更新内存中该节点的 text 与 XPath 表达式
        3. 即时刷新 DOM 树、属性表格、实时输入框
        4. 异步刷新真机原画截图并重新锚定当前节点
        """
        comp = self.comp_map.get(node_id)
        if not comp or not self.current_udid:
            return

        cx, cy = comp["center_x"], comp["center_y"]
        DeviceController.input_text(self.current_platform, self.current_udid, text, cx, cy)

        # 1. 立即就地同步内存对象中的属性
        comp["text"] = text
        comp["raw_attributes"]["text"] = text
        comp["raw_attributes"]["originalText"] = text

        # 2. 立即更新推荐定位代码
        c_type = comp.get("type", "Component")
        c_id = comp.get("id", "")
        if self.current_platform == "android":
            if c_id:
                rec_xpath = f"//*[@resource-id='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
            elif text:
                rec_xpath = f"//*[@text='{text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//*[@text='{text}']\")"
            else:
                rec_xpath = comp.get("xpath", "")
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"
        elif self.current_platform == "ios":
            if c_id:
                rec_xpath = f"//*[@name='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ACCESSIBILITY_ID, '{c_id}')"
            elif text:
                rec_xpath = f"//*[@label='{text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//*[@label='{text}']\")"
            else:
                rec_xpath = comp.get("xpath", "")
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"
        else:
            if c_id:
                rec_xpath = f"//{c_type}[@id='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
            elif text:
                rec_xpath = f"//{c_type}[@text='{text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{c_type}[@text='{text}']\")"
            else:
                rec_xpath = comp.get("xpath", "")
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"

        comp["rec_xpath"] = rec_xpath
        comp["rec_py"] = rec_py

        # 3. 立即就地更新 DOM 树该节点标签
        item = self.tree_item_map.get(node_id)
        if item:
            bounds_str = f"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]"
            short_t = text if len(text) <= 22 else text[:22] + "..."
            id_attr = f' id="{c_id}"' if c_id else ""
            txt_attr = f' text="{short_t}"' if text else ""
            item.setText(0, f"<{c_type}{id_attr}{txt_attr} bounds=\"{bounds_str}\">")

        # 4. 立即更新右侧属性表与实时输入框
        self.update_selected_element_panel(node_id)

        # 5. 极速模式：仅异步刷新真机最新原画截图，0.3 秒无感更新左侧视窗，不重构庞大的 DOM 树
        self.refresh_screen_only()

    def action_element_clear(self):
        """清空该输入框/编辑框内容并即时同步"""
        curr_id = self.canvas.selected_node_id
        comp = self.comp_map.get(curr_id)
        if comp and self.current_udid:
            cx, cy = comp["center_x"], comp["center_y"]
            DeviceController.clear_text(self.current_platform, self.current_udid, cx, cy)
            
            # 本地属性立即同步清空
            comp["text"] = ""
            comp["raw_attributes"]["text"] = ""
            comp["raw_attributes"]["originalText"] = ""
            self.edit_live_input.setText("")
            self.update_selected_element_panel(curr_id)
            
            # 后台快速刷新最新截图
            self.refresh_screen_only()

    def copy_to_clip(self, text: str):
        if text:
            QApplication.clipboard().setText(text)
            short_preview = text if len(text) <= 32 else text[:32] + "..."
            self.show_toast(f"✅ 已复制: {short_preview}", duration_ms=1000)

    def show_toast(self, message: str, duration_ms: int = 1000):
        """展示无阻塞轻量 Toast 提示，默认 1 秒后自动消失"""
        if not hasattr(self, "toast") or self.toast is None:
            self.toast = ToastNotification(self)
        self.toast.show_message(message, duration_ms)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toast") and self.toast and self.toast.isVisible():
            parent_rect = self.rect()
            x = (parent_rect.width() - self.toast.width()) // 2
            y = (parent_rect.height() - self.toast.height()) // 2
            self.toast.move(x, y)


    def changeEvent(self, event):
        """主视窗状态变化监听：从最小化恢复时，保证子任务窗口不丢失并提升"""
        if event.type() == QEvent.Type.WindowStateChange:
            if not self.isMinimized() and hasattr(self, "search_dialog") and self.search_dialog:
                if self.search_dialog.isVisible() and not self.search_dialog.isMinimized():
                    self.search_dialog.raise_()
        elif event.type() == QEvent.Type.ActivationChange:
            if hasattr(self, "search_dialog") and self.search_dialog and self.search_dialog.isVisible():
                self.search_dialog._update_stay_on_top_state()
        super().changeEvent(event)

    def closeEvent(self, event):
        """关闭主视窗时联动关闭独立查找器子任务窗口与实时投屏流，杜绝后台游离进程"""
        if getattr(self, "screencast_worker", None) is not None:
            try:
                self.screencast_worker.stop()
                self.screencast_worker.wait(500)
            except Exception:
                pass
        if hasattr(self, "search_dialog") and self.search_dialog:
            self.search_dialog.close()
        super().closeEvent(event)


def main():
    # 在 Windows 系统上显式声明进程级 AppUserModelID，使应用下的所有顶级子窗口在任务栏聚合显示多任务缩略图卡片
    if sys.platform == "win32":
        try:
            import ctypes
            myappid = "santiao.im.autotest.harmony.inspector"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setWindowIcon(create_modern_app_icon())
    window = HarmonyAppiumInspector()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
