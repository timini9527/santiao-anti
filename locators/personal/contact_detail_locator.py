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
    
    # 底部操作按钮区域
    BOTTOM_BAR = (AppiumBy.ID, f"{PACKAGE_ID}/friend")  # 底部按钮容器包含发送消息和视频通话
    SEND_MSG_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/send_message")   # 发送消息
    CALL_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/video_call")       # 视频通话
