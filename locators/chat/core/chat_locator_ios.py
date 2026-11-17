# -*- coding: utf-8 -*-
"""
iOS 平台聊天会话核心页面元素定位器 (XCUITest / WebDriverAgent 原生架构)
全面规范化为 Apple 官方 XCUIElementType* 元素类型与高效定位策略 (Predicate / Class Chain / Accessibility ID)
与 _ChatLocatorAndroid 保持 100% 接口、字段与注释对齐，覆盖消息列表流、多类型消息气泡、输入与加号面板、多选转发及详情页。
核心原则：有 name 属性就不冗余使用 label，保持表达式最纯粹高效。
"""
from typing import Tuple
from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_ios import _CommonLocatorIos


class _ChatLocatorIos:
    """
    iOS 平台聊天会话核心页面元素定位器 (XCUITest / WebDriverAgent 原生架构)

    定位策略优先级 (按 XCUITest 原生性能与稳定性排序)：
    1. ACCESSIBILITY_ID：对应 accessibilityIdentifier，哈希索引直达，最稳定首选；
    2. IOS_PREDICATE：NSPredicate 原生谓词，组合 XCUIElementType 与 name 过滤，不依赖视图层级；
    3. IOS_CLASS_CHAIN：原生层级链，用于精准父子/后代遍历；
    4. XPATH：规范使用 XCUIElementType* 前缀，仅用于复杂祖先/跨分支反向锚定场景。

    注意：本类不继承 CommonLocator。DynamicLocatorProxy 在类定义阶段解析基类，
    若继承会固化为 Android 基类，导致 iOS 页面继承到 resource-id 定位器。
    """

    # iOS 应用 Bundle ID
    PACKAGE_ID = _CommonLocatorIos.PACKAGE_ID

    # 静态文本类控件类型集合
    _TEXT_TYPES = "{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}"
    # 可点击类控件类型集合
    _BUTTON_TYPES = "{'XCUIElementTypeButton'}"

    # ==================================================================================================================
    # 聊天页面基础列表与行容器
    # ==================================================================================================================
    MESSAGES_LIST_ID = "messages"                                                       # 消息列表 RecyclerView (iOS 对应 Table)
    MESSAGES_LIST_ITEM = (                                                              # 消息列表
        AppiumBy.IOS_PREDICATE,
        'type == "XCUIElementTypeTable"',
    )

    # 消息行容器 (RecyclerView 下的各个 android.view.ViewGroup 消息行 / iOS 对应 Cell 单元格)
    MESSAGE_LAYOUT_XPATH = "//XCUIElementTypeCell"
    MESSAGE_LAYOUT_ITEM = (                                                             # 消息行容器
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeCell'",
    )

    # 头像相关
    AVATAR_ID = "avatar"
    AVATAR_ITEM = (                                                                     # 统一头像
        AppiumBy.XPATH,
        "//XCUIElementTypeCell/XCUIElementTypeImage[2]",
    )

    # 已读未读标识
    READ_STATUS_ID = "read_status"                                                      # 新版已读未读状态 ID
    READ_STATUS_ITEM = (                                                                # 已读未读状态控件
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name IN {'未读', '已读'}",
    )

    # 发送状态/失败红点
    FAIL_MSG_ID = "delivery_status"
    FAIL_MSG = (                                                                        # 消息发送状态/失败红点
        AppiumBy.ACCESSIBILITY_ID,
        "ic chat failed to send",
    )

    # 群聊页面显示用户昵称
    GROUP_CHAT_USER_NAME_ID = "sender_name"
    GROUP_CHAT_USER_NAME_ITEM = (                                                       # 用户名
        AppiumBy.XPATH,
        "//XCUIElementTypeCell/XCUIElementTypeImage/following-sibling::XCUIElementTypeStaticText",
    )

    # ==================================================================================================================
    # 核心消息类型定位器（一物一元组）
    # ==================================================================================================================
    # 1. 文本 / Emoji 消息
    MESSAGE_CONTENT_ID = "message_text"
    MESSAGE_CONTENT_ITEM = (                                                            # 文本内容
        AppiumBy.XPATH,
        "//XCUIElementTypeCell/XCUIElementTypeTextView/XCUIElementTypeTextView",
    )
    TEXT_MESSAGE_VIEW_XPATH = MESSAGE_CONTENT_ITEM

    # 2. 图片 / 动态表情包
    IMAGE_ID = "message_image"
    IMAGE_ITEM = (                                                                      # 图片/表情包
        AppiumBy.XPATH,
        "//XCUIElementTypeOther/XCUIElementTypeImage",
    )
    PREVIEW_IMAGE_ID = "preview_image"
    PREVIEW_IMAGE_ITEM = (                                                              # 预览图片
        AppiumBy.XPATH,
        "//XCUIElementTypeOther/XCUIElementTypeScrollView/XCUIElementTypeImage",
    )
    IV_DOWNLOAD_ID = "iv_download"
    IV_DOWNLOAD_ITEM = (                                                                # 下载图标
        AppiumBy.ACCESSIBILITY_ID,
        "st photo browser down",
    )

    # 3. 视频消息 TODO：IOS没有播放按钮元素
    VIDEO_PLAY_BUTTON_ID = "video_cover"
    VIDEO_PLAY_BUTTON_ITEM = (                                                          # 视频播放按钮 / 封面
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeButton[contains(@name, 'play') or contains(@name, '播放')] | //XCUIElementTypeCell//XCUIElementTypeImage[contains(@name, 'video')]",
    )
    VIDEO_DURATION_ID = "duration"
    VIDEO_DURATION_ITEM = (                                                             # 视频时长
        AppiumBy.XPATH,
        "//XCUIElementTypeCell/XCUIElementTypeStaticText[contains(@name, ':')]",
    )

    # 4. 语音消息
    AUDIO_BUBBLE_ID = "audio_bubble"
    AUDIO_BUBBLE = (                                                                    # 语音气泡 (匹配含秒数双引号 " 或秒的语音时长文本)
        AppiumBy.XPATH,
        '//XCUIElementTypeCell/XCUIElementTypeStaticText[contains(@name, \'"\')]',
    )

    # 5. 定位消息
    LOCATION_CARD_XPATH = "//XCUIElementTypeCell[.//XCUIElementTypeImage[starts-with(@name, 'ic_avatar_decoration')] and count(.//XCUIElementTypeStaticText) >= 2 and not(.//XCUIElementTypeStaticText[contains(@name, '个人名片') or contains(@name, '群名片')])]"
    LOCATION_CARD_ITEM = (                                                              # 定位卡片容器
        AppiumBy.XPATH,
        f"{LOCATION_CARD_XPATH}",
    )
    LOCATION_MESSAGE_TITLE_ID = "location_title"
    LOCATION_MESSAGE_TITLE = (                                                          # 定位主标题
        AppiumBy.XPATH,
        f"{LOCATION_CARD_XPATH}/",
    )
    LOCATION_MESSAGE_SUBTITLE_ID = "location_subtitle"
    LOCATION_MESSAGE_SUBTITLE = (                                                       # 定位副标题/详细地址
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeImage[contains(@name, 'location') or contains(@name, 'map') or contains(@name, '位置')]]//XCUIElementTypeStaticText[2]",
    )

    # 6. 名片消息
    PROFILE_CARD_ID = "profile_card"
    PROFILE_CARD_ITEM = (                                                               # 名片卡片容器
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '个人名片') or contains(@name, '名片') or contains(@name, 'ST号')]]",
    )
    CARD_NICKNAME_ID = "card_title"
    CARD_NICKNAME_ITEM = (                                                              # 名片昵称/标题
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '名片')]]//XCUIElementTypeStaticText[1]",
    )
    CARD_ST_ID = "card_subtitle"
    CARD_ST_ITEM = (                                                                    # 名片账号/ST号
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '名片')]]//XCUIElementTypeStaticText[contains(@name, 'ST') or contains(@name, '号') or contains(@name, '账号')]",
    )
    CARD_TAG_ID = "card_kind"
    CARD_TAG = (                                                                        # 名片类型标签
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '名片')]]//XCUIElementTypeStaticText[contains(@name, '个人名片') or contains(@name, '公众号') or contains(@name, '名片')]",
    )

    # 7. 文件消息
    FILE_CARD_ID = "file_card"
    FILE_CARD_ITEM = (                                                                  # 文件卡片容器
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeImage[contains(@name, 'file') or contains(@name, 'doc') or contains(@name, 'pdf') or contains(@name, '文件')]]",
    )
    FILE_NAME_ID = "file_name"
    FILE_NAME_ITEM = (                                                                  # 文件名
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeImage[contains(@name, 'file') or contains(@name, '文件')]]//XCUIElementTypeStaticText[1]",
    )
    FILE_STATUS_ID = "file_status"
    FILE_STATUS_ITEM = (                                                                # 文件状态
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeImage[contains(@name, 'file') or contains(@name, '文件')]]//XCUIElementTypeStaticText[contains(@name, '已下载') or contains(@name, '未下载') or contains(@name, '已发送')]",
    )
    FILE_SIZE_ID = "file_meta"
    FILE_SIZE_ITEM = (                                                                  # 文件大小/元数据
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeImage[contains(@name, 'file') or contains(@name, '文件')]]//XCUIElementTypeStaticText[contains(@name, 'B') or contains(@name, 'KB') or contains(@name, 'MB') or contains(@name, 'GB')]",
    )
    FILE_LINE_ID = "file_line"
    FILE_LINE_ITEM = (                                                                  # 分隔线
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeImage[contains(@name, 'file') or contains(@name, '文件')]]//XCUIElementTypeOther[1]",
    )

    # 8. 聊天记录（合并转发）卡片
    MERGE_CARD_ID = "merge_card"
    MERGE_CARD_MSG = (                                                                  # 合并转发卡片容器
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '聊天记录')]]",
    )
    MERGE_CARD_TITLE = (                                                                # 合并转发标题
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '聊天记录')]]//XCUIElementTypeStaticText[1]",
    )
    MERGE_CARD_PREVIEW = (                                                              # 合并转发预览文本
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '聊天记录')]]//XCUIElementTypeStaticText[2]",
    )
    MERGE_CARD_KIND = (                                                                 # 合并转发类型底部标签文本
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[contains(@name, '聊天记录')]",
    )

    # 9. 停用账号/封禁提示
    DISABLE_MESSAGE_TIP = (                                                             # 停用账号/封禁提示
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name CONTAINS '对方账号无法使用'",
    )

    # 10. 音视频通话记录卡片消息 (Call Card)
    CALL_CARD_ID = "call_card"
    CALL_CARD_ITEM = (                                                                  # 通话卡片容器
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '通话') or contains(@name, '来电') or contains(@name, '已取消') or contains(@name, '已拒绝')]]",
    )
    CALL_TITLE_ID = "call_title"
    CALL_TITLE_ITEM = (                                                                 # 通话卡片主标题 (如 "未接来电" / "已取消" / "已拒绝" / "通话时长 00:03")
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[contains(@name, '未接来电') or contains(@name, '已取消') or contains(@name, '已拒绝') or contains(@name, '通话时长')]",
    )
    CALL_SUBTITLE_ID = "call_subtitle"
    CALL_SUBTITLE_ITEM = (                                                              # 通话卡片副标题 (如 "轻触回拨")
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[contains(@name, '轻触回拨') or contains(@name, '再次呼叫')]",
    )

    # ==================================================================================================================
    # 聊天页面顶部元素定位
    # ==================================================================================================================
    TOP_BACK_UNREAD_BG = (                                                              # 返回未读背景
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar/XCUIElementTypeButton[1]",
    )
    TOP_IV_BACK_BTN = _CommonLocatorIos.TOP_IV_BACK_BTN
    TOP_BACK_BUTTON = _CommonLocatorIos.TOP_IV_BACK_BTN                                  # 返回按钮
    TOP_BACK_BNT = _CommonLocatorIos.TOP_IV_BACK_BTN                                     # 返回按钮
    TOP_BACK_UNREAD_BADGE = (                                                           # 返回按钮未读数角标
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar/XCUIElementTypeButton[1]//XCUIElementTypeStaticText",
    )
    TOP_USER_NAME_ID = "title"
    TOP_USER_NAME = (                                                                   # 聊天对象昵称/群名称
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar//XCUIElementTypeStaticText[1]",
    )
    TOP_TITLE = TOP_USER_NAME                                                           # 顶部会话标题
    TOP_USER_NAME_XPATH = (                                                             # 聊天对象昵称 XPath
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar//XCUIElementTypeStaticText[1]",
    )
    TOP_TV_TITLE = _CommonLocatorIos.TOP_TV_TITLE
    TOP_SHORT_NUMBER = (                                                                # 群聊ID
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar//XCUIElementTypeStaticText[contains(@name, 'ID') or contains(@name, '群号')]",
    )
    GROUP_NUMBER_COUNT = (                                                              # 群聊人数
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar//XCUIElementTypeStaticText[contains(@name, '(') and contains(@name, ')')]",
    )
    TOP_MORE_BUTTON = (                                                                 # 更多按钮
        AppiumBy.IOS_CLASS_CHAIN,
        "**/XCUIElementTypeNavigationBar/XCUIElementTypeButton[-1]",
    )

    # ==================================================================================================================
    # 聊天页面底部元素定位
    # ==================================================================================================================
    CHAT_INPUT = (                                                                      # 聊天输入区域
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[XCUIElementTypeTextView]/parent::XCUIElementTypeOther/parent::XCUIElementTypeOther",
    )
    CHAT_INPUT_CONTENT = (                                                              # 聊天输入框
        AppiumBy.XPATH,
        "//XCUIElementTypeOther/XCUIElementTypeTextView",
    )
    CHAT_INPUT_BOX = CHAT_INPUT_CONTENT                                                 # 聊天输入框
    VOICE_BUTTON = (                                                                    # 语音键盘切换按钮 (输入框左侧紧邻切换按钮)
        AppiumBy.XPATH,
        "(//XCUIElementTypeTextView/preceding::XCUIElementTypeButton)[last()]",
    )
    TEXT_INPUT = (                                                                      # 输入框
        AppiumBy.XPATH,
        "//XCUIElementTypeOther/XCUIElementTypeTextView",
    )
    EMOJI_BUTTON = (                                                                    # 表情按钮 (输入框内嵌表情切换按钮)
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[.//XCUIElementTypeTextView]/XCUIElementTypeButton[1]",
    )
    VOICE_BUTTON1 = (                                                                   # 语音输入按钮
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[.//XCUIElementTypeTextView]/XCUIElementTypeButton[1]",
    )
    SEND_BUTTON = (                                                                     # 发送按钮 (输入框右下角主操作按钮)
        AppiumBy.XPATH,
        "(//XCUIElementTypeButton)[last()]",
    )
    NEW_MESSAGE_INDICATOR = (                                                           # 导航到底部新消息提示
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeButton', 'XCUIElementTypeStaticText'} AND name CONTAINS '新消息'",
    )

    # 禁言状态输入框
    NOT_IN_INPUT_BOX = (                                                                # 禁言状态输入框
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name CONTAINS '全员禁言' OR name CONTAINS '已被禁言')",
    )
    TPV_1 = VOICE_BUTTON                                                                # 禁言状态语音按钮
    TV_NOT_IN_TIPS_TITLE = (                                                            # 禁言状态提示标题
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name CONTAINS '禁言'",
    )
    TV_NOT_IN_TIPS = (                                                                  # 禁言状态禁言时长
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name CONTAINS '分钟' OR name CONTAINS '小时' OR name CONTAINS '解除')",
    )
    TPV_2 = EMOJI_BUTTON                                                                # 禁言状态表情按钮
    TPV_3 = SEND_BUTTON                                                                 # 禁言状态加号按钮

    # 点击 + 按钮展开其它功能元素
    ADD_BUTTON = SEND_BUTTON                                                            # 添加按钮(+号按钮)
    INPUT_MORE_PAGER = (                                                                # 加号面板滑动区域
        AppiumBy.XPATH,
        "//XCUIElementTypeCollectionView | //XCUIElementTypeScrollView[.//XCUIElementTypeButton]",
    )
    INPUT_MORE_SCROLLABLE_INDICATOR = (                                                 # 可滑动标识
        AppiumBy.XPATH,
        "//XCUIElementTypePageIndicator",
    )

    # ==================================================================================================================
    # 聊天页面【多选菜单】元素定位
    # ==================================================================================================================
    TV_SELECT_NUM = (                                                                   # 勾选数量
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name CONTAINS '已选择' OR name CONTAINS '项')",
    )
    BT_SLEECT_ID = "message_selection"
    BT_SELECT = (                                                                       # 勾选消息按钮
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeButton[contains(@name, 'select') or contains(@name, 'check') or contains(@name, 'choice') or contains(@name, '选择')]",
    )
    BT_SELECT_NOT_FAIL = BT_SELECT
    IV_SHARE = (                                                                        # 转发按钮
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND (name CONTAINS '转发' OR name CONTAINS 'share')",
    )
    IV_DELETE = (                                                                       # 删除按钮
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND (name CONTAINS '删除' OR name CONTAINS 'delete')",
    )

    DESIGN_BOTTOM_SHEET = (                                                             # 转发弹窗
        AppiumBy.XPATH,
        "//XCUIElementTypeActionSheet | //XCUIElementTypeSheet | //XCUIElementTypeAlert",
    )
    TV_FORWARD_ONE_BY_ONE = (                                                           # 逐条转发
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name CONTAINS '逐条转发'",
    )
    TV_FORWARD_COMBINE = (                                                              # 合并转发
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name CONTAINS '合并转发'",
    )
    TV_CONFIRM = _CommonLocatorIos.DIALOG_CONFIRM_BTN                                    # 确定按钮
    TV_CANCEL = _CommonLocatorIos.DIALOG_CANCEL_BTN                                      # 取消按钮

    # ==================================================================================================================
    # 聊天页面【聊天记录（合并转发）详情页】内部元素定位
    # ==================================================================================================================
    CHAT_HISTORY_RECYCLER_ID = "recycler"
    CHAT_HISTORY_RECYCLER_VIEW = (                                                      # 聊天记录列表容器
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeTable', 'XCUIElementTypeCollectionView', 'XCUIElementTypeScrollView'}",
    )

    CHAT_HISTORY_TIME_ID = "tvTime"
    CHAT_HISTORY_TIME = (                                                               # 聊天记录时间
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[contains(@name, ':')]",
    )

    # 聊天记录详情页 - 文本/提示内容
    CHAT_HISTORY_TEXT_ID = "tv_message_text_content"
    CHAT_HISTORY_TEXT_CONTENT = (                                                       # 文本/系统提示内容
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[1]",
    )

    # 聊天记录详情页 - 位置消息
    CHAT_HISTORY_TITLE_ID = "tvTitle"
    CHAT_HISTORY_TITLE = (                                                              # 位置主标题
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[1]",
    )
    CHAT_HISTORY_SUBTITLE_ID = "tvSubTitle"
    CHAT_HISTORY_SUBTITLE = (                                                           # 位置副标题
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[2]",
    )

    # 聊天记录详情页 - 名片消息
    CHAT_HISTORY_CARD_NAME_ID = "tvName"
    CHAT_HISTORY_CARD_NAME = (                                                          # 名片昵称
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[1]",
    )
    CHAT_HISTORY_CARD_SUB_NAME_ID = "tvSubName"
    CHAT_HISTORY_CARD_SUB_NAME = (                                                      # 名片账号
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[2]",
    )
    CHAT_HISTORY_CARD_TAG_ID = "tvTag"
    CHAT_HISTORY_CARD_TAG = (                                                           # 名片标签
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[contains(@name, '名片')]",
    )

    # 聊天记录详情页 - 文件消息
    CHAT_HISTORY_FILE_NAME_ID = "tvFileName"
    CHAT_HISTORY_FILE_NAME = (                                                          # 文件名称
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[1]",
    )
    CHAT_HISTORY_FILE_STATUS_ID = "tvStatus"
    CHAT_HISTORY_FILE_STATUS = (                                                        # 文件状态/大小
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[2]",
    )

    HISTORY_TITLE_LAYOUT = (                                                            # 聊天记录详情页顶部标题栏
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar",
    )

    # ==================================================================================================================
    # 聊天页面【撤回和删除 / 通知】相关元素定位
    # ==================================================================================================================
    # CMD 系统通知消息（如截屏、撤回通知、移除群聊等居中系统提示，特征：消息行内无头像）
    CMD_MESSAGE_ITEM = (
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[not(.//XCUIElementTypeImage)]//XCUIElementTypeStaticText",
    )

    # 删除操作二次确认和取消
    TWO_CONFIRM = _CommonLocatorIos.DIALOG_CONFIRM_BTN
    TWO_CANCEL = _CommonLocatorIos.DIALOG_CANCEL_BTN

    ALERT_TITLE = (
        AppiumBy.XPATH,
        "//XCUIElementTypeAlert//XCUIElementTypeStaticText[1]",
    )
    BUTTON2 = _CommonLocatorIos.DIALOG_CANCEL_BTN
    BUTTON1 = _CommonLocatorIos.DIALOG_CONFIRM_BTN

    # 横幅通知消息定位器
    TV_NAME = (                                                                         # 横幅通知发送者名称
        AppiumBy.XPATH,
        "//XCUIElementTypeBanner//XCUIElementTypeStaticText[1] | //XCUIElementTypeWindow[2]//XCUIElementTypeStaticText[1]",
    )
    TV_PREVIEW = (                                                                      # 横幅通知文本
        AppiumBy.XPATH,
        "//XCUIElementTypeBanner//XCUIElementTypeStaticText[2] | //XCUIElementTypeWindow[2]//XCUIElementTypeStaticText[2]",
    )

    # 群公告/邀请人消息横幅
    NOTICE_ANNOUNCEMENT = (
        AppiumBy.XPATH,
        "//*[contains(@name, '公告') or contains(@name, '群公告')]",
    )
    NOTICE_TEXT = (                                                                     # 群公告详细文本
        AppiumBy.XPATH,
        "//*[contains(@name, '公告') or contains(@name, '群公告')]//XCUIElementTypeStaticText",
    )

    # ==================================================================================================================
    # 辅助工具方法
    # ==================================================================================================================
    @classmethod
    def get_message_item_by_text(cls, text: str) -> Tuple[str, str]:
        """通过传入的文本内容精确定位消息气泡"""
        safe_text = text.replace("'", "\\'")
        return (
            AppiumBy.IOS_PREDICATE,
            f"type IN {{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}} AND name CONTAINS '{safe_text}'",
        )
