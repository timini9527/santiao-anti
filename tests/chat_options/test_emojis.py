import allure
import pytest
import pytest_check as check
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_page import ChatPage
from strategy.chat.chat_strategy import (PRIVATE_USER1, SENDER_BUBBLE_STRATEGY)
from pages.main.main_page import MainPage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data

from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.chat_options.emojis.chat_emoji_store_page import ChatEmojiStorePage
from pages.chat_options.emojis.chat_emoji_manage_page import ChatEmojiManagePage
from pages.chat_options.emojis.chat_emoji_package_page import ChatEmojiPackagePage


def load_emoji_test_cases():
    """解析并提取表情包发送测试用的 YAML 数据"""
    try:
        data = load_yaml_data('chat_options/test_emojis_data.yaml')
        cases = []
        for item in data.get('send_emoji_package', []):
            cases.append((
                item.get('pkg_index'),
                item.get('strategy'),
                item.get('count'),
                item.get('network'),
                item.get('post_action'),
                item.get('desc')
            ))
        return cases
    except Exception as e:
        logger.error(f"加载表情包测试用例数据失败: {e}")
        return []


@allure.feature("表情包和表情")
@allure.story("发送表情包消息及业务流转验证")
class TestEmojis:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试类开始前，自动获取各类 Page 实例并绑定到 self
        """
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        
        self.emojiPage = ChatEmojiPage(driver_sender)
        self.emojiStorePage = ChatEmojiStorePage(driver_sender)
        self.emojiManagePage = ChatEmojiManagePage(driver_sender)
        self.emojiPackagePage = ChatEmojiPackagePage(driver_sender)

        yield  

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    def _enter_chat_and_open_emoji(self, name: str = PRIVATE_USER1.name):
        """进入指定聊天页面并打开表情面板"""
        self.chatListPage.enter_chat(name)
        self.chatPage.enter_emoji_page()

    """表情、表情包、表情包商店"""
    @allure.story("发送全部表情消息并验证")
    def test_send_all_emoji_message(self):
        with allure.step("1. 发送全部表情"):
            self._enter_chat_and_open_emoji()
            self.emojiPage.sent_all_emoji()
            input_text = self.chatPage.get_input_text()
            self.chatPage.click_send_button()

        with allure.step("2. 验证 表情UI显示"):
            active_text = self.chatPage.verify_message_content_by_input(input_text)
            check.equal(active_text, input_text, f"消息 actual: {active_text}, expected: {input_text} 不匹配")

    @allure.story("发送所有表情中的单个表情消息，验证1，8，当前页面随机一个，当前页面最后一个，最后一个")
    @pytest.mark.parametrize(
        "emoji_type", ["first", "eight", "random", "current_last", "absolute_last"]
    )
    def test_send_single_emoji_message(self, emoji_type):
        with allure.step("1. 发送单个表情"):
            self._enter_chat_and_open_emoji()
            self.chatPage.clear_input_text()
            self.emojiPage.sent_emoji(emoji_type)
            input_text = self.chatPage.get_input_text()
            self.chatPage.click_send_button()

        with allure.step("2. 验证表情UI显示"):
            active_text = self.chatPage.verify_message_content_by_input(input_text)
            check.equal(active_text, input_text, f"消息 actual: {active_text}, expected: {input_text} 不匹配")

    @allure.story("从所有发送新的表情消息，验证最近使用的表情是否添加上：1/8/16")
    @pytest.mark.parametrize("emoji_type, count, desc", [
        ("sequential", 1, "发送 1 个表情"),
        ("sequential", 8, "连续发送 8 个表情"),
        # ("sequential", 16, "连续发送 16 个表情"),
        ("random", 3, "随机发送 3 个表情")
    ])
    def test_send_new_emoji_to_later_message(self, emoji_type, count, desc):
        allure.dynamic.title(f"验证最近使用表情 - {desc}")
        with allure.step(f"1. {desc}"):
            self._enter_chat_and_open_emoji()
            self.chatPage.clear_input_text()
            self.emojiPage.sent_emoji(emoji_type, count)
            input_text = self.chatPage.get_input_text()
            input_list = self.emojiPage.str_to_emoji_list(input_text)
            self.mainPage.go_to_main_page()

        with allure.step(f"2. 验证最近使用的表情是否成功添加了 {count} 个"):
            self._enter_chat_and_open_emoji()
            self.emojiPage.sent_late_emoji(emoji_type, count)
            input_text_late = self.chatPage.get_input_text()
            input_list_late = self.emojiPage.str_to_emoji_list(input_text_late)
            check.is_true(
                set(input_list).issubset(set(input_list_late)),
                f"表情未成功添加到最近使用！发送的: {input_list}, 最近使用点出来的: {input_list_late}"
            )

    @allure.story("表情包商店：添加表情包")
    @pytest.mark.parametrize("emoji_type, count, desc", [
        ("sequential", 1, "按顺序添加 1 个表情包"),
        ("sequential", 4, "连续添加 4 个表情包"),
        ("current_last", 1, "添加屏幕可见的最后一个表情包"),
        ("all_in_page", 0, "连续添加当前页面所有表情包"),  # count=0 或 None 表示全部
        ("random", 3, "随机添加当前页面 3 个表情包"),
        ("last_page", 1, "表情商店中最后一个表情"),
    ])
    def test_add_emoji_store(self, emoji_type, count, desc):
        allure.dynamic.title(f"表情包商店测试 - {desc}")
        with allure.step("1. 打开表情面板，进入表情包商店"):
            self._enter_chat_and_open_emoji()
            self.emojiStorePage.open_emoji_store()

        with allure.step(f"3. 根据策略执行添加: {desc}"):
            added_pkg_names, add_status = self.emojiStorePage.add_emoji_packages(emoji_type, count)
            if not added_pkg_names:
                logger.warning("当前商店页面没有可供添加的表情包")
                pytest.skip("当前商店页面没有可供添加的表情包")
            if not add_status:
                logger.warning("添加表情包失败")
                pytest.skip("添加表情包失败")
            logger.info(f"本次操作成功添加了以下表情包: {added_pkg_names}")
            self.emojiStorePage.back_to_emoji_page()

        with allure.step("4. 验证添加的表情包是否成功"):
            verify_status = self.emojiStorePage.verify_added_packages(added_pkg_names)
            check.is_true(verify_status, f"添加的表情包未成功显示在表情面板中！添加的表情包: {added_pkg_names}")

    @allure.story("发送表情包消息及业务流转验证")
    @pytest.mark.parametrize("pkg_index, strategy, count, network, post_action, desc", load_emoji_test_cases())
    def test_send_emoji_package_message(self, pkg_index, strategy, count, network, post_action, desc):
        allure.dynamic.title(f"表情包核心业务 - {desc}")

        with allure.step(f"0. 前置条件: 设置网络状态为 {network}"):
            self.emojiPackagePage.set_network_connection(network)

        with allure.step(f"1.打开表情面板 选择表情包策略: {strategy}，发送 {count} 个表情"):
            self._enter_chat_and_open_emoji()
            
            if isinstance(pkg_index, list):
                sent_emoji_info = [] 
                for idx in pkg_index:
                    self.emojiPackagePage.switch_to_emoji_package(idx)
                    info = self.emojiPackagePage.sent_emoji_package(strategy, count)
                    if info: sent_emoji_info.extend(info)
            else:
                self.emojiPackagePage.switch_to_emoji_package(pkg_index)
                sent_emoji_info = self.emojiPackagePage.sent_emoji_package(strategy, count)

        with allure.step("2. 基础断言: 验证消息上屏与气泡渲染"):
            if network == "normal":
                verify_status = self.emojiPackagePage.verify_emoji_message_rendered(count)
            elif network == "offline":
                verify_status = self.chatPage.get_message_send_fail_status()
            check.is_true(verify_status, f"发送表情包后，聊天消息列表中未成功渲染大表情气泡")

    @allure.story("从表情包商店设置页删除表情包")
    @pytest.mark.parametrize("emoji_type, count, desc", [
        ("sequential", 1, "删除列表中的第 1 个表情包"),
        ("sequential", 3, "连续删除列表前 3 个表情包"),
        ("all", 0, "清空/删除当前拥有的全部表情包")
    ])
    def test_delete_all_emoji_store(self, emoji_type, count, desc):
        allure.dynamic.title(f"表情包商店删除表情包测试 - {desc}")

        with allure.step("1. 打开表情面板，进入表情包商店，进入设置页面进行删除"):
            self._enter_chat_and_open_emoji()
            self.emojiManagePage.open_emoji_store()
            self.emojiManagePage.open_emoji_package_setting()

        with allure.step(f"2. 根据策略执行删除: {desc}"):
            current_items = self.emojiManagePage._get_unadded_packages_on_screen()
            deleted_pkgs, aft_current_items, delete_result = self.emojiManagePage.delete_emoji_packages(emoji_type, count)
            
            if not delete_result:
                logger.warning("我的表情列表中没有可供删除的表情包或删除失败")
                pytest.skip("列表为空或删除失败，跳过验证")
            logger.info(f"执行删除操作成功，返回结果: {delete_result}")

        with allure.step("3. 验证删除的表情包是否成功"):
            check.is_true(delete_result, "删除表情包操作失败")
            del_status = self.emojiManagePage.verify_delete_emoji_packages(deleted_pkgs, aft_current_items)
            check.is_true(del_status, f"删除表情包后列表未更新，删除的包：{deleted_pkgs}，剩余包：{[p['name_str'] for p in aft_current_items]}")
            self.emojiManagePage.back_to_emoji_store()

    @allure.story("添加单个表情包")
    @pytest.mark.parametrize("pkg_count, add_count, desc", [
        (3, 1, "长按添加聊天列表中第1个表情包到收藏"),
        (3, None, "长按添加聊天列表中所有未收藏的表情包"),  # None 表示全部添加
    ])
    def test_add_single_emoji_package_to_coll(self, pkg_count, add_count, desc):
        allure.dynamic.title(f"在聊天页面中添加表情包到收藏夹 - {desc}")
        emoji_type = "single" 
        click_count = 1        

        with allure.step("0. 前置条件: 进入聊天页面，寻找表情包元素，并打开管理列表，获取已添加表情包的数量"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            empkg_elems, emoji_package_count_pre = self.emojiPackagePage.get_emoji_package_message_elements()
            self.chatPage.enter_emoji_page()
            self.emojiManagePage.open_collection_emoji_manage()
            coll_empkg_count_pre = self.emojiManagePage.get_collection_emoji_pkg_all_items()
        
        with allure.step(f"1. Tab栏表情包数量，有则切换到第 {click_count} 个表情包，没有则从商店添加"):
            tab_emoji_pkgs, added_empkg_count = self.emojiPage._get_top_tab_emoji_package_count()
            if added_empkg_count <= 0:
                logger.warning(f"我的表情列表中没有可供添加的表情包，将添加第 {pkg_count} 个表情包")
                self.emojiStorePage.open_emoji_store()
                added_pkg_names, add_status = self.emojiStorePage.add_emoji_packages(emoji_type, pkg_count)
                check.is_true(add_status, f"添加表情包操作失败，成功添加 {len(added_pkg_names)} 个，预期添加 {pkg_count} 个")
                self.emojiStorePage.back_to_emoji_store()
            self.emojiPackagePage.switch_to_emoji_package(click_count)

            # 根据 add_count 确定实际要添加的数量
            if add_count is None:
                emoji_list = self.emojiPage.get_visible_emojis()
                sent_count = len(emoji_list)
            else:
                sent_count = 1

        with allure.step(f"2. 聊天页面中有表情包则进行长按添加，没有则发送 {sent_count} 个表情包后再添加"):
            if add_count is None:
                # 处理“添加整个表情包”场景：执行带分页支持的原子级“发一个收藏一个”
                success_count, tried_count = self.emojiPackagePage.send_and_add_all_emojis_with_paging()
                add_count = tried_count  # 期望值为探测到的所有贴图总数
            else:
                if emoji_package_count_pre == 0:
                    logger.warning(f"当前聊天页面未找到任何表情包元素, 将发送 {sent_count} 个表情包")
                    self.emojiPackagePage.sent_emoji_package(emoji_type, sent_count)
                    self.chatPage.enter_emoji_page()
                    empkg_elems, emoji_package_count_aft = self.emojiPackagePage.get_emoji_package_message_elements()
                    add_count = emoji_package_count_aft
                
                success_count, status_dict = self.emojiPackagePage.long_press_emoji_package_and_add(empkg_elems[::-1], add_count)
            
            check.equal(success_count, add_count, f"添加表情包操作失败，成功添加 {success_count} 个，预期添加 {add_count} 个")

        with allure.step("3. 验证添加的表情包是否成功"):
            if emoji_package_count_pre == 0:
                self.chatPage.enter_emoji_page()
            self.emojiManagePage.open_collection_emoji_manage()
            coll_empkg_count_aft = self.emojiManagePage.get_collection_emoji_pkg_all_items()
            check.equal(coll_empkg_count_aft, coll_empkg_count_pre + success_count, 
                        f"添加的表情包未成功显示在表情面板中！添加前：{coll_empkg_count_pre}，添加后：{coll_empkg_count_aft}，预期添加：{success_count}")



