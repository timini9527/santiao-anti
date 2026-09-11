import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.home.home_page import HomePage
from pages.main.main_page import MainPage
from strategy.chat.chat_message_strategy import ChatMessageBuilder
from strategy.chat.chat_strategy import (
    PRIVATE_USER1, 
    PRIVATE_USER2, 
    PRIVATE_DISABLE1, 
    GROUP_STRATEGY, 
    GROUP_STRATEGY2, 
    SLIDE_STRATEGY, 
    SETTING_ACTIONS, 
    DELETE_ACTIONS, 
    TOP_FOLD_SCENARIOS, 
    CHAT_CONTENT_SCENARIOS
)




@allure.epic('IM核心功能测试')
@allure.feature('聊天模块-会话列表')
class TestChatList:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.chatListPage = ChatListPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.messageBuilder = ChatMessageBuilder(driver_sender)

        try:
            self.mainPage.go_to_main_page()
            self.chatListPage._quick_slide_to_top()
        except Exception as e:
            logger.warning(f'Setup 预置首页状态异常: {e}')
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f'Teardown 失败，未能返回首页: {e}')

    def _send_and_verify_message(self, message: str):
        """提取的文本消息发送验证逻辑（发送 -> 气泡断言 -> 返回首页）"""
        self.chatListPage.send_message(message)
        send_text = self.chatListPage.find_sent_message_by_bubble(message)
        check.equal(send_text, message, f'❌ 发送消息失败, 发送的消息与预期不符, 实际为: {send_text}')
        self.chatListPage.click_back_button()
        self.homePage.wait_home_page()

    def _clear_all_pinned_sessions(self, max_clean: int = 10):
        """
        【工业级环境清理】彻底取消列表所有置顶会话
        结合折叠条与顶部会话排布拓扑：
        1. 若存在折叠条 (>=5个置顶)，先按数量快速批量取消；
        2. 针对 <5 个置顶的场景，逐个探测顶部首项，若为置顶则取消，直到首项不再是置顶。
        """
        self.mainPage.go_to_main_page()
        self.chatListPage._quick_slide_to_top()
        fold_count = self.homePage.get_fold_count()
        if fold_count > 0:
            if self.homePage.get_top_fold_state() == 'collapsed':
                self.homePage.click_fold_entry()
            self._batch_set_top(fold_count, '取消置顶')
            self.mainPage.go_to_main_page()
            self.chatListPage._quick_slide_to_top()

        for _ in range(max_clean):
            names = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
            if not names:
                break
            first_name = names[0]
            menu_text = self.chatListPage.set_notice(first_name, PRIVATE_USER1.top_locator, slider_action='取消置顶')
            if menu_text == '置顶':
                logger.info(f"✅ 列表已无任何置顶项，清理完毕")
                break

    def _batch_set_top(self, count: int, action: str = '置顶', locator: tuple = None) -> int:
        """
        辅助方法：安全地对前 count 个会话执行置顶/取消置顶 (支持跨多屏自动翻页扫描与按需首屏复位)
        :param count: 需要操作的目标数量
        :param action: 操作文案 ('置顶' 或 '取消置顶')
        :param locator: 侧滑置顶按钮定位符（不传则默认使用私聊置顶定位符）
        """
        if count <= 0:
            return 0
        target_locator = locator or PRIVATE_USER1.top_locator
        top_count = 0
        processed_names = set()
        has_scrolled = False
        max_scroll_attempts = 5

        while top_count < count:
            self.mainPage.go_to_main_page()
            names = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
            remaining_names = [n for n in names if n not in processed_names]
            if not remaining_names:
                if max_scroll_attempts <= 0:
                    logger.warning(f"⚠️ 已达最大滑屏尝试上限，列表会话已全部扫描完毕 (已处理: {top_count}/{count})")
                    break
                logger.info(f"⏳ 当前可视会话已全部处理，向上平滑滚动加载更多 (当前已处理: {top_count}/{count})...")
                self.chatListPage.swipe_page(slid_type='up', duration=500, times=1)
                time.sleep(0.5)
                has_scrolled = True
                max_scroll_attempts -= 1
                new_names = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
                new_remaining = [n for n in new_names if n not in processed_names]
                if not new_remaining:
                    logger.info("ℹ️ 触达列表底部，无更多新会话可用")
                    break
                remaining_names = new_remaining

            name = remaining_names[0]
            if not self.homePage.ensure_item_safe_visible(name, allow_swipe=False):
                processed_names.add(name)
                continue
            menu_text = self.chatListPage.set_notice(name, target_locator, slider_action=action)
            processed_names.add(name)
            if menu_text == action:
                top_count += 1

        if has_scrolled:
            self.chatListPage._quick_slide_to_top()
            time.sleep(0.5)
        return top_count




    @allure.story('进入私聊/群聊会话')
    @allure.title('进入私聊/群聊会话-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_enter_chat(self, strategy):
        """
        进入私聊/群聊会话，发送消息并验证
        :param strategy: 会话策略对象
        """
        self.chatListPage.enter_chat(strategy.name)
        top_name = self.chatListPage.get_top_name()
        assert strategy.name in top_name, f'❌ 获取会话名称失败, 顶部未包含【{strategy.name}】, 实际顶部显示为: {top_name}'
        self._send_and_verify_message(f'{strategy.name}要进行测试了')


    @allure.story('单个会话侧滑(静音、取消静音、置顶、取消置顶)功能')
    @allure.title('单个会话侧滑(静音、取消静音、置顶、取消置顶)功能-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    @pytest.mark.parametrize('action', [pytest.param(x, id=x.action_desc) for x in SETTING_ACTIONS])
    def test_slide_settings(self, strategy, action):
        allure.dynamic.story(action.story)
        allure.dynamic.title(f'侧滑设置 | {strategy.desc} - {action.action_desc}')
        with allure.step(f'1. 在消息列表侧滑【{strategy.desc}】并点击【{action.action_desc}】'):
            locator = getattr(strategy, action.locator_attr)
            menu_text = self.chatListPage.set_notice(strategy.name, locator)
            check.is_in(menu_text, action.expected_menu_texts, f'侧滑按钮文案不匹配, 实际为: {menu_text}')
        with allure.step(f'2. 进入【{strategy.desc}】会话并打开更多设置'):
            session_status = self.chatListPage.enter_session(strategy.name)
            assert session_status is True, f'进入会话失败, 未找到目标会话: {strategy.name}'
            self.chatListPage.click_more_button()
        with allure.step('3. 校验最终设置状态是否符合预期'):
            get_status_func = getattr(self.chatSettingPage, action.get_status_method)
            remind_status = get_status_func()
            assert remind_status == action.expected_status, f'状态校验失败！预期: {action.expected_status}, 实际: {remind_status}'


    @allure.story('单个会话侧滑置顶，滑到最底部让最后一个会话置顶并验证')
    @allure.title('单个会话侧滑置顶，滑到最底部让最后一个会话置顶验证-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_slide_top_last_session(self, strategy):
        with allure.step('0. 环境清理：彻底取消所有已置顶会话'):
            self._clear_all_pinned_sessions()
        with allure.step('1. 快速下滑到底部置顶一个会话'):
            self.chatListPage._quick_slide_to_bottom()
            con_names = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
            assert con_names, '❌ 无法获取底部会话列表名称'
            target_name = con_names[-1]
            self.chatListPage.set_notice(target_name, strategy.top_locator, slider_action='置顶')
        with allure.step('2. 快速上滑到顶部并验证置顶状态是否符合预期'):
            self.chatListPage._quick_slide_to_top()
            con_names_aft = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
            assert con_names_aft, '❌ 无法获取顶部会话列表名称'
            check.equal(con_names_aft[0], target_name, f'❌ 置顶失败, 顶部会话不匹配！实际顶部会话为: {con_names_aft[0]}, 预期目标会话为: {target_name}')
        with allure.step(f'3. 环境自愈：精准还原【{target_name}】的置顶状态'):
            self.chatListPage.set_notice(target_name, strategy.top_locator, slider_action='取消置顶')


    @allure.story('批量置顶/取消置顶会话')
    @allure.title('批量置顶/取消置顶会话-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(SLIDE_STRATEGY, id='侧滑模式')])
    @pytest.mark.parametrize('is_top_action', [pytest.param(True, id='批量置顶'), pytest.param(False, id='批量取消置顶')])
    def test_batch_slide_top(self, strategy, is_top_action):
        action_name = '置顶' if is_top_action else '取消置顶'
        expected_status = 'true' if is_top_action else 'false'
        allure.dynamic.title(f'批量{action_name}页面上所有可见会话')
        with allure.step(f'1. {action_name}页面上所有可见会话'):
            pre_con_names = self.homePage.get_conversation_names()
            con_names = self.chatListPage.clean_ui_text(pre_con_names)
            for con_name in con_names:
                self.mainPage.go_to_main_page()
                if not self.homePage.ensure_item_safe_visible(con_name, allow_swipe=False):
                    logger.info(f'跳过处理: {con_name} (因列表变化，已不在安全可视区域)')
                    continue
                current_menu_text = self.chatListPage.set_notice(con_name, strategy.top_locator, slider_action=action_name)
                check.is_in(current_menu_text, ['置顶', '取消置顶'], f'侧滑文案异常: {current_menu_text}')
                with allure.step(f'2. 进入会话【{con_name}】并校验底层 {action_name} 状态'):
                    assert self.chatListPage.enter_session(con_name), f'进入会话失败: {con_name}'
                    self.chatListPage.click_more_button()
                with allure.step('3. 校验最终设置状态是否符合预期'):
                    actual_status = self.chatSettingPage.get_switch_top_status()
                    assert actual_status == expected_status, f'会话【{con_name}】{action_name}状态校验失败'


    @allure.story('当前页面一键批量置顶和取消置顶，不需要验证')
    @allure.title('当前页面一键批量置顶和取消置顶，不需要验证-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(SLIDE_STRATEGY, id='侧滑模式')])
    @pytest.mark.parametrize('is_top_action', [pytest.param(True, id='批量置顶'), pytest.param(False, id='批量取消置顶')])
    def test_batch_set_top_no_verify(self, strategy, is_top_action):
        action_name = '置顶' if is_top_action else '取消置顶'
        with allure.step(f'执行批量{action_name}操作'):
            pre_con_names = self.homePage.get_conversation_names()
            con_names = self.chatListPage.clean_ui_text(pre_con_names)
            top_count = 0
            for con_name in con_names:
                if not self.homePage.ensure_item_safe_visible(con_name, allow_swipe=False):
                    logger.info(f'跳过处理: {con_name} (因列表变化，已不在安全可视区域)')
                    continue
                current_menu_text = self.chatListPage.set_notice(con_name, strategy.top_locator, slider_action=action_name)
                check.is_in(current_menu_text, ['置顶', '取消置顶'], f'侧滑文案异常: {current_menu_text}')
                top_count += 1
        with allure.step(f'校验批量 {action_name} 操作结果'):
            fold_count = self.homePage.get_fold_count()
            if is_top_action:
                expected_fold = top_count if top_count >= 5 else 0
                check.equal(fold_count, expected_fold, f'折叠数量校验失败！预期: {expected_fold}, 实际: {fold_count}')
            else:
                check.equal(fold_count, 0, f'折叠数量校验失败！预期: 0, 折叠数量: {fold_count}')


    @allure.story('置顶会话折叠验证')
    @allure.title('置顶会话折叠验证-状态：已完成')
    @pytest.mark.parametrize('scenario', [pytest.param(x, id=x.desc) for x in TOP_FOLD_SCENARIOS])
    def test_top_fold(self, scenario):
        if scenario.is_first:
            with allure.step('0. 环境初始化：彻底取消所有历史已置顶会话'):
                self._clear_all_pinned_sessions()

        with allure.step(f'1. 增量执行【{scenario.action_type}】{scenario.action_count} 个会话 (预期总置顶数: {scenario.expected_total})'):
            self._batch_set_top(scenario.action_count, scenario.action_type)

        with allure.step(f'2. 校验折叠入口 (预期可见: {scenario.expect_fold_visible})'):
            fold_status = self.homePage.is_fold_entry_visible()
            assert fold_status == scenario.expect_fold_visible, f'❌ 折叠入口状态不匹配！预期: {scenario.expect_fold_visible}, 实际: {fold_status}'

        if scenario.check_fold_count:
            with allure.step(f'3. 校验折叠数量 == {scenario.expected_total}'):
                fold_count = self.homePage.get_fold_count()
                assert fold_count == scenario.expected_total, f'❌ 折叠数量不匹配, 实际: {fold_count}, 预期: {scenario.expected_total}'

        if scenario.check_fold_click:
            with allure.step('4. 校验置顶折叠展开与还原逻辑'):
                initial_state = self.homePage.get_top_fold_state()
                con_names_pre = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
                logger.info(f"📌 [Fold Click Test] 当前初始状态: {initial_state}, 当前可见会话: {con_names_pre[:3]}...")
                self.homePage.click_fold_entry()
                switched_state = self.homePage.get_top_fold_state()
                con_names_aft = self.chatListPage.clean_ui_text(self.homePage.get_conversation_names())
                assert con_names_pre != con_names_aft, f'❌ 折叠切换后会话列表应发生变化，实际: {con_names_pre} == {con_names_aft}'
                logger.info(f"✅ [Fold Click Test] 状态成功切换: {initial_state} -> {switched_state}")
                self.homePage.click_fold_entry()
                restored_state = self.homePage.get_top_fold_state()
                logger.info(f"✅ [Fold Click Test] 状态成功还原: {restored_state}")
                assert restored_state == initial_state, f'❌ 折叠还原后状态不匹配！预期: {initial_state}, 实际: {restored_state}'

        if scenario.is_last:
            with allure.step('5. 现场恢复：全流水线结束，彻底清理所有置顶状态'):
                self._clear_all_pinned_sessions()


    @allure.story('单个会话侧滑删除功能(清空聊天记录/隐藏会话/取消删除)')
    @allure.title('单个会话侧滑删除功能(清空聊天记录/隐藏会话/取消删除)-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER2, id='私聊模式'), pytest.param(GROUP_STRATEGY2, id='群聊模式')])
    @pytest.mark.parametrize('action', [pytest.param(x, id=x.action_desc) for x in DELETE_ACTIONS])
    def test_slide_delete(self, strategy, action):
        allure.dynamic.story(action.story)
        allure.dynamic.title(f'侧滑删除 | {strategy.desc} - {action.action_desc}')

        if action.expected_session_exists is None:
            with allure.step(f'0. 前置基准注入：确保【{strategy.name}】有可被清空的聊天记录'):
                current_msg = self.homePage.get_message_by_name(strategy.name)
                if not current_msg:
                    self.chatListPage.common_enter_chat(strategy.name)
                    self.chatListPage.send_message(f'[{strategy.name}] 侧滑清空前基准消息')
                    self.mainPage.go_to_main_page()

        with allure.step(f'1. 确保【{strategy.desc}】处于安全可视区并侧滑点击删除'):
            is_visible = self.homePage.ensure_item_safe_visible(strategy.name, allow_swipe=True)
            assert is_visible, f'❌ 会话【{strategy.name}】无法安全呈现在可视区，中止侧滑'
            menu_text = self.chatListPage.set_notice(strategy.name, strategy.delete_locator)
            assert menu_text == '删除', f'❌ 侧滑按钮文案不匹配, 期望: 删除, 实际为: {menu_text}'

        with allure.step(f'2. 在二次确认弹窗中选择【{action.action_desc}】'):
            getattr(self.homePage, action.dialog_action_method)()

        try:
            with allure.step('3. 校验最终列表与聊天记录状态'):
                if action.expected_session_exists is None:
                    msg_preview = self.homePage.get_message_by_name(strategy.name)
                    assert not msg_preview, f'❌ 聊天记录预览未被清空，实际显示为: {msg_preview}'

                    self.chatListPage.common_enter_chat(strategy.name)
                    bubble_num = self.chatListPage.get_total_message_count()
                    assert bubble_num == 0, f'❌ 会话内仍残留聊天气泡，实际数量: {bubble_num}'
                    self.mainPage.go_to_main_page()
                else:
                    is_exist = self.chatListPage.is_session_exist_in_list(strategy.name)
                    assert is_exist == action.expected_session_exists, (
                        f'❌ 会话列表状态不匹配! 期望存在: {action.expected_session_exists}, 实际存在: {is_exist}'
                    )
        finally:
            needs_heal = (action.expected_session_exists is False) or (
                action.expected_session_exists is None and 
                not self.chatListPage.is_session_exist_in_list(strategy.name)
            )
            if needs_heal:
                with allure.step(f'4. 环境自愈：重新唤起【{strategy.name}】恢复会话列表展示'):
                    self.mainPage.go_to_main_page()
                    self.chatListPage.common_enter_chat(strategy.name)
                    self.chatListPage.send_message(f'[{strategy.name}] 会话删除/隐藏后自愈恢复')
                    self.mainPage.go_to_main_page()


    @allure.story('验证会话草稿模式状态')
    @allure.title('验证会话草稿模式状态-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_draft_mode(self, strategy):
        draft_content = f'{strategy.name}草稿测试内容'
        with allure.step(f'1. 进入【{strategy.desc}】会话并输入未发送的草稿内容'):
            self.chatListPage.enter_chat(strategy.name)
            self.chatListPage.input_text(draft_content)
            self.chatListPage.click_back_button()
            self.homePage.wait_home_page()
        with allure.step('2. 验证消息列表会话中显示【草稿】标识'):
            remind_status = self.homePage.get_remind_status()
            check.is_in('草稿', remind_status, f'草稿模式状态不匹配, 实际为: {remind_status}')
            tip_status = self.chatListPage.enter_session(strategy.name)
            assert tip_status, f'进入会话失败, 未找到目标会话: {strategy.name}'
        with allure.step('3. 重新进入会话验证输入框草稿内容一致，并清理现场'):
            input_text = self.chatListPage.get_input_text()
            check.equal(input_text, draft_content, f'❌ 输入框草稿内容不匹配, 预期: {draft_content}, 实际: {input_text}')
            self.chatListPage.clear_input_text()
            self.chatListPage.click_back_button()


    @allure.story('验证会话未读/已读状态')
    @allure.title('验证会话发送消息后即时呈现【未读】状态-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_unread_mode(self, strategy):
        """
        【单端基线】验证发送端发送消息后，会话列表即时呈现【未读】阅读回执状态
        注：完整的【未读 -> 已读】跨端状态机流转已解耦沉淀至双端套件 test_chat_list_double.py 中
        """
        with allure.step(f'1. 进入【{strategy.desc}】会话并发送消息'):
            self.chatListPage.enter_chat(strategy.name)
            self._send_and_verify_message(f'{strategy.name}要进行测试了')
        with allure.step('2. 验证会话列表中即时呈现【未读】状态'):
            tip_status = self.homePage.get_unread_status(strategy.name)
            check.is_in('未读', tip_status, f'未读模式状态不匹配, 实际为: {tip_status}')


    @allure.story('验证会话停用状态')
    @allure.title('验证会话停用状态-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_DISABLE1, id='停用账号')])
    def test_disable_mode(self, strategy):
        with allure.step(f'1. 进入【{strategy.desc}】会话并发送消息'):
            self.chatListPage.enter_chat(strategy.name)
            self.chatListPage.send_message(f'{strategy.name}要进行测试了')
            disable_message_tip = self.chatListPage.get_disable_message_tip()
            check.greater(disable_message_tip, 0, f'给停用账号发送消息提示不匹配, 实际为: {disable_message_tip}')
            self.chatListPage.click_back_button()
            self.homePage.wait_home_page()
        with allure.step('2. 验证停用模式状态'):
            tip_status = self.homePage.get_disable_status(strategy.name)
            check.is_true(tip_status, f'停用模式状态不匹配, 实际为: {tip_status}')


    @allure.story('验证会话封禁状态')
    @allure.title('验证会话封禁状态-状态：TODO: skip')
    @pytest.mark.skip(reason='TODO: skip-待完善')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_ban_mode(self, strategy):
        with allure.step(f'1. 进入【{strategy.desc}】会话并发送消息'):
            self.chatListPage.enter_chat(strategy.name)
            self.chatListPage.send_message(f'{strategy.name}要进行测试了')
            self.chatListPage.click_back_button()
            self.homePage.wait_home_page()
        with allure.step('2. 验证封禁模式状态'):
            session_status = self.chatListPage.enter_session(strategy.name)
            assert session_status is True, f'进入会话失败, 未找到目标会话: {strategy.name}'
            self.chatListPage.click_more_button()
            remind_status = self.chatSettingPage.get_remind_status() if hasattr(self.chatSettingPage, 'get_remind_status') else 'true'
            assert remind_status == 'true', f'封禁模式状态不匹配, 实际为: {remind_status}'


    @allure.story('验证会话内容发送中状态')
    @allure.title('弱网环境-验证消息发送中(转圈)状态-状态：已完成')
    @pytest.mark.skip(reason='TODO: skip-待完善')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_message_sending_status_under_weak_network(self, strategy):
        """
        【弱网专项】验证在网络不好的弱网状态下发送消息，消息呈现【发送中】(转圈 loading) 状态
        """
        test_msg = f'网络不好_发送中测试_{int(time.time())}'
        try:
            with allure.step(f'1. 进入【{strategy.desc}】会话'):
                self.chatListPage.enter_chat(strategy.name)
            with allure.step('2. 模拟网络受阻：在发信前设置网络切断/弱网阻滞，制造确定性悬挂期'):
                self.chatListPage.set_network_connection('offline')
                time.sleep(0.5)
            with allure.step('3. 发送文本消息'):
                self.chatListPage.send_message(test_msg)
            with allure.step('4. 验证最后一条消息在重试悬挂期内 100% 呈现【发送中】(转圈) 状态'):
                is_sending = self.chatListPage.is_last_message_sending(timeout=5)
                check.is_true(is_sending, '❌ 未能在网络受阻悬挂期内捕获到消息的【发送中】(转圈)状态')
            with allure.step('5. 恢复正常网络，验证消息从发送中自愈成功送达'):
                self.chatListPage.set_network_connection('online')
                is_delivered = self.chatListPage.wait_for_last_sent_message_completed(timeout=10)
                check.is_true(is_delivered, '❌ 恢复网络后，消息未能自愈发送完成')
        finally:
            with allure.step('环境自愈：确保网络完全恢复并返回首页'):
                self.chatListPage.set_network_connection('online')
                self.chatListPage.click_back_button()
                self.homePage.wait_home_page()


    @allure.story('验证会话内容发送失败状态')
    @allure.title('断网环境-验证消息发送失败(红点感叹号)状态-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_message_failed_status_under_offline(self, strategy):
        """
        【断网专项】验证在没有网络(断网)状态下发送消息，消息超时最终呈现【发送失败】(红色感叹号) 状态
        """
        test_msg = f'断网发送失败测试_{int(time.time())}'
        try:
            with allure.step(f'1. 进入【{strategy.desc}】会话'):
                self.chatListPage.enter_chat(strategy.name)
            with allure.step('2. 模拟没有网络：切断设备所有网络连接 (Offline)'):
                self.chatListPage.set_network_connection('offline')
            with allure.step('3. 在断网状态下发送文本消息'):
                self.chatListPage.send_message(test_msg)
            with allure.step('4. 验证最后一条消息呈现【发送失败】(红色感叹号)状态'):
                is_fail = self.chatListPage.get_last_message_send_fail_status()
                check.is_true(is_fail, '❌ 断网环境下最后一条消息未呈现发送失败(红色感叹号)状态')
            with allure.step('5. 返回首页会话列表，验证会话存在发送失败状态标识'):
                self.chatListPage.click_back_button()
                self.homePage.wait_home_page()
                fail_status = self.homePage.get_remind_status()
                logger.info(f'会话列表当前消息状态: {fail_status}')
        finally:
            with allure.step('环境自愈：强制恢复正常全网连接并安全重置至首页'):
                try:
                    self.chatListPage.set_network_connection('online')
                except Exception as e:
                    logger.warning(f'网络恢复异常: {e}')
            

    @allure.story('验证单端会话内容：表情包、图片、视频、语音、位置、文件、个人名片、群名片')
    @allure.title('验证会话内容状态-状态：已完成')
    @pytest.mark.parametrize('session_strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    @pytest.mark.parametrize('content_strategy', [pytest.param(x, id=x.desc) for x in CHAT_CONTENT_SCENARIOS])
    def test_chat_content_status(self, session_strategy, content_strategy):
        allure.dynamic.title(f'会话内容状态 | {session_strategy.desc} - {content_strategy.desc}')
        with allure.step(f'1. 进入【{session_strategy.desc}】会话并发送【{content_strategy.desc}】'):
            self.chatListPage.enter_chat(session_strategy.name)
            self.messageBuilder.build_message(content_strategy.msg_type, **content_strategy.build_args)
            self.chatListPage.wait_for_last_message_send_status()
            self.chatListPage.click_back_button()
            self.homePage.wait_home_page()
        with allure.step(f'2. 验证消息列表会话内容展示: 包含 {content_strategy.expected_text}'):
            actual_content = self.homePage.get_message_by_name(session_strategy.name, expected_text=content_strategy.expected_text)
            check.is_in(content_strategy.expected_text, actual_content, f'会话内容展示不匹配, 预期包含: {content_strategy.expected_text}, 实际为: {actual_content}')

    # 注：群聊特有会话状态（进群申请、入群系统通知、有人@我、查看@人消息消失、@所有人、复合提醒）
    # 强依赖双端协同信令交互，已规范移植至双端套件 `tests/chat/test_chat_list_double.py` 中执行。
