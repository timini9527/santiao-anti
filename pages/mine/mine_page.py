from selenium.webdriver.common.by import By
from common.base_page import BasePage
from core.logger_utils import logger
from appium.webdriver.common.appiumby import AppiumBy

#   我的
class MinePage(BasePage):

    MENU_MINE = (By.ID, 'lottie_mine')
    COMMON_SETTING = (By.ID, 'currency_layout')
    EXIT_LAYOUT = (By.ID, 'setting_exit_layout')
    LAYOUT_TV = (By.ID, 'logout_tv')

    MINE_FEED = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的动态")')
    MSG_NOTIF = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("消息通知")')
    PRIVACY_PROTECTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("隐私防护")')
    ACCOUNT_SECURITY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("账号安全")')
    GENERAL_SETTING = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("通用设置")')

    # 通用设置中的元素


    def enter_mine_page(self):
        # 进入我的页面
        self.click(self.MENU_MINE)


    def exit_login_page(self) -> bool:
        #  是否已经登录上
        exit_l = self.find_element(self.MENU_MINE)
        print(f"账号异常，需要退出: {exit_l}")
        if exit_l is not None:
            logger.info(f"已在我的页面，需要退出: {exit_l}")
            self.click(self.MENU_MINE)
            self.click(self.COMMON_SETTING)
            self.click(self.EXIT_LAYOUT)
            self.click(self.LAYOUT_TV)
            return True
        return False




