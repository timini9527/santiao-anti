import pytest
import allure
import pytest_check as check
import time
from core.logger_utils import logger

from pages.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat_options.voice.chat_voice_page import ChatVoicePage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat_options.videos.chat_video_page import ChatVideoPage
from pages.chat_options.location.chat_position_page import ChatPositionPage
from pages.chat_options.file.chat_file_page import ChatFilePage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.chat_options.emojis.chat_emoji_store_page import ChatEmojiStorePage
from pages.chat_options.contact.chat_contact_card_page import ChatContactCardPage
from strategy.chat.chat_strategy import PRIVATE_USER1


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-单聊-多媒体与附件")
class TestSmokeChatOptions:
    """单聊发送各种多媒体与附件（语音、图片、视频、位置、文件、表情包、名片）冒烟用例"""

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.voicePage = ChatVoicePage(driver_sender)
        self.imagePage = ChatImagePage(driver_sender)
        self.videoPage = ChatVideoPage(driver_sender)
        self.positionPage = ChatPositionPage(driver_sender)
        self.filePage = ChatFilePage(driver_sender)
        self.emojiPage = ChatEmojiPage(driver_sender)
        self.emojiStorePage = ChatEmojiStorePage(driver_sender)
        self.contactCardPage = ChatContactCardPage(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception:
            pass

    @allure.story("发送语音消息")
    @allure.title("基础语音发送测试-状态：已完成")
    def test_voice_send_success(self):
        hold_time = 5
        strategy = PRIVATE_USER1

        with allure.step("1. 进入私聊并开启语音输入"):
            self.chatListPage.enter_chat(strategy.name)
            self.voicePage.click_voice_button()
            pre_snapshot = self.voicePage.get_voice_list_snapshot()

        with allure.step(f"2. 长按录音并发送 ({hold_time}秒)"):
            self.voicePage.send_voice_message(hold_time=hold_time)

        with allure.step("3. 校验语音消息显示"):
            is_success = self.voicePage.verify_voice_message_display(
                expected_time=hold_time, 
                pre_snapshot=pre_snapshot, 
                expect_sent=True
            )
            check.is_true(is_success, f"语音消息气泡未正常显示")

    @allure.story("发送图片消息")
    @allure.title("单张图片发送-纯发送-状态：已完成")
    def test_image_send_success(self):
        strategy = PRIVATE_USER1

        with allure.step("1. 进入会话并打开相册"):
            self.chatListPage.enter_chat(strategy.name)
            self.imagePage.open_panel_to_album()

        with allure.step("2. 选择单张图片并预览"):
            result = self.imagePage.select_single_image(mode=1)
            check.is_true(result, "勾选图片失败")
            self.imagePage.click_preview_button()
            preview_signature = self.imagePage.get_preview_signature()

        with allure.step("3. 点击发送图片并校验"):
            self.imagePage.click_send_button()
            self.imagePage.click_last_sent_image()
            sent_signature = self.imagePage.get_preview_signature()
            check.equal(preview_signature, sent_signature, "大图预览与发送出去的图片不一致")

    @allure.story("发送视频消息")
    @allure.title("单条视频发送并校验-状态：已完成")
    def test_video_send_success(self):
        strategy = PRIVATE_USER1

        with allure.step("1. 进入会话并打开视频选择"):
            self.chatListPage.enter_chat(strategy.name)
            self.videoPage.click_add_button()
            self.videoPage.click_image_button()
            self.videoPage.wait_for_image_page_load()

        with allure.step("2. 选择视频发送"):
            self.videoPage.select_single_video()
            self.videoPage.click_send_image()
            time.sleep(1)

        with allure.step("3. 校验视频上屏"):
            video_duration = self.chatPage.get_chat_video_duration(index=-1)
            check.is_true(bool(video_duration), "未检测到上屏视频消息的时长特征")

    @allure.story("发送位置消息")
    @allure.title("发送定位消息-状态：已完成")
    def test_position_send_success(self):
        strategy = PRIVATE_USER1

        with allure.step("1. 进入会话并打开位置"):
            self.chatListPage.enter_chat(strategy.name)
            self.positionPage.open_panel_to_location()

        with allure.step("2. 校验地图加载状态"):
            result = self.positionPage.verify_map_loading_status()
            check.is_true(result, "地图加载失败")

        with allure.step("3. 发送选中的位置信息"):
            self.positionPage.click_send_location_button()

        with allure.step("4. 验证聊天界面位置消息上屏"):
            time.sleep(0.5)
            is_present = self.chatPage.get_last_message_content_bubble_has_type(msg_type="position")
            check.is_true(is_present, "❌ 聊天屏幕上未找到发送的位置消息")

    @allure.story("发送文件消息")
    @allure.title("发送文件-正向流程-状态：已完成")
    def test_file_send_success(self):
        strategy = PRIVATE_USER1

        with allure.step("1. 进入会话并打开文件选择"):
            self.chatListPage.enter_chat(strategy.name)
            self.filePage.open_panel_enter_file_page()
            self.filePage.wait_for_file_page_load()

        with allure.step("2. 选择特定文件并发送"):
            self.filePage.click_file_menu_button()
            self.filePage.click_sub_menu_item("图片")
            self.filePage.select_any_file_in_dir(file_type='image')
            file_name = self.filePage.get_last_file_name_in_chat()
            self.filePage.click_send_file()

        with allure.step("3. 校验文件发送成功且上屏"):
            chat_file_names = self.chatPage.get_chat_all_file_name()
            check.is_true(file_name in chat_file_names, f"发送的文件名称 {file_name} 未在气泡中找到")

    @allure.story("发送表情包消息")
    @allure.title("发送表情包消息及业务流转验证-状态：已完成")
    def test_emoji_send_success(self):
        strategy = PRIVATE_USER1

        with allure.step("1. 进入会话并打开表情包面板"):
            self.chatListPage.enter_chat(strategy.name)
            self.emojiPage.click_emoji_button()
            self.emojiPage.wait_for_emoji_panel_load()

        with allure.step("2. 进入商店下载一个默认表情包（如不存在则使用现有）"):
            self.emojiPage.click_store_icon()
            self.emojiStorePage.wait_for_store_load()
            self.emojiStorePage.download_first_emoji_package()
            self.emojiStorePage.click_back_to_chat()

        with allure.step("3. 选择该表情包并发送"):
            self.emojiPage.select_downloaded_package(0)
            self.emojiPage.click_first_emoji_item()

        with allure.step("4. 验证表情消息发送上屏"):
            time.sleep(0.5)
            is_present = self.chatPage.get_last_message_content_bubble_has_type(msg_type="package")
            check.is_true(is_present, "❌ 聊天界面上未检测到发送的自定义表情包气泡")

    @allure.story("发送好友名片")
    @allure.title("发送好友名片-正向流程-状态：已完成")
    def test_contact_card_send_success(self):
        strategy = PRIVATE_USER1

        with allure.step("1. 进入会话并打开名片选择"):
            self.chatListPage.enter_chat(strategy.name)
            self.contactCardPage.open_panel_enter_card_page()
            self.contactCardPage.wait_for_card_page_load()

        with allure.step("2. 勾选指定的好友并发送"):
            self.contactCardPage.click_contact_by_name(strategy.name)
            self.contactCardPage.click_send_card_confirm()

        with allure.step("3. 校验名片消息已成功发送上屏"):
            time.sleep(0.5)
            is_present = self.chatPage.get_last_message_content_bubble_has_type(msg_type="card")
            check.is_true(is_present, "❌ 聊天界面上未检测到发送的名片消息气泡")
