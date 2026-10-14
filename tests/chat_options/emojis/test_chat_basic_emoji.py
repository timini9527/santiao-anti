import allure
import pytest
import pytest_check as check
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from strategy.chat.chat_strategy import PRIVATE_USER1
from pages.main.main_page import MainPage
from core.logger_utils import logger
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage






@allure.epic('IM核心功能测试')
@allure.feature('聊天面板-表情')
@allure.story('基础小表情与最近使用表情')
class TestChatBasicEmoji:

    _chat_target = None

    @pytest.fixture(scope="class", autouse=True)
    def setup_class_teardown(self, driver_sender):
        """
        类级别后置清理：表情模块全部用例执行完毕后，统一执行一次返回主页
        """
        yield
        try:
            self.__class__._chat_target = None
            MainPage(driver_sender).go_to_main_page()
            logger.info("🧹 [Class Teardown] 表情模块全部用例执行完毕，统一返回主页")
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """初始化页面对象"""
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.emojiPage = ChatEmojiPage(driver_sender)

    def _enter_chat_and_open_emoji(self, chat_name: str = PRIVATE_USER1.name):
        """进入指定的聊天会话并打开表情面板（支持同会话直接复用，首次进入后保持在面板内）"""
        if self.__class__._chat_target != chat_name:
            if self.__class__._chat_target is not None:
                logger.info(f"🔄 [Session Switch] 检测到聊天对象从【{self.__class__._chat_target}】切换为【{chat_name}】，退回首页重新进入")
                self.mainPage.go_to_main_page()
            self.chatListPage.enter_chat(chat_name)
            self.__class__._chat_target = chat_name
            self.chatPage.enter_emoji_page()
        else:
            self.chatPage.enter_emoji_page()



    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('发送全部表情消息并验证')
    @allure.title('发送全部表情消息并验证-状态：已完成')
    def test_send_all_emoji_message(self):
        with allure.step('1. 发送全部表情'):
            self._enter_chat_and_open_emoji(PRIVATE_USER1.name)
            self.emojiPage.sent_all_emoji()
            input_text = self.chatPage.get_input_text()
            self.chatPage.click_send_button()
        with allure.step('2. 验证 表情UI显示'):
            active_text = self.chatPage.verify_message_content_by_input(input_text)
            check.equal(active_text, input_text, f'消息 actual: {active_text}, expected: {input_text} 不匹配')


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('发送所有表情中的单个表情消息，验证1，8，当前页面随机一个，当前页面最后一个，最后一个')
    @allure.title('发送所有表情中的单个表情消息，验证1，8，当前页面随机一个，当前页面最后一个，最后一个-状态：已完成')
    @pytest.mark.parametrize('emoji_type, desc', [
        pytest.param('first', '第1个表情', id='第1个表情'), 
        pytest.param('eight', '第8个表情', id='第8个表情'), 
        pytest.param('random', '当前页随机表情', id='当前页随机表情'), 
        pytest.param('current_last', '当前页最后一个表情', id='当前页最后一个表情'), 
        pytest.param('absolute_last', '全部表情最后一个', id='全部表情最后一个')
    ])
    def test_send_single_emoji_message(self, emoji_type, desc):
        allure.dynamic.title(f'发送单个表情 - {desc}')
        with allure.step(f'1. 发送单个表情【{desc}】'):
            self._enter_chat_and_open_emoji(PRIVATE_USER1.name)
            self.chatPage.clear_input_text()
            self.emojiPage.sent_emoji(emoji_type)
            input_text = self.chatPage.get_input_text()
            self.chatPage.click_send_button()
        with allure.step('2. 验证表情UI显示'):
            active_text = self.chatPage.verify_message_content_by_input(input_text)
            check.equal(active_text, input_text, f'消息 actual: {active_text}, expected: {input_text} 不匹配')


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('从所有发送新的表情消息，验证最近使用的表情是否添加上：1/8/16')
    @allure.title('从所有发送新的表情消息，验证最近使用的表情是否添加上：1/8/16-状态：已完成')
    @pytest.mark.parametrize('emoji_type, count, desc', [
        pytest.param('sequential', 1, '发送 1 个表情', id='发送 1 个表情'), 
        pytest.param('sequential', 8, '连续发送 8 个表情', id='连续发送 8 个表情'), 
        pytest.param('random', 3, '随机发送 3 个表情', id='随机发送 3 个表情')
    ])
    def test_send_new_emoji_to_later_message(self, emoji_type, count, desc):
        allure.dynamic.title(f'验证最近使用表情 - {desc}')
        with allure.step(f'1. {desc}'):
            self._enter_chat_and_open_emoji(PRIVATE_USER1.name)
            self.chatPage.clear_input_text()
            self.emojiPage.sent_emoji(emoji_type, count)
            input_text = self.chatPage.get_input_text()
            input_list = self.emojiPage.str_to_emoji_list(input_text)
            self.mainPage.go_to_main_page()
            self.__class__._chat_target = None
        with allure.step(f'2. 验证最近使用的表情是否成功添加了 {count} 个'):
            self._enter_chat_and_open_emoji(PRIVATE_USER1.name)
            self.emojiPage.sent_late_emoji(emoji_type, count)
            input_text_late = self.chatPage.get_input_text()
            input_list_late = self.emojiPage.str_to_emoji_list(input_text_late)
            check.is_true(set(input_list).issubset(set(input_list_late)), f'表情未成功添加到最近使用！发送的: {input_list}, 最近使用点出来的: {input_list_late}')
            self.chatPage.click_send_button()