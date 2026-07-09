import time
from selenium.webdriver.common.by import By
from common.base_page import BasePage
from core.logger_utils import logger
from locators.home.home_locator import HomeLocator
from locators.main.main_locator import MainLocator


#   主页面
class MainPage(BasePage):

    def go_to_main_page(self, timeout: int = 1, max_retries: int = 10):
        """进入主页面消息列表页面，没有找到后，返回直到找到"""
        from selenium.common.exceptions import WebDriverException
        while max_retries > 0:
            title = self.get_attribute(HomeLocator.MIDDLE_TITLE,'text', timeout=timeout, expect_missing=True)
            if '三条' in title:
                logger.info(f" 🍏 已找到会话列表标题 {title}，回到主页面会话列表")
                time.sleep(1)
                return
            try:
                self.back()
                time.sleep(1.5)
            except WebDriverException as e:
                logger.error(f"❌ 系统返回失败，UiAutomator2 服务可能已崩溃或通信异常: {e}")
                break
            max_retries -= 1
            logger.warning(f" 🍎 未找到会话列表标题或标题不匹配，继续返回，剩余尝试次数：{max_retries}")