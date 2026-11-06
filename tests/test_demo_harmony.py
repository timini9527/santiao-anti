import time
import allure
import pytest
from appium import webdriver
from appium.options.common.base import AppiumOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from hypium import BY, UiDriver
from hypium.model.basic_data_type import InputTextMode
from core.logger_utils import LogIcon, logger


# ==============================================================================
# 测试类一：基于 appium-harmonyos-driver 框架的发送消息测试用例
# ==============================================================================
@allure.epic("IM核心功能测试")
@allure.feature("鸿蒙端框架对比-Appium-HarmonyOS-Driver")
class TestAppiumHarmonyOSDriver:
    """
    基于社区开源 appium-harmonyos-driver 的自动化测试套件。
    驱动链路：Python WebDriver Client -> Appium Server (Node.js) -> harmonyos 驱动插件 -> HDC/真机。
    所有连接参数与生命周期管理均在当前类内部独立维护。
    """

    # 1. 驱动与连接配置参数
    APPIUM_SERVER_URL: str = "http://127.0.0.1:4723"
    DEVICE_UDID: str = "3YZ9K25104007630"
    BUNDLE_NAME: str = "com.santiaohms.im"
    ABILITY_NAME: str = "EntryAbility"
    TARGET_SESSION_NAME: str = "测试0222"

    @pytest.fixture(autouse=False)
    def appium_driver(self):
        """
        初始化与启动 appium-harmonyos-driver 会话。
        前置：创建并连接 Appium WebDriver；后置：释放会话资源。
        """
        logger.info(
            f"{LogIcon.SETUP} [Appium-HarmonyOS-Driver] 正在连接 Appium Server: {self.APPIUM_SERVER_URL}"
        )
        capabilities = {
            "platformName": "harmonyos",
            "appium:automationName": "harmonyos",
            "appium:udid": self.DEVICE_UDID,
            "appium:bundleName": self.BUNDLE_NAME,
            "appium:abilityName": self.ABILITY_NAME,
            "appium:newCommandTimeout": 120,
            "appium:noReset": True,
        }
        options = AppiumOptions().load_capabilities(capabilities)
        driver = webdriver.Remote(
            command_executor=self.APPIUM_SERVER_URL,
            options=options,
        )
        driver.implicitly_wait(10)
        logger.info(f"{LogIcon.SUCCESS} [Appium-HarmonyOS-Driver] 驱动会话创建成功")

        try:
            yield driver
        finally:
            logger.info(f"{LogIcon.SETUP} [Appium-HarmonyOS-Driver] 正在销毁驱动会话...")
            try:
                driver.quit()
            except Exception as e:
                logger.warning(
                    f"{LogIcon.WARN} [Appium-HarmonyOS-Driver] 销毁会话异常: {e}"
                )

    @allure.story("会话消息收发")
    @allure.title("使用 appium-harmonyos-driver 在测试0222会话中发送文本消息")
    @pytest.mark.p0
    def test_send_message_via_appium_harmonyos_driver(self, appium_driver):
        """
        测试用例：通过 appium-harmonyos-driver 原生 WebDriver 协议向指定会话发送消息。
        测试步骤：
        1. 在主会话列表中检索并点击 '测试0222' 会话项；
        2. 定位聊天输入框并输入指定消息文本；
        3. 点击发送按钮完成消息下发；
        4. 检索聊天流，断言发送的消息内容已成功上屏。
        """
        send_content = f"AppiumHarmonyOS_{int(time.time())}"
        wait = WebDriverWait(appium_driver, timeout=15, poll_frequency=0.5)

        with allure.step(f"1. 查找并点击会话: '{self.TARGET_SESSION_NAME}'"):
            logger.info(
                f"{LogIcon.ACTION} 查找目标会话控件: {self.TARGET_SESSION_NAME}"
            )
            # 通过显式等待查找文本节点并点击进入
            session_element = wait.until(
                EC.presence_of_element_located((By.XPATH, f"//*[@text='{self.TARGET_SESSION_NAME}']")),
                message=f"超时未找到会话项: {self.TARGET_SESSION_NAME}"
            )
            session_element.click()
            time.sleep(1.0)

        with allure.step("2. 定位输入框并输入消息内容"):
            logger.info(f"{LogIcon.ACTION} 写入测试消息: '{send_content}'")
            # 兼容 ArkUI 常见输入组件类型；避免主动 click 导致强制呼出输入法软键盘
            input_box = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//TextInput | //TextArea | //RichEditor | //*[@id='inputText']",
                )),
                message="超时未找到聊天输入框组件"
            )
            input_box.send_keys(send_content)
            time.sleep(0.3)

        with allure.step("3. 触发发送操作"):
            logger.info(f"{LogIcon.ACTION} 点击发送按钮")
            send_button = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//*[@text='发送'] | //Button[@text='发送'] | //NavDestination//Row//Row/Stack/Image",
                )),
                message="超时未找到可点击的发送按钮"
            )
            send_button.click()
            time.sleep(1.0)

        with allure.step("4. 校验消息是否成功发送并上屏"):
            logger.info(f"{LogIcon.FIND} 验证消息上屏展示: '{send_content}'")
            sent_message_element = wait.until(
                EC.presence_of_element_located((By.XPATH, f"//*[@text='{send_content}']")),
                message=f"❌ 未在消息列表中检索到发送的消息: {send_content}"
            )
            assert sent_message_element is not None
            logger.info(f"{LogIcon.SUCCESS} [Appium-HarmonyOS-Driver] 消息发送成功并验证通过")


# ==============================================================================
# 测试类二：基于华为官方 Hypium 框架的发送消息测试用例
# ==============================================================================
@allure.epic("IM核心功能测试")
@allure.feature("鸿蒙端框架对比-Huawei-Hypium")
class TestHypiumDriver:
    """
    基于华为官方 Hypium 框架的自动化测试套件。
    驱动链路：Python Client -> UiDriver -> HDC / 设备端 uitest 守护进程。
    使用 Hypium 专有的 BY 选择器与控件操作接口，所有连接参数与生命周期管理均在当前类内部独立维护。
    """

    # 1. 驱动直连与设备配置参数
    DEVICE_SN: str = "3YZ9K25104007630"
    BUNDLE_NAME: str = "com.santiaohms.im"
    ABILITY_NAME: str = "EntryAbility"
    TARGET_SESSION_NAME: str = "测试0222"

    @pytest.fixture(autouse=False)
    def hypium_driver(self):
        """
        初始化与启动 Hypium UiDriver 连接。
        前置：通过 HDC 连接鸿蒙设备并拉起目标应用；后置：释放 UiDriver 连接。
        """
        logger.info(
            f"{LogIcon.SETUP} [Hypium] 正在通过 HDC 建立直连通道，目标设备: {self.DEVICE_SN}"
        )
        driver = UiDriver.connect(connector="hdc", device_sn=self.DEVICE_SN)
        # 拉起目标鸿蒙应用界面
        driver.start_app(self.BUNDLE_NAME, self.ABILITY_NAME)
        driver.wait_for_idle(2000)
        logger.info(f"{LogIcon.SUCCESS} [Hypium] UiDriver 通道就绪并成功启动应用")

        try:
            yield driver
        finally:
            logger.info(f"{LogIcon.SETUP} [Hypium] 正在断开 UiDriver 连接...")
            try:
                driver.close()
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} [Hypium] 断开连接异常: {e}")

    @allure.story("会话消息收发")
    @allure.title("使用华为官方 Hypium 框架在测试0222会话中发送文本消息")
    @pytest.mark.p0
    def test_send_message_via_hypium(self, hypium_driver):
        """
        测试用例：通过 Hypium 原生 UiDriver 与 BY 选择器向指定会话发送消息。
        测试步骤：
        1. 使用 BY.text 查找并点击 '测试0222' 会话；
        2. 使用 BY.type 或 BY.key 定位输入框并调用 input_text；
        3. 使用 BY.text 查找发送按钮并点击；
        4. 断言目标消息文本存在于当前界面。
        """
        send_content = f"Hypium_{int(time.time())}"

        with allure.step(f"1. 查找并点击会话: '{self.TARGET_SESSION_NAME}'"):
            logger.info(
                f"{LogIcon.ACTION} [Hypium] 查找会话控件: {self.TARGET_SESSION_NAME}"
            )
            # 使用 Hypium 原生 BY 选择器
            session_comp = hypium_driver.find_component(
                BY.text(self.TARGET_SESSION_NAME)
            )
            assert session_comp is not None, (
                f"❌ 未找到会话组件: {self.TARGET_SESSION_NAME}"
            )
            hypium_driver.click(session_comp)
            hypium_driver.wait_for_idle(1000)

        with allure.step("2. 定位输入框并输入消息内容"):
            logger.info(f"{LogIcon.ACTION} [Hypium] 写入消息: '{send_content}'")
            # Hypium 支持按组件类型或 key/id 查找组件
            input_comp = hypium_driver.find_component(
                BY.type("RichEditorContent")
            ) or hypium_driver.find_component(BY.type("RichEditor"))
            assert input_comp is not None, "❌ 未找到输入框组件"
            # 开启 paste(True) 剪贴板模式：像安卓一样整串原子性一次填入，避免逐字打字延迟与软键盘频繁拉起
            hypium_driver.input_text(input_comp, send_content, mode=InputTextMode().paste(True))
            hypium_driver.wait_for_idle(300)

        with allure.step("3. 触发发送操作"):
            logger.info(f"{LogIcon.ACTION} [Hypium] 点击发送")
            send_btn = hypium_driver.find_component(BY.text("发送"))
            assert send_btn is not None, "❌ 未找到发送按钮组件"
            hypium_driver.click(send_btn)
            hypium_driver.wait_for_idle(1000)

        with allure.step("4. 校验消息是否成功发送并上屏"):
            logger.info(f"{LogIcon.FIND} [Hypium] 校验消息上屏: '{send_content}'")
            sent_comp = hypium_driver.find_component(BY.text(send_content))
            assert sent_comp is not None, (
                f"❌ 未在界面检索到已发送消息: {send_content}"
            )
            logger.info(f"{LogIcon.SUCCESS} [Hypium] 消息发送成功并验证通过")


# ==============================================================================
# 测试类三：全工程标准框架集成演示 (基于 appium-harmonyos-driver 与 PageObject)
# ==============================================================================
@allure.epic("IM核心功能测试")
@allure.feature("鸿蒙端框架重构-工业级工程化标准接入")
class TestHarmonyAppiumFrameworkIntegration:
    """
    接入项目标准架构的鸿蒙测试用例：
    1. 彻底弃用 hmnextauto 框架与私有 Socket 管道；
    2. 全流程走 DriverFactory -> Appium Server (harmonyos driver) -> 真机/模拟器；
    3. 100% 复用项目标准 PageObject (MainPage, ChatPage) 与跨端定位器 (ChatLocator)；
    4. 天然支持安卓 + 鸿蒙多端跨设备交互用例。
    """

    TARGET_SESSION_NAME: str = "测试0222"

    @allure.story("标准框架-鸿蒙单端文本发送")
    @allure.title("使用项目标准架构向会话发送文本消息 (appium-harmonyos-driver)")
    @pytest.mark.p0
    def test_send_message_via_standard_framework(self, driver_harmony_sender):
        """
        测试用例：通过项目标准 DriverFactory 创建的标准 WebDriver 会话发送消息。
        测试步骤：
        1. 初始化 MainPage，进入指定会话 '测试0222'；
        2. 初始化 ChatPage，调用标准 input_text 输入文本并发送；
        3. 断言发送内容在页面成功上屏。
        """
        from pages.chat.list.chat_list_page import ChatListPage
        from pages.chat.core.chat_page import ChatPage

        chat_list_page = ChatListPage(driver_harmony_sender)
        chat_page = ChatPage(driver_harmony_sender)
        send_content = f"StandardFramework_{int(time.time())}"

        with allure.step(f"1. 检索并点击进入会话: '{self.TARGET_SESSION_NAME}'"):
            chat_list_page.enter_chat(self.TARGET_SESSION_NAME)

        with allure.step("2. 输入文本并点击发送按钮"):
            chat_page.input_text(send_content, fast=True)
            chat_page.click_send_button()

        with allure.step("3. 校验消息是否成功上屏"):
            assert chat_page.is_message_displayed(send_content), f"❌ 消息未成功上屏: {send_content}"
            logger.info(f"{LogIcon.SUCCESS} [Standard Framework] 鸿蒙消息发送并校验成功")

