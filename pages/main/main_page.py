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

    # 检测当前是否处于搜索覆盖层页面
    def is_in_search_page(self, timeout: int = 1) -> bool:
        """检测当前是否正处于搜索覆盖层页面（通过搜索结果特有文本或取消按钮判断）"""
        search_indicators = [
            HomeLocator.SEARCH_CLEAR
        ]
        for locator in search_indicators:
            try:
                if self.is_element_exist(locator, timeout=timeout, raise_exception=False):
                    return True
            except Exception:
                continue
        return False

    # 判断当前是否已处于主页面
    def is_in_main_page(self, timeout: int = 1, raise_exception: bool = False) -> bool:
        """ 判断当前是否已处于主页面（增加搜索覆盖层排他防御与标题强校验） """
        if self.is_in_search_page(timeout=timeout):
            logger.warning("⚠️ 检测到当前处于搜索结果覆盖层，非真正主页面")
            return False

        title = self.get_attribute(HomeLocator.MIDDLE_TITLE, 'text', timeout=timeout, raise_exception=raise_exception)
        if title and '三条' in title:
            logger.info(f"🍏 当前已成功处于主页面 (Title: {title})")
            return True

        if (
            self.is_element_exist(HomeLocator.LEFT_MENU, timeout=timeout, raise_exception=raise_exception)
            and self.is_element_exist(HomeLocator.RIGHT_MENU, timeout=timeout, raise_exception=raise_exception)
        ):
            logger.info("🍏 当前已成功处于主页面 (检测到 Home 专属导航图标)")
            return True

        logger.warning("⚠️ 当前未处于主页面")
        return False

    # 返回并进入主页面
    def go_to_main_page(self, timeout: int = 1, raise_exception: bool = False, max_retries: int = 10) -> None:
        """进入主页面消息列表页面；若处于搜索层等中间覆盖态，优先退回并关闭搜索层"""
        logger.info("准备返回主页面消息列表...")
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

        while max_retries > 0:
            if self.is_in_main_page(timeout=timeout, raise_exception=raise_exception):
                logger.info("🍏 当前已成功处于主页面，无需退回")
                return

            if self.is_in_search_page(timeout=1):
                logger.info("🔎 检测到当前卡在搜索覆盖层，尝试点击取消/清除以退出搜索...")
                if self.is_element_exist(HomeLocator.SEARCH_CANCEL, timeout=1, raise_exception=False):
                    logger.info("点击搜索取消按钮退出搜索覆盖层")
                    self.click(HomeLocator.SEARCH_CANCEL, force_wait=True)
                    continue

            try:
                logger.warning(f"⚠️ 当前未处于主页面，执行多级安全退回... 剩余尝试次数：{max_retries}")
                logger.info("执行返回操作以退回主页面...")
                self.back()
                logger.info(f"🍎 退回操作已完成，等待转场动画稳定")
            except Exception as e:
                logger.error(f"❌ [Back] 退回操作捕获异常: {e}")
            max_retries -= 1
        logger.error("❌ 多次退回后仍无法返回主页面")