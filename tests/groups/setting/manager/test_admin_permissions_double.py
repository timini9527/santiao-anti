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
from appium.webdriver.common.appiumby import AppiumBy


@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群管理员权限校验")
class TestAdminPermissionsDouble:
    """群管理员权限双端集中检验用例"""

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象，添加普通成员为管理员并全开权限，后置进行身份移除还原"""
        self.mainS = MainPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.groupSettingS = GroupSettingPage(driver_sender)
        self.groupManagerS = GroupManagerPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.chatLongPressR = ChatLongPressPage(driver_receiver)
        self.groupSettingR = GroupSettingPage(driver_receiver)
        self.groupManagerR = GroupManagerPage(driver_receiver)

        with allure.step("-> [前置准备] 发送端(群主)和接收端(普通成员)进入指定群聊"):
            self.chatListS.enter_chat(GROUP_STRATEGY.name)
            self.chatS.wait_for_chat_page_load()
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()

        with allure.step("-> [前置准备] 群主将普通成员设为管理员并全开权限"):
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_page_load()
            self.groupManagerS.click_administrators()
            self.groupManagerS.wait_for_admin_page_load()
            self.groupManagerS.click_add_admin()
            self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
            # 全选权限 (将 checked_str="false" 的全部开关点击为选中以赋予所有权限)
            self.groupManagerS.click_all_switch(checked_str="false")
            self.groupManagerS.click_confirm_button()
            self.chatS.wait_banner_message_disappear()

        yield

        with allure.step("-> [环境清理] 群主移除管理员身份，双端返回首页"):
            try:
                # 群主端移除管理员
                self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
                self.groupManagerS.click_sure_button()
                self.groupManagerS.click_sure_content_button()
                self.chatS.wait_banner_message_disappear()
                
                # 双端返回主页
                self.mainS.go_to_main_page()
                self.mainR.go_to_main_page()
            except Exception as e:
                logger.warning(f"⚠️ [Cleanup] 环境复原清理失败: {e}")

    @allure.story("管理员权限集中校验")
    @allure.title("【管理员权限校验】全量权限入口的可见性与可操作状态校验")
    def test_admin_all_permissions_ui_verification(self):
        """采用只读校验策略，一键检查分配给管理员的各项功能入口、开关状态及长按菜单权限（14项权限覆盖）"""
        
        # 1. 聊天界面长按菜单权限校验：包含 撤回 / 删除 成员消息
        with allure.step("1. 校验管理员对其他成员消息的长按删除与撤回权限"):
            # 成员端长按群主最后发送的消息
            self.chatLongPressR.long_press_last_message()
            self.chatLongPressR.wait_for_long_press_dialog()
            # is_admin=True 校验是否同时存在撤回和删除菜单项
            menu_res = self.chatLongPressR.get_menu_items(msg_type="文本", is_admin=True)
            check.is_true(menu_res, "❌ 管理员长按消息菜单中缺少【撤回】或【删除】权限项")
            # 关闭长按菜单
            self.chatLongPressR.click_back_button()

        # 2. @所有人权限校验
        with allure.step("2. 校验聊天输入框的【@所有人】权限"):
            self.chatR.input_text("@")
            time.sleep(0.5)
            # 校验选择弹窗中是否包含 "所有人"
            has_at_all = self.chatR.is_element_exist((AppiumBy.XPATH, "//*[@text='所有人']"), timeout=3)
            check.is_true(has_at_all, "❌ 管理员输入 @ 后未能找到【所有人】选择项")
            # 清空输入框内容并隐藏键盘
            self.chatR.clear_input_text()

        # 3. 群详情页的编辑入口及管理入口可见性校验：包含 修改群头像/修改群名称/编辑群公告/查看管理员列表
        with allure.step("3. 进入群详情页，校验群名称/群公告编辑入口以及【群管理】入口"):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            
            # 校验修改群头像、群名称和群公告入口是否存在且可操作
            check.is_true(self.groupSettingR.is_element_exist(GroupSettingLocator.SETTING_CHAT_GROUP_HEADER), "❌ 未找到【修改群头像】设置项")
            check.is_true(self.groupSettingR.is_element_exist(GroupSettingLocator.SETTING_CHAT_GROUP_NAME), "❌ 未找到【修改群名称】设置项")
            check.is_true(self.groupSettingR.is_element_exist(GroupSettingLocator.SETTING_CHAT_GROUP_ANNOUNCEMENT), "❌ 未找到【编辑群公告】设置项")
            
            # 校验群管理入口可见（查看管理员列表的入口）
            is_mgr_visible = self.groupSettingR.is_group_manager_visible()
            check.is_true(is_mgr_visible, "❌ 管理员在群设置中无法看到【群管理】选项")

        # 4. 进入群管理子页面，校验具体的管理项开关：包含 开启/关闭进群验证/全员禁言/指定成员禁言/禁止互加好友/成员进群审批
        with allure.step("4. 进入群管理页面，校验子权限开关（禁言、进群验证等）"):
            self.groupSettingR.click_group_manager()
            self.groupManagerR.wait_for_page_load()
            
            # 校验 成员进群审批（进群申请入口）与 指定成员禁言 入口是否存在
            from locators.groups.setting.manager.group_manager_locator import GroupManagerLocator
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.JOIN_TO_GROUP_APPLY), "❌ 未找到【成员进群审批】入口")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.GROUP_MEMBER_MUTE), "❌ 未找到【指定成员禁言】入口")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.GROUP_BLACK_MEMBER), "❌ 未找到【封禁用户/黑名单】入口")
            
            # 校验 开启/关闭进群验证 开关、全员禁言开关 以及 禁止互加好友开关
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.JOIN_TO_GROUP_VERIFY_SWITCH), "❌ 未找到【进群验证】开关")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.ALL_MEMBER_MUTE_SWITCH), "❌ 未找到【全员禁言】开关")
            check.is_true(self.groupManagerR.is_element_exist(GroupManagerLocator.UN_ADD_FRIEND_EACH_OTHER_SWITCH), "❌ 未找到【禁止群成员互相加好友】开关")

        # 5. 返回聊天页面
        with allure.step("5. 接收端(管理员)退回聊天页面，以便环境清理"):
            self.groupManagerR.click_back_button()
            self.groupSettingR.click_iv_back_button()
