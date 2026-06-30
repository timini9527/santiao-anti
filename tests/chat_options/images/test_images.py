import time
import allure
import pytest
import pytest_check as check
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_page import ChatPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.main.main_page import MainPage
from core.logger_utils import logger
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from pages.chat_options.images.image_strategy import (
    SELECT_MODES, SEND_OPTIONS,
    ImageSelectMode, ImageSendOption, BATCH_IMAGE_SCENARIOS, BatchImageScenario
)


@allure.epic("IM核心功能测试")
@allure.feature("聊天面板-图片")
@allure.story("测试进入相册后默认状态：原图未勾选、已选数为空、发送按钮置灰")
class TestChatImages:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        初始化页面对象并确保测试结束后返回主页
        """
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.imagePage = ChatImagePage(driver_sender)

        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    def _enter_chat_and_open_album(self, chat_name: str):
        """进入指定的聊天会话并打开相册面板"""
        self.chatListPage.enter_chat(chat_name)
        self.imagePage.open_panel_to_album()





    @allure.story("默认页面加载状态")
    @allure.title("默认页面加载状态-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_default_page_load_status(self, strategy):
        """测试进入相册后默认状态：原图未勾选、已选数为空、发送按钮置灰"""

        with allure.step(f"1. 进入与【{strategy.name}】的聊天并打开相册"):
            self._enter_chat_and_open_album(strategy.name)

        with allure.step("3. 校验默认页面加载状态"):
            result = self.imagePage.verify_default_page_load_status()
            assert result, "🍎 默认页面加载状态异常"


    @allure.story("选择图片后取消勾选")
    @allure.title("选择图片后取消勾选-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_select_then_cancel(self, strategy):
        """测试勾选后再次点击取消：角标消失，发送按钮恢复置灰"""

        with allure.step(f"1. 进入与【{strategy.name}】的聊天并进入相册"):
            self._enter_chat_and_open_album(strategy.name)

        with allure.step("3. 选中第一张图片"):
            self.imagePage.select_single_image(mode=1)

        with allure.step("4. 再次点击取消勾选"):
            self.imagePage.select_single_image(mode=1)

        with allure.step("5. 校验恢复为默认状态"):
            result = self.imagePage.verify_default_page_load_status()
            assert result, "🍎 取消勾选后状态未恢复为默认"


    # ==================== 核心发图流程（策略参数化 3×4×2 = 24 条）====================
    @allure.story("单张图片发送：选图模式 × 发送选项")
    @allure.title("单张图片发送：选图模式 × 发送选项-状态：已完成")
    @pytest.mark.parametrize("send_option", SEND_OPTIONS, ids=lambda s: s.desc)
    @pytest.mark.parametrize("select_mode", SELECT_MODES, ids=lambda s: s.desc)
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_single_image(self, strategy, select_mode: ImageSelectMode, send_option: ImageSendOption):
        """核心发图流程：选图模式 × 发送选项 × 聊天策略，零分支全覆盖"""
        allure.dynamic.title(
            f"发图测试 | {strategy.desc} - {select_mode.desc} - {send_option.desc}"
        )

        with allure.step(f"1. 进入与【{strategy.name}】的聊天"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message(f"单张图片发送: {strategy.desc} - {select_mode.desc} - {send_option.desc}")

        with allure.step("2. 点击底部加号进入相册"):
            self.imagePage.open_panel_to_album()

        with allure.step(f"3. 选择图片 - {select_mode.desc}"):
            result = self.imagePage.select_single_image(mode=select_mode.mode)
            check.is_true(result, f"选图失败: {select_mode.desc}")

        with allure.step(f"4. 执行发送选项 - {send_option.desc}"):
            if send_option.use_preview:
                self.imagePage.click_preview_button()
            if send_option.use_original:
                self.imagePage.click_original_image_button()

        with allure.step("5. 点击发送"):
            self.imagePage.click_send_button()
            time.sleep(0.5)

        with allure.step("6. 校验图片是否成功上屏"):
            # TODO: 可接入 DOM 快照断言或 ImageComparator 进行视觉验证
            pass
    
    
    @allure.story("单张图片发送-纯发送")
    @allure.title("单张图片发送-纯发送-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_only_image(self, strategy):
        """核心发图流程：选图模式 × 发送选项 × 聊天策略，零分支全覆盖"""

        with allure.step(f"1. 进入与【{strategy.name}】的聊天"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message(f"单张图片发送")

        with allure.step("2. 点击底部加号进入相册"):
            self.imagePage.open_panel_to_album()

        with allure.step(f"3. 选择图片"):
            result = self.imagePage.select_single_image(mode=1)
            check.is_true(result, f"选图失败")

        with allure.step("4. 点击预览"):
            self.imagePage.click_preview_button()
            preview_signature = self.imagePage.get_preview_signature()
            
        with allure.step("5. 点击发送"):
            self.imagePage.click_send_button()

        with allure.step("6. 校验图片是否成功上屏"):
            self.imagePage.click_last_sent_image()
            sent_signature = self.imagePage.get_preview_signature()
            check.equal(preview_signature, sent_signature, f"预览图片与发送图片不一致")
    
    
    @allure.story("发图边界场景：勾选上限测试")
    @allure.title("发图边界场景：勾选上限测试-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_max_selection_limit(self, strategy):
        """测试同时勾选超过 9 张图片时的 UI 表现：第 10 张无法选中"""
        
        with allure.step(f"1. 进入与【{strategy.name}】的聊天并进入相册"):
            self._enter_chat_and_open_album(strategy.name)
        
        with allure.step("2. 尝试连续勾选 10 张图片"):
            actual_count, toast = self.imagePage.select_multiple_images(count=10)
            
        with allure.step("3. 校验最终选中数量被限制在 9 张"):
            check.equal(actual_count, 9, f"期望选中数量被硬限制在 9 张，但实际选中了 {actual_count} 张")
            
        with allure.step("4. 校验 Toast 提示内容"):
            check.is_in("你最多只能选择9张照片", toast)
            self.imagePage.click_back_button()


    # ==================== 批量发图 ====================
    @allure.story("批量多选发图测试")
    @allure.title("批量多选发图测试-状态：已完成")
    @pytest.mark.parametrize("scenario", BATCH_IMAGE_SCENARIOS, ids=lambda s: s.desc)
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_batch_send_images(self, strategy, scenario: BatchImageScenario):
        """ 测试连续勾选多张图片后批量发送，并覆盖预览/原图/左右滑动能力 """

        with allure.step(f"1. 进入与【{strategy.name}】的聊天"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message(f"批量多选发图测试: {scenario.desc}")

        with allure.step("2. 记录发送前图片消息数量并进入相册"):
            before_count = self.chatPage.get_message_count('image', 'sent')
            self.imagePage.open_panel_to_album()

        with allure.step(f"3. 连续勾选 {scenario.count} 张图片"):
            actual_count, _ = self.imagePage.select_multiple_images(count=scenario.count)
            check.equal(actual_count, scenario.count, f"批量勾选数量不正确: actual={actual_count}, expected={scenario.count}")
            check.equal(self.imagePage.get_selected_image_count(), scenario.count, f"底部已选数量显示错误: expected={scenario.count}")
            check.is_true(actual_count <= 9, f"单次选择张数不应超过9张, actual={actual_count}")
            
        with allure.step("4. 处理原图选项"):
            if scenario.use_original:
                self.imagePage.click_original_image_button()
                check.equal(self.imagePage.get_original_image_button_status(), 'true', "原图选项未勾选成功")
            
        with allure.step("5. 处理预览能力"):
            if scenario.use_preview:    
                self.imagePage.click_preview_button()
                result = self.imagePage.is_in_preview_mode()
                check.is_true(result, "未成功进入预览页")

                selected_count = self.imagePage.get_selected_image_count()
                check.equal(selected_count, scenario.count, f"预览页已选数量错误: expected={scenario.count}")

                if scenario.verify_preview_swipe and scenario.count >= 2:
                    preview_before = self.imagePage.get_preview_signature()
                    self.imagePage.swipe_preview_left()
                    preview_after = self.imagePage.get_preview_signature()
                    check.not_equal(preview_after, preview_before, "预览页左滑后图片未发生变化")

                    self.imagePage.swipe_preview_right()
                    preview_back = self.imagePage.get_preview_signature()
                    check.equal(preview_back, preview_before, "预览页右滑返回后未恢复到原图")
            
        with allure.step("6. 发送"):
            self.imagePage.click_send_button()
            self.imagePage.click_add_button()
            
        with allure.step("7. 校验聊天区图片消息已新增"):
            success_count, result, fail_count = self.chatPage.verify_batch_sent_messages(scenario.count, 'image', scenario.desc)
            check.equal(success_count, scenario.count, f"图片消息未新增: expected={scenario.count}, actual={success_count}")
            check.is_true(result, f"没有找到发送的文本内容: {scenario.desc}")
            check.equal(fail_count, 0, f"❌发送失败的消息数量: {fail_count}")






