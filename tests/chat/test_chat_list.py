import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.chat.chat_collection_source_page import ChatCollectionSourcePage
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_setting_page import ChatSettingPage
from pages.home.home_page import HomePage
from pages.main.main_page import MainPage
from strategy.chat.chat_strategy import (
    PRIVATE_USER1,
    PRIVATE_USER2,
    PRIVATE_DISABLE1,
    GROUP_STRATEGY,
    SLIDE_STRATEGY,
    SETTING_ACTIONS,
    DELETE_ACTIONS,
    TOP_FOLD_SCENARIOS,
    CHAT_CONTENT_SCENARIOS
)


@allure.epic("IM核心功能测试")
@allure.feature("聊天模块-会话列表")
@allure.story("提取的文本消息发送验证逻辑")
class TestChatList:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试类开始前，自动获取 self.chatListPage 实例并绑定到 self
        这样下面的方法就不需要反复传参了
        """
        self.chatListPage = ChatListPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.chatListPage._quick_slide_to_top()
        self.homePage = HomePage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        # HomePage(driver_sender).get_top_middle_title()

        yield

        self.mainPage.go_to_main_page()  # 回到首页

    # 辅助方法：发送并验证消息
    def _send_and_verify_message(self, message):
        """提取的文本消息发送验证逻辑"""
        self.chatListPage.send_message(message)
        send_text = self.chatListPage.find_sent_message_by_bubble(message)
        check.equal(send_text, message,
                    f"❌ 发送消息失败, 发送的消息与预期不符, 实际为: {send_text}")
        self.chatListPage.click_back_button()
        self.homePage.click_bottom_expand_menu()

    # 辅助方法：批量设置置顶
    def _batch_set_top(self, count: int, action: str = "置顶") -> int:
        """辅助方法：对前 count 个会话执行置顶/取消置顶"""
        top_count = 0
        processed_names = set()

        while top_count < count:
            self.mainPage.go_to_main_page()
            names = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
            # 过滤掉本轮循环中已经处理过的名称
            remaining_names = [n for n in names if n not in processed_names]
            if not remaining_names:
                break

            name = remaining_names[0]
            self.chatListPage.set_notice(name, PRIVATE_USER1.top_locator, slider_action=action)
            processed_names.add(name)
            top_count += 1
        return top_count

    @allure.story("进入私聊/群聊会话")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_enter_chat(self, strategy):
        """
        进入私聊会话，发送消息并验证
        :param strategy: 私聊策略
        :return:
        """
        self.chatListPage.enter_chat(strategy.name)
        assert self.chatListPage.get_friend_name(strategy.name), "❌ 获取会话名称失败, 没有进入到聊天页面"

        self._send_and_verify_message(f"{strategy.name}要进行测试了")

    @allure.story("单个会话侧滑(静音、取消静音、置顶、取消置顶)功能")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    @pytest.mark.parametrize("action", SETTING_ACTIONS, ids=lambda a: a.action_desc)
    def test_slide_settings(self, strategy, action):
        allure.dynamic.story(action.story)
        allure.dynamic.title(f"侧滑设置 | {strategy.desc} - {action.action_desc}")

        with allure.step(f"1. 在消息列表侧滑【{strategy.desc}】并点击【{action.action_desc}】"):
            # 动态获取当前测试策略中具体的定位器属性 (如 notice_locator 或 top_locator)
            locator = getattr(strategy, action.locator_attr)
            menu_text = self.chatListPage.set_notice(strategy.name, locator)
            check.is_in(menu_text, action.expected_menu_texts,
                        f"侧滑按钮文案不匹配, 实际为: {menu_text}")

        with allure.step(f"2. 进入【{strategy.desc}】会话并打开更多设置"):
            session_status = self.chatListPage.enter_session(strategy.name)
            assert session_status is True, f"进入会话失败, 未找到目标会话: {strategy.name}"
            self.chatListPage.click_more_button()

        with allure.step("3. 校验最终设置状态是否符合预期"):
            get_status_func = getattr(self.chatSettingPage, action.get_status_method)
            remind_status = get_status_func()
            assert remind_status == action.expected_status, \
                f"状态校验失败！预期: {action.expected_status}, 实际: {remind_status}"

    @allure.story("单个会话侧滑置顶，滑到最底部让最后一个会话置顶并验证")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_slide_top_last_session(self, strategy):
        allure.dynamic.title("单个会话侧滑置顶，滑到最底部让最后一个会话置顶验证")

        with allure.step("0. 环境清理：取消所有已置顶会话"):
            fold_count = self.homePage.get_fold_count()
            self._batch_set_top(fold_count if fold_count > 0 else 4, "取消置顶")

        with allure.step("1. 快速下滑到底部置顶一个会话"):
            self.chatListPage._quick_slide_to_bottom()
            con_names = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
            self.chatListPage.set_notice(con_names[-1], strategy.top_locator)

        with allure.step("2. 快速上滑到顶部并验证置顶状态是否符合预期"):
            self.chatListPage._quick_slide_to_top()
            con_names_aft = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
            check.is_true(con_names_aft[0] == con_names[-1],
                        f"❌ 置顶失败, 置顶的会话不是最顶部的会话, 置顶的会话为: {con_names_aft[0]}, 置顶的会话为: {con_names[-1]}")
            self._batch_set_top(1, "取消置顶")

    @allure.story("批量置顶/取消置顶会话")
    @pytest.mark.parametrize("strategy", [SLIDE_STRATEGY], ids=lambda s: s.desc)
    @pytest.mark.parametrize("is_top_action", [True, False], ids=["测试批量置顶", "测试批量取消置顶"])
    def test_batch_slide_top(self, strategy, is_top_action):
        action_name = "置顶" if is_top_action else "取消置顶"
        expected_status = 'true' if is_top_action else 'false'

        allure.dynamic.title(f"批量{action_name}页面上所有可见会话")

        with allure.step(f"1. {action_name}页面上所有可见会话"):
            pre_con_names = self.homePage.get_conversation_names()
            con_names = self.chatListPage.clean_ui_text(pre_con_names)

            for con_name in con_names:
                self.mainPage.go_to_main_page()
                if not self.homePage.ensure_item_safe_visible(con_name, allow_swipe=False):
                    logger.info(f"跳过处理: {con_name} (因列表变化，已不在安全可视区域)")
                    continue

                current_menu_text = self.chatListPage.set_notice(con_name, strategy.top_locator, slider_action=action_name)
                check.is_in(current_menu_text, ["置顶", "取消置顶"], f"侧滑文案异常: {current_menu_text}")

                with allure.step(f"2. 进入会话【{con_name}】并校验底层 {action_name} 状态"):
                    assert self.chatListPage.enter_session(con_name), f"进入会话失败: {con_name}"
                    self.chatListPage.click_more_button()

                with allure.step("3. 校验最终设置状态是否符合预期"):
                    actual_status = self.chatSettingPage.get_switch_top_status()
                    assert actual_status == expected_status, f"会话【{con_name}】{action_name}状态校验失败"

    @allure.story("当前页面一键批量置顶和取消置顶，不需要验证")
    @pytest.mark.parametrize("strategy", [SLIDE_STRATEGY], ids=lambda s: s.desc)
    @pytest.mark.parametrize("is_top_action", [True, False], ids=["批量置顶", "批量取消置顶"])
    def test_batch_set_top_no_verify(self, strategy, is_top_action):
        action_name = "置顶" if is_top_action else "取消置顶"
        allure.dynamic.title(f"快速批量{action_name}（不进入详情校验）")

        with allure.step(f"执行批量{action_name}操作"):
            pre_con_names = self.homePage.get_conversation_names()
            con_names = self.chatListPage.clean_ui_text(pre_con_names)
            top_count = 0
            # top_count = self._batch_set_top(len(con_names), action_name)
            for con_name in con_names:
                if not self.homePage.ensure_item_safe_visible(con_name, allow_swipe=False):
                    logger.info(f"跳过处理: {con_name} (因列表变化，已不在安全可视区域)")
                    continue
                current_menu_text = self.chatListPage.set_notice(con_name, strategy.top_locator, slider_action=action_name)
                check.is_in(current_menu_text, ["置顶", "取消置顶"], f"侧滑文案异常: {current_menu_text}")
                top_count += 1

        with allure.step(f"校验批量 {action_name} 操作结果"):
            fold_count = self.homePage.get_fold_count()
            if is_top_action:
                check.equal(fold_count, top_count, f"折叠数量校验失败！预期: {top_count}, 实际: {fold_count}")
            else:
                check.equal(fold_count, 0, f"折叠数量校验失败！预期: 0, 折叠数量: {fold_count}")

    @allure.story("置顶会话折叠验证")
    @pytest.mark.parametrize("scenario", TOP_FOLD_SCENARIOS, ids=lambda s: s.desc)
    def test_top_fold(self, scenario):
        """置顶折叠验证：批量置顶 → 取消置顶 → 校验折叠状态"""
        allure.dynamic.story(scenario.story)
        allure.dynamic.title(f"折叠验证 | {scenario.desc}")

        # TODO: 当折叠入口被隐藏后，后续测试需确保所有会话已取消置顶以重置环境状态
        with allure.step("0. 环境清理：取消所有已置顶会话"):
            fold_count = self.homePage.get_fold_count()
            # fold_count = 0
            self._batch_set_top(fold_count if fold_count > 0 else 4, "取消置顶")

        with allure.step(f"1. 智能置顶前 {scenario.pin_count} 个会话"):
            self._batch_set_top(scenario.pin_count, "置顶")

        if scenario.unpin_one:
            with allure.step("2. 取消第一个会话的置顶"):
                self._batch_set_top(1, "取消置顶")

        with allure.step(f"3. 校验折叠入口 (预期可见: {scenario.expect_fold_visible})"):
            fold_status = self.homePage.is_fold_entry_visible()
            assert fold_status == scenario.expect_fold_visible, f"❌ 折叠入口状态不匹配！预期: {scenario.expect_fold_visible}"

        if scenario.check_fold_count:
            with (allure.step(f"4. 校验折叠数量 == {scenario.pin_count}")):
                fold_count = self.homePage.get_fold_count()
                assert fold_count == scenario.pin_count, f"❌ 折叠数量不匹配, 实际: {self.homePage.get_fold_count()}"

        if scenario.check_fold_click:
            with allure.step("5. 点击折叠，校验会话被隐藏，前后会话名称不一样"):
                con_names_pre = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
                self.homePage.click_fold_entry(con_names_pre[0])
                con_names_aft = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
                assert con_names_pre != con_names_aft, f"❌ 折叠后会话数应减少，实际: {con_names_pre} == {con_names_aft}"
                self.homePage.click_fold_entry(con_names_aft[0])

    @allure.story("单个会话侧滑删除功能(清空聊天记录/删除会话/取消删除)")
    @pytest.mark.parametrize("action", DELETE_ACTIONS, ids=lambda a: a.action_desc)
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_slide_delete(self, strategy, action):
        allure.dynamic.story(action.story)
        allure.dynamic.title(f"侧滑删除 | {strategy.desc} - {action.action_desc}")

        with allure.step(f"1. 在消息列表侧滑【{strategy.desc}】并点击删除"):
            menu_text = self.chatListPage.set_notice(strategy.name, strategy.delete_locator)
            check.equal(menu_text, "删除", f"侧滑按钮文案不匹配, 实际为: {menu_text}")

        with allure.step(f"2. 在二次确认弹窗中选择【{action.action_desc}】"):
            # 动态执行对应的弹窗操作
            getattr(self.homePage, action.dialog_action_method)()

        with allure.step("3. 校验最终列表状态是否符合预期"):
            if action.expected_session_exists is None:  # 清空聊天记录的特殊逻辑
                message = self.homePage.get_message_by_name(strategy.name)
                assert not message, f"聊天记录展示未被清空，实际显示为: {message}"

                session_status = self.chatListPage.enter_session(strategy.name)
                assert session_status is True, f"未找到目标会话: {strategy.name}"

                _, bubble_num = self.chatListPage.find_chat_bubbles()
                assert bubble_num == 0, f"进入会话内发现聊天气泡没有被删除，实际为: {bubble_num}"
            else:  # 取消删除 或 确认删除
                session_status = self.chatListPage._find_session_element_in_list(strategy.name)
                # 由于 _find_session_element_in_list 找不到会返回 None，找到了返回元素对象/True
                is_exist = bool(session_status)
                assert is_exist == action.expected_session_exists, \
                    f"会话列表状态不匹配! 期望存在: {action.expected_session_exists}, 实际存在: {is_exist}"

    @allure.story("验证会话草稿模式状态")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_draft_mode(self, strategy):
        allure.dynamic.title(f"草稿模式 | {strategy.desc}")

        with allure.step(f"1. 进入【{strategy.desc}】会话并发送消息"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatListPage.input_text(f"{strategy.name}要进行测试了")
            self.chatListPage.click_back_button()
            self.homePage.click_bottom_expand_menu()

        with allure.step("2. 验证【草稿模式】状态"):
            remind_status = self.homePage.get_remind_status()
            check.is_in('草稿', remind_status, f"草稿模式状态不匹配, 实际为: {remind_status}")

            tip_status = self.chatListPage.enter_session(strategy.name)
            assert tip_status, f"进入会话失败, 未找到目标会话: {strategy.name}"
        
        with allure.step("3. 验证输入框中的草稿是否存在"):
            input_text = self.chatListPage.get_input_text()
            # assert input_text == f"{strategy.name}要进行测试了", f"输入框中的草稿不匹配, 实际为: {input_text}"

    @allure.story("验证会话未读/已读状态（待完善）")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    @pytest.mark.parametrize("expected_status", ["未读"])
    # @pytest.mark.parametrize("expected_status", ["未读", "已读"])
    def test_unread_mode(self, strategy, expected_status):
        allure.dynamic.title(f"{expected_status}模式 | {strategy.desc}")

        with allure.step(f"1. 进入【{strategy.desc}】会话并发送消息"):
            self.chatListPage.enter_chat(strategy.name)
            self._send_and_verify_message(f"{strategy.name}要进行测试了")


        # 如果需要测试“已读”，这里可能需要额外的操作使状态变为已读
        # if expected_status == "已读":
        #     # TODO: 触发已读的操作 (例如侧滑标为已读，或是接收端读取)
        #     pass

        with allure.step(f"2. 验证{expected_status}模式状态"):
            tip_status = self.homePage.get_unread_status(strategy.name)
            check.is_in(expected_status, tip_status, f"{expected_status}模式状态不匹配, 实际为: {tip_status}")

    @allure.story("验证会话停用状态")
    @pytest.mark.parametrize("strategy", [PRIVATE_DISABLE1], ids=lambda s: s.desc)
    def test_disable_mode(self, strategy):
        allure.dynamic.title(f"停用模式 | {strategy.desc}")

        with allure.step(f"1. 进入【{strategy.desc}】会话并发送消息"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatListPage.send_message(f"{strategy.name}要进行测试了")
            disable_message_tip = self.chatListPage.get_disable_message_tip()
            check.greater(disable_message_tip, 0, f"给停用账号发送消息提示不匹配, 实际为: {disable_message_tip}")
            self.chatListPage.click_back_button()
            self.homePage.click_bottom_expand_menu()

        with allure.step("2. 验证停用模式状态"):
            tip_status = self.homePage.get_disable_status(strategy.name)
            check.is_true(tip_status, f"停用模式状态不匹配, 实际为: {tip_status}")
    
    @allure.story("验证会话封禁状态")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    @pytest.mark.skip("待完善")
    def test_ban_mode(self, strategy):

        allure.dynamic.title(f"封禁模式 | {strategy.desc}")

        with allure.step(f"1. 进入【{strategy.desc}】会话并发送消息"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatListPage.send_message(f"{strategy.name}要进行测试了")
            self.chatListPage.click_back_button()
            self.homePage.click_bottom_expand_menu()

        with allure.step("2. 验证停用模式状态"):
            session_status = self.chatListPage.enter_session(strategy.name)
            assert session_status is True, f"进入会话失败, 未找到目标会话: {strategy.name}"
            self.chatListPage.click_more_button()
            remind_status = self.chatListPage.get_remind_status()
            assert remind_status == 'true', f"停用模式状态不匹配, 实际为: {remind_status}"

    @allure.story("验证会话内容 发送中和发送失败 状态")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    @pytest.mark.skip("待完善")
    def test_sending_and_failed_status(self, strategy):

        allure.dynamic.title(f"发送中和发送失败 | {strategy.desc}")

        with allure.step(f"1. 进入【{strategy.desc}】会话并发送消息"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatListPage.send_message(f"{strategy.name}要进行测试了")
            self.chatListPage.click_back_button()
            self.homePage.click_bottom_expand_menu()

        with allure.step("2. 验证发送中和发送失败 状态"):
            session_status = self.chatListPage.enter_session(strategy.name)
            assert session_status is True, f"进入会话失败, 未找到目标会话: {strategy.name}"
            self.chatListPage.click_more_button()
            remind_status = self.chatListPage.get_remind_status()
            assert remind_status == 'true', f"发送中和发送失败 状态不匹配, 实际为: {remind_status}"

    @pytest.mark.skip("发送消息的具体方法待完善")
    @allure.story("验证会话会话内容：图片、视频、位置、文件、视频聊天、语音聊天、个人名片、群名片、进群邀请、表情、链接分享")
    @pytest.mark.parametrize("session_strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    @pytest.mark.parametrize("content_strategy", CHAT_CONTENT_SCENARIOS, ids=lambda c: c.desc)
    def test_chat_content_status(self, session_strategy, content_strategy):
        allure.dynamic.title(f"会话内容状态 | {session_strategy.desc} - {content_strategy.desc}")

        with allure.step(f"1. 进入【{session_strategy.desc}】会话并发送【{content_strategy.desc}】消息"):
            self.chatListPage.enter_chat(session_strategy.name)
            
            # 使用策略中提供的方法动态调用发送功能
            if hasattr(self.chatListPage, content_strategy.send_action):
                send_method = getattr(self.chatListPage, content_strategy.send_action)
                # 传入所需参数，如果策略定义了额外参数则解包传入
                send_method(*content_strategy.send_args)
            else:
                pytest.skip(f"方法 {content_strategy.send_action} 尚未在 ChatListPage 中实现。")
            
            self.chatListPage.click_back_button()
            self.homePage.click_bottom_expand_menu()

        with allure.step(f"2. 验证消息列表会话内容展示: 包含 {content_strategy.expected_text}"):
            actual_content = self.homePage.get_message_by_name(session_strategy.name)
            check.is_in(content_strategy.expected_text, actual_content, 
                        f"会话内容展示不匹配, 预期包含: {content_strategy.expected_text}, 实际为: {actual_content}")

    @pytest.mark.skip("待完善")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    @allure.story("验证会话内容：进群申请（管理员可见）、进群后显示某某某加入群聊、有人@我、查看@人消息消失、@所有人，查看@所有人消息消失、群主/管理员进群申请和@消息同时存在")
    def test_chat_group_content_status(self, strategy):

        allure.dynamic.title(f"会话内容状态 | {strategy.desc}")

        with allure.step(f"1. 进入【{strategy.desc}】会话并发送消息"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatListPage.send_message(f"{strategy.name}要进行测试了")
            self.chatListPage.click_back_button()
            self.homePage.click_bottom_expand_menu()

        with allure.step("2. 验证会话内容状态"):
            session_status = self.chatListPage.enter_session(strategy.name)
            assert session_status is True, f"进入会话失败, 未找到目标会话: {strategy.name}"
            self.chatListPage.click_more_button()
            remind_status = self.chatListPage.get_remind_status()
            assert remind_status == 'true', f"会话内容状态不匹配, 实际为: {remind_status}"

    





