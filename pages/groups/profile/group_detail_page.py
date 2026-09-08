import time
import re
from typing import List, Optional
from selenium.webdriver.remote.webelement import WebElement
from common.base_page import BasePage
from locators.groups.profile.group_detail_locator import GroupDetailLocator
from core.logger_utils import logger


class GroupDetailPage(BasePage):
    """群资料页面对象 (严格对接真实 Android XML 节点树)"""

    def wait_for_group_detail_page_load(self, timeout: int = 8) -> bool:
        """
        等待群资料页面加载完成
        :param timeout: 超时时间（秒）
        :return: 是否成功加载
        """
        res = self.is_element_exist(GroupDetailLocator.TV_TITLE, timeout=timeout)
        logger.info(f"⏳ [Wait - GroupDetail] 群资料页加载 {'成功' if res else '超时'} in {timeout}s")
        return res

    def get_group_name(self) -> str:
        """获取群资料页显示的群名称"""
        name = self.get_attribute(GroupDetailLocator.GROUP_NAME, 'text')
        logger.info(f"📋 [Action - GroupDetail] 获取群名称: {name}")
        return name or ""

    def get_group_id(self) -> str:
        """获取群 ID 文本 (提取纯数字)"""
        text = self.get_attribute(GroupDetailLocator.GROUP_ID_TEXT, 'text')
        match = re.search(r"\d+", text or "")
        group_id = match.group(0) if match else (text or "")
        logger.info(f"📋 [Action - GroupDetail] 获取群ID: {group_id}")
        return group_id

    def click_copy_group_id(self):
        """点击复制群 ID 图标"""
        self.click(GroupDetailLocator.GROUP_ID_COPY, force_wait=True)
        logger.info("📋 [Action - GroupDetail] 点击复制群ID")

    def get_group_tags(self) -> List[str]:
        """获取群资料页展示的所有群标签列表"""
        elements = self.find_elements(GroupDetailLocator.GROUP_TAG_ITEMS, timeout=2, expect_missing=True)
        tags = [el.text for el in elements if el.text]
        logger.info(f"🏷️ [Action - GroupDetail] 获取群标签列表: {tags}")
        return tags

    def click_send_message_or_join(self, force_wait: bool = True):
        """点击底部操作大按钮 (发送消息 / 加入群聊)"""
        self.click(GroupDetailLocator.GROUP_ADD, force_wait=force_wait)
        logger.info("🚀 [Action - GroupDetail] 点击底部【发送消息/加入群聊】按钮")

    def click_back(self):
        """点击顶部返回按钮退出群资料页"""
        self.click(GroupDetailLocator.IV_BACK, force_wait=True)
        logger.info("🔙 [Action - GroupDetail] 点击顶部返回按钮")

    def verify_is_on_group_detail_page(self, expected_group_name: Optional[str] = None) -> bool:
        """
        综合校验当前是否位于群资料页，并校验群名称是否匹配
        :param expected_group_name: 期望的群名称
        :return: 校验是否通过
        """
        if not self.wait_for_group_detail_page_load():
            logger.error("❌ [Verify - GroupDetail] 当前未处于群资料页面")
            return False
        if expected_group_name:
            actual_name = self.get_group_name()
            if expected_group_name not in actual_name:
                logger.error(f"❌ [Verify - GroupDetail] 群名称不匹配! 预期包含: {expected_group_name}, 实际: {actual_name}")
                return False
        logger.info(f"✅ [Verify - GroupDetail] 成功验证处于群资料详情页: {expected_group_name or ''}")
        return True
