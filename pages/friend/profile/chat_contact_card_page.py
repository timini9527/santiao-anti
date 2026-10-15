import allure
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement
from pages.chat.core.chat_page import ChatPage
from core.logger_utils import logger, LogIcon
from locators.friend.profile.chat_contact_card_locator import ChatContactCardLocator
from locators.common.contact_select_locator import ContactSelectLocator

class ChatContactCardPage(ChatPage):


    # 打开加号面板并点击名片按钮
    def open_panel_enter_contact_card_page(self) -> None:
        """打开加号面板并点击名片按钮"""
        logger.info(f"{LogIcon.ACTION} 准备进入联系人选择页面")
        self.click_add_button()
        self.click(ChatContactCardLocator.CONTACT_CARD_ROOT)
        time.sleep(2)


    # 等待群聊名片页面加载
    def wait_for_group_chat_card_page_load(self, timeout: int = 10) -> bool:
        """
        等待群聊名片页加载完成
        Args:
            timeout: 超时时间
        Returns:
            bool: True 表示加载成功，False 表示超时
        """
        logger.info(f"{LogIcon.WAIT} 等待群聊名片页加载完成，超时时间 {timeout} 秒")
        try:
            self.find_element(ChatContactCardLocator.GROUP_CARD_NAME, timeout=timeout)
            logger.info(f"{LogIcon.SUCCESS} 群聊名片页加载完成")
            return True
        except Exception:
            logger.error(f"{LogIcon.FAIL} 群聊名片页加载超时")
            return False


    # 获取群头像
    def get_group_avatar(self) -> WebElement | None:
        """获取群头像"""
        logger.info(f"{LogIcon.FIND} 🏷️ [Action] 群聊名片页 - 获取群头像")
        elem = self.find_element(ChatContactCardLocator.GROUP_CARD_AVATAR, timeout=2)
        return elem

    # 获取群名称
    def get_group_name(self) -> str:
        """获取群名称"""
        logger.info(f"{LogIcon.FIND} 🏷️ [Action] 群聊名片页 - 获取群名称")
        name = self.get_attribute(ChatContactCardLocator.GROUP_CARD_NAME, "text")
        logger.info(f"{LogIcon.FIND} 🏷️ [Action] 群聊名片页 - 获取群名称结果: {name}")
        return name or ""

    # 获取群成员数量
    def get_group_member_count(self) -> int:
        """获取群成员数量"""
        import re
        logger.info(f"{LogIcon.FIND} 🏷️ [Action] 群聊名片页 - 获取群成员数量")
        text = self.get_attribute(ChatContactCardLocator.GROUP_CARD_MEMBER_COUNT, "text")
        match = re.search(r"(\d+)", text or "")  # 正则匹配数字
        if match:
            count = int(match.group(1))
            logger.info(f"{LogIcon.FIND} 🏷️ [Action] 群聊名片页 - 获取群成员数量结果: {count}")
            return count
        else:
            logger.error(f"{LogIcon.FAIL} 群聊名片页 - 未能获取群成员数量，文本: {text}")
            return 0

    # 获取加入群聊状态
    def get_join_group_status(self) -> str:
        """获取加入群聊状态"""
        logger.info(f"{LogIcon.FIND} 🏷️ [Action] 群聊名片页 - 获取加入群聊状态")
        status = self.get_attribute(ChatContactCardLocator.JOIN_GROUP_STATUS_TEXT, "text")
        logger.info(f"{LogIcon.FIND} 🏷️ [Action] 群聊名片页 - 获取加入群聊状态结果: {status}")
        return status or ""

    # 点击加入群聊或发送消息按钮
    def click_join_or_send_message_button(self) -> None:
        """点击加入群聊或发送消息按钮"""
        logger.info(f"{LogIcon.ACTION} 🏷️ [Action] 群聊名片页 - 点击加入群聊或发送消息按钮")
        if self.wait_for_group_chat_card_page_load():
            self.click(ChatContactCardLocator.JOIN_GROUP_BTN, force_wait=True)
            return
        logger.warning(f"{LogIcon.FAIL} 群聊名片页加载超时，无法点击")