import allure
import pytest
import pytest_check as check
from pages.main.main_page import MainPage
from pages.chat.chat_list_page import ChatListPage
from pages.collection.collection_page import CollectionPage
from core.logger_utils import logger
from pages.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
import time


@allure.epic("IM核心功能测试")
@allure.feature("我的模块-收藏夹")
@allure.story("初始化页面对象")
class TestCollection:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.collectionPage = CollectionPage(driver_sender)
        
        yield

        with allure.step("后置步骤：返回主页"):
            self.mainPage.go_to_main_page()


    @allure.story("收藏管理-删除")
    @pytest.mark.skip(reason="从聊天页面发送收藏功能待完善")
    @allure.title("删除收藏条目流程")
    def test_delete_collection_success(self):
        """测试从收藏夹中成功删除条目的流程"""
        pass


    @allure.story("从聊天页面中的收藏发送消息")
    @pytest.mark.parametrize("index", [0, -1], ids=["First_Item", "Absolute_Last_Item"])
    @pytest.mark.parametrize("col_type", ["text","image"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_collection_message(self, strategy, col_type, index):
        """测试从聊天页面发送不同类型收藏消息的功能"""
        allure.title(f"发送【{col_type}】收藏验证 - {strategy.desc}")
        desc = f"AutoTest_{col_type}_{int(time.time())}"

        with allure.step("1. 进入会话和收藏页面"):
            self.chatListPage.enter_chat(strategy.name)
            self.collectionPage.open_panel_enter_collection_page()

        with allure.step(f"2. 打开【{col_type}】收藏项并验证内容"):
            coll_content = self.collectionPage.select_and_click_collection_item(col_type=col_type, index=index)
            if not coll_content:
                pytest.skip(f"⚠️ 当前测试账号缺少【{col_type}】类型的收藏记录，跳过执行此分支")

            item_content = self.collectionPage.get_selected_item_panel_content(col_type=col_type)
            if col_type == "image":
                is_similar = self.collectionPage.verify_image_similarity(coll_content, item_content)
                check.is_true(is_similar, f"❌ [Verify] 弹窗预览图片与列表指纹不匹配 (Hash1:{coll_content}, Hash2:{item_content})")
            else:
                check.equal(coll_content, item_content, f"❌ [Verify] 弹窗预览文本与列表不匹配 (期望:{item_content}, 实际:{coll_content})")

        with allure.step("3. 输入附加留言并执行发送操作"):
            self.collectionPage.send_collection_panel_input(desc)
            self.collectionPage.click_send_collection_panel_send()

        with allure.step("4. 验证核心负载及留言已成功上屏"):
            self.chatListPage.click_add_button()
            flag = self.collectionPage.verify_from_collection_message_content(
                col_type=col_type, 
                exp_content=coll_content, 
                msg=desc
            )
            check.is_true(flag, f"❌ {col_type} 消息发送上屏验证失败！")
    

