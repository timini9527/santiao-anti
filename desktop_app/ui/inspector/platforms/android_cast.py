# -*- coding: utf-8 -*-
"""
安卓 Android 实时投屏引擎：
1. run_android_scrcpy_stream：scrcpy-server MediaCodec 60FPS H.264 直通流；
2. run_android_stream：硬件流优先，平滑降级至 uiautomator2 takeScreenshot 与内置 adb exec-out；
3. cleanup_android_stream：安全释放套接字、设备进程与 adb reverse 端口映射。
"""
import base64
import contextlib
import logging
import os
import random
import socket
import struct
import subprocess
import sys
import time
from typing import Any, Optional

from PyQt6.QtGui import QImage

from desktop_app.core.path_resolver import SmartPathResolver
from desktop_app.ui.inspector.platforms.android import resolve_adb_bin

logger = logging.getLogger("Inspector")


def cleanup_android_stream(worker: Any) -> None:
    """释放安卓 scrcpy 套接字、子进程与 reverse 端口映射"""
    if getattr(worker, "_android_conn", None):
        with contextlib.suppress(Exception):
            worker._android_conn.close()
        worker._android_conn = None
    if getattr(worker, "_android_server_sock", None):
        with contextlib.suppress(Exception):
            worker._android_server_sock.close()
        worker._android_server_sock = None
    if getattr(worker, "_android_proc", None):
        with contextlib.suppress(Exception):
            worker._android_proc.terminate()
        worker._android_proc = None
    if getattr(worker, "_android_scid", "") and worker.udid:
        try:
            adb_bin = resolve_adb_bin()
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            subprocess.run(
                [adb_bin, "-s", worker.udid, "reverse", "--remove", f"localabstract:scrcpy_{worker._android_scid}"],
                capture_output=True,
                timeout=1.5,
                creationflags=creationflags,
            )
        except Exception:
            pass
        worker._android_scid = ""


def run_android_scrcpy_stream(worker: Any, cache_cls: Any) -> bool:
    """安卓端 scrcpy-server 硬件级 H.264 60FPS 直通流"""
    import av

    creationflags = 0x08000000 if sys.platform == "win32" else 0
    udid = worker.udid

    local_jar = SmartPathResolver.get_asset_path("desktop_app/assets/android/scrcpy-server")
    if not local_jar:
        env_scrcpy = os.environ.get("SCRCPY_SERVER_PATH", "").strip()
        if env_scrcpy and os.path.isfile(env_scrcpy):
            local_jar = env_scrcpy
    if not local_jar:
        logger.warning("[安卓投屏] 未找到本地 scrcpy-server 资源，跳过硬件流")
        return False

    adb_bin = resolve_adb_bin()

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

    worker._android_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    worker._android_server_sock.bind(("127.0.0.1", 0))
    local_port = worker._android_server_sock.getsockname()[1]
    worker._android_server_sock.listen(1)
    worker._android_server_sock.settimeout(4.0)

    worker._android_scid = f"{random.randint(0x10000000, 0x7FFFFFFF):08x}"
    cmd_rev = [adb_bin]
    if udid:
        cmd_rev.extend(["-s", udid])
    cmd_rev.extend(["reverse", f"localabstract:scrcpy_{worker._android_scid}", f"tcp:{local_port}"])
    res_rev = subprocess.run(cmd_rev, capture_output=True, text=True, timeout=2.0, creationflags=creationflags)
    if res_rev.returncode != 0:
        logger.warning(f"[安卓投屏] adb reverse 失败: {res_rev.stderr}")
        return False

    cmd_start = [adb_bin]
    if udid:
        cmd_start.extend(["-s", udid])
    cmd_start.extend([
        "shell",
        f"CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / com.genymobile.scrcpy.Server 3.3.4 "
        f"scid={worker._android_scid} log_level=info video=true audio=false control=false cleanup=false "
        f"tunnel_forward=false max_size=1080 video_bit_rate=4000000 max_fps=60",
    ])
    worker._android_proc = subprocess.Popen(
        cmd_start,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    try:
        worker._android_conn, _ = worker._android_server_sock.accept()
        worker._android_conn.settimeout(5.0)
        with contextlib.suppress(Exception):
            worker._android_conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            worker._android_conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
    except Exception as e:
        logger.warning(f"[安卓投屏] scrcpy 回连超时或失败: {e}")
        return False

    try:
        worker._android_conn.recv(64)
        worker._android_conn.recv(12)
    except Exception as e:
        logger.warning(f"[安卓投屏] 协议头读取失败: {e}")
        return False

    codec = av.CodecContext.create("h264", "r")
    with contextlib.suppress(Exception):
        codec.thread_type = "SLICE"
    with contextlib.suppress(Exception):
        codec.options = {"flags": "low_delay"}

    last_emit_t = 0.0
    has_emitted_first_frame = False

    def recv_exact(sock: socket.socket, n: int) -> Optional[bytes]:
        buf = bytearray()
        while len(buf) < n:
            if not worker._is_running:
                return None
            chunk = sock.recv(min(65536, n - len(buf)))
            if not chunk:
                return None
            buf.extend(chunk)
        return bytes(buf)

    try:
        while worker._is_running:
            hdr = recv_exact(worker._android_conn, 12)
            if not hdr or len(hdr) < 12:
                break
            _, sz = struct.unpack(">QI", hdr)
            if sz == 0:
                continue
            packet_data = recv_exact(worker._android_conn, sz)
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

            if newest_frame is not None and worker._is_running:
                now = time.time()
                if (worker.ui_ready or (now - last_emit_t >= 0.05)) and (now - last_emit_t >= 0.016):
                    last_emit_t = now
                    worker.ui_ready = False
                    rgb_array = newest_frame.to_ndarray(format="rgb24")
                    h, w, _ = rgb_array.shape
                    qimg = QImage(rgb_array.tobytes(), w, h, 3 * w, QImage.Format.Format_RGB888).copy()
                    cache_cls.latest_image = qimg
                    cache_cls.latest_frame_time = now
                    cache_cls.latest_udid = worker.udid
                    worker.frame_ready.emit(qimg, b"")
                    if not has_emitted_first_frame:
                        has_emitted_first_frame = True
                        worker.state_changed.emit(True, "投屏已连接")
    except Exception as e:
        logger.warning(f"[安卓投屏] 解码循环异常中断: {e}")
    finally:
        cleanup_android_stream(worker)

    return True


def run_android_stream(worker: Any, cache_cls: Any) -> None:
    """安卓投屏总调度：scrcpy 硬件流 -> uiautomator2 takeScreenshot -> adb exec-out"""
    cache_cls.is_active = True
    creationflags = 0x08000000 if sys.platform == "win32" else 0
    adb_bin = resolve_adb_bin()

    try:
        while worker._is_running:
            try:
                ok = run_android_scrcpy_stream(worker, cache_cls)
                if ok and not worker._is_running:
                    return
            except Exception as e:
                logger.warning(f"[安卓投屏] scrcpy 硬件流异常: {e}")
            break

        if not worker._is_running:
            return

        u2_device = None
        try:
            import uiautomator2 as u2

            u2_device = u2.connect(worker.udid) if worker.udid else u2.connect()
        except Exception as e:
            logger.warning(f"[安卓投屏] uiautomator2 初始化异常: {e}")

        emitted_any = False
        while worker._is_running:
            qimg = None
            raw_bytes = b""
            now = time.time()

            if u2_device is not None:
                try:
                    b64 = u2_device.jsonrpc.takeScreenshot(1, 55)
                    if b64:
                        raw_bytes = base64.b64decode(b64)
                        if raw_bytes:
                            qimg = QImage.fromData(raw_bytes, "JPEG")
                except Exception:
                    try:
                        import uiautomator2 as u2

                        u2_device = u2.connect(worker.udid) if worker.udid else u2.connect()
                    except Exception:
                        u2_device = None

            if (qimg is None or qimg.isNull()) and worker._is_running:
                try:
                    cmd_sc = [adb_bin]
                    if worker.udid:
                        cmd_sc.extend(["-s", worker.udid])
                    cmd_sc.extend(["exec-out", "screencap", "-p"])
                    res = subprocess.run(
                        cmd_sc,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        timeout=2.0,
                        creationflags=creationflags,
                    )
                    if res.stdout and len(res.stdout) > 1000:
                        raw_bytes = res.stdout
                        qimg = QImage.fromData(raw_bytes, "PNG")
                except Exception:
                    pass

            if qimg is not None and not qimg.isNull() and worker._is_running:
                cache_cls.latest_image = qimg
                cache_cls.latest_frame_time = now
                cache_cls.latest_udid = worker.udid
                if raw_bytes:
                    cache_cls.latest_frame_bytes = raw_bytes
                if not emitted_any:
                    emitted_any = True
                    worker.state_changed.emit(True, "投屏已连接")
                worker.frame_ready.emit(qimg, raw_bytes)

            time.sleep(0.005)
    finally:
        cache_cls.is_active = False
