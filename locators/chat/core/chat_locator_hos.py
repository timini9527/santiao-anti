from appium.webdriver.common.appiumby import AppiumBy
from locators.common.hos_by import HosBy


class _ChatLocatorHos:
    """
    鸿蒙 NEXT 平台聊天会话核心页面定位器 (HarmonyOS ArkUI 专享架构)
    底层原生支持 ArkUI 控件标签 (Text, Button, Image, List, ListItem, TextInput, TextArea, Row, Column, Stack, Flex, NavDestination 等)
    全面覆盖聊天页面消息流、输入交互、多媒体气泡、顶部导航、加号面板与长按上下文操作。
    """

    # ==================================================================================================================
    # 1. 聊天页面基础列表与行容器 (Message List & Item Rows)
    # ==================================================================================================================
    # 消息列表主滚动容器 (ArkUI List 组件，原生 type 直查)
    MESSAGES_LIST_ID = "__ChatMessagesList__"
    MESSAGES_LIST_ITEM = HosBy.type_only("List")

    # 消息单行容器 (每个消息气泡所属的 ListItem 容器)
    MESSAGE_LAYOUT_XPATH = "//ListItem//Row[2]"
    MESSAGE_LAYOUT_ITEM = (AppiumBy.XPATH, MESSAGE_LAYOUT_XPATH)

    # 消息行内头像 (统一头像图片，位于卡片边缘首个 Image)
    AVATAR_ID = "__MessageAvatar__"
    AVATAR_ITEM = (AppiumBy.XPATH, "//ListItem//Row[2]//Stack/Image")

    # 已读未读标识 (位于发送方消息气泡旁侧)
    READ_STATUS_ID = "__MessageReadStatus__"
    READ_STATUS_ITEM = (AppiumBy.XPATH, "//ListItem//Row[3]/Text")

    # 发送状态 / 发送失败叹号红点
    FAIL_MSG_ID = "__MessageDeliveryFail__"
    FAIL_MSG = (
        AppiumBy.XPATH,
        "//ListItem//Row/Column/Row/Image"
    )

    # 群聊页面显示发送者用户昵称 (气泡上方显示的用户名文本)
    GROUP_CHAT_USER_NAME_ID = "__MessageSenderName__"
    GROUP_CHAT_USER_NAME_ITEM = (AppiumBy.XPATH, "//ListItem//Row[2]//Column/Row/Text")


    # ==================================================================================================================
    # 2. 核心消息类型定位器（一物一元组，严格映射各类型气泡）
    # ==================================================================================================================
    # 2.1 文本 / Emoji 消息
    MESSAGE_CONTENT_ID = "__TextMessageContent__"
    MESSAGE_CONTENT_ITEM = (
        AppiumBy.XPATH,
        "//ListItem//Row//JsView/Column//Text"
    )
    TEXT_MESSAGE_VIEW_XPATH = MESSAGE_CONTENT_ITEM

    # 2.2 图片 / 动态表情包
    IMAGE_ID = "__ImageMessageContent__"
    IMAGE_ITEM = (AppiumBy.XPATH, "//ListItem//Row[2]//Stack//__Common__/Stack/Image")
    PREVIEW_IMAGE_ID = "__ImagePreview__"
    PREVIEW_IMAGE_ITEM = (AppiumBy.XPATH, "//ListItem//Row//Stack/Stack/__Common__/Image")
    # 预览图片保存按钮 (原生 SaveButton 组合直查)
    IV_DOWNLOAD_ID = "__ImageDownload__"
    IV_DOWNLOAD_ITEM = HosBy.type_text("SaveButton", "保存")
    # 预览图片顶部数字（如 1/6）
    IV_IMAGE_PAGE_TEXT = (AppiumBy.XPATH, "//Dialog//Stack/Row/Text")

    # 2.3 视频消息与时长
    VIDEO_PLAY_BUTTON_ID = "__VideoPlayButton__"
    VIDEO_PLAY_BUTTON_ITEM = (
        AppiumBy.XPATH,
        "//ListItem//Row[2]//Stack/Stack[2]"
    )
    VIDEO_DURATION_ID = "__VideoDuration__"
    VIDEO_DURATION_ITEM = (AppiumBy.XPATH, "//ListItem//Row[2]//Stack/Stack[2]//Text")

    # 2.4 语音消息 (语音播放条与时长气泡)
    AUDIO_BUBBLE_ID = "__AudioBubble__"
    AUDIO_BUBBLE = (
        AppiumBy.XPATH,
        "//ListItem//Row//Row/Text"
    )

    # 2.5 定位消息 (位置卡片容器、标题与副标题)
    LOCATION_CARD_ID = "__LocationCard__"
    LOCATION_CARD_ITEM = (AppiumBy.XPATH, "//ListItem//Row//Row/Stack/Column/Stack")
    LOCATION_MESSAGE_TITLE_ID = "__LocationTitle__"
    LOCATION_MESSAGE_TITLE = (AppiumBy.XPATH, "//ListItem//Row//Row/Stack/Column/Stack/Row/following-sibling::Column/Text[1]")
    LOCATION_MESSAGE_SUBTITLE_ID = "__LocationSubtitle__"
    LOCATION_MESSAGE_SUBTITLE = (AppiumBy.XPATH, "//ListItem//Row//Row/Stack/Column/Stack/Row/following-sibling::Column/Text[2]")

    # 2.6 名片消息 (个人名片卡片容器、昵称与ST账号)
    PROFILE_CARD_ID = "__ProfileCard__"
    PROFILE_CARD_ITEM = (AppiumBy.XPATH, "//ListItem//Row//__Common__/Column")
    CARD_NICKNAME_ID = "__CardNickname__"
    CARD_NICKNAME_ITEM = (AppiumBy.XPATH, "//ListItem//Row//__Common__/Column//Row/Column/Row[1]/Text")
    CARD_ST_ID = "__CardSTNumber__"
    CARD_ST_ITEM = (AppiumBy.XPATH, "//ListItem//Row//__Common__/Column//Row/Column/Row[2]/Text")
    CARD_TAG_ID = "__CardTag__"
    CARD_TAG = (AppiumBy.XPATH, "//ListItem//Row//__Common__/Column/Row/Text")

    # 2.7 文件消息 (文件卡片容器、文件名、文件大小、状态、分割线、文件图标)
    FILE_CARD_ID = "__FileCard__"
    FILE_CARD_ITEM = (AppiumBy.XPATH, "//ListItem//Row/Column/Row//Stack//Stack/Column/Row/Column")
    FILE_NAME_ID = "__FileName__"
    FILE_NAME_ITEM = (AppiumBy.XPATH, "//ListItem//Row/Column/Row//Stack//Stack/Column/Row/Column/Text")
    FILE_STATUS_ID = "__FileStatus__"
    FILE_STATUS_ITEM = (AppiumBy.XPATH, "//ListItem//Row/Column/Row//Stack//Stack/Column/Row/Column/Text")
    FILE_SIZE_ID = "__FileSize__"
    FILE_SIZE_ITEM = (AppiumBy.XPATH, "//ListItem//Row/Column/Row//Stack//Stack/Column/Row/Column/Row/Text[last()]")
    FILE_LINE_ID = "__FileLine__"
    FILE_LINE_ITEM = (AppiumBy.XPATH, "//ListItem//Row/Column/Row//Stack//Stack/Column/Row/Column/Row/Divider")
    FILE_ICON_ID = "__FileIcon__"
    FILE_ICON_ITEM = (AppiumBy.XPATH, "//ListItem//Row/Column/Row//Stack//Stack/Column/Row/Image")

    # 2.8 聊天记录（合并转发）卡片
    MERGE_CARD_ID = "__MergeCard__"
    MERGE_CARD_MSG = (AppiumBy.XPATH, "//ListItem//Row//Column/Text[contains(@text,'聊天记录')]/parent::Column")
    MERGE_CARD_TITLE = (AppiumBy.XPATH, "//ListItem//Column//Text[contains(@text, '的聊天记录')]")
    MERGE_CARD_PREVIEW = (AppiumBy.XPATH, "//ListItem//Column//Text[contains(@text, '的聊天记录')]/following-sibling::Text")
    MERGE_CARD_KIND = (AppiumBy.XPATH, "//ListItem//Column//Text[contains(@text, '的聊天记录')]/following-sibling::Text[last()]")

    # 2.9 停用账号 / 封禁提示 (原生 HypiumBy 文本直查)
    DISABLE_MESSAGE_TIP = HosBy.type_text("Text", "对方账号已无法使用 详情")

    # 2.10 音视频通话记录卡片 (Call Card) TODO：鸿蒙还没有做，等待优化
    CALL_CARD_ID = "__CallCard__"
    CALL_CARD_ITEM = (
        AppiumBy.XPATH,
        "//ListItem//Row//Stack/Text"
    )
    CALL_TITLE_ID = "__CallTitle__"
    CALL_TITLE_ITEM = (
        AppiumBy.XPATH,
        "//ListItem//Text[contains(@text, '通话') or contains(@text, '未接') or contains(@text, '已取消') or contains(@text, '已拒绝')]"
    )
    CALL_SUBTITLE_ID = "__CallSubtitle__"
    CALL_SUBTITLE_ITEM = (AppiumBy.XPATH, "//ListItem//Text[contains(@text, '轻触回拨') or contains(@text, '再次呼叫')]")


    # ==================================================================================================================
    # 3. 聊天页面顶部全局导航栏 (Top Navigation Bar)
    # ==================================================================================================================
    # 顶部左侧返回按钮 (NavDestination 标题栏首个图标)
    TOP_BACK_BUTTON = (
        AppiumBy.XPATH,
        "//NavDestination//Stack/Stack/__Common__//Row//Row/Image"
    )
    TOP_BACK_BNT = TOP_BACK_BUTTON

    # 顶部返回按钮未读数背景与角标文本
    TOP_BACK_UNREAD_BG = (AppiumBy.XPATH, "//NavDestinationTitleBar//Badge | //Row[1]//Badge")
    TOP_BACK_UNREAD_BADGE = (AppiumBy.XPATH, "//NavDestination//Stack/Stack/__Common__//Row//Row/Text")

    # 顶部聊天对象昵称 / 群名称
    TOP_USER_NAME_ID = "__TopUserName__"
    TOP_USER_NAME = (
        AppiumBy.XPATH,
        "//NavDestination//Stack/Stack/__Common__/Stack/Column/Row/Text"
    )
    TOP_USER_NAME_XPATH = TOP_USER_NAME

    # 顶部群聊短号 / 群 ID 文本
    TOP_SHORT_NUMBER = (
        AppiumBy.XPATH,
        "//NavDestination//Stack/Stack/__Common__/Stack/Column/Text"
    )

    # 顶部群聊人数统计 (如 "大群(40)")
    GROUP_NUMBER_COUNT = (
        AppiumBy.XPATH,
        "//NavDestination//Stack/Stack/__Common__/Stack/Column/Row/Text"
    )

    # 顶部右上角更多 "..." 菜单入口按钮 (单聊/群聊信息设置中心)
    TOP_MORE_BUTTON = (
        AppiumBy.XPATH,
        "//NavDestination//Stack/Stack/__Common__/Stack/Row/Column//Stack/Image"
    )


    # ==================================================================================================================
    # 4. 聊天页面底部输入交互区域 (Bottom Input Bar)
    # ==================================================================================================================
    # 底部输入整行容器
    CHAT_INPUT = (AppiumBy.XPATH, "//NavDestination//Stack/__Common__//Column/Stack/Column/Row")

    # 文本输入框 (TextInput / TextArea / RichEditor)
    CHAT_INPUT_CONTENT = (AppiumBy.XPATH, "")
    CHAT_INPUT_BOX = (AppiumBy.XPATH, "//TextInput | //TextArea")
    TEXT_INPUT = HosBy.type_only("RichEditor")

    # 语音 / 键盘切换按钮
    VOICE_BUTTON = (
        AppiumBy.XPATH,
        "//NavDestination//Stack/__Common__//Column/Stack/Column/Row/Column/Stack/Image"
    )

    # 表情按钮
    EMOJI_BUTTON = (
        AppiumBy.XPATH,
        "//Row[.//TextInput or .//TextArea]//Image[last()-1] | //Image[@id='emoji']"
    )

    # 扩展 "+" 号更多功能面板展开按钮
    ADD_BUTTON = (
        AppiumBy.XPATH,
        "//NavDestination//Stack/__Common__//Column/Stack/Column/Row/Stack/Image"
    )
    INPUT_MORE_PAGER = (AppiumBy.XPATH, "//Grid | //Scroll[.//Text[@text='图片' or @text='拍摄']]")
    INPUT_MORE_SCROLLABLE_INDICATOR = HosBy.type_only("Swiper")

    # 发送按钮 (文本变动后显示为 "发送")
    SEND_BUTTON = (
        AppiumBy.XPATH,
        "//NavDestination//Stack/__Common__//Column/Stack/Column/Row/Row//Row/Stack/Image"
    )

    # 底部新消息悬浮定位提示 (如 "X 条新消息" 气泡)
    NEW_MESSAGE_INDICATOR = (
        AppiumBy.XPATH,
        "//NavDestination//Stack//__Common__/Stack/Stack/Stack/Image"
    )

    # 禁言状态输入区域
    NOT_IN_INPUT_BOX = (AppiumBy.XPATH, "//NavDestination//Stack//__Common__/Stack/Column/Row/Row")
    TV_NOT_IN_TIPS = (AppiumBy.XPATH, "//Text[contains(@text, '禁言')]")
    TV_NOT_IN_TIPS_TITLE = (AppiumBy.XPATH, "//NavDestination//Stack//__Common__/Stack/Column/Row/Row/Text")
    TPV_1 = (AppiumBy.XPATH, "//NavDestination//Stack//__Common__/Stack/Column/Row/Stack")
    TPV_2 = (AppiumBy.XPATH, "//NavDestination//Stack//__Common__/Stack/Column/Row/Row/Image")
    TPV_3 = (AppiumBy.XPATH, "//NavDestination//Stack//__Common__/Stack/Column/Row/Stack[last()]")


    # ==================================================================================================================
    # 5. 聊天页面【多选模式】底部操作栏 (Multi-Select Menu)
    # ==================================================================================================================
    # 已勾选消息计数文本 (如 "已选择 2 项")
    TV_SELECT_CANCLE = (AppiumBy.XPATH, "//NavDestination//Stack//__Common__/Stack/Row/Column/Row/Text")
    TV_SELECT_NUM = (AppiumBy.XPATH, "//NavDestination//Stack//__Common__/Stack/Row/Column[2]/Row/Text")
    

    # 列表单行勾选圈选复选框
    BT_SLEECT_ID = "__MessageSelectionCheckbox__"
    BT_SELECT = (AppiumBy.XPATH, "//ListItem/Column/Column/Row/Image")
    BT_SELECT_NOT_FAIL = BT_SELECT

    # 底部合并转发与删除按钮
    IV_SHARE = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Stack/Column/Row/Image")
    IV_DELETE = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Stack/Column/Row/Image[2]")

    # 转发方式底部弹窗 (ActionSheet / Dialog)
    DESIGN_BOTTOM_SHEET = HosBy.type_only("Dialog")
    TV_FORWARD_ONE_BY_ONE = HosBy.type_text("Text", "逐条转发")
    TV_FORWARD_COMBINE = HosBy.type_text("Text", "合并转发")
    TV_CONFIRM = (AppiumBy.XPATH, "//Dialog//Column/Text[@text='确定']")
    TV_CANCEL = (AppiumBy.XPATH, "//Dialog/Column/Column/Text[@text='取消']")

    # ==================================================================================================================
    # 6. 聊天记录（合并转发）详情页内部结构 (Chat History Detail Page)
    # ==================================================================================================================
    CHAT_HISTORY_RECYCLER_ID = "__ChatHistoryList__"
    CHAT_HISTORY_RECYCLER_VIEW = HosBy.type_only("List")

    CHAT_HISTORY_TIME_ID = "__ChatHistoryTime__"
    CHAT_HISTORY_TIME = (AppiumBy.XPATH, "//ListItem//Text[contains(@text, ':')]")

    # 详情页文本与系统通知内容
    CHAT_HISTORY_TEXT_ID = "__ChatHistoryText__"
    CHAT_HISTORY_TEXT_CONTENT = (AppiumBy.XPATH, "//ListItem//Text")

    # 详情页位置消息
    CHAT_HISTORY_TITLE_ID = "__ChatHistoryTitle__"
    CHAT_HISTORY_TITLE = (AppiumBy.XPATH, "//ListItem//Text[1]")
    CHAT_HISTORY_SUBTITLE_ID = "__ChatHistorySubTitle__"
    CHAT_HISTORY_SUBTITLE = (AppiumBy.XPATH, "//ListItem//Text[2]")

    # 详情页名片消息
    CHAT_HISTORY_CARD_NAME_ID = "__ChatHistoryCardName__"
    CHAT_HISTORY_CARD_NAME = (AppiumBy.XPATH, "//ListItem//Column/Text[1]")
    CHAT_HISTORY_CARD_SUB_NAME_ID = "__ChatHistoryCardSubName__"
    CHAT_HISTORY_CARD_SUB_NAME = (AppiumBy.XPATH, "//ListItem//Column/Text[2]")
    CHAT_HISTORY_CARD_TAG_ID = "__ChatHistoryCardTag__"
    CHAT_HISTORY_CARD_TAG = (AppiumBy.XPATH, "//ListItem//Column/Text[last()]")

    # 详情页文件消息
    CHAT_HISTORY_FILE_NAME_ID = "__ChatHistoryFileName__"
    CHAT_HISTORY_FILE_NAME = (AppiumBy.XPATH, "//ListItem//Column/Text[1]")
    CHAT_HISTORY_FILE_STATUS_ID = "__ChatHistoryFileStatus__"
    CHAT_HISTORY_FILE_STATUS = (AppiumBy.XPATH, "//ListItem//Column/Text[last()]")

    # 详情页顶部标题栏
    HISTORY_TITLE_LAYOUT = (AppiumBy.XPATH, "//NavDestinationTitleBar | //Row[1]")

    # ==================================================================================================================
    # 7. 撤回、删除与系统通知消息 (CMD Messages & Alerts)
    # ==================================================================================================================
    # 居中系统通知（如撤回通知、拍一拍、截屏提醒、移出群聊等，特征：消息行内无独立头像）
    CMD_MESSAGE_ITEM = (
        AppiumBy.XPATH,
        "//ListItem//Text[contains(@text, '撤回') or contains(@text, '拍了拍') or contains(@text, '移出群聊') or contains(@text, '加入了群聊') or contains(@text, '截屏')]"
    )

    # 二次确认弹窗按钮
    TWO_CONFIRM = (AppiumBy.XPATH, "//Button[.//Text[@text='确定' or @text='删除']] | //Text[@text='确定' or @text='删除']")
    TWO_CANCEL = HosBy.text("取消")

    ALERT_TITLE = (AppiumBy.XPATH, "//Dialog//Text[1]")
    BUTTON1 = TWO_CONFIRM
    BUTTON2 = TWO_CANCEL

    # 横幅系统通知
    TV_NAME = (AppiumBy.XPATH, "//Row[contains(@id, 'banner')]//Text[1]")
    TV_PREVIEW = (AppiumBy.XPATH, "//Row[contains(@id, 'banner')]//Text[2]")

    # 群公告横幅
    NOTICE_ANNOUNCEMENT = (AppiumBy.XPATH, "//Row[.//Text[contains(@text, '公告')]]")
    NOTICE_TEXT = (AppiumBy.XPATH, "//Row[.//Text[contains(@text, '公告')]]//Text[last()]")

    # ==================================================================================================================
    # 8. 动态参数化精准元素定位器工厂 (Parameterized Factory Methods)
    # ==================================================================================================================
    @classmethod
    def get_message_item_by_text(cls, text: str) -> tuple[str, str]:
        """通过传入的文本内容精确定位消息气泡（原生 HypiumBy 直查，避免长消息流整树 XPath 扫描）"""
        return HosBy.type_text("Text", text)

    @classmethod
    def get_bubble_by_text(cls, text: str) -> tuple[str, str]:
        """通过消息文本反向定位其所属的整行 ListItem 容器"""
        return (AppiumBy.XPATH, f"//ListItem[.//Text[@text='{text}']]")

    @classmethod
    def get_avatar_by_text(cls, text: str) -> tuple[str, str]:
        """定位特定文本消息旁侧对应的发送者头像"""
        return (AppiumBy.XPATH, f"//ListItem[.//Text[@text='{text}']]//Image[1]")

    @classmethod
    def get_read_status_by_text(cls, text: str) -> tuple[str, str]:
        """定位特定文本消息旁侧的已读/未读状态文本"""
        return (
            AppiumBy.XPATH,
            f"//ListItem[.//Text[@text='{text}']]//Text[contains(@text, '已读') or contains(@text, '未读')]"
        )
