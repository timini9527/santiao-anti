import pytest
import allure
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.group_setting_page import GroupSettingPage
from pages.groups.setting.group_notice_page import GroupNoticePage
from pages.chat.chat_page import ChatPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY

@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群公告")
class TestGroupNotice:
    """群公告发布与内容测试"""

    @pytest.fixture(autouse=True)
    def setup_class(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupNoticePage = GroupNoticePage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        
        yield
        
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    
    def _enter_group(self):
        """进入群聊"""
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)
        self.chatPage.wait_for_chat_page_load()

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
            self.chatPage.wait_banner_message_disappear()
            self.chatPage.wait_for_chat_page_load()
    

    @allure.story("群公告功能")
    @allure.title("发布新群公告 - 正常发布流程")
    def test_publish_group_notice_success(self):
        """发布新群公告并校验"""
        # with allure.step("-> [前置准备] 创建临时群"):
        #     friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        #     self._create_temp_group(friend_list)

        with allure.step("-> [前置准备] 进入群聊"):
            self._enter_group()

        with allure.step("1. 进入群设置并点击群公告"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_notice()
            self.groupNoticePage.wait_for_notice_page_load()

        with allure.step("2. 输入公告内容并发布"):
            notice_content = "本群为自动化测试临时创建，请勿灌水！"
            self.groupNoticePage.input_notice_content(notice_content)
            self.groupNoticePage.click_publish_btn()

        with allure.step("3. 确认二次弹窗并验证公告内容"):
            self.groupNoticePage.click_confirm()
            # 确认后会留在显示页面，或者返回群设置页面。验证当前显示的公告内容
            current_notice = self.groupNoticePage.get_notice_content()
            check.equal(current_notice, notice_content, "❌ 群公告内容发布后校验不一致")

        with allure.step("4. 退出群设置并回到群聊，验证聊天窗口是否出现公告提示"):
            self.groupNoticePage.click_back_button()
            self.groupSettingPage.click_iv_back_button()
            self.chatPage.wait_for_chat_page_load()
            # 可以在此处增加断言，检查聊天窗口是否有“发布了新公告”等系统消息


    @allure.story("群公告功能")
    @allure.title("发布新群公告 - 取消发布流程")
    def test_publish_group_notice_cancel(self):
        """取消发布群公告"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._create_temp_group(friend_list)

        with allure.step("1. 进入群设置并点击群公告"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_notice()
            self.groupNoticePage.wait_for_notice_page_load()

        with allure.step("2. 输入公告内容，点击发布但取消确认"):
            notice_content = "取消发布公告测试"
            self.groupNoticePage.input_notice_content(notice_content)
            self.groupNoticePage.click_publish_btn()
            self.groupNoticePage.click_cancel()

        with allure.step("3. 验证页面依然留在编辑或未发布状态，返回群设置"):
            # 返回并再次进入群公告，验证内容依然为空或未发布
            self.groupNoticePage.click_back_button()
            self.groupSettingPage.click_group_notice()
            self.groupNoticePage.wait_for_notice_page_load()
            
            current_notice = self.groupNoticePage.get_notice_content()
            check.not_equal(current_notice, notice_content, "❌ 取消发布后群公告仍被发布成功")
