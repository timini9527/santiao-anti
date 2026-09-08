import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.common.contact_select_page import ContactSelectPage
from pages.friend.profile.chat_contact_card_page import ChatContactCardPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.common.session_select_page import SessionSelectPage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.profile.group_detail_page import GroupDetailPage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY

@allure.epic('IM核心功能测试')
@allure.feature('聊天面板-名片')
class TestContactCard:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.chatListPage = ChatListPage(driver_sender)
        self.chatContactCardPage = ChatContactCardPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)
        self.sessionSelectPage = SessionSelectPage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupDetailPage = GroupDetailPage(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f'Teardown 失败，未能返回首页: {e}')

    def _enter_chat_and_open_card(self, chat_name: str):
        """进入指定的聊天会话并打开名片面板"""
        self.chatListPage.enter_chat(chat_name)
        self.chatContactCardPage.open_panel_enter_contact_card_page()



    @allure.story('发送好友名片-正向流程')
    @allure.title('发送好友名片-正向流程-状态：已完成')
    @pytest.mark.parametrize('cardName', [pytest.param('测试0222', id='测试0222'), pytest.param('0223OiO', id='0223OiO')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_send_contact_card_success(self, strategy, cardName):
        """测试搜索并发送好友名片"""
        allure.dynamic.title(f'发送好友名片-正向流程【{strategy.desc} - {cardName}】')
        with allure.step(f'1. 进入聊天并打开名片页'):
            self._enter_chat_and_open_card(strategy.name)
        with allure.step(f'2. 选择好友页面没有则进行搜索，选择并确认发送'):
            is_success = self.contactSelectPage.click_contact_by_name(name=cardName)
            check.is_true(is_success, f'❌ 未能成功选择好友 {cardName}')
            self.contactSelectPage.click_confirm()
            self.chatPage.wait_for_chat_page_load()
        with allure.step('3. 验证聊天气泡显示'):
            result, card_info = self.chatPage.verify_card_in_chat(cardName)
            check.is_true(result, f'❌ 聊天气泡中未发现好友 {cardName} 的名片')
        with allure.step(f'4. 点击最后一条名片消息进入资料详情页'):
            self.chatPage.click_last_card_message()
        with allure.step('5. 验证资料详情页信息'):
            is_success = self.contactDetailPage.verify_is_on_detail_page(card_info)
            check.is_true(is_success, '❌ 未进入资料详情页或信息不匹配')
        with allure.step(f'6. 点击发送消息回到聊天页面'):
            self.contactDetailPage.click_send_message()
            check.is_true(self.chatPage.wait_for_chat_page_load(), '❌ 未能成功返回聊天页面')
            chat_object_title = self.chatPage.get_top_name()
            check.equal(chat_object_title, cardName, f'❌ 返回聊天页面后，聊天对象名称与预期不匹配 {chat_object_title}')


    @allure.story('发送好友名片-搜索无结果')
    @allure.title('发送好友名片-搜索无结果-状态：已完成')
    @pytest.mark.parametrize('cardName', [pytest.param('不存在的神秘人999', id='不存在的神秘人999')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_search_contact_no_results(self, strategy, cardName):
        """验证搜索不存在的好友时 UI 表现"""
        allure.dynamic.title(f'发送好友名片-搜索无结果【{strategy.desc}】')
        with allure.step(f'1. 进入聊天并打开名片页'):
            self._enter_chat_and_open_card(strategy.name)
        with allure.step(f'2. 搜索不存在的好友并验证列表为空'):
            is_success = self.contactSelectPage.click_contact_by_name(name=cardName)
            check.is_false(is_success, f'❌ 预期找不到不存在的好友，但返回了成功: {cardName}')
            is_empty = self.contactSelectPage.is_empty_result()
            check.is_true(is_empty, '❌ 预期搜索无结果，但列表不为空')
        with allure.step(f'3. 退出名片选择页并验证返回聊天页面'):
            self.contactSelectPage.click_iv_back_button()
            result = self.chatPage.verify_is_on_chat_page()
            check.is_true(result, '❌ 退出搜索后未正确返回聊天页面')


    @allure.story('发送好友名片-取消操作')
    @allure.title('发送好友名片-取消操作-状态：已完成')
    @pytest.mark.parametrize('cardName', [pytest.param('测试0222', id='测试0222')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_cancel_send_contact_card(self, strategy, cardName):
        """验证在选择好友页面取消后返回聊天页"""
        allure.dynamic.title(f'发送好友名片-取消操作【{strategy.desc}】')
        with allure.step(f'1. 进入聊天'):
            self._enter_chat_and_open_card(strategy.name)
        with allure.step(f'2. 选择好友并取消确认弹窗'):
            is_success = self.contactSelectPage.click_contact_by_name(name=cardName)
            check.is_true(is_success, f'❌ 未能成功选择好友 {cardName}')
            self.contactSelectPage.click_cancel()
        with allure.step(f'3. 退出名片选择页并验证返回聊天页面'):
            self.contactSelectPage.click_iv_back_button()
            result = self.chatPage.verify_is_on_chat_page()
            check.is_true(result, '❌ 点击取消退出后未正确返回聊天页面')


    @allure.story('发送群聊名片-正向流程')
    @allure.title('发送群聊名片-正向流程-状态：已完成')
    @pytest.mark.parametrize('group_card_name', [pytest.param('测试群aaaaa', id='测试群aaaaa')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_send_group_card_success(self, strategy, group_card_name):
        """测试搜索并发送群聊名片"""
        allure.dynamic.title(f'发送群聊名片-正向流程【{strategy.desc} - {group_card_name}】')
        with allure.step(f'0. 确保群聊存在并进入群聊'):
            self.chatListPage.enter_chat(group_card_name)
        with allure.step(f'1. 进入群聊详情页面并选择分享会话'):
            self.chatListPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_share()
            self.sessionSelectPage.wait_for_session_page_load(msg_type=1)
            is_selected = self.sessionSelectPage.select_session_by_name(strategy.name)
            check.is_true(is_selected, f'❌ 选择目标会话失败: {strategy.name}')
        with allure.step(f'2. 确认发送并校验【转发成功】Toast 提示'):
            is_toast = self.sessionSelectPage.send_share_and_verify_toast('转发成功')
            check.is_true(is_toast, '❌ 转发群名片后未捕获到【转发成功】Toast 提示')
            self.mainPage.go_to_main_page()
        with allure.step(f'3. 进入聊天并验证群聊名片信息'):
            self.chatListPage.enter_chat(strategy.name)
            result, card_info = self.chatPage.verify_card_in_chat(group_card_name)
            check.is_true(result, f'❌ 聊天气泡中未发现群聊 {group_card_name} 的名片')
        with allure.step(f'4. 点击群聊名片进入群资料页面'):
            self.chatPage.click_last_card_message()
            is_success = self.groupDetailPage.verify_is_on_group_detail_page(group_card_name)
            check.is_true(is_success, '❌ 未进入群资料详情页或群名称不匹配')
        with allure.step(f'5. 点击发送消息/加入群聊进入群聊，验证聊天对象名称'):
            self.groupDetailPage.click_send_message_or_join()
            check.is_true(self.chatPage.wait_for_chat_page_load(), '❌ 未能成功进入群聊页面')
            chat_object_title = self.chatPage.get_top_name()
            check.is_in(group_card_name, chat_object_title, f'❌ 返回聊天页面后，聊天对象名称与预期不匹配，{chat_object_title}')


    @allure.story('分享群聊名片-取消操作')
    @allure.title('分享群聊名片-取消操作-状态：已完成')
    @pytest.mark.parametrize('group_card_name', [pytest.param('测试群aaaaa', id='测试群aaaaa')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_cancel_send_group_card(self, strategy, group_card_name):
        """验证在分享群聊名片时，弹出确认弹窗后点击取消并安全返回"""
        allure.dynamic.title(f'分享群聊名片-取消操作【{strategy.desc} - {group_card_name}】')
        with allure.step(f'1. 确保群聊存在并进入群聊'):
            self.chatListPage.enter_chat(group_card_name)
        with allure.step(f'2. 进入群聊详情页面并点击分享群名片'):
            self.chatListPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_share()
            self.sessionSelectPage.wait_for_session_page_load(msg_type=1)
        with allure.step(f'3. 选择目标会话唤起确认弹窗，并点击弹窗【取消】按钮'):
            is_selected = self.sessionSelectPage.select_session_by_name(strategy.name)
            check.is_true(is_selected, f'❌ 选择目标会话失败: {strategy.name}')
            is_dialog = self.sessionSelectPage.wait_for_share_dialog_load()
            check.is_true(is_dialog, '❌ 未能成功唤起分享确认弹窗')
            self.sessionSelectPage.click_share_dialog_close()
        with allure.step(f'4. 在选择会话页点击返回退出'):
            self.sessionSelectPage.click_back_button()
        with allure.step(f'5. 验证成功返回群设置页并切回聊天页'):
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_iv_back_button()
            result = self.chatPage.verify_is_on_chat_page()
            check.is_true(result, '❌ 取消群名片分享后，未能正确回到聊天页')