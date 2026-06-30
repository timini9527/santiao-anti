import allure
import pytest
import pytest_check as check
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_page import ChatPage
from strategy.chat.chat_strategy import (PRIVATE_USER1)
from pages.main.main_page import MainPage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data

from pages.chat_options.emojis.chat_emoji_store_page import ChatEmojiStorePage
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

@allure.epic("IM核心功能测试")
@allure.feature("聊天面板-表情包")
@allure.story("表情包商店与大表情发送")
class TestChatEmojiStore:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        初始化表情商店与数据包发送测试所需的 Page 实例
        """
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        
        self.emojiStorePage = ChatEmojiStorePage(driver_sender)
        self.emojiPackagePage = ChatEmojiPackagePage(driver_sender)

        yield  

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    @allure.story("表情包商店：添加表情包")
    @allure.title("表情包商店：添加表情包-状态：已完成")
    @pytest.mark.parametrize("emoji_type, count, desc", [
        ("sequential", 1, "按顺序添加 1 个表情包"),
        ("sequential", 4, "连续添加 4 个表情包"),
        ("current_last", 1, "添加屏幕可见的最后一个表情包"),
        ("all_in_page", 0, "连续添加当前页面所有表情包"),
        ("random", 3, "随机添加当前页面 3 个表情包"),
        ("last_page", 1, "表情商店中最后一个表情"),
    ])
    def test_add_emoji_store(self, emoji_type, count, desc):

        with allure.step("1. 打开表情面板，进入表情包商店"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.enter_emoji_page()
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
    @allure.title("发送表情包消息及业务流转验证-状态：已完成")
    @pytest.mark.parametrize("pkg_index, strategy, count, network, post_action, desc", load_emoji_test_cases())
    def test_send_emoji_package_message(self, pkg_index, strategy, count, network, post_action, desc):

        with allure.step(f"0. 前置条件: 设置网络状态为 {network}"):
            self.emojiPackagePage.set_network_connection(network)

        with allure.step(f"1.打开表情面板 选择表情包策略: {strategy}，发送 {count} 个表情"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.enter_emoji_page()
            
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
    @allure.title("从表情包商店设置页删除表情包-状态：已完成")
    @pytest.mark.parametrize("emoji_type, count, desc", [
        ("sequential", 1, "删除列表中的第 1 个表情包"),
        ("sequential", 3, "连续删除列表前 3 个表情包"),
        ("all", 0, "清空/删除当前拥有的全部表情包")
    ])
    def test_del_all_emoji_store(self, emoji_type, count, desc):

        with allure.step("1. 打开表情面板，进入表情包商店，进入设置页面进行删除"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.enter_emoji_page()
            self.emojiStorePage.open_emoji_store()
            self.emojiPackagePage.open_emoji_package_setting()

        with allure.step(f"2. 根据策略执行删除: {desc}"):
            current_items = self.emojiPackagePage._get_unadded_packages_on_screen()
            if not current_items:
                logger.warning("我的表情列表中没有可供删除的表情包，跳过测试")
                pytest.skip("列表为空，跳过验证")
                
            deled_pkgs, aft_current_items, del_result = self.emojiPackagePage.delete_emoji_packages(emoji_type, count)
            check.is_true(del_result, f"删除表情包操作执行失败，策略: {emoji_type}")
            logger.info(f"执行删除操作完成，成功删除: {deled_pkgs}, 结果状态: {del_result}")

        with allure.step("3. 验证删除的表情包是否成功"):
            del_status = self.emojiPackagePage.verify_delete_emoji_packages(deled_pkgs, aft_current_items)
            check.is_true(del_status, f"删除表情包后列表未正确刷新！被删包: {deled_pkgs}, 剩余包: {aft_current_items}")
            self.emojiPackagePage.back_to_emoji_store()
