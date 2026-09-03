import allure
import pytest
import pytest_check as check
import time
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.main.main_page import MainPage
from pages.chat_options.location.chat_position_page import ChatPositionPage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data, load_csv_data
from strategy.chat.chat_strategy import (
    PRIVATE_USER1,
    PRIVATE_USER2,
    PRIVATE_USER8,
    GROUP_STRATEGY,
    GROUP_STRATEGY2,
    GROUP_STRATEGY3,
    GROUP_STRATEGY4,
    GROUP_STRATEGY5,
    TEST_GROUPS,
    TEST_PRIVATE_USERS
)



CHAT_DATA = load_yaml_data('chat/chat.yaml').get('test_data')
CHAT_CSV_DATA = load_csv_data('chat/chat_messages.csv')



# @pytest.mark.usefixtures('message_page')
@allure.epic('IM核心功能测试')
@allure.feature('聊天模块-单聊基础：已完成')
@allure.story('发送 Text 消息，验证')
class TestChat:
    _in_chat = False
    _chat_target = None
    _class_driver = None

    @classmethod
    def teardown_class(cls):
        """
        整个测试类所有测试方法执行完毕后的最终清理（类级别 teardown）
        强制关闭会话锁并退回主页，确保对其他测试模块完全隔离不造成干扰
        """
        if cls._in_chat and cls._class_driver:
            try:
                logger.info('🧹 [Class Teardown] 整个测试类执行结束，强制释放会话锁并退回主页')
                cls._in_chat = False
                cls._chat_target = None
                main_page = MainPage(cls._class_driver)
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f'[Class Teardown] 最终返回主页失败: {e}')

    @pytest.fixture(autouse=False)
    def setup(self, driver_sender, message_page, request):
        """仅用于 test_send_text_message 的专属前置初始化"""
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage_sender = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.emojiPage = ChatEmojiPage(driver_sender)
        self.chatImagePage = ChatImagePage(driver_sender)
        self.chatPositionPage = ChatPositionPage(driver_sender)
        self.__class__._class_driver = driver_sender
        yield
        if self.__class__._in_chat:
            logger.info(f'🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页')
            return
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f'Teardown 失败，未能返回首页: {e}')

    def _enter_chat(self, chat_name: str):
        """进入指定的聊天会话（支持同会话直接复用，跨会话自动退回主页重新进入）"""
        if self.__class__._chat_target != chat_name:
            if self.__class__._in_chat:
                logger.info(f'🔄 [Lock] 检测到聊天目标从 {self.__class__._chat_target} 切换为 {chat_name}，退回主页重新进入')
                try:
                    self.mainPage.go_to_main_page()
                except Exception as e:
                    logger.error(f'⚠️ [Error] 切换会话退回主页失败: {e}')
            self.__class__._in_chat = False
            self.__class__._chat_target = chat_name
        if not self.__class__._in_chat:
            self.chatListPage_sender.enter_chat(chat_name)
            self.__class__._in_chat = True
            logger.info(f'🔓 [Lock] 已成功进入与 {chat_name} 的聊天，会话保持锁开启')




    @allure.story('发送 Text 消息')
    @allure.title('发送 Text 消息，状态：已完成')
    @pytest.mark.parametrize('text_message', [pytest.param(x, id=str(x)) for x in CHAT_DATA.get('text_message')])
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式'), pytest.param(GROUP_STRATEGY, id='群聊模式')])
    def test_send_text_message(self, text_message, strategy, setup):
        """  用例名称：发送文本消息测试  """
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        try:
            with allure.step(f"1. 进入与【{strategy.name}】的聊天会话"):
                self._enter_chat(strategy.name)
            with allure.step(f"2. 发送文本消息"):
                self.chatPage.send_message(payload)
            with allure.step("3. 校验消息回显内容"):
                text = self.chatPage.get_text_message_content_by_index(index=-1, side='sent')
                check.equal(text, expected, f'消息 actual: {text}, expected: {expected} 不匹配')
        except Exception as e:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
            logger.error(f'⚠️ [Error] 发送消息或校验失败，释放会话锁以进行 Teardown 重置: {e}')
            raise e


    @allure.story('发送 CSV Text 消息')
    @allure.title('基于 CSV 数据集批量连续发送文本消息-状态：已完成')
    @pytest.mark.parametrize('strategy', [pytest.param(PRIVATE_USER1, id='私聊模式')])
    def test_send_text_message_multiple(self, strategy, setup):
        """用例名称：基于 CSV 数据集批量连续发送文本消息（单条用例展示，内容附带 Case ID）"""
        try:
            with allure.step(f"1. 进入与【{strategy.name}】的聊天会话"):
                self._enter_chat(strategy.name)

            with allure.step(f"2. 极速批量发送 CSV 中的文本消息集（共 {len(CHAT_CSV_DATA)} 条，内容携带 ID）"):
                payloads = [
                    f"[{msg_item.get('case_id', f'MSG_CASE_{idx+1:04d}')}] {str(msg_item.get('context', ''))}"
                    for idx, msg_item in enumerate(CHAT_CSV_DATA)
                ]
                self.chatPage.send_messages_batch(payloads, interval=0.4)
        except Exception as e:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
            logger.error(f'⚠️ [Error] 发送消息或校验失败，释放会话锁以进行 Teardown 重置: {e}')
            raise e


    @pytest.fixture(autouse=False)
    def setup_test(self, request):
        for idx in range(5, 10):
            try:
                driver = request.getfixturevalue(f'driver_device{idx}')
                if driver:
                    setattr(self, f'chatPageT{idx}', ChatPage(driver))
                    setattr(self, f'chatListPageT{idx}', ChatListPage(driver))
                    setattr(self, f'mainPageT{idx}', MainPage(driver))
                    setattr(self, f'emojiPageT{idx}', ChatEmojiPage(driver))
                    setattr(self, f'chatImagePageT{idx}', ChatImagePage(driver))
                    setattr(self, f'chatPositionPageT{idx}', ChatPositionPage(driver))
                    self.__class__._class_driver = driver
            except Exception as e:
                logger.warning(f'⚠️ [Setup Test] 设备 driver_device{idx} 启动失败 (对应的 Appium 服务可能未开启): {e}')
        current_test = request.node.originalname or request.node.name
        if 'test_send_text_message' not in current_test:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
        yield
        if self.__class__._in_chat:
            logger.info(f'🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页')
            return
        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f'Teardown 失败，未能返回首页: {e}')


    @pytest.fixture(autouse=False)
    def setup_device5(self, request):
        """单独初始化设备 5 (Device_5) 驱动及对应的 Page Object"""
        try:
            driver = request.getfixturevalue('driver_device3')
            if driver:
                self.chatPageT5 = ChatPage(driver)
                self.chatListPageT5 = ChatListPage(driver)
                self.mainPageT5 = MainPage(driver)
                self.emojiPageT5 = ChatEmojiPage(driver)
                self.chatImagePageT5 = ChatImagePage(driver)
                self.chatPositionPageT5 = ChatPositionPage(driver)
                self.__class__._class_driver = driver
        except Exception as e:
            logger.warning(f'⚠️ [Setup Device5] 设备 driver_device5 启动失败: {e}')
        yield
        if self.__class__._in_chat:
            logger.info(f'🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页')
            return
        try:
            if hasattr(self, 'mainPageT5') and self.mainPageT5:
                self.mainPageT5.go_to_main_page()
        except Exception as e:
            logger.error(f'Teardown 失败，未能返回首页: {e}')


    # 内部调度方法-多设备异步并发消息发送统一执行器
    def _run_async_multi_device_send(
        self,
        device_sessions_map: dict,
        loop_count: int = 1,
        interval: float = 0.5,
        session_type: str = "会话"
    ):
        """
        多设备异步并发消息发送统一调度执行器
        :param device_sessions_map: 设备序号与会话策略映射 {idx: (dev_name, [session_list])}
        :param loop_count: 每个会话连续循环发送轮数 (X 次)
        :param interval: 单条消息发送间隔（秒）
        :param session_type: 会话类型描述（"群聊" / "单聊"）
        """
        import threading
        exceptions = []

        def worker_send(chatListPage, chatPage, dev_name, sessions):
            try:
                # 兼容单一策略对象或列表；群聊取首个指定群，私聊按序轮询多会话
                session_list = sessions if isinstance(sessions, list) else [sessions]
                targets = [session_list[0]] if session_type == "群聊" else session_list
                total = len(targets)
                is_group = (session_type == "群聊")

                for s_idx, target in enumerate(targets):
                    desc = "指定群聊" if is_group else f"第 {s_idx + 1}/{total} 个单聊"
                    prefix = "" if is_group else f"U{s_idx + 1}_"

                    chatListPage.enter_chat(target.name)
                    logger.info(f'🚀 设备 [{dev_name}] 进入{desc}【{target.name}】，开始连续批量发送 {loop_count} 轮...')

                    for loop in range(loop_count):
                        payloads = [
                            f'[{dev_name}] {prefix}L{loop + 1}_M{idx + 1}: {msg_data.get("context", "")}'
                            for idx, msg_data in enumerate(CHAT_CSV_DATA)
                        ]
                        chatPage.send_messages_batch(payloads, interval=interval)
                        logger.debug(f'✅ 设备 [{dev_name}] 在{session_type}【{target.name}】中完成第 {loop + 1}/{loop_count} 轮发送')

                    action_tip = "退回主页..." if is_group or (s_idx + 1 == total) else "退回主页并轮询下一个会话..."
                    logger.info(f'✅ 设备 [{dev_name}] 已发完{desc}【{target.name}】的全部 {loop_count} 轮消息，{action_tip}')
                    chatPage.click_back_button()
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f'❌ 设备 [{dev_name}] {session_type}异步发送时发生异常: {e}')
                exceptions.append((dev_name, e))

        threads = []
        for idx, (dev_name, session_list) in device_sessions_map.items():
            chat_list_page = getattr(self, f'chatListPageT{idx}', None)
            chat_page = getattr(self, f'chatPageT{idx}', None)
            if chat_list_page and chat_page:
                t = threading.Thread(target=worker_send, args=(chat_list_page, chat_page, dev_name, session_list))
                threads.append(t)
                logger.info(f'🧵 已就绪{session_type}设备线程: {dev_name}')
            else:
                logger.warning(f'⚠️ 设备 {dev_name} 未就绪 (对应端口的 Appium 服务未开启)，跳过此线程')

        try:
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            self.__class__._in_chat = False
            self.__class__._chat_target = None

        if exceptions:
            err_msg = '\n'.join([f'设备 [{dev}]: {err}' for dev, err in exceptions])
            pytest.fail(f'❌ 异步多端{session_type}发送过程中有设备发生异常:\n{err_msg}')


    @allure.story('发送 Text 消息')
    @allure.title('单设备(Device_5)发送 Text 消息-状态：已完成')
    def test_send_text_message_device5(self, setup_device5):
        """
        用例名称：单设备(Device_5)发送消息测试
        步骤：
        1. 将目标测试群组策略分配给设备 5 (Device_5)
        2. 设备 5 进入目标聊天窗口、批量发送文本消息组
        3. 发送完毕后退回主列表并进入下一个会话
        4. 校验发送执行过程中的异常与断言结果
        """
        self._run_async_multi_device_send(
            device_sessions_map={5: ('Device_5', [TEST_GROUPS[0]])},
            loop_count=20,
            interval=0.5,
            session_type="群聊"
        )


    @allure.story('发送 Text 消息')
    @allure.title('多设备群聊异步并行发送 Text 消息-状态：已完成')
    def test_send_text_message_async_multi_device(self, setup_test):
        """
        用例名称：多设备群聊异步并行发送消息测试
        步骤：
        1. 轮流将测试群聊策略分配给已连接设备 (Device_5 ~ Device_9)
        2. 各设备线程异步进入目标群聊窗口、批量发送文本消息组
        3. 发送完后退回主列表并进入下一个会话
        4. 等待所有线程执行结束并做异常校验断言
        """
        dev5_groups = [TEST_GROUPS[0]]
        dev6_groups = [TEST_GROUPS[1]]
        dev7_groups = [TEST_GROUPS[2]]
        dev8_groups = [TEST_GROUPS[3]]
        dev9_groups = [TEST_GROUPS[4]]
        device_groups_map = {
            5: ('Device_5', dev5_groups),
            6: ('Device_6', dev6_groups),
            7: ('Device_7', dev7_groups),
            8: ('Device_8', dev8_groups),
            9: ('Device_9', dev9_groups)
        }
        self._run_async_multi_device_send(
            device_sessions_map=device_groups_map,
            loop_count=5,
            interval=0.5,
            session_type="群聊"
        )


    @allure.story('发送 Text 消息')
    @allure.title('多设备单聊异步并行发送 Text 消息-状态：已完成')
    def test_send_text_message_async_multi_device_private(self, setup_test):
        """
        用例名称：多设备单聊异步并行发送消息测试
        业务流程：
        1. 各就绪设备按 TEST_PRIVATE_USERS 策略列表顺序依次进入目标私聊会话
        2. 在当前会话中连续循环发送 loop_count (X) 轮 chat_messages.csv 数据集内容
        3. 当前会话全部 X 轮发送完成后，退回主列表
        4. 自动按序切换进入下一个私聊会话，继续连续循环发送 X 轮，依此类推完成所有会话
        5. 等待所有线程执行结束并做异常校验断言
        """
        device_users_map = {
            5: ('Device_5', TEST_PRIVATE_USERS),
            6: ('Device_6', TEST_PRIVATE_USERS),
            7: ('Device_7', TEST_PRIVATE_USERS),
            8: ('Device_8', TEST_PRIVATE_USERS),
            9: ('Device_9', TEST_PRIVATE_USERS)
        }
        self._run_async_multi_device_send(
            device_sessions_map=device_users_map,
            loop_count=5,
            interval=0.5,
            session_type="单聊"
        )


    @allure.story('发送 Text 消息')
    @allure.title('多设备群聊与单聊合并异步并行发送 Text 消息-状态：已完成')
    def test_send_text_message_async_multi_device_combined(self, setup_test):
        """
        用例名称：多设备群聊与单聊合并异步并行发送消息测试
        业务流程：
        1. 阶段一：各就绪设备异步并发进入目标群聊窗口，批量发送 CSV 文本消息集，全部发完后退回主列表；
        2. 阶段二：各就绪设备按序进入目标私聊会话，批量发送 CSV 文本消息集，全部发完后退回主列表；
        3. 等待各阶段所有线程执行结束并做异常校验断言
        """
        dev5_groups = [TEST_GROUPS[0]]
        dev6_groups = [TEST_GROUPS[1]]
        dev7_groups = [TEST_GROUPS[2]]
        dev8_groups = [TEST_GROUPS[3]]
        dev9_groups = [TEST_GROUPS[4]]
        device_groups_map = {
            5: ('Device_5', dev5_groups),
            6: ('Device_6', dev6_groups),
            7: ('Device_7', dev7_groups),
            8: ('Device_8', dev8_groups),
            9: ('Device_9', dev9_groups)
        }
        device_users_map = {
            5: ('Device_5', TEST_PRIVATE_USERS),
            6: ('Device_6', TEST_PRIVATE_USERS),
            7: ('Device_7', TEST_PRIVATE_USERS),
            8: ('Device_8', TEST_PRIVATE_USERS),
            9: ('Device_9', TEST_PRIVATE_USERS)
        }

        with allure.step("1. 阶段一：多设备群聊异步并发发送"):
            logger.info("🚀 [Combined Test] 启动阶段一：多设备群聊并发发送...")
            self._run_async_multi_device_send(
                device_sessions_map=device_groups_map,
                loop_count=1,
                interval=0.5,
                session_type="群聊"
            )

        with allure.step("2. 阶段二：多设备单聊异步并发发送"):
            logger.info("🚀 [Combined Test] 启动阶段二：多设备单聊并发发送...")
            self._run_async_multi_device_send(
                device_sessions_map=device_users_map,
                loop_count=1,
                interval=0.5,
                session_type="单聊"
            )




    @allure.story('发送和接收 Text 消息')
    @allure.title('发送和接收 Text 消息，状态：TODO：skip')
    @pytest.mark.skip('暂时跳过，待后续优化')
    @pytest.mark.parametrize('text_message', [pytest.param(x, id=str(x)) for x in CHAT_DATA.get('text_message')])
    def test_send_and_receive_text_message(self, text_message, driver_receiver):
        """
        用例名称：发送文本消息测试，接收消息测试
        步骤：
        发送 Text 文本消息，验证端到端测试，用于回归
        """
        self.chatPage_receiver = ChatPage(driver_receiver)
        self.chatListPage_receiver = ChatListPage(driver_receiver)
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        self.chatListPage_sender.enter_chat(PRIVATE_USER1.name)
        self.chatPage.send_message(payload)
        self.chatListPage_receiver.enter_chat(PRIVATE_USER2.name)
        text = self.chatPage_receiver.get_text_message_content_by_index(index=-1, side='received')
        self.chatPage.back()
        self.chatPage_receiver.back()
        check.equal(text, expected, f'消息 actual: {text}, expected: {expected} 不匹配')