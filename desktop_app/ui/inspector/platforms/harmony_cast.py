# -*- coding: utf-8 -*-
"""
鸿蒙 HarmonyOS NEXT 实时投屏与单帧静默抓取引擎：
1. capture_harmony_single_silent_frame：通过 scrcpy_server.so 硬件录屏通道按需抓取单帧（0 截屏广播）；
2. run_harmony_scrcpy_stream：gRPC + H.264 硬件录屏流循环；
3. run_harmony_stream：断线自愈与端口回收包装循环；
4. cleanup_harmony_port：释放 gRPC 通道与 HDC fport 端口映射。
"""
import contextlib
import logging
import threading
import time
from typing import Any, Optional

from PyQt6.QtCore import QBuffer, QByteArray
from PyQt6.QtGui import QImage

from desktop_app.ui.inspector.platforms.harmony import (
    HarmonyRpcLayoutClient,
    clean_harmony_scrcpy_fports,
    ensure_harmony_scrcpy_env,
    extract_harmony_nalu,
    run_hdc,
)

logger = logging.getLogger("Inspector")


def cleanup_harmony_port(worker: Any) -> None:
    """安全释放鸿蒙 gRPC 通道与 HDC 端口转发"""
    if getattr(worker, "_grpc_channel", None):
        with contextlib.suppress(Exception):
            worker._grpc_channel.close()
        worker._grpc_channel = None
    if getattr(worker, "_local_port", 0) > 0 and worker.udid:
        with contextlib.suppress(Exception):
            run_hdc(
                ["fport", "rm", f"tcp:{worker._local_port}", "localabstract:scrcpy_grpc_socket"],
                worker.udid,
                timeout=1.5,
            )
        worker._local_port = 0


def capture_harmony_single_silent_frame(cache_cls: Any, udid: str = "", timeout: float = 4.5) -> Optional[bytes]:
    """鸿蒙硬件录屏通道按需抓取单帧图像（0 截屏广播）"""
    import av
    import grpc

    if cache_cls.latest_frame_bytes and (time.time() - cache_cls.latest_frame_time < 4.0):
        return cache_cls.latest_frame_bytes

    ensure_harmony_scrcpy_env(udid)

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
            response_deserializer=lambda x: x,
        )
        req_idr = channel.unary_unary(
            "/ScrcpyService/onRequestIDRFrame",
            request_serializer=lambda x: b"",
            response_deserializer=lambda x: x,
        )
        stream = start_stream(b"")

        def send_idr() -> None:
            time.sleep(0.12)
            with contextlib.suppress(Exception):
                req_idr(b"")

        threading.Thread(target=send_idr, daemon=True).start()

        captured_bytes: Optional[bytes] = None
        codec = av.CodecContext.create("h264", "r")

        def stream_reader() -> None:
            nonlocal captured_bytes
            try:
                for resp in stream:
                    nalu = extract_harmony_nalu(resp)
                    if not nalu:
                        continue
                    for packet in codec.parse(nalu):
                        for f in codec.decode(packet):
                            rgb_array = f.to_ndarray(format="rgb24")
                            h, w, _ = rgb_array.shape
                            qimg = QImage(bytes(rgb_array.data), w, h, 3 * w, QImage.Format.Format_RGB888).copy()
                            buf = QByteArray()
                            buffer_io = QBuffer(buf)
                            buffer_io.open(QBuffer.OpenModeFlag.WriteOnly)
                            qimg.save(buffer_io, "JPEG", 85)
                            captured_bytes = bytes(buf)
                            cache_cls.latest_image = qimg
                            cache_cls.latest_frame_bytes = captured_bytes
                            cache_cls.latest_frame_time = time.time()
                            cache_cls.latest_udid = udid
                            return
            except Exception:
                pass

        read_thread = threading.Thread(target=stream_reader, daemon=True)
        read_thread.start()
        read_thread.join(timeout=timeout)
        return captured_bytes
    except Exception:
        return None
    finally:
        if channel:
            with contextlib.suppress(Exception):
                channel.close()
        if port > 0 and udid:
            with contextlib.suppress(Exception):
                run_hdc(["fport", "rm", f"tcp:{port}", "localabstract:scrcpy_grpc_socket"], udid, timeout=1.0)


def run_harmony_scrcpy_stream(worker: Any, cache_cls: Any) -> bool:
    """鸿蒙原生硬件录屏流引擎 (gRPC + H.264)"""
    import av
    import grpc

    clean_harmony_scrcpy_fports(worker.udid)
    ensure_harmony_scrcpy_env(worker.udid)

    socket_ready = False
    for _ in range(30):
        chk = run_hdc(["shell", "cat /proc/net/unix | grep scrcpy_grpc_socket"], worker.udid, timeout=1.0)
        if "scrcpy_grpc_socket" in chk:
            socket_ready = True
            break
        time.sleep(0.1)
    if not socket_ready:
        logger.warning("[投屏引擎] 守护进程 unix socket 初始化超时或已退出")
        worker.error_occurred.emit("鸿蒙底层投屏服务未能就绪，请确认设备屏幕已解锁并授权调试。")
        return False

    worker._local_port = HarmonyRpcLayoutClient._find_available_port()
    fport_res = run_hdc(
        ["fport", f"tcp:{worker._local_port}", "localabstract:scrcpy_grpc_socket"],
        worker.udid,
        timeout=2.0,
    )
    if "fail" in fport_res.lower() or "error" in fport_res.lower():
        worker.error_occurred.emit("鸿蒙投屏端口映射建立失败")
        return False

    try:
        worker._grpc_channel = grpc.insecure_channel(f"127.0.0.1:{worker._local_port}")
        start_stream = worker._grpc_channel.unary_stream(
            "/ScrcpyService/onStart",
            request_serializer=lambda x: b"",
            response_deserializer=lambda x: x,
        )
        req_idr = worker._grpc_channel.unary_unary(
            "/ScrcpyService/onRequestIDRFrame",
            request_serializer=lambda x: b"",
            response_deserializer=lambda x: x,
        )
        stream = start_stream(b"")
    except Exception as e:
        logger.warning(f"[投屏引擎] gRPC 连接建立异常: {e}")
        worker.error_occurred.emit(f"连接鸿蒙投屏通道失败: {e}")
        return False

    has_emitted_first_frame = False

    def request_idr_task() -> None:
        for _ in range(5):
            if has_emitted_first_frame or not worker._is_running:
                break
            time.sleep(0.1)
            with contextlib.suppress(Exception):
                req_idr(b"")

    threading.Thread(target=request_idr_task, daemon=True).start()

    codec = av.CodecContext.create("h264", "r")
    last_emit_t = 0.0

    try:
        for resp in stream:
            if not worker._is_running:
                break
            nalu = extract_harmony_nalu(resp)
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
            except Exception:
                pass
    except Exception:
        pass

    return has_emitted_first_frame or (not worker._is_running)


def run_harmony_stream(worker: Any, cache_cls: Any) -> None:
    """鸿蒙投屏主循环（含断线自愈与端口清理）"""
    cache_cls.is_active = True
    try:
        while worker._is_running:
            try:
                ok = run_harmony_scrcpy_stream(worker, cache_cls)
                if not ok:
                    break
            except Exception as e:
                logger.warning(f"[投屏引擎] 录屏流自愈重试: {e}")
            finally:
                cleanup_harmony_port(worker)

            if worker._is_running:
                time.sleep(0.3)
    finally:
        cache_cls.is_active = False
