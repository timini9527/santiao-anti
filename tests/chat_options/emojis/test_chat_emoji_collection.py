import allure
import pytest
import pytest_check as check
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_page import ChatPage
from strategy.chat.chat_strategy import (PRIVATE_USER1)
from pages.main.main_page import MainPage
from core.logger_utils import logger

from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.chat_options.emojis.chat_emoji_manage_page import ChatEmojiManagePage
from pages.chat_options.emojis.chat_emoji_package_page import ChatEmojiPackagePage
from pages.chat_options.emojis.chat_emoji_store_page import ChatEmojiStorePage

@allure.epic("IM核心功能测试")
@allure.feature("聊天面板-表情包")
@allure.story("自定义/收藏表情包管理")
class TestChatEmojiCollection:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        初始化收藏表情管理与批量删除测试所需的 Page 实例
        """
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        
        self.emojiPage = ChatEmojiPage(driver_sender)
        self.emojiManagePage = ChatEmojiManagePage(driver_sender)
        self.emojiPackagePage = ChatEmojiPackagePage(driver_sender)
        self.emojiStorePage = ChatEmojiStorePage(driver_sender) # 用于前置备货

        yield  

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    @allure.story("添加单个表情包/图片到收藏夹")
    @pytest.mark.parametrize("pkg_count, add_count, desc", [
        (3, 1, "长按添加聊天列表中第 1 个表情包到收藏"),
        (3, None, "长按添加聊天列表中所有未收藏的表情包"),
    ])
    def test_add_single_emoji_package_to_coll(self, pkg_count, add_count, desc):
        allure.dynamic.title(f"在聊天页面中添加表情包到收藏夹 - {desc}")
        emoji_type = "single" 
        click_count = 1        

        with allure.step("0. 前置条件: 进入聊天页面，准备数据环境"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            # 获取当前聊天中的表情包数量
            empkg_elems, emoji_package_count_pre = self.emojiPackagePage.get_emoji_package_message_elements()
            
            # 获取当前收藏夹中的总量
            self.chatPage.enter_emoji_page()
            self.emojiPackagePage.open_collection_emoji_manage()
            coll_empkg_count_pre = self.emojiPackagePage.get_collection_emoji_pkg_all_items()
        
        with allure.step(f"1. 确认 Tab 栏环境，确保有可发送的表情包"):
            tab_emoji_pkgs, added_empkg_count = self.emojiPage._get_top_tab_emoji_package_count()
            if added_empkg_count <= 0:
                logger.warning(f"本地无可发送表情包，将从商店添加第 {pkg_count} 个表情包作为货源")
                self.emojiStorePage.open_emoji_store()
                added_pkg_names, add_status = self.emojiStorePage.add_emoji_packages(emoji_type, pkg_count)
                check.is_true(add_status, f"商店加货失败")
                self.emojiStorePage.back_to_emoji_store()
            
            self.emojiPackagePage.switch_to_emoji_package(click_count)

            sent_count = 1 if add_count is not None else len(self.emojiPage.get_visible_emojis())

        with allure.step(f"2. 长按聊天气泡执行“添加到收藏”操作"):
            if add_count is None:
                success_count, tried_count = self.emojiPackagePage.send_and_add_all_emojis_with_paging()
                add_count = tried_count
            else:
                if emoji_package_count_pre == 0:
                    logger.info(f"聊天记录为空，先发送 {sent_count} 个表情包")
                    self.emojiPackagePage.sent_emoji_package(emoji_type, sent_count)
                    self.chatPage.enter_emoji_page()
                    empkg_elems, emoji_package_count_aft = self.emojiPackagePage.get_emoji_package_message_elements()
                    add_count = emoji_package_count_aft
                
                success_count, _ = self.emojiPackagePage.long_press_emoji_package_and_add(empkg_elems[::-1], add_count)
            
            check.equal(success_count, add_count, f"收藏操作完成数与预期不符")

        with allure.step("3. 验证收藏夹总量是否增加"):
            if emoji_package_count_pre == 0:
                self.chatPage.enter_emoji_page()
            self.emojiManagePage.open_collection_emoji_manage()
            coll_empkg_count_aft = self.emojiManagePage.get_collection_emoji_pkg_all_items()
            
            check.not_equal(coll_empkg_count_pre, coll_empkg_count_aft, 
                        f"收藏夹计数未发生变化！前: {coll_empkg_count_pre}, 后: {coll_empkg_count_aft}")

    @allure.story("从表情管理页面中删除已添加的表情包")
    @pytest.mark.parametrize("emoji_type, count, desc", [
        ("sequential", 1, "删除列表中的第一个表情包"),
        ("sequential", 3, "连续删除列表前 3 个表情包"),
        ("random", 1, "随机删除列表中的 1 个表情包"),
        ("all", 0, "清空/删除当前拥有的全部收藏表情")
    ])
    def test_delete_emoji_package_from_manage(self, emoji_type, count, desc):
        allure.dynamic.title(f"表情管理页面删除收藏表情测试 - {desc}")

        with allure.step("1. 打开表情面板，进入收藏管理详情页"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.enter_emoji_page()
            self.emojiManagePage.open_collection_emoji_manage()
            
            # 预判是否为空，避免不必要的报错
            initial_count = self.emojiManagePage.get_collection_emoji_pkg_all_items()
            if initial_count <= 0:
                logger.warning("当前收藏夹为空，无法执行删除策略")
                pytest.skip("收藏夹为空，跳过")
                
            self.emojiManagePage.enter_manage_page()

        with allure.step(f"2. 执行删除策略: {desc}"):
            self.emojiManagePage.click_right_btn()
            del_result = self.emojiManagePage.delete_manage_emoji_packages(emoji_type, count)
            
            check.is_true(del_result, f"策略【{emoji_type}】执行失败或数量未对齐")

        with allure.step("3. 任务结束，返回聊天页面"):
            self.emojiManagePage.click_back_btn()
