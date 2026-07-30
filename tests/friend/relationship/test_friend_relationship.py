import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.add_friend.add_friend_page import AddFriendPage
from pages.friend.add_friend.new_friend_page import NewFriendPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.friend.profile.remark_setting_page import RemarkSettingPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER3

SENDER_NAME = PRIVATE_USER3.name
RECEIVER_NAME = PRIVATE_USER1.name
RECEIVER_PHONE = PRIVATE_USER1.phone
VERIFY_MESSAGE = f"你好，我是 {SENDER_NAME}，申请加你为好友。"


@allure.epic("IM核心功能测试")
@allure.feature("好友关系管理")
@allure.story("双端好友关系流转与状态矩阵")
class TestFriendRelationship:
    """好友关系状态流转与双端交互测试集 (对应 0.1 好友关系.md)"""

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
        self.remarkSettingPageS = RemarkSettingPage(driver_sender)
        self.chatSettingPageS = ChatSettingPage(driver_sender)

        # R 端 (接收方 Receiver)
        self.mainPageR = MainPage(driver_receiver)
        self.homePageR = HomePage(driver_receiver)
        self.addFriendPageR = AddFriendPage(driver_receiver)
        self.newFriendPageR = NewFriendPage(driver_receiver)
        self.contactDetailPageR = ContactDetailPage(driver_receiver)
        self.contactSelectPageR = ContactSelectPage(driver_receiver)
        self.chatPageR = ChatPage(driver_receiver)
        self.remarkSettingPageR = RemarkSettingPage(driver_receiver)
        self.chatSettingPageR = ChatSettingPage(driver_receiver)

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
        self.addFriendPageS.wait_for_add_friend_page()
        self.addFriendPageS.search_friend_by_content(search_key)
        self.addFriendPageS.click_confirm_search()
        self.addFriendPageS.click_search_result_item()
        self.contactDetailPageS.wait_for_detail_page_load()
        is_unfriend_page = self.contactDetailPageS.is_add_friend_unfriend_visible()
        check.is_true(is_unfriend_page, "❌ 精确搜索后拉起资料卡失败，或界面未展示‘添加好友’申请入口")
        
        self.contactDetailPageS.click_add_friend_button()
        self.addFriendPageS.wait_for_send_friend_verify_page()
        self.addFriendPageS.input_remark(verify_message)
        self.addFriendPageS.click_finish()
        toast = self.addFriendPageS.get_toast("发送成功")
        check.is_true(toast, "❌ S端点击发送好友申请后，未弹出 [发送成功] Toast 提示")

    def _go_to_new_friend_page(self, side='R'):
        """辅助方法：进入‘新的朋友’申请列表页"""
        homePage = self.homePageR if side == 'R' else self.homePageS
        homePage.click_bottom_expand_button()
        homePage.click_friend()
        homePage.wait_for_friend_page_load()
        homePage.click_new_friend()

    def _go_to_contact_detail_from_list(self, name: str, side='R', raise_exception: bool = True, timeout: int = 8) -> bool:
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
            contactDetail.wait_for_detail_page_load(timeout=timeout)
        return click_ok



    @allure.story("好友申请与验证")
    @allure.title("同意好友申请并建立双向好友关系-状态：已完成")
    def test_relationship_flow_agree(self):
        """测试 S端 发起申请，R端 同意好友申请，双方成功建立好友关系并校验通讯录"""
        with allure.step("1. S端向R端发送好友验证申请"):
            self._sender_send_friend_request(RECEIVER_PHONE, VERIFY_MESSAGE)

        with allure.step(f"2. R端在新朋友列表中点击 {SENDER_NAME} 申请条目，点击接受"):
            self._go_to_new_friend_page(side='R')
            self.newFriendPageR.wait_for_new_friend_page_load()
            click_item = self.newFriendPageR.accept_apply_by_name(SENDER_NAME)
            check.is_true(click_item, f"❌ R端在新朋友列表中未找到并点击 {SENDER_NAME} 的申请项")

        with allure.step("3. 校验R端申请列表状态变更为‘已添加’"):
            is_agreed = self.newFriendPageR.verify_apply_status(SENDER_NAME, "已添加")
            check.is_true(is_agreed, "❌ R端接受好友申请后，新朋友列表内状态文本未成功流转为已添加")
            self.contactDetailPageR.click_iv_back()

        with allure.step("4. 交叉校验通讯录：R端好友列表中应能成功点击进入 S 端详情"):
            click_success = self._go_to_contact_detail_from_list(SENDER_NAME, side='R')
            check.is_true(click_success, f"❌ R端好友列表中找不到刚添加的好友: {SENDER_NAME}")

        with allure.step("5. 交叉校验通讯录：S端好友列表中应能成功点击进入 R 端详情"):
            click_success = self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            check.is_true(click_success, f"❌ S端好友列表中找不到刚接受好友申请的联系人: {RECEIVER_NAME}")

        with allure.step("6. S端删除好友以进行后置清理"):
            self.contactDetailPageS.delete_contact()


    @allure.story("好友申请与验证")
    @allure.title("左滑删除好友申请记录-状态：已完成")
    def test_relationship_flow_swipe_delete_apply(self):
        """测试 S端 发起好友申请，R端 在新朋友列表中左滑删除该申请记录"""
        with allure.step("1. S端向R端发送好友验证申请"):
            self._sender_send_friend_request(RECEIVER_PHONE, VERIFY_MESSAGE)

        with allure.step(f"2. R端进入新朋友页面，对 {SENDER_NAME} 的申请记录进行左滑删除"):
            self._go_to_new_friend_page(side='R')
            self.newFriendPageR.wait_for_new_friend_page_load()
            
            has_item = self.newFriendPageR.get_apply_item_by_name(SENDER_NAME)
            check.is_not_none(has_item, f"❌ R端在新朋友列表中未找到 {SENDER_NAME} 的申请条目")
            
            delete_ok = self.newFriendPageR.swipe_and_delete_by_name(SENDER_NAME)
            check.is_true(delete_ok, f"❌ R端左滑删除 {SENDER_NAME} 的申请记录操作失败")

        with allure.step(f"3. 验证 R端 新朋友列表中已不存在 {SENDER_NAME} 的申请项"):
            aft_item = self.newFriendPageR.get_apply_item_by_name(SENDER_NAME, timeout=2, raise_exception=False)
            check.is_none(aft_item, f"❌ R端在新朋友列表中仍然能找到 {SENDER_NAME} 的申请条目")
            self.newFriendPageR.click_iv_back()


    @allure.story("删除好友")
    @allure.title("删除好友关系与单向删除验证及重加恢复-状态：已完成")
    def test_relationship_flow_delete(self):
        """测试 S 端删除好友 R -> 交叉校验确认单向删除特征 -> S 重新申请 -> R 同意 -> 双方聊天功能恢复"""
        with allure.step("1. 确认前置：确保双方已经是好友关系，如果不是则先添加好友"):
            is_friend = self._go_to_contact_detail_from_list(RECEIVER_NAME, timeout=1, raise_exception=False, side='S')
            if not is_friend:
                self.mainPageS.go_to_main_page()
                self._sender_send_friend_request(RECEIVER_PHONE, "加个好友删除重试")
                self._go_to_new_friend_page(side='R')
                self.newFriendPageR.wait_for_new_friend_page_load()
                self.newFriendPageR.click_apply_item_by_name(SENDER_NAME)
                self.newFriendPageR.click_accept_in_detail()
                self.contactDetailPageR.click_iv_back()
                self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')

        with allure.step("2. S端在其个人详情页中删除好友 B"):
            delete_ok = self.contactDetailPageS.delete_contact()
            check.is_true(delete_ok, "❌ S端删除好友 B 失败")

        with allure.step("3. 校验好友关系变化（单向删除特征）"):
            has_receiver = self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S', raise_exception=False, timeout=2)
            check.is_false(has_receiver, f"❌ S端已删除 B，但 S端通讯录里仍然存在好友: {RECEIVER_NAME}")

            
            has_sender = self._go_to_contact_detail_from_list(SENDER_NAME, side='R', raise_exception=False, timeout=2)
            check.is_true(has_sender, f"❌ S端单向删除B后，B端通讯录中应当依旧保留A端好友: {SENDER_NAME}")
            self.contactDetailPageR.click_send_message()
            self.chatPageR.wait_for_chat_page_load()
            self.chatPageR.send_message("测试是否是好友并获取CMD通知")
            notification = self.chatPageR.get_cmd_notification_texts(index=-1)
            check.is_in("发送好友验证", notification, f"❌ S端单向删除B后，B端通讯录中应当依旧保留A端好友: {SENDER_NAME}")
            self.chatPageR.click_back_button()

        with allure.step("4. S端重新发起对 B 的添加好友申请"):
            self.mainPageS.go_to_main_page()
            self._sender_send_friend_request(RECEIVER_PHONE, VERIFY_MESSAGE)

        with allure.step(f"5. B端在新朋友列表中点击 {SENDER_NAME} 的申请项，进入验证详情页并接受"):
            self.mainPageR.go_to_main_page()
            self._go_to_new_friend_page(side='R')
            self.newFriendPageR.wait_for_new_friend_page_load()
            click_ok = self.newFriendPageR.click_apply_item_by_name(SENDER_NAME)
            check.is_true(click_ok, f"❌ R端在新朋友列表中未找到并点击 {SENDER_NAME} 的申请条目")
            self.newFriendPageR.click_accept_in_detail()
            self.contactDetailPageR.click_iv_back()

        with allure.step("6. 交叉验证聊天能力同步恢复"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            self.contactDetailPageS.click_send_message()
            self.chatPageS.wait_for_chat_page_load()
            chat_msg = "验证删除重加后的聊天同步能力_TEST"
            self.chatPageS.send_message(chat_msg)

            self._go_to_contact_detail_from_list(SENDER_NAME, side='R')
            self.contactDetailPageR.click_send_message()
            self.chatPageR.wait_for_chat_page_load()
            received_msg = self.chatPageR.find_message_content(index=-1, side='received')
            check.equal(received_msg, chat_msg, f"❌ 双端重新加回好友后，B端未成功收到A端发送的聊天消息，实际接收: {received_msg}")

        with allure.step("7. S端删除好友进行环境清理"):
            self.mainPageS.go_to_main_page()
            self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            self.contactDetailPageS.delete_contact()


    @allure.story("黑名单隐私")
    @allure.title("拉黑好友消息拒收与移出黑名单聊天恢复-状态：已完成")
    def test_relationship_flow_block_and_unblock(self):
        """测试 A 将 B 加入黑名单 -> B 发送消息提示拒收 -> A 移出黑名单 -> 双端聊天恢复"""
        with allure.step("1. 确认前置：确保双方已经是好友关系"):
            is_friend = self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            if not is_friend:
                logger.info("ℹ️ S端与R端当前不是好友，准备先建立好友关系")
                self.mainPageS.go_to_main_page()
                self._sender_send_friend_request(RECEIVER_PHONE, "加个好友拉黑重试")
                self._go_to_new_friend_page(side='R')
                self.newFriendPageR.wait_for_new_friend_page_load()
                self.newFriendPageR.click_apply_item_by_name(SENDER_NAME)
                self.newFriendPageR.click_accept_in_detail()
                self.contactDetailPageR.click_iv_back()
                self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')

        with allure.step("2. S端（A）在好友详情页中将 R端（B）加入黑名单"):
            block_ok = self.contactDetailPageS.set_contact_blocked(True)
            check.is_true(block_ok, "❌ S端将好友 B 加入黑名单操作失败")

        with allure.step("3. 交叉校验消息拒收：R端 给 S端 发消息被拒收，而 S端 发送正常"):
            self._go_to_contact_detail_from_list(SENDER_NAME, side='R')
            self.contactDetailPageR.click_send_message()
            self.chatPageR.wait_for_chat_page_load()
            self.chatPageR.send_message("你已经被我拉黑了吗？B发给A的")
            be_notificationR = self.chatPageR.get_cmd_notification_texts(index=-1)
            check.is_in("对方已将您加入黑名单", be_notificationR, "❌ 对方被拉黑后发消息，拉黑方未收到拒收提示")

            self.contactDetailPageS.click_send_message()
            self.chatPageS.wait_for_chat_page_load()
            self.chatPageS.send_message("拉黑你之后我发的消息")
            be_notificationS = self.chatPageS.get_cmd_notification_texts(index=-1)
            check.is_in("你已将对方拉入黑名单", be_notificationS, "❌ S端拉黑后发消息，S端未弹出拒收提示")

        with allure.step("4. S端（A）在其好友详情页中将 R端（B）移出黑名单"):
            self.chatPageS.click_more_button()
            self.chatSettingPageS.click_friend_avatar()
            unblock_ok = self.contactDetailPageS.set_contact_blocked(False)
            check.is_true(unblock_ok, "❌ S端将好友 B 移出黑名单操作失败")
            self.chatPageS.back_to_chat_page()

        with allure.step("5. 交叉校验聊天同步恢复"):
            self.chatPageR.send_message("被移除黑名单后测试消息恢复正常_TEST")
            af_notificationR = self.chatPageR.verify_message_sent_status()
            check.is_false(af_notificationR, "❌ 解黑后B端发出的聊天消息A端未成功接收")

            self.chatPageS.send_message("把好友移除黑名单后测试消息恢复正常_TEST")
            af_notificationS = self.chatPageS.verify_message_sent_status()
            check.is_false(af_notificationS, "❌ 解黑后A端发出的聊天消息B端未成功接收")

        with allure.step("6. S端删除好友进行环境清理"):
            self.mainPageS.go_to_main_page()
            self._go_to_contact_detail_from_list(RECEIVER_NAME, side='S')
            self.contactDetailPageS.delete_contact()



