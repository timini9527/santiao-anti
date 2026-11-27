# -*- coding: utf-8 -*-
"""
安卓 Android 审查器专属引擎：
1. ADB 工具链自动解析与指令执行 (resolve_adb_bin / run_adb)；
2. 安卓设备发现与动作控制 (scan_android_devices / tap / swipe / input_text / clear_text)；
3. 节点解析与系统浮层过滤 (parse_android_node / parse_android_layout)；
4. 多通道 DOM 抓取 (Appium 2.x/1.x 活跃会话 + uiautomator2 WebView 懒加载唤醒 + Toast 注入 + ADB 兜底)；
5. 安卓多通道静态截屏 (u2 / adb exec-out / adb screencap)。
"""
import logging
import os
import random
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Set

from desktop_app.core.path_resolver import SmartPathResolver
from desktop_app.ui.inspector.platforms.base import fetch_active_appium_source

logger = logging.getLogger("Inspector")

_EMPTY_WEBVIEW_RE = re.compile(r'<node\b[^>]*class="android\.webkit\.WebView"[^>]*/>')


def resolve_adb_bin() -> str:
    """解析安卓 ADB 可执行文件路径（优先内置绿色工具链）"""
    try:
        tc = SmartPathResolver.discover_mobile_toolchain()
        if tc.get("adb"):
            return str(tc["adb"])
    except Exception:
        pass
    return shutil.which("adb") or "adb"


def run_adb(cmd: List[str], udid: str = "", timeout: float = 8.0) -> str:
    """执行 ADB 指令（优先内置绿色工具链，Windows 静默无黑框）"""
    adb_bin = resolve_adb_bin()
    full_cmd = [adb_bin]
    if udid:
        full_cmd.extend(["-s", udid])
    full_cmd.extend(cmd)
    try:
        kwargs: Dict[str, Any] = {
            "capture_output": True,
            "text": True,
            "errors": "ignore",
            "timeout": timeout,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = 0x08000000
        res = subprocess.run(full_cmd, **kwargs)
        return res.stdout.strip()
    except Exception:
        return ""


def scan_android_devices(seen_udids: Set[str]) -> List[Dict[str, Any]]:
    """探测当前在线的安卓真机与模拟器（统一走内置/环境变量 ADB 工具链）"""
    devices: List[Dict[str, Any]] = []
    adb_bin = resolve_adb_bin()
    if not (os.path.isfile(adb_bin) or shutil.which(adb_bin) or os.environ.get("ANDROID_HOME")):
        return devices

    creationflags = 0x08000000 if sys.platform == "win32" else 0
    try:
        out = subprocess.check_output(
            [adb_bin, "devices"],
            text=True,
            errors="ignore",
            timeout=1.5,
            creationflags=creationflags,
        ).strip()
        for line in out.splitlines():
            line_str = line.strip()
            if re.search(r"\s+device$", line_str):
                udid = line_str.split()[0].strip()
                if udid and udid not in seen_udids:
                    seen_udids.add(udid)
                    is_real = not (udid.startswith("emulator-") or "127.0.0.1" in udid or "localhost" in udid)
                    model = run_adb(["shell", "getprop", "ro.product.model"], udid, timeout=1.0)
                    if model:
                        desc = f"安卓真机 ({model}): {udid}" if is_real else f"安卓模拟器 ({model}): {udid}"
                    else:
                        desc = f"安卓真机: {udid}" if is_real else f"安卓模拟器: {udid}"
                    devices.append({
                        "udid": udid,
                        "platform": "android",
                        "name": desc,
                        "is_real": is_real,
                    })
    except Exception:
        pass
    return devices


# ------------------------------------------------------------------
# 安卓设备动作控制
# ------------------------------------------------------------------
def android_tap(udid: str, x: int, y: int) -> None:
    run_adb(["shell", "input", "tap", str(x), str(y)], udid)


def android_swipe(udid: str, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
    run_adb(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)], udid)


def android_input_text(udid: str, text: str, cx: int = 0, cy: int = 0) -> None:
    if cx and cy:
        run_adb(["shell", "input", "tap", str(cx), str(cy)], udid)
    escaped_text = text.replace(" ", "%s").replace("&", r"\&").replace("<", r"\<").replace(">", r"\>")
    run_adb(["shell", "input", "text", escaped_text], udid)


def android_clear_text(udid: str, cx: int = 0, cy: int = 0) -> None:
    if cx and cy:
        run_adb(["shell", "input", "tap", str(cx), str(cy)], udid)
    run_adb(["shell", "input", "keyevent"] + ["67"] * 35, udid)


# ------------------------------------------------------------------
# 安卓 DOM XML 解析与系统浮层过滤
# ------------------------------------------------------------------
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
        "children": [parse_android_node(child) for child in elem if child.tag == "node"],
    }


def parse_android_layout(layout_path: str, root_bounds: str) -> Dict[str, Any]:
    """解析安卓 XML 布局文件，智能剥离系统侧边栏/状态栏浮层并保留 Toast 窗口"""
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

            app_nodes = [n for n in top_nodes if not _is_system_overlay(n) and not _is_launcher(n)]
            if app_nodes:
                selected_nodes = app_nodes
            else:
                launcher_nodes = [n for n in top_nodes if _is_launcher(n)]
                selected_nodes = launcher_nodes if launcher_nodes else top_nodes

            if len(selected_nodes) == 1:
                return parse_android_node(selected_nodes[0])
            return {
                "attributes": {"type": "Hierarchy", "bounds": root_bounds},
                "children": [parse_android_node(n) for n in selected_nodes],
            }
    except Exception:
        pass
    return {"attributes": {"type": "hierarchy", "bounds": root_bounds}, "children": []}


# ------------------------------------------------------------------
# 安卓 DOM 抓取（Appium 2.x/1.x + u2 WebView 唤醒 + Toast 注入 + ADB 兜底）
# ------------------------------------------------------------------
def inject_android_toast_xml(xml_text: str, toast_text: str) -> str:
    """将 uiautomator2 捕获的系统 Toast 注入 XML 层级树"""
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


def dump_android_hierarchy(udid: str, layout_file: str) -> bool:
    """
    安卓实时 DOM 树高可靠三通道抓取引擎：
    1. 通道 1：探测本地活跃 Appium Server (兼容 Appium 2.x /appium/sessions 与 1.x /sessions)；
    2. 通道 2：uiautomator2 JSON-RPC 直出 (max_depth=80) + 空壳 WebView 懒加载唤醒重抓 + Toast 注入；
    3. 通道 3：原生 ADB uiautomator dump 兜底（唯一时间戳路径防残留污染）。
    """
    norm_layout = os.path.normpath(os.path.abspath(layout_file))
    os.makedirs(os.path.dirname(norm_layout), exist_ok=True)
    if os.path.exists(norm_layout):
        try:
            os.remove(norm_layout)
        except Exception:
            pass

    # 通道 1：复用本地活跃 Appium 会话
    hit = fetch_active_appium_source(
        ports=(4723, 4725, 4724),
        udid=udid,
        platform_filter="android",
        source_validator=lambda s: "<hierarchy" in s,
        source_timeout=3.0,
    )
    if hit is not None:
        xml_str, _, _ = hit
        with open(norm_layout, "w", encoding="utf-8") as f_xml:
            f_xml.write(xml_str)
        return True

    # 通道 2：uiautomator2 内存直出 + 空壳 WebView 无障碍树自动唤醒重抓
    try:
        import uiautomator2 as u2

        d = u2.connect(udid) if udid else u2.connect()
        xml_text = d.dump_hierarchy(compressed=False, max_depth=80)
        if isinstance(xml_text, str) and "<hierarchy" in xml_text and len(xml_text) > 100:
            if _EMPTY_WEBVIEW_RE.search(xml_text):
                try:
                    wv = d(className="android.webkit.WebView")
                    _ = wv.info
                    _ = wv.child(index=0).exists(timeout=0.2)
                except Exception:
                    pass
                time.sleep(0.15)
                try:
                    retry_xml = d.dump_hierarchy(compressed=False, max_depth=80)
                    if isinstance(retry_xml, str) and "<hierarchy" in retry_xml and len(retry_xml) > len(xml_text):
                        xml_text = retry_xml
                except Exception:
                    pass

            try:
                toast_msg = (d.jsonrpc.getLastToast() or "").strip()
                if toast_msg:
                    xml_text = inject_android_toast_xml(xml_text, toast_msg)
                    d.jsonrpc.clearLastToast()
            except Exception:
                pass

            with open(norm_layout, "w", encoding="utf-8") as f_xml:
                f_xml.write(xml_text)
            return True
    except Exception as e:
        logger.debug(f"[安卓DOM抓取] uiautomator2 dump_hierarchy 通道未命中，切换 ADB 通道: {e}")

    # 通道 3：原生 ADB uiautomator dump 兜底
    uid = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    remote_xml = f"/data/local/tmp/appium_layout_{uid}.xml"
    try:
        run_adb(["shell", "rm", "-f", "/data/local/tmp/appium_layout.xml"], udid, timeout=1.5)
        out = run_adb(["shell", "uiautomator", "dump", remote_xml], udid, timeout=5.0)
        if "dumped to" not in out.lower():
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
        logger.warning(f"[安卓DOM抓取] ADB uiautomator dump 异常: {e}")
    finally:
        try:
            run_adb(["shell", "rm", "-f", remote_xml], udid, timeout=1.5)
        except Exception:
            pass

    return False


def capture_android_static_screen(udid: str, local_png: str) -> bool:
    """安卓离线多通道截屏：u2 显存直出 -> adb exec-out -> adb screencap + pull"""
    try:
        import uiautomator2 as u2

        d = u2.connect(udid) if udid else u2.connect()
        d.screenshot(local_png)
        if os.path.exists(local_png) and os.path.getsize(local_png) > 1000:
            return True
    except Exception:
        pass

    try:
        adb_bin = resolve_adb_bin()
        creationflags = 0x08000000 if sys.platform == "win32" else 0
        cmd = [adb_bin]
        if udid:
            cmd.extend(["-s", udid])
        cmd.extend(["exec-out", "screencap", "-p"])
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=6, creationflags=creationflags)
        if p.stdout and len(p.stdout) > 1000:
            with open(local_png, "wb") as f_out:
                f_out.write(p.stdout)
            return True
    except Exception:
        pass

    try:
        run_adb(["shell", "screencap", "-p", "/data/local/tmp/appium_shot.png"], udid)
        run_adb(["pull", "/data/local/tmp/appium_shot.png", local_png], udid)
        return os.path.exists(local_png) and os.path.getsize(local_png) > 1000
    except Exception:
        return False
