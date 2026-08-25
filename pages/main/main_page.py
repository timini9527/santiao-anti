import time
import subprocess
from selenium.webdriver.common.by import By
from common.base_page import BasePage
from core.logger_utils import logger
from locators.home.home_locator import HomeLocator
from locators.main.main_locator import MainLocator
from selenium.common.exceptions import WebDriverException

#   主页面
class MainPage(BasePage):

    def is_in_main_page(self, timeout: int = 1, raise_exception: bool = False) -> bool:
        """ 判断当前是否已处于主页面（结合主页特有导航图标、底部导航栏与标题综合判定） """
        if (
            self.is_element_exist(HomeLocator.LEFT_MENU, timeout=timeout, raise_exception=raise_exception)
            or self.is_element_exist(HomeLocator.RIGHT_MENU, timeout=timeout, raise_exception=raise_exception)
            or self.is_element_exist(HomeLocator.BOTTOM, timeout=timeout, raise_exception=raise_exception)
        ):
            logger.info("🍏 当前已成功处于主页面 (检测到 Home 专属导航组件)")
            return True

        title = self.get_attribute(HomeLocator.MIDDLE_TITLE, 'text', timeout=timeout, raise_exception=raise_exception)
        if title and '三条' in title:
            logger.info(f"🍏 当前已成功处于主页面 (Title: {title})")
            return True
        
        logger.warning("⚠️ 当前未处于主页面")
        return False

    def go_to_main_page(self, timeout: int = 1, raise_exception: bool = False, max_retries: int = 10):
        """进入主页面消息列表页面；若当前已在主页则直接返回，避免误按返回键退至后台"""
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

        while max_retries > 0:
            if self.is_in_main_page(timeout=timeout, raise_exception=raise_exception):
                logger.info("🍏 当前已成功处于主页面，无需退回")
                return
            try:
                logger.warning(f"⚠️ 当前未处于主页面，执行多级安全退回... 剩余尝试次数：{max_retries}")
                self.back()
                logger.info(f"🍎 退回操作已完成，等待转场动画稳定")
            except Exception as e:
                logger.error(f"❌ [Back] 退回操作捕获异常: {e}")
            max_retries -= 1
        logger.error("❌ 多次退回后仍无法返回主页面")