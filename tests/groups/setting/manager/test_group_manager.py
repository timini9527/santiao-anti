import pytest
import allure
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
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY


@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群管理")
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

        # 准备一个临时群并进入其群管理页面
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._enter_group_manager(friend_list)

        yield

        # 测试完毕后，返回首页以保证后续用例的前置状态干净
        self.mainPage.go_to_main_page()

    def _enter_group_manager(self, friend_list):
        """内部辅助：快速建群并导航进入群管理页面"""
        with allure.step("-> [前置准备] 在首页发起群聊创建临时群"):
            self.homePage.click_add_button()
            self.homePage.click_start_group_chat()
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()
            
            # 等待进群横幅消失，保证页面稳定
            self.chatPage.wait_banner_message_disappear()
            self.chatPage.wait_for_chat_page_load()

        with allure.step("-> 进入群详情设置页"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()

        with allure.step("-> 进入【群管理】子页面"):
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_page_load()

    # TODO：
    @allure.story("群管理-升级群组")
    @allure.title("【升级群组】功能正常使用校验")
    def test_upgrade_group_functionality(self):
        """测试【升级群组】功能是否正常使用"""
        
        with allure.step("1. 点击升级群组"):
            self.groupManagerPage.click_upgrade_group()

    @allure.story("群管理-管理员")
    @allure.title("【群管理员】功能正常使用校验")
    def test_group_manager_functionality(self):
        """测试【群管理员】功能是否正常使用"""
        
        with allure.step("1. 点击群管理员"):
            self.groupManagerPage.click_administrators()
    
    # TODO：
    @allure.story("群管理-群ID搜索开关")
    @allure.title("切换【群ID搜索】开关状态校验")
    def test_group_id_search_toggle(self):
        """测试群管理中【群ID搜索】开关的状态切换与校验"""
        with allure.step("1. 获取当前群ID搜索开关状态"):
            init_state = self.groupManagerPage.get_group_id_search_state()

        with allure.step("2. 点击切换群ID搜索开关"):
            self.groupManagerPage.click_group_id_search_switch()
            new_state = self.groupManagerPage.get_group_id_search_state()
            check.not_equal(init_state, new_state, "❌ 【群ID搜索】开关点击后状态未改变")

        with allure.step("3. 再次点击开关恢复至初始状态"):
            self.groupManagerPage.click_group_id_search_switch()
            final_state = self.groupManagerPage.get_group_id_search_state()
            check.equal(init_state, final_state, "❌ 【群ID搜索】开关恢复初始状态失败")

    @allure.story("群管理-进群验证开关")
    @allure.title("切换【进群验证】开关状态校验")
    def test_join_group_verify_toggle(self):
        """测试群管理中【进群验证】开关的状态切换与校验"""
        with allure.step("1. 获取当前进群验证开关状态"):
            init_state = self.groupManagerPage.get_join_group_verify_state()

        with allure.step("2. 点击切换进群验证开关"):
            self.groupManagerPage.click_join_group_verify_switch()
            new_state = self.groupManagerPage.get_join_group_verify_state()
            check.not_equal(init_state, new_state, "❌ 【进群验证】开关点击后状态未改变")

        with allure.step("3. 再次点击开关恢复至初始状态"):
            self.groupManagerPage.click_join_group_verify_switch()
            final_state = self.groupManagerPage.get_join_group_verify_state()
            check.equal(init_state, final_state, "❌ 【进群验证】开关恢复初始状态失败")

    @allure.story("群管理-全员禁言开关")
    @allure.title("切换【全员禁言】开关状态校验")
    def test_all_member_mute_toggle(self):
        """测试群管理中【全员禁言】开关的状态切换与校验"""
        with allure.step("1. 获取当前全员禁言开关状态"):
            init_state = self.groupManagerPage.get_all_member_mute_state()

        with allure.step("2. 点击切换全员禁言开关"):
            self.groupManagerPage.click_all_member_mute_switch()
            new_state = self.groupManagerPage.get_all_member_mute_state()
            check.not_equal(init_state, new_state, "❌ 【全员禁言】开关点击后状态未改变")

        with allure.step("3. 再次点击开关恢复至初始状态"):
            self.groupManagerPage.click_all_member_mute_switch()
            final_state = self.groupManagerPage.get_all_member_mute_state()
            check.equal(init_state, final_state, "❌ 【全员禁言】开关恢复初始状态失败")

    @allure.story("群管理-指定成员禁言")
    @allure.title("指定成员禁言页面初始状态校验")
    def test_specify_mute_page_init_state(self):
        """测试进入指定成员禁言页面时，默认无已禁言成员的状态"""
        with allure.step("1. 进入【指定成员禁言】子页面"):
            self.groupManagerPage.click_mute_member()
            self.groupManagerPage.wait_for_specify_mute_page_load()

        with allure.step("2. 校验已禁言群成员列表默认为空"):
            muted_members = self.groupManagerPage.get_muted_member_items()
            check.equal(len(muted_members), 0, "❌ 新建群聊的指定禁言成员列表默认不为空")

    @allure.story("群管理-禁止群成员互相加好友开关")
    @allure.title("切换【禁止群成员互相加好友】开关状态校验")
    def test_un_add_friend_each_other_toggle(self):
        """测试群管理中【禁止群成员互相加好友】开关的状态切换与校验"""
        with allure.step("1. 获取当前禁止互相加好友开关状态"):
            init_state = self.groupManagerPage.get_un_add_friend_each_other_state()

        with allure.step("2. 点击切换禁止互相加好友开关"):
            self.groupManagerPage.click_un_add_friend_each_other_switch()
            new_state = self.groupManagerPage.get_un_add_friend_each_other_state()
            check.not_equal(init_state, new_state, "❌ 【禁止群成员互相加好友】开关点击后状态未改变")

        with allure.step("3. 再次点击开关恢复至初始状态"):
            self.groupManagerPage.click_un_add_friend_each_other_switch()
            final_state = self.groupManagerPage.get_un_add_friend_each_other_state()
            check.equal(init_state, final_state, "❌ 【禁止群成员互相加好友】开关恢复初始状态失败")

    @allure.story("群管理-群黑名单")
    @allure.title("【群黑名单】功能正常使用校验")
    def test_group_blacklist_functionality(self):
        """测试群管理中【群黑名单】功能是否正常使用"""
        with allure.step("1. 点击群黑名单"):
            self.groupManagerPage.click_group_blacklist()
            self.groupManagerPage.wait_for_group_blacklist_page_load()

    @allure.story("群管理-转让群主")
    @allure.title("【转让群主】功能正常使用校验")
    def test_transfer_group_owner_functionality(self):
        """测试群管理中【转让群主】功能是否正常使用"""
        with allure.step("1. 点击转让群主"):
            self.groupManagerPage.click_transfer_group_owner()
            self.groupManagerPage.wait_for_transfer_group_owner_page_load()





