import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.mine.collection.collection_page import CollectionPage
from pages.mine.collection.chat_collection_page import ChatCollectionPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2
import time

@allure.epic('IM核心功能测试')
@allure.feature('我的收藏-收藏夹双端验证')
class TestCollectionDouble:
    """收藏夹相关功能的双端协同测试（发送端与接收端协同操作）"""

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象并保证双端进入私聊会话"""
        self.mainS = MainPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.collS = CollectionPage(driver_sender)
        self.chatCollS = ChatCollectionPage(driver_sender)
        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.collR = CollectionPage(driver_receiver)
        with allure.step('-> [前置准备] 发送端(Sender)进入接收端聊天室'):
            self.chatListS.enter_chat(PRIVATE_USER1.name)
            self.chatS.wait_for_chat_page_load()
        with allure.step('-> [前置准备] 接收端(Receiver)进入发送端聊天室'):
            self.chatListR.enter_chat(PRIVATE_USER2.name)
            self.chatR.wait_for_chat_page_load()
        yield
        with allure.step('-> [环境清理] 双端退出聊天室并返回首页'):
            try:
                self.mainS.go_to_main_page()
                self.mainR.go_to_main_page()
            except Exception as e:
                logger.warning(f'⚠️ [Cleanup] 双端清理返回首页失败: {e}')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('双端协同-收藏对方发送的消息')
    @allure.title('收藏对方发送的文本消息-双端实时状态校验-状态：已完成')
    def test_collect_received_text_message_double(self):
        """验证接收端发送消息，发送端长按点击收藏，并在我的收藏中成功同步校验"""
        test_msg = f'DoubleCollect_Text_{int(time.time())}'
        with allure.step('1. 接收端(Receiver)向发送端发送一条文本消息'):
            self.chatR.send_message(test_msg)
            self.chatR.wait_banner_message_disappear()
        with allure.step('2. 发送端(Sender)长按接收到的此条消息并执行收藏'):
            elem, text_val = self.collS.get_received_text(index=-1)
            check.equal(text_val, test_msg, f'❌ [Verify] 发送端接收到的最新消息内容不匹配')
            click_time = self.collS.get_first_collection_item(elem)
            toast = self.collS.get_toast(expected_toast='成功')
            check.is_true(toast, f'❌ [Verify] 发送端长按收藏失败')
        with allure.step('3. 发送端(Sender)退回到【我的收藏】页面中进行校验'):
            self.collS.back_to_main()
            self.collS.enter_my_collection()
            details = self.collS.get_collection_details_data(item_type='text', index=0)
            check.is_not_none(details, '❌ [Verify] 我的收藏列表中没有找到文本收藏项')
            actual_text_list = self.collS.get_collection_text_data(index=1)
            check.is_true(len(actual_text_list) > 0, '❌ [Verify] 未能读取到收藏项的文本内容')
            check.equal(actual_text_list[0], test_msg, f'❌ [Verify] 收藏项文本内容与原消息不符')
            check.equal(details['collected_person'], PRIVATE_USER1.name, f'❌ [Verify] 被收藏人姓名不匹配')
            click_dt = self.collS.str_to_dtime(click_time)
            show_dt = self.collS.str_to_dtime(details['collected_time'])
            diff = abs((show_dt - click_dt).total_seconds())
            logger.info(f"⏳ 收藏操作时间: {click_time}, UI显示时间: {details['collected_time']}, 误差: {diff}s")
            check.is_true(diff <= 1.5, f'❌ [Verify] 收藏落库时间误差 {diff}s 超过了 1.5s 限制')
        with allure.step('4. 环境清理：发送端(Sender)删除该条测试产生的收藏记录'):
            self.collS.del_collection_item(del_type='text', index=0)

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('双端协同-从收藏夹中选择并发送消息给对方')
    @allure.title('在会话中发送收藏消息-双端上屏与接收实时校验-状态：已完成')
    def test_send_collection_message_to_friend_double(self):
        """验证发送端从聊天输入扩展面板中，选取我的收藏项发送给接收端，接收端能够成功渲染接收"""
        append_msg = f'附言留言_{int(time.time())}'
        with allure.step('1. 发送端(Sender)打开输入面板并进入收藏选择页'):
            self.chatCollS.open_panel_enter_collection_page()
        with allure.step('2. 发送端选择一条文本收藏项（若为空则跳过）'):
            coll_content = self.chatCollS.select_and_click_collection_item(col_type='text', index=0)
            if not coll_content:
                pytest.skip('⚠️ 发送端账号当前收藏夹中没有文本类型的收藏条目，跳过此测试用例')
            preview_content = self.chatCollS.get_selected_item_panel_content(col_type='text')
            check.equal(preview_content, coll_content, f'❌ [Verify] 弹窗预览文本与列表文本不一致')
        with allure.step('3. 发送端输入附言留言并执行发送'):
            self.chatCollS.send_collection_panel_input(append_msg)
            self.chatCollS.click_send_collection_panel_send()
            self.chatCollS.wait_banner_message_disappear()
        with allure.step('4. 发送端(Sender)和接收端(Receiver)双端实时上屏校验'):
            self.chatListS.click_add_button()
            sender_flag = self.chatCollS.verify_from_collection_message_content(col_type='text', exp_content=coll_content, msg=append_msg)
            check.is_true(sender_flag, '❌ [Verify] 发送端聊天窗口未显示该收藏发送上屏记录')
            receiver_flag = self.chatR.verify_message_displayed(text=coll_content)
            check.is_true(receiver_flag, '❌ [Verify] 接收端聊天窗口没有渲染出发送端发出的收藏条目内容')
            receiver_append_flag = self.chatR.verify_message_displayed(text=append_msg)
            check.is_true(receiver_append_flag, '❌ [Verify] 接收端聊天窗口没有渲染出发送端附带的附言消息')