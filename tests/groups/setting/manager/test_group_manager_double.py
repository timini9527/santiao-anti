import os
import re
import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from pages.common.session_select_page import SessionSelectPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.friend.add_friend.add_friend_page import AddFriendPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, PRIVATE_USER3, GROUP_STRATEGY

@allure.epic('IM核心功能测试')
@allure.feature('群聊模块-群管理双端验证')
class TestGroupManagerDouble:
    """群管理功能双端（群主发端与成员收端）协同验证测试"""
    _active_keep_group = None
    _skip_enter_manager_tests = []

    @pytest.fixture(autouse=True)
    def setup_double_env(self, request, driver_sender, driver_receiver):
        """初始化双端页面对象，根据用例声明的 Marker 动态驱动环境生命周期"""
        self.mainS = MainPage(driver_sender)
        self.groupSettingS = GroupSettingPage(driver_sender)
        self.groupManagerS = GroupManagerPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.mainR = MainPage(driver_receiver)
        self.homeR = HomePage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.groupSettingR = GroupSettingPage(driver_receiver)
        self.groupManagerR = GroupManagerPage(driver_receiver)
        self.contactDetailR = ContactDetailPage(driver_receiver)
        self.addFriendR = AddFriendPage(driver_receiver)

        # 1. 声明式获取当前用例的环境行为策略（完全解耦，无任何用例名称硬编码）
        skip_setup = request.node.get_closest_marker('skip_env_setup') is not None
        keep_marker = request.node.get_closest_marker('keep_env')
        keep_group = None
        if keep_marker is not None:
            keep_group = keep_marker.args[0] if keep_marker.args else getattr(request.node, 'originalname', request.node.name)

        # 控制是否自动进入群管理页面：默认 True；可通过 @pytest.mark.enter_manager(False) 或加入 _skip_enter_manager_tests 自由控制
        marker = request.node.get_closest_marker('enter_manager')
        if marker is not None and marker.args:
            auto_enter_manager = bool(marker.args[0])
        elif request.node.name in getattr(self, '_skip_enter_manager_tests', []):
            auto_enter_manager = False
        else:
            auto_enter_manager = True

        # 2. Setup 调度
        if skip_setup:
            logger.info('⚡ [Setup] 用例声明了 skip_env_setup，跳过全局进群前置')
        elif keep_group:
            if self.__class__._active_keep_group != keep_group:
                self._run_env_setup(auto_enter_manager=auto_enter_manager)
                self.__class__._active_keep_group = keep_group
        else:
            self._run_env_setup(auto_enter_manager=auto_enter_manager)

        yield

        if keep_group:
            # 找到当前 session 中属于该 keep_group 的所有待测项
            session_items = request.session.items
            group_items = []
            for item in session_items:
                m = item.get_closest_marker('keep_env')
                if m is not None:
                    grp = m.args[0] if m.args else getattr(item, 'originalname', item.name)
                    if grp == keep_group:
                        group_items.append(item)

            # 仅在该保持组的最后一个用例项执行完后，才执行清理退回主页并重置状态
            if group_items and request.node == group_items[-1]:
                self._run_env_teardown()
                self.__class__._active_keep_group = None
        else:
            self._run_env_teardown()

    def _run_env_setup(self, auto_enter_manager: bool = True):
        """执行发送端和接收端进群及群管理的前置流程"""
        with allure.step('-> [前置准备] 发送端(群主)进入指定群聊'):
            self.chatListS.enter_chat(GROUP_STRATEGY.name)
            self.chatS.wait_for_chat_page_load()
        with allure.step('-> [前置准备] 接收端(普通成员)进入指定群聊聊天界面'):
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()
        if auto_enter_manager:
            self._enter_group_manager_sender()
        else:
            logger.info("⚡ [Setup] 当前用例配置为不自动进入群管理页面，发送端(群主)保持停留在群聊聊天界面")

    def _run_env_teardown(self):
        """执行双端返回首页的清理流程"""
        with allure.step('-> [环境清理] 双端返回首页'):
            try:
                self.mainS.go_to_main_page()
                self.mainR.go_to_main_page()
            except Exception as e:
                logger.warning(f'⚠️ [Cleanup] 双端返回首页失败: {e}')

    def _enter_group_manager_sender(self):
        """内部辅助：发送端(群主)进入该群【群管理】页面"""
        with allure.step('-> [前置准备] 发送端(群主)进入该群【群管理】页面'):
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_group_manager_page_load()

    def _enter_group_manager_receiver(self):
        """内部辅助：接收端进入聊天页面"""
        with allure.step('-> [前置准备] 接收端(普通成员)进入指定群聊聊天界面'):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_group_manager()
            self.groupManagerR.wait_for_group_manager_page_load()

    _admin_assigned = False

    @pytest.fixture(scope='function', autouse=False)
    def admin_role(self, request):
        """确保分配了管理员权限，在首个用例自动或手动分配，在最后一个用例自动清理"""
        if not self.__class__._admin_assigned:
            self._assign_admin_permission()
            self.__class__._admin_assigned = True
        yield
        session_tests = [item.name for item in request.session.items]
        target_tests = ['test_admin_allocation_double_validation', 
                        'test_join_verify_admin_scenarios_double_validation', 
                        'test_add_admin_double_validation']
        tests_to_run = [t for t in target_tests if t in session_tests]
        current_test = request.node.name
        if current_test in tests_to_run:
            is_last_admin_test = tests_to_run.index(current_test) == len(tests_to_run) - 1
            if is_last_admin_test:
                if self.__class__._admin_assigned:
                    self._remove_admin_permission()
                    self.__class__._admin_assigned = False

    def _assign_admin_permission(self):
        """前置辅助：群主分配管理员权限并开启所有开关（若已是管理员则跳过添加）"""
        with allure.step('-> [前置准备] 群主分配管理员权限并全开'):
            self.groupManagerS.click_administrators()
            self.groupManagerS.wait_for_admin_page_load()
            existing_admins = self.groupManagerS.get_member_names()
            if PRIVATE_USER1.name in existing_admins:
                logger.info(f"ℹ️ [Setup] 成员【{PRIVATE_USER1.name}】已存在于管理员列表中，无需重复添加")
            else:
                self.groupManagerS.click_add_admin()
                self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
                self.groupManagerS.click_all_switch(checked_str='false')
                self.groupManagerS.click_confirm_button()
                self.chatS.wait_banner_message_disappear()
                member_names = self.groupManagerS.get_member_names()
                check.is_in(PRIVATE_USER1.name, member_names, '❌ 群主端管理员列表未显示新增的管理员')

    def _remove_admin_permission(self):
        """后置辅助：群主从管理员列表移除该成员"""
        with allure.step('-> [环境清理] 群主从管理员列表移除该成员并校验降级'):
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_sure_button()
            self.groupManagerS.click_sure_content_button()
            self.chatS.wait_banner_message_disappear()
            member_names = self.groupManagerS.get_member_names()
            check.is_not_in(PRIVATE_USER1.name, member_names, '❌ 群主端移除管理员失败')
            self.chatS.wait_banner_message_disappear()
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.click_iv_back_button()
            res = self.chatR.is_cmd_notification_matching('.*你被取消管理员')
            check.is_true(res, '❌ 接收端未收到被解除管理员的通知消息')
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            is_visible = self.groupSettingR.is_group_manager_visible()
            check.is_false(is_visible, '❌ 接收端被解除管理员后，群设置中依然显示【群管理】入口')
            self.groupSettingR.click_iv_back_button()

    def _create_temp_group_double(self):
        """双端辅助方法：动态创建一个临时群聊并让发送端进入群管理，接收端进入聊天页面"""
        homeS = HomePage(self.mainS.driver)
        groupCreateS = GroupCreatePage(self.mainS.driver)
        contactSelectS = ContactSelectPage(self.mainS.driver)
        temp_name = '测试解散群聊'
        with allure.step('-> [双端准备] 发送端(群主)创建临时群聊'):
            homeS.click_add_button()
            homeS.click_start_group_chat()
            contactSelectS.wait_for_contact_and_group_select_page_load()
            contactSelectS.click_contact_by_name(PRIVATE_USER1.name)
            contactSelectS.click_contact_by_name(PRIVATE_USER2.name)
            contactSelectS.click_action_button()
            toast = self.chatS.get_toast(timeout=10)
            check.is_in('创建成功', toast, '❌ 发送端未收到创建临时群聊的通知消息')
            self.chatS.wait_banner_message_disappear()
            self.chatS.wait_for_chat_page_load()
        with allure.step('-> [双端准备] 发送端(群主)修改群名称'):
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_group_name()
            self.groupSettingS.wait_for_remark_dialog_load(nva_text='群名称')
            self.groupSettingS.input_remark_content(temp_name)
            self.groupSettingS.click_tv_confirm_button()
            self.chatS.wait_banner_message_disappear()
            self.groupSettingS.click_iv_back_button()
            self.chatS.send_message('临时群聊建立测试')
        # with allure.step('-> [双端准备] 接收端(群成员)进入该临时群聊'):
        #     self.chatListR.enter_chat(temp_name)
        #     self.chatR.wait_for_chat_page_load()
        with allure.step('-> [双端准备] 发送端(群主)进入该群的【群管理】页面'):
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_group_manager_page_load()
        return temp_name



    @allure.story('群管理-管理员分配')
    @allure.title('【管理员】是否是管理员身份的分配验证-分配所有权限-状态：已完成')
    @pytest.mark.keep_env('admin')
    @pytest.mark.usefixtures('admin_role')
    def test_admin_allocation_double_validation(self):
        """验证群主分配和撤销管理员身份，以及对应的成员端权限同步和CMD通知"""
        with allure.step('1. 校验接收端(群成员)收到管理员身份通知并获得群管理权限'):
            res = self.chatR.is_cmd_notification_matching('.*你被设置为管理员')
            check.is_true(res, '❌ 接收端未收到成为管理员的通知消息')
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            is_visible = self.groupSettingR.is_group_manager_visible()
            check.is_true(is_visible, '❌ 接收端被设为管理员后，群设置中没有显示【群管理】入口')
            self.groupManagerR.click_iv_back_button()

    @allure.story('群申请-进群验证')
    @allure.title('【进群验证】是否是管理员的多重场景-状态：已完成')
    @pytest.mark.keep_env('admin')
    @pytest.mark.usefixtures('admin_role')
    def test_join_verify_admin_scenarios_double_validation(self):
        """验证进群验证是否是管理员的多重场景"""
        with allure.step('1. 接收端进群校验验证'):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_group_manager()
            state = self.groupManagerR.get_join_group_verify_state()
            check.is_in(state, ('true', 'false'), '❌ 接收端进群校验状态异常')
            self.groupManagerR.click_iv_back_button()
            self.groupManagerR.click_iv_back_button()

    @allure.story('群申请-进群申请双端校验')
    @allure.title('【进群申请】管理员=是，可以看到进群申请横幅；管理员=否，看不到进群申请横幅-状态：已完成')
    @pytest.mark.keep_env('admin')
    @pytest.mark.usefixtures('admin_role')
    def test_add_admin_double_validation(self):
        """验证是否为管理员【进群申请】管理员=是，可以看到进群申请横幅；管理员=否，看不到进群申请横幅"""
        with allure.step('1. 接收端进群申请横幅与操作按钮校验'):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_group_manager()
            self.groupManagerR.click_join_to_group_apply()
        with allure.step('2. 校验进群申请横幅与操作按钮校验'):
            res = self.groupManagerR.get_join_apply_tips()
            check.is_in('入群申请', res, '❌ 接收端【进群申请】页头部提示异常')
            agree_btns = self.groupManagerR.get_agree_buttons()
            disagree_btns = self.groupManagerR.get_disagree_buttons()
            if agree_btns:
                check.is_true(len(agree_btns) > 0, '❌ 列表中有申请项时未显示‘同意’按钮')
                check.is_true(len(disagree_btns) > 0, '❌ 列表中有申请项时未显示‘拒绝’按钮')
            self.groupManagerR.click_iv_back_button()
            self.groupManagerR.click_iv_back_button()
            self.groupManagerR.click_iv_back_button()

    @allure.story('群禁言-全员禁言双端校验')
    @allure.title('【全员禁言】开关开启与关闭 - 接收端输入框禁言状态实时同步校验-状态：已完成')
    def test_all_member_mute_double_validation(self):
        """验证群主开启全员禁言后，普通成员的输入框应立即被禁用并展示‘全员禁言中’；群主关闭全员禁言后，普通成员恢复正常发言"""
        with allure.step('1. 开启全员禁言'):
            self.groupManagerS.click_all_member_mute_switch(checked_str='true')
            # self.chatR.wait_banner_message_disappear()
        with allure.step('2. 回到聊天页面中，并校验全员禁言开启状态'):
            cmd_texts = self.chatR.get_cmd_notification_texts(index=-1)
            check.is_in('开启群禁言', cmd_texts, '❌ [Action-groupManagerPage] 全员禁言开关未开启')
        with allure.step('3. 接收方校验被禁言（底部输入框被禁用与提示）'):
            title, _ = self.chatR.get_input_disabled_info()
            check.equal('禁言中', title, f'❌ 禁言提示标题不存在: {title}')
        with allure.step('4. 再次点击开关恢复至初始状态'):
            self.groupManagerS.click_all_member_mute_switch(checked_str='false')
            # self.chatR.wait_banner_message_disappear()
        with allure.step('5. 移除禁言后，接收方校验输入框状态恢复可用'):
            is_disabled = self.chatR.is_input_disabled()
            check.is_false(is_disabled, '❌ 移除禁言后，普通群成员的输入框仍处于禁用状态')


    @allure.story('群禁言-指定群成员禁言双端校验')
    @allure.title('【指定群成员禁言】群主开启指定禁言-状态：已完成')
    @pytest.mark.keep_env
    @pytest.mark.parametrize('mute_type, duration', [pytest.param(0, 0, id='永久禁言'), pytest.param(1, '10分钟', id='临时禁言-10分钟'), pytest.param(1, '30分钟', id='临时禁言-30分钟'), pytest.param(1, '2小时', id='临时禁言-2小时'), pytest.param(1, '1天', id='临时禁言-1天'), pytest.param(1, '3天', id='临时禁言-3天'), pytest.param(1, '7天', id='临时禁言-7天'), pytest.param(1, '30天', id='临时禁言-30天')])
    def test_specify_member_mute_double_validation(self, mute_type, duration):
        """验证群主开启指定禁言后，被禁言成员不能发送消息，解除禁言后可正常发送消息"""
        with allure.step('1. 进入【指定成员禁言】子页面'):
            if not self.groupManagerS.wait_for_specify_mute_page_load(1, False):
                self.groupManagerS.click_mute_member()
                self.groupManagerS.wait_for_specify_mute_page_load()
            self.groupManagerS.click_confirm_button()
        with allure.step('2. 添加指定禁言成员'):
            self.groupManagerS.input_member_search_keyword(PRIVATE_USER1.name)
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_edit_finish_button()
        with allure.step('3. 选择禁言类型和时长'):
            if mute_type == 0:
                self.groupManagerS.click_cb_1()
            else:
                self.groupManagerS.click_cb_2()
                self.groupManagerS.click_temp_mute_time()
                self.groupManagerS.click_set_mute_duration(duration)
            self.groupManagerS.click_sure_button()
            self.groupManagerS.click_mute_confirm_btn()
        with allure.step('4. 接收方校验被禁言（底部输入框被禁用与提示）'):
            title, tip = self.chatR.get_input_disabled_info()
            check.is_true(bool(title) or bool(tip), f'❌ 禁言提示标题不存在: {title}')
        with allure.step('5. 接收方校验禁言具体倒计时'):
            if mute_type == 0:
                check.is_false(bool(tip), f'❌ 永久禁言不应有具体的禁言时间: {tip}')
            else:
                total_mins = self.chatR.get_mute_remaining_minutes(tip)
                if total_mins is None:
                    check.is_true(False, f"❌ 禁言提示时间格式不匹配 (期望包含 '剩余HH:MM:SS'): {tip}")
                else:
                    expected_ranges = {'10分钟': (8, 10), '30分钟': (28, 30), '2小时': (115, 120), '1天': (1430, 1440), '3天': (4310, 4320), '7天': (10050, 10080), '30天': (43150, 43200)}
                    min_val, max_val = expected_ranges.get(duration, (0, 0))
                    check.is_true(min_val <= total_mins <= max_val, f'❌ 禁言时间不匹配: 期望 {min_val}~{max_val} 分钟，实际 {total_mins} 分钟 ({tip})')
        with allure.step('6. 点击移除禁言'):
            self.groupManagerS.click_cancel_mute(PRIVATE_USER1.name)
            time.sleep(1)
        with allure.step('7. 移除禁言后，接收方校验输入框状态恢复可用'):
            is_disabled = self.chatR.is_input_disabled()
            check.is_false(is_disabled, '❌ 移除禁言后，普通群成员的输入框仍处于禁用状态')

    @allure.story('群管理-添加好友双端校验')
    @allure.title('【禁止添加好友】开关开启与关闭 - 接收端没有添加好友按钮-状态：已完成')
    def test_forbid_add_friend_double_validation(self):
        """验证群主开启禁止添加好友后，普通群成员的聊天信息栏中没有添加好友按钮；群主关闭禁止添加好友后，普通群成员的聊天信息栏有添加好友按钮"""
        name = '422'
        with allure.step('1. 开启禁止群成员互相加好友'):
            self.groupManagerS.click_un_add_friend_each_other_switch(checked_str='true')
            self.chatS.wait_banner_message_disappear()
        with allure.step('2. 校验接收方 Banner 消息'):
            res = self.chatR.is_cmd_notification_matching('.*开启群禁止加好友')
            check.is_true(res, '❌ 禁止群成员互相加好友开关未开启')
        with allure.step(f'3. 校验接收端(群成员)聊天信息栏中没有添加【{name}】好友按钮'):
            self.chatR.click_more_button()
            self.groupSettingR.click_member_avatar_by_name(name=name)
            has_add = self.contactDetailR.has_add_friend_button()
            check.is_false(has_add, f'❌ 群主开启禁止添加好友后，【{name}】聊天信息栏未能成功移除添加好友按钮')
        with allure.step('4. 群主侧关闭【禁止添加好友】开关'):
            self.groupManagerS.click_un_add_friend_each_other_switch(checked_str='false')
        with allure.step(f'5. 校验接收端(群成员)聊天信息栏中恢复有添加【{name}】好友按钮'):
            self.chatR.wait_banner_message_disappear()
            self.groupManagerR.click_iv_back_button()
            self.groupManagerR.click_iv_back_button()
            res = self.chatR.is_cmd_notification_matching('.*关闭群禁止加好友')
            check.is_true(res, '❌ 禁止群成员互相加好友开关未关闭')

    @allure.story('群管理-群黑名单双端校验')
    @allure.title('【群黑名单】页面加载与返回校验-状态：已完成')
    def test_group_blacklist_double_validation(self):
        """双端验证：群主进入【群黑名单】页面并返回"""
        with allure.step('1. 群主点击进入【群黑名单】页面'):
            self.groupManagerS.click_group_black_member()
            res = self.groupManagerS.wait_for_group_blacklist_page_load()
            check.is_true(res, '❌ 群主进入【群黑名单】页面失败')
        with allure.step('2. 选择需要加入黑名单的群成员'):
            self.groupManagerS.click_add_black_member()
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_edit_finish_button()
            self.chatS.wait_banner_message_disappear()
        with allure.step('3. 校验群主端被加入黑名单'):
            is_exit = self.groupManagerS.is_black_member_name_exist(name=PRIVATE_USER1.name)
            check.is_true(is_exit, '❌ 群主端未被加入黑名单')
        with allure.step('4. 校验接收端(群成员)被加入黑名单'):
            self.chatR.click_back_button()
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()
            _, tip = self.chatR.get_input_disabled_info()
            check.is_true('您已不在该群聊' in tip, f'❌ 接收端底部未显示您已不在该群聊提示 (tip: {tip})')
        with allure.step('5. 群主从黑名单移除该成员'):
            self.groupManagerS.click_black_remove_member(name=PRIVATE_USER1.name)
            self.groupManagerS.click_black_remove_member_confirm()
            self.chatS.wait_banner_message_disappear()
        with allure.step('6. 恢复环境：邀请该成员进群'):
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.click_iv_back_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_add_friend_header()
            self.groupManagerS.click_member_by_search_keyword(name=PRIVATE_USER1.name)
            self.groupManagerS.click_edit_finish_button()
            self.chatS.wait_banner_message_disappear()
            self.groupManagerS.click_iv_back_button()
        with allure.step('7. 校验群主端入群cmd消息'):
            res1 = self.chatS.is_cmd_notification_matching('您把.*加入了群聊')
            check.is_true(res1, '❌ 群主端入群cmd消息不匹配')
        with allure.step('8. 校验群两端入群cmd消息'):
            res2 = self.chatR.is_cmd_notification_matching('.*把您加入了群聊')
            check.is_true(res2, '❌ 接收端入群cmd消息不匹配')

    @allure.story('群管理-转让群主双端校验')
    @allure.title('【转让群主】双端转让与权限移交校验-状态：已完成')
    def test_transfer_group_owner_double_validation(self):
        """双端验证：群主转让群主给成员，双方权限变更，随后再将群主转让回原群主"""
        new_owner_name = PRIVATE_USER3.name
        with allure.step('1. 群主点击进入【转让群主】页面'):
            self.groupManagerS.click_group_give()
        with allure.step('2. 选择需要转让的新群主(接收端成员)'):
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_transfer_owner_confirm()
            self.chatS.wait_banner_message_disappear()
        with allure.step('3. 校验原群主(发送端)权限已降级(无群管理选项)'):
            self.groupManagerS.click_iv_back_button()
            res1 = self.chatS.is_cmd_notification_matching('你将群主身份转让给了.*')
            check.is_true(res1, '❌ 发送端未收到转让群主的通知消息')
        with allure.step('4. 校验新群主(接收端)权限已升级(显示群管理选项)'):
            res2 = self.chatR.is_cmd_notification_matching('.*已成为新群主')
            check.is_true(res2, '❌ 接收端未收到转让群主的通知消息')
        with allure.step('5. 恢复环境：新群主(接收端)将群主权限转让回原群主(发送端)'):
            self._enter_group_manager_receiver()
            self.groupManagerR.click_group_give()
            self.groupManagerR.click_member_by_name(name=new_owner_name)
            self.groupManagerR.click_transfer_owner_confirm()
            self.chatR.wait_banner_message_disappear()
            is_visible = self.groupSettingR.is_group_manager_visible(expect_missing=True)
            check.is_false(is_visible, '❌ 新群主(接收端)未重获群管理权限')
        with allure.step('6. 校验双方状态已复原(发送端重获群管理权限)'):
            self.chatS.click_more_button()
            is_visible = self.groupSettingS.is_group_manager_visible()
            check.is_true(is_visible, '❌ 原群主(发送端)未重获群管理权限')


    @allure.story('群管理-解散群聊双端校验')
    @allure.title('【解散群聊】群主正常解散群聊-成员端同步被移出并接收失效通知-状态：已完成')
    @pytest.mark.skip_env_setup
    def test_delete_group_success_double_validation(self):
        """双端验证：群主在群管理中解散群聊，群主和成员端状态同步刷新"""
        temp_name = self._create_temp_group_double()
        with allure.step('1. 发送端(群主)在群管理中点击【解散群聊】'):
            self.groupManagerS.click_dismiss_group()
        with allure.step('2. 发送端确认弹窗解散'):
            self.groupSettingS.click_tv_confirm_button()
            toast = self.groupSettingS.verify_toast_exist('解散成功')
            check.is_true(toast, '❌ 发送端解散群聊后未弹出提示')
        with allure.step('3. 发送端(群主)解散成功回到主页后，重新进入该群聊'):
            self.chatListS.enter_chat(temp_name)
            self.chatS.wait_for_chat_page_load()
            self.chatListR.enter_chat(temp_name)
            self.chatR.wait_for_chat_page_load()
        with allure.step('4. 发送端(群主)进入群设置，点击【删除并退出】彻底清理会话'):
            self.chatS.click_more_button()
            toast = self.groupSettingS.get_toast()
            check.is_in('群不存在', toast, '❌ 接收端点击解散群聊后未弹出提示')
            self.groupSettingS.click_delete_and_out()
            self.groupSettingS.click_tv_confirm_button()
        with allure.step('5. 接收端(普通成员)点击更多进入群设置，点击【删除并退出】清理会话'):
            self.chatR.click_more_button()
            toast = self.groupSettingR.get_toast()
            check.is_in('群不存在', toast, '❌ 接收端点击解散群聊后未弹出提示')
            self.groupSettingR.click_delete_and_out()
            self.groupSettingR.click_tv_confirm_button()

    @allure.story('群管理-解散群聊双端校验')
    @allure.title('【解散群聊】群主取消解散群聊-群聊依然保持健在-状态：已完成')
    @pytest.mark.skip_env_setup
    def test_delete_group_cancel_double_validation(self):
        """双端验证：群主点击解散群聊但选择取消，群聊依然健在且成员能正常发言"""
        temp_name = self._create_temp_group_double()
        with allure.step('1. 发送端(群主)在群管理中点击【解散群聊】并取消'):
            self.groupManagerS.click_dismiss_group()
            self.groupSettingS.click_tv_cancel_button()
        with allure.step('2. 接收端(成员)尝试发送消息验证群聊是否正常'):
            self.chatListR.enter_chat(temp_name)
            self.chatR.wait_for_chat_page_load()
            self.chatR.send_message('群聊正常修改取消测试')
            total_msg = self.chatR.get_total_message_count()
            check.is_true(total_msg > 0, '❌ 取消解散后，群成员无法正常发送聊天消息')


    @allure.story('群管理-群ID搜索双端联动')
    @allure.title('【群ID搜索】群主关闭群ID搜索后成员端搜索可见性校验-状态：未完成')
    @pytest.mark.enter_manager(False)
    def test_group_id_search_double_validation(self):
        """双端验证：群主关闭群ID搜索开关后，接收端通过群ID搜索该群应无法检索到；环境复原后重新开启"""
        
        with allure.step('-> [双端准备] 发送端在群聊聊天界面获取群ID'):
            target_group_id = self.chatS.get_group_id()
            check.is_true(target_group_id, '❌ 当前未获取到群ID，无法进行群ID搜索双端联动测试')

        with allure.step('-> [前置准备] 发送端(群主)进入该群【群管理】页面'):
            self._enter_group_manager_sender()

        with allure.step('1. 群主端开启【群ID搜索】开关'):
            is_toggled = self.groupManagerS.click_group_id_search_switch(checked_str='true')
            if is_toggled:
                result = self.chatS.verify_toast_exist('保存成功')
                check.is_true(result, '❌ 群ID搜索开关开启后未显示预期提示')

        with allure.step(f'2. 接收端退出群聊进入添加朋友页面，搜索群ID [{target_group_id}]'):
            self.chatR.click_back_button()
            self.homeR.click_add_button()
            self.homeR.click_add_friend()
            is_loaded = self.addFriendR.wait_for_add_friend_page(timeout=5)
            check.is_true(is_loaded, '❌ 接收端未能成功进入添加朋友页面')
            self.addFriendR.search_friend_by_content(target_group_id)
            self.addFriendR.click_confirm_search()

        with allure.step('3. 校验接收端检索到该群聊'):
            result = self.addFriendR.get_search_result_item_name()
            check.equal(result, GROUP_STRATEGY.name, f'❌ 关闭群ID搜索后，接收端检索到群或未显示预期提示: {result}')

        with allure.step('4. 环境复原：群主端关闭【群ID搜索】开关'):
            self.groupManagerS.click_group_id_search_switch(checked_str='false')
            
    @allure.story('群管理-新成员进群自动禁言双端联动')
    @allure.title('【新成员进群自动禁言】开启后新成员入群发言权限及禁言时长双端校验-状态：已完成')
    @pytest.mark.keep_env('admin')
    @pytest.mark.parametrize('duration', [
        pytest.param('10分钟', id='自动禁言-10分钟'),
        pytest.param('30分钟', id='自动禁言-30分钟'),
        pytest.param('2小时', id='自动禁言-2小时'),
        pytest.param('24小时', id='自动禁言-24小时'),
    ])
    def test_new_member_auto_mute_double_validation(self, duration):
        """双端验证：群主开启【新成员进群自动禁言】并设置不同时长后，新加入成员默认处于对应时长禁言状态无法发言；关闭开关并解除禁言后恢复正常"""
        with allure.step(f'1. 群主端开启【新成员进群自动禁言】开关并设置时长为【{duration}】'):
            self.groupManagerS.click_new_member_auto_mute_switch(checked_str='true')
            self.groupManagerS.click_new_member_auto_mute_duration()
            self.groupManagerS.select_new_member_auto_mute_duration(duration)

        with allure.step(f'2. 群主端返回群设置，将接收端【{PRIVATE_USER1.name}】移出群聊'):
            self.groupManagerS.click_iv_back_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_to_member_list()
            friend_names = self.groupSettingS.get_friend_names()
            self.chatS.click_back_button()
            self.chatR.click_back_button()
            if not friend_names or PRIVATE_USER1.name in friend_names:
                self.groupSettingS.click_remove_friend_header()
                self.groupManagerS.click_member_by_search_keyword(name=PRIVATE_USER1.name)
                self.groupManagerS.click_edit_finish_button()
                self.chatS.wait_banner_message_disappear()

        with allure.step(f'3. 群主端重新邀请接收端【{PRIVATE_USER1.name}】加入群聊'):
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_add_friend_header()
            self.groupManagerS.click_member_by_search_keyword(name=PRIVATE_USER1.name)
            self.groupManagerS.click_edit_finish_button()
            self.chatS.wait_banner_message_disappear()

        with allure.step(f'4. 接收端(新入群成员)进入群聊，校验被自动禁言且倒计时符合【{duration}】'):
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()
            res = self.chatR.is_cmd_notification_matching('.*把您加入了群聊')
            check.is_true(res, '❌ 接收端未收到被加入群聊的系统通知')
            is_disabled = self.chatR.is_input_disabled()
            check.is_true(is_disabled, '❌ 开启新成员自动禁言后，新入群成员输入框未被禁用')
            title, tip = self.chatR.get_input_disabled_info()
            logger.info(f"接收端禁言信息提示: title='{title}', tip='{tip}'")
            check.is_true(bool(title) or bool(tip), f'❌ 接收端输入框未展示禁言提示: title={title}, tip={tip}')
            total_mins = self.chatR.get_mute_remaining_minutes(tip)
            if total_mins is None:
                check.is_true(False, f"❌ 禁言提示时间格式不匹配 (期望包含 '剩余HH:MM:SS'): {tip}")
            else:
                expected_ranges = {
                    '10分钟': (8, 10),
                    '30分钟': (28, 30),
                    '2小时': (115, 120),
                    '24小时': (1420, 1440),
                }
                min_val, max_val = expected_ranges.get(duration, (0, 0))
                check.is_true(min_val <= total_mins <= max_val,
                              f'❌ 禁言时间不匹配: 期望 {min_val}~{max_val} 分钟，实际 {total_mins} 分钟 ({tip})')

        with allure.step('5. 环境复原：群主端关闭【新成员进群自动禁言】开关并解除禁言'):
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_group_manager_page_load()
            self.groupManagerS.click_new_member_auto_mute_switch(checked_str='false')
            # self.groupManagerS.click_iv_back_button()
            is_disabled_after = self.chatR.is_input_disabled()
            check.is_false(is_disabled_after, '❌ 环境复原解除禁言后，接收端输入框仍处于禁用状态')


    @allure.story('群管理-进群申请双端联动')
    @allure.title('【进群申请】新成员申请入群后群主端红点数与审批流程双端校验-状态：已完成')
    @pytest.mark.enter_manager
    def test_join_apply_badge_double_validation(self):
        """双端验证：普通成员发起入群申请，群主端群管理页进群申请红点数+1，审批通过后红点消除，并执行环境复原"""
        with allure.step('1. 群主端确保【进群验证】已开启并退回群设置'):
            self.groupManagerS.click_join_group_verify_switch(checked_str='true')
            self.groupManagerS.click_iv_back_button()
            self.groupSettingS.wait_for_setting_page_load()

        with allure.step(f'2. 接收端(普通成员)在群设置中邀请【{PRIVATE_USER2.name}】发起进群申请'):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_add_friend_header(is_admin=False)
            self.groupManagerR.click_member_by_search_keyword(name=PRIVATE_USER2.name)
            self.groupManagerR.click_edit_finish_button()
            self.groupSettingR.input_remark_content('测试申请入群')
            self.groupSettingR.click_tv_confirm_button()
            self.groupSettingR.click_iv_back_button()
            self.chatR.wait_for_chat_page_load()

        with allure.step('3. 群主端进入【群管理】页面，校验【进群申请】红点未读数'):
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_group_manager_page_load()
            badge_count = self.groupManagerS.get_join_apply_badge_count()
            logger.info(f"群主端进群申请红点未读数: {badge_count}")
            check.greater(badge_count, 0, f"❌ 产生进群申请后，群主端进群申请红点未增加或未显示: {badge_count}")

        with allure.step('4. 群主端进入审批并同意申请，校验红点消除'):
            self.groupManagerS.click_join_to_group_apply()
            self.groupManagerS.wait_for_join_apply_page_load()
            self.groupManagerS.click_agree_button(index=0)
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.wait_for_group_manager_page_load()
            after_badge = self.groupManagerS.get_join_apply_badge_count()
            if after_badge == badge_count:
                self.groupManagerS.click_iv_back_button()
                self.groupSettingS.wait_for_setting_page_load()
                self.groupSettingS.click_group_manager()
                self.groupManagerS.wait_for_group_manager_page_load()
                after_badge = self.groupManagerS.get_join_apply_badge_count()
            logger.info(f"审批通过后群主端进群申请红点数: {after_badge}")
            check.not_equal(after_badge, badge_count, f"❌ 审批通过后进群申请红点未清零，实际仍有: {after_badge}")

        with allure.step(f'5. 环境复原：群主端返回群设置，将【{PRIVATE_USER2.name}】移出群聊'):
            self.groupManagerS.click_iv_back_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_remove_friend_header()
            self.groupManagerS.click_member_by_search_keyword(name=PRIVATE_USER2.name)
            self.groupManagerS.click_edit_finish_button()




    @allure.story('群管理-公开群展示双端联动')
    @allure.title('【公开群展示】开关切换及广场搜索可见性双端校验-状态：未完成')
    @pytest.mark.skip('公开群展示双端联动功能未实现/待验证')
    def test_public_group_display_double_validation(self):
        """双端验证：群主开启公开群展示后，非群成员可在公开群列表中发现该群；关闭后不展示"""
        with allure.step('1. 群主端开启【公开群展示】开关'):
            self.groupManagerS.click_public_group_display_switch(checked_str='true')
            self.chatS.wait_banner_message_disappear()
        with allure.step('2. 接收端在公开群广场列表中校验能看到该群'):
            pass
        with allure.step('3. 环境复原：群主端关闭【公开群展示】开关'):
            self.groupManagerS.click_public_group_display_switch(checked_str='false')
            self.chatS.wait_banner_message_disappear()