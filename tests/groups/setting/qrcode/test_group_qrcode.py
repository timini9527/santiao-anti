import pytest
import allure
import pytest_check as check
from datetime import datetime, timedelta
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.qrcode.group_qrcode_page import GroupQrCodePage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY

@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群二维码")
class TestGroupQrCode:
    """群二维码保存、分享与有效期修改测试"""

    @pytest.fixture(autouse=True)
    def setup_method(self, request, driver_sender):
        """初始化页面对象并在用例结束时自动返回首页"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupQrCodePage = GroupQrCodePage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        
        yield
        
        current_test = request.node.name
        is_validity_test = "test_group_qrcode_change_validity" in current_test
        is_last_validity_branch = "永久" in current_test

        if is_validity_test:
            if is_last_validity_branch:
                logger.info("🧹 [Teardown] 二维码修改最后一个分支执行完毕，开始清理返回主页")
                try:
                    self.mainPage.go_to_main_page()
                    self.__class__._enter_group_setting_state = False
                except Exception as e:
                    logger.error(f"Teardown 失败，未能返回首页: {e}")
            else:
                logger.info("⚡ [Teardown] 二维码修改参数化中间分支，保持当前页面用于复用")
        else:
            try:
                self.mainPage.go_to_main_page()
            except Exception as e:
                logger.error(f"Teardown 失败，未能返回首页: {e}")

    @pytest.fixture
    def restore_qrcode_validity(self):
        """环境强隔离清理：确保不论用例是否执行失败，最终都能将有效期恢复为默认的 7d"""
        yield
        
        try:
            self._ensure_on_qrcode_page()
            current_validity = self.groupQrCodePage.get_validity_text()
            
            now = datetime.now()
            expire_time = now + timedelta(days=7)
            expected_month_day = f"{expire_time.month}月{expire_time.day}日"
            expected_month_day_alt = f"{expire_time.month}月{expire_time.day}日前"
            
            is_7d = (expected_month_day in current_validity) or (expected_month_day_alt in current_validity)
            
            if not is_7d:
                self.groupQrCodePage.click_change_date_row()
                self.groupQrCodePage.select_validity_option('7d')
                logger.info("🧹 [Cleanup] 成功将群二维码有效期恢复为默认的 7天")
        except Exception as e:
            logger.warning(f"⚠️ [Cleanup] 恢复群二维码有效期环境失败: {e}")

    def _enter_group(self):
        """进入群聊"""
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)

    # 用例共享-群聊设置状态
    _enter_group_setting_state = False
    def _enter_group_setting(self):
        """进入群聊设置"""
        if self.__class__._enter_group_setting_state:
            logger.info("群聊设置已进入，无需再次进入")
            return

        with allure.step("1. 进入临时群"):
            self._enter_group()

        with allure.step("2. 进入群设置，并点击群二维码"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_qr_code()
            self.groupQrCodePage.wait_for_qrcode_page_load()
            self.__class__._enter_group_setting_state = True

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

    def _ensure_on_qrcode_page(self):
        """确保当前处于群二维码页面，如不在则重新导航进入"""
        try:
            if self.groupQrCodePage.wait_for_qrcode_page_load(timeout=2):
                return
        except Exception:
            pass

        logger.info("🔄 [Cleanup] 当前不在群二维码页面，正在重新导航进入...")
        self.mainPage.go_to_main_page()
        self._enter_group()
        self.chatPage.click_more_button()
        self.groupSettingPage.wait_for_setting_page_load()
        self.groupSettingPage.click_group_qr_code()
        self.groupQrCodePage.wait_for_qrcode_page_load()

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
            
            # 兼容带前导0与不带前导0的小时格式 (例如 "20:38" 或 "09:30" / "9:30")，并结合分钟误差范围进行匹配
            time_matched = False
            for p_m in possible_minutes:
                pattern1 = f"{hour:02d}:{p_m:02d}"
                pattern2 = f"{hour}:{p_m:02d}"
                if pattern1 in validity_text or pattern2 in validity_text:
                    time_matched = True
                    break
            
            check.is_true(time_matched, f"❌ 时间 '{hour:02d}:{minute:02d}' 不在有效期文案 '{validity_text}' 中")



    @allure.story("群二维码功能")
    @allure.title("保存与分享群二维码功能-状态：已完成")
    @allure.severity("Normal")
    def test_group_qrcode_save_and_share(self):
        with allure.step("1. 进入临时群"):
            self._enter_group()
            group_name = self.chatPage.get_group_name()

        with allure.step("2. 进入群设置，并点击群二维码"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_qr_code()
            self.groupQrCodePage.wait_for_qrcode_page_load()

        with allure.step("3. 校验群二维码页面基础元素渲染是否正确"):
            check.is_true(self.groupQrCodePage.is_qr_card_layout_visible(), "❌ 二维码卡片布局不可见")
            check.is_true(self.groupQrCodePage.is_group_header_visible(), "❌ 群头像未显示")
            check.is_true(self.groupQrCodePage.is_group_code_visible(), "❌ 二维码图片未渲染")
            group_name_on_card = self.groupQrCodePage.get_group_name()
            check.equal(group_name_on_card, group_name, "❌ 二维码卡片上显示的群名称与当前群聊不一致")

        with allure.step("4. 测试保存群二维码到本地"):
            self.groupQrCodePage.click_save_qrcode()
            toast = self.groupQrCodePage.get_toast()
            check.is_in("已保存到相册", toast, "❌ 保存二维码的提示信息有误")
            group_name_after_share = self.groupQrCodePage.get_group_name()
            check.is_in(group_name, group_name_after_share, "❌ 分享群二维码后，群名称不一致")

        with allure.step("5. 测试分享群二维码功能"):
            self.groupQrCodePage.click_share_qrcode()
            self.contactSelectPage.click_contact_by_name(name=GROUP_STRATEGY.name, select_type='share')
            self.contactSelectPage.click_action_button()
            toast = self.groupQrCodePage.get_toast(expected_toast="发送成功")
            check.is_true(toast, "❌ 分享二维码的提示信息有误")
        
        with allure.step("6. 回到消息列表进入群聊"):
            self.mainPage.go_to_main_page()
            self._enter_group()
        
        with allure.step("7. 校验群聊消息列表最后一条消息"):
            self.chatPage.click_image_message_by_index()
            image_data = self.groupQrCodePage.get_image_data()
            check.is_in(group_name, image_data, "❌ 群聊消息列表最后一条消息不是邀请二维码")


    @allure.story("群二维码功能")
    @allure.title("更改群二维码有效期功能-状态：已完成")
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
    @pytest.mark.usefixtures("restore_qrcode_validity")
    def test_group_qrcode_change_validity(self, validity_type, validity_text):
        """测试更改群二维码有效截止日期"""

        with allure.step("1. 进入群聊设置"):
            self._enter_group_setting()

        with allure.step("2. 获取更改前的二维码有效期截止文案（默认为 7 天）"):
            initial_validity_text = self.groupQrCodePage.get_validity_text()
            self._verify_validity_text(validity_type='7d', validity_text=initial_validity_text)

        with allure.step(f"3. 点击修改有效期入口，选择 {validity_text}"):
            self.groupQrCodePage.click_change_date_row()
            self.groupQrCodePage.select_validity_option(validity_type)
            
            validity_text_new = self.groupQrCodePage.get_validity_text()
            self._verify_validity_text(validity_type=validity_type, validity_text=validity_text_new)


    @allure.story("群二维码功能")
    @allure.title("识别过期群二维码失效提示校验-状态：未完成")
    @allure.severity("Critical")
    @pytest.mark.skip(reason="等待后端接口")
    def test_expired_qrcode_tips(self):
        with allure.step("1. 生成并分享一个 30分钟 有效期的群二维码"):
            self._enter_group()
            self.chatPage.click_more_button()
            self.groupSettingPage.click_group_qr_code()
            self.groupQrCodePage.click_change_date_row()
            self.groupQrCodePage.select_validity_option("30m")
            # 记录下二维码的唯一标识 (可以通过 OCR 提取或者从页面元素/API 获取)
            qrcode_text = self.groupQrCodePage.get_validity_text() 
            
        with allure.step("2. 后台篡改数据：将该二维码在数据库中设为过期"):
            # 调用后台测试工具类或数据库连接工具，将该群二维码有效期修改为 1分钟前
            # 例如：db_helper.set_qrcode_expired(group_id)
            pass

        with allure.step("3. 在聊天界面长按识别该二维码"):
            # 返回聊天界面，长按群邀请消息中的二维码
            # click_image_message_by_index() 之后进行长按识别
            # assert toast/弹窗文案为 "该二维码已失效"
            pass





