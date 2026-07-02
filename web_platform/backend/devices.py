import os
import subprocess
import urllib.request
import json
import logging
import socket

logger = logging.getLogger("web_console")

def get_local_ip_192() -> str:
    """
    执行 ipconfig 命令，解析并获取本机以 192.168. 开头的局域网 IP 地址。
    """
    try:
        # 执行 Windows 系统的 ipconfig 命令行，使用 GBK 编码进行解析
        out = subprocess.check_output("ipconfig", shell=True, timeout=5).decode("gbk", errors="ignore")
        for line in out.split("\n"):
            line = line.strip()
            # 搜索 IPv4 地址配置行
            if "IPv4" in line or "IP Address" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    ip = parts[1].strip()
                    if ip.startswith("192.168."):
                        return ip
    except Exception as e:
        logger.warning(f"通过 ipconfig 命令获取局域网 IP 异常: {e}")
        
    # 备用方案：通过 socket 获取本机 IP 列表进行过滤
    try:
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        for ip in ip_list:
            if ip.startswith("192.168."):
                return ip
    except Exception:
        pass
    
    return "127.0.0.1"

def detect_appium_status(port: int = 4723) -> str:
    """
    探测本地 Appium 服务是否可用。
    返回: 可用的 Appium 局域网映射地址，如 '192.168.1.100:4723'，探测失败则返回空字符串。
    """
    try:
        # 本地探测依然通过 127.0.0.1 接口进行以确保最快速的响应
        req = urllib.request.Request(f"http://127.0.0.1:{port}/status")
        with urllib.request.urlopen(req, timeout=1) as response:
            if response.status == 200:
                # 探测成功，获取本机以 192.168 开头的 IP 地址，供局域网内其他电脑访问
                local_ip = get_local_ip_192()
                return f"{local_ip}:{port}"
    except Exception:
        pass
    return ""

def detect_connected_devices() -> list[str]:
    """
    动态探测当前系统连接的移动设备。
    依次检测 Android (ADB) 和 鸿蒙 HarmonyOS NEXT (HDC)。
    返回: UDID 字符串列表。
    """
    devices = []
    
    # 1. 尝试使用 adb 探测安卓设备
    try:
        # 重启/启动 adb server 确保服务运行并拉起，无需 kill-server 以免导致模拟器强制掉线
        subprocess.run(["adb", "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        out = subprocess.check_output(["adb", "devices"], timeout=10).decode('utf-8')
        lines = out.strip().split('\n')
        for line in lines[1:]:
            if '\tdevice' in line:
                udid = line.split('\t')[0].strip()
                if udid:
                    devices.append(f"{udid} (Android)")
    except Exception as e:
        logger.warning(f"ADB 设备探测异常: {e}")

    # 2. 尝试使用 hdc 探测鸿蒙设备
    try:
        out = subprocess.check_output(["hdc", "list", "targets"], timeout=10).decode('utf-8')
        lines = out.strip().split('\n')
        for line in lines:
            # 过滤无效信息
            line_str = line.strip()
            if line_str and "Empty" not in line_str and "Error" not in line_str and "not found" not in line_str:
                devices.append(f"{line_str} (HarmonyOS)")
    except Exception as e:
        logger.warning(f"HDC 设备探测异常: {e}")

    return devices

def start_appium_server(os_type: str = "windows", port: int = 4723) -> bool:
    """
    在后台拉起 Appium 服务，自动开启 0.0.0.0 以供局域网其他电脑访问。
    参数: os_type - 系统类型: windows, mac, linux
          port - 服务监听端口
    返回: 是否成功发出启动命令。
    """
    try:
        if os_type == "windows":
            # 根据端口不同，定制执行对应的 Appium 命令
            if port == 4723:
                # 第一个 Appium 启动命令：执行 appium，并绑定 0.0.0.0 以支持局域网设备接入
                subprocess.Popen(["cmd.exe", "/c", "start", "appium", "-a", "0.0.0.0"])
            else:
                # 第二个 Appium 启动命令：执行 appium -p 4724，并绑定 0.0.0.0 以支持局域网设备接入
                subprocess.Popen(["cmd.exe", "/c", "start", "appium", "-p", str(port), "-a", "0.0.0.0"])
        elif os_type == "mac":
            if port == 4723:
                subprocess.Popen(["osascript", "-e", 'tell application "Terminal" to do script "appium -a 0.0.0.0"'])
            else:
                subprocess.Popen(["osascript", "-e", f'tell application "Terminal" to do script "appium -p {port} -a 0.0.0.0"'])
        else:
            if port == 4723:
                subprocess.Popen(["appium", "-a", "0.0.0.0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            else:
                subprocess.Popen(["appium", "-p", str(port), "-a", "0.0.0.0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception as e:
        logger.error(f"启动 Appium 服务失败: {e}")
        return False
