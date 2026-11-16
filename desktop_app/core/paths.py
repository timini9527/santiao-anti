# -*- coding: utf-8 -*-
"""桌面端核心运行路径解析模块。"""
import os
import sys

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
DESKTOP_APP_DIR = os.path.dirname(CORE_DIR)

try:
    from desktop_app.core.path_resolver import SmartPathResolver
    PROJECT_ROOT = SmartPathResolver.get_project_root()
except Exception:
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates = [
            exe_dir,
            os.path.dirname(exe_dir),
            os.getcwd(),
        ]
        for cand in candidates:
            if os.path.exists(os.path.join(cand, "tests")):
                PROJECT_ROOT = cand
                break
        else:
            PROJECT_ROOT = exe_dir
    else:
        PROJECT_ROOT = os.path.dirname(DESKTOP_APP_DIR)


def _resolve_writable_workspace() -> str:
    """解析可写工作区目录；当位于只读卷（如 macOS DMG）时回退至用户主目录。"""
    try:
        if sys.platform == "darwin" and os.path.abspath(PROJECT_ROOT).startswith("/Volumes/"):
            raise PermissionError("DMG 只读卷")
        test_dir = os.path.join(PROJECT_ROOT, "reports")
        os.makedirs(test_dir, exist_ok=True)
        probe = os.path.join(test_dir, ".write_probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return PROJECT_ROOT
    except Exception:
        fallback = os.path.join(os.path.expanduser("~"), "SantiaoAutoTest")
        os.makedirs(fallback, exist_ok=True)
        return fallback


WRITABLE_ROOT = _resolve_writable_workspace()
REPORTS_DIR = os.path.join(WRITABLE_ROOT, "reports")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
ALLURE_CLI_DIR = os.path.join(PROJECT_ROOT, "allure-cli")
TEMP_COLLECT_SCRIPT = os.path.join(WRITABLE_ROOT, "templates", "temp_collect.py")

# 确保核心产物目录自动就绪
try:
    os.makedirs(REPORTS_DIR, exist_ok=True)
except Exception:
    pass
