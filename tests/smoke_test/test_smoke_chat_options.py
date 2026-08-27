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
from pages.chat_options.emojis.chat_emoji_package_page import ChatEmojiPackagePage
from pages.friend.profile.chat_contact_card_page import ChatContactCardPage
from pages.common.contact_select_page import ContactSelectPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2

class BaseSmokeChatOptions:
    """单聊多媒体与附件测试基类"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
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
        self.emojiPackagePage = ChatEmojiPackagePage(driver_sender)
        self.contactCardPage = ChatContactCardPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception:
            pass

@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-单聊-多媒体与附件')
class TestSmokeChatOptions(BaseSmokeChatOptions):
    """单聊发送各种多媒体与附件（语音、图片、视频、位置、文件、表情包、名片）冒烟用例"""

    @allure.story('发送语音消息')
    @allure.title('基础语音发送测试-状态：已完成')
    def test_voice_send_success(self):
        hold_time = 5
        with allure.step('1. 进入私聊并开启语音输入'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.voicePage.click_voice_button()
            pre_snapshot = self.voicePage.get_voice_list_snapshot()
        with allure.step(f'2. 长按录音并发送 ({hold_time}秒)'):
            self.voicePage.send_voice_message(hold_time=hold_time)
        with allure.step('3. 校验语音消息显示'):
            is_success = self.voicePage.verify_voice_message_display(expected_time=hold_time, pre_snapshot=pre_snapshot, expect_sent=True)
            check.is_true(is_success, f'语音消息气泡未正常显示')

    @allure.story('发送图片消息')
    @allure.title('单张图片发送-纯发送-状态：已完成')
    def test_image_send_success(self):
        with allure.step('1. 进入会话并打开相册'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.imagePage.open_panel_to_album()
        with allure.step('2. 选择单张图片并预览'):
            result = self.imagePage.select_single_image(mode=1)
            check.is_true(result, '勾选图片失败')
            self.imagePage.click_preview_button()
            preview_signature = self.imagePage.get_preview_signature()
        with allure.step('3. 点击发送图片并校验'):
            self.imagePage.click_send_button()
            self.imagePage.click_last_sent_image()
            time.sleep(0.5)
            sent_signature = self.imagePage.get_preview_signature()
            from utils.cv_recognition.screenshot_utils import ScreenshotUtils
            distance = ScreenshotUtils.hamming_distance(preview_signature, sent_signature)
            logger.info(f'📊 [Image Hash Compare] 发送前 Hash: {preview_signature}, 发送后 Hash: {sent_signature}, 汉明距离: {distance}')
            check.is_true(distance <= 5, f'大图预览与发送出去的图片不一致 (汉明距离 {distance} > 5)')

    @allure.story('发送视频消息')
    @allure.title('单条视频发送并校验-状态：已完成')
    def test_video_send_success(self):
        with allure.step('1. 进入会话并打开视频选择'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.videoPage.open_panel_to_album()
        with allure.step('2. 选择视频发送'):
            self.videoPage.select_single_video(mode=1)
            self.videoPage.click_send_button()
        with allure.step('3. 校验视频上屏'):
            video_duration = self.chatPage.get_chat_video_duration(index=-1)
            check.is_true(bool(video_duration), '未检测到上屏视频消息的时长特征')

    @allure.story('发送位置消息')
    @allure.title('发送定位消息-状态：已完成')
    def test_position_send_success(self):
        with allure.step('1. 进入会话并打开位置'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.positionPage.open_panel_enter_location_page()
        with allure.step('2. 获取当前选中的 POI 信息并发送'):
            self.positionPage.click_current_location_button()
            poi_title, poi_detail = self.positionPage.get_selected_location_info()
            check.is_true(poi_title and poi_detail, '未获取到位置信息')
            self.positionPage.click_send_button()
            check.is_true(self.chatPage.verify_is_on_chat_page(), '未成功返回聊天页面')
        with allure.step('3. 验证聊天气泡内容'):
            check.is_true(self.chatPage.wait_for_last_message_send_status(), '测试发送位置失败，发送位置状态异常')
            actual_bubble = self.chatPage.verify_location_sent_status()
            check.is_in(poi_title, actual_bubble['title'], f"测试发送位置失败，地域匹配失败! Exp: 截取区域[{poi_title}] 未出现在, Act: 气泡地址[{actual_bubble['title']}] 中")
            check.equal(poi_detail, actual_bubble.get('detail_address'), f"发送位置 Exp: {poi_detail}, Act: {actual_bubble.get('detail_address')} 不匹配")
        with allure.step('4. 验证地图显示'):
            self.chatPage.verify_location_enter_map_detail()
            result = self.positionPage.verify_map_location_info(poi_title, poi_detail)
            check.is_true(result, f'发送位置 {poi_title} {poi_detail} 地图显示位置信息不一致')
            self.chatPage.click_top_back_bnt()

    @allure.story('发送文件消息')
    @allure.title('发送文件-正向流程-状态：已完成')
    def test_file_send_success(self):
        with allure.step('1. 进入会话并打开文件选择'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.filePage.open_panel_enter_file_page()
            self.filePage.wait_for_file_page_load()
        with allure.step('2. 搜索并选择固定文件发送'):
            file_name = '测试-图片'
            self.filePage.search_and_select_file_by_name(file_name)
        with allure.step('3. 校验文件发送成功且上屏'):
            chat_file_names = self.chatPage.get_chat_all_file_name()
            is_contained = any(file_name in name for name in chat_file_names)
            check.is_true(is_contained, f'发送的文件名称 {file_name} 未在气泡中找到')

    @allure.story('发送基础小表情消息')
    @allure.title('发送基础小表情消息-正向流程-状态：已完成')
    def test_basic_emoji_send_success(self):
        with allure.step('1. 进入会话并打开表情面板'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.enter_emoji_page()
            self.chatPage.clear_input_text()
        with allure.step('2. 选择第一个基础小表情'):
            self.emojiPage.sent_emoji('first')
            input_text = self.chatPage.get_input_text()
            check.is_true(bool(input_text), '❌ 未能在输入框中成功键入基础表情代号')
        with allure.step('3. 点击发送并校验上屏显示'):
            self.chatPage.click_send_button()
            active_text = self.chatPage.verify_message_content_by_input(input_text)
            check.equal(active_text, input_text, f'❌ 表情上屏文本不匹配！Act: {active_text}, Exp: {input_text}')

    @allure.story('发送表情包消息')
    @allure.title('发送表情包消息及业务流转验证-状态：已完成')
    def test_emoji_send_success(self):
        pkg_index = 1
        send_strategy = 'first'
        send_count = 1
        network = 'normal'
        with allure.step(f'0. 前置条件: 设置网络状态为 {network}'):
            self.emojiPackagePage.set_network_connection(network)
        with allure.step('1. 进入会话并打开表情包面板'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatPage.enter_emoji_page()
        with allure.step('2. 确保存在可发送的表情包'):
            self.emojiPackagePage._find_panel()
            _, package_count = self.emojiPackagePage._get_top_tab_emoji_package_count()
            if package_count == 0:
                self.emojiStorePage.open_emoji_store()
                added_pkg_names, add_status = self.emojiStorePage.add_emoji_packages('sequential', 1)
                if not added_pkg_names:
                    logger.warning('当前商店页面没有可供添加的表情包')
                    pytest.skip('当前商店页面没有可供添加的表情包')
                if not add_status:
                    logger.warning('添加表情包失败')
                    pytest.skip('添加表情包失败')
                self.emojiStorePage.back_to_emoji_page()
        with allure.step(f'3. 选择第 {pkg_index} 个表情包并发送 {send_count} 个贴图'):
            switch_status = self.emojiPackagePage.switch_to_emoji_package(pkg_index)
            check.is_true(switch_status, f'切换到第 {pkg_index} 个表情包失败')
            sent_emoji_info = self.emojiPackagePage.sent_emoji_package(send_strategy, send_count)
            check.is_true(sent_emoji_info, '未成功点击发送任何表情包贴图')
        with allure.step('4. 验证表情消息发送上屏并正确渲染'):
            verify_status = self.emojiPackagePage.verify_emoji_message_rendered(send_count)
            check.is_true(verify_status, '❌ 发送表情包后，聊天消息列表中未成功渲染大表情气泡')

    @allure.story('发送好友名片')
    @allure.title('发送好友名片-正向流程-状态：已完成')
    def test_contact_card_send_success(self):
        with allure.step('1. 进入会话并打开名片选择页'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.contactCardPage.open_panel_enter_contact_card_page()
            is_loaded = self.contactSelectPage.wait_for_contact_select_page_load()
            check.is_true(is_loaded, '❌ 名片联系人选择页加载失败')
        with allure.step(f'2. 选择好友名片并确认发送：{PRIVATE_USER2.name}'):
            is_selected = self.contactSelectPage.click_contact_by_name(name=PRIVATE_USER2.name)
            check.is_true(is_selected, f'❌ 未能成功选择好友名片 {PRIVATE_USER2.name}')
            self.contactSelectPage.click_confirm()
            self.chatPage.click_add_button()
        with allure.step('3. 验证聊天气泡内容显示'):
            result, card_info = self.chatPage.verify_card_in_chat(PRIVATE_USER2.name)
            check.is_true(result, f'❌ 聊天气泡中未发现好友 {PRIVATE_USER2.name} 的名片')
        with allure.step('4. 点击最后一条名片消息进入资料详情页'):
            self.chatPage.click_last_card_message()
        with allure.step('5. 验证资料详情页信息'):
            is_success = self.contactDetailPage.verify_is_on_detail_page(card_info)
            check.is_true(is_success, '❌ 未进入资料详情页或信息不匹配')
        with allure.step('6. 点击发送消息回到聊天页面'):
            self.contactDetailPage.click_send_message()
            check.is_true(self.chatPage.wait_for_chat_page_load(), '❌ 未能成功返回聊天页面')
            chat_object_title = self.chatPage.get_top_name()
            check.equal(chat_object_title, PRIVATE_USER2.name, f'❌ 返回聊天页面后，聊天对象名称与预期不匹配 {chat_object_title}')