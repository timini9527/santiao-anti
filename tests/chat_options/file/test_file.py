import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.chat.chat_list_page import ChatListPage 
from pages.chat.chat_page import ChatPage
from pages.chat_options.file.chat_file_page import ChatFilePage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY

@allure.epic("IM核心功能测试")
@allure.feature("聊天面板-文件")
@allure.story("测试在聊天中成功发送文件")
class TestChatFile:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.chatListPage = ChatListPage(driver_sender)
        self.chatFilePage = ChatFilePage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        
        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    def _enter_chat_and_open_file_page(self, chat_name: str):
        """进入指定的聊天会话并打开选择文件页面"""
        self.chatListPage.enter_chat(chat_name)
        self.chatFilePage.open_panel_enter_file_page()

    @allure.story("发送文件-正向流程")
    @allure.title("发送文件-正向流程-状态：已完成")
    @pytest.mark.parametrize("sub_menu_item, file_type, dir_name", [
        ("图片", 'image', "santiaoTalk"), 
        ("视频", 'video', "santiaoTalk"), 
        ("音频", 'audio', "Music"), 
        ("文档", 'document', "File")],
        # TODO：("下载",'download', "santiaoTalk"), 
        ids=["image", "video", "audio", "document"])
    @pytest.mark.parametrize("select_mode, target_index", [
        ("first", 0),
        ("last", 0),
        ("index", 1), 
        ("absolute_last", 0) 
    ], ids=["first_file", "last_file", "second_file", "absolute_last_file"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_file_success(self, strategy, sub_menu_item, file_type, dir_name, select_mode, target_index):
        """测试在聊天中成功发送文件"""
        allure.title(f"发送文件-正向流程【{strategy.desc}】- 模式: {select_mode}")
        
        with allure.step(f"1. 进入聊天并打开选择文件页"):
            self._enter_chat_and_open_file_page(strategy.name)
            assert self.chatFilePage.wait_for_file_page_load(), "❌ 未成功进入文件选择页面"

        with allure.step(f"2. 选择文件并发送 ({select_mode})"):
            self.chatFilePage.click_file_menu_button()
            self.chatFilePage.click_sub_menu_item(sub_menu_item)
            file_is_selected = self.chatFilePage.select_any_file_in_dir(
                primary_dir=dir_name,
                file_type=file_type,
                select_mode=select_mode, 
                target_index=target_index
            )
            check.is_true(file_is_selected, f"❌ 未成功选择文件 (模式: {select_mode})")
            self.chatFilePage.click_send_file()
            self.chatPage.click_add_button()

        with allure.step("3. 验证聊天气泡中是否存在文件消息"):
            self.chatPage.wait_for_chat_page_load()
            file_name = self.chatFilePage.get_last_file_name_in_chat()
            check.is_true(bool(file_name), "❌ 聊天气泡中未发现文件消息")
        
        with allure.step("4. 验证消息是否发送成功"):
            is_success = self.chatPage.wait_for_last_message_send_status()
            check.is_true(is_success, "❌ 消息未在规定时间内发送完成")


    @allure.story("发送文件-取消操作")
    @allure.title("发送文件-取消操作-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_cancel_send_file(self, strategy):
        """验证进入文件选择页后取消返回"""

        with allure.step(f"1. 进入聊天并打开选择文件页"):
            self._enter_chat_and_open_file_page(strategy.name)
            result = self.chatFilePage.wait_for_file_page_load()
            check.is_true(result, "❌ 未成功进入文件选择页面")
        
        with allure.step(f"2. 点击返回取消发送"):
            self.chatPage.back_to_chat_page()
            
        with allure.step(f"3. 验证正确返回聊天页面"):
            result = self.chatPage.verify_is_on_chat_page()
            check.is_true(result, "❌ 取消发送文件后，未能正确回到聊天页面")


    @allure.story("消息管理-文件撤回")
    @allure.title("消息管理-文件撤回-状态：未完成")
    @pytest.mark.skip(reason="UI元素匹配异常，待修复")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_revoke_file_message_success(self, strategy):
        """测试发送文件后 2 分钟内成功撤回"""
        allure.title(f"文件管理-成功撤回消息【{strategy.desc}】")

        with allure.step("1. 发送一个文件"):
            self._enter_chat_and_open_file_page(strategy.name)
            self.chatFilePage.wait_for_file_page_load()
            # 选择任意图片发送
            self.chatFilePage.select_any_file_in_dir(file_type='image')
            self.chatFilePage.click_send_file()
            # 确保消息已发送成功
            check.is_true(self.chatPage.wait_for_last_sent_message_completed(), "❌ 文件发送未能在规定时间内完成")

        with allure.step("2. 长按消息并点击撤回"):
            self.chatPage.long_press_last_message()
            self.chatPage.click_revoke()

        with allure.step("3. 验证撤回状态"):
            # 验证气泡消失，取而代之的是系统提示文本
            notice_text = self.chatPage.get_revoke_notice_text()
            check.is_in("撤回", notice_text, f"❌ 未能捕获到预期的撤回提示文字")
            logger.info(f"✅ 文件消息撤回验证通过: {notice_text}")


    @allure.story("发送异常-重试机制")
    @allure.title("发送异常-重试机制-状态：未完成")
    @pytest.mark.skip(reason="UI元素匹配异常，待修复")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_resend_file_on_fail(self, strategy):

        with allure.step("1. 发送文件（模拟环境异常）"):
            self._enter_chat_and_open_file_page(strategy.name)
            self.chatFilePage.wait_for_file_page_load()
            self.chatFilePage.select_any_file_in_dir(file_type='image')
            self.chatFilePage.click_send_file()
            
        with allure.step("2. 检查是否有失败红点并尝试重发"):
            # 监控是否出现失败标识
            has_fail = self.chatPage.get_last_message_send_fail_status()
            if has_fail:
                logger.info("🚩 检测到发送失败红点，准备执行重发")
                self.chatPage.click_last_message_resend_button()
                # 重发后再次等待完成
                success = self.chatPage.wait_for_last_sent_message_completed()
                check.is_true(success, "❌ 点击重发按钮后，消息仍未发送成功")
            else:
                logger.warning("⚠️ 当前环境网络太好，未触发发送失败场景，跳过重发点击步骤")
                # 如果没失败，至少验证消息是成功的
                check.is_true(self.chatPage.wait_for_last_sent_message_completed(), "❌ 消息发送状态异常")


    @allure.story("消息管理-文件删除")
    @allure.title("消息管理-文件删除-状态：未完成")
    @pytest.mark.skip(reason="删除功能待完善并接入通用交互逻辑")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_delete_file_message(self, strategy):
        pass


    @allure.story("消息管理-文件转发")
    @allure.title("消息管理-文件转发-状态：未完成")
    @pytest.mark.skip(reason="转发功能待完善并接入通用交互逻辑")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_forward_file_message(self, strategy):
        """验证文件消息可以被长按转发"""
        pass


    @allure.story("消息管理-文件收藏")
    @allure.title("消息管理-文件收藏-状态：未完成")
    @pytest.mark.skip(reason="收藏功能待完善并接入通用交互逻辑")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_favorite_file_message(self, strategy):
        """验证文件消息可以被长按收藏"""
        pass


    @allure.story("消息管理-文件引用回复")
    @allure.title("消息管理-文件引用回复-状态：未完成")
    @pytest.mark.skip(reason="回复功能待完善并接入通用交互逻辑")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_reply_file_message(self, strategy):
        """验证文件消息可以被长按引用回复"""
        pass
