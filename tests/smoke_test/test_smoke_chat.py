import pytest
import allure
import pytest_check as check
import time
from core.logger_utils import logger

from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.chat.search.chat_search_page import ChatSearchPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.home.side_slip_page import SideSlipPage
from pages.collection.chat_collection_page import ChatCollectionPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2
from utils.file_reader.data_loader import load_yaml_data

CHAT_DATA = load_yaml_data("chat/chat.yaml").get("test_data")


class BaseSmokeChat:
    """单聊及聊天设置/长按/搜索测试基类，统一管理 Page 实例化与后置清理"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.chatSearchPage = ChatSearchPage(driver_sender)
        self.longPressPage = ChatLongPressPage(driver_sender)
        self.collectionPage = ChatCollectionPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.sideSlipPage = SideSlipPage(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception:
            pass

    def _enter_setting(self, name: str):
        self.chatListPage.enter_chat(name)
        self.chatSettingPage.click_more_button()
        self.chatSettingPage.wait_for_setting_page_load()


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-单聊-基础与设置")
class TestSmokeChatCore(BaseSmokeChat):
    """单聊文本消息收发以及单聊选项（昵称、聊天密码、截屏、撤回、清空）冒烟用例"""

    @allure.story("发送文本消息")
    @allure.title("发送 Text 消息，状态：已完成")
    def test_send_text_message(self):
        text_message = CHAT_DATA.get("text_message")[0]
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])

        with allure.step("1. 进入私聊会话并发送消息"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.send_message(payload)

        with allure.step("2. 校验消息上屏"):
            text = self.chatPage.find_message_content(index=-1, side='sent')
            check.equal(text, expected, f"消息实际值 {text} 与预期值 {expected} 不匹配")

    @allure.story("查看好友昵称")
    @allure.title("单聊设置 - 获取聊天对象昵称-状态：已完成")
    def test_get_chat_nickname(self):
        with allure.step("1. 进入单聊设置"):
            self._enter_setting(PRIVATE_USER1.name)

        with allure.step("2. 获取并校验好友昵称"):
            nickname = self.chatSettingPage.get_friend_name()
            check.equal(nickname, PRIVATE_USER1.name, f"预期昵称: {PRIVATE_USER1.name}, 实际昵称: {nickname}")

    @allure.story("聊天密码开关")
    @allure.title("单聊设置 - 聊天密码开关-状态：已完成")
    def test_chat_password_switch(self):
        with allure.step("1. 进入单聊设置"):
            self._enter_setting(PRIVATE_USER1.name)

        with allure.step("2. 点击聊天密码开关"):
            init_status = self.chatSettingPage.get_switch_chat_pwd_status()
            if str(init_status).lower() == 'true':
                self.chatSettingPage.click_switch_chat_pwd()
                pytest.skip("聊天密码已开启，跳过测试")
            self.chatSettingPage.click_switch_chat_pwd()

        with allure.step("3. 回到主页校验消息已掩码"):
            self.mainPage.go_to_main_page()
            content = self.homePage.get_message_by_name(PRIVATE_USER1.name)
            check.is_in("******", content, "❌ 聊天密码未生效，内容未加密")

        with allure.step("4. 输入密码重新进入并还原开关"):
            self.homePage.get_conversation_by_name(PRIVATE_USER1.name).click()
            self.homePage.input_chat_password("111111")
            self.chatSettingPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
            self.chatSettingPage.click_switch_chat_pwd()

    @allure.story("清空聊天记录")
    @allure.title("单聊设置 - 清空聊天记录-状态：已完成")
    def test_clear_chat_records(self):
        with allure.step("1. 进入会话并发送待清理的消息"):
            self.chatListPage.enter_chat(PRIVATE_USER2.name)
            self.chatListPage.send_message("测试清空聊天记录功能")
            msg_count = self.chatListPage.get_total_message_count()
            check.is_true(bool(msg_count), "❌ 获取聊天消息数量失败")

        with allure.step("2. 进入设置页面执行清空"):
            self.chatSettingPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
            self.chatSettingPage.click_clear_chat_record()
            self.chatSettingPage.click_two_confirm()
            self.chatSettingPage.click_iv_back_button()

        with allure.step("3. 验证聊天记录已清空"):
            new_msg_count = self.chatListPage.get_total_message_count()
            check.equal(new_msg_count, 0, f"❌ 清空后消息数量应为 0，实际为 {new_msg_count}")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-单聊-检索")
class TestSmokeChatSearch(BaseSmokeChat):
    """聊天记录全文文本检索与定位冒烟用例"""

    @allure.story("文本消息检索")
    @allure.title("文本内容检索 - 消息存在-状态：已完成")
    def test_search_by_text_content_and_locate(self):
        keyword = "SearchMarker"
        test_msg = f"这是一条用于聊天记录搜索测试的独占关键字消息: {keyword}"

        with allure.step("1. 进入私聊并发送包含关键字的测试消息"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatSettingPage.send_message(test_msg)
            self.chatSettingPage.wait_for_last_message_send_status()

        with allure.step("2. 进入设置页，查找聊天记录"):
            self.chatSettingPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
            self.chatSettingPage.click_search_chat_record()
            self.chatSearchPage.wait_for_search_page_load()

        with allure.step("3. 输入关键字检索并点击结果定位"):
            self.chatSearchPage.input_search_keyword(keyword)
            results_count = self.chatSearchPage.get_search_results_count()
            check.greater(results_count, 0, f"❌ 未能检索到关键字: {keyword}")
            if results_count > 0:
                self.chatSearchPage.click_search_result_item(0)

        with allure.step("4. 验证是否精准定位回聊天主界面"):
            is_in_chat = self.chatSettingPage.wait_for_last_message_send_status()
            check.is_true(is_in_chat, "❌ 未成功返回聊天主会话流页面")
            last_message = self.chatSettingPage.get_text_message_content_by_index()
            check.is_in(keyword, last_message, f"❌ 未能在屏幕上找到定位消息")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-单聊-长按菜单")
class TestSmokeChatLongPress(BaseSmokeChat):
    """消息气泡长按动作（复制、收藏）冒烟用例"""

    @allure.story("长按菜单复制")
    @allure.title("长按菜单操作专项：复制-状态：已完成")
    def test_long_press_action_copy(self):
        payload = "测试气泡复制功能文本"
        
        with allure.step("1. 发送待测文本消息"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.send_message(payload)
            self.chatPage.wait_for_last_message_send_status()

        with allure.step("2. 长按消息气泡点击【复制】"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("复制")
            check.is_true(is_ok, "❌ 点击【复制】失败")

        with allure.step("3. 校验系统剪贴板内容"):
            paste_text = self.chatPage.paste_clipboard_text()
            check.equal(paste_text, payload, f"❌ 复制内容不一致: {paste_text}")

    @allure.story("长按菜单收藏")
    @allure.title("长按菜单操作专项：收藏-状态：已完成")
    def test_long_press_action_collection(self):
        payload = "测试气泡收藏功能文本"

        with allure.step("1. 发送待测文本消息"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.send_message(payload)
            self.chatPage.wait_for_last_message_send_status()

        with allure.step("2. 长按消息气泡点击【收藏】"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("收藏")
            check.is_true(is_ok, "❌ 点击【收藏】失败")

        with allure.step("3. 前往收藏夹比对内容"):
            self.mainPage.go_to_main_page()
            self.homePage.open_left_menu()
            self.sideSlipPage.click_collection()
            coll_tt = self.collectionPage.get_collection_text_content()
            check.equal(coll_tt, payload, f"❌ 收藏夹文本不一致: {coll_tt}")
