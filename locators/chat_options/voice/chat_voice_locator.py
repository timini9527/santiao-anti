from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator
from locators.chat.core.chat_locator import ChatLocator

class ChatVoiceLocator(CommonLocator, ChatLocator):
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # ==== 语音输入相关定位 ====
    VOICE_PRESS_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/voice_press_btn')                         # 按住说话按钮
    VOICE_RECORD_PREVIEW_ACTION = (AppiumBy.ID, f'{PACKAGE_ID}/voice_record_preview_action')    # 试听按钮
    VOICE_RECORD_CANCEL_ACTION = (AppiumBy.ID, f'{PACKAGE_ID}/voice_record_cancel_action')      # 录制时取消按钮
    VOICE_RECORD_HINT = (AppiumBy.ID, f'{PACKAGE_ID}/voice_record_hint')                        # 录制时提示文案
    VOICE_RECORD_TIME = (AppiumBy.ID, f'{PACKAGE_ID}/voice_record_time')                        # 语音时长
    VOICE_PREVIEW_PLAY_ACTION = (AppiumBy.ID, f'{PACKAGE_ID}/voice_preview_play_action')        # 播放按钮
    VOICE_PREVIEW_ROUTE_STATUS = (AppiumBy.ID, f'{PACKAGE_ID}/voice_preview_route_status')      # 听筒或外放文案状态
    VOICE_PREVIEW_ROUTE_ACTION = (AppiumBy.ID, f'{PACKAGE_ID}/voice_preview_route_action')      # 听筒或外放切换按钮
    VOICE_PREVIEW_ROUTE_LABEL = (AppiumBy.ID, f'{PACKAGE_ID}/voice_preview_route_label')        # 听筒或外放按钮文字
    VOICE_PREVIEW_CANCEL_ACTION = (AppiumBy.ID, f'{PACKAGE_ID}/voice_preview_cancel_action')    # 试听下取消按钮
    VOICE_PREVIEW_CANCEL_LABEL = (AppiumBy.ID, f'{PACKAGE_ID}/voice_preview_cancel_label')      # 试听下取消按钮文字
    VOICE_PREVIEW_SEND_ACTION = (AppiumBy.ID, f'{PACKAGE_ID}/voice_preview_send_action')        # 试听下发送按钮
    VOICE_RECORD_OVERLAY = (AppiumBy.ID, f'{PACKAGE_ID}/voice_record_overlay')                  # 录音悬浮窗

    # 语音消息整行容器
    AUDIO_BUBBLE_ID = f'{PACKAGE_ID}/audio_bubble'
    AUDIO_BUBBLE = (AppiumBy.ID, AUDIO_BUBBLE_ID)
    # 语音时长
    SENT_VOICE_MESSAGE_TIME_ID = f'{PACKAGE_ID}/duration'
    SENT_VOICE_MESSAGE_TIME = (AppiumBy.ID, SENT_VOICE_MESSAGE_TIME_ID) # 语音时长
    
    # 发送消息失败状态
    SENT_VOICE_MESSAGE_STATUS_ID = ChatLocator.FAIL_MSG_ID
    SENT_VOICE_MESSAGE_STATUS = ChatLocator.FAIL_MSG # 发送消息失败状态


    # 精确定位是发送方还是接收方的语音时长
    @classmethod
    def get_sent_voice_message_time_locator(cls, role: str = "sender"):
        """
        获取语音消息时长元素的定位器
        role: "sender" (发送方) / "receiver" (接收方)
        """
        side = "sent" if role == "sender" else "received"
        return cls._BUBBLE_XPATH(side, cls.SENT_VOICE_MESSAGE_TIME_ID)

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
        xpath = (f'(//*[@resource-id="{cls.MESSAGES_LIST_ID}"]//*[contains(@resource-id, "{cls.SENT_VOICE_MESSAGE_TIME_ID}") and contains(@text, "{time_text}")])[last()]'
                 f'/following-sibling::*[@resource-id="{cls.FAIL_MSG_ID}"]')
        return (AppiumBy.XPATH, xpath)
