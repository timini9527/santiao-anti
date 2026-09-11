import time
import allure
import pytest
import concurrent.futures
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_panel_page import ChatPanelPage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat.core.call_page import CallPage
from strategy.chat.chat_strategy import (
    PRIVATE_USER1, 
    PRIVATE_USER3, 
    GROUP_STRATEGY,
    CHAT_CONTENT_DOUBLE_SCENARIOS,
    CHAT_CALL_DOUBLE_SCENARIOS,
    CHAT_GROUP_CONTENT_SCENARIOS
)



SENDER_NAME = PRIVATE_USER3.name
RECEIVER_NAME = PRIVATE_USER1.name


@allure.epic('IM核心功能测试')
@allure.feature('聊天模块-会话列表双端协同')
class TestChatListDouble:
    """
    会话列表双端协同自动化测试集
    覆盖完整的端到端长连接生命周期与跨端协同：
    1. 消息阅读回执全生命周期 (未读 -> 已读)
    2. 音视频通话、进群邀请等双向交互在双方会话列表的摘要展示
    """

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象并确保双端就绪处于首页"""
        self.mainS = MainPage(driver_sender)
        self.homeS = HomePage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatPanelS = ChatPanelPage(driver_sender)
        self.callS = CallPage(driver_sender)
        self.groupSettingS = GroupSettingPage(driver_sender)
        self.groupManagerS = GroupManagerPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.homeR = HomePage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatPanelR = ChatPanelPage(driver_receiver)
        self.callR = CallPage(driver_receiver)
        self.groupSettingR = GroupSettingPage(driver_receiver)
        self.groupManagerR = GroupManagerPage(driver_receiver)

        with allure.step('前置准备：确认双端均安全返回并就绪于首页'):
            for main_page, side_desc in [(self.mainS, '发送端'), (self.mainR, '接收端')]:
                try:
                    main_page.go_to_main_page()
                except Exception as e:
                    logger.warning(f'⚡ [Setup] {side_desc} 返回首页异常: {e}')

        yield

        with allure.step('后置清理：双端安全返回首页'):
            for main_page, side_desc in [(self.mainS, '发送端'), (self.mainR, '接收端')]:
                try:
                    main_page.go_to_main_page()
                except Exception as e:
                    logger.error(f'❌ [Teardown] {side_desc} 清理返回首页失败: {e}')




    @allure.story('消息阅读回执状态机流转 (未读 -> 已读)')
    @allure.title('验证私聊消息阅读回执全生命周期流转 (未读 -> 已读)')
    def test_message_read_receipt_lifecycle(self):
        """ 双端闭环】验证发送端发消息后即刻未读，接收端阅读后发送端自适应刷新为已读 """
        test_msg = f'已读未读状态测试_{int(time.time())}'

        with allure.step(f'1. 发送端进入与【{RECEIVER_NAME}】的会话并发送消息'):
            self.chatListS.enter_chat(RECEIVER_NAME)
            self.chatS.wait_for_chat_page_load()
            self.chatS.send_message(test_msg)
            sent_bubble = self.chatListS.find_sent_message_by_bubble(test_msg)
            check.equal(sent_bubble, test_msg, f'❌ 发送端气泡内容校验不匹配, 实际为: {sent_bubble}')

        with allure.step('2. 发送端返回首页会话列表，断言消息即时呈现【未读】状态'):
            self.chatS.click_back_button()
            self.homeS.wait_home_page()
            initial_status = self.homeS.get_unread_status(RECEIVER_NAME)
            check.is_in('未读', initial_status, f'❌ 初始阅读状态异常，预期包含【未读】，实际为: {initial_status}')

        with allure.step(f'3. 接收端在首页打开与【{SENDER_NAME}】的会话，触发已读回执上报'):
            self.chatListR.enter_chat(SENDER_NAME)
            self.chatR.wait_for_chat_page_load()

        with allure.step('4. 发送端在首页显式等待长连接回执推送，验证阅读状态流转为【已读】'):
            is_read_synced = self.homeS.wait_for_read_status(RECEIVER_NAME, '已读', timeout=10)
            check.is_true(is_read_synced, f'❌ 发送端未能在超时时间内接收到【已读】状态更新')
            final_status = self.homeS.get_unread_status(RECEIVER_NAME)
            check.is_in('已读', final_status, f'❌ 最终阅读状态不匹配，预期包含【已读】，实际为: {final_status}')

        with allure.step('5. 接收端退出会话，恢复首页待命状态'):
            self.chatR.click_back_button()
            self.homeR.wait_home_page()


    @allure.story('音视频通话双端协同会话列表展示')
    @allure.title('双端音视频通话状态展示-状态：已完成')
    @pytest.mark.parametrize('call_strategy', [pytest.param(x, id=x.desc) for x in CHAT_CALL_DOUBLE_SCENARIOS])
    def test_chat_call_double_status(self, call_strategy):
        """
        【双端协同】验证音视频通话（视频/语音）在不同交互终态下，双端会话列表展示正确的状态文本：
        1. 主叫挂断 -> 主叫会话显示【已取消】，被叫会话显示【对方已取消】
        2. 被叫拒绝 -> 主叫会话显示【对方已拒绝】，被叫会话显示【已拒绝】
        3. 通话接通 -> 主叫会话显示【通话时长】，被叫会话显示【通话结束】
        4. 主被超时 -> 主叫会话显示【对方无应答】，被叫会话显示【未接来电】
        5. 通话中断 -> 双方断网，双方会话显示【通话中断】
        """
        allure.dynamic.title(f'双端通话会话状态 | {call_strategy.desc}')

        with allure.step(f'1. 发送端发起【{call_strategy.call_type}】呼叫'):
            self.chatListS.enter_chat(RECEIVER_NAME)
            self.chatS.wait_for_chat_page_load()
            self.chatS.click_add_button()
            self.chatPanelS.initiate_call_by_type(call_strategy.call_type)

        with allure.step(f'2. 执行【{call_strategy.desc}】交互信令与动作'):
            if call_strategy.action == "cancel":
                # 2.1 主叫自己主动挂断/取消呼叫
                self.callS.hangup()
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
            elif call_strategy.action == "reject":
                # 2.2 被叫拒绝通话
                self.callR.wait_incoming_call_page_load(timeout=10)
                self.callR.reject()
                time.sleep(1)
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
                self.homeR.wait_home_page()
            elif call_strategy.action == "accept":
                # 2.3 被叫接听通话，维持产生时长后由主叫主动挂断
                self.callR.wait_incoming_call_page_load(timeout=10)
                self.callR.accept()
                time.sleep(2)
                self.callS.hangup()
                time.sleep(1)
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
                self.homeR.wait_home_page()
            elif call_strategy.action == "timeout":
                # 2.4 主被超时：被叫保持振铃未接听，等待超时后主叫自动退回聊天页
                self.callR.wait_incoming_call_page_load(timeout=10)
                self.chatS.wait_for_chat_page_load(timeout=65)
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
                self.homeR.wait_home_page()
            elif call_strategy.action == "interrupt":
                # 2.5 通话中断：双方接通后进行断网，触发通话中断
                self.callR.wait_incoming_call_page_load(timeout=10)
                self.callR.accept()
                time.sleep(2)
                try:
                    logger.info("⚡ [Action-Call] 双方接通后切断主叫端网络，模拟通话中断...")
                    self.callS.set_network_connection("none")
                    # self.callR.set_network_connection("none")
                    logger.info("⏳ [Action-Call] 双端并发检测通话中断退出...")
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                        future_s = executor.submit(self.chatS.wait_for_chat_page_load, 35)
                        future_r = executor.submit(self.callR.wait_call_page_close, 35)
                        future_s.result()
                        future_r.result()
                finally:
                    logger.info("⚡ [Action-Call] 恢复主叫端网络连接...")
                    self.callS.set_network_connection("all")
                    # self.callR.set_network_connection("all")
                time.sleep(1)
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
                self.homeR.wait_home_page()



        with allure.step(f'3. 验证主叫端会话列表展示包含: {call_strategy.expected_text_s}'):
            actual_content_s = self.homeS.get_message_by_name(RECEIVER_NAME, expected_text=call_strategy.expected_text_s)
            check.is_in(call_strategy.expected_text_s, actual_content_s, 
                        f'❌ 主叫端会话内容展示不匹配, 预期包含: {call_strategy.expected_text_s}, 实际为: {actual_content_s}')

        with allure.step(f'4. 验证被叫端会话列表展示包含: {call_strategy.expected_text_r}'):
            actual_content_r = self.homeR.get_message_by_name(SENDER_NAME, expected_text=call_strategy.expected_text_r)
            check.is_in(call_strategy.expected_text_r, actual_content_r, 
                        f'❌ 被叫端会话内容展示不匹配, 预期包含: {call_strategy.expected_text_r}, 实际为: {actual_content_r}')



    @allure.story('群聊进群邀请双端协同展示')
    @allure.title('双端群聊进群邀请展示-状态：已完成')
    def test_chat_group_invite_double_status(self):
        """【双端协同】验证群聊邀请成员加入群聊后，双端会话列表摘要呈现【[进群邀请]】"""
        target_group = GROUP_STRATEGY.name
        expected_text = "[进群邀请]"

        with allure.step(f'1. 发送端在群聊【{target_group}】设置中发起邀请接收端【{RECEIVER_NAME}】并返回首页'):
            self.chatListS.enter_chat(target_group)
            self.chatS.wait_for_chat_page_load()
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_add_friend_header()
            self.groupManagerS.click_member_by_search_keyword(name=RECEIVER_NAME)
            self.groupManagerS.click_edit_finish_button()
            time.sleep(1)
            self.mainS.go_to_main_page()
            self.homeS.wait_home_page()
            self.homeR.wait_home_page()

        with allure.step(f'2. 验证发送端群聊会话列表展示包含: {expected_text}'):
            actual_content_s = self.homeS.get_message_by_name(target_group, expected_text=expected_text, timeout=10)
            check.is_in(expected_text, actual_content_s, 
                        f'❌ 发送端群聊会话内容展示不匹配, 预期包含: {expected_text}, 实际为: {actual_content_s}')

        with allure.step(f'3. 验证接收端群聊会话列表展示包含: {expected_text}'):
            actual_content_r = self.homeR.get_message_by_name(target_group, expected_text=expected_text, timeout=10)
            check.is_in(expected_text, actual_content_r, 
                        f'❌ 接收端群聊会话内容展示不匹配, 预期包含: {expected_text}, 实际为: {actual_content_r}')




    @allure.story('群聊会话内容与强提醒双端协同展示')
    @allure.title('群聊会话状态双端协同-状态：已完成')
    @pytest.mark.parametrize('remind_strategy', [pytest.param(x, id=x.desc) for x in CHAT_GROUP_CONTENT_SCENARIOS])
    def test_chat_group_content_double_status(self, remind_strategy):
        """
        【双端协同】验证群聊特有会话状态（进群申请、入群系统通知、有人@我、@所有人、已读消除、复合提醒）
        发送端(端A/SENDER)触发信令与动作，接收端(端B/RECEIVER)在首页会话列表中验证强提醒标签与消息摘要展示及核销
        """
        allure.dynamic.title(f'群聊会话状态双端协同 | {remind_strategy.desc}')
        group_name = GROUP_STRATEGY.name

        try:
            # 1. 发送端 (端A) 进入群聊并根据策略触发动作
            with allure.step(f'1. 发送端【{SENDER_NAME}】进入群聊【{group_name}】并触发【{remind_strategy.desc}】'):
                self.chatListS.enter_chat(group_name)
                self.chatS.wait_for_chat_page_load()

                if remind_strategy.remind_type == "at_me":
                    self.chatS.send_message(f"@{RECEIVER_NAME} 有人艾特自动化测试")
                elif remind_strategy.remind_type == "at_all":
                    self.chatS.send_message("@所有人 全员通知自动化测试")
                elif remind_strategy.remind_type == "join_notify":
                    self.chatS.send_message("欢迎新成员加入群聊")
                elif remind_strategy.remind_type == "apply":
                    self.chatS.send_message("申请加入群聊测试")
                elif remind_strategy.remind_type == "both_apply_and_at":
                    self.chatS.send_message(f"@{RECEIVER_NAME} 进群申请审批提醒")

                self.chatListS.click_back_button()
                self.homeS.wait_home_page()

            # 2. 接收端 (端B) 在首页会话列表中校验强提醒标签或消息内容展示
            with allure.step(f'2. 接收端【{RECEIVER_NAME}】在首页验证群聊【{group_name}】展示 (权限约束: {remind_strategy.required_role})'):
                actual_tag = self.homeR.get_remind_status_by_name(group_name)

                # 进群申请权限边界断言：普通成员无权限不可见 [进群申请]
                if remind_strategy.remind_type == "apply" and remind_strategy.required_role == "member":
                    logger.info(f"接收端为普通成员，校验进群申请提醒不可见，实际标签: '{actual_tag}'")
                    check.is_not_in("进群申请", actual_tag, f'❌ 普通成员无权限却显示了进群申请强提醒: {actual_tag}')
                elif remind_strategy.expected_tag:
                    tag_keyword = remind_strategy.expected_tag.strip("[]")
                    logger.info(f"接收端群聊 [{group_name}] 提醒标签: 实际='{actual_tag}', 预期包含='{tag_keyword}'")
                    check.is_in(tag_keyword, actual_tag, f'❌ 接收端群会话提醒标签不匹配, 预期包含: {remind_strategy.expected_tag}, 实际为: {actual_tag}')

                # 校验会话消息内容文本（如 "加入了群聊"）
                if remind_strategy.expected_content:
                    actual_content = self.homeR.get_message_by_name(group_name, expected_text=remind_strategy.expected_content)
                    logger.info(f"接收端群聊 [{group_name}] 消息内容: 实际='{actual_content}', 预期包含='{remind_strategy.expected_content}'")
                    check.is_in(remind_strategy.expected_content, actual_content, f'❌ 接收端群会话消息内容不匹配, 预期包含: {remind_strategy.expected_content}, 实际为: {actual_content}')

            # 3. 若标记了“查看后强提醒消除”，验证已读核销闭环
            if remind_strategy.check_disappear_after_enter:
                with allure.step(f'3. 接收端【{RECEIVER_NAME}】进入群聊查看消息，触发强提醒已读清除'):
                    self.chatListR.enter_chat(group_name)
                    self.chatR.wait_for_chat_page_load()
                    time.sleep(1)
                    self.chatListR.click_back_button()
                    self.homeR.wait_home_page()

                with allure.step(f'4. 接收端返回首页，验证【{remind_strategy.expected_tag}】强提醒已消失'):
                    refreshed_tag = self.homeR.get_remind_status_by_name(group_name)
                    tag_keyword = remind_strategy.expected_tag.strip("[]")
                    logger.info(f"已读消除后接收端群聊 [{group_name}] 提醒标签刷新为: '{refreshed_tag}'")
                    check.is_not_in(tag_keyword, refreshed_tag, f'❌ 查看消息返回后强提醒未能清除, 依然包含: {remind_strategy.expected_tag}')

        finally:
            with allure.step('双端环境自愈：确保双方均安全退回主页面就绪'):
                for main_page, desc in [(self.mainS, '发送端'), (self.mainR, '接收端')]:
                    try:
                        main_page.go_to_main_page()
                    except Exception as e:
                        logger.warning(f'双端环境清理退回首页异常 [{desc}]: {e}')


