import copy
from appium import webdriver
from appium.options.android import UiAutomator2Options
import os
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data


class DriverFactory:
    @staticmethod
    def get_driver(device_key: str):
        """
        工厂方法：根据 device_key ('sender' 或 'receiver') 创建驱动
        """
        # 1. 加载所有配置
        data = load_yaml_data("devices.yaml")

        # 2. 获取当前运行环境 (优先读取系统环境变量，其次读取 devices.yaml 顶层配置，默认 'dev')
        current_env = os.environ.get('ENV') or data.get('current_env', 'dev')
        logger.info(f"[DriverFactory] 当前指定的执行环境为: {current_env}")

        # 3. 获取公共 App 配置
        common_caps = data.get('app', {})

        # 4. 获取指定环境的设备配置
        env_config = data.get('devices', {}).get(current_env)
        if not env_config:
            raise ValueError(f"在 devices.yaml 的 devices 下找不到环境配置: {current_env}")

        device_config = env_config.get(device_key)
        if not device_config:
            raise ValueError(f"在 devices.yaml 的 '{current_env}' 环境下找不到设备配置: {device_key}")

        # 5. 合并 Capability (深拷贝防止污染)
        # 优先级：设备配置 > 公共配置
        desired_caps = copy.deepcopy(common_caps)
        desired_caps.update(device_config)
        
        # == 支持环境变量动态覆盖 (供 Web Runner 远程调用使用) ==
        env_udid = os.environ.get("REMOTE_UDID")
        env_appium = os.environ.get("REMOTE_APPIUM_URL")
        logger.info(f"[DriverFactory] 环境变量动态覆盖: {env_udid} {env_appium}")
        
        if env_udid:
            desired_caps['udid'] = env_udid
            
        appium_url = device_config.get('appiumServerUrl', 'http://localhost:4723/wd/hub')
        if env_appium:
            if not env_appium.startswith("http"):
                env_appium = f"http://{env_appium}"
            appium_url = env_appium

        # 5. 处理 Appium 2.0 Options
        options = UiAutomator2Options().load_capabilities(desired_caps)

        # logger.info(f"Appium Server URL: {appium_url}")

        # print(f"\n[DriverFactory] 正在启动设备: {device_key} | "
        #       f"UDID: {desired_caps.get('udid')} | "
        #       f"Port: {desired_caps.get('systemPort')}")
        logger.info(f"[DriverFactory] 启动设备: {device_key} | \n"
                    f"UDID: {desired_caps.get('udid')} | \n"
                    f"Port: {desired_caps.get('systemPort')} | \n"
                    f"Appium Server URL: {appium_url}")

        # 💡 在尝试连接 Appium 之前，先进行一次快速网络探测 (3秒超时)，防止 Appium 服务未启动时连接无限挂起导致页面卡死
        import urllib.request
        from urllib.parse import urlparse
        try:
            parsed_url = urlparse(appium_url)
            # 兼容 Appium 1.x / 2.x 的状态探测地址
            probe_url = f"{parsed_url.scheme}://{parsed_url.netloc}/status"
            if "/wd/hub" in parsed_url.path:
                probe_url = f"{parsed_url.scheme}://{parsed_url.netloc}/wd/hub/status"
            
            logger.info(f"[DriverFactory] 正在对 Appium 进行连接探测: {probe_url}")
            req = urllib.request.Request(probe_url)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                pass
        except Exception as e:
            raise ConnectionError(
                f"\n❌ [DriverFactory] 无法连接到指定的 Appium 服务器: {appium_url}\n"
                f"请检查:\n"
                f"1. 该 IP 和端口的 Appium 服务是否已启动？\n"
                f"2. 如果是远程 Appium，请确认 Appium 启动参数是否包含了 `-a 0.0.0.0` (允许局域网访问)？\n"
                f"3. 局域网防火墙是否开放了该端口？\n"
                f"探测失败原因: {e}\n"
            )

        driver = webdriver.Remote(command_executor=appium_url, options=options)

        # 显式等待是最佳实践，隐式等待设为0防止冲突
        driver.implicitly_wait(0)
        return driver