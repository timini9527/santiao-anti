import time
from common.base_page import BasePage
from locators.friend.add_friend.new_friend_locator import NewFriendLocator
from core.logger_utils import logger, LogIcon
from appium.webdriver.webelement import WebElement


class NewFriendPage(BasePage):
    """新的朋友申请列表页面对象 (对应 0.4 添加好友模块 新朋友申请处理)"""

    # 等待页面加载完成
    def wait_for_new_friend_page_load(self, timeout: int = 10, raise_exception: bool = True) -> bool:
        """ 等待新的朋友页面加载完成 """
        logger.info(f"{LogIcon.WAIT} 等待新的朋友页面加载 (超时: {timeout}s)")
        is_exit = self.wait_for_element_text(NewFriendLocator.TV_TITLE, expected_text="新的朋友", timeout=timeout, raise_exception=raise_exception)
        if is_exit:
            logger.info(f"{LogIcon.WAIT} 新的朋友页面加载完成")
        else:
            logger.error(f"{LogIcon.FAIL} 新的朋友页面加载超时")
        return is_exit

    # 新朋友申请列表 - 点击返回
    def click_iv_back(self) -> None:
        """ 新朋友申请列表 - 点击返回按钮 """
        logger.info(f"{LogIcon.ACTION} 新的朋友页 - 点击返回")
        self.click(NewFriendLocator.IV_BACK)

    # 新朋友申请列表 - 点击清空
    def click_fb_delete(self) -> None:
        """ 新朋友申请列表 - 点击右上角清空（垃圾桶）按钮 """
        logger.info(f"{LogIcon.SETUP} 新的朋友页 - 点击右上角清空")
        self.click(NewFriendLocator.FB_DELETE)
        
    # 新朋友申请列表 - 点击确认
    def click_confirm_btn(self) -> None:
        """ 新朋友申请列表 - 点击确认清空按钮 """
        logger.info(f"{LogIcon.SUCCESS} 新的朋友页 - 点击确认清空")
        self.click(NewFriendLocator.CONFIRM_BTN)
    
    # 新朋友申请列表 - 点击取消
    def click_cancel_btn(self) -> None:
        """ 新朋友申请列表 - 点击取消按钮 """
        logger.info(f"{LogIcon.FAIL} 新的朋友页 - 点击取消清空")
        self.click(NewFriendLocator.CANCEL_BTN)

    # 新朋友申请列表 - 点击顶部添加朋友入口
    def click_search_entry(self) -> None:
        """ 新朋友申请列表 - 点击顶部搜索区域，进入添加朋友页面 """
        logger.info(f"{LogIcon.FIND} 新的朋友页 - 点击添加朋友搜索入口")
        self.click(NewFriendLocator.FB_SEARCH)

    # 新朋友申请列表 - 输入搜索内容(也是添加好友入口)
    def send_keys_search(self, search_key: str) -> None:
        """ 新朋友申请列表 - 在页面顶部的搜索框中输入内容(也是添加好友入口) """
        logger.info(f"{LogIcon.FIND} 输入搜索内容(也是添加好友入口): {search_key}")
        self.send_keys(NewFriendLocator.ET_SEARCH, search_key)


    # 申请列表 - 获取申请列表的Item
    def get_apply_list_item(self, timeout: int = 2, raise_exception: bool = False) -> list[WebElement]:
        """ 申请列表 - 获取申请列表的Item """
        logger.info(f"{LogIcon.FIND} 获取申请列表的Item (超时: {timeout}s)")
        items = self.find_elements(NewFriendLocator.CL_ITEM, timeout=timeout, raise_exception=raise_exception)
        if not items:
            logger.warning(f"{LogIcon.WARN} 未找到申请列表的Item，请确认是否有新的好友申请，或者是否在列表页面")
            return []
        logger.info(f"{LogIcon.SUCCESS} 获取到 {len(items)} 个申请列表的Item")
        return items

    # 申请列表 - 获取当前可见申请人的昵称文本
    def get_apply_item_texts(self, timeout: int = 2) -> list[str]:
        """ 申请列表 - 获取当前可见申请人的昵称文本 """
        logger.info(f"{LogIcon.FIND} 获取当前可见申请人的昵称文本 (超时: {timeout}s)")
        elements = self.find_elements(NewFriendLocator.TV_NAME_XPATH, timeout=timeout, raise_exception=False)
        if not elements:
            logger.warning(f"{LogIcon.WARN} 未找到申请列表的Item")
            return []
        texts = [element.get_attribute("text").strip() for element in elements]
        logger.info(f"{LogIcon.FIND} 获取到 {len(texts)} 条申请人昵称")
        return texts
    
    # 申请列表 - 获取Item，通过index=0
    def get_apply_item_by_index(self, index: int = 0) -> WebElement | None:
        """ 申请列表 - 获取指定索引的Item """
        logger.info(f"{LogIcon.FIND} 获取指定索引的Item: {index}")
        items = self.get_apply_list_item()
        if index < 0 or index >= len(items):
            logger.warning(f"{LogIcon.WARN} 索引越界，索引: {index}，列表长度: {len(items)}")
            return None
        logger.info(f"{LogIcon.SUCCESS} 获取到第 {index + 1} 个申请列表的Item")
        return items[index]
    
    # 申请列表 - 获取Item，通过 nickname
    def get_apply_item_by_nickname(self, nickname: str) -> WebElement | None:
        """ 申请列表 - 获取指定昵称的Item """
        logger.info(f"{LogIcon.FIND} 通过昵称获取Item: {nickname}")
        items = self.get_apply_list_item()
        for item in items:
            if nickname in item.get_attribute("text"):
                logger.info(f"{LogIcon.SUCCESS} 获取到 {nickname} 的申请列表的Item")
                return item
        logger.warning(f"{LogIcon.WARN} 未找到 {nickname} 的申请列表的Item")
        return None
    
    # 申请列表 - 获取Item，通过nickname
    def get_apply_item_by_name(self, nickname: str, timeout: int = 8, raise_exception: bool = True) -> WebElement | None:
        """ 申请列表 - 获取指定昵称的Item """
        logger.info(f"{LogIcon.FIND} 定位申请Item: {nickname}")
        locator = NewFriendLocator.get_apply_item_by_name(nickname)
        item = self.find_element(locator, timeout=timeout, raise_exception=raise_exception)
        if item:
            logger.info(f"{LogIcon.SUCCESS} 获取到 {nickname} 的申请列表的Item")
        else:
            logger.warning(f"{LogIcon.WARN} 未找到 {nickname} 的申请列表的Item")
        return item
    
    # 申请列表 - 点击同意按钮，通过nickname
    def click_accept_btn_by_name(self, nickname: str, timeout: int = 8) -> bool:
        """ 申请列表 - 点击指定昵称好友的“接受/同意”按钮 """
        logger.info(f"{LogIcon.SETUP} 点击 {nickname} 右侧的接受按钮")
        locator = NewFriendLocator.get_accept_btn_by_name(nickname)
        try:
            self.click(locator, timeout=timeout)
            logger.info(f"{LogIcon.SUCCESS} 点击了 {nickname} 右侧的接受按钮")
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 点击 {nickname} 右侧的接受按钮失败: {e}")
            return False

    # 申请列表 - 点击指定好友申请条目
    def click_apply_item_by_name(self, sender_name: str) -> bool:
        """ 申请列表 - 点击指定好友昵称的申请条目整行，以进入验证详情页进行深度处理（如修改备注） """
        logger.info(f"{LogIcon.SETUP} 点击 {sender_name} 的申请条目行，准备进入验证详情页")
        locator = NewFriendLocator.get_apply_item_by_name(sender_name)
        try:
            self.click(locator, timeout=5)
            logger.info(f"{LogIcon.SUCCESS} 点击了 {sender_name} 的申请条目行，已进入验证详情页")
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 点击 {sender_name} 的申请条目行失败: {e}")
            return False
    
    # 申请列表 - 直接在列表中点击接受好友申请
    def accept_apply_by_name(self, sender_name: str) -> bool:
        """ 申请列表 - 在列表中，直接点击指定好友昵称右侧的“接受/同意”按钮 """
        logger.info(f"{LogIcon.SETUP} 准备在列表中点击 {sender_name} 右侧的接受按钮")
        locator = NewFriendLocator.get_accept_btn_by_name(sender_name)
        try:
            self.click(locator, timeout=5)
            logger.info(f"{LogIcon.SUCCESS} 点击了 {sender_name} 右侧的接受按钮")
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 未找到 {sender_name} 右侧的接受按钮: {e}")
            return False
    
    # 申请列表 - 点击删除按钮
    def click_delete_btn(self) -> None:
        """ 申请列表 - 点击删除按钮 """
        logger.info(f"{LogIcon.SETUP} 点击删除按钮")
        self.click(NewFriendLocator.LL_SWIPE_DELETE, force_wait=True)
    
    # 申请列表 - 滑动并删除申请记录
    def swipe_and_delete_by_name(self, nickname: str) -> bool:
        """ 申请列表 - 滑动并删除指定昵称好友的申请记录 """
        logger.info(f"{LogIcon.SETUP} 准备滑动并删除 {nickname} 的申请记录")
        item = self.get_apply_item_by_name(nickname)
        if item:
            self.swipe_page_quickly(element=item, slid_type="left", duration=200)
            logger.info(f"{LogIcon.SUCCESS} 滑动了 {nickname} 的申请记录")
            self.click_delete_btn()
            return True
        else:
            logger.warning(f"{LogIcon.WARN} 未找到 {nickname} 的申请列表的Item")
            return False

    # 申请详情页 - 点击接受/同意按钮
    def click_accept_in_detail(self, timeout: int = 2) -> bool:
        """ 申请详情页 - 点击【接受/同意】按钮 """
        logger.info(f"{LogIcon.SETUP} 申请详情页 - 准备点击【接受/同意】按钮")
        try:
            if not self.is_element_exist(NewFriendLocator.APPLY_ADD_FRIEND_BTN, timeout=timeout):
                logger.warning(f"{LogIcon.WARN} 申请详情页 - 未找到【接受/同意】按钮")
                return False
            self.click(NewFriendLocator.APPLY_ADD_FRIEND_BTN, force_wait=True, timeout=timeout)
            logger.info(f"{LogIcon.SUCCESS} 申请详情页 - 点击【接受/同意】按钮")
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 申请详情页 - 点击【接受/同意】按钮失败: {e}")
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
        logger.info(f"{LogIcon.FIND} 校验 {sender_name} 的申请状态是否流转为: {expected_status}")
        locator = NewFriendLocator.get_status_text_by_name(sender_name, expected_status)
        res = self.is_element_exist(locator, timeout=timeout)
        if res:
            logger.info(f"{LogIcon.SUCCESS} 校验成功，{sender_name} 的申请状态流转为: {expected_status}")
        else:
            logger.error(f"{LogIcon.FAIL} 校验失败，{sender_name} 的申请状态未流转为: {expected_status}")
        return res
