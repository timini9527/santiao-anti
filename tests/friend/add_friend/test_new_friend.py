import os

import allure
import pytest
import pytest_check as check

from core.logger_utils import logger
from pages.friend.add_friend.add_friend_page import AddFriendPage
from pages.friend.add_friend.new_friend_page import NewFriendPage
from pages.home.home_page import HomePage
from pages.main.main_page import MainPage





@allure.epic("IM核心功能测试")
@allure.feature("通讯录与好友管理")
@allure.story("新的朋友列表")
class TestNewFriend:
    """新的朋友页面入口、申请记录展示和清空操作测试。"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.newFriendPage = NewFriendPage(driver_sender)
        self.addFriendPage = AddFriendPage(driver_sender)

        if not self.newFriendPage.wait_for_new_friend_page_load(2, False):
            if not self.homePage.wait_for_friend_page_load(2, False):
                self.mainPage.go_to_main_page(raise_exception=False)
                assert self.homePage.go_to_friend_page(2, False), "❌ 未能进入好友页面"
            self.homePage.click_new_friend()
            assert self.newFriendPage.wait_for_new_friend_page_load(5, False), "❌ 未能进入新的朋友页面"

        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as error:
            logger.error(f"⚠️ [Teardown] 返回主页失败: {error}")



    @allure.title("进入新的朋友页并返回好友列表-状态：已完成")
    def test_new_friend_entry_and_back(self):
        with allure.step("1. 点击新的朋友页返回按钮"):
            self.newFriendPage.click_iv_back()

        with allure.step("2. 校验返回好友列表"):
            is_loaded = self.homePage.wait_for_friend_page_load(5, False)
            check.is_true(is_loaded, "❌ 返回后未显示好友列表")


    @allure.title("新的朋友申请记录展示完整-状态：已完成")
    def test_new_friend_apply_list_display(self):
        with allure.step("1. 获取当前可见的申请人昵称"):
            apply_names = self.newFriendPage.get_apply_item_texts()
            if not apply_names:
                pytest.skip("当前测试账号没有好友申请记录，无法校验申请列表展示")

        with allure.step("2. 校验每条申请记录均展示申请人昵称"):
            check.is_true(
                all(name for name in apply_names),
                f"❌ 申请列表存在昵称为空的记录: {apply_names}",
            )


    @allure.title("取消清空申请记录后列表保持不变-状态：已完成")
    def test_new_friend_clear_cancel(self):
        with allure.step("1. 记录清空前的申请人昵称"):
            names_before = self.newFriendPage.get_apply_item_texts()
            if not names_before:
                pytest.skip("当前测试账号没有好友申请记录，无法校验取消清空")

        with allure.step("2. 点击清空并在确认弹窗中取消"):
            self.newFriendPage.click_fb_delete()
            self.newFriendPage.click_cancel_btn()

        with allure.step("3. 校验申请记录未被清空"):
            names_after = self.newFriendPage.get_apply_item_texts()
            check.equal(names_after, names_before, "❌ 取消清空后申请记录发生变化")


    @allure.title("确认清空全部申请记录-状态：待显式执行")
    @pytest.mark.destructive
    def test_new_friend_clear_confirm(self):

        with allure.step("1. 确认当前存在可清空的申请记录"):
            names_before = self.newFriendPage.get_apply_item_texts()
            if not names_before:
                pytest.skip("当前测试账号没有好友申请记录，无法校验确认清空")

        with allure.step("2. 点击清空并确认"):
            self.newFriendPage.click_fb_delete()
            self.newFriendPage.click_confirm_btn()

        with allure.step("3. 校验申请记录已全部清空"):
            names_after = self.newFriendPage.get_apply_item_texts()
            check.equal(names_after, [], "❌ 确认清空后仍存在申请记录")
