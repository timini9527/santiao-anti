from selenium.webdriver.common.by import By
from common.base_page import BasePage
from core.logger_utils import logger, LogIcon
from appium.webdriver.common.appiumby import AppiumBy


class MinePage(BasePage):
    """我的页面对象"""

    MENU_MINE = (By.ID, 'lottie_mine')
    COMMON_SETTING = (By.ID, 'currency_layout')
    EXIT_LAYOUT = (By.ID, 'setting_exit_layout')
    LAYOUT_TV = (By.ID, 'logout_tv')

    MINE_FEED = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的动态")')
    MSG_NOTIF = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("消息通知")')
    PRIVACY_PROTECTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("隐私防护")')
    ACCOUNT_SECURITY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("账号安全")')
    GENERAL_SETTING = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("通用设置")')

    # 我的 - 点击进入我的页面
    def enter_mine_page(self) -> None:
        """ 进入我的页面 """
        logger.info(f"{LogIcon.SETUP} 点击底部导航【我的】进入我的页面")
        self.click(self.MENU_MINE)

    # 我的 - 退出登录操作
    def exit_login_page(self) -> bool:
        """ 退出登录操作，若当前已登录则执行退出 """
        logger.info(f"{LogIcon.SETUP} 检查登录状态并准备退出登录")
        exit_l = self.find_element(self.MENU_MINE, timeout=2, expect_missing=True)
        if exit_l is not None:
            logger.info(f"{LogIcon.SETUP} 检测到已在登录状态，开始执行退出步骤")
            logger.info(f"{LogIcon.SETUP} 点击【我的】导航")
            self.click(self.MENU_MINE)
            logger.info(f"{LogIcon.SETUP} 点击【通用设置】")
            self.click(self.COMMON_SETTING)
            logger.info(f"{LogIcon.SETUP} 点击【退出登录】入口")
            self.click(self.EXIT_LAYOUT)
            logger.info(f"{LogIcon.SETUP} 点击【确认退出】")
            self.click(self.LAYOUT_TV)
            logger.info(f"{LogIcon.SUCCESS} 退出登录成功")
            return True
        logger.warning(f"{LogIcon.WARN} 未在登录状态，无需退出")
        return False
