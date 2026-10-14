import pytest
import allure
import time
import pytest_check as check
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.add_friend.add_friend_page import AddFriendPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER3

TARGET_SEARCH_KEY = PRIVATE_USER1.phone
TARGET_FRIEND_NAME = PRIVATE_USER1.name

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



@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-联系人与好友')
class TestSmokeContacts(BaseSmokeContacts):
    """联系人与好友模块冒烟用例集"""

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('外部好友搜索与申请')
    @allure.title('通过右上角加号菜单添加朋友 - 正常搜索跳转与按钮状态校验')
    def test_smoke_search_and_view_friend_external(self):
        search_key = TARGET_SEARCH_KEY
        with allure.step('1. 进入添加朋友页面'):
            self.mainPage.go_to_main_page()
            self.homePage.click_add_button()
            self.homePage.click_add_friend()
        with allure.step(f'2. 输入搜索关键字 {search_key} 并确认'):
            self.addFriendPage.search_friend(search_key)
        with allure.step('3. 校验成功跳转到资料详情页，并验证好友/非好友基础控件存在'):
            is_loaded = self.contactDetailPage.wait_for_detail_page_load(timeout=8)
            check.is_true(is_loaded, '❌ 搜索后未能在超时时间内成功跳转到资料详情页')
            if self.contactDetailPage.has_add_friend_button():
                check.is_true(True, 'ℹ️ 目标对象当前为非好友状态，[申请加好友] 按钮显示正常')
            else:
                send_msg_exist = self.contactDetailPage.has_send_message_button()
                check.is_true(send_msg_exist, '❌ 目标对象已是好友状态，但资料详情页未显示 [发送消息] 按钮')


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('本地通讯录查看好友')
    @allure.title('在好友列表中搜索并查看好友资料详情-状态：已完成')
    def test_smoke_view_friend_detail_local(self):
        """测试进入通讯录好友列表，通过搜索精准定位好友并查看其资料卡昵称及ID完整性"""
        friend_name = TARGET_FRIEND_NAME
        with allure.step('1. 导航进入通讯录好友列表页面'):
            self.mainPage.go_to_main_page()
            self.homePage.click_bottom_expand_button()
            self.homePage.click_friend()
            is_on_friend_page = self.homePage.wait_for_friend_page_load(timeout=8)
            check.is_true(is_on_friend_page, '❌ 未能成功导航进入通讯录好友页面')

        with allure.step(f'2. 在好友列表中定位并点击指定好友: {friend_name}'):
            click_res = self.contactSelectPage.click_contact_by_name(friend_name, search=False, raise_exception=False)
            if not click_res:
                click_res = self.contactSelectPage.click_contact_by_name(friend_name, search=True)
            check.is_true(click_res, f'❌ 通讯录列表中未能找到并点击好友: {friend_name}')

        with allure.step('3. 验证进入了好友资料详情页，且基础信息完整展示'):
            time.sleep(0.5)
            is_loaded = self.contactDetailPage.wait_for_detail_page_load(timeout=2)
            check.is_true(is_loaded, '❌ 点击好友项后未能成功进入好友资料详情页')

            display_name = self.contactDetailPage.get_formatted_friend_name()
            check.is_in(friend_name, display_name, f"❌ 详情页显示名称 '{display_name}' 与预期好友 '{friend_name}' 不匹配")

            st_id = self.contactDetailPage.get_st_id()
            check.is_true(bool(st_id), '❌ 好友资料详情页显示的三条 ID 为空')
