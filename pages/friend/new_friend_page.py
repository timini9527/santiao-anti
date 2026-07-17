import time
from common.base_page import BasePage
from locators.friend.new_friend_locator import NewFriendLocator
from core.logger_utils import logger
from appium.webdriver.webelement import WebElement


class NewFriendPage(BasePage):
    """新的朋友申请列表页面对象 (对应 0.4 添加好友模块 新朋友申请处理)"""

    # 等待页面加载完成
    def wait_for_new_friend_page_load(self, timeout: int = 10) -> bool:
        """ 等待新的朋友页面加载完成 """
        is_exit = self.get_attribute(NewFriendLocator.TV_TITLE, "text", timeout=timeout) == "新的朋友"
        if is_exit:
            logger.info("⏳ [Wait - NewFriend] 新的朋友页面加载完成")
        else:
            logger.error("❌ [Wait - NewFriend] 新的朋友页面加载超时")
        return is_exit

    # 新朋友申请列表 - 点击返回
    def click_iv_back(self):
        """ 新朋友申请列表 - 点击返回按钮 """
        self.click(NewFriendLocator.IV_BACK)
        logger.info("🔙 [Action - NewFriend] 新的朋友页 - 点击返回")

    # 新朋友申请列表 - 点击清空
    def click_fb_delete(self):
        """ 新朋友申请列表 - 点击右上角清空（垃圾桶）按钮 """
        self.click(NewFriendLocator.FB_DELETE)
        logger.info("⚙️ [Action - NewFriend] 新的朋友页 - 点击右上角清空")
        
    # 新朋友申请列表 - 点击确认
    def click_confirm_btn(self):
        """ 新朋友申请列表 - 点击确认清空按钮 """
        self.click(NewFriendLocator.CONFIRM_BTN)
        logger.info("✅ [Action - NewFriend] 新的朋友页 - 点击确认清空")
    
    # 新朋友申请列表 - 点击取消
    def click_cancel_btn(self):
        """ 新朋友申请列表 - 点击取消按钮 """
        self.click(NewFriendLocator.CANCEL_BTN)
        logger.info("❌ [Action - NewFriend] 新的朋友页 - 点击取消清空")

    # 新朋友申请列表 - 输入搜索内容(也是添加好友入口)
    def send_keys_search(self, search_key: str):
        """ 新朋友申请列表 - 在页面顶部的搜索框中输入内容(也是添加好友入口) """
        self.send_keys(NewFriendLocator.ET_SEARCH, search_key)
        logger.info(f"🔍 [Action - NewFriend] 输入搜索内容(也是添加好友入口): {search_key}")


    # 申请列表 - 获取申请列表的Item
    def get_apply_list_item(self) -> list[WebElement]:
        """ 申请列表 - 获取申请列表的Item """
        items = self.find_elements(NewFriendLocator.CL_ITEM)
        if not items:
            logger.warning("⚠️ [Action - NewFriend] 未找到申请列表的Item，请确认是否有新的好友申请，或者是否在列表页面")
            return []
        logger.info(f"✅ [Action - NewFriend] 获取到 {len(items)} 个申请列表的Item")
        return items
    
    # 申请列表 - 获取Item，通过index=0
    def get_apply_item_by_index(self, index: int = 0) -> WebElement:
        """ 申请列表 - 获取指定索引的Item """
        items = self.get_apply_list_item()
        if index < 0 or index >= len(items):
            logger.warning(f"⚠️ [Action - NewFriend] 索引越界，索引: {index}，列表长度: {len(items)}")
            return None
        logger.info(f"✅ [Action - NewFriend] 获取到第 {index + 1} 个申请列表的Item")
        return items[index]
    
    # 申请列表 - 获取Item，通过 nickname
    def get_apply_item_by_nickname(self, nickname: str) -> WebElement:
        """ 申请列表 - 获取指定昵称的Item """
        items = self.get_apply_list_item()
        for item in items:
            if nickname in item.get_attribute("text"):
                logger.info(f"✅ [Action - NewFriend] 获取到 {nickname} 的申请列表的Item")
                return item
        logger.warning(f"⚠️ [Action - NewFriend] 未找到 {nickname} 的申请列表的Item")
        return None
    
    # 申请列表 - 获取Item，通过nickname
    def get_apply_item_by_name(self, nickname: str) -> WebElement | None:
        """ 申请列表 - 获取指定昵称的Item """
        locator = NewFriendLocator.get_apply_item_by_name(nickname)
        item = self.find_element(locator)
        if item:
            logger.info(f"✅ [Action - NewFriend] 获取到 {nickname} 的申请列表的Item")
        else:
            logger.warning(f"⚠️ [Action - NewFriend] 未找到 {nickname} 的申请列表的Item")
        return item
    
    # 申请列表 - 点击同意按钮，通过nickname
    def click_accept_btn_by_name(self, nickname: str) -> bool:
        """ 申请列表 - 点击指定昵称好友的“接受/同意”按钮 """
        locator = NewFriendLocator.get_accept_btn_by_name(nickname)
        try:
            self.click(locator)
            logger.info(f"✅ [Action - NewFriend] 点击了 {nickname} 右侧的接受按钮")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - NewFriend] 点击 {nickname} 右侧的接受按钮失败: {e}")
            return False

    # 申请列表 - 点击指定好友申请条目
    def click_apply_item_by_name(self, sender_name: str) -> bool:
        """ 申请列表 - 点击指定好友昵称的申请条目整行，以进入验证详情页进行深度处理（如修改备注） """
        locator = NewFriendLocator.get_apply_item_by_name(sender_name)
        try:
            self.click(locator, timeout=5)
            logger.info(f"✅ [Action - NewFriend] 点击了 {sender_name} 的申请条目行，准备进入验证详情页")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - NewFriend] 点击 {sender_name} 的申请条目行失败: {e}")
            return False
    
    # 申请列表 - 直接在列表中点击接受好友申请
    def accept_apply_by_name(self, sender_name: str) -> bool:
        """ 申请列表 - 在列表中，直接点击指定好友昵称右侧的“接受/同意”按钮 """
        locator = NewFriendLocator.get_accept_btn_by_name(sender_name)
        try:
            self.click(locator, timeout=5)
            logger.info(f"✅ [Action - NewFriend] 点击了 {sender_name} 右侧的接受按钮")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - NewFriend] 未找到 {sender_name} 右侧的接受按钮: {e}")
            return False
    
    # 申请列表 - 点击删除按钮
    def click_delete_btn(self) -> bool:
        """ 申请列表 - 点击删除按钮 """
        self.click(NewFriendLocator.LL_SWIPE_DELETE, force_wait=True)
        logger.info(f"✅ [Action - NewFriend] 点击了删除按钮")
    
    # 申请列表 - 滑动并删除申请记录
    def swipe_and_delete_by_name(self, nickname: str) -> bool:
        """ 申请列表 - 滑动并删除指定昵称好友的申请记录 """
        item = self.get_apply_item_by_name(nickname)
        if item:
            self.swipe_page_quickly(element=item, slid_type="left", duration=200)
            logger.info(f"✅ [Action - NewFriend] 滑动了 {nickname} 的申请记录")
            self.click_delete_btn()
            return True
        else:
            logger.warning(f"⚠️ [Action - NewFriend] 未找到 {nickname} 的申请列表的Item")
            return False
        
    












    # 验证申请条目的状态文字是否流转
    def verify_apply_status(self, sender_name: str, expected_status: str, timeout: int = 5) -> bool:
        """
        验证列表中指定昵称好友的申请状态是否符合预期（例如“已添加”、“已拒绝”）
        Args:
            sender_name: 申请发送人昵称
            expected_status: 期望的状态文本
            timeout: 超时时间
        Returns:
            bool: 是否流转成功
        """
        locator = NewFriendLocator.get_status_text_by_name(sender_name, expected_status)
        res = self.is_element_exist(locator, timeout=timeout)
        if res:
            logger.info(f"✅ [Action - NewFriend] 校验成功，{sender_name} 的申请状态流转为: {expected_status}")
        else:
            logger.error(f"❌ [Action - NewFriend] 校验失败，{sender_name} 的申请状态未流转为: {expected_status}")
        return res
