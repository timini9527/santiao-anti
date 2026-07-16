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
from pages.friend.new_friend_page import NewFriendPage
from pages.chat.core.chat_page import ChatPage
from appium.webdriver.common.appiumby import AppiumBy
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER3


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
        self.newFriendPageR = NewFriendPage(driver_receiver)
        self.chatPageS = ChatPage(driver_sender)

        # R 端 (接收方 Receiver)
        self.mainPageR = MainPage(driver_receiver)
        self.homePageR = HomePage(driver_receiver)
        self.addFriendPageR = AddFriendPage(driver_receiver)
        self.newFriendPageR = NewFriendPage(driver_receiver)
        self.contactDetailPageR = ContactDetailPage(driver_receiver)
        self.contactSelectPageR = ContactSelectPage(driver_receiver)
        self.newFriendPageR = NewFriendPage(driver_receiver)
        self.chatPageR = ChatPage(driver_receiver)

        yield
        # 后置清理：确保双端均返回主页，消除脏状态
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





    @allure.story("申请处理")
    @allure.title("双端协作 - 同意好友申请并交叉校验通讯录")
    def test_double_add_friend_agree(self):
        """测试 S 端发起申请，R 端在新朋友列表接受，双方成功建立好友关系并校验通讯录"""
        sender_name = PRIVATE_USER3.name      
        receiver_name = PRIVATE_USER1.name    
        receiver_phone = PRIVATE_USER1.phone
        verify_message = f"你好，我是 {sender_name}，申请加你为好友。"

        with allure.step("1. S端向R端发送好友验证申请"):
            self._sender_send_friend_request(receiver_phone, verify_message)

        with allure.step("2. R端进入‘新的朋友’列表"):
            self.homePageR.click_bottom_expand_button()
            self.homePageR.click_friend()
            self.homePageR.wait_for_friend_page_load()
            self.homePageR.click_new_friend()

        with allure.step(f"3. R端寻找 {sender_name} 的申请项，点击接受"):
            self.newFriendPageR.wait_for_new_friend_page_load()
            click_ok = self.newFriendPageR.click_accept_btn_by_name(sender_name)
            check.is_true(click_ok, f"❌ R端在新朋友列表中未找到 {sender_name} 的接受按钮")

        with allure.step("4. 校验R端申请列表状态变更为‘已添加’或‘已同意’"):
            is_agreed = self.newFriendPageR.verify_apply_status(sender_name, "已添加") or \
                        self.newFriendPageR.verify_apply_status(sender_name, "已同意")
            check.is_true(is_agreed, "❌ R端接受好友申请后，新朋友列表内状态文本未成功流转为已添加/已同意")

        with allure.step("5. 交叉校验通讯录：R端好友列表中应能成功点击进入 S 端详情"):
            self.mainPageR.go_to_main_page()
            self.homePageR.click_bottom_expand_button()
            self.homePageR.click_friend()
            self.homePageR.wait_for_friend_page_load()
            
            click_success = self.contactSelectPageR.click_contact_by_name(sender_name)
            check.is_true(click_success, f"❌ R端好友列表中找不到刚添加的好友: {sender_name}")
            is_detail_loaded = self.contactDetailPageR.wait_for_detail_page_load(timeout=2)
            check.is_true(is_detail_loaded, "❌ R端点击好友条目后，无法成功加载资料详情页")

        with allure.step("6. 交叉校验通讯录：S端好友列表中应能成功点击进入 R 端详情"):
            self.mainPageS.go_to_main_page()
            self.homePageS.click_bottom_expand_button()
            self.homePageS.click_friend()
            self.homePageS.wait_for_friend_page_load()
            
            click_success = self.contactSelectPageS.click_contact_by_name(receiver_name)
            check.is_true(click_success, f"❌ S端好友列表中找不到刚接受好友申请的联系人: {receiver_name}")
            is_detail_loaded = self.contactDetailPageS.wait_for_detail_page_load(timeout=2)
            check.is_true(is_detail_loaded, "❌ S端点击好友条目后，无法成功加载资料详情页")

        with allure.step("7. R端S端解散两人好友关系"):
            self.contactDetailPageS.delete_contact()
            # self.contactDetailPageR.delete_contact()

        # TODO: 有BUG
        # with allure.step("8. 校验R端S端通讯录中已无好友"):
        #     self.mainPageS.go_to_main_page()
        #     self.homePageS.click_bottom_expand_button()
        #     self.homePageS.click_friend()
        #     self.homePageS.wait_for_friend_page_load()
        #     has_receiver = self.contactSelectPageS.click_contact_by_name(receiver_name)
        #     check.is_false(has_receiver, f"❌ S端已删除好友，但其好友列表中仍能找到 R端好友: {receiver_name}")

        # with allure.step("10. 校验R端通讯录中已无S端好友"):
        #     self.mainPageR.go_to_main_page()
        #     self.homePageR.click_bottom_expand_button()
        #     self.homePageR.click_friend()
        #     self.homePageR.wait_for_friend_page_load()
        #     has_sender = self.contactSelectPageR.click_contact_by_name(sender_name)
        #     check.is_false(has_sender, f"❌ R端已删除好友，但其好友列表中仍能找到 S端好友: {sender_name}")



    @allure.story("申请处理")
    @allure.title("双端协作 - 拒绝好友申请并校验好友关系未建立")
    def test_double_add_friend_refuse(self):
        """测试 S 端发起申请，R 端在新朋友列表选择拒绝，双方不建立好友关系且无法在通讯录找到对方"""
        sender_name = PRIVATE_USER1.name      # 发送方昵称
        receiver_phone = PRIVATE_USER4.phone  # 接收方手机号
        receiver_name = PRIVATE_USER4.name    # 接收方昵称
        verify_message = f"你好，我是 {sender_name}，申请加你。"

        with allure.step("1. S端向R端发送好友验证申请"):
            self._sender_send_friend_request(receiver_phone, verify_message)

        with allure.step("2. R端进入‘新的朋友’列表"):
            self.homePageR.click_bottom_expand_button()
            self.homePageR.click_friend()
            self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
            self.homePageR.click_new_friend()

        with allure.step(f"3. R端寻找 {sender_name} 的申请项，点击拒绝"):
            self.newFriendPageR.wait_for_new_friend_page_load()
            # 拒绝按钮定位稍有不同，直接使用底层 xpath
            refuse_btn_locator = (
                AppiumBy.XPATH,
                f'//*[contains(@text, "{sender_name}")]/..//*[contains(@text, "拒绝") or contains(@text, "不同意")]'
            )
            self.newFriendPageR.click(refuse_btn_locator)

        with allure.step("4. 校验R端申请列表状态变更为‘已拒绝’或‘已不同意’"):
            is_refused = self.newFriendPageR.verify_apply_status(sender_name, "已拒绝") or \
                         self.newFriendPageR.verify_apply_status(sender_name, "已不同意")
            check.is_true(is_refused, "❌ R端拒绝好友申请后，新朋友列表内状态文本未成功流转为已拒绝")

        with allure.step("5. 交叉校验通讯录：双方列表中不应出现彼此"):
            # 校验 R 端列表
            self.mainPageR.go_to_main_page()
            self.homePageR.click_friend()
            self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
            has_sender = self.contactSelectPageR.click_contact_by_name(sender_name)
            check.is_false(has_sender, f"❌ 申请已被拒绝，但 R端好友列表中却找到了 S端联系人: {sender_name}")

            # 校验 S 端列表
            self.mainPageS.go_to_main_page()
            self.homePageS.click_friend()
            self.contactSelectPageS.wait_for_contact_and_group_select_page_load()
            has_receiver = self.contactSelectPageS.click_contact_by_name(receiver_name)
            check.is_false(has_receiver, f"❌ 申请已被拒绝，但 S端好友列表中却找到了 R端联系人: {receiver_name}")


    @allure.story("申请处理")
    @allure.title("双端协作 - 同意好友申请并设置备注且验证")
    def test_double_add_friend_with_remark(self):
        """测试 S 端发起申请，R 端进入申请详情并同意且设置备注，验证 R 端通讯录中以备注名显示该好友 (对应 ADD_HANDLE_004 P0)"""
        sender_name = PRIVATE_USER1.name      # 发送方昵称
        receiver_name = PRIVATE_USER4.name    # 接收方昵称
        receiver_phone = PRIVATE_USER4.phone  # 接收方手机号
        verify_message = f"你好，我是 {sender_name}，加个好友。"
        remark_name = f"{sender_name}_测试备注"

        with allure.step("1. S端向R端发送好友验证申请"):
            self._sender_send_friend_request(receiver_phone, verify_message)

        with allure.step("2. R端进入‘新的朋友’列表"):
            self.homePageR.click_bottom_expand_button()
            self.homePageR.click_friend()
            self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
            self.homePageR.click_new_friend()

        with allure.step(f"3. R端点击 {sender_name} 的申请项，进入验证详情页"):
            self.newFriendPageR.wait_for_new_friend_page_load()
            click_ok = self.newFriendPageR.click_apply_item_by_name(sender_name)
            check.is_true(click_ok, f"❌ R端在新朋友列表中未找到并点击 {sender_name} 的申请条目")

        with allure.step("4. R端在详情页中点击接受，并在验证设置页面中填写备注并点击完成"):
            accept_detail_locator = (AppiumBy.XPATH, '//*[@text="接受" or @text="同意"]')
            self.newFriendPageR.click(accept_detail_locator)
            
            # 等待验证设置页面的备注名输入框加载
            self.addFriendPageR.wait_for_send_friend_verify_page(timeout=10)
            self.addFriendPageR.input_remark(remark_name)
            self.addFriendPageR.click_finish()

        with allure.step("5. 校验R端申请列表状态变更为‘已添加’或‘已同意’"):
            is_agreed = self.newFriendPageR.verify_apply_status(sender_name, "已添加") or \
                        self.newFriendPageR.verify_apply_status(sender_name, "已同意")
            check.is_true(is_agreed, "❌ R端设置备注同意好友申请后，新朋友列表内状态文本未成功流转为已添加")

        with allure.step(f"6. 验证 R端通讯录列表中成功以备注名 {remark_name} 显示该好友"):
            self.mainPageR.go_to_main_page()
            self.homePageR.click_friend()
            self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
            
            # 搜索并点击刚才设置 of 备注名，验证能否成功加载详情页
            click_success = self.contactSelectPageR.click_contact_by_name(remark_name)
            check.is_true(click_success, f"❌ R端好友列表中找不到刚设置备注的好友: {remark_name}")
            is_detail_loaded = self.contactDetailPageR.wait_for_detail_page_load(timeout=8)
            check.is_true(is_detail_loaded, "❌ R端点击好友条目后，无法成功加载资料详情页")


    @allure.story("申请处理")
    @allure.title("双端协作 - 删除好友后重新添加并交叉验证聊天消息能力恢复")
    def test_double_add_friend_after_deleted(self):
        """测试 S 端删除好友 R -> 交叉校验确认非好友 -> S 重新申请 -> R 同意 -> 双方聊天功能恢复 (对应 ADD_LIMIT_003 P0 & ADD_SYNC_008 P1)"""
        sender_name = PRIVATE_USER1.name      # 发送方昵称 (S端)
        receiver_name = PRIVATE_USER4.name    # 接收方昵称 (R端)
        receiver_phone = PRIVATE_USER4.phone  # 接收方手机号 (S端搜索)
        verify_message = f"你好，我是 {sender_name}，重新加你为好友。"

        with allure.step("1. 确认前置：确保双方已经是好友关系"):
            # S端查看通讯录是否有R端
            self.homePageS.click_friend()
            self.contactSelectPageS.wait_for_contact_and_group_select_page_load()
            is_friend = self.contactSelectPageS.click_contact_by_name(receiver_name)
            
            if not is_friend:
                logger.info("ℹ️ S端与R端当前不是好友，准备先建立好友关系")
                self.mainPageS.go_to_main_page()
                # 发送申请
                self._sender_send_friend_request(receiver_phone, "加个好友删除重试")
                # B端接受
                self.homePageR.click_bottom_expand_button()
                self.homePageR.click_friend()
                self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
                self.homePageR.click_new_friend()
                self.newFriendPageR.wait_for_new_friend_page_load()
                self.newFriendPageR.click_accept_btn_by_name(sender_name)
                # 重新进入S端通讯录详情页
                self.mainPageS.go_to_main_page()
                self.homePageS.click_friend()
                self.contactSelectPageS.wait_for_contact_and_group_select_page_load()
                self.contactSelectPageS.click_contact_by_name(receiver_name)

            # 等待资料页加载
            self.contactDetailPageS.wait_for_detail_page_load(timeout=8)

        with allure.step("2. S端在其个人详情页中删除好友 B"):
            delete_ok = self.contactDetailPageS.delete_contact()
            check.is_true(delete_ok, "❌ S端删除好友 B 失败")

        with allure.step("3. 校验双方均不再是好友（非好友关系校验）"):
            # 3.1 校验 S 端通讯录中无法找到 R 端
            self.mainPageS.go_to_main_page()
            self.homePageS.click_friend()
            self.contactSelectPageS.wait_for_contact_and_group_select_page_load()
            has_receiver = self.contactSelectPageS.click_contact_by_name(receiver_name)
            check.is_false(has_receiver, f"❌ S端已删除 B，但 S端通讯录里仍然存在好友: {receiver_name}")

            # 3.2 校验 R 端通讯录中无法找到 S 端
            self.mainPageR.go_to_main_page()
            self.homePageR.click_friend()
            self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
            has_sender = self.contactSelectPageR.click_contact_by_name(sender_name)
            check.is_false(has_sender, f"❌ S端已删除 B，但 R端通讯录里仍能找到 A端好友: {sender_name}")

        with allure.step("4. S端重新发起对 B 的添加好友申请"):
            self.mainPageS.go_to_main_page()
            self._sender_send_friend_request(receiver_phone, verify_message)

        with allure.step("5. B端接受该申请建立好友关系"):
            self.homePageR.click_bottom_expand_button()
            self.homePageR.click_friend()
            self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
            self.homePageR.click_new_friend()
            self.newFriendPageR.wait_for_new_friend_page_load()
            self.newFriendPageR.click_accept_btn_by_name(sender_name)

        with allure.step("6. 交叉验证聊天能力同步恢复 (ADD_SYNC_008)"):
            # 6.1 S端通过搜索进入与R端的聊天窗口，发送消息
            self.mainPageS.go_to_main_page()
            self.homePageS.click_friend()
            self.contactSelectPageS.wait_for_contact_and_group_select_page_load()
            self.contactSelectPageS.click_contact_by_name(receiver_name)
            self.contactDetailPageS.wait_for_detail_page_load(timeout=8)
            self.contactDetailPageS.click_send_message()
            
            self.chatPageS.wait_for_chat_page_load(timeout=10)
            chat_msg = "验证删除重加后的聊天同步能力_TEST"
            self.chatPageS.send_message(chat_msg)
            logger.info("⚙️ S端成功发送了测试聊天消息")

            # 6.2 R端返回主页，搜索进入与S端的聊天窗口，验证是否收到消息
            self.mainPageR.go_to_main_page()
            self.homePageR.click_friend()
            self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
            self.contactSelectPageR.click_contact_by_name(sender_name)
            self.contactDetailPageR.wait_for_detail_page_load(timeout=8)
            self.contactDetailPageR.click_send_message()
            
            self.chatPageR.wait_for_chat_page_load(timeout=10)
            received_msg = self.chatPageR.find_message_content(index=-1, side='received')
            check.equal(received_msg, chat_msg, f"❌ 双端重新加回好友后，B端未成功收到A端发送的聊天消息，实际接收: {received_msg}")
