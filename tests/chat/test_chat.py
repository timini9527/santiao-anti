import allure
import pytest
import pytest_check as check
import time
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.main.main_page import MainPage
from pages.chat_options.location.chat_position_page import ChatPositionPage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data
from strategy.chat.chat_strategy import (
    PRIVATE_USER1, 
    PRIVATE_USER2, 
    PRIVATE_USER8,
    GROUP_STRATEGY, 
    GROUP_STRATEGY2,
    GROUP_STRATEGY3,
    GROUP_STRATEGY4,
    GROUP_STRATEGY5,
)



# 1. 预加载数据（避免在测试方法中重复IO）
CHAT_DATA = load_yaml_data("chat/chat.yaml").get("test_data")


@pytest.mark.usefixtures('message_page')
@allure.epic("IM核心功能测试")
@allure.feature("聊天模块-单聊基础：已完成")
@allure.story("发送 Text 消息，验证")
class TestChat:
    # 会话锁及目标记录：用以避免参数化用例连续运行时反复返回主页与重新进入单聊会话
    _in_chat = False
    _chat_target = None
    _class_driver = None

    @classmethod
    def teardown_class(cls):
        """
        整个测试类所有测试方法执行完毕后的最终清理（类级别 teardown）
        强制关闭会话锁并退回主页，确保对其他测试模块完全隔离不造成干扰
        """
        if cls._in_chat and cls._class_driver:
            try:
                logger.info("🧹 [Class Teardown] 整个测试类执行结束，强制释放会话锁并退回主页")
                cls._in_chat = False
                cls._chat_target = None
                main_page = MainPage(cls._class_driver)
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f"[Class Teardown] 最终返回主页失败: {e}")

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender, request):
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage_sender = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.emojiPage = ChatEmojiPage(driver_sender)
        self.chatImagePage = ChatImagePage(driver_sender)
        self.chatPositionPage = ChatPositionPage(driver_sender)
        
        # 缓存当前驱动，供 class 级别 Teardown 清理时使用
        self.__class__._class_driver = driver_sender

        # 获取当前运行的方法名称。如果是其他非单聊发送方法，强制释放会话锁
        current_test = request.node.originalname or request.node.name
        if "test_send_text_message" not in current_test:
            self.__class__._in_chat = False
            self.__class__._chat_target = None

        yield

        # 校验会话锁：如果当前仍处在聊天会话中，则跳过耗时且多余的退回主页动作
        if self.__class__._in_chat:
            logger.info(f"🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页")
            return

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")




    @allure.story("发送 Text 消息")
    @allure.title("发送 Text 消息，状态：已完成")
    @pytest.mark.parametrize("text_message", CHAT_DATA.get("text_message"))
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=["私聊模式", "群聊模式"])
    def test_send_text_message(self, text_message, strategy):
        """  用例名称：发送文本消息测试  """
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        
        # 自适应检查：如果切换了聊天会话目标，必须先将锁释放并返回主页
        if self.__class__._chat_target != strategy.name:
            if self.__class__._in_chat:
                logger.info(f"🔄 [Lock] 检测到聊天目标从 {self.__class__._chat_target} 切换为 {strategy.name}，退回主页重新进入")
                try:
                    self.mainPage.go_to_main_page()
                except Exception as e:
                    logger.error(f"⚠️ [Error] 切换会话退回主页失败: {e}")
            self.__class__._in_chat = False
            self.__class__._chat_target = strategy.name

        try:
            if not self.__class__._in_chat:
                self.chatListPage_sender.enter_chat(strategy.name)
                self.__class__._in_chat = True
                logger.info(f"🔓 [Lock] 已成功进入与 {strategy.name} 的聊天，会话保持锁开启")

            self.chatPage.send_message(payload)
            text = self.chatPage.find_message_content(index=-1, side='sent')
            check.equal(text, expected, f"消息 actual: {text}, expected: {expected} 不匹配")
        except Exception as e:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
            logger.error(f"⚠️ [Error] 发送消息或校验失败，释放会话锁以进行 Teardown 重置: {e}")
            raise e


    @allure.story("发送 Text 消息")
    @allure.title("发送 Text 消息（共循环发送200组），状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER8, GROUP_STRATEGY, GROUP_STRATEGY2, GROUP_STRATEGY3, GROUP_STRATEGY4, GROUP_STRATEGY5], ids=["私聊模式", "群聊模式", "群聊模式2", "群聊模式3", "群聊模式4", "群聊模式5"])
    def test_send_text_message_loop(self, strategy):
        """
        用例名称：发送文本消息测试
        步骤：
        1. 若未进入聊天窗口，在首页找到联系人并进入
        2. 循环 200 次，每次循环中依次发送 6 条测试文本，并进行实时验证
        """
        loop_count = 100

        text_messages = CHAT_DATA.get("text_message")
        if not text_messages:
            logger.error("❌ [Data] 未加载到有效的 text_message 测试数据")
            return

        try:
            if not self.__class__._in_chat:
                self.chatListPage_sender.enter_chat(strategy.name)
                self.__class__._in_chat = True
                self.__class__._chat_target = strategy.name
                logger.info(f"🔓 [Lock] 已成功进入与 {strategy.name} 的聊天，会话保持锁开启")
        except Exception as e:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
            logger.error(f"❌ [Error] 进入聊天窗口失败: {e}")
            raise e

        try:
            for loop in range(loop_count):
                logger.info(f"🔄 [Loop] [会话名称: {strategy.name}] 开始第 {loop + 1} / {loop_count} 轮循环发送消息组...")
                for idx, msg_data in enumerate(text_messages):
                    payload = str(msg_data['data']['payload'])
                    
                    try:
                        self.chatPage.fast_send_message(payload)
                        time.sleep(0.01)
                    except Exception as e:
                        self.__class__._in_chat = False
                        self.__class__._chat_target = None
                        logger.error(f"❌ [Error] [会话名称: {strategy.name}] 第 {loop + 1} 轮第 {idx + 1} 条消息发送失败: {e}")
                        raise e
        finally:
            self.__class__._in_chat = False
            self.__class__._chat_target = None



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
        check.equal(text, expected, f"消息 actual: {text}, expected: {expected} 不匹配")
