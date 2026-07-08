import allure
import pytest
import pytest_check as check

from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.system.main.main_page import MainPage
from pages.chat_options.location.chat_position_page import ChatPositionPage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data



# 1. 预加载数据（避免在测试方法中重复IO）
CHAT_DATA = load_yaml_data("chat/chat.yaml").get("test_data")


@pytest.mark.usefixtures('message_page')
@allure.epic("IM核心功能测试")
@allure.feature("聊天模块-单聊基础：已完成")
@allure.story("发送 Text 消息，验证")
class TestChat:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试类开始前，自动获取 self.collPage 实例并绑定到 self
        这样下面的方法就不需要反复传参了
        """
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage_sender = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.emojiPage = ChatEmojiPage(driver_sender)
        self.chatImagePage = ChatImagePage(driver_sender)
        self.chatPositionPage = ChatPositionPage(driver_sender)
        # self.data = load_yaml_data("chat.yaml").get("test_data")

        yield  # 让出执行权给测试用例

        # 【新增：后置清理逻辑】不管测试成功还是失败，都会执行这里
        try:
            # 尝试返回首页，保证下一个用例的起点是干净的
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")
            # 如果无法正常返回，建议在这里重启 App（ driver.terminate_app() -> launch_app() ）

    """ 执行测试函数前需要构造数据 """

    """ 测试用例执行 """
    @allure.story("发送 Text 消息")
    @allure.title("发送 Text 消息，状态：已完成")
    @pytest.mark.parametrize("text_message", CHAT_DATA.get("text_message"))
    def test_send_text_message(self, text_message):
        """
        用例名称：发送文本消息测试
        步骤：
        1. 在首页找到联系人并进入
        2. 输入文本消息
        3. 点击发送
        4. 验证消息气泡上屏
        """
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        self.chatListPage_sender.enter_chat(PRIVATE_USER1.name)
        self.chatPage.send_message(payload)
        text = self.chatPage.find_message_content(index=-1, side='sent')
        check.equal(text, expected, f"消息 actual: {text}, expected: {expected} 不匹配")

    @allure.story("发送和接收 Text 消息")
    @allure.title("发送和接收 Text 消息，状态：TODO：skip")
    @pytest.mark.skip("暂时跳过，待后续优化")
    @pytest.mark.parametrize("text_message", CHAT_DATA.get("text_message"))
    def test_send_and_receive_text_message(self, text_message, driver_receiver):
        """
        用例名称：发送文本消息测试，接收消息测试
        步骤：
        发送 Text 文本消息，验证端到端测试，用于回归
        """
        self.chatPage_receiver = ChatPage(driver_receiver)
        self.chatListPage_receiver = ChatListPage(driver_receiver)
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        self.chatListPage_sender.enter_chat(PRIVATE_USER1.name)
        self.chatPage.send_message(payload)
        self.chatListPage_receiver.enter_chat(PRIVATE_USER2.name)
        text = self.chatPage_receiver.find_message_content(index=-1, side='received')
        self.chatPage.back()
        self.chatPage_receiver.back()
        #
        check.equal(text, expected, f"消息 actual: {text}, expected: {expected} 不匹配")

    

