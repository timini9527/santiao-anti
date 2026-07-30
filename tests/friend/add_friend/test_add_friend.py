import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.add_friend.add_friend_page import AddFriendPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER4


@allure.epic("IM核心功能测试")
@allure.feature("通讯录与好友管理")
@allure.story("添加好友功能")
class TestAddFriend:
    """添加好友功能自动化测试集 (基于 0.4 添加好友模块 用例文档重构优化)"""

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


    @allure.story("添加好友页面")
    @allure.title("进入添加朋友页校验并点击返回-状态：已完成")
    def test_add_friend_entry_and_back(self):
        """测试从首页加号进入添加朋友页面，校验占位符，然后点击返回能成功回到主页"""
        with allure.step("1. 进入添加朋友页面并等待加载"):
            self._home_to_add_friend()

        with allure.step("2. 校验搜索框入口占位符文本是否存在"):
            entry_text = self.addFriendPage.get_search_input_text()
            check.is_in("三条ID/手机号/群ID", entry_text, "❌ 添加朋友页搜索框的占位文本不匹配")

        with allure.step("3. 点击左上角返回按钮"):
            self.addFriendPage.click_back()

        with allure.step("4. 校验成功返回到主页会话列表"):
            is_on_home = self.homePage.wait_home_page(timeout=5)
            check.is_true(is_on_home, "❌ 点击返回按钮后，未能成功退回主页面")


    @allure.story("搜索")
    @allure.title("搜索框为空/空格时的拦截校验-状态：已完成")
    def test_add_friend_search_empty_input(self):
        """测试在添加好友搜索框中不输入内容或输入空格，确认系统不展示搜索结果"""
        with allure.step("1. 进入添加朋友页面"):
            self._home_to_add_friend()

        with allure.step("2. 在搜索框中输入空格占位符"):
            self.addFriendPage.search_friend_by_content("    ")

        with allure.step("3. 校验搜索结果项不可见，无法发起无效搜索"):
            is_result = self.addFriendPage.get_search_result_item(raise_exception=False)
            check.is_false(is_result, "❌ 搜索为空或空格时，异常出现了搜索结果项")


    @allure.story("搜索")
    @allure.title("搜索不存在账号 - 验证未找到好友提示-状态：已完成")
    def test_add_friend_search_non_existent_account(self):
        """测试搜索不存在的账号，校验列表抛出未找到提示"""
        non_existent_key = "199999999991"

        with allure.step("1. 进入添加朋友页面"):
            self._home_to_add_friend()

        with allure.step(f"2. 输入不存在账号 {non_existent_key} 并确认搜索"):
            self.addFriendPage.search_friend_by_content(non_existent_key)
            self.addFriendPage.click_confirm_search()

        with allure.step("3. 校验弹出 ‘未找到好友/群组’ 提示"):
            msg = self.addFriendPage.get_search_result_item_message()
            check.equal("未找到好友/群组", msg, "❌ 搜索不存在账号时，未弹出预期 [未找到好友/群组] 提示")


    @allure.story("搜索")
    @allure.title("通过手机号搜索正常账号并校验资料详情-状态：已完成")
    def test_add_friend_search_success_and_view_profile(self):
        """测试搜索正常测试账号，成功进入资料详情页并校验详情字段展示"""
        search_key = PRIVATE_USER1.phone
        search_id = PRIVATE_USER1.st_id

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
            check.is_in(PRIVATE_USER1.name, nickname, f"❌ 资料页昵称为 {nickname}，不包含预期的 {PRIVATE_USER1.name}")
            st_id = self.contactDetailPage.get_st_id()
            check.is_in(search_id, st_id, f"❌ 资料页三条ID为 {st_id}，不包含预期的 {search_id}")


    @allure.story("申请")
    @allure.title("发送好友验证申请流-状态：已完成")
    def test_add_friend_request_flow(self):
        """测试发起好友申请，填写验证备注信息并发送的完整添加好友申请流"""
        search_key = PRIVATE_USER4.phone
        verify_message = "测试验证信息：你好，我是自动化测试助手。"

        with allure.step("1. 搜索目标账号并跳转到详情页"):
            self._home_to_add_friend()
            self.addFriendPage.search_friend_by_content(search_key)
            self.addFriendPage.click_confirm_search()
            self.addFriendPage.click_search_result_item()

        with allure.step("2. 判断是否已是好友。若是非好友，则发起申请加好友"):
            self.contactDetailPage.click_add_friend_button()
        
        with allure.step("3. 在发送朋友验证页面，输入备注并提交发送申请"):

            is_loaded = self.addFriendPage.wait_for_send_friend_verify_page()
            check.is_true(is_loaded, "❌ 未能成功进入发送朋友验证页面")
            self.addFriendPage.input_remark(verify_message)
            self.addFriendPage.click_finish()
        
        with allure.step("4. 校验是否成功发送申请"):
            toast = self.addFriendPage.get_toast("发送成功")
            check.is_in("发送成功", toast, "❌ 点击发送好友申请后，未弹出预期 Toast 提示")
            