import os
import pytest
import time
import yaml
import allure
import logging
import socket
from core.driver_factory import DriverFactory
from pages.main.main_page import MainPage

logger = logging.getLogger(__name__)

# socket.setdefaulttimeout(15)

def _get_default_env() -> str:
    """从 config/devices.yaml 中读取默认的运行环境，保持配置的一致性"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config", "devices.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
            return raw_data.get("current_env", "dev")
    except Exception:
        return "dev"


def pytest_addoption(parser):
    """注册命令行参数 --env，允许动态指定执行环境 (如 dev, test)"""
    parser.addoption(
        "--env",
        action="store",
        default=_get_default_env(),
        help="运行环境可选值: dev, test (默认读取 devices.yaml 中的配置)"
    )


def pytest_configure(config):
    """在测试启动时，将命令行传入的环境同步到系统环境变量 ENV，确保全局统一"""
    env = config.getoption("--env")
    if env:
        os.environ["ENV"] = env
        os.environ["TEST_ENV"] = env
        logger.info(f"🌐 [pytest_configure] 全局测试环境已设定为: {env}")


# ============================================================
# 全局重跑控制器
# 说明：基于 config/rerun.yaml 提供 Session 级重跑上限熔断、
#       逐次重跑日志追踪、Allure Flaky 标签自动标记。
# ============================================================

# 加载重跑配置
_RERUN_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "rerun.yaml")


def _load_rerun_config() -> dict:
    """加载 config/rerun.yaml 中的重跑策略配置"""
    try:
        with open(_RERUN_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("rerun", {})
    except FileNotFoundError:
        logger.warning(f"⚠️ 重跑配置文件不存在: {_RERUN_CONFIG_PATH}，使用默认值")
        return {}
    except Exception as e:
        logger.error(f"❌ 加载重跑配置失败: {e}，使用默认值")
        return {}


_rerun_cfg = _load_rerun_config()

# 从配置文件读取参数，提供合理的默认值
SESSION_MAX_RERUNS = _rerun_cfg.get("session_max_reruns", 20)
LOG_RERUN = _rerun_cfg.get("log_rerun", True)
ALLURE_LABEL = _rerun_cfg.get("allure_label", True)

# Session 级重跑计数器
_session_rerun_count = 0

#TODO：失败自动重跑截图功能待验证
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    全局 Hook：在每条用例执行完毕后检测是否触发了重跑，
    并进行日志记录、Allure 标记、Session 级熔断控制。
    """
    global _session_rerun_count
    outcome = yield
    report = outcome.get_result()

    # 只处理 "call" 阶段的结果（跳过 setup / teardown）
    if report.when != "call":
        return

    # 失败时自动截图并保存到 Allure 报告
    if report.failed:
        for driver_name in ["driver_sender", "driver_receiver", "driver"]:
            if driver_name in item.funcargs:
                try:
                    driver = item.funcargs[driver_name]
                    allure.attach(
                        driver.get_screenshot_as_png(),
                        name=f"失败现场截图 ({driver_name})",
                        attachment_type=allure.attachment_type.PNG
                    )
                    logger.info(f"📸 自动捕获失败截图: {driver_name}")
                except Exception as e:
                    logger.warning(f"⚠️ 捕获失败截图 {driver_name} 失败: {e}")

    # ---- 重跑检测 ----
    # pytest-rerunfailures 会在 item 上挂载 execution_count 属性
    exec_count = getattr(item, "execution_count", 0)

    if report.failed and exec_count > 0:
        # 本次是重跑后的结果
        _session_rerun_count += 1

        if LOG_RERUN:
            logger.warning(
                f"🔄 [Rerun] 用例 [{item.nodeid}] 第 {exec_count} 次重跑仍失败 "
                f"| Session 已重跑: {_session_rerun_count}/{SESSION_MAX_RERUNS}"
            )

        # Allure 标记 Flaky
        if ALLURE_LABEL:
            allure.dynamic.tag("flaky")
            allure.dynamic.label("severity", "normal")

        # Session 级熔断：当整个会话的重跑总次数超过上限时，跳过后续所有用例的重跑
        if _session_rerun_count >= SESSION_MAX_RERUNS:
            logger.error(
                f"🚨 [Rerun] Session 重跑总次数已达上限 ({SESSION_MAX_RERUNS})！"
                f"后续失败用例将不再重跑，请检查测试环境稳定性。"
            )
            # 通过移除 reruns marker 来阻止后续用例重跑
            item.config.option.reruns = 0

    elif report.passed and exec_count > 0:
        # 重跑后通过了
        _session_rerun_count += 1

        if LOG_RERUN:
            logger.info(
                f"✅ [Rerun] 用例 [{item.nodeid}] 第 {exec_count} 次重跑后通过 ✅ "
                f"| Session 已重跑: {_session_rerun_count}/{SESSION_MAX_RERUNS}"
            )

        if ALLURE_LABEL:
            allure.dynamic.tag("flaky-passed")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """在测试结束后输出重跑统计摘要"""
    if _session_rerun_count > 0:
        terminalreporter.write_sep("=", "重跑统计摘要 (Rerun Summary)")
        terminalreporter.write_line(
            f"  📊 本次 Session 共触发 {_session_rerun_count} 次重跑 "
            f"(上限: {SESSION_MAX_RERUNS})"
        )
        if _session_rerun_count >= SESSION_MAX_RERUNS:
            terminalreporter.write_line(
                "  🚨 已触发 Session 级熔断！建议检查测试环境稳定性。"
            )
        terminalreporter.write_sep("=", "")



# --- API 准备 (保持你原有的逻辑) ---
# @pytest.fixture(scope="session", autouse=True)
def prepare_api_token():
    print("\n[Setup] 正在进行 API 辅助账号登录...")
    # auth = AuthApi()
    # success = auth.login()
    # assert success, "API 账号登录失败"
    pass


_DRIVER_FIXTURE_NAMES = (
    "driver_sender",
    "driver_receiver",
    "driver_device3",
    "driver_device4",
    "driver_device5",
    "driver_device6",
    "driver_device7",
    "driver_device8",
    "driver_device9",
)


@pytest.fixture(autouse=True)
def ensure_driver_session_health(request):
    """每条用例执行前检查其 Driver；最近有成功命令时只做内存判断。"""
    for fixture_name in _DRIVER_FIXTURE_NAMES:
        if fixture_name not in request.fixturenames:
            continue

        driver = request.getfixturevalue(fixture_name)
        health_check = getattr(driver, "ensure_healthy", None)
        if health_check:
            health_check(timeout=2.0)


# --- Driver Fixtures ---
@pytest.fixture(scope="session")
def driver_sender():
    """ 启动发送方设备 (Session 级别，整个测试过程只启动一次) """
    driver = DriverFactory.get_driver('sender')
    # MainPage(driver).wait_for_main_page_load()
    time.sleep(5)
    try:
        yield driver
    finally:
        # 放进 finally：即使用例 setup/执行阶段抛异常，也保证执行清理逻辑，
        # 避免 driver 未 quit 导致 systemPort 残留、下次启动端口 busy。
        print("\n[Teardown] 关闭发送方驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()

@pytest.fixture(scope="session")
def driver_receiver():
    """ 启动接收方设备 """
    driver = DriverFactory.get_driver('receiver')
    try:
        yield driver
    finally:
        print("\n[Teardown] 关闭接收方驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()

@pytest.fixture(scope="session")
def driver_device3():
    """ 启动第3个设备 """
    driver = DriverFactory.get_driver('device3')
    try:
        yield driver
    finally:
        print("\n[Teardown] 关闭第3个设备驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()

@pytest.fixture(scope="session")
def driver_device4():
    """ 启动第4个设备 """
    driver = DriverFactory.get_driver('device4')
    try:
        yield driver
    finally:
        print("\n[Teardown] 关闭第4个设备驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()

@pytest.fixture(scope="session")
def driver_device5():
    """ 启动第5个设备 """
    driver = DriverFactory.get_driver('device5')
    try:
        yield driver
    finally:
        print("\n[Teardown] 关闭第5个设备驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()

@pytest.fixture(scope="session")
def driver_device6():
    """ 启动第6个设备 """
    driver = DriverFactory.get_driver('device6')
    try:
        yield driver
    finally:
        print("\n[Teardown] 关闭第6个设备驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()

@pytest.fixture(scope="session")
def driver_device7():
    """ 启动第7个设备 """
    driver = DriverFactory.get_driver('device7')
    try:
        yield driver
    finally:
        print("\n[Teardown] 关闭第7个设备驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()

@pytest.fixture(scope="session")
def driver_device8():
    """ 启动第8个设备 """
    driver = DriverFactory.get_driver('device8')
    try:
        yield driver
    finally:
        print("\n[Teardown] 关闭第8个设备驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()

@pytest.fixture(scope="session")
def driver_device9():
    """ 启动第9个设备 """
    driver = DriverFactory.get_driver('device9')
    try:
        yield driver
    finally:
        print("\n[Teardown] 关闭第9个设备驱动")
        if os.environ.get("DEBUG_MODE") == "1":
            print("🐞 [DEBUG 模式] 已保留 Appium Driver 存活，未主动退出。您可以随时使用 Inspector 连接。")
        else:
            driver.quit()


# --- Page Object Fixtures (依赖注入) ---


# @pytest.fixture(scope="function")
# def sender_app(driver_sender):
#     """ 返回发送方的业务操作对象 """
#     return ChatPage(driver_sender)
#
# @pytest.fixture(scope="function")
# def receiver_app(driver_receiver):
#     """ 返回接收方的业务操作对象 """
#     return ChatPage(driver_receiver)

""""""
# ==========================================
# 1. API 账号登录 Fixture (Session级别)
# ==========================================
# @pytest.fixture(scope="session", autouse=True)
# def prepare_api_token():
#     """
#     在所有测试开始前，先让 API 账号(User B)登录，
#     确保 auth_config.yaml 里有 Token，后续测试用例可以直接用。
#     """
#     print("\n[Setup] 正在进行 API 辅助账号登录...")
#     auth = AuthApi()
#     success = auth.login()
#     assert success, "API 账号登录失败，无法进行后续测试！"
#
#
# def reset_ime():
#     # 查询当前系统输入法列表
#     result = subprocess.check_output("adb shell ime list -s", shell=True).decode()
#     # print("IME list:", result)
#
#     # 设置为讯飞输入法（你需要换成自己的输入法ID）
#     subprocess.call("adb shell ime set com.iflytek.inputmethod.miui/.FlyIME", shell=True)

""""""
# ==========================================
# @pytest.fixture(scope="session")
# def driver():
#     # 设置 Desired Capabilities
#     desired_caps = {
#         'platformName': 'Android',  # 被测手机是安卓
#         "automationName": "UiAutomator2",
#         'platformVersion': '10.0',  # 安卓版本，如果是鸿蒙系统，依次尝试 12、11、10 版本号
#         # 'udid': '你的设备序列号',  # 指定连接设备
#         'deviceName': 'Android',  # 设备名，安卓手机可以随意填写
#         'appPackage': 'com.santiaotalk.im',  # 启动APP Package名称
#         'appActivity': 'com.vvchat.vcapp.activity.MainActivity',  # 启动Activity名称
#         'appWaitActivity': 'com.vvchat.vcapp.activity.MainActivity',  # 等待登录页
#
#         # 以下为vivo救命参数 ↓↓↓
#         'noSign': True,  # 跳过APK重签名
#         'skipServerInstallation': True,  # 强制重装Appium服务
#         'skipDeviceInitialization': True,  # 强制初始化设备
#         'disableWindowAnimation': False,  # False开启动画, True关闭动画
#         'autoGrantPermissions': True,  # 自动授权所有权限
#         'adbExecTimeout': 6000,  # ADB超时延长到60秒
#         'uiautomator2ServerLaunchTimeout': 6000,  # UiAutomator2服务启动超时
#         'appWaitForLaunch': False,  # 不等待默认启动（vivo会拦截）
#         'intentAction': 'android.intent.action.MAIN',  # 绕过vivo启动限制
#         'intentCategory': 'android.intent.category.LAUNCHER',
#         'unicodeKeyboard': True,  # 自动化需要输入中文时填True
#         'resetKeyboard': True,  # 执行完程序恢复原来输入法
#         'noReset': True,  # 不要重置App
#         'newCommandTimeout': 6000,
#     }
#
#     # 使用新的 Options 类封装
#     options = UiAutomator2Options().load_capabilities(desired_caps)
#     # 创建 WebDriver 实例
#     driver = webdriver.Remote(command_executor='http://localhost:4723/wd/hub', options=options)
#
#     print("✅ Android 驱动启动成功! 当前Activity:", driver.current_activity)
#     print("Driver started:", driver)
#
#     # driver.back()
#
#     yield driver
#
#     driver.quit()



""""""
# 按时用不到的代理
# PROXY_PORT = 8888
# PROXY_SCRIPT = "utils/addon_proxy.py"
# @pytest.fixture(scope="session", autouse=True)
# def proxy_server():
#     """
#     Session 级别的 Fixture：自动启动和停止 mitmdump 代理
#     """
#     # 1. 清理旧 Token 文件
#     if os.path.exists("temp_token.txt"):
#         os.remove("temp_token.txt")
#
#     print(f"\n🚀 正在启动 mitmproxy (Port: {PROXY_PORT})...")
#
#     # 2. 子进程启动 mitmdump
#     # -s 指定脚本, -p 指定端口, -q 静默模式
#     cmd = f"mitmdump -s {PROXY_SCRIPT} -p {PROXY_PORT} -q"
#     process = subprocess.Popen(cmd, shell=True)
#
#     # 等待几秒确保启动成功
#     time.sleep(3)
#
#     yield process
#
#     # 3. 测试结束，杀掉代理进程
#     print("\n🛑 正在关闭 mitmproxy...")
#     # Windows 使用 taskkill, Linux/Mac 使用 kill
#     if os.name == 'nt':
#         subprocess.run(f"taskkill /F /PID {process.pid}", shell=True, stderr=subprocess.DEVNULL)
#     else:
#         os.kill(process.pid, signal.SIGTERM)


""""""
# 核心：失败自动截图并保存到 Allure 报告
# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     outcome = yield
#     rep = outcome.get_result()
#     if rep.when == "call" and rep.failed:
#         mode = "a" if os.path.exists("failures") else "w"
#         try:
#             driver = item.funcargs['driver']
#             # 将截图附加到 Allure 报告中
#             allure.attach(
#                 driver.get_screenshot_as_png(),
#                 name="失败现场截图",
#                 attachment_type=allure.attachment_type.PNG
#             )
#         except Exception as e:
#             print(f"截图失败: {e}")



# Testing 中映射用例名称（使用 allure.title或者docstring 第一行）
# def pytest_itemcollected(item):
#     """
#     pytest 收集用例时的钩子：为用例添加自定义中文名称（优先使用 allure.title，其次使用 docstring）
#     这可以在 IDE（如 VS Code Testing 面板）和命令行执行输出中显示直观的中文名称
#     """
#     try:
#         # 1. 尝试从 allure.title 中获取自定义名称 (allure 内部使用 allure_display_name 标记)
#         allure_marker = item.get_closest_marker("allure_display_name")
#         if allure_marker and allure_marker.args:
#             custom_name = allure_marker.args[0]
#             # item.name = f"{item.name} [{custom_name}]"
#             item.name = f"[{custom_name}]"
#         # 2. 如果没有 allure.title，则使用函数 docstring 的第一行
#         elif item.obj and item.obj.__doc__:
#             doc_first_line = item.obj.__doc__.strip().split('\n')[0].strip()
#             if doc_first_line:
#                 # item.name = f"{item.name} [{doc_first_line}]"
#                 item.name = f"[{doc_first_line}]"
#     except Exception as e:
#         logger.warning(f"⚠️ [Hook-pytest_itemcollected] 自定义用例名称失败: {e}")
