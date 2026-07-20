from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class ContactDetailLocator:
    """好友资料详情页定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID
    
    # 头部个人资料区域
    AVATAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_avatar")               # 头像
    TV_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")               # 顶部显示的昵称
    TV_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/tv_name"]//android.widget.TextView')
    
    # 详情信息行
    INFO_NICKNAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_small_name")    # 昵称标签处的文字
    ST_ID = (AppiumBy.ID, f"{PACKAGE_ID}/tv_santiao_id")            # 三条 ID 标签处的文字
    LOCATION = (AppiumBy.ID, f"{PACKAGE_ID}/tv_location")           # 所在地标签处的文字
    
    # 业务功能列表项
    SET_REMARK_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/title_remark")   # 设置备注
    RECOMMEND_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/share_to_friend") # 推荐给朋友
    MOMENTS_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/title_moments")     # 动态
    MORE_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/title_more")           # 更多
    MAIN = (AppiumBy.ID, f"{PACKAGE_ID}/main")                      # 更多-NEW
    
    # 底部操作按钮区域
    BOTTOM_BAR = (AppiumBy.ID, f"{PACKAGE_ID}/friend")              # 底部按钮容器包含发送消息和视频通话
    SEND_MSG_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/send_message")      # 发送消息
    CALL_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/video_call")            # 视频通话


    # === 非好友详情页面 ===
    WHITE_UNFRIEND = (AppiumBy.ID, f"{PACKAGE_ID}/white_unfriend")  # 申请添加好友按钮



    # === 添加好友页面 ===
    # 添加好友页面 - 头像
    ADD_FRIEND_IV_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_avatar')
    # 添加好友页面 - 昵称
    ADD_FRIEND_TV_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_name')
    ADD_FRIEND_TV_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/tv_name"]//android.widget.TextView')
    # 添加好友页面 - 所在地
    ADD_FRIEND_TV_LOCATION = (AppiumBy.ID, f'{PACKAGE_ID}/tv_location')
    # 添加好友页面 - 好友资料容器
    ADD_FRIEND_LL= (AppiumBy.ID, f'{PACKAGE_ID}/ll')
    # 好友资料容器 - 好友资料标题行
    ADD_FRIEND_TITLE_REMARK = (AppiumBy.ID, f'{PACKAGE_ID}/title_remark')
    # 好友资料容器 - 资料卡标题容器
    ADD_FRIEND_TV_PROFILE_CARD_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/profile_card_title')
    # 好友资料容器 - 资料卡描述容器
    ADD_FRIEND_TV_PROFILE_CARD_DESC = (AppiumBy.ID, f'{PACKAGE_ID}/profile_card_desc')

    # 添加好友页面 - 好友动态
    ADD_FRIEND_TITLE_MOMENTS = (AppiumBy.ID, f'{PACKAGE_ID}/title_moments')  
    ADD_FRIEND_TITLE_TV = (AppiumBy.ID, f'{PACKAGE_ID}/title_tv')

    # 添加好友页面 - 未添加好友
    ADD_FRIEND_TV_NOT_FRIENDS = (AppiumBy.ID, f'{PACKAGE_ID}/cl_un_friends')
    ADD_FRIEND_TV_ADD_FRIEND = (AppiumBy.ID, f'{PACKAGE_ID}/add_friend')
    ADD_FRIEND_TV_ADD_FRIEND_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/add_friend"]//android.widget.TextView')



    # 好友详情页顶部
    IV_RIGHT = (AppiumBy.ID, f"{PACKAGE_ID}/iv_right")                      # 右上角更多图标
    IV_BACK = CommonLocator.TOP_IV_BACK_BTN                                 # 返回按钮
    CONFIRM_TWO_BTN = CommonLocator.DIALOG_CONFIRM_BTN                      # 二次确认按钮
    CANCEL_TWO_BTN = CommonLocator.DIALOG_CANCEL_BTN                        # 二次取消按钮
    TV_TITLE = CommonLocator.TOP_TV_TITLE                                   # 页面标题


    # 好友详情页解除好友关系
    UNFRIEND_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/card_unfriend")            # 解除好友关系
    UNFRIEND_TV_UNFRIEND = (AppiumBy.ID, f"{PACKAGE_ID}/tv_unfriend")       # 解除好友


    # === 设置备注与标签页面 (RemarkSetting) ===
    TV_CARD_REMARK = (AppiumBy.ID, f"{PACKAGE_ID}/card_remark")             # 设置备注与标签
    REMARK_NAME_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/item_remark_name")      # 备注名item
    ET_REMARK = (AppiumBy.ID, f"{PACKAGE_ID}/et_remark")                    # 备注名输入框
    IV_REMARK_CLEAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_remark_clear")        # 备注名清除按钮
    TV_NICKNAME_HINT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_nickname_hint")      # 昵称提示

    ROW_ADD_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/row_add_phone")            # 添加电话
    IV_ADD_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/iv_add_phone")              # 添加电话图标按钮
    RV_PHONE_LIST = (AppiumBy.ID, f"{PACKAGE_ID}/rv_phone_list")            # 电话列表
    SWIPE_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/swipe_phone")                # 电话行
    IV_PHONE_LEFT = (AppiumBy.ID, f"{PACKAGE_ID}/iv_phone_left")            # 电话左侧图标
    TV_PHONE_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_phone_value")          # 电话值
    
    ROW_ADD_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/row_add_tag")                # 添加标签行容器
    TV_ADD_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/tv_add_tag")                  # 添加标签文字
    FB_DONE = (AppiumBy.ID, f"{PACKAGE_ID}/fb_done")                        # 完成按钮
    ET_SEARCH = (AppiumBy.ID, f"{PACKAGE_ID}/et_search")                    # 搜索输入框
    LL_CREATE_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/ll_create_tag")            # 创建新标签容器
    TV_CREATE_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/tv_create_tag")            # 创建新标签按钮
    ET_TAG_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/et_tag_name")                # 标签名称输入框
    FB_CREATE_DONE = (AppiumBy.ID, f"{PACKAGE_ID}/fb_create_done")          # 创建新标签完成按钮
    CHIP_GROUP = (AppiumBy.ID, f"{PACKAGE_ID}/chip_group")                  # 标签组容器
    
    CARD_MEMO = (AppiumBy.ID, f"{PACKAGE_ID}/card_memo")                    # 备注卡片
    IV_MEMO_CLEAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_memo_clear")            # 备注清除按钮
    
    
    # 更多信息与共同群聊
    ITEM_COMMON_GROUPS = (AppiumBy.ID, f"{PACKAGE_ID}/item_common_groups")          # 共同群聊
    TV_COMMON_GROUPS_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_common_groups_title")  # 共同群聊标题
    TV_COMMON_GROUPS_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_common_groups_value")  # 共同群聊数量
    
    # 共同群聊详情页面
    TV_SEARCH_HINT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_search_hint")                  # 搜索共同群聊
    TV_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")                                # 群聊列表项





