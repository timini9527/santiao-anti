import allure
import pytest
from pages.main.main_page import MainPage
from pages.collection.collection_page import CollectionPage
from core.logger_utils import logger


@pytest.mark.usefixtures('message_page')
@allure.epic("IM核心功能测试")
@allure.feature("我的收藏-朋友圈收藏")
class TestCollection:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试类开始前，自动获取 self.collPage 实例并绑定到 self
        """
        self.collPage = CollectionPage(driver_sender)
        self.mainPage = MainPage(driver_sender)

    @allure.step("进入我的收藏页面")
    def common_enter_my_collection(self):
        """ 进入我的收藏页面 """
        with allure.step("进入我的收藏页面"):
            self.collPage.back_to_main()
            self.collPage.enter_my_collection()

    @allure.story("朋友圈页面收藏文本消息")
    def test_collection_friend_text(self):
        # TODO: 待后续开发朋友圈文本收藏自动化测试步骤
        pass

    @allure.story("朋友圈页面收藏图片消息")
    def test_collection_friend_image(self):
        # TODO: 待后续开发朋友圈图片收藏自动化测试步骤
        pass
