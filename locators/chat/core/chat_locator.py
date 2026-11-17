from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class _ChatLocatorAndroid:
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # ==================================================================================================================
    # 聊天页面基础列表与行容器
    # ==================================================================================================================
    MESSAGES_LIST_ID = f'{PACKAGE_ID}/messages'                                         # 消息列表 RecyclerView
    MESSAGES_LIST_ITEM = (AppiumBy.ID, MESSAGES_LIST_ID)                                # 消息列表
    
    # 消息行容器 (RecyclerView 下的各个 android.view.ViewGroup 消息行)
    MESSAGE_LAYOUT_XPATH = f'//*[@resource-id="{MESSAGES_LIST_ID}"]/android.view.ViewGroup'
    MESSAGE_LAYOUT_ITEM = (AppiumBy.XPATH, MESSAGE_LAYOUT_XPATH)                        # 消息行容器
    
    # 头像相关
    AVATAR_ID = f'{PACKAGE_ID}/avatar'
    AVATAR_ITEM = (AppiumBy.ID, AVATAR_ID)                                              # 统一头像

    # 已读未读标识
    READ_STATUS_ID = f'{PACKAGE_ID}/read_status'                                        # 新版已读未读状态 ID
    READ_STATUS_ITEM = (AppiumBy.ID, READ_STATUS_ID)                                    # 已读未读状态控件

    # 发送状态/失败红点
    FAIL_MSG_ID = f'{PACKAGE_ID}/delivery_status'
    FAIL_MSG = (AppiumBy.ID, FAIL_MSG_ID)                                              # 消息发送状态/失败红点

    # 群聊页面显示用户昵称
    GROUP_CHAT_USER_NAME_ID = f'{PACKAGE_ID}/sender_name'
    GROUP_CHAT_USER_NAME_ITEM = (AppiumBy.ID, GROUP_CHAT_USER_NAME_ID)                    # 用户名

    # ==================================================================================================================
    # 核心消息类型定位器（一物一元组）
    # ==================================================================================================================
    # 1. 文本 / Emoji 消息
    MESSAGE_CONTENT_ID = f'{PACKAGE_ID}/message_text'
    MESSAGE_CONTENT_ITEM = (AppiumBy.ID, MESSAGE_CONTENT_ID)                            # 文本内容
    TEXT_MESSAGE_VIEW_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{MESSAGE_CONTENT_ID}"]')

    # 2. 图片 / 动态表情包
    IMAGE_ID = f'{PACKAGE_ID}/message_image'
    IMAGE_ITEM = (AppiumBy.ID, IMAGE_ID)                                                # 图片/表情包
    PREVIEW_IMAGE_ID = f'{PACKAGE_ID}/preview_image'
    PREVIEW_IMAGE_ITEM = (AppiumBy.ID, PREVIEW_IMAGE_ID)                                # 预览图片
    IV_DOWNLOAD_ID = f'{PACKAGE_ID}/iv_download'
    IV_DOWNLOAD_ITEM = (AppiumBy.ID, IV_DOWNLOAD_ID)                                    # 下载图标

    # 3. 视频消息
    VIDEO_PLAY_BUTTON_ID = f'{PACKAGE_ID}/video_cover'
    VIDEO_PLAY_BUTTON_ITEM = (AppiumBy.ID, VIDEO_PLAY_BUTTON_ID)                        # 视频播放按钮 / 封面
    VIDEO_DURATION_ID = f'{PACKAGE_ID}/duration'
    VIDEO_DURATION_ITEM = (AppiumBy.ID, VIDEO_DURATION_ID)                              # 视频时长

    # 4. 语音消息
    AUDIO_BUBBLE_ID = f'{PACKAGE_ID}/audio_bubble'
    AUDIO_BUBBLE = (AppiumBy.ID, AUDIO_BUBBLE_ID)                                       # 语音气泡

    # 5. 定位消息
    LOCATION_CARD_ID = f'{PACKAGE_ID}/location_card'
    LOCATION_CARD_ITEM = (AppiumBy.ID, LOCATION_CARD_ID)                                # 定位卡片容器
    LOCATION_MESSAGE_TITLE_ID = f'{PACKAGE_ID}/location_title'
    LOCATION_MESSAGE_TITLE = (AppiumBy.ID, LOCATION_MESSAGE_TITLE_ID)                   # 定位主标题
    LOCATION_MESSAGE_SUBTITLE_ID = f'{PACKAGE_ID}/location_subtitle'
    LOCATION_MESSAGE_SUBTITLE = (AppiumBy.ID, LOCATION_MESSAGE_SUBTITLE_ID)             # 定位副标题/详细地址

    # 6. 名片消息
    PROFILE_CARD_ID = f'{PACKAGE_ID}/profile_card'
    PROFILE_CARD_ITEM = (AppiumBy.ID, PROFILE_CARD_ID)                                  # 名片卡片容器
    CARD_NICKNAME_ID = f'{PACKAGE_ID}/card_title'
    CARD_NICKNAME_ITEM = (AppiumBy.ID, CARD_NICKNAME_ID)                                # 名片昵称/标题
    CARD_ST_ID = f'{PACKAGE_ID}/card_subtitle'
    CARD_ST_ITEM = (AppiumBy.ID, CARD_ST_ID)                                            # 名片账号/ST号
    CARD_TAG_ID = f'{PACKAGE_ID}/card_kind'
    CARD_TAG = (AppiumBy.ID, CARD_TAG_ID)                                               # 名片类型标签

    # 7. 文件消息
    FILE_CARD_ID = f'{PACKAGE_ID}/file_card'
    FILE_CARD_ITEM = (AppiumBy.ID, FILE_CARD_ID)                                        # 文件卡片容器
    FILE_NAME_ID = f'{PACKAGE_ID}/file_name'
    FILE_NAME_ITEM = (AppiumBy.ID, FILE_NAME_ID)                                        # 文件名
    FILE_STATUS_ID = f'{PACKAGE_ID}/file_status'
    FILE_STATUS_ITEM = (AppiumBy.ID, FILE_STATUS_ID)                                    # 文件状态
    FILE_SIZE_ID = f'{PACKAGE_ID}/file_meta'
    FILE_SIZE_ITEM = (AppiumBy.ID, FILE_SIZE_ID)                                        # 文件大小/元数据
    FILE_LINE_ID = f'{PACKAGE_ID}/file_line'
    FILE_LINE_ITEM = (AppiumBy.ID, FILE_LINE_ID)                                        # 分隔线

    # 8. 聊天记录（合并转发）卡片
    MERGE_CARD_ID = f'{PACKAGE_ID}/merge_card'
    MERGE_CARD_MSG = (AppiumBy.ID, MERGE_CARD_ID)                                       # 合并转发卡片容器
    MERGE_CARD_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/merge_title')                       # 合并转发标题
    MERGE_CARD_PREVIEW = (AppiumBy.ID, f'{PACKAGE_ID}/merge_preview')                   # 合并转发预览文本
    MERGE_CARD_KIND = (AppiumBy.ID, f'{PACKAGE_ID}/merge_kind')                         # 合并转发类型底部标签文本

    # 9. 停用账号/封禁提示
    DISABLE_MESSAGE_TIP = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("对方账号无法使用 详情")')

    # 10. 音视频通话记录卡片消息 (Call Card)
    CALL_CARD_ID = f'{PACKAGE_ID}/call_card'
    CALL_CARD_ITEM = (AppiumBy.ID, CALL_CARD_ID)                                        # 通话卡片容器
    CALL_TITLE_ID = f'{PACKAGE_ID}/call_title'
    CALL_TITLE_ITEM = (AppiumBy.ID, CALL_TITLE_ID)                                      # 通话卡片主标题 (如 "未接来电" / "已取消" / "已拒绝" / "通话时长 00:03")
    CALL_SUBTITLE_ID = f'{PACKAGE_ID}/call_subtitle'
    CALL_SUBTITLE_ITEM = (AppiumBy.ID, CALL_SUBTITLE_ID)                                # 通话卡片副标题 (如 "轻触回拨")


    # ==================================================================================================================
    # 聊天页面顶部元素定位
    # ==================================================================================================================
    TOP_BACK_UNREAD_BG = (AppiumBy.ID, f'{PACKAGE_ID}/back_unread_background')          # 返回未读背景
    TOP_IV_BACK_BTN = CommonLocator.TOP_IV_BACK_BTN
    TOP_BACK_BUTTON = CommonLocator.TOP_IV_BACK_BTN                                     # 返回按钮
    TOP_BACK_UNREAD_BADGE = (AppiumBy.ID, f'{PACKAGE_ID}/back_unread_badge')            # 返回按钮未读数角标
    TOP_USER_NAME_ID = f'{PACKAGE_ID}/title'
    TOP_USER_NAME = (AppiumBy.ID, TOP_USER_NAME_ID)                                     # 聊天对象昵称/群名称
    TOP_TITLE = TOP_USER_NAME                                                           # 顶部会话标题
    TOP_USER_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{TOP_USER_NAME_ID}"]')   # 聊天对象昵称 XPath
    TOP_TV_TITLE = CommonLocator.TOP_TV_TITLE
    TOP_SHORT_NUMBER = (AppiumBy.ID, f'{PACKAGE_ID}/tv_short_no')                       # 群聊ID
    GROUP_NUMBER_COUNT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_group_number_count')           # 群聊人数
    TOP_MORE_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/more')                               # 更多按钮                               # 更多按钮
    TOP_BACK_BNT = CommonLocator.TOP_IV_BACK_BTN                              # 返回按钮

    # ==================================================================================================================
    # 聊天页面底部元素定位
    # ==================================================================================================================
    CHAT_INPUT = (AppiumBy.ID, f'{PACKAGE_ID}/chat_input')                              # 聊天输入区域
    CHAT_INPUT_CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/inputContent')                    # 聊天输入框
    CHAT_INPUT_BOX = (AppiumBy.ID, f'{PACKAGE_ID}/input_box')                           # 聊天输入框
    VOICE_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/voice_input_btn')                       # 语音键盘切换按钮
    TEXT_INPUT = (AppiumBy.ID, f'{PACKAGE_ID}/text_input')                              # 输入框
    EMOJI_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/input_expression_bnt')                  # 表情按钮
    SEND_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/input_send_bnt')                         # 发送按钮
    NEW_MESSAGE_INDICATOR = (AppiumBy.ID, f'{PACKAGE_ID}/new_message_indicator')        # 导航到底部新消息提示

    # 禁言状态输入框
    NOT_IN_INPUT_BOX = (AppiumBy.ID, f'{PACKAGE_ID}/not_in')                            # 禁言状态输入框
    TPV_1 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_1')                                        # 禁言状态语音按钮
    TV_NOT_IN_TIPS_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_not_in_tips_title')          # 禁言状态提示标题
    TV_NOT_IN_TIPS = (AppiumBy.ID, f'{PACKAGE_ID}/tv_not_in_tips')                      # 禁言状态禁言时长
    TPV_2 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_2')                                        # 禁言状态表情按钮
    TPV_3 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_3')                                        # 禁言状态加号按钮

    # 点击 + 按钮展开其它功能元素
    ADD_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_bnt')                          # 添加按钮(+号按钮)
    INPUT_MORE_PAGER = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_pager')                  # 加号面板滑动区域
    INPUT_MORE_SCROLLABLE_INDICATOR = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_indicator')   # 可滑动标识

    # ==================================================================================================================
    # 聊天页面【多选菜单】元素定位
    # ==================================================================================================================
    TV_SELECT_NUM = (AppiumBy.ID, f'{PACKAGE_ID}/tv_select_num')                        # 勾选数量
    BT_SLEECT_ID = f'{PACKAGE_ID}/message_selection'
    BT_SELECT = (AppiumBy.ID, BT_SLEECT_ID)                                             # 勾选消息按钮
    BT_SELECT_NOT_FAIL = (AppiumBy.XPATH, f'//*[@resource-id="{BT_SLEECT_ID}" and not(following-sibling::*[@resource-id="{FAIL_MSG_ID}"])]')
    IV_SHARE = (AppiumBy.ID, f'{PACKAGE_ID}/multi_select_share')                        # 转发按钮
    IV_DELETE = (AppiumBy.ID, f'{PACKAGE_ID}/multi_select_delete')                      # 删除按钮

    DESIGN_BOTTOM_SHEET = (AppiumBy.ID, f'{PACKAGE_ID}/design_bottom_sheet')            # 转发弹窗
    TV_FORWARD_ONE_BY_ONE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_forward_one_by_one')        # 逐条转发
    TV_FORWARD_COMBINE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_forward_combine')              # 合并转发
    TV_CONFIRM = CommonLocator.TV_CONFIRM_BTN                                           # 确定按钮
    TV_CANCEL = CommonLocator.TV_CANCEL_BTN                                             # 取消按钮

    # ==================================================================================================================
    # 聊天页面【聊天记录（合并转发）详情页】内部元素定位
    # ==================================================================================================================
    CHAT_HISTORY_RECYCLER_ID = f'{PACKAGE_ID}/recycler'
    CHAT_HISTORY_RECYCLER_VIEW = (AppiumBy.ID, CHAT_HISTORY_RECYCLER_ID)                # 聊天记录列表容器

    CHAT_HISTORY_TIME_ID = f'{PACKAGE_ID}/tvTime'
    CHAT_HISTORY_TIME = (AppiumBy.ID, CHAT_HISTORY_TIME_ID)                             # 聊天记录时间

    # 聊天记录详情页 - 文本/提示内容
    CHAT_HISTORY_TEXT_ID = f'{PACKAGE_ID}/tv_message_text_content'
    CHAT_HISTORY_TEXT_CONTENT = (AppiumBy.ID, CHAT_HISTORY_TEXT_ID)                     # 文本/系统提示内容

    # 聊天记录详情页 - 位置消息
    CHAT_HISTORY_TITLE_ID = f'{PACKAGE_ID}/tvTitle'
    CHAT_HISTORY_TITLE = (AppiumBy.ID, CHAT_HISTORY_TITLE_ID)                           # 位置主标题
    CHAT_HISTORY_SUBTITLE_ID = f'{PACKAGE_ID}/tvSubTitle'
    CHAT_HISTORY_SUBTITLE = (AppiumBy.ID, CHAT_HISTORY_SUBTITLE_ID)                     # 位置副标题

    # 聊天记录详情页 - 名片消息
    CHAT_HISTORY_CARD_NAME_ID = f'{PACKAGE_ID}/tvName'
    CHAT_HISTORY_CARD_NAME = (AppiumBy.ID, CHAT_HISTORY_CARD_NAME_ID)                   # 名片昵称
    CHAT_HISTORY_CARD_SUB_NAME_ID = f'{PACKAGE_ID}/tvSubName'
    CHAT_HISTORY_CARD_SUB_NAME = (AppiumBy.ID, CHAT_HISTORY_CARD_SUB_NAME_ID)           # 名片账号
    CHAT_HISTORY_CARD_TAG_ID = f'{PACKAGE_ID}/tvTag'
    CHAT_HISTORY_CARD_TAG = (AppiumBy.ID, CHAT_HISTORY_CARD_TAG_ID)                     # 名片标签

    # 聊天记录详情页 - 文件消息
    CHAT_HISTORY_FILE_NAME_ID = f'{PACKAGE_ID}/tvFileName'
    CHAT_HISTORY_FILE_NAME = (AppiumBy.ID, CHAT_HISTORY_FILE_NAME_ID)                   # 文件名称
    CHAT_HISTORY_FILE_STATUS_ID = f'{PACKAGE_ID}/tvStatus'
    CHAT_HISTORY_FILE_STATUS = (AppiumBy.ID, CHAT_HISTORY_FILE_STATUS_ID)               # 文件状态/大小

    HISTORY_TITLE_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/title_layout')                  # 聊天记录详情页顶部标题栏

    # ==================================================================================================================
    # 聊天页面【撤回和删除 / 通知】相关元素定位
    # ==================================================================================================================
    # CMD 系统通知消息（如截屏、撤回通知、移除群聊等居中系统提示，特征：消息列表行内无头像）
    CMD_MESSAGE_ITEM = (
        AppiumBy.XPATH,
        f'//*[@resource-id="{MESSAGES_LIST_ID}"]/*[not(.//*[@resource-id="{AVATAR_ID}"])]//*[@resource-id="{MESSAGE_CONTENT_ID}"]'
    )

    # 删除操作二次确认和取消
    TWO_CONFIRM = CommonLocator.DIALOG_CONFIRM_BTN
    TWO_CANCEL = CommonLocator.DIALOG_CANCEL_BTN

    ALERT_TITLE = (AppiumBy.ID, "android:id/alertTitle")
    BUTTON2 = (AppiumBy.ID, "android:id/button2")
    BUTTON1 = (AppiumBy.ID, "android:id/button1")

    # 横幅通知消息定位器
    TV_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")                                    # 横幅通知发送者名称
    TV_PREVIEW = (AppiumBy.ID, f"{PACKAGE_ID}/tv_preview")                              # 横幅通知文本

    # 群公告/邀请人消息横幅
    NOTICE_ANNOUNCEMENT = (AppiumBy.ID, f'{PACKAGE_ID}/notice_announcement')
    NOTICE_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/notice_text")                            # 群公告详细文本

    # ==================================================================================================================
    # 辅助工具方法
    # ==================================================================================================================
    @classmethod
    def get_message_item_by_text(cls, text: str):
        """通过传入的文本内容精确定位消息气泡"""
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{text}")')


# =========================================================================
# 跨端通用定位器透明代理 (自动识别 Android / HarmonyOS NEXT / iOS)
# =========================================================================
from core.locator_manager import DynamicLocatorMeta
from locators.chat.core.chat_locator_hos import _ChatLocatorHos
from locators.chat.core.chat_locator_ios import _ChatLocatorIos


class ChatLocator(_ChatLocatorHos, _ChatLocatorAndroid, _ChatLocatorIos, metaclass=DynamicLocatorMeta):
    """跨端聊天核心定位器（支持 IDE Ctrl + 鼠标左键直接跳转定义，运行时按设备平台动态分发）"""

    _android_cls = _ChatLocatorAndroid
    _harmony_cls = _ChatLocatorHos
    _ios_cls = _ChatLocatorIos
