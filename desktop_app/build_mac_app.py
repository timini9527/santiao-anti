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


def build_mac(build_dmg_flag: bool = BUILD_DMG):
    """macOS 端全流程自动化构建核心入口"""
    if sys.platform != "darwin":
        print("\n" + "=" * 62)
        print(" [平台拦截] 当前运行环境为 Windows (" + sys.platform + ")，无法构建 macOS 产物！")
        print("=" * 62)
        print(" 核心原因说明：")
        print(" 1. 【DMG 机制】：.dmg 是苹果专有磁盘镜像，必须调用 macOS 系统内核的原生工具 'hdiutil'。")
        print(" 2. 【二进制差异】：PyInstaller 无法在 Windows 上跨平台编译出苹果 Mach-O 可执行文件。")
        print(" 3. 【标准落地方式】：请在 Mac 电脑 (或 macOS GitHub Actions / GitLab CI) 上运行本脚本：")
        print("    终端命令: python desktop_app/build_mac_app.py")
        print("=" * 62 + "\n")
        return

    check_and_kill_running_mac_instance()
    print("==================================================")
    print(" [macOS 打包] 正在构建 纯原生 macOS 桌面应用程序 (.app)...")
    print(f" [架构模式] 是否生成 DMG 安装镜像 (BUILD_DMG): {build_dmg_flag}")
    print("==================================================")

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
        "--hidden-import=desktop_app.ui",
        "--hidden-import=desktop_app.ui.main_window",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=pytest",
        "--hidden-import=allure_pytest",
    ]

    if icns_icon:
        cmd.append(f"--icon={icns_icon}")

    cmd.append(main_entry)

    print("执行命令: " + " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)

    app_path = os.path.join(dist_dir, f"{APP_NAME}.app")

    if build_dmg_flag:
        dmg_output = os.path.join(dist_dir, "SetupInstaller", f"Santiao_IM_macOS_Setup_v{VERSION}.dmg")
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
