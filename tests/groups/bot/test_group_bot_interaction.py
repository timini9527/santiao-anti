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

    @staticmethod
    def _navigate_to_keyword_block(driver):
        """从主流程导航进入群助手【关键词】配置页（class fixture 专用，不依赖 self）

        方法内自带回主页步骤，调用时无需关心当前停留在哪个页面。
        """
        mainS = MainPage(driver)
        chatListS = ChatListPage(driver)
        chatS = ChatPage(driver)
        settingS = GroupSettingPage(driver)
        botS = GroupBotPage(driver)

        mainS.go_to_main_page()
        chatListS.enter_chat(GROUP_STRATEGY.name)
        chatS.wait_for_chat_page_load()
        chatS.click_more_button()
        settingS.wait_for_setting_page_load()
        settingS.click_friend_header()
        botS.wait_for_group_bot_page_load()
        botS.enter_keyword_block()
        return botS

    @pytest.fixture(scope="class", autouse=True)
    def setup_keyword_config(self, driver_sender):
        """整个测试类只执行一次：开启开关并配置违规关键词列表。

        处置方式（警告/禁言/移除群聊/仅撤回）不在此设置，由各参数化用例
        自行通过 _set_action_rule 切换，因此这里只负责关键词与开关这类
        所有用例共用的前置。driver 为 session 级别，配置后持久生效。
        class 级 fixture 早于 function 级 setup_method 运行，无法复用 self.botS，
        因此基于 driver_sender 创建临时页面对象完成配置与清理。
        """
        logger.info("⏳ [Class Setup] 进入群助手，开启开关并配置违规关键词列表")
        botS = self._navigate_to_keyword_block(driver_sender)
        botS.toggle_switch(enable=True)
        botS.click_keyword_row()
        botS.click_keyword_add_btn()  # TODO: 这里有问题待修复
        botS.set_keywords(["红包", "银行卡", "转账"])
        botS.save_keywords_config()
        botS.click_back()
        botS.click_back()
        botS.click_back()

        yield

        logger.info("⏳ [Class Teardown] 清空关键词并关闭开关，恢复环境")
        botS = self._navigate_to_keyword_block(driver_sender)
        botS.click_keyword_row()
        botS.clear_all_keywords()
        botS.click_back()
        botS.toggle_switch(enable=False)
        botS.click_back()
        botS.click_back()

    def _set_action_rule(self, rule_name: str):
        """进入群助手关键词配置页，将处置方式切换为指定规则后保存退出。

        关键词列表与开关已由 class 级 fixture 配好，这里只切换处置规则。
        """
        logger.info(f"⏳ [Pre-condition] 设置关键词处置方式为【{rule_name}】")
        botS = self._navigate_to_keyword_block(self.botS.driver)
        botS.select_action_rule(rule_name)
        botS.click_save()
        botS.click_back()
        botS.click_back()
        botS.click_back()

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

    def _trigger_and_assert_withdraw(self):
        """接收方发送命中关键词的消息，并校验原消息被群助手撤回。

        返回 None；撤回校验失败时通过 pytest_check 记录软断言。
        各处置方式用例共用此前置：先切到群聊发消息，再验证撤回提示。
        """
        with allure.step("接收方(普通群成员)进入群聊并发送命中关键词的消息"):
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()
            self.chatR.send_message("大家加我微信发红包啦")

        with allure.step("校验原消息被群助手撤回（系统撤回提示出现）"):
            withdraw_result = self.chatR.get_withdraw_message()
            check.is_not_none(withdraw_result, "❌ 未检测到任何撤回提示")
            if withdraw_result:
                withdraw_msg, _ = withdraw_result
                check.is_true("撤回" in withdraw_msg, f"❌ 撤回提示内容不正确: {withdraw_msg}")

    @allure.story("禁发关键词-仅撤回处置方式")
    @allure.title("命中违规关键词 - 触发群助手仅撤回")
    def test_keyword_action_revoke(self):
        """处置方式为【仅撤回】：命中关键词的消息被撤回，群内无额外提示消息。"""
        with allure.step("1. 设置处置方式为【仅撤回】"):
            self._set_action_rule("仅撤回")

        self._trigger_and_assert_withdraw()

        with allure.step("3. 校验群内未出现 @ 警告消息（仅撤回不发警告）"):
            last_msg = self.chatR.get_text_message_content_by_index(index=-1, side="all")
            check.is_false("@" in last_msg, f"❌ 仅撤回模式不应出现 @ 警告消息: {last_msg}")

    @allure.story("禁发关键词-警告处置方式")
    @allure.title("命中违规关键词 - 触发群助手撤回并群内@警告")
    def test_keyword_action_warn(self):
        """处置方式为【警告】：命中关键词的消息被撤回，且群助手发送 @ 警告消息。"""
        with allure.step("1. 设置处置方式为【警告】"):
            self._set_action_rule("警告")

        self._trigger_and_assert_withdraw()

        with allure.step("3. 校验群内收到群助手的 @ 警告消息"):
            warned_msg = self.chatR.get_text_message_content_by_index(index=-1, side="all")
            check.is_true("@" in warned_msg, "❌ 未检测到群助手发送的 @ 警告消息")

    @pytest.mark.destructive
    @allure.story("禁发关键词-禁言处置方式")
    @allure.title("命中违规关键词 - 触发群助手撤回并禁言发送者")
    def test_keyword_action_mute(self):
        """处置方式为【禁言】：命中关键词的消息被撤回，且发送者被禁言（输入框不可用）。

        注意：禁言会改变接收方账号状态且无自动还原，建议用 -k test_keyword_action_mute 单独运行。
        """
        with allure.step("1. 设置处置方式为【禁言】"):
            self._set_action_rule("禁言")

        self._trigger_and_assert_withdraw()

        with allure.step("3. 校验发送者被禁言（底部输入框被禁用）"):
            check.is_true(self.chatR.is_input_disabled(), "❌ 发送者未被禁言，输入框仍可用")

    @pytest.mark.destructive
    @allure.story("禁发关键词-移除群聊处置方式")
    @allure.title("命中违规关键词 - 触发群助手撤回并移除发送者")
    def test_keyword_action_kick(self):
        """处置方式为【移除群聊】：命中关键词的消息被撤回，且群内出现移除系统消息。

        注意：移除会将接收方踢出群聊且无自动还原，建议用 -k test_keyword_action_kick 单独运行。
        """
        with allure.step("1. 设置处置方式为【移除群聊】"):
            self._set_action_rule("移除群聊")

        self._trigger_and_assert_withdraw()

        with allure.step("3. 校验群内出现移除系统消息"):
            last_msg = self.chatR.get_text_message_content_by_index(index=-1, side="all")
            check.is_true(
                "移出" in last_msg or "移除" in last_msg,
                f"❌ 未检测到移除群聊的系统消息: {last_msg}",
            )
