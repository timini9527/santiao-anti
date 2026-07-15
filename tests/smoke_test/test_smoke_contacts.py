import pytest
import allure
import pytest_check as check
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.personal.add_friend_page import AddFriendPage
from pages.chat_options.contact.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1
from locators.common.contact_select_locator import ContactSelectLocator




class BaseSmokeContacts:
    """联系人与好友模块测试基类"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.addFriendPage = AddFriendPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception:
            pass


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-联系人与好友")
class TestSmokeContacts(BaseSmokeContacts):
    """联系人与好友模块冒烟用例集"""

    @allure.story("外部好友搜索与申请")
    @allure.title("通过右上角加号菜单添加朋友 - 正常搜索跳转与按钮状态校验")
    def test_smoke_search_and_view_friend_external(self):
        # 搜索测试号 (使用已配置的 PRIVATE_USER1 手机号或名称)
        search_key = "38100000224"

        with allure.step("1. 进入添加朋友页面"):
            self.mainPage.go_to_main_page()
            self.homePage.click_add_button()
            self.homePage.click_add_friend()

        with allure.step(f"2. 输入搜索关键字 {search_key} 并确认"):
            self.addFriendPage.search_friend(search_key)

        with allure.step("3. 校验成功跳转到资料详情页，并验证好友/非好友基础控件存在"):
            is_loaded = self.contactDetailPage.wait_for_detail_page_load(timeout=8)
            check.is_true(is_loaded, "❌ 搜索后未能在超时时间内成功跳转到资料详情页")
            
            # 若是非好友，验证有“申请加好友”按钮；若是好友，验证有“发送消息”按钮
            if self.contactDetailPage.has_add_friend_button():
                check.is_true(True, "ℹ️ 目标对象当前为非好友状态，[申请加好友] 按钮显示正常")
            else:
                send_msg_exist = self.contactDetailPage.is_element_exist(self.contactDetailPage.locators.SEND_MSG_BTN, timeout=3)
                check.is_true(send_msg_exist, "❌ 目标对象已是好友状态，但资料详情页未显示 [发送消息] 按钮")

    @allure.story("本地通讯录查看好友")
    @allure.title("在好友列表中搜索并查看好友资料详情")
    def test_smoke_view_friend_detail_local(self):
        friend_name = PRIVATE_USER1.name

        with allure.step("1. 从首页进入好友列表页面"):
            self.mainPage.go_to_main_page()
            self.homePage.click_friend()

        with allure.step(f"2. 在好友选择列表寻找并点击好友: {friend_name}"):
            # 等待列表加载
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            # 搜索好友
            self.contactSelectPage.input_search_keyword(friend_name)
            # 点击好友
            self.contactSelectPage.click_contact_by_name(friend_name)

        with allure.step("3. 验证进入了好友的资料详情页，且基本信息展示正常"):
            is_loaded = self.contactDetailPage.wait_for_detail_page_load(timeout=8)
            check.is_true(is_loaded, "❌ 未能成功进入好友资料详情页")
            
            # 好友姓名检查
            detail_nickname = self.contactDetailPage.get_contact_nickname()
            check.is_in(friend_name, detail_nickname, f"❌ 详情页昵称 '{detail_nickname}' 与预期好友昵称 '{friend_name}' 不匹配")
