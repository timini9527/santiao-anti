import pytest
import allure
import pytest_check as check
import time
from datetime import datetime
from core.logger_utils import logger

from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.collection.collection_page import CollectionPage
from pages.collection.chat_collection_page import ChatCollectionPage
from pages.home.side_slip_page import SideSlipPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2


class BaseSmokeCollectionSingle:
    """单端收藏夹测试基类，统一管理单端 Page 的初始化以及公共辅助方法"""

    @pytest.fixture(autouse=True)
    def setup_single(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.longPressPage = ChatLongPressPage(driver_sender)
        self.collectionPage = CollectionPage(driver_sender)
        self.chatCollectionPage = ChatCollectionPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.sideSlipPage = SideSlipPage(driver_sender)
        self.imagePage = ChatImagePage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        yield
        self.mainPage.go_to_main_page()

    def common_enter_my_collection(self):
        self.mainPage.go_to_main_page()
        self.sideSlipPage.open_left_menu()
        self.sideSlipPage.click_my_collection()
        self.chatCollectionPage.wait_for_collection_page_load()

    def _build_text(self, prefix: str, strategy) -> str:
        timestamp = datetime.now().strftime("%H%M%S%f")
        return f"{prefix} {strategy.name} {timestamp}"

    def _send_text_and_collect(self, text: str):
        self.chatPage.send_message(text)
        self.longPressPage.long_press_last_message()
        self.longPressPage.click_menu_item("收藏")
        toast = self.collectionPage.get_toast()
        check.equal("收藏成功", toast, f"收藏失败，实际 Toast：{toast}")

    def _send_image_and_collect(self, strategy):
        self.imagePage.open_panel_to_album()
        result = self.imagePage.select_single_image(mode=1)
        check.is_true(result, "选图失败")
        self.imagePage.click_send_button()
        self.mainPage.go_to_main_page()
        self.chatListPage.enter_chat(strategy.name)
        self.longPressPage.long_press_last_message()
        self.longPressPage.click_menu_item("收藏")
        self.collectionPage.get_toast()

    def _verify_latest_text(self, expected_text: str):
        actual_text = self.chatCollectionPage.get_collection_text_content(0)
        check.equal(actual_text, expected_text, f"校验失败：实际内容{actual_text}, 预期内容{expected_text}")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-我的收藏-管理")
class TestSmokeCollectionSingle(BaseSmokeCollectionSingle):
    """单端收藏夹条目删除、清空及快捷发送冒烟用例"""

    @allure.story("收藏条目删除")
    @allure.title("删除收藏夹中的单个条目流程 - 状态：已完成")
    def test_delete_collection_success(self):
        strategy = PRIVATE_USER1
        col_type = "text"
        
        with allure.step("1. 前置准备：发消息并收藏"):
            self.chatListPage.enter_chat(strategy.name)
            unique_text = self._build_text("smoke_del_t", strategy)
            self._send_text_and_collect(unique_text)

        self.common_enter_my_collection()

        with allure.step("2. 执行删除刚造的最新一条收藏"):
            before_content = self.collectionPage.get_collection_text_content(0)
            self.collectionPage.del_collection_item(del_type=col_type, index=0)

        with allure.step("3. 验证删除结果"):
            after_content = self.collectionPage.get_collection_text_content(0)
            check.not_equal(before_content, after_content, f"❌ 删除校验失败")

    @allure.story("清空收藏")
    @allure.title("一键清空全部收藏条目流程-状态：已完成")
    def test_delete_all_collection_items(self):
        strategy = PRIVATE_USER1
        
        with allure.step("1. 发送并收藏测试消息"):
            self.chatListPage.enter_chat(strategy.name)
            text1 = self._build_text("smoke_all_t1", strategy)
            self._send_text_and_collect(text1)
            
        self.common_enter_my_collection()
            
        with allure.step("2. 一键清空全部收藏并验证"):
            self.collectionPage.del_collection_all_item(del_type="all")
            after_items = self.collectionPage.get_collection_items()
            check.equal(len(after_items), 0, "❌ 校验失败：一键清空全部后收藏列表未清空")

    @allure.story("聊天中发送收藏")
    @allure.title("从聊天页面中的收藏发送消息-状态：已完成")
    def test_send_collection_message(self):
        strategy = PRIVATE_USER1
        col_type = "text"
        desc = f"Smoke_send_col_{int(time.time())}"

        with allure.step("1. 进入会话和收藏面板"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatCollectionPage.open_panel_enter_collection_page()

        with allure.step("2. 打开收藏项"):
            coll_content = self.chatCollectionPage.select_and_click_collection_item(col_type=col_type, index=0)
            if not coll_content:
                pytest.skip("⚠️ 缺少收藏记录，跳过执行")

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


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-我的收藏-聊天页面收藏")
class TestSmokeChatCollection(BaseSmokeCollectionSingle):
    """聊天消息的直接收藏与倒序排列校验冒烟用例"""

    @allure.story("收藏单条文本消息")
    @allure.title("聊天页面收藏一条文本消息，状态：已完成")
    def test_collection_first_text(self):
        strategy = PRIVATE_USER1
        
        with allure.step("1. 进入私聊并发送文本收藏"):
            self.chatListPage.enter_chat(strategy.name)
            text = self._build_text("smoke_collect_text", strategy)
            self._send_text_and_collect(text)

        with allure.step("2. 验证我的收藏记录"):
            self.common_enter_my_collection()
            actual_text = self.chatCollectionPage.get_collection_text_content(0)
            check.equal(actual_text, text, f"❌ 收藏内容不符")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-我的收藏-双端协同")
class TestSmokeCollectionDouble:
    """双端协同下的实时收藏与快捷发送校验冒烟用例"""

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        self.mainS = MainPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.collS = CollectionPage(driver_sender)
        self.chatCollS = ChatCollectionPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.collR = CollectionPage(driver_receiver)

        with allure.step("前置准备：发送端与接收端均进入聊天室"):
            self.chatListS.enter_chat(PRIVATE_USER1.name)
            self.chatS.wait_for_chat_page_load()
            self.chatListR.enter_chat(PRIVATE_USER2.name)
            self.chatR.wait_for_chat_page_load()
        yield
        try:
            self.mainS.go_to_main_page()
            self.mainR.go_to_main_page()
        except Exception:
            pass

    @allure.story("双端协同实时收藏")
    @allure.title("收藏对方发送的文本消息-双端实时状态校验-状态：已完成")
    def test_collect_received_text_message_double(self):
        test_msg = f"SmokeDoubleCollect_{int(time.time())}"

        with allure.step("1. 接收端发送消息"):
            self.chatR.send_message(test_msg)
            self.chatR.wait_banner_message_disappear()

        with allure.step("2. 发送端长按并收藏消息"):
            elem, text_val = self.collS.get_received_text(index=-1)
            check.equal(text_val, test_msg, "❌ 接收的最新消息内容不匹配")
            self.collS.get_first_collection_item(elem)
            toast = self.collS.toast_message()
            check.equal(toast, "成功", "❌ 收藏操作失败")

        with allure.step("3. 发送端进入我的收藏页面校验"):
            self.collS.back_to_main()
            self.collS.enter_my_collection()
            actual_text_list = self.collS.get_collection_text_data(index=1)
            check.is_true(len(actual_text_list) > 0, "❌ 收藏未同步")
            check.equal(actual_text_list[0], test_msg, "❌ 收藏的文本内容与原消息不符")

        with allure.step("4. 环境清理：删除该收藏"):
            self.collS.del_collection_item(del_type="text", index=0)
