import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.groups.setting.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from pages.groups.setting.group_manager_page import GroupManagerPage
from pages.common.session_select_page import SessionSelectPage
from pages.common.contact_select_page import ContactSelectPage
from locators.chat.chat_locator import ChatLocator
from strategy.chat.chat_strategy import GROUP_STRATEGY, PRIVATE_USER4


@allure.epic("IM核心功能测试")
@allure.feature("群助手-禁言发送关键词-双端交互与拦截")
class TestGroupBotInteraction:
    """群助手涉及到多端交互的功能测试"""

    # 声明类成员的类型注解，帮助 IDE 静态分析
    mainS: MainPage
    chatListS: ChatListPage
    chatS: ChatPage
    settingS: GroupSettingPage
    botS: GroupBotPage
    groupManagerS: GroupManagerPage
    sessionSelectS: SessionSelectPage
    contactSelectS: ContactSelectPage

    mainR: MainPage
    chatListR: ChatListPage
    chatR: ChatPage
    
    def _navigate_to_keyword_block(self):
        """从主页完整导航进入群助手【禁发关键词检测】配置页。
        setup 与 teardown 共用，避免 teardown 直接点击时假定页面停留位置而崩溃。
        """
        self.mainS.go_to_main_page()
        self.chatListS.enter_chat(GROUP_STRATEGY.name)
        self.chatS.wait_for_chat_page_load()
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        self.settingS.click_friend_header()
        self.botS.wait_for_group_bot_page_load()
        self.botS.enter_keyword_block()

    @pytest.fixture(scope="class", autouse=True)
    def setup_keyword_config(self, request, driver_sender, driver_receiver):
        """整个测试类只执行一次：初始化双端页面对象、开启开关并配置违规关键词列表"""
        # 发送方 (群主)
        request.cls.mainS = MainPage(driver_sender)
        request.cls.chatListS = ChatListPage(driver_sender)
        request.cls.chatS = ChatPage(driver_sender)
        request.cls.settingS = GroupSettingPage(driver_sender)
        request.cls.botS = GroupBotPage(driver_sender)
        request.cls.groupManagerS = GroupManagerPage(driver_sender)
        request.cls.sessionSelectS = SessionSelectPage(driver_sender)
        request.cls.contactSelectS = ContactSelectPage(driver_sender)

        # 接收方 (普通群成员或管理员)
        request.cls.mainR = MainPage(driver_receiver)
        request.cls.chatListR = ChatListPage(driver_receiver)
        request.cls.chatR = ChatPage(driver_receiver)

        logger.info("⏳ [Class Setup] 进入群助手，开启开关并配置违规关键词列表")
        self._navigate_to_keyword_block()

        botS = self.botS
        botS.toggle_switch(enable=True)
        botS.click_save()
        botS.click_keyword_row()
        botS.click_keyword_add_btn()  # TODO: 移除关键词也有 Bug，暂时先这样
        botS.set_keywords(["红包", "银行卡", "转账", "投资"])
        botS.save_keywords_config()

        yield

        logger.info("⏳ [Class Teardown] 清空关键词并关闭开关，恢复环境")
        try:
            self._navigate_to_keyword_block()
            botS.click_keyword_row()
            botS.clear_all_keywords(count=4)
            botS.toggle_switch(enable=False)
            botS.click_save()
            
            self.groupManagerS.click_back_button()
            self.groupManagerS.click_back_button()
            self.mainS.go_to_main_page()
        except Exception as e:
            logger.error(f"❌ [Class Teardown] 环境恢复失败，关键词配置可能残留，需人工检查: {e}")


    @pytest.fixture(autouse=True)
    def teardown_method(self):
        """每个测试用例执行完毕后，执行接收方的返回清理"""
        yield
        
        self.mainR.go_to_main_page()
    
    
    def _set_action_rule(self, rule_name: str, rule_time: str = None, old_summary: str = None):
        """进入群助手关键词配置页，将处置方式切换为指定规则后保存退出。

        关键词列表与开关已由 class 级 fixture 配好，这里只切换处置规则。
        """
        logger.info(f"⏳ [Pre-condition] 设置关键词处置方式为【{rule_name}】")
        botS = self.botS
        botS.select_action_rule(rule_name)
        if rule_name == "禁言":
            botS.select_mute_duration(rule_time, old_summary)
        botS.click_save()

    def _trigger_and_assert_withdraw(self, rule_name: str, message:str, rule_time: str = None):
        """接收方发送命中关键词的消息，并校验原消息被群助手撤回。

        返回 None；撤回校验失败时通过 pytest_check 记录软断言。
        各处置方式用例共用此前置：先切到群聊发消息，再验证撤回提示。
        """
        with allure.step("接收方(普通群成员)进入群聊并发送命中关键词的消息"):
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()
            self.chatR.send_message(f"{rule_name} 测试 {rule_time}")
            self.chatR.send_message(message)
            time.sleep(2)

        with allure.step("校验原消息被群助手撤回（系统撤回提示出现）"):
            withdraw_result = self.chatR.get_withdraw_message()
            check.is_not_none(withdraw_result, "❌ 未检测到任何撤回提示")
            if withdraw_result:
                withdraw_msg, _ = withdraw_result
                if rule_name == "移除群聊":
                    check.is_true("已被群助手移除群聊" in withdraw_msg, f"❌ 移除提示内容不正确: {withdraw_msg}")
                else:
                    check.is_true("撤回" in withdraw_msg, f"❌ 撤回提示内容不正确: {withdraw_msg}")

    def _owner_return_to_chat(self) -> None:
        """内部辅助方法：群主（发送方）从群助手设置页面返回群聊窗口"""
        self.chatS.wait_banner_message_disappear()
        self.botS.click_back()
        self.botS.click_back()
        self.settingS.click_iv_back_button()
        self.chatS.wait_for_chat_page_load()

    def _owner_enter_bot_setting(self) -> None:
        """内部辅助方法：群主（发送方）从群聊窗口进入群助手关键词配置页面"""
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        self.settingS.click_friend_header()
        self.botS.wait_for_group_bot_page_load()
        self.botS.enter_keyword_block()

    def _owner_assert_base_and_keyword_messages(self, rule_name: str, message: str) -> list:
        """内部辅助方法：群主端获取所有文本消息，校验基准消息和违规关键词消息是否存在"""
        all_messages = self.chatS.get_all_text_message_contents(side="all")
        has_base = any(rule_name in msg for msg in all_messages)
        has_keyword = any(message in msg for msg in all_messages)
        check.is_true(has_base, f"❌ 发送方（群主）未检测到基准消息: {rule_name} 测试")
        check.is_true(has_keyword, f"❌ 发送方（群主）未检测到违规关键词消息: {message}")
        return all_messages

    def _owner_invite_member_to_group(self, member_name: str) -> None:
        """内部辅助方法：群主（发送方）进入群设置邀请指定成员重回群聊"""
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        friend_headers = self.settingS.get_friend_headers()
        if friend_headers and len(friend_headers) >= 2:
            friend_headers[-2].click()
        else:
            raise Exception("❌ 未找到群详情页面的添加成员【+】按钮")
        
        # self.sessionSelectS.wait_for_session_page_load() # TODO: 这里需要加
        self.contactSelectS.click_contact_by_name(name=member_name, select_type="forward")
        self.sessionSelectS.click_finish_button()
        self.chatS.wait_banner_message_disappear()
        self.botS.click_back()


    @allure.story("禁发关键词-仅撤回处置方式")
    @allure.title("命中违规关键词 - 触发群助手仅撤回")
    def test_keyword_action_revoke(self):
        """处置方式为【仅撤回】：命中关键词的消息被撤回，群内无额外提示消息。"""

        rule_name = "仅撤回"
        message = "大家加我微信发红包啦"
        with allure.step(f"1. 设置处置方式为【{rule_name}】"):
            self._set_action_rule(rule_name)

        with allure.step(f"2. 接收方(普通群成员)进入群聊并发送【{message}】"):
            self._trigger_and_assert_withdraw(rule_name, message)

        with allure.step("3. 接收方校验群内未出现 @ 警告消息（仅撤回模式不发警告）"):
            last_msg = self.chatR.get_text_message_content_by_index(index=-1, side="all")
            check.is_true("@" not in last_msg, f"❌ 接收方：仅撤回模式不应出现 @ 警告消息: {last_msg}")
            check.is_in(rule_name, last_msg, f"❌ 接收方：最后一条应为基准消息（违规消息已撤回）: {last_msg}")

        with allure.step("4. 发送方(群主)退回群聊并校验撤回提示，且无额外提示"):
            self._owner_return_to_chat()
            self._owner_assert_base_and_keyword_messages(rule_name, message)

        with allure.step("5. 发送方重新进入设置以供 teardown 恢复环境"):
            self._owner_enter_bot_setting()


    @allure.story("禁发关键词-警告处置方式")
    @allure.title("命中违规关键词 - 触发群助手撤回并群内@警告")
    def test_keyword_action_warn(self):
        """处置方式为【警告】：命中关键词的消息被撤回，且群助手发送 @ 警告消息。"""
        rule_name = "警告"
        message = "大家加我微信转账啦"
        with allure.step(f"1. 设置处置方式为【{rule_name}】"):
            self._set_action_rule(rule_name)

        with allure.step(f"2. 接收方(普通群成员)进入群聊并发送【{message}】"):
            self._trigger_and_assert_withdraw(rule_name, message)

        with allure.step("3. 接收方校验群助手 @ 警告消息（5分钟内限流则只撤回不警告）"):
            last_msg = self.chatR.get_text_message_content_by_index(index=-1, side="all")
            has_warn = "@" in last_msg
            if has_warn:
                check.is_true(has_warn, f"❌ 接收方未发 @ 警告，实际消息为: {last_msg}")
            else:
                check.is_in(rule_name, last_msg, f"❌ 接收方未发 @ 警告且最后一条非基准消息，疑似撤回异常: {last_msg}")

        with allure.step("4. 发送方(群主)退回群聊并校验撤回提示与警告消息"):
            self._owner_return_to_chat()
            all_messages = self._owner_assert_base_and_keyword_messages(rule_name, message)

            has_warn2 = "@" in all_messages[-1]
            if has_warn2:
                check.is_true(has_warn2, f"❌ 发送方未检测到 @ 警告，实际消息为: {all_messages[-1]}")
            else:
                check.equal(all_messages[-1], message, f"❌ 接收方未发 @ 警告且最后一条非基准消息，疑似撤回异常: {last_msg}")
                
        with allure.step("5. 发送方重新进入设置以供 teardown 恢复环境"):
            self._owner_enter_bot_setting()


    @allure.story("禁发关键词-禁言处置方式")
    @allure.title("命中违规关键词 - 触发群助手撤回并禁言发送者")
    @pytest.mark.parametrize("rule_time", GroupBotPage.MUTE_DURATION_OPTIONS,
                             ids=[f"禁言-{t}" for t in GroupBotPage.MUTE_DURATION_OPTIONS])
    @pytest.mark.destructive
    def test_keyword_action_mute(self, rule_time):
        """处置方式为【禁言】：命中关键词的消息被撤回，且发送者被禁言（输入框不可用）。

        注意：禁言会改变接收方账号状态且无自动还原，建议用 -k test_keyword_action_mute 单独运行。
        """
        rule_name = "禁言"
        message = "大家加我微信发我银行卡号"
        with allure.step(f"1. 设置处置方式为【{rule_name}】，时长为【{rule_time}】"):
            old_summary = self.botS.get_mute_duration_summary()
            self._set_action_rule(rule_name, rule_time, old_summary)
        
        with allure.step("2. 验证时长是否修改成功"): 
            new_summary = self.botS.get_mute_duration_summary()
            check.equal(new_summary, rule_time, f"❌ 禁言时长修改失败: {new_summary}")

        with allure.step(f"3. 接收方(普通群成员)进入群聊并发送【{message}】"):
            self._trigger_and_assert_withdraw(rule_name, message, rule_time)

        with allure.step("4. 接收方校验被禁言（底部输入框被禁用与提示）"):
            title, tip = self.chatR.get_input_disabled_info()
            check.is_true(bool(title) or bool(tip), f"❌ 禁言提示标题不存在: {title}")
        
        with allure.step("5. 接收方校验禁言具体倒计时"):
            if rule_time == "永久禁言":
                check.is_false(bool(title), f"❌ 永久禁言不应有具体的禁言时间: {tip}")
            else:
                total_mins = self.chatR.get_mute_remaining_minutes(tip)
                if total_mins is None:
                    check.is_true(False, f"❌ 禁言提示时间格式不匹配 (期望包含 '剩余HH:MM:SS'): {tip}")
                else:
                    expected_ranges = {
                        "10分钟": (8, 10),
                        "30分钟": (28, 30),
                        "2小时": (115, 120),
                        "1天": (1430, 1440),
                        "7天": (10050, 10080),
                        "30天": (43150, 43200),
                    }
                    min_val, max_val = expected_ranges.get(rule_time, (0, 0))
                    check.is_true(
                        min_val <= total_mins <= max_val,
                        f"❌ 禁言时间不匹配: 期望 {min_val}~{max_val} 分钟，实际 {total_mins} 分钟 ({tip})"
                    )

        with allure.step("6. 发送方(群主)退回群聊并校验撤回提示与禁言提醒"):
            self._owner_return_to_chat()
            all_messages = self._owner_assert_base_and_keyword_messages(rule_name, message)
            
            has_warn2 = "@" in all_messages[-1]
            if has_warn2:
                check.is_true(has_warn2, f"❌ 发送方未检测到 @ 警告，实际消息为: {all_messages[-1]}")
            else:
                check.equal(all_messages[-1], message, f"❌ 接收方未发 @ 警告且最后一条非基准消息，疑似撤回异常")
        
        with allure.step(f"7. 发送方重新进入群管理，解除禁言恢复环境"):
            self.chatS.click_more_button()
            self.settingS.wait_for_setting_page_load()
            self.settingS.click_group_manager()
            self.groupManagerS.wait_for_page_load()
            self.groupManagerS.click_mute_member()
            self.groupManagerS.wait_for_specify_mute_page_load()
            self.groupManagerS.click_cancel_all_mute()
            self.groupManagerS.click_back_button()
            self.groupManagerS.click_back_button()
            self.settingS.click_iv_back_button()

        with allure.step("8. 发送方重新进入设置以供下一次参数化/teardown恢复环境"):
            self._owner_enter_bot_setting()


    @allure.story("禁发关键词-移除群聊处置方式")
    @allure.title("命中违规关键词 - 触发群助手撤回并移除发送者")
    @pytest.mark.destructive
    def test_keyword_action_kick(self):
        """处置方式为【移除群聊】：命中关键词的消息被撤回，且群内出现移除系统消息。

        注意：移除会将接收方踢出群聊且无自动还原，建议用 -k test_keyword_action_kick 单独运行。
        """
        rule_name = "移除群聊"
        message = "投资理财项目，收益可观"
        with allure.step(f"1. 设置处置方式为【{rule_name}】"):
            self._set_action_rule(rule_name)

        with allure.step(f"2. 接收方 (普通群成员) 进入群聊并发送【{message}】"):
            self._trigger_and_assert_withdraw(rule_name, message)

        with allure.step("3. 接收方校验群内出现移除系统消息"):
            # TODO：这里有 bug，需要等待 Android 修复
            self.chatR.click_back_button()
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()
            _, tip = self.chatR.get_input_disabled_info()
            check.is_true(
                "您已不在该群聊，无法发送消息" in tip,
                f"❌ 接收方未检测到移除群聊的系统消息: {tip}",
            )

        with allure.step("4. 发送方(群主)退回群聊并校验撤回提示与移出系统消息"):
            self._owner_return_to_chat()
            time.sleep(1)
            all_messages = self.chatS.get_withdraw_message()
            check.is_true("群助手" in all_messages[0], f"❌ 发送方未检测到移出群聊的系统消息: {all_messages[0]}")

        with allure.step("5. 重新邀请接收方进入群聊"):
            self._owner_invite_member_to_group(PRIVATE_USER4.name)

        with allure.step("6. 发送方重新进入设置以供 teardown 恢复环境"):
            self._owner_enter_bot_setting()
