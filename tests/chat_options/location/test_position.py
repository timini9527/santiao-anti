import allure
import pytest
import pytest_check as check
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.main.main_page import MainPage
from pages.chat_options.location.chat_position_page import ChatPositionPage
from core.logger_utils import logger, LogIcon
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY

@allure.epic('IM核心功能测试')
@allure.feature('聊天面板-位置')
@allure.story('测试搜索不存在的地点，验证 UI 空状态处理')
class TestChatPosition:
    _chat_target = None

    @pytest.fixture(scope="class", autouse=True)
    def setup_class_teardown(self, driver_sender):
        """
        类级别后置清理：所有用例执行完成后，统一执行一次返回主页
        """
        yield
        try:
            self.__class__._chat_target = None
            MainPage(driver_sender).go_to_main_page()
            logger.info(f"{LogIcon.SETUP} [Class Teardown] 位置模块全部用例执行完毕，统一返回主页")
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} Teardown 失败，未能返回首页: {e}")

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatLongPressPage = ChatLongPressPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.chatPositionPage = ChatPositionPage(driver_sender)

    def _enter_chat_and_open_location(self, chat_name: str):
        """进入指定的聊天会话并打开位置选择页面（支持同会话直接复用，跨会话自动退回主页切换）"""
        if self.__class__._chat_target != chat_name:
            if self.__class__._chat_target is not None:
                logger.info(f"{LogIcon.ACTION} [Session Switch] 检测到聊天对象从【{self.__class__._chat_target}】切换为【{chat_name}】，退回首页重新进入")
                self.mainPage.go_to_main_page()
            self.chatListPage.enter_chat(chat_name)
            self.__class__._chat_target = chat_name
        self.chatPositionPage.open_panel_enter_location_page()




    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('搜索位置-无结果异常场景')
    @allure.title('搜索位置-无结果异常场景-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_search_location_no_results(self, strategy):
        """测试搜索不存在的地点，验证 UI 空状态处理"""
        with allure.step(f'1. 进入【{strategy.name}】并进入位置选择页'):
            self._enter_chat_and_open_location(strategy.name)
        with allure.step('2. 输入无法搜到的关键词'):
            self.chatPositionPage.input_search_content('不存在的神秘地点123456789')
        with allure.step('3. 验证结果列表为空并点击取消返回'):
            _, poi_titles = self.chatPositionPage.get_all_location_titles()
            check.equal(len(poi_titles), 0, f'❌ 预期搜索无结果，但实际找到了 {len(poi_titles)} 个 POI')
            self.chatPositionPage.click_cancel_button()
            check.is_true(self.chatPage.verify_is_on_chat_page(), '❌ 点击取消后未能正常返回聊天页面')


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('搜索指定位置并发送')
    @allure.title('搜索指定位置并发送-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_search_and_send_location(self, strategy):
        """测试搜索特定 POI 并发送"""
        with allure.step(f'1. 进入【{strategy.name}】并进入位置页'):
            self._enter_chat_and_open_location(strategy.name)
        with allure.step('2. 搜索特定地点并选中发送'):
            search_key = 'C'
            self.chatPositionPage.input_search_content(search_key)
            _, poi_titles = self.chatPositionPage.get_all_location_titles()
            check.is_true(len(poi_titles) > 0, f"搜索关键字 '{search_key}' 未返回任何结果")
            self.chatPositionPage.get_search_result_and_click()
            self.chatPositionPage.click_send_button()
        with allure.step('3. 验证聊天气泡内容'):
            actual_bubble = self.chatPage.verify_location_sent_status()
            check.is_in(poi_titles[0], actual_bubble['title'], f"发送的搜索位置标题不匹配 {poi_titles} {actual_bubble['title']}")


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('取消发送位置流程')
    @allure.title('取消发送位置流程-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_cancel_send_location(self, strategy):
        """验证进入位置页面后取消发送，不会产生消息"""
        with allure.step(f'1. 进入【{strategy.name}】记录当前消息数并打开位置页'):
            if self.__class__._chat_target != strategy.name:
                if self.__class__._chat_target is not None:
                    self.mainPage.go_to_main_page()
                self.chatListPage.enter_chat(strategy.name)
                self.__class__._chat_target = strategy.name
            initial_count = self.chatPage.get_total_message_count()
            self.chatPositionPage.open_panel_enter_location_page()
        with allure.step('2. 点击取消并验证未产生新消息'):
            self.chatPositionPage.click_cancel_button()
            check.is_true(self.chatPage.verify_is_on_chat_page(), '取消后未返回聊天页')
            final_count = self.chatPage.get_total_message_count()
            check.equal(initial_count, final_count, '点击取消后不应产生新消息')


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('发送定位消息')
    @allure.title('发送定位消息-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_send_location_message(self, strategy):
        """测试获取当前定位并发送，同时校验气泡与地图详情"""
        with allure.step(f'1. 进入【{strategy.name}】并获取定位信息'):
            self._enter_chat_and_open_location(strategy.name)
            self.chatPositionPage.click_current_location_button()
            poi_title, poi_detail = self.chatPositionPage.get_selected_location_info()
            check.is_true(poi_title and poi_detail, '未获取到位置信息')
        with allure.step('2. 点击发送并校验气泡'):
            self.chatPositionPage.click_send_button()
            check.is_true(self.chatPage.verify_is_on_chat_page(), '未成功返回聊天页面')
            check.is_true(self.chatPage.wait_for_last_message_send_status(), '发送位置状态异常')
            actual_bubble = self.chatPage.verify_location_sent_status()
            check.is_in(poi_title, actual_bubble['title'], f"地域匹配失败! Exp: [{poi_title}], Act: [{actual_bubble['title']}]")
            check.equal(poi_detail, actual_bubble.get('detail_address'), f"详细地址不匹配 Exp: {poi_detail}, Act: {actual_bubble.get('detail_address')}")
        with allure.step('3. 验证地图详情显示'):
            self.chatPage.verify_location_enter_map_detail()
            result = self.chatPositionPage.verify_map_location_info(poi_title, poi_detail)
            check.is_true(result, f'发送位置 {poi_title} {poi_detail} 地图显示位置信息不一致')


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('位置消息-详情页返回')
    @allure.title('位置消息-详情页返回-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_back_from_map_detail(self, strategy):
        """验证进入地图详情页后，点击返回能正确回到聊天页"""
        with allure.step(f'1. 进入【{strategy.name}】并发送位置'):
            self._enter_chat_and_open_location(strategy.name)
            self.chatPositionPage.click_send_button()
        with allure.step('2. 进入地图详情并点击顶部返回'):
            self.chatPage.verify_location_enter_map_detail()
            self.chatPage.click_top_back_bnt()
            check.is_true(self.chatPage.verify_is_on_chat_page(), '未能正确返回聊天页面')


    @allure.story('位置消息-长按删除')
    @allure.title('位置消息-长按删除-状态：未完成')
    @pytest.mark.skip(reason='删除功能未实现')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_delete_location_message(self, strategy):
        """验证位置消息可以被长按删除"""
        self.chatListPage.enter_chat(strategy.name)
        with allure.step('1. 发送位置并记录总数'):
            self.chatPositionPage.open_panel_enter_location_page()
            self.chatPositionPage.click_send_button()
            count_pre = self.chatPage.get_total_message_count()
        with allure.step('2. 长按消息并删除'):
            self.chatLongPressPage.long_press_last_message()
            self.chatLongPressPage._execute_and_verify_menu_item('删除')
        with allure.step('3. 验证消息已消失'):
            count_aft = self.chatPage.get_total_message_count()
            check.equal(count_pre - 1, count_aft, '消息数量未减少，删除可能失败')


    @allure.story('位置消息-长按转发')
    @allure.title('位置消息-长按转发-状态：未完成')
    @pytest.mark.skip(reason='转发功能未实现')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_forward_location_message(self, strategy):
        """验证位置消息可以被长按转发"""
        self.chatListPage.enter_chat(strategy.name)
        with allure.step('1. 发送原始位置'):
            self.chatPositionPage.open_panel_enter_location_page()
            self.chatPositionPage.click_send_button()
            title_pre, _ = self.chatPage.verify_location_sent_status().values()
        with allure.step('2. 长按消息并转发'):
            self.chatLongPressPage.long_press_last_message()
            self.chatLongPressPage._execute_and_verify_menu_item('转发')
            self.chatListPage.enter_session(strategy.name)
        with allure.step('3. 验证转发成功'):
            actual_bubble = self.chatPage.verify_location_sent_status()
            check.is_in(title_pre, actual_bubble['title'], '转发后的位置标题不匹配')


    @allure.story('位置消息-长按撤回')
    @allure.title('位置消息-长按撤回-状态：未完成')
    @pytest.mark.skip(reason='撤回功能待完善并接入通用交互逻辑')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_revoke_location_message(self, strategy):
        """验证发送定位后可以成功撤回"""
        self.chatListPage.enter_chat(strategy.name)
        with allure.step('1. 发送定位消息'):
            self.chatPositionPage.open_panel_enter_location_page()
            self.chatPositionPage.click_send_button()
        with allure.step('2. 长按消息并点击撤回'):
            self.chatLongPressPage.long_press_last_message()
            self.chatLongPressPage._execute_and_verify_menu_item('撤回')
        with allure.step('3. 验证撤回提示'):
            notice_result = self.chatPage.get_withdraw_message()
            check.is_not_none(notice_result, '未能捕获到预期的撤回提示')
            if notice_result:
                notice_text, _ = notice_result
                check.is_in('撤回', notice_text, '未能捕获到预期的撤回提示文字')


    @allure.story('位置消息-长按收藏')
    @allure.title('位置消息-长按收藏-状态：未完成')
    @pytest.mark.skip(reason='收藏功能待完善并接入通用交互逻辑')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_favorite_location_message(self, strategy):
        """验证位置消息可以被长按收藏"""
        pass


    @allure.story('位置消息-引用回复')
    @allure.title('位置消息-引用回复-状态：未完成')
    @pytest.mark.skip(reason='回复功能待完善并接入通用交互逻辑')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_reply_location_message(self, strategy):
        """验证位置消息可以被长按引用回复"""
        pass