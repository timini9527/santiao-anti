import allure
import pytest
import pytest_check as check
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat_options.voice.chat_voice_page import ChatVoicePage
from pages.main.main_page import MainPage
from core.logger_utils import logger
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY


@allure.epic("IM核心功能测试")
@allure.feature("聊天面板-语音")
@allure.story("测试按住说话并发送语音的功能")
class TestChatVoice:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        初始化页面对象并确保测试结束后返回主页
        """
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.voicePage = ChatVoicePage(driver_sender)

        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    def _enter_chat_and_enable_voice(self, chat_name: str):
        """进入指定的聊天会话并开启语音输入模式"""
        self.chatListPage.enter_chat(chat_name)
        self.voicePage.click_voice_button()



    @allure.story("基础语音发送测试")
    @allure.title("基础语音发送测试-状态：已完成")
    @pytest.mark.parametrize("hold_time", [0, 1, 30, 59, 60, 61, 65])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_basic_voice_send(self, strategy, hold_time):
        """测试按住说话并发送语音的功能"""
        allure.dynamic.title(f"基础语音发送测试 - 策略: {strategy.name}, 悬停时间: {hold_time}秒")

        with allure.step(f"1. 进入与【{strategy.name}】的私聊并开启语音模式"):
            self._enter_chat_and_enable_voice(strategy.name)
        
        with allure.step("2. 【关键】获取操作前的聊天列表快照"):
            # 在按住语音按钮之前，给现在的列表拍个照
            pre_snapshot = self.voicePage.get_voice_list_snapshot() 

        with allure.step(f"3. 长按语音按钮进行录制并发送 ({hold_time}秒)"):
            send_result = self.voicePage.send_voice_message(hold_time=hold_time)

            # 校验场景 A：录音时间太短 (0秒)
            if hold_time == 0:
                check.equal(send_result["toast"], "说话时间太短", f"短录音提示失败，实际toast为: {send_result['toast']}")
            
            # 校验场景 B：录音超过 50 秒，验证红色倒计时提示
            elif hold_time >= 50:
                warning = send_result["warning_text"]
                check.is_true("秒后将发送" in warning, f"未出现倒计时警告，或文案不匹配！实际抓取到: {warning}")

        with allure.step("3. 校验语音消息上屏状态及展示时长"):
            if hold_time > 0:
                hold_time = 60 if hold_time > 60 else hold_time
                is_success = self.voicePage.verify_voice_message_display(
                    expected_time=hold_time, 
                    pre_snapshot=pre_snapshot, 
                    expect_sent=True
                )
                check.is_true(is_success, f"语音气泡显示异常！预期时长应为 {hold_time} 秒")


    @allure.story("语音录制取消测试")
    @allure.title("语音录制取消测试-状态：已完成")
    @pytest.mark.parametrize("press_time", [1])
    @pytest.mark.parametrize("hold_time", [5])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_voice_record_cancel(self, strategy, press_time, hold_time):
        """测试录音过程中取消发送"""
        allure.dynamic.title(f"语音录制取消测试 - 策略: {strategy.name}, 悬停时间: {hold_time}秒")
        
        with allure.step(f"1. 进入与【{strategy.name}】的私聊并开启语音模式"):
            self._enter_chat_and_enable_voice(strategy.name)
            
        with allure.step("2. 【关键】获取操作前的聊天列表快照"):
            # 在按住语音按钮之前，给现在的列表拍个照
            pre_snapshot = self.voicePage.get_voice_list_snapshot() 

        with allure.step("3. 长按语音并滑动到取消发送区域，悬停 10 秒"):
            # 调用底层神技：自动完成侦察、滑动、悬停和监听
            listen_result = self.voicePage.verify_voice_message_cancel(press_time=press_time, hold_time=hold_time)
            # 断言一：在悬停的 10 秒内，屏幕上是否出现了那四个字
            check.is_true(listen_result, "❌ 悬停在取消发送按钮上时，未出现『松开 取消发送』的红框提示文案！")
        
        with allure.step("4. 校验松手后是否成功取消发送, 页面是否有语音刚刚的语音消息"):
            expected_cancel_time = hold_time + press_time
            is_success = self.voicePage.verify_voice_message_display(
                    expected_time=expected_cancel_time, 
                    pre_snapshot=pre_snapshot, 
                    expect_sent=False
                )
            check.is_true(is_success, f"语音气泡显示异常！预期时长应为 {expected_cancel_time} 秒")


    @allure.story("语音进阶交互：滑动试听测试并操作(发送/取消)，并验证")
    @allure.title("语音进阶交互：滑动试听测试并操作(发送/取消)，并验证-状态：已完成")
    @pytest.mark.parametrize("action", ["send", "cancel"], ids=["发送", "取消"])
    @pytest.mark.parametrize("press_time", [1])
    @pytest.mark.parametrize("hold_time", [5])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_voice_swipe_to_preview_and_action(self, strategy, action, press_time, hold_time):
        """测试按住语音按钮并滑动到试听区域，验证提示语及状态切换，并能够进行发送或取消操作"""
        allure.dynamic.title(f"语音进阶交互测试 - 策略: {strategy.name}, 悬停时间: {hold_time}秒")

        with allure.step(f"1. 进入与【{strategy.name}】的私聊并开启语音模式"):
            self._enter_chat_and_enable_voice(strategy.name)
        
        with allure.step("2. 【关键】获取操作前的聊天列表快照"):
            # 在按住语音按钮之前，给现在的列表拍个照
            pre_snapshot = self.voicePage.get_voice_list_snapshot() 
            
        with allure.step("3. 长按语音并滑动到试听区域，悬停 10 秒"):
            # 调用底层神技：自动完成侦察、滑动、悬停和监听
            listen_result = self.voicePage.slide_to_listen_mode(press_time=press_time, hold_time=hold_time)

            # 断言一：在悬停的 10 秒内，屏幕上是否出现了那四个字
            check.is_true(listen_result, "❌ 悬停在试听按钮上时，未出现『松开 试听』的红框提示文案！")

        with allure.step("4. 校验松手后是否成功进入试听页面"):
            # 断言二：手指松开后，检查 UI 是否切换到了试听专属页面
            is_preview = self.voicePage.is_in_preview_mode()
            check.is_true(is_preview, "❌ 松开手指后，未能进入带有取消/发送按钮的语音试听界面！")
            
        with allure.step(f"5. 后续操作：{ '发送' if action == 'send' else '取消' }试听语音"):
            expected_listen_time = self.voicePage.get_preview_mode_time()
            if is_preview:
                if action == "send":
                    self.voicePage.click_voice_press_button_send()
                    is_success = self.voicePage.verify_voice_message_display(
                        expected_time=expected_listen_time, 
                        pre_snapshot=pre_snapshot, 
                        expect_sent=True
                    )
                    check.is_true(is_success, "❌ 语音发送验证失败（可能未真正发出，或时长不符）")
                else:
                    self.voicePage.click_voice_press_button_retry()
                    is_success = self.voicePage.verify_voice_message_display(
                        expected_time=expected_listen_time, 
                        pre_snapshot=pre_snapshot, 
                        expect_sent=False
                    )
                    check.is_true(is_success, "❌ 语音取消失败！页面上竟然刷出了新消息！")


    @allure.story("语音进阶交互：试听模式多场景操作测试 (播放/暂停、听筒/扬声器切换) + 最终发送/取消校验")
    @allure.title("语音进阶交互：试听模式多场景操作测试 (播放/暂停、听筒/扬声器切换) + 最终发送/取消校验-状态：已完成")
    @pytest.mark.parametrize("press_time", [1])
    @pytest.mark.parametrize("hold_time", [5])
    @pytest.mark.parametrize("action", ["send", "cancel"], ids=["最终发送", "最终取消"])
    @pytest.mark.parametrize("scenario", ["play", "pause", "earpiece", "speaker"], ids=["试听播放", "试听暂停", "听筒模式", "扬声器模式"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_voice_preview_multi_scenarios(self, strategy, scenario, action, press_time, hold_time):
        """测试在试听模式下各种不同的用户交互场景，并组合不同的最终动作（发送/取消）"""
        allure.dynamic.title(f"语音进阶交互测试 - 策略: {strategy.name}, 悬停时间: {hold_time}秒")
        
        with allure.step(f"1. 进入与【{strategy.name}】的私聊并开启语音模式"):
            self._enter_chat_and_enable_voice(strategy.name)
            
        with allure.step("2. 【关键】获取操作前的聊天列表快照"):
            # 在按住语音按钮之前，给现在的列表拍个照
            pre_snapshot = self.voicePage.get_voice_list_snapshot() 

        with allure.step(f"3. 长按语音并滑动到试听区域，悬停 {hold_time} 秒"):
            listen_result = self.voicePage.slide_to_listen_mode(press_time=press_time, hold_time=hold_time)
            check.is_true(listen_result, "❌ 悬停在试听按钮上时，未出现提示文案！")

        with allure.step("4. 确认成功进入带有按钮的试听界面"):
            is_preview = self.voicePage.is_in_preview_mode()
            check.is_true(is_preview, "❌ 未进入带有取消/发送/播放按钮的试听模式界面！")

        if not is_preview:
            # 提前终止用例，避免后续抛出找不到元素的异常
            pytest.fail("因未成功进入试听界面，当前用例被提前终止")

        with allure.step(f"5. 执行特定场景交互操作 - {scenario}"):
            expected_listen_time = self.voicePage.get_preview_mode_time()
            if expected_listen_time == 0:
                expected_listen_time = hold_time + press_time 
            if scenario == "play":  # 先播放，确保播放逻辑畅通
                self.voicePage.click_voice_press_button_play_or_pause()
                pause_result = self.voicePage.is_in_playing_mode("pause", "准备试听语音内容")
                check.is_true(pause_result, "❌ 暂停失败，未正确展示『准备试听语音内容』的文案！")
                self.voicePage.click_voice_press_button_play_or_pause()
                play_result = self.voicePage.is_in_playing_mode(scenario, "2秒后开始")
                check.is_true(play_result, "❌ 播放失败，未正确展示『2秒后开始』的文案！")
                
            elif scenario == "pause": # 播放后再暂停
                self.voicePage.click_voice_press_button_play_or_pause()
                pause_result = self.voicePage.is_in_playing_mode(scenario, "准备试听语音内容")
                check.is_true(pause_result, "❌ 暂停失败，未正确展示『准备试听语音内容』的文案！")
                
            elif scenario == "earpiece":    # 切换听筒
                earpiece_result = self.voicePage.is_in_playing_mode(scenario, "正在听筒播放内容")
                check.is_true(earpiece_result, "❌ 听筒失败，未正确展示『正在听筒播放内容』的文案！")
            
            elif scenario == "speaker":     # 切换扬声器
                self.voicePage.click_voice_press_button_play_or_pause()
                pause_result = self.voicePage.is_in_playing_mode("pause", "准备试听语音内容")
                check.is_true(pause_result, "❌ 暂停失败，未正确展示『准备试听语音内容』的文案！")
                self.voicePage.click_voice_press_button_play_or_pause()
                speaker_result = self.voicePage.is_in_playing_mode(scenario, "正在扬声器/外放播放内容")
                check.is_true(speaker_result, "❌ 扬声器失败，未正确展示『正在扬声器/外放播放内容』的文案！")

        with allure.step(f"6. 执行最终决定操作 - {'发送' if action == 'send' else '取消'}，并验证"):
            if action == "send":
                self.voicePage.click_voice_press_button_send()
                is_success = self.voicePage.verify_voice_message_display(
                    expected_time=expected_listen_time, 
                    pre_snapshot=pre_snapshot, 
                    expect_sent=True)
                check.is_true(is_success, "❌ 语音发送验证失败（可能未真正发出，或时长不符）")
            else:
                self.voicePage.click_voice_press_button_retry()
                is_success = self.voicePage.verify_voice_message_display(
                    expected_time=expected_listen_time, 
                    pre_snapshot=pre_snapshot, 
                    expect_sent=False)
                check.is_true(is_success, "❌ 语音取消失败！页面上竟然刷出了新消息！")


    @allure.story("识别语音内容，待完善")
    @allure.title("识别语音内容，待完善-状态：未完成")
    @pytest.mark.skip(reason="识别语音内容功能待完善")
    @pytest.mark.parametrize("press_time", [1])
    @pytest.mark.parametrize("hold_time", [10])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_voice_recognize_content(self, strategy, press_time, hold_time):
        """测试识别语音内容"""
        pass

        
    @allure.story("断网异常测试：无网络下发送语音验证红点提示")
    @allure.title("断网异常测试：无网络下发送语音验证红点提示-状态：已完成")
    @pytest.mark.skip(reason="断网异常测试功能待完善")
    @pytest.mark.parametrize("hold_time", [2])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_voice_network_failure(self, strategy, hold_time):
        """测试在断网(飞行模式)下发送语音，验证必定生成带红色失败感叹号的气泡"""
        allure.dynamic.title(f"断网发送异常测试 - 策略: {strategy.name}, 悬停: {hold_time}秒")
        
        with allure.step(f"1. 进入与【{strategy.name}】的私聊并开启语音模式"):
            self._enter_chat_and_enable_voice(strategy.name)
            
        with allure.step("2. 【关键】获取断网前的聊天快照"):
            pre_snapshot = self.voicePage.get_voice_list_snapshot() 
            
        with allure.step("3. 模拟极端弱网：切断设备网络 (开启飞行模式)"):
            try:
                # Appium 标准的设定网络 API: 1 代表飞行模式无网，6 代表全部开启
                self.voicePage.driver.set_network_connection(1)
            except Exception as e:
                pytest.skip(f"当前执行环境/模拟器不支持动态修改底层网络状态，跳过该断网测试: {e}")
            
        try:
            with allure.step(f"4. 强行录制并发送语音 ({hold_time}秒)"):
                self.voicePage.send_voice_message(hold_time=hold_time)
                
            with allure.step("5. 校验气泡出现，但必须带有发送失败的红色重发感叹号"):
                import time
                time.sleep(2) # 等待气泡弹层和底层的超时检测
                is_failed_icon_shown = self.voicePage.verify_voice_message_failed(hold_time, pre_snapshot)
                check.is_true(is_failed_icon_shown, "❌ 断网下测试失败：没有任何气泡，或者气泡上奇迹般地没有红色失败感叹号！")
                
        finally:
            with allure.step("清理：不论测试成功与否，务必恢复设备的正常网络"):
                try:
                    import time
                    self.voicePage.driver.set_network_connection(6)
                    time.sleep(3) # 给设备几秒钟重连Wi-Fi
                except Exception:
                    pass
    




