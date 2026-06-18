import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.groups.setting.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from strategy.chat.chat_strategy import GROUP_STRATEGY


@allure.epic("IM核心功能测试")
@allure.feature("群助手-发言管理-两端验证")
class TestGroupBotSpeechManage:
    """群助手发言管理功能测试 (采用双端分离协同架构)"""

    # 类型注解帮助 IDE 提示
    mainS: MainPage
    chatListS: ChatListPage
    chatS: ChatPage
    settingS: GroupSettingPage
    botS: GroupBotPage

    mainR: MainPage
    chatListR: ChatListPage
    chatR: ChatPage

    def _navigate_to_speech_manage(self):
        """发送方导航到群助手-发言管理页"""
        self.mainS.go_to_main_page()
        self.chatListS.enter_chat(GROUP_STRATEGY.name)
        self.chatS.wait_for_chat_page_load()
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        self.settingS.click_group_manager()
        self.botS.enter_group_bot()
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

        logger.info("⏳ [Class Setup] 发送方进入发言管理页，接收方进入聊天页")
        self._navigate_to_speech_manage()

        # 发送方：开启发言管理总开关
        self.botS.toggle_switch(enable=True)
        self.botS.click_save()

        # 接收方：进入指定群聊
        self.mainR.go_to_main_page()
        self.chatListR.enter_chat(GROUP_STRATEGY.name)
        self.chatR.wait_for_chat_page_load()

        yield

        logger.info("⏳ [Class Teardown] 恢复环境：关闭发言管理，双端退回主页")
        try:
            # 发送方恢复与退出
            self.botS.toggle_switch(enable=False)
            self.botS.click_save()
            self.botS.go_back()
            self.botS.go_back()
            self.settingS.click_iv_back_button()
            self.mainS.go_to_main_page()

            # 接收方恢复与退出
            self.chatR.click_back_button()
            self.mainR.go_to_main_page()
        except Exception as e:
            logger.error(f"❌ [Class Teardown] 恢复环境失败，发言管理配置可能残留: {e}")

    def _toggle_limit_and_save(self, item_name: str, enable: bool):
        """内部方法：发送方切换特定的限制项并保存"""
        self.botS.toggle_limit_item(item_name, enable=enable)
        self.botS.click_save()

    # ==========================
    # 具体拦截场景验证逻辑 (Action)
    # ==========================

    def _verify_text_blocked(self):
        """验证文本发送被拦截"""
        self.chatR.send_message("测试文本拦截")
        toast_text = self.chatR.get_toast_text()
        check.is_true("禁止" in toast_text, f"❌ 未捕获到正确的文本拦截提示，实际Toast: '{toast_text}'")

    def _verify_emoji_blocked(self):
        """验证表情/emoji发送被拦截"""
        self.chatR.click_emoji_button()
        time.sleep(0.5)
        # 尝试点击面板上的第一组系统表情
        emoji_locator = (self.chatR.by.ANDROID_UIAUTOMATOR, 'newUiSelector().resourceIdMatches(".*emoji.*").instance(0)')
        try:
            self.chatR.click(emoji_locator)
        except Exception:
            pass
        toast_text = self.chatR.get_toast_text()
        check.is_true("禁止" in toast_text, f"❌ 未捕获到正确的表情拦截提示，实际Toast: '{toast_text}'")
        self.chatR.send_message("恢复面板状态")

    def _verify_voice_blocked(self):
        """验证语音发送被拦截"""
        # 尝试点击语音切换按钮
        self.chatR.click_voice_button()
        time.sleep(0.5)
        toast_text = self.chatR.get_toast_text()
        check.is_true("禁止" in toast_text, f"❌ 未捕获到正确的语音拦截提示，实际Toast: '{toast_text}'")
        # 点击文本输入框以恢复状态
        try:
            self.chatR.click((self.chatR.by.ANDROID_UIAUTOMATOR, 'newUiSelector().textContains("按住 说话")'))
        except Exception:
            pass
        self.chatR.send_message("恢复状态")

    def _click_add_panel_item_and_verify(self, btn_text: str, expect_keyword: str = "禁止"):
        """辅助验证加号面板里的各种功能按钮"""
        self.chatR.click_add_button()
        time.sleep(0.5)
        # 使用 Contains 以兼容 '相册' 或 '图片'、'音视频通话' 等不同命名
        btn_locator = (self.chatR.by.ANDROID_UIAUTOMATOR, f'newUiSelector().textContains("{btn_text}")')
        self.chatR.click(btn_locator)
        
        toast_text = self.chatR.get_toast_text()
        check.is_true(expect_keyword in toast_text, f"❌ 未捕获到正确的【{btn_text}】拦截提示，实际Toast: '{toast_text}'")
        
        # 发送文本以自动收起加号面板，确保环境干净
        self.chatR.send_message("恢复面板状态")

    def _verify_file_blocked(self):
        self._click_add_panel_item_and_verify("文件", "禁止")

    def _verify_image_blocked(self):
        self._click_add_panel_item_and_verify("相册", "禁止")

    def _verify_camera_blocked(self):
        self._click_add_panel_item_and_verify("拍摄", "禁止")

    def _verify_video_blocked(self):
        self._click_add_panel_item_and_verify("视频", "禁止")

    def _verify_location_blocked(self):
        self._click_add_panel_item_and_verify("位置", "禁止")

    def _verify_card_blocked(self):
        self._click_add_panel_item_and_verify("名片", "禁止")

    def _verify_voice_call_blocked(self):
        self._click_add_panel_item_and_verify("通话", "禁止")

    def _verify_solitaire_blocked(self):
        self._click_add_panel_item_and_verify("接龙", "禁止")

    def _verify_poll_blocked(self):
        self._click_add_panel_item_and_verify("投票", "禁止")

    # ==========================
    # 长按菜单辅助验证逻辑
    # ==========================

    def _long_press_action_and_verify(self, action_name: str):
        """辅助验证长按消息弹窗的操作"""
        self.chatR.send_message("这是一条待操作的测试消息")
        time.sleep(1)
        
        text_items = self.chatR.get_message_elements(msg_type="text", side='sent')
        if text_items:
            self.chatR.long_press(text_items[-1])
            time.sleep(1)
            menu_item = (self.chatR.by.ANDROID_UIAUTOMATOR, f'newUiSelector().text("{action_name}")')
            self.chatR.click(menu_item)

            toast_text = self.chatR.get_toast_text()
            check.is_true("禁止" in toast_text, f"❌ 未捕获到正确的【{action_name}】拦截提示，实际Toast: '{toast_text}'")
        else:
            pytest.fail("❌ 未能在聊天窗口中找到可长按的消息")

    def _verify_forward_blocked(self):
        self._long_press_action_and_verify("转发")

    def _verify_copy_blocked(self):
        self._long_press_action_and_verify("复制")

    def _verify_save_blocked(self):
        self._long_press_action_and_verify("保存")

    def _verify_collect_blocked(self):
        self._long_press_action_and_verify("收藏")

    @allure.story("发言管理-直接发送限制验证")
    @allure.title("发送能力逐项验证: {item_name}")
    @pytest.mark.parametrize("item_name, check_method_name", [
        ("文本", "_verify_text_blocked"),
        ("emoji", "_verify_emoji_blocked"),
        ("语音", "_verify_voice_blocked"),
        ("表情包", "_verify_emoji_blocked"),
        ("图片", "_verify_image_blocked"),
        ("拍照", "_verify_camera_blocked"),
        ("视频", "_verify_video_blocked"),
        ("位置", "_verify_location_blocked"),
        ("名片", "_verify_card_blocked"),
        ("文件", "_verify_file_blocked"),
        ("音视频通话", "_verify_voice_call_blocked"),
        ("接龙", "_verify_solitaire_blocked"),
        ("投票", "_verify_poll_blocked")
    ], ids=["文本","emoji","语音","表情包","图片","拍照","视频","位置","名片","文件","音视频通话","接龙","投票"])
    def test_basic_message_restrictions(self, item_name, check_method_name):
        """
        验证直接在群内发起消息的拦截效果
        利用 Sender 停留在设置页，Receiver 停留在聊天页的特性，以几乎为零的跳转成本验证
        """
        with allure.step(f"1. 发送方(群主)开启限制: 【{item_name}】"):
            self._toggle_limit_and_save(item_name, True)

        with allure.step(f"2. 接收方尝试执行发送操作，验证系统能否成功拦截"):
            verify_func = getattr(self, check_method_name)
            verify_func()

        with allure.step(f"3. 测试后置：发送方关闭限制: 【{item_name}】"):
            self._toggle_limit_and_save(item_name, False)

    @allure.story("发言管理-长按消息菜单限制验证")
    @allure.title("长按能力逐项验证: {item_name}")
    @pytest.mark.parametrize("item_name, check_method_name", [
        ("禁止复制群内消息", "_verify_copy_blocked"),
        ("禁止转发群内消息", "_verify_forward_blocked"),
        ("禁止保存群内消息", "_verify_save_blocked"),
        ("禁止收藏群内消息", "_verify_collect_blocked")
    ], ids=["复制","转发","保存","收藏"])
    def test_long_press_message_restrictions(self, item_name, check_method_name):
        """ 验证长按已有消息时弹出的菜单项操作的拦截效果 """

        with allure.step(f"1. 发送方(群主)开启限制: 【{item_name}】"):
            self._toggle_limit_and_save(item_name, True)

        with allure.step(f"2. 接收方长按已有消息进行操作，验证能否被成功拦截"):
            verify_func = getattr(self, check_method_name)
            verify_func()

        with allure.step(f"3. 测试后置：发送方关闭限制: 【{item_name}】"):
            self._toggle_limit_and_save(item_name, False)
