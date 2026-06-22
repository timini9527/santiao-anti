from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class GroupNoticeLocator:
    """群公告页面定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部元素
    TITLE = CommonLocator.TOPBAR_TITLE                                                        # 页面标题
    BACK_BTN = CommonLocator.TOPBAR_LEFT_BACK_BTN                                             # 返回按钮
    PUBLISH_BTN = CommonLocator.TOPBAR_RIGHT_FINISH_BTN                                       # 发布/确定按钮

    # 编辑区域与列表
    NOTICE_CONTENT_INPUT = (AppiumBy.ID, f"{PACKAGE_ID}/announcement_et")                     # 群公告编辑框
    NOTICE_CONTENT_DISPLAY = (AppiumBy.ID, f"{PACKAGE_ID}/sub_title_tv")                      # 群公告显示文本
    