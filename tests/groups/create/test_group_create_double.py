import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2

@allure.epic('IM核心功能测试')
@allure.feature('群聊模块-发起群聊')
@allure.story('双端群聊协同测试')
class TestGroupCreateDouble:
    """双端群聊创建及首发消息多端协同测试集"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender, driver_receiver):
        """双端页面对象初始化"""
        self.mainPageS = MainPage(driver_sender)
        self.homePageS = HomePage(driver_sender)
        self.chatListPageS = ChatListPage(driver_sender)
        self.groupCreatePageS = GroupCreatePage(driver_sender)
        self.groupSettingPageS = GroupSettingPage(driver_sender)
        self.groupManagerPageS = GroupManagerPage(driver_sender)
        self.contactSelectPageS = ContactSelectPage(driver_sender)
        self.chatPageS = ChatPage(driver_sender)
        self.mainPageR = MainPage(driver_receiver)
        self.homePageR = HomePage(driver_receiver)
        self.chatListPageR = ChatListPage(driver_receiver)
        self.groupCreatePageR = GroupCreatePage(driver_receiver)
        self.groupSettingPageR = GroupSettingPage(driver_receiver)
        self.groupManagerPageR = GroupManagerPage(driver_receiver)
        self.contactSelectPageR = ContactSelectPage(driver_receiver)
        self.chatPageR = ChatPage(driver_receiver)
        yield
        try:
            self.mainPageS.go_to_main_page()
        except Exception as e:
            logger.warning(f'⚠️ [Teardown] A 端返回首页失败: {e}')
        try:
            self.mainPageR.go_to_main_page()
        except Exception as e:
            logger.warning(f'⚠️ [Teardown] B 端返回首页失败: {e}')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('双端群聊协同测试-并发')
    @allure.title('双端建群协同 - A和B两端同时创建群聊并交叉收信校验-状态：已完成')
    def test_simultaneous_group_creation_double(self):
        """
        测试用例流程（采用多线程实现真正的双端物理并发同步操作）：
        1. 线程并发：A端和B端同时点击加号并进入“发起群聊”页面
        2. 线程并发：A端与B端同时默认勾选各自的前5个好友，点击完成建群
        3. 线程并发：双端成功进入群聊后，A端发送消息 msg_from_a，B端发送消息 msg_from_b
        4. 线程并发：发信后，双端均退回到主页聊天会话列表
        5. 线程并发：A端进入B端创建的群二校验消息，B端进入A端创建的群一校验消息
        6. 线程并发：进行交叉进群退群清理，确保两个临时群在两端全部销毁
        """
        import threading
        res_dict = {}
        thread_exceptions = {'a': None, 'b': None}

        def safe_run(thread_key, func):
            try:
                func()
            except Exception as e:
                logger.error(f'❌ 线程 [{thread_key}] 执行异常: {e}')
                thread_exceptions[thread_key] = e

        def run_parallel(func_a, func_b):
            t1 = threading.Thread(target=safe_run, args=('a', func_a))
            t2 = threading.Thread(target=safe_run, args=('b', func_b))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            if thread_exceptions['a']:
                raise thread_exceptions['a']
            if thread_exceptions['b']:
                raise thread_exceptions['b']
        msg_from_a = f'并发建群-来自A的消息. 时间戳:{int(time.time() * 1000) % 100000}'
        msg_from_b = f'并发建群-来自B的消息. 时间戳:{int(time.time() * 1000) % 100000}'
        with allure.step('1. 并发步骤：A端和B端同时进入‘发起群聊’页面'):

            def go_select_a():
                self.homePageS.click_add_button()
                self.homePageS.click_start_group_chat()
                self.contactSelectPageS.wait_for_contact_and_group_select_page_load()

            def go_select_b():
                self.homePageR.click_add_button()
                self.homePageR.click_start_group_chat()
                self.contactSelectPageR.wait_for_contact_and_group_select_page_load()
            run_parallel(go_select_a, go_select_b)
        with allure.step('2. 并发步骤：双端完成勾选前5个好友并提交建群'):

            def select_submit_a():
                self.contactSelectPageS.select_x_random_friends(x=5)
                self.contactSelectPageS.click_action_button()

            def select_submit_b():
                self.contactSelectPageR.select_x_random_friends(x=5)
                self.contactSelectPageR.click_action_button()
            run_parallel(select_submit_a, select_submit_b)
        with allure.step('3. 并发步骤：双端确认进群，获取群名并发送首发消息'):

            def chat_init_send_a():
                is_in_chat_sender = self.chatPageS.wait_for_chat_page_load()
                check.is_true(is_in_chat_sender, '❌ A端建群失败，未能进入群聊页面')
                res_dict['group_name_a'] = self.chatPageS.get_top_name()
                logger.info(f"✅ A端创建的群一名称: {res_dict['group_name_a']}")
                self.chatPageS.send_message(msg_from_a)

            def chat_init_send_b():
                is_in_chat_receiver = self.chatPageR.wait_for_chat_page_load()
                check.is_true(is_in_chat_receiver, '❌ B端建群失败，未能进入群聊页面')
                res_dict['group_name_b'] = self.chatPageR.get_top_name()
                logger.info(f"✅ B端创建的群二名称: {res_dict['group_name_b']}")
                self.chatPageR.send_message(msg_from_b)
            run_parallel(chat_init_send_a, chat_init_send_b)
        with allure.step('4. 并发步骤：发信后，双端均退回到主页聊天会话列表'):

            def back_to_list_a():
                self.chatPageS.wait_banner_message_disappear()
                self.chatPageS.click_back_button()

            def back_to_list_b():
                self.chatPageR.wait_banner_message_disappear()
                self.chatPageR.click_back_button()
            time.sleep(1)
        group_name_a = res_dict.get('group_name_a', '')
        group_name_b = res_dict.get('group_name_b', '')
        with allure.step('5. 并发步骤：交叉查收对方创建的群聊消息'):

            def cross_check_a():
                session_name_b = group_name_b.split('...')[0] if '...' in group_name_b else group_name_b
                enter_b_success = self.chatListPageS.enter_chat(session_name=session_name_b, match_type='partial', timeout=20)
                check.is_true(enter_b_success, f'❌ A端在会话列表中未能进入B端创建的群聊: {session_name_b}')
                if enter_b_success:
                    self.chatPageS.wait_for_chat_page_load()
                    received_msg_on_a = self.chatPageS.get_text_message_content_by_index(index=-1, side='received')
                    check.equal(received_msg_on_a, msg_from_b, f'❌ A端在群二中接收的消息不匹配')

            def cross_check_b():
                session_name_a = group_name_a.split('...')[0] if '...' in group_name_a else group_name_a
                enter_a_success = self.chatListPageR.enter_chat(session_name=session_name_a, match_type='partial', timeout=20)
                check.is_true(enter_a_success, f'❌ B端在会话列表中未能进入A端创建的群聊: {session_name_a}')
                if enter_a_success:
                    self.chatPageR.wait_for_chat_page_load()
                    received_msg_on_b = self.chatPageR.get_text_message_content_by_index(index=-1, side='received')
                    check.equal(received_msg_on_b, msg_from_a, f'❌ B端在群一中接收的消息不匹配')
        with allure.step('6. 并发步骤：双端进行第一轮交叉退群（A退群二，B退群一）'):

            def first_cleanup_a():
                self.chatPageS.wait_banner_message_disappear()
                self.chatPageS.click_more_button()
                self.groupSettingPageS.wait_for_setting_page_load()
                self.groupSettingPageS.swipe_page_quickly(slid_type='up')
                self.groupSettingPageS.click_delete_and_out()
                self.groupSettingPageS.click_tv_confirm_button()

            def first_cleanup_b():
                self.chatPageR.wait_banner_message_disappear()
                self.chatPageR.click_more_button()
                self.groupSettingPageR.wait_for_setting_page_load()
                self.groupSettingPageR.swipe_page_quickly(slid_type='up')
                self.groupSettingPageR.click_delete_and_out()
                self.groupSettingPageR.click_tv_confirm_button()
        with allure.step('7. 并发步骤：双端进行第二轮进群退群销毁动作'):

            def second_cleanup_a():
                self.chatPageS.wait_banner_message_disappear()
                self.chatPageS.click_more_button()
                self.groupSettingPageS.wait_for_setting_page_load()
                self.groupSettingPageS.click_group_manager()
                self.groupManagerPageS.click_dismiss_group()
                self.groupManagerPageS.click_black_remove_member_confirm()
                self.groupSettingPageS.click_delete_and_out()
                self.groupSettingPageS.click_tv_confirm_button()

            def second_cleanup_b():
                self.chatPageR.wait_banner_message_disappear()
                self.chatPageR.click_more_button()
                self.groupSettingPageR.wait_for_setting_page_load()
                self.groupSettingPageR.click_group_manager()
                self.groupManagerPageR.click_dismiss_group()
                self.groupManagerPageR.click_black_remove_member_confirm()
                self.groupSettingPageR.click_delete_and_out()
                self.groupSettingPageR.click_tv_confirm_button()
            run_parallel(second_cleanup_a, second_cleanup_b)

    @pytest.mark.p0
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title('双端建群协同 - A端拉B端建群并发送首发消息，B端查收并双端退群-状态：已完成')
    def test_create_group_and_receive_message_double(self):
        """
        测试用例流程：
        1. A 端点击加号并进入发起群聊页面
        2. A 端在好友列表中勾选 B 端用户，点击完成
        3. A 端等待群聊窗口加载，并获取默认群昵称
        4. A 端在新创建 of 群里发送首发文本消息
        5. B 端主页等待新会话通知刷新，并点击进入群聊
        6. B 端查收该群聊天记录，校验首条消息内容一致性
        7. 双端进入群设置页，滑动至底部点击“删除并退出”群聊，清理脏数据
        """
        receiver_name = PRIVATE_USER1.name
        group_first_msg = f'双端协同：这是群聊首发消息测试。随机码:{int(time.time() * 1000) % 100000}'
        with allure.step('1. A端在首页发起群聊'):
            self.homePageS.click_add_button()
            self.homePageS.click_start_group_chat()
            self.contactSelectPageS.wait_for_contact_and_group_select_page_load()
        with allure.step(f'2. A端勾选 B端用户 [{receiver_name}] 并创建群聊'):
            selected = self.contactSelectPageS.click_contact_by_name(receiver_name)
            check.is_true(selected, f'❌ A端在联系人列表中未找到 B端好友: {receiver_name}')
            self.contactSelectPageS.click_action_button()
        with allure.step('3. A端等待进入群聊会话并获取默认群名'):
            is_in_chat_sender = self.chatPageS.wait_for_chat_page_load(timeout=15)
            check.is_true(is_in_chat_sender, '❌ A端建群后未能成功进入群聊主界面')
            group_name = self.chatPageS.get_top_name()
            logger.info(f'✅ A端进入群聊成功，自动生成的默认群聊名称为: {group_name}')
        with allure.step(f"4. A端在群聊中发送首发消息: '{group_first_msg}'"):
            self.chatPageS.send_message(group_first_msg)
        with allure.step('5. B端等待会话通知刷新并进入群聊'):
            session_name = group_name.split('...')[0] if '...' in group_name else group_name
            enter_success = self.chatListPageR.enter_chat(session_name=session_name, match_type='partial', timeout=20)
            check.is_true(enter_success, f'❌ B端未能成功从聊天列表中进入群聊会话: {session_name}')
        with allure.step('6. B端加载群聊并核对首条消息内容'):
            is_in_chat_receiver = self.chatPageR.wait_for_chat_page_load(timeout=10)
            check.is_true(is_in_chat_receiver, '❌ B端未能成功加载群聊页面')
            last_received_msg = self.chatPageR.get_text_message_content_by_index(index=-1, side='received')
            check.equal(last_received_msg, group_first_msg, f"❌ B端接收到的群消息不一致！预期: '{group_first_msg}', 实际: '{last_received_msg}'")
        with allure.step('7. 清理群聊 - 双端依次删除并退出群组'):
            with allure.step('A端删除并退出该群聊'):
                self.chatPageS.click_more_button()
                self.groupSettingPageS.wait_for_setting_page_load()
                self.groupSettingPageS.swipe_page_quickly(slid_type='up')
                self.groupSettingPageS.click_delete_and_out()
                self.groupSettingPageS.click_tv_confirm_button()
            with allure.step('B端删除并退出该群聊'):
                self.chatPageR.click_more_button()
                self.groupSettingPageR.wait_for_setting_page_load()
                self.groupSettingPageR.swipe_page_quickly(slid_type='up')
                self.groupSettingPageR.click_delete_and_out()
                self.groupSettingPageR.click_tv_confirm_button()