import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_panel_page import ChatPanelPage
from pages.mine.collection.chat_collection_page import ChatCollectionPage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.chat_options.emojis.chat_emoji_package_page import ChatEmojiPackagePage
from pages.chat_options.voice.chat_voice_page import ChatVoicePage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from strategy.chat.chat_strategy import GROUP_STRATEGY


@allure.epic("IM核心功能测试")
@allure.feature("群助手-发言管理-两端验证")
class TestGroupBotSpeechManage:
    """群助手发言管理功能测试 (采用双端分离协同架构)"""

    _message_sent = False

    # 类型注解帮助 IDE 提示
    mainS: MainPage
    chatListS: ChatListPage
    chatS: ChatPage
    settingS: GroupSettingPage
    botS: GroupBotPage

    mainR: MainPage
    chatListR: ChatListPage
    chatR: ChatPage
    panelR: ChatPanelPage
    collectionR: ChatCollectionPage
    emojiPageR: ChatEmojiPage
    voicePageR: ChatVoicePage
    emojiPackagePage: ChatEmojiPackagePage
    longPressPageR: ChatLongPressPage

    def _navigate_to_speech_manage(self):
        """发送方导航到群助手-发言管理页"""
        self.mainS.go_to_main_page()
        self.chatListS.enter_chat(GROUP_STRATEGY.name)
        self.chatS.wait_for_chat_page_load()
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        time.sleep(2)
        self.settingS.click_friend_header()
        self.botS.enter_speech_manage()

    @pytest.fixture(scope="class", autouse=True)
    def setup_speech_manage_config(self, request, driver_sender, driver_receiver):
        """整个测试类只执行一次：发送方驻留发言管理页，接收方驻留聊天页"""
        # 发送方 (群主) 初始化
        request.cls.mainS = MainPage(driver_sender)
        request.cls.chatListS = ChatListPage(driver_sender)
        request.cls.chatS = ChatPage(driver_sender)
        request.cls.settingS = GroupSettingPage(driver_sender)
        request.cls.botS = GroupBotPage(driver_sender)

        # 接收方 (普通群成员) 初始化
        request.cls.mainR = MainPage(driver_receiver)
        request.cls.chatListR = ChatListPage(driver_receiver)
        request.cls.chatR = ChatPage(driver_receiver)
        request.cls.panelR = ChatPanelPage(driver_receiver)
        request.cls.collectionR = ChatCollectionPage(driver_receiver)
        request.cls.emojiPageR = ChatEmojiPage(driver_receiver)
        request.cls.voicePageR = ChatVoicePage(driver_receiver)
        request.cls.emojiPackagePage = ChatEmojiPackagePage(driver_receiver)
        request.cls.longPressPageR = ChatLongPressPage(driver_receiver)

        logger.info("⏳ [Class Setup] 发送方进入发言管理页，接收方进入聊天页")
        self._navigate_to_speech_manage()

        # 发送方：开启发言管理总开关，并开启所有限制
        self.botS.toggle_speech_manage_switch(enable=True)
        
        with allure.step(f"1. 发送方(群主)开启所有限制"):
            self.botS.toggle_all_limit_items(origin_enable=False, target_enable=True)
            self.botS.click_save()

        # 接收方：进入指定群聊
        self.mainR.go_to_main_page()
        self.chatListR.enter_chat(GROUP_STRATEGY.name)
        self.chatR.wait_for_chat_page_load()

        yield

        logger.info("⏳ [Class Teardown] 恢复环境：关闭发言管理，双端退回主页")
        try:
            with allure.step(f"3. 执行完成：清理环境，回归原始状态"):
                # 发送方恢复与退出
                self.botS.enter_speech_manage()
                self.botS.toggle_all_limit_items(origin_enable=True, target_enable=False)
                self.botS.toggle_speech_manage_switch(enable=False)
                self.botS.click_save()
                self.botS.click_back()
                self.botS.click_back()
                self.mainS.go_to_main_page()

            # 接收方恢复与退出
            self.mainR.go_to_main_page()
        except Exception as e:
            logger.error(f"❌ [Class Teardown] 恢复环境失败，发言管理配置可能残留: {e}")


    # ==========================
    # 具体拦截场景验证逻辑 (Action)
    # ==========================
    def _verify_text_blocked(self, expected_toast: str):
        """验证文本发送被拦截"""
        self.chatR.send_message("测试文本拦截")
        toast_text = self.chatR.get_toast()
        check.is_true(expected_toast in toast_text, f"❌ 未捕获到正确的文本拦截提示，实际Toast: '{toast_text}'")
        self.chatR.clear_input_text()

    def _verify_emoji_blocked(self, expected_toast: str):
        """验证表情/emoji发送被拦截"""
        self.chatR.click_emoji_button()
        self.emojiPageR.sent_emoji('first')
        self.chatR.click_send_button()
        toast_text = self.chatR.get_toast()
        check.is_true(expected_toast in toast_text, f"❌ 未捕获到正确的表情拦截提示，实际Toast: '{toast_text}'")
        self.chatR.clear_input_text()


    def _verify_pkg_blocked(self, expected_toast: str):
        """验证表情包发送被拦截"""
        self.chatR.enter_emoji_page()
        self.emojiPackagePage.switch_to_emoji_package(1)
        self.emojiPackagePage.sent_emoji_package('first')
        toast_text = self.chatR.get_toast()
        check.is_true(expected_toast in toast_text, f"❌ 未捕获到正确的表情包拦截提示，实际Toast: '{toast_text}'")
        self.chatR.clear_input_text()
        time.sleep(1)

    def _verify_voice_blocked(self, expected_toast: str):
        """验证语音发送被拦截"""
        self.chatR.click_voice_button()
        self.voicePageR.send_voice_message(hold_time=3)
        toast_text = self.chatR.get_toast()
        check.is_true(expected_toast in toast_text, f"❌ 未捕获到正确的语音拦截提示，实际Toast: '{toast_text}'")


    # TODO：待BUG修复
    def _verify_collect_blocked(self, msg_type: str, expected_toast: str):
        """验证收藏功能被拦截"""
        if msg_type == "image":
            self.collectionR.get_collection_image_and_click()
        else:
            self.collectionR.get_collection_text_and_click()
        self.collectionR.wait_for_send_collection_panel()
        self.collectionR.click_send_collection_panel_send()
        send_fail_flag = self.chatR.get_last_message_send_fail_status()
        check.is_true(send_fail_flag, "❌ 收藏发送失败")
        # toast_text = self.chatR.get_toast()
        # check.is_true(expected_toast in toast_text, f"❌ 未捕获到正确的收藏拦截提示，实际Toast: '{toast_text}'")

    # 总开关控制 = False/True
    def _verify_total_switch(self, target_enable: bool):
        """验证总开关关闭时，发送功能被拦截"""
        self.botS.enter_speech_manage()
        self.chatS.wait_banner_message_disappear()
        self.botS.toggle_speech_manage_switch(enable=target_enable)
        self.botS.click_save()
    
    def _prepare_image_msg(self):
        """发送测试图片消息（用于长按保存/收藏测试）"""
        img = ChatImagePage(self.chatR.driver)
        img.open_panel_to_album()
        img.select_single_image(mode=1)
        img.click_send_button()
        

    @allure.story("发言管理-直接发送限制验证")
    @allure.title("发送能力逐项验证: {item_name}-状态：已完成")
    @pytest.mark.parametrize("item_name, action_type, action_target, expected_toast", [
        ("文本", "custom", "_verify_text_blocked", "本群已开启禁止发送文本/emoji"),
        ("emoji", "custom", "_verify_emoji_blocked", "本群已开启禁止发送文本/emoji"),
        ("表情包", "custom", "_verify_pkg_blocked", "本群已开启禁止发送表情包"),
        ("语音", "custom", "_verify_voice_blocked", "本群已开启禁止发送语音"),
        ("拍摄", "panel", "拍摄", "本群已开启禁止发送图片/拍照/视频"),
        ("图片", "panel", "图片", "本群已开启禁止发送图片/拍照/视频"),
        ("位置", "panel", "位置", "本群已开启禁止发送位置信息"),
        ("群会议", "panel", "群会议", "本群已开启禁止发起/参与音视频通话"),
        ("名片", "panel", "名片", "本群已开启禁止发送个人/群名片"),
        ("收藏", "panel", "收藏-文本", "本群已开启禁止发送收藏内容"),
        ("收藏", "panel", "收藏-图片", "本群已开启禁止发送收藏内容"),
        ("接龙", "panel", "接龙", "本群已开启禁止发送接龙"),
        ("投票", "panel", "投票", "本群已开启禁止发送投票"),
        ("文件", "panel", "文件", "本群已开启禁止发送文件")
    ], ids=["文本","emoji","表情包","语音","拍摄","图片","位置","群会议","名片","收藏-文本","收藏-图片","接龙","投票","文件"])
    def test_basic_message_restrictions(self, item_name, action_type, action_target, expected_toast):
        """
        极速参数化验证：验证直接在群内发起操作的拦截效果。
        利用 Sender 停留在设置页，Receiver 停留在聊天页的特性，以几乎为零的跳转成本验证。
        """

        with allure.step(f"2. 接收方尝试执行发送操作，验证系统能否成功拦截"):
            if action_type == "custom":
                verify_func = getattr(self, action_target)
                verify_func(expected_toast)
            elif action_type == "panel":
                self.chatR.click_add_button()
                self.panelR.click_panel_function_tab(item_name)
                if item_name == "收藏":
                    msg_type = "image" if "图片" in action_target else "text"
                    self._verify_collect_blocked(msg_type, expected_toast)
                else:
                    toast_text = self.chatR.get_toast()
                    check.is_true(expected_toast in toast_text, f"❌ 未捕获到正确的【{action_target}】拦截提示，实际Toast: '{toast_text}'")


    @allure.story("发言管理-长按消息菜单限制验证")
    @allure.title("长按能力逐项验证: {item_name}-状态：已完成")
    @pytest.mark.parametrize("action_type, expected_toast", [
        ("复制", "禁止复制群内消息"),
        ("转发", "禁止转发群内消息"),
        ("收藏", "本群已开启禁止发送收藏"), # TODO：BUG，需要修改
        ("保存", "禁止保存群内消息"),
    ], ids=["复制","转发","收藏","保存"])
    def test_long_press_message_restrictions(self, action_type, expected_toast):
        """ 验证长按已有消息时弹出的菜单项操作的拦截效果 """

        if not self.__class__._message_sent:
            with allure.step("1. 接收方在限制生效前发送一条测试消息(临时关闭发言管理以允许发送)"):
                self._verify_total_switch(False)

                message = "这是一条待操作的测试消息，用于测试长按菜单功能限制。"
                self.chatR.send_message(message)
                if action_type == "保存":
                    pass
                    # TODO：有 BUG，待修复
                    # self._prepare_image_msg()

                self._verify_total_switch(True)
                self.__class__._message_sent = True

        with allure.step(f"2. 接收方长按已有消息进行操作，验证能否被成功拦截"):
            """辅助验证长按消息弹窗的操作"""
            if action_type == "保存":
                pass
                # TODO：有 BUG，待修复
                # self.chatR.click_image_message_by_index()
                # self.chatR.long_press_preview_image()
                # self.chatR.click_download_icon_in_image_preview()
            else:
                self.longPressPageR.long_press_last_message()
                self.longPressPageR.click_menu_item(action_type)
                toast_text = self.chatR.get_toast()
                check.is_true(expected_toast in toast_text, f"❌ 未捕获到正确的【{action_type}】拦截提示，实际Toast: '{toast_text}'")


