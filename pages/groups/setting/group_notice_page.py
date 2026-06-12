from common.base_page import BasePage
from core.logger_utils import logger
from locators.groups.setting.group_notice_locator import GroupNoticeLocator

class GroupNoticePage(BasePage):
    """群公告子页面操作类"""

    def wait_for_notice_page_load(self, timeout=10) -> bool:
        """等待群公告页面加载"""
        res = self.get_attribute(GroupNoticeLocator.TITLE, "text") == "群公告"
        logger.info(f"⏳ [Action] GroupNoticePage - 页面加载{'成功' if res else '超时'}")
        return res

    def input_notice_content(self, text: str):
        """输入群公告内容"""
        self.send_keys(GroupNoticeLocator.NOTICE_CONTENT_INPUT, text)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass
        logger.info(f"✍️ [Action] GroupNoticePage - 输入群公告内容: '{text}'")

    def click_publish_btn(self):
        """点击发布按钮"""
        self.click(GroupNoticeLocator.PUBLISH_BTN)
        logger.info("⚙️ [Action] GroupNoticePage - 点击【发布/完成】")

    def click_confirm(self):
        """确认发布/弹窗确认"""
        self.click(GroupNoticeLocator.CONFIRM_BTN)
        logger.info("✅ [Action] GroupNoticePage - 弹窗确认")

    def click_cancel(self):
        """取消发布/弹窗取消"""
        self.click(GroupNoticeLocator.CANCEL_BTN)
        logger.info("❌ [Action] GroupNoticePage - 弹窗取消")

    def get_notice_content(self) -> str:
        """获取当前展示的群公告内容"""
        res = self.get_attribute(GroupNoticeLocator.NOTICE_DISPLAY_TEXT, "text")
        logger.info(f"📖 [Action] GroupNoticePage - 获取群公告内容: '{res}'")
        return res

    def click_back_button(self):
        """点击返回"""
        self.click(GroupNoticeLocator.BACK_BTN)
        logger.info("🔙 [Action] GroupNoticePage - 点击返回")
