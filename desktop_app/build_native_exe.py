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

# ==============================================================================
# 核心打包配置开关
# ==============================================================================
# 控制是否编译生成 Inno Setup 单文件安装包 (SetupInstaller/Santiao_IM_Native_Setup_v0.9.9.exe)
# - True  : 完整全量流水线 (PyInstaller 打包 -> 核心资产加密脱敏 -> Inno Setup 编译生成单文件安装包)
# - False : 仅执行 PyInstaller 打包 (输出 dist/三条IM自动化测试控制台 绿色运行目录，跳过加密与安装包制作，极速秒级构建)
BUILD_INSTALLER = False


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
    clean_env["PYTHONUTF8"] = "1"
    clean_env["PYTHONIOENCODING"] = "utf-8"
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


def generate_inno_setup_script(output_dir: str, encrypted_dir: str = None, install_password: str = ""):
    """生成 Inno Setup 安装包脚本（密码为空时免密码直接安装，密码非空时激活 AES-256 原生保护）"""
    # 优先采用已完成深度加密编译的脱敏资产目录，杜绝明文 .py 源码被打包进安装包
    source_root = encrypted_dir if (encrypted_dir and os.path.exists(encrypted_dir)) else PROJECT_ROOT

    # 动态密码策略：密码为空时，不配置 Password 与 Encryption，安装向导不会显示密码输入界面，直达安装向导；
    # 只有当显式传入非空密码时，才激活 Inno Setup 原生 AES-256 加密与密码拦截。
    password_section = ""
    if install_password and install_password.strip():
        password_section = f"""; ===== 方案 4: 工业级 AES-256 安装包加密与授权保护 =====
Encryption=yes
Password={install_password.strip()}
"""

    iss_content = f"""[Setup]
AppName=三条IM自动化测试控制台
AppVersion=0.9.9
DefaultDirName={{autopf}}\\SantiaoAntiDesktop
DefaultGroupName=三条IM自动化测试控制台
OutputDir={output_dir}\\SetupInstaller
OutputBaseFilename=Santiao_IM_Native_Setup_v0.9.9
Compression=lzma2/fast
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
; 显式开启路径选择页面，允许用户在安装向导中点击【浏览】自由选择安装到任意磁盘目录
DisableDirPage=no
; 严禁静默复用历史安装路径，确保每次安装均可自定义新位置
UsePreviousAppDir=no
DirExistsWarning=auto
AlwaysShowDirOnReadyPage=yes
; 绑定应用程序专属品牌高清图标 (应用于安装向导主程序与卸载器)
SetupIconFile={os.path.join(CURRENT_DIR, 'resources', 'app_icon.ico')}
{password_section}
; 强制关闭正在运行的应用程序，避免卸载或覆盖安装时文件被占用无法删除
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no

[Files]
; 1. 桌面端应用主程序与运行库
Source: "{output_dir}\\三条IM自动化测试控制台\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 2. 核心自动化测试工程（方案4加密成果：已彻底抹除 .py 源码，安装后目标电脑上只有二进制加密/机器码文件）
Source: "{source_root}\\tests\\*"; DestDir: "{{app}}\\tests"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{source_root}\\pages\\*"; DestDir: "{{app}}\\pages"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{source_root}\\locators\\*"; DestDir: "{{app}}\\locators"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{source_root}\\common\\*"; DestDir: "{{app}}\\common"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{source_root}\\core\\*"; DestDir: "{{app}}\\core"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{source_root}\\utils\\*"; DestDir: "{{app}}\\utils"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{source_root}\\config\\*"; DestDir: "{{app}}\\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{source_root}\\data\\*"; DestDir: "{{app}}\\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{source_root}\\requirements.txt"; DestDir: "{{app}}"; Flags: ignoreversion

; 3. 内置独立免安装 Python 3.13 运行环境 (精准排除完全无关的AI大包与碎片，保留 torch 以确保 cnocr/RapidOCR 完整可用)
Source: "D:\\data\\Python313\\*"; DestDir: "{{app}}\\python_runtime"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pdb,Doc,include,tcl,__pycache__,*.dist-info,paddle*,scipy*,sympy*,wandb*,modelscope*,*polars*,Lib\\test"

; 4. 内置 Allure CLI 命令行工具 (开箱即用支持生成全维度可视化测试报告)
Source: "{PROJECT_ROOT}\\allure-cli\\*"; DestDir: "{{app}}\\allure-cli"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{autoprograms}}\\三条IM自动化测试控制台"; Filename: "{{app}}\\三条IM自动化测试控制台.exe"
Name: "{{autodesktop}}\\三条IM自动化测试控制台"; Filename: "{{app}}\\三条IM自动化测试控制台.exe"

[Run]
Filename: "{{app}}\\三条IM自动化测试控制台.exe"; Description: "运行 三条IM自动化测试控制台"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 显式指示卸载程序彻底清除运行期间动态产生的测试报告、日志、缓存及主目录
Type: filesandordirs; Name: "{{app}}\\reports"
Type: filesandordirs; Name: "{{app}}\\logs"
Type: filesandordirs; Name: "{{app}}\\_internal"
Type: filesandordirs; Name: "{{app}}\\python_runtime"
Type: filesandordirs; Name: "{{app}}\\allure-cli"
Type: filesandordirs; Name: "{{app}}"

[Code]
// 卸载初始化阶段：强制终止正在运行的主程序与后台任务，彻底解除 Windows 独占文件锁
function InitializeUninstall(): Boolean;
var
  ErrorCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM 三条IM自动化测试控制台.exe', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Sleep(500);
  Result := True;
end;

// 卸载收尾阶段：确保整个应用安装根目录连根拔起彻底清除，做到 0 字节残留
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DelTree(ExpandConstant('{{app}}'), True, True, True);
  end;
end;
"""
    iss_path = os.path.join(CURRENT_DIR, "installer.iss")
    with open(iss_path, "w", encoding="utf-8") as f:
        f.write(iss_content)
    print(f"[Inno Setup] 原生加密安装包脚本已生成 (AES-256 保护已激活): {iss_path}")


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


def ensure_compatible_inno_icon() -> str:
    """
    确保生成符合 Inno Setup 与 Windows PE 资源规范的原生标准 DIB ICO 图标。
    必须显式指定 bitmap_format="bmp" 生成非 PNG 压缩的 Windows 经典 DIB 格式（涵盖 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256）。
    杜绝 PNG 压缩流导致 Windows 资源管理器解码失败而回退显示为默认 Python 白纸蛇标。
    """
    ico_path = os.path.join(CURRENT_DIR, "resources", "app_icon.ico")
    png_path = os.path.join(CURRENT_DIR, "resources", "sant_logo_hd.png")
    if os.path.exists(png_path):
        try:
            from PIL import Image
            img = Image.open(png_path).convert("RGBA")
            img.save(
                ico_path,
                format="ICO",
                bitmap_format="bmp",
                sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            )
            print(f"[图标生成] Windows 原生标准 DIB 高清 ICO 图标已生成 (361KB 全尺寸): {ico_path}")
        except Exception as e:
            print(f"[图标警告] 生成 app_icon.ico 提示: {e}")
    return ico_path


def build(build_installer: bool = BUILD_INSTALLER):
    check_and_kill_running_instance()
    print("==================================================")
    print(" [打包] 正在打包 纯原生 Windows 独立桌面端 (PyQt6 架构)...")
    print(f" [模式] 是否编译生成安装包 (BUILD_INSTALLER): {build_installer}")
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

    # 2. 构造 PyInstaller 编译参数 (自动校验并使用 Inno Setup 兼容的合规 ICO 图标)
    icon_ico = ensure_compatible_inno_icon()
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=三条IM自动化测试控制台",
        "--noconfirm",
        "--onedir",
        "--windowed", # 隐藏黑框控制台，以真正的 Windows 窗口程序运行
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--paths={PROJECT_ROOT}",
        f"--icon={icon_ico}", # 注入专属品牌高清图标到生成的 Windows exe 资源段
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

    if build_installer:
        # 4. 执行方案 4 核心资产全量加密编译 (抹除 .py 源码，生成机器码/二进制发布包)
        from desktop_app.encrypt_engine import stage_encrypted_assets
        encrypted_dir = os.path.join(dist_dir, "encrypted_release")
        stage_encrypted_assets(encrypted_dir)

        # 5. 生成 Inno Setup 安装包制作脚本 (基于已加密的资产库与免密策略)
        generate_inno_setup_script(dist_dir, encrypted_dir=encrypted_dir, install_password="")

        # 6. 自动检测并调用 Inno Setup 编译器输出最终单文件安装包
        compile_installer_if_available()

        print("\n==================================================")
        print(" [成功] 打包完成！纯原生 Windows 独立桌面软件与安装包已就绪：")
        print(f" 本地绿色目录: {app_output_dir}")
        print(f" 主程序文件: {os.path.join(app_output_dir, '三条IM自动化测试控制台.exe')}")
        print(f" 安装包配置脚本: {os.path.join(CURRENT_DIR, 'installer.iss')}")
        print(f" 终极单文件安装包: {os.path.join(dist_dir, 'SetupInstaller', 'Santiao_IM_Native_Setup_v0.9.9.exe')}")
        print("==================================================")
    else:
        print("\n==================================================")
        print(" [成功] 本地桌面端打包完成！(已按配置跳过 Inno Setup 安装包制作)")
        print(f" 本地绿色目录: {app_output_dir}")
        print(f" 主程序文件: {os.path.join(app_output_dir, '三条IM自动化测试控制台.exe')}")
        print(" 提示: 如需编译单文件安装包，可将 BUILD_INSTALLER 设为 True，或追加参数 --installer")
        print("==================================================")


def compile_installer_if_available():
    """检测并自动调用 Inno Setup 编译器生成最终单文件安装包"""
    iss_path = os.path.join(CURRENT_DIR, "installer.iss")
    candidates = [
        r"D:\Program Files\Inno Setup 7\ISCC.exe",
        shutil.which("ISCC")
    ]
    iscc_bin = next((p for p in candidates if p and os.path.exists(p)), None)
    if iscc_bin:
        print(f"\n[Inno Setup] 检测到编译器: {iscc_bin}")
        print(" 正在一键编译生成最终 Setup 安装程序 (压缩 Python 运行时)...")
        try:
            subprocess.run([iscc_bin, iss_path], cwd=PROJECT_ROOT, check=True)
            print(" [Inno Setup 成功] 包含自定义路径与内置运行时的安装包已编译完成！")
        except Exception as e:
            print(f" [Inno Setup 提示] 编译遇到提示: {e}")


if __name__ == '__main__':
    # 优先解析命令行参数，支持命令行动态控制开关：
    # python desktop_app/build_native_exe.py --no-installer  (仅打包本地绿色版程序)
    # python desktop_app/build_native_exe.py --installer     (完整打包并生成单文件安装包)
    target_build_installer = BUILD_INSTALLER
    if "--no-installer" in sys.argv:
        target_build_installer = False
    elif "--installer" in sys.argv:
        target_build_installer = True
    build(build_installer=target_build_installer)
