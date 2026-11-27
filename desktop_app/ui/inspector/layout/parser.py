# -*- coding: utf-8 -*-
"""
跨端布局文件统一解析调度器：
1. get_layout_physical_size：从布局数据自适应提取物理分辨率；
2. parse_layout_file：按平台派发给 HarmonyOS / Android / iOS 独立解析器（原生含三端 WebView 容错与遮挡自愈）。
"""
import json
import os
import re
from typing import Any, Dict, Tuple

from desktop_app.ui.inspector.platforms.android import parse_android_layout
from desktop_app.ui.inspector.platforms.harmony import parse_harmony_layout
from desktop_app.ui.inspector.platforms.ios import parse_ios_layout


def get_layout_physical_size(layout_data: Any, default_w: int = 1084, default_h: int = 2412) -> Tuple[int, int]:
    """从布局数据或文件自适应提取真实物理分辨率（支持鸿蒙 JSON 与安卓/iOS XML）"""
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


def parse_layout_file(layout_path: Any, platform: str, screen_w: int = 0, screen_h: int = 0) -> Dict[str, Any]:
    """统一解析三端布局文件为通用 DOM 节点树，并自动应用各端专属 WebView/可见性自愈逻辑"""
    plat = str(platform or "").lower()
    if plat in ("harmony", "android"):
        phys_w, phys_h = get_layout_physical_size(
            layout_path,
            1084 if plat == "harmony" else 1080,
            2412 if plat == "harmony" else 2400,
        )
        if screen_w < 800 or screen_h < 1200:
            screen_w, screen_h = phys_w, phys_h

    root_w = screen_w if screen_w > 0 else 1080
    root_h = screen_h if screen_h > 0 else 2400
    root_bounds = f"[0,0][{root_w},{root_h}]"

    if plat == "harmony":
        return parse_harmony_layout(layout_path, screen_w=screen_w, screen_h=screen_h, root_bounds=root_bounds)
    if plat == "android":
        return parse_android_layout(str(layout_path or ""), root_bounds=root_bounds)
    if plat == "ios":
        return parse_ios_layout(str(layout_path or ""), root_bounds=root_bounds)
    return {}
