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
from pages.chat.call.call_page import CallPage
from pages.chat.mention.chat_mention_page import ChatMentionPage
from strategy.chat.chat_strategy import (
    PRIVATE_USER1, 
    PRIVATE_USER2,
    PRIVATE_USER3, 
    GROUP_STRATEGY,
    GROUP_STRATEGY2,
    CHAT_CALL_DOUBLE_SCENARIOS
)



SENDER_NAME = PRIVATE_USER3.name
RECEIVER_NAME = PRIVATE_USER1.name
INVITE_USER = PRIVATE_USER2.name


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
        self.chatMentionS = ChatMentionPage(driver_sender)
        self.groupSettingS = GroupSettingPage(driver_sender)
        self.groupManagerS = GroupManagerPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.homeR = HomePage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatPanelR = ChatPanelPage(driver_receiver)
        self.callR = CallPage(driver_receiver)
        self.chatMentionR = ChatMentionPage(driver_receiver)
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
                logger.info("⚡ [Action-Call] 主叫自己主动挂断/取消呼叫")
                self.callS.hangup()
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
            elif call_strategy.action == "reject":
                logger.info("⚡ [Action-Call] 被叫拒绝通话")
                self.callR.wait_incoming_call_page_load()
                self.callR.reject()
                time.sleep(1)
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
                self.homeR.wait_home_page()
            elif call_strategy.action == "accept":
                logger.info("⚡ [Action-Call] 被叫接听通话，维持产生时长后由主叫主动挂断")
                self.callR.wait_incoming_call_page_load()
                self.callR.accept()
                time.sleep(2)
                self.callS.hangup()
                time.sleep(1)
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
                self.homeR.wait_home_page()
            elif call_strategy.action == "timeout":
                logger.info("⚡ [Action-Call] 主被超时：被叫保持振铃未接听，等待超时后主叫自动退回聊天页")
                self.callR.wait_incoming_call_page_load()
                self.chatS.wait_for_chat_page_load(timeout=65)
                self.chatS.click_back_button()
                self.homeS.wait_home_page()
                self.homeR.wait_home_page()
            elif call_strategy.action == "interrupt":
                logger.info("⚡ [Action-Call] 双方接通后切断主叫端网络，模拟通话中断")
                self.callR.wait_incoming_call_page_load()
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
            candidates_s = call_strategy.expected_s_candidates
            actual_content_s = self.homeS.get_message_by_name(RECEIVER_NAME, expected_text=candidates_s, timeout=10)
            matched_s = any(cand in actual_content_s for cand in candidates_s)
            check.is_true(matched_s, f'❌ 主叫端会话内容展示不匹配, 预期满足 {candidates_s} 之一, 实际为: {actual_content_s}')

        with allure.step(f'4. 验证被叫端会话列表展示包含: {call_strategy.expected_text_r}'):
            candidates_r = call_strategy.expected_r_candidates
            actual_content_r = self.homeR.get_message_by_name(SENDER_NAME, expected_text=candidates_r, timeout=10)
            matched_r = any(cand in actual_content_r for cand in candidates_r)
            check.is_true(matched_r, f'❌ 被叫端会话内容展示不匹配, 预期满足 {candidates_r} 之一, 实际为: {actual_content_r}')


    @allure.story('群聊进群邀请双端协同展示')
    @allure.title('双端群聊进群邀请展示-状态：已完成')
    def test_chat_group_invite_double_status(self):
        """【双端协同】验证群聊邀请成员加入群聊后，双端会话列表摘要呈现【[群邀请确认]】"""
        target_group = GROUP_STRATEGY2.name
        expected_text = "[群邀请确认]"

        with allure.step(f'1. 发送端进入群聊【{target_group}】并打开群设置'):
            self.chatListS.enter_chat(target_group)
            self.chatS.wait_for_chat_page_load()
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            friend_names = self.groupSettingS.get_friend_names()
            if RECEIVER_NAME in friend_names:
                logger.info(f"ℹ️ 检测到群成员中已存在接收端【{RECEIVER_NAME}】，执行移出群聊前置清理...")
                self.groupSettingS.click_remove_friend_header()
                self.groupManagerS.click_member_by_search_keyword(name=RECEIVER_NAME)
                self.groupManagerS.click_edit_finish_button()
        
        with allure.step(f'2. 在群成员管理中邀请接收端【{RECEIVER_NAME}】并完成提交'):
            self.groupSettingS.click_add_friend_header()
            self.groupManagerS.click_member_by_search_keyword(name=RECEIVER_NAME)
            self.groupManagerS.click_edit_finish_button()
            self.chatS.wait_banner_message_disappear()

        with allure.step('3. 发送端安全退回首页，确保双端主页面加载就绪'):
            self.mainS.go_to_main_page()
            self.homeS.wait_home_page()
            self.homeR.wait_home_page()

        with allure.step(f'4. 验证接收端在与【{PRIVATE_USER3.name}】私聊会话列表中展示包含: {expected_text}'):
            actual_content_r = self.homeR.get_message_by_name(PRIVATE_USER3.name, expected_text=expected_text, timeout=10)
            logger.info(f"接收端与【{PRIVATE_USER3.name}】私聊会话摘要内容: 实际='{actual_content_r}', 预期包含='{expected_text}'")
            check.is_in(expected_text, actual_content_r, 
                        f'❌ 接收端与【{PRIVATE_USER3.name}】私聊会话内容展示不匹配, 预期包含: {expected_text}, 实际为: {actual_content_r}')

        with allure.step(f'5. 接收端进入与【{PRIVATE_USER3.name}】的私聊会话验证收到的群邀请确认消息'):
            self.chatListR.enter_chat(PRIVATE_USER3.name)
            self.chatR.wait_for_chat_page_load()

            invite_msg_text = ""
            try:
                invite_msg_elem = self.chatR.get_last_message_content_element()
                invite_msg_text = (invite_msg_elem.get_attribute("text") or invite_msg_elem.text or "").strip()
            except Exception:
                pass

            if not invite_msg_text:
                all_texts = self.chatR.get_all_text_message_contents(side="all")
                if all_texts:
                    invite_msg_text = all_texts[-1]
                else:
                    invite_msg_text = self.chatR.get_cmd_notification_texts(index=-1) or ""

            logger.info(f"接收端私聊会话内部捕获群邀请确认消息内容: '{invite_msg_text}'")
            is_invite_valid = any(kw in invite_msg_text for kw in [target_group, "邀请你加入群聊", expected_text])
            check.is_true(is_invite_valid, 
                        f'❌ 接收端私聊会话内未检测到有效的群邀请确认消息, 实际内容为: {invite_msg_text}')
            self.chatR.click_back_button()
            self.homeR.wait_home_page()


    @allure.story('群聊@强提醒与核销双端协同')
    @allure.title('群聊@强提醒生命周期验证 (有人@我 / @所有人 / 已读核销)')
    @pytest.mark.parametrize('at_type, expected_tag', [
        pytest.param('at_me', '[有人@我]', id='有人@我强提醒'),
        pytest.param('at_all', '[@所有人]', id='@所有人全员强提醒'),
    ])
    def test_chat_group_mention_remind_lifecycle(self, at_type: str, expected_tag: str):
        """【双端协同】验证群聊@强提醒触发及进入查看后标签即时消除的闭环流转"""
        allure.dynamic.title(f'群聊@强提醒协同 | {expected_tag} 触发与已读核销闭环')
        group_name = GROUP_STRATEGY.name
        tag_keyword = expected_tag.strip("[]")
        target_desc = f"成员【{RECEIVER_NAME}】" if at_type == 'at_me' else "【所有人】"

        with allure.step(f'1. 发送端进入群聊【{group_name}】并通过输入@选择{target_desc}发送强提醒'):
            self.chatListS.enter_chat(group_name)
            self.chatS.wait_for_chat_page_load()
            self.chatS.mention_and_send(target=at_type, member_name=RECEIVER_NAME, append_text="自动化测试")
            self.chatListS.click_back_button()
            self.homeS.wait_home_page()

        with allure.step(f'2. 接收端在首页验证群聊呈现强提醒标签: {expected_tag}'):
            actual_tag = self.homeR.get_remind_status_by_name(group_name, timeout=10)
            logger.info(f"接收端群聊 [{group_name}] 提醒标签: 实际='{actual_tag}', 预期包含='{tag_keyword}'")
            check.is_in(tag_keyword, actual_tag, f'❌ 接收端群会话提醒标签不匹配, 预期包含: {expected_tag}, 实际为: {actual_tag}')

        with allure.step('3. 接收端进入群聊查看消息，触发强提醒已读清除'):
            self.chatListR.enter_chat(group_name)
            self.chatR.wait_for_chat_page_load()
            self.chatListR.click_back_button()
            self.homeR.wait_home_page()

        with allure.step(f'4. 接收端返回首页，验证【{expected_tag}】强提醒已消失'):
            refreshed_tag = self.homeR.get_remind_status_by_name(group_name, timeout=3)
            logger.info(f"已读消除后接收端群聊 [{group_name}] 提醒标签刷新为: '{refreshed_tag}'")
            check.is_not_in(tag_keyword, refreshed_tag, f'❌ 查看消息返回后强提醒未能清除, 依然包含: {expected_tag}')


    @allure.story('群聊系统通知双端展示')
    @allure.title('双端群聊系统通知展示-新成员加入群聊摘要呈现')
    def test_chat_group_join_notify_status(self):
        """【双端协同】验证群聊新成员入群系统通知在会话列表呈现正确文本摘要【加入了群聊】"""
        group_name = GROUP_STRATEGY.name
        expected_content = "加入了群聊"

        with allure.step(f'1. 发送端进入群聊【{group_name}】并发送包含入群关键词的消息'):
            self.chatListS.enter_chat(group_name)
            self.chatS.wait_for_chat_page_load()
            self.chatS.send_message(f"欢迎新成员{expected_content}")
            self.chatListS.click_back_button()
            self.homeS.wait_home_page()

        with allure.step(f'2. 接收端在首页验证群聊会话摘要包含: {expected_content}'):
            actual_content = self.homeR.get_message_by_name(group_name, expected_text=expected_content, timeout=10)
            logger.info(f"接收端群聊 [{group_name}] 消息摘要内容: 实际='{actual_content}', 预期包含='{expected_content}'")
            check.is_in(expected_content, actual_content, f'❌ 接收端群会话消息内容不匹配, 预期包含: {expected_content}, 实际为: {actual_content}')


    @allure.story('群聊进群申请与权限边界')
    @allure.title('验证进群申请强提醒在不同权限角色下的可见性')
    def test_chat_group_apply_permission_and_composite_status(self):
        """【双端协同】验证进群申请强提醒的权限隔离边界（群主端可见 / 普通成员端不可见）：
        1. 发送端（群主）进入群管理，判断并确保【进群验证】开关处于开启状态后返回首页；
        2. 接收端（普通成员）进入群设置邀请人员进群，由于进群验证已开启，触发生成进群申请；
        3. 接收端（普通成员）退回首页，验证无权限看到【[进群申请]】强提醒标签；
        4. 发送端（群主）在首页验证成功捕获【[进群申请]】强提醒标签。
        """
        group_name = GROUP_STRATEGY.name
        expected_tag = "[入群申请]"
        tag_keyword = expected_tag.strip("[]")

        with allure.step(f'1. 发送端(群主)进入群聊【{group_name}】群管理，检查并确保【进群验证】开关开启'):
            self.chatListS.enter_chat(group_name)
            self.chatS.wait_for_chat_page_load()
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load()
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_page_load()

            self.groupManagerS.click_join_group_verify_switch()
            self.mainS.go_to_main_page()
            self.homeS.wait_home_page()

        with allure.step(f'2. 接收端(普通成员)进入群聊【{group_name}】群设置，邀请【{INVITE_USER}】产生进群申请'):
            self.chatListR.enter_chat(group_name)
            self.chatR.wait_for_chat_page_load()
            self.chatR.click_more_button()
            self.groupSettingR.wait_for_setting_page_load()
            self.groupSettingR.click_add_friend_header(is_admin=False)
            self.groupManagerR.click_member_by_search_keyword(name=INVITE_USER)
            self.groupManagerR.click_edit_finish_button()
            self.groupSettingR.input_remark_content('申请入群')
            self.groupSettingR.click_tv_confirm_button()
            self.mainR.go_to_main_page()
            self.homeR.wait_home_page()

        with allure.step(f'3. 接收端(普通成员)在首页验证无【{tag_keyword}】强提醒权限'):
            actual_tag_r = self.homeR.get_remind_status_by_name(group_name, timeout=1)
            logger.info(f"接收端(普通成员)群聊 [{group_name}] 首页提醒标签: '{actual_tag_r}'")
            check.is_not_in(tag_keyword, actual_tag_r, 
                            f'❌ 接收端(普通成员)无审批权限却显示了进群申请强提醒: {actual_tag_r}')

        with allure.step(f'4. 发送端(群主)在首页验证展示【{expected_tag}】强提醒'):
            actual_tag_s = self.homeS.get_remind_status_by_name(group_name, timeout=2)
            logger.info(f"发送端(群主)群聊 [{group_name}] 首页提醒标签: '{actual_tag_s}'")
            check.is_in(tag_keyword, actual_tag_s, 
                        f'❌ 发送端(群主)在成员提交进群申请后未检测到【{expected_tag}】强提醒, 实际展示为: {actual_tag_s}')




