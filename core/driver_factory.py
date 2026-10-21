import copy
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
from typing import Any
from urllib.parse import urlparse
from appium import webdriver
from appium.webdriver.client_config import AppiumClientConfig
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import WebDriverException
from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import load_yaml_data


class DriverFactory:
    @staticmethod
    def get_driver(device_key: str):
        return RecoverableDriver(device_key)

    @staticmethod
    def _create_driver(device_key: str):
        """
        工厂方法：根据 device_key ('sender' 或 'receiver') 创建驱动
        """
        # 1. 加载所有配置
        data = load_yaml_data("devices.yaml")

        # 2. 获取当前测试环境与设备配置集
        current_env = os.environ.get('ENV') or data.get('current_env', 'dev')
        logger.info(f"{LogIcon.ACTION} [DriverFactory] 当前测试环境: [{current_env}], 请求设备: [{device_key}]")

        env_config = data.get('devices', {}).get(current_env)
        if not env_config:
            raise ValueError(f"在 devices.yaml 的 devices 下找不到环境配置: {current_env}")

        clean_key = str(device_key).strip()
        actual_key = clean_key

        # 3. 平台智能路由与别名映射
        target_platform = (os.environ.get('PLATFORM') or data.get('current_platform') or 'android').strip().lower()

        # 规则 1：通用角色 (sender / receiver) 根据当前目标测试平台自动智能路由
        if clean_key in ('sender', 'receiver'):
            if target_platform in ('harmonyos', 'openharmony', 'hos'):
                target_key = f'harmony_{clean_key}'
                if target_key in env_config:
                    actual_key = target_key
                    logger.info(f"{LogIcon.SETUP} [DriverFactory] 当前测试平台为鸿蒙，通用角色 '{clean_key}' 智能路由至: '{actual_key}'")
            elif target_platform in ('ios', 'apple'):
                target_key = f'ios_{clean_key}'
                if target_key in env_config:
                    actual_key = target_key
                    logger.info(f"{LogIcon.SETUP} [DriverFactory] 当前测试平台为 iOS，通用角色 '{clean_key}' 智能路由至: '{actual_key}'")

        # 规则 2：显式端别名映射 (android_sender -> sender)
        elif clean_key == 'android_sender' and 'sender' in env_config:
            actual_key = 'sender'
        elif clean_key == 'android_receiver' and 'receiver' in env_config:
            actual_key = 'receiver'

        # 从当前环境中提取最终设备配置
        device_config = env_config.get(actual_key)
        if not device_config:
            raise ValueError(f"在 devices.yaml 的 '{current_env}' 环境下找不到设备配置: {clean_key} (最终路由: {actual_key})")

        # 4. 判定设备的真实所属平台（以设备自身配置的 platformName 为最高准则，支持异构三端多设备共存交互）
        raw_platform = str(device_config.get('platformName') or '').strip().lower()
        if not raw_platform:
            if 'harmony' in actual_key.lower():
                raw_platform = 'harmonyos'
            elif 'ios' in actual_key.lower():
                raw_platform = 'ios'
            else:
                raw_platform = 'android'

        from core.locator_manager import LocatorPlatformManager

        # =========================================================================
        # 🌐 平台一：鸿蒙原生环境 (HarmonyOS NEXT 6.0+)
        # =========================================================================
        if raw_platform in ('harmonyos', 'openharmony', 'hos'):
            LocatorPlatformManager.set_current_platform('harmonyos')
            harmony_common = data.get('harmony_app', {})
            merged_caps = copy.deepcopy(harmony_common)
            merged_caps.update(device_config)

            from core.harmony_driver import HarmonyDriver
            logger.info(f"{LogIcon.SETUP} [DriverFactory] 识别到鸿蒙平台设备 ({actual_key})，构建 HarmonyDriver 实例")
            h_driver = HarmonyDriver(merged_caps)
            h_driver._factory_device_key = device_key
            h_driver._factory_env = current_env
            h_driver._factory_udid = merged_caps.get("udid")
            h_driver._platform_name = "harmonyos"
            return h_driver

        # =========================================================================
        # 🌐 平台二：iOS 环境 (XCUITest)
        # =========================================================================
        if raw_platform in ('ios', 'apple'):
            LocatorPlatformManager.set_current_platform('ios')
            ios_common = data.get('ios_app', {})
            desired_caps = copy.deepcopy(ios_common)
            desired_caps.update(device_config)

            from appium.options.ios import XCUITestOptions
            options = XCUITestOptions().load_capabilities(desired_caps)
            appium_url = device_config.get('appiumServerUrl', 'http://127.0.0.1:4725')

            logger.info(f"{LogIcon.SETUP} [DriverFactory] 识别到 iOS 平台设备 ({actual_key})，构建 XCUITest 驱动实例")
            appium_http_timeout = 95
            client_config = AppiumClientConfig(
                remote_server_addr=appium_url,
                timeout=appium_http_timeout,
            )
            driver = webdriver.Remote(
                command_executor=appium_url,
                options=options,
                client_config=client_config,
            )
            driver.implicitly_wait(0)
            driver._factory_device_key = device_key
            driver._factory_appium_url = appium_url
            driver._factory_udid = desired_caps.get("udid")
            driver._factory_env = current_env
            driver._platform_name = "ios"
            return driver

        # =========================================================================
        # 🌐 平台三：Android 环境 (UiAutomator2)
        # =========================================================================
        LocatorPlatformManager.set_current_platform('android')
        common_caps = data.get('app', {})
        desired_caps = copy.deepcopy(common_caps)
        desired_caps.update(device_config)

        # 🔌 动态分配 free systemPort 解决 Windows TCP TIME_WAIT 导致第一次重启失败的问题
        system_port = desired_caps.get('systemPort')
        if system_port:
            base_port = 8200 if 'sender' in device_key.lower() else 8220
            free_port = system_port

            # 💡 先清理「原始配置端口」与设备端残留：上次用例异常 / debug 退出时 driver 未正常 quit，
            # 老的 adb forward 规则与手机端 uiautomator2 server 仍占用「原始 systemPort」。必须在动态分配
            # 「之前」清理它——否则后面清理的是分配后的新端口，老残留依旧占位，导致第一次启动 busy、第二次才成功。
            origin_udid = desired_caps.get('udid')
            try:
                forward_command = ["adb"]
                if origin_udid:
                    forward_command.extend(["-s", origin_udid])
                forward_command.extend(["forward", "--remove", f"tcp:{system_port}"])
                subprocess.run(forward_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"{LogIcon.SETUP} [DriverFactory] 已清理原始配置端口的 adb 转发规则: tcp:{system_port}")
                if origin_udid:
                    subprocess.run(
                        ["adb", "-s", origin_udid, "shell", "am", "force-stop", "io.appium.uiautomator2.server"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    subprocess.run(
                        ["adb", "-s", origin_udid, "shell", "am", "force-stop", "io.appium.uiautomator2.server.test"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    logger.info(f"{LogIcon.SETUP} [DriverFactory] 已强杀手机端残留的 UiAutomator2 Server 进程 (设备: {origin_udid})")
            except Exception as e:
                logger.debug(f"{LogIcon.WARN} [DriverFactory] 清理原始端口残留异常: {e}")

            try:
                # 优先使用 psutil 检查，因为它可以识别 TIME_WAIT 状态，避免 socket.bind 的假自由判定
                import psutil
                for port in range(base_port, base_port + 20):
                    in_use = False
                    for conn in psutil.net_connections(kind='inet'):
                        if conn.laddr and conn.laddr.port == port:
                            in_use = True
                            break
                    if not in_use:
                        free_port = port
                        break
            except (ImportError, Exception):
                # 如果未安装 psutil 或权限不足，回退到 socket 探测
                import socket
                for port in range(base_port, base_port + 20):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        try:
                            s.bind(('127.0.0.1', port))
                            free_port = port
                            break
                        except socket.error:
                            continue
            desired_caps['systemPort'] = free_port
            logger.info(f"{LogIcon.SETUP} [DriverFactory] 动态分配 systemPort: {free_port} (原始配置: {system_port})")
        
        # == 支持环境变量与 Web 回执动态覆盖 ==
        env_udid = os.environ.get("REMOTE_UDID")
        env_udid2 = os.environ.get("REMOTE_UDID2")
        env_appium = os.environ.get("REMOTE_APPIUM_URL")
        env_appium2 = os.environ.get("REMOTE_APPIUM_URL2")
        logger.info(f"{LogIcon.SETUP} [DriverFactory] 环境变量动态覆盖：UDID1={env_udid}, UDID2={env_udid2}, Appium1={env_appium}, Appium2={env_appium2}")
        
        # 1. 覆盖 UDID
        if 'sender' in device_key.lower():
            if env_udid and env_udid.strip():
                desired_caps['udid'] = env_udid.strip()
        elif 'receiver' in device_key.lower():
            if env_udid2 and env_udid2.strip():
                desired_caps['udid'] = env_udid2.strip()
                logger.info(f"{LogIcon.SETUP} [DriverFactory] 使用 REMOTE_UDID2 覆盖 receiver 设备的 UDID: {env_udid2.strip()}")
            else:
                receipt_str = os.environ.get("WEB_RECEIPT_DATA")
                if receipt_str:
                    try:
                        import json
                        web_receipt = json.loads(receipt_str)
                        receipt_udid = web_receipt.get("设备1")
                        if receipt_udid and receipt_udid.strip():
                            desired_caps['udid'] = receipt_udid.strip()
                            logger.info(f"{LogIcon.SETUP} [DriverFactory] 从 Web 回执中成功提取 '设备1' 覆盖 receiver 设备的 UDID: {receipt_udid.strip()}")
                    except Exception as e:
                        logger.warning(f"{LogIcon.WARN} [DriverFactory] 解析 WEB_RECEIPT_DATA 动态覆盖设备异常: {e}")

        # 2. 覆盖 Appium Server 物理连接地址
        appium_url = device_config.get('appiumServerUrl', 'http://localhost:4723/wd/hub')
        target_appium = None

        if 'sender' in device_key.lower():
            target_appium = env_appium
        elif 'receiver' in device_key.lower():
            target_appium = env_appium2

        if target_appium and target_appium.strip():
            if not target_appium.startswith("http"):
                target_appium = f"http://{target_appium}"
            appium_url = target_appium
            logger.info(f"{LogIcon.SETUP} [DriverFactory] 覆盖 {device_key} Appium 地址为: {appium_url}")

        # 5. 处理 Appium 2.0 Options
        options = UiAutomator2Options().load_capabilities(desired_caps)

        logger.debug(
            f"{LogIcon.FIND} \n{LogIcon.SETUP} [DriverFactory] 启动设备: {device_key} | \n"
            f"{LogIcon.FIND} UDID: {desired_caps.get('udid')} | \n"
            f"{LogIcon.FIND} Port: {desired_caps.get('systemPort')} | \n"
            f"{LogIcon.FIND} Appium Server URL: {appium_url}"
        )

        # 💡 兜底：清理「新分配端口」可能残留的 adb forward 规则。
        # 原始端口残留与设备端 uiautomator2 server 已在动态分配前统一清理，
        # 这里只针对最终选定的新端口再移除一次 forward，避免极小概率的占位。
        system_port = desired_caps.get('systemPort')
        if system_port:
            try:
                selected_udid = desired_caps.get("udid")
                forward_command = ["adb"]
                if selected_udid:
                    forward_command.extend(["-s", selected_udid])
                forward_command.extend(["forward", "--remove", f"tcp:{system_port}"])
                subprocess.run(forward_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"{LogIcon.SETUP} [DriverFactory] 已清理新分配端口的 adb 转发规则: tcp:{system_port}")
            except Exception as e:
                logger.debug(f"{LogIcon.WARN} [DriverFactory] 清理新分配端口 adb 转发异常: {e}")

        # 💡 在尝试连接 Appium 之前，先进行一次快速网络探测 (3秒超时)，防止 Appium 服务未启动时连接无限挂起导致页面卡死
        try:
            parsed_url = urlparse(appium_url)
            # 兼容 Appium 1.x / 2.x 的状态探测地址
            probe_url = f"{parsed_url.scheme}://{parsed_url.netloc}/status"
            if "/wd/hub" in parsed_url.path:
                probe_url = f"{parsed_url.scheme}://{parsed_url.netloc}/wd/hub/status"
            
            logger.info(f"{LogIcon.SETUP} [DriverFactory] 正在对 Appium 进行连接探测: {probe_url}")
            req = urllib.request.Request(probe_url)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                pass
        except Exception as e:
            raise ConnectionError(
                f"\n🔴 [DriverFactory] 无法连接到指定的 Appium 服务器: {appium_url}\n"
                f"请检查:\n"
                f"1. 该 IP 和端口的 Appium 服务是否已启动？\n"
                f"2. 如果是远程 Appium，请确认 Appium 启动参数是否包含了 `-a 0.0.0.0` (允许局域网访问) ?\n"
                f"3. 局域网防火墙是否开放了该端口？\n"
                f"探测失败原因: {e}\n"
            )

        # driver = webdriver.Remote(command_executor=appium_url, options=options)
        appium_http_timeout = 95

        client_config = AppiumClientConfig(
            remote_server_addr=appium_url,
            timeout=appium_http_timeout,
        )

        logger.info(
            f"{LogIcon.WAIT} [DriverFactory] Appium客户端HTTP超时: "
            f"{LogIcon.WAIT} {appium_http_timeout}s"
        )
        driver = webdriver.Remote(
            command_executor=appium_url,
            options=options,
            client_config=client_config,
        )

        # 显式等待是最佳实践，隐式等待设为0防止冲突
        driver.implicitly_wait(0)
        driver._factory_device_key = device_key
        driver._factory_system_port = system_port
        driver._factory_appium_url = appium_url
        driver._factory_udid = desired_caps.get("udid")
        driver._factory_env = current_env
        driver._platform_name = "android"
        return driver





class UiAutomator2RecoveryError(WebDriverException):
    """移动端驱动会话失效且已完成一次重建，当前用例应从 setup 重跑。"""


class RecoverableDriver:
    """保持同一 Driver 引用，并在 Android 或鸿蒙通信失效时原子替换底层会话。"""

    # teardown 方法失败时不能触发重建，否则测试结束阶段可能反而创建一个新 Session。
    _NO_RECOVERY_METHODS = {"close", "quit", "stop_client"}
    # 连续执行中的用例只比较本地时间；空闲超过该阈值才访问设备做健康检查。
    _HEALTH_CHECK_IDLE_SECONDS = 30.0

    def __init__(self, device_key: str):
        driver = DriverFactory._create_driver(device_key)
        object.__setattr__(self, "_device_key", device_key)
        object.__setattr__(self, "_driver", driver)
        object.__setattr__(self, "_platform_name", getattr(driver, "_platform_name", "android"))
        object.__setattr__(self, "_generation", 0)
        object.__setattr__(self, "_recovery_lock", threading.Lock())
        object.__setattr__(self, "_last_successful_command_at", time.monotonic())

    @staticmethod
    def _is_recoverable_transport_error(error: WebDriverException) -> bool:
        """只识别通信层故障，避免把定位器或业务错误误判为会话失效。"""
        if getattr(error, "command_outcome_unknown", False):
            # 结果未知的点击、输入等动作不能触发整条用例自动重跑。
            return False
        if getattr(error, "recoverable_transport_error", False):
            return True

        message = str(error).lower()
        proxy_timeout = (
            "could not proxy command to the remote server" in message
            and any(
                marker in message
                for marker in (
                    "timeout of",
                    "timed out",
                    "socket hang up",
                    "econnrefused",
                )
            )
        )
        server_stopped = any(
            marker in message
            for marker in (
                "uiautomator2 server is not running",
                "instrumentation process is not running",
                "the instrumentation process cannot be initialized",
                "hdc 失败",
                "target not found",
                "device not found",
                "no devices",
                "hdc server",
            )
        )
        return proxy_timeout or server_stopped

    def _probe_driver_health(self, timeout: float) -> None:
        """根据当前驱动类型（Android/HarmonyOS/iOS）自适应探测健康状态"""
        driver = object.__getattribute__(self, "_driver")
        plat = getattr(driver, "_platform_name", "")

        # 1. 鸿蒙探活同时检查设备在线状态和 UiTest 界面树服务
        if plat == "harmonyos" or hasattr(driver, "is_healthy"):
            if not driver.is_healthy(timeout=timeout):
                raise ConnectionError(f"鸿蒙设备 HDC 离线或服务异常 (设备: {getattr(driver, 'udid', '')})")
            return

        # 2. iOS 探活：轻量级窗口命令探测
        if plat == "ios":
            driver.get_window_size()
            return

        # 3. Android UiAutomator2 探活：优先直连本地端口
        system_port = getattr(driver, "_factory_system_port", None)
        appium_url = getattr(driver, "_factory_appium_url", "")
        parsed_url = urlparse(appium_url)
        local_hosts = {"127.0.0.1", "localhost", "::1"}

        if system_port and parsed_url.hostname in local_hosts:
            status_url = f"http://127.0.0.1:{system_port}/status"
            with urllib.request.urlopen(status_url, timeout=timeout) as response:
                payload = json.load(response)
            status = payload.get("value", payload)
            if status.get("ready") is not True:
                raise ConnectionError(f"UiAutomator2 未就绪: {status_url}")
            return

        # 远程 Appium 的 systemPort 不在本机，无法直连时使用轻量 WebDriver 命令探测。
        driver.get_window_size()

    def ensure_healthy(self, timeout: float = 2.0, force: bool = False) -> bool:
        """检查当前 Session；近期已有成功命令时跳过真实设备探测。"""
        last_successful_command_at = object.__getattribute__(self, "_last_successful_command_at")
        idle_seconds = time.monotonic() - last_successful_command_at
        if not force and idle_seconds < self._HEALTH_CHECK_IDLE_SECONDS:
            return True

        generation = object.__getattribute__(self, "_generation")
        try:
            self._probe_driver_health(timeout)
            object.__setattr__(self, "_last_successful_command_at", time.monotonic())
            return True
        except Exception as error:
            driver = object.__getattribute__(self, "_driver")
            plat = getattr(driver, "_platform_name", "")
            driver_type = "HarmonyOS" if plat == "harmonyos" else ("iOS" if plat == "ios" else "UiAutomator2")
            logger.warning(
                f"{LogIcon.WARN} [DriverRecovery] {self._device_key} 的 {driver_type} 健康检查失败，"
                f"{LogIcon.WARN} 准备重建 Session: {type(error).__name__}: {error}"
            )
            self._recover(generation, error)
            return True

    def _recover(self, failed_generation: int, cause: Exception) -> None:
        """在同一代 Session 上只执行一次重建，避免并发命令重复创建 Driver。"""
        recovery_lock = object.__getattribute__(self, "_recovery_lock")
        with recovery_lock:
            current_generation = object.__getattribute__(self, "_generation")
            # 其他线程已经完成重建时，当前线程直接复用新 Session。
            if current_generation != failed_generation:
                return

            old_driver = object.__getattribute__(self, "_driver")
            is_harmony = getattr(old_driver, "_is_harmony_driver", False)
            driver_type = "HarmonyOS" if is_harmony else "UiAutomator2"
            logger.error(
                f"{LogIcon.ACTION} [DriverRecovery] 检测到 {self._device_key} 的 "
                f"{driver_type} 通信失效，{LogIcon.FAIL} 开始单次重建 Session | "
                f"原因: {type(cause).__name__}: {cause}"
            )

            if is_harmony:
                # HMNextAuto 按设备缓存 Driver；先关闭旧实例才能真正建立新连接。
                try:
                    old_driver.quit()
                except Exception as close_error:
                    logger.warning(
                        f"{LogIcon.WARN} [DriverRecovery] 关闭旧鸿蒙会话失败，"
                        f"继续尝试重建: {type(close_error).__name__}: {close_error}"
                    )
            # Android 不主动 quit 冻结会话，工厂会清理 UiAutomator2 与端口残留。
            try:
                new_driver = DriverFactory._create_driver(self._device_key)
            except Exception as recovery_error:
                raise UiAutomator2RecoveryError(
                    f"{self._device_key} 的 {driver_type} Session 重建失败: "
                    f"{recovery_error}"
                ) from recovery_error

            object.__setattr__(self, "_driver", new_driver)
            object.__setattr__(self, "_platform_name", getattr(new_driver, "_platform_name", "android"))
            object.__setattr__(self, "_generation", current_generation + 1)
            object.__setattr__(self, "_last_successful_command_at", time.monotonic())
            logger.info(
                f"{LogIcon.SUCCESS} [DriverRecovery] {self._device_key} 的 "
                f"{driver_type} Session 已重建，"
                f"{LogIcon.ACTION} 新 Session ID: {new_driver.session_id}"
            )

    def _bind_recoverable_result(self, result: Any) -> Any:
        """让鸿蒙元素后续动作继续经过当前 RecoverableDriver 代理。"""
        result_items = result if isinstance(result, (list, tuple)) else (result,)
        for item in result_items:
            bind_driver = getattr(item, "_bind_command_driver", None)
            if callable(bind_driver):
                bind_driver(self)
        return result

    def _raise_after_recovery(
        self,
        generation: int,
        error: WebDriverException,
        failed_driver: Any,
    ) -> None:
        """按异常类型决定是否重建，并阻止当前业务步骤在新页面继续执行。"""
        if not self._is_recoverable_transport_error(error):
            raise error

        plat = getattr(failed_driver, "_platform_name", "")
        driver_type = "HarmonyOS" if plat == "harmonyos" else ("iOS" if plat == "ios" else "UiAutomator2")
        self._recover(generation, error)
        raise UiAutomator2RecoveryError(
            f"{self._device_key} 的 {driver_type} Session 已自动重建；"
            "为避免在错误页面继续执行，当前用例需要从 setup 重跑一次"
        ) from error

    def __getattr__(self, name: str) -> Any:
        # Page Object 始终持有本代理；属性和命令在调用时再解析到当前底层 Driver。
        driver = object.__getattribute__(self, "_driver")
        generation = object.__getattribute__(self, "_generation")
        try:
            attribute = getattr(driver, name)
        except WebDriverException as error:
            self._raise_after_recovery(generation, error, driver)
        if not callable(attribute) or name in self._NO_RECOVERY_METHODS:
            return attribute

        def guarded_command(*args: Any, **kwargs: Any) -> Any:
            current_driver = object.__getattribute__(self, "_driver")
            current_generation = object.__getattribute__(self, "_generation")
            try:
                result = getattr(current_driver, name)(*args, **kwargs)
                result = self._bind_recoverable_result(result)
                object.__setattr__(self, "_last_successful_command_at", time.monotonic())
                return result
            except WebDriverException as error:
                self._raise_after_recovery(
                    current_generation,
                    error,
                    current_driver,
                )

        return guarded_command

    def quit(self):
        driver = object.__getattribute__(self, "_driver")
        return driver.quit()

    @property
    def raw_driver(self):
        return object.__getattribute__(self, "_driver")
