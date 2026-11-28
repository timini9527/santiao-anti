# -*- coding: utf-8 -*-
"""
三端异步抓取后台线程 (CaptureWorker)：
按平台协调截图采集与 DOM 树抓取，优先复用投屏活跃内存帧，具体底层实现全部委托给 platforms/{harmony,android,ios}.py。
"""
import json
import os
import random
import shutil
import time
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QThread, pyqtSignal

from desktop_app.ui.inspector.platforms.android import (
    capture_android_static_screen,
    dump_android_hierarchy,
    inject_android_toast_xml,
)
from desktop_app.ui.inspector.platforms.base import create_placeholder_screenshot
from desktop_app.ui.inspector.platforms.harmony import dump_harmony_layout, run_hdc
from desktop_app.ui.inspector.platforms.ios import (
    capture_ios_fallback_screen,
    dump_ios_hierarchy,
    normalize_ios_screenshot_file,
)
from desktop_app.ui.inspector.platforms.ios_service import IosWdaManager
from desktop_app.ui.inspector.workers.screencast_worker import ScreenCastWorker


class CaptureWorker(QThread):
    """后台异步抓取线程：支持 HarmonyOS / Android / iOS 三端截图与 UI 层次拉取"""

    finished = pyqtSignal(str, str, str)  # local_png, layout_file, platform
    screen_finished = pyqtSignal(str)
    dom_finished = pyqtSignal(str, str)  # layout_file, platform
    failed = pyqtSignal(str)

    def __init__(self, udid: str, platform: str, tmp_dir: str, mode: str = "full") -> None:
        super().__init__()
        self.udid = udid
        self.platform = platform
        self.tmp_dir = tmp_dir
        self.mode = mode

    @staticmethod
    def _silent_capture_harmony_screen(udid: str, local_png: str) -> bool:
        """鸿蒙静默截屏：投屏内存帧复用 -> 本地磁盘缓存 -> snapshot_display -> 单帧录屏通道"""
        norm_local_path = os.path.normpath(os.path.abspath(local_png))
        os.makedirs(os.path.dirname(norm_local_path), exist_ok=True)

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

        latest_bytes = ScreenCastWorker.get_latest_jpeg_bytes(udid)
        if latest_bytes:
            try:
                with open(norm_local_path, "wb") as f_out:
                    f_out.write(latest_bytes)
                return True
            except Exception:
                pass

        cached_cast = os.path.join(os.path.dirname(norm_local_path), "screencast_last_harmony.jpeg")
        if os.path.exists(cached_cast) and (time.time() - os.path.getmtime(cached_cast) < 5.0):
            try:
                shutil.copyfile(cached_cast, norm_local_path)
                return True
            except Exception:
                pass

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
        return inject_android_toast_xml(xml_text, toast_text)

    @staticmethod
    def _dump_android_hierarchy(udid: str, layout_file: str) -> bool:
        return dump_android_hierarchy(udid, layout_file)

    @staticmethod
    def _dump_ios_hierarchy(udid: str, layout_file: str) -> bool:
        return dump_ios_hierarchy(udid, layout_file)

    def _cleanup_old_temp_files(self) -> None:
        try:
            now_t = time.time()
            for fn in os.listdir(self.tmp_dir):
                if fn.startswith(("shot_", "layout_")):
                    fp = os.path.join(self.tmp_dir, fn)
                    if os.path.isfile(fp) and (now_t - os.path.getmtime(fp) > 300):
                        try:
                            os.remove(fp)
                        except Exception:
                            pass
        except Exception:
            pass

    def _run_harmony(self, local_png: str, layout_file: str) -> None:
        if self.mode == "screen_only":
            run_hdc(["shell", "power-shell wakeup"], self.udid, timeout=0.6)
            if self._silent_capture_harmony_screen(self.udid, local_png) and os.path.exists(local_png):
                self.screen_finished.emit(local_png)
            else:
                self.failed.emit("静默截屏失败，请确认设备屏幕已点亮且处于解锁状态。")
            return

        if self.mode == "dom_only":
            if dump_harmony_layout(self.udid, layout_file, screencast_active=ScreenCastWorker.is_active, rpc_timeout=3.5):
                self.dom_finished.emit(layout_file, "harmony")
            else:
                self.failed.emit("获取组件层级树失败，请确认设备已连接且 uitest 守护进程活跃。")
            return

        # 全量同步模式：截屏与 DOM 树并行抓取，同时异步发送亮屏保活，耗时从两者之和降至最大值
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="HarmonySync") as pool:
            fut_wake = pool.submit(run_hdc, ["shell", "power-shell wakeup"], self.udid, 0.6)
            fut_layout = pool.submit(
                dump_harmony_layout,
                self.udid,
                layout_file,
                ScreenCastWorker.is_active,
                3.0,
            )
            fut_shot = pool.submit(self._silent_capture_harmony_screen, self.udid, local_png)
            layout_ok = bool(fut_layout.result())
            shot_ok = bool(fut_shot.result())
            try:
                fut_wake.result(timeout=0.2)
            except Exception:
                pass

        if shot_ok and layout_ok:
            self.finished.emit(local_png, layout_file, "harmony")
        elif layout_ok and not shot_ok:
            create_placeholder_screenshot(
                local_png,
                1084,
                2412,
                "真机画面获取超时 (屏幕熄灭或权限受限)",
                "DOM 组件层级树已成功载入，可在中栏与右栏正常审查",
            )
            self.finished.emit(local_png, layout_file, "harmony")
        elif shot_ok and not layout_ok:
            self.screen_finished.emit(local_png)
            self.failed.emit("组件层级树拉取超时，请稍后再次点击刷新。")
        else:
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

    def _run_android(self, local_png: str, layout_file: str) -> None:
        if self.mode == "dom_only":
            if self._dump_android_hierarchy(self.udid, layout_file):
                self.dom_finished.emit(layout_file, "android")
            else:
                self.failed.emit("获取安卓组件层级树失败，请确认设备屏幕已解锁且已授权 USB 调试。")
            return

        def _capture_android_shot() -> bool:
            if ScreenCastWorker.is_active and (ScreenCastWorker.latest_udid == self.udid or not ScreenCastWorker.latest_udid):
                latest_bytes = ScreenCastWorker.get_latest_jpeg_bytes(self.udid)
                if latest_bytes:
                    try:
                        with open(local_png, "wb") as f_out:
                            f_out.write(latest_bytes)
                        return True
                    except Exception:
                        pass
            return capture_android_static_screen(self.udid, local_png)

        if self.mode == "screen_only":
            if _capture_android_shot():
                self.screen_finished.emit(local_png)
            else:
                self.failed.emit("获取安卓真机画面失败，请确认屏幕已点亮并解锁。")
            return

        # 全量同步模式：DOM 层级与真机截屏并行采集，单次同步耗时砍半
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="AndroidSync") as pool:
            fut_layout = pool.submit(self._dump_android_hierarchy, self.udid, layout_file)
            fut_shot = pool.submit(_capture_android_shot)
            layout_ok = bool(fut_layout.result())
            shot_ok = bool(fut_shot.result())

        if shot_ok and os.path.exists(local_png) and layout_ok and os.path.exists(layout_file):
            self.finished.emit(local_png, layout_file, "android")
        elif shot_ok and os.path.exists(local_png):
            self.screen_finished.emit(local_png)
            self.failed.emit("抓取安卓组件层级树失败，请确认设备屏幕已解锁且已授权 USB 调试。")
        else:
            self.failed.emit("抓取安卓现场数据失败，请确认设备屏幕已解锁且已授权 USB 调试。")

    def _run_ios(self, local_png: str, layout_file: str) -> None:
        if self.mode == "dom_only":
            if self._dump_ios_hierarchy(self.udid, layout_file):
                self.dom_finished.emit(layout_file, "ios")
            else:
                if not IosWdaManager.test_wda_status("http://127.0.0.1:8100", timeout=0.6):
                    self.failed.emit("8100 端口 WDA 服务未连通，请先点击顶部【启动服务】直至显示绿色【正在运行】。")
                else:
                    self.failed.emit("WDA 已在线但未能返回页面 DOM 树，请解锁手机并确保前台应用处于活跃状态后重试。")
            return

        shot_ok = False
        shot_from_wda = False

        # 1. 若实时投屏正活跃，直接 0ms 复用内存最新帧（非投屏态不复用历史旧缓存，确保画面为当前真机最新帧）
        if ScreenCastWorker.is_active and (ScreenCastWorker.latest_udid == self.udid or not ScreenCastWorker.latest_udid):
            for _ in range(40):
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

        # 2. WDA 8100/8200 在线时优先直连 WDA /screenshot (~0.2s)，跳过耗时的 userspace 隧道冷启动与冲突超时
        if not shot_ok:
            wda_url, _ = IosWdaManager.get_wda_url(self.udid, allow_spawn=False)
            if wda_url:
                shot_ok = capture_ios_fallback_screen(self.udid, local_png, allow_dvt_cli=False)
                if shot_ok:
                    shot_from_wda = True

        if self.mode == "screen_only" and shot_ok:
            self.screen_finished.emit(local_png)
            return

        # 3. 仅当 WDA 不在线或直连截屏失败时，才回落 CoreDevice 单帧截屏与 DVT CLI 兜底
        if not shot_ok and not ScreenCastWorker.is_active:
            single_bytes = ScreenCastWorker.capture_single_ios_frame(self.udid, timeout=4.0)
            if single_bytes:
                try:
                    with open(local_png, "wb") as f_out:
                        f_out.write(single_bytes)
                    shot_ok = True
                except Exception:
                    pass

        if not shot_ok:
            shot_ok = capture_ios_fallback_screen(
                self.udid, local_png, allow_dvt_cli=not ScreenCastWorker.is_active
            )

        if self.mode == "screen_only":
            if shot_ok:
                self.screen_finished.emit(local_png)
            else:
                self.failed.emit("未能从 iOS 设备获取画面：请确认 iPhone 处于【解锁点亮状态】。")
            return

        layout_ok = self._dump_ios_hierarchy(self.udid, layout_file)

        if shot_ok and layout_ok and not shot_from_wda:
            try:
                normalize_ios_screenshot_file(local_png, layout_file)
            except Exception:
                pass

        if shot_ok and layout_ok:
            self.finished.emit(local_png, layout_file, "ios")
        elif layout_ok and not shot_ok:
            create_placeholder_screenshot(
                local_png,
                1170,
                2532,
                "真机画面获取超时 (屏幕熄灭或权限受限)",
                "iOS 原生 DOM 组件层级树已成功载入，可在中栏与右栏正常审查",
            )
            self.finished.emit(local_png, layout_file, "ios")
        elif shot_ok:
            minimal_root = {"attributes": {"type": "Screen", "bounds": "[0,0][1170,2532]"}, "children": []}
            with open(layout_file, "w", encoding="utf-8") as f:
                json.dump(minimal_root, f)
            self.finished.emit(local_png, layout_file, "ios")
        else:
            self.failed.emit(
                "未能从 iOS 设备获取画面：请确认 iPhone 处于【解锁点亮状态】（息屏会自动休眠开发者调试通道），且未被爱思助手等外部工具独占投屏通道。"
            )

    def run(self) -> None:
        try:
            ts = int(time.time() * 1000)
            local_png = os.path.normpath(os.path.abspath(os.path.join(self.tmp_dir, f"shot_{self.platform}_{ts}.png")))
            layout_file = os.path.normpath(os.path.abspath(os.path.join(self.tmp_dir, f"layout_{self.platform}_{ts}.dat")))
            self._cleanup_old_temp_files()

            if self.platform == "harmony":
                self._run_harmony(local_png, layout_file)
            elif self.platform == "android":
                self._run_android(local_png, layout_file)
            elif self.platform == "ios":
                self._run_ios(local_png, layout_file)
            else:
                self.failed.emit(f"不支持的抓取平台: {self.platform}")
        except Exception as e:
            self.failed.emit(str(e))
