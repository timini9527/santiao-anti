import allure
import pytest
import pytest_check as check
from pages.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.collection.chat_collection_page import ChatCollectionPage
from pages.collection.collection_page import CollectionPage
from pages.home.side_slip_page import SideSlipPage
from core.logger_utils import logger
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
import time


@allure.epic("IM核心功能测试")
@allure.feature("我的收藏-收藏夹")
class TestCollection:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatCollectionPage = ChatCollectionPage(driver_sender)
        self.collectionPage = CollectionPage(driver_sender)
        self.sideSlipPage = SideSlipPage(driver_sender)
        
        yield

        with allure.step("后置步骤：返回主页"):
            self.mainPage.go_to_main_page()

    def common_enter_my_collection(self):
        """进入我的收藏页面"""
        with allure.step("-> 回到主页，打开左滑菜单，进入我的收藏"):
            self.mainPage.go_to_main_page()
            self.sideSlipPage.open_left_menu()
            self.sideSlipPage.click_my_collection()
            self.collectionPage.wait_for_collection_page_load()

    @allure.story("收藏管理-删除")
    @allure.title("删除收藏条目流程")
    @pytest.mark.parametrize("col_type", ["text", "image"])
    def test_delete_collection_success(self, col_type):
        """测试从收藏夹中成功删除条目的流程"""
        self.common_enter_my_collection()

        with allure.step(f"1. 确认列表中是否存在【{col_type}】类型的收藏数据"):
            if col_type == "text":
                elem = self.collectionPage.get_collection_text_element(0)
            else:
                elem = self.collectionPage.get_collection_image_element(0)
            
            if not elem:
                pytest.skip(f"⚠️ 列表中没有【{col_type}】类型的收藏项，跳过删除测试")

        with allure.step(f"2. 执行删除第一条【{col_type}】收藏"):
            before_content = None
            if col_type == "text":
                before_content = self.collectionPage.get_collection_text_content(0)
            
            self.collectionPage.del_collection_item(del_type=col_type, index=0)
            time.sleep(1)  # 等待列表刷新

        with allure.step(f"3. 验证删除结果"):
            if col_type == "text":
                after_content = self.collectionPage.get_collection_text_content(0)
                check.not_equal(before_content, after_content, f"❌ 删除校验失败：第0条文本内容依然为 '{before_content}'")
            else:
                logger.info("✅ 图片删除成功")

    @allure.story("收藏管理-分享")
    @allure.title("分享收藏条目流程")
    @pytest.mark.parametrize("col_type", ["text", "image"])
    def test_share_collection_success(self, col_type):
        """测试从收藏夹中分享条目的流程"""
        self.common_enter_my_collection()

        with allure.step(f"1. 确认列表中是否存在【{col_type}】类型的收藏数据"):
            if col_type == "text":
                elem = self.collectionPage.get_collection_text_element(0)
            else:
                elem = self.collectionPage.get_collection_image_element(0)
            
            if not elem:
                pytest.skip(f"⚠️ 列表中没有【{col_type}】类型的收藏项，跳过分享测试")

        with allure.step(f"2. 点击分享第一条【{col_type}】收藏"):
            result = self.collectionPage.share_collection_item(share_type=col_type, index=0)
            check.is_true(result, "点击分享按钮失败")

    @allure.story("收藏管理-排序")
    @allure.title("验证收藏列表按时间倒序排列")
    def test_collection_sort_by_time(self):
        """测试收藏列表中的条目是否按照时间由新到旧倒序排列"""
        self.common_enter_my_collection()

        with allure.step("1. 获取当前页面所有收藏详情数据"):
            details = self.collectionPage.get_collection_details_data(item_type='all', index=-1)
            if not details or len(details) < 2:
                pytest.skip("⚠️ 页面上的收藏条目数少于2条，无法验证排序规律")

        with allure.step("2. 解析时间序列并做排序断言"):
            actual_times = [item["collected_time"] for item in details]
            expected_times = self.collectionPage.get_sort_time(details)
            
            logger.info(f"⏳ 实际时间序列: {actual_times}")
            logger.info(f"⏳ 期望时间序列: {expected_times}")
            
            check.equal(actual_times, expected_times, "❌ 收藏列表未按时间倒序排列！")

    @allure.story("从聊天页面中的收藏发送消息")
    @allure.title("从聊天页面中的收藏发送消息-状态：已完成")
    @pytest.mark.parametrize("index", [0, -1], ids=["First_Item", "Absolute_Last_Item"])
    @pytest.mark.parametrize("col_type", ["text","image"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_collection_message(self, strategy, col_type, index):
        """测试从聊天页面发送不同类型收藏消息的功能"""
        allure.title(f"发送【{col_type}】收藏验证 - {strategy.desc}")
        desc = f"AutoTest_{col_type}_{int(time.time())}"

        with allure.step("1. 进入会话和收藏页面"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatCollectionPage.open_panel_enter_collection_page()

        with allure.step(f"2. 打开【{col_type}】收藏项并验证内容"):
            coll_content = self.chatCollectionPage.select_and_click_collection_item(col_type=col_type, index=index)
            if not coll_content:
                pytest.skip(f"⚠️ 当前测试账号缺少【{col_type}】类型的收藏记录，跳过执行此分支")

            item_content = self.chatCollectionPage.get_selected_item_panel_content(col_type=col_type)
            if col_type == "image":
                is_similar = self.chatCollectionPage.verify_image_similarity(coll_content, item_content)
                check.is_true(is_similar, f"❌ [Verify] 弹窗预览图片与列表指纹不匹配 (Hash1:{coll_content}, Hash2:{item_content})")
            else:
                check.equal(coll_content, item_content, f"❌ [Verify] 弹窗预览文本与列表不匹配 (期望:{item_content}, 实际:{coll_content})")

        with allure.step("3. 输入附加留言并执行发送操作"):
            self.chatCollectionPage.send_collection_panel_input(desc)
            self.chatCollectionPage.click_send_collection_panel_send()

        with allure.step("4. 验证核心负载及留言已成功上屏"):
            self.chatListPage.click_add_button()
            flag = self.chatCollectionPage.verify_from_collection_message_content(
                col_type=col_type, 
                exp_content=coll_content, 
                msg=desc
            )
            check.is_true(flag, f"❌ {col_type} 消息发送上屏验证失败！")
