import pytest
import allure
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY, GROUP_STRATEGY2

@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群管理")
class TestGroupSetting:
    """群聊设置/群管理相关测试用例"""

    _has_entered_setting_page = False

    @pytest.fixture(autouse=True)
    def setup_class(self, request, driver_sender):
        """初始化页面对象并控制 Teardown 时机"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupManagerPage = GroupManagerPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        
        yield
        
        current_test_name = request.node.name
        should_go_home = False
        
        # 针对单次运行且执行完毕后停留在其他子页面、必须退回首页的用例
        single_test_need_home = [
            "test_group_show_member_nickname_toggle",
            "test_modify_my_group_nickname",
            "test_delete_group_cancel",
            "test_clear_group_chat_records"
        ]
        
        if any(name in current_test_name for name in single_test_need_home):
            should_go_home = True
        elif "test_group_remark_validation" in current_test_name and "超长20字限制截断" in current_test_name:
            should_go_home = True
        elif "test_group_name_validation" in current_test_name and "群名称包含敏感词" in current_test_name:
            should_go_home = True
            
        if should_go_home:
            logger.info(f"🧹 [Teardown] 用例满足退回首页条件，执行 go_to_main_page: {current_test_name}")
            self.mainPage.go_to_main_page()
        else:
            logger.info(f"⏭️ [Teardown] 用例无需/已自行完成退回首页，略过 Teardown 回收: {current_test_name}")

    def _create_temp_group(self, friend_list):
        """内部辅助方法：快速创建一个用于测试的临时群聊"""
        with allure.step("-> [前置准备] 在首页发起群聊创建临时群"):
            self.homePage.click_add_button()
            self.homePage.click_start_group_chat()
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()
            
            self.chatPage.wait_banner_message_disappear()
            self.chatPage.wait_for_chat_page_load()

    def _create_group_and_go_to_dismiss(self, friend_list):
        """进入已建临时群并打开解散群聊确认界面"""
        self._create_temp_group(friend_list)
        with allure.step("1. 在群聊聊天页面点击右上角'...' -> 群设置"):
            self.chatPage.click_more_button()
        with allure.step("2. 进入群详情页，进入群管理并点击解散群聊"):
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.click_dismiss_group()
        
    
    # 
    def _enter_group_setting_page(self, group_name):
        """进入群设置页面 (使用内存 Flag 限制全局仅进入一次)"""
        if getattr(self.__class__, "_has_entered_setting_page", False):
            logger.info("⚡ [Setup] 当前已在群聊设置页，跳过重复进入流程")
            return
            
        with allure.step("1. 进入群设置页面"):
            self.chatListPage.enter_chat(group_name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.__class__._has_entered_setting_page = True



    @allure.story("群聊详情设置")
    @allure.title("切换显示群成员昵称开关并校验状态-状态：已完成")
    def test_group_show_member_nickname_toggle(self):
        """测试显示群成员昵称开关"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._create_temp_group(friend_list)
        
        with allure.step("1. 在群聊页面点击右上角进入群详情"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            
        with allure.step("2. 获取当前显示群成员昵称状态"):
            init_state = self.groupSettingPage.get_show_member_name_switch_state()
            
        with allure.step("3. 点击显示群成员昵称进行切换"):
            self.groupSettingPage.click_chat_show_member_name()
            new_state = self.groupSettingPage.get_show_member_name_switch_state()
            check.not_equal(init_state, new_state, "❌ 显示群成员昵称开关切换失败")
            
        with allure.step("4. 再次点击恢复初始状态"):
            self.groupSettingPage.click_chat_show_member_name()
            final_state = self.groupSettingPage.get_show_member_name_switch_state()
            check.equal(init_state, final_state, "❌ 显示群成员昵称开关恢复初始状态失败")


    @allure.story("群聊详情设置")
    @allure.title("修改‘我在本群昵称’并校验修改成功-状态：已完成")
    def test_modify_my_group_nickname(self):
        """测试修改我在本群的昵称"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._create_temp_group(friend_list)
        
        with allure.step("1. 在群聊页面点击右上角进入群详情"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            
        with allure.step("2. 获取修改前的群内昵称值"):
            old_nickname = self.groupSettingPage.get_my_group_nickname()
            
        with allure.step("3. 输入新昵称并确认保存"):
            target_nickname = "自动化测试群昵称"
            self.groupSettingPage.change_my_group_nickname(target_nickname)
            
        with allure.step("4. 校验群内昵称是否更新成功"):
            new_nickname = self.groupSettingPage.get_my_group_nickname()
            check.equal(new_nickname, target_nickname, "❌ 我在本群昵称修改值不一致")
            
        with allure.step("5. 恢复初始群内昵称值"):
            # 如果原先是空，则输入空字符
            restore_nickname = old_nickname if old_nickname else ""
            self.groupSettingPage.change_my_group_nickname(restore_nickname)

    
    @allure.story("解散群聊")
    @allure.title("通过群聊聊天页面解散群聊 - 正常解散流程-状态：已完成")
    def test_delete_group_success(self):
        allure.dynamic.description(f"通过群聊聊天页面解散群聊")
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        
        self._create_group_and_go_to_dismiss(friend_list)

        with allure.step("3. 确认弹窗"):
            self.groupSettingPage.click_confirm_button()
            toast = self.groupSettingPage.get_toast()
            check.is_in("群不存在", toast, "❌ 解散群聊后未弹出解散成功/群不存在提示")
            
            self.groupSettingPage.click_iv_back_button()
            self.chatPage.click_back_button()
            title = self.homePage.get_top_middle_title()
            check.is_in("三条", title, "❌ 解散群聊后未能返回消息首页")
        
        with allure.step("4. 验证群聊是否已解散"):
            # TODO: 后续可以加入搜索验证或消息列表检查，确保群已被移除
            pass

    @allure.story("解散群聊")
    @allure.title("通过群聊聊天页面解散群聊 - 取消解散流程-状态：已完成")
    def test_delete_group_cancel(self):
        allure.dynamic.description(f"通过群聊聊天页面解散群聊")
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        
        self._create_group_and_go_to_dismiss(friend_list)

        with allure.step("3. 取消确认"):
            self.groupSettingPage.click_cancel_button()
            
            # 返回群管理 -> 返回群设置 -> 返回聊天页面
            self.groupSettingPage.click_iv_back_button()
            self.groupSettingPage.click_iv_back_button()
            
            title = self.chatPage.get_top_name()
            group_number = self.groupCreatePage.is_chat_group(title)
            check.is_true(group_number is not False, f"❌ 取消解散后未能正确返回群聊页面")


    @allure.story("群聊设置 - 清空聊天记录")
    @allure.title("清空聊天记录-状态：已完成")
    @pytest.mark.parametrize("chat_strategy", [GROUP_STRATEGY2], ids=["群聊-清空聊天记录"])
    def test_clear_group_chat_records(self, chat_strategy):
        """点击清空聊天记录"""
        allure.dynamic.title(f"{chat_strategy.name} - 清空聊天记录")
        
        with allure.step("1、进入特定群的群聊会话"):
            self.chatListPage.enter_chat(chat_strategy.name)
            self.chatListPage.send_message("测试清空聊天记录功能")

        with allure.step("1、获取聊天页面消息数量"):
            msg_count = self.chatListPage.get_total_message_count()
            check.is_true(bool(msg_count), "❌ 获取聊天页面消息数量失败")
        
        with allure.step("2、进入设置页面"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
                    
        with allure.step("3、清空聊天记录"):
            self.groupSettingPage.click_clear_group_chat_message()
            self.groupSettingPage.click_confirm_button()
            self.groupSettingPage.click_iv_back_button()
        
        with allure.step("4、获取聊天页面消息数量"):
            new_msg_count = self.chatListPage.get_total_message_count()
            check.equal(new_msg_count, 0, f"❌ 清空聊天记录后，消息数量应为 0，实际为 {new_msg_count}")


    @allure.story("群备注功能")
    @allure.title("群备注修改校验 - {test_id}-状态：已完成")
    @pytest.mark.parametrize("test_id, input_content, action, expect_truncated, last_case", [
        ("正常修改并保存", "测试群备注1", "confirm", False, False),
        ("敏感词", "习近平", "confirm", False, False),
        ("修改并取消", "企图修改备注但取消", "cancel", False, False),
        ("超长20字限制截断", "一二三四五六七八九十一二三四五六七八九十加", "confirm", True, True),
    ], ids=["正常修改并保存", "敏感词", "修改并取消", "超长20字限制截断"])
    @pytest.mark.parametrize("chat_strategy", [GROUP_STRATEGY], ids=["群聊-群备注功能"])
    def test_group_remark_validation(self, test_id, input_content, action, expect_truncated, last_case, chat_strategy):
        """测试不同场景下的群备注修改逻辑（保存、取消、超长限制）"""
        
        with allure.step("1. 进入群设置页面"):
            self._enter_group_setting_page(chat_strategy.name)
            
        with allure.step("2. 获取修改前的群备注"):
            old_remark = self.groupSettingPage.get_group_remark()
            
        with allure.step(f"3. 点击群备注，输入待测内容: '{input_content}'并执行【{action}】"):
            self.groupSettingPage.click_group_remark()
            self.groupSettingPage.wait_for_remark_dialog_load(nva_text="群备注")
            self.groupSettingPage.input_remark_content(input_content)
            if action == "confirm":
                self.groupSettingPage.click_remark_confirm()
            else:
                self.groupSettingPage.click_remark_cancel()
            
        with allure.step("4. 校验修改后的群备注结果"):
            if test_id == "敏感词":
                toast = self.groupSettingPage.get_toast()
                check.is_in("群备注名不合法，请换个群备注名", toast, "❌ 群备注包含敏感词后未弹出提示")
                new_remark = self.groupSettingPage.get_group_remark()
                check.equal(new_remark, old_remark, f"❌ 敏感词被拦截后，群备注发生意外变更")
            else:
                new_remark = self.groupSettingPage.get_group_remark()
                if action == "confirm":
                    expected_remark = input_content[:20] if expect_truncated else input_content
                    check.equal(new_remark, expected_remark, f"❌ 群备注确认修改后保存内容不一致")
                else:
                    check.equal(new_remark, old_remark, f"❌ 取消修改后群备注被变更了")

        # TODO：BUG待修复，群聊不展示群备注
        # with allure.step("5. 校验群名称是否修改"):
        #     self.groupSettingPage.click_iv_back_button()
        #     title = self.chatPage.get_top_name()
        #     check.is_in(expected_remark, title, f"❌ 群名称校验失败")
 
        with allure.step("6. 恢复初始群备注值"):
            if last_case:
                self.groupSettingPage.click_group_remark()
                self.groupSettingPage.wait_for_remark_dialog_load(nva_text="群备注")
                self.groupSettingPage.input_remark_content("")
                self.groupSettingPage.click_remark_confirm()


    @allure.story("群名称功能")
    @allure.title("群聊名称修改校验-状态：已完成")
    @pytest.mark.parametrize(
        "scenario, input_name, expected_toast, expected_result, should_change", 
        [
            ("empty", "", "群名称不能为空", "", False),
            ("success", "新群聊名称", "", "新群聊名称", True),
            ("limit_10", "一二三四五六七八九十", "", "一二三四五六七八九十", True),
            ("limit_over", "一二三四五六七八九十一二", "", "一二三四五六七八九十", True),
            ("sensitive", "习近平", "操作不成功，请换个名称！", "", False)
        ],
        ids=["群名称设置为空", "群名称正常修改", "群名称上限10个字", "群名称超限10字截断", "群名称包含敏感词"]
    )
    @pytest.mark.parametrize("chat_strategy", [GROUP_STRATEGY], ids=["群聊-群名称功能"])
    def test_group_name_validation(self, scenario, input_name, expected_toast, expected_result, should_change, chat_strategy):
        """验证群聊名称的修改规则，包含空输入、字数上限10个字截断、敏感词拦截等边界与异常场景"""

        self._enter_group_setting_page(chat_strategy.name)

        with allure.step("2. 获取修改前的群名称"):
            old_group_name = self.groupSettingPage.get_nva_group_name()
        
        with allure.step(f"3. 触发修改群名称，输入: '{input_name}'"):
            self.groupSettingPage.click_group_name()
            self.groupSettingPage.wait_for_remark_dialog_load(nva_text="群名称")
            self.groupSettingPage.input_remark_content(input_name)
            self.groupSettingPage.click_remark_confirm()

        with allure.step("4. 校验修改后的结果与提示"):
            if expected_toast:
                toast_text = self.groupSettingPage.get_toast()
                check.is_in(expected_toast, toast_text, f"❌ 未能监测到预期的 Toast 提示: '{expected_toast}', 实际: '{toast_text}'")
            
            if not should_change:
                current_name = self.groupSettingPage.get_nva_group_name()
                check.equal(old_group_name, current_name, f"❌ 异常输入后，群聊名称意外发生了改变")
            else:
                current_name = self.groupSettingPage.get_nva_group_name()
                check.equal(expected_result, current_name, f"❌ 修改后的群聊名称与预期不符。预期: '{expected_result}', 实际: '{current_name}'")

        with allure.step("5. 恢复初始群名称值"):
            if should_change and old_group_name != expected_result:
                self.groupSettingPage.click_group_name()
                self.groupSettingPage.wait_for_remark_dialog_load(nva_text="群名称")
                self.groupSettingPage.input_remark_content(old_group_name)
                self.groupSettingPage.click_remark_confirm()

