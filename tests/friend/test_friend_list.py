import allure
import pytest
import time
import pytest_check as check

from core.logger_utils import logger, LogIcon
from pages.common.contact_select_page import ContactSelectPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.home.home_page import HomePage
from pages.main.main_page import MainPage
from strategy.chat.chat_strategy import PRIVATE_USER1





@allure.epic("IM核心功能测试")
@allure.feature("通讯录与好友管理")
@allure.story("好友列表")
class TestFriendList:
    """好友列表入口、内容展示和资料跳转测试。"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)

        if not self.homePage.wait_for_friend_page_load(2, False):
            self.mainPage.go_to_main_page(raise_exception=False)
            assert self.homePage.go_to_friend_page(2, False), "❌ 未能进入好友页面"

        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as error:
            logger.error(f"{LogIcon.WARN} 返回主页失败: {error}")


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("好友列表入口与基础内容展示-状态：已完成")
    def test_friend_list_entry_display(self):
        with allure.step("1. 校验好友列表固定入口"):
            check.equal(self.homePage.get_new_friend_text(), "新的朋友", "❌ 好友页未正确展示新的朋友入口")
            check.is_in("分组", self.homePage.get_category_manager_text(), "❌ 好友页未正确展示分组管理入口")

        with allure.step("2. 校验好友列表至少展示一位联系人"):
            contact_names = self.contactSelectPage.get_contact_names()
            check.is_true(contact_names, "❌ 好友列表没有展示任何联系人")


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("从好友列表点击联系人进入资料详情-状态：已完成")
    def test_friend_list_click_contact_opens_profile(self):
        with allure.step(f"1. 点击好友列表中的联系人 {PRIVATE_USER1.name}"):
            clicked = self.contactSelectPage.click_contact_by_name(PRIVATE_USER1.name, raise_exception=False, search=False)
            check.is_true(clicked, f"❌ 好友列表中未找到好友 {PRIVATE_USER1.name}")
            time.sleep(1)

        with allure.step("2. 校验进入目标好友资料页"):
            is_loaded = self.contactDetailPage.wait_for_detail_page_load()
            check.is_true(is_loaded, "❌ 点击好友后未进入资料详情页")
            actual_name = self.contactDetailPage.get_formatted_friend_name()
            check.equal(actual_name, PRIVATE_USER1.name, f"❌ 资料页好友昵称不匹配，实际为: {actual_name}")
