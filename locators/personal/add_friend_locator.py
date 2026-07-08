from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class AddFriendLocator:
    """添加朋友页面定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 搜索输入框
    SEARCH_INPUT = (AppiumBy.ID, f"{PACKAGE_ID}/et_search")

    # 展开搜索条目（如“搜索: 13800000000”）
    SEARCH_ITEM = (AppiumBy.XPATH, "//*[contains(@text, '搜索:')]")

    # 返回按钮
    BACK_BTN = CommonLocator.TOP_IV_BACK_BTN
