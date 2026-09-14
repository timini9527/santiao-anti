from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class CallLocator(CommonLocator):
    """
    音视频通话全屏页面元素定位器 (AVChat / Video & Voice Call Activity)
    覆盖主叫呼叫、被叫振铃、接听通话中的控制项与状态提示
    """
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # =========================================================================
    # 1. 顶部控制栏与通话状态
    # =========================================================================
    AVCHAT_MINI = (AppiumBy.ID, f'{PACKAGE_ID}/avchatMini')                                     # 最小化悬浮窗按钮
    AVCHAT_VIDEO_TIME = (AppiumBy.ID, f'{PACKAGE_ID}/avchatVideoTime')                          # 通话时长计时 (如 "01:22")
    VIEW_CENTRE = (AppiumBy.ID, f'{PACKAGE_ID}/viewCentre')                                     # 视频通话中心画面视图

    # =========================================================================
    # 2. 状态提示文本 (麦克风静音等)
    # =========================================================================
    AVCHAT_VIDEO_MUTE_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/avchatVideoMuteText')                 # 对方麦克风关闭提示 ("对方的麦克风已关闭")
    AVCHAT_MICROPHONE_STATE_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/avchat_microphone_state_text')  # 本地麦克风关闭提示 ("您的麦克风已关闭")

    # =========================================================================
    # 3. 底层通话硬件开关控制项
    # =========================================================================
    # 麦克风
    IV_MICROPHONE_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/ivMicrophoneSwitch')                    # 麦克风开关图标
    TV_MICROPHONE_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/tvMicrophoneSwitch')                    # 麦克风状态文本 ("麦克风已关" / "麦克风已开")

    # 扬声器 / 免提
    IV_SPEAKER_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/ivSpeakerSwitch')                          # 扬声器开关图标
    TV_SPEAKER_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/tvSpeakerSwitch')                          # 扬声器状态文本 ("扬声器已关" / "扬声器已开")

    # 摄像头与模式切换
    IV_VIDEO_AUDIO_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/ivVideoAudioSwitch')                   # 摄像头开关 / 音视频模式切换图标
    TV_VIDEO_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/tvVideoSwitch')                              # 摄像头状态文本 ("摄像头已开" / "摄像头已关")
    IV_VIDEO_CAMERA_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/ivVideoCameraSwitch')                 # 翻转摄像头图标
    TV_CAMERA_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/tvCameraSwitch')                            # 翻转摄像头文本 ("翻转摄像头")

    # =========================================================================
    # 4. 挂断与结束控制
    # =========================================================================
    IV_HANGUP = (AppiumBy.ID, f'{PACKAGE_ID}/ivHangup')                                         # 挂断按钮图标
    TV_HANGUP = (AppiumBy.XPATH, '//*[@text="挂断"]')                                           # 挂断文本

    # =========================================================================
    # 5. 被叫接听、拒绝与来电提示控制项
    # =========================================================================
    # 拒绝
    IV_REFUSE = (AppiumBy.ID, f'{PACKAGE_ID}/refuseAudio')                                      # 拒绝按钮图标
    TV_REFUSE = (AppiumBy.XPATH, '//*[@text="拒绝"]')                                           # 拒绝文本
    BTN_REJECT = IV_REFUSE                                                                      # 别名兼容

    # 接听
    IV_RECEIVE = (AppiumBy.ID, f'{PACKAGE_ID}/receiveAudioVideo')                               # 接听按钮图标
    TV_RECEIVE = (AppiumBy.ID, f'{PACKAGE_ID}/text_answer')                                     # 接听文本 ("接听")
    BTN_ACCEPT = IV_RECEIVE                                                                     # 别名兼容

    # 来电通知提示
    TV_AVCHAT_NOTIFY = (AppiumBy.ID, f'{PACKAGE_ID}/avchatAudioNotify')                         # 来电提示文本 (如 "邀请你语音通话" / "邀请你视频通话")
