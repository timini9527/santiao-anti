# -*- coding: utf-8 -*-
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_PLATFORM_DIR = os.path.dirname(BACKEND_DIR)

try:
    from desktop_app.core.path_resolver import SmartPathResolver
    PROJECT_ROOT = SmartPathResolver.get_project_root()
except Exception:
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates = [
            exe_dir,
            os.path.dirname(exe_dir),
            os.getcwd()
        ]
        for cand in candidates:
            if os.path.exists(os.path.join(cand, "tests")):
                PROJECT_ROOT = cand
                break
        else:
            PROJECT_ROOT = exe_dir
    else:
        PROJECT_ROOT = os.path.dirname(WEB_PLATFORM_DIR)

# 全局核心动态绝对路径定义（保证在任意工作目录运行均 100% 准确）
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
ALLURE_CLI_DIR = os.path.join(PROJECT_ROOT, "allure-cli")
TEMP_COLLECT_SCRIPT = os.path.join(PROJECT_ROOT, "templates", "temp_collect.py")
TASK_DEBUG_LOG = os.path.join(BACKEND_DIR, "task_debug.log")

# 确保核心产物目录自动就绪
try:
    os.makedirs(REPORTS_DIR, exist_ok=True)
except Exception:
    pass
