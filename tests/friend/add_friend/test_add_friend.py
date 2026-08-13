import allure
import pytest
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.add_friend.add_friend_page import AddFriendPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, PRIVATE_USER3, PRIVATE_USER4

@allure.epic('IM核心功能测试')
@allure.feature('通讯录与好友管理')
@allure.story('添加好友功能')
class TestAddFriend:
    """添加好友功能自动化测试集 (基于 0.4 添加好友模块 用例文档重构优化)"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        """方法级前置与后置：初始化相关的 Page Object 并确保初始状态重置"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.addFriendPage = AddFriendPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f'⚠️ [Teardown] 返回首页失败: {e}')

    def _home_to_add_friend(self):
        """从首页进入添加好友页面"""
        self.homePage.click_add_button()
        self.homePage.click_add_friend()
        is_loaded = self.addFriendPage.wait_for_add_friend_page()
        check.is_true(is_loaded, '❌ 未能成功进入添加朋友页面')

    def _search_and_open_profile(self, search_key: str):
        """进入添加朋友页，搜索账号并打开资料详情"""
        self._home_to_add_friend()
        self.addFriendPage.search_friend_by_content(search_key)
        self.addFriendPage.click_confirm_search()
        self.addFriendPage.click_search_result_item()
        is_loaded = self.contactDetailPage.wait_for_detail_page_load()
        assert is_loaded, f'❌ 搜索 {search_key} 后未能进入资料详情页'

    @allure.story('添加好友页面')
    @allure.title('进入添加朋友页校验并点击返回-状态：已完成')
    def test_add_friend_entry_and_back(self):
        """测试从首页加号进入添加朋友页面，校验占位符，然后点击返回能成功回到主页"""
        with allure.step('1. 进入添加朋友页面并等待加载'):
            self._home_to_add_friend()
        with allure.step('2. 校验搜索框入口占位符文本是否存在'):
            entry_text = self.addFriendPage.get_search_input_text()
            check.is_in('三条ID/手机号/群ID', entry_text, '❌ 添加朋友页搜索框的占位文本不匹配')
        with allure.step('3. 点击左上角返回按钮'):
            self.addFriendPage.click_back()
        with allure.step('4. 校验成功返回到主页会话列表'):
            is_on_home = self.homePage.wait_home_page(timeout=5)
            check.is_true(is_on_home, '❌ 点击返回按钮后，未能成功退回主页面')

    @allure.story('搜索')
    @allure.title('搜索框为空/空格时的拦截校验-状态：已完成')
    @pytest.mark.parametrize('search_key', [pytest.param('', id='空值'), pytest.param(' ', id='单个空格'), pytest.param('    ', id='多个空格')])
    def test_add_friend_search_empty_input(self, search_key):
        """测试在添加好友搜索框中不输入内容或输入空格，确认系统不展示搜索结果"""
        with allure.step('1. 进入添加朋友页面'):
            self._home_to_add_friend()
        with allure.step(f'2. 在搜索框中输入无效内容: {search_key!r}'):
            self.addFriendPage.search_friend_by_content(search_key)
        with allure.step('3. 校验无法发起搜索且不展示搜索结果'):
            can_search = self.addFriendPage.is_confirm_search_visible()
            is_result = self.addFriendPage.get_search_result_item(raise_exception=False)
            check.is_false(can_search, '❌ 搜索为空或空格时，异常出现了确认搜索项')
            check.is_false(is_result, '❌ 搜索为空或空格时，异常出现了搜索结果项')

    @allure.story('搜索')
    @allure.title('搜索不存在账号 - 验证未找到好友提示-状态：已完成')
    def test_add_friend_search_non_existent_account(self):
        """测试搜索不存在的账号，校验列表抛出未找到提示"""
        non_existent_key = '199999999991'
        with allure.step('1. 进入添加朋友页面'):
            self._home_to_add_friend()
        with allure.step(f'2. 输入不存在账号 {non_existent_key} 并确认搜索'):
            self.addFriendPage.search_friend_by_content(non_existent_key)
            self.addFriendPage.click_confirm_search()
        with allure.step('3. 校验弹出 ‘未找到好友/群组’ 提示'):
            msg = self.addFriendPage.get_search_result_item_message()
            check.equal('未找到好友/群组', msg, '❌ 搜索不存在账号时，未弹出预期 [未找到好友/群组] 提示')


    @allure.story('搜索')
    @allure.title('通过{search_type}搜索正常账号并校验资料详情-状态：已完成')
    @pytest.mark.parametrize('search_type, search_key', [
        pytest.param('手机号', PRIVATE_USER1.phone, id='手机号搜索'), 
        pytest.param('三条ID', PRIVATE_USER1.st_id, id='三条ID搜索')
        ])
    def test_add_friend_search_success_and_view_profile(self, search_type, search_key):
        """测试通过手机号或三条ID搜索正常账号并校验资料详情"""
        search_id = PRIVATE_USER1.st_id
        with allure.step(f'1. 通过{search_type} {search_key} 搜索并进入资料详情'):
            self._search_and_open_profile(search_key)

        with allure.step('2. 校验个人资料详情页基本元素展示'):
            nickname = self.contactDetailPage.get_raw_nickname()
            check.is_in(PRIVATE_USER1.name, nickname, f'❌ 资料页昵称为 {nickname}，不包含预期的 {PRIVATE_USER1.name}')
            
            is_unfriend = self.contactDetailPage.is_add_friend_unfriend_visible(timeout=1, raise_exception=False)
            if not is_unfriend:
                st_id = self.contactDetailPage.get_st_id()
                check.is_in(search_id, st_id, f'❌ 资料页三条ID为 {st_id}，不包含预期的 {search_id}')
            else:
                logger.info("ℹ️ [Action - AddFriend] 当前搜索到的账号为非好友，资料页不展示三条ID，跳过三条ID断言")


    @allure.story('搜索')
    @allure.title('搜索当前登录账号时禁止添加自己-状态：已完成')
    def test_add_friend_search_self(self):
        """测试搜索当前登录账号后不会出现添加好友申请入口"""
        with allure.step(f'1. 搜索当前登录账号 {PRIVATE_USER3.phone} 并进入资料详情'):
            self._search_and_open_profile(PRIVATE_USER3.phone)

        with allure.step('2. 校验资料身份正确且不显示添加好友按钮'):
            nickname = self.contactDetailPage.get_contact_nickname()
            has_add_button = self.contactDetailPage.is_add_friend_unfriend_visible()
            check.is_in(PRIVATE_USER3.name, nickname, f'❌ 搜索自己后资料昵称不正确，实际为: {nickname}')
            check.is_false(has_add_button, '❌ 搜索自己后异常显示了添加好友按钮')


    @allure.story('搜索')
    @allure.title('搜索已有好友时展示发送消息入口-状态：已完成')
    def test_add_friend_search_existing_friend(self):
        """测试从添加朋友入口搜索已有好友后的按钮状态"""
        with allure.step(f'1. 搜索已有好友 {PRIVATE_USER4.name} 并进入资料详情'):
            self._search_and_open_profile(PRIVATE_USER4.phone)

        with allure.step('2. 校验显示发送消息入口且不显示添加好友按钮'):
            has_send_button = self.contactDetailPage.has_send_message_button()
            has_add_button = self.contactDetailPage.is_add_friend_unfriend_visible()
            check.is_true(has_send_button, '❌ 搜索已有好友后未显示发送消息按钮')
            check.is_false(has_add_button, '❌ 搜索已有好友后异常显示了添加好友按钮')


    @allure.story('申请')
    @allure.title('发送好友验证申请流-状态：已完成')
    def test_add_friend_request_flow(self):
        """测试发起好友申请，填写验证备注信息并发送的完整添加好友申请流"""
        search_key = PRIVATE_USER1.phone
        verify_message = '测试验证信息：你好，我是自动化测试助手。'
        with allure.step('1. 搜索目标账号并跳转到详情页'):
            self._home_to_add_friend()
            self.addFriendPage.search_friend_by_content(search_key)
            self.addFriendPage.click_confirm_search()
            self.addFriendPage.click_search_result_item()

        with allure.step('2. 判断是否已是好友。若是非好友，则发起申请加好友'):
            self.contactDetailPage.click_add_friend_button()

        with allure.step('3. 在发送朋友验证页面，输入备注并提交发送申请'):
            is_loaded = self.addFriendPage.wait_for_send_friend_verify_page()
            check.is_true(is_loaded, '❌ 未能成功进入发送朋友验证页面')
            self.addFriendPage.input_remark(verify_message)
            self.addFriendPage.click_finish()

        with allure.step('4. 校验是否成功发送申请'):
            toast = self.addFriendPage.verify_toast_exist('发送成功')
            check.is_true(toast, '❌ 点击发送好友申请后，未弹出预期 Toast 提示')


    @allure.story('申请')
    @allure.title('重复发送待处理好友申请-状态：已完成')
    def test_add_friend_repeat_pending_request(self):
        """测试同一好友申请待处理时可以再次发送验证信息"""
        verify_messages = ('第一次待处理好友验证申请', '第二次重复好友验证申请')

        for index, verify_message in enumerate(verify_messages, start=1):
            with allure.step(f'1. 第{index}次搜索目标账号并发起好友申请'):
                self.mainPage.go_to_main_page()
                self._search_and_open_profile(PRIVATE_USER1.phone)

                has_add_button = self.contactDetailPage.is_add_friend_unfriend_visible()
                check.is_true(has_add_button, f'❌ 第{index}次申请：未显示添加好友按钮，无法发送')
                
                self.contactDetailPage.click_add_friend_button()
                is_loaded = self.addFriendPage.wait_for_send_friend_verify_page()
                check.is_true(is_loaded, f'❌ 第{index}次申请：未能进入发送朋友验证页面')
                
                self.addFriendPage.input_remark(verify_message)
                self.addFriendPage.click_finish()

            with allure.step(f'2. 校验第{index}次好友申请发送结果'):
                toast = self.addFriendPage.verify_toast_exist('发送成功')
                check.is_true(toast, f'❌ 第{index}次好友申请未发送成功')
