import time
from selenium.webdriver.common.by import By
from common.base_page import BasePage
from core.logger_utils import logger
from locators.home.home_locator import HomeLocator
from locators.main.main_locator import MainLocator


#   主页面
class MainPage(BasePage):

    def is_login_success(self) -> bool:
        """通过判断底部菜单是否存在来确认登录成功"""
        main_page = self.find_element(MainLocator.MENU_MAIN)
        logger.info(f"已在主页面: {main_page}")
        return main_page is not None

    def go_to_message_page(self):
        """进入消息页面"""
        self.click(MainLocator.MENU_MAIN, force_wait=True)
        logger.info("🚀 [Action] 进入消息页面")

    def go_to_moments_page(self):
        """进入朋友圈（动态）页面"""
        self.click(HomeLocator.DYNAMIC)
        logger.info("🚀 [Action] 进入朋友圈（动态）页面")

    def go_to_friends_page(self):
        """进入好友列表页面"""
        self.click(HomeLocator.FRIEND)
        logger.info("🚀 [Action] 进入好友列表页面")

    # 等待主页面加载完成
    def wait_for_main_page_load(self, timeout: int = 10):
        """等待主页面加载完成"""
        title = self.get_attribute(HomeLocator.MIDDLE_TITLE,'text', expect_missing=True)
        if '三条' in title:
            logger.info(f" 🍏 已找到会话列表标题 {title}，主页面加载完成")
            time.sleep(2)
            return

    def go_to_main_page(self, max_retries: int = 10):
        """进入主页面消息列表页面，没有找到后，返回知道找到"""
        while max_retries > 0:
            title = self.get_attribute(HomeLocator.MIDDLE_TITLE,'text', expect_missing=True)
            if '三条' in title:
                logger.info(f" 🍏 已找到会话列表标题 {title}，回到主页面会话列表")
                time.sleep(3)
                return
            self.back()
            time.sleep(1)  # 短暂等待页面加载
            max_retries -= 1
            logger.warning(f" 🍎 未找到会话列表标题或标题不匹配，继续返回，剩余尝试次数：{max_retries}")