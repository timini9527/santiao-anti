import allure
import pytest
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.chat_options.file.chat_file_page import ChatFilePage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from strategy.chat_options.file_strategy import (
    FILE_CATEGORIES, FILE_SELECT_MODES, EXACT_FILE_SCENARIOS,
    FileCategoryScenario, FileSelectMode, ExactFileScenario
)




@allure.epic('IM核心功能测试')
@allure.feature('聊天面板-文件')
class TestChatFile:

    _chat_target = None

    @pytest.fixture(scope="class", autouse=True)
    def setup_class_teardown(self, driver_sender):
        """
        类级别后置清理：所有用例执行完成后，统一执行一次返回主页
        """
        yield
        try:
            self.__class__._chat_target = None
            MainPage(driver_sender).go_to_main_page()
            logger.info("🧹 [Class Teardown] 文件模块全部用例执行完毕，统一返回主页")
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.chatListPage = ChatListPage(driver_sender)
        self.chatFilePage = ChatFilePage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.chatLongPressPage = ChatLongPressPage(driver_sender)
        self.mainPage = MainPage(driver_sender)

    def _enter_chat_and_open_file_page(self, chat_name: str):
        """进入指定的聊天会话并打开选择文件页面（支持同会话直接复用，跨会话如私聊切群聊时自动退回主页重新进入）"""
        if self.__class__._chat_target != chat_name:
            if self.__class__._chat_target is not None:
                logger.info(f"🔄 [Session Switch] 检测到聊天对象从【{self.__class__._chat_target}】切换为【{chat_name}】，退回首页重新进入")
                self.mainPage.go_to_main_page()
            self.chatListPage.enter_chat(chat_name)
            self.__class__._chat_target = chat_name
        self.chatFilePage.open_panel_enter_file_page()

    def _send_file_message_helper(self, chat_name: str, file_type: str = 'image', sub_menu_item: str = '图片', 
                                  dir_name: str = 'santiaoTalk', select_mode: str = 'first', target_index: int = 0) -> bool:
        """通用辅助方法：进入聊天会话并选择发送一个文件（供正向用例、消息管理与异常测试用例统一复用）"""
        self._enter_chat_and_open_file_page(chat_name)
        if not self.chatFilePage.wait_for_file_page_load():
            return False
        self.chatFilePage.switch_to_file_category()
        return self.chatFilePage.get_recently_page_files(file_type=file_type, sub_menu_item=sub_menu_item, 
            primary_dir=dir_name, select_mode=select_mode, target_index=target_index
        )




    # =========================================================================
    # 1. 发送文件 - 固定文件名搜索 (强校验模式)
    # =========================================================================
    @allure.story('发送文件-固定文件名搜索')
    @allure.title('发送文件-固定文件名搜索并精准强断言-状态：已完成')
    @pytest.mark.parametrize('exact_scenario', EXACT_FILE_SCENARIOS, ids=lambda s: s.desc)
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'),
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_send_file_by_exact_name(self, strategy, exact_scenario: ExactFileScenario):
        """测试通过完整固定文件名搜索并精准发送，执行 100% 强断言校验"""
        allure.dynamic.title(f'固定文件名搜索 | {strategy.desc} - {exact_scenario.desc} ({exact_scenario.exact_file_name})')
        with allure.step(f'1. 进入【{strategy.name}】聊天并打开文件选择页'):
            self._enter_chat_and_open_file_page(strategy.name)
            assert self.chatFilePage.wait_for_file_page_load(), '❌ 未成功进入文件选择页面'
        with allure.step(f'2. 搜索固定文件名并发送: {exact_scenario.exact_file_name}'):
            file_is_selected = self.chatFilePage.search_and_select_file_by_name(exact_scenario.exact_file_name)
            check.is_true(file_is_selected, f'❌ 搜索并选择固定文件失败: {exact_scenario.exact_file_name}')
            self.chatPage.click_add_button()
        with allure.step('3. 验证聊天气泡中文件名 100% 精准匹配'):
            self.chatPage.wait_for_chat_page_load()
            actual_file_name = self.chatFilePage.get_last_file_name_in_chat()
            check.equal(actual_file_name, exact_scenario.exact_file_name, 
                        f'❌ 发送的文件名不一致。预期: {exact_scenario.exact_file_name}, 实际: {actual_file_name}')
        with allure.step('4. 验证消息是否发送成功'):
            time.sleep(0.5)
            result = self.chatPage.get_last_message_send_fail_status()
            check.is_false(result, '❌ 消息发送失败')


    # =========================================================================
    # 2. 发送文件 - 正向流程 (分类 × 选法 × 聊天策略 矩阵覆盖)
    # =========================================================================
    @allure.story('发送文件-正向流程')
    @allure.title('发送文件-正向流程-状态：已完成')
    @pytest.mark.parametrize('category', FILE_CATEGORIES, ids=lambda c: c.desc)
    @pytest.mark.parametrize('select_mode', FILE_SELECT_MODES, ids=lambda m: m.desc)
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_send_file_success(self, strategy, category: FileCategoryScenario, select_mode: FileSelectMode):
        """测试在聊天中成功发送文件：矩阵覆盖各大分类与选取模式"""
        allure.dynamic.title(f'发送文件测试 | {strategy.desc} - {category.desc} - {select_mode.desc}')
        with allure.step(f'1. 选择并发送文件 ({category.desc} - {select_mode.desc})'):
            file_is_selected = self._send_file_message_helper(
                chat_name=strategy.name,
                file_type=category.file_type,
                sub_menu_item=category.sub_menu_item,
                dir_name=category.dir_name,
                select_mode=select_mode.mode,
                target_index=select_mode.target_index
            )
            check.is_true(file_is_selected, f'❌ 未成功选择文件 (分类: {category.desc}, 模式: {select_mode.desc})')
        with allure.step('2. 验证聊天气泡中是否存在文件消息'):
            self.chatPage.wait_for_chat_page_load()
            file_name = self.chatFilePage.get_last_file_name_in_chat()
            check.is_true(bool(file_name), '❌ 聊天气泡中未发现文件消息')
        with allure.step('3. 验证消息是否发送成功'):
            is_success = self.chatPage.wait_for_last_message_send_status()
            check.is_true(is_success, '❌ 消息未在规定时间内发送完成')


    # =========================================================================
    # 3. 发送文件 - 取消返回流程
    # =========================================================================
    @allure.story('发送文件-取消操作')
    @allure.title('发送文件-取消操作-状态：已完成')
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_cancel_send_file(self, strategy):
        """验证进入文件选择页后取消返回"""
        allure.dynamic.title(f'取消发送文件 | {strategy.desc}')
        with allure.step(f'1. 进入【{strategy.name}】聊天并打开文件选择页'):
            self._enter_chat_and_open_file_page(strategy.name)
            result = self.chatFilePage.wait_for_file_page_load()
            check.is_true(result, '❌ 未成功进入文件选择页面')
        with allure.step('2. 点击返回取消发送'):
            self.chatPage.back_to_chat_page()
        with allure.step('3. 验证正确返回聊天页面'):
            result = self.chatPage.verify_is_on_chat_page()
            check.is_true(result, '❌ 取消发送文件后，未能正确回到聊天页面')


    # =========================================================================
    # 4. 消息管理与长按菜单交互
    # =========================================================================
    @allure.story('消息管理-文件撤回')
    @allure.title('消息管理-文件撤回-状态：未完成')
    @pytest.mark.skip(reason='UI元素匹配异常，待修复')
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_revoke_file_message_success(self, strategy):
        """测试发送文件后 2 分钟内成功撤回"""
        allure.dynamic.title(f'文件管理-成功撤回消息【{strategy.desc}】')
        with allure.step('1. 发送一个文件'):
            is_sent = self._send_file_message_helper(strategy.name, file_type='image')
            check.is_true(is_sent, '❌ 辅助发送文件失败')
            self.chatPage.wait_for_chat_page_load()
            check.is_true(self.chatPage.wait_for_last_message_send_status(), '❌ 文件发送未能在规定时间内完成')
        with allure.step('2. 长按消息并点击撤回'):
            self.chatLongPressPage.long_press_last_message()
            is_ok = self.chatLongPressPage._execute_and_verify_menu_item('撤回')
            check.is_true(is_ok, '❌ 长按点击【撤回】操作失败')
        with allure.step('3. 验证撤回状态'):
            withdraw_result = self.chatPage.get_withdraw_message()
            check.is_not_none(withdraw_result, '❌ 未能捕获到预期的撤回提示')
            if withdraw_result:
                notice_text, _ = withdraw_result
                check.is_in('撤回', notice_text, f'❌ 未能捕获到预期的撤回提示文字: {notice_text}')
                logger.info(f'✅ 文件消息撤回验证通过: {notice_text}')


    @allure.story('发送异常-重试机制')
    @allure.title('发送异常-重试机制-状态：未完成')
    @pytest.mark.skip(reason='UI元素匹配异常，待修复')
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_resend_file_on_fail(self, strategy):
        with allure.step('1. 发送文件（模拟环境异常）'):
            is_sent = self._send_file_message_helper(strategy.name, file_type='image')
            check.is_true(is_sent, '❌ 辅助发送文件失败')
        with allure.step('2. 检查是否有失败红点并尝试重发'):
            has_fail = self.chatPage.get_last_message_send_fail_status()
            if has_fail:
                logger.info('🚩 检测到发送失败红点，准备执行重发')
                self.chatPage.click_last_message_resend_button()
                success = self.chatPage.wait_for_last_sent_message_completed()
                check.is_true(success, '❌ 点击重发按钮后，消息仍未发送成功')
            else:
                logger.warning('⚠️ 当前环境网络太好，未触发发送失败场景，跳过重发点击步骤')
                check.is_true(self.chatPage.wait_for_last_sent_message_completed(), '❌ 消息发送状态异常')


    @allure.story('消息管理-文件删除')
    @allure.title('消息管理-文件删除-状态：未完成')
    @pytest.mark.skip(reason='删除功能待完善并接入通用交互逻辑')
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_delete_file_message(self, strategy):
        pass

    @allure.story('消息管理-文件转发')
    @allure.title('消息管理-文件转发-状态：未完成')
    @pytest.mark.skip(reason='转发功能待完善并接入通用交互逻辑')
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_forward_file_message(self, strategy):
        """验证文件消息可以被长按转发"""
        pass


    @allure.story('消息管理-文件收藏')
    @allure.title('消息管理-文件收藏-状态：未完成')
    @pytest.mark.skip(reason='收藏功能待完善并接入通用交互逻辑')
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_favorite_file_message(self, strategy):
        """验证文件消息可以被长按收藏"""
        pass


    @allure.story('消息管理-文件引用回复')
    @allure.title('消息管理-文件引用回复-状态：未完成')
    @pytest.mark.skip(reason='回复功能待完善并接入通用交互逻辑')
    @pytest.mark.parametrize('strategy', [
        pytest.param(PRIVATE_USER1, id='私聊模式'), 
        pytest.param(GROUP_STRATEGY, id='群聊模式')
    ])
    def test_reply_file_message(self, strategy):
        """验证文件消息可以被长按引用回复"""
        pass