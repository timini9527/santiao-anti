from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator
from locators.chat.core.chat_locator import ChatLocator

class ChatVoiceLocator(CommonLocator, ChatLocator):
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # ==== 语音输入相关定位 ====
    VOICE_PRESS_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/voice_press_btn')                         # 按住说话按钮
    VOICE_PRESS_BUTTON_LISTEN = (AppiumBy.ID, f'{PACKAGE_ID}/btnListen')                        # 试听按钮
    VOICE_PRESS_BUTTON_CANCEL = (AppiumBy.ID, f'{PACKAGE_ID}/btnCancelTop')                     # 录制时取消按钮
    VOICE_PRESS_BUTTON_RETRY = (AppiumBy.ID, f'{PACKAGE_ID}/btnRetry')                          # 试听下取消按钮
    VOICE_PRESS_BUTTON_SEND = (AppiumBy.ID, f'{PACKAGE_ID}/btnSend')                            # 试听下发送按钮
    VOICE_PRESS_BUTTON_SPEAKER = (AppiumBy.ID, f'{PACKAGE_ID}/playModeGroup')                   # 听筒或外放按钮整个容器
    VOICE_PRESS_BUTTON_SPEAKER_IN_LISTEN = (AppiumBy.ID, f'{PACKAGE_ID}/playMode')              # 试听下听筒或外放喇叭按钮
    VOICE_PRESS_BUTTON_SPEAKER_IN_LISTEN_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/playModeText')     # 试听下听筒或外放喇叭按钮文字
    VOICE_PRESS_BUTTON_PLAY_OR_PAUSE = (AppiumBy.ID, f'{PACKAGE_ID}/btnMain')                   # 试听下播放或暂停按钮
    VOICE_PRESS_BUTTON_TIME = (AppiumBy.ID, f'{PACKAGE_ID}/tvRecordTime')                       # 语音时长
    VOICE_PRESS_BUTTON_WAVE = (AppiumBy.ID, f'{PACKAGE_ID}/waveBar')                            # 播放波形效果

    # 语音消息整行容器
    SENT_VOICE_MESSAGE_ROW_ID = f'{PACKAGE_ID}/message_row'
    SENT_VOICE_MESSAGE_ROW = (AppiumBy.ID, SENT_VOICE_MESSAGE_ROW_ID) # 语音消息整行容器
    # 发送消息失败或成功状态
    SENT_VOICE_MESSAGE_STATUS_ID = f'{PACKAGE_ID}/btn_state'
    SENT_VOICE_MESSAGE_STATUS = (AppiumBy.ID, SENT_VOICE_MESSAGE_STATUS_ID) # 发送消息失败或成功状态
    # 语音消息气泡容器
    SENT_VOICE_MESSAGE_BUBBLE_ID = f'{PACKAGE_ID}/container'
    SENT_VOICE_MESSAGE_BUBBLE = (AppiumBy.ID, SENT_VOICE_MESSAGE_BUBBLE_ID) # 语音消息气泡容器
    # 语音时长
    SENT_VOICE_MESSAGE_TIME_ID = f'{PACKAGE_ID}/tvDuration'
    SENT_VOICE_MESSAGE_TIME = (AppiumBy.ID, SENT_VOICE_MESSAGE_TIME_ID) # 语音时长
    # 录制语音超过50s提示
    # ==== 录音/滑动悬停状态提示文案 (Hints) ====
    VOICE_HINT_BOX = (AppiumBy.ID, f'{PACKAGE_ID}/tvHint') 
    VOICE_HINT_TIME_LIMIT = (AppiumBy.XPATH, "//*[contains(@text, '秒后将发送')]")                # 录音接近60s倒计时警告
    VOICE_HINT_AUDITION = (AppiumBy.XPATH, "//*[contains(@text, '试听')]")                       # 滑动至试听区提示
    VOICE_HINT_CANCEL = (AppiumBy.XPATH, "//*[contains(@text, '取消发送')]")                     # 滑动至取消区提示
    
    # ==== 试听前准备倒计时文案 ====
    VOICE_PREPARE_LISTEN = (AppiumBy.XPATH, "//*[contains(@text, '准备试听语音内容')]")             # 暂停提示，准备试听语音内容
    VOICE_PLAY_SOON_EARPIECE = (AppiumBy.XPATH, "//*[contains(@text, '2秒后开始听筒播放')]")        # 播放提示，准备试听语音内容,2秒后开始听筒播放
    VOICE_PLAY_SOON_SPEAKER = (AppiumBy.XPATH, "//*[contains(@text, '2秒后开始扬声器播放')]")       # 播放提示，准备试听语音内容,2秒后开始扬声器播放
    VOICE_PLAYING_SPEAKER = (AppiumBy.XPATH, "//*[contains(@text, '正在扬声器播放内容')]")          # 正在扬声器播放内容
    VOICE_PLAYING_EARPIECE = (AppiumBy.XPATH, "//*[contains(@text, '正在听筒播放内容')]")           # 正在听筒播放内容
    
    # 播放波形效果
    SENT_VOICE_MESSAGE_WAVE_ID = f'{PACKAGE_ID}/ivVoice'
    SENT_VOICE_MESSAGE_WAVE = (AppiumBy.ID, SENT_VOICE_MESSAGE_WAVE_ID) # 播放波形效果

    # 精确定位是发送方还是接收方的语音时长
    @classmethod
    def get_sent_voice_message_time_locator(cls, role: str = "sender"):
        """
        获取语音消息时长元素的定位器
        role: "sender" (发送方) / "receiver" (接收方)
        """
        # 获取基础的头像 -> 气泡容器路径
        base_locator = cls.SENT_MESSAGE_CONTENT_ITEM if role == "sender" else cls.RECEIVED_MESSAGE_CONTENT_ITEM
        base_xpath = base_locator[1]
        
        # 优化方案：在气泡容器内，只要同时存在 时长ID 和 声波ID，即判定为语音气泡
        final_xpath = f'{base_xpath}[.//*[@resource-id="{cls.SENT_VOICE_MESSAGE_TIME_ID}"] and .//*[@resource-id="{cls.SENT_VOICE_MESSAGE_WAVE_ID}"]]//*[@resource-id="{cls.SENT_VOICE_MESSAGE_TIME_ID}"]'
        return (AppiumBy.XPATH, final_xpath)

    # 语音消息不同文案显示
    @classmethod
    def get_voice_message_locator(cls, text: str):
        return (AppiumBy.XPATH, f'//*[contains(@text, "{text}")]')
    
    # 最新语音消息发送状态的定位
    @classmethod
    def get_latest_voice_message_status_locator(cls, time_text: int):
        """
        定位指定时长语音消息的发送状态图标(红点)
        """
        # 逻辑：找一个 message_row，它内部包含指定的时长文本，且包含声波图标
        # 然后定位到该 row 下的失败状态按钮
        
        xpath = (f'(//*[@resource-id="{cls.MESSAGE_LAYOUT_ID}" '
                 f'and .//*[@resource-id="{cls.SENT_VOICE_MESSAGE_TIME_ID}" and contains(@text, "{time_text}")] '
                 f'and .//*[@resource-id="{cls.SENT_VOICE_MESSAGE_WAVE_ID}"]])[last()]'
                 f'//*[@resource-id="{cls.SENT_VOICE_MESSAGE_STATUS_ID}"]')
        return (AppiumBy.XPATH, xpath)
