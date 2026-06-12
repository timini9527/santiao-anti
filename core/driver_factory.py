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
        # 1. 获取当前运行环境 (从 api_config.yaml 读取，支持环境变量覆盖)
        env = os.environ.get("TEST_ENV")
        if not env:
            try:
                api_config = load_yaml_data("api_config.yaml")
                env = api_config.get("current_env", "dev")
            except Exception as e:
                logger.warning(f"⚠️ [DriverFactory] 无法读取 api_config.yaml，默认使用 dev 环境: {e}")
                env = "dev"
        
        logger.info(f"⚙️ [DriverFactory] 当前测试环境: {env}")

        # 2. 尝试读取环境专属的配置文件 (如 devices_dev.yaml)，如果不存在则使用默认的 devices.yaml
        device_file = f"devices_{env}.yaml"
        from utils.file_reader.data_loader import find_file
        
        if find_file(device_file):
            logger.info(f"📂 [DriverFactory] 发现环境专属设备配置文件: {device_file}")
            data = load_yaml_data(device_file)
            devices_section = data.get('devices', {})
            # 兼容嵌套环境和直接平铺设备的情况
            if env in devices_section:
                device_config = devices_section.get(env, {}).get(device_key)
            else:
                device_config = devices_section.get(device_key)
        else:
            logger.info("📂 [DriverFactory] 读取通用 devices.yaml 配置文件")
            data = load_yaml_data("devices.yaml")
            devices_section = data.get('devices', {})
            device_config = devices_section.get(env, {}).get(device_key)

        if not device_config:
            raise ValueError(f"❌ 在设备配置文件中找不到环境 '{env}' 下的设备: {device_key}")

        # 3. 获取公共 App 配置
        common_caps = data.get('app', {})

        # 4. 合并 Capability (深拷贝防止污染)
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