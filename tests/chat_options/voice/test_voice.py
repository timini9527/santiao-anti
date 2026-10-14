import allure
import pytest
import pytest_check as check
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat_options.voice.chat_voice_page import ChatVoicePage
from pages.main.main_page import MainPage
from core.logger_utils import logger
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY






@allure.epic('IM核心功能测试')
@allure.feature('聊天面板-语音')
@allure.story('测试按住说话并发送语音的功能')
class TestChatVoice:
    _chat_target = None

    @pytest.fixture(scope="class", autouse=True)
    def setup_class_teardown(self, driver_sender):
        """
        类级别后置清理：所有用例执行完成后，统一执行一次返回主页
        """
        yield
        try:
            self.__class__._chat_target = None
            MainPage(driver_sender).go_to_main_page()
            logger.info("🧹 [Class Teardown] 语音模块全部用例执行完毕，统一返回主页")
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.voicePage = ChatVoicePage(driver_sender)

    def _enter_chat_and_enable_voice(self, chat_name: str):
        """进入指定的聊天会话并开启语音输入模式（支持同会话直接复用，跨会话如私聊切群聊时自动退回主页重新进入）"""
        if self.__class__._chat_target != chat_name:
            if self.__class__._chat_target is not None:
                logger.info(f"🔄 [Session Switch] 检测到聊天对象从【{self.__class__._chat_target}】切换为【{chat_name}】，退回首页重新进入")
                self.mainPage.go_to_main_page()
            self.chatListPage.enter_chat(chat_name)
            self.__class__._chat_target = chat_name
            self.voicePage.click_voice_button()
        else:
            btn = self.voicePage.get_voice_press_button()
            if not btn:
                self.voicePage.click_voice_button()

    def _execute_preview_decision(self, action: str, expected_time: int, pre_snapshot: dict):
        """[通用辅助] 试听面板决策执行与上屏断言（发送 或 取消）"""
        if action == 'send':
            self.voicePage.click_voice_press_button_send()
            is_ok = self.voicePage.verify_voice_message_display(
                expected_time=expected_time, pre_snapshot=pre_snapshot, expect_sent=True
            )
            check.is_true(is_ok, '❌ 语音试听发送失败（未成功上屏或时长不符）')
        else:
            self.voicePage.click_voice_press_button_retry()
            is_ok = self.voicePage.verify_voice_message_display(
                expected_time=expected_time, pre_snapshot=pre_snapshot, expect_sent=False
            )
            check.is_true(is_ok, '❌ 语音试听取消失败（页面意外刷出了新消息）')




    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('基础语音发送测试')
    @allure.title('基础语音发送测试-状态：已完成')
    @pytest.mark.parametrize('hold_time', [
        pytest.param(0, id='0秒-太短'), 
        pytest.param(1, id='1秒-正常'), 
        pytest.param(30, id='30秒-正常'), 
        pytest.param(59, id='59秒-临界'), 
        pytest.param(60, id='60秒-上限'), 
        pytest.param(61, id='61秒-超限')
    ])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_basic_voice_send(self, strategy, hold_time):
        """测试按住说话并发送语音的功能"""
        allure.dynamic.title(f'基础语音发送测试 - 策略: {strategy.name}, 悬停时间: {hold_time}秒')
        with allure.step(f'1. 进入【{strategy.name}】并开启语音模式'):
            self._enter_chat_and_enable_voice(strategy.name)
            pre_snapshot = self.voicePage.get_voice_list_snapshot()
        with allure.step(f'2. 录制并发送语音 ({hold_time}秒)'):
            send_result = self.voicePage.send_voice_message(hold_time=hold_time)
            if hold_time == 0:
                check.equal(send_result['toast'], '说话时间太短', f"短录音提示失败，实际toast为: {send_result['toast']}")
        with allure.step('3. 校验语音消息上屏状态及展示时长'):
            if hold_time > 0:
                expected_time = 60 if hold_time > 60 else hold_time
                is_success = self.voicePage.verify_voice_message_display(expected_time=expected_time, pre_snapshot=pre_snapshot, expect_sent=True)
                check.is_true(is_success, f'语音气泡显示异常！预期时长应约为 {expected_time} 秒')


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('语音录制取消测试')
    @allure.title('语音录制取消测试-状态：已完成')
    @pytest.mark.parametrize('press_time', [pytest.param(1, id='按压1秒')])
    @pytest.mark.parametrize('hold_time', [pytest.param(5, id='悬停5秒')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_voice_record_cancel(self, strategy, press_time, hold_time):
        """测试录音过程中滑动取消发送"""
        allure.dynamic.title(f'语音录制取消测试 - 策略: {strategy.name}, 悬停时间: {hold_time}秒')
        with allure.step(f'1. 进入【{strategy.name}】并开启语音模式'):
            self._enter_chat_and_enable_voice(strategy.name)
            pre_snapshot = self.voicePage.get_voice_list_snapshot()
        with allure.step('2. 长按语音并滑动到取消区域'):
            self.voicePage.verify_voice_message_cancel(press_time=press_time, hold_time=hold_time)
        with allure.step('3. 校验松手后成功取消发送，无新增语音气泡'):
            is_success = self.voicePage.verify_voice_message_display(expected_time=hold_time + press_time, pre_snapshot=pre_snapshot, expect_sent=False)
            check.is_true(is_success, '❌ 语音取消发送校验失败！页面上出现了新消息')


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('语音进阶交互：滑动试听测试并操作(发送/取消)，并验证')
    @allure.title('语音进阶交互：滑动试听测试并操作(发送/取消)，并验证-状态：已完成')
    @pytest.mark.parametrize('action', [pytest.param('send', id='发送'), pytest.param('cancel', id='取消')])
    @pytest.mark.parametrize('press_time', [pytest.param(1, id='按压1秒')])
    @pytest.mark.parametrize('hold_time', [pytest.param(5, id='悬停5秒')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_voice_swipe_to_preview_and_action(self, strategy, action, press_time, hold_time):
        """测试按住语音按钮并滑动到试听区域，并进行发送或取消操作"""
        allure.dynamic.title(f'语音进阶交互测试 - 策略: {strategy.name}, 悬停时间: {hold_time}秒')
        with allure.step(f'1. 进入【{strategy.name}】并开启语音模式'):
            self._enter_chat_and_enable_voice(strategy.name)
            pre_snapshot = self.voicePage.get_voice_list_snapshot()
        with allure.step('2. 长按语音并滑动到试听区域'):
            self.voicePage.slide_to_listen_mode(press_time=press_time, hold_time=hold_time)
            is_preview = self.voicePage.is_in_preview_mode()
            check.is_true(is_preview, '❌ 松开手指后未能进入语音试听界面！')
        with allure.step(f"3. 执行后续决策：{('发送' if action == 'send' else '取消')}试听语音"):
            listen_time = self.voicePage.get_preview_mode_time() or (hold_time + press_time)
            if is_preview:
                self._execute_preview_decision(action, listen_time, pre_snapshot)


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('语音进阶交互：试听模式多场景操作测试 (播放/暂停、听筒/扬声器切换) + 最终发送/取消校验')
    @allure.title('语音进阶交互：试听模式多场景操作测试 (播放/暂停、听筒/扬声器切换) + 最终发送/取消校验-状态：已完成')
    @pytest.mark.parametrize('press_time', [pytest.param(1, id='按压1秒')])
    @pytest.mark.parametrize('hold_time', [pytest.param(5, id='悬停5秒')])
    @pytest.mark.parametrize('action', [pytest.param('send', id='最终发送'), pytest.param('cancel', id='最终取消')])
    @pytest.mark.parametrize('scenario', [
        pytest.param('play', id='试听播放'), 
        pytest.param('pause', id='试听暂停'), 
        pytest.param('earpiece', id='听筒模式'), 
        pytest.param('speaker', id='扬声器模式')
    ])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_voice_preview_multi_scenarios(self, strategy, scenario, action, press_time, hold_time):
        """测试在试听模式下各种不同的用户交互场景，并组合不同的最终动作（发送/取消）"""
        allure.dynamic.title(f'语音进阶交互测试 - 策略: {strategy.name}, 场景: {scenario}, 最终: {action}')
        with allure.step(f'1. 进入【{strategy.name}】并进入试听模式'):
            self._enter_chat_and_enable_voice(strategy.name)
            pre_snapshot = self.voicePage.get_voice_list_snapshot()
            self.voicePage.slide_to_listen_mode(press_time=press_time, hold_time=hold_time)
            if not self.voicePage.is_in_preview_mode():
                pytest.fail('未进入试听模式界面，终止后续操作')
        with allure.step(f'2. 执行场景交互：{scenario}'):
            listen_time = self.voicePage.get_preview_mode_time() or (hold_time + press_time)
            if scenario in ('play', 'pause'):
                self.voicePage.click_voice_press_button_play_or_pause()
            elif scenario in ('earpiece', 'speaker'):
                self.voicePage.click_voice_press_button_speaker()
            check.is_true(self.voicePage.is_in_playing_mode(scenario), f'❌ {scenario} 交互校验未达预期！')
        with allure.step(f"3. 执行最终决定：{('发送' if action == 'send' else '取消')}"):
            self._execute_preview_decision(action, listen_time, pre_snapshot)


    @allure.story('识别语音内容')
    @allure.title('识别语音内容-状态：未完成')
    @pytest.mark.skip(reason='识别语音内容功能待完善')
    @pytest.mark.parametrize('press_time', [pytest.param(1, id='按压1秒')])
    @pytest.mark.parametrize('hold_time', [pytest.param(10, id='悬停10秒')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_voice_recognize_content(self, strategy, press_time, hold_time):
        """测试识别语音内容"""
        pass


    @allure.story('断网异常测试：无网络下发送语音验证红点提示')
    @allure.title('断网异常测试：无网络下发送语音验证红点提示-状态：未完成')
    @pytest.mark.skip(reason='断网异常测试功能待完善')
    @pytest.mark.parametrize('hold_time', [pytest.param(2, id='悬停2秒')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_voice_network_failure(self, strategy, hold_time):
        """测试在断网(飞行模式)下发送语音，验证必定生成带红色失败感叹号的气泡"""
        allure.dynamic.title(f'断网发送异常测试 - 策略: {strategy.name}, 悬停: {hold_time}秒')
        with allure.step(f'1. 进入与【{strategy.name}】的会话并开启语音模式'):
            self._enter_chat_and_enable_voice(strategy.name)
        with allure.step('2. 获取断网前的聊天快照'):
            pre_snapshot = self.voicePage.get_voice_list_snapshot()
        with allure.step('3. 模拟极端弱网：切断设备网络 (开启飞行模式)'):
            try:
                self.voicePage.driver.set_network_connection(1)
            except Exception as e:
                pytest.skip(f'当前执行环境/模拟器不支持动态修改底层网络状态，跳过该断网测试: {e}')
        try:
            with allure.step(f'4. 强行录制并发送语音 ({hold_time}秒)'):
                self.voicePage.send_voice_message(hold_time=hold_time)
            with allure.step('5. 校验气泡出现，但必须带有发送失败的红色重发感叹号'):
                import time
                time.sleep(2)
                is_failed_icon_shown = self.voicePage.verify_voice_message_failed(hold_time, pre_snapshot)
                check.is_true(is_failed_icon_shown, '❌ 断网下测试失败：没有任何气泡，或者气泡上没有红色失败感叹号！')
        finally:
            with allure.step('清理：恢复设备的正常网络'):
                try:
                    import time
                    self.voicePage.driver.set_network_connection(6)
                    time.sleep(3)
                except Exception:
                    pass