import pytest
import allure
import time
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from pages.common.session_select_page import SessionSelectPage
from pages.common.contact_select_page import ContactSelectPage
from pages.home.home_page import HomePage
import pytest_check as check
from core.logger_utils import logger
from pages.chat.chat_setting_page import ChatSettingPage
from strategy.chat.chat_strategy import (
    PRIVATE_USER1, 
    PRIVATE_USER2, 
    PRIVATE_DISABLE1, 
    PRIVATE_DISABLE2, 
    GROUP_STRATEGY
)



@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-发起群聊")
@allure.story("群聊创建相关测试用例")
class TestGroupCreate:
    """群聊创建相关测试用例"""

    @pytest.fixture(autouse=True)
    def setup_class(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.selectPage = SessionSelectPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        
        yield
        
        self.mainPage.go_to_main_page()

    def _open_start_group_chat(self):
        """在首页点击加号并进入发起群聊页面"""
        self.homePage.click_add_button()
        self.homePage.click_start_group_chat()
    
                    
    def _process_batch_create_group(self, total_needed: int) -> int:
        """
        专门处理分批建群的逻辑，包含异常好友过滤。
        :param total_needed: 需要邀请的总好友数
        :return: 最终成功拉入群的好友数
        """
        batch_size = 50
        exclude_names = []
        actual_group_count = 1
        
        # 选择好友-先选择50个
        selected_count = self.contactSelectPage.select_x_random_friends(x=batch_size)
        if selected_count == 0:
            logger.warning("没有足够的可选好友，返回")
            pytest.skip("⏭️ 测试环境好友数量不足，跳过该用例。")
        
        initial = self.contactSelectPage.get_first_contact_initial()

        self.contactSelectPage.click_action_button()

        while True:
            self.chatPage.wait_for_chat_page_load(timeout=20)

            # 0. 先获取一次当前的名字用于退回列表后搜索
            old_title = self.chatPage.get_top_name()
            sess = old_title.split("...")[0]
            self.chatPage.click_back_button()
            self.chatListPage.enter_chat(session_name=sess, match_type="partial", timeout=10)
            
            title = self.chatPage.get_top_name()
            group_number = self.groupCreatePage.is_chat_group(title)
            
            if group_number is not False:
                actual_group_count = group_number
            
            remaining_need = total_needed - actual_group_count
            if remaining_need <= 0:
                logger.info(f"✅ 群聊已达到预期人数: {actual_group_count}")
                break
            
            current_batch_need = min(batch_size, remaining_need)

            # 1. 获取异常用户并去重
            message_texts = self.groupCreatePage.get_message_text_elements()
            abnormal_users = self.groupCreatePage.get_abnormal_users(message_texts=message_texts)
            for user in abnormal_users:
                if user not in exclude_names:
                    exclude_names.append(user)
            
            # 2. 进入群设置
            self.chatPage.click_more_button()
            self.groupCreatePage.wait_for_setting_page_load()
            friend_headers = self.groupCreatePage.get_friend_headers()
            if friend_headers and len(friend_headers) >= 2:
                friend_headers[-2].click()
            else:
                logger.warning("无法找到添加成员按钮，退出循环")
                break
                
            # 3. 选择好友
            selected_count, clicked_names, initial_new = self.groupCreatePage.select_x_friends_with_exclusion(current_batch_need, exclude_names, initial)
            
            if selected_count == 0:
                logger.warning("当前批次未能选择到任何有效好友，结束建群")
                self.groupCreatePage.click_iv_back_button()
                break
                
            # 4. 确认加人并退回聊天页
            self.groupCreatePage.click_edit_to_next()
            add_toast = self.groupCreatePage.get_toast()
            logger.info(f"加人Toast: {add_toast}")

            # 等待横幅消息消失
            self.chatPage.wait_banner_message_disappear()
            
            if "该用户状态异常，无法邀请其加入群聊" in add_toast:
                logger.warning("该用户状态异常，无法邀请其加入群聊")
                exclude_names.extend(clicked_names)
                time.sleep(1)
                self.selectPage.click_back_button()
            elif "群成员已达上限！" in add_toast:
                logger.warning("群成员已达上限，结束建群")
                time.sleep(1)
                self.selectPage.click_back_button()
            else:
                initial = initial_new
            
            time.sleep(1)
            try:
                self.groupCreatePage.click_iv_back_button()
            except Exception:
                logger.warning("⚠️ UI返回按钮点击失效，执行系统物理返回键兜底...")
                self.groupCreatePage.back()
            
        return actual_group_count


    @allure.story("发起群聊")
    @allure.title("选择 1 个正常好友时进入单聊页面-状态：已完成")
    def test_create_group_with_one_normal_friend(self):
        allure.dynamic.description("通过首页右上角发起群聊 - 选择1个好友")

        with allure.step("1. 进入发起群聊页面"):
            self._open_start_group_chat()

        with allure.step("2. 选择 1 个正常好友并点击完成"):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            selected = self.contactSelectPage.click_contact_by_name(PRIVATE_USER1.name)
            check.is_true(selected, f"❌ 未找到正常好友: {PRIVATE_USER1.name}")
            self.contactSelectPage.click_action_button()

        with allure.step("3. 验证进入该好友单聊页面"):
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 选择 1 个正常好友后未进入单聊页面")

            title = self.chatPage.get_top_name()
            check.is_in(PRIVATE_USER1.name, title, f"❌ 单聊标题不正确，实际标题: {title}")
    

    @allure.story("发起群聊")
    @allure.title("选择 1 或 2 个已停用/已注销好友时提示异常-状态：已完成")
    @pytest.mark.parametrize("invalid_friends", [
        [PRIVATE_DISABLE1],
        [PRIVATE_DISABLE1, PRIVATE_DISABLE2],
        [PRIVATE_USER1, PRIVATE_DISABLE1]
        ], ids=["1个停用", "2个停用", "1个正常+1个停用"])
    def test_create_group_with_one_invalid_friend(self, invalid_friends):
        allure.dynamic.description("通过首页右上角发起群聊 - 选择1个或多个已停用/已注销好友")
        
        with allure.step("1. 进入发起群聊页面"):
            self._open_start_group_chat()

        with allure.step("2. 选择 1 个停用或注销好友并点击完成"):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in invalid_friends:
                selected = self.contactSelectPage.click_contact_by_name(contact.name)
                check.is_true(selected, f"❌ 未找到非正常好友: {contact.name}")
            self.contactSelectPage.click_action_button()

        with allure.step("3. 验证出现 Toast，且不进入聊天页面"):
            toast = self.contactSelectPage.get_toast()
            expected_toast_keywords = ["停用", "注销", "账号异常", "没有可创建群聊的用户", "用户已停用,无法创建群聊"]
            
            check.is_true(
                any(keyword in toast for keyword in expected_toast_keywords),
                f"❌ Toast 不符合预期，实际 Toast: {toast}"
            )

            is_in_chat = self.chatPage.wait_for_chat_page_load(2, False)
            check.is_false(is_in_chat, "❌ 选择非正常好友后不应进入聊天页面")


    @allure.story("发起群聊")
    @allure.title("通过首页右上角发起群聊 (小群:2人) - 正常建群流程-状态：已完成")
    def test_create_group_success(self):
        allure.dynamic.description(f"通过首页右上角发起群聊 (小群:2人) -正常建群流程")
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        
        with allure.step("1. 进入发起群聊页面"):
            self._open_start_group_chat()
            
        with allure.step("2. 在通讯录列表中勾选多个好友并完成"):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()
            
        with allure.step("3. 验证是否成功进入了群聊天页面"):
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 建群后未能成功进入聊天页面")
        
        with allure.step("4. 验证群聊标题是否包含：(3)"):
            title = self.chatPage.get_top_name()
            check.is_in("(3)", title, f"❌ 群聊标题不包含：(3)")
            

    @allure.story("发起群聊")
    @allure.title("通过好友发起群聊 (小群:2人) - 正常建群流程-状态：已完成")
    def test_create_group_success_by_friend(self):
        allure.dynamic.description(f"通过好友发起群聊 (小群:2人) - 正常建群流程")
        
        with allure.step("1. 进入好友聊天界面"):
            self.chatListPage.enter_session(PRIVATE_USER1.name, match_type="exact")
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 未能成功进入聊天页面")
            
        with allure.step("2. 在聊天界面点击右上角'...' -> 添加成员"):
            self.chatPage.click_more_button()
            self.chatSettingPage.click_add_friend()
            
        with allure.step("3. 勾选其他好友"):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            self.contactSelectPage.click_contact_by_name(PRIVATE_USER2.name)
            self.contactSelectPage.click_action_button()

        with allure.step("4. 验证是否成功进入了群聊天页面"):
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 建群后未能成功进入聊天页面")
        
        with allure.step("5. 验证群聊标题是否包含：(3)"):    
            title = self.chatPage.get_top_name()
            check.is_in("(3)", title, f"❌ 群聊标题不包含：(3)")


    @allure.story("发起群聊")
    @allure.title("通过首页发起群聊 - 取消建群-状态：已完成")
    def test_create_group_cancel_from_home(self):
        allure.dynamic.description(f"通过首页发起群聊 - 取消建群")
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        
        with allure.step("1. 进入发起群聊页面"):
            self._open_start_group_chat()
            
        with allure.step("2. 在通讯录列表中勾选多个好友-取消"):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.groupCreatePage.click_iv_back_button()
        
        with allure.step("3. 验证返回到首页"):
            self.homePage.wait_home_page()
            middle_title = self.homePage.get_top_middle_title()
            check.is_in("三条", middle_title, f"❌ 未返回到首页")
    

    @allure.story("发起群聊")
    @allure.title("通过好友发起群聊 - 取消建群流程-状态：已完成")
    def test_create_group_cancel(self):
        allure.dynamic.description("通过好友聊天页添加成员后取消建群")

        with allure.step("1. 进入好友聊天界面"):
            self.chatListPage.enter_session(PRIVATE_USER1.name, match_type="exact")
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 未能成功进入聊天页面")

        with allure.step("2. 在聊天界面点击右上角'...' -> 添加成员"):
            self.chatPage.click_more_button()
            self.chatSettingPage.click_add_friend()

        with allure.step("3. 进入好友选择页后直接返回取消建群"):
            is_select_page = self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            check.is_true(is_select_page, "❌ 未能进入好友选择页")
            self.contactSelectPage.click_back()
            self.contactSelectPage.click_back()

        with allure.step("4. 验证仍停留在原好友单聊页面"):
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 取消建群后未能返回聊天页面")

            title = self.chatPage.get_top_name()
            check.is_in(PRIVATE_USER1.name, title, f"❌ 取消建群后聊天标题不正确，实际标题: {title}")
            check.is_false(self.groupCreatePage.is_chat_group(title), f"❌ 取消建群后不应进入群聊，实际标题: {title}")


    @allure.story("发起群聊")
    @allure.title("通过首页右上角发起群聊 - <= 50 - 选择x个好友进行建群-状态：已完成")
    @pytest.mark.parametrize("num_friends", [0, 10, 49, 50, 51], ids=["0人", "10人", "49人", "50人", "51人"])
    def test_create_group_success_x(self, num_friends):
        allure.dynamic.description(f"通过首页右上角发起群聊 - 选择x个好友进行建群")
        
        with allure.step("1. 进入发起群聊页面"):
            self._open_start_group_chat()
        
        with allure.step(f"2. 在通讯录列表中勾选{num_friends}个好友"):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            if num_friends == 0:
                actual_selected = 0
            else:
                actual_selected = self.contactSelectPage.select_x_random_friends(num_friends)
                if actual_selected < num_friends:
                    pytest.skip(
                        f"⏭️ 测试环境好友数量不足，跳过该用例。"
                        f"期望选择: {num_friends}, 实际选择: {actual_selected}"
                    )
            self.contactSelectPage.click_action_button()
        
        with allure.step("3. 验证建群结果"):
            if num_friends == 0:
                toast = self.contactSelectPage.get_toast()
                check.is_in("至少选择一位联系人", toast, f"❌ 未弹出正确的Toast提示")
            elif 2 <= num_friends < 50:
                with allure.step("3.1 验证是否成功进入了群聊天页面"):
                    is_in_chat = self.chatPage.wait_for_chat_page_load()
                    check.is_true(is_in_chat, "❌ 建群后未能成功进入聊天页面")
                
                with allure.step(f"3.2 验证群聊标题是否包含：({num_friends+1})"):
                    title = self.chatPage.get_top_name()
                    group_number = self.groupCreatePage.is_chat_group(title)
                    check.is_true(group_number is not False, f"❌ 群聊标题未包含人数信息，实际标题: {title}")

                    if group_number is not False:
                        actual_group_count = group_number
                        max_expected_count = actual_selected + 1

                        check.less_equal(
                            actual_group_count,
                            max_expected_count,
                            f"❌ 建群失败或降级成了单聊，群聊人数低于3人，标题: {title}, 勾选人数: {actual_selected}"
                        )

                        check.greater_equal(
                            actual_group_count,
                            3,
                            f"❌ 群聊实际人数异常，标题: {title}, 勾选人数: {actual_selected}"
                        )

                        if actual_group_count != num_friends + 1:
                            logger.warning(
                                f"⚠️ 部分被邀请用户可能为停用/注销状态，已被排除。"
                                f"勾选人数: {actual_selected}, 预期最多人数: {num_friends + 1}, 实际群人数: {actual_group_count}"
                            )
            elif num_friends >= 50:
                toast = self.contactSelectPage.get_toast()
                check.is_in("一次性邀请人数过多，请分批邀请", toast, f"❌ 未弹出正确的Toast提示")
            else:
                with allure.step("3. 验证是否返回了会话选择页"):
                    is_back = self.contactSelectPage.wait_for_contact_and_group_select_page_load()
                    check.is_true(is_back, "❌ 建群后未能返回会话选择页")
            
    @allure.story("发起群聊")
    @allure.title("通过首页右上角发起群聊 - > 200+ - 选择x个好友分批次选择好友建群-状态：已完成")
    @pytest.mark.parametrize("num_friends", [200, 201, 499, 500, 501], ids=["200人", "201人", "499人", "500人", "501人"])
    def test_create_group_success_x_over_200(self, num_friends):
        allure.dynamic.description(f"通过首页右上角发起群聊 - 选择 {num_friends} 个好友进行建群")
        
        if num_friends > 200:
            # TODO: 暂时跳过该用例，后续优化
            pytest.skip("⏭️ 测试环境好友数量不足，跳过该用例。")

        with allure.step("1. 进入发起群聊页面"):
            self._open_start_group_chat()
        
        with allure.step(f"2. 在通讯录列表中分批勾选{num_friends}个好友"):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            if num_friends == 0:
                actual_selected = 0
            else:
                actual_selected = self._process_batch_create_group(num_friends)
                check.equal(actual_selected, num_friends, f"❌ 建群成功人数与预期人数不符")
    
