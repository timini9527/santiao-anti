from appium.webdriver.common.appiumby import AppiumBy
from locators.chat_options.media_select_locator import MediaSelectLocator
from locators.chat.core.chat_locator import ChatLocator


class ChatVideoLocator(MediaSelectLocator):
    """ 视频模块专属定位器 """
    
    # ==================== 相册网格中的视频特征 ====================
    VIDEO_ITEM_CONTAINER = (AppiumBy.ID, f'{MediaSelectLocator.PACKAGE_ID}/iv_video_icon')  # 视频左下角的小图标
    VIDEO_DURATION       = (AppiumBy.ID, f'{MediaSelectLocator.PACKAGE_ID}/tv_duration')    # 视频时长文本 (如 00:05)
    
    # 视频特有的选择框 (部分 UI 可能会与图片共用，这里做映射)
    VIDEO_CHECK_BOX      = (AppiumBy.ID, f'{MediaSelectLocator.PACKAGE_ID}/select_right_ll') 
    
    # 预览页
    PREVIEW_VIDEO_PLAY   = (AppiumBy.ID, f'{MediaSelectLocator.PACKAGE_ID}/iv_play_video')  # 预览页中央的播放按钮
    VIDEO_SIZE_TEXT      = (AppiumBy.ID, f'{MediaSelectLocator.PACKAGE_ID}/tv_video_size')  # 视频大小信息


    # ==================== 聊天页面中的视频气泡 ====================
    VIDEO_PLAY_BUTTON_ID = ChatLocator.VIDEO_PLAY_BUTTON_ID                     # 视频播放按钮ID
    VIDEO_PLAY_BUTTON_ITEM = ChatLocator.VIDEO_PLAY_BUTTON_ITEM                 # 视频播放按钮
    SENT_VIDEO_PLAY_BUTTON_ITEM = ChatLocator.SENT_VIDEO_PLAY_BUTTON_ITEM       # 发送方视频播放按钮
    RECEIVE_VIDEO_PLAY_BUTTON_ITEM = ChatLocator.RECEIVE_VIDEO_PLAY_BUTTON_ITEM # 接收方视频播放按钮

