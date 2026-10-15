import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger, LogIcon
from pages.main.main_page import MainPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from utils.file_reader.data_loader import load_yaml_data
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, PRIVATE_USER3

CHAT_DATA = load_yaml_data('chat/chat.yaml').get('test_data')

# 双端会话目标定义（发送端进入接收端会话，接收端进入发送端会话）
SENDER_TARGET = PRIVATE_USER1.name
RECEIVER_TARGET = PRIVATE_USER3.name


@allure.epic('IM核心功能测试')
@allure.feature('聊天模块-单聊双端协同')
class TestChatDouble:
    """
    单聊核心消息收发双端协同自动化测试集：
    覆盖 A 端（Sender）发送不同类型消息，B 端（Receiver）长连接实时接收与端到端内容闭环校验
    """

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象并确保双端均就绪处于首页"""
        self.mainS = MainPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)

        with allure.step('前置准备：确认双端均安全返回并就绪于首页'):
            for main_page, side_desc in [(self.mainS, '发送端'), (self.mainR, '接收端')]:
                try:
                    main_page.go_to_main_page()
                except Exception as e:
                    logger.warning(f'{LogIcon.ACTION} {side_desc} 返回首页异常: {e}')

        yield

        with allure.step('后置清理：双端安全返回首页'):
            for main_page, side_desc in [(self.mainS, '发送端'), (self.mainR, '接收端')]:
                try:
                    main_page.go_to_main_page()
                except Exception as e:
                    logger.error(f'{LogIcon.FAIL} {side_desc} 清理返回首页失败: {e}')

    def _wait_for_received_message(self, expected_text: str, timeout: int = 8) -> str:
        """
        [工业级探针] 显式智能轮询等待接收端长连接推送并匹配目标消息：
        一旦目标消息渲染就绪立即返回（平均 0.3s~0.8s），彻底杜绝死等与竞态条件
        """
        start_time = time.time()
        last_text = ""
        while time.time() - start_time < timeout:
            last_text = self.chatR.get_text_message_content_by_index(index=-1, side='received', expect_missing=True)
            if last_text == expected_text:
                logger.info(f"{LogIcon.ACTION} [Sync] 接收端在 {time.time() - start_time:.2f}s 内成功捕获目标消息: '{expected_text}'")
                return last_text
            time.sleep(0.3)
        return last_text



    @pytest.mark.p0
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.story('发送和接收 Text 消息')
    @allure.title('单聊双端文本消息发送与实时接收端到端校验')
    @pytest.mark.parametrize(
        'text_message',
        [pytest.param(x, id=f"msg_{x.get('data', {}).get('payload', '')[:8]}") for x in CHAT_DATA.get('text_message', [])]
    )
    def test_send_and_receive_text_message(self, text_message):
        """
        用例名称：单聊文本消息发送与接收端到端全链路闭环测试
        步骤：
        1. 双端分别进入单聊会话并等待页面渲染就绪
        2. 发送端发送文本消息，并校验发送端本地气泡回显
        3. 接收端显式智能轮询捕获长连接下行推送，并断言内容一致性
        """
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        allure.dynamic.title(f"单聊双端收发 - '{payload[:12]}'")

        with allure.step(f"1. 双端分别进入单聊会话并就绪：发送端进入【{SENDER_TARGET}】，接收端进入【{RECEIVER_TARGET}】"):
            self.chatListS.enter_chat(SENDER_TARGET)
            self.chatS.wait_for_chat_page_load()
            self.chatListR.enter_chat(RECEIVER_TARGET)
            self.chatR.wait_for_chat_page_load()

        with allure.step(f"2. 发送端发送文本消息并校验本地回显: '{payload}'"):
            self.chatS.send_message(payload)
            sent_text = self.chatS.get_text_message_content_by_index(index=-1, side='sent')
            check.equal(sent_text, expected, f"❌ 发送端本地气泡回显不匹配！期望: '{expected}', 实际: '{sent_text}'")

        with allure.step("3. 接收端智能等待长连接推送到达，并校验接收消息内容"):
            actual_text = self._wait_for_received_message(expected, timeout=8)
            check.equal(actual_text, expected, f"❌ 接收端消息未能同步或不匹配！期望: '{expected}', 实际: '{actual_text}'")


    # @allure.story('发送和接收 红包 消息')
    # @allure.title('单聊双端红包消息发送与实时接收端到端校验')
    # def test_send_and_receive_redpacket_message(self):
    #     pass
    
    





