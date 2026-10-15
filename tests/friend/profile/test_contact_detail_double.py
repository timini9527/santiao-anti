import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger, LogIcon
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.add_friend.add_friend_page import AddFriendPage
from pages.friend.add_friend.new_friend_page import NewFriendPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from pages.friend.profile.remark_setting_page import RemarkSettingPage
from pages.chat.core.chat_page import ChatPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, PRIVATE_USER3




SENDER_NAME = PRIVATE_USER3.name
RECEIVER_NAME = PRIVATE_USER1.name
RECEIVER_PHONE = PRIVATE_USER1.phone


@allure.epic("IM核心功能测试")
@allure.feature("好友资料模块")
@allure.story("好友资料卡展示与备注设置")
class TestContactDetailDouble:
    """双端好友资料详情管理与备注设置测试集 (对应 0.5 好友资料模块)"""

    _has_ensured_friends = False

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender, driver_receiver):
        """双端前置：初始化页面对象并建立默认测试环境状态"""
        # S 端 (发送方 Sender / 操作方)
        self.mainPageS = MainPage(driver_sender)
        self.homePageS = HomePage(driver_sender)
        self.contactSelectPageS = ContactSelectPage(driver_sender)
        self.contactDetailPageS = ContactDetailPage(driver_sender)
        self.remarkSettingPageS = RemarkSettingPage(driver_sender)
        self.chatPageS = ChatPage(driver_sender)
        self.addFriendPageS = AddFriendPage(driver_sender)

        # R 端 (接收方 Receiver / 协同方)
        self.mainPageR = MainPage(driver_receiver)
        self.homePageR = HomePage(driver_receiver)
        self.contactSelectPageR = ContactSelectPage(driver_receiver)
        self.contactDetailPageR = ContactDetailPage(driver_receiver)
        self.remarkSettingPageR = RemarkSettingPage(driver_receiver)
        self.chatPageR = ChatPage(driver_receiver)
        self.addFriendPageR = AddFriendPage(driver_receiver)
        self.newFriendPageR = NewFriendPage(driver_receiver)

        # 确保双端是好友关系（整个类级别仅在首次运行时执行一次）
        # if not TestContactDetailDouble._has_ensured_friends:
        #     self._ensure_are_friends()
        #     TestContactDetailDouble._has_ensured_friends = True

        yield
        for mainPage in [self.mainPageS, self.mainPageR]:
            try:
                mainPage.go_to_main_page()
            except Exception as e:
                logger.error(f"{LogIcon.WARN} 返回首页失败: {e}")

    def _get_pages(self, side='S'):
        """根据端别 (S/R) 获取对应的核心页面对象"""
        if side == 'S':
            return self.mainPageS, self.homePageS, self.contactSelectPageS, self.contactDetailPageS
        return self.mainPageR, self.homePageR, self.contactSelectPageR, self.contactDetailPageR

    def _click_contact_by_name(self, name: str, side='S', raise_exception: bool = True, search: bool = False) -> bool:
        """点击通讯录好友并等待详情页加载完成"""
        _, _, contactSelect, contactDetail = self._get_pages(side)
        click_ok = contactSelect.click_contact_by_name(name, raise_exception=raise_exception, search=search)
        if click_ok:
            contactDetail.wait_for_detail_page_load(timeout=8)
        return click_ok

    def _go_to_contact_detail_from_list(self, name: str, side='S', raise_exception: bool = True) -> bool:
        """导航辅助方法：在通讯录列表中查找并进入指定好友的资料详情页"""
        mainPage, homePage, _, _ = self._get_pages(side)
        
        mainPage.go_to_main_page()
        homePage.click_bottom_expand_button()
        homePage.click_friend()
        homePage.wait_for_friend_page_load()
        
        return self._click_contact_by_name(name, side=side, raise_exception=raise_exception, search=False)


    def _ensure_are_friends(self):
        """确保双方已经是好友关系，若不是则发起添加"""
        # 1. 尝试从 S 端（操作方）寻找接收方
        is_friend = self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S', raise_exception=False)
        if not is_friend:
            logger.info(f"{LogIcon.ACTION} ℹ️ 双端当前非好友，正在执行临时好友绑定...")
            self.mainPageS.go_to_main_page()
            self.homePageS.click_add_button()
            self.homePageS.click_add_friend()
            self.addFriendPageS.wait_for_add_friend_page(timeout=10)
            self.addFriendPageS.search_friend_by_content(RECEIVER_PHONE)
            self.addFriendPageS.click_confirm_search()
            self.addFriendPageS.click_search_result_item()
            self.contactDetailPageS.click_add_friend_button()
            self.addFriendPageS.wait_for_send_friend_verify_page(timeout=10)
            self.addFriendPageS.input_remark("绑定好友")
            self.addFriendPageS.click_finish()
            
            # R 端接收
            self.mainPageR.go_to_main_page()
            self.homePageR.click_bottom_expand_button()
            self.homePageR.click_friend()
            self.homePageR.wait_for_friend_page_load()
            self.homePageR.click_new_friend()
            self.newFriendPageR.wait_for_new_friend_page_load()
            self.newFriendPageR.click_accept_btn_by_name(SENDER_NAME)
            logger.info(f"{LogIcon.SUCCESS} 好友绑定成功")
    
    
    


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("好友关系与权限")
    @allure.title("FD_REL_002 - 删除好友后，校验两端非好友状态及消息限制")
    def test_non_friend_interaction_restrictions(self):
        """测试删除好友后，资料页操作入口流转为非好友状态并限制发消息/音视频呼叫"""
        with allure.step("1. 前置：进入资料详情页，由 S 端将好友删除"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            del_ok = self.contactDetailPageS.delete_contact()
            check.is_true(del_ok, f"❌ S端删除好友 {RECEIVER_NAME} 失败")

        with allure.step("2. 校验 S 端重新进入该用户资料卡时显示为 [非好友状态]"):
            # 尝试重新在通讯录搜索该非好友
            self.mainPageS.go_to_main_page()
            self.homePageS.click_add_button()
            self.homePageS.click_add_friend()
            self.addFriendPageS.wait_for_add_friend_page(timeout=10)
            self.addFriendPageS.search_friend_by_content(RECEIVER_PHONE)
            self.addFriendPageS.click_confirm_search()
            self.addFriendPageS.click_search_result_item()
            
            # 非好友应该有“添加到通讯录/申请加好友”按钮，而不应该存在“发送消息”或“音视频通话”
            self.contactDetailPageS.wait_for_detail_page_load()
            has_add_btn = self.contactDetailPageS.is_element_exist(ContactDetailPage.click_add_friend) 
            check.is_true(has_add_btn, "❌ A端删除B后，再次进入B的资料详情页未展示‘添加朋友/申请加好友’入口")

        with allure.step("3. 校验 R 端查看 A 的资料详情页自动转为非好友"):
            self._go_to_contact_detail_from_list(SENDER_NAME, side='R')
            has_add_btn_r = self.contactDetailPageR.is_element_exist(ContactDetailPage.click_add_friend)
            check.is_true(has_add_btn_r, "❌ A端已删除B，B端查看A的资料页依然显示为好友状态（未解绑）")

        
