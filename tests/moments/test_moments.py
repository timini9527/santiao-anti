import allure
import pytest
import pytest_check as check
from pages.main.main_page import MainPage
from pages.message.MomentsPage import MomentsPage
from core.logger_utils import logger


@allure.epic("IM核心功能测试")
@allure.feature("朋友圈模块-发布与互动")
@allure.story("测试发布纯文字朋友圈的功能")
class TestMoments:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        初始化页面对象并确保测试结束后返回主页
        """
        self.mainPage = MainPage(driver_sender)
        self.momentsPage = MomentsPage(driver_sender)

        # 统一进入朋友圈页面
        with allure.step("前置步骤：进入朋友圈页面"):
            self.mainPage.go_to_moments_page()

        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    @allure.story("发布纯文字朋友圈")
    @pytest.mark.parametrize("content", ["Hello Moments! 这是一个自动化测试动态。", "测试 Emoji 🌟🔥🚀"])
    def test_post_text_moment(self, content):
        """测试发布纯文字朋友圈的功能"""
        allure.dynamic.title(f"发布纯文字朋友圈 - 内容: {content[:10]}...")

        with allure.step(f"1. 发布动态: {content}"):
            self.momentsPage.post_text_moment(content)

        with allure.step("2. 校验动态是否在列表首位显示"):
            actual_content = self.momentsPage.get_first_moment_content()
            check.equal(actual_content, content, "朋友圈发布内容不匹配！")

    @allure.story("朋友圈点赞测试")
    def test_like_moment(self):
        """测试对朋友圈动态进行点赞"""
        allure.dynamic.title("朋友圈点赞测试")

        with allure.step("1. 为第一条动态点赞"):
            self.momentsPage.like_first_moment()
            # 这里可以进一步校验点赞状态，比如图标变色或点赞数增加
            # 由于缺乏具体定位器，暂做动作演示

    @allure.story("朋友圈评论测试")
    def test_comment_moment(self):
        """测试对朋友圈动态进行评论"""
        allure.dynamic.title("朋友圈评论测试")
        comment_text = "自动化评论测试"

        with allure.step(f"1. 为第一条动态发表评论: {comment_text}"):
            self.momentsPage.comment_on_first_moment(comment_text)
            # 这里可以校验评论是否出现在评论列表中
