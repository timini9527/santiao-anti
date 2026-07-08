import pytest
import allure
import pytest_check as check
from pages.system.main.main_page import MainPage
from pages.moments.moments_page import MomentsPage
from core.logger_utils import logger


class BaseSmokeMoments:
    """朋友圈/动态模块测试基类"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.momentsPage = MomentsPage(driver_sender)
        
        with allure.step("前置步骤：进入朋友圈（动态）页面"):
            self.mainPage.go_to_moments_page()
            
        yield
        
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 异常，未能返回首页: {e}")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-朋友圈与动态")
class TestSmokeMoments(BaseSmokeMoments):
    """朋友圈/动态模块冒烟用例集"""

    @allure.story("动态发布与验证")
    @allure.title("发布纯文本动态并在列表首位成功展示")
    def test_smoke_post_text_moment(self):
        test_content = "冒烟测试：这是一条自动发布的纯文字朋友圈动态。"

        with allure.step(f"1. 发送纯文本朋友圈: {test_content}"):
            self.momentsPage.post_text_moment(test_content)

        with allure.step("2. 校验朋友圈列表第一条内容是否匹配"):
            actual_content = self.momentsPage.get_first_moment_content()
            check.equal(actual_content, test_content, "❌ 发布的朋友圈文本内容与首条展示内容不符")

    @allure.story("动态点赞与评论")
    @allure.title("对朋友圈动态进行点赞与评论操作")
    def test_smoke_like_and_comment_moment(self):
        comment_text = "冒烟测试：自动化点赞与评论测试"

        with allure.step("1. 对朋友圈列表第一条进行点赞"):
            self.momentsPage.like_first_moment()

        with allure.step(f"2. 对朋友圈列表第一条进行评论: {comment_text}"):
            self.momentsPage.comment_on_first_moment(comment_text)
