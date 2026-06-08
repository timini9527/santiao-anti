import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_setting_page import ChatSettingPage
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.chat.chat_long_press_page import ChatLongPressPage
from pages.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY, PRIVATE_USER2, GROUP_STRATEGY2


@allure.epic("IM核心功能测试")
@allure.feature("聊天模块-单聊设置")
class TestChatSetting:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """初始化页面对象，进入单聊并打开设置页"""
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.longPressPage = ChatLongPressPage(driver_sender)

        yield

        # 后置清理：回到主页面，保证环境整洁
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    def _enter_setting(self, name: str):
        """进入好友单聊并打开设置页面"""
        self.chatListPage.enter_chat(name)
        self.chatSettingPage.click_more_button()
        self.chatSettingPage.wait_for_setting_page_load()


    @allure.story("单聊设置 - 获取聊天对象昵称")
    @pytest.mark.parametrize("chat_strategy", [PRIVATE_USER1])
    def test_get_chat_nickname(self, chat_strategy):
        """获取聊天对象的昵称并校验"""
        allure.dynamic.title("获取聊天对象的昵称")

        with allure.step("1、进入单聊并打开设置"):
            self._enter_setting(chat_strategy.name)

        with allure.step("2、获取聊天对象的昵称"):
            nickname = self.chatSettingPage.get_friend_name()
            check.equal(nickname, chat_strategy.name, f"预期昵称应为: {chat_strategy.name}, 实际为: {nickname}")


    @allure.story("单聊设置 - 聊天密码开关")
    @pytest.mark.parametrize("chat_strategy", [PRIVATE_USER1])
    def test_chat_password_switch(self, chat_strategy):
        """切换聊天密码开关并校验状态"""
        allure.dynamic.title("聊天密码开关")

        with allure.step("1、进入单聊并打开设置"):
            self._enter_setting(chat_strategy.name)

        
        with allure.step("2、获取聊天密码开关状态，如果已开启，跳过测试"):
            init_status = self.chatSettingPage.get_switch_chat_pwd_status()
            if str(init_status).lower() == 'true':
                self.chatSettingPage.click_switch_chat_pwd()
                pytest.skip("聊天密码已开启，跳过测试")
            self.chatSettingPage.click_switch_chat_pwd()

        with allure.step("3、回到主页"):
            self.mainPage.go_to_main_page()
            content = self.homePage.get_message_by_name(chat_strategy.name)
            check.is_in("******", content, "❌ 聊天密码未生效，内容未加密")

        with allure.step("4、重新进入单聊输入聊天密码"):
            self.homePage.get_conversation_by_name(chat_strategy.name).click()
            self.homePage.input_chat_password("111111")

        with allure.step("5、获取新的聊天密码开关状态"):
            self.chatSettingPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
            
        with allure.step("6、校验聊天密码状态"):
            new_status = self.chatSettingPage.get_switch_chat_pwd_status()
            check.not_equal(new_status, init_status, "❌ 聊天密码状态未发生切换")
        
        with allure.step("7、点击聊天密码开关恢复原始状态"):
            self.chatSettingPage.click_switch_chat_pwd()
            check.equal(self.chatSettingPage.get_switch_chat_pwd_status(), init_status, "❌ 聊天密码状态未能成功恢复")

    @allure.story("单聊设置 - 截屏通知开关")
    @pytest.mark.parametrize("chat_strategy", [PRIVATE_USER1])
    def test_screenshot_notification_switch(self, chat_strategy):
        """切换截屏通知开关并校验状态"""
        allure.dynamic.title("截屏通知开关")
        
        with allure.step("1、进入单聊并打开设置"):
            self._enter_setting(chat_strategy.name)

        
        with allure.step("2、获取截屏通知开关状态，并确保其为开启状态"):
            init_status = self.chatSettingPage.get_switch_screenshot_status()
            if str(init_status).lower() != 'true':
                self.chatSettingPage.click_switch_screenshot()
            self.chatSettingPage.click_iv_back_button()

 
        with allure.step("3、进行截屏操作"):
            has_notice = self.chatListPage.trigger_system_screenshot()
            check.is_true(has_notice, "❌ 未能在指定时间内捕获到截屏通知")
        
        with allure.step("4、获取截屏通知消息"):
            notice_msg, _ = self.chatListPage.get_withdraw_message()
            check.is_in("您在聊天中截图了", notice_msg, "❌ 截屏通知消息中不包含'您在聊天中截图了'字段")

        with allure.step("5、恢复截屏通知开关的最原始状态，并验证其状态"):
            self.chatSettingPage.click_more_button()
            if str(init_status).lower() == 'false':
                self.chatSettingPage.click_switch_screenshot()
            final_status = self.chatSettingPage.get_switch_screenshot_status()
            check.equal(final_status, init_status, "❌ 恢复原始状态失败")


    @allure.story("单聊设置 - 撤回通知开关")
    @pytest.mark.parametrize("chat_strategy", [PRIVATE_USER1])
    def test_recall_notification_switch(self, chat_strategy):
        """切换撤回通知开关并校验状态"""
        allure.dynamic.title("撤回通知开关")

        with allure.step("1、进入特定好友的单聊会话"):
            self.chatListPage.enter_chat(chat_strategy.name)
        
        with allure.step("1.5、发送一条消息，用于后续验证撤回功能"):
            self.chatListPage.send_message("测试撤回通知功能")
            is_sent = self.chatListPage.wait_for_last_message_send_status()
            check.is_true(is_sent, f"❌ 消息撤回通知功能专项测试：消息未能成功发送上屏 或 发送失败")

        with allure.step("1.6、进入设置页面"):
            self.chatSettingPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()

        with allure.step("2、获取撤回通知开关状态，并确保其为开启状态"):
            init_status = self.chatSettingPage.get_switch_recall_status()
            if str(init_status).lower() != 'true':
                self.chatSettingPage.click_switch_recall()
            self.chatSettingPage.click_iv_back_button()


        with allure.step("3、对最后一条消息长按，点击【撤回】按钮"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("撤回")
            check.is_true(is_ok, "❌ 长按点击【撤回】失败")

        with allure.step("4、获取撤回消息"):
            notice_msg, _ = self.chatListPage.get_withdraw_message()
            check.is_in("撤回了一条消息", notice_msg, "❌ 撤回消息中不包含'撤回了一条消息'字段")
       
        with allure.step("5、恢复撤回通知开关的最原始状态，并验证其状态"):
            self.chatSettingPage.click_more_button()
            if str(init_status).lower() == 'false':
                self.chatSettingPage.click_switch_recall()
            final_status = self.chatSettingPage.get_switch_recall_status()
            check.equal(final_status, init_status, "❌ 恢复原始状态失败")


    @allure.story("单聊设置 - 清空聊天记录")
    @pytest.mark.parametrize("chat_strategy", [PRIVATE_USER2])
    def test_clear_chat_records(self, chat_strategy):
        """点击清空聊天记录"""
        
        with allure.step("1、进入特定好友的单聊会话"):
            self.chatListPage.enter_chat(chat_strategy.name)
            self.chatListPage.send_message("测试清空聊天记录功能")

        with allure.step("1、获取聊天页面消息数量"):
            msg_count = self.chatListPage.get_total_message_count()
            check.is_true(bool(msg_count), "❌ 获取聊天页面消息数量失败")
        
        with allure.step("2、进入设置页面"):
            self.chatSettingPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
                    
        with allure.step("3、清空聊天记录"):
            self.chatSettingPage.click_clear_chat_record()
            self.chatSettingPage.click_two_confirm()
            self.chatSettingPage.click_iv_back_button()
        
        with allure.step("4、获取聊天页面消息数量"):
            new_msg_count = self.chatListPage.get_total_message_count()
            check.equal(new_msg_count, 0, f"❌ 清空聊天记录后，消息数量应为 0，实际为 {new_msg_count}")


        
        
            
