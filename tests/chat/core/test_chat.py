import time
import allure
import pytest
import pytest_check as check
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.main.main_page import MainPage
from pages.chat_options.location.chat_position_page import ChatPositionPage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data, load_csv_data
from strategy.chat.chat_strategy import (
    PRIVATE_USER1,
    PRIVATE_USER2,
    GROUP_STRATEGY,
)



CHAT_DATA = load_yaml_data('chat/chat.yaml').get('test_data')
CHAT_CSV_DATA = load_csv_data('chat/chat_messages.csv')



@allure.epic('IM核心功能测试')
@allure.feature('聊天模块-单聊基础：已完成')
@allure.story('发送 Text 消息，验证')
class TestChat:
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
                logger.info('🧹 [Class Teardown] 整个测试类执行结束，强制释放会话锁并退回主页')
                cls._in_chat = False
                cls._chat_target = None
                main_page = MainPage(cls._class_driver)
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f'[Class Teardown] 最终返回主页失败: {e}')

    @pytest.fixture(autouse=False)
    def setup(self, driver_sender, message_page, request):
        """仅用于 test_send_text_message 的专属前置初始化"""
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage_sender = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.emojiPage = ChatEmojiPage(driver_sender)
        self.chatImagePage = ChatImagePage(driver_sender)
        self.chatPositionPage = ChatPositionPage(driver_sender)
        self.__class__._class_driver = driver_sender
        yield
        if self.__class__._in_chat:
            logger.info(f'🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页')
            return
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f'Teardown 失败，未能返回首页: {e}')

    def _enter_chat(self, chat_name: str):
        """进入指定的聊天会话（支持同会话直接复用，跨会话自动退回主页重新进入）"""
        if self.__class__._chat_target != chat_name:
            if self.__class__._in_chat:
                logger.info(f'🔄 [Lock] 检测到聊天目标从 {self.__class__._chat_target} 切换为 {chat_name}，退回主页重新进入')
                try:
                    self.mainPage.go_to_main_page()
                except Exception as e:
                    logger.error(f'⚠️ [Error] 切换会话退回主页失败: {e}')
            self.__class__._in_chat = False
            self.__class__._chat_target = chat_name
        if not self.__class__._in_chat:
            self.chatListPage_sender.enter_chat(chat_name)
            self.__class__._in_chat = True
            logger.info(f'🔓 [Lock] 已成功进入与 {chat_name} 的聊天，会话保持锁开启')




    @allure.story('发送 Text 消息')
    @allure.title('发送 Text 消息，状态：已完成')
    @pytest.mark.parametrize('text_message', [pytest.param(x, id=str(x)) for x in CHAT_DATA.get('text_message')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_send_text_message(self, text_message, strategy, setup):
        """  用例名称：发送文本消息测试  """
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        try:
            with allure.step(f"1. 进入与【{strategy.name}】的聊天会话"):
                self._enter_chat(strategy.name)
            with allure.step(f"2. 发送文本消息"):
                self.chatPage.send_message(payload)
            with allure.step("3. 校验消息回显内容"):
                text = self.chatPage.get_text_message_content_by_index(index=-1, side='sent')
                check.equal(text, expected, f'消息 actual: {text}, expected: {expected} 不匹配')
        except Exception as e:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
            logger.error(f'⚠️ [Error] 发送消息或校验失败，释放会话锁以进行 Teardown 重置: {e}')
            raise e


    @allure.story('发送 CSV Text 消息')
    @allure.title('基于 CSV 数据集批量连续发送文本消息-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_send_text_message_multiple(self, strategy, setup):
        """用例名称：基于 CSV 数据集批量连续发送文本消息（单条用例展示，内容附带 Case ID）"""
        try:
            with allure.step(f"1. 进入与【{strategy.name}】的聊天会话"):
                self._enter_chat(strategy.name)

            with allure.step(f"2. 极速批量发送 CSV 中的文本消息集（共 {len(CHAT_CSV_DATA)} 条，内容携带 ID）"):
                payloads = [
                    f"[{msg_item.get('case_id', f'MSG_CASE_{idx+1:04d}')}] {str(msg_item.get('context', ''))}"
                    for idx, msg_item in enumerate(CHAT_CSV_DATA)
                ]
                self.chatPage.send_messages_batch(payloads, interval=0.4)
        except Exception as e:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
            logger.error(f'⚠️ [Error] 发送消息或校验失败，释放会话锁以进行 Teardown 重置: {e}')
            raise e






    @allure.story('发送和接收 Text 消息')
    @allure.title('发送和接收 Text 消息，状态：TODO：skip')
    @pytest.mark.skip('暂时跳过，待后续优化')
    @pytest.mark.parametrize('text_message', [pytest.param(x, id=str(x)) for x in CHAT_DATA.get('text_message')])
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
        text = self.chatPage_receiver.get_text_message_content_by_index(index=-1, side='received')
        self.chatPage.back()
        self.chatPage_receiver.back()
        check.equal(text, expected, f'消息 actual: {text}, expected: {expected} 不匹配')