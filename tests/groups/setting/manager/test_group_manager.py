import pytest
import allure
import pytest_check as check
from datetime import datetime, timedelta
from core.logger_utils import logger, LogIcon
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY

@allure.epic('IM核心功能测试')
@allure.feature('群聊模块-群管理')
class TestGroupManager:
    """群管理子页面相关功能测试"""

    @pytest.fixture(autouse=True)
    def setup_method(self, driver_sender):
        """初始化页面对象并自动导航进入群管理页面"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupManagerPage = GroupManagerPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self._enter_group_manager()
        yield
        self.mainPage.go_to_main_page()

    def _enter_group_setting(self):
        """内部辅助：进入群详情设置页"""
        with allure.step('-> 进入群详情设置页'):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
        with allure.step('-> 进入【群管理】子页面'):
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_group_manager_page_load()

    def _enter_group_manager(self):
        """内部辅助：快速建群并导航进入群管理页面"""
        with allure.step('-> [前置准备] 进入群聊'):
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
        self._enter_group_setting()

    @allure.story('群管理-升级群组')
    @allure.title('【升级群组】功能正常使用校验-状态：未完成')
    @pytest.mark.skip('升级群组功能未实现')
    def test_upgrade_group_functionality(self):
        """测试【升级群组】功能是否正常使用"""
        with allure.step('1. 点击升级群组'):
            self.groupManagerPage.click_upgrade_group()

    @allure.story('群管理-提升群活跃')
    @allure.title('【提升群活跃】入口及今日活跃点查看-状态：未完成')
    @pytest.mark.skip('提升群活跃功能未实现/待验证')
    def test_improve_group_activity_functionality(self):
        """测试群管理中【提升群活跃】入口跳转及今日活跃点展示"""
        with allure.step('1. 校验【提升群活跃】项标题与今日活跃点'):
            title = self.groupManagerPage.get_group_active_point_title()
            check.is_in('提升群活跃', title, f'❌ 【提升群活跃】项标题不匹配: {title}')
            points_text = self.groupManagerPage.get_group_activity_points()
            logger.info(f"{LogIcon.ACTION} 今日活跃点: {points_text}")
        with allure.step('2. 点击提升群活跃入口'):
            self.groupManagerPage.click_improve_group_activity()
        with allure.step('3. 返回群管理'):
            self.groupManagerPage.click_iv_back_button()

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('群管理-管理员')
    @allure.title('【群管理员】功能正常使用校验-状态：已完成')
    def test_group_manager_functionality(self):
        """测试【群管理员】功能是否正常使用"""
        with allure.step('1. 点击群管理员，并添加管理员'):
            self.groupManagerPage.click_administrators()
            self.groupManagerPage.click_add_admin()
        with allure.step('2. 准备群管理员数据'):
            self.groupManagerPage.click_member_by_name(name=PRIVATE_USER1.name)
        with allure.step('3. 点击新增群管理员'):
            self.groupManagerPage.click_all_switch(checked_str='false')
            self.groupManagerPage.click_confirm_button()
            self.chatPage.wait_banner_message_disappear()
        with allure.step('4. 返回管理员列表，并校验管理员状态'):
            member_names = self.groupManagerPage.get_member_names()
            check.is_in(PRIVATE_USER1.name, member_names, '❌ [Action-groupManagerPage] 添加管理员失败')
        with allure.step('5. 移除管理员'):
            self.groupManagerPage.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerPage.click_sure_button()
            self.groupManagerPage.click_sure_content_button()
            self.chatPage.wait_banner_message_disappear()
            member_names = self.groupManagerPage.get_member_names()
            check.is_not_in(PRIVATE_USER1.name, member_names, '❌ [Action-groupManagerPage] 移除管理员失败')

    @allure.story('群管理-添加群助手')
    @allure.title('【添加群助手】入口及状态显示校验-状态：未完成')
    @pytest.mark.skip('添加群助手功能未实现/待验证')
    def test_add_group_assistant_entry(self):
        """测试群管理中【添加群助手】入口点击及助手状态展示"""
        with allure.step('1. 校验【添加群助手】标题及当前配置状态'):
            title = self.groupManagerPage.get_group_assistant_title()
            check.is_in('群助手', title, f'❌ 【添加群助手】标题不匹配: {title}')
            status = self.groupManagerPage.get_group_assistant_status()
            logger.info(f"{LogIcon.ACTION} 群助手状态: {status}")
        with allure.step('2. 点击添加群助手入口'):
            self.groupManagerPage.click_add_group_assistant()
        with allure.step('3. 返回群管理页面'):
            self.groupManagerPage.click_iv_back_button()

    @allure.story('群管理-群ID搜索开关')
    @allure.title('切换【群ID搜索】开关状态校验-状态：已完成')
    @pytest.mark.skip('群ID搜索功能未实现')
    def test_group_id_search_toggle(self):
        """测试群管理中【群ID搜索】开关的状态切换与校验"""
        with allure.step('1. 获取当前群ID搜索开关状态'):
            init_state = self.groupManagerPage.get_group_id_search_state()
        with allure.step('2. 点击切换群ID搜索开关'):
            self.groupManagerPage.click_group_id_search_switch()
            new_state = self.groupManagerPage.get_group_id_search_state()
            check.not_equal(init_state, new_state, '❌ 【群ID搜索】开关点击后状态未改变')
        with allure.step('3. 再次点击开关恢复至初始状态'):
            self.groupManagerPage.click_group_id_search_switch()
            final_state = self.groupManagerPage.get_group_id_search_state()
            check.equal(init_state, final_state, '❌ 【群ID搜索】开关恢复初始状态失败')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('群管理-进群验证开关')
    @allure.title('切换【进群验证】开关状态校验-状态：已完成')
    def test_join_group_verify_toggle(self):
        """测试群管理中【进群验证】开关的状态切换与校验"""
        with allure.step('1. 开启进群验证'):
            self.groupManagerPage.click_join_group_verify_switch(checked_str='true')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('2. 回到聊天页面中，并校验进群验证开关状态'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('已启用"群聊邀请确认"', cmd_texts, '❌ [Action-groupManagerPage] 进群验证开关未开启')
        with allure.step('3. 再次点击开关恢复至初始状态'):
            self._enter_group_setting()
            self.groupManagerPage.click_join_group_verify_switch(checked_str='false')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('4. 回到聊天页面中，并校验进群验证关闭后Banner消息'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('已恢复默认进群模式', cmd_texts, '❌ [Action-groupManagerPage] 进群验证开关未关闭')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('群管理-全员禁言开关')
    @allure.title('切换【全员禁言】开关状态校验-状态：已完成')
    def test_all_member_mute_toggle(self):
        """测试群管理中【全员禁言】开关的状态切换与校验"""
        with allure.step('1. 开启全员禁言'):
            self.groupManagerPage.click_all_member_mute_switch(checked_str='true')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('2. 回到聊天页面中，并校验全员禁言开启状态'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('开启全员禁言', cmd_texts, '❌ [Action-groupManagerPage] 全员禁言开关未开启')
        with allure.step('3. 再次点击开关恢复至初始状态'):
            self._enter_group_setting()
            self.groupManagerPage.click_all_member_mute_switch(checked_str='false')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('4. 回到聊天页面中，并校验全员禁言关闭后Banner消息'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('关闭全员禁言', cmd_texts, '❌ [Action-groupManagerPage] 全员禁言开关未关闭')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('群管理-指定成员禁言')
    @allure.title('指定成员禁言页面初始状态校验-状态：已完成')
    @pytest.mark.parametrize('mute_type, duration', [pytest.param(0, 0, id='永久禁言'), pytest.param(1, '10分钟', id='临时禁言-10分钟'), pytest.param(1, '30分钟', id='临时禁言-30分钟'), pytest.param(1, '2小时', id='临时禁言-2小时'), pytest.param(1, '1天', id='临时禁言-1天'), pytest.param(1, '3天', id='临时禁言-3天'), pytest.param(1, '7天', id='临时禁言-7天'), pytest.param(1, '30天', id='临时禁言-30天')])
    def test_specify_mute_page_init_state(self, mute_type, duration):
        """测试进入指定成员禁言页面时，默认无已禁言成员的状态"""
        with allure.step('1. 进入【指定成员禁言】子页面'):
            self.groupManagerPage.click_mute_member()
            self.groupManagerPage.wait_for_specify_mute_page_load()
            self.groupManagerPage.click_confirm_button()
        with allure.step('2. 添加指定禁言成员'):
            self.groupManagerPage.input_member_search_keyword(PRIVATE_USER1.name)
            self.groupManagerPage.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerPage.click_edit_finish_button()
        with allure.step('3. 选择禁言类型和时长'):
            if mute_type == 0:
                self.groupManagerPage.click_cb_1()
            else:
                self.groupManagerPage.click_cb_2()
                self.groupManagerPage.click_temp_mute_time()
                self.groupManagerPage.click_set_mute_duration(duration)
            self.groupManagerPage.click_sure_button()
            self.groupManagerPage.click_mute_confirm_btn()
        with allure.step('4. 验证禁言状态'):
            res = self.groupManagerPage.get_mute_status(PRIVATE_USER1.name)
            if mute_type == 0:
                check.is_in('永久禁言', res, f'❌ [Action-groupManagerPage] 指定成员禁言状态未生效: {res}')
            else:
                check.is_in('预计', res, f'❌ [Action-groupManagerPage] 指定成员禁言状态未生效: {res}')
                check.is_in('恢复', res, f'❌ [Action-groupManagerPage] 指定成员禁言状态未生效: {res}')

                def get_expected_delta(d_str: str) -> timedelta:
                    if '分钟' in d_str:
                        return timedelta(minutes=int(d_str.replace('分钟', '')))
                    elif '小时' in d_str:
                        return timedelta(hours=int(d_str.replace('小时', '')))
                    elif '天' in d_str:
                        return timedelta(days=int(d_str.replace('天', '')))
                    return timedelta(0)
                try:
                    time_str = res.replace('预计', '').replace('恢复', '').strip()
                    actual_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                    expected_time = datetime.now() + get_expected_delta(duration)
                    diff_seconds = abs((actual_time - expected_time).total_seconds())
                    check.less(diff_seconds, 120, f'❌ [Action-groupManagerPage] 禁言恢复时间不符: 预期约 {expected_time}, 实际 {actual_time}')
                except Exception as e:
                    pytest.fail(f'❌ [Action-groupManagerPage] 解析/校验禁言恢复时间失败: {res}, Error: {e}')
        with allure.step('5. 点击移除禁言'):
            self.groupManagerPage.click_cancel_mute(PRIVATE_USER1.name)
            self.groupManagerPage.click_iv_back_button()
            self.groupManagerPage.click_iv_back_button()
            self.groupManagerPage.click_iv_back_button()

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('群管理-禁止群成员互相加好友开关')
    @allure.title('切换【禁止群成员互相加好友】开关状态校验-状态：已完成')
    def test_un_add_friend_each_other_toggle(self):
        """测试群管理中【禁止群成员互相加好友】开关的状态切换与校验"""
        with allure.step('1. 开启禁止群成员互相加好友'):
            self.groupManagerPage.click_un_add_friend_each_other_switch(checked_str='true')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('2. 回到聊天页面中，并校验禁止互相加好友开启状态'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('开启群内禁止添加好友', cmd_texts, '❌ [Action-groupManagerPage] 禁止群成员互相加好友开关未开启')
        with allure.step('3. 再次点击开关恢复至初始状态'):
            self._enter_group_setting()
            self.groupManagerPage.click_un_add_friend_each_other_switch(checked_str='false')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('4. 回到聊天页面中，并校验关闭后的Banner消息'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('关闭群内禁止添加好友', cmd_texts, '❌ [Action-groupManagerPage] 禁止群成员互相加好友开关未关闭')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('群管理-群主transfer')
    @allure.title('转让群主功能校验-状态：已完成')
    def test_transfer_group_owner(self):
        """测试群管理中【转让群主】功能"""
        new_owner_name = '1234567890'
        with allure.step('1. 转让群主转让给自己'):
            self.groupManagerPage.click_group_give()
            self.groupManagerPage.click_member_by_name(name=new_owner_name)
        with allure.step('2. 验证toast：你已经是群主'):
            toasts = self.chatPage.get_toast()
            check.is_in('你已经是群主', toasts, f'❌ [Action-groupManagerPage] 转让群主失败，toast: {toasts}')
        with allure.step('3. 退出群管理页面'):
            self.groupManagerPage.click_iv_back_button()

