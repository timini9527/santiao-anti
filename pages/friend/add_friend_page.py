import time
from common.base_page import BasePage
from locators.friend.add_friend_locator import AddFriendLocator
from core.logger_utils import logger
from selenium.webdriver.remote.webelement import WebElement




class AddFriendPage(BasePage):
    """添加朋友页面对象"""

    # 添加朋友 - 等待添加朋友页面出现
    def wait_for_add_friend_page(self, timeout=10) -> bool:
        """ 添加朋友 - 等待添加朋友页面出现 """
        isExit = self.get_attribute(AddFriendLocator.TV_TITLE, "text", timeout=timeout) == "添加朋友"
        if isExit:
            logger.info("⏳ [Wait - AddFriend] 等待添加朋友页面")
        else:
            logger.error("❌ [Wait - AddFriend] 未能成功进入添加朋友页面")
        return isExit

    # 添加朋友 - 点击返回
    def click_back(self):
        """ 添加朋友 - 点击返回 """
        self.click(AddFriendLocator.IV_BACK)
        logger.info("🔙 [Action - AddFriend] 添加朋友页 - 点击返回")
    
    # 添加朋友 - 点击完成按钮
    def click_finish(self):
        """ 添加朋友 - 点击完成按钮 """
        self.click(AddFriendLocator.FB_ACTION)
        logger.info("🔙 [Action - AddFriend] 添加朋友页 - 点击完成按钮")


    # =================================================================================
    # 搜索功能
    # =================================================================================
    # 添加朋友 - 获取搜索框内部文本
    def get_search_input_text(self) -> str:
        """ 添加朋友 - 获取搜索框内部文本 """
        text = self.get_attribute(AddFriendLocator.SEARCH_ENTRY_XPATH, "text")
        if text:
            logger.info(f"🔍 [Action - AddFriend] 添加朋友页 - 搜索框内部文本: {text}")
        else:
            logger.error("❌ [Action - AddFriend] 添加朋友页 - 搜索框内部文本获取失败")
        return text
        
    # 添加朋友 - 点击搜索框
    def click_search_input(self):
        """ 添加朋友 - 点击搜索框 """
        self.click(AddFriendLocator.SEARCH_ENTRY_XPATH)
        logger.info("⚙️ [Action - AddFriend] 添加朋友页 - 点击搜索框")
    
    # 添加朋友 - 搜索框输入内容，并搜索好友
    def search_friend_by_content(self, friend_content: str):
        """
        添加朋友 - 输入搜索关键字（手机号或STID或群ID等）并点击搜索项
        Args:
            friend_content: 搜索的手机号或 STID 或 群ID等
        """
        self.click_search_input()
        self.send_keys(AddFriendLocator.ET_SEARCH, friend_content)
        logger.info(f"🔍 [Action - AddFriend] 添加朋友页 - 搜索框输入内容: {friend_content}")
    
    # 添加朋友 - 点击取消
    def click_cancel(self):
        """ 添加朋友 - 点击取消 """
        self.click(AddFriendLocator.TV_CANCEL)
        logger.info("🔙 [Action - AddFriend] 添加朋友页 - 点击取消")

    # 添加朋友 - 点击确认搜索
    def click_confirm_search(self):
        """ 添加朋友 - 点击确认搜索 """
        self.click(AddFriendLocator.TV_SEARCH_KEY_MARK)
        logger.info("⚙️ [Action - AddFriend] 添加朋友页 - 点击确认搜索")
    
    # 添加朋友 - 获取搜索结果昵称 item
    def get_search_result_item(self, raise_exception: bool = True) -> WebElement | None:
        """ 添加朋友 - 获取搜索结果item """
        item = self.find_element(AddFriendLocator.RESULT_ITEM_TV_NAME, timeout=2, raise_exception=raise_exception)
        if item:
            logger.info("🔍 [Action - AddFriend] 搜索结果item获取成功")
        else:
            logger.warning("⚠️ [Action - AddFriend] 搜索结果item获取失败")
        return item

    # 添加朋友 - 获取搜索结果item中的昵称
    def get_search_result_item_name(self) -> str:
        """ 添加朋友 - 获取搜索结果item中的昵称 """
        item = self.get_search_result_item()
        if item:
            name = item.get_attribute("text")
            if name:
                logger.info(f"🔍 [Action - AddFriend] 搜索结果item中的昵称: {name}")
            else:
                logger.error("❌ [Action - AddFriend] 搜索结果item中的昵称获取失败")
            return name
        else:
            logger.error("❌ [Action - AddFriend] 搜索结果item获取失败")
            return 
    
    # 添加朋友 - 点击搜索结果item
    def click_search_result_item(self):
        """ 添加朋友 - 点击搜索结果item """
        item = self.get_search_result_item()
        if item:
            item.click()
            logger.info("⚙️ [Action - AddFriend] 添加朋友页 - 点击搜索结果item")
        else:
            logger.error("❌ [Action - AddFriend] 搜索结果item获取失败，无法点击")
    
    # 添加朋友 - 输入备注
    def input_remark(self, remark: str):
        """ 添加朋友 - 输入备注 """
        self.send_keys(AddFriendLocator.INPUT_REMARK, remark)
        logger.info(f"📝 [Action - AddFriend] 添加朋友页 - 输入备注: {remark}")

    # 添加朋友 - 发送申请
    def click_send_apply(self, remark: str):
        """ 添加朋友 - 发送申请 """
        self.input_remark(remark)
        self.click_finish()
        logger.info("⚙️ [Action - AddFriend] 添加朋友页 - 发送申请")

    # 添加朋友 - 获取搜索结果item中的消息
    def get_search_result_item_message(self) -> str:
        """ 添加朋友 - 获取搜索结果item中的消息 """
        message = self.get_attribute(AddFriendLocator.RESULT_ITEM_TV_MESSAGE, "text")
        if message:
            logger.info(f"🔍 [Action - AddFriend] 搜索结果item中的消息: {message}")
        else:
            logger.warning("⚠️ [Action - AddFriend] 搜索结果item中的消息获取失败")
        return message

    # =================================================================================
    # 发送好友验证页面
    # =================================================================================
    # 添加朋友 - 等待发送朋友验证页面出现
    def wait_for_send_friend_verify_page(self, timeout=10) -> bool:
        """ 添加朋友 - 等待发送朋友验证页面出现 """
        isExit = self.get_attribute(AddFriendLocator.TV_TITLE, "text", timeout=timeout) == "朋友验证"
        if isExit:
            logger.info("⏳ [Wait - AddFriend] 等待发送朋友验证页面")
        else:
            logger.error("❌ [Wait - AddFriend] 未能成功进入发送朋友验证页面")
        return isExit


