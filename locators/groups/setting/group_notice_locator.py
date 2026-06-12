from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class GroupNoticeLocator:
    """群公告页面定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部元素
    TITLE = CommonLocator.TOP_TV_TITLE                                                        # 页面标题
    BACK_BTN = CommonLocator.TOP_IV_BACK_BTN                                                  # 返回按钮
    PUBLISH_BTN = CommonLocator.TOP_FB_ACTION_BTN                                             # 发布/确定按钮

    # 编辑区域与列表
    NOTICE_CONTENT_INPUT = (AppiumBy.ID, f"{PACKAGE_ID}/et_content")                          # 公告编辑框
    NOTICE_DISPLAY_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_content")                           # 已发布公告显示文本
    
    # 二次确认弹窗
    CONFIRM_BTN = CommonLocator.TEXT_CONFIRM_BTN                                              # 二次确认
    CANCEL_BTN = CommonLocator.TEXT_CANCEL_BTN                                                # 二次取消
