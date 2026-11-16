# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 - macOS 原生应用与 DMG 打包脚本
=======================================================
用途：
1. 在 macOS (Apple Silicon M系列 / Intel x86_64) 环境下，将 desktop_app/main.py 编译为原生 .app Bundle
2. 集成方案 4 核心资产代码加密 (通过 Clang/Cython 将核心业务代码编译为原生 .so 机器码，抹除 .py 源码)
3. 自动生成标准 macOS 拖拽式 .dmg 安装镜像 (开箱即用，支持将 .app 拖拽入 /Applications)
4. 注入苹果视网膜高清图标 (app_icon.icns) 与自动化测试沙盒权限声明 (Info.plist)
=======================================================
"""

import os
import sys
import shutil
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# ==============================================================================
# 核心打包配置开关
# ==============================================================================
# 控制是否生成最终的 macOS .dmg 单文件拖拽安装包
# - True  : 完整流程 (PyInstaller 打包 .app -> 核心加密编译 -> hdiutil 封装为 .dmg 安装镜像)
# - False : 仅生成本地运行的 .app 应用程序包 (dist/三条IM自动化测试控制台.app)，极速构建与本地调试
BUILD_DMG = True

APP_NAME = "三条IM自动化测试控制台"
BUNDLE_ID = "com.santiao.qa.desktop"
VERSION = "0.9.9"


def check_and_kill_running_mac_instance():
    """打包前关闭可能正在运行的 Mac 实例，防止文件冲突"""
    if sys.platform == "darwin":
        try:
            subprocess.run(["pkill", "-f", APP_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def generate_icns_if_needed():
    """检查并自动生成 macOS 专用高清 .icns 视网膜图标"""
    icns_path = os.path.join(CURRENT_DIR, "resources", "app_icon.icns")
    png_path = os.path.join(CURRENT_DIR, "resources", "sant_logo_hd.png")
    if not os.path.exists(icns_path) and os.path.exists(png_path):
        try:
            from PIL import Image
            img = Image.open(png_path).convert("RGBA")
            large = img.resize((512, 512), Image.Resampling.LANCZOS)
            large.save(icns_path, format="ICNS")
            print(f"[资源准备] 已自动生成 macOS 高清图标: {icns_path}")
        except Exception as e:
            print(f"[资源警告] 生成 .icns 图标提示: {e}")
    return icns_path if os.path.exists(icns_path) else None


def build_dmg(app_bundle_path: str, output_dmg_path: str):
    """
    使用 macOS 原生内置命令行工具 hdiutil 自动封装为用户友好的 .dmg 磁盘安装镜像
    无需安装任何第三方商业工具，系统级原生稳定支持
    """
    if sys.platform != "darwin":
        print("[DMG 跳过] 当前非 macOS 环境，无法调用原生 hdiutil 工具封装 .dmg")
        return

    print("\n==================================================")
    print(" [DMG 封装] 正在调用 macOS 原生 hdiutil 生成标准安装镜像...")
    print("==================================================")

    dmg_temp_dir = os.path.join(PROJECT_ROOT, "build", "dmg_temp")
    if os.path.exists(dmg_temp_dir):
        shutil.rmtree(dmg_temp_dir, ignore_errors=True)
    os.makedirs(dmg_temp_dir, exist_ok=True)

    # 1. 将 .app 复制到 DMG 临时目录
    dest_app = os.path.join(dmg_temp_dir, f"{APP_NAME}.app")
    shutil.copytree(app_bundle_path, dest_app, symlinks=True)

    # 2. 创建到系统 /Applications 目录的替身快捷链接 (实现经典的拖拽安装体验)
    applications_link = os.path.join(dmg_temp_dir, "Applications")
    try:
        os.symlink("/Applications", applications_link)
    except Exception:
        pass

    # 3. 若目标 dmg 已存在先清理
    if os.path.exists(output_dmg_path):
        os.remove(output_dmg_path)
    os.makedirs(os.path.dirname(output_dmg_path), exist_ok=True)

    # 4. 调用 hdiutil 执行高压缩比镜像创建
    cmd = [
        "hdiutil", "create",
        "-volname", APP_NAME,
        "-srcfolder", dmg_temp_dir,
        "-ov",
        "-format", "UDZO", # zlib 压缩格式
        output_dmg_path
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f" [DMG 成功] macOS 标准拖拽式安装镜像已生成: {output_dmg_path}")
    except Exception as e:
        print(f" [DMG 异常] 封装 DMG 镜像失败: {e}")
    finally:
        shutil.rmtree(dmg_temp_dir, ignore_errors=True)


def _resolve_github_actions_url() -> str:
    """从本地 Git 远程仓库配置动态解析 GitHub Actions 构建页面链接"""
    default_url = "https://github.com/timini9527/santiao-anti/actions/workflows/build_mac_dmg.yml"
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5
        )
        remote_url = (res.stdout or "").strip()
        if remote_url:
            if remote_url.startswith("git@github.com:"):
                repo_path = remote_url.replace("git@github.com:", "").removesuffix(".git")
                return f"https://github.com/{repo_path}/actions/workflows/build_mac_dmg.yml"
            if "github.com/" in remote_url:
                repo_path = remote_url.split("github.com/", 1)[1].removesuffix(".git")
                return f"https://github.com/{repo_path}/actions/workflows/build_mac_dmg.yml"
    except Exception:
        pass
    return default_url


def trigger_github_cloud_build():
    """
    在非 macOS 环境下运行本脚本时，全自动执行：
    1. 自动暂存与提交当前本地所有源码变更 (排除临时数据库等垃圾文件)；
    2. 仅推送至构建分支 (origin/build-mac)；
    3. 触发 GitHub Actions 云端 macOS 虚拟机编译 .app 与封装 .dmg；
    4. 若无代码改动且装有 gh CLI，则通过 workflow_dispatch 强制触发云端重打。
    """
    from datetime import datetime

    print("\n" + "=" * 66)
    print(f" [双模分发] 当前系统为 {sys.platform}，启动【一键自动 Push + GitHub 云端打包】")
    print("=" * 66)

    actions_url = _resolve_github_actions_url()

    # 1. 自动暂存并提交本地所有有效改动 (排除 androguard.db 等临时文件)
    print(" ▶ [1/3] 正在检查并自动提交本地代码修改...")
    try:
        # 仅暂存已追踪文件的修改以及项目核心目录的新文件，跳过临时数据库
        subprocess.run(["git", "add", "-u"], cwd=PROJECT_ROOT, capture_output=True, timeout=10)
        for track_dir in ["desktop_app", "web_platform", "config", "tests", "pages", "locators", "core", "utils", "scripts", ".github"]:
            dir_path = os.path.join(PROJECT_ROOT, track_dir)
            if os.path.exists(dir_path):
                subprocess.run(["git", "add", track_dir], cwd=PROJECT_ROOT, capture_output=True, timeout=10)

        diff_res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5
        )
        staged_files = [f.strip() for f in (diff_res.stdout or "").splitlines() if f.strip()]
        if staged_files:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"chore: 自动提交并触发 macOS 云端构建打包 ({ts})"
            commit_res = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15
            )
            if commit_res.returncode == 0:
                print(f" ✅ 已自动提交 {len(staged_files)} 个变更文件 -> {commit_msg}")
            else:
                print(f" ⚠️ 自动提交提示: {((commit_res.stderr or '') or (commit_res.stdout or '')).strip()}")
        else:
            print(" ℹ️ 本地工作区干净，无新增未提交修改。")
    except Exception as e:
        print(f" ⚠️ 检查/提交本地修改异常: {e}")

    # 2. 仅自动推送至 build-mac 分支触发云端构建
    print(" ▶ [2/3] 正在自动推送代码至 GitHub (origin/build-mac)...")
    push_triggered = False
    try:
        # 仅推送至 build-mac 分支触发工作流
        push_res = subprocess.run(
            ["git", "push", "origin", "HEAD:build-mac"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        push_output = f"{push_res.stdout or ''}\n{push_res.stderr or ''}".strip()
        if push_res.returncode == 0:
            if "Everything up-to-date" in push_output:
                print(" ℹ️ 远程 build-mac 分支已是最新提交状态。")
            else:
                print(" ✅ 已成功推送最新代码至 origin/build-mac，GitHub 云端打包已自动触发！")
                push_triggered = True
        else:
            print(f" ⚠️ 推送至 origin/build-mac 失败: {push_output}")
    except Exception as e:
        print(f" ⚠️ Git 推送异常: {e}")

    # 3. 若未产生新提交且装有 gh CLI，自动调用 workflow_dispatch 强制触发云端打包
    gh_bin = shutil.which("gh")
    if not push_triggered and gh_bin:
        print(" ▶ [3/3] 检测到 GitHub CLI (gh)，正在远程派发强制云端打包任务...")
        try:
            gh_res = subprocess.run(
                [gh_bin, "workflow", "run", "build_mac_dmg.yml", "--ref", "build-mac"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15
            )
            if gh_res.returncode == 0:
                print(" ✅ 已成功通过 GitHub CLI 触发云端 macOS 打包任务！")
                push_triggered = True
            else:
                print(f" ⚠️ GitHub CLI 触发未成功: {((gh_res.stderr or '') or (gh_res.stdout or '')).strip()}")
        except Exception as e:
            print(f" ⚠️ GitHub CLI 调用异常: {e}")
    else:
        print(" ▶ [3/3] 打包派发校验完成。")

    print("\n" + "=" * 66)
    if push_triggered:
        print(" 🚀 [成功] 已自动 Push 并触发 GitHub 云端 macOS 打包！")
    else:
        print(" ℹ️ [提示] 代码已是最新；如需强制重打，请打开下方链接点击 [Run workflow]：")
    print(f" 🔗 查看构建进度与下载 DMG 安装包：\n    {actions_url}")
    print("=" * 66 + "\n")


def build_mac(build_dmg_flag: bool = BUILD_DMG):
    """macOS 端全流程自动化构建核心入口"""
    if sys.platform != "darwin":
        trigger_github_cloud_build()
        return

    check_and_kill_running_mac_instance()
    print("==================================================")
    print(" [macOS 打包] 正在构建 纯原生 macOS 桌面应用程序 (.app)...")
    print(f" [架构模式] 是否生成 DMG 安装镜像 (BUILD_DMG): {build_dmg_flag}")
    print("==================================================")

    # 0. 自动预提取最新全量用例元数据并同步刷新 tests_catalog.json 静态索引
    try:
        import json
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        from web_platform.backend.collector import collect_all_tests
        src_tests = os.path.join(PROJECT_ROOT, "tests")
        if os.path.exists(src_tests):
            catalog = collect_all_tests(src_tests)
            catalog_file = os.path.join(src_tests, "tests_catalog.json")
            with open(catalog_file, "w", encoding="utf-8") as f:
                json.dump(catalog, f, ensure_ascii=False, indent=2)
            print(f" [用例索引] 已同步刷新测试用例索引: {catalog_file} (收录 {len(catalog)} 个测试文件)")
    except Exception as e:
        print(f" [用例警告] 自动刷新 tests_catalog.json 提示: {e}")

    main_entry = os.path.join(CURRENT_DIR, "main.py")
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    build_dir = os.path.join(PROJECT_ROOT, "build_mac")

    icns_icon = generate_icns_if_needed()

    # 构造 macOS 专用的 PyInstaller 编译参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        f"--name={APP_NAME}",
        "--noconfirm",
        "--onedir",
        "--windowed", # 生成苹果原生 GUI Bundle (.app)
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--paths={PROJECT_ROOT}",
        f"--osx-bundle-identifier={BUNDLE_ID}",
        f"--add-data={os.path.join(CURRENT_DIR, 'resources')}:desktop_app/resources",
        "--hidden-import=desktop_app",
        "--hidden-import=desktop_app.style",
        "--hidden-import=desktop_app.config",
        "--hidden-import=desktop_app.core",
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
        "--hidden-import=desktop_app.core.file_watcher",
        "--hidden-import=desktop_app.core.report_scanner",
        "--hidden-import=web_platform",
        "--hidden-import=web_platform.backend",
        "--hidden-import=web_platform.backend.devices",
        "--hidden-import=web_platform.backend.collector",
        "--hidden-import=web_platform.backend.paths",
        "--hidden-import=web_platform.backend.runner",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=pytest",
        "--hidden-import=pytest_check",
        "--hidden-import=allure_pytest",
        "--hidden-import=appium",
        "--hidden-import=selenium",
        "--hidden-import=hmnextauto",
        "--hidden-import=lxml",
        "--hidden-import=websockets",
        "--hidden-import=pandas",
        "--hidden-import=pypinyin",
        "--hidden-import=dateutil",
        "--hidden-import=psutil",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=yaml",
        "--hidden-import=colorlog",
        "--hidden-import=imagehash",
        "--hidden-import=PIL",
        "--hidden-import=tidevice",
        "--hidden-import=uiautomator2",
        "--hidden-import=grpc",
        "--collect-all=tidevice",
        "--collect-all=uiautomator2",
        "--collect-all=hmnextauto",
        "--copy-metadata=tidevice",
    ]

    # 动态检测当前打包环境中已安装的扩展库并注入 PyInstaller
    import importlib.util
    import platform
    target_arch = platform.machine().lower()
    if target_arch in ("x86_64", "arm64"):
        cmd.append(f"--target-arch={target_arch}")

    if importlib.util.find_spec("av") is not None:
        cmd.extend(["--hidden-import=av", "--collect-all=av", "--copy-metadata=av"])

    if importlib.util.find_spec("pymobiledevice3") is not None:
        cmd.extend([
            "--hidden-import=pymobiledevice3",
            "--hidden-import=pymobiledevice3.remote.userspace_tunnel",
            "--hidden-import=pymobiledevice3.remote.core_device.display_service",
            "--hidden-import=pymobiledevice3.remote.core_device.screen_stream",
            "--hidden-import=pymobiledevice3.services.power_assertion",
            "--hidden-import=pymobiledevice3.tunneld.api",
            "--hidden-import=pymobiledevice3.services.dvt.instruments.dvt_provider",
            "--hidden-import=pymobiledevice3.services.dvt.instruments.screenshot",
            "--collect-all=pymobiledevice3",
            "--copy-metadata=pymobiledevice3",
        ])

    # 附加 desktop_app/assets
    assets_dir = os.path.join(CURRENT_DIR, "assets")
    if os.path.isdir(assets_dir):
        cmd.append(f"--add-data={assets_dir}:desktop_app/assets")

    # 注入全量测试用例与业务资产 (tests, pages, locators, config, data, core, conftest.py 等)
    try:
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        from desktop_app.core.path_resolver import SmartPathResolver
        project_assets = SmartPathResolver.discover_project_assets(PROJECT_ROOT)
        for d_name in project_assets.get("business_dirs", []):
            if d_name == "bin":
                # 跳过 Windows 专属的 .exe/.dll 工具目录，减小 macOS 包体积
                continue
            src_d = os.path.join(PROJECT_ROOT, d_name)
            if os.path.isdir(src_d):
                cmd.append(f"--add-data={src_d}:{d_name}")
        for f_name in project_assets.get("core_files", []):
            src_f = os.path.join(PROJECT_ROOT, f_name)
            if os.path.isfile(src_f):
                cmd.append(f"--add-data={src_f}:.")
        print(f" [资产打包] 已注入业务目录: {project_assets.get('business_dirs', [])}")
    except Exception as e:
        print(f" [资产警告] 注入测试业务目录异常: {e}")

    if icns_icon:
        cmd.append(f"--icon={icns_icon}")

    cmd.append(main_entry)

    print("执行命令: " + " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)

    app_path = os.path.join(dist_dir, f"{APP_NAME}.app")

    if build_dmg_flag:
        import platform
        cpu_arch = platform.machine().lower()
        dmg_output = os.path.join(dist_dir, "SetupInstaller", f"Santiao_IM_macOS_{cpu_arch}_Setup_v{VERSION}.dmg")
        build_dmg(app_path, dmg_output)
        if os.path.exists(dmg_output):
            print("\n==================================================")
            print(" [成功] macOS 原生独立桌面应用与 DMG 安装镜像已全部就绪：")
            print(f" 应用程序包: {app_path}")
            print(f" 终极 DMG 安装包: {dmg_output}")
            print(" 部署方式: 双击 DMG，将应用拖拽入 Applications 即可开箱即用！")
            print("==================================================")
        else:
            print(f"\n[构建异常] DMG 封装未成功生成: {dmg_output}")
    else:
        print("\n==================================================")
        print(" [成功] macOS 原生桌面应用程序包 (.app) 构建完成！(已跳过 DMG 制作)")
        print(f" 本地运行应用包: {app_path}")
        print(" 运行方式: open \"" + app_path + "\"")
        print("==================================================")


if __name__ == '__main__':
    target_flag = BUILD_DMG
    if "--no-dmg" in sys.argv:
        target_flag = False
    elif "--dmg" in sys.argv:
        target_flag = True
    build_mac(build_dmg_flag=target_flag)
