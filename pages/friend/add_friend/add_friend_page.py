import time
from common.base_page import BasePage
from locators.friend.add_friend.add_friend_locator import AddFriendLocator
from core.logger_utils import logger
from selenium.webdriver.remote.webelement import WebElement




class AddFriendPage(BasePage):
    """添加朋友页面对象"""

    # 添加朋友 - 等待添加朋友页面出现
    def wait_for_add_friend_page(self, timeout: int = 10, raise_exception: bool = False) -> bool:
        """ 添加朋友 - 等待添加朋友页面出现 """
        isExit = self.wait_for_element_text(AddFriendLocator.TV_TITLE, expected_text="添加朋友", timeout=timeout, raise_exception=raise_exception)
        if isExit:
            logger.info("⏳ [Wait - AddFriend] 等待添加朋友页面")
        else:
            logger.error("❌ [Wait - AddFriend] 未能成功进入添加朋友页面")
        return isExit

    # 添加朋友 - 点击返回
    def click_back(self) -> None:
        """ 添加朋友 - 点击返回 """
        logger.info("🔙 [Action - AddFriend] 添加朋友页 - 点击返回")
        self.click(AddFriendLocator.IV_BACK)
    
    # 添加朋友 - 点击完成按钮
    def click_finish(self) -> None:
        """ 添加朋友 - 点击完成按钮 """
        logger.info("🔙 [Action - AddFriend] 添加朋友页 - 点击完成按钮")
        self.click(AddFriendLocator.FB_ACTION)


    # =================================================================================
    # 搜索功能
    # =================================================================================
    # 添加朋友 - 获取搜索框内部文本
    def get_search_input_text(self) -> str:
        """ 添加朋友 - 获取搜索框内部文本 """
        logger.info("🔍 [Action - AddFriend] 获取搜索框内部文本")
        text = self.get_attribute(AddFriendLocator.SEARCH_ENTRY_XPATH, "text")
        if text:
            logger.info(f"🔍 [Action - AddFriend] 添加朋友页 - 搜索框内部文本: {text}")
        else:
            logger.error("❌ [Action - AddFriend] 添加朋友页 - 搜索框内部文本获取失败")
        return text or ""
        
    # 添加朋友 - 点击搜索框
    def click_search_input(self) -> None:
        """ 添加朋友 - 点击搜索框 """
        logger.info("⚙️ [Action - AddFriend] 添加朋友页 - 点击搜索框")
        self.click(AddFriendLocator.SEARCH_ENTRY_XPATH)
    
    # 添加朋友 - 搜索框输入内容，并搜索好友
    def search_friend_by_content(self, friend_content: str) -> None:
        """
        添加朋友 - 输入搜索关键字（手机号或STID或群ID等）并点击搜索项
        Args:
            friend_content: 搜索的手机号或 STID 或 群ID等
        """
        logger.info(f"🔍 [Action - AddFriend] 添加朋友页 - 准备搜索内容: {friend_content}")
        self.click_search_input()
        if friend_content:
            self.send_keys(AddFriendLocator.ET_SEARCH, friend_content)
    
    # 添加朋友 - 点击取消
    def click_cancel(self) -> None:
        """ 添加朋友 - 点击取消 """
        logger.info("🔙 [Action - AddFriend] 添加朋友页 - 点击取消")
        self.click(AddFriendLocator.TV_CANCEL)

    # 添加朋友 - 点击确认搜索
    def click_confirm_search(self) -> None:
        """ 添加朋友 - 点击确认搜索 """
        logger.info("⚙️ [Action - AddFriend] 添加朋友页 - 点击确认搜索")
        self.click(AddFriendLocator.TV_SEARCH_KEY_MARK)

    # 添加朋友 - 判断确认搜索项是否可见
    def is_confirm_search_visible(self, timeout: int = 1) -> bool:
        """添加朋友 - 判断确认搜索项是否可见"""
        logger.info(f"🔍 [Action - AddFriend] 检查确认搜索项是否可见 (超时: {timeout}s)")
        visible = self.is_element_exist(AddFriendLocator.TV_SEARCH_KEY_MARK, timeout=timeout, raise_exception=False)
        if visible:
            logger.info("✅ [Action - AddFriend] 添加朋友页 - 确认搜索项可见")
        else:
            logger.warning("⚠️ [Action - AddFriend] 添加朋友页 - 确认搜索项不可见")
        return visible
    
    # 添加朋友 - 获取搜索结果昵称 item
    def get_search_result_item(self, raise_exception: bool = True) -> WebElement | None:
        """ 添加朋友 - 获取搜索结果item """
        logger.info("🔍 [Action - AddFriend] 获取搜索结果item")
        item = self.find_element(AddFriendLocator.RESULT_ITEM_TV_NAME, timeout=2, raise_exception=raise_exception)
        if item:
            logger.info("🔍 [Action - AddFriend] 搜索结果item获取成功")
        else:
            logger.warning("⚠️ [Action - AddFriend] 搜索结果item获取失败")
        return item

    # 添加朋友 - 获取搜索结果item中的昵称
    def get_search_result_item_name(self) -> str:
        """ 添加朋友 - 获取搜索结果item中的昵称 """
        logger.info("🔍 [Action - AddFriend] 获取搜索结果item中的昵称")
        item = self.get_search_result_item()
        if item:
            name = item.get_attribute("text")
            if name:
                logger.info(f"🔍 [Action - AddFriend] 搜索结果item中的昵称: {name}")
                return name
            else:
                logger.error("❌ [Action - AddFriend] 搜索结果item中的昵称获取失败")
                return ""
        else:
            logger.error("❌ [Action - AddFriend] 搜索结果item获取失败")
            return ""
    
    # 添加朋友 - 点击搜索结果item
    def click_search_result_item(self) -> None:
        """ 添加朋友 - 点击搜索结果item """
        logger.info("⚙️ [Action - AddFriend] 添加朋友页 - 准备点击搜索结果item")
        item = self.get_search_result_item()
        if item:
            logger.info("⚙️ [Action - AddFriend] 添加朋友页 - 点击搜索结果item")
            item.click()
        else:
            logger.error("❌ [Action - AddFriend] 搜索结果item获取失败，无法点击")
        time.sleep(1)
    
    # 添加朋友 - 输入备注
    def input_remark(self, remark: str) -> None:
        """ 添加朋友 - 输入备注 """
        logger.info(f"📝 [Action - AddFriend] 添加朋友页 - 输入备注: {remark}")
        self.send_keys(AddFriendLocator.INPUT_REMARK, remark)

    # 添加朋友 - 发送申请
    def click_send_apply(self, remark: str) -> None:
        """ 添加朋友 - 发送申请 """
        logger.info(f"⚙️ [Action - AddFriend] 添加朋友页 - 发送申请 (备注: {remark})")
        self.input_remark(remark)
        self.click_finish()

    # 添加朋友 - 获取搜索结果item中的消息
    def get_search_result_item_message(self) -> str:
        """ 添加朋友 - 获取搜索结果item中的消息 """
        logger.info("🔍 [Action - AddFriend] 获取搜索结果item中的消息")
        message = self.get_attribute(AddFriendLocator.RESULT_ITEM_TV_MESSAGE, "text")
        if message:
            logger.info(f"🔍 [Action - AddFriend] 搜索结果item中的消息: {message}")
        else:
            logger.warning("⚠️ [Action - AddFriend] 搜索结果item中的消息获取失败")
        return message or ""

    # =================================================================================
    # 发送好友验证页面
    # =================================================================================
    # 添加朋友 - 等待发送朋友验证页面出现
    def wait_for_send_friend_verify_page(self, timeout: int = 10) -> bool:
        """ 添加朋友 - 等待发送朋友验证页面出现 """
        logger.info(f"⏳ [Wait - AddFriend] 等待发送朋友验证页面出现 (超时: {timeout}s)")
        isExit = self.get_attribute(AddFriendLocator.TV_TITLE, "text", timeout=timeout) == "朋友验证"
        if isExit:
            logger.info("⏳ [Wait - AddFriend] 等待发送朋友验证页面成功")
        else:
            logger.error("❌ [Wait - AddFriend] 未能成功进入发送朋友验证页面")
        return isExit

    # =================================================================================
    # 顶部导航功能 (二维码、扫一扫)
    # =================================================================================
    def click_title_qrcode(self) -> None:
        """添加朋友页 - 点击顶部二维码图标"""
        logger.info("⚙️ [Action - AddFriend] 点击顶部二维码图标")
        self.click(AddFriendLocator.IV_TITLE_QRCODE)

    def click_title_scan(self) -> None:
        """添加朋友页 - 点击顶部扫一扫图标"""
        logger.info("⚙️ [Action - AddFriend] 点击顶部扫一扫图标")
        self.click(AddFriendLocator.IV_TITLE_SCAN)

