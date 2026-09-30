import os
import subprocess
import urllib.request
import json
import logging
import socket

logger = logging.getLogger("web_console")

def get_local_ip() -> str:
    """
    全自动动态获取当前电脑在当前局域网下的真实有效 IP（自适应 192.168.*、10.*、172.* 等任意局域网段）。
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    # 备用方案：通过 socket 获取本机 IP 列表进行过滤
    try:
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        for ip in ip_list:
            if not ip.startswith("127.") and not ip.startswith("169.254.") and not ip.endswith(".1"):
                return ip
    except Exception:
        pass
    
    return "127.0.0.1"

# 兼容别名
get_local_ip_192 = get_local_ip

def detect_appium_status(port: int = 4723) -> str:
    """
    探测本地 Appium 服务是否可用。
    返回: 可用的 Appium 局域网映射地址，如 '{local_ip}:{port}'，探测失败则返回空字符串。
    """
    try:
        # 本地探测依然通过 127.0.0.1 接口进行以确保最快速的响应
        req = urllib.request.Request(f"http://127.0.0.1:{port}/status")
        with urllib.request.urlopen(req, timeout=1) as response:
            if response.status == 200:
                local_ip = get_local_ip()
                return f"{local_ip}:{port}"
    except Exception:
        pass
    return ""

def get_configured_devices() -> tuple[str, str]:
    """
    控制台页面默认绑定的双机设备（无需修改 config/devices.yaml 文件）：
    发送端(第一部手机): QFF0219A11009305
    接收端(第二部手机): 20a5fa17
    """
    return "QFF0219A11009305", "20a5fa17"

def detect_raw_connected_devices() -> list[tuple[str, str, bool]]:
    """
    动态探测当前系统连接的移动设备。
    依次检测 Android (ADB) 和 鸿蒙 HarmonyOS NEXT (HDC)。
    返回: [(udid, platform, is_real)] 列表，其中 is_real 为 True 表示 USB 硬件真机。
    """
    raw_devices = []
    no_window = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    
    # 1. 尝试使用 adb 探测安卓设备
    try:
        subprocess.run(["adb", "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, creationflags=no_window)
        out = subprocess.check_output(["adb", "devices"], timeout=10, creationflags=no_window).decode('utf-8')
        lines = out.strip().split('\n')
        for line in lines[1:]:
            if '\tdevice' in line:
                udid = line.split('\t')[0].strip()
                if udid:
                    # 判断是否为物理真机（模拟器通常以 emulator-、127.0.0.1: 或 localhost: 开头）
                    is_real = not (udid.startswith("emulator-") or "127.0.0.1" in udid or "localhost" in udid)
                    raw_devices.append((udid, "Android", is_real))
    except Exception as e:
        logger.warning(f"ADB 设备探测异常: {e}")

    # 2. 尝试使用 hdc 探测鸿蒙设备
    try:
        out = subprocess.check_output(["hdc", "list", "targets"], timeout=10, creationflags=no_window).decode('utf-8')
        lines = out.strip().split('\n')
        for line in lines:
            line_str = line.strip()
            if line_str and "Empty" not in line_str and "Error" not in line_str and "not found" not in line_str:
                raw_devices.append((line_str, "HarmonyOS", True))
    except Exception as e:
        logger.warning(f"HDC 设备探测异常: {e}")

    return raw_devices

def detect_device_details() -> dict:
    """
    获取详细的设备列表及真实 USB 物理硬件分类信息。
    """
    raw_devices = detect_raw_connected_devices()
    default_sender, default_receiver = get_configured_devices()
    
    real_devices = []
    emulator_devices = []
    all_devices = []
    device_items = []
    legacy_devices = []

    for udid, platform, is_real in raw_devices:
        all_devices.append(udid)
        if is_real:
            real_devices.append(udid)
            desc = f"USB真机 ({platform})"
        else:
            emulator_devices.append(udid)
            desc = f"模拟器 ({platform})"
            
        device_items.append({
            "udid": udid,
            "desc": desc,
            "is_real": is_real,
            "platform": platform
        })
        legacy_devices.append(f"{udid} ({'USB真机' if is_real else '模拟器'})")

    return {
        "real_devices": real_devices,
        "emulator_devices": emulator_devices,
        "all_devices": all_devices,
        "device_items": device_items,
        "legacy_devices": legacy_devices,
        "sender_default": default_sender,
        "receiver_default": default_receiver
    }

def detect_connected_devices() -> list[str]:
    """
    保持向下兼容的探测函数，返回格式化后的设备描述列表。
    优先排列物理真机。
    """
    details = detect_device_details()
    return details["legacy_devices"]

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
