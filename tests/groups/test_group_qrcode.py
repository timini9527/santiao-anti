import pytest
import allure
import pytest_check as check
from datetime import datetime, timedelta
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

    def _verify_validity_text(self, validity_type: str, validity_text: str):
        """验证二维码有效期文本是否符合预期"""
        logger.info(f"🔍 验证有效期文本: '{validity_text}', 预期类型: '{validity_type}'")
        if validity_type == 'forever':
            check.is_true("永久" in validity_text, f"❌ 有效期文本 '{validity_text}' 中未包含 '永久'")
            return

        now = datetime.now()
        if validity_type == '30m':
            expire_time = now + timedelta(minutes=30)
        elif validity_type == '2h':
            expire_time = now + timedelta(hours=2)
        elif validity_type == '24h':
            expire_time = now + timedelta(days=1)
        elif validity_type == '7d':
            expire_time = now + timedelta(days=7)
        elif validity_type == '30d':
            expire_time = now + timedelta(days=30)
        elif validity_type == '90d':
            expire_time = now + timedelta(days=90)
        else:
            raise ValueError(f"未知有效期类型: {validity_type}")

        expected_month_day = f"{expire_time.month}月{expire_time.day}日"
        expected_month_day_alt = f"{expire_time.month}月{expire_time.day}日前"
        
        month_day_matched = (expected_month_day in validity_text) or (expected_month_day_alt in validity_text)
        check.is_true(month_day_matched, f"❌ 月份和日期 '{expire_time.month}月{expire_time.day}日' 不在有效期文案 '{validity_text}' 中")

        if validity_type in ['30m', '2h', '24h']:
            hour = expire_time.hour
            minute = expire_time.minute
            
            possible_minutes = [minute, (minute - 1) % 60, (minute + 1) % 60]
            
            # 兼容带前导0与不带前导0的小时格式 (例如 "20:38" 或 "09:30" / "9:30")
            time_matched = False
            for p_m in possible_minutes:
                pattern1 = f"{hour:02d}:{p_m:02d}"
                pattern2 = f"{hour}:{p_m:02d}"
                if pattern1 in validity_text or pattern2 in validity_text:
                    time_matched = True
                    break
            
            check.is_true(time_matched, f"❌ 时间 '{hour:02d}:{minute:02d}' 不在有效期文案 '{validity_text}' 中")

    @allure.story("群二维码功能")
    @allure.title("保存与分享群二维码功能")
    @allure.severity("Normal")
    def test_group_qrcode_save_and_share(self):
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
    @allure.title("更改群二维码有效期功能")
    @allure.severity("Normal")
    @pytest.mark.parametrize("validity_type, validity_text", [
        ('30m', '30分钟'),
        ('2h', '2小时'),
        ('24h', '24小时'),
        ('7d', '7天'),
        ('30d', '30天'),
        ('90d', '90天'),
        ('forever', '永久')
    ], ids=["30分钟", "2小时", "24小时", "7天", "30天", "90天", "永久"])
    def test_group_qrcode_change_validity(self, validity_type, validity_text):
        """测试更改群二维码有效截止日期"""
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

        with allure.step("3. 获取更改前的二维码有效期截止文案（默认为 7 天）"):
            initial_validity_text = self.groupQrCodePage.get_validity_text()
            self._verify_validity_text(validity_type='7d', validity_text=initial_validity_text)

        with allure.step(f"4. 点击修改有效期入口，选择 {validity_text}"):
            self.groupQrCodePage.click_change_date_row()
            self.groupQrCodePage.select_validity_option(validity_type)
            
            validity_text_new = self.groupQrCodePage.get_validity_text()
            self._verify_validity_text(validity_type=validity_type, validity_text=validity_text_new)

        if validity_type != '7d':
            with allure.step("5. 恢复环境：将有效期重新选择为默认的 7天"):
                self.groupQrCodePage.click_change_date_row()
                self.groupQrCodePage.select_validity_option('7d')
                
                validity_text_final = self.groupQrCodePage.get_validity_text()
                self._verify_validity_text(validity_type='7d', validity_text=validity_text_final)


