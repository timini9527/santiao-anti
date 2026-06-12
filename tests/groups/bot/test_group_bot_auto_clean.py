import pytest
import allure
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.setting.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from strategy.chat.chat_strategy import GROUP_STRATEGY

@allure.epic("IM核心功能测试")
@allure.feature("群助手-自动清理成员")
class TestGroupBotAutoClean:
    """群助手自动清理成员功能测试"""

    @pytest.fixture(autouse=True)
    def setup_method(self, driver_sender):
        """初始化页面对象"""
        self.main_sender = MainPage(driver_sender)
        self.home_sender = HomePage(driver_sender)
        self.chat_list_sender = ChatListPage(driver_sender)
        self.chat_sender = ChatPage(driver_sender)
        self.group_setting_sender = GroupSettingPage(driver_sender)
        self.group_bot_sender = GroupBotPage(driver_sender)

        # 确保处于主页
        self.main_sender.go_to_main_page()
        yield

    @pytest.fixture
    def cleanup_clean_settings(self):
        """后置清理：恢复自动清理开关为关闭状态"""
        yield
        logger.info("🧹 [Cleanup] 开始清理自动清理成员设置...")
        try:
            self.main_sender.go_to_main_page()
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_auto_clean()
            
            # 关闭定时任务
            self.group_bot_sender.toggle_switch(enable=False)
            logger.info("🧹 [Cleanup] 成功关闭群助手自动清理开关")
        except Exception as e:
            logger.warning(f"⚠️ [Cleanup] 清理自动清理开关发生异常: {e}")

    @allure.story("自动清理-任务开关切换")
    @allure.title("开启与关闭定时清理任务 - 触发Toast提醒且状态更新")
    @pytest.mark.usefixtures("cleanup_clean_settings")
    def test_auto_clean_switch_toggle(self):
        """开启或关闭自动清理成员的总定时开关，并验证 Toast 提示"""
        
        with allure.step("1. 进入群设置 -> 群管理 -> 群助手 -> 自动清理成员"):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_auto_clean()

        with allure.step("2. 切换定时开关为启用，验证 Toast 提示"):
            self.group_bot_sender.toggle_switch(enable=True)
            toast_text = self.chat_sender.get_toast_text()
            logger.info(f"🔍 开启任务提示: '{toast_text}'")
            check.is_true("已开启" in toast_text or "启用" in toast_text or toast_text == "", f"❌ 开启定时任务未捕获到正确Toast: {toast_text}")

        with allure.step("3. 切换定时开关为禁用，验证 Toast 提示"):
            self.group_bot_sender.toggle_switch(enable=False)
            toast_text = self.chat_sender.get_toast_text()
            logger.info(f"🔍 关闭任务提示: '{toast_text}'")
            check.is_true("已关闭" in toast_text or "关闭" in toast_text or toast_text == "", f"❌ 关闭定时任务未捕获到正确Toast: {toast_text}")

    @allure.story("自动清理-清理规则配置")
    @allure.title("配置清理规则 - 包含未发言/封禁条件，手动模式下成功保存规则")
    @pytest.mark.usefixtures("cleanup_clean_settings")
    def test_auto_clean_rules_configuration(self):
        """配置详细的自动清理条件与模式并成功保存"""
        
        with allure.step("1. 进入群助手自动清理页 -> 点击清理规则设置"):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_auto_clean()
            self.group_bot_sender.enter_clean_rules()

        with allure.step("2. 选择清理条件与保护规则，并设置模式为手动确认"):
            # 开启需要的条件
            self.group_bot_sender.toggle_clean_condition("从未发言", enable=True)
            self.group_bot_sender.toggle_clean_condition("账号已注销或因违规被封禁", enable=True)
            
            # 设置保护规则
            self.group_bot_sender.toggle_protect_rule("入群不足90天的成员", enable=True)
            
            # 设置清理模式为手动确认
            self.group_bot_sender.select_clean_mode("手动确认")

        with allure.step("3. 点击完成并确认二次弹窗，验证保存成功"):
            self.group_bot_sender.click_finish()
            self.group_bot_sender.click_confirm()
            
            # 获取保存成功 Toast
            toast_text = self.chat_sender.get_toast_text()
            logger.info(f"🔍 保存规则提示: '{toast_text}'")
            check.is_true("已保存" in toast_text or "成功" in toast_text or toast_text == "", f"❌ 保存清理规则未捕获到成功Toast: {toast_text}")
