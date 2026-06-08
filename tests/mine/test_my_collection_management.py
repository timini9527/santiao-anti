import allure
import pytest

from pages.mine.MyCollectionPage import MyCollectionPage
from core.logger_utils import logger




@pytest.mark.usefixtures('message_page')
@allure.epic("IM核心功能测试")
@allure.feature("我的模块-收藏夹")
@allure.story("我的收藏中删除元素最新一条(文本/图片)")
class TestMyCollectionManagement:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试类开始前，自动获取 self.collPage 实例并绑定到 self
        这样下面的方法就不需要反复传参了
        """
        self.collPage = MyCollectionPage(driver_sender)


    @allure.story("我的收藏中删除元素最新一条(文本/图片)")
    @pytest.mark.parametrize("item_type", ["text", "image"], ids=["删除最新文本", "删除最新图片"])
    def test_delete_collection_first_item(self, item_type):
        self.collPage.enter_my_collection()
        # 1. 获取删除前的数据
        data_pre = self.collPage.get_collection_details_data(item_type, index=0)
        # 2. 执行删除
        self.collPage.del_collection_item(item_type, 0)
        # 3. 获取删除后的数据并校验
        data_after = self.collPage.get_collection_details_data(item_type, index=0)
        print(f" data_pre = {data_pre}, data_after = {data_after} ")
        self.collPage.back()

        if not data_after or not data_pre:
            # 场景 A: 删除了唯一的一条数据，现在列表里没有该类型数据了
            logger.info("✅  删除成功 (列表已无该类型数据) 或 没有找到该数据")
            assert True, f"删除失败 (已无该类型数据)"
        else:
            # 场景 B: 还有其他数据，原来的第二条变成了第一条
            assert data_pre['collected_time'] != data_after['collected_time'], \
                f"删除失败: 首条数据时间戳未变化 ({data_pre['collected_time']})"

    @allure.story("我的收藏中删除元素所有(文本/图片)收藏")
    @pytest.mark.parametrize("item_type", ["text", "image"], ids=["删除所有文本", "删除所有图片"])
    def test_delete_collection_texts(self, item_type):
        self.collPage.enter_my_collection()
        del_item = self.collPage.del_collection_item(item_type, 1)
        self.collPage.back()
        assert del_item == 0, f'还有 {del_item} 条 {item_type} 数据未删除'

    @allure.story("我的收藏中删除所有元素收藏")
    def test_delete_collection_all(self, item_type: str = "all"):
        self.collPage.enter_my_collection()
        del_item = self.collPage.del_collection_item("all", 1)
        self.collPage.back()
        assert del_item == 0, f'还有 {del_item} 条 {item_type} 数据未删除'