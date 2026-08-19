from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


def _make_bubble_xpath(side: str, sub_id: str, pid: str = CommonLocator.PACKAGE_ID) -> tuple:
    """生成基于头像定位的气泡子元素 XPath"""
    axis = "following-sibling" if side in ("sent", "following-sibling") else "preceding-sibling"
    xpath = (
        f'//*[@resource-id="{pid}/avatar"]/{axis}::*[contains(@resource-id, "{sub_id}") or .//*[@resource-id="{sub_id}"]]'
    )
    return (AppiumBy.XPATH, xpath)


class ChatLocator:
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    _BUBBLE_XPATH = staticmethod(_make_bubble_xpath)
    _BUBBLE_XPATH_TEXT = staticmethod(_make_bubble_xpath)
        

    # ==================================================================================================================
    # 聊天页面相关（头像、文本）
    # ==================================================================================================================
    # 聊天页面元素
    # 聊天页面整个气泡框 / 消息列表
    MESSAGES_LIST_ID = f'{PACKAGE_ID}/messages'                     # 消息列表 RecyclerView
    MESSAGES_LIST_ITEM = (AppiumBy.ID, MESSAGES_LIST_ID)            # 消息列表
    
    # 消息行容器 (RecyclerView 下的各个 android.view.ViewGroup 消息行)
    MESSAGE_LAYOUT_XPATH = f'//*[@resource-id="{MESSAGES_LIST_ID}"]/android.view.ViewGroup'
    MESSAGE_LAYOUT_ITEM = (AppiumBy.XPATH, MESSAGE_LAYOUT_XPATH)    # 消息行容器
    
    MESSAGE_CONTENT_ID = f'{PACKAGE_ID}/message_text'
    MESSAGE_CONTENT_ITEM = (AppiumBy.ID, MESSAGE_CONTENT_ID)        # 消息内容
    
    # 头像相关
    AVATAR_ID = f'{PACKAGE_ID}/avatar'
    AVATAR_ITEM = (AppiumBy.ID, AVATAR_ID)                          # 统一头像
    
    # 已读未读标识
    READ_STATUS_ID = f'{PACKAGE_ID}/read_status'                    # 新版已读未读状态 ID
    READ_STATUS_ITEM = (AppiumBy.ID, READ_STATUS_ID)                # 已读未读状态控件
    SENT_LOCATION_BUBBLE_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{READ_STATUS_ID}"]')
       

    # 发送方头像（右侧）：同级前驱包含消息内容
    SENT_HEAD_XPATH = (
        f'//*[@resource-id="{AVATAR_ID}"][preceding-sibling::*[@resource-id="{MESSAGE_CONTENT_ID}"]]'
    )
    SENT_HEAD_ITEM = (AppiumBy.XPATH, SENT_HEAD_XPATH)
    # 接收方头像（左侧）：同级后继包含消息内容
    RECEIVED_HEAD_XPATH = (
        f'//*[@resource-id="{AVATAR_ID}"][following-sibling::*[@resource-id="{MESSAGE_CONTENT_ID}"]]'
    )
    RECEIVED_HEAD_ITEM = (AppiumBy.XPATH, RECEIVED_HEAD_XPATH)

    # 发送方文本气泡框（头像在右，气泡在头像前驱节点）
    SENT_TEXT_BUBBLE_XPATH = (
        f'//*[@resource-id="{AVATAR_ID}"]/preceding-sibling::*[@resource-id="{MESSAGE_CONTENT_ID}"]'
    )
    SENT_TEXT_BUBBLE_ITEM = (AppiumBy.XPATH, SENT_TEXT_BUBBLE_XPATH)

    # 接收方文本气泡框（头像在左，气泡在头像后继节点）
    RECEIVED_TEXT_BUBBLE_XPATH = (
        f'//*[@resource-id="{AVATAR_ID}"]/following-sibling::*[@resource-id="{MESSAGE_CONTENT_ID}"]'
    )
    RECEIVED_TEXT_BUBBLE_ITEM = (AppiumBy.XPATH, RECEIVED_TEXT_BUBBLE_XPATH)

    # 发送方和接收方的聊天行容器
    SENT_MESSAGE_ROW_ITEM = _BUBBLE_XPATH("preceding-sibling", MESSAGE_CONTENT_ID)
    RECEIVED_MESSAGE_ROW_ITEM = _BUBBLE_XPATH("following-sibling", MESSAGE_CONTENT_ID)

    # 发送方和接收方的聊天内容容器
    SENT_MESSAGE_CONTENT_ITEM = _BUBBLE_XPATH("preceding-sibling", MESSAGE_CONTENT_ID)
    RECEIVED_MESSAGE_CONTENT_ITEM = _BUBBLE_XPATH("following-sibling", MESSAGE_CONTENT_ID)

    # 群聊页面显示用户昵称
    GROUP_CHAT_USER_NAME_ID = f'{PACKAGE_ID}/sender_name'
    GROUP_CHAT_USER_NAME_ITEM = (AppiumBy.ID, GROUP_CHAT_USER_NAME_ID)                                # 用户名


    # ==================================================================================================================
    # 文本消息相关
    # ==================================================================================================================
    TEXT_MESSAGE_VIEW_CLASS = (AppiumBy.CLASS_NAME, "android.widget.TextView")
    TEXT_MESSAGE_VIEW_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{MESSAGE_CONTENT_ID}"]')
    
    # 文本消息内容 (用于根据消息类型过滤气泡)
    TEXT_MESSAGE_CLASS = f'//*[@resource-id="{MESSAGE_CONTENT_ID}"]'
    SENT_TEXT_MESSAGE_ITEM = _BUBBLE_XPATH("following-sibling", MESSAGE_CONTENT_ID)
    RECEIVED_TEXT_MESSAGE_ITEM = _BUBBLE_XPATH("preceding-sibling", MESSAGE_CONTENT_ID)


    # ==================================================================================================================
    # 图片/视频相关
    # ==================================================================================================================
    IMAGE_ID = f'{PACKAGE_ID}/message_image'
    IMAGE_ITEM = (AppiumBy.ID, IMAGE_ID) # 图片
    # 发送方图片
    SEND_IMAGE_ITEM = _BUBBLE_XPATH("following-sibling", IMAGE_ID)
    # 接收方图片
    RECEIV_IMAGE_ITEM = _BUBBLE_XPATH("preceding-sibling", IMAGE_ID)

    # 预览图片
    PREVIEW_IMAGE_ID = f'{PACKAGE_ID}/preview_image'
    PREVIEW_IMAGE_ITEM = (AppiumBy.ID, PREVIEW_IMAGE_ID)
    # 下载图标
    IV_DOWNLOAD_ID = f'{PACKAGE_ID}/iv_download'
    IV_DOWNLOAD_ITEM = (AppiumBy.ID, IV_DOWNLOAD_ID)


    # 视频播放按钮 / 视频封面
    VIDEO_PLAY_BUTTON_ID = f'{PACKAGE_ID}/video_cover'
    VIDEO_PLAY_BUTTON_ITEM = (AppiumBy.ID, VIDEO_PLAY_BUTTON_ID)    # 视频播放按钮 / 封面
    SENT_VIDEO_PLAY_BUTTON_ITEM = _BUBBLE_XPATH("following-sibling", VIDEO_PLAY_BUTTON_ID)
    RECEIVE_VIDEO_PLAY_BUTTON_ITEM = _BUBBLE_XPATH("preceding-sibling", VIDEO_PLAY_BUTTON_ID)

    # 视频时长元素
    VIDEO_DURATION_ID = f'{PACKAGE_ID}/duration'
    VIDEO_DURATION_ITEM = (AppiumBy.ID, VIDEO_DURATION_ID)          # 视频时长
    SENT_VIDEO_DURATION_ITEM = _BUBBLE_XPATH("following-sibling", VIDEO_DURATION_ID)
    RECEIVE_VIDEO_DURATION_ITEM = _BUBBLE_XPATH("preceding-sibling", VIDEO_DURATION_ID)

    # 消息发送失败
    FAIL_MSG_ID = f'{PACKAGE_ID}/delivery_status'
    FAIL_MSG = (AppiumBy.ID, FAIL_MSG_ID)
    # 发送方和接收方的消息发送失败
    SENT_MESSAGE_FAIL_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{AVATAR_ID}"]/following-sibling::*[@resource-id="{FAIL_MSG_ID}"]')
    RECEIVE_MESSAGE_FAIL_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{AVATAR_ID}"]/following-sibling::*[@resource-id="{FAIL_MSG_ID}"]')
    

    # ==================================================================================================================
    # 定位消息相关
    # ==================================================================================================================
    LOCATION_CARD_ID = f'{PACKAGE_ID}/location_card'                                # 定位卡片容器
    LOCATION_CARD_ITEM = (AppiumBy.ID, LOCATION_CARD_ID)
    LOCATION_MESSAGE_TITLE_ID  = f'{PACKAGE_ID}/location_title'                     # 定位主标题
    LOCATION_MESSAGE_TITLE = (AppiumBy.ID, LOCATION_MESSAGE_TITLE_ID)               
    LOCATION_MESSAGE_SUBTITLE_ID = f'{PACKAGE_ID}/location_subtitle'                # 定位副标题/详细地址
    LOCATION_MESSAGE_SUBTITLE = (AppiumBy.ID, LOCATION_MESSAGE_SUBTITLE_ID)         

    # 发送方的定位消息
    SENT_LOCATION_MESSAGE_TITLE = _BUBBLE_XPATH("following-sibling", LOCATION_MESSAGE_TITLE_ID)
    SENT_LOCATION_MESSAGE_SUBTITLE = _BUBBLE_XPATH("following-sibling", LOCATION_MESSAGE_SUBTITLE_ID)

    # 接收方的定位消息
    RECEIVE_LOCATION_MESSAGE_TITLE = _BUBBLE_XPATH("preceding-sibling", LOCATION_MESSAGE_TITLE_ID)
    RECEIVE_LOCATION_MESSAGE_SUBTITLE = _BUBBLE_XPATH("preceding-sibling", LOCATION_MESSAGE_SUBTITLE_ID)


    # ==================================================================================================================
    # 名片消息相关
    # ==================================================================================================================
    # 名片气泡内部特征
    PROFILE_CARD_ID = f'{PACKAGE_ID}/profile_card'                              # 名片卡片容器
    PROFILE_CARD_ITEM = (AppiumBy.ID, PROFILE_CARD_ID)
    CARD_NICKNAME_ID = f'{PACKAGE_ID}/card_title'                               # 名片上的昵称/标题（如: 测试0221）
    CARD_NICKNAME_ITEM = (AppiumBy.ID, CARD_NICKNAME_ID)
    CARD_ST_ID = f'{PACKAGE_ID}/card_subtitle'                                  # 名片上的账号ID/副标题（如: imid_xxx）
    CARD_ST_ITEM = (AppiumBy.ID, CARD_ST_ID)
    CARD_TAG_ID = f'{PACKAGE_ID}/card_kind'                                     # 名片类型标识（如: 个人名片）
    CARD_TAG = (AppiumBy.ID, CARD_TAG_ID) 

    # CARD_AVATAR_ID = f'{PACKAGE_ID}/avatar'                                     # 名片上的头像
    # CARD_AVATAR_ITEM = (AppiumBy.ID, CARD_AVATAR_ID)

    # 发送方的名片气泡
    SENT_CARD_NAME_ITEM = _BUBBLE_XPATH("following-sibling", CARD_NICKNAME_ID)
    SENT_CARD_ST_ITEM = _BUBBLE_XPATH("following-sibling", CARD_ST_ID)
    SENT_CARD_TAG_ITEM = _BUBBLE_XPATH("following-sibling", CARD_TAG_ID)

    # 接收方的名片气泡
    RECEIVE_CARD_NAME_ITEM = _BUBBLE_XPATH("preceding-sibling", CARD_NICKNAME_ID)
    RECEIVE_CARD_ST_ITEM = _BUBBLE_XPATH("preceding-sibling", CARD_ST_ID)
    RECEIVE_CARD_TAG_ITEM = _BUBBLE_XPATH("preceding-sibling", CARD_TAG_ID)
    
    
    # ==================================================================================================================
    # 文件消息相关
    # ==================================================================================================================
    FILE_CARD_ID = f'{PACKAGE_ID}/file_card'                                    # 文件卡片容器
    FILE_CARD_ITEM = (AppiumBy.ID, FILE_CARD_ID)
    FILE_NAME_ID = f'{PACKAGE_ID}/file_name'                                    # 文件名称（如: 测试-图片.jpg）
    FILE_NAME_ITEM = (AppiumBy.ID, FILE_NAME_ID)                                # 文件名称
    FILE_SIZE_ID = f'{PACKAGE_ID}/file_meta'                                    # 文件大小/元数据（如: 38KB）
    FILE_SIZE_ITEM = (AppiumBy.ID, FILE_SIZE_ID)                                # 文件大小
    FILE_LINE_ID = f'{PACKAGE_ID}/file_line'                                    # 文件信息分隔线
    FILE_LINE_ITEM = (AppiumBy.ID, FILE_LINE_ID)
    FILE_ICON_ID = f'{PACKAGE_ID}/file_card'                                    # 文件图标/卡片
    FILE_ICON_ITEM = (AppiumBy.ID, FILE_ICON_ID)                                # 文件图标
    FILE_STATUS_ID = f'{PACKAGE_ID}/file_status'                                # 文件状态（如: 发送成功）
    FILE_STATUS_ITEM = (AppiumBy.ID, FILE_STATUS_ID)                            # 文件状态

    # 发送方的文件气泡
    SENT_FILE_NAME_ITEM = _BUBBLE_XPATH("following-sibling", FILE_NAME_ID)
    SENT_FILE_SIZE_ITEM = _BUBBLE_XPATH("following-sibling", FILE_SIZE_ID)
    SENT_FILE_STATUS_ITEM = _BUBBLE_XPATH("following-sibling", FILE_STATUS_ID)

    # 接收方的文件气泡
    RECEIVE_FILE_NAME_ITEM = _BUBBLE_XPATH("preceding-sibling", FILE_NAME_ID)
    RECEIVE_FILE_SIZE_ITEM = _BUBBLE_XPATH("preceding-sibling", FILE_SIZE_ID)
    RECEIVE_FILE_STATUS_ITEM = _BUBBLE_XPATH("preceding-sibling", FILE_STATUS_ID)


    # 封禁消息展示
    # 给停用账号发送消息提示
    DISABLE_MESSAGE_TIP = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("对方账号已无法使用 详情")') # 给停用账号发送消息提示
    


    # ==================================================================================================================
    # 聊天页面顶部元素定位
    # ==================================================================================================================
    TOP_BACK_UNREAD_BG = (AppiumBy.ID, f'{PACKAGE_ID}/back_unread_background')          # 返回未读背景
    TOP_BACK_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/back')                               # 返回按钮
    TOP_BACK_UNREAD_BADGE = (AppiumBy.ID, f'{PACKAGE_ID}/back_unread_badge')            # 返回按钮未读数角标
    TOP_USER_NAME_ID = f'{PACKAGE_ID}/title'                                            # 聊天对象昵称/群名称
    TOP_USER_NAME = (AppiumBy.ID, TOP_USER_NAME_ID)                                     
    TOP_USER_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{TOP_USER_NAME_ID}"]')   # 聊天对象昵称
    TOP_SHORT_NUMBER = (AppiumBy.ID, f'{PACKAGE_ID}/tv_short_no')                       # 群聊ID
    GROUP_NUMBER_COUNT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_group_number_count')           # 群聊人数
    TOP_MORE_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/more')                               # 更多按钮


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


    # 禁言状态输入框（包含容器）
    NOT_IN_INPUT_BOX = (AppiumBy.ID, f'{PACKAGE_ID}/not_in')                            # 禁言状态输入框
    TPV_1 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_1')                                        # 禁言状态语音按钮
    TV_NOT_IN_TIPS_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_not_in_tips_title')          # 禁言状态提示标题
    TV_NOT_IN_TIPS = (AppiumBy.ID, f'{PACKAGE_ID}/tv_not_in_tips')                      # 禁言状态禁言时长
    TPV_2 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_2')                                        # 禁言状态表情按钮
    TPV_3 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_3')                                        # 禁言状态加号按钮


    # 点击 + 按钮展开其它功能元素
    ADD_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_bnt')                              # 添加按钮(+号按钮)
    INPUT_MORE_PAGER = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_pager')                      # 加号面板滑动区域
    INPUT_MORE_SCROLLABLE_INDICATOR = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_indicator')   # 加号面板可左右滑动标识
    # ELEM_BUTTON = (AppiumBy.ID, 'll_grid_item')  # 元素按钮
    # ELEM_GIRD_TEXT = (AppiumBy.ID, 'type_name')  # 拍摄、图片、小视频、位置、视频聊天、名片、文件文本按钮


    # ==================================================================================================================
    # 聊天页面【多选菜单】元素定位
    # ==================================================================================================================
    TV_SELECT_NUM = (AppiumBy.ID, f'{PACKAGE_ID}/tv_select_num')                            # 勾选数量
    BT_SLEECT_ID = f'{PACKAGE_ID}/message_selection'
    BT_SELECT = (AppiumBy.ID, BT_SLEECT_ID)                                                 # 勾选消息按钮
    # 勾选消息不包含发送失败的按钮
    BT_SELECT_NOT_FAIL = (AppiumBy.XPATH, f'//*[@resource-id="{BT_SLEECT_ID}" and not(following-sibling::*[@resource-id="{FAIL_MSG_ID}"])]')
    IV_SHARE = (AppiumBy.ID, f'{PACKAGE_ID}/multi_select_share')                            # 转发按钮
    IV_DELETE = (AppiumBy.ID, f'{PACKAGE_ID}/multi_select_delete')                          # 删除按钮

    DESIGN_BOTTOM_SHEET = (AppiumBy.ID, f'{PACKAGE_ID}/design_bottom_sheet')                # 转发弹窗
    TV_FORWARD_ONE_BY_ONE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_forward_one_by_one')            # 逐条转发
    TV_FORWARD_COMBINE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_forward_combine')                  # 合并转发
    TV_CANCEL = CommonLocator.TV_CANCEL_BTN                                                 # 取消按钮
    
    # 聊天记录（合并转发）消息内容
    LEFT_TEXT = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/left_text"]')             

    # ==================================================================================================================
    # 聊天页面【聊天记录（合并转发）详情页】内部元素定位
    # ==================================================================================================================
    CHAT_HISTORY_RECYCLER_ID = f'{PACKAGE_ID}/recycler'
    CHAT_HISTORY_RECYCLER_VIEW = (AppiumBy.ID, CHAT_HISTORY_RECYCLER_ID)                    # 聊天记录列表容器
    RECYCLER_VIEW = CHAT_HISTORY_RECYCLER_VIEW                                              # 列表容器别名

    CHAT_HISTORY_TIME_ID = f'{PACKAGE_ID}/tvTime'
    CHAT_HISTORY_TIME = (AppiumBy.ID, CHAT_HISTORY_TIME_ID)                                 # 聊天记录（合并转发）时间
    TV_TIME = CHAT_HISTORY_TIME                                                             # 时间别名

    # 聊天记录详情页 - 文本/提示内容
    CHAT_HISTORY_TEXT_ID = f'{PACKAGE_ID}/tv_message_text_content'
    CHAT_HISTORY_TEXT_CONTENT = (AppiumBy.ID, CHAT_HISTORY_TEXT_ID)                         # 文本/系统提示内容
    CHAT_HISTORY_CONTENT_ID = CHAT_HISTORY_TEXT_ID
    CHAT_HISTORY_CONTENT = CHAT_HISTORY_TEXT_CONTENT                                         # 兼容别名

    # 聊天记录详情页 - 位置消息
    CHAT_HISTORY_TITLE_ID = f'{PACKAGE_ID}/tvTitle'
    CHAT_HISTORY_TITLE = (AppiumBy.ID, CHAT_HISTORY_TITLE_ID)                               # 位置主标题（如: 北大资源财富森林5栋）
    CHAT_HISTORY_SUBTITLE_ID = f'{PACKAGE_ID}/tvSubTitle'
    CHAT_HISTORY_SUBTITLE = (AppiumBy.ID, CHAT_HISTORY_SUBTITLE_ID)                         # 位置副标题/详细地址

    # 聊天记录详情页 - 名片消息
    CHAT_HISTORY_CARD_NAME_ID = f'{PACKAGE_ID}/tvName'
    CHAT_HISTORY_CARD_NAME = (AppiumBy.ID, CHAT_HISTORY_CARD_NAME_ID)                       # 名片昵称/标题（如: 测试0222）
    CHAT_HISTORY_CARD_SUB_NAME_ID = f'{PACKAGE_ID}/tvSubName'
    CHAT_HISTORY_CARD_SUB_NAME = (AppiumBy.ID, CHAT_HISTORY_CARD_SUB_NAME_ID)               # 名片账号/副标题（如: MN0123）
    CHAT_HISTORY_CARD_TAG_ID = f'{PACKAGE_ID}/tvTag'
    CHAT_HISTORY_CARD_TAG = (AppiumBy.ID, CHAT_HISTORY_CARD_TAG_ID)                         # 名片类型标签（如: 个人名片）

    # 聊天记录详情页 - 文件消息
    CHAT_HISTORY_FILE_NAME_ID = f'{PACKAGE_ID}/tvFileName'
    CHAT_HISTORY_FILE_NAME = (AppiumBy.ID, CHAT_HISTORY_FILE_NAME_ID)                       # 文件名称（如: xxx.jpg）
    CHAT_HISTORY_FILE_STATUS_ID = f'{PACKAGE_ID}/tvStatus'
    CHAT_HISTORY_FILE_STATUS = (AppiumBy.ID, CHAT_HISTORY_FILE_STATUS_ID)                   # 文件状态与大小（如: 发送成功 | 146KB、未下载 · 327KB）

    # 聊天主页面 - 合并转发卡片气泡（在聊天列表中）
    SENT_CHAT_HISTORY_CONTENT = _BUBBLE_XPATH("following-sibling", CHAT_HISTORY_CONTENT_ID)
    RECEIVE_CHAT_HISTORY_CONTENT = _BUBBLE_XPATH("preceding-sibling", CHAT_HISTORY_CONTENT_ID)

    HISTORY_TITLE_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/title_layout')                      # 聊天记录顶部标题栏
    

    # ==================================================================================================================
    # 聊天页面 【撤回和删除】 相关元素定位
    # ==================================================================================================================
    
    # CMD 系统通知消息（如截屏、撤回通知，位于 FrameLayout 容器）
    CMD_MESSAGE_ITEM = (AppiumBy.XPATH, f'//android.widget.FrameLayout/*[@resource-id="{MESSAGE_CONTENT_ID}"]')

    # 排除CMD消息的气泡（必须带有同级头像的普通聊天文本）
    MESSAGE_CONTENT_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{AVATAR_ID}"]/following-sibling::*[@resource-id="{MESSAGE_CONTENT_ID}"]')

    # 删除操作二次确认和取消
    DEL_CONFIRM = CommonLocator.TV_CONFIRM_BTN
    DEL_CANCEL = CommonLocator.TV_CANCEL_BTN
    
    ALERT_TITLE = (AppiumBy.ID, "android:id/alertTitle")
    BUTTON2 = (AppiumBy.ID, "android:id/button2")
    BUTTON1 = (AppiumBy.ID, "android:id/button1")


    # 横幅通知消息定位器
    TV_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")        # 横幅通知消息发送者名称
    TV_PREVIEW = (AppiumBy.ID, f"{PACKAGE_ID}/tv_preview")  # 横幅通知消息详细文本

    # 群公告/邀请人消息横幅
    NOTICE_ANNOUNCEMENT = (AppiumBy.ID, f'{PACKAGE_ID}/notice_announcement')
    NOTICE_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/notice_text")  # 群公告/邀请人消息横幅详细文本

    


    # ==================================================================================================================
    # 聊天页面的公共逻辑方法
    # ==================================================================================================================

    @classmethod
    def get_avatar_bubble_locator(cls, sub_id: str, is_sender: bool = True):
        """
        基于头像定位的消息气泡子元素通用工厂
        :param sub_id: 子元素的完整 resource-id (例如 cls.LOCATION_MESSAGE_TITLE_ID)
        :param is_sender: True-发送方(preceding), False-接收方(following)
        """
        sib = "preceding-sibling" if is_sender else "following-sibling"
        return cls._BUBBLE_XPATH(sib, sub_id)

    # 通过传入对应的文本获取气泡的元素定位 - 不区分发送者和接收者
    @classmethod
    def get_message_item_by_text(cls, text: str):
        return (AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().text("{text}")')

    # 通过传入的文本获取气泡的元素定位 - 发送者和接收者
    @classmethod
    def get_message_item_by_text_contains(cls, sent_type: str = "sender", text: str = ""):
        axis = "preceding-sibling" if sent_type == "sender" else "following-sibling"
        return (AppiumBy.XPATH,
                f'//*[@resource-id="{cls.AVATAR_ID}"]/{axis}::*[contains(@text, "{text}") or .//*[contains(@text, "{text}")]]')

    @classmethod
    def get_specific_message_locator(cls, role: str="sender", target_text: str="") -> tuple:
        """
        进阶：精确查找【指定角色】发送的【特定文本】气泡
        :param role: "sender" (自己发出的) 或 "receiver" (对方发来的)
        :param target_text: 目标消息的精确文本
        :return: (AppiumBy.XPATH, xpath_string)
        """
        if role == "sender":
            xpath = f'{cls.SENT_TEXT_BUBBLE_XPATH}[@text="{target_text}"]'
        elif role == "receiver":
            xpath = f'{cls.RECEIVED_TEXT_BUBBLE_XPATH}[@text="{target_text}"]'
        else:
            raise ValueError(f"未知的角色: {role}")

        return (AppiumBy.XPATH, xpath)

    # 精确定位是发送方还是接收方的文本消息
    @classmethod
    def get_sent_text_message_locator(cls, sent_type: str = "sender"):
        return cls.SENT_TEXT_MESSAGE_ITEM if sent_type == "sender" else cls.RECEIVED_TEXT_MESSAGE_ITEM

    # 通过传入的文本获取 已读或未读 的元素定位
    @classmethod
    def get_status_item_by_text(cls, text: str):
        return (AppiumBy.XPATH,
                f'//*[@resource-id="{cls.AVATAR_ID}"][preceding-sibling::*[contains(@text, "{text}") or .//*[contains(@text, "{text}")]]]'
                f'/preceding-sibling::*[@resource-id="{cls.READ_STATUS_ID}"]')

   



