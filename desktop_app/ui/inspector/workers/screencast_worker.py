# -*- coding: utf-8 -*-
"""
跨平台实时投屏调度线程 (ScreenCastWorker)：
负责投屏线程生命周期管理、类级最新帧内存缓存与按平台分发，
三端具体视频流解码与通道实现已分别下沉至 platforms/{harmony_cast,android_cast,ios_cast}.py。
"""
import socket
import subprocess
import threading
import time
from typing import Any, Optional

from PyQt6.QtCore import QBuffer, QByteArray, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

from desktop_app.ui.inspector.platforms.android_cast import (
    cleanup_android_stream,
    run_android_scrcpy_stream,
    run_android_stream,
)
from desktop_app.ui.inspector.platforms.harmony import (
    clean_harmony_scrcpy_fports,
    ensure_harmony_scrcpy_env,
    extract_harmony_nalu,
    kill_harmony_scrcpy_daemons,
)
from desktop_app.ui.inspector.platforms.harmony_cast import (
    capture_harmony_single_silent_frame,
    cleanup_harmony_port,
    run_harmony_scrcpy_stream,
    run_harmony_stream,
)
from desktop_app.ui.inspector.platforms.ios_cast import (
    capture_single_ios_frame,
    dispatch_ios_hid,
    release_all_ios_tunnels,
    run_ios_legacy_fallback_stream,
    run_ios_pymobiledevice3_stream,
    run_ios_stream,
)
from desktop_app.ui.inspector.platforms.ios_service import IosWdaManager, register_ios_hid_dispatcher


class ScreenCastWorker(QThread):
    """三端实时投屏后台调度线程，维护类级最新帧内存缓存供抓图与审查 0ms 复用"""

    frame_ready = pyqtSignal(QImage, bytes)
    state_changed = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)

    latest_image: Optional[QImage] = None
    latest_pixmap: Optional[QPixmap] = None
    latest_frame_bytes: Optional[bytes] = None
    latest_frame_time: float = 0.0
    latest_udid: str = ""
    is_active: bool = False
    _active_ios_server: Optional[Any] = None
    _active_ios_loop: Optional[Any] = None
    _ios_tunnel_lock: threading.Lock = threading.Lock()

    @classmethod
    def release_all_tunnels(cls) -> None:
        release_all_ios_tunnels()

    @classmethod
    def clear_cache(cls) -> None:
        """清空全量内存投屏帧缓存，杜绝跨设备脏画面污染"""
        cls.latest_image = None
        cls.latest_pixmap = None
        cls.latest_frame_bytes = None
        cls.latest_frame_time = 0.0
        cls.latest_udid = ""
        cls.is_active = False

    @classmethod
    def dispatch_ios_hid(cls, action: str, **kwargs: Any) -> bool:
        return dispatch_ios_hid(cls, action, **kwargs)

    def __init__(self, udid: str, platform: str) -> None:
        super().__init__()
        self.udid = udid
        self.platform = platform
        self._is_running = False
        self.ui_ready = True
        self._sock: Optional[socket.socket] = None
        self._grpc_channel: Any = None
        self._local_port = 0
        self._android_proc: Optional[subprocess.Popen] = None
        self._android_scid: str = ""
        self._android_server_sock: Optional[socket.socket] = None
        self._android_conn: Optional[socket.socket] = None
        self._ios_stop_hook: Optional[Any] = None
        self._ios_mjpeg_relay_proc: Optional[subprocess.Popen] = None
        self._last_ios_error: str = ""

    @staticmethod
    def _extract_nalu(resp_bytes: bytes) -> bytes:
        return extract_harmony_nalu(resp_bytes)

    @classmethod
    def get_latest_jpeg_bytes(cls, target_udid: str = "") -> Optional[bytes]:
        """按需从内存最新 QImage 压缩为 JPEG 字节流"""
        if target_udid and cls.latest_udid and cls.latest_udid != target_udid:
            return None
        max_age = 60.0 if cls.is_active else 3.0
        if cls.latest_frame_bytes and (time.time() - cls.latest_frame_time < max_age):
            return cls.latest_frame_bytes
        if (
            cls.latest_image
            and not cls.latest_image.isNull()
            and (cls.is_active or (time.time() - cls.latest_frame_time < max_age))
        ):
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
    def _clean_all_scrcpy_fports(cls, udid: str = "") -> None:
        clean_harmony_scrcpy_fports(udid)

    @classmethod
    def _kill_existing_scrcpy_daemons(cls, udid: str = "") -> None:
        kill_harmony_scrcpy_daemons(udid)

    @classmethod
    def _ensure_harmony_env(cls, udid: str = "") -> None:
        ensure_harmony_scrcpy_env(udid)

    @classmethod
    def capture_single_silent_frame(cls, udid: str = "", timeout: float = 4.5) -> Optional[bytes]:
        return capture_harmony_single_silent_frame(cls, udid=udid, timeout=timeout)

    @classmethod
    def capture_single_ios_frame(cls, udid: str = "", timeout: float = 4.5) -> Optional[bytes]:
        return capture_single_ios_frame(cls, udid=udid, timeout=timeout)

    def stop(self) -> None:
        """优雅停止实时投屏流并回收底层进程、隧道与端口转发"""
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

    def _cleanup_android_stream(self) -> None:
        cleanup_android_stream(self)

    def _cleanup_harmony_port(self) -> None:
        cleanup_harmony_port(self)

    def _run_harmony_scrcpy_stream(self) -> bool:
        return run_harmony_scrcpy_stream(self, ScreenCastWorker)

    def _run_harmony_stream(self) -> None:
        run_harmony_stream(self, ScreenCastWorker)

    def _run_android_scrcpy_stream(self) -> bool:
        return run_android_scrcpy_stream(self, ScreenCastWorker)

    def _run_android_stream(self) -> None:
        run_android_stream(self, ScreenCastWorker)

    def _run_ios_pymobiledevice3_stream(self) -> bool:
        return run_ios_pymobiledevice3_stream(self, ScreenCastWorker)

    def _run_ios_legacy_fallback_stream(self, is_ios_17_plus: bool = True) -> bool:
        return run_ios_legacy_fallback_stream(self, ScreenCastWorker, is_ios_17_plus=is_ios_17_plus)

    def _run_ios_stream(self) -> None:
        run_ios_stream(self, ScreenCastWorker)

    def run(self) -> None:
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


# 注册 CoreDevice HID 回调到 ios_service，消除循环导入
register_ios_hid_dispatcher(ScreenCastWorker.dispatch_ios_hid)
