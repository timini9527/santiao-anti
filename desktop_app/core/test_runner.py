# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 原生多线程测试执行器
=======================================================
基于 PyQt6 QThread 实现非阻塞测试执行、实时日志多线程投递、
强力进程清理以及 Allure 报告生成。
"""
import os
import sys
import time
import subprocess
import shutil
import re
from typing import Optional, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

from desktop_app.config import PROJECT_ROOT
from desktop_app.core.path_resolver import SmartPathResolver

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web_platform.backend.paths import (
    REPORTS_DIR,
    ALLURE_CLI_DIR
)
from web_platform.backend.runner import auto_detect_system_java_home

# 国际标准 ANSI / VT100 转义控制序列与不可打印字符匹配正则
ANSI_ESCAPE_RE = re.compile(
    r'\x1b\[[0-?]*[ -/]*[@-~]'            # CSI 转义控制序列 (如 \x1b[32m, \x1b[0m, \x1b[2K)
    r'|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'  # OSC 序列
    r'|\x1b[ -/]*[@-~]'                   # 2 字节 ANSI 转义码
    r'|[\x00-\x08\x0b\x0c\x0e-\x1f]'     # 不可打印控制字符 (保留 \t 与 \n)
)

def clean_ansi_log(text: str) -> str:
    """清洗日志文本中的 ANSI 颜色代码与特殊终端控制符，消除头部和尾部多余字符"""
    if not text:
        return ""
    cleaned = ANSI_ESCAPE_RE.sub('', text)
    # 规避日志框架占位符导致的行首单空格，确保 [2026-xx-xx ...] 顶格平齐
    if cleaned.startswith(" [") and "]" in cleaned:
        cleaned = cleaned[1:]
    return cleaned.rstrip("\r\n")

class TestExecutionWorker(QThread):
    """PyQt6 独立的测试执行线程，确保主界面 120 帧丝滑不卡顿"""
    
    # 信号定义
    log_signal = pyqtSignal(str)              # 逐行实时日志
    status_signal = pyqtSignal(str, str)      # (状态类型: 'running'|'finished'|'error', 提示信息)
    finished_signal = pyqtSignal(int, str)    # (返回码, 报告目录路径)

    def __init__(self, run_config: Dict[str, Any]):
        super().__init__()
        self.config = run_config
        self.process: Optional[subprocess.Popen] = None
        self._is_killed = False
        self.task_id = f"task_{int(time.time() * 1000)}"
        self.allure_results_dir = os.path.join(REPORTS_DIR, "allure_results", self.task_id)
        self.allure_report_dir = os.path.join(REPORTS_DIR, "allure_reports", self.task_id)

    def run(self):
        """线程主执行逻辑"""
        try:
            self._execute_pytest()
        except Exception as e:
            self.log_signal.emit(f"\n❌ [执行引擎异常]: {str(e)}\n")
            self.status_signal.emit("error", str(e))
            self.finished_signal.emit(-1, "")

    def _execute_pytest(self):
        self.status_signal.emit("running", "测试运行中...")
        self.log_signal.emit(f"==================================================")
        self.log_signal.emit(f"  🚀 启动三条 IM 自动化测试任务: {self.task_id}")
        self.log_signal.emit(f"  测试目标: {self.config.get('nodeid', '全量用例')}")
        self.log_signal.emit(f"  发送端设备: {self.config.get('remote_udid')} (Appium: {self.config.get('remote_appium')})")
        self.log_signal.emit(f"  接收端设备: {self.config.get('remote_udid2')} (Appium: {self.config.get('remote_appium2')})")
        self.log_signal.emit(f"  私聊好友: {self.config.get('private_chat_name')} | 群聊好友: {self.config.get('group_chat_name')}")
        self.log_signal.emit(f"  调试模式: {'开启 (失败保持现场)' if self.config.get('debug_mode') else '关闭'}")
        self.log_signal.emit(f"==================================================\n")

        # 准备 Allure 结果目录
        os.makedirs(self.allure_results_dir, exist_ok=True)
        os.makedirs(self.allure_report_dir, exist_ok=True)

        # 环境变量注入
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        # 净化运行环境：彻底移除 PyInstaller 与 pytest 禁用变量污染，确保外部 Python 能够自动扫描并加载全局 site-packages 中的全部插件 (如 allure-pytest, pytest-rerunfailures)
        for var in ("PYTHONHOME", "PYTHONPATH", "_MEIPASS2", "_MEIPASS", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTHONNOUSERSITE"):
            env.pop(var, None)

        # 净化 PATH：剔除 PyInstaller 打包注入的 _internal / _MEI 目录，避免污染外部 Python 进程环境
        path_items = [p for p in env.get("PATH", "").split(os.pathsep) if p and "_internal" not in p and "_MEI" not in p]
        env["PATH"] = os.pathsep.join(path_items)

        env["PYTHONPATH"] = PROJECT_ROOT
        
        # 注入用户在控制台配置的动态设备参数
        if self.config.get("remote_appium"):
            env["REMOTE_APPIUM"] = self.config["remote_appium"]
        if self.config.get("remote_appium2"):
            env["REMOTE_APPIUM2"] = self.config["remote_appium2"]
        if self.config.get("remote_udid"):
            env["REMOTE_UDID"] = self.config["remote_udid"]
        if self.config.get("remote_udid2"):
            env["REMOTE_UDID2"] = self.config["remote_udid2"]
        if self.config.get("private_chat_name"):
            env["PRIVATE_CHAT_NAME"] = self.config["private_chat_name"]
        if self.config.get("group_chat_name"):
            env["GROUP_CHAT_NAME"] = self.config["group_chat_name"]
        if self.config.get("debug_mode"):
            env["DEBUG_MODE"] = "1"
        if self.config.get("env"):
            env["TEST_ENV"] = self.config["env"]

        # 动态定位真实的 Python 解释器（基于 SmartPathResolver 多级雷达扫描：便携运行时/虚拟环境/系统安装/注册表/PATH）
        runtime_info = SmartPathResolver.discover_python_runtime()
        py_bin = runtime_info.get("executable") or sys.executable or "python"

        # 若命中内置便携环境，确保将其 Scripts 与根目录注入 PATH 最前列
        py_home = os.path.dirname(os.path.abspath(py_bin))
        scripts_dir = os.path.join(py_home, "Scripts")
        env["PATH"] = f"{py_home};{scripts_dir};{env.get('PATH', '')}"

        # 构造 Pytest 执行命令
        cmd = [
            py_bin, "-m", "pytest",
            "-v", "-s",
            f"--alluredir={self.allure_results_dir}",
            "--clean-alluredir"
        ]

        nodeid = self.config.get("nodeid")
        if nodeid:
            cmd.append(nodeid)
        else:
            cmd.append("tests/chat")

        self.log_signal.emit(f"[运行环境]: {py_bin}")
        self.log_signal.emit(f"[执行命令]: {' '.join(cmd)}\n")

        # 启动子进程：在 Windows 平台显式指定 CREATE_NO_WINDOW，彻底杜绝弹出控制台命令框
        creationflags = (subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if sys.platform == "win32" else 0
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=PROJECT_ROOT,
            env=env,
            creationflags=creationflags,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        # 逐行非阻塞读取控制台输出
        if self.process.stdout:
            for line in iter(self.process.stdout.readline, ''):
                if self._is_killed:
                    break
                self.log_signal.emit(clean_ansi_log(line))
            self.process.stdout.close()

        exit_code = self.process.wait() if not self._is_killed else -9

        if self._is_killed:
            self.log_signal.emit("\n⚠️ [测试已被用户强力终止]\n")
            self.status_signal.emit("error", "测试已被手动终止")
            # 自动物理清理本次任务预建的空结果与报告目录，防止残留空报告污染历史
            import shutil
            for d in (self.allure_results_dir, self.allure_report_dir):
                if d and os.path.exists(d):
                    try:
                        shutil.rmtree(d, ignore_errors=True)
                    except Exception:
                        pass
            self.finished_signal.emit(-9, "")
            return

        self.log_signal.emit(f"\n==================================================")
        self.log_signal.emit(f"  🏁 测试执行完毕，退出码: {exit_code}")
        self.log_signal.emit(f"  正在自动生成 Allure 多维度测试报告...")
        self.log_signal.emit(f"==================================================")

        # 自动生成 Allure 测试报告
        report_path = self._generate_allure_report()
        
        self.status_signal.emit("finished", f"测试完成 (退出码: {exit_code})")
        self.finished_signal.emit(exit_code, report_path)

    def _generate_allure_report(self) -> str:
        """自动定位 Java 环境与 Allure CLI 并编译报告"""
        allure_info = SmartPathResolver.discover_allure_cli()
        allure_bin = allure_info.get("executable")
        java_home = auto_detect_system_java_home()
        
        gen_env = os.environ.copy()
        if java_home:
            gen_env["JAVA_HOME"] = java_home
            gen_env["PATH"] = f"{os.path.join(java_home, 'bin')};{gen_env.get('PATH', '')}"

        if not allure_bin or not os.path.exists(allure_bin):
            self.log_signal.emit("[Allure] 未检测到本地 Allure CLI，可直接在 Allure 插件中查看原始测试数据。")
            return self.allure_results_dir

        try:
            cmd = [allure_bin, "generate", self.allure_results_dir, "-o", self.allure_report_dir, "--clean"]
            no_window = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.run(cmd, env=gen_env, cwd=PROJECT_ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=no_window)
            self.log_signal.emit(f"✅ Allure 报告生成成功: {self.allure_report_dir}")
            
            # 生成精简/完整视角标记
            role = self.config.get("role", "business")
            self.log_signal.emit(f"✅ 当前已配置测试视角: {'💼 业务精简视角' if role == 'business' else '🛠️ 开发完整视角'}")
            return self.allure_report_dir
        except Exception as e:
            self.log_signal.emit(f"⚠️ 生成 Allure 报告遇到警告: {e}")
            return self.allure_report_dir

    def stop(self):
        """强力终止当前正在执行的测试进程树"""
        self._is_killed = True
        if self.process and self.process.poll() is None:
            pid = self.process.pid
            try:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    self.process.terminate()
            except Exception as e:
                print(f"终止进程树异常: {e}")
