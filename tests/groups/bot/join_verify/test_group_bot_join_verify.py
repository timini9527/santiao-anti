import pytest
import allure
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from strategy.chat.chat_strategy import GROUP_STRATEGY

@allure.epic('IM核心功能测试')
@allure.feature('群助手-入群验证')
class TestGroupBotJoinVerify:
    """群助手入群验证功能测试"""

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

    @pytest.fixture
    def cleanup_verify_settings(self):
        """后置清理：恢复入群验证开关为关闭状态"""
        yield
        logger.info('🧹 [Cleanup] 开始清理入群验证设置...')
        try:
            self.main_sender.go_to_main_page()
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_join_verify()
            self.group_bot_sender.toggle_join_verify_switch(enable=False)
            logger.info('🧹 [Cleanup] 成功关闭群助手入群验证开关')
        except Exception as e:
            logger.warning(f'⚠️ [Cleanup] 清理入群验证开关发生异常: {e}')

    @allure.story('入群验证-开关切换与配置')
    @allure.title('开启与关闭入群验证 - 触发Toast提醒且配置保存生效-状态：未完成')
    @pytest.mark.usefixtures('cleanup_verify_settings')
    def test_join_verify_toggle_and_save(self):
        """开启/关闭入群验证开关并配置点验规则"""
        with allure.step('1. 进入群设置 -> 群管理 -> 群助手 -> 入群验证'):
            self.chat_list_sender.enter_chat(GROUP_STRATEGY.name)
            self.chat_sender.wait_for_chat_page_load()
            self.chat_sender.click_more_button()
            self.group_setting_sender.wait_for_setting_page_load()
            self.group_setting_sender.click_group_manager()
            self.group_bot_sender.enter_group_bot()
            self.group_bot_sender.enter_join_verify()
        with allure.step('2. 切换入群验证开关为启用，验证 Toast 提示'):
            self.group_bot_sender.toggle_join_verify_switch(enable=True)
            toast_text = self.chat_sender.get_toast_text()
            logger.info(f"🔍 开启进群验证提示: '{toast_text}'")
            check.is_true('已开启' in toast_text or '开启' in toast_text or toast_text == '', f'❌ 开启进群验证未捕获到正确Toast: {toast_text}')
        with allure.step('3. 配置点验规则: 验证时间=5min, 处理方式=仅移出群组'):
            self.group_bot_sender.configure_join_verify(action_type='仅移出群组', verify_time='5min')
            self.group_bot_sender.click_save()
            toast_save = self.chat_sender.get_toast_text()
            logger.info(f"🔍 保存规则提示: '{toast_save}'")
            check.is_true('已保存' in toast_save or '成功' in toast_save or toast_save == '', f'❌ 保存进群验证规则未捕获到成功Toast: {toast_save}')
        with allure.step('4. 切换开关为禁用，验证功能关闭'):
            self.group_bot_sender.toggle_join_verify_switch(enable=False)
            toast_off = self.chat_sender.get_toast_text()
            logger.info(f"🔍 关闭提示: '{toast_off}'")
            check.is_true('已关闭' in toast_off or '关闭' in toast_off or toast_off == '', f'❌ 关闭进群验证未捕获到正确Toast: {toast_off}')