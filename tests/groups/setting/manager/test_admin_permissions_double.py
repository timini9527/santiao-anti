import re
import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_long_press_page import ChatLongPressPage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from locators.groups.setting.general.group_setting_locator import GroupSettingLocator
from locators.groups.setting.manager.group_manager_locator import GroupManagerLocator

@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-管理员权限专项校验")
class TestAdminPermissionsDouble:
    """管理员所有权限入口与操作可见性双端专项验证测试"""

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象，并让双端进入指定群聊"""
        self.mainS = MainPage(driver_sender)
        self.groupSettingS = GroupSettingPage(driver_sender)
        self.groupManagerS = GroupManagerPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.chatLongPressR = ChatLongPressPage(driver_receiver)
        self.groupSettingR = GroupSettingPage(driver_receiver)
        self.groupManagerR = GroupManagerPage(driver_receiver)

        with allure.step("-> [前置准备] 发送端(群主)与接收端(成员)进入指定群聊"):
            self.chatListS.enter_chat(GROUP_STRATEGY.name)
            self.chatS.wait_for_chat_page_load()
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()

        yield

        with allure.step("-> [环境清理] 双端返回首页"):
            try:
                self.mainS.go_to_main_page()
                self.mainR.go_to_main_page()
            except Exception as e:
                logger.warning(f"清理环境失败: {e}")

    @allure.story("管理员权限-全量入口与状态代理校验")
    @allure.title("【管理员权限校验】分配所有权限时，通过 UI 代理与可见性状态一键校验")
    def test_admin_permissions_visibility_double_validation(self):
        """
        通过只读 UI 代理校验，一键验证分配给新晋管理员的所有权限入口及开关状态：
        包含：修改群头像、修改群名称、编辑群公告、全员禁言、指定成员禁言、进群验证开关、成员进群审批、删除/撤回成员消息、查看管理员列表、禁止互加好友、封禁用户。
        """
        with allure.step("1. 发送端(群主)点击群管理进入管理员分配页面"):
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_page_load()
            self.groupManagerS.click_administrators()
            self.groupManagerS.wait_for_admin_page_load()

        with allure.step("2. 群主新增管理员，勾选全部权限并保存"):
            self.groupManagerS.click_add_admin()
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            # 开启所有权限开关并点击确定
            self.groupManagerS.click_all_switch(checked_str="false")
            self.groupManagerS.click_confirm_button()
            self.chatS.wait_banner_message_disappear()

        with allure.step("3. 接收端(管理员)验证收到管理员身份分配通知"):
            res = self.chatR.is_cmd_notification_matching(r".*将您添加为管理员")
            check.is_true(res, "❌ 接收端未收到成为管理员的通知消息")

        with allure.step("4. 接收端(管理员)进入群设置页面，验证修改群信息权限入口（群头像/群名称/群公告）"):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            
            # 校验群头像、群聊名称、群公告是否可见
            check.is_true(self.groupSettingR.is_element_exist(GroupSettingLocator.SETTING_CHAT_GROUP_HEADER), "❌ 新晋管理员无法看到群头像修改入口")
            check.is_true(self.groupSettingR.is_element_exist(GroupSettingLocator.SETTING_CHAT_GROUP_NAME), "❌ 新晋管理员无法看到群名称修改入口")
            check.is_true(self.groupSettingR.is_element_exist(GroupSettingLocator.SETTING_CHAT_GROUP_ANNOUNCEMENT), "❌ 新晋管理员无法看到群公告编辑入口")

        with allure.step("5. 接收端(管理员)进入群管理页面，验证各项管理权限控制开关（禁言/加好友/进群审批/黑名单/管理员列表）"):
            self.groupSettingR.click_group_manager()
            self.groupManagerR.wait_for_page_load()
            
            # 校验群管理员列表、进群审批、指定成员禁言、群黑名单(封禁用户)入口可见性
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.IT_GROUP_MANAGER), "❌ 无法看到【查看管理员列表】入口")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.JOIN_TO_GROUP_APPLY), "❌ 无法看到【成员进群审批】入口")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.GROUP_MEMBER_MUTE), "❌ 无法看到【指定成员禁言】入口")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.GROUP_BLACK_MEMBER), "❌ 无法看到【群黑名单/封禁用户】入口")
            
            # 校验开关存在与启用状态（进群验证开关、全员禁言开关、禁止互加好友开关）
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.JOIN_TO_GROUP_VERIFY_SWITCH), "❌ 无法看到【开启/关闭进群验证】开关")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.ALL_MEMBER_MUTE_SWITCH), "❌ 无法看到【全员禁言】开关")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.UN_ADD_FRIEND_EACH_OTHER_SWITCH), "❌ 无法看到【禁止互加好友】开关")

        with allure.step("6. 群主端退回群聊页面，并发送一条测试消息"):
            self.groupManagerS.click_back_button()  # 返回管理员列表
            self.groupManagerS.click_back_button()  # 返回群设置
            self.groupSettingS.click_iv_back_button()  # 返回聊天页面
            self.chatS.wait_for_chat_page_load()
            self.chatS.input_text("管理员权限测试消息")
            self.chatS.click_send_button()
            time.sleep(1)

        with allure.step("7. 接收端(管理员)回退至聊天页面，校验消息管理权限（删除/撤回成员消息）"):
            self.groupManagerR.click_back_button()  # 返回群设置
            self.groupSettingR.click_iv_back_button()  # 返回聊天页面
            self.chatR.wait_for_chat_page_load()
            
            # 接收端(管理员)长按群主发送的最后一条消息，验证长按菜单中同时包含“撤回”和“删除”
            self.chatLongPressR.long_press_last_message()
            self.chatLongPressR.wait_for_long_press_dialog()
            
            # 校验菜单中是否同时包含删除和撤回选项
            has_revoke = self.chatLongPressR.is_element_exist(self.chatLongPressR.get_menu_item_by_name("撤回"), timeout=2, raise_exception=False)
            has_delete = self.chatLongPressR.is_element_exist(self.chatLongPressR.get_menu_item_by_name("删除"), timeout=2, raise_exception=False)
            check.is_true(has_revoke and has_delete, "❌ 管理员长按成员消息时，没有同时展现【撤回】与【删除】权限选项")
            
            # 回退/关闭长按菜单弹窗返回聊天页面
            self.chatLongPressR.back()
