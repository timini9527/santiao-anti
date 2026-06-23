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

    @pytest.fixture(autouse=True)
    def setup_class(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupManagerPage = GroupManagerPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        
        yield
        
        # 测试结束后返回首页，保证下一个用例有个干净的前置状态
        self.mainPage.go_to_main_page()

    def _create_temp_group(self, friend_list):
        """内部辅助方法：快速创建一个用于测试的临时群聊"""
        with allure.step("-> [前置准备] 在首页发起群聊创建临时群"):
            self.homePage.click_add_button()
            self.homePage.click_start_group_chat()
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()
            
            # 等待进群横幅消失，保证页面稳定
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

    @allure.story("群聊详情设置")
    @allure.title("切换显示群成员昵称开关并校验状态")
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
    @allure.title("修改‘我在本群昵称’并校验修改成功")
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
    @allure.title("通过群聊聊天页面解散群聊 - 正常解散流程")
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
    @allure.title("通过群聊聊天页面解散群聊 - 取消解散流程")
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
    @allure.title("群备注修改校验 - {test_id}")
    @pytest.mark.parametrize("test_id, input_content, action, expect_truncated", [
        ("正常修改并保存", "测试群备注1", "confirm", False),
        ("修改并取消", "企图修改备注但取消", "cancel", False),
        ("超长20字限制截断", "一二三四五六七八九十一二三四五六七八九十加", "confirm", True),
    ], ids=["正常修改并保存", "修改并取消", "超长20字限制截断"])
    @pytest.mark.parametrize("chat_strategy", [GROUP_STRATEGY], ids=["群聊-群备注功能"])
    def test_group_remark_validation(self, test_id, input_content, action, expect_truncated, chat_strategy):
        """测试不同场景下的群备注修改逻辑（保存、取消、超长限制）"""
        
        with allure.step("1. 进入群设置页面"):
            self.chatListPage.enter_chat(chat_strategy.name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            
        with allure.step("2. 获取修改前的群备注"):
            old_remark = self.groupSettingPage.get_group_remark()
            
        with allure.step(f"3. 点击群备注，输入待测内容: '{input_content}'并执行【{action}】"):
            self.groupSettingPage.click_group_remark()
            self.groupSettingPage.wait_for_remark_dialog_load()
            
            self.groupSettingPage.input_remark_content(input_content)
            if action == "confirm":
                self.groupSettingPage.click_remark_confirm()
            else:
                self.groupSettingPage.click_remark_cancel()
            
        with allure.step("4. 校验修改后的群备注结果"):
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
            self.groupSettingPage.click_group_remark()
            self.groupSettingPage.wait_for_remark_dialog_load()
            self.groupSettingPage.input_remark_content("")
            self.groupSettingPage.click_remark_confirm()

    @allure.story("群聊详情设置")
    @allure.title("切换消息免打扰开关并校验状态")
    def test_group_dnd_toggle(self):
        """测试消息免打扰开关"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._create_temp_group(friend_list)
        
        with allure.step("1. 在群聊页面点击右上角进入群详情"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            
        with allure.step("2. 获取当前消息免打扰状态"):
            init_state = self.groupSettingPage.get_dnd_switch_state()
            
        with allure.step("3. 点击消息免打扰进行切换"):
            self.groupSettingPage.click_chat_dnd()
            new_state = self.groupSettingPage.get_dnd_switch_state()
            check.not_equal(init_state, new_state, "❌ 消息免打扰开关切换失败")
            
        with allure.step("4. 再次点击恢复初始状态"):
            self.groupSettingPage.click_chat_dnd()
            final_state = self.groupSettingPage.get_dnd_switch_state()
            check.equal(init_state, final_state, "❌ 消息免打扰开关恢复初始状态失败")

    @allure.story("群聊详情设置")
    @allure.title("切换置顶聊天开关并校验状态")
    def test_group_settop_toggle(self):
        """测试置顶聊天开关"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._create_temp_group(friend_list)
        
        with allure.step("1. 在群聊页面点击右上角进入群详情"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            
        with allure.step("2. 获取当前置顶聊天状态"):
            init_state = self.groupSettingPage.get_settop_switch_state()
            
        with allure.step("3. 点击置顶聊天进行切换"):
            self.groupSettingPage.click_chat_settop()
            new_state = self.groupSettingPage.get_settop_switch_state()
            check.not_equal(init_state, new_state, "❌ 置顶聊天开关切换失败")
            
        with allure.step("4. 再次点击恢复初始状态"):
            self.groupSettingPage.click_chat_settop()
            final_state = self.groupSettingPage.get_settop_switch_state()
            check.equal(init_state, final_state, "❌ 置顶聊天开关恢复初始状态失败")

    @allure.story("群聊详情设置")
    @allure.title("切换聊天密码开关并校验状态")
    def test_group_pwd_toggle(self):
        """测试聊天密码开关"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._create_temp_group(friend_list)
        
        with allure.step("1. 在群聊页面点击右上角进入群详情"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            
        with allure.step("2. 获取当前聊天密码状态"):
            init_state = self.groupSettingPage.get_pwd_switch_state()
            
        with allure.step("3. 点击聊天密码进行切换"):
            self.groupSettingPage.click_chat_pwd()
            new_state = self.groupSettingPage.get_pwd_switch_state()
            check.not_equal(init_state, new_state, "❌ 聊天密码开关切换失败")
            
        with allure.step("4. 再次点击恢复初始状态"):
            self.groupSettingPage.click_chat_pwd()
            final_state = self.groupSettingPage.get_pwd_switch_state()
            check.equal(init_state, final_state, "❌ 聊天密码开关恢复初始状态失败")




