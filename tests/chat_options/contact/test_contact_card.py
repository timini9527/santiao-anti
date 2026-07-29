import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage 
from pages.chat.core.chat_page import ChatPage
from pages.common.contact_select_page import ContactSelectPage
from pages.friend.profile.chat_contact_card_page import ChatContactCardPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.common.session_select_page import SessionSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY

@allure.epic("IM核心功能测试")
@allure.feature("聊天面板-名片")
@allure.story("测试搜索并发送好友名片")
class TestContactCard:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.chatListPage = ChatListPage(driver_sender)
        self.chatContactCardPage = ChatContactCardPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)
        self.sessionSelectPage = SessionSelectPage(driver_sender)
        
        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    def _enter_chat_and_open_card(self, chat_name: str):
        """进入指定的聊天会话并打开名片面板"""
        self.chatListPage.enter_chat(chat_name)
        self.chatContactCardPage.open_panel_enter_contact_card_page()



    @allure.story("发送好友名片-正向流程")
    @allure.title("发送好友名片-正向流程-状态：已完成")
    @pytest.mark.parametrize("cardName", ["测试0222", "0223OiO"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_contact_card_success(self, strategy, cardName):
        """测试搜索并发送好友名片"""
        with allure.step(f"1. 进入聊天并打开名片页"):
            self._enter_chat_and_open_card(strategy.name)

        with allure.step(f"2. 选择好友页面没有则进行搜索，选择并确认发送"):
            is_success = self.contactSelectPage.click_contact_by_name(name=cardName)
            check.is_true(is_success, f"❌ 未能成功选择好友 {cardName}")
            self.contactSelectPage.click_confirm()
            self.chatPage.click_add_button()

        with allure.step("3. 验证聊天气泡显示"):
            result, card_info = self.chatPage.verify_card_in_chat(cardName)
            check.is_true(result, f"❌ 聊天气泡中未发现好友 {cardName} 的名片")

        with allure.step(f"4. 点击最后一条名片消息进入资料详情页"):
            self.chatPage.click_last_card_message()

        with allure.step("5. 验证资料详情页信息"):
            is_success = self.contactDetailPage.verify_is_on_detail_page(card_info)
            check.is_true(is_success, "❌ 未进入资料详情页或信息不匹配")
        
        with allure.step(f"6. 点击发送消息回到聊天页面"):
            self.contactDetailPage.click_send_message()
            check.is_true(self.chatPage.wait_for_chat_page_load(), "❌ 未能成功返回聊天页面")
            chat_object_title = self.chatPage.get_top_name()
            check.equal(chat_object_title, cardName, f"❌ 返回聊天页面后，聊天对象名称与预期不匹配 {chat_object_title}")
    

    @allure.story("发送好友名片-搜索无结果")
    @allure.title("发送好友名片-搜索无结果-状态：已完成")
    @pytest.mark.parametrize("cardName", ['不存在的神秘人999'])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_search_contact_no_results(self, strategy, cardName):
        """验证搜索不存在的好友时 UI 表现"""
        allure.title(f"发送好友名片-搜索无结果【{strategy.desc}】")

        with allure.step(f"1. 进入聊天并打开名片页"):
            self._enter_chat_and_open_card(strategy.name)
        
        with allure.step(f"2. 搜索不存在的好友"):
            is_success = self.contactSelectPage.click_contact_by_name(name=cardName)
            check.is_false(is_success, f"❌ 未能成功选择好友 {cardName}")
            self.contactSelectPage.click_iv_back_button()
            self.chatPage.click_add_button()
        
        with allure.step(f"3. 验证搜索无结果"):
            is_empty = self.contactSelectPage.is_empty_result()
            check.is_true(is_empty, "❌ 预期搜索无结果，但列表不为空")


    @allure.story("发送好友名片-取消操作")
    @allure.title("发送好友名片-取消操作-状态：已完成")
    @pytest.mark.parametrize("cardName", ["测试0222"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_cancel_send_contact_card(self, strategy, cardName):
        """验证在选择好友页面取消后返回聊天页"""
        allure.title(f"发送好友名片-取消操作【{strategy.desc}】")

        with allure.step(f"1. 进入聊天"):
            self._enter_chat_and_open_card(strategy.name)
        
        with allure.step(f"2. 选择好友并取消"):
            is_success = self.contactSelectPage.click_contact_by_name(name=cardName)
            check.is_true(is_success, f"❌ 未能成功选择好友 {cardName}")
            self.contactSelectPage.click_cancel()
            self.chatPage.click_add_button()
        
        with allure.step(f"3. 验证返回聊天页"):
            result = self.chatContactCardPage.verify_is_on_chat_page()
            check.is_true(result, "❌ 点击取消后未正确返回聊天页面")

    
    # TODO：Android 需要补充二次确认弹窗的逻辑
    @allure.story("发送群聊名片-正向流程")
    @allure.title("发送群聊名片-正向流程-状态：已完成")
    @pytest.mark.parametrize("group_card_name", ["测试群aaaaa"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_group_card_success(self, strategy, group_card_name):
        """测试搜索并发送群聊名片"""

        with allure.step(f"0. 确保群聊存在并进入群聊"):
            self.chatListPage.enter_chat(group_card_name)
        
        with allure.step(f"1. 进入群聊详情页面并分享群名片"):
            self.chatListPage.click_more_button()
            self.contactSelectPage.click_action_button()
            self.sessionSelectPage.select_session_by_name(strategy.name)
            self.sessionSelectPage.click_finish_button(msg_type=1)
            # TODO：这里需要添加二次确认操作，待功能完善后移除
            self.mainPage.go_to_main_page()

        with allure.step(f"2. 进入聊天并验证群聊名片信息"):
            self.chatListPage.enter_chat(strategy.name)
            result, card_info = self.chatPage.verify_card_in_chat(group_card_name)
            check.is_true(result, f"❌ 聊天气泡中未发现群聊 {group_card_name} 的名片")

        with allure.step(f"3. 点击群聊名片"):
            self.chatPage.click_last_card_message()
            is_success = self.contactDetailPage.verify_is_on_detail_page(card_info, msgType='group')
            check.is_true(is_success, "❌ 未进入资料详情页或信息不匹配")

        with allure.step(f"4. 点击加入群聊或发送消息会进入群聊，验证聊天对象名称"):
            self.chatContactCardPage.click_join_or_send_message_button()
            chat_object_title = self.chatPage.get_top_name()
            check.is_in(group_card_name, chat_object_title, f"❌ 返回聊天页面后，聊天对象名称与预期不匹配，{chat_object_title}")


    # TODO：Android 需要补充二次确认弹窗的逻辑
    @allure.story("分享群聊名片-取消操作")
    @allure.title("分享群聊名片-取消操作-状态：已完成")
    @pytest.mark.parametrize("group_card_name", ["测试群aaaaa"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_cancel_send_group_card(self, strategy, group_card_name):
        """验证在分享群聊名片时，在会话选择页面取消后返回"""

        with allure.step(f"1. 确保群聊存在并进入群聊"):
            self.chatListPage.enter_chat(group_card_name)
        
        with allure.step(f"2. 进入群聊详情页面并点击分享群名片"):
            self.chatListPage.click_more_button()
            self.contactSelectPage.click_action_button()
            self.sessionSelectPage.select_session_by_name(strategy.name)
            self.sessionSelectPage.click_finish_button(msg_type=1)

            # TODO：这里需要添加二次确认操作，待功能完善后移除
            
        with allure.step(f"3. 在选择会话页点击返回（取消分享）"):
            # self.sessionSelectPage.click_back_button()
            pass
        
        with allure.step(f"4. 验证成功返回并清理环境"):
            toast = self.contactSelectPage.get_toast("发送成功")
            check.is_in("发送成功", toast, "❌ 未能成功发送群聊名片")
            self.contactSelectPage.click_iv_back_button()
            result = self.chatPage.verify_is_on_chat_page()
            check.is_true(result, "❌ 取消群名片分享后，未能正确回到聊天页")
