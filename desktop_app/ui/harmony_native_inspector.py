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
import ast
import base64
import contextlib
import json
import os
import random
import re
import shutil
import socket
import logging
import psutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
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
try:
    from PyQt6.QtSvg import QSvgRenderer
    _HAS_QTSVG = True
except (ImportError, ModuleNotFoundError):
    QSvgRenderer = None
    _HAS_QTSVG = False
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLayout, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter, QStyle,
    QStyledItemDelegate, QStyleOptionViewItem, QTableWidget, QTableWidgetItem, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)


# ==============================================================================
# 现代矢量级 Retina 应用图标生成器 (High-End Studio Inspector Icon)
# ==============================================================================

def create_modern_app_icon() -> QIcon:
    """
    动态生成高定多分辨率矢量级 Retina 审查器专属图标：
    1. 优先探测本地自定义图标 (desktop_app/assets/icons/app_logo.svg 或 .png)；
    2. 采用 Apple/Linear 顶级工业设计规范：深邃曜石墨蓝渐变超椭圆底板 (Squircle)；
    3. 带有 1px 细微光玻璃态内轮廓倒角，告别塑料感；
    4. 核心图形为精密的四角光学雷达对焦卡尺 + 双层多维 UI 透视组件卡片 + 翡翠绿核心呼吸光点，
       极富科技品质与空间透视感，与 SanT 品牌视觉完美契合。
    """
    # 优先检查本地是否配置了专属高清现成图标
    local_custom_candidates = [
        os.path.join(SmartPathResolver.get_project_root(), "desktop_app", "assets", "icons", "app_logo.svg"),
        os.path.join(SmartPathResolver.get_project_root(), "desktop_app", "assets", "icons", "app_logo.png"),
        os.path.join(SmartPathResolver.get_project_root(), "desktop_app", "resources", "app_icon.png"),
    ]
    for cand in local_custom_candidates:
        if os.path.exists(cand):
            custom_icon = QIcon(cand)
            if not custom_icon.isNull():
                return custom_icon

    icon = QIcon()
    for size in (16, 24, 28, 32, 48, 64, 128):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        scale = size / 64.0

        # 1. 高定曜石墨深蓝流光超椭圆外壳 (Squircle)
        pad = max(0.8, 1.2 * scale)
        rect = QRectF(pad, pad, float(size - 2 * pad), float(size - 2 * pad))
        radius = float(size) * 0.24
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # 顶级深海曜石微渐变: #0b1329 (深空极夜) -> #111827 -> #1e3a8a (克莱因深海)
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0.0, QColor("#090d16"))
        grad.setColorAt(0.40, QColor("#111827"))
        grad.setColorAt(1.0, QColor("#1e3a8a"))
        p.fillPath(path, QBrush(grad))

        # 2. 细微玻璃态高光内边缘 (Apple 风格 1px 微光倒角)
        pen_border = QPen(QColor(255, 255, 255, 45), max(1.0, 1.0 * scale))
        p.setPen(pen_border)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # 3. 四角精密微米对焦点 (Precision Viewfinder Brackets)
        b_margin = 13.0 * scale
        b_len = 7.0 * scale
        pen_bracket = QPen(QColor(56, 189, 248, 225), max(1.4, 2.0 * scale))
        pen_bracket.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_bracket)

        x1 = b_margin
        y1 = b_margin
        x2 = size - b_margin
        y2 = size - b_margin

        # 左上角
        p.drawLine(QPointF(x1, y1 + b_len), QPointF(x1, y1))
        p.drawLine(QPointF(x1, y1), QPointF(x1 + b_len, y1))
        # 右上角
        p.drawLine(QPointF(x2 - b_len, y1), QPointF(x2, y1))
        p.drawLine(QPointF(x2, y1), QPointF(x2, y1 + b_len))
        # 左下角
        p.drawLine(QPointF(x1, y2 - b_len), QPointF(x1, y2))
        p.drawLine(QPointF(x1, y2), QPointF(x1 + b_len, y2))
        # 右下角
        p.drawLine(QPointF(x2 - b_len, y2), QPointF(x2, y2))
        p.drawLine(QPointF(x2, y2), QPointF(x2, y2 - b_len))

        # 4. 中心多维层级透视卡片 (UI Layer Stack)
        cx = float(size) / 2.0
        cy = float(size) / 2.0

        # 底层虚化层级卡片 (淡蓝微光)
        card_w = 16.0 * scale
        card_h = 16.0 * scale
        p.setPen(QPen(QColor(14, 165, 233, 120), max(1.0, 1.2 * scale)))
        p.setBrush(QBrush(QColor(14, 165, 233, 40)))
        p.drawRoundedRect(QRectF(cx - card_w / 2.0 - 2.5 * scale, cy - card_h / 2.0 - 2.5 * scale, card_w, card_h), 2.5 * scale, 2.5 * scale)

        # 顶层聚焦层级卡片 (纯白高光，锐利透视)
        p.setPen(QPen(QColor(255, 255, 255, 240), max(1.2, 1.6 * scale)))
        p.setBrush(QBrush(QColor(255, 255, 255, 45)))
        p.drawRoundedRect(QRectF(cx - card_w / 2.0 + 2.0 * scale, cy - card_h / 2.0 + 2.0 * scale, card_w, card_h), 2.5 * scale, 2.5 * scale)

        # 5. 中心全息探测聚焦点 (翡翠光球 / Quantum Spark，呼应三条 Logo)
        dot_r = max(1.8, 2.8 * scale)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#22c55e")))
        p.drawEllipse(QPointF(cx + 2.0 * scale, cy + 2.0 * scale), dot_r, dot_r)

        p.end()
        icon.addPixmap(pix)
    return icon


# ==============================================================================
# 全局现成矢量与网络图标引擎 (Official SVG & Remote Network Icon Engine)
# 1. 采用大厂官方现成顶级矢量设计规范 (Lucide Icons / Remix Icons 标准规范)
# 2. 支持直接传入网络 URL 下载并自动持久化缓存到本地 desktop_app/assets/icons/
# 3. 支持用户直接向本地 desktop_app/assets/icons/ 文件夹添加现成的 .svg / .png 文件
# 4. 基于 QtSvg 实时高清无损渲染，动态自适应按状态染色 (科技蓝/纯白/冷灰)
# ==============================================================================

# 本地现成图标资源存储根目录
LOCAL_ICON_DIR = os.path.normpath(
    os.path.join(SmartPathResolver.get_project_root(), "desktop_app", "assets", "icons")
)
os.makedirs(LOCAL_ICON_DIR, exist_ok=True)

# 官方标准现成开源 SVG 模板库 (业界顶级 Lucide 官方矢量规范)
_OFFICIAL_SVG_TEMPLATES = {
    "refresh": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>""",
    "target": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="22" x2="18" y1="12" y2="12"/><line x1="6" x2="2" y1="12" y2="12"/><line x1="12" x2="12" y1="6" y2="2"/><line x1="12" x2="12" y1="22" y2="18"/><circle cx="12" cy="12" r="2.5" fill="{color}"/></svg>""",
    "tap": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 3 7.07 16.97 2.51-7.39 7.39-2.51L3 3z" fill="{color}" fill-opacity="0.2"/><path d="m13 13 6 6"/></svg>""",
    "search": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" x2="16.65" y1="21" y2="16.65"/></svg>""",
    "cast": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" x2="16" y1="21" y2="21"/><line x1="12" x2="12" y1="17" y2="21"/><polygon points="10 7 15 10 10 13 10 7" fill="{color}" stroke="{color}"/></svg>""",
    "sync": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 3 4 4-4 4"/><path d="M20 7H4"/><path d="m8 21-4-4 4-4"/><path d="M4 17h16"/></svg>""",
    "copy": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="13" height="13" x="9" y="9" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>""",
    "save": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>""",
    "expand": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" x2="14" y1="3" y2="10"/><line x1="3" x2="10" y1="21" y2="14"/></svg>""",
    "collapse": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" x2="21" y1="10" y2="3"/><line x1="3" x2="10" y1="21" y2="14"/></svg>""",
    "send": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" x2="11" y1="2" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>""",
    "clear": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>""",
    "play": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3" fill="{color}"/></svg>""",
    "check": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>""",
    "spinner": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>""",
    "loader": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>"""
}

# 自动将官方现成 SVG 模板持久化落盘至本地 assets/icons 目录
for _name, _raw_svg in _OFFICIAL_SVG_TEMPLATES.items():
    _svg_file = os.path.join(LOCAL_ICON_DIR, f"{_name}.svg")
    try:
        with open(_svg_file, "w", encoding="utf-8") as _f:
            _f.write(_raw_svg.replace("{color}", "currentColor"))
    except Exception:
        pass

def import_network_icon(url: str, save_name: str = "") -> Optional[str]:
    """从网络 URL 下载现成图标并自动导入至本地图标库缓存中"""
    try:
        if not save_name:
            parsed = urllib.parse.urlparse(url)
            save_name = os.path.basename(parsed.path) or f"icon_{int(time.time())}.svg"
        if not save_name.endswith((".svg", ".png", ".jpg", ".webp")):
            save_name += ".svg"
        dest_path = os.path.join(LOCAL_ICON_DIR, save_name)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = resp.read()
            with open(dest_path, "wb") as f:
                f.write(data)
        return dest_path
    except Exception as e:
        logger.warning(f"下载网络图标失败: {url}, 异常: {e}")
        return None

_TECH_ICON_CACHE: Dict[Tuple[str, str, int, int], QIcon] = {}

def get_tech_icon(name: str, color: str = "#0284c7", size: int = 24, rotation: float = 0.0) -> QIcon:
    """
    全方位现成与网络图标加载器：
    1. 整体按钮图标垂直微调向下移动 2 个像素 (Y_OFFSET = 2)，彻底对齐按钮文本视觉水平中线；
    2. 支持 rotation 浮点角度旋转参数，为刷新/同步等操作提供原位 Loading 动态转圈状态；
    3. 支持 QtSvg Retina 视网膜渲染，无模块时平滑降级至纯原生 QPainter 高清抗锯齿矢量绘制；
    4. 带有内存级缓存，杜绝高频旋转和重复解析的 I/O 损耗。
    """
    rot_int = int(round(rotation)) % 360
    cache_key = (name, color, size, rot_int)
    if cache_key in _TECH_ICON_CACHE:
        return _TECH_ICON_CACHE[cache_key]

    # 1. 网络 URL 图标导入处理
    if name.startswith(("http://", "https://")):
        cached_file = import_network_icon(name)
        if cached_file and os.path.exists(cached_file):
            name = os.path.splitext(os.path.basename(cached_file))[0]

    # 2. 检查本地 assets/icons 现成文件
    local_svg = os.path.join(LOCAL_ICON_DIR, f"{name}.svg")
    local_png = os.path.join(LOCAL_ICON_DIR, f"{name}.png")

    svg_content = ""
    if os.path.exists(local_svg):
        try:
            with open(local_svg, "r", encoding="utf-8") as f:
                svg_content = f.read()
        except Exception:
            pass

    name_alias = {
        "reload": "refresh",
        "select": "target",
        "inspect": "target",
        "pointer": "tap",
        "touch": "tap",
        "find": "search",
        "screen": "cast",
        "live": "cast",
        "lightning": "sync",
        "clone": "copy",
        "export": "save",
        "plus": "expand",
        "minus": "collapse",
        "trash": "clear",
        "clean": "clear",
        "loading": "spinner",
        "spin": "spinner",
        "loader": "spinner"
    }.get(name, name)

    if not svg_content:
        svg_content = _OFFICIAL_SVG_TEMPLATES.get(name_alias, "")

    Y_OFFSET = 2.0  # 整体按钮前面的图标向下移动两个像素

    # 3. 若当前 Python 环境支持 QtSvg，优先进行 Retina 视网膜矢量渲染与动态染色
    if _HAS_QTSVG and QSvgRenderer is not None and svg_content:
        try:
            colored_svg = svg_content.replace("{color}", color).replace("currentColor", color)
            icon = QIcon()
            renderer = QSvgRenderer(QByteArray(colored_svg.encode("utf-8")))
            if renderer.isValid():
                for s in (16, 20, 24, 32, 48):
                    pix = QPixmap(s, s)
                    pix.fill(Qt.GlobalColor.transparent)
                    p = QPainter(pix)
                    p.setRenderHint(QPainter.RenderHint.Antialiasing)
                    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    if rot_int != 0:
                        p.translate(s / 2.0, s / 2.0 + Y_OFFSET)
                        p.rotate(rot_int)
                        p.translate(-s / 2.0, -(s / 2.0 + Y_OFFSET))
                    # 目标矩形向下平移 2 像素
                    renderer.render(p, QRectF(0, Y_OFFSET, s, max(1.0, s - Y_OFFSET)))
                    p.end()
                    icon.addPixmap(pix)
                _TECH_ICON_CACHE[cache_key] = icon
                return icon
        except Exception:
            pass

    # 4. 本地 PNG 现成位图兜底加载
    if os.path.exists(local_png):
        src_pix = QPixmap(local_png)
        icon = QIcon()
        for s in (16, 20, 24, 32, 48):
            pix = QPixmap(s, s)
            pix.fill(Qt.GlobalColor.transparent)
            p = QPainter(pix)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            if rot_int != 0:
                p.translate(s / 2.0, s / 2.0 + Y_OFFSET)
                p.rotate(rot_int)
                p.translate(-s / 2.0, -(s / 2.0 + Y_OFFSET))
            p.drawPixmap(0, int(Y_OFFSET), s, int(max(1, s - Y_OFFSET)), src_pix)
            p.end()
            icon.addPixmap(pix)
        _TECH_ICON_CACHE[cache_key] = icon
        return icon

    # 5. 优雅降级：纯原生 QPainter 高清抗锯齿矢量绘制 (零外部模块依赖，向下偏移 2px)
    icon = QIcon()
    for s in (16, 20, 24, 32, 48):
        pix = QPixmap(s, s)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if rot_int != 0:
            p.translate(s / 2.0, s / 2.0 + Y_OFFSET)
            p.rotate(rot_int)
            p.translate(-s / 2.0, -(s / 2.0 + Y_OFFSET))

        pen = QPen(QColor(color), max(1.5, s / 12.0))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        pad = s * 0.16
        w = s - 2 * pad
        h = max(1.0, s - 2 * pad - Y_OFFSET)
        cx = s / 2.0
        cy = s / 2.0 + Y_OFFSET

        if name_alias in ("spinner", "loader", "loading"):
            r = w * 0.42
            rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
            p.drawArc(rect, 45 * 16, 275 * 16)
        elif name_alias in ("refresh", "sync"):
            r = w * 0.42
            rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
            p.drawArc(rect, 45 * 16, 270 * 16)
            p.drawLine(QPointF(cx + r, cy), QPointF(cx + r + 2.5, cy - 2.5))
            p.drawLine(QPointF(cx + r, cy), QPointF(cx + r - 2.5, cy - 2.5))
        elif name_alias in ("target", "inspect"):
            r = w * 0.44
            p.drawEllipse(QPointF(cx, cy), r, r)
            p.drawEllipse(QPointF(cx, cy), r * 0.35, r * 0.35)
            p.drawLine(QPointF(cx - r - 1.5, cy), QPointF(cx + r + 1.5, cy))
            p.drawLine(QPointF(cx, cy - r - 1.5), QPointF(cx, cy + r + 1.5))
        elif name_alias in ("tap", "touch"):
            p.drawEllipse(QPointF(cx, cy), w * 0.25, w * 0.25)
            p.drawEllipse(QPointF(cx, cy), w * 0.44, w * 0.44)
        elif name_alias in ("search", "find"):
            r = w * 0.32
            p.drawEllipse(QPointF(cx - 1.5, cy - 1.5), r, r)
            p.drawLine(QPointF(cx - 1.5 + r * 0.7, cy - 1.5 + r * 0.7), QPointF(cx + w * 0.44, cy + h * 0.44))
        elif name_alias in ("cast", "screen"):
            p.drawRoundedRect(QRectF(pad, pad + Y_OFFSET, w, h * 0.72), 2, 2)
            p.drawLine(QPointF(cx, pad + Y_OFFSET + h * 0.72), QPointF(cx, pad + Y_OFFSET + h * 0.95))
            p.drawLine(QPointF(cx - w * 0.3, pad + Y_OFFSET + h * 0.95), QPointF(cx + w * 0.3, pad + Y_OFFSET + h * 0.95))
        elif name_alias in ("copy", "clone"):
            p.drawRoundedRect(QRectF(pad + w * 0.22, pad + Y_OFFSET, w * 0.68, h * 0.68), 2, 2)
            p.drawRoundedRect(QRectF(pad, pad + Y_OFFSET + h * 0.22, w * 0.68, h * 0.68), 2, 2)
        elif name_alias in ("save", "export"):
            p.drawRoundedRect(QRectF(pad, pad + Y_OFFSET, w, h), 2, 2)
            p.drawRect(QRectF(pad + w * 0.25, pad + Y_OFFSET, w * 0.5, h * 0.35))
        elif name_alias in ("expand", "plus"):
            p.drawLine(QPointF(cx - w * 0.35, cy), QPointF(cx + w * 0.35, cy))
            p.drawLine(QPointF(cx, cy - h * 0.35), QPointF(cx, cy + h * 0.35))
        elif name_alias in ("collapse", "minus"):
            p.drawLine(QPointF(cx - w * 0.35, cy), QPointF(cx + w * 0.35, cy))
        elif name_alias in ("clear", "trash"):
            p.drawLine(QPointF(cx - w * 0.3, cy - h * 0.3), QPointF(cx + w * 0.3, cy + h * 0.3))
            p.drawLine(QPointF(cx + w * 0.3, cy - h * 0.3), QPointF(cx - w * 0.3, cy + h * 0.3))
        elif name_alias in ("phone", "device"):
            p.drawRoundedRect(QRectF(pad + w * 0.15, pad + Y_OFFSET, w * 0.7, h), 3, 3)
            p.drawPoint(QPointF(cx, pad + Y_OFFSET + h * 0.85))
        else:
            p.drawRoundedRect(QRectF(pad, pad + Y_OFFSET, w, h), 3, 3)

        p.end()
        icon.addPixmap(pix)

    _TECH_ICON_CACHE[cache_key] = icon
    return icon


class ButtonSpinner:
    """
    工业级通用按钮 Loading 转圈控制器：
    1. 统一使用专属圆圈 Loading 图标 (Circular Spinner) 进行 360° 加载转圈，杜绝业务图标自身旋转；
    2. 加载结束时，自动平滑恢复该按钮原本应有的业务静态图标 (如投屏/双向箭头/刷新/播放)；
    3. 任务完成后恢复原始文字与激活状态，保持高品质科技感交互。
    """
    def __init__(self, button: QPushButton, orig_icon_name: str = "refresh", icon_color: str = "#0284c7"):
        self.button = button
        self.orig_icon_name = orig_icon_name
        self.icon_color = icon_color
        self.loading_icon_name = "spinner"  # 无论什么按钮，加载时统一使用标准圆圈 Loading 图标
        self.angle = 0
        self.timer = QTimer(button)
        self.timer.timeout.connect(self._on_tick)
        self._orig_text = button.text()

    def start(self, loading_text: Optional[str] = None):
        self._orig_text = self.button.text()
        if loading_text is not None:
            self.button.setText(loading_text)
        self.angle = 0
        self.button.setIcon(get_tech_icon(self.loading_icon_name, self.icon_color, rotation=0.0))
        self.timer.start(35)  # 约 28fps 平滑顺畅旋转

    def _on_tick(self):
        self.angle = (self.angle + 30) % 360
        self.button.setIcon(get_tech_icon(self.loading_icon_name, self.icon_color, rotation=self.angle))

    def stop(self, restore_text: bool = True):
        self.timer.stop()
        if restore_text and self._orig_text:
            self.button.setText(self._orig_text)
        self.button.setIcon(get_tech_icon(self.orig_icon_name, self.icon_color, rotation=0.0))
        self.button.setEnabled(True)


# ==============================================================================
# 全局统一轻奢圆角置顶弹窗系统 (ModernMessageBox & ModernInputDialog)
# 1. 纯白轻奢卡片外观 (border-radius: 12px, 柔和高级投影, 与整个审查器 UI 风格一致)
# 2. 绝对层级置顶强化 (Qt WindowStaysOnTopHint + Win32 SetWindowPos HWND_TOPMOST)
#    彻底解决弹窗被【元素定位与查找器】等浮窗遮挡的问题
# ==============================================================================

class FlowLayout(QLayout):
    """自适应流式换行布局：窗口宽时单行排布，窗口缩小时自动平滑折行，杜绝按钮重叠与截断"""

    def __init__(self, parent=None, margin: int = 0, h_spacing: int = 8, v_spacing: int = 6):
        super().__init__(parent)
        self._items: list = []
        self._h_space = h_spacing
        self._v_space = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def addWidgetRight(self, widget: QWidget):
        """添加标记为靠右对齐的控件（单行排布时自动推至行尾最右侧，折行后正常顺排）"""
        widget.setProperty("_flow_align_right", True)
        self.addWidget(widget)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        total_w = 0
        max_h = 0
        visible_count = 0
        for item in self._items:
            wid = item.widget()
            if wid is not None and wid.isHidden():
                continue
            hint = item.sizeHint()
            total_w += hint.width()
            max_h = max(max_h, hint.height())
            visible_count += 1
        if visible_count > 1:
            total_w += self._h_space * (visible_count - 1)
        m = self.contentsMargins()
        return QSize(total_w + m.left() + m.right(), max_h + m.top() + m.bottom())

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            wid = item.widget()
            if wid is not None and wid.isHidden():
                continue
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0
        row_items: list = []

        def _flush_row(items_in_row: list, row_y: int, row_h: int):
            if test_only or not items_in_row:
                return
            # 检查本行末尾控件是否标记为右对齐；若是，将其整体推至行尾最右侧以还原标准左右分区布局
            right_indices = [
                i for i, (it, _, _) in enumerate(items_in_row)
                if it.widget() is not None and bool(it.widget().property("_flow_align_right"))
            ]
            if right_indices and right_indices[0] > 0:
                split_idx = right_indices[0]
                right_chunk = items_in_row[split_idx:]
                right_total_w = sum(h.width() for _, _, h in right_chunk) + self._h_space * (len(right_chunk) - 1)
                prev_it, prev_x, prev_h = items_in_row[split_idx - 1]
                left_end = prev_x + prev_h.width() + self._h_space
                target_start = effective.right() + 1 - right_total_w
                if target_start > left_end:
                    cur_rx = target_start
                    for i in range(split_idx, len(items_in_row)):
                        it, _, h = items_in_row[i]
                        items_in_row[i] = (it, cur_rx, h)
                        cur_rx += h.width() + self._h_space

            for r_item, r_x, r_hint in items_in_row:
                offset_y = max(0, (row_h - r_hint.height()) // 2)
                r_item.setGeometry(QRect(QPoint(r_x, row_y + offset_y), r_hint))

        for item in self._items:
            wid = item.widget()
            if wid is not None and wid.isHidden():
                continue
            hint = item.sizeHint()
            next_x = x + hint.width() + self._h_space
            if next_x - self._h_space > effective.right() + 1 and line_height > 0:
                _flush_row(row_items, y, line_height)
                row_items = []
                x = effective.x()
                y = y + line_height + self._v_space
                next_x = x + hint.width() + self._h_space
                line_height = 0

            row_items.append((item, x, hint))
            x = next_x
            line_height = max(line_height, hint.height())

        _flush_row(row_items, y, line_height)
        total_h = y + line_height - rect.y() + m.bottom() + 2
        if not test_only:
            p = self.parentWidget()
            if p is not None and p.objectName() == "topBar" and p.minimumHeight() != total_h:
                p.setMinimumHeight(total_h)
        return total_h


class ModernMessageBox(QDialog):
    """
    全中文轻奢圆角置顶消息对话框：
    - 统一圆角微光拟物风格 (无生硬系统灰色边框)
    - 自动吸附屏幕或父窗口中央
    - 强化最高层级置顶 (最高优先级的 Z-Order，绝不被任何浮窗遮挡)
    """
    IconNone = 0
    IconInformation = 1
    IconWarning = 2
    IconCritical = 3
    IconQuestion = 4

    def __init__(
        self,
        title: str = "提示",
        text: str = "",
        icon_type: int = IconInformation,
        buttons: list[str] = None,
        parent=None,
        center_align: bool = False,
    ):
        super().__init__(parent)
        self.icon_type = icon_type
        self.center_align = center_align
        self.clicked_button = ""
        self._drag_pos = None

        # 1. 无框 + 置顶 + 对话框 + 透明底板
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(title)
        self.setWindowIcon(create_modern_app_icon())

        if buttons is None:
            buttons = ["确定"]
        self.buttons = buttons

        # 2. 布局初始化
        self._init_ui(title, text)

    def _init_ui(self, title: str, text: str):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(0)

        # 卡片本体容器
        self.card = QFrame(self)
        self.card.setObjectName("ModernMsgCard")
        self.card.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.card.setAutoFillBackground(True)
        self.card.setStyleSheet("""
            QFrame#ModernMsgCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(15, 23, 42, 50))
        shadow.setOffset(0, 6)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 1. 顶部标题栏
        title_bar = QWidget(self.card)
        title_bar.setFixedHeight(44)
        title_bar.setAutoFillBackground(True)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid #f1f5f9;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 12, 0)
        title_layout.setSpacing(8)

        lbl_title_icon = QLabel()
        title_icon_map = {
            self.IconCritical: "❌",
            self.IconWarning: "⚠️",
            self.IconInformation: "ℹ️",
            self.IconQuestion: "❓",
        }
        lbl_title_icon.setText(title_icon_map.get(self.icon_type, "💡"))
        lbl_title_icon.setStyleSheet("font-size: 14px; background-color: #ffffff; border: none;")
        title_layout.addWidget(lbl_title_icon)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f172a; background-color: #ffffff; border: none;")
        title_layout.addWidget(lbl_title, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: none;
                border-radius: 4px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #ef4444;
            }
        """)
        btn_close.clicked.connect(self.reject)
        title_layout.addWidget(btn_close)
        card_layout.addWidget(title_bar)

        # 2. 中间内容区
        content_widget = QWidget(self.card)
        content_widget.setAutoFillBackground(True)
        content_widget.setStyleSheet("background-color: #ffffff; border: none;")

        lines = text.strip().split("\n", 1)
        headline = lines[0]
        detail = lines[1].strip() if len(lines) > 1 else ""

        badge = QLabel()
        badge.setFixedSize(46, 46)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.icon_type == self.IconCritical:
            badge.setText("✕")
            badge.setStyleSheet("background-color: #fee2e2; color: #dc2626; font-size: 20px; font-weight: 900; border-radius: 23px; border: 1px solid #fecaca;")
        elif self.icon_type == self.IconWarning:
            badge.setText("!")
            badge.setStyleSheet("background-color: #fef3c7; color: #d97706; font-size: 22px; font-weight: 900; border-radius: 23px; border: 1px solid #fde68a;")
        elif self.icon_type == self.IconQuestion:
            badge.setText("?")
            badge.setStyleSheet("background-color: #e0f2fe; color: #0284c7; font-size: 22px; font-weight: 900; border-radius: 23px; border: 1px solid #bae6fd;")
        else:
            badge.setText("ℹ")
            badge.setStyleSheet("background-color: #e0f2fe; color: #0284c7; font-size: 20px; font-weight: 900; border-radius: 23px; border: 1px solid #bae6fd;")

        if self.center_align:
            # 顶部「左图标 + 右标题」横向布局 + 中间全宽紧凑详情框，无多余空白
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(20, 16, 20, 16)
            content_layout.setSpacing(12)

            badge.setFixedSize(38, 38)
            badge.setStyleSheet(badge.styleSheet().replace("border-radius: 23px", "border-radius: 19px").replace("font-size: 22px", "font-size: 18px").replace("font-size: 20px", "font-size: 17px"))

            header_row = QHBoxLayout()
            header_row.setContentsMargins(0, 0, 0, 0)
            header_row.setSpacing(12)
            header_row.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)

            lbl_head = QLabel(headline)
            lbl_head.setWordWrap(True)
            lbl_head.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            lbl_head.setStyleSheet("color: #0f172a; font-size: 14px; font-weight: 600; line-height: 1.45; background-color: #ffffff;")
            lbl_head.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            header_row.addWidget(lbl_head, 1)
            content_layout.addLayout(header_row)

            if detail:
                lbl_detail = QLabel(detail)
                lbl_detail.setWordWrap(True)
                lbl_detail.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                lbl_detail.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                lbl_detail.setStyleSheet("""
                    QLabel {
                        background-color: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        color: #334155;
                        font-size: 12.5px;
                        font-family: 'Microsoft YaHei UI', Consolas, sans-serif;
                        line-height: 1.65;
                        padding: 12px 14px;
                    }
                """)
                lbl_detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                content_layout.addWidget(lbl_detail)
        else:
            content_layout = QHBoxLayout(content_widget)
            content_layout.setContentsMargins(20, 18, 20, 16)
            content_layout.setSpacing(16)
            content_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

            # 右侧文本排版
            right_layout = QVBoxLayout()
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(8)

            lbl_head = QLabel(headline)
            lbl_head.setWordWrap(True)
            lbl_head.setStyleSheet("color: #0f172a; font-size: 14px; font-weight: 600; line-height: 1.4; background-color: #ffffff;")
            lbl_head.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            right_layout.addWidget(lbl_head)

            if detail:
                txt_detail = QPlainTextEdit()
                txt_detail.setReadOnly(True)
                txt_detail.setPlainText(detail)
                txt_detail.setStyleSheet("""
                    QPlainTextEdit {
                        background-color: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 6px;
                        color: #334155;
                        font-size: 12px;
                        font-family: Consolas, 'Courier New', monospace;
                        padding: 8px;
                    }
                """)
                txt_detail.setMaximumHeight(160)
                txt_detail.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                right_layout.addWidget(txt_detail)

            content_layout.addLayout(right_layout, 1)

        card_layout.addWidget(content_widget, 1)

        # 3. 底部按钮栏
        btn_bar = QWidget(self.card)
        btn_bar.setFixedHeight(54)
        btn_bar.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid #f1f5f9;
            }
        """)
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(16, 0, 20, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        for btn_text in self.buttons:
            btn = QPushButton(btn_text)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            is_primary = (btn_text in ("确定", "OK", "是", "Yes", "保存", "立即安装"))
            if is_primary:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7;
                        color: #ffffff;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: 600;
                        padding: 0 18px;
                    }
                    QPushButton:hover { background-color: #0369a1; }
                    QPushButton:pressed { background-color: #075985; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #475569;
                        border: 1px solid #cbd5e1;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: 500;
                        padding: 0 16px;
                    }
                    QPushButton:hover { background-color: #f1f5f9; color: #0f172a; border-color: #94a3b8; }
                """)
            btn.clicked.connect(lambda checked=False, val=btn_text: self._on_btn_clicked(val))
            btn_layout.addWidget(btn)

        if self.center_align:
            btn_layout.addStretch()

        card_layout.addWidget(btn_bar)
        root_layout.addWidget(self.card)

        self.setMinimumWidth(440)
        self.setMaximumWidth(580)
        self.adjustSize()

    def _on_btn_clicked(self, val: str):
        self.clicked_button = val
        if val in ("确定", "OK", "是", "Yes", "保存", "立即安装"):
            self.accept()
        else:
            self.reject()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        # 智能居中于当前前台活跃窗口或屏幕视口中心，彻底消除被【元素定位与查找器】等浮窗遮挡的问题
        target_rect = None
        active_w = QApplication.activeWindow()
        if active_w and active_w.isVisible() and active_w is not self:
            target_rect = active_w.frameGeometry()
        elif self.parentWidget() and self.parentWidget().isVisible():
            target_rect = self.parentWidget().frameGeometry()
        else:
            screen = QApplication.primaryScreen()
            if screen:
                target_rect = screen.availableGeometry()

        if target_rect:
            self.move(
                target_rect.center().x() - self.width() // 2,
                target_rect.center().y() - self.height() // 2
            )

        self.raise_()
        self.activateWindow()
        self._apply_native_topmost()

    def _apply_native_topmost(self):
        try:
            import ctypes
            hwnd = int(self.winId())
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_SHOWWINDOW = 0x0040
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            ctypes.windll.user32.BringWindowToTop(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    @classmethod
    def critical(cls, parent, title: str, text: str) -> None:
        dlg = cls(title=title, text=text, icon_type=cls.IconCritical, buttons=["确定"], parent=parent)
        dlg.exec()

    @classmethod
    def warning(cls, parent, title: str, text: str) -> None:
        dlg = cls(title=title, text=text, icon_type=cls.IconWarning, buttons=["确定"], parent=parent)
        dlg.exec()

    @classmethod
    def information(cls, parent, title: str, text: str) -> None:
        dlg = cls(title=title, text=text, icon_type=cls.IconInformation, buttons=["确定"], parent=parent)
        dlg.exec()

    @classmethod
    def question(cls, parent, title: str, text: str, buttons: list[str] = None) -> bool:
        if buttons is None:
            buttons = ["确定", "取消"]
        dlg = cls(title=title, text=text, icon_type=cls.IconQuestion, buttons=buttons, parent=parent)
        res = dlg.exec()
        return res == QDialog.DialogCode.Accepted or dlg.clicked_button in ("确定", "是", "Yes")


class ModernInputDialog(QDialog):
    """全中文轻奢圆角置顶输入弹窗 (替代系统默认直角 QInputDialog)"""
    def __init__(self, parent=None, title: str = "输入内容", label: str = "请输入内容:", default_text: str = ""):
        super().__init__(parent)
        self._drag_pos = None
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(title)
        self.setWindowIcon(create_modern_app_icon())

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)

        card = QFrame(self)
        card.setObjectName("ModernInputCard")
        card.setStyleSheet("""
            QFrame#ModernInputCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(15, 23, 42, 50))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 标题栏
        title_bar = QWidget(card)
        title_bar.setFixedHeight(44)
        title_bar.setStyleSheet("background-color: #ffffff; border-top-left-radius: 12px; border-top-right-radius: 12px; border-bottom: 1px solid #f1f5f9;")
        t_layout = QHBoxLayout(title_bar)
        t_layout.setContentsMargins(16, 0, 12, 0)
        lbl_t = QLabel(f"✏️ {title}")
        lbl_t.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f172a;")
        t_layout.addWidget(lbl_t, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("QPushButton { background: transparent; border: none; color: #94a3b8; font-size: 13px; font-weight: bold; } QPushButton:hover { background: #fee2e2; color: #ef4444; border-radius: 4px; }")
        btn_close.clicked.connect(self.reject)
        t_layout.addWidget(btn_close)
        card_layout.addWidget(title_bar)

        # 内容区
        body = QWidget(card)
        body.setStyleSheet("background-color: #ffffff;")
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(20, 18, 20, 18)
        b_layout.setSpacing(10)

        lbl_prompt = QLabel(label)
        lbl_prompt.setStyleSheet("font-size: 13px; color: #334155; font-weight: 500;")
        b_layout.addWidget(lbl_prompt)

        self.edit_input = QLineEdit(default_text)
        self.edit_input.setFixedHeight(36)
        self.edit_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0284c7;
            }
        """)
        self.edit_input.returnPressed.connect(self.accept)
        b_layout.addWidget(self.edit_input)
        card_layout.addWidget(body)

        # 底部按钮
        btn_bar = QWidget(card)
        btn_bar.setFixedHeight(52)
        btn_bar.setStyleSheet("background-color: #f8fafc; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; border-top: 1px solid #f1f5f9;")
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(16, 0, 20, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.setFixedHeight(32)
        btn_cancel.setStyleSheet("QPushButton { background: #ffffff; color: #475569; border: 1px solid #cbd5e1; border-radius: 6px; padding: 0 16px; font-size: 12px; } QPushButton:hover { background: #f1f5f9; }")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("确定")
        btn_ok.setFixedHeight(32)
        btn_ok.setStyleSheet("QPushButton { background: #0284c7; color: #ffffff; border: none; border-radius: 6px; padding: 0 18px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: #0369a1; }")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        card_layout.addWidget(btn_bar)

        root_layout.addWidget(card)
        self.setMinimumWidth(400)
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def showEvent(self, event):
        super().showEvent(event)
        target_rect = None
        active_w = QApplication.activeWindow()
        if active_w and active_w.isVisible() and active_w is not self:
            target_rect = active_w.frameGeometry()
        elif self.parentWidget() and self.parentWidget().isVisible():
            target_rect = self.parentWidget().frameGeometry()
        else:
            screen = QApplication.primaryScreen()
            if screen:
                target_rect = screen.availableGeometry()

        if target_rect:
            self.move(
                target_rect.center().x() - self.width() // 2,
                target_rect.center().y() - self.height() // 2
            )
        self.raise_()
        self.activateWindow()
        self._apply_native_topmost()
        self.edit_input.setFocus()

    def _apply_native_topmost(self):
        try:
            import ctypes
            hwnd = int(self.winId())
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_SHOWWINDOW = 0x0040
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            ctypes.windll.user32.BringWindowToTop(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    @classmethod
    def getText(cls, parent, title: str, label: str, default_text: str = "") -> tuple[str, bool]:
        dlg = cls(parent=parent, title=title, label=label, default_text=default_text)
        res = dlg.exec()
        if res == QDialog.DialogCode.Accepted:
            return dlg.edit_input.text().strip(), True
        return "", False

# 模块级透明映射，彻底杜绝任何系统原生直角灰色弹窗泄漏
QMessageBox = ModernMessageBox
QInputDialog = ModernInputDialog


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
    _relay_udid: str = ""
    _active_wda_url: str = "http://127.0.0.1:8100"

    @classmethod
    def kill_relays(cls, ports: Tuple[int, ...] = (9100,)):
        """
        工业级彻底终结孤儿 tidevice relay 进程并回收端口：
        1. 优雅终止当前类持有的 _relay_proc；
        2. 扫描 Windows 底层 netstat 并强行释放被独占的 8100/9100 端口，
           确保新旧 iPhone 切换时绝不发生 [WinError 10048] 端口冲突与流量串连。
        """
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

        if sys.platform == "win32":
            creationflags = 0x08000000
            my_pid = os.getpid()
            for port in ports:
                try:
                    out = subprocess.check_output(
                        f'netstat -ano | findstr ":{port} "',
                        shell=True,
                        text=True,
                        errors="ignore",
                        creationflags=creationflags
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
                                        creationflags=creationflags
                                    )
                except Exception:
                    pass

    _version_cache: Dict[str, str] = {}

    @classmethod
    def get_device_product_version(cls, udid: str) -> Optional[str]:
        """毫秒级高速查询目标 iOS 设备的系统版本 (优先内存缓存，0ms 零 I/O 阻塞)"""
        if not udid or udid.startswith("wda_localhost"):
            return None
        cached = cls._version_cache.get(udid)
        if cached:
            return cached
        import asyncio
        from pymobiledevice3.lockdown import create_using_usbmux
        async def _query():
            ld = await create_using_usbmux(serial=udid, autopair=False, connection_type="USB")
            try:
                ver = str(getattr(ld, "product_version", "") or "")
                if ver:
                    cls._version_cache[udid] = ver
                return ver
            finally:
                await ld.close()
        try:
            return asyncio.run(asyncio.wait_for(_query(), timeout=1.0))
        except Exception:
            return None

    @classmethod
    def test_wda_status(cls, url: str, timeout: float = 1.2) -> bool:
        """测试指定 URL 的 WDA 是否处于正常响应状态 (前置 40ms 极速端口探活，杜绝端口未开时的阻塞等待)"""
        import urllib.request
        from urllib.parse import urlparse
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
        """
        获取当前可用的 WDA 服务地址 (优先 40ms 极速本地端口探活；按需后台建立 usbmux 8100 端口映射)
        返回值: (有效_wda_url, 诊断状态描述)
        """
        for port in (8100, 8200):
            test_url = f"http://127.0.0.1:{port}"
            if cls.test_wda_status(test_url, timeout=0.6):
                cls._active_wda_url = test_url
                return test_url, f"WDA 服务已连通 ({test_url})"

        if allow_spawn and udid and not udid.startswith("wda_localhost"):
            tidevice_bin = shutil.which("tidevice")
            if not tidevice_bin:
                candidate_td = os.path.join(os.path.dirname(sys.executable), "Scripts", "tidevice.exe")
                if os.path.isfile(candidate_td):
                    tidevice_bin = candidate_td
            if tidevice_bin:
                try:
                    # 若设备发生变更或当前进程已失效，先彻底释放原有端口并杀死旧设备中继
                    if cls._relay_udid and cls._relay_udid != udid:
                        cls.kill_relays((8100,))

                    creationflags = 0x08000000 if sys.platform == "win32" else 0
                    if cls._relay_proc is None or cls._relay_proc.poll() is not None:
                        # 确保端口 8100 未被其他孤儿进程霸占
                        cls.kill_relays((8100,))
                        relay_cmd = [tidevice_bin, "-u", udid, "relay", "8100", "8100"]
                        cls._relay_proc = subprocess.Popen(
                            relay_cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=creationflags
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
    检查 iOS WDA 8100 两个核心服务是否处于运行状态：
    1. 真机 WDA Runner (developer dvt xcuitest / WebDriverAgentRunner / tidevice wdaproxy)
    2. 8100 端口转发 (usbmux forward 8100 / tidevice relay 8100 / iproxy 8100)
    若 127.0.0.1:8100/status 已实际连通响应，直接判定双服务均就绪。
    返回: (is_xcuitest_running, is_forward_running)
    """
    # 优先极速探活本地 8100 WDA 接口 (前置 40ms TCP 探活，未启动时不阻塞)
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

                # 检查服务 1: developer dvt xcuitest / WebDriverAgentRunner / tidevice wdaproxy
                if (
                    ("dvt" in cmdline_str and "xcuitest" in cmdline_str)
                    or ("webdriveragentrunner" in cmdline_str and "pymobiledevice3" in cmdline_str)
                    or ("tidevice" in cmdline_str and "wdaproxy" in cmdline_str)
                ):
                    is_xcuitest = True

                # 检查服务 2: usbmux forward 8100 / tidevice relay 8100 / tidevice wdaproxy / iproxy 8100
                if "8100" in cmdline_str and (
                    ("usbmux" in cmdline_str and "forward" in cmdline_str)
                    or ("tidevice" in cmdline_str and ("relay" in cmdline_str or "wdaproxy" in cmdline_str))
                    or "iproxy" in cmdline_str
                ):
                    # 校验 8100 转发进程是否真正能 TCP 握手，若已被管道死锁卡死则标记为异常触发【重启服务】
                    import socket as _sock
                    try:
                        with _sock.create_connection(("127.0.0.1", 8100), timeout=0.35):
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


class IosServiceActionWorker(QThread):
    """
    iOS WDA 自动化服务异步控制线程 (静默执行脚本并监控进程生命周期):
    1. 启动/重启: 静默调用 stop_ios_wda.bat 彻底清理解锁端口，再静默拉起 start_ios_wda.bat 并轮询直到就绪；
    2. 停止: 静默调用 stop_ios_wda.bat 安全回收；
    3. 进程完全隔离，CREATE_NO_WINDOW 消除弹窗与黑框，智能处理 pause 避免死锁挂起。
    """
    finished_sig = pyqtSignal(bool, str, str)

    def __init__(self, action: str, parent=None):
        super().__init__(parent)
        self.action = action  # "start_or_restart" 或 "stop"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
        try:
            from desktop_app.core.path_resolver import SmartPathResolver
            resolved_root = SmartPathResolver.get_project_root()
            if resolved_root and os.path.isdir(os.path.join(resolved_root, "scripts")):
                project_root = resolved_root
        except Exception:
            pass
        self.stop_bat = os.path.join(project_root, "scripts", "stop_ios_wda.bat")
        self.start_bat = os.path.join(project_root, "scripts", "start_ios_wda.bat")

    def _get_python_exe(self) -> str:
        """获取真实 Python 解释器路径，严禁在打包 EXE 态下误将 sys.executable (GUI 主程序) 当作 python 调用"""
        if not getattr(sys, "frozen", False) and sys.executable and "python" in os.path.basename(sys.executable).lower():
            return sys.executable
        try:
            from desktop_app.core.path_resolver import SmartPathResolver
            py_info = SmartPathResolver.discover_python_runtime()
            if py_info and py_info.get("executable"):
                return py_info["executable"]
        except Exception:
            pass
        return shutil.which("python") or shutil.which("python3") or "python"

    def _execute_stop_bat(self) -> bool:
        """静默执行停止脚本，并彻底回收所有看门狗及关联进程树，杜绝自动复活"""
        stop_py = os.path.join(os.path.dirname(self.stop_bat), "stop_ios_wda.py")
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
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
            elif os.path.exists(self.stop_bat):
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

        # 彻底精准终结所有看门狗宿主与整棵关联进程树，物理阻断看门狗几秒后自动重新拉起服务
        target_kws = [
            "start_ios_wda",
            "usbmux forward 8100",
            "developer dvt xcuitest",
            "webdriveragentrunner",
        ]
        my_pid = os.getpid()
        for p in psutil.process_iter(["pid", "cmdline"]):
            try:
                if p.info["pid"] == my_pid:
                    continue
                cmdline = " ".join(p.info.get("cmdline") or []).lower()
                if any(kw in cmdline for kw in target_kws):
                    try:
                        for child in p.children(recursive=True):
                            try:
                                child.kill()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 轮询直到操作系统内核彻底回收双项服务进程 (最多等待 3 秒)
        for _ in range(10):
            is_xcuitest, is_forward = check_ios_wda_services()
            if not is_xcuitest and not is_forward:
                break
            time.sleep(0.3)

        return True

    def _execute_start_bat(self) -> bool:
        """静默启动 start_ios_wda.py 守护进程，并在后台轮询等待双服务就绪"""
        start_py = os.path.join(os.path.dirname(self.start_bat), "start_ios_wda.py")
        if not os.path.exists(start_py) and not os.path.exists(self.start_bat):
            logger.warning(f"[IosService] 未找到启动脚本: {self.start_bat}")
            return False
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            py_exe = self._get_python_exe()
            if os.path.exists(start_py) and py_exe:
                subprocess.Popen(
                    [py_exe, "-u", start_py],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                    cwd=os.path.dirname(start_py),
                )
            else:
                subprocess.Popen(
                    ["cmd.exe", "/c", self.start_bat],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                    cwd=os.path.dirname(self.start_bat),
                )

            # 轮询探测服务是否已双双拉起并稳定存活 (最多等待 30 秒，兼顾首次自动挂载 DeveloperDiskImage 耗时)
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
            return False
        except Exception as e:
            logger.error(f"[IosService] 执行启动脚本异常: {e}")
            return False

    def run(self):
        if self.action == "stop":
            self._execute_stop_bat()
            self.finished_sig.emit(True, "服务已停止", "stop")
        else:
            self._execute_stop_bat()
            ok = self._execute_start_bat()
            self.finished_sig.emit(ok, "服务已启动" if ok else "服务启动未完全就绪", "start_or_restart")


def run_ios_action(action: str, udid: str = "", **kwargs) -> bool:
    """执行 iOS 动作 (优先复用 pymobiledevice3 CoreDevice 原生 HID 通道，备选 WebDriverAgent 8100/8200 端口)"""
    if ScreenCastWorker.dispatch_ios_hid(action, **kwargs):
        return True

    import urllib.request
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
        elif action == "swipe":
            x1, y1 = kwargs.get("x1", 0), kwargs.get("y1", 0)
            x2, y2 = kwargs.get("x2", 0), kwargs.get("y2", 0)
            dur = kwargs.get("duration", 0.3)
            data = json.dumps({"fromX": x1, "fromY": y1, "toX": x2, "toY": y2, "duration": dur}).encode("utf-8")
            req = urllib.request.Request(f"{wda_url}/wda/dragfromtoforduration", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                return resp.status == 200
        elif action == "home":
            req = urllib.request.Request(f"{wda_url}/wda/homescreen", data=b"{}", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status == 200
        elif action == "keys":
            text = kwargs.get("text", "")
            data = json.dumps({"value": list(text)}).encode("utf-8")
            req = urllib.request.Request(f"{wda_url}/wda/keys", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                return resp.status == 200
        elif action == "clear":
            req = urllib.request.Request(f"{wda_url}/wda/element/active", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    el_id = json.loads(resp.read().decode("utf-8")).get("value", {}).get("ELEMENT")
                    if el_id:
                        del_req = urllib.request.Request(f"{wda_url}/element/{el_id}/clear", data=b"{}", headers={"Content-Type": "application/json"})
                        urllib.request.urlopen(del_req, timeout=1.5)
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

    # 3. 探测 iOS 设备 (首选进程内 pymobiledevice3 usbmux 30ms 极速直连探测，辅以 tidevice 兜底)
    try:
        import asyncio
        import contextlib
        from pymobiledevice3.usbmux import list_devices as pmd_list_devices
        from pymobiledevice3.lockdown import create_using_usbmux as pmd_create_lockdown

        async def _scan_ios_usbmux() -> List[Dict[str, Any]]:
            found_ios: List[Dict[str, Any]] = []
            mux_devs = await asyncio.wait_for(pmd_list_devices(), timeout=1.5)
            for mdev in (mux_devs or []):
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

    # 备选：通过 tidevice list 补充扫描 (兼容旧环境，超时放宽至 3.5s 防止 lockdown 握手被截断)
    tidevice_bin = shutil.which("tidevice")
    if not tidevice_bin:
        candidate_td = os.path.join(os.path.dirname(sys.executable), "Scripts", "tidevice.exe")
        if os.path.isfile(candidate_td):
            tidevice_bin = candidate_td
    if tidevice_bin:
        try:
            out = subprocess.check_output([tidevice_bin, "list"], text=True, errors="ignore", timeout=3.5, creationflags=creationflags).strip()
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
                            "is_real": True
                        })
        except Exception:
            pass

    # 备选 2：Windows 原生 CfgMgr32 / PnP 即插即用硬件层保底扫描 (0ms 开销，手机连接无论是否锁屏 100% 识别)
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
                        # 仅探测当前处于真实物理连接在线 (CR_SUCCESS = 0) 的设备
                        if cfgmgr32.CM_Locate_DevNodeW(ctypes.byref(devnode), dev_inst, 0) == 0:
                            if cfgmgr32.CM_Get_DevNode_Status(ctypes.byref(status), ctypes.byref(problem), devnode, 0) == 0:
                                udid = f"{raw_id[:8]}-{raw_id[8:]}" if (len(raw_id) == 24 and "-" not in raw_id) else raw_id
                                if udid and udid not in seen_udids:
                                    seen_udids.add(udid)
                                    devices.append({
                                        "udid": udid,
                                        "platform": "ios",
                                        "name": f"苹果真机 (iPhone): {udid}",
                                        "is_real": True
                                    })
                    except OSError:
                        break
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
            "full_type": raw_class,
            "id": res_id,
            "text": text,
            "bounds": bounds,
            "class": raw_class,
            "resource-id": res_id,
            "package": attrs.get("package", ""),
            "content-desc": attrs.get("content-desc", ""),
            "clickable": attrs.get("clickable", "false"),
            "longClickable": attrs.get("long-clickable", "false"),
            "enabled": attrs.get("enabled", "true"),
            "focusable": attrs.get("focusable", "false"),
            "scrollable": attrs.get("scrollable", "false"),
            "visible": attrs.get("visible-to-user", "true"),
            "hint": attrs.get("hint", ""),
        },
        "children": [parse_android_node(child) for child in elem if child.tag == "node"]
    }


def extract_ios_logical_size(layout_file: str) -> Optional[Tuple[int, int]]:
    """从 iOS WDA 布局文件提取应用原生逻辑点尺寸 (如 390x844)"""
    if not layout_file or not os.path.exists(layout_file):
        return None
    try:
        with open(layout_file, "r", encoding="utf-8", errors="ignore") as f_lay:
            head_txt = f_lay.read(8192)
        m_app = re.search(r'<XCUIElementTypeApplication[^>]*width=\\?"(\d+)\\?"[^>]*height=\\?"(\d+)\\?"', head_txt)
        if m_app:
            app_w, app_h = int(m_app.group(1)), int(m_app.group(2))
            if app_w > 100 and app_h > 100:
                return app_w, app_h
        if len(head_txt) >= 8192:
            with open(layout_file, "r", encoding="utf-8", errors="ignore") as f_full:
                full_txt = f_full.read()
        else:
            full_txt = head_txt
        data = json.loads(full_txt)
        val = data.get("value", data) if isinstance(data, dict) else None
        if isinstance(val, dict):
            rect = val.get("rect", {})
            app_w, app_h = int(float(rect.get("width", 0))), int(float(rect.get("height", 0)))
            if app_w > 100 and app_h > 100:
                return app_w, app_h
    except Exception:
        pass
    return None


def crop_ios_dvt_image(img: QImage, logical_size: Optional[Tuple[int, int]]) -> QImage:
    """裁剪 iOS DVT/CoreDevice 帧缓冲内存对齐产生的右侧/底部纯黑填充区"""
    if img.isNull() or not logical_size:
        return img
    app_w, app_h = logical_size
    if app_w <= 100 or app_h <= 100:
        return img
    retina = round(min(img.width() / app_w, img.height() / app_h))
    real_w, real_h = app_w * retina, app_h * retina
    if retina not in (2, 3) or img.width() < real_w or img.height() < real_h:
        return img
    if img.width() == real_w and img.height() == real_h:
        return img

    def _is_near_black(px: int, py: int) -> bool:
        c = img.pixelColor(px, py)
        return c.red() <= 15 and c.green() <= 15 and c.blue() <= 15

    if img.width() > real_w:
        if not (_is_near_black(real_w, real_h // 4) and _is_near_black(real_w, real_h // 2)):
            return img
    if img.height() > real_h:
        if not (_is_near_black(real_w // 4, real_h) and _is_near_black(real_w // 2, real_h)):
            return img
    return img.copy(0, 0, real_w, real_h)


def normalize_ios_screenshot_file(img_path: str, layout_file: str) -> Optional[Tuple[int, int]]:
    """标准化 iOS 静态截图底图并裁剪 DVT 对齐黑边，返回应用原生逻辑尺寸"""
    logical_size = extract_ios_logical_size(layout_file)
    if img_path and os.path.exists(img_path) and logical_size:
        img = QImage(img_path)
        cropped = crop_ios_dvt_image(img, logical_size)
        if not cropped.isNull() and (cropped.width() != img.width() or cropped.height() != img.height()):
            cropped.save(img_path, "PNG")
    return logical_size


def parse_ios_node(elem: ET.Element, scale_x: float = 1.0, scale_y: float = 1.0) -> Dict[str, Any]:
    """将 iOS WDA XML 节点转换为通用 DOM 结构 (保留元素原生坐标与尺寸)"""
    attrs = elem.attrib.copy()
    tag = elem.tag
    short_type = tag.replace("XCUIElementType", "") if tag.startswith("XCUIElementType") else tag
    c_id = attrs.get("name", "")
    c_text = attrs.get("label", "") or attrs.get("value", "")
    try:
        x = float(attrs.get("x", 0))
        y = float(attrs.get("y", 0))
        w = float(attrs.get("width", 0))
        h = float(attrs.get("height", 0))
        # 乘以 Retina 缩放系数，使 Point 坐标严丝合缝映射到 Pixel 截图物理画面
        sx = int(round(x * scale_x))
        sy = int(round(y * scale_y))
        sw = int(round(w * scale_x))
        sh = int(round(h * scale_y))
        bounds = f"[{sx},{sy}][{sx + sw},{sy + sh}]"
    except Exception:
        bounds = attrs.get("bounds", "[0,0][0,0]")

    return {
        "attributes": {
            "type": short_type,
            "full_type": tag,
            "id": c_id,
            "text": c_text,
            "bounds": bounds,
            "name": c_id,
            "label": attrs.get("label", ""),
            "value": attrs.get("value", ""),
            "enabled": attrs.get("enabled", "true"),
            "visible": attrs.get("visible", "true"),
        },
        "children": [parse_ios_node(child, scale_x, scale_y) for child in elem]
    }


def parse_ios_json_node(data: Dict[str, Any], scale_x: float = 1.0, scale_y: float = 1.0) -> Dict[str, Any]:
    """将 iOS WDA JSON 节点转换为通用 DOM 结构 (支持 Retina 视网膜缩放)"""
    if not isinstance(data, dict):
        return {"attributes": {"type": "Element", "full_type": "XCUIElementTypeElement", "bounds": "[0,0][0,0]"}, "children": []}
    raw_type = data.get("type", "Element")
    short_type = raw_type.replace("XCUIElementType", "") if raw_type.startswith("XCUIElementType") else raw_type
    c_id = data.get("name") or data.get("id") or ""
    c_text = data.get("label") or data.get("value") or ""
    rect = data.get("rect", {})
    x = float(rect.get("x", 0))
    y = float(rect.get("y", 0))
    w = float(rect.get("width", 0))
    h = float(rect.get("height", 0))
    sx = int(round(x * scale_x))
    sy = int(round(y * scale_y))
    sw = int(round(w * scale_x))
    sh = int(round(h * scale_y))
    bounds = f"[{sx},{sy}][{sx + sw},{sy + sh}]"

    return {
        "attributes": {
            "type": short_type,
            "full_type": raw_type if raw_type.startswith("XCUIElementType") else f"XCUIElementType{raw_type}",
            "id": c_id,
            "text": c_text,
            "bounds": bounds,
            "name": c_id,
            "label": str(data.get("label", "")),
            "value": str(data.get("value", "")),
            "enabled": str(data.get("enabled", "true")),
            "visible": str(data.get("visible", "true")),
        },
        "children": [parse_ios_json_node(child, scale_x, scale_y) for child in data.get("children", []) if isinstance(child, dict)]
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
            # 前置探测：当 uitest 运行于 scrcpy_server.so 扩展投屏模式时，内核仅注册 @scrcpy_grpc_socket 而无 @uitest_socket，
            # 此时 0ms 直接返回 None 交由 uitest dumpLayout CLI 抓取，避免无效连接阻塞或重启投屏守护进程
            unix_socks = run_hdc(["shell", "cat /proc/net/unix | grep -E 'uitest_socket|scrcpy_grpc_socket'"], udid, timeout=1.0)
            if "scrcpy_grpc_socket" in unix_socks and "uitest_socket" not in unix_socks:
                return None
            if "uitest_socket" not in unix_socks:
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
    for k in ("type", "id", "key", "text", "originalText", "visible", "visibility", "hidden", "opacity", "alpha", "clip", "description", "clickable", "enabled", "bounds", "rect"):
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
    支持鸿蒙 JSON 与安卓/iOS XML 布局文件自动提取最大屏幕物理边界
    """
    try:
        data = None
        if isinstance(layout_data, str) and os.path.exists(layout_data):
            with open(layout_data, "r", encoding="utf-8") as f:
                raw_text = f.read(65536).lstrip()
            if raw_text.startswith("<"):
                max_w, max_h = 0, 0
                for m in re.finditer(r'bounds="\[0,0\]\[(\d+),(\d+)\]"', raw_text):
                    w, h = int(m.group(1)), int(m.group(2))
                    if w >= 600 and h >= 1000:
                        max_w = max(max_w, w)
                        max_h = max(max_h, h)
                if max_w >= 600 and max_h >= 1000:
                    return max_w, max_h
                return default_w, default_h
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
    if platform in ("harmony", "android"):
        phys_w, phys_h = get_layout_physical_size(
            layout_path,
            1084 if platform == "harmony" else 1080,
            2412 if platform == "harmony" else 2400,
        )
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
            top_nodes = [ch for ch in root if ch.tag == "node"]
            if top_nodes:
                overlay_keywords = (
                    "smartsidebar", "sidebar", "float", "touchassistant",
                    "cocktailbar", "edgepanel", "subscreen", "aod",
                    "inputmethod", "input_", "keyboard", "pinyin",
                )
                launcher_keywords = (
                    "launcher", "miui.home", "trebuchet", "lawnchair", "wallpaper",
                )

                def _contains_toast_node(elem: ET.Element) -> bool:
                    """判断顶层窗口是否包含系统或自定义 Toast 节点，避免被系统浮层过滤逻辑误删"""
                    for node in elem.iter("node"):
                        cls_name = (node.attrib.get("class") or "").strip().lower()
                        res_id = (node.attrib.get("resource-id") or "").strip().lower()
                        if cls_name == "android.widget.toast" or "toast" in res_id:
                            return True
                    return False

                def _is_system_overlay(elem: ET.Element) -> bool:
                    if _contains_toast_node(elem):
                        return False
                    pkg = (elem.attrib.get("package") or "").strip().lower()
                    if pkg == "com.android.systemui":
                        return True
                    return any(k in pkg for k in overlay_keywords)

                def _is_launcher(elem: ET.Element) -> bool:
                    pkg = (elem.attrib.get("package") or "").strip().lower()
                    return any(k in pkg for k in launcher_keywords)

                app_nodes = [
                    n for n in top_nodes
                    if not _is_system_overlay(n) and not _is_launcher(n)
                ]
                if app_nodes:
                    selected_nodes = app_nodes
                else:
                    launcher_nodes = [n for n in top_nodes if _is_launcher(n)]
                    selected_nodes = launcher_nodes if launcher_nodes else top_nodes

                if len(selected_nodes) == 1:
                    return parse_android_node(selected_nodes[0])
                return {
                    "attributes": {
                        "type": "Hierarchy",
                        "bounds": root_bounds,
                    },
                    "children": [parse_android_node(n) for n in selected_nodes],
                }
        except Exception:
            pass
        return {"attributes": {"type": "hierarchy", "bounds": root_bounds}, "children": []}
    elif platform == "ios":
        try:
            if not layout_path or not os.path.exists(layout_path):
                return {"attributes": {"type": "Screen", "bounds": root_bounds}, "children": []}
            with open(layout_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            if not content:
                return {"attributes": {"type": "Screen", "bounds": root_bounds}, "children": []}

            xml_content = ""
            json_data = None
            if content.startswith("<"):
                xml_content = content
            else:
                try:
                    raw_json = json.loads(content)
                    val = raw_json.get("value", raw_json)
                    if isinstance(val, str) and ("<XCUIElementType" in val or "<AppiumAUT" in val or val.strip().startswith("<")):
                        xml_content = val.strip()
                    elif isinstance(val, dict):
                        json_data = val
                except Exception:
                    if "<" in content:
                        xml_content = content[content.find("<"):]

            if xml_content:
                root = ET.fromstring(xml_content)
                app_node = root.find(".//XCUIElementTypeApplication")
                target_node = app_node if app_node is not None else root
                # iOS 直接保留 WDA 原生逻辑点坐标 (x, y, width, height)，绝不受底图黑边或缩放比例污染
                return parse_ios_node(target_node, 1.0, 1.0)
            elif json_data:
                return parse_ios_json_node(json_data, 1.0, 1.0)
        except Exception as e:
            logging.warning(f"[iOS布局解析] 异常降级: {e}")
        return {"attributes": {"type": "Screen", "bounds": root_bounds}, "children": []}
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
    _active_ios_server: Optional[Any] = None
    _active_ios_loop: Optional[Any] = None
    _ios_tunnel_lock: "threading.Lock" = threading.Lock()

    @classmethod
    def release_all_tunnels(cls):
        """强制清理并重置残留的 userspace_tunnel 句柄与单例状态 (换机或异常重置时调用)"""
        try:
            from pymobiledevice3.remote import userspace_tunnel
            for attr_name in ("_active_tunnel", "_cli_tunnel"):
                tun = getattr(userspace_tunnel, attr_name, None)
                if tun is not None:
                    with contextlib.suppress(Exception):
                        if hasattr(tun, "close"):
                            tun.close()
                    setattr(userspace_tunnel, attr_name, None)
            userspace_tunnel.USERSPACE_ACTIVE = False
        except Exception:
            pass

    @classmethod
    def clear_cache(cls):
        """清空全量内存投屏帧缓存 (设备切换时强制调用，彻底杜绝跨设备脏画面污染)"""
        cls.latest_image = None
        cls.latest_pixmap = None
        cls.latest_frame_bytes = None
        cls.latest_frame_time = 0.0
        cls.latest_udid = ""
        cls.is_active = False

    @classmethod
    def dispatch_ios_hid(cls, action: str, **kwargs) -> bool:
        """通过活跃的 pymobiledevice3 ScreenStreamServer 异步派发原生 CoreDevice HID 触控与按键事件"""
        server = cls._active_ios_server
        loop = cls._active_ios_loop
        if server is None or loop is None or not cls.is_active:
            return False

        def _norm_coord(x_val: float, y_val: float) -> Tuple[int, int]:
            ref_w, ref_h = 390.0, 844.0
            if cls.latest_image is not None and not cls.latest_image.isNull():
                iw, ih = float(cls.latest_image.width()), float(cls.latest_image.height())
                if x_val > 440 or y_val > 960:
                    ref_w, ref_h = iw, ih
            hx = max(0, min(65535, int(round((x_val / max(1.0, ref_w)) * 65535.0))))
            hy = max(0, min(65535, int(round((y_val / max(1.0, ref_h)) * 65535.0))))
            return hx, hy

        try:
            if action == "tap":
                hx, hy = _norm_coord(float(kwargs.get("x", 0)), float(kwargs.get("y", 0)))
                payload = json.dumps({"type": "tap", "x": hx, "y": hy}).encode("utf-8")
                loop.call_soon_threadsafe(server._hid_queue.put_nowait, ("/touch", payload))
                return True
            elif action == "home":
                payload = json.dumps({"name": "home", "state": "press"}).encode("utf-8")
                loop.call_soon_threadsafe(server._hid_queue.put_nowait, ("/button", payload))
                return True
            elif action == "swipe":
                x1, y1 = float(kwargs.get("x1", 0)), float(kwargs.get("y1", 0))
                x2, y2 = float(kwargs.get("x2", 0)), float(kwargs.get("y2", 0))
                ref_w, ref_h = 390.0, 844.0
                if cls.latest_image is not None and not cls.latest_image.isNull():
                    iw, ih = float(cls.latest_image.width()), float(cls.latest_image.height())
                    if max(x1, x2) > 440 or max(y1, y2) > 960:
                        ref_w, ref_h = iw, ih
                hx1 = max(0, min(65535, int(round((x1 / max(1.0, ref_w)) * 65535.0))))
                hy1 = max(0, min(65535, int(round((y1 / max(1.0, ref_h)) * 65535.0))))
                hx2 = max(0, min(65535, int(round((x2 / max(1.0, ref_w)) * 65535.0))))
                hy2 = max(0, min(65535, int(round((y2 / max(1.0, ref_h)) * 65535.0))))
                dur = max(0.1, float(kwargs.get("duration", 0.3)))

                async def _async_swipe():
                    import asyncio as _aio
                    steps = 12
                    for i in range(steps + 1):
                        t = i / steps
                        cx = int(round(hx1 + (hx2 - hx1) * t))
                        cy = int(round(hy1 + (hy2 - hy1) * t))
                        server._hid_queue.put_nowait(
                            ("/touch", json.dumps({"type": "contact", "x": cx, "y": cy}).encode("utf-8"))
                        )
                        await _aio.sleep(dur / steps)
                    server._hid_queue.put_nowait(
                        ("/touch", json.dumps({"type": "release", "x": hx2, "y": hy2}).encode("utf-8"))
                    )

                import asyncio as _aio
                _aio.run_coroutine_threadsafe(_async_swipe(), loop)
                return True
        except Exception:
            pass
        return False

    def __init__(self, udid: str, platform: str):
        super().__init__()
        self.udid = udid
        self.platform = platform
        self._is_running = False
        self.ui_ready = True  # 自适应消费门阀：主线程渲染完毕才推新帧，彻底消除事件队列堆积与切屏延迟
        self._sock: Optional[socket.socket] = None
        self._grpc_channel: Any = None
        self._local_port = 0
        self._android_proc: Optional[subprocess.Popen] = None
        self._android_scid: str = ""
        self._android_server_sock: Optional[socket.socket] = None
        self._android_conn: Optional[socket.socket] = None
        self._ios_stop_hook: Optional[Any] = None
        self._last_ios_error: str = ""

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
        max_age = 60.0 if cls.is_active else 3.0
        if cls.latest_frame_bytes and (time.time() - cls.latest_frame_time < max_age):
            return cls.latest_frame_bytes
        if cls.latest_image and not cls.latest_image.isNull() and (cls.is_active or (time.time() - cls.latest_frame_time < max_age)):
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
        """1:1 对齐 HoKit 进程治理：仅精准清理 start-daemon 或 xdevice_scrcpy 守护进程，绝不误杀正在执行的 uitest dumpLayout 或 uiInput"""
        try:
            ps_res = run_hdc(["shell", "ps -ef"], udid, timeout=2.0)
            if ps_res:
                pids_to_kill = []
                for line in ps_res.splitlines():
                    if "grep" in line:
                        continue
                    if "start-daemon" not in line and "xdevice_scrcpy" not in line:
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

        # 3. 投屏启动前主动点亮屏幕并重启守护进程，杜绝 Stop 状态污染与息屏卡死
        try:
            # 主动唤醒屏幕
            run_hdc(["shell", "power-shell wakeup"], udid, timeout=1.0)
            # 彻底强杀真机旧残留，保证每次建立投屏均处于全新的 VirtualScreen 会话
            cls._kill_existing_scrcpy_daemons(udid)
            time.sleep(0.15)
            cmd_start = (
                "cd /data/local/tmp && export LD_LIBRARY_PATH=/data/local/tmp:$LD_LIBRARY_PATH && "
                "(uitest start-daemon singleness --extension-name scrcpy_server.so "
                "-scale 2 -frameRate 30 -bitRate 10485760 -p 9958 -screenId 0 "
                "-encodeType 0 -iFrameInterval 500 -repeatInterval 33 >/dev/null 2>&1 &)"
            )
            run_hdc(["shell", cmd_start], udid, timeout=2.5)
            time.sleep(0.2)
        except Exception:
            pass

    def stop(self):
        """请求优雅停止实时投屏流"""
        self._is_running = False
        self.ui_ready = True
        ScreenCastWorker.is_active = False
        ios_hook = getattr(self, "_ios_stop_hook", None)
        if callable(ios_hook):
            try:
                ios_hook()
            except Exception:
                pass
            self._ios_stop_hook = None
        if getattr(self, "_grpc_channel", None):
            try:
                self._grpc_channel.close()
            except Exception:
                pass
            self._grpc_channel = None
        mjpeg_proc = getattr(self, "_ios_mjpeg_relay_proc", None)
        if mjpeg_proc is not None:
            try:
                mjpeg_proc.terminate()
                mjpeg_proc.wait(timeout=0.5)
            except Exception:
                try:
                    mjpeg_proc.kill()
                except Exception:
                    pass
            self._ios_mjpeg_relay_proc = None
        IosWdaManager.kill_relays()
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

    @classmethod
    def capture_single_ios_frame(cls, udid: str = "", timeout: float = 4.5) -> Optional[bytes]:
        """
        iOS 真机单帧静默截屏能力 (iOS 17+ CoreDevice 原生 DisplayService):
        1. 优先复用当前活跃实时投屏流中的内存新鲜帧 (耗时 0ms，零外部调用)；
        2. 若未开启投屏，基于 UserspaceRsdTunnel + ScreenStreamServer 单次极速握手抓取首帧 (耗时仅 ~0.5s)，
           抓取完毕立即释放会话与隧道，杜绝占用 USB 通道。
        """
        import asyncio
        import contextlib
        import time

        # 1. 优先复用内存最新新鲜帧 (耗时 0ms)
        if cls.latest_image is not None and not cls.latest_image.isNull():
            if not udid or not cls.latest_udid or cls.latest_udid == udid:
                now = time.time()
                if cls.is_active or (now - cls.latest_frame_time < 5.0):
                    return cls.get_latest_jpeg_bytes(udid)

        # 核心互斥协同：若实时投屏当前活跃中，严禁建立新隧道引发撞车，直接等待投屏流最新帧
        if cls.is_active:
            for _ in range(40):
                if cls.latest_image is not None and (not udid or cls.latest_udid == udid):
                    return cls.get_latest_jpeg_bytes(udid)
                time.sleep(0.05)
            return cls.get_latest_jpeg_bytes(udid)

        # 尝试非阻塞获取 iOS 隧道锁，若已被投屏引擎持有或启动中则直接复用内存帧，绝不并发争夺 RSD 隧道
        acquired = cls._ios_tunnel_lock.acquire(blocking=False)
        if not acquired:
            for _ in range(30):
                if cls.latest_image is not None and (not udid or cls.latest_udid == udid):
                    return cls.get_latest_jpeg_bytes(udid)
                time.sleep(0.05)
            return cls.get_latest_jpeg_bytes(udid)

        target_udid = udid if (udid and not udid.startswith("wda_localhost")) else None

        # 2. 进程内极速单帧握手
        async def _capture_one_frame_async() -> Optional[bytes]:
            from pymobiledevice3.remote import userspace_tunnel
            from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
            from pymobiledevice3.remote.core_device.screen_stream import ScreenStreamServer, _SubState
            from pymobiledevice3.remote.core_device.display_service import DisplayService
            import av

            # 强力重置可能遗留的旧隧道句柄
            for attr_name in ("_active_tunnel", "_cli_tunnel"):
                setattr(userspace_tunnel, attr_name, None)
            userspace_tunnel.USERSPACE_ACTIVE = False

            owned_tunnel = UserspaceRsdTunnel(serial=target_udid, autopair=True)
            rsd = None
            server = None
            try:
                rsd = await asyncio.wait_for(owned_tunnel.aopen(), timeout=timeout)
                server = ScreenStreamServer(rsd=rsd, audio_default_on=False, motion_idr=False, rctl_enabled=True)
                sub_q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=10)
                sub_state = _SubState()
                sub_state.needs_key = True
                server._subscribers[sub_q] = sub_state

                async def _silent_audio(transport):
                    while True:
                        try:
                            pkt = await transport.recv(65535)
                            if not pkt:
                                break
                        except Exception:
                            break
                server._audio_udp_recv = _silent_audio

                await asyncio.wait_for(server._eager_stream_start(), timeout=timeout)
                msg = await asyncio.wait_for(sub_q.get(), timeout=timeout)
                if not msg or len(msg) < 6:
                    return None

                au_data = msg[5:]
                nals = []
                pos = 0
                data_len = len(au_data)
                while pos + 4 <= data_len:
                    nal_len = int.from_bytes(au_data[pos : pos + 4], "big")
                    pos += 4
                    if nal_len <= 0 or pos + nal_len > data_len:
                        break
                    nals.append(au_data[pos : pos + nal_len])
                    pos += nal_len

                vps, sps, pps = server._vps_nal, server._sps_nal, server._pps_nal
                if vps and sps and pps:
                    nals = [vps, sps, pps] + nals

                annexb_bytes = b"".join(b"\x00\x00\x00\x01" + n for n in nals)
                codec = av.CodecContext.create("hevc", "r")
                with contextlib.suppress(Exception):
                    codec.options = {"flags": "low_delay"}
                frames = codec.decode(av.Packet(annexb_bytes))
                if frames:
                    f = frames[-1]
                    bgr = f.reformat(format="bgra")
                    plane = bgr.planes[0]
                    qimg = QImage(bytes(plane), bgr.width, bgr.height, plane.line_size, QImage.Format.Format_RGB32).copy()
                    buf = QByteArray()
                    buffer_io = QBuffer(buf)
                    buffer_io.open(QBuffer.OpenModeFlag.WriteOnly)
                    qimg.save(buffer_io, "PNG")
                    cls.latest_image = qimg
                    cls.latest_frame_bytes = bytes(buf)
                    cls.latest_frame_time = time.time()
                    cls.latest_udid = udid
                    return bytes(buf)
                return None
            except Exception as e:
                logging.debug(f"[iOS单帧截屏] 异常: {e}")
                return None
            finally:
                if server is not None:
                    with contextlib.suppress(Exception):
                        async with server._stream_lock:
                            await asyncio.wait_for(server._stop_active_stream(), timeout=1.0)
                if rsd is not None:
                    with contextlib.suppress(Exception):
                        await asyncio.wait_for(DisplayService.stop_all_streams(rsd), timeout=1.5)
                if owned_tunnel is not None:
                    with contextlib.suppress(Exception):
                        await asyncio.wait_for(owned_tunnel.aclose(), timeout=1.5)
                for attr_name in ("_active_tunnel", "_cli_tunnel"):
                    setattr(userspace_tunnel, attr_name, None)
                userspace_tunnel.USERSPACE_ACTIVE = False

        try:
            return asyncio.run(_capture_one_frame_async())
        except Exception:
            return None
        finally:
            cls._ios_tunnel_lock.release()

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
        # 智能复用或按需拉起 scrcpy_server.so 守护进程 (不盲目强杀已就绪守护进程，避免与 CaptureWorker dumpLayout 冲突)
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

        # 异步并发循环请求关键帧 IDR (最多尝试 5 次，每 100ms 一次)，极速激活首帧 H.264 解码，确保 1.5s 瞬时出图
        def request_idr_task():
            for _ in range(5):
                if has_emitted_first_frame or not self._is_running:
                    break
                time.sleep(0.1)
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
                        # 自适应门阀调度：主线程就绪或达到 50ms 保底周期时派发，杜绝固定 28ms 门限与 60Hz 刷新率共振丢帧
                        if (self.ui_ready or (now - last_emit_t >= 0.05)) and (now - last_emit_t >= 0.016):
                            last_emit_t = now
                            self.ui_ready = False
                            rgb_array = newest_frame.to_ndarray(format="rgb24")
                            h, w, _ = rgb_array.shape
                            qimg = QImage(rgb_array.tobytes(), w, h, 3 * w, QImage.Format.Format_RGB888).copy()
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

        return has_emitted_first_frame or (not self._is_running)

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
            f"CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / com.genymobile.scrcpy.Server 3.3.4 scid={self._android_scid} log_level=info video=true audio=false control=false cleanup=false tunnel_forward=false max_size=1080 video_bit_rate=4000000 max_fps=60"
        ])
        self._android_proc = subprocess.Popen(
            cmd_start,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )

        # 5. 等待真机连接并开启底层 TCP_NODELAY 极速传输通道 (彻底清除 Nagle 算法 40ms 缓冲区延迟)
        try:
            self._android_conn, _ = self._android_server_sock.accept()
            self._android_conn.settimeout(5.0)
            try:
                self._android_conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self._android_conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
            except Exception:
                pass
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

        # 7. 解码循环 (开启 SLICE 低延迟模式，消除多帧缓存排队延迟)
        codec = av.CodecContext.create("h264", "r")
        try:
            codec.thread_type = "SLICE"
        except Exception:
            pass
        try:
            codec.options = {"flags": "low_delay"}
        except Exception:
            pass
        last_emit_t = 0.0
        has_emitted_first_frame = False

        def recv_exact(sock, n):
            buf = bytearray()
            while len(buf) < n:
                if not self._is_running:
                    return None
                chunk = sock.recv(min(65536, n - len(buf)))
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
                    # 自适应消费门阀调度：主线程渲染完毕或达到 50ms 保底周期即刻派发，杜绝固定 28ms 门限导致的周期性掉帧跳帧
                    if (self.ui_ready or (now - last_emit_t >= 0.05)) and (now - last_emit_t >= 0.016):
                        last_emit_t = now
                        self.ui_ready = False
                        rgb_array = newest_frame.to_ndarray(format="rgb24")
                        h, w, _ = rgb_array.shape
                        qimg = QImage(rgb_array.tobytes(), w, h, 3 * w, QImage.Format.Format_RGB888).copy()
                        ScreenCastWorker.latest_image = qimg
                        ScreenCastWorker.latest_frame_time = now
                        ScreenCastWorker.latest_udid = self.udid
                        self.frame_ready.emit(qimg, b"")
                        if not has_emitted_first_frame:
                            has_emitted_first_frame = True
                            self.state_changed.emit(True, "投屏已连接")
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

    def _run_ios_pymobiledevice3_stream(self) -> bool:
        """
        基于 pymobiledevice3 ScreenStreamServer 重构的双线程解耦硬件级 60 FPS 实时投屏主引擎：
        1. 生产者 (Asyncio 协程线程)：1:1 复用 pymobiledevice3 原生 ScreenStreamServer (--userspace --no-audio)
           与 UserspaceRsdTunnel，仅执行 UDP 收包、RFC 7798 HEVC 组帧、逐帧内联 RCTL 收据回传与 RTCP 保活，
           事件循环 0 解码阻塞、0 丢包、0 假性拥塞限帧；
        2. 消费者 (独立硬件解码线程)：通过线程安全队列异步消费 Annex-B 帧，调用 PyAV (FFmpeg) hevc SLICE + low_delay
           释放 GIL 持续更新 DPB 参考帧，仅在 UI 就绪时通过 swscale 硬件转换为 32 位对齐 Format_RGB32 QImage，
           彻底消除 Web 端与审查器端之间的性能鸿沟。
        返回 True 表示 pymobiledevice3 引擎曾成功接管运行；返回 False 表示当前设备不支持，自动切换至备选投屏通道。
        """
        import asyncio
        import contextlib
        import queue
        import threading
        import av

        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.remote import userspace_tunnel
            from pymobiledevice3.remote.core_device.display_service import (
                DisplayService,
                is_media_in_use_error,
            )
            from pymobiledevice3.remote.core_device.screen_stream import (
                ScreenStreamServer,
                _SubState,
            )
            from pymobiledevice3.tunneld.api import get_tunneld_device_by_udid
        except Exception as e:
            logging.warning(f"[iOS投屏] pymobiledevice3 ScreenStreamServer 依赖未就绪，切换备选方案: {e}")
            return False

        target_udid = self.udid if (self.udid and not self.udid.startswith("wda_localhost")) else None
        emitted_any_frame = False
        decode_q: "queue.Queue[Optional[Tuple[int, bytes]]]" = queue.Queue(maxsize=90)

        def _hevc_decode_worker():
            """独立硬件解码与 32 位图像转换线程 (彻底脱离 asyncio 事件循环，确保 UDP 收包与 RCTL 回传零延迟)"""
            nonlocal emitted_any_frame

            def _create_hevc_codec():
                c = av.CodecContext.create("hevc", "r")
                with contextlib.suppress(Exception):
                    c.thread_type = "SLICE"
                with contextlib.suppress(Exception):
                    c.options = {"flags": "low_delay"}
                return c

            codec = _create_hevc_codec()
            decoded_any = False
            last_emit_t = 0.0
            stop_decode = False

            while self._is_running and not stop_decode:
                try:
                    first_item = decode_q.get(timeout=0.15)
                except queue.Empty:
                    continue
                if first_item is None:
                    break

                # 批量排空当前队列中到达的帧；若批次中存在最新关键帧则直接跳至最新关键帧开始解码
                batch = [first_item]
                while not decode_q.empty():
                    try:
                        nxt = decode_q.get_nowait()
                    except queue.Empty:
                        break
                    if nxt is None:
                        stop_decode = True
                        break
                    batch.append(nxt)

                last_key_idx = -1
                for idx, (ftype, _) in enumerate(batch):
                    if ftype in (0, 2):
                        last_key_idx = idx
                if last_key_idx > 0:
                    batch = batch[last_key_idx:]

                newest_frame = None
                for ftype, annexb_bytes in batch:
                    if not self._is_running:
                        break
                    if ftype == 2 and decoded_any:
                        with contextlib.suppress(Exception):
                            codec = _create_hevc_codec()
                    try:
                        frames = codec.decode(av.Packet(annexb_bytes))
                        if frames:
                            newest_frame = frames[-1]
                            decoded_any = True
                    except Exception:
                        continue

                # 仅对批次中的最新帧执行一次 swscale 缩放与 32 位对齐 QImage 构造
                if newest_frame is not None and self._is_running:
                    now = time.time()
                    if (self.ui_ready or (now - last_emit_t >= 0.035)) and (now - last_emit_t >= 0.012):
                        try:
                            last_emit_t = now
                            self.ui_ready = False
                            if newest_frame.width > 720:
                                out_w = (newest_frame.width // 2) & ~1
                                out_h = (newest_frame.height // 2) & ~1
                                bgr_frame = newest_frame.reformat(width=out_w, height=out_h, format="bgra")
                            else:
                                bgr_frame = newest_frame.reformat(format="bgra")
                            plane = bgr_frame.planes[0]
                            w, h = bgr_frame.width, bgr_frame.height
                            qimg = QImage(bytes(plane), w, h, plane.line_size, QImage.Format.Format_RGB32).copy()
                            ScreenCastWorker.latest_image = qimg
                            ScreenCastWorker.latest_frame_bytes = None
                            ScreenCastWorker.latest_frame_time = now
                            ScreenCastWorker.latest_udid = self.udid
                            if not emitted_any_frame:
                                emitted_any_frame = True
                                self.state_changed.emit(True, "投屏已连接")
                            self.frame_ready.emit(qimg, b"")
                        except Exception as dec_err:
                            logging.debug(f"[iOS投屏] 帧转换异常: {dec_err}")
                            self.ui_ready = True

        async def _pymobiledevice3_session() -> bool:
            nonlocal emitted_any_frame

            if not self._is_running:
                return True

            loop = asyncio.get_running_loop()
            stop_event = asyncio.Event()
            rsd = None
            owned_tunnel = None
            from_tunneld = False
            server: Optional[ScreenStreamServer] = None
            bg_tasks: List[asyncio.Task] = []

            def _threadsafe_stop():
                def _do_stop():
                    if not stop_event.is_set():
                        stop_event.set()
                with contextlib.suppress(Exception):
                    loop.call_soon_threadsafe(_do_stop)

            self._ios_stop_hook = _threadsafe_stop

            # 启动独立硬件解码消费者线程
            decode_thread = threading.Thread(
                target=_hevc_decode_worker,
                name="IOSPyAVDecodeThread",
                daemon=True,
            )
            decode_thread.start()

            try:
                # 2. 建立 RSD 连接：优先复用后台 tunneld，否则启动免管理员进程内 UserspaceRsdTunnel (--userspace)
                if target_udid:
                    with contextlib.suppress(Exception):
                        rsd = await asyncio.wait_for(get_tunneld_device_by_udid(target_udid), timeout=0.5)
                        if rsd is not None:
                            from_tunneld = True

                if rsd is None:
                    # 强力重置与自愈：清理可能遗留的旧隧道句柄
                    for attr_name in ("_active_tunnel", "_cli_tunnel"):
                        prev_tun = getattr(userspace_tunnel, attr_name, None)
                        if prev_tun is not None:
                            with contextlib.suppress(Exception):
                                await asyncio.wait_for(prev_tun.aclose(), timeout=1.5)
                            setattr(userspace_tunnel, attr_name, None)
                    userspace_tunnel.USERSPACE_ACTIVE = False

                    # 尝试建立隧道，若遇端口占用或单例冲突自动退避自愈
                    for attempt in range(3):
                        try:
                            owned_tunnel = userspace_tunnel.UserspaceRsdTunnel(serial=target_udid, autopair=True, remotepairing_fallback=False)
                            rsd = await asyncio.wait_for(owned_tunnel.aopen(), timeout=8.0)
                            break
                        except Exception as open_err:
                            err_str = str(open_err)
                            if ("already active" in err_str or "ARP Cache" in err_str or "RemoteXPC" in err_str) and attempt < 2:
                                logging.info(f"[iOS投屏] 检测到隧道/端口残留冲突，执行重置与等待自愈 ({attempt+1}/3)...")
                                for attr_name in ("_active_tunnel", "_cli_tunnel"):
                                    setattr(userspace_tunnel, attr_name, None)
                                userspace_tunnel.USERSPACE_ACTIVE = False
                                await asyncio.sleep(0.8)
                            else:
                                raise open_err

                if not self._is_running or rsd is None:
                    return True

                # 3. 优先使用 Apple DVT 开发者通道 (DvtProvider + Screenshot) 进行实时投屏：
                #    不开启系统媒体录屏流，不点亮状态栏紫色投屏图标，彻底绕过 App 的 UIScreen.isCaptured 防录屏白屏/遮罩限制
                try:
                    from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
                    from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

                    logging.info("[iOS投屏] 正在建立 DVT 开发者免录屏检测直连通道...")
                    async with DvtProvider(rsd) as dvt, Screenshot(dvt) as sc:
                        if not self._is_running:
                            return True
                        last_emit_t = 0.0
                        while self._is_running and not stop_event.is_set():
                            raw_bytes = await sc.get_screenshot()
                            if raw_bytes and self._is_running:
                                now = time.time()
                                if self.ui_ready or (now - last_emit_t >= 0.03):
                                    last_emit_t = now
                                    self.ui_ready = False
                                    qimg = QImage.fromData(raw_bytes, "PNG")
                                    if qimg and not qimg.isNull():
                                        ScreenCastWorker.latest_image = qimg
                                        ScreenCastWorker.latest_frame_time = now
                                        ScreenCastWorker.latest_udid = self.udid
                                        ScreenCastWorker.latest_frame_bytes = raw_bytes
                                        if not emitted_any_frame:
                                            emitted_any_frame = True
                                            self.state_changed.emit(True, "投屏已连接 (DVT免录屏屏蔽通道)")
                                        self.frame_ready.emit(qimg, b"")
                            await asyncio.sleep(0.01)
                        return emitted_any_frame or (not self._is_running)
                except Exception as dvt_err:
                    logging.info(f"[iOS投屏] DVT 免录屏通道暂不可用，降级尝试媒体流通道: {dvt_err}")

                # 4. 兜底回退 ScreenStreamServer (若 DVT 开发者镜像未挂载或不可用)
                server = ScreenStreamServer(
                    rsd=rsd,
                    audio_default_on=False,
                    motion_idr=False,
                    rctl_enabled=True,
                    allow_rtcp_fb=False,
                    ltrp_enabled=False,
                )

                async def _silent_audio_udp_drain(transport):
                    """Windows 静默排空配对音频流 RTP 包并更新序号 (--no-audio 免解码，保持双流会话配对活跃)"""
                    while self._is_running and not stop_event.is_set():
                        try:
                            pkt = await transport.recv(65535)
                        except (OSError, asyncio.CancelledError, Exception):
                            return
                        if len(pkt) < 12:
                            continue
                        pt = pkt[1] & 0x7F
                        if 64 <= pt <= 95:
                            continue
                        server._audio_rtp_packets_received += 1
                        seq = int.from_bytes(pkt[2:4], "big")
                        cur_ext = server._audio_rtp_highest_seq
                        cycles = (cur_ext >> 16) & 0xFFFF
                        last_seq16 = cur_ext & 0xFFFF
                        if seq < last_seq16 and (last_seq16 - seq) > 0x8000:
                            cycles = (cycles + 1) & 0xFFFF
                        new_ext = (cycles << 16) | seq
                        if cur_ext == 0 or ((new_ext - cur_ext) & 0xFFFFFFFF) < 0x80000000:
                            server._audio_rtp_highest_seq = new_ext

                server._audio_udp_recv = _silent_audio_udp_drain

                # 预先挂载内存订阅队列，确保首帧 IDR 到达瞬间即刻捕获
                sub_q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=90)
                sub_state = _SubState()
                sub_state.needs_key = True
                sub_state.reset_on_key = True
                sub_state.needs_key_since = loop.time()
                server._subscribers[sub_q] = sub_state

                # 4. 启动音视频配对流与 ScreenStreamServer 守护协程组
                await asyncio.wait_for(server._eager_stream_start(), timeout=15.0)
                if server._active_service is None:
                    logging.info("[iOS投屏] 当前设备未提供原生 startmediastream 硬件视频流，就地复用当前 RSD 隧道切入 DVT 开发者通道")
                    from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
                    from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot
                    async with DvtProvider(rsd) as dvt, Screenshot(dvt) as sc:
                        if not self._is_running:
                            return True
                        last_emit_t = 0.0
                        while self._is_running and not stop_event.is_set():
                            raw_bytes = await sc.get_screenshot()
                            if raw_bytes and self._is_running:
                                now = time.time()
                                if self.ui_ready or (now - last_emit_t >= 0.03):
                                    last_emit_t = now
                                    self.ui_ready = False
                                    qimg = QImage.fromData(raw_bytes, "PNG")
                                    if qimg and not qimg.isNull():
                                        ScreenCastWorker.latest_image = qimg
                                        ScreenCastWorker.latest_frame_time = now
                                        ScreenCastWorker.latest_udid = self.udid
                                        ScreenCastWorker.latest_frame_bytes = raw_bytes
                                        if not emitted_any_frame:
                                            emitted_any_frame = True
                                            self.state_changed.emit(True, "投屏已连接 (DVT开发者通道)")
                                        self.frame_ready.emit(qimg, b"")
                            await asyncio.sleep(0.01)
                        return emitted_any_frame or (not self._is_running)
                if server._init_sequence is not None and sub_q.empty():
                    sub_state.needs_key = False
                    sub_state.reset_on_key = False
                    sub_q.put_nowait(server._init_sequence)
                elif server._active_service is not None and server._rtcp_dest is not None:
                    asyncio.create_task(server._send_rtcp_pli())

                bg_tasks.append(asyncio.create_task(server._stall_watchdog()))
                bg_tasks.append(asyncio.create_task(server._decoder_refresh_loop()))
                bg_tasks.append(asyncio.create_task(server._rctl_feedback_loop()))
                bg_tasks.append(asyncio.create_task(server._keep_awake_loop()))
                server._hid_worker_task = asyncio.create_task(server._hid_worker())
                bg_tasks.append(server._hid_worker_task)

                ScreenCastWorker._active_ios_server = server
                ScreenCastWorker._active_ios_loop = loop

                # 5. 纯内存零阻塞桥接循环：将 HVCC 帧组装为 Annex-B 字节流并投递至独立解码线程
                while self._is_running and not stop_event.is_set():
                    try:
                        msg = await asyncio.wait_for(sub_q.get(), timeout=0.4)
                    except asyncio.TimeoutError:
                        if not emitted_any_frame and server._active_service is not None:
                            with contextlib.suppress(Exception):
                                await server._send_rtcp_pli()
                        continue
                    except (asyncio.CancelledError, Exception):
                        break

                    if not msg or len(msg) < 6:
                        continue

                    frame_type = msg[4]
                    au_data = msg[5:]
                    nals: List[bytes] = []
                    pos = 0
                    data_len = len(au_data)
                    while pos + 4 <= data_len:
                        nal_len = int.from_bytes(au_data[pos : pos + 4], "big")
                        pos += 4
                        if nal_len <= 0 or pos + nal_len > data_len:
                            break
                        nals.append(au_data[pos : pos + nal_len])
                        pos += nal_len

                    if not nals:
                        continue

                    if frame_type in (0, 2):
                        vps, sps, pps = server._vps_nal, server._sps_nal, server._pps_nal
                        if vps and sps and pps:
                            has_inline_vps = any(((n[0] >> 1) & 0x3F) == 32 for n in nals if n)
                            if not has_inline_vps:
                                nals = [vps, sps, pps] + nals

                    annexb_bytes = b"".join(b"\x00\x00\x00\x01" + n for n in nals)
                    if decode_q.full():
                        with contextlib.suppress(queue.Empty):
                            decode_q.get_nowait()
                    decode_q.put_nowait((frame_type, annexb_bytes))

                return emitted_any_frame or (not self._is_running)

            except Exception as exc:
                self._last_ios_error = str(exc)
                if is_media_in_use_error(exc):
                    self.error_occurred.emit("iPhone 相机或麦克风正被前台应用占用，请退出该应用后重新开启投屏")
                    return True
                logging.warning(f"[iOS投屏] pymobiledevice3 视频流异常退出: {exc}")
                return emitted_any_frame
            finally:
                ScreenCastWorker._active_ios_server = None
                ScreenCastWorker._active_ios_loop = None
                self._ios_stop_hook = None
                stop_event.set()
                with contextlib.suppress(Exception):
                    decode_q.put_nowait(None)

                for t in bg_tasks:
                    t.cancel()
                if bg_tasks:
                    with contextlib.suppress(Exception):
                        await asyncio.wait(bg_tasks, timeout=1.0)

                if server is not None:
                    server._subscribers.clear()
                    with contextlib.suppress(Exception):
                        await asyncio.wait_for(server._stop_hid(), timeout=1.0)
                    with contextlib.suppress(Exception):
                        async with server._stream_lock:
                            await asyncio.wait_for(server._stop_active_stream(), timeout=1.5)
                    with contextlib.suppress(Exception):
                        async with server._audio_lock:
                            await asyncio.wait_for(server._stop_audio_stream(), timeout=1.5)

                if rsd is not None:
                    with contextlib.suppress(Exception):
                        await asyncio.wait_for(DisplayService.stop_all_streams(rsd), timeout=2.5)
                    if from_tunneld:
                        with contextlib.suppress(Exception):
                            await asyncio.wait_for(rsd.close(), timeout=1.5)

                if owned_tunnel is not None:
                    with contextlib.suppress(Exception):
                        await asyncio.wait_for(owned_tunnel.aclose(), timeout=2.5)
                for attr_name in ("_active_tunnel", "_cli_tunnel"):
                    setattr(userspace_tunnel, attr_name, None)
                userspace_tunnel.USERSPACE_ACTIVE = False

                decode_thread.join(timeout=0.5)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_pymobiledevice3_session())
        except Exception as e:
            logging.warning(f"[iOS投屏] pymobiledevice3 事件循环退出: {e}")
            return emitted_any_frame
        finally:
            try:
                pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
                for t in pending:
                    t.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            asyncio.set_event_loop(None)
            loop.close()

    def _run_ios_legacy_fallback_stream(self, is_ios_17_plus: bool = True):
        """
        备选 iOS 投屏通道 (当设备系统版本低于 iOS 17 或不支持 CoreDevice 视频流时启用):
        1. 优先探测 WDA 原生 MJPEG 视频流 (/mjpegstream 或 9100 端口)；
        2. 备选 WDA /screenshot 轮询通道；
        3. 兜底进程内 DvtProvider 截图会话。
        """
        import asyncio
        import base64
        import urllib.request

        emitted_any = False
        wda_url, _ = IosWdaManager.get_wda_url(self.udid, allow_spawn=False)
        if not wda_url:
            wda_url = "http://127.0.0.1:8100"

        if self.udid and not self.udid.startswith("wda_localhost"):
            tidevice_bin = shutil.which("tidevice")
            if not tidevice_bin:
                candidate_td = os.path.join(os.path.dirname(sys.executable), "Scripts", "tidevice.exe")
                if os.path.isfile(candidate_td):
                    tidevice_bin = candidate_td
            if tidevice_bin:
                try:
                    # 启动针对当前设备的 9100 串流映射前，彻底杀死旧中继
                    IosWdaManager.kill_relays((9100,))
                    creationflags = 0x08000000 if sys.platform == "win32" else 0
                    self._ios_mjpeg_relay_proc = subprocess.Popen(
                        [tidevice_bin, "-u", self.udid, "relay", "9100", "9100"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags
                    )
                except Exception:
                    pass

        # 探测本地 WDA 端口是否在线，若未启动则 0ms 直接穿透至备选 3 (DVT 原生开发者通道)
        wda_online = IosWdaManager.test_wda_status(wda_url, timeout=0.25)
        if wda_online:
            try:
                settings_payload = json.dumps({
                    "settings": {
                        "mjpegServerFramerate": 60,
                        "mjpegServerScreenshotQuality": 30,
                        "mjpegScalingFactor": 60,
                        "screenshotQuality": 2
                    }
                }).encode("utf-8")
                set_req = urllib.request.Request(
                    f"{wda_url}/appium/settings",
                    data=settings_payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(set_req, timeout=0.8) as _:
                    pass
            except Exception:
                pass

            candidate_urls = [
                "http://127.0.0.1:9100",
                f"{wda_url}/mjpegstream",
                f"{wda_url}/mjpegstream?scale=0.6",
                f"{wda_url}/mjpegstream?fps=30",
            ]

            mjpeg_resp = None
            for test_url in candidate_urls:
                if not self._is_running:
                    break
                try:
                    req = urllib.request.Request(test_url)
                    resp = urllib.request.urlopen(req, timeout=0.8)
                    if resp.status == 200:
                        mjpeg_resp = resp
                        break
                except Exception:
                    continue

            if mjpeg_resp is not None:
                try:
                    with mjpeg_resp as resp:
                        buffer = bytearray()
                        last_emit_t = 0.0
                        while self._is_running:
                            chunk = resp.read1(65536) if hasattr(resp, "read1") else resp.read(8192)
                            if not chunk:
                                break
                            buffer.extend(chunk)
                            if len(buffer) > 4194304:
                                last_soi = buffer.rfind(b"\xff\xd8")
                                if last_soi != -1:
                                    del buffer[:last_soi]
                                else:
                                    buffer.clear()

                            latest_jpg = None
                            while True:
                                start_idx = buffer.find(b"\xff\xd8")
                                if start_idx == -1:
                                    if len(buffer) > 1:
                                        del buffer[:-1]
                                    break
                                end_idx = buffer.find(b"\xff\xd9", start_idx + 2)
                                if end_idx == -1:
                                    if start_idx > 0:
                                        del buffer[:start_idx]
                                    break
                                latest_jpg = bytes(buffer[start_idx : end_idx + 2])
                                del buffer[: end_idx + 2]

                            if latest_jpg and self._is_running:
                                now = time.time()
                                if (self.ui_ready or (now - last_emit_t >= 0.04)) and (now - last_emit_t >= 0.016):
                                    last_emit_t = now
                                    self.ui_ready = False
                                    qimg = QImage.fromData(latest_jpg, "JPEG")
                                    if qimg and not qimg.isNull():
                                        ScreenCastWorker.latest_image = qimg
                                        ScreenCastWorker.latest_frame_time = now
                                        ScreenCastWorker.latest_udid = self.udid
                                        ScreenCastWorker.latest_frame_bytes = latest_jpg
                                        self.frame_ready.emit(qimg, b"")
                                        emitted_any = True
                    if emitted_any:
                        return True
                except Exception:
                    pass

        if not self._is_running:
            return emitted_any

        # 备选 2: WDA /screenshot 极速轮询通道 (原生 20-30 FPS 丝滑出图，多进程防冲突最高保障)
        if IosWdaManager.test_wda_status(wda_url, timeout=0.6) and self._is_running:
            last_poll_t = 0.0
            consecutive_errors = 0
            while self._is_running:
                try:
                    now = time.time()
                    if self.ui_ready or (now - last_poll_t >= 0.035):
                        last_poll_t = now
                        req = urllib.request.Request(f"{wda_url}/screenshot", headers={"Accept": "application/json"})
                        with urllib.request.urlopen(req, timeout=1.2) as resp:
                            if resp.status == 200:
                                data = json.loads(resp.read().decode("utf-8"))
                                b64_img = data.get("value", "")
                                if b64_img:
                                    raw_bytes = base64.b64decode(b64_img)
                                    qimg = QImage.fromData(raw_bytes)
                                    if qimg and not qimg.isNull() and self._is_running:
                                        self.ui_ready = False
                                        ScreenCastWorker.latest_image = qimg
                                        ScreenCastWorker.latest_frame_time = now
                                        ScreenCastWorker.latest_udid = self.udid
                                        ScreenCastWorker.latest_frame_bytes = raw_bytes
                                        if not emitted_any:
                                            emitted_any = True
                                            self.state_changed.emit(True, "投屏已连接 (WDA自动化通道)")
                                        self.frame_ready.emit(qimg, b"")
                                        consecutive_errors = 0
                except Exception:
                    consecutive_errors += 1
                    if consecutive_errors > 8:
                        break
                    time.sleep(0.08)
                    continue
                time.sleep(0.005)
            if emitted_any:
                return True

        if not self._is_running:
            return emitted_any

        # 备选 3: 进程内 DvtProvider 持久会话兜底 (双模自适应：RSD 隧道 + Lockdown 双栈兼容)
        async def _run_in_process_dvt():
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.remote import userspace_tunnel
            from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
            from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

            udid = self.udid if (self.udid and not self.udid.startswith("wda_localhost")) else None
            provider = None
            owned_tunnel = None
            emitted_any = False
            try:
                # 仅针对 iOS 17+ 设备尝试 UserspaceRsdTunnel (并禁用 bonjour 广播回退杜绝挂起)
                if is_ios_17_plus:
                    try:
                        for attr_name in ("_active_tunnel", "_cli_tunnel"):
                            setattr(userspace_tunnel, attr_name, None)
                        userspace_tunnel.USERSPACE_ACTIVE = False
                        owned_tunnel = userspace_tunnel.UserspaceRsdTunnel(serial=udid, autopair=True, remotepairing_fallback=False)
                        provider = await asyncio.wait_for(owned_tunnel.aopen(), timeout=2.5)
                    except Exception:
                        provider = None

                # 若 RSD 不支持或系统低于 iOS 17，则降级为传统 USB Lockdown (iOS 16 及以下旧机型)
                if provider is None:
                    provider = await create_using_usbmux(serial=udid)

                try:
                    async with DvtProvider(provider) as dvt, Screenshot(dvt) as sc:
                        last_emit_t = 0.0
                        while self._is_running:
                            raw_bytes = await sc.get_screenshot()
                            if raw_bytes and self._is_running:
                                now = time.time()
                                if self.ui_ready or (now - last_emit_t >= 0.03):
                                    last_emit_t = now
                                    self.ui_ready = False
                                    qimg = QImage.fromData(raw_bytes, "PNG")
                                    if qimg and not qimg.isNull():
                                        ScreenCastWorker.latest_image = qimg
                                        ScreenCastWorker.latest_frame_time = now
                                        ScreenCastWorker.latest_udid = self.udid
                                        ScreenCastWorker.latest_frame_bytes = raw_bytes
                                        if not emitted_any:
                                            emitted_any = True
                                            self.state_changed.emit(True, "投屏已连接 (DVT开发者通道)")
                                        self.frame_ready.emit(qimg, b"")
                            await asyncio.sleep(0.01)
                except Exception as dvt_err:
                    # 若 DVT 服务不可用 (如 iOS <= 16 未挂载 Developer Disk Image)，尝试通过原生 ScreenshotService 兜底
                    if not emitted_any and not is_ios_17_plus and self._is_running:
                        try:
                            from pymobiledevice3.services.screenshot import ScreenshotService
                            sc_svc = ScreenshotService(provider)
                            last_emit_t = 0.0
                            while self._is_running:
                                raw_bytes = await sc_svc.take_screenshot()
                                if raw_bytes and self._is_running:
                                    now = time.time()
                                    if self.ui_ready or (now - last_emit_t >= 0.04):
                                        last_emit_t = now
                                        self.ui_ready = False
                                        qimg = QImage.fromData(raw_bytes, "PNG")
                                        if qimg and not qimg.isNull():
                                            ScreenCastWorker.latest_image = qimg
                                            ScreenCastWorker.latest_frame_time = now
                                            ScreenCastWorker.latest_udid = self.udid
                                            ScreenCastWorker.latest_frame_bytes = raw_bytes
                                            if not emitted_any:
                                                emitted_any = True
                                                self.state_changed.emit(True, "投屏已连接 (原生截屏通道)")
                                            self.frame_ready.emit(qimg, b"")
                                await asyncio.sleep(0.01)
                        except Exception:
                            pass
                return emitted_any or (not self._is_running)
            finally:
                if owned_tunnel is not None:
                    with contextlib.suppress(Exception):
                        await asyncio.wait_for(owned_tunnel.aclose(), timeout=1.5)
                for attr_name in ("_active_tunnel", "_cli_tunnel"):
                    setattr(userspace_tunnel, attr_name, None)
                userspace_tunnel.USERSPACE_ACTIVE = False

        try:
            return asyncio.run(_run_in_process_dvt())
        except Exception as e:
            logging.warning(f"[iOS备选投屏] DvtProvider 通道退出: {e}")
            return False
        finally:
            mjpeg_proc = getattr(self, "_ios_mjpeg_relay_proc", None)
            if mjpeg_proc is not None:
                try:
                    mjpeg_proc.terminate()
                    mjpeg_proc.wait(timeout=0.5)
                except Exception:
                    try:
                        mjpeg_proc.kill()
                    except Exception:
                        pass
                self._ios_mjpeg_relay_proc = None

    def _run_ios_stream(self):
        """
        iOS 实时投屏总调度器：
        1. 针对 iOS 17+ 架构设备 (iPhone 12/13/14/15/16 等)，优先使用 pymobiledevice3 原生 CoreDevice / DVT 开发者通道 (_run_ios_pymobiledevice3_stream)；
        2. 针对 iOS 16 及以下旧架构设备 (iPhone 6s/7/8/X 等)，自动跳过 RSD 隧道与 5s 冗余 Bonjour 广播扫描，直连 WDA MJPEG / USB Lockdown DVT 通道；
        3. 启动前与退出后自动彻底释放 8100/9100 中继端口，杜绝换机端口冲突。
        """
        ScreenCastWorker.is_active = True
        # 换机安全屏障：启动前彻底清理可能残留的 8100/9100 端口独占
        IosWdaManager.kill_relays()

        acquired_lock = ScreenCastWorker._ios_tunnel_lock.acquire(blocking=True, timeout=3.5)
        if not acquired_lock:
            # 隧道冲突自愈保护：若被旧会话遗留锁占用，强制清理并给予 2.0s 重试
            ScreenCastWorker.release_all_tunnels()
            acquired_lock = ScreenCastWorker._ios_tunnel_lock.acquire(blocking=True, timeout=2.0)
            if not acquired_lock:
                logging.warning(f"[iOS投屏] 设备 {self.udid} 隧道锁正被占用")
                self.error_occurred.emit("iOS 投屏通道正忙，请稍候再试")
                return
        try:
            # 极速探测设备 iOS 主版本 (耗时仅 ~40-80ms)
            is_ios_17_plus = True
            if self.udid and not self.udid.startswith("wda_localhost"):
                try:
                    ver_str = IosWdaManager.get_device_product_version(self.udid)
                    if ver_str:
                        major_ver = int(ver_str.split(".")[0])
                        if major_ver < 17:
                            is_ios_17_plus = False
                            logging.info(f"[iOS投屏] 设备 {self.udid} 系统版本为 iOS {ver_str} (< 17)，自动跳过 RSD 隧道直接启用经典 USB/WDA 投屏")
                except Exception:
                    pass

            ok = False
            # 智能双模调度：若本地 8100 WDA 服务已在线 (如外部守护脚本已就绪)，优先复用 WDA 高速通道，杜绝底层 RSD 隧道抢占
            wda_ready = IosWdaManager.test_wda_status("http://127.0.0.1:8100", timeout=0.25)
            if wda_ready:
                logging.info(f"[iOS投屏] 检测到 WDA 8100 处于就绪状态，优先复用 WDA 串流通道")
                ok = bool(self._run_ios_legacy_fallback_stream(is_ios_17_plus=is_ios_17_plus))

            if not ok and self._is_running and is_ios_17_plus:
                ok = self._run_ios_pymobiledevice3_stream()

            if not self._is_running:
                return

            # 若原生硬件流未激活，秒级平滑切入备选 WDA / DVT 通道
            if not ok and self._is_running:
                ok = bool(self._run_ios_legacy_fallback_stream(is_ios_17_plus=is_ios_17_plus))

            # 若所有投屏通道均未能建立且 Worker 仍处于运行状态，向用户发出精准提示，彻底杜绝无提示闪退
            if not ok and self._is_running:
                import asyncio
                from pymobiledevice3.usbmux import list_devices as pmd_list_devices
                online_serials = []
                with contextlib.suppress(Exception):
                    mux_devs = asyncio.run(asyncio.wait_for(pmd_list_devices(), timeout=1.0))
                    online_serials = [str(getattr(m, "serial", "") or "") for m in (mux_devs or [])]

                if self.udid and self.udid not in online_serials:
                    self.error_occurred.emit(f"未检测到设备 {self.udid} 的USB物理连接，请确认数据线插紧并点击 [🔄] 刷新列表")
                else:
                    last_err = getattr(self, "_last_ios_error", "")
                    is_trust_issue = any(k in last_err.lower() for k in [
                        "not paired", "passwordprotected", "pairingdialog", "trust", "invalidhostid"
                    ])
                    if is_trust_issue:
                        self.error_occurred.emit("未能从 iPhone 获取投屏画面：请确认屏幕已【点亮并解锁】，且已在手机上点击【信任此电脑】")
                    elif last_err:
                        self.error_occurred.emit(f"未能建立 iOS 投屏通道 ({last_err})，请重新点击【实时投屏】开启")
                    else:
                        self.error_occurred.emit("未能建立 iOS 投屏通道，请确认手机已点亮解锁并点击 [🔄] 刷新设备")
        finally:
            ScreenCastWorker.is_active = False
            IosWdaManager.kill_relays()
            if acquired_lock:
                try:
                    ScreenCastWorker._ios_tunnel_lock.release()
                except RuntimeError:
                    pass

    def run(self):
        self._is_running = True
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

    @staticmethod
    def _inject_android_toast_xml(xml_text: str, toast_text: str) -> str:
        """
        将 Android 无障碍事件 (TYPE_NOTIFICATION_STATE_CHANGED) 捕获的系统 Toast 注入层级树 XML：
        Android 原生 dumpWindowHierarchy 不会导出 android.widget.Toast 悬浮窗，
        通过 uiautomator2 getLastToast 补齐标准 Toast 节点，使审查器 DOM 树与推荐定位器完整可见。
        """
        if not toast_text or "</hierarchy>" not in xml_text or "android.widget.Toast" in xml_text:
            return xml_text
        from xml.sax.saxutils import escape as _xml_escape

        w, h = 1080, 2340
        for m in re.finditer(r'bounds="\[0,0\]\[(\d+),(\d+)\]"', xml_text[:65536]):
            cand_w, cand_h = int(m.group(1)), int(m.group(2))
            if cand_w >= 600 and cand_h >= 1000:
                w, h = cand_w, cand_h
                break
        left, top, right, bottom = int(w * 0.25), int(h * 0.49), int(w * 0.75), int(h * 0.56)
        safe_text = _xml_escape(toast_text, {'"': "&quot;", "'": "&apos;"})
        toast_node = (
            f'<node index="99" text="{safe_text}" resource-id="" '
            f'class="android.widget.Toast" package="android" content-desc="" '
            f'checkable="false" checked="false" clickable="false" enabled="true" '
            f'focusable="false" focused="false" scrollable="false" long-clickable="false" '
            f'password="false" selected="false" bounds="[{left},{top}][{right},{bottom}]" />'
        )
        idx = xml_text.rfind("</hierarchy>")
        return xml_text[:idx] + toast_node + xml_text[idx:]

    @staticmethod
    def _dump_android_hierarchy(udid: str, layout_file: str) -> bool:
        """
        安卓实时 DOM 树高可靠抓取引擎（彻底根治 uiautomator 服务锁抢占与固定路径旧文件残留污染）：
        1. 优先探测本地活跃 Appium Session (/sessions -> /source)，调试用例期间零冲突秒级共享最新 DOM；
        2. 次选复用 uiautomator2 (u2.dump_hierarchy) JSON-RPC 内存直出，与审查器自身 u2 截屏/投屏同进程零锁冲突，且免疫动态光标/动画阻塞；
        3. 兜底采用唯一时间戳路径的 adb shell uiautomator dump（若遇僵尸 uiautomator 锁冲突则自动释放锁重试，且绝不读取历史残留的旧 XML）。
        """
        import urllib.request

        norm_layout = os.path.normpath(os.path.abspath(layout_file))
        os.makedirs(os.path.dirname(norm_layout), exist_ok=True)
        if os.path.exists(norm_layout):
            try:
                os.remove(norm_layout)
            except Exception:
                pass

        # 通道 1：探测本地活跃的 Appium Server 会话（前置 50ms TCP 快探，跳过未监听端口，避免拖慢瞬态 Toast 抓树时机）
        import socket as _sock
        for port in (4723, 4725):
            try:
                with _sock.create_connection(("127.0.0.1", port), timeout=0.05):
                    pass
            except Exception:
                continue
            for prefix in ("", "/wd/hub"):
                base_url = f"http://127.0.0.1:{port}{prefix}"
                try:
                    req = urllib.request.Request(f"{base_url}/sessions")
                    with urllib.request.urlopen(req, timeout=0.35) as resp:
                        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    sessions = data.get("value") or []
                    for sess in sessions:
                        sid = sess.get("id")
                        caps = sess.get("capabilities") or {}
                        sess_udid = str(caps.get("deviceUDID") or caps.get("udid") or caps.get("deviceName") or "")
                        if sid and (not udid or not sess_udid or udid in sess_udid):
                            src_req = urllib.request.Request(f"{base_url}/session/{sid}/source")
                            with urllib.request.urlopen(src_req, timeout=2.5) as src_resp:
                                src_data = json.loads(src_resp.read().decode("utf-8", errors="ignore"))
                            xml_str = src_data.get("value") or ""
                            if isinstance(xml_str, str) and "<hierarchy" in xml_str and len(xml_str) > 100:
                                with open(norm_layout, "w", encoding="utf-8") as f_xml:
                                    f_xml.write(xml_str)
                                return True
                except Exception:
                    continue

        # 通道 2：复用 uiautomator2 JSON-RPC 守护进程直接导出最新层级树（与 u2.screenshot 共享服务，零锁冲突，不受页面动态动画阻塞）
        try:
            import uiautomator2 as u2
            d = u2.connect(udid) if udid else u2.connect()
            xml_text = d.dump_hierarchy(compressed=False)
            if isinstance(xml_text, str) and "<hierarchy" in xml_text and len(xml_text) > 100:
                # 同步读取并消费 Android 无障碍事件捕获的系统 Toast（dumpWindowHierarchy 原生不导出 android.widget.Toast）
                try:
                    toast_msg = (d.jsonrpc.getLastToast() or "").strip()
                    if toast_msg:
                        xml_text = CaptureWorker._inject_android_toast_xml(xml_text, toast_msg)
                        d.jsonrpc.clearLastToast()
                except Exception:
                    pass
                with open(norm_layout, "w", encoding="utf-8") as f_xml:
                    f_xml.write(xml_text)
                return True
        except Exception as e:
            logging.debug(f"[安卓DOM抓取] uiautomator2 dump_hierarchy 通道未命中，切换 ADB 通道: {e}")

        # 通道 3：原生 ADB uiautomator dump（使用唯一时间戳远端路径，彻底斩断旧文件缓存污染，并在锁冲突时自动清理重试）
        uid = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        remote_xml = f"/data/local/tmp/appium_layout_{uid}.xml"
        try:
            # 清理历史遗留的固定路径旧缓存文件
            run_adb(["shell", "rm", "-f", "/data/local/tmp/appium_layout.xml"], udid, timeout=1.5)

            out = run_adb(["shell", "uiautomator", "dump", remote_xml], udid, timeout=5.0)
            if "dumped to" not in out.lower():
                # 释放可能残留的僵尸 uiautomator 占用锁后重试一次
                run_adb(["shell", "am", "force-stop", "com.github.uiautomator"], udid, timeout=1.5)
                run_adb(["shell", "pkill", "-f", "uiautomator"], udid, timeout=1.5)
                time.sleep(0.15)
                out = run_adb(["shell", "uiautomator", "dump", "--compressed", remote_xml], udid, timeout=5.0)
                if "dumped to" not in out.lower():
                    run_adb(["shell", "uiautomator", "dump", remote_xml], udid, timeout=5.0)

            run_adb(["pull", remote_xml, norm_layout], udid, timeout=4.0)
            if os.path.exists(norm_layout) and os.path.getsize(norm_layout) > 100:
                return True
        except Exception as e:
            logging.warning(f"[安卓DOM抓取] ADB uiautomator dump 异常: {e}")
        finally:
            try:
                run_adb(["shell", "rm", "-f", remote_xml], udid, timeout=1.5)
            except Exception:
                pass

        return False

    @staticmethod
    def _dump_ios_hierarchy(udid: str, layout_file: str) -> bool:
        """
        iOS 实时 DOM 树高可靠多通道抓取引擎 (对齐安卓多通道架构与 Appium Inspector):
        1. 通道 1 (首选)：探测本地活跃的 Appium Server 会话 (4724, 4723, 4725 等)，若 Appium Inspector 或自动化测试正处于调试会话中，直接复用 /session/{sid}/source，耗时仅 1~2s，100% 与 Inspector 原生树完全一致且零冲突；
        2. 通道 2 (WDA 直连会话)：若未启动 Appium Server，探测本地活跃 WDA 8100/8200 端口；若无会话则自动向 /session 建立通用前台轻量会话，再通过 /session/{sid}/source 快速提取 App 结构；
        3. 通道 3 (WDA 根降级)：作为保底兜底尝试 GET /source?format=xml。
        """
        import urllib.request
        norm_layout = os.path.normpath(os.path.abspath(layout_file))
        os.makedirs(os.path.dirname(norm_layout), exist_ok=True)
        if os.path.exists(norm_layout):
            try:
                os.remove(norm_layout)
            except Exception:
                pass

        # 通道 1：优先探测本地活跃 Appium Server 会话（前置 50ms TCP 快探，跳过未监听端口）
        import socket as _sock
        for port in (4724, 4723, 4725, 4726, 4728):
            try:
                with _sock.create_connection(("127.0.0.1", port), timeout=0.05):
                    pass
            except Exception:
                continue
            for prefix in ("", "/wd/hub"):
                base_url = f"http://127.0.0.1:{port}{prefix}"
                try:
                    req = urllib.request.Request(f"{base_url}/sessions")
                    with urllib.request.urlopen(req, timeout=0.35) as resp:
                        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    sessions = data.get("value") or []
                    for sess in sessions:
                        sid = sess.get("id")
                        caps = sess.get("capabilities") or {}
                        plat = str(caps.get("platformName") or "").lower()
                        sess_udid = str(caps.get("deviceUDID") or caps.get("udid") or "")
                        # 匹配 iOS 平台会话 (或单会话直接复用)
                        if sid and (plat in ("ios", "") or len(sessions) == 1):
                            if not udid or not sess_udid or udid in sess_udid or len(sessions) == 1:
                                src_req = urllib.request.Request(f"{base_url}/session/{sid}/source")
                                with urllib.request.urlopen(src_req, timeout=4.5) as src_resp:
                                    src_data = json.loads(src_resp.read().decode("utf-8", errors="ignore"))
                                xml_str = src_data.get("value") or ""
                                if isinstance(xml_str, str) and ("<XCUIElementType" in xml_str or "<AppiumAUT" in xml_str) and len(xml_str) > 100:
                                    with open(norm_layout, "w", encoding="utf-8") as f_xml:
                                        f_xml.write(xml_str)
                                    logging.info(f"[iOS DOM抓取] 成功命中 Appium 活跃会话 (端口 {port}, Session {sid[:8]})")
                                    return True
                except Exception:
                    continue

        # 通道 2：直连本地 WDA 服务端口 (8100 / 8200)，支持自动激活前台轻量会话
        wda_url, _ = IosWdaManager.get_wda_url(udid, allow_spawn=False)
        if not wda_url:
            wda_url = "http://127.0.0.1:8100"

        if IosWdaManager.test_wda_status(wda_url, timeout=1.5):
            sid = None
            try:
                st_req = urllib.request.Request(f"{wda_url}/status")
                with urllib.request.urlopen(st_req, timeout=2.0) as st_resp:
                    st_data = json.loads(st_resp.read().decode("utf-8", errors="ignore"))
                sid = st_data.get("sessionId") or st_data.get("value", {}).get("sessionId")
            except Exception:
                pass

            # 2.1 若已有活跃 sessionId，直接获取页面树
            if sid:
                try:
                    src_url = f"{wda_url}/session/{sid}/source?format=xml"
                    src_req = urllib.request.Request(src_url)
                    with urllib.request.urlopen(src_req, timeout=12.0) as src_resp:
                        raw_bytes = src_resp.read()
                    if raw_bytes and len(raw_bytes) > 100:
                        with open(norm_layout, "wb") as f_out:
                            f_out.write(raw_bytes)
                        logging.info(f"[iOS DOM抓取] 成功通过 WDA 会话 {sid[:8]} 提取组件树 (大小: {len(raw_bytes)} 字节)")
                        return True
                except Exception as e:
                    logging.debug(f"[iOS DOM抓取] WDA session/source 尝试降级: {e}")

            # 2.2 优先尝试免创建会话直接请求根路径 /source (对 WDA 原生直连最快，耗时 0.5~3s)
            for fmt in ("xml", "json"):
                try:
                    req = urllib.request.Request(f"{wda_url}/source?format={fmt}")
                    with urllib.request.urlopen(req, timeout=10.0) as resp:
                        raw_bytes = resp.read()
                    if raw_bytes and len(raw_bytes) > 100 and (b"<XCUIElementType" in raw_bytes or b"\"children\"" in raw_bytes or b"\"type\"" in raw_bytes):
                        with open(norm_layout, "wb") as f_out:
                            f_out.write(raw_bytes)
                        logging.info(f"[iOS DOM抓取] 成功通过 WDA 根 /source ({fmt}) 提取组件树")
                        return True
                except Exception:
                    pass

            # 2.3 若根路径需绑定会话，按 W3C 标准创建一个轻量会话后再读取 /session/{sid}/source
            try:
                init_data = json.dumps({"capabilities": {"alwaysMatch": {}, "firstMatch": [{}]}}).encode("utf-8")
                init_req = urllib.request.Request(
                    f"{wda_url}/session",
                    data=init_data,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(init_req, timeout=6.0) as init_resp:
                    init_res = json.loads(init_resp.read().decode("utf-8", errors="ignore"))
                    new_sid = init_res.get("sessionId") or init_res.get("value", {}).get("sessionId")
                if new_sid:
                    src_req = urllib.request.Request(f"{wda_url}/session/{new_sid}/source?format=xml")
                    with urllib.request.urlopen(src_req, timeout=12.0) as src_resp:
                        raw_bytes = src_resp.read()
                    if raw_bytes and len(raw_bytes) > 100:
                        with open(norm_layout, "wb") as f_out:
                            f_out.write(raw_bytes)
                        logging.info(f"[iOS DOM抓取] 成功通过新建 WDA 会话 {new_sid[:8]} 提取组件树")
                        return True
            except Exception as e:
                logging.debug(f"[iOS DOM抓取] WDA 新建会话抓取异常: {e}")

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
                # 主动点亮屏幕，杜绝熄屏休眠导致 dumpLayout 超时
                run_hdc(["shell", "power-shell wakeup"], self.udid, timeout=0.8)
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
                            for attempt in range(2):
                                run_hdc(["shell", f"uitest dumpLayout -p {remote_json}"], self.udid, timeout=4.5)
                                run_hdc(["file", "recv", remote_json, layout_file], self.udid, timeout=4.0)
                                layout_ok = os.path.exists(layout_file) and os.path.getsize(layout_file) > 100
                                if layout_ok:
                                    break
                                if attempt == 0:
                                    time.sleep(0.35)
                        except Exception:
                            pass
                        finally:
                            try:
                                run_hdc(["shell", f"rm -f {remote_json}"], self.udid, timeout=1.0)
                            except Exception:
                                pass

                    if not layout_ok and not ScreenCastWorker.is_active:
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

                # 步骤 1.1: 若 RPC 偶发受限，再平滑尝试 CLI dumpLayout (含守护进程刚启动时的 0.35s 自愈重试)
                if not layout_ok:
                    try:
                        for attempt in range(2):
                            run_hdc(["shell", f"uitest dumpLayout -p {remote_json}"], self.udid, timeout=4.5)
                            run_hdc(["file", "recv", remote_json, layout_file], self.udid, timeout=4.0)
                            layout_ok = os.path.exists(layout_file) and os.path.getsize(layout_file) > 100
                            if layout_ok:
                                break
                            if attempt == 0:
                                time.sleep(0.35)
                    except Exception:
                        pass
                    finally:
                        try:
                            run_hdc(["shell", f"rm -f {remote_json}"], self.udid, timeout=1.0)
                        except Exception:
                            pass

                if not layout_ok and not ScreenCastWorker.is_active:
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
                    if self._dump_android_hierarchy(self.udid, layout_file):
                        self.dom_finished.emit(layout_file, "android")
                    else:
                        self.failed.emit("获取安卓组件层级树失败，请确认设备屏幕已解锁且已授权 USB 调试。")
                    return

                # 全量模式优先抢抓 DOM 树，最大限度在 Toast/悬浮弹窗消失前捕获瞬态节点，紧接着再抓画面底图
                layout_ok = False
                if self.mode != "screen_only":
                    layout_ok = self._dump_android_hierarchy(self.udid, layout_file)

                # 安卓画面采集: 优先复用当前活跃投屏的新鲜显存帧 (耗时 0ms)
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

                if self.mode == "screen_only":
                    if shot_ok:
                        self.screen_finished.emit(local_png)
                    else:
                        self.failed.emit("获取安卓真机画面失败，请确认屏幕已点亮并解锁。")
                    return

                if shot_ok and os.path.exists(local_png) and layout_ok and os.path.exists(layout_file):
                    self.finished.emit(local_png, layout_file, "android")
                elif shot_ok and os.path.exists(local_png):
                    self.screen_finished.emit(local_png)
                    self.failed.emit("抓取安卓组件层级树失败，请确认设备屏幕已解锁且已授权 USB 调试。")
                else:
                    self.failed.emit("抓取安卓现场数据失败，请确认设备屏幕已解锁且已授权 USB 调试。")

            elif self.platform == "ios":
                import urllib.request
                shot_ok = False
                layout_ok = False

                # 1. 纯 DOM 刷新模式：直接调用高可靠多通道引擎，失败时明确提示原因，避免覆盖为空树
                if self.mode == "dom_only":
                    if self._dump_ios_hierarchy(self.udid, layout_file):
                        self.dom_finished.emit(layout_file, "ios")
                    else:
                        wda_ok = IosWdaManager.test_wda_status("http://127.0.0.1:8100", timeout=0.6)
                        if not wda_ok:
                            self.failed.emit("8100 端口 WDA 服务未连通，请先点击顶部【启动服务】直至显示绿色【正在运行】。")
                        else:
                            self.failed.emit("WDA 已在线但未能返回页面 DOM 树，请解锁手机并确保前台应用处于活跃状态后重试。")
                    return

                # 2. 优先零拷贝复用 pymobiledevice3 实时投屏内存帧
                if (
                    ScreenCastWorker.is_active
                    or (ScreenCastWorker.latest_image is not None and ScreenCastWorker.latest_udid == self.udid)
                ):
                    for _ in range(160):
                        latest_bytes = ScreenCastWorker.get_latest_jpeg_bytes(self.udid)
                        if latest_bytes:
                            try:
                                with open(local_png, "wb") as f_out:
                                    f_out.write(latest_bytes)
                                shot_ok = True
                                break
                            except Exception:
                                pass
                        if not ScreenCastWorker.is_active:
                            break
                        time.sleep(0.05)

                if self.mode == "screen_only" and shot_ok:
                    self.screen_finished.emit(local_png)
                    return

                # 3. 若投屏未开启且尚未获取画面，安全尝试 CoreDevice 单帧截屏能力获取现场
                if not shot_ok and not ScreenCastWorker.is_active:
                    single_bytes = ScreenCastWorker.capture_single_ios_frame(self.udid, timeout=4.0)
                    if single_bytes:
                        try:
                            with open(local_png, "wb") as f_out:
                                f_out.write(single_bytes)
                            shot_ok = True
                        except Exception:
                            pass

                # 3.1 工业级坚固兜底：若投屏未开启且单帧通道未返回，启用 Apple DVT 原生开发者通道截屏
                if not shot_ok and not ScreenCastWorker.is_active:
                    try:
                        creationflags = 0x08000000 if sys.platform == "win32" else 0
                        pmd_cmd = ["pymobiledevice3", "developer", "dvt", "screenshot", local_png]
                        if self.udid and not self.udid.startswith("wda_localhost"):
                            pmd_cmd.extend(["--udid", self.udid])
                        subprocess.run(pmd_cmd, timeout=8, capture_output=True, creationflags=creationflags)
                        shot_ok = os.path.exists(local_png) and os.path.getsize(local_png) > 1000
                    except Exception:
                        pass

                # 3.2 终极画面兜底：若前序通道均未取到画面，尝试 WDA /screenshot
                if not shot_ok:
                    wda_url, _ = IosWdaManager.get_wda_url(self.udid, allow_spawn=False)
                    if not wda_url:
                        wda_url = "http://127.0.0.1:8100"
                    try:
                        req = urllib.request.Request(f"{wda_url}/screenshot")
                        with urllib.request.urlopen(req, timeout=5) as resp:
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
                    else:
                        self.failed.emit("未能从 iOS 设备获取画面：请确认 iPhone 处于【解锁点亮状态】。")
                    return

                # 4. 抓取 DOM 树：调用工业级多通道高可靠抓取引擎
                layout_ok = self._dump_ios_hierarchy(self.udid, layout_file)

                # 4.1 源头去黑边：在落盘后立即将 DVT/CoreDevice 帧缓冲对齐黑边裁净，确保与实时投屏同尺寸
                if shot_ok and layout_ok:
                    try:
                        normalize_ios_screenshot_file(local_png, layout_file)
                    except Exception:
                        pass

                # 5. 结果输出与静默兜底 (底图与 DOM 树交付)
                if shot_ok and layout_ok:
                    self.finished.emit(local_png, layout_file, "ios")
                elif layout_ok and not shot_ok:
                    # DOM 结构树已完整获取，画面临时获取超时 -> 自动生成轻量占位背景图，确保 DOM 审查流程畅通无阻
                    try:
                        qimg = QImage(1170, 2532, QImage.Format.Format_RGB32)
                        qimg.fill(QColor("#f8fafc"))
                        painter = QPainter(qimg)
                        painter.setPen(QPen(QColor("#cbd5e1"), 2))
                        painter.drawRect(20, 20, 1130, 2492)
                        painter.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
                        painter.setPen(QColor("#64748b"))
                        painter.drawText(QRect(40, 1000, 1090, 100), Qt.AlignmentFlag.AlignCenter, "真机画面获取超时 (屏幕熄灭或权限受限)")
                        painter.setFont(QFont("Microsoft YaHei", 14))
                        painter.setPen(QColor("#94a3b8"))
                        painter.drawText(QRect(40, 1120, 1090, 80), Qt.AlignmentFlag.AlignCenter, "iOS 原生 DOM 组件层级树已成功载入，可在中栏与右栏正常审查")
                        painter.end()
                        qimg.save(local_png, "PNG")
                    except Exception:
                        pass
                    self.finished.emit(local_png, layout_file, "ios")
                elif shot_ok:
                    minimal_root = {"attributes": {"type": "Screen", "bounds": "[0,0][1170,2532]"}, "children": []}
                    with open(layout_file, "w", encoding="utf-8") as f:
                        json.dump(minimal_root, f)
                    self.finished.emit(local_png, layout_file, "ios")
                else:
                    self.failed.emit("未能从 iOS 设备获取画面：请确认 iPhone 处于【解锁点亮状态】（息屏会自动休眠开发者调试通道），且未被爱思助手等外部工具独占投屏通道。")

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
        self.screen_image: Optional[QImage] = None
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
        self.screen_image = None
        self.flat_components.clear()
        self.comp_map.clear()
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
        self.screen_image = None
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

    def update_screen_image(self, img: QImage, keep_components: bool = True):
        """
        实时投屏流极速直通渲染 (0 QPixmap 转换开销，硬件级显卡纹理合成):
        直接在显存/内存中装载 QImage，避免在 Qt 主线程执行耗时 5~15ms 的 QPixmap.fromImage 拷贝，
        保留当前高亮组件，彻底杜绝切屏掉帧与事件积压，实现真 60fps 丝滑无延迟渲染。
        """
        if not img or img.isNull():
            return
        self.screen_image = img
        self.orig_w = img.width()
        self.orig_h = img.height()
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

    def update_components_only(self, components: List[Dict[str, Any]], layout_size: Optional[Tuple[int, int]] = None):
        """
        仅更新 DOM 组件层级数据 (复用当前底图与缩放比例，对齐 HoKit UIViewer 叠加层机制):
        1. 保持当前视口缩放和平移状态不被重置，审查体验丝滑连贯；
        2. 优先使用解析 DOM 树时所用的精确屏幕基准分辨率 (layout_size)，杜绝部分组件边界导致比例偏移。
        """
        self.flat_components = components
        self.comp_map = {c["node_id"]: c for c in components}
        self.hover_node_id = ""
        if self.selected_node_id not in self.comp_map:
            self.selected_node_id = ""
        if layout_size and layout_size[0] > 0 and layout_size[1] > 0:
            self.layout_w, self.layout_h = int(layout_size[0]), int(layout_size[1])
        else:
            # 自适应从组件最大右下边界校准 layout 坐标系
            max_r = max((c.get("right", 0) for c in components if c.get("right", 0) > 0), default=0)
            max_b = max((c.get("bottom", 0) for c in components if c.get("bottom", 0) > 0), default=0)
            if max_r >= 800 and max_b >= 1200:
                self.layout_w = max_r
                self.layout_h = max_b
        self.update()

    def load_screenshot(self, img_path: str, components: List[Dict[str, Any]], layout_size: Optional[Tuple[int, int]] = None):
        self.screen_image = None
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

        # 最权威基准：直接对齐解析 DOM 时所用的精确屏幕基准尺寸，杜绝离屏/未满屏组件边界拉偏画布比例
        if layout_size and layout_size[0] > 0 and layout_size[1] > 0:
            self.layout_w, self.layout_h = int(layout_size[0]), int(layout_size[1])
            self.hover_node_id = ""
            self.update()
            return

        # 权威基准对齐：真机物理截图的绝对分辨率即为唯一真理！
        # 绝不允许被滚动列表或离屏项的 max_b != orig_h 篡改导致纵向比例严重错位
        max_r = max((c.get("right", 0) for c in components if c.get("right", 0) > 0), default=0)
        max_b = max((c.get("bottom", 0) for c in components if c.get("bottom", 0) > 0), default=0)

        # 仅当底图确属投屏硬件半分辨率缩略帧 (如 542x1206，组件边界明显大于底图 1.25 倍) 时才回退组件物理边界
        if max_r > 0 and max_b > 0 and max_r > self.orig_w * 1.25:
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
        img_size = None
        if self.screen_image and not self.screen_image.isNull():
            img_size = self.screen_image.size()
        elif self.pixmap and not self.pixmap.isNull():
            img_size = self.pixmap.size()

        if not img_size or img_size.isEmpty():
            return QRect()
        avail_w = max(50, self.width() - 24)
        avail_h = max(50, self.height() - 24)
        # 纯几何等比缩放计算 (0 内存分配与 0 CPU 重采样损耗，耗时由 20ms 降至 0.0001ms)
        target_size = img_size.scaled(
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

        # 2. 属于天然的具体内容或交互组件 (全面覆盖鸿蒙 ArkUI、iOS XCUITest 与 Android 原生体系)
        content_types = {
            # 文本展示
            "Text", "Span", "StaticText", "TextClock", "Marquee", "Badge", "Divider",
            # 图标与富媒体 (重点覆盖鸿蒙 SymbolGlyph 等原生图标与画布)
            "SymbolGlyph", "Image", "Icon", "QRCode", "ImageView", "Video", "Web", "XComponent", "Canvas",
            # 按钮与操作交互
            "Button", "Toggle", "Checkbox", "Radio", "Switch", "ImageButton", "Slider", "Rating", "LoadingProgress",
            # 输入表单与编辑器 (全面支持 iOS TextView/TextField 与各端输入框)
            "TextInput", "TextArea", "Search", "SearchField", "RichEditor", "RichEditorContent", "TextField", "TextView", "EditText",
            # 菜单与弹窗选择器
            "Select", "MenuItem", "Menu", "DatePicker", "TimePicker", "TextPicker",
            # iOS 原生完整类型对应组件
            "XCUIElementTypeButton", "XCUIElementTypeImage", "XCUIElementTypeStaticText",
            "XCUIElementTypeTextField", "XCUIElementTypeSecureTextField", "XCUIElementTypeTextView",
            "XCUIElementTypeSearchField", "XCUIElementTypeIcon", "XCUIElementTypeLink", "XCUIElementTypeCell"
        }
        full_t = comp.get("full_type", "")
        if c_type in content_types or full_t in content_types or c_type.endswith("Input") or c_type.endswith("Field"):
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
            # 双重防御：绝不拾取或悬停高亮任何被遮挡或未暴露的底层图层
            if comp.get("is_occluded", False) or not comp.get("is_exposed", True):
                continue
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
        has_content = (self.screen_image and not self.screen_image.isNull()) or (self.pixmap and not self.pixmap.isNull())
        if not has_content or draw_rect.isEmpty():
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

        # 2. 绘制实际真机屏幕原画截图 (直通硬件加速纹理贴图缩放，彻底消除 CPU 软件插值与 QPixmap 转换开销)
        screen_path = QPainterPath()
        screen_path.addRoundedRect(QRectF(draw_rect), 10, 10)
        painter.save()
        painter.setClipPath(screen_path)
        if self.screen_image and not self.screen_image.isNull():
            painter.drawImage(draw_rect, self.screen_image)
        elif self.pixmap and not self.pixmap.isNull():
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


# ==============================================================================
# XPath 高级扩展函数注册中枢 (为 lxml 注册 matches 正则、lower-case、upper-case、ends-with 等)
# ==============================================================================

_LXML_EXTENSIONS_REGISTERED = False

def _init_lxml_xpath_extensions():
    """为 lxml 注册高级扩展函数 (支持 XPath 2.0 的 matches 正则、lower-case、upper-case、ends-with 等)"""
    global _LXML_EXTENSIONS_REGISTERED
    if _LXML_EXTENSIONS_REGISTERED:
        return
    try:
        from lxml import etree
        ns = etree.FunctionNamespace(None)

        def xpath_matches(context, text_arg, pattern_arg, flags_arg=""):
            try:
                if isinstance(text_arg, list):
                    if not text_arg:
                        return False
                    first = text_arg[0]
                    target_str = str(getattr(first, "text", first) or "")
                else:
                    target_str = str(text_arg or "")
                pattern = str(pattern_arg or "")
                py_flags = 0
                f = str(flags_arg).lower()
                if "i" in f:
                    py_flags |= re.IGNORECASE
                if "s" in f:
                    py_flags |= re.DOTALL
                if "m" in f:
                    py_flags |= re.MULTILINE
                return bool(re.search(pattern, target_str, py_flags))
            except Exception:
                return False

        def xpath_lower_case(context, text_arg):
            if isinstance(text_arg, list):
                s = str(getattr(text_arg[0], "text", text_arg[0]) or "") if text_arg else ""
            else:
                s = str(text_arg or "")
            return s.lower()

        def xpath_upper_case(context, text_arg):
            if isinstance(text_arg, list):
                s = str(getattr(text_arg[0], "text", text_arg[0]) or "") if text_arg else ""
            else:
                s = str(text_arg or "")
            return s.upper()

        def xpath_ends_with(context, text_arg, sub_arg):
            if isinstance(text_arg, list):
                s = str(getattr(text_arg[0], "text", text_arg[0]) or "") if text_arg else ""
            else:
                s = str(text_arg or "")
            return s.endswith(str(sub_arg or ""))

        ns["matches"] = xpath_matches
        ns["lower-case"] = xpath_lower_case
        ns["upper-case"] = xpath_upper_case
        ns["ends-with"] = xpath_ends_with
        _LXML_EXTENSIONS_REGISTERED = True
    except Exception:
        pass

_init_lxml_xpath_extensions()


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

    # 3. 校验路径是否以 /、// 或 . 开头（考虑可能存在外层多重嵌套括号包装，如 ((//Text)[1])[1] 或 (//Row//Image)[last()]）
    base_xp = xp
    while base_xp.startswith("(") and ")" in base_xp:
        # 核心：正确匹配开头 '(' 对应的闭合 ')'，而非从右向左使用 rfind (避免被 [last()] 或 [contains()] 中的 ')' 造成误判)
        p_depth = 0
        match_paren_idx = -1
        in_s = False
        in_d = False
        for idx, ch in enumerate(base_xp):
            if ch == "'" and not in_d:
                in_s = not in_s
            elif ch == '"' and not in_s:
                in_d = not in_d
            elif not in_s and not in_d:
                if ch == '(':
                    p_depth += 1
                elif ch == ')':
                    p_depth -= 1
                    if p_depth == 0:
                        match_paren_idx = idx
                        break
        if match_paren_idx == -1:
            return "XPath 表达式圆括号 '(' 与 ')' 未正确配对闭合"
        inner_content = base_xp[1:match_paren_idx].strip()
        outer_pred = base_xp[match_paren_idx+1:].strip()
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

                # 校验方括号谓语内单标识符（数字索引、系统内置函数或子元素节点测试）
                if re.match(r"^[a-zA-Z0-9_\-]+$", p_content):
                    if p_content.isdigit():
                        if int(p_content) <= 0:
                            return f"XPath 索引从 1 开始计数，不能使用 0 或负数 '[{p_content}]'"
                    elif p_content in ("last()", "position()", "true()", "false()"):
                        pass
                    elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_\-]*$", p_content):
                        # W3C XPath 标准规范：谓语中包含单个标签名属于合法的子元素存在性断言 (例如 //Row[TextInput], //Stack[Search])
                        pass
                    else:
                        return (
                            f"谓语 '[{p_content}]' 语法异常：'{p_content}' 格式非法，"
                            f"既非有效数字索引，也非合法子元素标签或属性过滤，请检查是否拼写错误"
                        )

                # 仅对简单单属性等值表达式做 '=' 校验，跳过复合逻辑/不等式/函数调用 (交给 lxml 权威校验)
                is_compound_expr = any(op in p_content for op in (" and ", " or ", ">=", "<=", "!="))
                if "=" in p_content and not is_compound_expr and not any(p_content.startswith(fn) for fn in ["contains", "starts-with", "not", "count"]):
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

                # 仅对纯粹的单子路径嵌套谓语做递归校验，复合布尔表达式 (and/or/比较运算) 交由下方 lxml.etree.XPath 深度校验
                if p_content.startswith((".", "//", "/")) and not is_compound_expr:
                    sub_err = validate_xpath_syntax(p_content)
                    if sub_err:
                        return f"嵌套谓语 '[{p_content}]' 内部语法错误: {sub_err}"

    # 7. 若系统安装了 lxml，尝试用 lxml 最终深度校验 (支持 matches 等高级扩展函数)
    try:
        _init_lxml_xpath_extensions()
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
        elif "Unregistered function" in lxml_err:
            m_fn = re.search(r"([a-zA-Z_\-]+)\s*\(", xp)
            fn_name = m_fn.group(1) if m_fn else "所调用的"
            return (
                f"不支持的 XPath 函数 '{fn_name}()' (Unregistered function)："
                f"请核对函数名拼写，当前支持 matches()、contains()、starts-with()、ends-with()、lower-case()、upper-case() 等"
            )
        return f"XPath 语法错误: {lxml_err}"

    return None


def tokenize_ios_predicate(raw: str) -> Tuple[Optional[str], List[str], str]:
    """
    将 iOS NSPredicate 表达式解析为原子条件列表与纯布尔逻辑表达式。
    支持保留引号内字符串、IN {...} 集合，识别 AND / OR / NOT / && / || / ! 以及括号 ()。
    返回: (错误信息, 原子条件列表, Python布尔表达式字符串)
    若解析成功，错误信息为 None；若语法结构非法，返回具体错误提示。
    """
    raw_s = raw.strip()
    if not raw_s:
        return ("定位表达式不能为空", [], "")

    in_sq = False
    in_dq = False
    in_brace = False
    tokens: List[Tuple[str, str]] = []
    buf: List[str] = []

    def flush_atom():
        nonlocal buf
        s = "".join(buf).strip()
        if s:
            tokens.append(("atom", s))
        buf = []

    i = 0
    n = len(raw_s)
    while i < n:
        ch = raw_s[i]
        if ch == '\\':
            buf.append(ch)
            if i + 1 < n:
                buf.append(raw_s[i + 1])
                i += 2
            else:
                i += 1
            continue

        if ch == "'" and not in_dq:
            in_sq = not in_sq
            buf.append(ch)
            i += 1
            continue
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
            buf.append(ch)
            i += 1
            continue

        if not in_sq and not in_dq:
            if ch == '{':
                in_brace = True
                buf.append(ch)
                i += 1
                continue
            elif ch == '}':
                in_brace = False
                buf.append(ch)
                i += 1
                continue

            if not in_brace:
                if ch in ('(', ')'):
                    flush_atom()
                    tokens.append(("paren", ch))
                    i += 1
                    continue

                sub = raw_s[i:]
                and_m = re.match(r'^(?:AND\b|&&)', sub, re.IGNORECASE)
                or_m = re.match(r'^(?:OR\b|\|\|)', sub, re.IGNORECASE)
                not_m = re.match(r'^(?:NOT\b|!)', sub, re.IGNORECASE)

                if and_m:
                    flush_atom()
                    tokens.append(("op", "and"))
                    i += and_m.end()
                    continue
                elif or_m:
                    flush_atom()
                    tokens.append(("op", "or"))
                    i += or_m.end()
                    continue
                elif not_m and not "".join(buf).strip():
                    flush_atom()
                    tokens.append(("op", "not"))
                    i += not_m.end()
                    continue

        buf.append(ch)
        i += 1

    flush_atom()

    if in_sq:
        return ("单引号 ''' 未闭合，字符串缺少结束单引号", [], "")
    if in_dq:
        return ('双引号 \'"\' 未闭合，字符串缺少结束双引号', [], "")
    if in_brace:
        return ("集合花括号 '{{' 未闭合，缺少结束 '}}'", [], "")

    atom_list: List[str] = []
    py_parts: List[str] = []
    for t_type, t_val in tokens:
        if t_type == "atom":
            atom_idx = len(atom_list)
            atom_list.append(t_val)
            py_parts.append(f"_c_{atom_idx}")
        elif t_type in ("op", "paren"):
            py_parts.append(t_val)

    py_expr = " ".join(py_parts).strip()
    if not py_expr:
        return ("Predicate 表达式不能为空", [], "")

    # 校验布尔逻辑结构合法性 (如连续 AND/OR、操作符悬挂在首尾、括号不匹配等)
    try:
        ast.parse(py_expr, mode='eval')
    except SyntaxError:
        if py_parts and py_parts[-1] in ("and", "or", "not"):
            return (f"Predicate 表达式不完整，不能以逻辑运算符 '{py_parts[-1].upper()}' 结尾", [], "")
        if py_parts and py_parts[0] in ("and", "or"):
            return (f"Predicate 表达式逻辑结构错误: 不能以逻辑运算符 '{py_parts[0].upper()}' 开头", [], "")
        if "()" in py_expr or "( )" in py_expr:
            return ("Predicate 括号内部不能为空", [], "")
        return ("Predicate 表达式布尔逻辑结构非法，请检查 AND / OR 及括号连接", [], "")

    return (None, atom_list, py_expr)


def validate_ios_selector_syntax(strategy: str, val: str) -> Tuple[Optional[str], str]:
    """
    iOS 五大核心定位策略工业级严格静态语法校验器 (专用于元素定位与查找器弹窗)：
    1. id / accessibility id (name / label 标识)
    2. xpath (XPath 路径表达式)
    3. class name (XCUIElementType 组件类型)
    4. ios predicate string (谓词表达式)
    5. ios class chain (类链表达式)

    返回 (错误提示信息, 推荐标准示例)；若语法合法则返回 (None, "")
    """
    if not val or not val.strip():
        return "定位表达式不能为空", ""

    raw = val.strip()

    # 0. 通用检测：Python 字符串前缀 (f"...", r"...", b"...", u"...")、外层多余引号与尾部游离字符
    py_prefix_match = re.match(r'^([fFrRuUbB]{1,2})(["\'])(.*)$', raw, re.DOTALL)
    if py_prefix_match:
        prefix_str = py_prefix_match.group(1)
        quote_ch = py_prefix_match.group(2)
        rest_str = py_prefix_match.group(3)
        clean_example = rest_str[:-1].strip() if rest_str.endswith(quote_ch) else rest_str.strip()
        clean_example = clean_example.replace("{_TAP_TYPES}", "{'XCUIElementTypeButton', 'XCUIElementTypeStaticText'}")
        clean_example = clean_example.replace("{_TEXT_TYPES}", "{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}")
        return (
            f"检测到 Python 格式化字符串前缀 '{prefix_str}{quote_ch}...'；请移除外部的 {prefix_str}{quote_ch}...{quote_ch} 代码包装，直接输入纯定位表达式",
            clean_example
        )

    first_ch = raw[0]
    if first_ch in ('"', "'"):
        match_idx = -1
        i = 1
        n = len(raw)
        while i < n:
            ch = raw[i]
            if ch == '\\':
                i += 2
                continue
            if ch == first_ch:
                match_idx = i
                break
            i += 1
        if match_idx != -1:
            trailing = raw[match_idx + 1:].strip()
            inner_content = raw[1:match_idx].strip()
            if trailing:
                return (
                    f"引号在第 {match_idx + 1} 位提前闭合，引号后存在非法游离字符 '{trailing}'；请移除外部包裹的引号与尾部残留字符",
                    inner_content
                )
            else:
                return (
                    f"表达式无需在最外层包裹多余的代码引号 ({first_ch}...{first_ch})；请直接输入表达式内容",
                    inner_content
                )

    # 检测未展开的 Python f-string 变量占位符 (如 {_TAP_TYPES}, {_TEXT_TYPES}, {var})
    py_var_match = re.search(r'\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}', raw)
    if py_var_match:
        var_name = py_var_match.group(1)
        clean_example = raw.replace("{_TAP_TYPES}", "{'XCUIElementTypeButton', 'XCUIElementTypeStaticText'}")
        clean_example = clean_example.replace("{_TEXT_TYPES}", "{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}")
        if clean_example == raw:
            clean_example = re.sub(r'\{\s*' + re.escape(var_name) + r'\s*\}', "{'XCUIElementTypeButton'}", raw)
        return (
            f"检测到未展开的 Python 变量占位符 '{{{var_name}}}'；查找器仅接收纯定位表达式（集合内字符串必须加引号）",
            clean_example
        )

    # 1. 策略: id / accessibility id (name / label 标识)
    if strategy == "id":
        if raw.startswith(("//", "/", ".")) or ("[" in raw and "]" in raw):
            return (
                "检测到 XPath 路径语法特征；当前策略为 [id]，若要使用路径定位请切换策略为 [xpath]",
                "login_button 或 ic delete 48"
            )
        if raw.startswith("**/"):
            return (
                "检测到 Class Chain 语法特征；当前策略为 [id]，请切换策略为 [ios class chain]",
                "**/XCUIElementTypeButton[`name == '确定'`]"
            )
        if raw.startswith("@"):
            return (
                "ID 选择器无需添加 '@' 前缀，请直接输入组件名称或标识",
                raw.lstrip("@")
            )
        if re.search(r'\b(OR|AND|NOT|IN)\b|[=!<>]=?', raw, re.IGNORECASE):
            return (
                "ID / Accessibility ID 仅支持单一标识精确匹配，不支持 'OR'/'AND'/'==' 等逻辑运算符；若需多条件二选一，请切换策略为 [ios predicate string] 或 [xpath]",
                "name IN {'密码验证登录', '短信验证登录'}"
            )
        return None, ""

    # 2. 策略: xpath (XPath 路径表达式)
    elif strategy == "xpath":
        if not (raw.startswith("/") or raw.startswith("./") or raw.startswith("(")):
            return (
                "XPath 表达式必须以 '//' 或 '/' 开头",
                "//XCUIElementTypeButton[@name='确定'] 或 //Button"
            )
        if re.search(r'\[\s*(name|label|value|type|enabled|visible)\s*=', raw):
            return (
                "XPath 属性过滤必须以 '@' 开头，请勿漏写 '@' 符号",
                "//Button[@name='确定']"
            )
        xp_err = validate_xpath_syntax(raw)
        if xp_err:
            return f"XPath 语法错误: {xp_err}", "//XCUIElementTypeButton[@name='登录']"
        return None, ""

    # 3. 策略: class name (XCUIElementType 组件类型)
    elif strategy in ("class name", "type"):
        if any(ch in raw for ch in ("/", "\\", "[", "]", "@", "=", "(", ")", "'", '"')):
            return (
                "Class Name 仅为单一组件类型名称，无需包含斜杠、方括号或属性条件；若要按层级查找请使用 [xpath] 或 [ios class chain]",
                "XCUIElementTypeButton 或 Button"
            )
        if " " in raw:
            return (
                "组件类名不能包含空格，请输入合法的类名标识符",
                "XCUIElementTypeButton"
            )
        if raw.startswith("android.") or "widget." in raw:
            return (
                "当前为 iOS 平台，不能使用 Android 控件类名 (android.widget.*)；请输入 iOS 的 XCUIElementType* 类名",
                "XCUIElementTypeButton 或 XCUIElementTypeStaticText"
            )
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', raw):
            return (
                "组件类名必须由英文字母、数字或下划线组成",
                "XCUIElementTypeButton"
            )
        return None, ""

    # 4. 策略: ios predicate string (谓词表达式)
    elif strategy == "predicate":
        in_sq = False
        in_dq = False
        paren_stack = []
        brace_stack = []
        bracket_stack = []
        i = 0
        n = len(raw)
        while i < n:
            ch = raw[i]
            if ch == '\\':
                i += 2
                continue
            if ch == "'" and not in_dq:
                in_sq = not in_sq
            elif ch == '"' and not in_sq:
                in_dq = not in_dq
            elif not in_sq and not in_dq:
                if ch == '(':
                    paren_stack.append(i)
                elif ch == ')':
                    if not paren_stack:
                        return f"第 {i + 1} 个字符处圆括号 ')' 提前闭合，缺少对应的 '('", "label == '设置'"
                    paren_stack.pop()
                elif ch == '{':
                    brace_stack.append(i)
                elif ch == '}':
                    if not brace_stack:
                        return f"第 {i + 1} 个字符处花括号 '}}' 提前闭合，缺少对应的 '{{'", "name IN {'A', 'B'}"
                    brace_stack.pop()
                elif ch == '[':
                    bracket_stack.append(i)
                elif ch == ']':
                    if not bracket_stack:
                        return f"第 {i + 1} 个字符处方括号 ']' 提前闭合，缺少对应的 '['", "name == '确定'"
                    bracket_stack.pop()
            i += 1

        if in_sq:
            return "单引号 ''' 未闭合，字符串字面量缺少结束单引号", "name == '登录'"
        if in_dq:
            return '双引号 \'"\' 未闭合，字符串字面量缺少结束双引号', 'name == "登录"'
        if paren_stack:
            return f"第 {paren_stack[-1] + 1} 个字符处圆括号 '(' 未闭合，缺少对应的 ')'", "(name == 'A' OR name == 'B')"
        if brace_stack:
            return f"第 {brace_stack[-1] + 1} 个字符处集合花括号 '{{' 未闭合，缺少对应的 '}}'", "name IN {'A', 'B'}"
        if bracket_stack:
            return f"第 {bracket_stack[-1] + 1} 个字符处方括号 '[' 未闭合，缺少对应的 ']'", "name == '确定'"

        if raw.startswith(("//", "/", "./", "**/")):
            return (
                "检测到路径语法特征；Predicate 为属性比较表达式，无需斜杠；例如: name == '确定' 或 label CONTAINS '登录'",
                "name == '确定' OR label == '确定'"
            )
        if re.search(r'@(name|label|value|type)\b', raw):
            return (
                "Predicate 表达式属性名无需添加 '@' 前缀；请直接书写属性名 (例如: name == '确定' 而非 @name)",
                "name == '确定'"
            )
        if re.search(r'\bIN\s*\(', raw, re.IGNORECASE):
            return (
                "NSPredicate 的集合语法必须使用花括号 {}，不能使用圆括号 ()",
                "name IN {'密码验证登录', '短信验证登录'}"
            )
        for set_m in re.finditer(r'\bIN\s*\{([^}]*)\}', raw, re.IGNORECASE):
            set_body = set_m.group(1).strip()
            if not set_body:
                return "IN 集合花括号 '{}' 内部不能为空", "name IN {'密码验证登录', '短信验证登录'}"
            for raw_item in set_body.split(","):
                it = raw_item.strip()
                if not it:
                    continue
                if not ((it.startswith("'") and it.endswith("'")) or (it.startswith('"') and it.endswith('"')) or it.isdigit()):
                    return (
                        f"IN 集合内部的字符串元素 '{it}' 缺少引号包裹；集合元素必须使用单引号或双引号包裹",
                        "type IN {'XCUIElementTypeButton', 'XCUIElementTypeStaticText'}"
                    )
        if re.search(r'\b(AND|OR|NOT|IN|LIKE|CONTAINS|BEGINSWITH|ENDSWITH|MATCHES)\s*$|[=!<>]=?\s*$', raw, re.IGNORECASE):
            return (
                "Predicate 表达式不完整，不能以运算符 (如 '==', 'AND', 'OR', 'IN') 结尾",
                "label == '确定' AND visible == 1"
            )
        has_cmp = re.search(r'==|!=|<=|>=|<|>|<>|\b(CONTAINS|BEGINSWITH|ENDSWITH|LIKE|MATCHES|IN|BETWEEN)\b', raw, re.IGNORECASE)
        if not has_cmp:
            return (
                "Predicate 表达式必须包含比较运算符 (如 ==, CONTAINS, IN 等)；若仅按 ID 匹配请切换为 [id] 策略",
                "label == '设置' 或 name IN {'密码验证登录', '短信验证登录'}"
            )

        # 逐个校验由 tokenize_ios_predicate 严格分词得出的原子条件子句，拦截尾部多余字符、未加引号字面量或未知属性名
        err_msg, atom_list, py_expr = tokenize_ios_predicate(raw)
        if err_msg:
            return (
                err_msg,
                "type == 'Link' AND (label == '注册' OR name == '注册')"
            )

        valid_pred_attrs = {
            "name", "label", "value", "type", "enabled", "visible", "accessible",
            "selected", "focused", "hittable", "wdtype", "wdname", "wdlabel",
            "wdvalue", "wdrect", "wdvisible", "wdenabled", "wdaccessible", "wduid",
            "rect", "frame", "placeholdervalue", "title", "identifier", "traits", "index",
        }

        for atom in atom_list:
            c_str_no_not = re.sub(r'^(?:NOT\s+|!\s*)', '', atom, flags=re.IGNORECASE).strip()
            # 1) 检测 IN { ... } 子句及花括号闭合后的非法游离字符
            in_clause_m = re.match(
                r'^([A-Za-z_][A-Za-z0-9_\.]*)\s+IN(?:\s*\[[cd]+\])?\s*\{([^}]*)\}(.*)$',
                c_str_no_not,
                re.IGNORECASE | re.DOTALL,
            )
            if in_clause_m:
                attr_name = in_clause_m.group(1)
                set_inner = in_clause_m.group(2)
                trailing_after_brace = in_clause_m.group(3).strip()
                if attr_name.lower().split(".")[0] not in valid_pred_attrs:
                    return (
                        f"未知的 iOS Predicate 属性名 '{attr_name}'；常用属性包括: name, label, value, type, enabled, visible",
                        f"name IN {{{set_inner}}}"
                    )
                if trailing_after_brace:
                    return (
                        f"集合表达式 '}}' 闭合后存在非法多余内容 '{trailing_after_brace}'；条件之间必须使用 AND / OR 连接，请移除尾部多余字符",
                        f"{attr_name} IN {{{set_inner}}}"
                    )
                continue

            # 2) 检测比较运算子句 (==, !=, =, <>, <=, >=, <, >, CONTAINS, BEGINSWITH, ENDSWITH, LIKE, MATCHES 等)
            cmp_clause_m = re.match(
                r'^([A-Za-z_][A-Za-z0-9_\.]*)\s*(==|!=|=|<>|<=|>=|<|>|\b(?:CONTAINS|BEGINSWITH|ENDSWITH|LIKE|MATCHES)\b(?:\s*\[[cd]+\])?)\s*(.+)$',
                c_str_no_not,
                re.IGNORECASE | re.DOTALL,
            )
            if cmp_clause_m:
                attr_name = cmp_clause_m.group(1)
                op_str = cmp_clause_m.group(2).strip()
                rhs_str = cmp_clause_m.group(3).strip()
                if attr_name.lower().split(".")[0] not in valid_pred_attrs:
                    return (
                        f"未知的 iOS Predicate 属性名 '{attr_name}'；常用属性包括: name, label, value, type, enabled, visible",
                        f"name {op_str} {rhs_str}"
                    )
                if rhs_str[0] in ("'", '"'):
                    q_ch = rhs_str[0]
                    q_end = -1
                    k = 1
                    while k < len(rhs_str):
                        if rhs_str[k] == '\\':
                            k += 2
                            continue
                        if rhs_str[k] == q_ch:
                            q_end = k
                            break
                        k += 1
                    if q_end != -1:
                        rhs_trailing = rhs_str[q_end + 1:].strip()
                        if rhs_trailing:
                            clean_rhs = rhs_str[:q_end + 1]
                            return (
                                f"字符串字面量 {clean_rhs} 闭合引号后存在非法多余内容 '{rhs_trailing}'；请移除多余字符或使用 AND / OR 连接新条件",
                                f"{attr_name} {op_str} {clean_rhs}"
                            )
                else:
                    if not re.match(r'^(?:true|false|yes|no|nil|null|\d+(?:\.\d+)?)$', rhs_str, re.IGNORECASE):
                        return (
                            f"比较运算符 '{op_str}' 右侧的字符串值 '{rhs_str}' 缺少引号包裹，或包含多余字符",
                            f"{attr_name} {op_str} '{rhs_str}'"
                        )
                continue

            # 3) 检测布尔常量或独立布尔属性
            if re.match(r'^(?:TRUEPREDICATE|FALSEPREDICATE|1|0|true|false|enabled|visible|accessible|selected|hittable)$', c_str_no_not, re.IGNORECASE):
                continue

            return (
                f"Predicate 子表达式 '{atom}' 语法格式非法；每个条件子句必须为 '属性 运算符 值' 格式 (如 name == '确定' 或 name IN {{'A', 'B'}})",
                "type == 'Link' AND (label == '注册' OR name == '注册')"
            )

        return None, ""

    # 5. 策略: ios class chain (类链表达式)
    elif strategy == "class chain":
        if not (raw.startswith("**/") or raw.startswith("/*") or raw.startswith("/")):
            return (
                "Class Chain 表达式必须以 '**/' 或 '/' 开头",
                "**/XCUIElementTypeButton[`name == '确定'`]"
            )
        if raw.count("[") != raw.count("]"):
            return "Class Chain 表达式方括号 '[' 与 ']' 未成对闭合", "**/XCUIElementTypeButton[`name == '确定'`]"
        if raw.count("`") % 2 != 0:
            return "Class Chain 嵌套谓词反引号 '`' 未成对闭合", "**/XCUIElementTypeButton[`label == '确定'`]"
        if raw.count('"') % 2 != 0 or raw.count("'") % 2 != 0:
            return "Class Chain 内部字符串引号未成对闭合", "**/XCUIElementTypeButton[`name == '确定'`]"
        if re.search(r'\[\s*@(name|label|text)', raw):
            return (
                "Class Chain 中的属性过滤需使用反引号包裹 Predicate 语法，如 [`name == '确定'`]，无需使用 XPath 的 '@' 属性语法",
                "**/XCUIElementTypeButton[`name == '确定'`]"
            )
        if "//" in raw and not raw.startswith("**/"):
            return (
                "Class Chain 使用 '**/' 表示任意深度后代遍历，不能使用 XPath 的 '//'",
                "**/XCUIElementTypeButton[`name == '确定'`]"
            )
        # 校验 Class Chain 各层级节点段以及方括号闭合后的非法游离字符
        cc_segs = []
        cc_buf = []
        cc_bt = False
        cc_sq = False
        cc_dq = False
        for ch in raw:
            if ch == "`" and not cc_sq and not cc_dq:
                cc_bt = not cc_bt
                cc_buf.append(ch)
            elif ch == "'" and not cc_dq:
                cc_sq = not cc_sq
                cc_buf.append(ch)
            elif ch == '"' and not cc_sq:
                cc_dq = not cc_dq
                cc_buf.append(ch)
            elif ch == "/" and not cc_bt and not cc_sq and not cc_dq:
                cc_segs.append("".join(cc_buf))
                cc_buf = []
            else:
                cc_buf.append(ch)
        cc_segs.append("".join(cc_buf))
        for seg in cc_segs:
            seg_s = seg.strip()
            if not seg_s or seg_s in ("**", "*"):
                continue
            seg_m = re.match(r'^(\*|[A-Za-z_][A-Za-z0-9_]*)(.*)$', seg_s, re.DOTALL)
            if not seg_m:
                return f"Class Chain 节点段 '{seg_s}' 类名格式非法", "**/XCUIElementTypeButton[`name == '确定'`]"
            seg_rest = seg_m.group(2).strip()
            if seg_rest:
                if not seg_rest.startswith("[") or not seg_rest.endswith("]"):
                    return (
                        f"Class Chain 节点 '{seg_m.group(1)}' 后存在未包裹在方括号 '[]' 内的非法多余字符: '{seg_rest}'",
                        f"**/{seg_m.group(1)}[`name == '确定'`]"
                    )
                for bt_m in re.finditer(r'\[\s*[`$]([^`$]*)[`$]\s*\]', seg_rest):
                    inner_p_err, inner_p_ex = validate_ios_selector_syntax("predicate", bt_m.group(1))
                    if inner_p_err:
                        inner_fallback = inner_p_ex if inner_p_ex else "name == '确定'"
                        return f"Class Chain 嵌套 Predicate 语法错误: {inner_p_err}", f"**/{seg_m.group(1)}[`{inner_fallback}`]"
        return None, ""

    return None, ""


# ==============================================================================
# 鸿蒙 HypiumBy (BY.* 原生链式表达式) 静态解析与 DOM 树求值引擎
# ==============================================================================

_HYPIUM_MATCH_PATTERNS: Dict[str, int] = {
    "EQUALS": 0,
    "CONTAINS": 1,
    "STARTS_WITH": 2,
    "ENDS_WITH": 3,
    "REGEXP": 4,
    "REGEXP_ICASE": 5,
}

_HYPIUM_STR_METHODS = frozenset({
    "text", "type", "id", "key", "hint", "description", "inWindow",
    "originalText", "bundleName", "accessibilityId",
})
_HYPIUM_XPATH_METHODS = frozenset({"xpath"})
_HYPIUM_BOOL_METHODS = frozenset({
    "clickable", "longClickable", "scrollable", "enabled",
    "focused", "selected", "checked", "checkable",
})
_HYPIUM_REL_METHODS = frozenset({"within", "isBefore", "isAfter"})

_HARMONY_TUPLE_STRATEGY_MAP: Dict[str, str] = {
    "hypiumby": "hypium",
    "byexpression": "hypium",
    "hypium": "hypium",
    "xpath": "xpath",
    "text": "text",
    "type": "type",
    "class name": "type",
    "id": "id",
    "key": "id",
    "description": "description",
    "accessibility id": "description",
}


def _eval_hosby_ast_arg(node: ast.AST) -> Tuple[Optional[str], Any]:
    """安全静态求值 HosBy.xxx(...) 调用中的字面量与常量参数（零 eval 风险）。"""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (str, int, float, bool)) or node.value is None:
            return None, node.value
        return f"不支持的常量参数类型: {type(node.value).__name__}", None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        if isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, (int, float)) and not isinstance(node.operand.value, bool):
            return None, -node.operand.value
    if isinstance(node, ast.Name):
        low = node.id.lower()
        if low == "true":
            return None, True
        if low == "false":
            return None, False
        if low in ("none", "null"):
            return None, None
        return f"不支持的变量引用 '{node.id}'，请替换为具体字面量字符串或 HosBy.MATCH_* 常量", None
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        if node.value.id in ("HosBy", "MatchPattern"):
            attr_name = node.attr.upper()
            if attr_name.startswith("MATCH_"):
                attr_name = attr_name[6:]
            if attr_name in _HYPIUM_MATCH_PATTERNS:
                return None, _HYPIUM_MATCH_PATTERNS[attr_name]
        return f"不支持的属性引用 '{node.value.id}.{node.attr}'", None
    return "HosBy 参数仅支持字符串、数字、布尔值、None 及 HosBy.MATCH_* 常量", None


def _convert_hosby_call_to_by_expr(raw: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    安全静态解析从源码直接复制的 HosBy.<method>(...) 调用（兼容变量赋值前缀、return 前缀与多行缩进），
    返回 (是否识别为 HosBy 调用, 转换后的标准 BY.* 表达式, 错误提示信息)。
    """
    cleaned = (raw or "").strip()
    if not cleaned:
        return False, None, None

    # 剥离从 *_hos.py 整行复制时可能携带的 "VAR_NAME = " 或 "return " 前缀
    cleaned = re.sub(r"^(?:return\s+|[A-Za-z_][A-Za-z0-9_]*\s*=\s*)", "", cleaned).strip()
    if not re.match(r"^HosBy\.", cleaned):
        return False, None, None

    # 去除行尾孤立逗号（如从参数/列表里顺手复制出来的尾逗号）
    if cleaned.endswith(","):
        cleaned = cleaned[:-1].strip()

    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError as e:
        return True, None, f"HosBy 调用语法错误（请检查引号与括号是否闭合）: {e.msg}"

    call_node = tree.body
    if (
        not isinstance(call_node, ast.Call)
        or not isinstance(call_node.func, ast.Attribute)
        or not isinstance(call_node.func.value, ast.Name)
        or call_node.func.value.id != "HosBy"
    ):
        return True, None, "请输入完整的 HosBy.<方法>(...) 调用，例如 HosBy.text_contains(\"我已阅读且同意\", \"Text\")"

    method_name = call_node.func.attr
    if method_name.startswith("_"):
        return True, None, f"不允许调用私有方法 HosBy.{method_name}"

    try:
        from locators.common.hos_by import HosBy as _ProjectHosBy
    except Exception as imp_err:
        return True, None, f"无法加载 locators.common.hos_by.HosBy: {imp_err}"

    target_fn = getattr(_ProjectHosBy, method_name, None)
    if not callable(target_fn):
        return True, None, f"HosBy 中不存在方法 '{method_name}'，请核对 locators/common/hos_by.py 中的方法名"

    pos_args: List[Any] = []
    for arg in call_node.args:
        a_err, a_val = _eval_hosby_ast_arg(arg)
        if a_err:
            return True, None, f"HosBy.{method_name}() 参数错误: {a_err}"
        pos_args.append(a_val)

    kw_args: Dict[str, Any] = {}
    for kw in call_node.keywords:
        if not kw.arg:
            return True, None, f"HosBy.{method_name}() 不支持 **kwargs 展开"
        a_err, a_val = _eval_hosby_ast_arg(kw.value)
        if a_err:
            return True, None, f"HosBy.{method_name}({kw.arg}=...) 参数错误: {a_err}"
        kw_args[kw.arg] = a_val

    try:
        res = target_fn(*pos_args, **kw_args)
    except Exception as call_err:
        return True, None, f"HosBy.{method_name}() 参数校验失败: {call_err}"

    if not (isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], str) and isinstance(res[1], str)):
        return True, None, f"HosBy.{method_name}() 返回值不是标准 (strategy, value) 二元组"

    strat_raw, val_raw = res[0].strip(), res[1].strip()
    strat_low = strat_raw.lower()
    if strat_low in ("hypiumby", "byexpression", "hypium"):
        return True, val_raw, None

    # 将 HosBy.text / type_only / id_only / key 等单条件直查统一等价转为精确 BY.*，严格保持真机精确语义
    safe_v = _ProjectHosBy._escape(val_raw)
    if strat_low == "text":
        return True, f'BY.text("{safe_v}")', None
    if strat_low == "type":
        return True, f'BY.type("{safe_v}")', None
    if strat_low == "key":
        return True, f'BY.key("{safe_v}")', None
    if strat_low == "id":
        return True, f'BY.id("{safe_v}")', None
    return True, val_raw, None


def resolve_harmony_locator_input(raw: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    统一识别鸿蒙端粘贴的多种高级定位格式（不修改输入框原文，仅返回规范化后的策略与值）：
    1. 源码直贴：HosBy.between_texts(...) / AGREE_AND_LOGIN_BTN = HosBy.within_type(...)
    2. 日志/代码二元组：('HypiumBy', 'BY....') / ('text', '手机号登录') / ('type', 'TextInput') /
       ('key', '...') / ('id', '...') / ('xpath', '//...') / (AppiumBy.XPATH, '//...') 及整行日志
    3. 纯 HypiumBy 链式表达式：BY.isAfter(...).type("Image")
    返回 (目标策略键或 None, 解包后的表达式值或 None, 语法错误信息或 None)。
    """
    text = (raw or "").strip()
    if not text:
        return None, None, None

    # 1. 优先识别源码直贴的 HosBy.<method>(...)
    is_hosby, by_expr, hosby_err = _convert_hosby_call_to_by_expr(text)
    if is_hosby:
        if hosby_err:
            return "hypium", None, hosby_err
        return "hypium", by_expr, None

    # 2. 尝试解包任意鸿蒙定位二元组（支持整行日志、AppiumBy.XXX 与普通字符串策略名）
    def _try_parse_locator_tuple(candidate: str) -> Optional[Tuple[str, str]]:
        # 先兼容 (AppiumBy.XPATH, "//...") / (AppiumBy.ID, "...") 等代码二元组
        cand_norm = re.sub(
            r"^\(\s*(?:AppiumBy|By)\.([A-Za-z_]+)\s*,",
            lambda m: f"('{m.group(1).lower().replace('_', ' ')}',",
            candidate.strip(),
        )
        try:
            parsed = ast.literal_eval(cand_norm)
        except Exception:
            return None
        if isinstance(parsed, (tuple, list)) and len(parsed) == 2 and isinstance(parsed[0], str) and isinstance(parsed[1], str):
            mapped = _HARMONY_TUPLE_STRATEGY_MAP.get(parsed[0].strip().lower())
            if mapped:
                return mapped, parsed[1].strip()
        if isinstance(parsed, str) and re.match(r"^(?:BY|By|by)\.", parsed.strip()):
            return "hypium", parsed.strip()
        return None

    direct_tuple = _try_parse_locator_tuple(text)
    if direct_tuple is not None:
        return direct_tuple[0], direct_tuple[1], None

    # 剥离整行复制的 "VAR_NAME = (AppiumBy.XPATH, '...')" 赋值前缀后再尝试一次
    no_assign = re.sub(r"^(?:return\s+|[A-Za-z_][A-Za-z0-9_]*\s*=\s*)", "", text).strip().rstrip(",").strip()
    if no_assign != text:
        assign_tuple = _try_parse_locator_tuple(no_assign)
        if assign_tuple is not None:
            return assign_tuple[0], assign_tuple[1], None

    # 扫描运行日志文本中嵌套的平衡圆括号定位元组，如 "正在查找元素: ('text', '手机号登录') (模式: visibility)"
    strat_keys_pat = "|".join(re.escape(k) for k in _HARMONY_TUPLE_STRATEGY_MAP)
    m_tuple = re.search(
        rf"\(\s*(?:['\"](?:{strat_keys_pat})['\"]|(?:AppiumBy|By)\.[A-Za-z_]+)\s*,",
        text,
        re.IGNORECASE,
    )
    if m_tuple:
        start_idx = m_tuple.start()
        depth = 0
        in_sq = False
        in_dq = False
        escaped = False
        for i in range(start_idx, len(text)):
            ch = text[i]
            if escaped:
                escaped = False
                continue
            if ch == "\\" and (in_sq or in_dq):
                escaped = True
                continue
            if ch == "'" and not in_dq:
                in_sq = not in_sq
            elif ch == '"' and not in_sq:
                in_dq = not in_dq
            elif not in_sq and not in_dq:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        extracted = _try_parse_locator_tuple(text[start_idx:i + 1])
                        if extracted is not None:
                            return extracted[0], extracted[1], None
                        break

    # 3. 识别纯 BY.xxx(...) 表达式
    if re.match(r"^(?:BY|By|by)\.", text):
        return "hypium", text, None

    return None, None, None


def extract_hypium_expression(raw: str) -> str:
    """
    智能规范化用户粘贴的 HypiumBy 表达式：
    1. 支持直接粘贴源码调用：HosBy.between_texts(...) / HosBy.text_contains(...)
    2. 支持直接粘贴纯表达式：BY.isAfter(BY.text("...", 4)).isBefore(BY.text("我已阅读且同意", 1)).type("Image")
    3. 支持直接粘贴日志元组或整行日志：正在查找元素: ('HypiumBy', 'BY....') (模式: visibility)
    """
    resolved_strat, resolved_val, err = resolve_harmony_locator_input(raw)
    if err is None and resolved_strat == "hypium" and resolved_val:
        return resolved_val
    return (raw or "").strip()


def _eval_hypium_match_pattern(arg_node: ast.AST) -> Tuple[Optional[str], int]:
    """解析 HypiumBy 字符串方法的第 2 个匹配模式参数（支持 0~5 整型或 MatchPattern.XXX）。"""
    if isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, int) and not isinstance(arg_node.value, bool):
        mode = int(arg_node.value)
        if 0 <= mode <= 5:
            return None, mode
        return f"匹配模式数值 {mode} 超出有效范围 (0=精确, 1=包含, 2=前缀, 3=后缀, 4=正则, 5=正则忽略大小写)", 0
    if isinstance(arg_node, ast.Attribute) and isinstance(arg_node.value, ast.Name):
        if arg_node.value.id in ("MatchPattern", "HosBy"):
            attr_name = arg_node.attr.upper()
            if attr_name.startswith("MATCH_"):
                attr_name = attr_name[6:]
            if attr_name in _HYPIUM_MATCH_PATTERNS:
                return None, _HYPIUM_MATCH_PATTERNS[attr_name]
    return "匹配模式参数非法，请传入 0~5 整数或 MatchPattern.CONTAINS / MatchPattern.REGEXP", 0


def _eval_hypium_bool_arg(arg_node: ast.AST) -> Tuple[Optional[str], bool]:
    """解析 HypiumBy 布尔参数（兼容 JS true/false 与 Python True/False）。"""
    if isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, bool):
        return None, bool(arg_node.value)
    if isinstance(arg_node, ast.Name):
        low = arg_node.id.lower()
        if low == "true":
            return None, True
        if low == "false":
            return None, False
    return "布尔状态方法参数必须为 true / false (或 True / False)", True


def _parse_hypium_ast_chain(node: ast.AST) -> Tuple[Optional[str], List[Tuple[str, Tuple[Any, ...]]]]:
    """递归解析单条 BY.xxx(...).yyy(...) 链式调用 AST 为有序条件步骤列表。"""
    if isinstance(node, ast.Name):
        if node.id in ("BY", "By", "by"):
            return None, []
        return f"HypiumBy 表达式必须以 'BY.' 开头，不能以 '{node.id}' 开头", []

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return "HypiumBy 表达式必须为标准链式方法调用，如 BY.type(\"Text\").text(\"确定\")", []

    if node.keywords:
        return f"方法 .{node.func.attr}() 不支持关键字参数，请使用位置参数", []

    err, prev_steps = _parse_hypium_ast_chain(node.func.value)
    if err:
        return err, []

    method = node.func.attr
    args = node.args

    if method in _HYPIUM_STR_METHODS:
        if len(args) not in (1, 2):
            return f"方法 .{method}() 需要 1~2 个参数，当前传入了 {len(args)} 个", []
        if not (isinstance(args[0], ast.Constant) and isinstance(args[0].value, str)):
            return f"方法 .{method}() 第 1 个参数必须为字符串字面量", []
        val_str = str(args[0].value)
        mode = 0
        if len(args) == 2:
            m_err, mode = _eval_hypium_match_pattern(args[1])
            if m_err:
                return f"方法 .{method}() {m_err}", []
        if mode in (4, 5):
            try:
                re.compile(val_str, re.IGNORECASE if mode == 5 else 0)
            except re.error as re_err:
                return f"方法 .{method}() 中的正则表达式语法无效: {re_err}", []
        prev_steps.append((method, (val_str, mode)))
        return None, prev_steps

    if method in _HYPIUM_XPATH_METHODS:
        if len(args) != 1:
            return f"方法 .{method}() 必须且只能传入 1 个 XPath 字符串参数", []
        if not (isinstance(args[0], ast.Constant) and isinstance(args[0].value, str)):
            return f"方法 .{method}() 参数必须为 XPath 字符串字面量", []
        xp_str = str(args[0].value).strip()
        xp_err = validate_xpath_syntax(xp_str)
        if xp_err:
            return f".xpath(...) 内部 XPath 语法错误: {xp_err}", []
        prev_steps.append((method, (xp_str,)))
        return None, prev_steps

    if method in _HYPIUM_BOOL_METHODS:
        if len(args) == 0:
            prev_steps.append((method, (True,)))
            return None, prev_steps
        if len(args) == 1:
            b_err, flag = _eval_hypium_bool_arg(args[0])
            if b_err:
                return f"方法 .{method}() {b_err}", []
            prev_steps.append((method, (flag,)))
            return None, prev_steps
        return f"方法 .{method}() 最多接受 1 个布尔参数，当前传入了 {len(args)} 个", []

    if method in _HYPIUM_REL_METHODS:
        if len(args) != 1:
            return f"关系定位方法 .{method}() 必须且只能传入 1 个子 BY 表达式", []
        sub_err, sub_steps = _parse_hypium_ast_chain(args[0])
        if sub_err:
            return f".{method}(...) 内部子表达式错误: {sub_err}", []
        if not sub_steps:
            return f".{method}(...) 内部不能仅传入空的 BY，请补充至少一个过滤条件", []
        prev_steps.append((method, (sub_steps,)))
        return None, prev_steps

    supported_list = "text / originalText / type / id / key / hint / description / accessibilityId / inWindow / bundleName / xpath / checked / clickable / within / isBefore / isAfter"
    return f"暂不支持的 HypiumBy 方法 '.{method}()'；当前支持: {supported_list}", []


def parse_hypium_by_expression(raw: str) -> Tuple[Optional[str], List[Tuple[str, Tuple[Any, ...]]]]:
    """
    校验并解析鸿蒙 HypiumBy (BY.*) 表达式（兼容直接粘贴 HosBy.xxx(...) 源码调用与日志元组）。
    返回 (错误提示信息或 None, 解析后的链式条件列表)。
    """
    is_hosby, by_expr, hosby_err = _convert_hosby_call_to_by_expr(raw)
    if is_hosby:
        if hosby_err:
            return hosby_err, []
        expr = by_expr or ""
    else:
        expr = extract_hypium_expression(raw)

    if not expr:
        return "HypiumBy 表达式不能为空", []

    if not re.match(r"^(?:BY|By|by)\.", expr):
        return (
            "HypiumBy 表达式必须以 'BY.' 开头（也可直接粘贴 HosBy.xxx(...) 源码或日志中的 ('HypiumBy', 'BY....') 元组）",
            [],
        )

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        return f"HypiumBy 表达式语法错误（请检查引号与括号是否闭合）: {e.msg}", []

    err, steps = _parse_hypium_ast_chain(tree.body)
    if err:
        return err, []
    if not steps:
        return "HypiumBy 表达式缺少条件方法，请至少追加一个如 .text(...) 或 .type(...)", []
    return None, steps


def _match_hypium_str(actual: str, pattern: str, mode: int) -> bool:
    """按鸿蒙 uitest MatchPattern (0~5) 规则执行字符串匹配。"""
    if mode == 0:
        return actual == pattern
    if mode == 1:
        return pattern in actual
    if mode == 2:
        return actual.startswith(pattern)
    if mode == 3:
        return actual.endswith(pattern)
    if mode == 4:
        return bool(re.search(pattern, actual))
    if mode == 5:
        return bool(re.search(pattern, actual, re.IGNORECASE))
    return actual == pattern


def _eval_hypium_attr_step(
    method: str,
    args: Tuple[Any, ...],
    comp: Dict[str, Any],
    elem: Optional[ET.Element],
    parent_map: Dict[ET.Element, ET.Element],
    comp_by_elem: Dict[ET.Element, Dict[str, Any]],
) -> bool:
    """求值单条非关系型 HypiumBy 属性/状态过滤步骤。"""
    raw_attrs = comp.get("raw_attributes") or comp.get("raw") or {}

    if method == "text":
        pat, mode = args
        val = str(comp.get("text") or raw_attrs.get("text") or raw_attrs.get("originalText") or "")
        return _match_hypium_str(val, pat, mode)

    if method == "originalText":
        pat, mode = args
        val = str(raw_attrs.get("originalText") or comp.get("text") or raw_attrs.get("text") or "")
        return _match_hypium_str(val, pat, mode)

    if method == "type":
        pat, mode = args
        c_type = str(comp.get("type") or raw_attrs.get("type") or "")
        c_full = str(comp.get("full_type") or "")
        return _match_hypium_str(c_type, pat, mode) or (bool(c_full) and _match_hypium_str(c_full, pat, mode))

    if method == "id":
        pat, mode = args
        candidates = [
            str(comp.get("id") or ""),
            str(raw_attrs.get("id") or ""),
            str(raw_attrs.get("key") or ""),
        ]
        return any(_match_hypium_str(c, pat, mode) for c in candidates if c or pat == "")

    if method == "key":
        pat, mode = args
        candidates = [
            str(raw_attrs.get("key") or ""),
            str(comp.get("id") or ""),
            str(raw_attrs.get("id") or ""),
        ]
        return any(_match_hypium_str(c, pat, mode) for c in candidates if c or pat == "")

    if method == "accessibilityId":
        pat, mode = args
        val = str(raw_attrs.get("accessibilityId") or raw_attrs.get("accessibility-id") or comp.get("id") or "")
        return _match_hypium_str(val, pat, mode)

    if method == "hint":
        pat, mode = args
        val = str(raw_attrs.get("hint") or raw_attrs.get("placeholder") or "")
        return _match_hypium_str(val, pat, mode)

    if method == "description":
        pat, mode = args
        val = str(
            raw_attrs.get("description")
            or raw_attrs.get("accessibilityDescription")
            or raw_attrs.get("content-desc")
            or ""
        )
        return _match_hypium_str(val, pat, mode)

    if method in ("inWindow", "bundleName"):
        pat, mode = args
        cur_el = elem
        while cur_el is not None:
            cur_comp = comp_by_elem.get(cur_el) or {}
            cur_attrs = cur_comp.get("raw_attributes") or cur_comp.get("raw") or {}
            bundle = str(cur_attrs.get("bundleName") or cur_attrs.get("package") or "")
            if bundle:
                return _match_hypium_str(bundle, pat, mode)
            cur_el = parent_map.get(cur_el)
        bundle = str(raw_attrs.get("bundleName") or raw_attrs.get("package") or "")
        return _match_hypium_str(bundle, pat, mode)

    if method in _HYPIUM_BOOL_METHODS:
        expected_flag = bool(args[0])
        kebab_key = re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), method)
        raw_val = None
        for k in (method, method.lower(), kebab_key):
            if k in raw_attrs:
                raw_val = raw_attrs.get(k)
                break
        if isinstance(raw_val, bool):
            actual_flag = raw_val
        else:
            actual_flag = str(raw_val or "").strip().lower() in ("true", "1", "yes")
        return actual_flag == expected_flag

    return False


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
# 自适应内容换行状态标签控件 (防止单行长文本撑大窗口)
# ==============================================================================

class AutoWrapStatusLabel(QLabel):
    """
    自适应内容换行的状态标签：
    1. 彻底断绝单行长文本向外撑开父级布局/窗口宽度；
    2. 水平方向不向父级索取超长尺寸 (minimumSizeHint 返回 0 宽度)；
    3. 根据当前实际获得宽度自适应多行折行渲染 (WordWrap)，高度自适应增高。
    """
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self) -> QSize:
        w = self.width() if self.width() > 50 else 300
        h = self.heightForWidth(w)
        return QSize(w, max(24, h))


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
        self.setWindowTitle(f"元素定位与查找器 ({plat_title})")
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

            /* 统一标准按钮基类 (规整 32px 高度、圆角 6px、细边框白底黑字，字号 13px) */
            QPushButton {
                background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 16px; font-weight: 600; font-size: 13px; min-height: 32px;
                text-align: center;
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
                font-size: 13px; font-weight: 600; padding: 0 18px; min-height: 32px;
                text-align: center;
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
                font-size: 13px; min-height: 32px;
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

        self.chk_stay_on_top = QCheckBox("保持置顶 (防遮挡)")
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

        # 快速格式切换胶囊按钮组 (Locator Format Quick Pills)
        self.format_pill_layout = QHBoxLayout()
        self.format_pill_layout.setSpacing(6)
        self.format_pill_layout.setContentsMargins(0, 0, 0, 0)
        self.format_pill_buttons: Dict[str, QPushButton] = {}
        layout.addLayout(self.format_pill_layout)

        layout.addWidget(QLabel("选择器表达式 (Selector):"))
        sel_row = QHBoxLayout()
        # 核心：使用 AutoResizingTextEdit 随填写内容上下自适应调整输入框高度 (默认 54px，更大更宽裕，最高自适应撑开至 180px)，左右宽度由父布局撑满
        self.edit_selector = AutoResizingTextEdit(min_height=54, max_height=180)
        self.edit_selector.textChanged.connect(self._on_selector_text_changed)
        sel_row.addWidget(self.edit_selector, 1)

        self.btn_pick_current = QPushButton("填入主视窗选中元素")
        self.btn_pick_current.setIcon(get_tech_icon("target", "#0284c7"))
        self.btn_pick_current.setIconSize(QSize(14, 14))
        self.btn_pick_current.setFixedHeight(34)
        self.btn_pick_current.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick_current.setToolTip("将当前在真机画面或 DOM 树中选中的组件表达式快速填入输入框")
        self.btn_pick_current.clicked.connect(self.pick_current_element_to_input)
        sel_row.addWidget(self.btn_pick_current, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(sel_row)

        # 跟随主界面点击自动填充复选框
        self.chk_auto_pick = QCheckBox("主视窗点击真机或 DOM 树时，自动填充推荐定位器")
        self.chk_auto_pick.setChecked(False)
        self.chk_auto_pick.setStyleSheet("color: #475569; font-size: 12px;")
        layout.addWidget(self.chk_auto_pick)

        # 智能过滤被遮挡/未展开的隐藏层元素复选框
        self.chk_only_visible = QCheckBox("仅匹配当前真实展示元素 (智能过滤被遮挡/未展开的隐藏层)")
        self.chk_only_visible.setChecked(True)
        self.chk_only_visible.setStyleSheet("color: #0284c7; font-size: 12px; font-weight: 600;")
        self.chk_only_visible.stateChanged.connect(self._on_only_visible_changed)
        layout.addWidget(self.chk_only_visible)

        # 构建策略下拉项并设置初始占位符与信号监听
        self._rebuild_strategies()
        self.combo_strategy.currentIndexChanged.connect(self._on_strategy_changed)

        btn_layout = QHBoxLayout()
        self.btn_search = QPushButton("查找匹配元素 (Search)")
        self.btn_search.setIcon(get_tech_icon("search", "#ffffff"))
        self.btn_search.setIconSize(QSize(15, 15))
        self.btn_search.setObjectName("btnSearchExec")
        self.btn_search.setFixedHeight(32)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self.do_search)
        self.edit_selector.returnPressed.connect(self.do_search)
        btn_layout.addWidget(self.btn_search, 0, Qt.AlignmentFlag.AlignTop)

        self.lbl_status = AutoWrapStatusLabel("就绪，请输入表达式或点击主视窗元素后点击查找")
        self.lbl_status.setStyleSheet("color: #0284c7; font-weight: 600;")
        btn_layout.addWidget(self.lbl_status, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("匹配到的元素列表 (Elements Found):"))
        self.list_results = QListWidget()
        self.list_results.setWordWrap(True)
        self.list_results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_results.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_results, 1)

        bottom_box = QHBoxLayout()
        bottom_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.btn_tap = QPushButton("点击该元素 (Tap)")
        self.btn_tap.setIcon(get_tech_icon("tap", "#0284c7"))
        self.btn_tap.setIconSize(QSize(15, 15))
        self.btn_tap.setFixedHeight(32)
        self.btn_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tap.setEnabled(False)
        self.btn_tap.clicked.connect(self.on_tap_clicked)
        bottom_box.addWidget(self.btn_tap)

        self.btn_send_keys = QPushButton("输入文本 (Send Keys)")
        self.btn_send_keys.setIcon(get_tech_icon("send", "#0284c7"))
        self.btn_send_keys.setIconSize(QSize(15, 15))
        self.btn_send_keys.setFixedHeight(32)
        self.btn_send_keys.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_keys.setEnabled(False)
        self.btn_send_keys.clicked.connect(self.on_send_keys_clicked)
        bottom_box.addWidget(self.btn_send_keys)

        bottom_box.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setFixedHeight(32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setObjectName("btnCancel")
        btn_close.clicked.connect(self.close)
        bottom_box.addWidget(btn_close)
        layout.addLayout(bottom_box)

    def _get_platform_strategies(self) -> List[Tuple[str, str, str]]:
        """
        获取当前平台定位策略的推荐性能与优先级排行 (单例统一基线，首位即为最佳性能首选):
        1. 原生高速索引/ID 永远排在第 1 位 (哈希索引直达，10-30ms)
        2. 原生结构化层级与谓词 (Class Chain / Predicate / UiAutomator / Text) 排在第 2-3 位
        3. 遍历整棵虚拟 DOM 树的慢速 XPath 放在第 4 位作为灵活兜底 (避免一律默认慢速全表扫描)
        4. 类型/类名放在末尾作为组件批量筛选
        """
        if self.platform == "android":
            return [
                ("id", "Resource-ID", "id (resource-id 标识 - 推荐首选)"),
                ("accessibility id", "Accessibility ID", "accessibility id (content-desc 文本/描述)"),
                ("uiautomator", "UiAutomator", "android uiautomator (UiSelector 语法表达式)"),
                ("xpath", "XPath", "xpath (XPath 路径表达式 - 灵活兜底)"),
                ("class name", "Class Name", "class name (组件类名)"),
            ]
        elif self.platform == "ios":
            return [
                ("id", "Accessibility ID", "id / accessibility id (name / label 标识 - 推荐首选)"),
                ("class chain", "Class Chain", "ios class chain (原生类链表达式 - 快速层级)"),
                ("predicate", "Predicate String", "ios predicate string (原生谓词表达式 - 复合条件)"),
                ("xpath", "XPath", "xpath (XPath 路径表达式 - 灵活兜底)"),
                ("class name", "Class Name", "class name (XCUIElementType 组件类型)"),
            ]
        else:  # harmony
            return [
                ("id", "ID / Key", "id (组件 Key / ID 标识 - By.id - 推荐首选)"),
                ("text", "Text 文本", "text (文本内容 - By.text - 原生高效)"),
                ("hypium", "HypiumBy", "HypiumBy (BY.* 原生链式表达式 - 支持 isAfter/isBefore/within)"),
                ("description", "Description", "description (无障碍描述 - By.description)"),
                ("xpath", "XPath", "xpath (XPath 路径表达式 - 灵活兜底)"),
                ("type", "Type 类型", "type / class name (ArkUI 组件类型名 - By.type)"),
            ]

    def _rebuild_strategies(self):
        """根据当前运行平台重建所支持的查找定位策略胶囊与下拉项，严格遵循性能优先级排列"""
        self.combo_strategy.blockSignals(True)
        self.combo_strategy.clear()

        # 清除旧胶囊按钮
        if hasattr(self, "format_pill_layout"):
            while self.format_pill_layout.count():
                item = self.format_pill_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            self.format_pill_buttons.clear()

        strategies = self._get_platform_strategies()

        for s_key, s_short, s_full in strategies:
            self.combo_strategy.addItem(s_full, s_key)
            if hasattr(self, "format_pill_layout"):
                btn = QPushButton(s_short)
                btn.setFixedHeight(26)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setToolTip(f"一键切换至 [{s_short}] 格式并自动填入表达式")
                btn.clicked.connect(lambda checked=False, k=s_key: self._on_format_pill_clicked(k))
                self.format_pill_layout.addWidget(btn)
                self.format_pill_buttons[s_key] = btn

        if hasattr(self, "format_pill_layout"):
            self.format_pill_layout.addStretch()

        # 默认严格选中第 0 项（即推荐排在第一位的最高效定位策略）
        self.combo_strategy.setCurrentIndex(0)
        self.combo_strategy.blockSignals(False)
        self._update_format_pills_active_state(self.combo_strategy.currentData())
        self.update_placeholder()

    def _update_format_pills_active_state(self, active_key: str):
        """刷新胶囊按钮的高亮选中状态"""
        if not hasattr(self, "format_pill_buttons"):
            return
        for k, btn in self.format_pill_buttons.items():
            if k == active_key:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7; color: #ffffff;
                        border: 1px solid #0284c7; border-radius: 13px;
                        padding: 0 12px; font-weight: 700; font-size: 11px; min-height: 26px;
                    }
                    QPushButton:hover { background-color: #0369a1; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8fafc; color: #475569;
                        border: 1px solid #cbd5e1; border-radius: 13px;
                        padding: 0 12px; font-weight: 600; font-size: 11px; min-height: 26px;
                    }
                    QPushButton:hover { background-color: #f1f5f9; color: #0f172a; border-color: #94a3b8; }
                """)

    def _on_format_pill_clicked(self, strategy_key: str):
        """用户点击快捷格式胶囊标签时，秒级切换定位策略并智能回填"""
        idx = self.combo_strategy.findData(strategy_key)
        if idx >= 0:
            self.combo_strategy.setCurrentIndex(idx)

    def _get_expression_for_strategy(self, strategy: str, comp: Dict[str, Any]) -> str:
        """根据定位策略智能提取组件对应的标准化推荐表达式"""
        if not comp:
            return ""
        rec_xp = comp.get("rec_xpath") or comp.get("xpath") or ""
        rec_id = comp.get("rec_id") or comp.get("id") or ""
        rec_text = comp.get("text") or ""
        rec_type = comp.get("type") or ""
        rec_full_type = comp.get("full_type") or comp.get("rec_class") or rec_type
        rec_pred = comp.get("rec_predicate") or ""
        rec_chain = comp.get("rec_class_chain") or ""
        raw_attrs = comp.get("raw_attributes") or comp.get("raw") or {}

        if strategy == "xpath":
            return rec_xp
        elif strategy == "predicate":
            if rec_pred:
                return rec_pred
            ios_val = raw_attrs.get("value") or ""
            if rec_id:
                return f'type == "{rec_full_type}" AND name == "{rec_id}"'
            elif rec_text:
                return f'type == "{rec_full_type}" AND (label == "{rec_text}" OR name == "{rec_text}")'
            elif ios_val:
                return f'type == "{rec_full_type}" AND value == "{ios_val}"'
            return f'type == "{rec_full_type}"'
        elif strategy == "class chain":
            if rec_chain:
                return rec_chain
            if rec_id:
                return f'**/{rec_full_type}[`name == "{rec_id}"`]'
            elif rec_text:
                return f'**/{rec_full_type}[`label == "{rec_text}"`]'
            return f'**/{rec_full_type}'
        elif strategy in ("id", "accessibility id"):
            if self.platform == "ios":
                ios_name = raw_attrs.get("name") or raw_attrs.get("id") or rec_id
                ios_label = raw_attrs.get("label") or rec_text
                return ios_name or ios_label or rec_id
            return rec_id or rec_text
        elif strategy in ("class name", "type"):
            return rec_full_type if self.platform in ("ios", "android") else rec_type
        elif strategy == "text":
            return rec_text
        elif strategy == "hypium":
            safe_type = rec_type.replace("\\", "\\\\").replace('"', '\\"') if rec_type else ""
            safe_id = rec_id.replace("\\", "\\\\").replace('"', '\\"') if rec_id else ""
            safe_text = rec_text.replace("\\", "\\\\").replace('"', '\\"') if rec_text else ""
            raw_hint = str(raw_attrs.get("hint") or raw_attrs.get("placeholder") or "")
            safe_hint = raw_hint.replace("\\", "\\\\").replace('"', '\\"') if raw_hint else ""
            if safe_type and safe_id:
                return f'BY.type("{safe_type}").id("{safe_id}")'
            if safe_id:
                return f'BY.id("{safe_id}")'
            if safe_type and safe_text:
                return f'BY.type("{safe_type}").text("{safe_text}")'
            if safe_text:
                return f'BY.text("{safe_text}")'
            if safe_type and safe_hint:
                return f'BY.type("{safe_type}").hint("{safe_hint}")'
            if safe_type:
                return f'BY.type("{safe_type}")'
            return ""
        elif strategy == "description":
            return str(raw_attrs.get("description") or raw_attrs.get("content-desc") or rec_text)
        elif strategy == "uiautomator":
            if rec_text:
                return f'text("{rec_text}")'
            elif rec_id:
                return f'resourceId("{rec_id}")'
            elif rec_full_type:
                return f'className("{rec_full_type}")'
            return ""
        return rec_xp

    def _on_strategy_changed(self):
        strat = self.combo_strategy.currentData()
        self._update_format_pills_active_state(strat)
        self.update_placeholder()
        self._save_memory()

        # 若主视窗当前已选中元素，切换格式时自动刷新输入框中的表达式
        comp = getattr(self, "last_main_selected_comp", None)
        if comp:
            expr = self._get_expression_for_strategy(strat, comp)
            if expr:
                self.edit_selector.setText(expr)
                strat_name = self.combo_strategy.currentText().split(" (")[0]
                self.lbl_status.setText(f"已切换为 [{strat_name}] 格式表达式，点击【查找】验证")

    def _on_only_visible_changed(self):
        self._save_memory()
        if hasattr(self, "edit_selector") and self.edit_selector.text().strip():
            self.do_search()

    def _apply_native_topmost(self, on_top: bool):
        """
        可靠切换窗口置顶状态 (Qt 标准 WindowStaysOnTopHint + Win32 SetWindowPos 双重加固):
        1. 必须始终显式同步 Qt 自身的 WindowStaysOnTopHint 窗口标志，确保 Qt 内部重绘/激活状态机不会覆盖置顶；
        2. Windows 平台通过 SetWindowPos 深度加固 HWND_TOPMOST / HWND_NOTOPMOST，确保 100% 绝对置顶于主视窗之上防遮挡。
        """
        was_visible = self.isVisible()
        flags = self.windowFlags()
        if on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint

        if self.windowFlags() != flags:
            self.setWindowFlags(flags)
            if was_visible:
                self.show()

        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                HWND_TOPMOST = -1
                HWND_NOTOPMOST = -2
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                flags_pos = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                target = HWND_TOPMOST if on_top else HWND_NOTOPMOST
                ctypes.windll.user32.SetWindowPos(hwnd, target, 0, 0, 0, 0, flags_pos)
            except Exception as e:
                logger.debug(f"Win32 SetWindowPos 调度异常: {e}")

    def _update_stay_on_top_state(self):
        """核心调度：直接严格遵从用户勾选状态进行置顶，彻底消除焦点切换带来的闪烁与误解除"""
        if not hasattr(self, "chk_stay_on_top"):
            return
        on_top = self.chk_stay_on_top.isChecked() and self.isVisible()
        self._apply_native_topmost(on_top)

    def _toggle_stay_on_top(self, checked: bool):
        """响应用户点击【📌 保持置顶】复选框：100% 即刻生效"""
        self._save_memory()
        self._apply_native_topmost(checked)
        if checked:
            self.raise_()
            self.activateWindow()

    def _on_app_state_changed(self, state: Qt.ApplicationState):
        """系统级应用状态变化监听"""
        pass

    def changeEvent(self, event: QEvent):
        """窗口激活状态变化监听"""
        super().changeEvent(event)

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
            self.setWindowTitle(f"元素定位与查找器 ({plat_title})")
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
            raw_attrs = comp.get("raw_attributes") or comp.get("raw") or {}
            attr_summary = ""
            if self.platform == "ios":
                ios_name = raw_attrs.get("name") or raw_attrs.get("id") or comp.get("id") or ""
                ios_label = raw_attrs.get("label") or ""
                ios_value = raw_attrs.get("value") or comp.get("text") or ""
                if ios_value:
                    short_v = ios_value if len(ios_value) <= 20 else ios_value[:20] + "..."
                    attr_summary += f' value="{short_v}"'
                if ios_name:
                    short_n = ios_name if len(ios_name) <= 20 else ios_name[:20] + "..."
                    attr_summary += f' name="{short_n}"'
                if ios_label and ios_label != ios_value:
                    short_l = ios_label if len(ios_label) <= 20 else ios_label[:20] + "..."
                    attr_summary += f' label="{short_l}"'
            else:
                if comp.get("id"):
                    attr_summary += f' id="{comp["id"]}"'
                if comp.get("text"):
                    short_t = comp["text"] if len(comp["text"]) <= 22 else comp["text"][:22] + "..."
                    attr_summary += f' text="{short_t}"'
            self.lbl_status.setText(f"主视窗已选中: <{c_tag}{attr_summary} bounds=\"{c_bounds}\"> (点击【填入主视窗选中元素】)")

    def pick_current_element_to_input(self):
        """将主视窗当前选中的组件推荐表达式按当前策略填入选择器输入框"""
        comp = getattr(self, "last_main_selected_comp", None)
        if not comp:
            self.lbl_status.setText("提示: 请先在主视窗点击选中任意真机或 DOM 树元素")
            return

        curr_strat = self.combo_strategy.currentData()
        target_expr = self._get_expression_for_strategy(curr_strat, comp)
        if not target_expr:
            # 若当前策略无法生成表达式（如当前策略为 ID 但该元素无 ID），按推荐优先级顺序自动探测可用最佳策略
            for s_key, _, _ in self._get_platform_strategies():
                candidate_expr = self._get_expression_for_strategy(s_key, comp)
                if candidate_expr:
                    target_expr = candidate_expr
                    idx = self.combo_strategy.findData(s_key)
                    if idx >= 0:
                        self.combo_strategy.setCurrentIndex(idx)
                    break

        if target_expr:
            self.edit_selector.setText(target_expr)

        strat_title = self.combo_strategy.currentText().split(" (")[0]
        self.lbl_status.setText(f"已按 [{strat_title}] 策略填入 <{comp.get('type')}> 推荐表达式，点击【查找】验证")

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
                "id": "例如: ic delete 48 或 login_btn (Accessibility ID / Name / Label 标识)",
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
                "hypium": '例如: BY.type("Text").text("手机号登录")，或直接粘贴源码 HosBy.between_texts(...) / 日志元组',
                "type": "例如: Button 或 Text 或 TextInput (ArkUI 类型)",
                "description": "例如: 无障碍描述文本",
            }
        self.edit_selector.setPlaceholderText(tips.get(strategy, "请输入定位选择器表达式"))

    def do_search(self):
        # 执行前主动校验并对齐父级主窗口的最新 XML 与组件映射树，防止跨生命周期串位
        parent_win = getattr(self, "inspector", None) or self.parent()
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
        # 鸿蒙平台友好增强：自动识别并解包源码 HosBy.xxx(...)、日志定位二元组 ('text'/'type'/'id'/'key'/'xpath'/'HypiumBy', ...) 与 BY.* 表达式
        # 仅在内部按解包后的策略与值执行查询，保持输入框原文不变，方便用户微调参数反复验证
        hos_pre_err = None
        if self.platform == "harmony":
            res_strat, res_val, hos_pre_err = resolve_harmony_locator_input(val)
            if res_strat:
                if res_strat != strategy:
                    target_idx = self.combo_strategy.findData(res_strat)
                    if target_idx >= 0:
                        self.combo_strategy.blockSignals(True)
                        self.combo_strategy.setCurrentIndex(target_idx)
                        self.combo_strategy.blockSignals(False)
                        self._update_format_pills_active_state(res_strat)
                        self.update_placeholder()
                        strategy = res_strat
                if res_val is not None:
                    val = res_val

        syntax_err = hos_pre_err
        example_str = 'HosBy.between_texts(after_text="密码验证登录", before_text="我已阅读且同意", target_type="Image")' if hos_pre_err else ""
        if syntax_err:
            pass
        elif self.platform == "ios":
            syntax_err, example_str = validate_ios_selector_syntax(strategy, val)
        elif strategy == "hypium":
            syntax_err, _ = parse_hypium_by_expression(val)
            example_str = 'BY.isAfter(BY.text("密码验证登录")).isBefore(BY.text("我已阅读且同意", 1)).type("Image") 或 HosBy.text_contains("我已阅读且同意", "Text")'
        elif strategy == "xpath":
            syntax_err = validate_xpath_syntax(val)
            example_str = "//Text[@text='会员中心'] 或 //Button[contains(@text, '发送')]"
        elif strategy == "id":
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到 XPath 路径语法特征；当前策略为 [id]，若要使用路径定位请切换策略为 [xpath]"
                example_str = "login_button 或 send_btn 或 com.santiao.im:id/btn_send"
            elif val.startswith("@"):
                syntax_err = "ID 选择器无需添加 '@' 前缀；请直接输入组件 ID 或 Key"
                example_str = val.lstrip("@")
            elif " " in val and self.platform != "ios":
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

        def eval_atomic_predicate(atom_expr: str, comp: Dict[str, Any]) -> bool:
            sub = atom_expr.strip().strip("()")
            if not sub:
                return True
            is_neg = False
            if re.match(r'^(?:NOT\s+|!\s*)', sub, re.IGNORECASE):
                is_neg = True
                sub = re.sub(r'^(?:NOT\s+|!\s*)', '', sub, flags=re.IGNORECASE).strip().strip("()")

            raw_attrs = comp.get("raw_attributes", {}) or comp.get("raw", {})
            c_label = str(raw_attrs.get("label", "") or comp.get("text", "") or raw_attrs.get("value", "")).lower()
            c_name = str(raw_attrs.get("name", "") or comp.get("id", "") or raw_attrs.get("label", "")).lower()
            c_type = comp.get("type", "").lower()
            c_type_full = c_type if c_type.startswith("xcuielementtype") else f"xcuielementtype{c_type}"
            c_type_short = c_type.replace("xcuielementtype", "")
            c_val = str(raw_attrs.get("value", "")).lower()

            res = True
            # 1. 优先支持集合判定: type IN {'XCUIElementTypeButton', ...} 或 label IN {'a', 'b'}
            in_match = re.search(r'^([A-Za-z_][A-Za-z0-9_\.]*)\s+IN(?:\s*\[[cd]+\])?\s*\{([^}]+)\}$', sub, re.IGNORECASE)
            if in_match:
                attr_key = in_match.group(1).lower()
                items = []
                for raw_s in in_match.group(2).split(","):
                    tok = raw_s.strip()
                    if not tok:
                        continue
                    if (tok.startswith("'") and tok.endswith("'")) or (tok.startswith('"') and tok.endswith('"')):
                        tok = tok[1:-1]
                    items.append(tok.lower())
                if attr_key == "type":
                    res = (c_type in items) or (c_type_full in items) or (c_type_short in items)
                else:
                    target_val = c_label if attr_key == "label" else (c_name if attr_key == "name" else c_val)
                    res = target_val in items
            else:
                # 2. 基础比较运算符判定 (==, =, !=, CONTAINS, BEGINSWITH, ENDSWITH, LIKE, MATCHES)
                cmp_m = re.search(
                    r'^([A-Za-z_][A-Za-z0-9_\.]*)\s*(==|!=|=|<>|<=|>=|<|>|\b(?:CONTAINS|BEGINSWITH|ENDSWITH|LIKE|MATCHES)\b(?:\s*\[[cd]+\])?)\s*(.+)$',
                    sub,
                    re.IGNORECASE,
                )
                if cmp_m:
                    attr_key = cmp_m.group(1).lower()
                    op = cmp_m.group(2).upper()
                    rhs = cmp_m.group(3).strip()
                    if (rhs.startswith("'") and rhs.endswith("'")) or (rhs.startswith('"') and rhs.endswith('"')):
                        rhs = rhs[1:-1]
                    rhs_lower = rhs.lower()
                    if attr_key == "type":
                        rhs_short = rhs_lower.replace("xcuielementtype", "")
                        rhs_full = rhs_lower if rhs_lower.startswith("xcuielementtype") else f"xcuielementtype{rhs_lower}"
                        is_type_eq = (c_type == rhs_lower or c_type == rhs_short or c_type_full == rhs_full or c_type_short == rhs_short)
                        res = is_type_eq if op in ("==", "=") else not is_type_eq
                    else:
                        if attr_key in ("visible", "isvisible"):
                            raw_vis = raw_attrs.get("visible") if "visible" in raw_attrs else comp.get("is_visible", "")
                            lhs = str(raw_vis).lower()
                        else:
                            lhs = c_label if attr_key == "label" else (c_name if attr_key == "name" else (c_val if attr_key == "value" else str(raw_attrs.get(attr_key, "")).lower()))
                        bool_true = {"true", "1", "yes"}
                        bool_false = {"false", "0", "no"}
                        if op in ("==", "="):
                            if (lhs in bool_true or lhs in bool_false) and (rhs_lower in bool_true or rhs_lower in bool_false):
                                res = (lhs in bool_true) == (rhs_lower in bool_true)
                            else:
                                res = (lhs == rhs_lower)
                        elif op in ("!=", "<>"):
                            if (lhs in bool_true or lhs in bool_false) and (rhs_lower in bool_true or rhs_lower in bool_false):
                                res = (lhs in bool_true) != (rhs_lower in bool_true)
                            else:
                                res = (lhs != rhs_lower)
                        elif op.startswith("BEGINSWITH"):
                            res = lhs.startswith(rhs_lower)
                        elif op.startswith("ENDSWITH"):
                            res = lhs.endswith(rhs_lower)
                        elif op.startswith("MATCHES"):
                            try:
                                res = bool(re.search(rhs, raw_attrs.get(attr_key, "") or ""))
                            except Exception:
                                res = False
                        else:
                            res = (rhs_lower in lhs)
                else:
                    res = False

            return (not res) if is_neg else res

        def eval_ast_bool(node, c_map: Dict[str, bool]) -> bool:
            if isinstance(node, ast.Expression):
                return eval_ast_bool(node.body, c_map)
            elif isinstance(node, ast.BoolOp):
                if isinstance(node.op, ast.And):
                    return all(eval_ast_bool(v, c_map) for v in node.values)
                elif isinstance(node.op, ast.Or):
                    return any(eval_ast_bool(v, c_map) for v in node.values)
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                return not eval_ast_bool(node.operand, c_map)
            elif isinstance(node, ast.Name):
                return c_map.get(node.id, False)
            elif isinstance(node, ast.Constant):
                return bool(node.value)
            return False

        def match_ios_predicate(pred_expr: str, comps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            p_err, atom_list, py_expr = tokenize_ios_predicate(pred_expr)
            if p_err or not atom_list:
                atom_list = [pred_expr]
                py_expr = "_c_0"
            try:
                eval_tree = ast.parse(py_expr, mode='eval')
            except Exception:
                eval_tree = None
            out = []
            for comp in comps:
                if eval_tree:
                    c_map = {f"_c_{k}": eval_atomic_predicate(atom, comp) for k, atom in enumerate(atom_list)}
                    if eval_ast_bool(eval_tree, c_map):
                        out.append(comp)
                elif all(eval_atomic_predicate(atom, comp) for atom in atom_list):
                    out.append(comp)
            return out

        try:
            if strategy == "id":
                for c in self.flat_components:
                    cid = c.get("id", "")
                    raw_attrs = c.get("raw_attributes", {}) or c.get("raw", {})
                    raw_id = raw_attrs.get("resource-id", "") or raw_attrs.get("name", "") or raw_attrs.get("id", "")
                    raw_label = raw_attrs.get("label", "") if self.platform == "ios" else ""
                    raw_ident = raw_attrs.get("identifier", "") if self.platform == "ios" else ""
                    targets = [t for t in (cid, raw_id, raw_label, raw_ident) if t]
                    if any(val_lower == t.lower() or val_lower in t.lower() for t in targets):
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
                    if self.platform == "ios":
                        ctype_short = ctype.lower().replace("xcuielementtype", "")
                        val_short = val_lower.replace("xcuielementtype", "")
                        c_full_type = str(c.get("full_type", "")).lower()
                        if val_short == ctype_short or val_lower == c_full_type or val_short in ctype_short or val_lower in ctype.lower():
                            matched.append(c)
                    else:
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
                # 支持 iOS 原生 Predicate 表达式 (完整覆盖 AST 级布尔树、括号嵌套、OR/AND/NOT、IN {...} 集合与 ==/CONTAINS)
                matched = match_ios_predicate(val, self.flat_components)
            elif strategy == "class chain" and "`" not in val and "$" not in val and re.fullmatch(r"(\*\*/|/)?[\w*]+(\[-?\d+\])?(/(\*\*/)?[\w*]+(\[-?\d+\])?)*", val.strip()):
                chain_xp = val.strip().replace("**/", "//")
                if not chain_xp.startswith("/"):
                    chain_xp = "/" + chain_xp
                chain_xp = re.sub(r"(?<=/)(?!XCUIElementType|\*)([A-Za-z]\w*)", r"XCUIElementType\1", chain_xp)
                chain_xp = re.sub(
                    r"\[-(\d+)\]",
                    lambda m: "[last()]" if m.group(1) == "1" else f"[last()-{int(m.group(1)) - 1}]",
                    chain_xp,
                )
                matched = self.match_xpath(chain_xp)
            elif strategy == "class chain":
                raw_chain = val.strip()
                # 提取链条目标末端节点（处理多级斜杠 /，但忽略反引号内部的 /）
                segs = [s.strip() for s in re.split(r'/(?![^\[]*\])', raw_chain) if s.strip() and s.strip() not in ("**", "*")]
                last_seg = segs[-1] if segs else raw_chain.replace("**/", "").replace("/*", "").strip()

                # 从末端段分离组件类名、自身谓词 [`predicate`]、子孙谓词 [$predicate$] 或索引 [1]
                pred_inner = ""
                desc_pred_inner = ""
                idx_filter = None
                chain_type = last_seg

                m_pred = re.search(r'\[`([^`]+)`\]', last_seg)
                m_desc_pred = re.search(r'\[\$([^$]+)\$\]', last_seg)
                if m_pred:
                    pred_inner = m_pred.group(1).strip()
                    chain_type = last_seg[:m_pred.start()].strip()
                elif m_desc_pred:
                    desc_pred_inner = m_desc_pred.group(1).strip()
                    chain_type = last_seg[:m_desc_pred.start()].strip()
                else:
                    m_idx = re.search(r'\[(-?\d+)\]', last_seg)
                    if m_idx:
                        idx_filter = int(m_idx.group(1))
                        chain_type = last_seg[:m_idx.start()].strip()
                    else:
                        m_plain_pred = re.search(r'\[([a-zA-Z_].+)\]', last_seg)
                        if m_plain_pred:
                            pred_inner = m_plain_pred.group(1).strip()
                            chain_type = last_seg[:m_plain_pred.start()].strip()

                chain_type_clean = chain_type.replace("**/", "").replace("/*", "").strip()
                chain_type_lower = chain_type_clean.lower()
                chain_type_short = chain_type_lower.replace("xcuielementtype", "")

                # 若含 [$...$] 子孙条件，预先构建符合条件的后代 node_id 集合及 XML 节点索引
                desc_matched_ids = set()
                xml_node_by_id: Dict[str, Any] = {}
                if desc_pred_inner:
                    desc_matched_ids = {
                        mc.get("node_id")
                        for mc in match_ios_predicate(desc_pred_inner, list(self.comp_map.values()) or self.flat_components)
                        if mc.get("node_id")
                    }
                    if self.xml_root is not None:
                        xml_node_by_id = {
                            el.attrib.get("node_id"): el
                            for el in self.xml_root.iter()
                            if el.attrib.get("node_id")
                        }

                cand_matched = []
                for c in self.flat_components:
                    c_type = c.get("type", "").lower()
                    c_type_short = c_type.replace("xcuielementtype", "")
                    c_full_type = str(c.get("full_type", "")).lower()

                    # 1. 类型判定：兼容通配符 *、XCUIElementType* 完整类名及短类名双向匹配
                    if chain_type_clean and chain_type_clean != "*":
                        type_matched = (
                            chain_type_short == c_type_short
                            or chain_type_lower == c_full_type
                            or chain_type_short in c_type_short
                            or chain_type_lower in c_type
                        )
                        if not type_matched:
                            continue

                    # 2. 自身谓词求值 (若存在 [`predicate`])
                    if pred_inner and not match_ios_predicate(pred_inner, [c]):
                        continue

                    # 3. 子孙谓词求值 (若存在 [$predicate$])
                    if desc_pred_inner:
                        c_nid = c.get("node_id")
                        xml_el = xml_node_by_id.get(c_nid)
                        if xml_el is not None:
                            has_desc = any(
                                sub is not xml_el and sub.attrib.get("node_id") in desc_matched_ids
                                for sub in xml_el.iter()
                            )
                            if not has_desc:
                                continue
                        else:
                            continue

                    cand_matched.append(c)

                # 3. 索引过滤 (Class Chain 规范为 1-based 索引)
                if idx_filter is not None and cand_matched:
                    if idx_filter > 0 and idx_filter <= len(cand_matched):
                        matched = [cand_matched[idx_filter - 1]]
                    elif idx_filter < 0 and abs(idx_filter) <= len(cand_matched):
                        matched = [cand_matched[idx_filter]]
                    else:
                        matched = []
                else:
                    matched = cand_matched
            elif strategy == "hypium":
                matched = self.match_hypium_by(val)
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
                "xpath": "建议核对标签名大小写、属性值及层级，或点击【填入主视窗选中元素】获取推荐路径",
                "text": "建议核对文本大小写、去除首尾空格，或取消勾选【仅匹配当前真实展示元素】重试",
                "hypium": "建议核对 BY.text/type/isAfter/isBefore 参数与匹配模式 (0=精确, 1=包含, 4=正则)，或取消勾选【仅匹配当前真实展示元素】排查背景页命中情况",
                "type": "未找到该类型的组件，请核对组件类型拼写 (如 Button、Text、ListItem、Flex)",
                "class name": "未找到该类型的组件，请核对类型名拼写",
                "description": "未找到包含该无障碍描述的组件，请检查 accessibility 属性设置",
                "accessibility id": "未找到包含该描述的组件，请检查 content-desc / label 属性",
            }
            tip_detail = strat_tips.get(strategy, "请核对选择器表达式与当前真机画面组件是否匹配")
            strat_label = self.combo_strategy.currentText().split(" (")[0]
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
            c_type = comp.get("type", "Component")
            c_scheme = get_dom_tag_color(c_type)
            title = f"元素 {idx + 1} - <{c_type}"
            raw_attrs = comp.get("raw_attributes") or comp.get("raw") or {}
            if self.platform == "ios":
                ios_name = raw_attrs.get("name") or raw_attrs.get("id") or comp.get("id") or ""
                ios_label = raw_attrs.get("label") or ""
                ios_value = raw_attrs.get("value") or comp.get("text") or ""
                if ios_value:
                    short_v = ios_value if len(ios_value) <= 20 else ios_value[:20] + "..."
                    title += f' value="{short_v}"'
                if ios_name:
                    short_n = ios_name if len(ios_name) <= 20 else ios_name[:20] + "..."
                    title += f' name="{short_n}"'
                if ios_label and ios_label != ios_value:
                    short_l = ios_label if len(ios_label) <= 20 else ios_label[:20] + "..."
                    title += f' label="{short_l}"'
            else:
                if comp.get('id'):
                    title += f" id=\"{comp['id']}\""
                if comp.get('text'):
                    c_text = comp['text']
                    short_t = c_text if len(c_text) <= 22 else c_text[:22] + "..."
                    title += f" text=\"{short_t}\""
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
                elem_tag = str(getattr(elem, "tag", "")).lower()
                comp_type = str(comp.get("type", "")).lower()
                comp_full = str(comp.get("full_type", "")).lower()
                if elem_tag and comp_type and elem_tag != "component":
                    elem_short = elem.attrib.get("short_type", "").lower() if hasattr(elem, "attrib") else ""
                    if not elem_short:
                        elem_short = elem_tag.replace("xcuielementtype", "").split(".")[-1]
                    # 双向兼容匹配短类型、完整原生类型与标签后缀
                    type_matched = (
                        elem_tag == comp_type
                        or elem_tag == comp_full
                        or elem_short == comp_type
                        or elem_tag.endswith(comp_type)
                    )
                    if not type_matched:
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

        raw_xp = xp.strip()

        # 优先支持 (//expr)[1] 或 (//expr)[last()] 等全局集合切片表达式 (FilterExpr)
        if raw_xp.startswith("("):
            p_depth = 0
            match_paren_idx = -1
            in_s = False
            in_d = False
            for idx, ch in enumerate(raw_xp):
                if ch == "'" and not in_d:
                    in_s = not in_s
                elif ch == '"' and not in_s:
                    in_d = not in_d
                elif not in_s and not in_d:
                    if ch == '(':
                        p_depth += 1
                    elif ch == ')':
                        p_depth -= 1
                        if p_depth == 0:
                            match_paren_idx = idx
                            break
            if match_paren_idx != -1:
                inner_xp = raw_xp[1:match_paren_idx].strip()
                outer_tail = raw_xp[match_paren_idx+1:].strip()
                if not outer_tail:
                    return self._evaluate_xpath_natively(root_elem, inner_xp)
                if outer_tail.startswith("[") and outer_tail.endswith("]"):
                    inner_nodes = self._evaluate_xpath_natively(root_elem, inner_xp)
                    pred = outer_tail[1:-1].strip()
                    if pred == "last()":
                        return [inner_nodes[-1]] if inner_nodes else []
                    elif pred.isdigit():
                        idx = int(pred)
                        if 1 <= idx <= len(inner_nodes):
                            return [inner_nodes[idx - 1]]
                        return []

        clean_xp = raw_xp.strip().strip("()")
        if clean_xp.startswith(".//"):
            clean_xp = clean_xp[1:]
        elif clean_xp.startswith("./"):
            clean_xp = clean_xp[1:]

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
                            candidates = list(reversed(siblings[:curr_idx]))
                        except ValueError:
                            pass
                elif axis_name == "preceding":
                    all_elems = list(root_elem.iter())
                    try:
                        curr_idx = all_elems.index(node)
                        candidates = list(reversed(all_elems[:curr_idx]))
                    except ValueError:
                        pass
                elif axis_name == "following":
                    all_elems = list(root_elem.iter())
                    try:
                        curr_idx = all_elems.index(node)
                        candidates = all_elems[curr_idx + 1:]
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

                # 按标签类型初筛 (双向容错支持短类型与完整原生类名，如 XCUIElementTypeTextField <=> TextField)
                filtered_by_tag = []
                query_short_l = tag_lower.replace("xcuielementtype", "").split(".")[-1]
                for cand in candidates:
                    cand_tag_l = cand.tag.lower()
                    cand_full_l = str(cand.attrib.get("full_type", "")).lower()
                    cand_short_l = str(cand.attrib.get("short_type", "")).lower() or cand_tag_l.replace("xcuielementtype", "").split(".")[-1]
                    match_tag = (
                        tag_name == "*"
                        or cand_tag_l == tag_lower
                        or cand_full_l == tag_lower
                        or cand_short_l == query_short_l
                        or cand_short_l == tag_lower
                        or cand_tag_l.endswith(tag_lower)
                    )
                    if match_tag:
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

                        def _eval_atomic(el_node, p_str):
                            p_str = p_str.strip()
                            attrs = el_node.attrib
                            # 1. contains(@attr, 'val') 或 contains(text(), 'val')
                            m_contains = re.match(r"^contains\s*\(\s*(@[a-zA-Z0-9_\-]+|text\(\))\s*,\s*['\"](.*?)['\"]\s*\)$", p_str, re.IGNORECASE)
                            if m_contains:
                                target_k, target_v = m_contains.group(1), m_contains.group(2)
                                actual_val = (attrs.get("text", "") or attrs.get("label", "") or (el_node.text or "")) if target_k == "text()" else attrs.get(target_k[1:], "")
                                return target_v in str(actual_val)

                            # 2. matches(@attr, 'pattern') 或 matches(text(), 'pattern')
                            m_matches = re.match(r"^matches\s*\(\s*(@[a-zA-Z0-9_\-]+|text\(\))\s*,\s*['\"](.*?)['\"](?:\s*,\s*['\"](.*?)['\"])?\s*\)$", p_str, re.IGNORECASE)
                            if m_matches:
                                target_k, pat, flags = m_matches.group(1), m_matches.group(2), m_matches.group(3) or ""
                                actual_val = (attrs.get("text", "") or attrs.get("label", "") or (el_node.text or "")) if target_k == "text()" else attrs.get(target_k[1:], "")
                                py_flags = re.IGNORECASE if "i" in flags.lower() else 0
                                try:
                                    return bool(re.search(pat, str(actual_val), py_flags))
                                except Exception:
                                    return False

                            # 3. @attr='val' 或 @attr="val"
                            m_eq = re.match(r"^@([a-zA-Z0-9_\-]+)\s*=\s*['\"](.*?)['\"]$", p_str)
                            if m_eq:
                                attr_k, attr_v = m_eq.group(1), m_eq.group(2)
                                actual_v = attrs.get(attr_k, "")
                                if not actual_v and attr_k in ("id", "resource-id", "name"):
                                    actual_v = attrs.get("id") or attrs.get("resource-id") or attrs.get("name") or ""
                                elif not actual_v and attr_k in ("text", "label", "value"):
                                    actual_v = attrs.get("text") or attrs.get("label") or attrs.get("value") or ""
                                return str(actual_v) == attr_v

                            # 4. [@id] 存在性过滤
                            if p_str.startswith("@"):
                                return bool(p_str[1:] in attrs and attrs[p_str[1:]])

                            # 5. 子路径或后代节点断言 (支持如 [.//Text[@text='...']] 或 [Row//Text])
                            if p_str.startswith((".", "//", "/")):
                                try:
                                    return bool(self._evaluate_xpath_natively(el_node, p_str))
                                except Exception:
                                    return False

                            # 6. 子元素标签名存在性过滤：例如 //Row[TextInput], //Stack[Search]
                            return any(sub.tag.lower() == p_str.lower() for sub in el_node.iter() if sub is not el_node)

                        def _eval_predicate(el_node, p_str):
                            p_str = p_str.strip()
                            # 处理 ' or ' 逻辑析取
                            if " or " in p_str:
                                or_branches = re.split(r"\s+or\s+", p_str)
                                return any(_eval_predicate(el_node, b) for b in or_branches)
                            # 处理 ' and ' 逻辑合取
                            if " and " in p_str:
                                and_branches = re.split(r"\s+and\s+", p_str)
                                return all(_eval_predicate(el_node, b) for b in and_branches)
                            return _eval_atomic(el_node, p_str)

                        pred_matched = [el for el in cand_results if _eval_predicate(el, pred)]

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

    def match_hypium_by(self, expr: str) -> List[Dict[str, Any]]:
        """
        基于当前 DOM 完整节点树执行鸿蒙 HypiumBy (BY.*) 原生语义匹配：
        完整支持 text/type/id/key/hint/description/inWindow (含 MatchPattern 0~5)、
        布尔状态属性以及 within / isBefore / isAfter 递归相对位置定位。
        """
        err, steps = parse_hypium_by_expression(expr)
        if err:
            raise ValueError(err)

        parent_map: Dict[ET.Element, ET.Element] = {}
        comp_by_elem: Dict[ET.Element, Dict[str, Any]] = {}
        ordered_items: List[Tuple[Optional[ET.Element], Dict[str, Any], int]] = []

        if self.xml_root is not None:
            for p in self.xml_root.iter():
                for ch in p:
                    parent_map[ch] = p

            idx_counter = 0
            for el in self.xml_root.iter():
                node_id = el.attrib.get("node_id")
                if not node_id:
                    continue
                comp = self.comp_map.get(node_id) if self.comp_map else None
                if not comp:
                    continue
                comp_by_elem[el] = comp
                ordered_items.append((el, comp, idx_counter))
                idx_counter += 1
        else:
            for idx_counter, comp in enumerate(self.flat_components):
                ordered_items.append((None, comp, idx_counter))

        def _is_ancestor(maybe_anc: Optional[ET.Element], node: Optional[ET.Element]) -> bool:
            if maybe_anc is None or node is None or maybe_anc is node:
                return False
            cur = parent_map.get(node)
            while cur is not None:
                if cur is maybe_anc:
                    return True
                cur = parent_map.get(cur)
            return False

        def _eval_chain(chain_steps: List[Tuple[str, Tuple[Any, ...]]]) -> List[Tuple[Optional[ET.Element], Dict[str, Any], int]]:
            candidates = list(ordered_items)
            for method, args in chain_steps:
                if not candidates:
                    break
                if method == "within":
                    sub_steps = args[0]
                    container_elems = {el for el, _, _ in _eval_chain(sub_steps) if el is not None}
                    if not container_elems:
                        candidates = []
                        continue
                    next_cands = []
                    for el, comp, idx in candidates:
                        cur = parent_map.get(el) if el is not None else None
                        found_anc = False
                        while cur is not None:
                            if cur in container_elems:
                                found_anc = True
                                break
                            cur = parent_map.get(cur)
                        if found_anc:
                            next_cands.append((el, comp, idx))
                    candidates = next_cands
                elif method == "isBefore":
                    sub_steps = args[0]
                    anchors = _eval_chain(sub_steps)
                    if not anchors:
                        candidates = []
                        continue
                    next_cands = []
                    for el, comp, idx in candidates:
                        if any(idx < a_idx and not _is_ancestor(el, a_el) for a_el, _, a_idx in anchors):
                            next_cands.append((el, comp, idx))
                    candidates = next_cands
                elif method == "isAfter":
                    sub_steps = args[0]
                    anchors = _eval_chain(sub_steps)
                    if not anchors:
                        candidates = []
                        continue
                    next_cands = []
                    for el, comp, idx in candidates:
                        if any(idx > a_idx and not _is_ancestor(a_el, el) for a_el, _, a_idx in anchors):
                            next_cands.append((el, comp, idx))
                    candidates = next_cands
                elif method == "xpath":
                    xp_str = str(args[0])
                    xp_matched_ids = {c.get("node_id") for c in self.match_xpath(xp_str) if c.get("node_id")}
                    candidates = [
                        (el, comp, idx)
                        for el, comp, idx in candidates
                        if comp.get("node_id") in xp_matched_ids
                    ]
                else:
                    candidates = [
                        (el, comp, idx)
                        for el, comp, idx in candidates
                        if _eval_hypium_attr_step(method, args, comp, el, parent_map, comp_by_elem)
                    ]
            return candidates

        result_items = _eval_chain(steps)
        return [comp for _, comp, _ in result_items]

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
                _init_lxml_xpath_extensions()
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
                self.lbl_status.setText("正在真机上执行点击动作...")
                QApplication.processEvents()
                self.tap_requested.emit(node_id)
                self.lbl_status.setText("已在设备上成功执行点击动作")

    def on_send_keys_clicked(self):
        curr = self.list_results.currentItem()
        if curr:
            node_id = curr.data(Qt.ItemDataRole.UserRole)
            if node_id:
                text, ok = ModernInputDialog.getText(self, "输入文本", "请输入要发送至该元素的文本内容:")
                if ok and text:
                    self.lbl_status.setText("正在向设备下发文本内容...")
                    QApplication.processEvents()
                    self.send_keys_requested.emit(node_id, text)
                    self.lbl_status.setText("文本已成功发送至目标组件")



# ==============================================================================
# 轻量高颜值无阻塞 Toast 悬浮提示条 (纯透明背景，绿色大号居中)
# ==============================================================================

class ToastNotification(QLabel):
    """
    轻量高颜值无阻塞 Toast 悬浮提示条：
    1. 居中悬浮展示 (视口正中央)，纯透明背景，绿色大号粗体醒目提示，鼠标事件完全穿透；
    2. 默认 1.5 秒后自动平滑消失，杜绝弹窗阻塞打断用户心流。
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

    def show_message(self, message: str, duration_ms: int = 1500):
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


class DeviceComboBox(QComboBox):
    """
    零残影纯原生菜单式设备选择下拉框：
    彻底弃用 Qt 默认的 QComboBoxPrivateContainer (380x127 浮动容器)，
    从根源上 100% 物理消除 Windows DWM 下切换设备或点击服务按钮时产生的 380x127 透明幽灵方框。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._active_menu: Optional[QMenu] = None
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def showPopup(self) -> None:
        """拦截默认 QComboBoxPrivateContainer 弹窗，改用一次性轻量级实体 QMenu 并在关闭后立即销毁"""
        self.hidePopup()
        if self.count() <= 0:
            return

        menu = QMenu(self)
        self._active_menu = menu
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setMinimumWidth(self.width())
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                padding: 4px;
                font-family: 'Segoe UI', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
                background-color: #ffffff;
                color: #0f172a;
            }
            QMenu::item:selected {
                background-color: #e0f2fe;
                color: #0284c7;
                font-weight: 600;
            }
        """)

        actions_map = {}
        curr_idx = self.currentIndex()
        for i in range(self.count()):
            act = menu.addAction(self.itemText(i))
            if i == curr_idx:
                font = act.font()
                font.setBold(True)
                act.setFont(font)
            actions_map[act] = i

        popup_pos = self.mapToGlobal(QPoint(0, self.height() + 2))
        chosen_act = menu.exec(popup_pos)
        self.hidePopup()

        if chosen_act is not None and chosen_act in actions_map:
            target_idx = actions_map[chosen_act]
            if target_idx != self.currentIndex():
                QTimer.singleShot(0, lambda idx=target_idx: self.setCurrentIndex(idx))

    def hidePopup(self) -> None:
        """彻底隐藏并销毁弹出菜单"""
        if self._active_menu is not None:
            try:
                self._active_menu.hide()
                self._active_menu.close()
                self._active_menu.deleteLater()
            except Exception:
                pass
            self._active_menu = None
        super().hidePopup()



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
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setIndentation(13)  # 精致紧凑层级缩进 (对标专业 IDE 规范，彻底消除过宽留白)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setExpandsOnDoubleClick(False)  # 双击节点不展开/收起DOM树，保留前方箭头展开收起

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

        # 悬浮轻量 Toast 提示组件 (1 秒自动消失)
        self.toast = ToastNotification(self)
        self._worker_start_time: float = 0.0

        # 三个核心操作的独立超时守卫定时器 (在 init_ui 之前彻底完成初始化，杜绝任何提前回调导致 AttributeError)
        self._timer_screencast = QTimer(self)
        self._timer_screencast.setSingleShot(True)
        self._timer_screencast.timeout.connect(self._on_screencast_timeout)

        self._timer_sync_screen = QTimer(self)
        self._timer_sync_screen.setSingleShot(True)
        self._timer_sync_screen.timeout.connect(self._on_sync_screen_timeout)

        self._timer_refresh = QTimer(self)
        self._timer_refresh.setSingleShot(True)
        self._timer_refresh.timeout.connect(self._on_refresh_timeout)

        # iOS WDA 服务状态定时探活定时器 (轻量进程扫描，2.5s 周期自愈刷新)
        self.timer_ios_service = QTimer(self)
        self.timer_ios_service.setInterval(2500)
        self.timer_ios_service.timeout.connect(self._on_ios_service_timer_tick)
        self.timer_ios_service.start()

        self.apply_white_luxury_theme()
        self.init_ui()

        # 注册全局 Ctrl+F 快捷键，一键唤醒 DOM 树搜索栏
        self.shortcut_dom_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_dom_search.activated.connect(self.toggle_dom_search)

        self.load_device_list(auto_capture=True)



    def apply_white_luxury_theme(self):
        """采用现代高级纯白 + 极客科技感设计系统 (统一色系、字体、几何边框与交互态)"""
        self.setStyleSheet("""
            /* 全局基础背景与高保真字体中枢 */
            QMainWindow { background-color: #f8fafc; }
            QWidget {
                color: #0f172a;
                font-family: 'Segoe UI', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
                font-size: 12px;
            }

            /* 顶部纯白科技操作栏 (允许折行时自适应撑开高度，禁止 max-height 裁切) */
            QFrame#topBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                min-height: 46px;
            }
            QLabel#topBrand {
                font-weight: 800; color: #0f172a; font-size: 14px; margin-right: 4px;
            }
            QLabel#platformBadge {
                background-color: #e0f2fe; color: #0284c7; font-weight: 700;
                font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bae6fd;
            }

            /* 统一设备选择下拉框 (强制 combobox-popup: 0，禁止创建 Windows Native 浮动窗口，彻底根除透明幽灵框) */
            QComboBox {
                combobox-popup: 0;
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 1px 24px 1px 8px;
                font-weight: 500;
                font-size: 12px;
                min-height: 26px;
                max-height: 30px;
            }
            QComboBox:hover { border-color: #0284c7; }
            QComboBox:focus { border: 1px solid #0284c7; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                selection-background-color: #e0f2fe;
                selection-color: #0284c7;
                padding: 4px;
                outline: none;
            }

            /* 统一模式切换分段按钮 (30px 精致高度，字号 12.5px 加粗，完整不截断) */
            QPushButton.mode-btn {
                background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 8px; font-weight: 600; font-size: 12.5px; min-height: 30px; max-height: 30px;
                text-align: center;
            }
            QPushButton.mode-btn:hover {
                background-color: #f1f5f9; border-color: #0284c7; color: #0284c7;
            }
            QPushButton.mode-btn:checked {
                background-color: #0284c7; color: #ffffff; border: 1px solid #0284c7; font-weight: 700;
            }

            /* 顶部功能操作按钮 (统一 30px 精致规格，字号 12.5px 加粗) */
            QPushButton.action-btn {
                background-color: #ffffff; color: #334155; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 8px; font-weight: 600; font-size: 12.5px; min-height: 30px; max-height: 30px;
                text-align: center;
            }
            QPushButton.action-btn:hover {
                background-color: #f8fafc; border-color: #0284c7; color: #0284c7;
            }
            QPushButton.action-btn:pressed {
                background-color: #f1f5f9;
            }

            /* 次级功能操作按钮 (统一 28px 精致高度，字号 11.5px 加粗，圆角 6px) */
            QPushButton.sub-action-btn {
                background-color: #ffffff; color: #334155; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 8px; font-weight: 600; font-size: 11.5px; min-height: 28px; max-height: 28px;
                text-align: center;
            }
            QPushButton.sub-action-btn:hover {
                background-color: #f1f5f9; border-color: #0284c7; color: #0284c7;
            }
            QPushButton.sub-action-btn:pressed {
                background-color: #e2e8f0;
            }

            /* 分割线与三栏背景容器 (自由拖拽手柄：精致 3px 极细科技设计) */
            QSplitter::handle:horizontal {
                background-color: #e2e8f0; width: 3px; margin: 0px; border-radius: 1px;
            }
            QSplitter::handle:horizontal:hover {
                background-color: #0284c7;
            }
            QFrame.panel-card {
                background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
            }

            /* App Source DOM 树形视图 (紧凑层级排版 + 科技高亮) */
            QTreeWidget {
                background-color: #ffffff; border: 1px solid #e2e8f0;
                border-radius: 6px; padding: 4px; color: #0f172a;
                font-family: 'JetBrains Mono', Consolas, monospace; font-size: 12px;
            }
            QTreeWidget::item {
                min-height: 22px; padding: 1px 4px; border-radius: 4px; margin-bottom: 1px;
            }
            QTreeWidget::item:hover {
                background-color: #f1f5f9; border: 1px solid #cbd5e1;
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
                border-radius: 6px; gridline-color: #f1f5f9; color: #0f172a;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f8fafc; color: #475569; border: none;
                border-bottom: 1px solid #e2e8f0; padding: 6px 10px; font-weight: 700; font-size: 11px;
            }

            /* 统一文本输入框 */
            QLineEdit {
                background-color: #ffffff; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 2px 10px; color: #0f172a;
                font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 12px;
                selection-background-color: #0284c7; selection-color: #ffffff;
            }
            QLineEdit:focus { border: 1px solid #0284c7; }

            /* 面包屑导航栏：支持多行舒展展示 */
            QLabel#breadcrumb {
                background-color: #f8fafc; border: 1px solid #e2e8f0;
                border-radius: 6px; padding: 6px 12px; color: #0284c7;
                font-family: 'JetBrains Mono', Consolas, monospace; font-size: 11px;
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
        # 1. 顶部操作栏 (自适应流式布局：窗口缩小时自动平滑折行，绝不重叠错乱)
        # ----------------------------------------------------------------------
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        top_layout = FlowLayout(top_bar, margin=0, h_spacing=6, v_spacing=6)
        top_layout.setContentsMargins(12, 9, 12, 11)

        # 品牌区：Retina 应用图标 + 品牌名 + 动态系统徽章 (保留上下 2px 呼吸余量防裁切)
        brand_widget = QWidget()
        brand_widget.setMinimumHeight(32)
        brand_widget.setStyleSheet("background: transparent;")
        brand_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(0, 1, 2, 1)
        brand_layout.setSpacing(6)

        lbl_logo = QLabel()
        lbl_logo.setPixmap(create_modern_app_icon().pixmap(22, 22))
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_layout.addWidget(lbl_logo)

        lbl_brand = QLabel("三条 UI 审查器")
        lbl_brand.setObjectName("topBrand")
        lbl_brand.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_layout.addWidget(lbl_brand)

        self.lbl_platform_badge = QLabel("HarmonyOS")
        self.lbl_platform_badge.setObjectName("platformBadge")
        self.lbl_platform_badge.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_layout.addWidget(self.lbl_platform_badge)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(brand_widget)

        # 设备选择组（保留上下 2px 呼吸余量，防止高 DPI 下下拉框边框被下方容器遮挡）
        dev_group = QWidget()
        dev_group.setMinimumHeight(32)
        dev_group.setStyleSheet("background: transparent;")
        dev_group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        dev_layout = QHBoxLayout(dev_group)
        dev_layout.setContentsMargins(0, 1, 2, 1)
        dev_layout.setSpacing(6)
        dev_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_dev = QLabel("设备:")
        lbl_dev.setStyleSheet("color: #64748b; font-weight: 600; font-size: 12.5px;")
        dev_layout.addWidget(lbl_dev)

        self.combo_devices = DeviceComboBox()
        self.combo_devices.setFixedHeight(30)
        self.combo_devices.setFixedWidth(270)
        self.combo_devices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_devices.currentIndexChanged.connect(self.on_device_changed)
        dev_layout.addWidget(self.combo_devices)

        self.btn_refresh_devices = QPushButton()
        self.btn_refresh_devices.setIcon(get_tech_icon("refresh", "#0284c7"))
        self.btn_refresh_devices.setIconSize(QSize(16, 16))
        self.btn_refresh_devices.setToolTip("点击获取并刷新当前已连接的设备列表")
        self.btn_refresh_devices.setProperty("class", "action-btn")
        self.btn_refresh_devices.setFixedSize(30, 30)
        self.btn_refresh_devices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_devices.clicked.connect(self.refresh_devices_action)
        dev_layout.addWidget(self.btn_refresh_devices)
        top_layout.addWidget(dev_group)

        # 统一精致操作按键规格 (96px × 30px，字号 12.5px 加粗，图标 14x14，文字完整不截断)
        BTN_W = 96
        BTN_H = 30

        # 模式切换分段按钮
        self.btn_mode_select = QPushButton("元素审查")
        self.btn_mode_select.setIcon(get_tech_icon("target", "#ffffff"))
        self.btn_mode_select.setIconSize(QSize(14, 14))
        self.btn_mode_select.setProperty("class", "mode-btn")
        self.btn_mode_select.setFixedSize(BTN_W, BTN_H)
        self.btn_mode_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_select.setCheckable(True)
        self.btn_mode_select.setChecked(True)
        self.btn_mode_select.clicked.connect(lambda: self.switch_mode(InspectorMode.SELECT))
        top_layout.addWidget(self.btn_mode_select)

        self.btn_mode_tap = QPushButton("坐标点击")
        self.btn_mode_tap.setIcon(get_tech_icon("tap", "#475569"))
        self.btn_mode_tap.setIconSize(QSize(14, 14))
        self.btn_mode_tap.setProperty("class", "mode-btn")
        self.btn_mode_tap.setFixedSize(BTN_W, BTN_H)
        self.btn_mode_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_tap.setCheckable(True)
        self.btn_mode_tap.clicked.connect(lambda: self.switch_mode(InspectorMode.TAP))
        top_layout.addWidget(self.btn_mode_tap)

        btn_search_modal = QPushButton("查找元素")
        btn_search_modal.setIcon(get_tech_icon("search", "#0284c7"))
        btn_search_modal.setIconSize(QSize(14, 14))
        btn_search_modal.setProperty("class", "action-btn")
        btn_search_modal.setObjectName("btnSearch")
        btn_search_modal.setFixedSize(BTN_W, BTN_H)
        btn_search_modal.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_modal.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_search_modal.clicked.connect(self.open_search_dialog)
        top_layout.addWidget(btn_search_modal)

        # iOS WDA 服务控制按钮 (仅选择 iOS 设备时显示)
        self.btn_ios_service = QPushButton("启动服务")
        self.btn_ios_service.setObjectName("btnIosService")
        self.btn_ios_service.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 严格隔离焦点：被 disabled 禁用或切换时绝不向外部或设备下拉框转移焦点
        self.btn_ios_service.setIcon(get_tech_icon("play", "#475569"))
        self.btn_ios_service.setIconSize(QSize(14, 14))
        self.btn_ios_service.setFixedSize(BTN_W, BTN_H)
        self.btn_ios_service.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ios_service.clicked.connect(self.on_ios_service_btn_clicked)
        self.btn_ios_service.hide()  # 默认隐藏，只有选择 iOS 设备时才显示
        top_layout.addWidget(self.btn_ios_service)

        self.spinner_ios_service = ButtonSpinner(self.btn_ios_service, "refresh", "#0284c7")

        right_actions = QWidget()
        right_actions.setMinimumHeight(BTN_H + 2)
        right_actions.setStyleSheet("background: transparent;")
        right_actions_layout = QHBoxLayout(right_actions)
        right_actions_layout.setContentsMargins(0, 1, 0, 1)
        right_actions_layout.setSpacing(6)
        right_actions_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        btn_copy_xml = QPushButton("复制源码")
        btn_copy_xml.setIcon(get_tech_icon("copy", "#475569"))
        btn_copy_xml.setIconSize(QSize(14, 14))
        btn_copy_xml.setProperty("class", "action-btn")
        btn_copy_xml.setFixedSize(BTN_W, BTN_H)
        btn_copy_xml.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy_xml.clicked.connect(self.copy_xml_source)
        right_actions_layout.addWidget(btn_copy_xml)

        btn_save_shot = QPushButton("保存截图")
        btn_save_shot.setIcon(get_tech_icon("save", "#475569"))
        btn_save_shot.setIconSize(QSize(14, 14))
        btn_save_shot.setProperty("class", "action-btn")
        btn_save_shot.setFixedSize(BTN_W, BTN_H)
        btn_save_shot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save_shot.clicked.connect(self.save_screenshot)
        right_actions_layout.addWidget(btn_save_shot)

        top_layout.addWidgetRight(right_actions)

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

        left_header = FlowLayout(margin=0, h_spacing=6, v_spacing=6)
        lbl_left_title = QLabel("真机实时视窗")
        lbl_left_title.setFixedHeight(28)
        lbl_left_title.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_left_title.setStyleSheet("color: #334155; font-weight: 700; font-size: 13px; padding-right: 4px;")
        left_header.addWidget(lbl_left_title)

        # 统一精致副操作按键规格 (88px × 28px，字号 11.5px 加粗，图标 13x13)
        SUB_BTN_W = 88

        # 实时投屏控制按钮
        self.btn_screencast = QPushButton("实时投屏")
        self.btn_screencast.setIcon(get_tech_icon("cast", "#0284c7"))
        self.btn_screencast.setIconSize(QSize(13, 13))
        self.btn_screencast.setFixedSize(SUB_BTN_W, 28)
        self.btn_screencast.setToolTip("切换真机低延迟实时投屏 (0 截屏广播，完全不触发软件内部截屏通知)")
        self.btn_screencast.setProperty("class", "sub-action-btn")
        self.btn_screencast.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_screencast.clicked.connect(self.toggle_screencast)
        left_header.addWidget(self.btn_screencast)

        self.btn_sync_screen = QPushButton("同步画面")
        self.btn_sync_screen.setIcon(get_tech_icon("sync", "#0284c7"))
        self.btn_sync_screen.setIconSize(QSize(13, 13))
        self.btn_sync_screen.setFixedSize(SUB_BTN_W, 28)
        self.btn_sync_screen.setToolTip("仅极速拉取真机最新画面 (0.05s)，与投屏即刻保持一致")
        self.btn_sync_screen.setProperty("class", "sub-action-btn")
        self.btn_sync_screen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_screen.clicked.connect(self.refresh_screen_only)
        left_header.addWidget(self.btn_sync_screen)

        # 刷新界面按钮
        self.btn_refresh = QPushButton("刷新界面")
        self.btn_refresh.setIcon(get_tech_icon("refresh", "#0284c7"))
        self.btn_refresh.setIconSize(QSize(13, 13))
        self.btn_refresh.setFixedSize(SUB_BTN_W, 28)
        self.btn_refresh.setToolTip("仅刷新 DOM 控件树，保留当前画面底图")
        self.btn_refresh.setProperty("class", "sub-action-btn")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_screen_and_dom)
        left_header.addWidget(self.btn_refresh)

        # 实例化专属 Loading 转圈动画控制器 (无沙漏 emoji，原位 360° 平滑转圈)
        self.spinner_dev_refresh = ButtonSpinner(self.btn_refresh_devices, "refresh", "#0284c7")
        self.spinner_screencast = ButtonSpinner(self.btn_screencast, "cast", "#0284c7")
        self.spinner_sync = ButtonSpinner(self.btn_sync_screen, "sync", "#0284c7")
        self.spinner_refresh = ButtonSpinner(self.btn_refresh, "refresh", "#0284c7")

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
        tree_header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_mid_title = QLabel("ArkUI 组件层级树")
        lbl_mid_title.setStyleSheet("color: #334155; font-weight: 700; font-size: 13.5px;")
        tree_header.addWidget(lbl_mid_title)
        tree_header.addStretch()

        btn_search_dom = QPushButton("搜索 (Ctrl+F)")
        btn_search_dom.setIcon(get_tech_icon("search", "#0284c7"))
        btn_search_dom.setIconSize(QSize(15, 15))
        btn_search_dom.setFixedHeight(30)
        btn_search_dom.setProperty("class", "sub-action-btn")
        btn_search_dom.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_dom.clicked.connect(self.toggle_dom_search)
        tree_header.addWidget(btn_search_dom)

        btn_expand = QPushButton("展开全部")
        btn_expand.setIcon(get_tech_icon("expand", "#475569"))
        btn_expand.setIconSize(QSize(14, 14))
        btn_expand.setFixedHeight(30)
        btn_expand.setProperty("class", "sub-action-btn")
        btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_expand.clicked.connect(lambda: self.tree_widget.expandAll())
        tree_header.addWidget(btn_expand)

        btn_collapse = QPushButton("折叠全部")
        btn_collapse.setIcon(get_tech_icon("collapse", "#475569"))
        btn_collapse.setIconSize(QSize(14, 14))
        btn_collapse.setFixedHeight(30)
        btn_collapse.setProperty("class", "sub-action-btn")
        btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_collapse.clicked.connect(lambda: self.tree_widget.collapseAll())
        tree_header.addWidget(btn_collapse)
        mid_layout.addLayout(tree_header)

        # 面包屑路径 (开启自动换行，绝不单行截断溢出)
        self.lbl_breadcrumb = QLabel("路径: Hierarchy (根节点)")
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

        lbl_s_icon = QLabel()
        lbl_s_icon.setPixmap(get_tech_icon("search", "#0284c7").pixmap(14, 14))
        lbl_s_icon.setStyleSheet("background: transparent; border: none;")
        search_layout.addWidget(lbl_s_icon)

        self.edit_dom_search = QLineEdit()
        self.edit_dom_search.setPlaceholderText("搜索 DOM 标签、ID、文本、属性 (Enter 下一个 / Shift+Enter 上一个 / Esc 关闭)...")
        self.edit_dom_search.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 12px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 1px solid #0284c7;
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
        self.lbl_dom_search_count.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 11px; min-width: 40px; background: transparent; border: none;")
        search_layout.addWidget(self.lbl_dom_search_count)

        btn_prev_match = QPushButton("↑")
        btn_prev_match.setToolTip("上一个匹配项 (Shift+Enter)")
        btn_prev_match.setFixedSize(24, 24)
        btn_prev_match.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prev_match.setStyleSheet("QPushButton { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #0284c7; font-weight: bold; font-size: 12px; } QPushButton:hover { background: #e0f2fe; border-color: #0284c7; }")
        btn_prev_match.clicked.connect(self.on_dom_search_prev)
        search_layout.addWidget(btn_prev_match)

        btn_next_match = QPushButton("↓")
        btn_next_match.setToolTip("下一个匹配项 (Enter)")
        btn_next_match.setFixedSize(24, 24)
        btn_next_match.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_next_match.setStyleSheet("QPushButton { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #0284c7; font-weight: bold; font-size: 12px; } QPushButton:hover { background: #e0f2fe; border-color: #0284c7; }")
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

        # 树视图：开启像素级平滑水平/垂直滚动条，禁用文本省略与自动横向跳动
        self.tree_widget = DOMTreeWidget()
        self.tree_widget.setIndentation(13)
        self.tree_widget.setHeaderLabels([""])  # 留空交由表头自定义工具条统一渲染
        self.tree_widget.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.tree_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_widget.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tree_widget.header().setStretchLastSection(False)
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
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
        self.chk_show_occluded.setChecked(False)
        self.chk_show_occluded.setToolTip("默认隐藏看不见/被遮挡的底层元素；勾选后可查看被遮挡或隐藏的元素")
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

        self.chk_show_full_type = QCheckBox("显示原生完整类型")
        self.chk_show_full_type.setChecked(False)
        self.chk_show_full_type.setToolTip("开启后，iOS 将呈现 XCUIElementTypeLink 等全类名，Android 将呈现 android.widget.TextView 等全类名")
        self.chk_show_full_type.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_show_full_type.setStyleSheet("""
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
        self.chk_show_full_type.stateChanged.connect(self.on_toggle_show_full_type)
        header_bar_layout.addWidget(self.chk_show_full_type)
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

        lbl_sync_title = QLabel("输入框实时调试与下发")
        lbl_sync_title.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px; border: none; background: transparent;")
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

        self.btn_sync_send = QPushButton("实时下发")
        self.btn_sync_send.setIcon(get_tech_icon("send", "#ffffff"))
        self.btn_sync_send.setIconSize(QSize(13, 13))
        self.btn_sync_send.setFixedHeight(30)
        self.btn_sync_send.setFixedWidth(84)
        self.btn_sync_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_send.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; font-weight: 700; border: none; border-radius: 5px; font-size: 11px; padding: 0 4px;"
        )
        self.btn_sync_send.clicked.connect(self.sync_live_input)
        row_sync.addWidget(self.btn_sync_send)

        self.btn_sync_clear = QPushButton("清空")
        self.btn_sync_clear.setIcon(get_tech_icon("clear", "#475569"))
        self.btn_sync_clear.setIconSize(QSize(13, 13))
        self.btn_sync_clear.setFixedHeight(30)
        self.btn_sync_clear.setFixedWidth(60)
        self.btn_sync_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_clear.setStyleSheet(
            "background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1; border-radius: 5px; font-weight: 600; font-size: 11px;"
        )
        self.btn_sync_clear.clicked.connect(self.action_element_clear)
        row_sync.addWidget(self.btn_sync_clear)

        sync_layout.addLayout(row_sync)
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

        lbl_loc_title = QLabel("自动化定位代码推荐 (一键复用)")
        lbl_loc_title.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px; border: none; background: transparent;")
        loc_layout.addWidget(lbl_loc_title)

        grid_loc = QGridLayout()
        grid_loc.setContentsMargins(0, 0, 0, 0)
        grid_loc.setHorizontalSpacing(6)
        grid_loc.setVerticalSpacing(6)

        def _create_loc_row(label_text: str, placeholder: str, row_idx: int):
            lbl = QLabel(label_text)
            lbl.setFixedWidth(56)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("color: #475569; font-weight: 700; font-size: 11px; font-family: 'JetBrains Mono', Consolas, monospace; border: none; background: transparent;")

            txt = QLineEdit()
            txt.setFixedHeight(30)
            txt.setReadOnly(True)
            txt.setStyleSheet("font-size: 12px; padding: 2px 8px; font-family: 'JetBrains Mono', Consolas, monospace;")
            txt.setPlaceholderText(placeholder)

            btn = QPushButton("复制")
            btn.setIcon(get_tech_icon("copy", "#0284c7"))
            btn.setIconSize(QSize(13, 13))
            btn.setFixedHeight(30)
            btn.setFixedWidth(64)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background-color: #ffffff; color: #0284c7; border: 1px solid #bae6fd; border-radius: 5px; font-weight: 700; font-size: 11px; }"
                "QPushButton:hover { background-color: #0284c7; color: #ffffff; border-color: #0284c7; }"
            )
            btn.clicked.connect(lambda: self.copy_to_clip(txt.text()))

            grid_loc.addWidget(lbl, row_idx, 0)
            grid_loc.addWidget(txt, row_idx, 1)
            grid_loc.addWidget(btn, row_idx, 2)
            return txt

        self.txt_loc_id = _create_loc_row("id", "ID 定位代码: (该元素无 ID)", 0)
        self.txt_loc_class_chain = _create_loc_row("chain", "iOS Class Chain 类链表达式", 1)
        self.txt_loc_predicate = _create_loc_row("predicate", "iOS Predicate 谓词表达式", 2)
        self.txt_loc_xpath = _create_loc_row("xpath", "XPath 表达式", 3)
        self.txt_loc_py = _create_loc_row("python", "Python 语句", 4)

        loc_layout.addLayout(grid_loc)
        right_layout.addWidget(loc_box)

        # 详细属性表 (优化默认行高与文本展示，消除上下截断)
        lbl_attr_header = QLabel("详细属性清单 (Attributes)")
        lbl_attr_header.setStyleSheet("color: #334155; font-weight: 700; font-size: 13px; margin-top: 4px;")
        right_layout.addWidget(lbl_attr_header)

        self.table_attrs = QTableWidget()
        self.table_attrs.setColumnCount(2)
        self.table_attrs.setHorizontalHeaderLabels(["属性名称 (Attribute)", "属性值 (Value)"])
        self.table_attrs.setWordWrap(True)
        self.table_attrs.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.table_attrs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_attrs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_attrs.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_attrs.verticalHeader().setMinimumSectionSize(32)
        self.table_attrs.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right_layout.addWidget(self.table_attrs, 1)
        self.splitter.splitterMoved.connect(lambda *_: self.table_attrs.resizeRowsToContents())

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

        if self.combo_devices.count() == 0:
            self.combo_devices.addItem("正在扫描已连接设备...", None)

        self.scan_worker = DeviceScanWorker()
        self.scan_worker.devices_ready.connect(lambda devs: self._on_devices_scanned(devs, auto_capture))
        self.scan_worker.start()

    def _on_devices_scanned(self, devices: List[Dict[str, Any]], auto_capture: bool):
        """异步扫描完成后的主线程无缝回调与智能设备选中"""
        if hasattr(self, "spinner_dev_refresh"):
            self.spinner_dev_refresh.stop()
        if hasattr(self, "btn_refresh_devices"):
            self.btn_refresh_devices.setEnabled(True)

        self.combo_devices.blockSignals(True)
        self.combo_devices.clear()

        if devices:
            target_index = -1
            item_texts = []
            for idx, dev in enumerate(devices):
                item_text = f"[{dev['platform'].upper()}] {dev['name']}"
                item_texts.append(item_text)
                self.combo_devices.addItem(item_text, dev)
                self.combo_devices.setItemData(idx, f"序列号 (UDID): {dev['udid']}\n机型描述: {dev['name']}", Qt.ItemDataRole.ToolTipRole)
                if dev["udid"] == self.current_udid:
                    target_index = idx

            if target_index >= 0:
                self.combo_devices.setCurrentIndex(target_index)
                self.combo_devices.setToolTip(f"当前选中设备 UDID: {self.current_udid}")
                self.update_platform_badge()
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
                    delay_ms = 1200 if was_screencasting else 500
                    QTimer.singleShot(delay_ms, self.refresh_screen_only)
        else:
            self.combo_devices.addItem("未检测到在线设备 (请检查 USB/网络连接)", None)
            self.current_udid = ""
            self.current_platform = "harmony"
            self.combo_devices.setToolTip("未检测到可用在线设备")
            self.update_platform_badge()
            self.combo_devices.blockSignals(False)

    def refresh_devices_action(self):
        """用户点击 [🔄] 按钮，原位图标启动 Loading 360°顺滑转圈，绝无多余按钮与沙漏"""
        if hasattr(self, "spinner_dev_refresh"):
            self.spinner_dev_refresh.start()
        self.load_device_list(auto_capture=False)

    def on_device_changed(self, index: int):
        dev = self.combo_devices.currentData()
        if dev and isinstance(dev, dict):
            new_udid = dev.get("udid", "")
            new_plat = dev.get("platform", "harmony")
            self.combo_devices.setToolTip(f"当前选中设备 UDID: {new_udid}")

            # 切换或选中 iOS 设备时，立即主动检测服务状态并更新按钮
            if new_plat == "ios":
                if hasattr(self, "btn_ios_service"):
                    self.btn_ios_service.show()
                    self.refresh_ios_service_status()
            else:
                if hasattr(self, "btn_ios_service"):
                    self.btn_ios_service.hide()

            if new_udid != self.current_udid or new_plat != self.current_platform:
                was_screencasting = self.is_screencasting
                if self.screencast_worker:
                    old_worker = self.screencast_worker
                    self.stop_screencast()
                    if old_worker.isRunning():
                        old_worker.wait(800)
                # 换机隔离：强力终结旧设备所有残留端口中继 (8100/9100)、释放 RSD 隧道并清理内存帧
                IosWdaManager.kill_relays()
                ScreenCastWorker.release_all_tunnels()
                ScreenCastWorker.clear_cache()
                self.current_screenshot_path = ""
                if hasattr(self, "canvas") and self.canvas is not None:
                    self.canvas.clear_screen()
                self.current_udid = new_udid
                self.current_platform = new_plat
                self.update_platform_badge()
                if was_screencasting:
                    QTimer.singleShot(400, self.start_screencast)
                    QTimer.singleShot(1100, self.refresh_screen_only)
                else:
                    QTimer.singleShot(350, self.refresh_screen_only)

    def update_platform_badge(self):
        """动态更新顶部品牌栏的系统类型胶囊徽章与平台专属控件显隐"""
        if self.current_platform == "harmony":
            self.lbl_platform_badge.setText("HarmonyOS NEXT")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #e0f2fe; color: #0284c7; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bae6fd;"
            )
            if hasattr(self, "btn_ios_service"):
                self.btn_ios_service.hide()
        elif self.current_platform == "android":
            self.lbl_platform_badge.setText("Android")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #dcfce7; color: #16a34a; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bbf7d0;"
            )
            if hasattr(self, "btn_ios_service"):
                self.btn_ios_service.hide()
        elif self.current_platform == "ios":
            self.lbl_platform_badge.setText("iOS")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #f1f5f9; color: #334155; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #cbd5e1;"
            )
            if hasattr(self, "btn_ios_service"):
                self.btn_ios_service.show()
                self.refresh_ios_service_status()

    def refresh_ios_service_status(self, force_state: Optional[str] = None):
        """
        根据底层核心服务运行状态或指定状态动态更新按钮呈现：
        1. running (两者均运行): 文本【正在运行】，背景翠绿高亮；
        2. abnormal (仅单服务存活): 文本【重启服务】，背景警告橙黄 (异常状态)；
        3. stopped (均未运行): 文本【启动服务】，背景白色半透明。
        """
        if not hasattr(self, "btn_ios_service"):
            return
        if force_state is None and getattr(self, "_ios_service_running_action", False):
            return  # 异步任务执行中保持 Loading 态，避免状态抖动

        if force_state in ("running", "abnormal", "stopped"):
            target_state = force_state
        else:
            is_xcuitest, is_forward = check_ios_wda_services()
            if is_xcuitest and is_forward:
                target_state = "running"
            elif is_xcuitest or is_forward:
                target_state = "abnormal"
            else:
                target_state = "stopped"

        if target_state == "running":
            self._ios_service_state = "running"
            self.btn_ios_service.setText("正在运行")
            self.btn_ios_service.setIcon(get_tech_icon("check", "#ffffff"))
            self.btn_ios_service.setToolTip("iOS WDA 自动化服务与 8100 端口正常运行中 (点击可一键停止服务)")
            self.btn_ios_service.setStyleSheet("""
                QPushButton#btnIosService {
                    background-color: #10b981;
                    color: #ffffff;
                    border: 1px solid #059669;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 12.5px;
                    padding: 0 8px;
                }
                QPushButton#btnIosService:hover {
                    background-color: #059669;
                }
                QPushButton#btnIosService:disabled {
                    background-color: #6ee7b7;
                    color: #f0fdf4;
                }
            """)
        elif target_state == "abnormal":
            self._ios_service_state = "abnormal"
            self.btn_ios_service.setText("重启服务")
            self.btn_ios_service.setIcon(get_tech_icon("refresh", "#ffffff"))
            self.btn_ios_service.setToolTip("检测到仅单项子服务运行 (状态异常)，点击一键停止并重启 WDA 服务")
            self.btn_ios_service.setStyleSheet("""
                QPushButton#btnIosService {
                    background-color: #f59e0b;
                    color: #ffffff;
                    border: 1px solid #d97706;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 12.5px;
                    padding: 0 8px;
                }
                QPushButton#btnIosService:hover {
                    background-color: #d97706;
                }
                QPushButton#btnIosService:disabled {
                    background-color: #fcd34d;
                    color: #fffbeb;
                }
            """)
        else:
            self._ios_service_state = "stopped"
            self.btn_ios_service.setText("启动服务")
            self.btn_ios_service.setIcon(get_tech_icon("play", "#475569"))
            self.btn_ios_service.setToolTip("点击一键启动 iOS WDA 守护进程与 8100 端口透传")
            self.btn_ios_service.setStyleSheet("""
                QPushButton#btnIosService {
                    background-color: rgba(255, 255, 255, 0.9);
                    color: #334155;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 12.5px;
                    padding: 0 8px;
                }
                QPushButton#btnIosService:hover {
                    background-color: #f1f5f9;
                    border-color: #94a3b8;
                    color: #0f172a;
                }
                QPushButton#btnIosService:disabled {
                    background-color: #f8fafc;
                    color: #94a3b8;
                }
            """)

    def _on_ios_service_timer_tick(self):
        """轻量定时探活：仅在选择 iOS 设备且未执行异步任务时周期性同步状态"""
        if self.current_platform != "ios":
            return
        if not hasattr(self, "btn_ios_service") or not self.btn_ios_service.isVisible():
            return
        if getattr(self, "_ios_service_running_action", False):
            return
        self.refresh_ios_service_status()

    def on_ios_service_btn_clicked(self):
        """iOS 服务控制按钮点击事件 (智能派发启动/重启或停止操作)"""
        if getattr(self, "_ios_service_running_action", False):
            return

        if hasattr(self, "toast") and self.toast:
            self.toast.hide()

        current_state = getattr(self, "_ios_service_state", "stopped")

        if current_state == "running":
            action = "stop"
            loading_text = "正在停止..."
        else:
            action = "start_or_restart"
            loading_text = "正在启动..."

        self._ios_service_running_action = True
        self.setFocus()  # 将键盘焦点收回主窗口，彻底阻断禁用按钮引起的焦点回退至设备下拉框
        self.btn_ios_service.setEnabled(False)

        # 启动 360° Loading 转圈动画
        if hasattr(self, "spinner_ios_service"):
            if current_state in ("running", "abnormal"):
                self.spinner_ios_service.icon_color = "#ffffff"
            else:
                self.spinner_ios_service.icon_color = "#0284c7"
            self.spinner_ios_service.start(loading_text)

        self._ios_service_worker = IosServiceActionWorker(action, parent=self)
        self._ios_service_worker.finished_sig.connect(self._on_ios_service_action_finished)
        self._ios_service_worker.start()

    def _on_ios_service_action_finished(self, success: bool, message: str, action: str = ""):
        """服务操作完成回调：停止转圈，直接刷新按钮状态，弹出高质感轻量 Toast 提示"""
        self._ios_service_running_action = False

        if hasattr(self, "spinner_ios_service"):
            self.spinner_ios_service.stop(restore_text=False)
        self.btn_ios_service.setEnabled(True)

        if action == "stop":
            self.refresh_ios_service_status(force_state="stopped")
            self.show_toast("✅ 服务已停止", duration_ms=1500)
        else:
            if success:
                self.refresh_ios_service_status(force_state="running")
                self.show_toast("✅ 服务已启动", duration_ms=1500)
            else:
                self.refresh_ios_service_status() 
                self.show_toast("⚠️ 服务启动未完全就绪，请重试", duration_ms=2000)

    def refresh_screen_and_dom(self):
        """
        刷新界面按钮点击处理：
        仅刷新 DOM 控件树，保留当前真机画面底图 (零截屏广播通知，30~50ms 极速响应，带 12s 超时防死锁机制)
        """
        if not self.current_udid:
            ModernMessageBox.warning(self, "设备未连接", "未检测到在线移动设备，请确认开启 USB 调试并连接设备。")
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
                self.show_toast("⏳ 上一轮刷新仍在进行中，请稍候...", duration_ms=1200)
                return

        self._worker_start_time = time.time()
        self.btn_refresh.setEnabled(False)
        if hasattr(self, "spinner_refresh"):
            self.spinner_refresh.start(loading_text="正在刷新...")
        else:
            self.btn_refresh.setText("正在刷新...")
        self._timer_refresh.start(20000)

        project_root = SmartPathResolver.get_project_root()
        tmp_dir = os.path.normpath(os.path.abspath(os.path.join(project_root, "reports", "inspector")))
        os.makedirs(tmp_dir, exist_ok=True)

        # 核心：纯 DOM 刷新模式，不抓取/刷新画面，保留当前画面底图
        self.capture_worker = CaptureWorker(self.current_udid, self.current_platform, tmp_dir, mode="dom_only")
        self.capture_worker.dom_finished.connect(self.on_dom_only_success)
        self.capture_worker.failed.connect(self.on_capture_failed)
        self.capture_worker.start()

    def _reset_capture_buttons(self):
        """重置同步真机画面与刷新界面按钮状态，停止 Loading 转圈动画"""
        self._timer_sync_screen.stop()
        self._timer_refresh.stop()
        if hasattr(self, "spinner_sync"):
            self.spinner_sync.stop(restore_text=True)
        elif hasattr(self, "btn_sync_screen"):
            self.btn_sync_screen.setEnabled(True)
            self.btn_sync_screen.setText("同步画面")

        if hasattr(self, "spinner_refresh"):
            self.spinner_refresh.stop(restore_text=True)
        elif hasattr(self, "btn_refresh"):
            self.btn_refresh.setEnabled(True)
            self.btn_refresh.setText("刷新界面")

    def _on_sync_screen_timeout(self):
        """同步真机画面超时回调"""
        logging.warning("[UI审查器] 同步真机画面超时 (20s)")
        if self.capture_worker and self.capture_worker.isRunning():
            try:
                self.capture_worker.terminate()
            except Exception:
                pass
            self.capture_worker = None
        self._reset_capture_buttons()
        self.show_toast("⚠️ 同步真机画面超时 (20s)，已重置状态")

    def _on_refresh_timeout(self):
        """刷新界面超时回调"""
        logging.warning("[UI审查器] 刷新界面超时 (20s)")
        if self.capture_worker and self.capture_worker.isRunning():
            try:
                self.capture_worker.terminate()
            except Exception:
                pass
            self.capture_worker = None
        self._reset_capture_buttons()
        self.show_toast("⚠️ 刷新界面超时 (20s)，已重置状态")

    def _on_screencast_timeout(self):
        """开启实时投屏超时回调"""
        logging.warning("[UI审查器] 开启实时投屏超时 (15s)")
        self.stop_screencast()
        self._timer_screencast.stop()
        self._update_screencast_btn_style(False)
        self.show_toast("⚠️ 开启实时投屏超时 (15s)，投屏通道未响应，已自动复位")

    @staticmethod
    def _resolve_layout_viewport_size(local_png: str, layout_file: str, platform: str) -> Tuple[int, int]:
        """统一计算各平台 DOM 树与画布对齐基准尺寸 (iOS 使用原生逻辑点并裁剪 DVT 黑边)"""
        if platform == "ios":
            logical_size = normalize_ios_screenshot_file(local_png, layout_file)
            if logical_size:
                return logical_size
            return 390, 844

        phys_w, phys_h = get_layout_physical_size(layout_file, 1084, 2412)
        pix = QPixmap(local_png) if (local_png and os.path.exists(local_png)) else QPixmap()
        if not pix.isNull() and pix.width() >= 800 and pix.height() >= 1200:
            return pix.width(), pix.height()
        return phys_w, phys_h

    def on_dom_only_success(self, layout_file: str, platform: str):
        """对齐 HoKit UIViewer 叠加层机制：仅更新 DOM 组件树，复用当前底图与缩放比例 (零截屏/零系统广播)"""
        self._reset_capture_buttons()
        local_png = self.current_screenshot_path

        try:
            prev_selected_id = self.canvas.selected_node_id
            screen_w, screen_h = self._resolve_layout_viewport_size(local_png, layout_file, platform)
            # 若历史缓存底图刚被去黑边裁剪过，同步刷新画布底图以免残留旧黑边比例
            if platform == "ios" and local_png and os.path.exists(local_png) and not self.is_screencasting:
                self.canvas.update_screen_pixmap(QPixmap(local_png), keep_components=True)

            raw_tree = parse_layout_file(layout_file, platform, screen_w=screen_w, screen_h=screen_h)

            self.clear_dom_search_highlights()
            self.flat_components.clear()
            self.comp_map.clear()
            self.tree_item_map.clear()
            self.tree_widget.clear()
            self.node_counter = 0

            # 全局模态弹窗预检测：检查整机当前是否展示了处于活跃状态且具备真实几何尺寸的模态弹窗
            def find_active_dialogs(n: Dict[str, Any]) -> bool:
                a = n.get("attributes", {})
                t = a.get("type", "")
                vis = str(a.get("visible", "true")).lower() != "false"
                if t in ("Dialog", "CustomDialog", "ActionSheet", "AlertDialog", "Popup") and vis:
                    b_str = a.get("bounds", "")
                    m_b = re.match(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", b_str)
                    if m_b:
                        w = int(m_b.group(3)) - int(m_b.group(1))
                        h = int(m_b.group(4)) - int(m_b.group(2))
                        # 必须满足有效物理展示尺寸 (>=100x100) 且子节点不为空，杜绝空结构常驻误判
                        if w >= 100 and h >= 100 and len(n.get("children", [])) > 0:
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

            # 全树构建完成后，依据当前复选框状态统一进行一次自底向上可见性保护同步 (防断枝误杀)
            show_occluded = self.chk_show_occluded.isChecked() if hasattr(self, "chk_show_occluded") else False
            self.apply_occluded_visibility_to_tree(show_occluded)

            # 仅刷新组件层级，保留当前画布底图与缩放视口，并严格锁定同一套坐标基准 (screen_w, screen_h)
            self.canvas.update_components_only(self.flat_components, layout_size=(screen_w, screen_h))
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
            screen_w, screen_h = self._resolve_layout_viewport_size(local_png, layout_file, platform)

            raw_tree = parse_layout_file(layout_file, platform, screen_w=screen_w, screen_h=screen_h)

            self.clear_dom_search_highlights()
            self.flat_components.clear()
            self.comp_map.clear()
            self.tree_item_map.clear()
            self.tree_widget.clear()
            self.node_counter = 0

            # 全局模态弹窗预检测：检查整机当前是否展示了处于活跃状态且具备真实几何尺寸的模态弹窗
            def find_active_dialogs(n: Dict[str, Any]) -> bool:
                a = n.get("attributes", {})
                t = a.get("type", "")
                vis = str(a.get("visible", "true")).lower() != "false"
                if t in ("Dialog", "CustomDialog", "ActionSheet", "AlertDialog", "Popup") and vis:
                    b_str = a.get("bounds", "")
                    m_b = re.match(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", b_str)
                    if m_b:
                        w = int(m_b.group(3)) - int(m_b.group(1))
                        h = int(m_b.group(4)) - int(m_b.group(2))
                        # 必须满足有效物理展示尺寸 (>=100x100) 且子节点不为空，杜绝空结构常驻误判
                        if w >= 100 and h >= 100 and len(n.get("children", [])) > 0:
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

            # 全树构建完成后，依据当前复选框状态统一进行一次自底向上可见性保护同步 (防断枝误杀)
            show_occluded = self.chk_show_occluded.isChecked() if hasattr(self, "chk_show_occluded") else False
            self.apply_occluded_visibility_to_tree(show_occluded)

            # 工业级高保真视窗装载：装载底图与组件，并严格锁定解析 DOM 所用的坐标基准 (screen_w, screen_h)
            if is_real_shot:
                self.canvas.load_screenshot(local_png, self.flat_components, layout_size=(screen_w, screen_h))
            elif (
                ScreenCastWorker.latest_udid == self.current_udid
                and ScreenCastWorker.latest_image is not None
                and not ScreenCastWorker.latest_image.isNull()
            ):
                cast_img = (
                    crop_ios_dvt_image(ScreenCastWorker.latest_image, (screen_w, screen_h))
                    if platform == "ios"
                    else ScreenCastWorker.latest_image
                )
                mem_pix = QPixmap.fromImage(cast_img)
                self.canvas.update_screen_pixmap(mem_pix, keep_components=False)
                self.canvas.update_components_only(self.flat_components, layout_size=(screen_w, screen_h))
            elif os.path.exists(local_png):
                self.canvas.load_screenshot(local_png, self.flat_components, layout_size=(screen_w, screen_h))

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
        # 若当前正在执行 iOS 服务的启停/重启操作，静默忽略过渡期的连接失败，绝不弹窗打扰
        if getattr(self, "_ios_service_running_action", False):
            return
        if self.current_platform == "ios":
            self.show_toast(f"📱 iOS 提示: {err_msg}")
            return
        ModernMessageBox.critical(self, "抓取失败", f"无法获取设备现场界面与布局:\n{err_msg}")

    def refresh_screen_only(self):
        """
        同步真机画面按钮点击处理：
        同时刷新真机画面与 DOM 树 (对齐用户诉求：全量同步最新现场，带 12s 超时防死锁机制)
        """
        if not self.current_udid:
            ModernMessageBox.warning(self, "设备未连接", "未检测到在线设备，请先连接并选中设备。")
            return

        if self.capture_worker and self.capture_worker.isRunning():
            if getattr(self, "_worker_start_time", 0) and (time.time() - self._worker_start_time > 8):
                try:
                    self.capture_worker.terminate()
                    self.capture_worker.wait(500)
                except Exception:
                    pass
            else:
                self.show_toast("⏳ 任务正在执行中，请勿重复点击", duration_ms=1200)
                return

        self._worker_start_time = time.time()
        project_root = SmartPathResolver.get_project_root()
        tmp_dir = os.path.normpath(os.path.abspath(os.path.join(project_root, "reports", "inspector")))
        os.makedirs(tmp_dir, exist_ok=True)

        # iOS 协同：若投屏活跃中，优先直接从内存取帧刷新；若未开启投屏，则通过 CaptureWorker 极速获取物理真机原画
        if self.current_platform == "ios":
            if self.is_screencasting or ScreenCastWorker.is_active:
                mem_bytes = ScreenCastWorker.get_latest_jpeg_bytes(self.current_udid)
                if mem_bytes:
                    try:
                        shot_path = os.path.join(tmp_dir, "screencast_last_ios.jpeg")
                        with open(shot_path, "wb") as f_s:
                            f_s.write(mem_bytes)
                        self.current_screenshot_path = shot_path
                    except Exception:
                        pass

        self.btn_sync_screen.setEnabled(False)
        if hasattr(self, "spinner_sync"):
            self.spinner_sync.start(loading_text="正在同步...")
        else:
            self.btn_sync_screen.setText("正在同步...")
        self._timer_sync_screen.start(20000)

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
        """启动后台低延迟实时投屏流 (iOS 优选 pymobiledevice3 引擎，鸿蒙/安卓原生流引擎，带 15s 超时防死锁)"""
        if not self.current_udid:
            ModernMessageBox.warning(self, "设备未连接", "未检测到在线设备，请先连接并选中设备。")
            return

        self.btn_screencast.setEnabled(False)
        if hasattr(self, "spinner_screencast"):
            self.spinner_screencast.start(loading_text="连接中...")
        else:
            self.btn_screencast.setText("连接中...")
        self._timer_screencast.start(15000)

        # 1. 抓取与投屏互斥治理：若当前有抓取工作线程正在运行，立即断开其信号并停止，避免与投屏争抢 USB 隧道
        if hasattr(self, "capture_worker") and self.capture_worker and self.capture_worker.isRunning():
            try:
                self.capture_worker.finished.disconnect()
            except Exception:
                pass
            try:
                self.capture_worker.screen_finished.disconnect()
            except Exception:
                pass
            try:
                self.capture_worker.dom_finished.disconnect()
            except Exception:
                pass
            try:
                self.capture_worker.failed.disconnect()
            except Exception:
                pass
            self.capture_worker.quit()
            self.capture_worker.wait(300)

        # 2. 换设备安全自愈：对已存在的旧 worker 彻底切断所有 Qt 信号连接，并真正等待其结束退出
        if self.screencast_worker:
            old_w = self.screencast_worker
            self.screencast_worker = None
            try:
                old_w.frame_ready.disconnect()
            except Exception:
                pass
            try:
                old_w.state_changed.disconnect()
            except Exception:
                pass
            try:
                old_w.error_occurred.disconnect()
            except Exception:
                pass
            old_w.stop()
            if old_w.isRunning():
                old_w.wait(1500)

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
            try:
                worker.frame_ready.disconnect(self.on_screencast_frame)
                worker.state_changed.disconnect(self.on_screencast_state_changed)
                worker.error_occurred.disconnect(self.on_screencast_error)
            except Exception:
                pass
            worker.stop()
            # 异步延时回收线程并释放中继端口
            def _async_cleanup():
                worker.wait(500)
                IosWdaManager.kill_relays()
            QTimer.singleShot(0, _async_cleanup)
        else:
            IosWdaManager.kill_relays()

    def on_screencast_frame(self, image: QImage, raw_bytes: bytes):
        """收到最新一帧投屏画面：实时更新画布 (100% 显存/内存直通，零磁盘 I/O 阻塞主线程)"""
        try:
            if not image or image.isNull():
                return
            if not self.is_screencasting:
                self.is_screencasting = True
                self._timer_screencast.stop()
                self._update_screencast_btn_style(True)
            elif self._timer_screencast.isActive():
                self._timer_screencast.stop()

            # iOS DVT 实时投屏若包含字节对齐黑边，渲染前按当前逻辑分辨率等比裁剪干净
            if self.current_platform == "ios" and 250 <= self.canvas.layout_w <= 700 and 400 <= self.canvas.layout_h <= 1400:
                image = crop_ios_dvt_image(image, (self.canvas.layout_w, self.canvas.layout_h))

            # 内存直通渲染 QImage，彻底免去主线程 QPixmap.fromImage(image) 额外 CPU 耗时，切屏零卡顿
            self.canvas.update_screen_image(image, keep_components=True)

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
        finally:
            # 释放生产者流控门阀，允许 Worker 线程继续生成或调度下一帧，彻底消除 Qt 事件队列积压
            if self.screencast_worker:
                self.screencast_worker.ui_ready = True

    def on_screencast_state_changed(self, is_running: bool, msg: str):
        """投屏通道状态变更通知"""
        if is_running:
            self._timer_screencast.stop()
            self.is_screencasting = True
            self._update_screencast_btn_style(True)
            self.show_toast("✅ 实时投屏已启动 (零截屏通知/低延迟硬件流)")
        else:
            self._timer_screencast.stop()
            self.is_screencasting = False
            self._update_screencast_btn_style(False)

    def on_screencast_error(self, err_msg: str):
        """投屏异常处理"""
        self._timer_screencast.stop()
        self.is_screencasting = False
        self._update_screencast_btn_style(False)
        self.show_toast(f"⚠️ 投屏提示: {err_msg}", duration_ms=4500)

    def _update_screencast_btn_style(self, is_running: bool):
        """动态更新实时投屏控制按钮视觉呈现"""
        if not hasattr(self, "btn_screencast"):
            return
        if hasattr(self, "spinner_screencast"):
            self.spinner_screencast.stop(restore_text=False)
        self.btn_screencast.setEnabled(True)
        if is_running:
            self.btn_screencast.setText("停止投屏")
            self.btn_screencast.setIcon(get_tech_icon("cast", "#ef4444"))
            self.btn_screencast.setStyleSheet(
                "QPushButton { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 5px; "
                "color: #dc2626; font-size: 11px; font-weight: 700; padding: 0 10px; min-height: 26px; } "
                "QPushButton:hover { background: #fee2e2; border-color: #ef4444; }"
            )
        else:
            self.btn_screencast.setText("实时投屏")
            self.btn_screencast.setIcon(get_tech_icon("cast", "#0284c7"))
            self.btn_screencast.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px; "
                "color: #334155; font-size: 11px; font-weight: 600; padding: 0 10px; min-height: 26px; } "
                "QPushButton:hover { background: #f1f5f9; border-color: #0284c7; color: #0284c7; }"
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
        full_type = attrs.get("full_type") or attrs.get("class") or c_type
        if self.current_platform == "ios" and not full_type.startswith("XCUIElementType"):
            full_type = f"XCUIElementType{c_type}"
        elif self.current_platform == "android" and "." not in full_type and attrs.get("class"):
            full_type = attrs.get("class")

        c_id = attrs.get("id") or attrs.get("resource-id") or attrs.get("key") or ""
        if self.current_platform == "ios" and not c_id:
            c_id = attrs.get("name") or attrs.get("label") or ""
        c_text = attrs.get("text") or attrs.get("label") or attrs.get("originalText") or ""

        # 1. 深度综合判定组件自身的可见性属性 (全面覆盖鸿蒙 ArkUI、Android 与 iOS)
        raw_visible = str(attrs.get("visible", "")).strip().lower()
        raw_visibility = str(attrs.get("visibility", "")).strip().lower()
        is_hidden_attr = str(attrs.get("hidden", "")).lower() in ("true", "1") or str(attrs.get("isHidden", "")).lower() in ("true", "1")
        # 鸿蒙 ArkUI 专属：visibility (None / Hidden / Visible，或数字 0=Visible, 1=Hidden, 2=None)
        is_visibility_hidden = raw_visibility in ("none", "hidden", "2", "1")
        is_explicitly_invisible = raw_visible in ("false", "0") or is_visibility_hidden or is_hidden_attr

        is_visible = not is_explicitly_invisible
        try:
            opacity = float(attrs.get("opacity", attrs.get("alpha", "1.0")))
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
        # 特例豁免：移动端验证码/PIN密码/聊天输入框等，具备完整的点击聚焦与输入能力，必须被视为有效交互与展示节点！
        ctrl_min = 8 if self.current_platform == "ios" else 15
        is_transparent_input = (
            c_type in ("TextInput", "TextArea", "SearchField", "TextField", "TextView", "EditText")
            or full_type in ("XCUIElementTypeTextView", "XCUIElementTypeTextField", "XCUIElementTypeSecureTextField", "XCUIElementTypeSearchField")
            or c_type.endswith("Input")
            or c_type.endswith("Field")
        ) and is_visible and width >= ctrl_min and height >= ctrl_min
        node_visible = parent_visible and is_visible and (opacity > 0.05 or is_transparent_input)
        if not node_in_active_page:
            node_visible = False

        # 核心图形学与几何实体遮挡判定 (Geometry Occlusion & Hit-Test)
        # 1. 纯透明布局容器（如 Row, Column, Stack, Flex, RelativeContainer 等且有子节点）本身不绘制实体背景像素，
        #    其自身遮挡状态由其子节点自底向上聚合决定，绝不能因容器外框与上方实体相交而判定整行/整列容器被遮挡！
        ARKUI_CONTAINER_TYPES = (
            "Row", "Column", "Stack", "Flex", "RelativeContainer", "__Common__",
            "List", "ListItem", "ListItemGroup", "Scroll", "Grid", "GridRow", "GridCol", "GridItem",
            "Swiper", "WaterFlow", "FlowItem", "Refresh", "Navigation", "NavDestination",
            "NavDestinationContent", "NavRouter", "Tabs", "TabContent", "SideBarContainer", "Panel",
            "root", "Component", "Page", "Window", "Stage", "Ability", "Hierarchy", "UIComponent",
            "View", "ViewGroup", "FrameLayout", "LinearLayout", "RelativeLayout",
            "XCUIElementTypeWindow", "XCUIElementTypeOther", "XCUIElementTypeApplication", "Other"
        )
        has_child_nodes = len(node.get("children", [])) > 0
        is_transparent_container = (
            c_type in ARKUI_CONTAINER_TYPES
            or c_type.lower() in ("root", "component", "page", "window", "stage", "ability", "hierarchy", "uicomponent")
            or c_type.endswith("Container")
            or c_type.endswith("Layout")
            or c_type.endswith("Group")
            or (has_child_nodes and c_type not in (
                "Text", "Button", "TextInput", "Image", "TextArea", "Toggle", "Checkbox",
                "Radio", "Slider", "Progress", "LoadingProgress", "DatePicker", "TimePicker", "TextView", "TextField"
            ))
        ) and has_child_nodes

        # 模态弹窗排他性规则 (Modal Dialog Exclusivity)
        is_dialog_root = c_type in ("Dialog", "CustomDialog", "ActionSheet", "AlertDialog", "Popup")
        current_is_dialog = is_in_dialog or is_dialog_root
        # 顶层应用视窗骨架保护：根节点与一级容器绝不可被误判为遮挡，确保 DOM 树结构永不坍塌
        is_top_level_skeleton = depth <= 1 or c_type in ("Hierarchy", "root", "Component", "Page", "WindowScene", "XCUIElementTypeWindow")

        if is_top_level_skeleton:
            is_node_occluded = False
        elif is_dialog_root:
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
            total_inter_area = 0
            for c_l, c_t, c_r, c_b in covering_rects:
                # 规则 1: 遮挡物覆盖了该组件的几何中心交互点 (交互点击命中区)
                if c_l <= center_x <= c_r and c_t <= center_y <= c_b:
                    is_node_occluded = True
                    break
                # 规则 2: 累积重叠面积计算 (支持多个图层/小图标聚合覆盖，彻底根治气泡内多个表情覆盖背景图片的问题)
                inter_l = max(left, c_l)
                inter_t = max(top, c_t)
                inter_r = min(right, c_r)
                inter_b = min(bottom, c_b)
                if inter_r > inter_l and inter_b > inter_t:
                    inter_area = (inter_r - inter_l) * (inter_b - inter_t)
                    total_inter_area += inter_area
                    if inter_area / node_area >= 0.50:
                        is_node_occluded = True
                        break
            if not is_node_occluded and node_area > 0 and (total_inter_area / node_area >= 0.40):
                is_node_occluded = True

        # 3. 针对无文字、无描述、不可交互且纯属底层占位/背景缝隙的退化节点深度过滤
        is_clickable_comp = str(attrs.get("clickable", "false")).lower() in ("true", "1") or str(attrs.get("longClickable", "false")).lower() in ("true", "1")
        has_content = bool(c_text or c_id or attrs.get("description") or attrs.get("content-desc") or is_clickable_comp)

        # 极细缝隙组件 (空占位容器) 判定为已遮挡/未暴露层
        gap_min = 3 if self.current_platform == "ios" else 8
        if (width <= gap_min or height <= gap_min) and not has_content and depth > 0:
            is_node_occluded = True

        # 针对 Image 组件：若没有文字、没有 ID、没有描述且不可点击，且其处于 Stack 内部存在实心覆盖物时，判定为已遮挡背景层
        if c_type == "Image" and not has_content and covering_rects:
            is_node_occluded = True

        # 核心免疫防护：输入框与输入表单组件 (TextView, TextField, TextInput 等) 无论是否带文字，
        # 均属于最核心的用户交互热区，绝不允许被外层背景边框或兄弟布局图层误判为已遮挡！
        is_interactive_form_control = (
            c_type in ("TextView", "TextField", "TextInput", "TextArea", "SearchField", "EditText", "Button")
            or full_type in ("XCUIElementTypeTextView", "XCUIElementTypeTextField", "XCUIElementTypeSecureTextField", "XCUIElementTypeButton", "XCUIElementTypeSearchField")
            or c_type.endswith("Input")
            or c_type.endswith("Field")
        )
        if is_interactive_form_control and width >= ctrl_min and height >= ctrl_min and is_visible:
            is_node_occluded = False

        is_exposed = node_visible and (not is_node_occluded)
        is_node_exposed = is_exposed and node_in_active_page

        # 判定当前节点是否属于被遮挡/隐藏层
        is_occluded_node = (not is_node_exposed) and depth > 0

        # 屏幕视口相交判定 (Viewport In-Screen Check):
        # 排除完全滚出真机视口之外的离屏组件 (iOS 按原生逻辑视口校准，Android/鸿蒙按物理像素视口校准)
        if self.current_platform == "ios":
            vw = screen_w if screen_w >= 250 else 390
            vh = screen_h if screen_h >= 400 else 844
            plain_min, content_min = 4, 2
        else:
            vw = screen_w if screen_w >= 800 else 1084
            vh = screen_h if screen_h >= 1200 else 2412
            plain_min, content_min = 10, 4
        is_in_viewport = not (right <= 0 or left >= vw or bottom <= 0 or top >= vh)
        # 核心优化：画布交互拾取仅限真实暴露在顶层的有效组件 (is_exposed) 且排除微细占位
        is_valid_size = (width >= plain_min and height >= plain_min) if not has_content else (width >= content_min and height >= content_min)
        if is_interactive_form_control and width >= ctrl_min and height >= ctrl_min:
            is_interactive = node_in_active_page and (not is_node_occluded) and is_in_viewport
        else:
            is_interactive = node_in_active_page and is_exposed and is_in_viewport and is_valid_size

        node_xpath = f"{current_xpath}/{c_type}"
        
        # 智能推荐定位器代码 (区分鸿蒙、安卓与 iOS 权威最佳实践)
        rec_id = c_id if c_id else ""
        rec_predicate = ""
        rec_class_chain = ""
        if self.current_platform == "android":
            if c_id:
                rec_xpath = f"//*[@resource-id='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
            elif c_text:
                rec_xpath = f"//{full_type}[@text='{c_text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{full_type}[@text='{c_text}']\")"
            else:
                rec_xpath = node_xpath
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"
            rec_predicate = f'text == "{c_text}"' if c_text else ""
            rec_class_chain = ""
        elif self.current_platform == "ios":
            ios_val = attrs.get("value") or ""
            if c_id:
                rec_xpath = f"//{full_type}[@name='{c_id}']"
                rec_predicate = f'type == "{full_type}" AND name == "{c_id}"'
                rec_class_chain = f'**/{full_type}[`name == "{c_id}"`]'
                rec_py = f"driver.find_element(AppiumBy.ACCESSIBILITY_ID, '{c_id}')"
            elif c_text:
                rec_xpath = f"//{full_type}[@label='{c_text}']"
                rec_predicate = f'type == "{full_type}" AND (label == "{c_text}" OR name == "{c_text}")'
                rec_class_chain = f'**/{full_type}[`label == "{c_text}"`]'
                rec_py = f"driver.find_element(AppiumBy.IOS_PREDICATE, '{rec_predicate}')"
            elif ios_val:
                rec_xpath = f"//{full_type}[@value='{ios_val}']"
                rec_predicate = f'type == "{full_type}" AND value == "{ios_val}"'
                rec_class_chain = f'**/{full_type}[`value == "{ios_val}"`]'
                rec_py = f"driver.find_element(AppiumBy.IOS_PREDICATE, '{rec_predicate}')"
            else:
                rec_xpath = f"//{full_type}" if full_type else node_xpath
                rec_predicate = f'type == "{full_type}"'
                rec_class_chain = f'**/{full_type}'
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
            rec_predicate = ""
            rec_class_chain = ""
        comp = {
            "node_id": node_id,
            "type": c_type,
            "full_type": full_type,
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
            "rec_predicate": rec_predicate,
            "rec_class_chain": rec_class_chain,
            "rec_id": rec_id,
            "rec_py": rec_py,
            "rec_class": full_type,
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

        # 安全清洗并生成标准 XML 标签与属性字典 (iOS 优先使用原生全称 XCUIElementType...)
        target_tag = full_type if (self.current_platform == "ios" or (self.current_platform == "android" and "." not in full_type)) else c_type
        safe_tag = re.sub(r'[^a-zA-Z0-9_\-]', '', target_tag) or "Component"
        if safe_tag[0].isdigit() or safe_tag[0] == '-':
            safe_tag = f"comp_{safe_tag}"

        clean_xml_attrs = {
            "node_id": node_id,
            "id": c_id,
            "text": c_text,
            "type": c_type,
            "full_type": full_type,
            "short_type": c_type,
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

        # 高颜值彩色节点标签渲染 (支持精炼视图 / 原生全类名双模切换)
        is_full_mode = self.chk_show_full_type.isChecked() if hasattr(self, "chk_show_full_type") else False
        display_type = full_type if is_full_mode else c_type
        type_badge = f"<{display_type}"
        attrs_str = ""
        if self.current_platform == "ios":
            ios_name = attrs.get("name") or attrs.get("id") or ""
            ios_label = attrs.get("label") or ""
            ios_value = attrs.get("value") or ""
            if ios_value:
                attrs_str += f' value="{ios_value}"'
            if ios_name:
                attrs_str += f' name="{ios_name}"'
            if ios_label and ios_label != ios_value:
                attrs_str += f' label="{ios_label}"'
        else:
            if c_id:
                attrs_str += f' id="{c_id}"'
            if c_text:
                attrs_str += f' text="{c_text}"'
        attrs_str += f' bounds="{bounds_str}"'
        if is_occluded_node:
            attrs_str += ' occluded="true"'
        attrs_str += '>'
        item = QTreeWidgetItem([f"{type_badge}{attrs_str}"])
        item.setData(0, Qt.ItemDataRole.UserRole, node_id)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, bool(is_occluded_node))
        item.setToolTip(0, f"原生全类名: {full_type}\n精炼类型: {c_type}\n边界范围: {bounds_str}")

        # 统一为各组件类型专属的高颜值莫兰迪配色 (被遮挡元素使用优雅弱化浅灰调)
        if is_occluded_node:
            item.setForeground(0, QColor("#94a3b8"))
            item.setBackground(0, QBrush(QColor("#f8fafc")))
        else:
            scheme = get_dom_tag_color(c_type)
            item.setForeground(0, QColor(scheme["text"]))
            item.setBackground(0, QBrush(QColor(scheme["bg"])))

        # 根据当前复选框状态决定初始是否隐藏 (默认不展示被遮挡/不可见元素，有子节点的容器交由后序遍历自底向上处理防误杀)
        show_occluded = self.chk_show_occluded.isChecked() if hasattr(self, "chk_show_occluded") else False
        has_children_init = len(node.get("children", [])) > 0
        if is_occluded_node and not show_occluded and not has_children_init:
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
        # 如果当前节点是纯透明布局容器且包含子节点：
        # 1. 只要有至少一个子节点真实暴露可见，则该容器自身判定为有效暴露；
        # 2. 若所有子节点全部被判定为被遮挡/不可见，则该父容器视觉上无任何有效内容，必须严格自底向上继承并标记为已遮挡！
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
                if not attrs_str_clean.endswith('>'):
                    attrs_str_clean += '>'
                item.setText(0, f"{type_badge}{attrs_str_clean}")
                item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
                item.setHidden(False)
            else:
                is_node_occluded = True
                is_occluded_node = True
                comp["is_occluded"] = True
                comp["is_exposed"] = False
                comp["is_interactive"] = False
                clean_xml_attrs["occluded"] = "true"
                clean_xml_attrs["exposed"] = "false"
                xml_elem.attrib["occluded"] = "true"
                xml_elem.attrib["exposed"] = "false"
                item.setForeground(0, QColor("#94a3b8"))
                item.setBackground(0, QBrush(QColor("#f8fafc")))
                base_txt = re.sub(r'\s+occluded="[^"]*"', '', attrs_str)
                if base_txt.endswith('>'):
                    base_txt = base_txt[:-1]
                item.setText(0, f"{type_badge}{base_txt} occluded=\"true\">")
                item.setData(0, Qt.ItemDataRole.UserRole + 1, True)
                # 关键：彻底从画布交互拾取列表中剔除，绝不可再被鼠标悬停或点击拾取出来！
                if comp in self.flat_components:
                    self.flat_components.remove(comp)
                # 若未勾选【显示被遮挡元素】，默认将全遮挡父容器随子节点一同隐藏
                show_occluded = self.chk_show_occluded.isChecked() if hasattr(self, "chk_show_occluded") else False
                if not show_occluded:
                    item.setHidden(True)

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
        is_sel = (mode == InspectorMode.SELECT)
        self.btn_mode_select.setChecked(is_sel)
        self.btn_mode_tap.setChecked(not is_sel)
        self.btn_mode_select.setIcon(get_tech_icon("target", "#ffffff" if is_sel else "#475569"))
        self.btn_mode_tap.setIcon(get_tech_icon("tap", "#ffffff" if not is_sel else "#475569"))
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
            ModernMessageBox.information(self, "保存成功", f"截图已保存至:\n{path}")

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
        show_occluded = self.chk_show_occluded.isChecked() if hasattr(self, "chk_show_occluded") else False
        self.apply_occluded_visibility_to_tree(show_occluded)

    def on_toggle_show_full_type(self, state: int):
        """响应【显示原生完整类型】复选框切换，毫秒级无损平滑切换 DOM 树标签全称与简称"""
        is_full = self.chk_show_full_type.isChecked() if hasattr(self, "chk_show_full_type") else False
        for node_id, item in self.tree_item_map.items():
            comp = self.comp_map.get(node_id)
            if not comp:
                continue
            full_t = comp.get("full_type") or comp.get("type", "Component")
            short_t = comp.get("type", "Component")
            disp_t = full_t if is_full else short_t

            raw_attrs = comp.get("raw") or comp.get("raw_attributes") or {}
            c_id = comp.get("id", "")
            c_text = comp.get("text", "")
            bounds_str = f"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]"
            is_occluded = comp.get("is_occluded", False)

            attrs_str = ""
            if self.current_platform == "ios":
                ios_name = raw_attrs.get("name") or c_id
                ios_label = raw_attrs.get("label") or ""
                ios_value = raw_attrs.get("value") or ""
                if ios_value:
                    attrs_str += f' value="{ios_value}"'
                if ios_name:
                    attrs_str += f' name="{ios_name}"'
                if ios_label and ios_label != ios_value:
                    attrs_str += f' label="{ios_label}"'
            else:
                if c_id:
                    attrs_str += f' id="{c_id}"'
                if c_text:
                    attrs_str += f' text="{c_text}"'
            attrs_str += f' bounds="{bounds_str}"'
            if is_occluded:
                attrs_str += ' occluded="true"'

            item.setText(0, f"<{disp_t}{attrs_str}>")
    def apply_occluded_visibility_to_tree(self, show_occluded: bool):
        """
        动态更新当前 DOM 树中所有被遮挡节点的显示/隐藏状态：
        遵循严格的【自底向上保护法则】(Bottom-Up Visibility Guard)：
        1. 若勾选【显示被遮挡元素】(show_occluded=True)：全部节点 100% 展开可见；
        2. 若取消勾选 (show_occluded=False)：仅隐藏自身被遮挡且【没有任何可见子孙】的节点；
           若某个节点自身虽然带有 occluded 标记，但其子树中含有可见内容，坚决保留该节点展示，绝不连坐隐藏整个子树！
        """
        def update_item_visibility(item: QTreeWidgetItem) -> bool:
            """后序遍历返回该节点及其子树中是否至少存在一个可见节点"""
            has_visible_child = False
            for i in range(item.childCount()):
                child_visible = update_item_visibility(item.child(i))
                if child_visible:
                    has_visible_child = True

            is_self_occluded = bool(item.data(0, Qt.ItemDataRole.UserRole + 1))

            if show_occluded:
                item.setHidden(False)
                return True
            else:
                # 隐藏被遮挡模式：
                # 核心防连坐：若子树中包含有效可见节点，父级容器坚决保留显示！
                if has_visible_child:
                    item.setHidden(False)
                    return True
                elif is_self_occluded:
                    item.setHidden(True)
                    return False
                else:
                    item.setHidden(False)
                    return True

        visible_top_count = 0
        for idx in range(self.tree_widget.topLevelItemCount()):
            top = self.tree_widget.topLevelItem(idx)
            if top:
                has_vis = update_item_visibility(top)
                # 核心防消失：顶层根节点是视窗主干骨架，永远不被隐藏
                top.setHidden(False)
                if has_vis:
                    visible_top_count += 1

        # 终极保护：若所有子树节点均因遮挡判定被折叠隐藏，自动回退展示前两层，确保 DOM 树绝不全部消失
        if not show_occluded and visible_top_count == 0 and self.tree_widget.topLevelItemCount() > 0:
            for idx in range(self.tree_widget.topLevelItemCount()):
                top = self.tree_widget.topLevelItem(idx)
                if top:
                    top.setHidden(False)
                    for c_idx in range(top.childCount()):
                        top.child(c_idx).setHidden(False)

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
        """双击 DOM 树里面的元素：确立当前项、联动真机与属性面板，保持当前节点展开/收起状态不变"""
        if not item:
            return
        h_bar = self.tree_widget.horizontalScrollBar()
        h_val = h_bar.value()

        # 1. 设为当前树选中项并锁定水平视口
        self.tree_widget.setCurrentItem(item)
        item.setSelected(True)
        h_bar.setValue(h_val)

        # 2. 联动真机画面高亮框、右侧属性面板及查找器定位器同步 (双击不再触发展开/折叠，由节点前方箭头独立控制)
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

    def _sync_after_device_action(self, delay_ms: int = 300) -> None:
        """
        设备交互动作（点击/滑动/直接点击元素）后的视图刷新统一调度：
        - 实时投屏中：画面由投屏流实时推送，仅延迟刷新 DOM 树（iOS 无 WDA 时静默跳过）；
        - 非投屏状态：延迟等待页面跳转/渲染完成后，全量同步最新真机画面与 DOM 树。
        """
        def _do_sync() -> None:
            if not self.current_udid:
                return
            if self.is_screencasting:
                if self.current_platform == "ios":
                    wda_ok, _ = IosWdaManager.get_wda_url(self.current_udid, allow_spawn=False)
                    if not wda_ok:
                        return
                self.refresh_screen_and_dom()
            else:
                self.refresh_screen_only()

        QTimer.singleShot(delay_ms, _do_sync)

    def on_canvas_coordinate_tapped(self, x: int, y: int):
        if self.current_udid:
            DeviceController.tap(self.current_platform, self.current_udid, x, y)
            self._sync_after_device_action(delay_ms=300)

    def on_canvas_coordinate_swiped(self, x1: int, y1: int, x2: int, y2: int):
        if self.current_udid:
            DeviceController.swipe(self.current_platform, self.current_udid, x1, y1, x2, y2, 600)
            self._sync_after_device_action(delay_ms=350)

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

        # 核心：输入框和文本框才展示实时输入区
        is_input_or_text = (
            c_type in ("TextInput", "TextArea", "Search", "Text", "RichText", "Span", "TextField", "SecureTextField")
            or any(k in c_type.lower() for k in ("input", "edit", "text", "search", "field"))
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

        # 推荐定位器展示 (各端原生定位语法支持)
        self.txt_loc_id.setText(comp.get("rec_id", ""))
        self.txt_loc_xpath.setText(comp.get("rec_xpath", ""))
        self.txt_loc_py.setText(comp.get("rec_py", ""))
        if hasattr(self, "txt_loc_predicate"):
            self.txt_loc_predicate.setText(comp.get("rec_predicate", ""))
            self.txt_loc_predicate.setCursorPosition(0)
        if hasattr(self, "txt_loc_class_chain"):
            self.txt_loc_class_chain.setText(comp.get("rec_class_chain", ""))
            self.txt_loc_class_chain.setCursorPosition(0)

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

        full_type_val = comp.get("full_type") or comp.get("rec_class") or c_type
        display_attrs = [
            ("原生全类名 (Full Type)", full_type_val),
            ("精炼类型 (Type)", c_type),
            ("id / name / key", id_show),
            ("text / label / value", comp.get("text", "-")),
            ("Predicate (iOS谓词)", comp.get("rec_predicate", "-")),
            ("Class Chain (iOS类链)", comp.get("rec_class_chain", "-")),
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

        known_keys = {"id", "key", "text", "originalText", "type", "full_type", "bounds", "bundleName", "clickable", "enabled", "focusable", "focused", "scrollable", "visible"}
        for k, v in raw.items():
            if k not in known_keys:
                display_attrs.append((f"raw: {k}", str(v)))

        self.table_attrs.setUpdatesEnabled(False)
        self.table_attrs.setRowCount(len(display_attrs))
        for row, (k, v) in enumerate(display_attrs):
            k_item = QTableWidgetItem(str(k))
            v_item = QTableWidgetItem(str(v))
            v_item.setToolTip(str(v))
            if any(key in k for key in ("Full Type", "Type", "id", "text", "Predicate", "Class Chain", "xpath", "bounds", "size")):
                k_item.setForeground(QColor("#0284c7"))
                v_item.setForeground(QColor("#d97706"))
                k_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            else:
                k_item.setForeground(QColor("#64748b"))
                v_item.setForeground(QColor("#0f172a"))
            self.table_attrs.setItem(row, 0, k_item)
            self.table_attrs.setItem(row, 1, v_item)
        self.table_attrs.resizeRowsToContents()
        self.table_attrs.setUpdatesEnabled(True)
    # --------------------------------------------------------------------------
    # 实时输入同步 (Live Input & Device Sync)
    # --------------------------------------------------------------------------

    def sync_live_input(self):
        """将实时输入框中的文字下发到真机，并即时同步全量视图"""
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
            self._sync_after_device_action(delay_ms=300)

    def direct_send_keys_to_element(self, node_id: str, text: str):
        """
        向目标组件下发文本，并实现零延迟的视图与真机双向实时同步：
        1. 跨平台指令下发到真机执行物理输入
        2. 立即就地更新内存中该节点的 text 与定位表达式
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
        if "raw_attributes" in comp:
            comp["raw_attributes"]["text"] = text
            comp["raw_attributes"]["originalText"] = text

        # 2. 立即更新推荐定位代码
        c_type = comp.get("type", "Component")
        full_type = comp.get("full_type") or comp.get("rec_class") or c_type
        c_id = comp.get("id", "")
        if self.current_platform == "android":
            if c_id:
                rec_xpath = f"//*[@resource-id='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
            elif text:
                rec_xpath = f"//{full_type}[@text='{text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{full_type}[@text='{text}']\")"
            else:
                rec_xpath = comp.get("xpath", "")
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"
        elif self.current_platform == "ios":
            if c_id:
                rec_xpath = f"//{full_type}[@name='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ACCESSIBILITY_ID, '{c_id}')"
            elif text:
                rec_xpath = f"//{full_type}[@label='{text}']"
                rec_py = f"driver.find_element(AppiumBy.IOS_PREDICATE, 'type == \"{full_type}\" AND label == \"{text}\"')"
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
            id_attr = f' id="{c_id}"' if c_id else ""
            txt_attr = f' text="{text}"' if text else ""
            is_full = self.chk_show_full_type.isChecked() if hasattr(self, "chk_show_full_type") else False
            tag_name = full_type if is_full else c_type
            item.setText(0, f"<{tag_name}{id_attr}{txt_attr} bounds=\"{bounds_str}\">")

        # 4. 立即更新右侧属性表与实时输入框
        self.update_selected_element_panel(node_id)

        # 5. 异步刷新真机最新截图
        self.refresh_screen_only()

    def action_element_clear(self):
        """清空该输入框/编辑框内容并即时同步"""
        curr_id = self.canvas.selected_node_id
        comp = self.comp_map.get(curr_id)
        if comp and self.current_udid:
            cx, cy = comp["center_x"], comp["center_y"]
            DeviceController.clear_text(self.current_platform, self.current_udid, cx, cy)

            comp["text"] = ""
            if "raw_attributes" in comp:
                comp["raw_attributes"]["text"] = ""
                comp["raw_attributes"]["originalText"] = ""
            self.edit_live_input.setText("")
            self.update_selected_element_panel(curr_id)
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