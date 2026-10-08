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

# 统一从桌面应用配置中心获取标准项目根目录
from desktop_app.config import PROJECT_ROOT

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

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
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "程序运行异常", f"检测到启动错误:\n\n{err_msg}")
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
    base_res = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    icon_candidates = [
        os.path.join(base_res, "resources", "sant_logo_hd.png"),
        os.path.join(base_res, "resources", "app_icon.png"),
        os.path.join(base_res, "resources", "app_icon.ico"),
        os.path.join(base_res, "desktop_app", "resources", "sant_logo_hd.png"),
        os.path.join(base_res, "desktop_app", "resources", "app_icon.png"),
        os.path.join(base_res, "desktop_app", "resources", "app_icon.ico"),
        os.path.join(PROJECT_ROOT, "desktop_app", "resources", "sant_logo_hd.png"),
        os.path.join(PROJECT_ROOT, "desktop_app", "resources", "app_icon.png"),
        os.path.join(PROJECT_ROOT, "desktop_app", "resources", "app_icon.ico"),
    ]
    for ic_p in icon_candidates:
        if os.path.exists(ic_p):
            app.setWindowIcon(QIcon(ic_p))
            break

    # 注册全局异常钩子
    sys.excepthook = handle_exception

    # 设置系统默认平滑字体
    font = QFont("Segoe UI", 9)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # 加载白金轻奢现代科技主题 (与 Web 端 1:1 对齐)
    app.setStyleSheet(LIGHT_LUXURY_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    run_app()
