# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面独立端) - 主入口
=======================================================
纯原生 Windows 桌面应用程序，不依赖任何 WebView 壳子，
原生 C++ 渲染管线，极速响应，零卡顿，状态永久记忆。
"""
import os
import sys
import multiprocessing
import ctypes
from typing import Optional

_QT_DLL_HANDLES = []

# 必须在最开头调用，防止 Windows 打包时多进程/子进程递归拉起产生进程炸弹
multiprocessing.freeze_support()


def _prepare_qt_runtime() -> None:
    """在 PyInstaller 环境及 Windows 下注册系统目录与 Qt6 原生 DLL/插件目录，彻底避免 DLL 符号冲突。"""
    global _QT_DLL_HANDLES

    # 优先将 Windows 原生系统核心 DLL 目录加入搜寻列表，确保 Qt6Core 正确链接系统 icuuc.dll
    if sys.platform == "win32":
        sys32_dir = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
        if os.path.isdir(sys32_dir):
            try:
                _QT_DLL_HANDLES.append(os.add_dll_directory(sys32_dir))
            except Exception:
                pass

    if not getattr(sys, "frozen", False):
        return

    exe_dir = os.path.dirname(sys.executable)
    bundle_dir = getattr(sys, "_MEIPASS", exe_dir)

    # 核心自愈：检测 _internal 中是否被误打包了冲突的第三方 icuuc.dll / icudt*.dll
    # PyQt6 在 Windows 下依赖系统原生 C:\Windows\System32\icuuc.dll
    # 若被第三方不兼容的 icu 覆盖，会导致 Qt6Core.dll 抛出 [WinError 127 找不到指定的程序]
    for bad_dll in ["icuuc.dll", "icudt78.dll", "icudt77.dll", "icudt76.dll"]:
        bad_path = os.path.join(bundle_dir, bad_dll)
        if os.path.exists(bad_path):
            try:
                isolated_path = bad_path + ".conflict_isolated"
                if os.path.exists(isolated_path):
                    os.remove(isolated_path)
                os.rename(bad_path, isolated_path)
            except Exception:
                pass

    qt_bin_dir = os.path.join(bundle_dir, "PyQt6", "Qt6", "bin")
    qt_plugins_dir = os.path.join(bundle_dir, "PyQt6", "Qt6", "plugins")

    for d in [bundle_dir, qt_bin_dir]:
        if os.path.isdir(d):
            try:
                _QT_DLL_HANDLES.append(os.add_dll_directory(d))
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            except Exception:
                pass

    if os.path.isdir(qt_plugins_dir):
        os.environ["QT_PLUGIN_PATH"] = qt_plugins_dir


_prepare_qt_runtime()

# 确保项目根路径优先注入 sys.path，支持脚本直接运行与打包环境
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# 统一从桌面应用配置中心获取标准项目根目录
from desktop_app.config import PROJECT_ROOT

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# 在本地工程源码目录下运行打包 EXE 时，优先加载本地 desktop_app 最新源码，确保 Ctrl+R 热重启实时生效
if getattr(sys, "frozen", False) and os.path.isdir(os.path.join(PROJECT_ROOT, "desktop_app", "ui")):
    try:
        import importlib.machinery
        if importlib.machinery.PathFinder in sys.meta_path:
            sys.meta_path.remove(importlib.machinery.PathFinder)
        sys.meta_path.insert(0, importlib.machinery.PathFinder)
        for _mod_name in list(sys.modules.keys()):
            if _mod_name.startswith("desktop_app.ui") or _mod_name == "desktop_app.style":
                sys.modules.pop(_mod_name, None)
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from desktop_app.style import LIGHT_LUXURY_QSS
from desktop_app.ui.main_window import MainWindow

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    import traceback
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(err_msg, file=sys.stderr)
    try:
        from PyQt6.QtWidgets import QMessageBox, QSplashScreen
        from PyQt6.QtCore import Qt

        # 1. 彻底关闭并销毁任何遗留的闪屏/Splash窗口，杜绝闪屏死在屏幕上
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QSplashScreen) or widget.inherits("QSplashScreen"):
                try:
                    widget.close()
                    widget.deleteLater()
                except Exception:
                    pass

        # 2. 异常提示窗口强制设置最上层置顶展示
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("程序运行异常")
        msg_box.setText(f"检测到启动错误:\n\n{err_msg}")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # 强制设置置顶标志
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg_box.show()
        msg_box.raise_()
        msg_box.activateWindow()

        # Windows 原生 Win32 API 强制置顶 (HWND_TOPMOST = -1, SWP_NOMOVE | SWP_NOSIZE)
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.SetWindowPos(
                    int(msg_box.winId()), -1, 0, 0, 0, 0, 0x0001 | 0x0002
                )
            except Exception:
                pass

        msg_box.exec()
    except Exception:
        pass

MAIN_WINDOW_TITLE = "三条 IM 自动化测试控制台"
_MUTEX_HANDLE = None


def _activate_existing_window() -> bool:
    """
    定位正在运行的应用主窗口，将其从最小化或后台状态中恢复并强制激活置顶到最前台。
    """
    if sys.platform != "win32":
        return False

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    target_hwnds = []

    # 1. 优先通过精确窗口标题寻找
    hwnd = user32.FindWindowW(None, MAIN_WINDOW_TITLE)
    if hwnd and user32.IsWindow(hwnd):
        target_hwnds.append(hwnd)
    else:
        # 2. 若标题动态附加了版本或状态，通过枚举窗口标题匹配
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def _enum_cb(h, _):
            if user32.IsWindow(h) and user32.IsWindowVisible(h):
                length = user32.GetWindowTextLengthW(h)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(h, buff, length + 1)
                    title = buff.value
                    if "三条" in title and "控制台" in title:
                        target_hwnds.append(h)
            return True

        user32.EnumWindows(WNDENUMPROC(_enum_cb), 0)

    if not target_hwnds:
        return False

    h_target = target_hwnds[0]

    # 若窗口处于最小化，调用 SW_RESTORE (9) 恢复正常窗口；否则调用 SW_SHOW (5)
    SW_RESTORE = 9
    SW_SHOW = 5
    if user32.IsIconic(h_target):
        user32.ShowWindow(h_target, SW_RESTORE)
    else:
        user32.ShowWindow(h_target, SW_SHOW)

    # 突破 Windows 前台激活锁限制：通过 AttachThreadInput 临时共享输入队列实现绝对置顶
    try:
        fore_hwnd = user32.GetForegroundWindow()
        fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
        curr_thread = kernel32.GetCurrentThreadId()

        if fore_thread != curr_thread and fore_thread != 0:
            user32.AttachThreadInput(curr_thread, fore_thread, True)
            user32.SetForegroundWindow(h_target)
            user32.SetFocus(h_target)
            user32.AttachThreadInput(curr_thread, fore_thread, False)
        else:
            user32.SetForegroundWindow(h_target)
            user32.SetFocus(h_target)
    except Exception:
        user32.SetForegroundWindow(h_target)

    return True


def _acquire_single_instance_lock() -> bool:
    """
    单实例互斥锁：
    若当前已有实例在运行，自动唤醒前台窗口并返回 False；
    若为首个实例，成功获取系统全局命名互斥体并返回 True。
    支持 Ctrl+R 热重启平滑握手：等待旧进程彻底终结，杜绝时序竞争导致的闪退。
    """
    global _MUTEX_HANDLE
    if sys.platform != "win32":
        return True

    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183
    mutex_name = "Local\\Santiao_IM_AutoTest_Console_SingleInstance_Mutex"

    # 1. 检测是否是由 Ctrl+R 热重启拉起的新进程
    restarting_pid = None
    for arg in sys.argv:
        if arg.startswith("--restart-from-pid="):
            try:
                restarting_pid = int(arg.split("=", 1)[1])
            except Exception:
                pass
            break

    # 若为热重启场景，新进程精准等待旧进程完全退出（毫秒级释放内核资源）
    if restarting_pid:
        PROCESS_SYNCHRONIZE = 0x00100000
        h_old_proc = kernel32.OpenProcess(PROCESS_SYNCHRONIZE, False, restarting_pid)
        if h_old_proc:
            # 最多等待 3000ms，旧进程一旦退出内核立即返回 WAIT_OBJECT_0
            kernel32.WaitForSingleObject(h_old_proc, 3000)
            kernel32.CloseHandle(h_old_proc)

    # 2. 循环重试获取互斥锁（热重启时轮询重试最多 20 次，每次 50ms）
    max_retries = 20 if restarting_pid else 1
    import time
    for _ in range(max_retries):
        if _MUTEX_HANDLE:
            kernel32.CloseHandle(_MUTEX_HANDLE)
            _MUTEX_HANDLE = None

        _MUTEX_HANDLE = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        if last_error != ERROR_ALREADY_EXISTS:
            return True
        time.sleep(0.05)

    # 3. 若多次重试后仍然冲突，且非热重启场景，则属于普通双击多开：激活已有窗口并退出
    for _ in range(5):
        if _activate_existing_window():
            break
        time.sleep(0.2)
    return False


def get_best_app_icon_path() -> Optional[str]:
    """优先获取原生 Windows 多分辨率 .ico 格式图标，其次为 png 矢量图"""
    base_res = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_res, "resources", "app_icon.ico"),
        os.path.join(base_res, "desktop_app", "resources", "app_icon.ico"),
        os.path.join(PROJECT_ROOT, "desktop_app", "resources", "app_icon.ico"),
        os.path.join(base_res, "resources", "app_icon.png"),
        os.path.join(base_res, "desktop_app", "resources", "app_icon.png"),
        os.path.join(PROJECT_ROOT, "desktop_app", "resources", "app_icon.png"),
        os.path.join(base_res, "resources", "sant_logo_hd.png"),
        os.path.join(base_res, "desktop_app", "resources", "sant_logo_hd.png"),
        os.path.join(PROJECT_ROOT, "desktop_app", "resources", "sant_logo_hd.png"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def apply_win32_window_icon(hwnd: int, ico_path: str) -> None:
    """
    通过 Windows Win32 API 强制向窗口句柄写入大/小图标句柄 (WM_SETICON)，
    彻底穿透并刷新 Windows 任务栏缓存，确保任务栏 100% 显示专属高清图标。
    """
    if sys.platform != "win32" or not ico_path or not os.path.exists(ico_path):
        return
    try:
        user32 = ctypes.windll.user32
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040

        h_icon_big = user32.LoadImageW(
            None, ico_path, IMAGE_ICON,
            0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
        )
        h_icon_small = user32.LoadImageW(
            None, ico_path, IMAGE_ICON,
            16, 16, LR_LOADFROMFILE
        )

        if h_icon_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon_big)
        if h_icon_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
    except Exception:
        pass


def run_app():
    # 开启 Windows 4K/高分屏矢量渲染优化
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    # 注册 Windows 原生任务栏专属 AppId，确保任务栏独立显示专属高清图标
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SantiaoQA.AntiIM.Desktop.Platform")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("三条 IM 自动化测试控制台")
    app.setOrganizationName("SantiaoQA")

    # 注入应用程序全局专属高清图标 (覆盖任务栏、主窗口与通知托盘)
    from PyQt6.QtGui import QIcon
    icon_path = get_best_app_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    # 注册全局异常钩子
    sys.excepthook = handle_exception

    # 设置系统默认平滑字体
    font = QFont("Segoe UI", 9)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # 加载白金轻奢现代科技主题 (与 Web 端 1:1 对齐)
    app.setStyleSheet(LIGHT_LUXURY_QSS)

    # 毫秒级即时呈现轻奢启动画面，彻底消除 Windows 鼠标转圈盲等
    from desktop_app.ui.splash_screen import AppSplashScreen
    splash = AppSplashScreen()
    if icon_path:
        splash.setWindowIcon(QIcon(icon_path))
    splash.show()
    splash.update_progress(25, "正在初始化自动化引擎与运行时环境...")

    window = None
    try:
        splash.update_progress(65, "正在装载控制台架构与测试工作台...")
        window = MainWindow()
        if icon_path:
            window.setWindowIcon(QIcon(icon_path))

        splash.update_progress(100, "就绪，正在呈现主工作台...")
        window.show()

        # 强制向 Win32 HWND 写入任务栏原生高清图标
        if sys.platform == "win32" and icon_path and icon_path.endswith(".ico"):
            apply_win32_window_icon(int(window.winId()), icon_path)

        # 平滑过渡并移交主窗口焦点，并确保闪屏彻底关闭销毁
        splash.finish(window)
        splash.close()
        splash.deleteLater()
    except Exception:
        if splash:
            try:
                splash.close()
                splash.deleteLater()
            except Exception:
                pass
        raise

    # 再次刷新以防 finish 过程覆盖任务栏图标
    if sys.platform == "win32" and icon_path and icon_path.endswith(".ico") and window:
        apply_win32_window_icon(int(window.winId()), icon_path)

    sys.exit(app.exec())


if __name__ == '__main__':
    # 核心单实例保护：只允许启动一次，第二次启动自动激活并置顶已有窗口
    if not _acquire_single_instance_lock():
        sys.exit(0)
    run_app()
