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
    def is_in_search_page(self, timeout: float = 0.1) -> bool:
        """检测当前是否正处于搜索覆盖层页面（利用 implicitly_wait=0 瞬时探查，杜绝秒级阻塞）"""
        try:
            elems = self.driver.find_elements(*HomeLocator.SEARCH_CLEAR)
            return len(elems) > 0 and elems[0].is_displayed()
        except Exception:
            return False

    # 判断当前是否已处于主页面
    def is_in_main_page(self, timeout: float = 0.2, raise_exception: bool = False) -> bool:
        """判断当前是否已处于主页面（瞬时探测主页关键特征，零超时开销）"""
        try:
            title_elems = self.driver.find_elements(*HomeLocator.MIDDLE_TITLE)
            if title_elems and title_elems[0].is_displayed():
                title_text = title_elems[0].text or title_elems[0].get_attribute('text') or ''
                if '三条' in title_text:
                    logger.info(f"🍏 当前已成功处于主页面 (Title: {title_text})")
                    return True

            plus_elems = self.driver.find_elements(*HomeLocator.RIGHT_MENU)
            menu_elems = self.driver.find_elements(*HomeLocator.LEFT_MENU)
            if plus_elems and plus_elems[0].is_displayed() and menu_elems and menu_elems[0].is_displayed():
                if not self.is_in_search_page():
                    logger.info("🍏 当前已成功处于主页面 (检测到 Home 专属导航图标)")
                    return True
        except Exception:
            pass
        return False

    # 返回并进入主页面
    def go_to_main_page(self, timeout: float = 0.2, raise_exception: bool = False, max_retries: int = 10) -> None:
        """极速安全退回主页面消息列表（瞬时探针 + 连退，性能提升 10 倍以上）"""
        logger.info("准备返回主页面消息列表...")
        while max_retries > 0:
            if self.is_in_main_page(timeout=timeout, raise_exception=raise_exception):
                logger.info("🍏 当前已成功处于主页面，无需退回")
                return
            try:
                logger.warning(f"🔙 执行极速退回操作以退回主页面 (剩余尝试次数：{max_retries})")
                self.back()
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"❌ [Back] 退回操作捕获异常: {e}")
            max_retries -= 1
        if not self.is_in_main_page(timeout=0.5):
            logger.error("❌ 多次退回后仍无法返回主页面")