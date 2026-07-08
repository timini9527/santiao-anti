import allure
import pytest
import pytest_check as check
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.system.main.main_page import MainPage
from pages.chat.chat_options.location.chat_position_page import ChatPositionPage
from core.logger_utils import logger
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY


@allure.epic("IM核心功能测试")
@allure.feature("聊天面板-位置")
@allure.story("测试搜索不存在的地点，验证 UI 空状态处理")
class TestChatPosition:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        初始化页面对象并确保测试结束后返回主页
        """
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.chatPositionPage = ChatPositionPage(driver_sender)

        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    def _enter_chat_and_open_location(self, chat_name: str):
        """进入指定的聊天会话并打开位置选择页面"""
        self.chatListPage.enter_chat(chat_name)
        self.chatPositionPage.open_panel_enter_location_page()
    



    @allure.story("搜索位置-无结果异常场景")
    @allure.title("搜索位置-无结果异常场景-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_search_location_no_results(self, strategy):
        """测试搜索不存在的地点，验证 UI 空状态处理"""
        with allure.step("1. 进入位置选择页"):
            self.chatListPage.enter_chat(strategy.name)
            titles_pre = self.chatPage.get_all_location_titles()
            self.chatPositionPage.open_panel_enter_location_page()

        with allure.step("2. 输入无法搜到的关键词"):
            search_key = "不存在的神秘地点123456789"
            self.chatPositionPage.input_search_content(search_key)
            
        with allure.step("3. 验证结果列表为空"):
            _, poi_titles = self.chatPositionPage.get_all_location_titles()
            check.equal(len(poi_titles), 0, f"❌ 预期搜索无结果，但实际找到了 {len(poi_titles)} 个 POI")
            self.chatPositionPage.click_cancel_button()
        
        with allure.step("4. 验证返回聊天页面"):
            self.chatPage.click_add_button()
            titles_aft = self.chatPage.get_all_location_titles()
            check.equal(titles_pre, titles_aft, f"❌ 预期返回聊天页面，但实际没有搜索结果")
    

    @allure.story("搜索指定位置并发送")
    @allure.title("搜索指定位置并发送-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_search_and_send_location(self, strategy):
        """测试搜索特定 POI 并发送"""
        with allure.step(f"1. 进入与【{strategy.name}】的聊天并进入位置页"):
            self._enter_chat_and_open_location(strategy.name)

        with allure.step("2. 搜索特定地点并选择"):
            search_key = "C"
            self.chatPositionPage.input_search_content(search_key)
            _, poi_titles = self.chatPositionPage.get_all_location_titles()
            check.is_true(len(poi_titles) > 0, f"搜索关键字 '{search_key}' 未返回任何结果")

            self.chatPositionPage.get_search_result_and_click()
            self.chatPositionPage.click_send_button()

        with allure.step("3. 验证聊天气泡内容"):
            actual_bubble = self.chatPage.verify_location_sent_status()
            check.is_in(poi_titles[0], actual_bubble['title'], f"发送的搜索位置标题不匹配 {poi_titles} {actual_bubble['title']}")


    @allure.story("取消发送位置流程")
    @allure.title("取消发送位置流程-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_cancel_send_location(self, strategy):
        """验证进入位置页面后取消发送，不会产生消息"""
        self.chatListPage.enter_chat(strategy.name)
        
        with allure.step("1. 记录发送前的消息数量"):
            initial_count = self.chatPage.get_total_message_count()

        with allure.step("2. 进入位置页并点击取消"):
            self.chatPositionPage.open_panel_enter_location_page()
            self.chatPositionPage.click_cancel_button()
            self.chatPage.click_add_button()

        with allure.step("3. 验证未产生新消息"):
            check.is_true(self.chatPage.verify_is_on_chat_page(), "取消后未返回聊天页")
            final_count = self.chatPage.get_total_message_count()
            check.equal(initial_count, final_count, "点击取消后不应产生新消息")


    @allure.story("发送定位消息")
    @allure.title("发送定位消息-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_send_location_message(self, strategy):
        # with allure.step("1. 检查获取位置权限没有则开启权限"):
        #     self.chatPage_sender.open_child_elem(attrName='位置')

        with allure.step(f"1. 进入与【{strategy.name}】的聊天"):
            self._enter_chat_and_open_location(strategy.name)

        with allure.step("2. 获取当前选中的 POI 信息并发送"):
            self.chatPositionPage.click_current_location_button()
            poi_title, poi_detail = self.chatPositionPage.get_selected_location_info()
            check.is_true(poi_title and poi_detail, f"未获取到位置信息")

            self.chatPositionPage.click_send_button()
            check.is_true(self.chatPage.verify_is_on_chat_page(), "未成功返回聊天页面")

        with allure.step("3. 验证聊天气泡内容"):
            actual_bubble = self.chatPage.verify_location_sent_status()
            check.is_true(self.chatPage.verify_message_sent_status(), f"测试发送位置失败，发送位置状态异常")
            check.is_in(poi_title, actual_bubble['title'],
                        f"测试发送位置失败，地域匹配失败!  Exp:截取区域[{poi_title}] 未出现在, Act:气泡地址[{actual_bubble['title']}] 中")
            check.equal(poi_detail, actual_bubble.get('detail_address'),
                        f"发送位置 Exp: {poi_detail}, Act: {actual_bubble.get('detail_address')} 不匹配")

        with allure.step("4. 验证地图显示"):
            self.chatPage.verify_location_enter_map_detail()
            result = self.chatPositionPage.verify_map_location_info(poi_title, poi_detail)
            check.is_true(result, f"发送位置 {poi_title} {poi_detail} 地图显示位置信息不一致")


    @allure.story("位置消息-详情页返回")
    @allure.title("位置消息-详情页返回-状态：已完成")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_back_from_map_detail(self, strategy):
        """验证进入地图详情页后，点击返回能正确回到聊天页"""
        with allure.step(f"1. 进入与【{strategy.name}】的聊天并进入位置页"):
            self._enter_chat_and_open_location(strategy.name)
            self.chatPositionPage.click_send_button()
        
        with allure.step("2. 进入地图详情并返回"):
            self.chatPage.verify_location_enter_map_detail()
            self.chatPage.click_back_button()
            
        with allure.step("3. 验证是否回到聊天页"):
            check.is_true(self.chatPage.verify_is_on_chat_page(), "未能正确返回聊天页面")


    @allure.story("位置消息-长按删除")
    @allure.title("位置消息-长按删除-状态：未完成")
    @pytest.mark.skip(reason="删除功能未实现")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_delete_location_message(self, strategy):
        """验证位置消息可以被长按删除"""
        self.chatListPage.enter_chat(strategy.name)
        
        with allure.step("1. 发送位置并记录总数"):
            self.chatPositionPage.open_panel_enter_location_page()
            self.chatPositionPage.click_send_button()
            count_pre = self.chatPage.get_total_message_count()
            
        with allure.step("2. 长按消息并删除"):
            self.chatPage.long_press_last_location_message()
            self.chatPage.click_delete()
            
        with allure.step("3. 验证消息已消失"):
            count_aft = self.chatPage.get_total_message_count()
            check.equal(count_pre - 1, count_aft, "消息数量未减少，删除可能失败")


    @allure.story("位置消息-长按转发")
    @allure.title("位置消息-长按转发-状态：未完成")
    @pytest.mark.skip(reason="转发功能未实现")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_forward_location_message(self, strategy):
        """验证位置消息可以被长按转发"""
        self.chatListPage.enter_chat(strategy.name)
        
        with allure.step("1. 发送原始位置"):
            self.chatPositionPage.open_panel_enter_location_page()
            self.chatPositionPage.click_send_button()
            title_pre, _ = self.chatPage.verify_location_sent_status().values()
            
        with allure.step("2. 长按消息并转发"):
            self.chatPage.long_press_last_location_message()
            self.chatPage.click_forward()
            # 在转发列表中选择自己（作为测试简化）
            self.chatListPage.enter_session(strategy.name) 
            
        with allure.step("3. 验证转发成功"):
            actual_bubble = self.chatPage.verify_location_sent_status()
            check.is_in(title_pre, actual_bubble['title'], "转发后的位置标题不匹配")


    @allure.story("位置消息-长按撤回")
    @allure.title("位置消息-长按撤回-状态：未完成")
    @pytest.mark.skip(reason="撤回功能待完善并接入通用交互逻辑")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_revoke_location_message(self, strategy):
        """验证发送定位后可以成功撤回"""
        self.chatListPage.enter_chat(strategy.name)
        
        with allure.step("1. 发送定位消息"):
            self.chatPositionPage.open_panel_enter_location_page()
            self.chatPositionPage.click_send_button()
            
        with allure.step("2. 长按消息并点击撤回"):
            # TODO: 将 long_press_last_location_message 替换或兼容全局通用的长按逻辑
            self.chatPage.long_press_last_location_message()
            self.chatPage.click_revoke()
            
        with allure.step("3. 验证撤回提示"):
            notice_text = self.chatPage.get_revoke_notice_text()
            check.is_in("撤回", notice_text, "未能捕获到预期的撤回提示文字")


    @allure.story("位置消息-长按收藏")
    @allure.title("位置消息-长按收藏-状态：未完成")
    @pytest.mark.skip(reason="收藏功能待完善并接入通用交互逻辑")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_favorite_location_message(self, strategy):
        """验证位置消息可以被长按收藏"""
        pass


    @allure.story("位置消息-引用回复")
    @allure.title("位置消息-引用回复-状态：未完成")
    @pytest.mark.skip(reason="回复功能待完善并接入通用交互逻辑")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1], ids=lambda s: s.desc)
    def test_reply_location_message(self, strategy):
        """验证位置消息可以被长按引用回复"""
        pass
