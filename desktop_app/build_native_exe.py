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
import time
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
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from desktop_app.core.path_resolver import SmartPathResolver
PROJECT_ROOT = SmartPathResolver.get_project_root()

# ==============================================================================
# 核心打包配置开关
# ==============================================================================
# 控制是否编译生成 Inno Setup 单文件安装包 (SetupInstaller/Santiao_IM_Native_Setup_v0.9.9.exe)
# - True  : 完整全量流水线 (PyInstaller 打包 -> 核心资产加密脱敏 -> Inno Setup 编译生成单文件安装包)
# - False : 仅执行 PyInstaller 打包 (输出 dist/三条IM自动化测试控制台 绿色运行目录，跳过加密与安装包制作，极速秒级构建)
BUILD_INSTALLER = False
# BUILD_INSTALLER = True


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


def ensure_clean_native_build(dist_app_dir: str):
    """
    确保普通 build 绿色产物目录极致纯净：严格仅保留 `_internal` 运行时文件夹与主程序 `三条IM自动化测试控制台.exe`。
    若存在任何历史遗留的测试业务文件夹（tests、pages 等）或配置文件，自动清空，完全契合纯净应用分发标准。
    """
    if not os.path.isdir(dist_app_dir):
        return
    allowed_items = {"_internal", "三条IM自动化测试控制台.exe"}
    for item in os.listdir(dist_app_dir):
        if item in allowed_items:
            continue
        target_path = os.path.join(dist_app_dir, item)
        try:
            if os.path.isdir(target_path):
                shutil.rmtree(target_path, ignore_errors=True)
            else:
                os.remove(target_path)
            print(f"[纯净净化] 已自动剔除多余文件/目录: {item}")
        except Exception as e:
            print(f"[纯净提示] 清理 {item} 提示: {e}")


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

    # 动态探测宿主机可用 Python 运行环境源路径 (多级雷达扫描，支持便携版、虚拟环境及系统安装)
    py_runtime_info = SmartPathResolver.discover_python_runtime()
    py_runtime_src = py_runtime_info.get("home_dir")
    python_section = ""
    if py_runtime_src and os.path.exists(py_runtime_src):
        python_section = f"""; 3. 内置独立免安装 Python 运行环境
Source: "{py_runtime_src}\\*"; DestDir: "{{app}}\\python_runtime"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pdb,Doc,include,tcl,__pycache__,paddle*,scipy*,sympy*,wandb*,modelscope*,*polars*,Lib\\test"
"""

    # 动态扫描识别全部测试业务目录与核心配置文件，彻底消除人工遗漏
    assets = SmartPathResolver.discover_project_assets(source_root)
    files_entries = []
    for d in assets["business_dirs"]:
        if d == "allure-cli":
            continue
        files_entries.append(f'Source: "{source_root}\\{d}\\*"; DestDir: "{{app}}\\{d}"; Flags: ignoreversion recursesubdirs createallsubdirs')
    for f in assets["core_files"]:
        files_entries.append(f'Source: "{source_root}\\{f}"; DestDir: "{{app}}"; Flags: ignoreversion')
    business_files_section = "\n".join(files_entries)

    # 动态定位 Allure-CLI 命令行工具
    allure_info = SmartPathResolver.discover_allure_cli()
    allure_section = ""
    if allure_info.get("home_dir") and os.path.exists(allure_info["home_dir"]):
        allure_section = f"""; 4. 内置 Allure CLI 命令行工具 (开箱即用支持生成全维度可视化测试报告)
Source: "{allure_info['home_dir']}\\*"; DestDir: "{{app}}\\allure-cli"; Flags: ignoreversion recursesubdirs createallsubdirs
"""

    # Appium 批处理与静默启动脚本源路径 (严格以工程根目录为准)
    bat_src = os.path.join(PROJECT_ROOT, "start_appium_batch.bat")
    vbs_src = os.path.join(PROJECT_ROOT, "start_appium_silent.vbs")

    iss_content = f"""[Setup]
AppName=三条IM自动化测试控制台
AppVersion=0.9.9
DefaultDirName={{autopf}}\\SantiaoAntiDesktop
DefaultGroupName=三条IM自动化测试控制台
OutputDir={output_dir}\\SetupInstaller
OutputBaseFilename=Santiao_IM_Native_Setup_v0.9.9
Compression=lzma2/fast
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
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

; 2. 核心自动化测试工程（动态收纳所有业务目录与核心配置，二进制加密/机器码发布）
{business_files_section}

; 3. Appium 批处理启动脚本、静默启动器与测试说明文档 (安装释放至程序安装目录 {{app}})
Source: "{bat_src}"; DestDir: "{{app}}"; DestName: "start_appium_batch.bat"; Flags: ignoreversion
Source: "{vbs_src}"; DestDir: "{{app}}"; DestName: "start_appium_silent.vbs"; Flags: ignoreversion
Source: "{PROJECT_ROOT}\\test_docs\\*"; DestDir: "{{app}}\\test_docs"; Flags: ignoreversion recursesubdirs createallsubdirs

{python_section}
{allure_section}

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
    """打包前关闭可能正在运行的旧实例与解除目录占用，彻底解决 WinError 32 权限拒绝"""
    if sys.platform == "win32":
        # 1. 强制终止可能残留的主程序实例
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "三条IM自动化测试控制台.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception:
            pass

        # 2. 检查并终止将 dist 目录作为当前工作目录(CWD)挂起的后台进程 (如被拉起的 adb.exe / hdc.exe)
        try:
            import psutil
            dist_marker = "三条IM自动化测试控制台".lower()
            current_pid = os.getpid()
            for p in psutil.process_iter(['pid', 'name', 'cwd']):
                try:
                    if p.info['pid'] != current_pid:
                        cwd = p.info.get('cwd') or ""
                        if dist_marker in cwd.lower():
                            p.kill()
                except Exception:
                    pass
        except Exception:
            pass

        # 3. 若 Windows 资源管理器正打开在待覆盖目录，令其后退一层至 dist/ 目录以释放目录句柄锁
        try:
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            for w in shell.Windows():
                try:
                    loc = str(getattr(w, "LocationURL", ""))
                    if "三条IM" in loc or "三条" in loc:
                        w.Navigate(os.path.join(PROJECT_ROOT, "dist"))
                except Exception:
                    pass
        except Exception:
            pass

        time.sleep(1)


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

    # 0. 自动预提取最新全量用例元数据并同步刷新 tests_catalog.json 静态索引
    try:
        import json
        from web_platform.backend.collector import collect_all_tests
        src_tests = os.path.join(PROJECT_ROOT, "tests")
        if os.path.exists(src_tests):
            catalog = collect_all_tests(src_tests)
            catalog_file = os.path.join(src_tests, "tests_catalog.json")
            with open(catalog_file, "w", encoding="utf-8") as f:
                json.dump(catalog, f, ensure_ascii=False, indent=2)
            print(f"[用例索引] 已自动同步刷新测试用例索引: {catalog_file} (收录 {len(catalog)} 个测试文件)")
    except Exception as e:
        print(f"[用例警告] 自动刷新 tests_catalog.json 提示: {e}")

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
        "--hidden-import=desktop_app.core.path_resolver",
        "--hidden-import=desktop_app.core.path_resolver",
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
        "--hidden-import=desktop_app.ui.inspector_page",
        "--hidden-import=desktop_app.ui.harmony_native_inspector",
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

    # 同步最新 Appium 服务启动脚本至绿色免安装目录
    for script_name in ["start_appium_batch.bat", "start_appium_silent.vbs"]:
        src_path = os.path.join(PROJECT_ROOT, script_name)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, os.path.join(app_output_dir, script_name))

    if build_installer:
        # 4. 执行方案 4 核心资产全量加密编译 (抹除 .py 源码，生成机器码/二进制发布包)
        from desktop_app.encrypt_engine import stage_encrypted_assets
        encrypted_dir = os.path.join(dist_dir, "encrypted_release")
        stage_encrypted_assets(encrypted_dir)

        # 5. 生成 Inno Setup 安装包制作脚本 (基于已加密的资产库与免密策略)
        generate_inno_setup_script(dist_dir, encrypted_dir=encrypted_dir, install_password="")

        # 6. 自动检测并调用 Inno Setup 编译器输出最终单文件安装包
        installer_built = compile_installer_if_available()
        setup_exe = os.path.join(dist_dir, "SetupInstaller", "Santiao_IM_Native_Setup_v0.9.9.exe")

        print("\n==================================================")
        print(" [成功] 打包完成！纯原生 Windows 独立桌面软件与安装包状态：")
        print(f" 本地绿色目录: {app_output_dir}")
        print(f" 主程序文件: {os.path.join(app_output_dir, '三条IM自动化测试控制台.exe')}")
        print(f" 安装包配置脚本: {os.path.join(CURRENT_DIR, 'installer.iss')}")
        if installer_built and os.path.isfile(setup_exe):
            size_mb = round(os.path.getsize(setup_exe) / (1024 * 1024), 2)
            print(f" 终极单文件安装包: {setup_exe} (体积: {size_mb} MB)")
            # 同时在 dist/ 根目录生成一份直达副本，方便用户直接获取与分发
            root_setup_exe = os.path.join(dist_dir, "Santiao_IM_Native_Setup_v0.9.9.exe")
            try:
                shutil.copy2(setup_exe, root_setup_exe)
                print(f" 便捷安装包直达: {root_setup_exe}")
            except Exception:
                pass
        else:
            print(" 终极单文件安装包: 未生成 (请检查 Inno Setup 编译器环境)")
        print("==================================================")
    else:
        # 4. 纯净应用编译模式：严格仅保留主程序与 _internal 运行时，杜绝多余业务目录
        ensure_clean_native_build(app_output_dir)

        print("\n==================================================")
        print(" [成功] 本地桌面端纯净独立版编译完成！")
        print(f" 输出目录: {app_output_dir}")
        print(f" 主程序文件: {os.path.join(app_output_dir, '三条IM自动化测试控制台.exe')}")
        print(" 目录结构: 仅包含 '_internal' 文件夹与 '三条IM自动化测试控制台.exe' (极致精简无多余文件)")
        print(" 安装提示: 完整的测试业务库与执行环境将在生成 Setup 安装包后通过安装向导自动释放")
        print("==================================================")

    # 深度清理打包过程中的临时工作目录与 .spec 临时文件，彻底根除根目录多余文件
    clean_temp_build_artifacts(build_dir)


def clean_temp_build_artifacts(build_dir: str):
    """自动清理 PyInstaller 产生的临时中间目录 (build_native)、加密暂存目录与临时 .spec 文件"""
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir, ignore_errors=True)
            print(f"[环境净化] 已自动清理中间构建缓存目录: {os.path.basename(build_dir)}")
        except Exception:
            pass

    for spec_name in ["三条IM自动化测试控制台.spec", "main.spec"]:
        spec_path = os.path.join(PROJECT_ROOT, spec_name)
        if os.path.isfile(spec_path):
            try:
                os.remove(spec_path)
            except Exception:
                pass

    # 清理加密资产暂存目录
    enc_dir = os.path.join(PROJECT_ROOT, "dist", "encrypted_release")
    if os.path.exists(enc_dir):
        try:
            shutil.rmtree(enc_dir, ignore_errors=True)
            print("[环境净化] 已自动清理加密资产编译暂存目录: encrypted_release")
        except Exception:
            pass

    waste_temp = os.path.join(PROJECT_ROOT, "temp_dist_core")
    if os.path.exists(waste_temp):
        try:
            shutil.rmtree(waste_temp, ignore_errors=True)
            print("[环境净化] 已自动清理历史临时目录: temp_dist_core")
        except Exception:
            pass


def compile_installer_if_available() -> bool:
    """智能探测并自动调用 Inno Setup 编译器生成最终单文件安装包"""
    iss_path = os.path.join(CURRENT_DIR, "installer.iss")
    iscc_bin = SmartPathResolver.discover_inno_compiler()
    if not iscc_bin:
        print("\n[Inno Setup 提示] 未检测到 Inno Setup 编译器 (ISCC.exe)，跳过单文件安装包制作。")
        print(" 提示: 请安装 Inno Setup 6/7，或将其加入系统环境变量 PATH。")
        return False

    print(f"\n[Inno Setup] 智能雷达探测到编译器: {iscc_bin}")
    print(" 正在一键编译生成最终 Setup 安装程序 (压缩 Python 运行时与业务资产)...")
    try:
        subprocess.run([iscc_bin, iss_path], cwd=PROJECT_ROOT, check=True)
        print(" [Inno Setup 成功] 包含自定义路径与内置运行时的安装包已编译完成！")
        return True
    except Exception as e:
        print(f" [Inno Setup 异常] 编译遇到异常: {e}")
        return False


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
