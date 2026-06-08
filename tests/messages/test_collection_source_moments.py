import allure
import pytest

from pages.message.MomentsPage import MomentsPage


@pytest.mark.usefixtures('message_page')
@allure.epic("IM核心功能测试")
@allure.feature("朋友圈模块-发布与互动")
@allure.story("朋友圈页面收藏文本消息")
class TestCollectionSourceMoments:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试类开始前，自动获取 self.collPage 实例并绑定到 self
        这样下面的方法就不需要反复传参了
        """
        self.momentsPage = MomentsPage(driver_sender)

    @allure.story("朋友圈页面收藏文本消息")
    def test_collection_friend_text(self):
        pass

    @allure.story("朋友圈页面收藏图片消息")
    def test_collection_friend_image(self):
        pass

    @allure.story("收藏中当前页面分享第一条文本消息")
    def test_share_first_text(self):
        pass

    @allure.story("收藏中当前页面随机分享一条文本消息")
    def test_share_random_text(self):
        pass

    @allure.story("收藏中当前页面分享第一张图片消息")
    def test_share_first_image(self):
        pass

    @allure.story("收藏中当前页面随机分享一张图片消息")
    def test_share_random_image(self):
        pass

    @allure.story("收藏中分享最后一条文本消息")
    def test_share_last_text(self):
        pass

    @allure.story("收藏中分享最后一张图片消息")
    def test_share_last_image(self):
        pass






