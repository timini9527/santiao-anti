import pytest
import allure
import time
from datetime import datetime, timedelta
import pytest_check as check
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.chat.search.chat_search_page import ChatSearchPage
from pages.main.main_page import MainPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat_options.videos.chat_video_page import ChatVideoPage
from pages.chat_options.file.chat_file_page import ChatFilePage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.common.contact_select_page import ContactSelectPage

@allure.epic('IM核心功能测试')
@allure.feature('聊天设置')
@allure.story('单聊设置 - 查找聊天记录')
class TestChatSearch:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.driver = driver_sender
        self.chatListPage = ChatListPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.chatSearchPage = ChatSearchPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.imagePage = ChatImagePage(driver_sender)
        self.videoPage = ChatVideoPage(driver_sender)
        self.filePage = ChatFilePage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        yield
        with allure.step('后置清理：退回到主页'):
            try:
                self.mainPage.go_to_main_page()
            except Exception:
                pass

    def _enter_search_page(self, strategy):
        """进入聊天记录检索页面（区分群聊和单聊）"""
        self.chatSettingPage.click_more_button()
        if '群聊' in strategy.desc:
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_search_chat_record()
        else:
            self.chatSettingPage.wait_for_setting_page_load()
            self.chatSettingPage.click_search_chat_record()
        self.chatSearchPage.wait_for_search_page_load()

    @allure.story('文本内容检索 - 消息存在')
    @allure.title('文本内容检索 - 消息存在-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='param_1'), pytest.param(GROUP_STRATEGY, id='param_2')])
    def test_search_by_text_content_and_locate(self, strategy):
        """测试在搜索框中输入特定文本，找到对应的记录并定位回聊天界面"""
        keyword = 'SearchMarker'
        test_msg = f'这是一条用于聊天记录搜索测试的独占关键字消息: {keyword}'
        with allure.step(f"前置准备：进入目标好友的{('群' if strategy.is_admin else '单')}聊会话"):
            self.chatListPage.enter_chat(strategy.name)
        with allure.step('1、发送一条包含特殊关键字的测试消息'):
            self.chatSettingPage.send_message(test_msg)
            self.chatSettingPage.wait_for_last_message_send_status()
        with allure.step('2、进入设置页面，点击‘查找聊天记录’'):
            self._enter_search_page(strategy)
        with allure.step(f'3、在搜索框中输入关键字: {keyword}'):
            self.chatSearchPage.input_search_keyword(keyword)
        with allure.step('4、验证检索结果数量并点击定位'):
            results_count = self.chatSearchPage.get_search_results_count()
            check.greater(results_count, 0, f"❌ 未能检索到包含关键字 '{keyword}' 的消息记录")
            if results_count > 0:
                self.chatSearchPage.click_search_result_item(0)
        with allure.step('5、验证是否成功返回聊天主界面，并在聊天界面中根据关键字定位'):
            is_in_chat = self.chatSettingPage.wait_for_last_message_send_status()
            check.is_true(is_in_chat, '❌ 定位失败，未成功返回聊天主会话流页面')
            last_message = self.chatSettingPage.get_text_message_content_by_index()
            check.is_in(keyword, last_message, f"❌ 未能在聊天屏幕上找到包含关键字 '{keyword}' 的定位消息")

    @allure.story('文本内容检索 - 消息不存在')
    @allure.title('文本内容检索 - 消息不存在-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='param_1'), pytest.param(GROUP_STRATEGY, id='param_2')])
    def test_search_by_text_content_not_exist(self, strategy):
        """测试在搜索框中输入特定文本，未找到对应的记录"""
        keyword = 'SearchMarkerNotExist'
        with allure.step(f"前置准备：进入目标好友的{('群' if strategy.is_admin else '单')}聊会话"):
            self.chatListPage.enter_chat(strategy.name)
        with allure.step('1、进入设置页面，点击‘查找聊天记录’'):
            self._enter_search_page(strategy)
        with allure.step(f'2、在搜索框中输入关键字: {keyword}'):
            self.chatSearchPage.input_search_keyword(keyword)
        with allure.step('3、验证检索结果数量'):
            results_count = self.chatSearchPage.get_search_results_count()
            check.equal(results_count, 0, f"❌ 检索到包含关键字 '{keyword}' 的消息记录")

    @allure.story('日期日历面板筛选聊天记录状态校验')
    @allure.title('日期日历面板筛选聊天记录状态校验-状态：已完成')
    @pytest.mark.parametrize('day_type, delta_days, fixed_date, expected_gray, send_msg_before', [pytest.param('today_has_msg', 0, None, False, True, id='今天（有消息）'), pytest.param('future_no_msg', 2, None, True, False, id='未来某天（无消息）'), pytest.param('past_no_msg', -60, None, True, False, id='过去某天（无消息）'), pytest.param('fixed_date_no_msg', None, ('2026-4', '19'), True, False, id='固定日期2026年4月19日（无消息）'), pytest.param('fixed_date_has_msg', None, ('2026-4', '30'), False, True, id='固定日期2026年4月30日（有消息）'), pytest.param('fixed_date_no_msg', None, ('2026-5', '24'), True, False, id='固定日期2026年5月24日（无消息）'), pytest.param('fixed_date_has_msg', None, ('2026-5', '25'), False, True, id='固定日期2026年5月25日（有消息）')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='param_1'), pytest.param(GROUP_STRATEGY, id='param_2')])
    def test_search_by_date_calendar(self, strategy, day_type, delta_days, fixed_date, expected_gray, send_msg_before):
        """测试按不同日期类型筛选，验证日历中日期的灰显/激活状态"""
        now = datetime.now()
        if fixed_date:
            year_month_input, target_day = fixed_date
        else:
            target_date = now + timedelta(days=delta_days)
            target_day = target_date.strftime('%e').strip()
            year_month_input = target_date.strftime('%Y-%m')
        year, month = year_month_input.split('-')
        clean_month = month.lstrip('0')
        month_day = f'{clean_month}-{target_day}'
        year_month = self.chatSearchPage.get_year_month_from_date(year_month_input)
        with allure.step(f"前置准备：进入目标好友的{('群' if strategy.is_admin else '单')}聊会话"):
            self.chatListPage.enter_chat(strategy.name)
        if send_msg_before:
            with allure.step('1、确保当前会话中今天有消息记录'):
                now_time = now.strftime('%H:%M')
                self.chatSettingPage.send_message('今天日期搜索测试定位信息')
                self.chatSettingPage.wait_for_last_message_send_status()
        with allure.step('2、进入设置页面并点击‘查找聊天记录’'):
            self._enter_search_page(strategy)
        with allure.step('3、点击选择‘日期’筛选'):
            self.chatSearchPage.click_date_option()
        with allure.step(f"4、滚动查找并验证 {day_type} 对应的日期 '{year_month} {target_day}日'"):
            result = self.chatSearchPage.scroll_date_panel(year_month, target_day)
            check.is_not_none(result, f"❌ 未能成功在日历中定位到日期元素 '{year_month} {target_day}日'")
            if expected_gray:
                check.is_false(result, f"❌ 预期日期 '{year_month} {target_day}日' 应该是灰色(不可点)，但实际识别为黑色(可点)")
            else:
                check.is_true(result, f"❌ 预期日期 '{year_month} {target_day}日' 应该是黑色(可点)，但实际识别为灰色(不可点)")
                with allure.step('5、获取并验证消息定位后的日期'):
                    texts = self.chatSearchPage.get_date_from_ocr()
                    expected_date_str = f'{clean_month}月{target_day}日'
                    expected_short_str = f'{clean_month}-{target_day}'
                    if day_type == 'today_has_msg':
                        import re
                        time_pattern = re.compile('\\b(2[0-3]|[0-1]?[0-9]):([0-5][0-9])\\b')
                        found_times = []
                        for t in texts:
                            match = time_pattern.search(t)
                            if match:
                                if not any((kw in t for kw in ['年', '月', '日', '-', '/'])):
                                    found_times.append(match.group(0))
                        check.is_true(len(found_times) > 0, f"❌ OCR识别的文本列表 '{texts}' 中，未找到属于今天（24小时内，仅 HH:MM 格式）的时间展示")
                    else:
                        found = any((expected_date_str in t or expected_short_str in t or target_day in t for t in texts))
                        check.is_true(found, f"❌ OCR识别的文本列表 '{texts}' 中，均不包含目标日期 '{expected_date_str}' 或 '{target_day}'")

    @allure.story('多媒体（图片/视频/文件）分类过滤定位测试')
    @allure.title('多媒体（图片/视频/文件）分类过滤定位测试-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='param_1'), pytest.param(GROUP_STRATEGY, id='param_2')])
    def test_search_by_media_category_and_locate(self, strategy):
        """测试进入图片/视频/文件分类视图，选择媒体项并定位到聊天上下文"""
        with allure.step(f"前置准备：进入目标好友的{('群' if strategy.is_admin else '单')}聊会话"):
            self.chatListPage.enter_chat(strategy.name)
        with allure.step('1、发送一张图片作为测试数据'):
            self.imagePage.click_add_button()
            self.imagePage.click_image_button()
            self.imagePage.wait_for_image_page_load()
            self.imagePage.select_single_image()
            self.imagePage.click_send_image()
            image_hash = self.chatPage.get_chat_image_hash(index=-1)
        with allure.step(f'2、进入设置页面并进入‘查找聊天记录’'):
            self._enter_search_page(strategy)
        with allure.step('3、点击‘图片’分类过滤项'):
            self.chatSearchPage.click_image_option()
            self.chatSearchPage.wait_for_media_page_load()
        with allure.step('4、验证图片分类归档网格中有数据并点击缩略图'):
            media_count = self.chatSearchPage.get_media_items_count()
            check.greater(media_count, 0, '❌ 图片归档页中没有找到任何图片记录')
            if media_count > 0:
                self.chatSearchPage.click_media_item(index=0)
                self.chatPage.wait_for_chat_page_load()
                to_user_name = self.chatPage.get_top_name()
                check.is_true(strategy.name in to_user_name, f'❌ 返回聊天窗口与预期不符')
                chat_image_hash = self.chatPage.get_chat_all_image_hash()
                check.is_true(image_hash in chat_image_hash, f'❌ 图片 hash 值不匹配')

    @allure.story('视频分类过滤定位测试')
    @allure.title('视频分类过滤定位测试-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='param_1'), pytest.param(GROUP_STRATEGY, id='param_2')])
    def test_search_by_video_category_and_locate(self, strategy):
        """测试进入视频分类视图，选择视频并定位到聊天上下文"""
        with allure.step(f"前置准备：进入目标好友的{('群' if strategy.is_admin else '单')}聊会话"):
            self.chatListPage.enter_chat(strategy.name)
        with allure.step('1、发送一段视频作为测试数据'):
            self.videoPage.click_add_button()
            self.videoPage.click_image_button()
            self.videoPage.wait_for_image_page_load()
            self.videoPage.select_single_video()
            self.videoPage.click_send_image()
            video_duration = self.chatPage.get_chat_video_duration(index=-1)
        with allure.step(f'2、进入设置页面并进入‘查找聊天记录’'):
            self._enter_search_page(strategy)
        with allure.step('3、点击‘视频’分类过滤项'):
            self.chatSearchPage.click_video_option()
            self.chatSearchPage.wait_for_media_page_load()
        with allure.step('4、验证视频分类归档网格中有数据并点击缩略图'):
            media_count = self.chatSearchPage.get_media_items_count()
            check.greater(media_count, 0, '❌ 视频归档页中没有找到任何视频记录')
            if media_count > 0:
                self.chatSearchPage.click_media_item(index=0)
                self.chatPage.wait_for_chat_page_load()
                to_user_name = self.chatPage.get_top_name()
                check.is_true(strategy.name in to_user_name, f'❌ 返回聊天窗口与预期不符')
                chat_video_duration = self.chatPage.get_chat_all_video_duration()
                check.is_true(video_duration in chat_video_duration, f'❌ 视频时长不匹配')

    @allure.story('文件分类过滤定位测试')
    @allure.title('文件分类过滤定位测试-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='param_1'), pytest.param(GROUP_STRATEGY, id='param_2')])
    def test_search_by_file_category_and_locate(self, strategy):
        """测试进入文件分类视图，选择文件并定位到聊天上下文"""
        with allure.step(f"前置准备：进入目标好友的{('群' if strategy.is_admin else '单')}聊会话"):
            self.chatListPage.enter_chat(strategy.name)
        with allure.step('1、发送一个文件作为测试数据'):
            self.filePage.open_panel_enter_file_page()
            self.filePage.wait_for_file_page_load()
            self.filePage.click_file_menu_button()
            self.filePage.click_sub_menu_item('图片')
            self.filePage.select_any_file_in_dir(file_type='image')
            self.filePage.click_send_file()
            file_name = self.filePage.get_last_file_name_in_chat()
        with allure.step(f'2、进入设置页面并进入‘查找聊天记录’'):
            self._enter_search_page(strategy)
        with allure.step('3、点击‘文件’分类过滤项'):
            self.chatSearchPage.click_file_option()
            self.chatSearchPage.wait_for_file_page_load()
        with allure.step('4、验证文件分类归档列表中有数据并点击该文件项'):
            file_count = self.chatSearchPage.get_file_items_count()
            check.greater(file_count, 0, '❌ 文件归档页中没有找到任何文件记录')
            if file_count > 0:
                self.chatSearchPage.click_file_item(index=0)
                self.chatPage.wait_for_chat_page_load()
                to_user_name = self.chatPage.get_top_name()
                check.is_true(strategy.name in to_user_name, f'❌ 返回聊天窗口与预期不符')
                chat_file_names = self.chatPage.get_chat_all_file_name()
                check.is_true(file_name in chat_file_names, f'❌ 文件名称不匹配')

    @allure.story('群成员分类过滤定位测试')
    @allure.title('群成员分类过滤定位测试-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(GROUP_STRATEGY, id='param_1')])
    def test_search_by_group_member_category_and_locate(self, strategy):
        """测试进入群成员分类视图，选择群成员并定位到聊天上下文"""
        keyword = 'GroupMemberSearchMarker'
        test_msg = f'这是一条群成员定位专属测试消息: {keyword}'
        with allure.step(f'前置准备：进入目标好友的群聊会话'):
            self.chatListPage.enter_chat(strategy.name)
        with allure.step('1、发送一条群聊专属测试消息'):
            self.chatSettingPage.send_message(test_msg)
            self.chatSettingPage.wait_for_last_message_send_status()
        with allure.step(f'2、进入设置页面并进入‘查找聊天记录’'):
            self._enter_search_page(strategy)
        with allure.step('3、点击‘群成员’分类过滤项'):
            self.chatSearchPage.click_group_member_option()
        with allure.step('4、验证群成员分类归档列表中有数据并点击首个群成员项'):
            self.contactSelectPage.click_contact_by_name(name='1234567890', select_type='forward')
        with allure.step('5、在该成员的消息检索结果中，点击对应的消息并跳转回聊天页'):
            results_count = self.chatSearchPage.get_group_members_count()
            check.greater(results_count, 0, '❌ 未找到该成员的任何聊天记录')
            if results_count > 0:
                self.chatSearchPage.click_message_item(index=0)
                self.chatPage.wait_for_chat_page_load()
                to_user_name = self.chatPage.get_top_name()
                check.is_true(strategy.name in to_user_name, f'❌ 返回聊天窗口与预期不符')
                last_message = self.chatSettingPage.get_text_message_content_by_index()
                check.is_in(keyword, last_message, f"❌ 未能在聊天屏幕上找到包含关键字 '{keyword}' 的定位消息")