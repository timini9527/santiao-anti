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
from locators.chat.chat_locator import ChatLocator
from strategy.chat.chat_strategy import GROUP_STRATEGY


@allure.epic("IM核心功能测试")
@allure.feature("群助手-群内禁言关键词-双端交互与拦截规则")
class TestGroupBotInteraction:
    """群助手涉及到多端交互的功能测试"""

    @pytest.fixture(autouse=True)
    def setup_method(self, driver_sender, driver_receiver):
        """同时初始化发送方和接收方的页面对象"""
        # 发送方 (群主)
        self.mainS = MainPage(driver_sender)
        self.homeS = HomePage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.settingS = GroupSettingPage(driver_sender)
        self.botS = GroupBotPage(driver_sender)
        
        # 接收方 (普通群成员)
        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)

        yield
        
        self.mainS.go_to_main_page()
        self.mainR.go_to_main_page()

    def _enter_keyword_config_page(self):
        """进入关键词配置列表（辅助方法）"""
        logger.info("⏳ [Pre-condition] 进入关键词配置列表")
        self.chatListS.enter_chat(GROUP_STRATEGY.name)
        self.chatS.wait_for_chat_page_load()
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        self.settingS.click_friend_header()
        self.botS.wait_for_group_bot_page_load()
        self.botS.enter_keyword_block()
        self.botS.toggle_switch(enable=True)
        
    def _exit_keyword_config_page(self):
        """退出关键词配置列表，返回到群聊界面（辅助方法）"""
        logger.info("⏳ [Post-condition] 退出群助手配置，返回群聊")
        self.botS.click_back()  
        self.botS.click_back() 
        self.botS.click_back() 


    @allure.story("禁发关键词-警告处置方式")
    @allure.title("命中违规关键词 - 触发群助手撤回并群内@警告")
    def test_group_bot_keyword_warning_flow(self):
        """群普通成员发送命中违规词的消息，消息被撤回且群助手发送@警告消息"""

        with allure.step("1. 发送方(群主/管理员)进入群助手，配置违规关键词并设置处置方式为【警告】"):
            self._enter_keyword_config_page()
            self.botS.click_keyword_row()
            self.botS.click_keyword_add_btn() # TODO: 这里有问题待修复
            self.botS.set_keywords(["红包", "银行卡", "转账"])
            self.botS.save_keywords_config()
            self.botS.select_action_rule("警告")
            self.botS.click_save()
            self._exit_keyword_config_page()

        with allure.step("2. 接收方(普通群成员)进入相同群聊并发送命中关键词的消息"):
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()
            self.chatR.send_message("大家加我微信发红包啦")

        with allure.step("3. 校验原消息被群助手撤回（系统撤回提示出现）"):
            withdraw_result = self.chatR.get_withdraw_message()
            check.is_not_none(withdraw_result, "❌ 未检测到任何撤回提示")
            if withdraw_result:
                withdraw_msg, _ = withdraw_result
                check.is_true("撤回" in withdraw_msg, f"❌ 撤回提示内容不正确: {withdraw_msg}")

        with allure.step("4. 校验群内收到群助手的@警告消息"):
            warned_msg = self.chatR.get_text_message_content_by_index(index=-1, side="all")
            check.is_true("@" in warned_msg, "❌ 未检测到群助手发送的 @ 警告消息")
