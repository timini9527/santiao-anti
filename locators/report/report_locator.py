from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class ReportLocator(CommonLocator):
    PACKAGE_ID = 'com.santiaotalk.im:id'

    TV_REPORT_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{CommonLocator.TOP_TV_TITLE_ID}" and @text="投诉"]')
    # 动态获取具体投诉项（如：“色情”、“赌博”、“违法犯罪及违禁品”等）
    @staticmethod
    def get_option_by_text(text: str) -> tuple:
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{text}")')
        
    # 投诉描述输入框
    REPORT_DESC_INPUT = (AppiumBy.CLASS_NAME, 'android.widget.EditText')
    
    # 提交按钮
    REPORT_SUBMIT_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("提交")')
    
