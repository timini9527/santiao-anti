import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.system.main.main_page import MainPage
from pages.system.home.home_page import HomePage
from pages.chat.groups.create.group_create_page import GroupCreatePage
from pages.chat.groups.setting.general.group_setting_page import GroupSettingPage
from pages.chat.groups.setting.notice.group_notice_page import GroupNoticePage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.system.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY
from utils.file_reader.data_loader import load_yaml_data
from locators.system.common.common_locator import CommonLocator




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
        d["expected"]["expected_toast"],
        d["expected"].get("truncate", False)  # 输入超长时 App 当场截断后仍成功发布，默认 False
    ))
notice_ids = [d["title"] for d in notice_rules]


@allure.epic("IM核心功能测试")
@allure.feature("群聊模块-群公告")
class TestGroupNotice:
    """群公告发布与内容测试"""

    # 类型注解帮助 IDE 提示
    mainPage: MainPage
    homePage: HomePage
    groupCreatePage: GroupCreatePage
    groupSettingPage: GroupSettingPage
    groupNoticePage: GroupNoticePage
    chatPage: ChatPage
    chatListPage: ChatListPage
    contactSelectPage: ContactSelectPage

    @pytest.fixture(scope="class", autouse=True)
    def setup_class_objects(self, request, driver_sender):
        """类级别 Setup & Teardown：初始化页面对象并在所有测试完成后清理环境"""
        request.cls.mainPage = MainPage(driver_sender)
        request.cls.homePage = HomePage(driver_sender)
        request.cls.groupCreatePage = GroupCreatePage(driver_sender)
        request.cls.groupSettingPage = GroupSettingPage(driver_sender)
        request.cls.groupNoticePage = GroupNoticePage(driver_sender)
        request.cls.chatPage = ChatPage(driver_sender)
        request.cls.chatListPage = ChatListPage(driver_sender)
        request.cls.contactSelectPage = ContactSelectPage(driver_sender)
                
        yield
        
        logger.info("🧹 [Teardown Class] 开始进行群公告环境清理...")
        try:
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
            desc = self.chatPage.get_group_notice_content()
            if desc != "":
                self.chatPage.click_group_notice()
                self.groupNoticePage.click_publish_btn()
                self.groupNoticePage.input_notice_content("")
                self.groupNoticePage.click_publish_btn()
                logger.info("✅ [Teardown Class] 已成功清空并删除群公告")
            else:
                logger.info("✅ [Teardown Class] 当前无已发布的群公告，无需清理")
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"❌ [Teardown Class] 群公告环境清理失败: {e}")

    @pytest.fixture(scope="function", autouse=True)
    def reset_to_main_page(self):
        """方法级别 Teardown：保证每个用例执行完都返回首页"""
        yield
        self.mainPage.go_to_main_page()

    
    def _enter_group(self):
        """进入群聊"""
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)
        self.chatPage.wait_for_chat_page_load(timeout=1, raise_exception=False)
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
            
            self.chatPage.wait_banner_message_disappear()
            self.chatPage.wait_for_chat_page_load()
    

    @allure.story("群公告功能")
    @allure.title("发布群公告限制校验 - {test_id}-状态：已完成")
    @pytest.mark.parametrize("test_id, content, should_success, expected_toast, truncate", notice_params, ids=notice_ids)
    def test_publish_group_notice_restrictions(self, test_id, content, should_success, expected_toast, truncate):
        """测试发布群公告的各种限制条件（特殊字符、长度、敏感词）"""
        with allure.step("1. 进入群聊并打开群公告页面"):
            self._enter_group()
            desc = self.groupNoticePage.get_notice_content()

        with allure.step("2. 进入群公告并开启编辑"):
            self.groupSettingPage.click_group_notice()
            self.groupNoticePage.wait_for_notice_page_load()
            if desc != "":
                self.groupNoticePage.click_publish_btn()
                time.sleep(0.5)

        expected_content = content[:300] if truncate else content

        with allure.step(f"3. 输入待测的群公告内容: '{test_id}'"):
            self.groupNoticePage.input_notice_content(content)
            if truncate:
                toast_msg = self.groupNoticePage.get_toast(expected_toast, timeout=1)
                check.is_true(toast_msg != "", f"❌ 预期弹出包含 '{expected_toast}' 的 Toast 提示，但实际未捕获到 {toast_msg}")

        with allure.step("4. 点击发布并验证结果"):
            self.groupNoticePage.click_publish_btn()

            if should_success:
                current_notice = self.groupNoticePage.get_notice_content()
                check.equal(current_notice, expected_content, f"❌ 群公告内容发布后校验不一致 {current_notice}")
            else:
                toast_msg = self.groupNoticePage.get_toast(expected_toast, timeout=1)
                check.is_true(toast_msg != "", f"❌ 预期弹出包含 '{expected_toast}' 的 Toast 提示，但实际未捕获到 {toast_msg}")

        with allure.step("5. [后置清理] 返回到聊天主页, 并验证横幅消息内容"):
            self.chatPage.back_to_chat_page()
            if should_success:
                banner_text = self.chatPage.get_group_notice_content()
                check.equal(banner_text, expected_content, f"❌ 群公告内容发布后校验不一致 {banner_text}")


    @allure.story("群公告功能")
    @allure.title("发布新群公告 - 取消发布流程-状态：已完成")
    def test_publish_group_notice_cancel(self):
        """取消发布群公告"""
        with allure.step("1. 进入群聊并打开群公告页面"):
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