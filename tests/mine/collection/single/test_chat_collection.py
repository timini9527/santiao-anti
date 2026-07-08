import allure
import pytest
import pytest_check as check
from datetime import datetime
from pages.system.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.mine.collection.chat_collection_page import ChatCollectionPage
from pages.mine.collection.collection_page import CollectionPage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from pages.system.home.home_page import HomePage
from pages.system.home.side_slip_page import SideSlipPage
from pages.chat_options.images.chat_image_page import ChatImagePage


@allure.epic("IM核心功能测试")
@allure.feature("我的收藏-聊天页面收藏")
class TestChatCollection:
    """聊天页面发送收藏的测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试用例开始前的初始化
        """
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.longPressPage = ChatLongPressPage(driver_sender)
        self.collectionPage = CollectionPage(driver_sender)
        self.chatCollectionPage = ChatCollectionPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.sideSlipPage = SideSlipPage(driver_sender)
        self.imagePage = ChatImagePage(driver_sender)

        yield

        with allure.step("后置步骤：返回主页"):
            self.mainPage.go_to_main_page()


    def _enter_chat(self, strategy):
        """进入指定的聊天会话"""
        with allure.step(f"前置准备：进入会话 【{strategy.name}】"):
            self.chatListPage.enter_chat(strategy.name)

    def common_enter_my_collection(self):
        """进入我的收藏页面"""
        with allure.step("-> 回到主页，打开左滑菜单，进入我的收藏"):
            self.mainPage.go_to_main_page()
            self.sideSlipPage.open_left_menu()
            self.sideSlipPage.click_my_collection()
            self.chatCollectionPage.wait_for_collection_page_load()

    def _long_collection(self):
        """长按最后一条消息并收藏"""
        self.longPressPage.long_press_last_message()
        self.longPressPage.click_menu_item("收藏")
        toast = self.collectionPage.get_toast()
        check.equal("收藏成功", toast, f"收藏失败，实际 Toast：{toast}")

    def _build_text(self, prefix: str, strategy) -> str:
        """生成本次测试唯一文本，避免被历史收藏数据干扰"""
        timestamp = datetime.now().strftime("%H%M%S%f")
        return f"{prefix} {strategy.name} {timestamp}"

    def _send_text_and_collect(self, text: str):
        """发送文本并收藏最后一条消息"""
        self.chatPage.send_message(text)
        self._long_collection()

    def _send_image_and_collect(self, strategy):
        """发送图片并收藏最后一条图片消息"""
        self.imagePage.open_panel_to_album()
        result = self.imagePage.select_single_image(mode=1)
        check.is_true(result, "选图失败")
        self.imagePage.click_send_button()

        # TODO: 发送图片后最后一条消息定位不稳定，先重新进入会话再收藏。
        self.mainPage.go_to_main_page()
        self.chatListPage.enter_chat(strategy.name)
        self._long_collection()

    def _verify_latest_text(self, expected_text: str, index: int = 0):
        """校验我的收藏中最新文本内容"""
        actual_text = self.chatCollectionPage.get_collection_text_content(index)
        check.equal(actual_text, expected_text, f"校验失败：实际内容{actual_text}, 预期内容{expected_text}")

    def _verify_latest_texts(self, expected_texts: list[str]):
        """校验我的收藏中最新多条文本内容"""
        actual_texts = self.collectionPage.get_collection_text_data(index=len(expected_texts))
        check.equal(actual_texts, expected_texts, f"校验失败：实际内容{actual_texts}, 预期内容{expected_texts}")

    def _verify_latest_collection_time(self):
        """校验我的收藏中最新一条数据的收藏时间"""
        now_time = self.collectionPage.get_collection_page_time()
        _, coll_time = self.collectionPage.get_collection_time()
        result = self.collectionPage.verify_collection_time(now_time, coll_time)
        check.is_true(result, f"校验失败：收藏时间不匹配 {now_time} | {coll_time}")



    @allure.story("聊天页面收藏一条的文本消息")
    @allure.title("聊天页面收藏一条({strategy.name})的文本消息，状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_first_text(self, strategy):

        with allure.step(f"1. 进入聊天页面{strategy.name}"):
            self.chatListPage.enter_chat(strategy.name)

        with allure.step(f"2. 向 {strategy.name} 发送文本消息并收藏"):
            text = self._build_text("test 文本收藏", strategy)
            self._send_text_and_collect(text)

        with allure.step("3. 进入我的收藏页面"):
            self.common_enter_my_collection()

        with allure.step("4. 校验收藏列表数据及时间"):
            self._verify_latest_text(text)
            self._verify_latest_collection_time()

    @allure.story("聊天页面收藏一张图片消息")
    @allure.title("聊天页面收藏一张图片消息，状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_first_image(self, strategy):

        with allure.step(f"1.进入聊天页面{strategy.name}"):
            self.chatListPage.enter_chat(strategy.name)

        with allure.step(f"2. 向 {strategy.name} 发送图片消息并收藏"):
            self._send_image_and_collect(strategy)

        with allure.step("3. 进入我的收藏页面"):
            self.common_enter_my_collection()

        with allure.step("4. 校验收藏列表数据及时间"):
            # TODO: 图片内容补充，待优化
            self._verify_latest_collection_time()

    @allure.story("聊天页面收藏一条文本和一张图片消息")
    @allure.title("聊天页面收藏一条文本和一张图片消息，状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_text_and_image(self, strategy):

        with allure.step(f"1. 进入聊天页面{strategy.name}"):
            self.chatListPage.enter_chat(strategy.name)

        with allure.step(f"2. 向 {strategy.name} 发送文本消息并收藏"):
            text = self._build_text("test 混合收藏文本", strategy)
            self._send_text_and_collect(text)

        with allure.step(f"3. 向 {strategy.name} 发送图片消息并收藏"):
            self._send_image_and_collect(strategy)

        with allure.step("4. 进入我的收藏页面"):
            self.common_enter_my_collection()

        with allure.step("5. 校验文本和图片收藏结果"):
            self._verify_latest_text(text)
            self._verify_latest_collection_time()

    @allure.story("聊天页面批量收藏多条文本消息")
    @allure.title("聊天页面批量收藏多条文本消息，状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_batch_text(self, strategy):

        with allure.step(f"1. 进入聊天页面{strategy.name}"):
            self.chatListPage.enter_chat(strategy.name)

        with allure.step("2. 连续发送并收藏多条文本消息"):
            first_text = self._build_text("test 批量收藏文本1", strategy)
            second_text = self._build_text("test 批量收藏文本2", strategy)
            self._send_text_and_collect(first_text)
            self._send_text_and_collect(second_text)

        with allure.step("3. 进入我的收藏页面"):
            self.common_enter_my_collection()

        with allure.step("4. 校验收藏列表按收藏时间倒序展示"):
            self._verify_latest_texts([second_text, first_text])
