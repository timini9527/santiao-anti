# -*- coding: utf-8 -*-
"""
iOS 布局解析、WKWebView 可见性自愈、DOM 抓取与截图标准化引擎：
1. 逻辑分辨率提取与 DVT 对齐黑边裁剪 (extract_ios_logical_size / crop_ios_dvt_image / normalize_ios_screenshot_file)；
2. WDA XML/JSON 节点解析与 WKWebView 容器/纯 CSS 控件可见性自愈 (parse_ios_node / parse_ios_json_node / parse_ios_layout)；
3. 多通道 iOS DOM 抓取 (Appium 2.x/1.x 活跃会话 + WDA 会话/根路径/新建会话)；
4. 离线静态截屏兜底 (支持打包态 --internal-pmd3 与 WDA /screenshot)。
"""
import base64
import json
import logging
import os
import re
import socket
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional, Tuple

from PyQt6.QtGui import QImage

from desktop_app.ui.inspector.platforms.base import fetch_active_appium_source, parse_bounds_wh
from desktop_app.ui.inspector.platforms.ios_service import IosWdaManager

logger = logging.getLogger("Inspector")

_IOS_WRAPPER_TYPES = frozenset({
    "Other", "XCUIElementTypeOther",
    "WebView", "XCUIElementTypeWebView",
    "ScrollView", "XCUIElementTypeScrollView",
    "Window", "XCUIElementTypeWindow",
    "Application", "XCUIElementTypeApplication",
})


def extract_ios_logical_size(layout_file: str) -> Optional[Tuple[int, int]]:
    """从 iOS WDA 布局文件提取应用原生逻辑点尺寸（如 390x844）"""
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
    """将 iOS WDA XML 节点转换为通用 DOM 结构"""
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
        "children": [parse_ios_node(child, scale_x, scale_y) for child in elem],
    }


def parse_ios_json_node(data: Dict[str, Any], scale_x: float = 1.0, scale_y: float = 1.0) -> Dict[str, Any]:
    """将 iOS WDA JSON 节点转换为通用 DOM 结构"""
    if not isinstance(data, dict):
        return {
            "attributes": {"type": "Element", "full_type": "XCUIElementTypeElement", "bounds": "[0,0][0,0]"},
            "children": [],
        }
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
        "children": [
            parse_ios_json_node(child, scale_x, scale_y)
            for child in data.get("children", [])
            if isinstance(child, dict)
        ],
    }


def _promote_webview_css_leaf_widgets(node: Any) -> None:
    """将活跃 iOS WebView 展示容器内实体小尺寸纯 CSS <div> 节点从误报 visible="false" 校正为 visible="true" """
    if not isinstance(node, dict):
        return
    attrs = node.get("attributes")
    if isinstance(attrs, dict):
        node_type = str(attrs.get("type") or attrs.get("full_type") or "")
        raw_vis = str(attrs.get("visible", "")).strip().lower()
        raw_en = str(attrs.get("enabled", "true")).strip().lower()
        left, top, w, h = parse_bounds_wh(str(attrs.get("bounds", "")))
        if (
            node_type in ("Other", "XCUIElementTypeOther")
            and raw_vis in ("false", "0")
            and raw_en not in ("false", "0")
            and left >= 0
            and top >= 0
            and 8 <= w <= 260
            and 8 <= h <= 260
        ):
            attrs["visible"] = "true"
    for ch in node.get("children") or []:
        _promote_webview_css_leaf_widgets(ch)


def heal_ios_container_visibility(node: Any, in_webview: bool = False) -> bool:
    """
    修复 iOS WKWebView / UIKit 纯包装容器误报 visible="false" 导致子树连坐隐藏的问题，
    并校正活跃 WebView 容器下纯 CSS 小控件的可见性误判。
    """
    if not isinstance(node, dict):
        return False
    attrs = node.get("attributes")
    children = node.get("children") or []
    node_type = str(attrs.get("type") or attrs.get("full_type") or "") if isinstance(attrs, dict) else ""
    cur_in_webview = in_webview or node_type in ("WebView", "XCUIElementTypeWebView")

    has_visible_child = False
    has_direct_visible_sibling = False
    for ch in children:
        ch_vis = heal_ios_container_visibility(ch, in_webview=cur_in_webview)
        if ch_vis:
            has_visible_child = True
            if isinstance(ch, dict):
                ch_attrs = ch.get("attributes") or {}
                if str(ch_attrs.get("visible", "")).strip().lower() in ("true", "1"):
                    has_direct_visible_sibling = True

    if cur_in_webview and has_direct_visible_sibling:
        for ch in children:
            if isinstance(ch, dict):
                ch_attrs = ch.get("attributes") or {}
                if str(ch_attrs.get("visible", "")).strip().lower() in ("false", "0"):
                    _promote_webview_css_leaf_widgets(ch)

    if not isinstance(attrs, dict):
        return has_visible_child

    raw_vis = str(attrs.get("visible", "")).strip().lower()
    if raw_vis in ("false", "0") and has_visible_child and node_type in _IOS_WRAPPER_TYPES:
        attrs["visible"] = "true"
        return True

    return raw_vis in ("true", "1") or has_visible_child


def parse_ios_layout(layout_path: str, root_bounds: str) -> Dict[str, Any]:
    """解析 iOS 布局文件 (XML / JSON) 并执行 WKWebView 可见性自愈"""
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
                if isinstance(val, str) and (
                    "<XCUIElementType" in val or "<AppiumAUT" in val or val.strip().startswith("<")
                ):
                    xml_content = val.strip()
                elif isinstance(val, dict):
                    json_data = val
            except Exception:
                if "<" in content:
                    xml_content = content[content.find("<") :]

        parsed: Optional[Dict[str, Any]] = None
        if xml_content:
            root = ET.fromstring(xml_content)
            app_node = root.find(".//XCUIElementTypeApplication")
            target_node = app_node if app_node is not None else root
            parsed = parse_ios_node(target_node, 1.0, 1.0)
        elif json_data:
            parsed = parse_ios_json_node(json_data, 1.0, 1.0)

        if parsed is not None:
            heal_ios_container_visibility(parsed)
            return parsed
    except Exception as e:
        logger.warning(f"[iOS布局解析] 异常降级: {e}")
    return {"attributes": {"type": "Screen", "bounds": root_bounds}, "children": []}


def dump_ios_hierarchy(udid: str, layout_file: str) -> bool:
    """
    iOS 实时 DOM 树多通道抓取引擎：
    1. 通道 1：探测本地活跃 Appium Server (兼容 Appium 2.x /appium/sessions 与 1.x /sessions)；
    2. 通道 2：直连 WDA 8100/8200（活跃 session -> 根 /source -> W3C 新建轻量会话）。
    """
    norm_layout = os.path.normpath(os.path.abspath(layout_file))
    os.makedirs(os.path.dirname(norm_layout), exist_ok=True)
    if os.path.exists(norm_layout):
        try:
            os.remove(norm_layout)
        except Exception:
            pass

    # 通道 1：活跃 Appium Server 会话
    hit = fetch_active_appium_source(
        ports=(4724, 4723, 4725, 4726, 4728),
        udid=udid,
        platform_filter="ios",
        source_validator=lambda s: ("<XCUIElementType" in s or "<AppiumAUT" in s),
        source_timeout=4.5,
    )
    if hit is not None:
        xml_str, port, sid = hit
        with open(norm_layout, "w", encoding="utf-8") as f_xml:
            f_xml.write(xml_str)
        logger.info(f"[iOS DOM抓取] 成功命中 Appium 活跃会话 (端口 {port}, Session {sid[:8]})")
        return True

    # 通道 2：直连本地 WDA 服务端口 (8100 / 8200)
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

        def _is_timeout_error(err: BaseException) -> bool:
            """判断是否为网络/WDA 响应超时（超时场景严禁连环重发 /source 导致主线程雪崩）"""
            if isinstance(err, (TimeoutError, socket.timeout)):
                return True
            reason = getattr(err, "reason", None)
            if isinstance(reason, (TimeoutError, socket.timeout)):
                return True
            return "timed out" in str(err).lower()

        def _post_wda_settings(target_sid: str, settings: Dict[str, Any], timeout: float = 1.5) -> bool:
            """轻量更新 WDA 会话参数，用于在抓 DOM 前暂停高频 MJPEG 抢占并关闭空闲等待"""
            if not target_sid:
                return False
            try:
                req = urllib.request.Request(
                    f"{wda_url}/session/{target_sid}/appium/settings",
                    data=json.dumps({"settings": settings}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=timeout):
                    return True
            except Exception:
                return False

        throttled_sid = ""
        try:
            # 优先确保拥有一个带限流与免静止等待参数的轻量 WDA 会话，避免无 session 裸调 /source 触发默认 10s 等待超时
            if not sid:
                try:
                    init_data = json.dumps({
                        "capabilities": {
                            "alwaysMatch": {
                                "shouldWaitForQuiescence": False,
                                "waitForQuiescence": False,
                                "shouldUseTestManagerForVisibilityDetection": False,
                            },
                            "firstMatch": [{}],
                        }
                    }).encode("utf-8")
                    init_req = urllib.request.Request(
                        f"{wda_url}/session",
                        data=init_data,
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(init_req, timeout=4.0) as init_resp:
                        init_res = json.loads(init_resp.read().decode("utf-8", errors="ignore"))
                        sid = init_res.get("sessionId") or (init_res.get("value") or {}).get("sessionId")
                except Exception as e:
                    logger.debug(f"[iOS DOM抓取] 创建轻量 WDA 会话失败，降级根 /source: {e}")

            if sid:
                # 抓 DOM 期间临时把 MJPEG 降频至 1fps，并限制 snapshotMaxChildren=25 过滤屏幕外冗余列表项，
                # 实测保留全部真实 visible 属性的同时耗时从 8.4s 降至 ~3s
                if _post_wda_settings(
                    sid,
                    {
                        "mjpegServerFramerate": 1,
                        "waitForIdleTimeout": 0,
                        "animationCoolOffTimeout": 0,
                        "useFirstMatch": True,
                        "snapshotMaxDepth": 25,
                        "snapshotMaxChildren": 25,
                        "boundElementsByIndex": True,
                    },
                ):
                    throttled_sid = sid

                # 严格保留真实 visible 属性以过滤 iOS 隐藏占位控件，仅排除审查器不使用的冗余属性提速
                source_candidates = (
                    f"{wda_url}/session/{sid}/source?format=xml&excluded_attributes=accessible,focused,index,traits",
                    f"{wda_url}/session/{sid}/source?format=xml",
                )
                for src_url in source_candidates:
                    try:
                        src_req = urllib.request.Request(src_url)
                        with urllib.request.urlopen(src_req, timeout=14.0) as src_resp:
                            raw_bytes = src_resp.read()
                        if raw_bytes and len(raw_bytes) > 100 and (
                            b"<XCUIElementType" in raw_bytes or b"<AppiumAUT" in raw_bytes
                        ):
                            with open(norm_layout, "wb") as f_out:
                                f_out.write(raw_bytes)
                            logger.info(
                                f"[iOS DOM抓取] 成功通过 WDA 会话 {sid[:8]} 提取组件树 (大小: {len(raw_bytes)} 字节)"
                            )
                            return True
                    except Exception as e:
                        if _is_timeout_error(e):
                            logger.warning(f"[iOS DOM抓取] WDA session/source 超时，中止连环重试以避免堵死主线程: {e}")
                            return False
                        logger.debug(f"[iOS DOM抓取] WDA {src_url} 尝试降级: {e}")

            for fmt in ("xml", "json"):
                try:
                    req = urllib.request.Request(
                        f"{wda_url}/source?format={fmt}"
                        + ("&excluded_attributes=accessible,focused,index,traits" if fmt == "xml" else "")
                    )
                    with urllib.request.urlopen(req, timeout=12.0) as resp:
                        raw_bytes = resp.read()
                    if raw_bytes and len(raw_bytes) > 100 and (
                        b"<XCUIElementType" in raw_bytes or b'"children"' in raw_bytes or b'"type"' in raw_bytes
                    ):
                        with open(norm_layout, "wb") as f_out:
                            f_out.write(raw_bytes)
                        logger.info(f"[iOS DOM抓取] 成功通过 WDA 根 /source ({fmt}) 提取组件树")
                        return True
                except Exception as e:
                    if _is_timeout_error(e):
                        logger.warning(f"[iOS DOM抓取] WDA 根 /source ({fmt}) 超时，中止连环重试: {e}")
                        return False
        finally:
            if throttled_sid:
                _post_wda_settings(throttled_sid, {"mjpegServerFramerate": 20}, timeout=1.2)

    return False


def capture_ios_fallback_screen(udid: str, local_png: str, allow_dvt_cli: bool = True) -> bool:
    """iOS 静态截图兜底（支持打包态内置 --internal-pmd3 DVT 截图与 WDA /screenshot）"""
    if allow_dvt_cli:
        try:
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            if getattr(sys, "frozen", False):
                pmd_cmd = [sys.executable, "--internal-pmd3", "developer", "dvt", "screenshot", local_png]
            else:
                pmd_cmd = ["pymobiledevice3", "developer", "dvt", "screenshot", local_png]
            if udid and not udid.startswith("wda_localhost"):
                pmd_cmd.extend(["--udid", udid])
            subprocess.run(pmd_cmd, timeout=8, capture_output=True, creationflags=creationflags)
            if os.path.exists(local_png) and os.path.getsize(local_png) > 1000:
                return True
        except Exception:
            pass

    wda_url, _ = IosWdaManager.get_wda_url(udid, allow_spawn=False)
    if not wda_url:
        wda_url = "http://127.0.0.1:8100"
    try:
        req = urllib.request.Request(f"{wda_url}/screenshot")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                b64_img = data.get("value", "")
                if b64_img:
                    with open(local_png, "wb") as f_out:
                        f_out.write(base64.b64decode(b64_img))
                    return True
    except Exception:
        pass
    return False
