import time
from common.base_page import BasePage
from core.logger_utils import logger
from locators.chat.moments.moments_locator import MomentsLocator


class MomentsPage(BasePage):

    def click_post_moments(self):
        """点击发布朋友圈按钮"""
        self.click(MomentsLocator.POST_MOMENTS_BUTTON)
        logger.info("🚀 [Action] 点击发布朋友圈按钮")

    def input_moments_content(self, text: str):
        """输入朋友圈文字内容"""
        self.send_keys(MomentsLocator.EDIT_TEXT, text)
        logger.info(f"🚀 [Action] 输入朋友圈内容: {text}")

    def click_publish(self):
        """点击发表"""
        self.click(MomentsLocator.PUBLISH_BUTTON)
        logger.info("🚀 [Action] 点击发表按钮")
        time.sleep(1) # 等待上传和刷新

    def post_text_moment(self, text: str):
        """快速发布一条纯文字动态"""
        self.click_post_moments()
        self.input_moments_content(text)
        self.click_publish()

    def get_first_moment_content(self) -> str:
        """获取朋友圈第一条动态的正文内容"""
        content = self.get_attribute(MomentsLocator.MOMENT_CONTENT_TEXT, 'text')
        logger.info(f"🔍 [Check] 朋友圈第一条内容: {content}")
        return content

    def like_first_moment(self):
        """为第一条动态点赞"""
        self.click(MomentsLocator.LIKE_BUTTON)
        logger.info("🚀 [Action] 为第一条动态点赞")

    def comment_on_first_moment(self, comment_text: str):
        """为第一条动态发表评论"""
        self.click(MomentsLocator.COMMENT_BUTTON)
        self.send_keys(MomentsLocator.COMMENT_INPUT, comment_text)
        self.click(MomentsLocator.COMMENT_SEND)
        logger.info(f"🚀 [Action] 发表评论: {comment_text}")