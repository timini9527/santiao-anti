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
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2


@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群管理双端验证")
class TestGroupManagerDouble:
    """群管理功能双端（群主发端与成员收端）协同验证测试"""

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象，自动建群并让群主驻留群管理页面，普通成员驻留聊天页面"""
        # 发送端 (群主/Sender) 页面初始化
        self.mainS = MainPage(driver_sender)
        self.homeS = HomePage(driver_sender)
        self.groupCreateS = GroupCreatePage(driver_sender)
        self.groupSettingS = GroupSettingPage(driver_sender)
        self.groupManagerS = GroupManagerPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.contactSelectS = ContactSelectPage(driver_sender)

        # 接收端 (群成员/Receiver) 页面初始化
        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)

        # 创建群名称标识
        self.temp_group_name = None

        with allure.step("-> [前置准备] 发送端(群主)发起群聊创建临时群，拉取 Receiver 进群"):
            self.homeS.click_add_button()
            self.homeS.click_start_group_chat()
            self.contactSelectS.wait_for_contact_and_group_select_page_load()
            # 必须拉取 receiver 账号（即 PRIVATE_USER1.name）
            self.contactSelectS.click_contact_by_name(PRIVATE_USER1.name)
            # 再拉取一个备用账号以确保是三人及以上群聊
            self.contactSelectS.click_contact_by_name(PRIVATE_USER2.name)
            self.contactSelectS.click_action_button()

            # 等待进群，获取当前临时群名称
            self.chatS.wait_banner_message_disappear()
            self.chatS.wait_for_chat_page_load()
            self.temp_group_name = self.chatS.get_group_name()

        with allure.step("-> [前置准备] 接收端(普通成员)进入该群聊天界面"):
            self.mainR.go_to_main_page()
            self.chatListR.enter_chat(self.temp_group_name)
            self.chatR.wait_for_chat_page_load()

        with allure.step("-> [前置准备] 发送端进入该群【群管理】页面"):
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_page_load()

        yield

        # 清理环境，双端退回主页，防止影响后续测试
        with allure.step("-> [环境清理] 双端返回首页"):
            try:
                # 群主侧退回首页
                self.groupManagerS.click_back_button()
                self.groupSettingS.click_iv_back_button()
                self.chatS.click_back_button()
                self.mainS.go_to_main_page()
            except Exception as e:
                logger.warning(f"⚠️ [Cleanup] 群主侧返回首页失败: {e}")

            try:
                # 成员侧退回首页
                self.mainR.go_to_main_page()
            except Exception as e:
                logger.warning(f"⚠️ [Cleanup] 群成员侧返回首页失败: {e}")

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
