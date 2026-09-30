# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 - Windows EXE 自动化打包脚本
=======================================================
用途：
1. 自动收集前端编译产物 (web_platform/backend/static) 及后端依赖
2. 通过 PyInstaller 打包生成独立桌面 EXE 程序
3. 自动生成配套的 Inno Setup 安装包制作脚本 (installer.iss)
"""
import os
import sys
import shutil
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

def check_static_files():
    """检查前端静态资源是否就绪"""
    static_dir = os.path.join(CURRENT_DIR, "backend", "static")
    index_html = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_html):
        print(f"⚠️ 未检测到前端静态资源: {index_html}")
        frontend_dir = os.path.join(CURRENT_DIR, "frontend")
        if os.path.exists(frontend_dir):
            print("正在自动编译前端 Vue 项目 (npm run build)...")
            subprocess.run("npm run build", cwd=frontend_dir, shell=True, check=True)
    print("✅ 前端静态资源已就绪！")

def generate_inno_setup_script(output_dir: str):
    """生成 Inno Setup 安装包编译器脚本"""
    iss_content = f"""[Setup]
AppName=三条IM自动化测试控制台
AppVersion=1.0.0
DefaultDirName={{autopf}}\\SantiaoAntiPlatform
DefaultGroupName=三条IM自动化测试控制台
OutputDir={output_dir}\\SetupInstaller
OutputBaseFilename=Santiao_IM_Console_Setup_v1.0.0
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
    print(f"✅ Inno Setup 安装包脚本已生成: {iss_path}")

def build():
    check_static_files()
    
    print("\n==================================================")
    print(" 🛠️ 开始执行 PyInstaller 自动化打包...")
    print("==================================================")

    launcher_path = os.path.join(CURRENT_DIR, "desktop_launcher.py")
    static_src = os.path.join(CURRENT_DIR, "backend", "static")
    
    # 静态资源打包参数
    add_data_param = f"{static_src};web_platform/backend/static"
    
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    build_dir = os.path.join(PROJECT_ROOT, "build")
    
    # PyInstaller 打包命令（使用 onedir 绿色目录，秒级冷启动，稳定性极佳）
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=三条IM自动化测试控制台",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed", # 隐藏黑框，以标准 Windows 窗口程序运行
        f"--add-data={add_data_param}",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=fastapi",
        "--hidden-import=pydantic",
        launcher_path
    ]
    
    print("正在执行命令: " + " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    
    # 生成安装包脚本
    generate_inno_setup_script(dist_dir)
    
    print("\n==================================================")
    print(" 🎉 打包完成！产物路径如下：")
    print(f" 📂 绿色免安装运行目录: {os.path.join(dist_dir, '三条IM自动化测试控制台')}")
    print(f" 🚀 可执行程序: {os.path.join(dist_dir, '三条IM自动化测试控制台', '三条IM自动化测试控制台.exe')}")
    print(f" 📦 安装包配置脚本: {os.path.join(CURRENT_DIR, 'installer.iss')}")
    print("==================================================")

if __name__ == '__main__':
    build()
