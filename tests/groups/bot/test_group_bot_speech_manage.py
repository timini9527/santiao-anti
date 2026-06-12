import pytest
import allure
import time
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
@allure.feature("群助手-发言管理")
class TestGroupBotSpeechManage:
    """群助手发言管理功能测试"""

    @pytest.fixture(autouse=True)
    def setup_method(self, driver_sender, driver_receiver):
        """初始化发送方和接收方的页面对象"""
        self.main_sender = MainPage(driver_sender)
        self.home_sender = HomePage(driver_sender)
        self.chat_list_sender = ChatListPage(driver_sender)
        self.chat_sender = ChatPage(driver_sender)
        self.group_setting_sender = GroupSettingPage(driver_sender)
        self.group_bot_sender = GroupBotPage(driver_sender)

        self.main_receiver = MainPage(driver_receiver)
        self.home_receiver = HomePage(driver_receiver)
        self.chat_list_receiver = ChatListPage(driver_receiver)
        self.chat_receiver = ChatPage(driver_receiver)

        # 确保双端都处于聊天列表主页
        self.main_sender.go_to_main_page()
        self.main_receiver.go_to_main_page()
        yield

    @pytest.fixture
    def cleanup_speech_settings(self):
        """用例后置清理：确保禁用发言管理，恢复群聊环境"""
        yield
        logger.info("🧹 [Cleanup] 开始清理群助手发言管理设置...")
        try:
            self.main_sender.go_to_main_page()
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_speech_manage()
            
            # 关闭开关并保存
            self.group_bot_sender.toggle_switch(enable=False)
            self.group_bot_sender.click_save()
            logger.info("🧹 [Cleanup] 成功关闭群助手发言管理设置")
        except Exception as e:
            logger.warning(f"⚠️ [Cleanup] 清理发言管理设置时发生异常: {e}")

    @allure.story("发言管理-限制发送文件")
    @allure.title("限制文件发送 - 普通成员发送文件触发拦截提示")
    @pytest.mark.usefixtures("cleanup_speech_settings")
    def test_group_bot_limit_file_flow(self):
        """管理员开启禁止发送文件限制，普通成员尝试发送文件被拦截并弹出Toast提示"""
        
        with allure.step("1. 发送方(群主/管理员)进入群助手，开启发言管理，勾选【文件】限制并保存"):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_speech_manage()
            
            # 开启总开关
            self.group_bot_sender.toggle_switch(enable=True)
            
            # 勾选文件限制
            self.group_bot_sender.toggle_limit_item("文件", enable=True)
            self.group_bot_sender.click_save()
            
            # 返回聊天界面
            self.group_bot_sender.go_back()
            self.group_bot_sender.go_back()
            self.group_bot_sender.go_back()

        with allure.step("2. 接收方(普通成员)在相同群聊中尝试点击文件发送功能"):
            self.chat_list_receiver.enter_chat(GROUP_STRATEGY.name)
            self.chat_receiver.wait_for_chat_page_load()
            
            # 点击聊天页的“+”更多面板
            self.chat_receiver.click_add_button()
            time.sleep(0.5)
            # 点击【文件】选项
            # 由于在 chat_page 中可能有一些通用组件，直接模拟点击
            file_btn_locator = (self.chat_receiver.by.ANDROID_UIAUTOMATOR, 'newUiSelector().text("文件")')
            self.chat_receiver.click(file_btn_locator)

        with allure.step("3. 校验是否出现拦截 Toast 提示: '本群已开启禁止发送文件'"):
            toast_text = self.chat_receiver.get_toast_text()
            logger.info(f"🔍 捕获到拦截提示: '{toast_text}'")
            check.is_true("禁止发送文件" in toast_text, f"❌ 未捕获到正确的禁止文件发送提示，实际Toast: '{toast_text}'")

    @allure.story("发言管理-限制转发消息")
    @allure.title("限制转发 - 普通成员长按群消息转发被禁止")
    @pytest.mark.usefixtures("cleanup_speech_settings")
    def test_group_bot_limit_forward_flow(self):
        """管理员开启禁止转发限制，普通成员长按消息尝试转发被禁止"""
        
        with allure.step("1. 发送方配置发言管理，勾选【禁止转发】限制并保存"):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_speech_manage()
            
            self.group_bot_sender.toggle_switch(enable=True)
            self.group_bot_sender.toggle_limit_item("禁止转发", enable=True)
            self.group_bot_sender.click_save()
            
            self.group_bot_sender.go_back()
            self.group_bot_sender.go_back()
            self.group_bot_sender.go_back()

        with allure.step("2. 接收方在群聊中尝试长按最新消息并点击【转发】"):
            self.chat_list_receiver.enter_chat(GROUP_STRATEGY.name)
            self.chat_receiver.wait_for_chat_page_load()
            
            # 发送一条普通消息用于长按
            self.chat_receiver.send_message("这是一条待转发的测试消息")
            time.sleep(1)
            
            # 长按该消息
            text_items = self.chat_receiver.get_message_elements(msg_type="text", side='sent')
            if text_items:
                self.chat_receiver.long_press(text_items[-1])
                time.sleep(1)
                
                # 点击菜单中的【转发】选项
                forward_menu_item = (self.chat_receiver.by.ANDROID_UIAUTOMATOR, 'newUiSelector().text("转发")')
                self.chat_receiver.click(forward_menu_item)
            else:
                pytest.fail("❌ 未能在聊天窗口中找到可长按的消息")

        with allure.step("3. 校验是否出现拦截提示: '本群已开启禁止转发群内消息'"):
            toast_text = self.chat_receiver.get_toast_text()
            logger.info(f"🔍 捕获到拦截提示: '{toast_text}'")
            check.is_true("禁止转发" in toast_text, f"❌ 未捕获到正确的禁止转发提示，实际Toast: '{toast_text}'")
