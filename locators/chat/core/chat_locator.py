from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class ChatLocator:
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # --- 辅助方法：生成基于头像定位的气泡子元素 XPath ---
    # sib: preceding-sibling (发送方) / following-sibling (接收方)
    _BUBBLE_XPATH = lambda sib, sub_id, pid = PACKAGE_ID: (AppiumBy.XPATH, 
        f'//*[@resource-id="{pid}/iv_avatar"]/{sib}::*[@resource-id="{pid}/message_layout"]//*[@resource-id="{sub_id}"]')

    _BUBBLE_XPATH_TEXT = lambda sib, sub_id, pid = PACKAGE_ID: (AppiumBy.XPATH, 
        f'//*[@resource-id="{pid}/iv_avatar"]/{sib}::*[@resource-id="{pid}/message_layout"]{sub_id}')
        

    """ 新版 """
    # 聊天页面元素
    # 聊天页面整个气泡框
    MESSAGE_LAYOUT_ID = f'{PACKAGE_ID}/message_layout'              # 整个气泡容器
    MESSAGE_LAYOUT_ITEM = (AppiumBy.ID, MESSAGE_LAYOUT_ID)          # 气泡容器
    # 气泡容器 (过滤掉不含消息主体或头像的系统消息、时间分割线和撤回提醒)
    # MESSAGE_LAYOUT_ITEM = (AppiumBy.XPATH, 
    #     f'//*[@resource-id="{MESSAGE_LAYOUT_ID}" and ('
    #     f'.//*[@resource-id="{PACKAGE_ID}/message_content"] or '
    #     f'.//*[@resource-id="{PACKAGE_ID}/container"] or '
    #     f'.//*[contains(@resource-id, "avatar")]'
    #     f')]'
    # )
    MESSAGE_CONTAINER_ID = f'{PACKAGE_ID}/message_container'        # 聊天消息容器
    MESSAGE_CONTAINER_ITEM = (AppiumBy.ID, MESSAGE_CONTAINER_ID)    # 消息容器
    SENT_HEAD_ID = f'{PACKAGE_ID}/iv_sender_avatar'
    SENT_HEAD_ITEM = (AppiumBy.ID, SENT_HEAD_ID)                    # 发送方头像
    # 发送方文本气泡框
    SENT_TEXT_BUBBLE_XPATH = (f'//*[contains(@resource-id, "{SENT_HEAD_ID}")]'
                              f'/preceding-sibling::*[1]/*//android.widget.TextView')
    SENT_TEXT_BUBBLE_ITEM = (AppiumBy.XPATH, SENT_TEXT_BUBBLE_XPATH)
    RECEIVED_HEAD_ID = f'{PACKAGE_ID}/iv_receiver_avatar'
    RECEIVED_HEAD_ITEM = (AppiumBy.ID, RECEIVED_HEAD_ID) # 接收方头像
    # 接收方文本气泡框
    RECEIVED_TEXT_BUBBLE_XPATH = (f'//*[contains(@resource-id, "{RECEIVED_HEAD_ID}")]'
                                  f'/preceding-sibling::*[1]/*//android.widget.TextView')
    # RECEIVED_TEXT_BUBBLE_ITEM = (AppiumBy.XPATH, )
    # 已读未读标识
    SENT_LOCATION_BUBBLE_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{MESSAGE_CONTAINER_ID}" '
                                                 f'and .//*[@text="[哼][哈哈][嘘][哼]"]]'
                                                 f'//*[@text="已读" or @text="未读"]")]')
       

    # ==================================================================================================================
    # 聊天页面相关
    # ==================================================================================================================
    # UI 变化后元素，头像元素 、文本
    MESSAGE_ROW_ID = f'{PACKAGE_ID}/message_row'
    MESSAGE_ROW_ITEM = (AppiumBy.ID, MESSAGE_ROW_ID)            # 消息行
    MESSAGE_CONTENT_ID = f'{PACKAGE_ID}/message_content'
    MESSAGE_CONTENT_ITEM = (AppiumBy.ID, MESSAGE_CONTENT_ID)    # 消息内容
    # 排除CMD消息的气泡
    MESSAGE_CONTENT_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{MESSAGE_CONTENT_ID}" and not(./android.widget.TextView)]')

    # 发送方和接收方的聊天行容器
    SENT_MESSAGE_ROW_ITEM = _BUBBLE_XPATH("preceding-sibling", f"{PACKAGE_ID}/message_row")
    RECEIVED_MESSAGE_ROW_ITEM = _BUBBLE_XPATH("following-sibling", f"{PACKAGE_ID}/message_row")

    # 发送方和接收方的聊天内容容器
    SENT_MESSAGE_CONTENT_ITEM = _BUBBLE_XPATH("preceding-sibling", f"{PACKAGE_ID}/message_content")
    RECEIVED_MESSAGE_CONTENT_ITEM = _BUBBLE_XPATH("following-sibling", f"{PACKAGE_ID}/message_content")

    AVATAR_ID = f'{PACKAGE_ID}/iv_avatar'
    AVATAR_ITEM = (AppiumBy.ID, AVATAR_ID)                                      # 头像

    # 群聊页面显示用户昵称
    GROUP_CHAT_USER_NAME_ID = f'{PACKAGE_ID}/userName'
    GROUP_CHAT_USER_NAME_ITEM = (AppiumBy.ID, GROUP_CHAT_USER_NAME_ID)                                # 用户名
    GROUP_CHAT_USER_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{GROUP_CHAT_USER_NAME_ID}"]/android.widget.TextView')



    # ==================================================================================================================
    # 文本消息相关
    # ==================================================================================================================
    TEXT_MESSAGE_VIEW_ID = f'{PACKAGE_ID}/text_message_view'                    # 文本消息
    TEXT_MESSAGE_VIEW_ITEM = (AppiumBy.ID, TEXT_MESSAGE_VIEW_ID)    
    TEXT_MESSAGE_VIEW_CLASS = (AppiumBy.CLASS_NAME, "android.widget.TextView")
    TEXT_MESSAGE_VIEW_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{TEXT_MESSAGE_VIEW_ID}"]/android.widget.TextView')
    
    # 文本消息内容 (用于根据消息类型过滤气泡)
    TEXT_MESSAGE_CLASS = f'//*[@resource-id="{TEXT_MESSAGE_VIEW_ID}"]/android.widget.TextView'
    SENT_TEXT_MESSAGE_ITEM = _BUBBLE_XPATH_TEXT("preceding-sibling", TEXT_MESSAGE_CLASS)
    RECEIVED_TEXT_MESSAGE_ITEM = _BUBBLE_XPATH_TEXT("following-sibling", TEXT_MESSAGE_CLASS)

    # 已读/未读角标元素
    READ_FOOTER_STATUS_ID = f'{PACKAGE_ID}/message_footer_status'
    READ_FOOTER_STATUS_ITEM = (AppiumBy.ID, READ_FOOTER_STATUS_ID) 
    READ_FOOTER_READ_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_unRead')            # 已读/未读角标文本


    # ==================================================================================================================
    # 图片/视频相关
    # ==================================================================================================================
    IMAGE_ID = f'{PACKAGE_ID}/ivImage'
    IMAGE_ITEM = (AppiumBy.ID, IMAGE_ID) # 图片
    # 发送方图片
    SEND_IMAGE_ITEM = _BUBBLE_XPATH("preceding-sibling", IMAGE_ID)
    # 接收方图片
    RECEIV_IMAGE_ITEM = _BUBBLE_XPATH("following-sibling", IMAGE_ID)

    # 预览图片
    PREVIEW_IMAGE_ID = f'{PACKAGE_ID}/preview_image'
    PREVIEW_IMAGE_ITEM = (AppiumBy.ID, PREVIEW_IMAGE_ID)
    # 下载图标
    IV_DOWNLOAD_ID = f'{PACKAGE_ID}/iv_download'
    IV_DOWNLOAD_ITEM = (AppiumBy.ID, IV_DOWNLOAD_ID)


    # 视频播放按钮
    VIDEO_PLAY_BUTTON_ID = f'{PACKAGE_ID}/ivPlay'
    VIDEO_PLAY_BUTTON_ITEM = (AppiumBy.ID, VIDEO_PLAY_BUTTON_ID)    # 视频播放按钮
    SENT_VIDEO_PLAY_BUTTON_ITEM = _BUBBLE_XPATH("preceding-sibling", VIDEO_PLAY_BUTTON_ID)
    RECEIVE_VIDEO_PLAY_BUTTON_ITEM = _BUBBLE_XPATH("following-sibling", VIDEO_PLAY_BUTTON_ID)

    # 视频时长元素
    VIDEO_DURATION_ID = f'{PACKAGE_ID}/tvDuration'
    VIDEO_DURATION_ITEM = (AppiumBy.ID, VIDEO_DURATION_ID)          # 视频时长
    SENT_VIDEO_DURATION_ITEM = _BUBBLE_XPATH("preceding-sibling", VIDEO_DURATION_ID)
    RECEIVE_VIDEO_DURATION_ITEM = _BUBBLE_XPATH("following-sibling", VIDEO_DURATION_ID)

    # 消息发送失败
    FAIL_MSG_ID = f'{PACKAGE_ID}/btn_state'
    FAIL_MSG = (AppiumBy.ID, FAIL_MSG_ID)
    # 发送方和接收方的消息发送失败
    SENT_MESSAGE_FAIL_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/iv_avatar"]'
                                        f'/preceding-sibling::*[@resource-id="{PACKAGE_ID}/message_layout"]'
                                        f'//*[@resource-id="{FAIL_MSG_ID}"]')
    RECEIVE_MESSAGE_FAIL_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/iv_avatar"]'
                                            f'/following-sibling::*[@resource-id="{PACKAGE_ID}/message_layout"]'
                                            f'//*[@resource-id="{FAIL_MSG_ID}"]')
    

    # ==================================================================================================================
    # 定位消息相关
    # ==================================================================================================================
    LOCATION_MESSAGE_TITLE_ID  = f'{PACKAGE_ID}/tvTitle'
    LOCATION_MESSAGE_TITLE = (AppiumBy.ID, LOCATION_MESSAGE_TITLE_ID)            # 定位、合并转发聊天记录、消息标题
    LOCATION_MESSAGE_SUBTITLE_ID = f'{PACKAGE_ID}/tvSubTitle'
    LOCATION_MESSAGE_SUBTITLE = (AppiumBy.ID, LOCATION_MESSAGE_SUBTITLE_ID)      # 定位消息地址
    LOCATION_MESSAGE_MAP_ID = f'{PACKAGE_ID}/ivMap'
    LOCATION_MESSAGE_MAP = (AppiumBy.ID, LOCATION_MESSAGE_MAP_ID)                # 定位消息地图
    # 发送方的定位消息
    SENT_LOCATION_MESSAGE_TITLE = _BUBBLE_XPATH("preceding-sibling", LOCATION_MESSAGE_TITLE_ID)
    SENT_LOCATION_MESSAGE_SUBTITLE = _BUBBLE_XPATH("preceding-sibling", LOCATION_MESSAGE_SUBTITLE_ID)
    SENT_LOCATION_MESSAGE_MAP = _BUBBLE_XPATH("preceding-sibling", LOCATION_MESSAGE_MAP_ID)

    # 接收方的定位消息
    RECEIVE_LOCATION_MESSAGE_TITLE = _BUBBLE_XPATH("following-sibling", LOCATION_MESSAGE_TITLE_ID)
    RECEIVE_LOCATION_MESSAGE_SUBTITLE = _BUBBLE_XPATH("following-sibling", LOCATION_MESSAGE_SUBTITLE_ID)
    RECEIVE_LOCATION_MESSAGE_MAP = _BUBBLE_XPATH("following-sibling", LOCATION_MESSAGE_MAP_ID)


    # ==================================================================================================================
    # 名片消息相关
    # ==================================================================================================================
    # 名片气泡内部特征
    CARD_TAG_ID = f'{PACKAGE_ID}/tvTag'                         # 名片类型标识
    CARD_TAG = (AppiumBy.ID, CARD_TAG_ID) 
    
    CARD_BG_ID = f'{PACKAGE_ID}/ivBlurBg'                       # 名片背景
    CARD_BG = (AppiumBy.ID, CARD_BG_ID)

    CARD_AVATAR_ID = f'{PACKAGE_ID}/ivAvatarSingle'             # 名片上的头像
    CARD_AVATAR_ITEM = (AppiumBy.ID, CARD_AVATAR_ID)
    
    CARD_NICKNAME_ID = f'{PACKAGE_ID}/tvName'                   # 名片上的昵称
    CARD_NICKNAME_ITEM = (AppiumBy.ID, CARD_NICKNAME_ID)
    
    CARD_NAME_XPATH = f'//*[@resource-id="{CARD_NICKNAME_ID}"]' # 名片上的名称
    CARD_NAME_ITEM = (AppiumBy.XPATH, CARD_NAME_XPATH)

    CARD_ST_ID = f'{PACKAGE_ID}/tvSubName'                      # 名片上的ID
    CARD_ST_ITEM = (AppiumBy.ID, CARD_ST_ID)

    # 发送方的名片气泡
    SENT_CARD_NAME_ITEM = _BUBBLE_XPATH_TEXT("preceding-sibling", CARD_NAME_XPATH)
    SENT_CARD_ST_ITEM = _BUBBLE_XPATH("preceding-sibling", CARD_ST_ID)
    SENT_CARD_TAG_ITEM = _BUBBLE_XPATH("preceding-sibling", CARD_TAG_ID)

    # 接收方的名片气泡
    RECEIVE_CARD_NAME_ITEM = _BUBBLE_XPATH_TEXT("following-sibling", CARD_NAME_XPATH)
    RECEIVE_CARD_ST_ITEM = _BUBBLE_XPATH("following-sibling", CARD_ST_ID)
    RECEIVE_CARD_TAG_ITEM = _BUBBLE_XPATH("following-sibling", CARD_TAG_ID)
    
    
    # ==================================================================================================================
    # 文件消息相关
    # ==================================================================================================================
    FILE_NAME_ID = f'{PACKAGE_ID}/tvFileName'               # TODO: 替换实际文件名称ID
    FILE_NAME_ITEM = (AppiumBy.ID, FILE_NAME_ID)            # 文件名称
    FILE_SIZE_ID = f'{PACKAGE_ID}/tvFileSize'               # TODO: 替换实际文件大小ID
    FILE_SIZE_ITEM = (AppiumBy.ID, FILE_SIZE_ID)            # 文件大小
    FILE_ICON_ID = f'{PACKAGE_ID}/ivFileIcon'               # TODO: 替换实际文件图标ID
    FILE_ICON_ITEM = (AppiumBy.ID, FILE_ICON_ID)            # 文件图标
    FILE_STATUS_ID = f'{PACKAGE_ID}/tvStatus'               # TODO: 替换实际文件状态ID
    FILE_STATUS_ITEM = (AppiumBy.ID, FILE_STATUS_ID)        # 文件状态

    # 发送方的文件气泡
    SENT_FILE_NAME_ITEM = _BUBBLE_XPATH("preceding-sibling", FILE_NAME_ID)
    SENT_FILE_SIZE_ITEM = _BUBBLE_XPATH("preceding-sibling", FILE_SIZE_ID)
    SENT_FILE_STATUS_ITEM = _BUBBLE_XPATH("preceding-sibling", FILE_STATUS_ID)

    # 接收方的文件气泡
    RECEIVE_FILE_NAME_ITEM = _BUBBLE_XPATH("following-sibling", FILE_NAME_ID)
    RECEIVE_FILE_SIZE_ITEM = _BUBBLE_XPATH("following-sibling", FILE_SIZE_ID)
    RECEIVE_FILE_STATUS_ITEM = _BUBBLE_XPATH("following-sibling", FILE_STATUS_ID)


    # 封禁消息展示
    # 给停用账号发送消息提示
    DISABLE_MESSAGE_TIP = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("对方账号已无法使用 详情")') # 给停用账号发送消息提示
    

    # ==================================================================================================================
    # 聊天页面顶部元素定位
    # ==================================================================================================================
    TOP_BACK_BUTTON = CommonLocator.TOP_BACK_BTN                     # 返回按钮
    TOP_USER_NAME_ID = f'{PACKAGE_ID}/to_user_name'                     # 聊天对象昵称ID
    TOP_USER_NAME = (AppiumBy.ID, TOP_USER_NAME_ID)                     # 聊天对象昵称
    TOP_USER_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{TOP_USER_NAME_ID}"]/android.widget.TextView') # 聊天对象昵称
    TOP_MORE_BUTTON = (AppiumBy.ID, 'right_bnt')                        # 更多按钮 setting


    # ==================================================================================================================
    # 聊天页面底部元素定位
    # ==================================================================================================================
    CHAT_INPUT= (AppiumBy.ID, f'{PACKAGE_ID}/chat_input')                                   # 聊天输入区域
    CHAT_INPUT_CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/inputContent')                        # 聊天输入框
    CHAT_INPUT_BOX= (AppiumBy.ID, f'{PACKAGE_ID}/input_box')                                # 聊天输入框
    VOICE_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/voice_input_btn')                           # 语音键盘切换按钮
    TEXT_INPUT = (AppiumBy.ID, f'{PACKAGE_ID}/text_input')                                  # 输入框
    EMOJI_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/input_expression_bnt')                      # 表情按钮
    SEND_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/input_send_bnt')                             # 发送按钮


    # 禁言状态输入框（包含容器）
    NOT_IN_INPUT_BOX = (AppiumBy.ID, f'{PACKAGE_ID}/not_in')                                # 禁言状态输入框
    TPV_1 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_1')                                            # 禁言状态语音按钮
    TV_NOT_IN_TIPS_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_not_in_tips_title')              # 禁言状态提示标题
    TV_NOT_IN_TIPS = (AppiumBy.ID, f'{PACKAGE_ID}/tv_not_in_tips')                          # 禁言状态禁言时长
    TPV_2 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_2')                                            # 禁言状态表情按钮
    TPV_3 = (AppiumBy.ID, f'{PACKAGE_ID}/tpv_3')                                            # 禁言状态加号按钮


    # 点击 + 按钮展开其它功能元素
    ADD_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_bnt')                              # 添加按钮(+号按钮)
    INPUT_MORE_PAGER = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_pager')                      # 加号面板滑动区域
    INPUT_MORE_SCROLLABLE_INDICATOR = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_indicator')   # 加号面板可左右滑动标识
    # ELEM_BUTTON = (AppiumBy.ID, 'll_grid_item')  # 元素按钮
    # ELEM_GIRD_TEXT = (AppiumBy.ID, 'type_name')  # 拍摄、图片、小视频、位置、视频聊天、名片、文件文本按钮


    # ==================================================================================================================
    # 聊天页面【多选菜单】元素定位
    # ==================================================================================================================
    BT_SLEECT_ID = f'{PACKAGE_ID}/bt_select'
    BT_SELECT = (AppiumBy.ID, BT_SLEECT_ID)                   # 勾选消息按钮
    # 勾选消息不包含发送失败的按钮
    BT_SELECT_NOT_FAIL = (AppiumBy.XPATH, f'//*[@resource-id="{BT_SLEECT_ID}"'
                                            f'and following-sibling::*[@resource-id="{PACKAGE_ID}/message_layout"'
                                            f'and not(.//*[@resource-id="{PACKAGE_ID}/btn_state"])]]') 
    IV_SHARE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_share')                                                          # 转发按钮
    IV_DELETE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_delete')                                                        # 删除按钮
    TV_FORWARD_ONE_BY_ONE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_forward_one_by_one')                                # 逐条转发
    TV_FORWARD_COMBINE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_forward_combine')                                      # 合并转发
    TV_CANCEL = CommonLocator.TV_CANCEL_BTN                                                                   # 取消按钮
    MULIT_TOAST_MESSAGE = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/toast_message" and @text="发送中"]') # 发送中
    LEFT_TEXT = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/left_text"]')                                 # 聊天记录（合并转发）消息内容


    # ==================================================================================================================
    # 聊天页面【聊天记录】内部元素定位
    # ==================================================================================================================
    CHAT_HISTORY_CONTENT_ID = f'{PACKAGE_ID}/tvContent'
    CHAT_HISTORY_CONTENT = (AppiumBy.ID, CHAT_HISTORY_CONTENT_ID)           # 聊天记录（合并转发）消息内容

    SENT_CHAT_HISTORY_CONTENT = _BUBBLE_XPATH("preceding-sibling", CHAT_HISTORY_CONTENT_ID)
    RECEIVE_CHAT_HISTORY_CONTENT = _BUBBLE_XPATH("following-sibling", CHAT_HISTORY_CONTENT_ID)

    HISTORY_TITLE_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/title_layout')      # 聊天记录（合并转发）标题栏
    

    # ==================================================================================================================
    # 聊天页面 【撤回和删除】 相关元素定位
    # ==================================================================================================================
    
    # 撤回、截屏消息通知
    WITHDRAW_MESSAGE_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{MESSAGE_LAYOUT_ID}"]//*[@resource-id="{MESSAGE_CONTENT_ID}"]/android.widget.TextView')
    
    # 删除操作二次确认和取消
    DEL_CONFIRM = CommonLocator.TV_CONFIRM_BTN
    DEL_CANCEL = CommonLocator.TV_CANCEL_BTN


    TOAST_MSG = CommonLocator.TOAST_MSG


    # 横幅通知消息定位器
    TV_PREVIEW_ID = f"{PACKAGE_ID}/tv_preview"
    TV_PREVIEW = (AppiumBy.ID, TV_PREVIEW_ID)                                          # 横幅消息详细文本

    # 群公告/邀请人消息横幅
    NEW_ANNOUNCEMENT_CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/new_announcement_content')

    


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
    def get_message_item_by_text_contains(cls, sent_type: str="sender", text: str=""):
        sent_type = cls.SENT_HEAD_ID if sent_type == "sender" else cls.RECV_HEAD_ID
        return (AppiumBy.XPATH,
                f'//*[contains(@resource-id, "{sent_type}")]/ancestor::android.view.ViewGroup[1]//*[contains(@text, "{text}")]')

    @classmethod
    def get_specific_message_locator(cls, role: str="sender", target_text: str="") -> tuple:
        """
        进阶：精确查找【指定角色】发送的【特定文本】气泡
        :param role: "sender" (自己发出的) 或 "receiver" (对方发来的)
        :param target_text: 目标消息的精确文本
        :return: (AppiumBy.XPATH, xpath_string)
        """
        if role == "sender":
            # 发送方逻辑：找头像 -> 找它【前面】紧挨着的容器 -> 找精确文本
            xpath = f'{cls.SENT_TEXT_BUBBLE_XPATH}[@text="{target_text}"]'
        elif role == "receiver":
            # 接收方逻辑：找头像 -> 找它【后面】紧挨着的容器 -> 找精确文本
            xpath = f'{cls.RECEIVED_TEXT_BUBBLE_XPATH}[@text="{target_text}"]'
        else:
            raise ValueError(f"未知的角色: {role}")

        return (AppiumBy.XPATH, xpath)

     # 精确定位是发送方还是接收方的文本消息
    @classmethod
    def get_sent_text_message_locator(cls, sent_type: str = "sender"):
        if sent_type == "sender":
            poist_type = 'following-sibling'
        else:
            poist_type = 'preceding-sibling'
        return (AppiumBy.XPATH,  f'//*[@resource-id="{cls.MESSAGE_LAYOUT_ID}" and {poist_type}::*[@resource-id="{cls.AVATAR_ID}"]]'
                                 f'//*[@resource-id="{cls.TEXT_MESSAGE_VIEW_ID}"]/android.widget.TextView')
        

    # 通过传入的文本获取 已读或未读 的元素定位
    @classmethod
    def get_status_item_by_text(cls, text: str):
        return (AppiumBy.XPATH,
                f'//*[@resource-id="{cls.MESSAGE_CONTAINER_ID}" and .//*[@text="{text}"]]//*[@text="已读" or @text="未读"]')

   



