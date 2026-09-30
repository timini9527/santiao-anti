# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 - Windows 桌面独立端启动器
支持：
1. 优先使用 PyWebView (Edge WebView2 原生窗体引擎)
2. 无需额外依赖的 Windows Edge 原生 App 独立无边框窗口模式
3. 退出窗口时自动清理后台服务与端口，零孤儿进程残留
=======================================================
"""
import os
import sys
import time
import socket
import threading
import subprocess
import urllib.request

# 动态定位项目根目录并注入模块搜索路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

def find_available_port(start_port: int = 8000) -> int:
    """自动探测可用端口，若 8000 被占用则顺延递增"""
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1
    return start_port

def wait_server_ready(url: str, timeout: float = 6.0) -> bool:
    """等待后台后端服务就绪"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DesktopLauncher'})
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False

def start_backend_server(port: int):
    """在后台独立线程启动 Uvicorn ASGI 服务"""
    try:
        import uvicorn
        from web_platform.backend.main import app
        config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="warning")
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        print(f"[Desktop Launcher] 后端启动异常: {e}", file=sys.stderr)

def launch_desktop_window(target_url: str):
    """
    调起独立的 Windows 桌面原生软件窗口：
    优先调用 pywebview；若未安装，则无缝切换到 Windows 系统自带的 Edge 独立应用窗口（零安装）。
    """
    # 方案 1: 尝试使用 pywebview
    try:
        import webview
        print("[Desktop Launcher] 正在以 WebView2 原生窗体启动控制台...")
        window = webview.create_window(
            title="三条 IM 自动化测试控制台",
            url=target_url,
            width=1440,
            height=900,
            min_size=(1024, 700),
            confirm_close=False
        )
        webview.start()
        return
    except ImportError:
        pass

    # 方案 2: Windows Edge 原生独立 App 窗口模式 (无地址栏、无标签栏、独立任务栏应用)
    print("[Desktop Launcher] 正在以 Windows 原生桌面 App 模式启动控制台...")
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        "msedge.exe"
    ]
    
    edge_executable = None
    for p in edge_paths:
        if os.path.exists(p) or p == "msedge.exe":
            edge_executable = p
            break

    if edge_executable:
        edge_cmd = [
            edge_executable,
            f"--app={target_url}",
            "--window-size=1440,900",
            "--start-maximized"
        ]
        proc = subprocess.Popen(edge_cmd)
        proc.wait() # 阻塞直至桌面软件窗口被用户关闭
    else:
        # 极度兜底：调用默认浏览器打开
        import webbrowser
        webbrowser.open(target_url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

def main():
    port = find_available_port(8000)
    target_url = f"http://127.0.0.1:{port}"
    print(f"==================================================")
    print(f"  🚀 正在启动 三条 IM 自动化测试控制台 桌面端...")
    print(f"  服务地址: {target_url}")
    print(f"==================================================")

    # 1. 后台线程启动 FastAPI 引擎
    server_thread = threading.Thread(target=start_backend_server, args=(port,), daemon=True)
    server_thread.start()

    # 2. 等待服务就绪
    wait_server_ready(f"{target_url}/api/overview")

    # 3. 调起独立桌面客户端界面并阻塞等待退出
    try:
        launch_desktop_window(target_url)
    finally:
        print("\n[Desktop Launcher] 桌面客户端已关闭，正在安全退出后台服务...")
        # 释放资源退出
        os._exit(0)

if __name__ == '__main__':
    main()
