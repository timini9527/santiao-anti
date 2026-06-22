import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.group_setting_page import GroupSettingPage
from pages.groups.setting.group_notice_page import GroupNoticePage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY
from utils.file_reader.data_loader import load_yaml_data




# 加载群公告外部测试数据
notice_yaml_data = load_yaml_data('groups/group_notice_rules.yaml')
notice_rules = notice_yaml_data.get("test_data", {}).get("notice_validation", [])
notice_params = []
for d in notice_rules:
    content = d["data"]["content"]
    # 动态展开 GENERATE_CHAR 占位符
    if content.startswith("GENERATE_CHAR:"):
        _, char, count = content.split(":")
        content = char * int(count)
        
    notice_params.append((
        d["title"],
        content,
        d["expected"]["should_success"],
        d["expected"]["expected_toast"]
    ))
notice_ids = [d["title"] for d in notice_rules]


@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群公告")
class TestGroupNotice:
    """群公告发布与内容测试"""

    @pytest.fixture(autouse=True)
    def setup_class(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupNoticePage = GroupNoticePage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        
        
        yield
        
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    
    def _enter_group(self):
        """进入群聊"""
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)
        self.chatPage.wait_for_chat_page_load()
        self.chatPage.click_more_button()
        self.groupSettingPage.wait_for_setting_page_load()


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
    

    @allure.story("群公告功能")
    @allure.title("发布群公告限制校验 - {test_id}")
    @pytest.mark.parametrize("test_id, content, should_success, expected_toast", notice_params, ids=notice_ids)
    def test_publish_group_notice_restrictions(self, test_id, content, should_success, expected_toast):
        """测试发布群公告的各种限制条件（特殊字符、长度、敏感词）"""
        with allure.step("1. 进入群聊并获取当前公告状态"):
            self._enter_group()
            desc = self.groupNoticePage.get_notice_content()

        with allure.step("2. 进入群公告并开启编辑"):
            self.groupSettingPage.click_group_notice()
            self.groupNoticePage.wait_for_notice_page_load()
            if desc != "":
                self.groupNoticePage.click_publish_btn()
                time.sleep(0.5)

        with allure.step(f"3. 输入待测的群公告内容: '{test_id}'"):
            self.groupNoticePage.input_notice_content(content)
            if len(content) > 300:
                toast_msg = self.groupNoticePage.get_toast(expected_toast, timeout=1)
                check.is_true(toast_msg != "", f"❌ 预期弹出包含 '{expected_toast}' 的 Toast 提示，但实际未捕获到 {toast_msg}")
                content = content[:300]
                should_success = True

        with allure.step("4. 点击发布并验证结果"):
            self.groupNoticePage.click_publish_btn()
            
            if should_success:
                current_notice = self.groupNoticePage.get_notice_content()
                check.equal(current_notice, content, f"❌ 群公告内容发布后校验不一致 {current_notice}")
            else:
                toast_msg = self.groupNoticePage.get_toast(expected_toast, timeout=1)
                check.is_true(toast_msg != "", f"❌ 预期弹出包含 '{expected_toast}' 的 Toast 提示，但实际未捕获到 {toast_msg}")

        with allure.step("5. [后置清理] 返回到聊天主页, 并验证横幅消息内容"):
            self.chatPage.back_to_chat_page()
            if should_success:
                banner_text = self.chatPage.get_group_notice_content()
                check.equal(banner_text, content, f"❌ 群公告内容发布后校验不一致 {banner_text}")


    @allure.story("群公告功能")
    @allure.title("发布新群公告 - 取消发布流程")
    def test_publish_group_notice_cancel(self):
        """取消发布群公告"""
        with allure.step("1. 进入群聊并获取当前公告状态"):
            self._enter_group()
            desc = self.groupNoticePage.get_notice_content()

        with allure.step("2. 进入群公告并开启编辑"):
            self.groupSettingPage.click_group_notice()
            self.groupNoticePage.wait_for_notice_page_load()
            if desc != "":
                self.groupNoticePage.click_publish_btn()
                time.sleep(0.5)

        with allure.step("3. 输入待测的群公告内容并点击返回"):
            notice_content = "取消发布公告测试"
            self.groupNoticePage.input_notice_content(notice_content)
            self.groupNoticePage.click_back_button()

        with allure.step("4. 验证公告内容未发生改变并返回主页"):
            current_notice = self.groupNoticePage.get_notice_content()
            check.equal(current_notice, desc, f"❌ 取消保存后，公告内容不应改变，实际为: {current_notice}")