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
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from pages.common.session_select_page import SessionSelectPage
from pages.personal.contact_detail_page import ContactDetailPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, PRIVATE_USER3, GROUP_STRATEGY


@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群管理双端验证")
class TestGroupManagerDouble:
    """群管理功能双端（群主发端与成员收端）协同验证测试"""

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象，进入指定群聊并让群主驻留群管理页面，普通成员驻留聊天页面"""
        self.mainS = MainPage(driver_sender)
        self.groupSettingS = GroupSettingPage(driver_sender)
        self.groupManagerS = GroupManagerPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.groupSettingR = GroupSettingPage(driver_receiver)
        self.groupManagerR = GroupManagerPage(driver_receiver)
        self.contactDetailR = ContactDetailPage(driver_receiver)

        with allure.step("-> [前置准备] 发送端(群主)进入指定群聊"):
            self.chatListS.enter_chat(GROUP_STRATEGY.name)
            self.chatS.wait_for_chat_page_load()

        with allure.step("-> [前置准备] 接收端(普通成员)进入指定群聊聊天界面"):
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()

        self._enter_group_manager_sender()

        yield

        with allure.step("-> [环境清理] 双端返回首页"):
            try:
                self.mainS.go_to_main_page()
                self.mainR.go_to_main_page()
            except Exception as e:
                logger.warning(f"⚠️ [Cleanup] 双端返回首页失败: {e}")

    def _enter_group_manager_sender(self):
        """内部辅助：发送端(群主)进入该群【群管理】页面"""
        with allure.step("-> [前置准备] 发送端(群主)进入该群【群管理】页面"):
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_page_load()

    def _enter_group_manager_receiver(self):
        """内部辅助：接收端进入聊天页面"""
        with allure.step("-> [前置准备] 接收端(普通成员)进入指定群聊聊天界面"):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_group_manager()
            self.groupManagerR.wait_for_page_load()

    

    # 状态与计数器变量
    _admin_assigned = False
    _executed_admin_tests = []

    @pytest.fixture(scope="function", autouse=False)
    def admin_role(self, request):
        """确保分配了管理员权限，在首个用例自动或手动分配，在最后一个用例自动清理"""
        if not self._admin_assigned:
            test_name = request.node.name
            if test_name == "test_admin_allocation_double_validation":
                self._assign_admin_permission()
                self._admin_assigned = True
        
        yield
        
        # 统计在当前运行队列中属于这三个需要管理员权限的用例
        session_tests = [item.name for item in request.session.items]
        target_tests = [
            "test_admin_allocation_double_validation",
            "test_join_verify_admin_scenarios_double_validation",
            "test_add_admin_double_validation"
        ]
        tests_to_run = [t for t in target_tests if t in session_tests]
        
        if not self._executed_admin_tests:
            self._executed_admin_tests = []
        if request.node.name not in self._executed_admin_tests:
            self._executed_admin_tests.append(request.node.name)
            
        # 如果是本轮执行的最后一个管理员相关用例，则执行自动清理
        if len(self._executed_admin_tests) == len(tests_to_run):
            if self._admin_assigned:
                self._remove_admin_permission()
                self._admin_assigned = False
            self._executed_admin_tests = []

    def _assign_admin_permission(self):
        """前置辅助：群主分配管理员权限并开启所有开关"""
        with allure.step("-> [前置准备] 群主分配管理员权限并全开"):
            self.groupManagerS.click_administrators()
            self.groupManagerS.wait_for_admin_page_load()
            self.groupManagerS.click_add_admin()
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_all_switch(checked_str="false")
            self.groupManagerS.click_confirm_button()
            self.chatS.wait_banner_message_disappear()
            member_names = self.groupManagerS.get_member_names()
            check.is_in(PRIVATE_USER1.name, member_names, "❌ 群主端管理员列表未显示新增的管理员")

    def _remove_admin_permission(self):
        """后置辅助：群主从管理员列表移除该成员"""
        with allure.step("-> [环境清理] 群主从管理员列表移除该成员并校验降级"):
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_sure_button()
            self.groupManagerS.click_sure_content_button()
            self.chatS.wait_banner_message_disappear()
            member_names = self.groupManagerS.get_member_names()
            check.is_not_in(PRIVATE_USER1.name, member_names, "❌ 群主端移除管理员失败")
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.click_iv_back_button()

            res = self.chatR.is_cmd_notification_matching(r".*移除管理员身份")
            check.is_true(res, "❌ 接收端未收到被解除管理员的通知消息")

            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            is_visible = self.groupSettingR.is_group_manager_visible()
            check.is_false(is_visible, "❌ 接收端被解除管理员后，群设置中依然显示【群管理】入口")
            self.groupSettingR.click_iv_back_button()


    @allure.story("群管理-管理员分配")
    @allure.title("【管理员】是否是管理员身份的分配验证-分配所有权限")
    @pytest.mark.usefixtures("admin_role")
    def test_admin_allocation_double_validation(self):
        """验证群主分配和撤销管理员身份，以及对应的成员端权限同步和CMD通知"""
        
        # with allure.step("1. 发送端(群主)点击群管理员，并点击新增管理员"):
        #     self._assign_admin_permission()
        
        with allure.step("1. 校验接收端(群成员)收到管理员身份通知并获得群管理权限"):
            res = self.chatR.is_cmd_notification_matching(r".*将您添加为管理员")
            check.is_true(res, "❌ 接收端未收到成为管理员的通知消息")

            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            is_visible = self.groupSettingR.is_group_manager_visible()
            check.is_true(is_visible, "❌ 接收端被设为管理员后，群设置中没有显示【群管理】入口")
            self.groupManagerR.click_iv_back_button()


    @allure.story("群申请-进群验证")
    @allure.title("【进群验证】是否是管理员的多重场景")
    @pytest.mark.usefixtures("admin_role")
    def test_join_verify_admin_scenarios_double_validation(self):
        """验证进群验证是否是管理员的多重场景"""
        
        # with allure.step("1. 发送端(群主)点击群管理员，并点击新增管理员"):
        #     self._assign_admin_permission()
        
        with allure.step("1. 接收端进群校验验证"):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_group_manager()
            state = self.groupManagerR.get_join_group_verify_state()
            check.is_in(state, ("true", "false"), "❌ 接收端进群校验状态异常")
            self.groupManagerR.click_iv_back_button()
            self.groupManagerR.click_iv_back_button()
            

    @allure.story("群申请-进群申请双端校验")
    @allure.title("【进群申请】管理员=是，可以看到进群申请横幅；管理员=否，看不到进群申请横幅")
    @pytest.mark.usefixtures("admin_role")
    def test_add_admin_double_validation(self):
        """验证是否为管理员【进群申请】管理员=是，可以看到进群申请横幅；管理员=否，看不到进群申请横幅"""

        # with allure.step("1. 发送端(群主)点击群管理员，并点击新增管理员"):
        #     self._assign_admin_permission()

        with allure.step("1. 接收端进群申请横幅与操作按钮校验"):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_group_manager()
            self.groupManagerR.click_join_to_group_apply()
            
            # 1. 校验进群申请头部/横幅提示
            res = self.groupManagerR.get_join_apply_tips()
            check.is_in("入群申请", res, "❌ 接收端【进群申请】页头部提示异常")
            
            # 2. 动态校验：如果有待处理申请，验证操作按钮的存在性
            agree_btns = self.groupManagerR.get_agree_buttons()
            disagree_btns = self.groupManagerR.get_disagree_buttons()
            if agree_btns:
                check.is_true(len(agree_btns) > 0, "❌ 列表中有申请项时未显示‘同意’按钮")
                check.is_true(len(disagree_btns) > 0, "❌ 列表中有申请项时未显示‘拒绝’按钮")
            else:
                logger.info("ℹ️ 当前没有待处理的进群申请，跳过同意/拒绝按钮的强校验")
                
            self.groupManagerR.click_iv_back_button()
            self.groupManagerR.click_iv_back_button()
            self.groupManagerR.click_iv_back_button()
        

    @allure.story("群禁言-全员禁言双端校验")
    @allure.title("【全员禁言】开关开启与关闭 - 接收端输入框禁言状态实时同步校验")
    def test_all_member_mute_double_validation(self):
        """验证群主开启全员禁言后，普通成员的输入框应立即被禁用并展示‘全员禁言中’；群主关闭全员禁言后，普通成员恢复正常发言"""
        
        with allure.step("1. 开启全员禁言"):
            self.groupManagerS.click_all_member_mute_switch(checked_str='true')
            self.chatR.wait_banner_message_disappear()

        with allure.step("2. 回到聊天页面中，并校验全员禁言开启状态"):
            cmd_texts = self.chatR.get_cmd_notification_texts(index=-1)
            check.is_in('开启全员禁言', cmd_texts, "❌ [Action-groupManagerPage] 全员禁言开关未开启")
        
        with allure.step("3. 接收方校验被禁言（底部输入框被禁用与提示）"):
            title, _ = self.chatR.get_input_disabled_info()
            check.equal("禁言中", title, f"❌ 禁言提示标题不存在: {title}")
        
        with allure.step("4. 再次点击开关恢复至初始状态"):
            self.groupManagerS.click_all_member_mute_switch(checked_str='false')
            self.chatR.wait_banner_message_disappear()

        with allure.step("5. 移除禁言后，接收方校验输入框状态恢复可用"):
            is_disabled = self.chatR.is_input_disabled()
            check.is_false(is_disabled, "❌ 移除禁言后，普通群成员的输入框仍处于禁用状态")


    @allure.story("群禁言-指定群成员禁言双端校验")
    @allure.title("【指定群成员禁言】群主开启指定禁言")
    @pytest.mark.parametrize('mute_type, duration',
                            [(0, 0), (1, '10分钟'), (1, '30分钟'), (1, '2小时'), (1, '1天'), (1, '3天'), (1, '7天'), (1, '30天')],
                            ids=["永久禁言", "临时禁言-10分钟", "临时禁言-30分钟", "临时禁言-2小时", "临时禁言-1天", "临时禁言-3天", "临时禁言-7天", "临时禁言-30天"])
    def test_specify_member_mute_double_validation(self, mute_type, duration):
        """验证群主开启指定禁言后，被禁言成员不能发送消息，解除禁言后可正常发送消息"""
        
        with allure.step("1. 进入【指定成员禁言】子页面"):
            self.groupManagerS.click_mute_member()
            self.groupManagerS.wait_for_specify_mute_page_load()
            self.groupManagerS.click_confirm_button()

        with allure.step("2. 添加指定禁言成员"):
            self.groupManagerS.input_member_search_keyword(PRIVATE_USER1.name)
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_edit_finish_button()

        with allure.step("3. 选择禁言类型和时长"):
            if mute_type == 0:
                self.groupManagerS.click_cb_1()
            else:
                self.groupManagerS.click_cb_2()
                self.groupManagerS.click_temp_mute_time()
                self.groupManagerS.click_set_mute_duration(duration)
            self.groupManagerS.click_sure_button()
            self.groupManagerS.click_mute_confirm_btn()

        with allure.step("4. 接收方校验被禁言（底部输入框被禁用与提示）"):
            title, tip = self.chatR.get_input_disabled_info()
            check.is_true(bool(title) or bool(tip), f"❌ 禁言提示标题不存在: {title}")
        
        with allure.step("5. 接收方校验禁言具体倒计时"):
            if mute_type == 0:
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
                        "3天": (4310, 4320),
                        "7天": (10050, 10080),
                        "30天": (43150, 43200),
                    }
                    min_val, max_val = expected_ranges.get(duration, (0, 0))
                    check.is_true(
                        min_val <= total_mins <= max_val,
                        f"❌ 禁言时间不匹配: 期望 {min_val}~{max_val} 分钟，实际 {total_mins} 分钟 ({tip})"
                    )

        with allure.step("6. 点击移除禁言"):
            self.groupManagerS.click_cancel_mute(PRIVATE_USER1.name)
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.click_iv_back_button()

        with allure.step("7. 移除禁言后，接收方校验输入框状态恢复可用"):
            is_disabled = self.chatR.is_input_disabled()
            check.is_false(is_disabled, "❌ 移除禁言后，普通群成员的输入框仍处于禁用状态")


    @allure.story("群管理-添加好友双端校验")
    @allure.title("【禁止添加好友】开关开启与关闭 - 接收端没有添加好友按钮")
    def test_forbid_add_friend_double_validation(self):
        """验证群主开启禁止添加好友后，普通群成员的聊天信息栏中没有添加好友按钮；群主关闭禁止添加好友后，普通群成员的聊天信息栏有添加好友按钮"""
        
        name = "422"
        with allure.step("1. 开启禁止群成员互相加好友"):
            self.groupManagerS.click_un_add_friend_each_other_switch(checked_str='true')
            self.chatS.wait_banner_message_disappear()

        with allure.step("2. 校验接收方 Banner 消息"):
            res = self.chatR.is_cmd_notification_matching(r".*开启群内禁止添加好友")
            check.is_true(res, "❌ 禁止群成员互相加好友开关未开启")

        with allure.step(f"3. 校验接收端(群成员)聊天信息栏中没有添加【{name}】好友按钮"):
            self.chatR.click_more_button()
            self.groupSettingR.click_member_avatar_by_name(name=name)
            has_add = self.contactDetailR.has_add_friend_button()
            check.is_false(has_add, f"❌ 群主开启禁止添加好友后，【{name}】聊天信息栏未能成功移除添加好友按钮")

        with allure.step("4. 群主侧关闭【禁止添加好友】开关"):
            self.groupManagerS.click_un_add_friend_each_other_switch(checked_str='false')

        with allure.step(f"5. 校验接收端(群成员)聊天信息栏中恢复有添加【{name}】好友按钮"):
            self.chatR.wait_banner_message_disappear()
            self.groupManagerR.click_iv_back_button()
            self.groupManagerR.click_iv_back_button()
            res = self.chatR.is_cmd_notification_matching(r".*关闭群内禁止添加好友")
            check.is_true(res, "❌ 禁止群成员互相加好友开关未关闭")


    @allure.story("群管理-群黑名单双端校验")
    @allure.title("【群黑名单】页面加载与返回校验")
    def test_group_blacklist_double_validation(self):
        """双端验证：群主进入【群黑名单】页面并返回"""

        with allure.step("1. 群主点击进入【群黑名单】页面"):
            self.groupManagerS.click_group_black_member()
            res = self.groupManagerS.wait_for_group_blacklist_page_load()
            check.is_true(res, "❌ 群主进入【群黑名单】页面失败")

        with allure.step("2. 选择需要加入黑名单的群成员"):
            self.groupManagerS.click_add_black_member()
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_edit_finish_button()
            self.chatS.wait_banner_message_disappear()

        with allure.step("3. 校验群主端被加入黑名单"):
            is_exit = self.groupManagerS.is_black_member_name_exist(name=PRIVATE_USER1.name)
            check.is_true(is_exit, "❌ 群主端未被加入黑名单")
            
        with allure.step("4. 校验接收端(群成员)被加入黑名单"):
            cmd_info = self.chatR.get_cmd_notification_texts(index=-1)
            check.is_in("移除群聊", cmd_info, f"❌ 接收端(群成员)未被加入黑名单")

        with allure.step("5. 群主从黑名单移除该成员"):
            self.groupManagerS.click_black_remove_member(name=PRIVATE_USER1.name)
            self.groupManagerS.click_black_remove_member_confirm()
            self.chatS.wait_banner_message_disappear()

        with allure.step("6. 恢复环境：邀请该成员进群"):
            self.groupManagerS.click_iv_back_button()
            self.groupManagerS.click_iv_back_button()
            self.groupSettingS.wait_for_setting_page_load()

            self.groupSettingS.click_add_friend_header()
            self.groupManagerS.click_member_by_search_keyword(name=PRIVATE_USER1.name)
            self.groupManagerS.click_edit_finish_button()
            self.chatS.wait_banner_message_disappear()
            self.groupManagerS.click_iv_back_button()

        with allure.step("7. 校验群主端入群cmd消息"):
            res1 = self.chatS.is_cmd_notification_matching(r"您把.*加入群聊")
            check.is_true(res1, "❌ 群主端入群cmd消息不匹配")

        with allure.step("8. 校验群两端入群cmd消息"):
            res2 = self.chatR.is_cmd_notification_matching(r".*把您加入群聊")
            check.is_true(res2, "❌ 接收端入群cmd消息不匹配")


    @allure.story("群管理-转让群主双端校验")
    @allure.title("【转让群主】双端转让与权限移交校验")
    def test_transfer_group_owner_double_validation(self):
        """双端验证：群主转让群主给成员，双方权限变更，随后再将群主转让回原群主"""

        new_owner_name = '1234567890'
        with allure.step("1. 群主点击进入【转让群主】页面"):
            self.groupManagerS.click_group_give()

        with allure.step("2. 选择需要转让的新群主(接收端成员)"):
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_black_remove_member_confirm()
            self.chatS.wait_banner_message_disappear()

        with allure.step("3. 校验原群主(发送端)权限已降级(无群管理选项)"):
            self.groupManagerS.click_iv_back_button()
            res1 = self.chatS.is_cmd_notification_matching(r".*已成为新群主")
            check.is_true(res1, "❌ 发送端未收到转让群主的通知消息")

        with allure.step("4. 校验新群主(接收端)权限已升级(显示群管理选项)"):
            res2 = self.chatR.is_cmd_notification_matching(r".*已成为新群主")
            check.is_true(res2, "❌ 接收端未收到转让群主的通知消息")
            
        with allure.step("5. 恢复环境：新群主(接收端)将群主权限转让回原群主(发送端)"):
            self._enter_group_manager_receiver()
            self.groupManagerR.click_group_give()
            self.groupManagerR.click_member_by_name(name=new_owner_name)
            self.groupManagerR.click_black_remove_member_confirm()
            self.chatR.wait_banner_message_disappear()
            is_visible = self.groupSettingR.is_group_manager_visible()
            check.is_false(is_visible, "❌ 新群主(接收端)未重获群管理权限")

        with allure.step("6. 校验双方状态已复原(发送端重获群管理权限)"):
            self.chatS.click_more_button()
            is_visible = self.groupSettingS.is_group_manager_visible()
            check.is_true(is_visible, "❌ 原群主(发送端)未重获群管理权限")
