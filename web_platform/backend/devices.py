import os
import subprocess
import urllib.request
import json
import logging

logger = logging.getLogger("web_console")

def detect_appium_status() -> str:
    """
    探测本地 Appium 服务是否可用。
    返回: 可用的 Appium 地址，如 '127.0.0.1:4723'，探测失败则返回空字符串。
    """
    try:
        # Appium 2.x 的状态检测接口
        req = urllib.request.Request("http://127.0.0.1:4723/status")
        with urllib.request.urlopen(req, timeout=1) as response:
            if response.status == 200:
                return "127.0.0.1:4723"
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
        # 重启 adb server 确保设备状态刷新
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

def start_appium_server(os_type: str = "windows") -> bool:
    """
    根据运行系统的平台类型，在后台拉起 Appium 监听服务。
    参数: os_type - 系统类型: windows, mac, linux
    返回: 是否成功发出启动命令。
    """
    try:
        if os_type == "windows":
            # Windows: 弹窗形式拉起后台运行 cmd，不阻塞主服务
            subprocess.Popen(["cmd.exe", "/c", "start", "appium", "-a", "0.0.0.0"])
        elif os_type == "mac":
            # Mac: 唤起 Terminal 应用并执行 appium
            subprocess.Popen(["osascript", "-e", 'tell application "Terminal" to do script "appium -a 0.0.0.0"'])
        else:
            # Linux: 后台静默执行，脱离主进程生命周期
            subprocess.Popen(["appium", "-a", "0.0.0.0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception as e:
        logger.error(f"启动 Appium 服务失败: {e}")
        return False
