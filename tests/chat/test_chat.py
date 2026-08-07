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
    TEST_GROUPS
)



# 1. 预加载数据（避免在测试方法中重复IO）
CHAT_DATA = load_yaml_data("chat/chat.yaml").get("test_data")


@pytest.mark.usefixtures('message_page')
@allure.epic("IM核心功能测试")
@allure.feature("聊天模块-单聊基础：已完成")
@allure.story("发送 Text 消息，验证")
class TestChat:
    # 会话锁及目标记录：用以避免参数化用例连续运行时反复返回主页与重新进入单聊会话
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
                logger.info("🧹 [Class Teardown] 整个测试类执行结束，强制释放会话锁并退回主页")
                cls._in_chat = False
                cls._chat_target = None
                main_page = MainPage(cls._class_driver)
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f"[Class Teardown] 最终返回主页失败: {e}")

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender, request):
        if request.node.get_closest_marker("no_setup"):
            yield
            return

        self.chatPage = ChatPage(driver_sender)
        self.chatListPage_sender = ChatListPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        self.emojiPage = ChatEmojiPage(driver_sender)
        self.chatImagePage = ChatImagePage(driver_sender)
        self.chatPositionPage = ChatPositionPage(driver_sender)
        
        # 缓存当前驱动，供 class 级别 Teardown 清理时使用
        self.__class__._class_driver = driver_sender

        # 获取当前运行的方法名称。如果是其他非单聊发送方法，强制释放会话锁
        current_test = request.node.originalname or request.node.name
        if "test_send_text_message" not in current_test:
            self.__class__._in_chat = False
            self.__class__._chat_target = None

        yield

        # 校验会话锁：如果当前仍处在聊天会话中，则跳过耗时且多余的退回主页动作
        if self.__class__._in_chat:
            logger.info(f"🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页")
            return

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")




    @allure.story("发送 Text 消息")
    @allure.title("发送 Text 消息，状态：已完成")
    @pytest.mark.parametrize("text_message", CHAT_DATA.get("text_message"))
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=["私聊模式", "群聊模式"])
    def test_send_text_message(self, text_message, strategy):
        """  用例名称：发送文本消息测试  """
        payload = str(text_message['data']['payload'])
        expected = str(text_message['expected']['expected_payload'])
        
        # 自适应检查：如果切换了聊天会话目标，必须先将锁释放并返回主页
        if self.__class__._chat_target != strategy.name:
            if self.__class__._in_chat:
                logger.info(f"🔄 [Lock] 检测到聊天目标从 {self.__class__._chat_target} 切换为 {strategy.name}，退回主页重新进入")
                try:
                    self.mainPage.go_to_main_page()
                except Exception as e:
                    logger.error(f"⚠️ [Error] 切换会话退回主页失败: {e}")
            self.__class__._in_chat = False
            self.__class__._chat_target = strategy.name

        try:
            if not self.__class__._in_chat:
                self.chatListPage_sender.enter_chat(strategy.name)
                self.__class__._in_chat = True
                logger.info(f"🔓 [Lock] 已成功进入与 {strategy.name} 的聊天，会话保持锁开启")

            self.chatPage.send_message(payload)
            text = self.chatPage.find_message_content(index=-1, side='sent')
            check.equal(text, expected, f"消息 actual: {text}, expected: {expected} 不匹配")
        except Exception as e:
            self.__class__._in_chat = False
            self.__class__._chat_target = None
            logger.error(f"⚠️ [Error] 发送消息或校验失败，释放会话锁以进行 Teardown 重置: {e}")
            raise e




    @pytest.fixture(autouse=False)
    def setup_test(self, request):
        # 批量动态初始化 T3 至 T9 模拟器的 Page Object，若端口服务未开启则跳过，防报错阻断测试
        for idx in range(5, 10):
            try:
                driver = request.getfixturevalue(f"driver_device{idx}")
                if driver:
                    setattr(self, f"chatPageT{idx}", ChatPage(driver))
                    setattr(self, f"chatListPageT{idx}", ChatListPage(driver))
                    setattr(self, f"mainPageT{idx}", MainPage(driver))
                    setattr(self, f"emojiPageT{idx}", ChatEmojiPage(driver))
                    setattr(self, f"chatImagePageT{idx}", ChatImagePage(driver))
                    setattr(self, f"chatPositionPageT{idx}", ChatPositionPage(driver))
                    self.__class__._class_driver = driver
            except Exception as e:
                logger.warning(f"⚠️ [Setup Test] 设备 driver_device{idx} 启动失败 (对应的 Appium 服务可能未开启): {e}")

        # 获取当前运行的方法名称。如果是其他非单聊发送方法，强制释放会话锁
        current_test = request.node.originalname or request.node.name
        if "test_send_text_message" not in current_test:
            self.__class__._in_chat = False
            self.__class__._chat_target = None

        yield

        # 校验会话锁：如果当前仍处在聊天会话中，则跳过耗时且多余的退回主页动作
        if self.__class__._in_chat:
            logger.info(f"🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页")
            return

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    @pytest.fixture(autouse=False)
    def setup_device5(self, request):
        """单独初始化设备 5 (Device_5) 驱动及对应的 Page Object"""
        try:
            driver = request.getfixturevalue("driver_device5")
            if driver:
                self.chatPageT5 = ChatPage(driver)
                self.chatListPageT5 = ChatListPage(driver)
                self.mainPageT5 = MainPage(driver)
                self.emojiPageT5 = ChatEmojiPage(driver)
                self.chatImagePageT5 = ChatImagePage(driver)
                self.chatPositionPageT5 = ChatPositionPage(driver)
                self.__class__._class_driver = driver
        except Exception as e:
            logger.warning(f"⚠️ [Setup Device5] 设备 driver_device5 启动失败: {e}")

        yield

        if self.__class__._in_chat:
            logger.info(f"🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页")
            return

        try:
            if hasattr(self, 'mainPageT5') and self.mainPageT5:
                self.mainPageT5.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")

    @allure.story("发送 Text 消息")
    @allure.title("单设备(Device_5)发送 Text 消息-状态：已完成")
    @pytest.mark.no_setup
    def test_send_text_message_device5(self, setup_device5):
        """
        用例名称：单设备(Device_5)发送消息测试
        步骤：
        1. 将目标测试群组策略分配给设备 5 (Device_5)
        2. 设备 5 进入目标聊天窗口、批量发送文本消息组
        3. 发送完毕后退回主列表并进入下一个会话
        4. 校验发送执行过程中的异常与断言结果
        """
        import threading

        loop_count = 20

        text_messages = load_csv_data("chat/chat_messages.csv")

        exceptions = []
        def worker_send(chatListPage, chatPage, dev_name, group_list):
            cnt = 0
            try:
                for grp in group_list:
                    chatListPage.enter_chat(grp.name)
                    logger.info(f"🚀 设备 [{dev_name}] 成功进入与 {grp.name} 的聊天，开始并发发送...")
                    
                    for loop in range(loop_count):
                        for idx, msg_data in enumerate(text_messages):
                            payload = f"[{dev_name}] L{loop+1}_M{idx+1}: " + str(msg_data['context'])
                            chatPage.fast_send_message(payload)
                            time.sleep(0.01)
                            cnt += 1
                        logger.debug(f"✅ 设备 [{dev_name}] 第 {loop + 1} 轮发送完成，已累计发送 {cnt} 条消息")
                    logger.info(f"✅ 设备 [{dev_name}] 已发完与 {grp.name} 的聊天，准备退回主页并进入下一会话...")
                    chatPage.click_back_button()
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"❌ 设备 [{dev_name}] 异步发送时发生异常: {e}")
                exceptions.append((dev_name, e))

        dev5_groups = [TEST_GROUPS[0]]

        threads = []
        device_groups_map = {
            5: ("Device_5", dev5_groups),
        }
        for idx, (dev_name, group_list) in device_groups_map.items():
            chat_list_page = getattr(self, f"chatListPageT{idx}", None)
            chat_page = getattr(self, f"chatPageT{idx}", None)
            if chat_list_page and chat_page:
                t = threading.Thread(
                    target=worker_send,
                    args=(chat_list_page, chat_page, dev_name, group_list)
                )
                threads.append(t)
                logger.info(f"🧵 已就绪设备线程: {dev_name}")
            else:
                logger.warning(f"⚠️ 设备 {dev_name} 未就绪 (对应端口的 Appium 服务未开启)，跳过此线程")


        try:
            for t in threads:
                t.start()

            for t in threads:
                t.join()
        finally:
            self.__class__._in_chat = False
            self.__class__._chat_target = None

        if exceptions:
            err_msg = "\n".join([f"设备 [{dev}]: {err}" for dev, err in exceptions])
            pytest.fail(f"❌ 异步多端发送过程中有设备发生异常:\n{err_msg}")


    @allure.story("发送 Text 消息")
    @allure.title("多设备异步并行发送 Text 消息-状态：已完成")
    @pytest.mark.no_setup
    def test_send_text_message_async_multi_device(self, setup_test):
        """
        用例名称：多设备异步并行发送消息测试
        步骤：
        1. 轮流将 7 个测试群聊策略分配给设备3和设备4
        2. 设备 3 处理奇数编号群组（测试001, 测试003, 测试005, 测试007）
        3. 设备 4 处理偶数编号群组（测试002, 测试004, 测试006）
        4. 各个设备线程异步进入目标聊天窗口、发送文本消息组，发送完后退回主列表并进入下一个会话
        5. 等待所有线程执行结束并做异常校验断言
        """
        import threading

        loop_count = 20

        text_messages = load_csv_data("chat/chat_messages.csv")

        exceptions = []

        def worker_send(chatListPage, chatPage, dev_name, group_list):
            try:
                for grp in group_list:
                    chatListPage.enter_chat(grp.name)
                    logger.info(f"🚀 设备 [{dev_name}] 成功进入与 {grp.name} 的聊天，开始并发发送...")
                    
                    for loop in range(loop_count):
                        for idx, msg_data in enumerate(text_messages):
                            payload = f"[{dev_name}] L{loop+1}_M{idx+1}: " + str(msg_data['context'])
                            chatPage.fast_send_message(payload)
                            time.sleep(0.01)
                    
                    logger.info(f"✅ 设备 [{dev_name}] 已发完与 {grp.name} 的聊天，准备退回主页并进入下一会话...")
                    chatPage.click_back_button()
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"❌ 设备 [{dev_name}] 异步发送时发生异常: {e}")
                exceptions.append((dev_name, e))

        # 设备3分配奇数项（索引为0, 2, 4, 6，对应测试001, 003, 005, 007）
        dev3_groups = TEST_GROUPS[::2]
        # 设备4分配偶数项（索引为1, 3, 5，对应测试002, 004, 006）
        dev4_groups = TEST_GROUPS[1::2]
        
        dev5_groups = [TEST_GROUPS[0]]
        dev6_groups = [TEST_GROUPS[1]]
        dev7_groups = [TEST_GROUPS[2]]
        dev8_groups = [TEST_GROUPS[3]]
        dev9_groups = [TEST_GROUPS[4]]

        threads = []
        device_groups_map = {
            # 3: ("Device_3", dev3_groups),
            # 4: ("Device_4", dev4_groups),
            5: ("Device_5", dev5_groups),
            6: ("Device_6", dev6_groups),
            7: ("Device_7", dev7_groups),
            8: ("Device_8", dev8_groups),
            9: ("Device_9", dev9_groups),
        }
        for idx, (dev_name, group_list) in device_groups_map.items():
            chat_list_page = getattr(self, f"chatListPageT{idx}", None)
            chat_page = getattr(self, f"chatPageT{idx}", None)
            if chat_list_page and chat_page:
                t = threading.Thread(
                    target=worker_send,
                    args=(chat_list_page, chat_page, dev_name, group_list)
                )
                threads.append(t)
                logger.info(f"🧵 已就绪设备线程: {dev_name}")
            else:
                logger.warning(f"⚠️ 设备 {dev_name} 未就绪 (对应端口的 Appium 服务未开启)，跳过此线程")


        try:
            for t in threads:
                t.start()

            for t in threads:
                t.join()
        finally:
            self.__class__._in_chat = False
            self.__class__._chat_target = None

        if exceptions:
            err_msg = "\n".join([f"设备 [{dev}]: {err}" for dev, err in exceptions])
            pytest.fail(f"❌ 异步多端发送过程中有设备发生异常:\n{err_msg}")


    @allure.story("发送和接收 Text 消息")
    @allure.title("发送和接收 Text 消息，状态：TODO：skip")
    @pytest.mark.skip("暂时跳过，待后续优化")
    @pytest.mark.parametrize("text_message", CHAT_DATA.get("text_message"))
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
        text = self.chatPage_receiver.find_message_content(index=-1, side='received')
        self.chatPage.back()
        self.chatPage_receiver.back()
        check.equal(text, expected, f"消息 actual: {text}, expected: {expected} 不匹配")
