import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.add_friend_page import AddFriendPage
from pages.chat_options.contact.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage


@allure.epic("IM核心功能测试")
@allure.feature("通讯录与好友管理")
@allure.story("添加好友功能")
class TestAddFriend:
    """添加好友功能自动化测试集 (基于 0.4 添加好友模块 用例文档重构)"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        """方法级前置与后置：初始化相关的 Page Object 并确保初始状态重置"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.addFriendPage = AddFriendPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"⚠️ [Teardown] 返回首页失败: {e}")


    def _home_to_add_friend(self):
        """从首页进入添加好友页面"""
        self.homePage.click_add_button()
        self.homePage.click_add_friend()
        is_loaded = self.addFriendPage.wait_for_add_friend_page(timeout=10)
        check.is_true(is_loaded, "❌ 未能成功进入添加朋友页面")


    @allure.story("添加好友入口")
    @allure.title("从首页加号进入添加朋友页并校验")
    def test_add_friend_entry_via_home_add_button(self):
        """测试从首页加号进入添加朋友页面，并校验页面标题和基础元素展示"""
        with allure.step("1. 在首页点击右上角加号并选择添加朋友"):
            self._home_to_add_friend()

        with allure.step("2. 校验搜索框入口占位符文本是否存在"):
            entry_text = self.addFriendPage.get_search_input_text()
            check.is_in("三条号/手机号", entry_text, "❌ 添加朋友页搜素框的占位文本不匹配，未展示三条号/手机号等")

    @allure.story("添加好友页面")
    @allure.title("进入添加朋友页并点击返回")
    def test_add_friend_page_back(self):
        """测试进入添加朋友页面后，点击左上角返回按钮，能够成功返回主页"""
        with allure.step("1. 进入添加朋友页面并等待加载"):
            self._home_to_add_friend()

        with allure.step("2. 点击左上角返回按钮"):
            self.addFriendPage.click_back()

        with allure.step("3. 校验成功返回到主页会话列表"):
            is_on_home = self.homePage.wait_home_page(timeout=5)
            check.is_true(is_on_home, "❌ 点击返回按钮后，未能成功退回主页面")

    @allure.story("搜索")
    @allure.title("搜索框为空时的拦截校验")
    def test_add_friend_search_empty_input(self):
        """测试在添加好友搜索框中不输入任何内容，确认是否不发起搜索或不进行跳转"""
        with allure.step("1. 进入添加朋友页面"):
            self._home_to_add_friend()

        with allure.step("2. 点击搜索框，保持为空状态"):
            self.addFriendPage.click_search_input()

        with allure.step("3. 校验确认搜索标识不可见，无法执行无效搜索"):
            is_confirm_visible = self.addFriendPage.is_element_exist(
                AddFriendLocator.TV_SEARCH_KEY_MARK, timeout=2
            )
            check.is_false(is_confirm_visible, "❌ 未输入内容时，确认搜索按钮异常显示，预期不应发起搜索")


    @allure.story("搜索")
    @allure.title("搜索框输入空格时的拦截校验")
    def test_add_friend_search_spaces_blocked(self):
        """测试在添加好友搜索框输入空格，点击确认搜索时，被系统拦截并留在当前页"""
        with allure.step("1. 进入添加朋友页面"):
            self._home_to_add_friend()

        with allure.step("2. 在搜索框输入空格并点击确认搜索"):
            self.addFriendPage.search_friend_by_content("   ")
            self.addFriendPage.click_confirm_search()

        with allure.step("3. 校验页面并未跳转，依然停留在添加好友搜索页面"):
            is_on_page = self.addFriendPage.wait_for_add_friend_page(timeout=5)
            check.is_true(is_on_page, "❌ 输入空格进行搜索后跳转了页面，预期应在原页面拦截")

    @allure.story("搜索")
    @allure.title("搜索不存在账号 - 验证用户不存在Toast提示")
    def test_add_friend_search_non_existent_account(self):
        """测试搜索不存在的手机号，校验应用会弹出对应的用户不存在Toast"""
        non_existent_key = "19999999999"

        with allure.step("1. 进入添加朋友页面"):
            self._home_to_add_friend()

        with allure.step(f"2. 输入不存在的手机号关键字 {non_existent_key} 并确认搜索"):
            self.addFriendPage.search_friend_by_content(non_existent_key)
            self.addFriendPage.click_confirm_search()

        with allure.step("3. 校验弹出 ‘用户不存在’ 提示"):
            toast_msg = self.addFriendPage.get_toast("用户不存在")
            check.equal(toast_msg, "用户不存在", "❌ 搜索不存在账号时，未弹出预期 [用户不存在] 提示")

    @allure.story("搜索")
    @allure.title("通过手机号搜索正常账号并校验资料详情")
    def test_add_friend_search_success_and_view_profile(self):
        """测试搜索正常测试账号，成功进入资料详情页并校验详情字段展示"""
        search_key = "38100000224"

        with allure.step("1. 进入添加朋友页面"):
            self._home_to_add_friend()

        with allure.step(f"2. 输入有效搜索关键字 {search_key}，搜索并点击进入结果项"):
            self.addFriendPage.search_friend_by_content(search_key)
            self.addFriendPage.click_confirm_search()
            self.addFriendPage.click_search_result_item()

        with allure.step("3. 校验跳转到个人资料详情页并等待加载"):
            is_loaded = self.contactDetailPage.wait_for_detail_page_load(timeout=10)
            check.is_true(is_loaded, "❌ 搜索成功后，未能正常跳转到个人资料详情页")

        with allure.step("4. 校验个人资料详情页基本元素展示（昵称/三条ID）"):
            nickname = self.contactDetailPage.get_contact_nickname()
            check.is_true(bool(nickname), "❌ 资料页昵称为空")
            st_id = self.contactDetailPage.get_st_id()
            check.is_true(bool(st_id), "❌ 资料页三条ID为空")

    @allure.story("申请")
    @allure.title("发送好友验证申请流")
    def test_add_friend_request_flow(self):
        """测试发起好友申请，填写验证备注信息并发送的完整添加好友申请流"""
        search_key = "38100000224"
        verify_message = "测试验证信息：你好，我是自动化测试助手。"

        with allure.step("1. 搜索目标账号并跳转到详情页"):
            self._home_to_add_friend()
            self.addFriendPage.search_friend_by_content(search_key)
            self.addFriendPage.click_confirm_search()
            self.addFriendPage.click_search_result_item()
            self.contactDetailPage.wait_for_detail_page_load()

        with allure.step("2. 判断是否已是好友。若是非好友，则发起申请加好友"):
            if self.contactDetailPage.has_add_friend_button():
                self.contactDetailPage.click_add_friend()

                with allure.step("3. 在发送朋友验证页面，输入备注并提交发送申请"):
                    self.addFriendPage.click_send_apply(verify_message)

                with allure.step("4. 校验是否成功发送申请并返回详情页"):
                    toast = self.addFriendPage.get_toast("发送成功")
                    check.is_in("发送成功", toast, "❌ 点击发送好友申请后，未弹出预期 Toast 提示")

                    is_loaded = self.contactDetailPage.wait_for_detail_page_load(timeout=8)
                    check.is_true(is_loaded, "❌ 发送好友申请后，未能自动返回到资料详情页")
            else:
                logger.warning(f"⚠️ [Skip Action] 目标用户 [{search_key}] 已经是好友状态，跳过发起申请流程")
