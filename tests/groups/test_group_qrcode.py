import pytest
import allure
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.group_create_page import GroupCreatePage
from pages.groups.group_setting_page import GroupSettingPage
from pages.groups.group_qrcode_page import GroupQrCodePage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY

@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群二维码")
class TestGroupQrCode:
    """群二维码保存、分享与有效期修改测试"""

    @pytest.fixture(autouse=True)
    def setup_class(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupQrCodePage = GroupQrCodePage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        
        yield
        
        # 测试结束后返回首页
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    def _enter_group(self):
        """进入群聊"""
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)

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

    @allure.story("群二维码功能")
    @allure.title("保存与分享群二维码功能校验")
    def test_group_qrcode_save_and_share(self):
        """测试群二维码的保存和分享交互"""
        # friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        # self._create_temp_group(friend_list)

        with allure.step("1. 进入临时群"):
            self._enter_group()
            group_name = self.chatPage.get_group_name()

        with allure.step("2. 进入群设置，并点击群二维码"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_qr_code()
            self.groupQrCodePage.wait_for_qrcode_page_load()

        with allure.step("3. 测试保存群二维码到本地"):
            self.groupQrCodePage.click_save_qrcode()
            toast = self.groupQrCodePage.get_toast()
            check.is_in("已保存到相册", toast, "❌ 保存二维码的提示信息有误")
            group_name_after_share = self.groupQrCodePage.get_group_name()
            check.is_in(group_name, group_name_after_share, "❌ 分享群二维码后，群名称不一致")

        with allure.step("4. 测试分享群二维码功能"):
            self.groupQrCodePage.click_share_qrcode()
            self.contactSelectPage.click_contact_by_name(name=GROUP_STRATEGY.name, select_type='share')
            self.contactSelectPage.click_action_button()
            toast = self.groupQrCodePage.get_toast(expected_toast="发送成功")
            check.is_in("发送成功", toast, "❌ 分享二维码的提示信息有误")
        
        with allure.step("5. 回到消息列表进入群聊"):
            self.mainPage.go_to_main_page()
            self._enter_group()
        
        with allure.step("6. 校验群聊消息列表最后一条消息"):
            self.chatPage.click_image_message_by_index()
            image_data = self.groupQrCodePage.get_image_data()
            check.is_in(group_name, image_data, "❌ 群聊消息列表最后一条消息不是邀请二维码")


    @allure.story("群二维码功能")
    @allure.title("更改群二维码有效期功能校验")
    def test_group_qrcode_change_validity(self):
        """测试更改群二维码有效截止日期"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._create_temp_group(friend_list)

        with allure.step("1. 进入群设置，并点击群二维码"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_qr_code()
            self.groupQrCodePage.wait_for_qrcode_page_load()

        with allure.step("2. 获取更改前的二维码有效期截止文案"):
            initial_validity_text = self.groupQrCodePage.get_validity_text()
            logger.info(f"📅 初始二维码有效期文案为: {initial_validity_text}")

        with allure.step("3. 点击修改有效期入口，选择 30 天"):
            self.groupQrCodePage.click_change_date_row()
            self.groupQrCodePage.select_validity_option("30d")
            
            # 获取最新的有效期文案并验证是否更新
            validity_text_30 = self.groupQrCodePage.get_validity_text()
            logger.info(f"📅 修改为30天后有效期文案为: {validity_text_30}")
            check.not_equal(initial_validity_text, validity_text_30, "❌ 更改为30天有效期后，文案未更新")

        with allure.step("4. 点击修改有效期入口，重新选择为 7 天"):
            self.groupQrCodePage.click_change_date_row()
            self.groupQrCodePage.select_validity_option("7d")
            
            # 获取最新的有效期文案并验证是否恢复/更新
            validity_text_7 = self.groupQrCodePage.get_validity_text()
            logger.info(f"📅 修改为7天后有效期文案为: {validity_text_7}")
            check.not_equal(validity_text_30, validity_text_7, "❌ 更改为7天有效期后，文案未更新")
