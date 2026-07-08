import time
from pages.common.common_page import CommonPage
from locators.personal.add_friend_locator import AddFriendLocator
from core.logger_utils import logger

class AddFriendPage(CommonPage):
    """添加朋友页面对象"""

    def search_friend(self, search_key: str):
        """
        输入搜索关键字（手机号或ID）并点击搜索项
        Args:
            search_key: 搜索的手机号或 ID
        """
        logger.info(f"🔎 [Action] 添加朋友页 - 输入关键字: {search_key}")
        self.send_keys(AddFriendLocator.SEARCH_INPUT, search_key)
        time.sleep(1)
        
        logger.info("⚙️ [Action] 添加朋友页 - 点击 [搜索: xxx] 条目")
        self.click(AddFriendLocator.SEARCH_ITEM)
        time.sleep(2.5)  # 等待页面加载与跳转

    def click_back(self):
        """点击返回"""
        logger.info("🔙 [Action] 添加朋友页 - 点击返回")
        self.click(AddFriendLocator.BACK_BTN)
