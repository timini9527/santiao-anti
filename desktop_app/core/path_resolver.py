# -*- coding: utf-8 -*-
"""
==============================================================================
三条 IM 自动化测试体系 · 智能路径与环境发现引擎 (SmartPathResolver)
==============================================================================
职责：
1. 全自动智能定位工程根目录，杜绝硬编码路径带来的跨设备运行异常；
2. 动态自适应扫描工程全部业务模块目录（tests, pages, locators, strategy 等）与核心配置文件；
3. 智能多级雷达探测宿主机/便携包中的 Python 运行时、Inno Setup 编译器、Allure-CLI、Java 及移动端工具链；
4. 为打包流水线（Inno Setup / 绿色便携包）与运行期（TestRunner / Collector）提供统一、高内聚的路径服务。
==============================================================================
"""

import os
import sys
import glob
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple


class SmartPathResolver:
    """智能路径与环境感知解析器"""

    # 动态构建与临时缓存黑名单目录（智能排除，不纳入业务资产打包）
    EXCLUDED_DIR_NAMES = {
        '.git', '.github', '.vscode', '.idea', '.agents', '.claude',
        '__pycache__', '.pytest_cache', '.cache',
        'build', 'build_native', 'build_desktop', 'build_mac',
        'dist', 'logs', 'reports', 'screenshots', 'allure-results', 'allure-report',
        'desktop_app', 'web_platform', 'web_console_v2', 'tmp', 'scratch', 'output',
        'node_modules', '.venv', 'venv', 'env'
    }

    # 核心根目录单文件资产白名单候选
    CORE_CONFIG_FILES = [
        'requirements.txt',
        'pytest.ini',
        'conftest.py',
        'config.py'
    ]

    _cached_root: Optional[str] = None

    @classmethod
    def get_project_root(cls) -> str:
        """
        智能识别并返回当前工程的绝对根目录。
        在源码运行、相对路径拉起以及 PyInstaller 打包环境（sys.frozen）下自适应回溯。
        """
        if cls._cached_root and os.path.isdir(cls._cached_root):
            return cls._cached_root

        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            candidates = [
                exe_dir,                                              # 1. 独立安装包目录
                os.path.dirname(exe_dir),                             # 2. 上级目录 (如 dist/)
                os.path.dirname(os.path.dirname(exe_dir)),             # 3. 上上级工程根目录
                os.path.dirname(os.path.dirname(os.path.dirname(exe_dir))),
                os.getcwd(),                                          # 4. 当前工作目录
                os.path.dirname(os.getcwd()),
                os.path.dirname(os.path.dirname(os.getcwd())),
            ]
            for cand in candidates:
                if cand and os.path.isdir(cand) and os.path.exists(os.path.join(cand, "tests")):
                    cls._cached_root = os.path.abspath(cand)
                    return cls._cached_root
            cls._cached_root = exe_dir
            return cls._cached_root
        else:
            # 源码运行状态：当前文件位于 desktop_app/core/path_resolver.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            desktop_app_dir = os.path.dirname(current_dir)
            cls._cached_root = os.path.dirname(desktop_app_dir)
            return cls._cached_root

    @classmethod
    def discover_project_assets(cls, source_root: Optional[str] = None) -> Dict[str, Any]:
        """
        智能扫描并识别工程中的全部测试业务目录与核心配置文件。
        无论后续新增什么业务模块（如 business_helpers, strategy, resources），均自动感知，无需手动修改打包配置。
        
        :param source_root: 指定扫描根路径，默认使用 get_project_root()
        :return: {"business_dirs": [目录名列表], "core_files": [文件名列表], "all_assets": [...]}
        """
        root = os.path.abspath(source_root) if source_root else cls.get_project_root()
        discovered_dirs: List[str] = []
        discovered_files: List[str] = []

        if not os.path.isdir(root):
            return {"business_dirs": [], "core_files": [], "all_assets": []}

        # 1. 动态过滤识别根目录下的业务资产子目录
        for entry in os.listdir(root):
            full_path = os.path.join(root, entry)
            if not os.path.isdir(full_path):
                continue
            
            name_lower = entry.lower()
            if name_lower in cls.EXCLUDED_DIR_NAMES or entry.startswith('.'):
                continue

            # 只要不是排除目录，即作为测试业务模块资产自动收纳
            discovered_dirs.append(entry)

        # 排序确保构建一致性，基础核心目录置顶
        priority_dirs = ['tests', 'core', 'common', 'locators', 'pages', 'strategy', 'business_helpers', 'config', 'data', 'resources', 'allure-cli']
        discovered_dirs.sort(key=lambda x: (priority_dirs.index(x) if x in priority_dirs else 99, x))

        # 2. 动态识别根目录下的核心配置文件
        for f in cls.CORE_CONFIG_FILES:
            if os.path.isfile(os.path.join(root, f)):
                discovered_files.append(f)

        return {
            "business_dirs": discovered_dirs,
            "core_files": discovered_files,
            "all_assets": discovered_dirs + discovered_files
        }

    @classmethod
    def discover_python_runtime(cls) -> Dict[str, Optional[str]]:
        """
        智能多级雷达探测宿主机或工程内置的 Python 运行时环境。
        依次扫描：内置便携运行时 -> 当前解释器主目录 -> 注册表与系统标准安装路径 -> PATH 环境变量。
        
        :return: {"executable": python可执行文件绝对路径, "home_dir": Python安装根目录}
        """
        root = cls.get_project_root()
        candidates: List[str] = []

        # 1. 内置便携运行时 (真正实现 0 依赖环境)
        candidates.append(os.path.join(root, "python_runtime", "python.exe"))
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            candidates.append(os.path.join(exe_dir, "python_runtime", "python.exe"))

        # 2. 当前正在运行的 Python 宿主根目录（自动剔除虚拟环境代理，定位实体环境）
        base_prefix = getattr(sys, 'base_prefix', sys.prefix)
        if base_prefix:
            candidates.append(os.path.join(base_prefix, "python.exe"))
        if sys.executable and not getattr(sys, 'frozen', False):
            candidates.append(sys.executable)

        # 3. Windows 平台注册表自动探测
        if sys.platform == "win32":
            try:
                import winreg
                for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    for sub_key in [r"SOFTWARE\Python\PythonCore", r"SOFTWARE\WOW6432Node\Python\PythonCore"]:
                        try:
                            with winreg.OpenKey(root_key, sub_key) as k:
                                num_subkeys = winreg.QueryInfoKey(k)[0]
                                for i in range(num_subkeys):
                                    ver = winreg.EnumKey(k, i)
                                    try:
                                        with winreg.OpenKey(root_key, f"{sub_key}\\{ver}\\InstallPath") as ik:
                                            p = winreg.QueryValue(ik, "")
                                            if p:
                                                candidates.append(os.path.join(p.strip(), "python.exe"))
                                    except Exception:
                                        pass
                        except Exception:
                            pass
            except Exception:
                pass

        # 4. Windows 常见标准全盘安装默认路径
        std_patterns = [
            r"C:\Program Files\Python*\python.exe",
            r"C:\Program Files (x86)\Python*\python.exe",
            r"C:\Python*\python.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python*\python.exe"),
            r"D:\Python*\python.exe",
            r"D:\data\Python*\python.exe",
            r"E:\Python*\python.exe",
        ]
        for pat in std_patterns:
            candidates.extend(glob.glob(pat))

        # 5. 系统环境变量 PATH (python / python3 / py)
        for cmd in ["python", "python3", "py"]:
            found = shutil.which(cmd)
            if found:
                candidates.append(found)

        # 校验并返回第一个真实有效且可执行的 Python
        for cand in candidates:
            if cand and os.path.isfile(cand) and os.path.exists(cand):
                abs_cand = os.path.abspath(cand)
                home_dir = os.path.dirname(abs_cand)
                # 排除可能残留的空路径或临时目录
                if os.path.isfile(os.path.join(home_dir, "python.exe")):
                    return {
                        "executable": abs_cand,
                        "home_dir": home_dir
                    }

        # 兜底回退
        fallback_exe = shutil.which("python") or "python"
        return {
            "executable": fallback_exe,
            "home_dir": os.path.dirname(fallback_exe) if os.path.isabs(fallback_exe) else None
        }

    @classmethod
    def discover_inno_compiler(cls) -> Optional[str]:
        """
        智能探测 Inno Setup 安装包编译器 (ISCC.exe)。
        自动检索环境变量、注册表以及各磁盘驱动器标准安装路径。
        """
        # 1. PATH 环境变量命中
        which_iscc = shutil.which("ISCC") or shutil.which("iscc.exe")
        if which_iscc and os.path.isfile(which_iscc):
            return os.path.abspath(which_iscc)

        candidates: List[str] = []

        # 2. Windows 注册表卸载项探测
        if sys.platform == "win32":
            try:
                import winreg
                for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    for sub in [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]:
                        try:
                            with winreg.OpenKey(root_key, sub) as k:
                                num = winreg.QueryInfoKey(k)[0]
                                for i in range(num):
                                    app_key_name = winreg.EnumKey(k, i)
                                    if "inno setup" in app_key_name.lower():
                                        try:
                                            with winreg.OpenKey(root_key, f"{sub}\\{app_key_name}") as ik:
                                                loc = winreg.QueryValueEx(ik, "InstallLocation")[0]
                                                if loc:
                                                    candidates.append(os.path.join(loc.strip(), "ISCC.exe"))
                                        except Exception:
                                            pass
                        except Exception:
                            pass
            except Exception:
                pass

        # 3. 常见全盘驱动器安装路径通配扫描 (涵盖 Inno Setup 5 / 6 / 7)
        patterns = [
            r"C:\Program Files*\Inno Setup*\ISCC.exe",
            r"D:\Program Files*\Inno Setup*\ISCC.exe",
            r"E:\Program Files*\Inno Setup*\ISCC.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup*\ISCC.exe"),
        ]
        for pat in patterns:
            candidates.extend(glob.glob(pat))

        for cand in candidates:
            if cand and os.path.isfile(cand) and os.path.exists(cand):
                return os.path.abspath(cand)

        return None

    @classmethod
    def discover_allure_cli(cls) -> Dict[str, Optional[str]]:
        """
        智能定位 Allure-CLI 命令行工具目录与执行脚本。
        """
        root = cls.get_project_root()
        candidates = [
            os.path.join(root, "allure-cli"),
            os.path.join(os.path.dirname(root), "allure-cli"),
        ]
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            candidates.insert(0, os.path.join(exe_dir, "allure-cli"))

        for cand in candidates:
            bat_path = os.path.join(cand, "bin", "allure.bat")
            sh_path = os.path.join(cand, "bin", "allure")
            if os.path.exists(bat_path) or os.path.exists(sh_path):
                return {
                    "home_dir": os.path.abspath(cand),
                    "executable": os.path.abspath(bat_path if sys.platform == "win32" else sh_path)
                }

        # 系统 PATH fallback
        which_allure = shutil.which("allure")
        if which_allure:
            return {
                "home_dir": os.path.dirname(os.path.dirname(which_allure)),
                "executable": os.path.abspath(which_allure)
            }

        return {"home_dir": None, "executable": None}

    @classmethod
    def discover_java_runtime(cls) -> Optional[str]:
        """
        智能探测系统 Java 运行环境 (JRE / JDK 11+，渲染 Allure HTML 报告必备)。
        """
        # 1. 检查 JAVA_HOME / JDK_HOME
        for env_var in ["JAVA_HOME", "JDK_HOME"]:
            j_home = os.environ.get(env_var, "").strip()
            if j_home:
                exe = os.path.join(j_home, "bin", "java.exe" if sys.platform == "win32" else "java")
                if os.path.isfile(exe):
                    return os.path.abspath(exe)

        # 2. 检查系统 PATH
        which_java = shutil.which("java")
        if which_java:
            return os.path.abspath(which_java)

        # 3. 常见默认安装路径扫描
        if sys.platform == "win32":
            java_patterns = [
                r"C:\Program Files\Java\*\bin\java.exe",
                r"C:\Program Files\Eclipse Adoptium\*\bin\java.exe",
                r"C:\Program Files\Amazon Corretto\*\bin\java.exe",
                r"C:\Program Files\Zulu\*\bin\java.exe",
                r"C:\Program Files\BellSoft\*\bin\java.exe",
                r"D:\Program Files\Java\*\bin\java.exe",
                r"D:\data\Java\*\bin\java.exe",
            ]
            for pat in java_patterns:
                matched = glob.glob(pat)
                if matched:
                    return os.path.abspath(matched[0])

        return None

    @classmethod
    def discover_mobile_toolchain(cls) -> Dict[str, Optional[str]]:
        """
        智能探测移动端 ADB 与 HDC 工具链绝对路径。
        """
        tools = {"adb": None, "hdc": None}

        # 1. ADB 探测
        adb_candidates = []
        for env_var in ["ANDROID_HOME", "ANDROID_SDK_ROOT"]:
            sdk = os.environ.get(env_var, "").strip()
            if sdk:
                adb_candidates.append(os.path.join(sdk, "platform-tools", "adb.exe" if sys.platform == "win32" else "adb"))
        if sys.platform == "win32":
            adb_candidates.append(os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"))

        for cand in adb_candidates:
            if cand and os.path.isfile(cand):
                tools["adb"] = os.path.abspath(cand)
                break
        if not tools["adb"]:
            tools["adb"] = shutil.which("adb")

        # 2. HDC 探测
        hdc_candidates = []
        for env_var in ["HDC_HOME", "OHOS_BASE_SDK_HOME", "HARMONY_SDK_HOME"]:
            h_sdk = os.environ.get(env_var, "").strip()
            if h_sdk:
                hdc_candidates.append(os.path.join(h_sdk, "toolchains", "hdc.exe" if sys.platform == "win32" else "hdc"))
                hdc_candidates.append(os.path.join(h_sdk, "hdc.exe" if sys.platform == "win32" else "hdc"))

        for cand in hdc_candidates:
            if cand and os.path.isfile(cand):
                tools["hdc"] = os.path.abspath(cand)
                break
        if not tools["hdc"]:
            tools["hdc"] = shutil.which("hdc")

        return tools
