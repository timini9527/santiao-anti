# -*- coding: utf-8 -*-
"""
=======================================================
三条自动化测试控制台 - 一键智能启动器
作者: 哇哇叫
=======================================================
"""
import os
import sys
import socket
import subprocess

def safe_print(msg: str):
    """防御性打印：防止 Windows 下的 GBK 终端因 Unicode 绘文字崩溃"""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            # 尝试过滤无法在当前编码下表示的字符
            encoding = sys.stdout.encoding or 'gbk'
            clean_msg = msg.encode(encoding, errors='ignore').decode(encoding)
            print(clean_msg)
        except Exception:
            # 极度兜底：过滤任何可能引发问题的字符只打印纯 ASCII/中文
            print(msg.encode('ascii', errors='ignore').decode('ascii'))

def get_host_ip() -> str:
    """获取本机局域网内网真实有效 IP（自适应 192.168.*、10.*、172.* 等任意网段），用于非开发人员通过其他电脑访问"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        _, _, ips = socket.gethostbyname_ex(hostname)
        for ip in ips:
            if not ip.startswith("127.") and not ip.startswith("169.254.") and not ip.endswith(".1"):
                return ip
    except Exception:
        pass

    return '127.0.0.1'

def check_and_install_dependencies():
    """检查并自动安装重构后控制台所需的第三方库"""
    required_packages = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "sse_starlette": "sse-starlette"
    }
    
    missing_packages = []
    for module_name, pip_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(pip_name)
            
    if missing_packages:
        safe_print("=" * 60)
        safe_print(" [Web Console] 检测到重构版控制台缺少必要的依赖包：")
        for pkg in missing_packages:
            safe_print(f"  - {pkg}")
        safe_print(" 正在为您自动安装，请稍候...")
        safe_print("=" * 60)
        
        try:
            # 调用 pip 自动静默安装
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
            safe_print("\n [Web Console] 依赖安装完成！")
        except Exception as e:
            safe_print(f"\n [Web Console] ❌ 自动安装依赖失败: {e}")
            safe_print(" 请尝试手动执行以下命令进行安装：")
            safe_print(f"  {sys.executable} -m pip install {' '.join(missing_packages)}")
            sys.exit(1)

def main():
    # 1. 确保当前工作目录位于项目根目录，以便于正常扫描 tests/ 目录
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_file_dir)
    os.chdir(project_root)
    sys.path.insert(0, project_root)
    
    # 2. 检查并补齐依赖库
    check_and_install_dependencies()
    
    # 3. 动态加载并使用 uvicorn 调起服务
    try:
        import uvicorn
    except ImportError:
        safe_print(" [Web Console] ❌ 未能成功导入 uvicorn，请确保已正确安装依赖。")
        sys.exit(1)
        
    port = 8000
    host_ip = get_host_ip()
    
    safe_print("=" * 60)
    safe_print("        🚀 IM 三端自动化测试重构控制台服务已就绪")
    safe_print("=" * 60)
    safe_print(f" 本地访问地址:   http://localhost:{port}")
    safe_print(f" 局域网访问地址: http://{host_ip}:{port}")
    safe_print(" (非开发人员通过手机或局域网内的其它电脑即可直接访问)")
    safe_print("=" * 60)
    
    # 启动 ASGI 服务
    try:
        uvicorn.run("web_platform.backend.main:app", host="0.0.0.0", port=port, reload=True)
    except KeyboardInterrupt:
        safe_print("\n [Web Console] 🛑 接收到终端 Ctrl+C 中断信号，正在清理并强行退出...")
        # 强行释放 8000 端口，解决 Windows 平台下 Uvicorn reload=True 产生的孤儿进程无法终止的问题
        try:
            import subprocess
            kill_cmd = f'for /f "tokens=5" %%a in (\'netstat -ano ^| findstr :{port} ^| findstr LISTENING\') do taskkill /F /PID %%a'
            subprocess.run(kill_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        
        os._exit(0)

if __name__ == '__main__':
    main()
