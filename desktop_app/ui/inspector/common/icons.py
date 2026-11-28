# -*- coding: utf-8 -*-
"""
UI 审查器通用图标引擎与 DOM 标签配色中心：
1. 多分辨率矢量级 Retina 应用图标生成 (create_modern_app_icon)；
2. 本地 SVG / PNG 与网络 URL 图标加载缓存 (get_tech_icon / import_network_icon)；
3. DOM 元素标签低饱和度语义配色方案 (get_dom_tag_color)。
"""
import logging
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

from PyQt6.QtCore import QByteArray, QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap

try:
    from PyQt6.QtSvg import QSvgRenderer

    _HAS_QTSVG = True
except (ImportError, ModuleNotFoundError):
    QSvgRenderer = None
    _HAS_QTSVG = False

from desktop_app.core.path_resolver import SmartPathResolver
from desktop_app.core.paths import WRITABLE_ROOT

logger = logging.getLogger("Inspector")


def create_modern_app_icon() -> QIcon:
    """
    动态生成高定多分辨率矢量级 Retina 审查器专属图标：
    优先探测本地自定义图标，缺失时使用 QPainter 绘制高分辨率超椭圆矢量图标。
    """
    local_custom_candidates = [
        SmartPathResolver.get_asset_path("desktop_app/assets/icons/app_logo.svg"),
        SmartPathResolver.get_asset_path("desktop_app/assets/icons/app_logo.png"),
        SmartPathResolver.get_asset_path("desktop_app/resources/app_icon.png"),
    ]
    for cand in local_custom_candidates:
        if cand and os.path.exists(cand):
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

        pad = max(0.8, 1.2 * scale)
        rect = QRectF(pad, pad, float(size - 2 * pad), float(size - 2 * pad))
        radius = float(size) * 0.24
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0.0, QColor("#090d16"))
        grad.setColorAt(0.40, QColor("#111827"))
        grad.setColorAt(1.0, QColor("#1e3a8a"))
        p.fillPath(path, QBrush(grad))

        pen_border = QPen(QColor(255, 255, 255, 45), max(1.0, 1.0 * scale))
        p.setPen(pen_border)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        b_margin = 13.0 * scale
        b_len = 7.0 * scale
        pen_bracket = QPen(QColor(56, 189, 248, 225), max(1.4, 2.0 * scale))
        pen_bracket.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_bracket)

        x1 = b_margin
        y1 = b_margin
        x2 = size - b_margin
        y2 = size - b_margin

        p.drawLine(QPointF(x1, y1 + b_len), QPointF(x1, y1))
        p.drawLine(QPointF(x1, y1), QPointF(x1 + b_len, y1))
        p.drawLine(QPointF(x2 - b_len, y1), QPointF(x2, y1))
        p.drawLine(QPointF(x2, y1), QPointF(x2, y1 + b_len))
        p.drawLine(QPointF(x1, y2 - b_len), QPointF(x1, y2))
        p.drawLine(QPointF(x1, y2), QPointF(x1 + b_len, y2))
        p.drawLine(QPointF(x2 - b_len, y2), QPointF(x2, y2))
        p.drawLine(QPointF(x2, y2), QPointF(x2, y2 - b_len))

        cx = float(size) / 2.0
        cy = float(size) / 2.0

        card_w = 16.0 * scale
        card_h = 16.0 * scale
        p.setPen(QPen(QColor(14, 165, 233, 120), max(1.0, 1.2 * scale)))
        p.setBrush(QBrush(QColor(14, 165, 233, 40)))
        p.drawRoundedRect(
            QRectF(cx - card_w / 2.0 - 2.5 * scale, cy - card_h / 2.0 - 2.5 * scale, card_w, card_h),
            2.5 * scale,
            2.5 * scale,
        )

        p.setPen(QPen(QColor(255, 255, 255, 240), max(1.2, 1.6 * scale)))
        p.setBrush(QBrush(QColor(255, 255, 255, 45)))
        p.drawRoundedRect(
            QRectF(cx - card_w / 2.0 + 2.0 * scale, cy - card_h / 2.0 + 2.0 * scale, card_w, card_h),
            2.5 * scale,
            2.5 * scale,
        )

        dot_r = max(1.8, 2.8 * scale)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#22c55e")))
        p.drawEllipse(QPointF(cx + 2.0 * scale, cy + 2.0 * scale), dot_r, dot_r)

        p.end()
        icon.addPixmap(pix)
    return icon


def _resolve_local_icon_dir() -> str:
    """解析本地图标目录：优先定位内置资产目录，无写权限（只读安装卷）时回退至可写工作区目录。"""
    builtin_dir = SmartPathResolver.get_asset_path("desktop_app/assets/icons")
    default_dir = os.path.normpath(
        os.path.join(SmartPathResolver.get_project_root(), "desktop_app", "assets", "icons")
    )
    fallback_dir = os.path.normpath(os.path.join(WRITABLE_ROOT, "logs", "inspector_icons"))

    if builtin_dir and os.path.isdir(builtin_dir):
        try:
            probe = os.path.join(builtin_dir, ".icon_probe")
            with open(probe, "w", encoding="utf-8") as _f:
                _f.write("ok")
            os.remove(probe)
            return builtin_dir
        except Exception:
            if any(fn.endswith(".svg") for fn in os.listdir(builtin_dir)):
                return builtin_dir

    for cand in (default_dir, fallback_dir):
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, ".icon_probe")
            with open(probe, "w", encoding="utf-8") as _f:
                _f.write("ok")
            os.remove(probe)
            return cand
        except Exception:
            continue

    return builtin_dir or fallback_dir


LOCAL_ICON_DIR: str = _resolve_local_icon_dir()

_OFFICIAL_SVG_TEMPLATES: Dict[str, str] = {
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
    "loader": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>""",
}

# 仅在本地图标缺失时补齐落盘，避免每次导入重复覆写磁盘或触发只读目录写入异常
for _icon_name, _raw_svg in _OFFICIAL_SVG_TEMPLATES.items():
    _svg_file = os.path.join(LOCAL_ICON_DIR, f"{_icon_name}.svg")
    if not os.path.exists(_svg_file):
        try:
            with open(_svg_file, "w", encoding="utf-8") as _f:
                _f.write(_raw_svg.replace("{color}", "currentColor"))
        except Exception:
            pass


def import_network_icon(url: str, save_name: str = "") -> Optional[str]:
    """从网络 URL 下载图标并缓存到本地图标目录"""
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
    全方位本地/网络矢量图标加载器（支持动态染色、旋转角度与内存缓存）。
    """
    rot_int = int(round(rotation)) % 360
    cache_key = (name, color, size, rot_int)
    if cache_key in _TECH_ICON_CACHE:
        return _TECH_ICON_CACHE[cache_key]

    if name.startswith(("http://", "https://")):
        cached_file = import_network_icon(name)
        if cached_file and os.path.exists(cached_file):
            name = os.path.splitext(os.path.basename(cached_file))[0]

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
        "loader": "spinner",
    }.get(name, name)

    if not svg_content:
        svg_content = _OFFICIAL_SVG_TEMPLATES.get(name_alias, "")

    y_offset = 2.0

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
                        p.translate(s / 2.0, s / 2.0 + y_offset)
                        p.rotate(rot_int)
                        p.translate(-s / 2.0, -(s / 2.0 + y_offset))
                    renderer.render(p, QRectF(0, y_offset, s, max(1.0, s - y_offset)))
                    p.end()
                    icon.addPixmap(pix)
                _TECH_ICON_CACHE[cache_key] = icon
                return icon
        except Exception:
            pass

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
                p.translate(s / 2.0, s / 2.0 + y_offset)
                p.rotate(rot_int)
                p.translate(-s / 2.0, -(s / 2.0 + y_offset))
            p.drawPixmap(0, int(y_offset), s, int(max(1, s - y_offset)), src_pix)
            p.end()
            icon.addPixmap(pix)
        _TECH_ICON_CACHE[cache_key] = icon
        return icon

    icon = QIcon()
    for s in (16, 20, 24, 32, 48):
        pix = QPixmap(s, s)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if rot_int != 0:
            p.translate(s / 2.0, s / 2.0 + y_offset)
            p.rotate(rot_int)
            p.translate(-s / 2.0, -(s / 2.0 + y_offset))

        pen = QPen(QColor(color), max(1.5, s / 12.0))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        pad = s * 0.16
        w = s - 2 * pad
        h = max(1.0, s - 2 * pad - y_offset)
        cx = s / 2.0
        cy = s / 2.0 + y_offset

        if name_alias in ("spinner", "loader", "loading"):
            r = w * 0.42
            p.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), 45 * 16, 275 * 16)
        elif name_alias in ("refresh", "sync"):
            r = w * 0.42
            p.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), 45 * 16, 270 * 16)
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
            p.drawRoundedRect(QRectF(pad, pad + y_offset, w, h * 0.72), 2, 2)
            p.drawLine(QPointF(cx, pad + y_offset + h * 0.72), QPointF(cx, pad + y_offset + h * 0.95))
            p.drawLine(QPointF(cx - w * 0.3, pad + y_offset + h * 0.95), QPointF(cx + w * 0.3, pad + y_offset + h * 0.95))
        elif name_alias in ("copy", "clone"):
            p.drawRoundedRect(QRectF(pad + w * 0.22, pad + y_offset, w * 0.68, h * 0.68), 2, 2)
            p.drawRoundedRect(QRectF(pad, pad + y_offset + h * 0.22, w * 0.68, h * 0.68), 2, 2)
        elif name_alias in ("save", "export"):
            p.drawRoundedRect(QRectF(pad, pad + y_offset, w, h), 2, 2)
            p.drawRect(QRectF(pad + w * 0.25, pad + y_offset, w * 0.5, h * 0.35))
        elif name_alias in ("expand", "plus"):
            p.drawLine(QPointF(cx - w * 0.35, cy), QPointF(cx + w * 0.35, cy))
            p.drawLine(QPointF(cx, cy - h * 0.35), QPointF(cx, cy + h * 0.35))
        elif name_alias in ("collapse", "minus"):
            p.drawLine(QPointF(cx - w * 0.35, cy), QPointF(cx + w * 0.35, cy))
        elif name_alias in ("clear", "trash"):
            p.drawLine(QPointF(cx - w * 0.3, cy - h * 0.3), QPointF(cx + w * 0.3, cy + h * 0.3))
            p.drawLine(QPointF(cx + w * 0.3, cy - h * 0.3), QPointF(cx - w * 0.3, cy + h * 0.3))
        elif name_alias in ("phone", "device"):
            p.drawRoundedRect(QRectF(pad + w * 0.15, pad + y_offset, w * 0.7, h), 3, 3)
            p.drawPoint(QPointF(cx, pad + y_offset + h * 0.85))
        else:
            p.drawRoundedRect(QRectF(pad, pad + y_offset, w, h), 3, 3)

        p.end()
        icon.addPixmap(pix)

    _TECH_ICON_CACHE[cache_key] = icon
    return icon


def get_dom_tag_color(c_type: str) -> Dict[str, Any]:
    """
    统一 DOM 元素标签低饱和度语义配色方案（兼容鸿蒙/安卓/iOS 原生与 WebView 节点）。
    """
    ct = (c_type or "").strip()

    if ct in (
        "Text", "Span", "StaticText", "label", "TextClock", "Marquee",
        "XCUIElementTypeStaticText", "staticText", "labelText", "heading",
    ):
        return {
            "bg": "#fef3c7",
            "border": "#d97706",
            "text": "#78350f",
            "box_border": "#d97706",
            "box_bg": QColor(217, 119, 6, 35),
        }

    if ct in (
        "Button", "Toggle", "Checkbox", "Radio", "Switch", "LoadingProgress",
        "Select", "MenuItem", "XCUIElementTypeButton", "button", "link",
        "checkBox", "radioButton",
    ):
        return {
            "bg": "#e0f2fe",
            "border": "#0284c7",
            "text": "#075985",
            "box_border": "#0284c7",
            "box_bg": QColor(2, 132, 199, 35),
        }

    if ct in (
        "TextInput", "TextArea", "Search", "SearchField", "RichEditor",
        "RichEditorContent", "TextField", "EditText", "XCUIElementTypeTextField",
        "XCUIElementTypeSecureTextField", "textField", "searchBox",
    ):
        return {
            "bg": "#dcfce7",
            "border": "#16a34a",
            "text": "#14532d",
            "box_border": "#16a34a",
            "box_bg": QColor(22, 163, 74, 35),
        }

    if ct in (
        "Image", "QRCode", "Icon", "SymbolGlyph", "Badge", "Video", "ImageView",
        "Divider", "XCUIElementTypeImage", "XCUIElementTypeIcon", "image",
    ):
        return {
            "bg": "#ffe4e6",
            "border": "#e11d48",
            "text": "#881337",
            "box_border": "#e11d48",
            "box_bg": QColor(225, 29, 72, 35),
        }

    if ct in (
        "List", "ListItem", "Scroll", "Refresh", "Swiper", "Grid", "GridItem",
        "XCUIElementTypeScrollView",
    ):
        return {
            "bg": "#ede9fe",
            "border": "#7c3aed",
            "text": "#581c87",
            "box_border": "#7c3aed",
            "box_bg": QColor(124, 58, 237, 35),
        }

    if ct in (
        "Column", "Row", "Stack", "Flex", "RelativeContainer", "ViewGroup",
        "FrameLayout", "LinearLayout", "RelativeLayout", "XCUIElementTypeOther",
        "genericContainer", "rootWebArea", "Web",
    ):
        return {
            "bg": "#f1f5f9",
            "border": "#64748b",
            "text": "#334155",
            "box_border": "#64748b",
            "box_bg": QColor(100, 116, 139, 30),
        }

    if ct in (
        "Hierarchy", "root", "Navigation", "NavBar", "NavBarContent",
        "NavigationContent", "NavDestination", "NavDestinationContent",
        "WindowScene", "XCUIElementTypeWindow",
    ):
        return {
            "bg": "#f3e8ff",
            "border": "#9333ea",
            "text": "#6b21a8",
            "box_border": "#9333ea",
            "box_bg": QColor(147, 51, 234, 35),
        }

    return {
        "bg": "#f8fafc",
        "border": "#94a3b8",
        "text": "#1e293b",
        "box_border": "#0284c7",
        "box_bg": QColor(2, 132, 199, 30),
    }
