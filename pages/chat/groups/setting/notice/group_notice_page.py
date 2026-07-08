import time
from core.logger_utils import logger
from locators.chat.groups.setting.notice.group_notice_locator import GroupNoticeLocator
from pages.chat.groups.setting.general.group_setting_page import GroupSettingPage

class GroupNoticePage(GroupSettingPage):
    """群公告子页面操作类"""


    def wait_for_notice_page_load(self, timeout=10) -> bool:
        """群公告 - 等待群公告页面加载"""
        res = self.get_attribute(GroupNoticeLocator.TITLE, "text") == "群公告"
        logger.info(f"⏳ [Action] GroupNoticePage - 页面加载{'成功' if res else '超时'}")
        return res

    def input_notice_content(self, text: str):
        """群公告 - 输入群公告内容"""
        self.send_keys(GroupNoticeLocator.NOTICE_CONTENT_INPUT, text)
        logger.info(f"✍️ [Action] GroupNoticePage - 输入群公告内容: '{text}'")

    def click_publish_btn(self):
        """群公告 - 点击发布按钮"""
        self.click(GroupNoticeLocator.PUBLISH_BTN)
        logger.info("⚙️ [Action] GroupNoticePage - 点击【发布/完成】")
        time.sleep(0.5)

    def get_notice_content(self) -> str:
        """群公告 - 获取当前展示的群公告内容"""
        res = self.get_attribute(GroupNoticeLocator.NOTICE_CONTENT_DISPLAY, "text", timeout=2, raise_exception=False)
        logger.info(f"📖 [Action] GroupNoticePage - 获取群公告内容: '{res}'")
        return res

    def click_back_button(self):
        """群公告 - 点击返回"""
        self.click(GroupNoticeLocator.BACK_BTN)
        logger.info("🔙 [Action] GroupNoticePage - 点击返回")
