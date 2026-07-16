from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class ContactDetailLocator:
    """好友资料详情页定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID
    
    # 头部个人资料区域
    AVATAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_avatar")               # 头像
    NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")                   # 顶部显示的昵称

    
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
    # 好友资料容器 - 备注容器
    ADD_FRIEND_TV_REMARK = (AppiumBy.ID, f'{PACKAGE_ID}/title_remark')
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
    CONFIRM_TWO_BTN = CommonLocator.DIALOG_CONFIRM_BTN                      # 确认按钮
    CANCEL_TWO_BTN = CommonLocator.DIALOG_CANCEL_BTN                        # 取消按钮


    # 好友详情页解除好友关系
    UNFRIEND_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/card_unfriend")            # 解除好友关系
    UNFRIEND_TV_UNFRIEND = (AppiumBy.ID, f"{PACKAGE_ID}/tv_unfriend")       # 解除好友





