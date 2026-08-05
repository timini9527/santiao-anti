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

    def is_in_main_page(self, timeout: int = 1) -> bool:
        """ 判断当前是否已处于主页面 """
        title = self.get_attribute(HomeLocator.MIDDLE_TITLE, 'text', timeout=timeout, raise_exception=False)
        if title and '三条' in title:
            logger.info(" 🍏 当前已成功处于主页面 (Title: 三条)")
            return True
        
        logger.warning(" ⚠️ 当前未处于主页面")
        return False

    def go_to_main_page(self, timeout: int = 1, max_retries: int = 10):
        """进入主页面消息列表页面；若当前已在主页则直接返回，避免误按返回键退至后台"""
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

        while max_retries > 0:
            if self.is_in_main_page(timeout=timeout):
                logger.info(" 🍏 当前已成功处于主页面，无需退回")
                time.sleep(0.5)
                return

            try:
                logger.warning(f" ⚠️ 当前未处于主页面，执行安全退回... 剩余尝试次数：{max_retries}")
                self.back()
                # self.driver.press_keycode(4)  # 改用 KeyCode 4 物理返回
                logger.info(f" 🍎 退回操作正在执行")
                
                # udid = self.driver.capabilities.get("udid")
                # cmd = f"adb -s {udid} shell input keyevent 4" if udid else "adb shell input keyevent 4"
                # subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # logger.info(" 🔙 [ADB Direct] 本地直连发送物理返回键成功")
            except WebDriverException as e:
                logger.error(f"❌ [Back] 退回操作过程捕获通信波动: {e}")
                time.sleep(1)

            max_retries -= 1

        logger.error("❌ 多次退回后仍无法返回主页面")