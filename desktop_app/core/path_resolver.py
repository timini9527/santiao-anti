# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 - 环境解析器 (SmartPathResolver)
=======================================================
设计原则：
1. 遵循标准工程规范：直接通过系统 cmd 命令 (where / shutil.which) 及标准环境变量检索工具链。
2. 坚决摒弃复杂扫盘与注册表黑魔法：找不到即代表本机未安装或未加入环境变量，直接返回 None，
   避免猜测路径导致加载错误或残留环境。
3. 高效极简：零冗余磁盘 I/O，毫秒级响应。
"""

import os
import sys
import shutil
import subprocess
from typing import Dict, List, Optional


def ensure_cross_platform_path() -> None:
    """
    跨平台环境变量健全性自愈补全：
    解决 macOS / Linux 下桌面 GUI 应用由于未加载 shell profile 导致 PATH 缺失，
    无法定位 homebrew (如 /opt/homebrew/bin)、nvm、sdk 等命令行工具链的固有顽疾。
    """
    if sys.platform == "darwin":
        import glob
        extra_paths = [
            "/opt/homebrew/bin",
            "/opt/homebrew/sbin",
            "/usr/local/bin",
            "/usr/local/sbin",
            os.path.expanduser("~/bin"),
            os.path.expanduser("~/.local/bin"),
            # Android SDK 默认目录 (adb)
            os.path.expanduser("~/Library/Android/sdk/platform-tools"),
            # 鸿蒙 DevEco Studio 内置默认 toolchains 目录 (hdc)
            "/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains",
            "/Applications/DevEco-Studio.app/Contents/tools/ohpm/bin",
        ]
        glob_patterns = [
            os.path.expanduser("~/Library/Huawei/Sdk/*/openharmony/toolchains"),
            os.path.expanduser("~/Library/Huawei/Sdk/openharmony/*/toolchains"),
            os.path.expanduser("~/Library/OpenHarmony/Sdk/*/toolchains"),
            os.path.expanduser("~/Library/Python/3.*/bin"),
            "/Library/Frameworks/Python.framework/Versions/3.*/bin",
            os.path.expanduser("~/.nvm/versions/node/*/bin"),
        ]
        for pat in glob_patterns:
            try:
                for matched in sorted(glob.glob(pat), reverse=True):
                    if os.path.isdir(matched):
                        extra_paths.append(matched)
            except Exception:
                pass
        current_path = os.environ.get("PATH", "")
        parts = current_path.split(":")
        for p in extra_paths:
            if os.path.isdir(p) and p not in parts:
                parts.insert(0, p)
        os.environ["PATH"] = ":".join(parts)


ensure_cross_platform_path()


class SmartPathResolver:
    """系统环境与项目路径解析器"""

    _cached_project_root: Optional[str] = None
    _cached_python_runtime: Optional[Dict[str, Optional[str]]] = None
    _cached_java_home: Optional[str] = None
    _cached_inno_compiler: Optional[str] = None
    _cached_allure_cli: Optional[Dict[str, Optional[str]]] = None
    _cached_mobile_toolchain: Optional[Dict[str, Optional[str]]] = None

    @classmethod
    def get_project_root(cls) -> str:
        """
        获取项目真实根目录。
        1. 环境变量 SANTIAO_PROJECT_ROOT 显式指定
        2. 打包运行态 (sys.frozen)：主程序 exe 所在目录
        3. 源码开发态：向上回溯寻找 tests 或 config 目录
        4. 兜底回退：当前工作目录
        """
        if cls._cached_project_root and os.path.isdir(cls._cached_project_root):
            return cls._cached_project_root

        # 1. 显式环境变量
        env_root = os.environ.get("SANTIAO_PROJECT_ROOT", "").strip()
        if env_root and os.path.isdir(env_root):
            cls._cached_project_root = os.path.abspath(env_root)
            return cls._cached_project_root

        # 2. 打包运行态
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            # 2.1 若位于最终安装目录 (同级已被安装包释放了 tests 或 config 资源)
            if os.path.isdir(os.path.join(exe_dir, "tests")) or os.path.isdir(os.path.join(exe_dir, "config")):
                cls._cached_project_root = exe_dir
                return cls._cached_project_root
            # 2.2 macOS .app Bundle 标准资源目录 (Contents/Resources) 与 PyInstaller _MEIPASS
            meipass = getattr(sys, "_MEIPASS", "")
            if meipass and (os.path.isdir(os.path.join(meipass, "tests")) or os.path.isdir(os.path.join(meipass, "config"))):
                cls._cached_project_root = os.path.abspath(meipass)
                return cls._cached_project_root
            mac_resources = os.path.abspath(os.path.join(exe_dir, "..", "Resources"))
            if os.path.isdir(os.path.join(mac_resources, "tests")) or os.path.isdir(os.path.join(mac_resources, "config")):
                cls._cached_project_root = mac_resources
                return cls._cached_project_root
            # 2.3 若位于本地工程编译产物目录 (dist/三条IM自动化测试控制台)，向上回溯定位工程根目录
            parent = os.path.dirname(exe_dir)
            while parent and parent != os.path.dirname(parent):
                if os.path.isdir(os.path.join(parent, "tests")) or os.path.isdir(os.path.join(parent, "config")):
                    cls._cached_project_root = parent
                    return cls._cached_project_root
                parent = os.path.dirname(parent)
            cls._cached_project_root = exe_dir
            return cls._cached_project_root

        # 3. 源码态：向上递归查找项目特征目录
        current = os.path.dirname(os.path.abspath(__file__))
        while True:
            if os.path.isdir(os.path.join(current, "tests")) or os.path.isdir(os.path.join(current, "config")):
                cls._cached_project_root = current
                return cls._cached_project_root
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        # 4. 兜底当前目录
        cls._cached_project_root = os.path.abspath(os.getcwd())
        return cls._cached_project_root

    @classmethod
    def _find_cmd(cls, cmd_name: str) -> Optional[str]:
        """
        通过系统原生命令探测工具绝对路径。
        过滤 WindowsApps 微软商店占位符替身。找不到直接返回 None。
        """
        # 1. 首选标准库快速查询
        found = shutil.which(cmd_name)
        if found and os.path.isfile(found) and "windowsapps" not in found.lower():
            return os.path.abspath(found)

        # 2. Windows 环境下调用 where 命令检索所有候选路径
        if sys.platform == "win32":
            try:
                proc = subprocess.run(
                    ["where", cmd_name],
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=2
                )
                if proc.returncode == 0 and proc.stdout:
                    for line in proc.stdout.splitlines():
                        candidate = line.strip()
                        if candidate and os.path.isfile(candidate) and "windowsapps" not in candidate.lower():
                            return os.path.abspath(candidate)
            except Exception:
                pass

        return None

    @classmethod
    def discover_python_runtime(cls, force_refresh: bool = False) -> Dict[str, Optional[str]]:
        """
        定位 Python 运行环境。
        找不到即代表环境未就绪，返回 None。
        """
        if not force_refresh and cls._cached_python_runtime:
            return cls._cached_python_runtime

        root = cls.get_project_root()
        exe_path: Optional[str] = None

        # 1. 项目内置独立便携包 (如果有)
        portable_py = os.path.join(root, "python_runtime", "python.exe" if sys.platform == "win32" else "bin/python")
        if os.path.isfile(portable_py):
            exe_path = os.path.abspath(portable_py)

        # 2. 源码开发状态下当前正在执行的 Python
        elif not getattr(sys, "frozen", False) and sys.executable and os.path.isfile(sys.executable):
            exe_path = os.path.abspath(sys.executable)

        # 3. 命令行 where python 查找
        if not exe_path:
            exe_path = cls._find_cmd("python") or cls._find_cmd("python3")

        if exe_path and os.path.isfile(exe_path):
            parent = os.path.dirname(exe_path)
            # 若位于 Scripts 或 bin 虚拟环境目录，推导实际环境根目录
            if os.path.basename(parent).lower() in ["scripts", "bin"]:
                home_dir = os.path.dirname(parent)
            else:
                home_dir = parent

            cls._cached_python_runtime = {
                "executable": exe_path,
                "home_dir": os.path.abspath(home_dir)
            }
            return cls._cached_python_runtime

        # 找不到环境，绝不去猜其他路径
        cls._cached_python_runtime = {
            "executable": None,
            "home_dir": None
        }
        return cls._cached_python_runtime

    @classmethod
    def discover_java_home(cls, force_refresh: bool = False) -> Optional[str]:
        """
        定位 Java 运行环境根目录 (JAVA_HOME)。
        1. 优先读取系统环境变量 JAVA_HOME / JDK_HOME
        2. 通过 cmd 命令 where java 解析其所在根目录
        找不到即返回 None。
        """
        if not force_refresh and cls._cached_java_home:
            return cls._cached_java_home

        # 1. 环境变量优先
        for env_k in ["JAVA_HOME", "JDK_HOME"]:
            val = os.environ.get(env_k, "").strip()
            if val and os.path.isdir(val):
                java_bin = os.path.join(val, "bin", "java.exe" if sys.platform == "win32" else "java")
                if os.path.isfile(java_bin):
                    cls._cached_java_home = os.path.abspath(val)
                    return cls._cached_java_home

        # 2. 通过 where java 反推
        java_exe = cls._find_cmd("java")
        if java_exe:
            real_path = os.path.realpath(java_exe)
            bin_dir = os.path.dirname(real_path)
            candidate_home = os.path.dirname(bin_dir)
            if os.path.isdir(candidate_home):
                cls._cached_java_home = os.path.abspath(candidate_home)
                return cls._cached_java_home

        cls._cached_java_home = None
        return None

    @classmethod
    def discover_inno_compiler(cls, force_refresh: bool = False) -> Optional[str]:
        """
        定位 Inno Setup 编译器 (ISCC.exe)。
        直接通过 cmd 命令 where iscc 查找，找不到即返回 None。
        """
        if not force_refresh and cls._cached_inno_compiler:
            return cls._cached_inno_compiler

        # 1. 优先检查 cmd 命令与环境变量
        found = cls._find_cmd("iscc") or cls._find_cmd("iscc.exe")
        if found:
            cls._cached_inno_compiler = os.path.abspath(found)
            return cls._cached_inno_compiler

        # 2. 未配置 PATH 时，秒级检查各盘标准 Program Files 默认安装目录 (绝不全盘递归)
        if sys.platform == "win32":
            import glob
            for drv in ["C", "D", "E", "F"]:
                for sub in ["Program Files", "Program Files (x86)"]:
                    patterns = [
                        rf"{drv}:\{sub}\Inno Setup*\ISCC.exe",
                        rf"{drv}:\Inno Setup*\ISCC.exe",
                    ]
                    for pat in patterns:
                        for matched in glob.glob(pat):
                            if os.path.isfile(matched):
                                cls._cached_inno_compiler = os.path.abspath(matched)
                                return cls._cached_inno_compiler

        cls._cached_inno_compiler = None
        return None

    @classmethod
    def discover_allure_cli(cls, force_refresh: bool = False) -> Dict[str, Optional[str]]:
        """
        定位 Allure-CLI 命令行工具。
        1. 项目根目录或 exe 同级下的 allure-cli 目录
        2. cmd 命令 where allure
        找不到即返回 None。
        """
        if not force_refresh and cls._cached_allure_cli:
            return cls._cached_allure_cli

        root = cls.get_project_root()
        local_candidates = [
            os.path.join(root, "allure-cli"),
            os.path.join(os.path.dirname(root), "allure-cli")
        ]
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            local_candidates.insert(0, os.path.join(exe_dir, "allure-cli"))

        for cand in local_candidates:
            bat_bin = os.path.join(cand, "bin", "allure.bat" if sys.platform == "win32" else "allure")
            if os.path.isfile(bat_bin):
                cls._cached_allure_cli = {
                    "home_dir": os.path.abspath(cand),
                    "executable": os.path.abspath(bat_bin)
                }
                return cls._cached_allure_cli

        # cmd 命令查找
        allure_bin = cls._find_cmd("allure") or cls._find_cmd("allure.bat") or cls._find_cmd("allure.cmd")
        if allure_bin:
            home = os.path.dirname(os.path.dirname(allure_bin))
            cls._cached_allure_cli = {
                "home_dir": os.path.abspath(home),
                "executable": os.path.abspath(allure_bin)
            }
            return cls._cached_allure_cli

        cls._cached_allure_cli = {"home_dir": None, "executable": None}
        return cls._cached_allure_cli

    @classmethod
    def get_asset_path(cls, subpath: str) -> Optional[str]:
        """
        全场景鲁棒定位项目/运行时内置资产文件 (支持源码开发态、PyInstaller 打包态与 Inno Setup 安装态)。
        subpath 示例: "desktop_app/assets/android/scrcpy-server" 或 "desktop_app/assets/harmony/agent.so"
        """
        subpath_norm = subpath.replace("/", os.sep)
        candidates = []

        # 1. 打包运行态：优先检索 _internal 与 sys._MEIPASS 以及同级目录
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", "")
            if meipass and os.path.isdir(meipass):
                candidates.append(os.path.join(meipass, subpath_norm))
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            candidates.append(os.path.join(exe_dir, "_internal", subpath_norm))
            candidates.append(os.path.join(exe_dir, subpath_norm))

        # 2. 源码开发态与安装态外层目录
        root = cls.get_project_root()
        candidates.append(os.path.join(root, subpath_norm))

        for cand in candidates:
            if os.path.isfile(cand) or os.path.isdir(cand):
                return os.path.abspath(cand)

        return None

    @classmethod
    def discover_mobile_toolchain(cls, force_refresh: bool = False) -> Dict[str, Optional[str]]:
        """
        定位移动端调试工具链 (ADB / HDC / iOS 工具链: tidevice, idevice_id, xcrun)。
        优先级策略 (傻瓜式开箱即用闭环):
        1. 优先检索程序安装目录或项目根目录下的内置 bin/ 目录 (免装 SDK、零配置开箱即用)；
        2. 检索专用环境变量 (ANDROID_HOME / HDC_HOME 等)；
        3. 检索系统 PATH 命令 (where/which 工具)；找不到返回 None。
        """
        if not force_refresh and cls._cached_mobile_toolchain:
            return cls._cached_mobile_toolchain

        tools: Dict[str, Optional[str]] = {
            "adb": None,
            "hdc": None,
            "tidevice": None,
            "idevice_id": None,
            "xcrun": None,
        }

        # 0. 优先检测内置绿色 bin/ 工具链目录 (涵盖 _internal、sys._MEIPASS、exe_dir 与项目根目录)
        root = cls.get_project_root()
        bin_candidates = [
            os.path.join(root, "bin"),
            os.path.join(os.path.dirname(root), "bin")
        ]
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", "")
            if meipass and os.path.isdir(meipass):
                bin_candidates.insert(0, os.path.join(meipass, "bin"))
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            bin_candidates.insert(0, os.path.join(exe_dir, "_internal", "bin"))
            bin_candidates.insert(0, os.path.join(exe_dir, "bin"))

        for b_dir in bin_candidates:
            if not os.path.isdir(b_dir):
                continue
            cand_adb = os.path.join(b_dir, "adb.exe" if sys.platform == "win32" else "adb")
            cand_hdc = os.path.join(b_dir, "hdc.exe" if sys.platform == "win32" else "hdc")
            cand_tidevice = os.path.join(b_dir, "tidevice.exe" if sys.platform == "win32" else "tidevice")
            cand_idevice = os.path.join(b_dir, "idevice_id.exe" if sys.platform == "win32" else "idevice_id")
            if not tools["adb"] and os.path.isfile(cand_adb):
                tools["adb"] = os.path.abspath(cand_adb)
            if not tools["hdc"] and os.path.isfile(cand_hdc):
                tools["hdc"] = os.path.abspath(cand_hdc)
            if not tools["tidevice"] and os.path.isfile(cand_tidevice):
                tools["tidevice"] = os.path.abspath(cand_tidevice)
            if not tools["idevice_id"] and os.path.isfile(cand_idevice):
                tools["idevice_id"] = os.path.abspath(cand_idevice)

        # 1. ADB 降级检索: ANDROID_HOME 环境变量 -> cmd 命令 where adb
        if not tools["adb"]:
            android_home = os.environ.get("ANDROID_HOME", "").strip() or os.environ.get("ANDROID_SDK_ROOT", "").strip()
            if android_home and os.path.isdir(android_home):
                adb_file = os.path.join(android_home, "platform-tools", "adb.exe" if sys.platform == "win32" else "adb")
                if os.path.isfile(adb_file):
                    tools["adb"] = os.path.abspath(adb_file)

        if not tools["adb"]:
            tools["adb"] = cls._find_cmd("adb")

        # 2. HDC 降级检索: HDC_HOME 环境变量 -> cmd 命令 where hdc
        if not tools["hdc"]:
            hdc_home = os.environ.get("HDC_HOME", "").strip() or os.environ.get("OHOS_BASE_SDK_HOME", "").strip()
            if hdc_home and os.path.isdir(hdc_home):
                for sub in ["toolchains/hdc.exe" if sys.platform == "win32" else "toolchains/hdc", "hdc.exe" if sys.platform == "win32" else "hdc"]:
                    hdc_file = os.path.join(hdc_home, sub.replace("/", os.sep))
                    if os.path.isfile(hdc_file):
                        tools["hdc"] = os.path.abspath(hdc_file)
                        break

        if not tools["hdc"]:
            tools["hdc"] = cls._find_cmd("hdc")

        # 3. iOS 工具链检索: tidevice / idevice_id / xcrun
        if not tools["tidevice"]:
            tools["tidevice"] = cls._find_cmd("tidevice")

        if not tools["idevice_id"]:
            tools["idevice_id"] = cls._find_cmd("idevice_id")

        if sys.platform == "darwin":
            tools["xcrun"] = cls._find_cmd("xcrun")

        cls._cached_mobile_toolchain = tools
        return tools

    @classmethod
    def discover_project_assets(cls, source_root: str) -> Dict[str, List[str]]:
        """
        精确收敛纯测试业务模块与核心配置文件（供构建与独立运行使用）。
        严禁将临时目录 (build_native, temp_dist_core, tmp)、无关平台代码 (web_platform, web_console_v2)、
        桌面端源码自身 (desktop_app) 以及根目录历史调试脚本拷贝进发布运行包。
        """
        source_root = os.path.abspath(source_root)

        # 1. 严格限定必须同步的测试业务模块白名单 (包含绿色工具链 bin)
        candidate_dirs = [
            "tests", "pages", "locators", "common", "core",
            "business_helpers", "config", "data", "utils", "apis",
            "resources", "strategy", "performance", "IOS", "bin", "scripts"
        ]
        business_dirs = [
            d for d in candidate_dirs
            if os.path.isdir(os.path.join(source_root, d))
        ]

        # 2. 严格限定必须同步的测试核心配置文件
        candidate_files = [
            "pytest.ini", "conftest.py", "requirements.txt"
        ]
        core_files = [
            f for f in candidate_files
            if os.path.isfile(os.path.join(source_root, f))
        ]

        return {
            "business_dirs": sorted(business_dirs),
            "core_files": sorted(core_files)
        }


# 兼容简写别名
PathResolver = SmartPathResolver
