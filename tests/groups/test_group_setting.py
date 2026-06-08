import pytest
import allure
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.group_create_page import GroupCreatePage
from pages.groups.group_setting_page import GroupSettingPage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from pages.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2

@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群管理")
class TestGroupSetting:
    """群聊设置/群管理相关测试用例"""

    @pytest.fixture(autouse=True)
    def setup_class(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        
        yield
        
        # 测试结束后返回首页，保证下一个用例有个干净的前置状态
        self.mainPage.go_to_main_page()

    def _create_temp_group(self, friend_list):
        """内部辅助方法：快速创建一个用于测试的临时群聊"""
        with allure.step("-> [前置准备] 在首页发起群聊创建临时群"):
            self.homePage.click_add_button()
            self.homePage.click_start_group_chat()
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()
            
            # 等待进群横幅消失，保证页面稳定
            self.groupCreatePage.wait_banner_message_disappear()
            self.chatPage.wait_for_chat_page_load()

    def _create_group_and_go_to_dismiss(self, friend_list):
        """进入已建临时群并打开解散群聊确认界面"""
        self._create_temp_group(friend_list)
        with allure.step("1. 在群聊聊天页面点击右上角'...' -> 群设置"):
            self.chatPage.click_more_button()
        with allure.step("2. 进入群详情页，进入群管理并点击解散群聊"):
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_manager()
            self.groupSettingPage.click_dismiss_group()

    @allure.story("解散群聊")
    @allure.title("通过群聊聊天页面解散群聊 - 正常解散流程")
    def test_delete_group_success(self):
        allure.dynamic.description(f"通过群聊聊天页面解散群聊")
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        
        self._create_group_and_go_to_dismiss(friend_list)

        with allure.step("3. 确认弹窗"):
            self.groupSettingPage.click_confirm_button()
            toast = self.groupSettingPage.get_toast()
            check.is_in("群不存在", toast, "❌ 解散群聊后未弹出解散成功/群不存在提示")
            
            self.groupSettingPage.click_iv_back_button()
            self.chatPage.click_back_button()
            title = self.homePage.get_top_middle_title()
            check.is_in("三条", title, "❌ 解散群聊后未能返回消息首页")
        
        with allure.step("4. 验证群聊是否已解散"):
            # TODO: 后续可以加入搜索验证或消息列表检查，确保群已被移除
            pass


    @allure.story("解散群聊")
    @allure.title("通过群聊聊天页面解散群聊 - 取消解散流程")
    def test_delete_group_cancel(self):
        allure.dynamic.description(f"通过群聊聊天页面解散群聊")
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        
        self._create_group_and_go_to_dismiss(friend_list)

        with allure.step("3. 取消确认"):
            self.groupSettingPage.click_cancel_button()
            
            # 返回群管理 -> 返回群设置 -> 返回聊天页面
            self.groupSettingPage.click_iv_back_button()
            self.groupSettingPage.click_iv_back_button()
            
            title = self.chatPage.get_top_name()
            group_number = self.groupCreatePage.is_chat_group(title)
            check.is_true(group_number is not False, f"❌ 取消解散后未能正确返回群聊页面")

