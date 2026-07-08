import pytest
import allure
import pytest_check as check
from core.logger_utils import logger
from pages.system.main.main_page import MainPage
from pages.system.home.home_page import HomePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from strategy.chat.chat_strategy import GROUP_STRATEGY

@allure.epic("IM核心功能测试")
@allure.feature("群助手-进群欢迎语")
class TestGroupBotWelcome:
    """群助手进群欢迎语配置测试"""

    @pytest.fixture(autouse=True)
    def setup_method(self, driver_sender):
        """初始化页面对象"""
        self.main_sender = MainPage(driver_sender)
        self.home_sender = HomePage(driver_sender)
        self.chat_list_sender = ChatListPage(driver_sender)
        self.chat_sender = ChatPage(driver_sender)
        self.group_setting_sender = GroupSettingPage(driver_sender)
        self.group_bot_sender = GroupBotPage(driver_sender)

        self.main_sender.go_to_main_page()
        yield

    @pytest.fixture
    def cleanup_welcome_settings(self):
        """后置清理：清空群欢迎语，恢复初始状态"""
        yield
        logger.info("🧹 [Cleanup] 开始清理进群欢迎语设置...")
        try:
            self.main_sender.go_to_main_page()
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_welcome()
            
            # 清空欢迎语并保存
            self.group_bot_sender.configure_welcome("")
            logger.info("🧹 [Cleanup] 成功清空群助手进群欢迎语")
        except Exception as e:
            logger.warning(f"⚠️ [Cleanup] 清理进群欢迎语发生异常: {e}")

    @allure.story("进群欢迎语-保存与修改状态更新")
    @allure.title("保存进群欢迎语 - 输入带变量的文本并成功保存，校验状态更新-状态：未完成")
    @pytest.mark.usefixtures("cleanup_welcome_settings")
    def test_welcome_message_save_and_edit_status(self):
        """配置非空的进群欢迎语并保存，验证界面入口状态从添加欢迎语变更为修改欢迎语"""
        
        with allure.step("1. 进入群设置 -> 群管理 -> 群助手"):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()

        with allure.step("2. 进入进群欢迎页并输入带变量的文本保存"):
            self.group_bot_sender.enter_welcome()
            welcome_text = "欢迎{@新成员}加入{群名称}！祝生活愉快~"
            self.group_bot_sender.configure_welcome(welcome_text)

        with allure.step("3. 校验状态刷新，群助手管理页展示【修改欢迎语】"):
            # 返回群助手管理页后，验证状态已更新
            # 由于 configure_welcome 保存后会自动返回上一级，我们在当前页判断
            from locators.groups.bot.group_bot_locator import GroupBotLocator
            edit_btn_visible = len(self.group_bot_sender.find_elements(GroupBotLocator.WELCOME_EDIT_BTN, timeout=5))
            check.is_true(edit_btn_visible > 0, "❌ 保存欢迎语后，入口状态未更新为“修改欢迎语”")
