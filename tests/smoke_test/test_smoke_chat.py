import pytest
import allure
import pytest_check as check
from pages.system.main.main_page import MainPage
from pages.system.home.home_page import HomePage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.chat.search.chat_search_page import ChatSearchPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.system.home.side_slip_page import SideSlipPage
from pages.mine.collection.chat_collection_page import ChatCollectionPage
from pages.mine.collection.collection_page import CollectionPage
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
        self.chatCollectionPage = ChatCollectionPage(driver_sender)
        self.collectionPage = CollectionPage(driver_sender)
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
        enabled_by_test = False

        try:
            with allure.step("1. 进入单聊设置"):
                self._enter_setting(PRIVATE_USER1.name)

            with allure.step("2. 开启聊天密码开关"):
                init_status = self.chatSettingPage.get_switch_chat_pwd_status()
                if str(init_status).lower() == 'true':
                    pytest.skip("聊天密码已开启，跳过测试，避免改变已有环境状态")

                self.chatSettingPage.click_switch_chat_pwd()
                enabled_by_test = True

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
                enabled_by_test = False
        finally:
            if enabled_by_test:
                with allure.step("后置清理：关闭本用例开启的聊天密码"):
                    try:
                        self.mainPage.go_to_main_page()
                        self.homePage.get_conversation_by_name(PRIVATE_USER1.name).click()
                        self.homePage.input_chat_password("111111")
                        self.chatSettingPage.click_more_button()
                        self.chatSettingPage.wait_for_setting_page_load()
                        if str(self.chatSettingPage.get_switch_chat_pwd_status()).lower() == 'true':
                            self.chatSettingPage.click_switch_chat_pwd()
                    except Exception:
                        pass

    @allure.story("截屏通知开关")
    @allure.title("单聊设置 - 截屏通知开关-状态：已完成")
    def test_screenshot_notification_switch(self):
        init_status = None
        changed = False

        try:
            with allure.step("1. 进入单聊设置"):
                self._enter_setting(PRIVATE_USER1.name)

            with allure.step("2. 切换截屏通知开关并校验"):
                init_status = self.chatSettingPage.get_switch_screenshot_status()
                self.chatSettingPage.click_switch_screenshot()
                changed = True
                new_status = self.chatSettingPage.get_switch_screenshot_status()
                check.not_equal(new_status, init_status, "❌ 截屏通知开关状态未发生切换")

            with allure.step("3. 还原截屏通知开关"):
                self.chatSettingPage.click_switch_screenshot()
                changed = False
                final_status = self.chatSettingPage.get_switch_screenshot_status()
                check.equal(final_status, init_status, "❌ 截屏通知开关状态未还原")
        finally:
            if changed:
                with allure.step("后置清理：恢复初始截屏通知状态"):
                    try:
                        if not self.chatSettingPage.wait_for_setting_page_load(timeout=2):
                            self.mainPage.go_to_main_page()
                            self.chatListPage.enter_chat(PRIVATE_USER1.name)
                            self.chatSettingPage.click_more_button()
                            self.chatSettingPage.wait_for_setting_page_load()
                        
                        curr_status = self.chatSettingPage.get_switch_screenshot_status()
                        if curr_status != init_status and init_status is not None:
                            self.chatSettingPage.click_switch_screenshot()
                    except Exception:
                        pass

    @allure.story("撤回通知开关")
    @allure.title("单聊设置 - 撤回通知开关-状态：已完成")
    def test_recall_notification_switch(self):
        init_status = None
        changed = False

        try:
            with allure.step("1. 进入单聊设置"):
                self._enter_setting(PRIVATE_USER1.name)

            with allure.step("2. 切换撤回通知开关并校验"):
                init_status = self.chatSettingPage.get_switch_recall_status()
                self.chatSettingPage.click_switch_recall()
                changed = True
                new_status = self.chatSettingPage.get_switch_recall_status()
                check.not_equal(new_status, init_status, "❌ 撤回通知开关状态未发生切换")

            with allure.step("3. 还原撤回通知开关"):
                self.chatSettingPage.click_switch_recall()
                changed = False
                final_status = self.chatSettingPage.get_switch_recall_status()
                check.equal(final_status, init_status, "❌ 撤回通知开关状态未还原")
        finally:
            if changed:
                with allure.step("后置清理：恢复初始撤回通知状态"):
                    try:
                        if not self.chatSettingPage.wait_for_setting_page_load(timeout=2):
                            self.mainPage.go_to_main_page()
                            self.chatListPage.enter_chat(PRIVATE_USER1.name)
                            self.chatSettingPage.click_more_button()
                            self.chatSettingPage.wait_for_setting_page_load()
                        
                        curr_status = self.chatSettingPage.get_switch_recall_status()
                        if curr_status != init_status and init_status is not None:
                            self.chatSettingPage.click_switch_recall()
                    except Exception:
                        pass



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

    @allure.story("文本消息检索 - 消息不存在")
    @allure.title("文本内容检索 - 消息不存在(空边界)-状态：已完成")
    def test_search_text_content_not_exist(self):
        non_exist_keyword = "NonExist_#@!_Marker_9527"

        with allure.step("1. 进入私聊并进入查找聊天记录页"):
            self._enter_setting(PRIVATE_USER1.name)
            self.chatSettingPage.click_search_chat_record()
            self.chatSearchPage.wait_for_search_page_load()

        with allure.step("2. 输入确保不存在的关键字并校验结果为空"):
            self.chatSearchPage.input_search_keyword(non_exist_keyword)
            results_count = self.chatSearchPage.get_search_results_count()
            check.equal(results_count, 0, f"❌ 预期无搜索结果，但实际找到了 {results_count} 条记录")

    @allure.story("快速分类检索入口")
    @allure.title("快速分类检索入口可用性校验-状态：已完成")
    def test_search_by_category_entry(self):
        with allure.step("1. 进入私聊并进入查找聊天记录页"):
            self._enter_setting(PRIVATE_USER1.name)
            self.chatSettingPage.click_search_chat_record()
            self.chatSearchPage.wait_for_search_page_load()

        with allure.step("2. 点击【图片】分类并验证加载"):
            self.chatSearchPage.click_image_option()
            is_media_loaded = self.chatSearchPage.wait_for_media_page_load()
            check.is_true(is_media_loaded, "❌ 图片分类检索页面加载失败")
            self.chatSearchPage.back()
            self.chatSearchPage.wait_for_search_page_load()

        with allure.step("3. 点击【文件】分类并验证加载"):
            self.chatSearchPage.click_file_option()
            is_file_loaded = self.chatSearchPage.wait_for_file_page_load()
            check.is_true(is_file_loaded, "❌ 文件分类检索页面加载失败")
            self.chatSearchPage.back()


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-单聊-长按菜单")
class TestSmokeChatLongPress(BaseSmokeChat):
    """消息气泡长按动作（复制、收藏）冒烟用例"""

    @allure.story("长按菜单复制")
    @allure.title("长按菜单操作专项：复制-状态：已完成")
    def test_long_press_action_copy(self):
        payload = "测试气泡复-制功能文本"
        
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
        payload = "测试气泡收-藏功能文本"

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
            self.sideSlipPage.click_my_collection()
            coll_tt = self.chatCollectionPage.get_collection_text_content()
            check.equal(coll_tt, payload, f"❌ 收藏夹文本不一致: {coll_tt}")

        with allure.step("4. 删除本次测试产生的收藏内容"):
            is_deleted = self.collectionPage.del_collection_item(del_type="text", index=0)
            check.is_true(is_deleted, "❌ 删除本次测试产生的收藏内容失败")


    @allure.story("长按菜单删除")
    @allure.title("长按菜单操作专项：删除消息-状态：已完成")
    def test_long_press_action_delete(self):
        payload = "临时待删-除的消息"

        with allure.step("1. 进入私聊并发送待删除的测试消息"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.send_message(payload)
            is_sent = self.chatPage.wait_for_last_message_send_status()
            check.is_true(is_sent, "❌ 测试消息发送失败，无法进行删除测试")

        with allure.step("2. 校验最后一条发送的消息内容为待删除文本"):
            last_msg = self.chatPage.get_text_message_content_by_index(index=-1, side="sent")
            check.equal(last_msg, payload, "❌ 发送待删除的消息内容不匹配")

        with allure.step("3. 长按消息点击【删除】并校验该内容已成功抹除"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("删除")
            check.is_true(is_ok, "❌ 长按点击【删除】失败")
            post_last_msg = self.chatPage.get_text_message_content_by_index(index=-1, side="sent", expect_missing=True)
            check.not_equal(post_last_msg, payload, "❌ 删除消息后，最后一条消息内容仍为已删除的文本")


    @allure.story("长按菜单撤回")
    @allure.title("长按菜单操作专项：撤回消息-状态：已完成")
    def test_long_press_action_recall(self):
        payload = "临时待撤-回的消息"

        with allure.step("1. 进入私聊并发送待撤回的消息"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.send_message(payload)
            is_sent = self.chatPage.wait_for_last_message_send_status()
            check.is_true(is_sent, "❌ 测试消息发送失败，无法进行撤回测试")

        with allure.step("2. 长按消息点击【撤回】"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("撤回")
            check.is_true(is_ok, "❌ 长按点击【撤回】失败")
            self.longPressPage.click_dialog_confirm()

        with allure.step("3. 验证撤回通知上屏"):
            notice_msg, _ = self.chatListPage.get_withdraw_message()
            check.is_in("撤回了一条消息", notice_msg, "❌ 聊天流中未发现'撤回了一条消息'的提示信息")


