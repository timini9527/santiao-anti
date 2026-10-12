import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from utils.file_reader.data_loader import load_yaml_data, load_csv_data
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY

CHAT_DATA = load_yaml_data('chat/chat.yaml').get('test_data')
CHAT_CSV_DATA = load_csv_data('chat/chat_messages.csv')



@allure.epic('IM核心功能测试')
@allure.feature('聊天模块-文本消息收发')
class TestChat:
    """
    单聊与群聊文本消息发送核心测试集：
    支持会话智能复用、跨会话平滑切换与异常自愈清理
    """
    _in_chat = False
    _chat_target = None
    _class_driver = None

    @classmethod
    def teardown_class(cls):
        """测试类执行结束的兜底清理，确保会话关闭并退回主页"""
        if cls._in_chat and cls._class_driver:
            try:
                logger.info('🧹 [Class Teardown] 测试类结束，释放会话锁并退回主页')
                cls._in_chat = False
                cls._chat_target = None
                MainPage(cls._class_driver).go_to_main_page()
            except Exception as e:
                logger.error(f'[Class Teardown] 返回主页失败: {e}')

    @pytest.fixture(autouse=False)
    def setup(self, driver_sender, message_page, request):
        """轻量级按需初始化与会话生命周期管理"""
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.__class__._class_driver = driver_sender
        yield
        # 针对用例执行失败或会话未锁定的情况，进行故障自愈
        rep_call = getattr(request.node, "rep_call", None)
        if (rep_call and rep_call.failed) or not self.__class__._in_chat:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
            try:
                self.mainPage.go_to_main_page()
            except Exception as e:
                logger.error(f'⚠️ [Teardown] 异常自愈退回首页失败: {e}')
        else:
            logger.info(f'🔒 [Teardown] 会话保持在【{self.__class__._chat_target}】，跳过退回主页')

    def _enter_chat(self, chat_name: str) -> None:
        """进入指定的聊天会话（支持同会话直接复用，跨会话自动退回主页重新进入）"""
        if self.__class__._chat_target != chat_name:
            if self.__class__._in_chat:
                logger.info(f'🔄 [Lock] 会话切换: {self.__class__._chat_target} -> {chat_name}，退回主页重新进入')
                try:
                    self.mainPage.go_to_main_page()
                except Exception as e:
                    logger.error(f'⚠️ [Error] 切换会话退回主页失败: {e}')
            self.__class__._in_chat = False
            self.__class__._chat_target = chat_name

        if not self.__class__._in_chat:
            self.chatListPage.enter_chat(chat_name)
            self.__class__._in_chat = True
            logger.info(f'🔓 [Lock] 已成功进入与【{chat_name}】的会话，开启会话保持锁')

    def _reenter_chat(self, chat_name: str) -> None:
        """重新进入当前会话：用于大批量消息发送后刷新视口并强制锚定至最新消息底部"""
        logger.info(f"🔄 [Re-enter] 重新进入与【{chat_name}】的会话以刷新最新消息视口...")
        self.mainPage.go_to_main_page()
        self.__class__._in_chat = False
        self._enter_chat(chat_name)



    @allure.story('发送基础 Text 消息')
    @pytest.mark.parametrize(
        'text_message',
        [pytest.param(x, id=f"msg_{x.get('data', {}).get('payload', '')[:8]}") for x in CHAT_DATA.get('text_message', [])]
    )
    @pytest.mark.parametrize(
        'strategy',
        [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')]
    )
    def test_send_text_message(self, text_message, strategy, setup):
        """验证单条文本消息发送与回显一致性（支持单聊/群聊）"""
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        allure.dynamic.title(f"发送文本消息 [{strategy.desc}] - {payload[:15]}")

        with allure.step(f"1. 进入与【{strategy.name}】的聊天会话"):
            self._enter_chat(strategy.name)

        with allure.step(f"2. 发送文本消息: '{payload}'"):
            self.chatPage.send_message(payload)

        with allure.step("3. 校验最新发送消息回显内容"):
            actual_text = self.chatPage.get_text_message_content_by_index(index=-1, side='sent')
            check.equal(actual_text, expected, f"❌ 消息回显不匹配！期望: '{expected}', 实际: '{actual_text}'")


    @allure.story('批量发送 CSV 数据集')
    @allure.title('批量极速发送 CSV 文本数据集前 50 条并校验闭环')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_send_text_message_multiple(self, strategy, setup):
        """基于 CSV 聊天测试数据集批量连续发送前 50 条文本消息，验证批量吞吐与最终落盘一致性"""
        assert CHAT_CSV_DATA, "❌ 未加载到 CSV 聊天测试数据集，请检查 chat/chat_messages.csv"

        with allure.step(f"1. 进入与【{strategy.name}】的聊天会话"):
            self._enter_chat(strategy.name)

        with allure.step("2. 批量极速发送 CSV 数据集前 50 条文本消息"):
            target_data = CHAT_CSV_DATA[:50]
            payloads = [
                f"[{msg_item.get('case_id', f'MSG_CASE_{idx+1:04d}')}] {str(msg_item.get('context', ''))}"
                for idx, msg_item in enumerate(target_data)
            ]
            self.chatPage.send_messages_batch(payloads, interval=0.1)

        with allure.step("3. 校验批量发送闭环：重新进入会话锚定最新消息并验证回显"):
            self._reenter_chat(strategy.name)
            last_payload = payloads[-1]
            actual_text = self.chatPage.get_text_message_content_by_index(index=-1, side='sent')
            check.equal(actual_text, last_payload, f"❌ 最新一条消息内容不匹配！期望: '{last_payload}', 实际: '{actual_text}'")