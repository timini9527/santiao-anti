import pytest
import allure
import pytest_check as check
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from strategy.chat.chat_strategy import GROUP_STRATEGY

@allure.epic("IM核心功能测试")
@allure.feature("群助手-定时消息")
class TestGroupBotTimedMsg:
    """群助手定时消息生命周期测试"""

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

    @allure.story("定时消息-增删生命周期")
    @allure.title("定时消息周期管理 - 成功添加一条定时消息并成功删除，校验列表刷新")
    def test_timed_msg_lifecycle(self):
        """测试定时消息任务的创建与删除"""
        
        test_content = "自动化测试定时发送的内容"
        
        with allure.step("1. 进入群设置 -> 群管理 -> 群助手 -> 定时消息页"):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_timed_msg()

        with allure.step("2. 添加一条新的定时消息"):
            self.group_bot_sender.add_timed_msg(test_content)
            
            # 验证新增的内容已展示在列表中
            from appium.webdriver.common.appiumby import AppiumBy
            list_item = (AppiumBy.ANDROID_UIAUTOMATOR, f'newUiSelector().textContains("{test_content}")')
            check.is_true(len(self.group_bot_sender.find_elements(list_item, timeout=5)) > 0, "❌ 新增定时消息未在列表中展示")

        with allure.step("3. 删除刚刚添加的定时消息"):
            self.group_bot_sender.delete_timed_msg(test_content)
            
            # 确认列表已不存在该消息
            check.is_true(len(self.group_bot_sender.find_elements(list_item, timeout=3)) == 0, "❌ 删除定时消息后列表中仍存在该内容")
