# -*- coding: utf-8 -*-
"""
苹果 iOS 实时投屏、CoreDevice HID 派发与单帧静默截屏引擎：
1. release_all_ios_tunnels / dispatch_ios_hid / capture_single_ios_frame；
2. run_ios_pymobiledevice3_stream：iOS 17+ CoreDevice HEVC + DVT 开发者免录屏通道；
3. run_ios_legacy_fallback_stream：WDA MJPEG (9100) + WDA /screenshot 轮询 + 进程内 DVT/ScreenshotService；
4. run_ios_stream：按系统版本与 WDA 在线状态智能选路与锁治理。
"""
import asyncio
import base64
import contextlib
import json
import logging
import queue
import subprocess
import sys
import threading
import time
import urllib.request
from typing import Any, List, Optional, Tuple

from PyQt6.QtCore import QBuffer, QByteArray
from PyQt6.QtGui import QImage

from desktop_app.ui.inspector.platforms.ios_service import IosWdaManager, _resolve_tidevice_cmd

logger = logging.getLogger("Inspector")


def release_all_ios_tunnels() -> None:
    """强制清理并重置残留的 userspace_tunnel 句柄与单例状态"""
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


def dispatch_ios_hid(cache_cls: Any, action: str, **kwargs: Any) -> bool:
    """通过活跃的 pymobiledevice3 ScreenStreamServer 异步派发 CoreDevice HID 触控与按键事件"""
    server = cache_cls._active_ios_server
    loop = cache_cls._active_ios_loop
    if server is None or loop is None or not cache_cls.is_active:
        return False

    def _norm_coord(x_val: float, y_val: float) -> Tuple[int, int]:
        ref_w, ref_h = 390.0, 844.0
        if cache_cls.latest_image is not None and not cache_cls.latest_image.isNull():
            iw, ih = float(cache_cls.latest_image.width()), float(cache_cls.latest_image.height())
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
        if action == "home":
            payload = json.dumps({"name": "home", "state": "press"}).encode("utf-8")
            loop.call_soon_threadsafe(server._hid_queue.put_nowait, ("/button", payload))
            return True
        if action == "swipe":
            x1, y1 = float(kwargs.get("x1", 0)), float(kwargs.get("y1", 0))
            x2, y2 = float(kwargs.get("x2", 0)), float(kwargs.get("y2", 0))
            ref_w, ref_h = 390.0, 844.0
            if cache_cls.latest_image is not None and not cache_cls.latest_image.isNull():
                iw, ih = float(cache_cls.latest_image.width()), float(cache_cls.latest_image.height())
                if max(x1, x2) > 440 or max(y1, y2) > 960:
                    ref_w, ref_h = iw, ih
            hx1 = max(0, min(65535, int(round((x1 / max(1.0, ref_w)) * 65535.0))))
            hy1 = max(0, min(65535, int(round((y1 / max(1.0, ref_h)) * 65535.0))))
            hx2 = max(0, min(65535, int(round((x2 / max(1.0, ref_w)) * 65535.0))))
            hy2 = max(0, min(65535, int(round((y2 / max(1.0, ref_h)) * 65535.0))))
            dur = max(0.1, float(kwargs.get("duration", 0.3)))

            async def _async_swipe() -> None:
                steps = 12
                for i in range(steps + 1):
                    t = i / steps
                    cx = int(round(hx1 + (hx2 - hx1) * t))
                    cy = int(round(hy1 + (hy2 - hy1) * t))
                    server._hid_queue.put_nowait(
                        ("/touch", json.dumps({"type": "contact", "x": cx, "y": cy}).encode("utf-8"))
                    )
                    await asyncio.sleep(dur / steps)
                server._hid_queue.put_nowait(
                    ("/touch", json.dumps({"type": "release", "x": hx2, "y": hy2}).encode("utf-8"))
                )

            asyncio.run_coroutine_threadsafe(_async_swipe(), loop)
            return True
    except Exception:
        pass
    return False


def capture_single_ios_frame(cache_cls: Any, udid: str = "", timeout: float = 4.5) -> Optional[bytes]:
    """iOS CoreDevice 单帧静默截屏（优先复用投屏内存帧，避免隧道冲突）"""
    if cache_cls.latest_image is not None and not cache_cls.latest_image.isNull():
        if not udid or not cache_cls.latest_udid or cache_cls.latest_udid == udid:
            if cache_cls.is_active or (time.time() - cache_cls.latest_frame_time < 5.0):
                return cache_cls.get_latest_jpeg_bytes(udid)

    if cache_cls.is_active:
        for _ in range(40):
            if cache_cls.latest_image is not None and (not udid or cache_cls.latest_udid == udid):
                return cache_cls.get_latest_jpeg_bytes(udid)
            time.sleep(0.05)
        return cache_cls.get_latest_jpeg_bytes(udid)

    acquired = cache_cls._ios_tunnel_lock.acquire(blocking=False)
    if not acquired:
        for _ in range(30):
            if cache_cls.latest_image is not None and (not udid or cache_cls.latest_udid == udid):
                return cache_cls.get_latest_jpeg_bytes(udid)
            time.sleep(0.05)
        return cache_cls.get_latest_jpeg_bytes(udid)

    target_udid = udid if (udid and not udid.startswith("wda_localhost")) else None

    async def _capture_one_frame_async() -> Optional[bytes]:
        import av
        from pymobiledevice3.remote import userspace_tunnel
        from pymobiledevice3.remote.core_device.display_service import DisplayService
        from pymobiledevice3.remote.core_device.screen_stream import ScreenStreamServer, _SubState
        from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel

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

            async def _silent_audio(transport) -> None:
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
                cache_cls.latest_image = qimg
                cache_cls.latest_frame_bytes = bytes(buf)
                cache_cls.latest_frame_time = time.time()
                cache_cls.latest_udid = udid
                return bytes(buf)
            return None
        except Exception as e:
            logger.debug(f"[iOS单帧截屏] 异常: {e}")
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
        cache_cls._ios_tunnel_lock.release()


def run_ios_pymobiledevice3_stream(worker: Any, cache_cls: Any) -> bool:
    """iOS 17+ CoreDevice / DVT 双线程硬件解码投屏主引擎"""
    import av

    try:
        from pymobiledevice3.remote import userspace_tunnel
        from pymobiledevice3.remote.core_device.display_service import DisplayService, is_media_in_use_error
        from pymobiledevice3.remote.core_device.screen_stream import ScreenStreamServer, _SubState
        from pymobiledevice3.tunneld.api import get_tunneld_device_by_udid
    except Exception as e:
        logger.warning(f"[iOS投屏] pymobiledevice3 依赖未就绪，切换备选方案: {e}")
        return False

    target_udid = worker.udid if (worker.udid and not worker.udid.startswith("wda_localhost")) else None
    emitted_any_frame = False
    decode_q: "queue.Queue[Optional[Tuple[int, bytes]]]" = queue.Queue(maxsize=90)

    def _hevc_decode_worker() -> None:
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

        while worker._is_running and not stop_decode:
            try:
                first_item = decode_q.get(timeout=0.15)
            except queue.Empty:
                continue
            if first_item is None:
                break

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
                if not worker._is_running:
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

            if newest_frame is not None and worker._is_running:
                now = time.time()
                if (worker.ui_ready or (now - last_emit_t >= 0.035)) and (now - last_emit_t >= 0.012):
                    try:
                        last_emit_t = now
                        worker.ui_ready = False
                        if newest_frame.width > 720:
                            out_w = (newest_frame.width // 2) & ~1
                            out_h = (newest_frame.height // 2) & ~1
                            bgr_frame = newest_frame.reformat(width=out_w, height=out_h, format="bgra")
                        else:
                            bgr_frame = newest_frame.reformat(format="bgra")
                        plane = bgr_frame.planes[0]
                        qimg = QImage(
                            bytes(plane), bgr_frame.width, bgr_frame.height, plane.line_size, QImage.Format.Format_RGB32
                        ).copy()
                        cache_cls.latest_image = qimg
                        cache_cls.latest_frame_bytes = None
                        cache_cls.latest_frame_time = now
                        cache_cls.latest_udid = worker.udid
                        if not emitted_any_frame:
                            emitted_any_frame = True
                            worker.state_changed.emit(True, "投屏已连接")
                        worker.frame_ready.emit(qimg, b"")
                    except Exception as dec_err:
                        logger.debug(f"[iOS投屏] 帧转换异常: {dec_err}")
                        worker.ui_ready = True

    async def _pymobiledevice3_session() -> bool:
        nonlocal emitted_any_frame
        if not worker._is_running:
            return True

        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()
        rsd = None
        owned_tunnel = None
        from_tunneld = False
        server: Optional[ScreenStreamServer] = None
        bg_tasks: List[asyncio.Task] = []

        def _threadsafe_stop() -> None:
            def _do_stop() -> None:
                if not stop_event.is_set():
                    stop_event.set()

            with contextlib.suppress(Exception):
                loop.call_soon_threadsafe(_do_stop)

        worker._ios_stop_hook = _threadsafe_stop

        decode_thread = threading.Thread(target=_hevc_decode_worker, name="IOSPyAVDecodeThread", daemon=True)
        decode_thread.start()

        try:
            if target_udid:
                with contextlib.suppress(Exception):
                    rsd = await asyncio.wait_for(get_tunneld_device_by_udid(target_udid), timeout=0.5)
                    if rsd is not None:
                        from_tunneld = True

            if rsd is None:
                for attr_name in ("_active_tunnel", "_cli_tunnel"):
                    prev_tun = getattr(userspace_tunnel, attr_name, None)
                    if prev_tun is not None:
                        with contextlib.suppress(Exception):
                            await asyncio.wait_for(prev_tun.aclose(), timeout=1.5)
                        setattr(userspace_tunnel, attr_name, None)
                userspace_tunnel.USERSPACE_ACTIVE = False

                for attempt in range(3):
                    try:
                        owned_tunnel = userspace_tunnel.UserspaceRsdTunnel(
                            serial=target_udid, autopair=True, remotepairing_fallback=False
                        )
                        rsd = await asyncio.wait_for(owned_tunnel.aopen(), timeout=8.0)
                        break
                    except Exception as open_err:
                        err_str = str(open_err)
                        if ("already active" in err_str or "ARP Cache" in err_str or "RemoteXPC" in err_str) and attempt < 2:
                            logger.info(f"[iOS投屏] 检测到隧道/端口残留冲突，重置自愈 ({attempt + 1}/3)...")
                            for attr_name in ("_active_tunnel", "_cli_tunnel"):
                                setattr(userspace_tunnel, attr_name, None)
                            userspace_tunnel.USERSPACE_ACTIVE = False
                            await asyncio.sleep(0.8)
                        else:
                            raise

            if not worker._is_running or rsd is None:
                return True

            try:
                from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
                from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

                logger.info("[iOS投屏] 正在建立 DVT 开发者免录屏检测直连通道...")
                async with DvtProvider(rsd) as dvt, Screenshot(dvt) as sc:
                    if not worker._is_running:
                        return True
                    last_emit_t = 0.0
                    while worker._is_running and not stop_event.is_set():
                        raw_bytes = await sc.get_screenshot()
                        if raw_bytes and worker._is_running:
                            now = time.time()
                            if worker.ui_ready or (now - last_emit_t >= 0.03):
                                last_emit_t = now
                                worker.ui_ready = False
                                qimg = QImage.fromData(raw_bytes, "PNG")
                                if qimg and not qimg.isNull():
                                    cache_cls.latest_image = qimg
                                    cache_cls.latest_frame_time = now
                                    cache_cls.latest_udid = worker.udid
                                    cache_cls.latest_frame_bytes = raw_bytes
                                    if not emitted_any_frame:
                                        emitted_any_frame = True
                                        worker.state_changed.emit(True, "投屏已连接 (DVT免录屏屏蔽通道)")
                                    worker.frame_ready.emit(qimg, b"")
                        await asyncio.sleep(0.01)
                    return emitted_any_frame or (not worker._is_running)
            except Exception as dvt_err:
                logger.info(f"[iOS投屏] DVT 免录屏通道暂不可用，降级尝试媒体流通道: {dvt_err}")

            server = ScreenStreamServer(
                rsd=rsd,
                audio_default_on=False,
                motion_idr=False,
                rctl_enabled=True,
                allow_rtcp_fb=False,
                ltrp_enabled=False,
            )

            async def _silent_audio_udp_drain(transport) -> None:
                while worker._is_running and not stop_event.is_set():
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

            sub_q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=90)
            sub_state = _SubState()
            sub_state.needs_key = True
            sub_state.reset_on_key = True
            sub_state.needs_key_since = loop.time()
            server._subscribers[sub_q] = sub_state

            await asyncio.wait_for(server._eager_stream_start(), timeout=15.0)
            if server._active_service is None:
                logger.info("[iOS投屏] 当前设备未提供原生 startmediastream 硬件视频流，就地切入 DVT 通道")
                from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
                from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

                async with DvtProvider(rsd) as dvt, Screenshot(dvt) as sc:
                    if not worker._is_running:
                        return True
                    last_emit_t = 0.0
                    while worker._is_running and not stop_event.is_set():
                        raw_bytes = await sc.get_screenshot()
                        if raw_bytes and worker._is_running:
                            now = time.time()
                            if worker.ui_ready or (now - last_emit_t >= 0.03):
                                last_emit_t = now
                                worker.ui_ready = False
                                qimg = QImage.fromData(raw_bytes, "PNG")
                                if qimg and not qimg.isNull():
                                    cache_cls.latest_image = qimg
                                    cache_cls.latest_frame_time = now
                                    cache_cls.latest_udid = worker.udid
                                    cache_cls.latest_frame_bytes = raw_bytes
                                    if not emitted_any_frame:
                                        emitted_any_frame = True
                                        worker.state_changed.emit(True, "投屏已连接 (DVT开发者通道)")
                                    worker.frame_ready.emit(qimg, b"")
                        await asyncio.sleep(0.01)
                    return emitted_any_frame or (not worker._is_running)

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

            cache_cls._active_ios_server = server
            cache_cls._active_ios_loop = loop

            while worker._is_running and not stop_event.is_set():
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

            return emitted_any_frame or (not worker._is_running)

        except Exception as exc:
            worker._last_ios_error = str(exc)
            if is_media_in_use_error(exc):
                worker.error_occurred.emit("iPhone 相机或麦克风正被前台应用占用，请退出该应用后重新开启投屏")
                return True
            logger.warning(f"[iOS投屏] pymobiledevice3 视频流异常退出: {exc}")
            return emitted_any_frame
        finally:
            cache_cls._active_ios_server = None
            cache_cls._active_ios_loop = None
            worker._ios_stop_hook = None
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
        logger.warning(f"[iOS投屏] pymobiledevice3 事件循环退出: {e}")
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


def run_ios_legacy_fallback_stream(worker: Any, cache_cls: Any, is_ios_17_plus: bool = True) -> bool:
    """WDA MJPEG (9100) -> WDA /screenshot 轮询 -> 进程内 DvtProvider/ScreenshotService"""
    emitted_any = False
    wda_url, _ = IosWdaManager.get_wda_url(worker.udid, allow_spawn=False)
    if not wda_url:
        wda_url = "http://127.0.0.1:8100"

    if worker.udid and not worker.udid.startswith("wda_localhost"):
        relay_cmd = _resolve_tidevice_cmd(worker.udid, "relay", "9100", "9100")
        if relay_cmd:
            try:
                IosWdaManager.kill_relays((9100,))
                creationflags = 0x08000000 if sys.platform == "win32" else 0
                worker._ios_mjpeg_relay_proc = subprocess.Popen(
                    relay_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                time.sleep(0.25)
            except Exception:
                pass

    wda_online = IosWdaManager.test_wda_status(wda_url, timeout=0.25)
    if wda_online:
        try:
            settings_payload = json.dumps({
                "settings": {
                    "mjpegServerFramerate": 60,
                    "mjpegServerScreenshotQuality": 30,
                    "mjpegScalingFactor": 60,
                    "screenshotQuality": 2,
                }
            }).encode("utf-8")
            set_req = urllib.request.Request(
                f"{wda_url}/appium/settings",
                data=settings_payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(set_req, timeout=0.8):
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
            if not worker._is_running:
                break
            try:
                resp = urllib.request.urlopen(urllib.request.Request(test_url), timeout=0.8)
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
                    while worker._is_running:
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

                        if latest_jpg and worker._is_running:
                            now = time.time()
                            if (worker.ui_ready or (now - last_emit_t >= 0.04)) and (now - last_emit_t >= 0.016):
                                last_emit_t = now
                                worker.ui_ready = False
                                qimg = QImage.fromData(latest_jpg, "JPEG")
                                if qimg and not qimg.isNull():
                                    cache_cls.latest_image = qimg
                                    cache_cls.latest_frame_time = now
                                    cache_cls.latest_udid = worker.udid
                                    cache_cls.latest_frame_bytes = latest_jpg
                                    if not emitted_any:
                                        emitted_any = True
                                        worker.state_changed.emit(True, "投屏已连接 (WDA MJPEG 通道)")
                                    worker.frame_ready.emit(qimg, b"")
                if emitted_any:
                    return True
            except Exception:
                pass

    if not worker._is_running:
        return emitted_any

    if IosWdaManager.test_wda_status(wda_url, timeout=0.6) and worker._is_running:
        last_poll_t = 0.0
        consecutive_errors = 0
        while worker._is_running:
            try:
                now = time.time()
                if worker.ui_ready or (now - last_poll_t >= 0.035):
                    last_poll_t = now
                    req = urllib.request.Request(f"{wda_url}/screenshot", headers={"Accept": "application/json"})
                    with urllib.request.urlopen(req, timeout=1.2) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            b64_img = data.get("value", "")
                            if b64_img:
                                raw_bytes = base64.b64decode(b64_img)
                                qimg = QImage.fromData(raw_bytes)
                                if qimg and not qimg.isNull() and worker._is_running:
                                    worker.ui_ready = False
                                    cache_cls.latest_image = qimg
                                    cache_cls.latest_frame_time = now
                                    cache_cls.latest_udid = worker.udid
                                    cache_cls.latest_frame_bytes = raw_bytes
                                    if not emitted_any:
                                        emitted_any = True
                                        worker.state_changed.emit(True, "投屏已连接 (WDA自动化通道)")
                                    worker.frame_ready.emit(qimg, b"")
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

    if not worker._is_running:
        return emitted_any

    async def _run_in_process_dvt() -> bool:
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.remote import userspace_tunnel
        from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
        from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

        udid = worker.udid if (worker.udid and not worker.udid.startswith("wda_localhost")) else None
        provider = None
        owned_tunnel = None
        local_emitted = False
        try:
            if is_ios_17_plus:
                try:
                    for attr_name in ("_active_tunnel", "_cli_tunnel"):
                        setattr(userspace_tunnel, attr_name, None)
                    userspace_tunnel.USERSPACE_ACTIVE = False
                    owned_tunnel = userspace_tunnel.UserspaceRsdTunnel(
                        serial=udid, autopair=True, remotepairing_fallback=False
                    )
                    provider = await asyncio.wait_for(owned_tunnel.aopen(), timeout=2.5)
                except Exception:
                    provider = None

            if provider is None:
                provider = await create_using_usbmux(serial=udid)

            try:
                async with DvtProvider(provider) as dvt, Screenshot(dvt) as sc:
                    last_emit_t = 0.0
                    while worker._is_running:
                        raw_bytes = await sc.get_screenshot()
                        if raw_bytes and worker._is_running:
                            now = time.time()
                            if worker.ui_ready or (now - last_emit_t >= 0.03):
                                last_emit_t = now
                                worker.ui_ready = False
                                qimg = QImage.fromData(raw_bytes, "PNG")
                                if qimg and not qimg.isNull():
                                    cache_cls.latest_image = qimg
                                    cache_cls.latest_frame_time = now
                                    cache_cls.latest_udid = worker.udid
                                    cache_cls.latest_frame_bytes = raw_bytes
                                    if not local_emitted:
                                        local_emitted = True
                                        worker.state_changed.emit(True, "投屏已连接 (DVT开发者通道)")
                                    worker.frame_ready.emit(qimg, b"")
                        await asyncio.sleep(0.01)
            except Exception:
                if not local_emitted and not is_ios_17_plus and worker._is_running:
                    try:
                        from pymobiledevice3.services.screenshot import ScreenshotService

                        sc_svc = ScreenshotService(provider)
                        last_emit_t = 0.0
                        while worker._is_running:
                            raw_bytes = await sc_svc.take_screenshot()
                            if raw_bytes and worker._is_running:
                                now = time.time()
                                if worker.ui_ready or (now - last_emit_t >= 0.04):
                                    last_emit_t = now
                                    worker.ui_ready = False
                                    qimg = QImage.fromData(raw_bytes, "PNG")
                                    if qimg and not qimg.isNull():
                                        cache_cls.latest_image = qimg
                                        cache_cls.latest_frame_time = now
                                        cache_cls.latest_udid = worker.udid
                                        cache_cls.latest_frame_bytes = raw_bytes
                                        if not local_emitted:
                                            local_emitted = True
                                            worker.state_changed.emit(True, "投屏已连接 (原生截屏通道)")
                                        worker.frame_ready.emit(qimg, b"")
                            await asyncio.sleep(0.01)
                    except Exception:
                        pass
            return local_emitted or (not worker._is_running)
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
        logger.warning(f"[iOS备选投屏] DvtProvider 通道退出: {e}")
        return False
    finally:
        mjpeg_proc = getattr(worker, "_ios_mjpeg_relay_proc", None)
        if mjpeg_proc is not None:
            try:
                mjpeg_proc.terminate()
                mjpeg_proc.wait(timeout=0.5)
            except Exception:
                try:
                    mjpeg_proc.kill()
                except Exception:
                    pass
            worker._ios_mjpeg_relay_proc = None


def run_ios_stream(worker: Any, cache_cls: Any) -> None:
    """iOS 投屏总调度器（按系统版本与 WDA 状态选路，严格守卫隧道锁与 is_active）"""
    IosWdaManager.kill_relays()
    acquired_lock = cache_cls._ios_tunnel_lock.acquire(blocking=True, timeout=3.5)
    if not acquired_lock:
        release_all_ios_tunnels()
        acquired_lock = cache_cls._ios_tunnel_lock.acquire(blocking=True, timeout=2.0)
        if not acquired_lock:
            logger.warning(f"[iOS投屏] 设备 {worker.udid} 隧道锁正被占用")
            worker.error_occurred.emit("iOS 投屏通道正忙，请稍候再试")
            return

    cache_cls.is_active = True
    try:
        is_ios_17_plus = True
        if worker.udid and not worker.udid.startswith("wda_localhost"):
            try:
                ver_str = IosWdaManager.get_device_product_version(worker.udid)
                if ver_str and int(ver_str.split(".")[0]) < 17:
                    is_ios_17_plus = False
                    logger.info(f"[iOS投屏] 设备 {worker.udid} 系统版本为 iOS {ver_str} (< 17)，直接启用 USB/WDA 投屏")
            except Exception:
                pass

        ok = False
        if IosWdaManager.test_wda_status("http://127.0.0.1:8100", timeout=0.25):
            logger.info("[iOS投屏] 检测到 WDA 8100 就绪，优先复用 WDA 串流通道")
            ok = bool(run_ios_legacy_fallback_stream(worker, cache_cls, is_ios_17_plus=is_ios_17_plus))

        if not ok and worker._is_running and is_ios_17_plus:
            ok = run_ios_pymobiledevice3_stream(worker, cache_cls)

        if not worker._is_running:
            return

        if not ok and worker._is_running:
            ok = bool(run_ios_legacy_fallback_stream(worker, cache_cls, is_ios_17_plus=is_ios_17_plus))

        if not ok and worker._is_running:
            online_serials: List[str] = []
            with contextlib.suppress(Exception):
                from pymobiledevice3.usbmux import list_devices as pmd_list_devices

                mux_devs = asyncio.run(asyncio.wait_for(pmd_list_devices(), timeout=1.0))
                online_serials = [str(getattr(m, "serial", "") or "") for m in (mux_devs or [])]

            if worker.udid and worker.udid not in online_serials:
                worker.error_occurred.emit(
                    f"未检测到设备 {worker.udid} 的USB物理连接，请确认数据线插紧并点击 [🔄] 刷新列表"
                )
            else:
                last_err = getattr(worker, "_last_ios_error", "")
                is_trust_issue = any(
                    k in last_err.lower()
                    for k in ("not paired", "passwordprotected", "pairingdialog", "trust", "invalidhostid")
                )
                if is_trust_issue:
                    worker.error_occurred.emit(
                        "未能从 iPhone 获取投屏画面：请确认屏幕已【点亮并解锁】，且已在手机上点击【信任此电脑】"
                    )
                elif last_err:
                    worker.error_occurred.emit(f"未能建立 iOS 投屏通道 ({last_err})，请重新点击【实时投屏】开启")
                else:
                    worker.error_occurred.emit("未能建立 iOS 投屏通道，请确认手机已点亮解锁并点击 [🔄] 刷新设备")
    finally:
        cache_cls.is_active = False
        IosWdaManager.kill_relays()
        if acquired_lock:
            with contextlib.suppress(RuntimeError):
                cache_cls._ios_tunnel_lock.release()
