import time
from core.logger_utils import logger, LogIcon
from locators.groups.setting.notice.group_notice_locator import GroupNoticeLocator
from pages.groups.setting.general.group_setting_page import GroupSettingPage

class GroupNoticePage(GroupSettingPage):
    """群公告子页面操作类"""


    # 等待群公告页面加载
    def wait_for_notice_page_load(self, timeout: int = 10) -> bool:
        """群公告 - 等待群公告页面加载"""
        logger.info(f"{LogIcon.WAIT} GroupNoticePage - 等待群公告页面加载")
        res = self.wait_for_element_text(GroupNoticeLocator.TITLE, expected_text="群公告", timeout=timeout)
        logger.info(f"{LogIcon.SUCCESS} GroupNoticePage - 页面加载{'成功' if res else '超时'}")
        return res

    # 输入群公告内容
    def input_notice_content(self, text: str) -> None:
        """群公告 - 输入群公告内容"""
        logger.info(f"{LogIcon.ACTION} GroupNoticePage - 输入群公告内容: '{text}'")
        self.send_keys(GroupNoticeLocator.NOTICE_CONTENT_INPUT, text)

    # 点击发布按钮
    def click_publish_btn(self) -> None:
        """群公告 - 点击发布按钮"""
        logger.info(f"{LogIcon.SETUP} GroupNoticePage - 点击【发布/完成】")
        self.click(GroupNoticeLocator.PUBLISH_BTN)
        time.sleep(0.5)

    # 获取当前展示的群公告内容
    def get_notice_content(self) -> str | None:
        """群公告 - 获取当前展示的群公告内容"""
        logger.info(f"{LogIcon.FIND} 📖 [Action] GroupNoticePage - 获取群公告内容")
        res = self.get_attribute(GroupNoticeLocator.NOTICE_CONTENT_DISPLAY, "text", timeout=2, raise_exception=False)
        return res

    # 点击返回
    def click_back_button(self) -> None:
        """群公告 - 点击返回"""
        logger.info(f"{LogIcon.ACTION} GroupNoticePage - 点击返回")
        self.click(GroupNoticeLocator.BACK_BTN)
