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
@allure.feature("群助手-禁止发送关键词")
class TestGroupBotKeyword:
    """群助手禁止发送关键词功能测试"""

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
    def cleanup_keyword_settings(self):
        """用例后置清理：确保禁用禁发关键词检测，恢复群聊环境"""
        yield
        logger.info("🧹 [Cleanup] 开始清理群助手禁发关键词设置...")
        try:
            self.main_sender.go_to_main_page()
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_keyword_block()
            
            # 关闭开关并保存
            self.group_bot_sender.toggle_switch(enable=False)
            self.group_bot_sender.click_save()
            logger.info("🧹 [Cleanup] 成功关闭群助手禁发关键词设置")
        except Exception as e:
            logger.warning(f"⚠️ [Cleanup] 清理禁发关键词设置时发生异常: {e}")

    @allure.story("禁发关键词-警告处置方式")
    @allure.title("命中违规关键词 - 触发群助手撤回并群内@警告")
    @pytest.mark.usefixtures("cleanup_keyword_settings")
    def test_group_bot_keyword_warning_flow(self):
        """群普通成员发送包含违规词的消息，消息被撤回且群助手发送警告消息"""
        
        with allure.step("1. 发送方(群主/管理员)进入群助手，配置违规关键词并设置处置方式为【警告】"):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_keyword_block()
            
            # 开启开关
            self.group_bot_sender.toggle_switch(enable=True)
            
            # 配置关键词
            self.group_bot_sender.click_keyword_row()
            self.group_bot_sender.set_keywords(["打折", "发票"])
            
            # 选择警告
            self.group_bot_sender.select_action_rule("警告")
            self.group_bot_sender.click_save()
            
            # 返回聊天界面
            self.group_bot_sender.go_back()  # 从群助手返回群管理
            self.group_bot_sender.go_back()  # 从群管理返回群设置
            self.group_bot_sender.go_back()  # 返回群聊页面

        with allure.step("2. 接收方(普通群成员)进入相同群聊并发送命中关键词的消息"):
            self.chat_list_receiver.enter_chat(GROUP_STRATEGY.name)
            self.chat_receiver.wait_for_chat_page_load()
            self.chat_receiver.send_message("大家想要低价打折商品吗")

        with allure.step("3. 校验消息是否被撤回/拦截，并检查群内是否收到群助手的@警告消息"):
            time.sleep(3)  # 等待机器人处理和撤回
            
            # 接收端检查最后一条消息是否为群助手的警告消息
            # 默认警告文本：“您发送的信息已被撤回 🌟请勿发送与本群无关的内容”
            try:
                last_msg = self.chat_receiver.find_message_content(index=-1, side='received')
                logger.info(f"🔍 接收方最后收到的消息内容: {last_msg}")
                check.is_true("撤回" in last_msg or "无关" in last_msg, f"❌ 未收到群助手的警告消息: {last_msg}")
            except Exception as e:
                logger.warning(f"⚠️ 获取接收方消息时发生错误或未找到: {e}")
                # 尝试用发送端检查
                last_msg_sender = self.chat_sender.find_message_content(index=-1, side='received')
                logger.info(f"🔍 发送方(群主)最后收到的消息内容: {last_msg_sender}")
                check.is_true("撤回" in last_msg_sender or "无关" in last_msg_sender, "❌ 群主未看到群助手的警告消息")

    @allure.story("禁发关键词-功能关闭")
    @allure.title("功能关闭 - 发送关键词不触发拦截")
    def test_group_bot_keyword_disabled_flow(self):
        """群助手禁发关键词功能关闭时，发送关键词消息正常显示且不触发拦截"""
        
        with allure.step("1. 发送方进入群助手，关闭禁发关键词检测功能并保存"):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_keyword_block()
            
            self.group_bot_sender.toggle_switch(enable=False)
            self.group_bot_sender.click_save()
            
            self.group_bot_sender.go_back()
            self.group_bot_sender.go_back()
            self.group_bot_sender.go_back()

        with allure.step("2. 接收方发送包含关键词的消息"):
            self.chat_list_receiver.enter_chat(GROUP_STRATEGY.name)
            self.chat_receiver.wait_for_chat_page_load()
            
            test_msg = "正常咨询打折相关事宜"
            self.chat_receiver.send_message(test_msg)

        with allure.step("3. 发送方和接收方验证该消息正常显示，未被撤回"):
            time.sleep(2)
            # 接收方校验最后一条发送的消息是否还在
            actual_msg = self.chat_receiver.find_message_content(index=-1, side='sent')
            check.equal(actual_msg, test_msg, "❌ 消息被撤回或内容不符")
