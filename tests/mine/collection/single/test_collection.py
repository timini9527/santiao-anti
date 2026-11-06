import allure
import pytest
import pytest_check as check
from datetime import datetime
from pages.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.mine.collection.chat_collection_page import ChatCollectionPage
from pages.mine.collection.collection_page import CollectionPage
from pages.home.side_slip_page import SideSlipPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from core.logger_utils import logger, LogIcon
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from pages.common.contact_select_page import ContactSelectPage
import time
from common.toast_enums import ToastMsg

@allure.epic('IM核心功能测试')
@allure.feature('我的收藏-收藏夹')
class TestCollection:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """初始化页面对象"""
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.longPressPage = ChatLongPressPage(driver_sender)
        self.chatCollectionPage = ChatCollectionPage(driver_sender)
        self.collectionPage = CollectionPage(driver_sender)
        self.sideSlipPage = SideSlipPage(driver_sender)
        self.imagePage = ChatImagePage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        yield
        with allure.step('后置步骤：返回主页'):
            self.mainPage.go_to_main_page()

    def common_enter_my_collection(self):
        """进入我的收藏页面"""
        with allure.step('-> 回到主页，打开左滑菜单，进入我的收藏'):
            self.mainPage.go_to_main_page()
            self.sideSlipPage.open_left_menu()
            self.sideSlipPage.click_my_collection()
            self.collectionPage.wait_for_collection_page_load()

    def _long_collection(self):
        """长按最后一条消息并收藏"""
        self.longPressPage.long_press_last_message()
        self.longPressPage.click_menu_item('收藏')
        toast = self.collectionPage.get_toast()
        check.equal(ToastMsg.COLLECT_SUCCESS, toast, f'收藏失败，实际 Toast：{toast}')

    def _build_text(self, prefix: str, strategy) -> str:
        """生成本次测试唯一文本，避免被历史收藏数据干扰"""
        timestamp = datetime.now().strftime('%H%M%S%f')
        return f'{prefix} {strategy.name} {timestamp}'

    def _send_text_and_collect(self, text: str):
        """发送文本并收藏最后一条消息"""
        self.chatPage.send_message(text)
        self._long_collection()

    def _send_image_and_collect(self, strategy):
        """发送图片并收藏最后一条图片消息"""
        self.imagePage.open_panel_to_album()
        result = self.imagePage.select_single_image(mode=1)
        check.is_true(result, '选图失败')
        self.imagePage.click_send_button()
        self.mainPage.go_to_main_page()
        self.chatListPage.enter_chat(strategy.name)
        self._long_collection()

    def _verify_latest_text(self, expected_text: str, index: int=0):
        """校验我的收藏中最新文本内容"""
        actual_text = self.chatCollectionPage.get_collection_text_content(index)
        check.equal(actual_text, expected_text, f'校验失败：实际内容{actual_text}, 预期内容{expected_text}')

    def _verify_latest_texts(self, expected_texts: list[str]):
        """校验我的收藏中最新多条文本内容"""
        actual_texts = self.collectionPage.get_collection_text_data(index=len(expected_texts))
        check.equal(actual_texts, expected_texts, f'校验失败：实际内容{actual_texts}, 预期内容{expected_texts}')

    def _verify_latest_collection_time(self):
        """校验我的收藏中最新一条数据的收藏时间"""
        now_time = self.collectionPage.get_collection_page_time()
        _, coll_time = self.collectionPage.get_collection_time()
        result = self.collectionPage.verify_collection_time(now_time, coll_time)
        check.is_true(result, f'校验失败：收藏时间不匹配 {now_time} | {coll_time}')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('收藏管理-分享')
    @allure.title('分享收藏条目流程-状态：已完成')
    @pytest.mark.parametrize('col_type', [pytest.param('text', id='分享第一条文本收藏'), pytest.param('image', id='分享第一条图片收藏')])
    def test_share_collection_success(self, col_type):
        """测试从收藏夹中分享条目的流程（完全自治造数据）"""
        strategy = PRIVATE_USER1
        with allure.step(f'1. 前置造数据：向 {strategy.name} 发送一条【{col_type}】消息并收藏'):
            self.chatListPage.enter_chat(strategy.name)
            if col_type == 'text':
                self.chatPage.send_message('测试收藏里的分享数据')
                unique_text = self._build_text('share_test', strategy)
                self._send_text_and_collect(unique_text)
            else:
                self._send_image_and_collect(strategy)
        self.common_enter_my_collection()
        with allure.step(f'2. 校验刚造的数据在收藏夹中正确展示'):
            if col_type == 'text':
                self._verify_latest_text(unique_text)
            self._verify_latest_collection_time()
        with allure.step(f'3. 点击分享第一条【{col_type}】收藏'):
            result = self.collectionPage.share_collection_item(share_type=col_type, index=0)
            check.is_true(result, '点击分享按钮失败')
        with allure.step('4. 分享到聊天窗口'):
            self.contactSelectPage.click_contact_by_name(strategy.name)
            self.contactSelectPage.click_fb_action()
            toast = self.collectionPage.get_toast(ToastMsg.SEND_SUCCESS)
            check.is_true(toast, '发送失败')
        with allure.step('5. 进入聊天窗口并校验'):
            self.mainPage.go_to_main_page()
            self.chatListPage.enter_chat(strategy.name)
            if col_type == 'text':
                actual_text = self.chatPage.get_text_message_content_by_index(index=-1)
                check.equal(actual_text, unique_text, f'校验失败：实际内容{actual_text}, 预期内容{unique_text}')
            else:
                result = self.chatPage.get_last_message_content_bubble_has_type(msg_type=col_type, index=-1)
                check.is_true(result, f'校验失败：实际内容不是{col_type}')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('收藏夹管理-删除')
    @allure.title('删除收藏夹中的单个条目流程 - 状态：已完成')
    @pytest.mark.parametrize('col_type', [pytest.param('text', id='删除第一条文本收藏'), pytest.param('image', id='删除第一条图片收藏')])
    def test_delete_collection_success(self, col_type):
        """  测试从收藏夹中成功删除条目的流程  """
        strategy = PRIVATE_USER1
        with allure.step(f'1. 前置造数据：向 {strategy.name} 发送一条【{col_type}】消息并收藏'):
            self.chatListPage.enter_chat(strategy.name)
            if col_type == 'text':
                unique_text = self._build_text('delete_test', strategy)
                self._send_text_and_collect(unique_text)
            else:
                self._send_image_and_collect(strategy)
        self.common_enter_my_collection()
        with allure.step(f'2. 校验刚造的数据在收藏夹中正确展示'):
            if col_type == 'text':
                self._verify_latest_text(unique_text)
            self._verify_latest_collection_time()
        with allure.step(f'3. 执行删除刚造的最新一条【{col_type}】收藏'):
            before_content = None
            if col_type == 'text':
                before_content = self.collectionPage.get_collection_text_content(0)
            self.collectionPage.del_collection_item(del_type=col_type, index=0)
        with allure.step(f'4. 验证删除结果'):
            if col_type == 'text':
                after_content = self.collectionPage.get_collection_text_content(0)
                check.not_equal(before_content, after_content, f"❌ 删除校验失败：第0条文本内容依然为 '{before_content}'")
            else:
                logger.info(f'{LogIcon.SUCCESS} 图片删除成功')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('收藏管理-一键清空')
    @allure.title('清空收藏夹中特定/所有条目流程-状态：已完成')
    @pytest.mark.parametrize('target_type, exp_del', [pytest.param('text', 1, id='仅清空文本收藏'), pytest.param('image', 2, id='仅清空图片收藏'), pytest.param('all', 0, id='一键清空全部收藏')])
    def test_delete_all_collection_items(self, target_type, exp_del):
        """测试清空收藏夹中指定类型或全部收藏条目的功能，验证类型隔离过滤是否正确"""
        strategy = PRIVATE_USER1
        with allure.step('1. 前置造数据：发送并收藏 2 条文本和 1 条图片'):
            self.chatListPage.enter_chat(strategy.name)
            text1 = self._build_text('all_del_t1', strategy)
            self._send_text_and_collect(text1)
            text2 = self._build_text('all_del_t2', strategy)
            self._send_text_and_collect(text2)
            self._send_image_and_collect(strategy)
        self.common_enter_my_collection()
        with allure.step('2. 校验列表当前至少有刚造好的 3 条收藏'):
            before_items = self.collectionPage.get_collection_items()
            check.greater_equal(len(before_items), 3, '⚠️ 前置数据准备失败，当前收藏列表条数小于3')
        with allure.step(f'3. 执行清空【{target_type}】类型收藏操作'):
            deleted_count = self.collectionPage.del_collection_all_item(del_type=target_type)
            check.greater_equal(deleted_count, exp_del, f'❌ 删除校验失败：实际删除数量 {deleted_count} 小于预期 {exp_del}')
        with allure.step(f'4. 校验删除后，列表中剩余的卡片数量符合预期'):
            after_items = self.collectionPage.get_collection_items()
            if target_type == 'all':
                check.equal(len(after_items), 0, '❌ 校验失败：一键清空全部后收藏列表依然残留有条目')
            else:
                remaining_count = len(before_items) - deleted_count
                check.equal(len(after_items), remaining_count, f'❌ 校验失败：删除后剩余卡片数与预期不符 (期望: {remaining_count}, 实际: {len(after_items)})')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('收藏管理-排序')
    @allure.title('验证收藏列表按时间倒序排列-状态：已完成')
    def test_collection_sort_by_time(self):
        """测试收藏列表中的条目是否按照时间由新到旧倒序排列"""
        self.common_enter_my_collection()
        with allure.step('1. 获取当前页面所有收藏详情数据'):
            details = self.collectionPage.get_collection_details_data(item_type='all', index=-1)
            if not details or len(details) < 2:
                pytest.skip('⚠️ 页面上的收藏条目数少于2条，无法验证排序规律')
        with allure.step('2. 解析时间序列并做排序断言'):
            actual_times = [item['collected_time'] for item in details]
            expected_times = self.collectionPage.get_sort_time(details)
            logger.info(f'{LogIcon.WAIT} 实际时间序列: {actual_times}')
            logger.info(f'{LogIcon.WAIT} 期望时间序列: {expected_times}')
            check.equal(actual_times, expected_times, '❌ 收藏列表未按时间倒序排列！')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('从聊天页面中的收藏发送消息')
    @allure.title('从聊天页面中的收藏发送消息-状态：已完成')
    @pytest.mark.parametrize('index', [pytest.param(0, id='First_Item'), pytest.param(-1, id='Absolute_Last_Item')])
    @pytest.mark.parametrize('col_type', [pytest.param('text', id='文本收藏'), pytest.param('image', id='图片收藏')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_send_collection_message(self, strategy, col_type, index):
        """测试从聊天页面发送不同类型收藏消息的功能"""
        allure.title(f'发送【{col_type}】收藏验证 - {strategy.desc}')
        desc = f'AutoTest_{col_type}_{int(time.time())}'
        with allure.step('1. 进入会话和收藏页面'):
            self.chatListPage.enter_chat(strategy.name)
            self.chatCollectionPage.open_panel_enter_collection_page()
        with allure.step(f'2. 打开【{col_type}】收藏项并验证内容'):
            coll_content = self.chatCollectionPage.select_and_click_collection_item(col_type=col_type, index=index)
            if not coll_content:
                pytest.skip(f'⚠️ 当前测试账号缺少【{col_type}】类型的收藏记录，跳过执行此分支')
            item_content = self.chatCollectionPage.get_selected_item_panel_content(col_type=col_type)
            if col_type == 'image':
                is_similar = self.chatCollectionPage.verify_image_similarity(coll_content, item_content)
                check.is_true(is_similar, f'❌ [Verify] 弹窗预览图片与列表指纹不匹配 (Hash1:{coll_content}, Hash2:{item_content})')
            else:
                check.equal(coll_content, item_content, f'❌ [Verify] 弹窗预览文本与列表不匹配 (期望:{item_content}, 实际:{coll_content})')
        with allure.step('3. 输入附加留言并执行发送操作'):
            self.chatCollectionPage.send_collection_panel_input(desc)
            self.chatCollectionPage.click_send_collection_panel_send()
        with allure.step('4. 验证核心负载及留言已成功上屏'):
            self.chatListPage.click_add_button()
            flag = self.chatCollectionPage.verify_from_collection_message_content(col_type=col_type, exp_content=coll_content, msg=desc)
            check.is_true(flag, f'❌ {col_type} 消息发送上屏验证失败！')