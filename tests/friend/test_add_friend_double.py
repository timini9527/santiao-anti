import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.add_friend_page import AddFriendPage
from pages.friend.new_friend_page import NewFriendPage
from pages.chat_options.contact.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from pages.chat.core.chat_page import ChatPage
from appium.webdriver.common.appiumby import AppiumBy
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER3





SENDER_NAME = PRIVATE_USER3.name
RECEIVER_NAME = PRIVATE_USER1.name
RECEIVER_PHONE = PRIVATE_USER1.phone
VERIFY_MESSAGE = f"你好，我是 {SENDER_NAME}，申请加你为好友。"


@allure.epic("IM核心功能测试")
@allure.feature("通讯录与好友管理")
@allure.story("双端好友申请处理")
class TestAddFriendDouble:
    """双端好友申请与验证处理测试集 (对应 0.4 添加好友模块 新朋友申请处理)"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender, driver_receiver):
        """双端前置与后置：初始化两端对应的 Page Object"""
        # S 端 (发送方 Sender)
        self.mainPageS = MainPage(driver_sender)
        self.homePageS = HomePage(driver_sender)
        self.addFriendPageS = AddFriendPage(driver_sender)
        self.newFriendPageS = NewFriendPage(driver_sender)
        self.contactDetailPageS = ContactDetailPage(driver_sender)
        self.contactSelectPageS = ContactSelectPage(driver_sender)
        self.chatPageS = ChatPage(driver_sender)

        # R 端 (接收方 Receiver)
        self.mainPageR = MainPage(driver_receiver)
        self.homePageR = HomePage(driver_receiver)
        self.addFriendPageR = AddFriendPage(driver_receiver)
        self.newFriendPageR = NewFriendPage(driver_receiver)
        self.contactDetailPageR = ContactDetailPage(driver_receiver)
        self.contactSelectPageR = ContactSelectPage(driver_receiver)
        self.chatPageR = ChatPage(driver_receiver)

        yield
        for mainPage in [self.mainPageS, self.mainPageR]:
            try:
                mainPage.go_to_main_page()
            except Exception as e:
                logger.error(f"⚠️ [Teardown] 返回首页失败: {e}")

    def _sender_send_friend_request(self, search_key: str, verify_message: str):
        """辅助方法：S端进入添加朋友，搜索R端并发送好友申请"""
        self.homePageS.click_add_button()
        self.homePageS.click_add_friend()
        self.addFriendPageS.wait_for_add_friend_page(timeout=10)
        self.addFriendPageS.search_friend_by_content(search_key)
        self.addFriendPageS.click_confirm_search()
        self.addFriendPageS.click_search_result_item()
        
        # 点击添加好友并输入备注发送
        self.contactDetailPageS.click_add_friend_button()
        self.addFriendPageS.wait_for_send_friend_verify_page(timeout=10)

        self.addFriendPageS.input_remark(verify_message)
        self.addFriendPageS.click_finish()

        # 校验发送成功提示
        toast = self.addFriendPageS.get_toast("发送成功")
        check.is_in("发送成功", toast, "❌ S端点击发送好友申请后，未弹出 [发送成功] Toast 提示")

    def _go_to_new_friend_page(self, side='R'):
        """辅助方法：进入‘新的朋友’申请列表页"""
        homePage = self.homePageR if side == 'R' else self.homePageS
        homePage.click_bottom_expand_button()
        homePage.click_friend()
        homePage.wait_for_friend_page_load()
        homePage.click_new_friend()

    def _go_to_contact_detail_from_list(self, name: str, side='R', raise_exception: bool = True) -> bool:
        """辅助方法：在好友通讯录列表中查找并进入指定好友的详情页"""
        mainPage = self.mainPageR if side == 'R' else self.mainPageS
        homePage = self.homePageR if side == 'R' else self.homePageS
        contactSelect = self.contactSelectPageR if side == 'R' else self.contactSelectPageS
        contactDetail = self.contactDetailPageR if side == 'R' else self.contactDetailPageS
        
        mainPage.go_to_main_page()
        homePage.click_bottom_expand_button()
        homePage.click_friend()
        homePage.wait_for_friend_page_load()
        
        click_ok = contactSelect.click_contact_by_name(name, raise_exception=raise_exception, search=False)
        if click_ok:
            contactDetail.wait_for_detail_page_load(timeout=8)
        return click_ok

    def _accept_friend_request(self, applicant_name: str, side='R') -> bool:
        """辅助方法：进入新朋友列表并同意好友申请"""
        self._go_to_new_friend_page(side)
        newFriendPage = self.newFriendPageR if side == 'R' else self.newFriendPageS
        newFriendPage.wait_for_new_friend_page_load()
        click_ok = newFriendPage.click_accept_btn_by_name(applicant_name)
        return click_ok


    @allure.story("申请处理")
    @allure.title("双端协作 - 同意好友申请并交叉校验通讯录-状态：已完成")
    def test_double_add_friend_agree(self):
        """测试 S 端发起申请，R 端在新朋友列表接受，双方成功建立好友关系并校验通讯录"""
        with allure.step("1. S端向R端发送好友验证申请"):
            self._sender_send_friend_request(RECEIVER_PHONE, VERIFY_MESSAGE)

        with allure.step(f"2. R端在新朋友列表中接受 {SENDER_NAME} 的好友申请"):
            click_ok = self._accept_friend_request(SENDER_NAME, side='R')
            check.is_true(click_ok, f"❌ R端在新朋友列表中未找到 {SENDER_NAME} 的接受按钮")

        with allure.step("3. 校验R端申请列表状态变更为‘已添加’"):
            is_agreed = self.newFriendPageR.verify_apply_status(SENDER_NAME, "已添加")
            check.is_true(is_agreed, "❌ R端接受好友申请后，新朋友列表内状态文本未成功流转为已添加")

        with allure.step("4. 交叉校验通讯录：R端好友列表中应能成功点击进入 S 端详情"):
            click_success = self._go_to_contact_detail_from_list(SENDER_NAME, side='R')
            check.is_true(click_success, f"❌ R端好友列表中找不到刚添加的好友: {SENDER_NAME}")

        with allure.step("5. 交叉校验通讯录：S端好友列表中应能成功点击进入 R 端详情"):
            click_success = self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            check.is_true(click_success, f"❌ S端好友列表中找不到刚接受好友申请的联系人: {RECEIVER_NAME}")

        with allure.step("6. S端删除好友以进行后置清理"):
            self.contactDetailPageS.delete_contact()


    @allure.story("申请处理")
    @allure.title("双端协作 - 同意好友申请并设置备注且验证")
    def test_double_add_friend_with_remark(self):
        """测试 S 端发起申请，R 端进入申请详情并同意且设置备注，验证 R 端通讯录中以备注名显示该好友 (对应 ADD_HANDLE_004 P0)"""
        remark_name = f"{SENDER_NAME}_测试备注"

        with allure.step("1. S端向R端发送好友验证申请"):
            self._sender_send_friend_request(RECEIVER_PHONE, VERIFY_MESSAGE)

        with allure.step(f"2. R端在新朋友列表中点击 {SENDER_NAME} 的申请项，进入验证详情页"):
            self._go_to_new_friend_page(side='R')
            self.newFriendPageR.wait_for_new_friend_page_load()
            click_ok = self.newFriendPageR.click_apply_item_by_name(SENDER_NAME)
            check.is_true(click_ok, f"❌ R端在新朋友列表中未找到并点击 {SENDER_NAME} 的申请条目")

        with allure.step("3. R端在详情页中点击接受，并在验证设置页面中填写备注并点击完成"):
            accept_detail_locator = (AppiumBy.XPATH, '//*[@text="接受" or @text="同意"]')
            self.newFriendPageR.click(accept_detail_locator)
            self.addFriendPageR.wait_for_send_friend_verify_page(timeout=10)
            self.addFriendPageR.input_remark(remark_name)
            self.addFriendPageR.click_finish()

        with allure.step("4. 校验R端申请列表状态变更为‘已添加’"):
            is_agreed = self.newFriendPageR.verify_apply_status(SENDER_NAME, "已添加")
            check.is_true(is_agreed, "❌ R端设置备注同意好友申请后，新朋友列表内状态文本未成功流转为已添加")

        with allure.step(f"5. 验证 R端通讯录列表中成功以备注名 {remark_name} 显示该好友"):
            click_success = self._go_to_contact_detail_from_list(remark_name, side='R')
            check.is_true(click_success, f"❌ R端好友列表中找不到刚设置备注的好友: {remark_name}")

    @allure.story("申请处理")
    @allure.title("双端协作 - 删除好友后重新添加并交叉验证聊天消息能力恢复")
    def test_double_add_friend_after_deleted(self):
        """测试 S 端删除好友 R -> 交叉校验确认非好友 -> S 重新申请 -> R 同意 -> 双方聊天功能恢复 (对应 ADD_LIMIT_003 P0 & ADD_SYNC_008 P1)"""
        with allure.step("1. 确认前置：确保双方已经是好友关系"):
            is_friend = self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            
            if not is_friend:
                logger.info("ℹ️ S端与R端当前不是好友，准备先建立好友关系")
                self.mainPageS.go_to_main_page()
                self._sender_send_friend_request(RECEIVER_PHONE, "加个好友删除重试")
                self._accept_friend_request(SENDER_NAME, side='R')
                self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')

        with allure.step("2. S端在其个人详情页中删除好友 B"):
            delete_ok = self.contactDetailPageS.delete_contact()
            check.is_true(delete_ok, "❌ S端删除好友 B 失败")

        with allure.step("3. 校验双方均不再是好友（非好友关系校验）"):
            # 3.1 校验 S 端通讯录中无法找到 R 端
            has_receiver = self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S', raise_exception=False)
            check.is_false(has_receiver, f"❌ S端已删除 B，但 S端通讯录里仍然存在好友: {RECEIVER_NAME}")

            # 3.2 校验 R 端通讯录中无法找到 S 端
            has_sender = self._go_to_contact_detail_from_list(SENDER_NAME, side='R', raise_exception=False)
            check.is_false(has_sender, f"❌ S端已删除 B，但 R端通讯录里仍能找到 A端好友: {SENDER_NAME}")

        with allure.step("4. S端重新发起对 B 的添加好友申请"):
            self.mainPageS.go_to_main_page()
            self._sender_send_friend_request(RECEIVER_PHONE, VERIFY_MESSAGE)

        with allure.step("5. B端接受该申请建立好友关系"):
            self._accept_friend_request(SENDER_NAME, side='R')

        with allure.step("6. 交叉验证聊天能力同步恢复 (ADD_SYNC_008)"):
            # 6.1 S端通过搜索进入与R端的聊天窗口，发送消息
            self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            self.contactDetailPageS.click_send_message()
            self.chatPageS.wait_for_chat_page_load(timeout=10)
            chat_msg = "验证删除重加后的聊天同步能力_TEST"
            self.chatPageS.send_message(chat_msg)
            logger.info("⚙️ S端成功发送了测试聊天消息")

            # 6.2 R端返回主页，搜索进入与S端的聊天窗口，验证是否收到消息
            self._go_to_contact_detail_from_list(SENDER_NAME, side='R')
            self.contactDetailPageR.click_send_message()
            self.chatPageR.wait_for_chat_page_load(timeout=10)
            received_msg = self.chatPageR.find_message_content(index=-1, side='received')
            check.equal(received_msg, chat_msg, f"❌ 双端重新加回好友后，B端未成功收到A端发送的聊天消息，实际接收: {received_msg}")
