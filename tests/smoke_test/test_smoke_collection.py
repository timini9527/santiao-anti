import pytest
import allure
import pytest_check as check
import time
from datetime import datetime

from pages.system.main.main_page import MainPage
from pages.system.home.home_page import HomePage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.mine.collection.collection_page import CollectionPage
from pages.mine.collection.chat_collection_page import ChatCollectionPage
from pages.system.home.side_slip_page import SideSlipPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2


class BaseSmokeCollectionSingle:
    """单端收藏夹测试基类，统一管理单端 Page 的初始化以及公共辅助方法"""

    @pytest.fixture(autouse=True)
    def setup_single(self, driver_sender):
        self.init_single_pages(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception:
            pass

    def init_single_pages(self, driver):
        """显式初始化单端（及双端发送端）页面对象，确保 IDE 静态推导与跳转"""
        self.mainPage = MainPage(driver)
        self.chatListPage = ChatListPage(driver)
        self.chatPage = ChatPage(driver)
        self.longPressPage = ChatLongPressPage(driver)
        self.collectionPage = CollectionPage(driver)
        self.chatCollectionPage = ChatCollectionPage(driver)
        self.homePage = HomePage(driver)
        self.sideSlipPage = SideSlipPage(driver)
        self.imagePage = ChatImagePage(driver)

    def init_receiver_pages(self, driver):
        """显式初始化双端接收端页面对象，确保 IDE 静态推导与跳转"""
        self.mainPageR = MainPage(driver)
        self.chatListPageR = ChatListPage(driver)
        self.chatPageR = ChatPage(driver)
        self.collectionPageR = CollectionPage(driver)
        self.chatCollectionPageR = ChatCollectionPage(driver)

    def common_enter_my_collection(self):
        self.mainPage.go_to_main_page()
        self.sideSlipPage.open_left_menu()
        self.sideSlipPage.click_my_collection()
        self.chatCollectionPage.wait_for_collection_page_load()

    def _build_text(self, prefix: str) -> str:
        timestamp = datetime.now().strftime("%H%M%S%f")
        return f"{prefix} {PRIVATE_USER1.name} {timestamp}"

    def _send_text_and_collect(self, text: str):
        self.chatPage.send_message(text)
        is_sent = self.chatPage.wait_for_last_message_send_status()
        if not is_sent:
            pytest.fail("❌ 消息发送失败，无法继续收藏")

        self.longPressPage.long_press_last_message()
        self.longPressPage.click_menu_item("收藏")
        toast = self.collectionPage.get_toast()
        if toast != "收藏成功":
            pytest.fail(f"❌ 收藏失败，实际 Toast：{toast}")

    def _send_image_and_collect(self):
        self.imagePage.open_panel_to_album()
        result = self.imagePage.select_single_image(mode=1)
        check.is_true(result, "选图失败")
        self.imagePage.click_send_button()
        self.mainPage.go_to_main_page()
        self.chatListPage.enter_chat(PRIVATE_USER1.name)
        self.longPressPage.long_press_last_message()
        self.longPressPage.click_menu_item("收藏")
        toast = self.collectionPage.get_toast()
        if toast != "收藏成功":
            pytest.fail(f"❌ 收藏图片失败，实际 Toast：{toast}")

    def _assert_latest_text_collection(self, expected_text: str) -> str:
        actual_text = self.chatCollectionPage.get_collection_text_content(0)
        if actual_text != expected_text:
            pytest.fail(f"❌ 最新收藏不是本用例创建的数据，停止操作。期望: {expected_text}, 实际: {actual_text}")
        return actual_text

    def _delete_latest_text_collection(self, expected_text: str) -> bool:
        self._assert_latest_text_collection(expected_text)
        is_deleted = self.collectionPage.del_collection_item(del_type="text", index=0)
        check.is_true(is_deleted, f"❌ 删除本用例收藏失败：{expected_text}")
        time.sleep(1)
        return is_deleted

    def _assert_latest_image_collection(self):
        first_image = self.chatCollectionPage.get_collection_image_element(0)
        if not first_image:
            pytest.fail("❌ 最新收藏不是图片条目，停止操作。")
        return first_image

    def _delete_latest_image_collection(self) -> bool:
        self._assert_latest_image_collection()
        is_deleted = self.collectionPage.del_collection_item(del_type="image", index=0)
        check.is_true(is_deleted, "❌ 删除本用例图片收藏失败")
        return is_deleted


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-我的收藏-管理")
class TestSmokeCollectionSingle(BaseSmokeCollectionSingle):
    """单端收藏夹条目管理（收藏、删除、发送）冒烟用例"""

    @allure.story("收藏条目删除")
    @allure.title("删除收藏夹中的单个条目流程 - 状态：已完成")
    def test_delete_collection_success(self):
        col_type = "text"
        
        with allure.step("1. 前置准备：发消息并收藏"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            unique_text = self._build_text("smoke_del_t")
            self._send_text_and_collect(unique_text)

        self.common_enter_my_collection()

        with allure.step("2. 确认最新收藏为本用例数据并删除"):
            self._delete_latest_text_collection(unique_text)

        with allure.step("3. 验证本用例收藏已被删除"):
            after_content = self.chatCollectionPage.get_collection_text_content(0)
            check.not_equal(after_content, unique_text, "❌ 删除校验失败：本用例收藏仍在最新位置")

    @allure.story("连续删除本用例收藏")
    @allure.title("连续删除本用例创建的收藏条目-状态：已完成")
    def test_delete_created_collection_items(self):
        with allure.step("1. 连续发送并收藏两条测试消息"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            first_text = self._build_text("smoke_batch_t1")
            second_text = self._build_text("smoke_batch_t2")
            self._send_text_and_collect(first_text)
            self._send_text_and_collect(second_text)

        self.common_enter_my_collection()

        with allure.step("2. 按最新顺序只删除本用例创建的两条收藏"):
            self._delete_latest_text_collection(second_text)
            self._delete_latest_text_collection(first_text)

        with allure.step("3. 验证本用例创建的收藏已清理"):
            latest_text = self.chatCollectionPage.get_collection_text_content(0)
            check.is_not_in(latest_text, [first_text, second_text], "❌ 本用例创建的收藏未清理干净")

    @allure.story("聊天中发送收藏")
    @allure.title("从聊天页面中的收藏发送消息-状态：已完成")
    def test_send_collection_message(self):
        col_type = "text"
        desc = f"Smoke_send_col_{int(time.time())}"
        source_text = self._build_text("smoke_send_source")

        with allure.step("1. 创建本用例专用收藏并进入收藏面板"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self._send_text_and_collect(source_text)
            self.chatCollectionPage.open_panel_enter_collection_page()

        with allure.step("2. 打开本用例刚创建的收藏项"):
            coll_content = self.chatCollectionPage.select_and_click_collection_item(col_type=col_type, index=0)
            if coll_content != source_text:
                pytest.fail(f"❌ 打开的收藏不是本用例数据，期望: {source_text}, 实际: {coll_content}")

        with allure.step("3. 输入附言并发送"):
            self.chatCollectionPage.send_collection_panel_input(desc)
            self.chatCollectionPage.click_send_collection_panel_send()

        with allure.step("4. 验证发送上屏"):
            self.chatListPage.click_add_button()
            flag = self.chatCollectionPage.verify_from_collection_message_content(
                col_type=col_type,
                exp_content=coll_content,
                msg=desc
            )
            check.is_true(flag, "❌ 收藏消息发送上屏验证失败")

        with allure.step("5. 清理本用例创建的收藏"):
            self.common_enter_my_collection()
            self._delete_latest_text_collection(source_text)


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-我的收藏-聊天页面收藏")
class TestSmokeChatCollection(BaseSmokeCollectionSingle):
    """聊天消息的直接收藏校验冒烟用例"""

    @allure.story("收藏单条文本消息")
    @allure.title("聊天页面收藏一条文本消息，状态：已完成")
    def test_collection_first_text(self):
        with allure.step("1. 进入私聊并发送文本收藏"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            text = self._build_text("smoke_collect_text")
            self._send_text_and_collect(text)

        with allure.step("2. 验证我的收藏记录"):
            self.common_enter_my_collection()
            self._assert_latest_text_collection(text)

        with allure.step("3. 清理本用例创建的收藏"):
            self._delete_latest_text_collection(text)

    @allure.story("收藏单条图片消息")
    @allure.title("聊天页面收藏一条图片消息，状态：已完成")
    def test_collection_first_image(self):
        with allure.step("1. 进入私聊并发送图片进行收藏"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self._send_image_and_collect()

        with allure.step("2. 验证我的收藏记录"):
            self.common_enter_my_collection()
            self._assert_latest_image_collection()

        with allure.step("3. 清理本用例创建的图片收藏"):
            self._delete_latest_image_collection()


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-我的收藏-双端协同")
class TestSmokeCollectionDouble(BaseSmokeCollectionSingle):
    """双端协同下的实时收藏与快捷发送校验冒烟用例"""

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        self.init_single_pages(driver_sender)
        self.init_receiver_pages(driver_receiver)

        with allure.step("前置准备：发送端与接收端均进入聊天室"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.wait_for_chat_page_load()
            self.chatListPageR.enter_chat(PRIVATE_USER2.name)
            self.chatPageR.wait_for_chat_page_load()
        yield
        try:
            self.mainPage.go_to_main_page()
            self.mainPageR.go_to_main_page()
        except Exception:
            pass

    @allure.story("双端协同实时收藏")
    @allure.title("收藏对方发送的文本消息-双端实时状态校验-状态：已完成")
    @pytest.mark.skip("用例本身需要双端同步，暂时跳过执行")
    def test_collect_received_text_message_double(self):
        test_msg = f"SmokeDoubleCollect_{int(time.time())}"

        with allure.step("1. 接收端发送消息"):
            self.chatPageR.send_message(test_msg)
            self.chatPageR.wait_banner_message_disappear()

        with allure.step("2. 发送端长按并收藏消息"):
            elem, text_val = self.collectionPage.get_received_text(index=-1)
            check.equal(text_val, test_msg, "❌ 接收的最新消息内容不匹配")
            self.collectionPage.get_first_collection_item(elem)
            toast = self.collectionPage.toast_message()
            check.equal(toast, "成功", "❌ 收藏操作失败")

        with allure.step("3. 发送端进入我的收藏页面校验"):
            self.collectionPage.back_to_main()
            self.collectionPage.enter_my_collection()
            actual_text_list = self.collectionPage.get_collection_text_data(index=1)
            check.is_true(len(actual_text_list) > 0, "❌ 收藏未同步")
            check.equal(actual_text_list[0], test_msg, "❌ 收藏的文本内容与原消息不符")

        with allure.step("4. 环境清理：删除该收藏"):
            self.collectionPage.del_collection_item(del_type="text", index=0)
