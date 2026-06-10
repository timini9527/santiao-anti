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

    def _verify_validity_text(self, validity_text: str, validity_type: str):
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

        m = expire_time.strftime("%m")
        d = expire_time.strftime("%d")
        h = expire_time.strftime("%H")
        minute_val = int(expire_time.strftime("%M"))

        # 允许分钟有一分钟左右的执行延迟差
        possible_minutes = [f"{minute_val:02d}", f"{(minute_val - 1) % 60:02d}", f"{(minute_val + 1) % 60:02d}"]

        check.is_in(m, validity_text, f"❌ 月份 '{m}' 不在有效期文案中")
        check.is_in(d, validity_text, f"❌ 日期 '{d}' 不在有效期文案中")
        check.is_in(h, validity_text, f"❌ 小时 '{h}' 不在有效期文案中")
        
        minute_matched = any(p_m in validity_text for p_m in possible_minutes)
        check.is_true(minute_matched, f"❌ 分钟 '{minute_val:02d}' 不在有效期文案中，实际文案: '{validity_text}'")

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
            self._verify_validity_text(initial_validity_text, '7d')

        with allure.step(f"4. 点击修改有效期入口，选择 {validity_text}"):
            self.groupQrCodePage.click_change_date_row()
            self.groupQrCodePage.select_validity_option(validity_type)
            
            # 获取最新的有效期文案并验证
            validity_text_new = self.groupQrCodePage.get_validity_text()
            self._verify_validity_text(validity_text_new, validity_type)

        # 交替切换验证：当前不是 7d 时切换回 7d；如果是 7d 则切换为 30d
        target_toggle_type = '7d' if validity_type != '7d' else '30d'
        target_toggle_text = '7天' if validity_type != '7d' else '30天'

        with allure.step(f"5. 点击修改有效期入口，重新选择为 {target_toggle_text}"):
            self.groupQrCodePage.click_change_date_row()
            self.groupQrCodePage.select_validity_option(target_toggle_type)
            
            # 获取最新的有效期文案并验证是否恢复/更新
            validity_text_final = self.groupQrCodePage.get_validity_text()
            self._verify_validity_text(validity_text_final, target_toggle_type)
