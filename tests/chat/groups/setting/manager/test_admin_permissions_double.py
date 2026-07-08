import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.system.main.main_page import MainPage
from pages.chat.groups.setting.general.group_setting_page import GroupSettingPage
from pages.chat.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.chat.groups.bot.group_bot_page import GroupBotPage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from locators.chat.groups.setting.general.group_setting_locator import GroupSettingLocator
from appium.webdriver.common.appiumby import AppiumBy


@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群管理员-分配管理员单独权限校验")
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
        self.groupBotR = GroupBotPage(driver_receiver)

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
            self.groupManagerS.click_all_switch(checked_str="false")
            self.groupManagerS.click_confirm_button()
            self.chatS.wait_banner_message_disappear()

        yield

        with allure.step("-> [环境清理] 群主移除管理员身份，双端返回首页"):
            try:
                self.groupManagerS.click_member_by_name(name=PRIVATE_USER1.name)
                self.groupManagerS.click_sure_button()
                self.groupManagerS.click_sure_content_button()
                self.chatS.wait_banner_message_disappear()
                
                self.mainS.go_to_main_page()
                self.mainR.go_to_main_page()
            except Exception as e:
                logger.warning(f"⚠️ [Cleanup] 环境复原清理失败: {e}")



    @allure.story("管理员权限集中校验")
    @allure.title("【管理员权限校验】全量权限入口的可见性与可操作状态校验-状态：已完成")
    def test_admin_all_permissions_ui_verification(self):
        """采用只读校验策略，一键检查分配给管理员的各项功能入口、开关状态及长按菜单权限（14项权限覆盖）"""

        with allure.step("1. 校验修改群头像权限"):
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_group_avatar()
            self.groupManagerR.click_confirm_button()
            is_displayed = self.groupSettingR.is_album_dialog_displayed()
            check.is_true(is_displayed, "❌ 未找到【相册弹窗】，管理员没有对应权限")
            self.groupSettingR.click_group_avatar_cancel()
            self.groupManagerR.click_iv_back_button()

        with allure.step("2. 校验修改群名称权限"):
            self.groupSettingR.click_group_name()
            dialog_message = self.groupSettingR.get_group_name_dialog_message()
            check.is_in("修改群聊名称后，将在群内通知其他成员", dialog_message, "❌ 未找到【修改群聊名称后，将在群内通知其他成员】提示")
            self.groupSettingR.click_remark_cancel()

        with allure.step("3. 校验编辑群公告权限"):
            self.groupSettingR.click_group_notice()
            dialog_message = self.groupSettingR.wait_for_notice_dialog_load()
            check.is_true(dialog_message, "❌ 未找到【群公告】弹窗")
            self.groupSettingR.click_back_button()

        with allure.step("4. 校验管理群成员权限"):
            is_displayed = self.groupSettingR.is_delete_member_btn_visible()
            check.is_true(is_displayed, "❌ 未找到【删除群成员】按钮")
            self.groupManagerR.click_iv_back_button()
        
        with allure.step("5. 校验删除（撤回）群成员消息权限"):
            self.chatLongPressR.long_press_last_message()
            self.chatLongPressR.wait_for_long_press_dialog()
            menu_res = self.chatLongPressR.get_menu_item_status("撤回")
            check.is_true(menu_res, "❌ 管理员长按消息菜单中缺少【撤回】或【删除】权限项")
            self.chatR.click_text_message_by_index(index=-1, side="all")

        with allure.step("6. 校验@所有人权限"):
            self.chatR.input_text("@")
            is_displayed = self.groupSettingR.is_at_all_displayed()
            check.is_true(is_displayed, "❌ 管理员输入 @ 后未能找到【所有人】选择项")
            self.groupSettingR.click_back_button()
            self.chatR.clear_input_text()

        with allure.step("7. 校验群助手权限"):
            self.chatR.click_more_button()
            self.groupSettingR.click_friend_header()
            is_group_assistant_visible = self.groupBotR.has_group_assistant_permission()
            check.is_false(is_group_assistant_visible, "❌ 管理员具有【群助手】权限")
            self.groupManagerR.click_iv_back_button()

        with allure.step("8. 校验查看管理员列表权限"):
            manager_permissions = ['管理员', '进群验证', '进群申请', '全员禁言', '指定成员禁言', '禁止群成员互相加好友', '群黑名单']
            # TODO：Android 这里有BUG
            self.groupSettingR.click_iv_back_button()
            self.chatR.click_more_button()

            self.groupSettingR.click_group_manager()
            permissions = self.groupManagerR.get_has_permissions_names()
            res = set(manager_permissions).issubset(set(permissions))
            check.is_true(res, f"❌ 管理员在群设置中无法看到【群管理】选项: {set(manager_permissions) - set(permissions)}")

        with allure.step("9. 接收端(管理员)退回聊天页面，以便环境清理"):
            self.groupManagerR.click_iv_back_button()
            self.groupSettingR.click_iv_back_button()
