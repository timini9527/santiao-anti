import copy
import json
import os
import subprocess
import threading
import time
import urllib.request
from urllib.parse import urlparse
from appium import webdriver
from appium.webdriver.client_config import AppiumClientConfig
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import WebDriverException
from core.logger_utils import logger
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
                logger.info(f"🧹 [DriverFactory] 已清理原始配置端口的 adb 转发规则: tcp:{system_port}")
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
                    logger.info(f"🧹 [DriverFactory] 已强杀手机端残留的 UiAutomator2 Server 进程 (设备: {origin_udid})")
            except Exception as e:
                logger.debug(f"[DriverFactory] 清理原始端口残留异常: {e}")

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
            logger.info(f"🔌 [DriverFactory] 动态分配 systemPort: {free_port} (原始配置: {system_port})")
        
        # == 支持环境变量与 Web 回执动态覆盖 ==
        env_udid = os.environ.get("REMOTE_UDID")
        env_udid2 = os.environ.get("REMOTE_UDID2")
        env_appium = os.environ.get("REMOTE_APPIUM_URL")
        env_appium2 = os.environ.get("REMOTE_APPIUM_URL2")
        logger.info(f"[DriverFactory] 环境变量动态覆盖：UDID1={env_udid}, UDID2={env_udid2}, Appium1={env_appium}, Appium2={env_appium2}")
        
        # 1. 覆盖 UDID
        if 'sender' in device_key.lower():
            if env_udid and env_udid.strip():
                desired_caps['udid'] = env_udid.strip()
        elif 'receiver' in device_key.lower():
            if env_udid2 and env_udid2.strip():
                desired_caps['udid'] = env_udid2.strip()
                logger.info(f"[DriverFactory] 使用 REMOTE_UDID2 覆盖 receiver 设备的 UDID: {env_udid2.strip()}")
            else:
                receipt_str = os.environ.get("WEB_RECEIPT_DATA")
                if receipt_str:
                    try:
                        import json
                        web_receipt = json.loads(receipt_str)
                        receipt_udid = web_receipt.get("设备1")
                        if receipt_udid and receipt_udid.strip():
                            desired_caps['udid'] = receipt_udid.strip()
                            logger.info(f"[DriverFactory] 从 Web 回执中成功提取 '设备1' 覆盖 receiver 设备的 UDID: {receipt_udid.strip()}")
                    except Exception as e:
                        logger.warning(f"[DriverFactory] 解析 WEB_RECEIPT_DATA 动态覆盖设备异常: {e}")

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
            logger.info(f"[DriverFactory] 覆盖 {device_key} Appium 地址为: {appium_url}")

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
                logger.info(f"🧹 [DriverFactory] 已清理新分配端口的 adb 转发规则: tcp:{system_port}")
            except Exception as e:
                logger.debug(f"[DriverFactory] 清理新分配端口 adb 转发异常: {e}")

        # 💡 在尝试连接 Appium 之前，先进行一次快速网络探测 (3秒超时)，防止 Appium 服务未启动时连接无限挂起导致页面卡死
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
                f"2. 如果是远程 Appium，请确认 Appium 启动参数是否包含了 `-a 0.0.0.0` (允许局域网访问) ?\n"
                f"3. 局域网防火墙是否开放了该端口？\n"
                f"探测失败原因: {e}\n"
            )

        # driver = webdriver.Remote(command_executor=appium_url, options=options)
        appium_http_timeout = 15

        client_config = AppiumClientConfig(
            remote_server_addr=appium_url,
            timeout=appium_http_timeout,
        )

        logger.info(
            f"[DriverFactory] Appium客户端HTTP超时: "
            f"{appium_http_timeout}s"
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
        return driver





class UiAutomator2RecoveryError(WebDriverException):
    """UiAutomator2 会话失效且已完成一次重建，当前用例应从 setup 重跑。"""


class RecoverableDriver:
    """对外保持同一个 Driver 引用，底层 UiAutomator2 Session 失效时可原子替换。"""

    # teardown 方法失败时不能触发重建，否则测试结束阶段可能反而创建一个新 Session。
    _NO_RECOVERY_METHODS = {"close", "quit", "stop_client"}
    # 连续执行中的用例只比较本地时间；空闲超过该阈值才访问设备做健康检查。
    _HEALTH_CHECK_IDLE_SECONDS = 30.0

    def __init__(self, device_key: str):
        object.__setattr__(self, "_device_key", device_key)
        object.__setattr__(self, "_driver", DriverFactory._create_driver(device_key))
        object.__setattr__(self, "_generation", 0)
        object.__setattr__(self, "_recovery_lock", threading.Lock())
        object.__setattr__(self, "_last_successful_command_at", time.monotonic())

    @staticmethod
    def _is_uiautomator2_proxy_error(error: WebDriverException) -> bool:
        """只识别服务端代理/Instrumentation 故障，避免把定位器错误当成设备故障。"""
        message = str(error).lower()
        proxy_timeout = (
            "could not proxy command to the remote server" in message
            and any(marker in message for marker in ("timeout of", "timed out", "socket hang up", "econnrefused"))
        )
        server_stopped = any(
            marker in message
            for marker in (
                "uiautomator2 server is not running",
                "instrumentation process is not running",
                "the instrumentation process cannot be initialized",
            )
        )
        return proxy_timeout or server_stopped

    def _probe_uiautomator2(self, timeout: float) -> None:
        """优先绕过 Appium 直连 UiAutomator2，快速判断手机端服务是否还能响应。"""
        driver = object.__getattribute__(self, "_driver")
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
            self._probe_uiautomator2(timeout)
            object.__setattr__(self, "_last_successful_command_at", time.monotonic())
            return True
        except Exception as error:
            logger.warning(
                f"⚠️ [DriverRecovery] {self._device_key} 的 UiAutomator2 健康检查失败，"
                f"准备重建 Session: {type(error).__name__}: {error}"
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

            logger.error(
                f"🔄 [DriverRecovery] 检测到 {self._device_key} 的 UiAutomator2 通信失效，"
                f"开始单次重建 Session | 原因: {type(cause).__name__}: {cause}"
            )
            # 不调用旧 driver.quit()：冻结会话的 DELETE 请求可能再次阻塞，或误停随后启动的新服务。
            # _create_driver() 会按设备清理残留 UiAutomator2 进程和 adb forward，再创建全新 Session。
            try:
                new_driver = DriverFactory._create_driver(self._device_key)
            except Exception as recovery_error:
                raise UiAutomator2RecoveryError(
                    f"{self._device_key} 的 UiAutomator2 Session 重建失败: {recovery_error}"
                ) from recovery_error

            object.__setattr__(self, "_driver", new_driver)
            object.__setattr__(self, "_generation", current_generation + 1)
            object.__setattr__(self, "_last_successful_command_at", time.monotonic())
            logger.info(
                f"✅ [DriverRecovery] {self._device_key} 的 UiAutomator2 Session 已重建，"
                f"新 Session ID: {new_driver.session_id}"
            )

    def __getattr__(self, name):
        # Page Object 始终持有本代理；属性和命令在调用时再解析到当前底层 Driver。
        driver = object.__getattribute__(self, "_driver")
        attribute = getattr(driver, name)
        if not callable(attribute) or name in self._NO_RECOVERY_METHODS:
            return attribute

        def guarded_command(*args, **kwargs):
            current_driver = object.__getattribute__(self, "_driver")
            generation = object.__getattribute__(self, "_generation")
            try:
                result = getattr(current_driver, name)(*args, **kwargs)
                object.__setattr__(self, "_last_successful_command_at", time.monotonic())
                return result
            except WebDriverException as error:
                if not self._is_uiautomator2_proxy_error(error):
                    raise

                self._recover(generation, error)
                # 新 Session 可能重新启动到主页面，不能在原业务步骤后直接继续执行。
                raise UiAutomator2RecoveryError(
                    f"{self._device_key} 的 UiAutomator2 Session 已自动重建；"
                    "为避免在错误页面继续执行，当前用例需要从 setup 重跑一次"
                ) from error

        return guarded_command

    def quit(self):
        driver = object.__getattribute__(self, "_driver")
        return driver.quit()

    @property
    def raw_driver(self):
        return object.__getattribute__(self, "_driver")
