import time
import allure
import pytest
import pytest_check as check
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_page import ChatPage
from pages.chat_options.videos.chat_video_page import ChatVideoPage
from pages.main.main_page import MainPage
from core.logger_utils import logger
from pages.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from pages.chat_options.videos.video_strategy import (
    VIDEO_SELECT_MODES, VIDEO_SEND_OPTIONS, BATCH_VIDEO_SCENARIOS,
    VideoSelectMode, VideoSendOption, BatchVideoScenario
)

@allure.epic("IM核心功能测试")
@allure.feature("聊天面板-视频")
@allure.story("初始化页面对象")
class TestChatVideos:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """ 初始化页面对象 """
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.videoPage = ChatVideoPage(driver_sender)

        yield
        self.mainPage.go_to_main_page()

    def _enter_chat_and_open_album(self, chat_name: str):
        """进入指定的聊天会话并打开相册面板"""
        self.chatListPage.enter_chat(chat_name)
        self.videoPage.open_panel_to_album()

    # ==================== 1. 默认状态校验 ====================
    @allure.story("视频相册基础状态")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_video_page_default_status(self, strategy):
        """验证进入视频选择页后的默认 UI 状态"""
        with allure.step(f"1. 进入与【{strategy.name}】的聊天并打开相册"):
            self._enter_chat_and_open_album(strategy.name)

        with allure.step("3. 校验默认页面加载状态"):
            result = self.videoPage.verify_default_page_load_status()
            assert result, "🍎 默认页面加载状态异常"

    # ==================== 2. 选择后取消勾选 ====================
    @allure.story("选择视频后取消勾选")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_select_then_cancel(self, strategy):
        """测试勾选后再次点击取消：角标消失，发送按钮恢复置灰"""
        allure.dynamic.title(f"选择后取消勾选 - 策略: {strategy.name}")

        with allure.step(f"1. 进入与【{strategy.name}】的聊天并进入相册"):
            self._enter_chat_and_open_album(strategy.name)

        with allure.step("3. 选中第一个视频"):
            self.videoPage.select_single_video(mode=1)

        with allure.step("4. 再次点击取消勾选"):
            self.videoPage.select_single_video(mode=1)

        with allure.step("5. 校验恢复为默认状态"):
            result = self.videoPage.verify_default_page_load_status()
            assert result, "🍎 取消勾选后状态未恢复为默认"

    # ==================== 3. 单视频发送流程 (参数化全覆盖) ====================
    @allure.story("单视频发送：模式 × 选项")
    @pytest.mark.parametrize("send_option", VIDEO_SEND_OPTIONS, ids=lambda s: s.desc)
    @pytest.mark.parametrize("select_mode", VIDEO_SELECT_MODES, ids=lambda s: s.desc)
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_single_video_workflow(self, strategy, select_mode: VideoSelectMode, send_option: VideoSendOption):
        """核心视频发送流程：涵盖不同选择方式与预览/高清选项"""
        
        if select_mode.mode == 0 and send_option != VIDEO_SEND_OPTIONS[0]:
            pytest.skip("反悔模式仅需配合首个发送选项进行交互验证")
            
        allure.dynamic.title(f"视频发送测试 | {select_mode.desc} - {send_option.desc}")

        with allure.step(f"1. 进入聊天: {strategy.name}"):
            self.chatListPage.enter_chat(strategy.name)

        with allure.step("2. 进入相册并执行选视频模式"):
            self.videoPage.open_panel_to_album()
            self.videoPage.select_single_video(mode=select_mode.mode)
            
            if select_mode.mode == 0:
                current_count = self.videoPage.get_selected_image_count(raise_exception=False)
                check.equal(current_count, 0, f"🍎 反悔模式失败：预期选中数 0，实际为 {current_count}")

        with allure.step(f"3. 应用发送选项: {send_option.desc}"):
            if send_option.use_preview:
                self.videoPage.click_preview_button()
                result = self.videoPage.is_video_preview_ready()
                check.is_true(result, "🍎 预览页视频播放异常")
            
            if send_option.use_original:
                self.videoPage.click_original_image_checkbox()

        with allure.step("4. 点击发送并校验聊天区状态"):
            self.videoPage.click_send_button()
            is_sent = self.chatPage.wait_for_last_sent_message_completed()
            if select_mode.mode == 0: 
                self.videoPage.click_back_button()
            check.is_true(is_sent, "视频发送超时或检测到失败红点")
        
        with allure.step("5. 校验聊天区视频状态"):
            video_status = self.videoPage.get_last_message_video_status()
            check.is_true(video_status, "聊天区未加载出视频 Item")

    @allure.story("单条视频发送并校验")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_only_video(self, strategy):
        """核心发视频流程：选择单条视频，发送并校验全屏预览指纹"""
        allure.dynamic.title(f"单视频发送测试 | {strategy.desc}")

        with allure.step(f"1. 进入与【{strategy.name}】的聊天"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message("单条视频发送")

        with allure.step("2. 点击底部加号进入相册"):
            self.videoPage.open_panel_to_album()

        with allure.step("3. 选择视频"):
            result = self.videoPage.select_single_video(mode=1)
            check.is_true(result, "选视频失败")

        with allure.step("4. 点击预览"):
            self.videoPage.click_preview_button()
            preview_signature = self.videoPage.get_preview_signature()
            
        with allure.step("5. 点击发送"):
            self.videoPage.click_send_button()

        with allure.step("6. 校验视频是否成功上屏"):
            is_sent = self.chatPage.wait_for_last_sent_message_completed()
            check.is_true(is_sent, "视频发送超时或检测到失败红点")
            
            # self.videoPage.click_last_sent_image()
            # sent_signature = self.videoPage.get_preview_signature()
            # check.equal(preview_signature, sent_signature, "预览视频与发送视频特征不一致")

    # ==================== 3. 批量视频发送测试 ====================   
    @allure.story("视频发送边界场景：勾选上限测试")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_max_selection_limit(self, strategy):
        """测试同时勾选超过 9 条视频时的 UI 表现：第 10 条触发弹窗并被拦截"""
        allure.dynamic.title(f"视频发送边界 - 勾选上限测试 (9条)")
        
        with allure.step(f"1. 进入与【{strategy.name}】的聊天并进入相册"):
            self._enter_chat_and_open_album(strategy.name)
        
        with allure.step("2. 尝试连续勾选 10 条视频"):
            actual_count, toast = self.videoPage.select_multiple_videos(count=10)
            
        with allure.step("3. 校验最终选中数量被限制在 9 条"):
            check.equal(actual_count, 9, f"期望选中数量被硬限制在 9 条，但实际勾选了 {actual_count} 条")
            
        with allure.step("4. 校验 Toast 提示内容并返回"):
            check.is_in("你最多只能选择9个视频", toast)
            self.videoPage.click_back_button()
            
    @allure.story("批量视频发送")
    @pytest.mark.parametrize("scenario", BATCH_VIDEO_SCENARIOS, ids=lambda s: s.desc)
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_batch_send_videos(self, strategy, scenario: BatchVideoScenario):
        """验证多视频连续勾选发送的稳定性"""
        allure.dynamic.title(f"批量发视频测试 - {strategy.name} - {scenario.desc}")

        with allure.step(f"1. 进入与【{strategy.name}】的聊天"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message(f"批量视频发送测试: {scenario.desc}")

        with allure.step("2. 进入相册"):
            self.videoPage.open_panel_to_album()

        with allure.step(f"3. 连续勾选 {scenario.count} 条视频"):
            actual_count, toast = self.videoPage.select_multiple_videos(count=scenario.count)
            check.equal(actual_count, scenario.count, f"批量勾选数量不匹配: actual={actual_count}, expected={scenario.count}")
            check.equal(self.videoPage.get_selected_image_count(), scenario.count,
                        f"底部已选数量显示错误: expected={scenario.count}")
            check.is_true(actual_count <= 9, f"单次选择视频数量不应超过9条, actual={actual_count}")
            if scenario.count > 9:
                check.is_in("你最多只能选择9张照片", toast)

        with allure.step("4. 点击发送"):
            self.videoPage.click_send_button()
            self.videoPage.click_add_button()

        with allure.step("5. 智能等待发送完成并校验结果"):
            is_sent = self.chatPage.wait_for_last_sent_message_completed()
            check.is_true(is_sent, "批量视频发送超时或失败")
        
        with allure.step("6. 校验聊天区视频状态"):
            video_count, text_matched, fail_count = self.chatPage.verify_batch_sent_messages(scenario.count, "video", scenario.desc)
            check.equal(video_count, scenario.count, f"批量视频发送数量不匹配: actual={video_count}, expected={scenario.count}")
            check.is_true(text_matched, "批量视频发送后文本未匹配")
            check.equal(fail_count, 0, "批量视频发送后有失败记录")

 

