# -*- coding: utf-8 -*-
"""
鸿蒙 HarmonyOS NEXT 审查器专属引擎：
1. HDC 工具链自动解析与指令执行 (resolve_hdc_bin / run_hdc)；
2. 鸿蒙设备发现与动作控制 (scan_harmony_devices / tap / swipe / input_text / clear_text)；
3. UITest RPC 高速布局拉取与多通道兜底 (HarmonyRpcLayoutClient / dump_harmony_layout)；
4. 节点归一化、ArkUI <Web> 透明度自愈、全屏 <Web> 下层遮挡抑制 (normalize_harmony_node / parse_harmony_layout)；
5. 鸿蒙 scrcpy_server.so 硬件录屏环境维护、静默截屏与 NALU 提取。
"""
import json
import logging
import os
import random
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from desktop_app.core.path_resolver import SmartPathResolver
from desktop_app.ui.inspector.platforms.base import parse_bounds_wh

logger = logging.getLogger("Inspector")


def resolve_hdc_bin() -> str:
    """解析鸿蒙 HDC 可执行文件路径（优先使用内置绿色工具链）"""
    try:
        tc = SmartPathResolver.discover_mobile_toolchain()
        if tc.get("hdc"):
            return str(tc["hdc"])
    except Exception:
        pass
    return shutil.which("hdc") or "hdc"


def run_hdc(cmd: List[str], udid: str = "", timeout: float = 8.0) -> str:
    """执行 HDC 指令（优先内置绿色工具链，Windows 静默无黑框）"""
    hdc_bin = resolve_hdc_bin()
    full_cmd = [hdc_bin]
    if udid:
        full_cmd.extend(["-t", udid])
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


def scan_harmony_devices(seen_udids: Set[str]) -> List[Dict[str, Any]]:
    """探测当前在线的鸿蒙设备（统一走内置/环境变量 HDC 工具链）"""
    devices: List[Dict[str, Any]] = []
    hdc_bin = resolve_hdc_bin()
    if not (os.path.isfile(hdc_bin) or shutil.which(hdc_bin) or os.environ.get("HDC_HOME")):
        return devices

    creationflags = 0x08000000 if sys.platform == "win32" else 0
    try:
        out = subprocess.check_output(
            [hdc_bin, "list", "targets"],
            text=True,
            errors="ignore",
            timeout=1.5,
            creationflags=creationflags,
        ).strip()
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
                    "is_real": True,
                })

        if not devices:
            out_v = subprocess.check_output(
                [hdc_bin, "list", "targets", "-v"],
                text=True,
                errors="ignore",
                timeout=1.5,
                creationflags=creationflags,
            ).strip()
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
                        "is_real": True,
                    })
    except Exception:
        pass
    return devices


# ------------------------------------------------------------------
# 鸿蒙设备动作控制
# ------------------------------------------------------------------
def harmony_tap(udid: str, x: int, y: int) -> None:
    run_hdc(["shell", "uitest", "uiInput", "click", str(x), str(y)], udid)


def harmony_swipe(udid: str, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
    run_hdc(["shell", "uitest", "uiInput", "swipe", str(x1), str(y1), str(x2), str(y2), "1500"], udid)


def harmony_input_text(udid: str, text: str, cx: int = 0, cy: int = 0) -> None:
    safe_text = text.replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")
    if cx and cy:
        cmd_str = f'uitest uiInput click {cx} {cy} && uitest uiInput inputText {cx} {cy} "{safe_text}"'
    else:
        cmd_str = f'uitest uiInput inputText {cx} {cy} "{safe_text}"'
    run_hdc(["shell", cmd_str], udid)


def harmony_clear_text(udid: str, cx: int = 0, cy: int = 0) -> None:
    if cx and cy:
        cmd_clear = f"uitest uiInput click {cx} {cy} && for i in $(seq 1 35); do uitest uiInput keyEvent 2055; done"
    else:
        cmd_clear = "for i in $(seq 1 35); do uitest uiInput keyEvent 2055; done"
    run_hdc(["shell", cmd_clear], udid)


# ------------------------------------------------------------------
# 鸿蒙高速 UITest RPC 通信客户端
# ------------------------------------------------------------------
class HarmonyRpcLayoutClient:
    """鸿蒙原生 uitest 守护进程 RPC 通信客户端，内存级直出 captureLayout"""

    RPC_HEAD = b"_uitestkit_rpc_message_head_"
    RPC_TAIL = b"_uitestkit_rpc_message_tail_"

    @classmethod
    def _find_available_port(cls) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return int(s.getsockname()[1])

    @classmethod
    def _ensure_daemon_running(cls, udid: str = "") -> bool:
        ps_res = run_hdc(["shell", "pgrep -f uitest"], udid)
        if ps_res and any(line.strip().isdigit() for line in ps_res.splitlines()):
            return True
        run_hdc(["shell", "uitest start-daemon singleness"], udid)
        time.sleep(0.25)
        return True

    @classmethod
    def _build_request_packet(cls, payload: Dict[str, Any]) -> bytes:
        json_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        session_id = random.randint(1, 0x7FFFFFFF)
        header = cls.RPC_HEAD + struct.pack(">II", session_id, len(json_bytes))
        return header + json_bytes + cls.RPC_TAIL

    @classmethod
    def capture_layout_fast(cls, udid: str = "", timeout: float = 3.5) -> Optional[Any]:
        """通过 RPC 内存高速抓取当前活动页面 UI 结构，失败时返回 None 交由 CLI 降级"""
        local_port = 0
        sock = None
        try:
            unix_socks = run_hdc(
                ["shell", "cat /proc/net/unix | grep -E 'uitest_socket|scrcpy_grpc_socket'"],
                udid,
                timeout=1.0,
            )
            if "scrcpy_grpc_socket" in unix_socks and "uitest_socket" not in unix_socks:
                return None
            if "uitest_socket" not in unix_socks:
                cls._ensure_daemon_running(udid)
            local_port = cls._find_available_port()

            fport_ret = run_hdc(["fport", f"tcp:{local_port}", "localabstract:uitest_socket"], udid)
            if "fail" in fport_ret.lower() or "error" in fport_ret.lower():
                return None

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(("127.0.0.1", local_port))

            rpc_payload = {
                "module": "com.ohos.devicetest.hypiumApiHelper",
                "method": "Captures",
                "params": {"api": "captureLayout", "args": {}},
            }
            sock.sendall(cls._build_request_packet(rpc_payload))

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
                        _, expected_body_len = struct.unpack(">II", raw_buf[head_len : head_len + 8])
                    else:
                        h_idx = raw_buf.find(cls.RPC_HEAD)
                        if h_idx != -1:
                            del raw_buf[:h_idx]
                            if len(raw_buf) >= head_len + 8:
                                _, expected_body_len = struct.unpack(">II", raw_buf[head_len : head_len + 8])

                if expected_body_len != -1 and len(raw_buf) >= head_len + 8 + expected_body_len + tail_len:
                    body_start = head_len + 8
                    body_bytes = raw_buf[body_start : body_start + expected_body_len]
                    resp_json = json.loads(body_bytes.decode("utf-8", errors="ignore"))
                    return resp_json.get("result", resp_json.get("data", resp_json))

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


# ------------------------------------------------------------------
# 鸿蒙 DOM 节点清洗与 <Web> 遮挡/透明度自愈
# ------------------------------------------------------------------
def normalize_harmony_node(node: Dict[str, Any], path_id: str = "root") -> Dict[str, Any]:
    """规范化清洗鸿蒙节点，统一 bounds 格式与唯一标识"""
    if not isinstance(node, dict):
        return {"attributes": {"type": "Unknown", "bounds": "[0,0][0,0]"}, "children": []}

    attrs = dict(node.get("attributes", {}))
    for k in (
        "type", "id", "key", "text", "originalText", "visible", "visibility",
        "hidden", "opacity", "alpha", "clip", "description", "clickable",
        "enabled", "bounds", "rect",
    ):
        if k in node and k not in attrs:
            attrs[k] = node[k]

    c_type = str(attrs.get("type") or node.get("type") or "Component")
    real_id = str(attrs.get("id") or attrs.get("key") or node.get("id") or "")
    if real_id and not real_id.startswith("win-"):
        attrs["id"] = real_id
    else:
        attrs["id"] = ""
        attrs["dom_path"] = path_id

    raw_b = attrs.get("bounds") or attrs.get("rect") or node.get("bounds") or node.get("rect")
    norm_bounds = "[0,0][0,0]"
    if isinstance(raw_b, str) and "[" in raw_b:
        norm_bounds = raw_b
    elif isinstance(raw_b, dict):
        if "left" in raw_b and "top" in raw_b:
            left, top = int(raw_b.get("left", 0)), int(raw_b.get("top", 0))
            right, bottom = int(raw_b.get("right", left)), int(raw_b.get("bottom", top))
            norm_bounds = f"[{left},{top}][{right},{bottom}]"
        elif "x" in raw_b and "y" in raw_b:
            x, y = int(raw_b.get("x", 0)), int(raw_b.get("y", 0))
            w, h = int(raw_b.get("width", 0)), int(raw_b.get("height", 0))
            norm_bounds = f"[{x},{y}][{x + w},{y + h}]"
    attrs["bounds"] = norm_bounds
    attrs["type"] = c_type

    raw_children = node.get("children", [])
    clean_children: List[Dict[str, Any]] = []
    if isinstance(raw_children, list):
        for idx, ch in enumerate(raw_children):
            clean_children.append(normalize_harmony_node(ch, f"{path_id}-{idx}"))

    return {"attributes": attrs, "children": clean_children}


def heal_harmony_web_opacity(node: Any, in_visible_web: bool = False) -> None:
    """
    修复鸿蒙 ArkUI <Web> 无障碍子树默认上报 opacity="0.000000" 导致整棵网页树被误判 occluded="true" 的问题：
    当外层 <Web> 自身可见且不透明时，将其子树中 visible="true" 但 opacity <= 0.05 的节点校正为 "1.0"。
    """
    if not isinstance(node, dict):
        return
    attrs = node.get("attributes")
    next_in_web = in_visible_web
    if isinstance(attrs, dict):
        n_type = str(attrs.get("type", "") or "")
        raw_vis = str(attrs.get("visible", "true")).strip().lower()
        try:
            op_val = float(attrs.get("opacity", "1.0"))
        except Exception:
            op_val = 1.0

        if n_type == "Web":
            next_in_web = (raw_vis not in ("false", "0")) and (op_val > 0.05)
        elif in_visible_web and raw_vis not in ("false", "0") and op_val <= 0.05:
            attrs["opacity"] = "1.0"

    for ch in node.get("children") or []:
        heal_harmony_web_opacity(ch, in_visible_web=next_in_web)


def _find_fullscreen_web_rect(node: Any, min_area: float) -> Optional[Tuple[int, int, int, int]]:
    """检测分支内是否存在覆盖面积达到阈值且活跃可见的 <Web> 实心图层"""
    if not isinstance(node, dict):
        return None
    attrs = node.get("attributes") or {}
    raw_vis = str(attrs.get("visible", "true")).strip().lower()
    if raw_vis in ("false", "0"):
        return None
    try:
        op_val = float(attrs.get("opacity", "1.0"))
    except Exception:
        op_val = 1.0
    if op_val <= 0.05:
        return None

    if str(attrs.get("type", "") or "") == "Web":
        left, top, w, h = parse_bounds_wh(str(attrs.get("bounds", "")))
        if w > 0 and h > 0 and (w * h) >= min_area:
            return (left, top, left + w, top + h)

    for ch in node.get("children") or []:
        found = _find_fullscreen_web_rect(ch, min_area)
        if found is not None:
            return found
    return None


def _mark_subtree_occluded_by_overlay(node: Any, cover_rect: Tuple[int, int, int, int]) -> None:
    """将落入上层全屏 <Web> 覆盖区内的底层节点标为不可见，防止 TextInput 免遮挡特权把底层表单撑开"""
    if not isinstance(node, dict):
        return
    attrs = node.get("attributes")
    if isinstance(attrs, dict):
        left, top, w, h = parse_bounds_wh(str(attrs.get("bounds", "")))
        cl, ct, cr, cb = cover_rect
        if w > 0 and h > 0:
            cx = left + w // 2
            cy = top + h // 2
            if cl <= cx <= cr and ct <= cy <= cb:
                attrs["visible"] = "false"
    for ch in node.get("children") or []:
        _mark_subtree_occluded_by_overlay(ch, cover_rect)


def suppress_under_fullscreen_web(node: Any, min_area: float) -> None:
    """在鸿蒙 Stack / RelativeContainer 层叠容器中，若后序兄弟包含全屏 <Web>，屏蔽其遮盖的底层兄弟"""
    if not isinstance(node, dict):
        return
    attrs = node.get("attributes") or {}
    n_type = str(attrs.get("type", "") or "")
    children = node.get("children") or []
    if n_type in ("Stack", "RelativeContainer") and len(children) > 1:
        cover_rect: Optional[Tuple[int, int, int, int]] = None
        cover_idx = -1
        for idx in range(len(children) - 1, -1, -1):
            rect = _find_fullscreen_web_rect(children[idx], min_area)
            if rect is not None:
                cover_rect = rect
                cover_idx = idx
                break
        if cover_rect is not None and cover_idx > 0:
            for prev_idx in range(cover_idx):
                _mark_subtree_occluded_by_overlay(children[prev_idx], cover_rect)
    for ch in children:
        suppress_under_fullscreen_web(ch, min_area)


def parse_harmony_layout(
    layout_path: Any,
    screen_w: int,
    screen_h: int,
    root_bounds: str,
) -> Dict[str, Any]:
    """解析鸿蒙布局文件并执行 <Web> 透明度校正与全屏覆盖层抑制"""
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
        cleaned_windows = [normalize_harmony_node(w, f"win-{i}") for i, w in enumerate(raw)]
        tree: Dict[str, Any] = {
            "attributes": {"type": "Hierarchy", "bounds": root_bounds, "origBounds": root_bounds},
            "children": cleaned_windows,
        }
    elif isinstance(raw, dict):
        tree = normalize_harmony_node(raw, "root")
    else:
        return {"attributes": {"type": "Hierarchy", "bounds": root_bounds}, "children": []}

    heal_harmony_web_opacity(tree)
    sw = screen_w if screen_w >= 600 else 1084
    sh = screen_h if screen_h >= 1000 else 2412
    suppress_under_fullscreen_web(tree, min_area=float(sw * sh) * 0.65)
    return tree


# ------------------------------------------------------------------
# 鸿蒙 DOM 多通道抓取与 scrcpy 环境维护
# ------------------------------------------------------------------
def dump_harmony_layout(
    udid: str,
    layout_file: str,
    screencast_active: bool = False,
    rpc_timeout: float = 3.5,
) -> bool:
    """鸿蒙多通道 DOM 抓取：RPC 内存直出 -> CLI dumpLayout (含重试) -> hmnextauto 兜底"""
    try:
        rpc_tree = HarmonyRpcLayoutClient.capture_layout_fast(udid, timeout=rpc_timeout)
        if rpc_tree is not None:
            with open(layout_file, "w", encoding="utf-8") as f:
                json.dump(rpc_tree, f, ensure_ascii=False)
            return True
    except Exception:
        pass

    uid = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    remote_json = f"/data/local/tmp/santiao_layout_{uid}.json"
    try:
        for attempt in range(2):
            run_hdc(["shell", f"uitest dumpLayout -p {remote_json}"], udid, timeout=4.5)
            run_hdc(["file", "recv", remote_json, layout_file], udid, timeout=4.0)
            if os.path.exists(layout_file) and os.path.getsize(layout_file) > 100:
                return True
            if attempt == 0:
                time.sleep(0.35)
    except Exception:
        pass
    finally:
        try:
            run_hdc(["shell", f"rm -f {remote_json}"], udid, timeout=1.0)
        except Exception:
            pass

    if not screencast_active:
        try:
            from hmnextauto.driver import Driver as HMDriver

            for k in list(logging.Logger.manager.loggerDict.keys()):
                if "hmnextauto" in k:
                    sub_l = logging.getLogger(k)
                    sub_l.setLevel(logging.WARNING)
                    for h in sub_l.handlers:
                        if hasattr(h, "setStream"):
                            h.setStream(sys.stdout)
            hm_client = HMDriver(serial=udid or None)
            hm_tree = hm_client.dump_hierarchy()
            if hm_tree:
                with open(layout_file, "w", encoding="utf-8") as f:
                    json.dump(hm_tree, f, ensure_ascii=False)
                return True
        except Exception:
            pass

    return False


def extract_harmony_nalu(resp_bytes: bytes) -> bytes:
    """从鸿蒙 scrcpy ReplyMessage Protobuf 字节中提取真实 H.264 NALU 数据包"""
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


def clean_harmony_scrcpy_fports(udid: str = "") -> None:
    """清理鸿蒙真机上所有指向 scrcpy_grpc_socket 的历史残留 fport 端口映射"""
    if not udid:
        return
    try:
        fport_list = run_hdc(["fport", "ls"], udid, timeout=2.0)
        if fport_list:
            for line in fport_list.splitlines():
                if "scrcpy_grpc_socket" in line and "tcp:" in line:
                    for p in line.split():
                        if p.startswith("tcp:"):
                            run_hdc(["fport", "rm", p, "localabstract:scrcpy_grpc_socket"], udid, timeout=1.0)
                            break
    except Exception:
        pass


def kill_harmony_scrcpy_daemons(udid: str = "") -> None:
    """仅精准清理 start-daemon 或 xdevice_scrcpy 守护进程，不误杀正在执行的 dumpLayout/uiInput"""
    try:
        ps_res = run_hdc(["shell", "ps -ef"], udid, timeout=2.0)
        if ps_res:
            pids_to_kill: List[str] = []
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


def ensure_harmony_scrcpy_env(udid: str = "") -> None:
    """确保鸿蒙真机已部署 agent.so 与 scrcpy_server.so 并拉起干净的守护会话"""
    if not udid:
        return

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

    try:
        chk_sc = run_hdc(["shell", "[ -f /data/local/tmp/scrcpy_server.so ] && echo 'yes' || echo 'no'"], udid, timeout=1.5)
        if "yes" not in chk_sc:
            builtin_so = SmartPathResolver.get_asset_path("desktop_app/assets/harmony/scrcpy_server.so") or ""
            candidate_so = builtin_so if os.path.isfile(builtin_so) else ""
            if not candidate_so:
                temp_dirs = [
                    os.path.join(tempfile.gettempdir(), "hokit-so"),
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp", "hokit-so"),
                ]
                for td in temp_dirs:
                    if os.path.isdir(td):
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

    try:
        run_hdc(["shell", "power-shell wakeup"], udid, timeout=1.0)
        kill_harmony_scrcpy_daemons(udid)
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
