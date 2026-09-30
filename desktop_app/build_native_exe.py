# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - EXE 打包脚本
=======================================================
用途：
1. 将 desktop_app/main.py 编译为纯原生 Windows 独立应用程序
2. 环境净化：自动过滤 PATH 中的第三方不兼容 DLL 注入 (如 poppler/icuuc.dll)
3. 产物后处理与自愈：清理冲突文件，确保 PyQt6 原生链接 Windows 系统 DLL
4. 自动生成配套的 Inno Setup 安装包制作脚本
"""
import os
import sys
import shutil
import subprocess

# 强制终端输出兼容 UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)


def sanitize_build_environment() -> dict:
    """
    深度净化构建环境变量，剔除第三方工具路径中冲突的 DLL。
    Windows 下 PyQt6 依赖 C:\\Windows\\System32\\icuuc.dll。
    若 PATH 中含有第三方 poppler/icuuc.dll，PyInstaller 会将其误复制进 _internal，
    导致运行时报 [WinError 127 找不到指定的程序]。
    """
    clean_env = os.environ.copy()
    current_path = clean_env.get("PATH", "")
    filtered_dirs = []

    for path_item in current_path.split(os.pathsep):
        p_clean = path_item.strip()
        if not p_clean:
            continue
        # 排除包含冲突 icuuc.dll 或第三方运行时工具库的路径
        p_lower = p_clean.lower()
        if "poppler" in p_lower or "codex-runtimes" in p_lower:
            continue
        filtered_dirs.append(p_clean)

    # 确保 Windows 系统核心目录排列在最前
    sys32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    if sys32 not in filtered_dirs and os.path.isdir(sys32):
        filtered_dirs.insert(0, sys32)

    clean_env["PATH"] = os.pathsep.join(filtered_dirs)
    return clean_env


def post_build_cleanup(dist_app_dir: str):
    """
    打包后产物自愈与校验：清理 _internal 目录中被错误打包进来的第三方冲突 DLL。
    """
    internal_dir = os.path.join(dist_app_dir, "_internal")
    if not os.path.isdir(internal_dir):
        return

    # 需清理的冲突 DLL 列表
    conflict_dlls = ["icuuc.dll", "icudt78.dll", "icudt77.dll", "icudt76.dll"]
    for dll_name in conflict_dlls:
        target_file = os.path.join(internal_dir, dll_name)
        if os.path.exists(target_file):
            try:
                os.remove(target_file)
                print(f"[产物净化] 已自动清理第三方冲突 DLL: {dll_name}")
            except Exception as e:
                print(f"[产物净化] 清理 {dll_name} 提示: {e}")


def generate_inno_setup_script(output_dir: str):
    """生成 Inno Setup 安装包脚本"""
    iss_content = f"""[Setup]
AppName=三条IM自动化测试控制台
AppVersion=2.5.0
DefaultDirName={{autopf}}\\SantiaoAntiDesktop
DefaultGroupName=三条IM自动化测试控制台
OutputDir={output_dir}\\SetupInstaller
OutputBaseFilename=Santiao_IM_Native_Setup_v2.5.0
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Files]
Source: "{output_dir}\\三条IM自动化测试控制台\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{autoprograms}}\\三条IM自动化测试控制台"; Filename: "{{app}}\\三条IM自动化测试控制台.exe"
Name: "{{autodesktop}}\\三条IM自动化测试控制台"; Filename: "{{app}}\\三条IM自动化测试控制台.exe"

[Run]
Filename: "{{app}}\\三条IM自动化测试控制台.exe"; Description: "运行 三条IM自动化测试控制台"; Flags: nowait postinstall skipifsilent
"""
    iss_path = os.path.join(CURRENT_DIR, "installer.iss")
    with open(iss_path, "w", encoding="utf-8") as f:
        f.write(iss_content)
    print(f"[Inno Setup] 原生安装包脚本已生成: {iss_path}")


def check_and_kill_running_instance():
    """打包前关闭可能正在运行的旧实例，防止 DLL 占用导致拒绝访问"""
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "三条IM自动化测试控制台.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(1)
        except Exception:
            pass


def build():
    check_and_kill_running_instance()
    print("==================================================")
    print(" [打包] 正在打包 纯原生 Windows 独立桌面端 (PyQt6 架构)...")
    print("==================================================")

    main_entry = os.path.join(CURRENT_DIR, "main.py")
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    build_dir = os.path.join(PROJECT_ROOT, "build_native")

    target_app_dir = os.path.join(dist_dir, "三条IM自动化测试控制台")
    if os.path.exists(target_app_dir):
        import time
        for _ in range(5):
            try:
                shutil.rmtree(target_app_dir)
                break
            except Exception:
                time.sleep(0.8)

    # 1. 净化环境变量，杜绝不兼容动态链接库被打包
    build_env = sanitize_build_environment()

    # 2. 构造 PyInstaller 编译参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=三条IM自动化测试控制台",
        "--noconfirm",
        "--onedir",
        "--windowed", # 隐藏黑框控制台，以真正的 Windows 窗口程序运行
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--paths={PROJECT_ROOT}",
        f"--add-data={os.path.join(CURRENT_DIR, 'resources')};desktop_app/resources",
        "--hidden-import=desktop_app",
        "--hidden-import=desktop_app.style",
        "--hidden-import=desktop_app.config",
        "--hidden-import=desktop_app.core",
        "--hidden-import=desktop_app.core.device_manager",
        "--hidden-import=desktop_app.core.test_collector",
        "--hidden-import=desktop_app.core.test_runner",
        "--hidden-import=desktop_app.ui",
        "--hidden-import=desktop_app.ui.main_window",
        "--hidden-import=desktop_app.ui.mobile_page",
        "--hidden-import=desktop_app.ui.web_page",
        "--hidden-import=desktop_app.ui.api_page",
        "--hidden-import=desktop_app.ui.devices_page",
        "--hidden-import=desktop_app.ui.reports_page",
        "--hidden-import=web_platform",
        "--hidden-import=web_platform.backend",
        "--hidden-import=web_platform.backend.collector",
        "--hidden-import=web_platform.backend.devices",
        "--hidden-import=web_platform.backend.paths",
        "--hidden-import=web_platform.backend.runner",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=pytest",
        "--hidden-import=allure_pytest",
        main_entry
    ]

    print("执行命令: " + " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, env=build_env, check=True)

    # 3. 产物后处理与清理自愈
    app_output_dir = os.path.join(dist_dir, "三条IM自动化测试控制台")
    post_build_cleanup(app_output_dir)

    # 4. 生成 Inno Setup 安装包制作脚本
    generate_inno_setup_script(dist_dir)

    print("\n==================================================")
    print(" [成功] 打包完成！纯原生 Windows 独立桌面软件已就绪：")
    print(f" 目录: {app_output_dir}")
    print(f" 主程序: {os.path.join(app_output_dir, '三条IM自动化测试控制台.exe')}")
    print(f" 安装包配置脚本: {os.path.join(CURRENT_DIR, 'installer.iss')}")
    print("==================================================")


if __name__ == '__main__':
    build()
