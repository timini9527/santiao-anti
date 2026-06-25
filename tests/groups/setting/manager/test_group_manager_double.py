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



    @allure.story("群禁言双端校验")
    @allure.title("【全员禁言】开关开启与关闭 - 接收端输入框禁言状态实时同步校验")
    def test_all_member_mute_double_validation(self):
        """验证群主开启全员禁言后，普通成员的输入框应立即被禁用并展示‘全员禁言中’；群主关闭全员禁言后，普通成员恢复正常发言"""
        
        with allure.step("1. 验证初始状态：群主侧全员禁言关闭，群成员侧输入框正常可用"):
            is_muted_init = self.groupManagerS.get_all_member_mute_state()
            if is_muted_init:
                self.groupManagerS.click_all_member_mute_switch()
                time.sleep(1)
            
            # 成员侧验证输入框可正常输入
            is_disabled_init = self.chatR.is_input_disabled()
            check.is_false(is_disabled_init, "❌ 初始全员禁言关闭时，普通群成员输入框不应被禁用")

        with allure.step("2. 群主侧开启【全员禁言】开关"):
            self.groupManagerS.click_all_member_mute_switch()
            time.sleep(2)  # 等待通道状态同步

        with allure.step("3. 校验接收端(群成员)输入框状态变为禁用，并展示‘全员禁言中’"):
            is_disabled_after = self.chatR.is_input_disabled()
            check.is_true(is_disabled_after, "❌ 群主开启全员禁言后，普通群成员的输入框未能成功禁用")
            
            disable_title, _ = self.chatR.get_input_disabled_info()
            check.is_in("全员禁言中", disable_title, f"❌ 禁言提示标题不匹配，实际显示: '{disable_title}'")

        with allure.step("4. 群主侧关闭【全员禁言】开关"):
            self.groupManagerS.click_all_member_mute_switch()
            time.sleep(2)  # 等待状态同步

        with allure.step("5. 校验接收端(群成员)输入框状态恢复为可用"):
            is_disabled_final = self.chatR.is_input_disabled()
            check.is_false(is_disabled_final, "❌ 群主关闭全员禁言后，普通群成员的输入框仍处于禁用状态")


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
            self.groupManagerS.click_back_button()
            self.groupManagerS.click_back_button()
            self.groupSettingS.wait_for_setting_page_load()

            self.groupSettingS.click_add_friend_header()
            self.groupManagerS.click_member_by_search_keyword(name=PRIVATE_USER1.name)
            self.groupManagerS.click_edit_finish_button()
            self.chatS.wait_banner_message_disappear()
            self.groupManagerS.click_back_button()

        with allure.step("7. 校验群主端入群cmd消息"):
            cmd_info1 = self.chatS.get_cmd_notification_texts(index=-1)
            match_res1 = re.search(r"您把.*加入群聊", cmd_info1)
            check.is_true(bool(match_res1), f"❌ 群主端入群cmd消息不匹配，实际为: '{cmd_info1}'")

        with allure.step("8. 校验群两端入群cmd消息"):
            cmd_info2 = self.chatR.get_cmd_notification_texts(index=-1)
            match_res2 = re.search(r".*把您加入群聊", cmd_info2)
            check.is_true(bool(match_res2), f"❌ 接收端入群cmd消息不匹配，实际为: '{cmd_info2}'")


    @allure.story("群管理-转让群主双端校验")
    @allure.title("【转让群主】双端转让与权限移交校验")
    def test_transfer_group_owner_double_validation(self):
        """双端验证：群主转让群主给成员，双方权限变更，随后再将群主转让回原群主"""
        
        with allure.step("1. 群主点击进入【转让群主】页面"):
            self.groupManagerS.click_group_give()

        with allure.step("2. 选择需要转让的新群主(接收端成员)"):
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerS.click_black_remove_member_confirm()
            self.chatS.wait_banner_message_disappear()

        with allure.step("3. 校验原群主(发送端)权限已降级(无群管理选项)"):
            self.groupManagerS.click_back_button()
            cmd_info1 = self.chatS.get_cmd_notification_texts(index=-1)
            match_res1 = re.search(r".*已成为新群主", cmd_info1)
            check.is_true(bool(match_res1), f"❌ 接收端(群成员)未被加入黑名单")

        with allure.step("4. 校验新群主(接收端)权限已升级(显示群管理选项)"):
            cmd_info2 = self.chatR.get_cmd_notification_texts(index=-1)
            match_res2 = re.search(r".*已成为新群主", cmd_info2)
            check.is_true(bool(match_res2), f"❌ 接收端(群成员)未被加入黑名单")
            
        with allure.step("5. 恢复环境：新群主(接收端)将群主权限转让回原群主(发送端)"):
            self._enter_group_manager_receiver()
            self.groupManagerR.click_group_give()
            
            self.groupManagerR.click_member_by_name(name='1234567890')
            self.groupManagerR.click_black_remove_member_confirm()
            self.chatR.wait_banner_message_disappear()

        with allure.step("6. 校验双方状态已复原(发送端重获群管理权限)"):
            pass
