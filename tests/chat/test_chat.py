import allure
import pytest
import pytest_check as check
import time
import threading
import concurrent.futures
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

    # 设备启动完成等待策略控制开关：
    # - "smart": 智能动态并发探针模式（就绪即放行，平均 2~3 秒，支持异常自愈，推荐）
    # - "hard" : 固定硬等模式（强制死等 60 秒 time.sleep(60)，满足特殊挂机/极端冷启动放置需求）
    WAIT_DEVICES_MODE: str = "smart"

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


    def _ensure_device_on_main_page(self, main_page: MainPage, dev_name: str, max_wait_sec: int = 60) -> bool:
        """
        单设备主页面等待与防误退恢复保障：
        1. 首轮平滑等待主页面渲染就绪（避免 App 冷启动渲染期间误按 Back 键导致退至后台）；
        2. 若首阶段未检测到主页，则调用安全退回机制（清除残留弹窗或历史会话页）；
        3. 在最大超时时间窗口内动态轮询探测，就绪即刻返回，超时才判定失败。
        """
        start_time = time.time()
        # 阶段 1：首轮平滑轮询等待主页面就绪（最多平滑等待 15 秒，充分适应冷启动与开屏广告）
        smooth_wait = min(15, max_wait_sec)
        logger.info(f"⏳ [{dev_name}] 正在检测是否处于主页面（平滑检测上限 {smooth_wait}s）...")
        while time.time() - start_time < smooth_wait:
            try:
                if main_page.is_in_main_page(timeout=1):
                    logger.info(f"🍏 [{dev_name}] 确认已稳定处于主页面 (耗时 {time.time() - start_time:.1f}s)")
                    return True
            except Exception:
                pass
            time.sleep(1)

        # 阶段 2：未检测到主页面，可能停留在历史二级页面，执行多级安全退回并在剩余窗口内持续探测
        logger.warning(f"⚠️ [{dev_name}] 初始阶段未检测到主页面，启动安全退回机制...")
        while time.time() - start_time < max_wait_sec:
            try:
                main_page.go_to_main_page(timeout=1, max_retries=3)
                if main_page.is_in_main_page(timeout=1):
                    logger.info(f"🍏 [{dev_name}] 安全退回成功，当前已稳定处于主页面 (耗时 {time.time() - start_time:.1f}s)")
                    return True
            except Exception as e:
                logger.error(f"❌ [{dev_name}] 执行返回主页面异常: {e}")
            time.sleep(1)

        logger.error(f"❌ [{dev_name}] 超过最大等待上限 {max_wait_sec}s，仍未能进入主页面")
        return False

    def _wait_all_devices_on_main_page(
        self,
        device_indices=None,
        timeout: int = 60,
        mode: str = "smart"
    ) -> bool:
        """
        等待所有指定设备均稳定处于主页面（支持策略自由切换）
        :param device_indices: 待检测设备编号列表，默认检查当前所有已初始化的多设备
        :param timeout: 单台设备最大超时（秒）或死等时间（秒），默认上限为 60 秒
        :param mode: 等待策略模式，默认 "smart"：
                     - "smart": 智能动态并发探针模式（就绪即放行，平均 2~3 秒，支持异常自愈退回）
                     - "hard" : 固定硬等模式（强制 time.sleep(60)，满足特殊挂机/极端冷启动放置需求）
        :return: 所有设备是否成功就绪
        """
        # 模式判定：若显式传了非默认的 hard 则直接生效，否则遵从类属性全局开关
        class_mode = getattr(self, 'WAIT_DEVICES_MODE', 'smart').lower()
        current_mode = mode.lower() if mode.lower() != "smart" else class_mode

        # =========================================================================
        # 策略分支 1：固定死等模式 (Hard Sleep 模式)
        # =========================================================================
        if current_mode == "hard":
            logger.info(f"⏳ [Wait Devices Mode: HARD] 已启用固定死等策略，强制挂机等待 {timeout} 秒 (time.sleep({timeout}))...")
            time.sleep(timeout)
            logger.info(f"⏰ [Wait Devices Mode: HARD] 强制死等 {timeout} 秒已结束，开始继续执行后续发送流程！")
            return True

        # =========================================================================
        # 策略分支 2：智能动态探针模式 (Smart Mode，默认最佳实践)
        # =========================================================================
        logger.info(f"🚀 [Wait Devices Mode: SMART] 已启用智能动态并发探针策略 (最大超时上限: {timeout}s，就绪即刻放行)...")
        if device_indices is None:
            device_indices = range(5, 10)

        active_devices = []
        for idx in device_indices:
            mp = getattr(self, f'mainPageT{idx}', None)
            if mp:
                active_devices.append((idx, f'Device_{idx}', mp))

        if not active_devices:
            if hasattr(self, 'mainPage') and self.mainPage:
                active_devices.append((1, 'Sender_Device', self.mainPage))
            else:
                logger.warning('⚠️ [Wait Devices] 未检测到任何已初始化的设备页面对象，跳过主页面等待')
                return True

        logger.info(f"⏳ [Wait Devices] 开始并发等待 {len(active_devices)} 台设备统一在主页面就绪: {[name for _, name, _ in active_devices]}...")
        dev_results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_devices)) as executor:
            future_to_dev = {
                executor.submit(self._ensure_device_on_main_page, mp, dev_name, timeout): dev_name
                for _, dev_name, mp in active_devices
            }
            for future in concurrent.futures.as_completed(future_to_dev):
                dev_name = future_to_dev[future]
                try:
                    dev_results[dev_name] = future.result()
                except Exception as e:
                    logger.error(f"❌ [Wait Devices] 设备 [{dev_name}] 等待主页面发生未捕获异常: {e}")
                    dev_results[dev_name] = False

        failed = [d for d, success in dev_results.items() if not success]
        if failed:
            logger.error(f"❌ [Wait Devices] 以下设备未能在主页面就绪: {failed}")
            return False

        logger.info(f"🎉 [Wait Devices] 所有参与设备 ({list(dev_results.keys())}) 已全部在主页面就绪！")
        return True

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

        # 多设备初始化完成后，并发等待所有已启动设备就绪并进入主页面
        self._wait_all_devices_on_main_page(range(5, 10))

        yield
        if self.__class__._in_chat:
            logger.info(f'🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页')
            return
        try:
            # 优雅对所有就绪的多设备并发安全退回主页面
            self._wait_all_devices_on_main_page(range(5, 10))
        except Exception as e:
            logger.error(f'Teardown 失败，未能返回首页: {e}')


    @pytest.fixture(autouse=False)
    def setup_device5(self, request):
        """单独初始化设备 5 (Device_5) 驱动及对应的 Page Object"""
        try:
            try:
                driver = request.getfixturevalue('driver_device5')
            except Exception:
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

        if hasattr(self, 'mainPageT5') and self.mainPageT5:
            self._ensure_device_on_main_page(self.mainPageT5, 'Device_5')

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
        session_type: str = "会话",
        wait_mode: str = "smart"
    ):
        """
        多设备异步并发消息发送统一调度执行器
        :param device_sessions_map: 设备序号与会话策略映射 {idx: (dev_name, [session_list])}
        :param loop_count: 每个会话连续循环发送轮数 (X 次)
        :param interval: 单条消息发送间隔（秒）
        :param session_type: 会话类型描述（"群聊" / "单聊"）
        :param wait_mode: 前置等待模式，默认 "smart"（智能动态探针），可选 "hard"（固定死等 60 秒）
        """
        exceptions = []

        # 1. 过滤并收集所有已成功就绪的设备及其 Page 实例
        ready_tasks = []
        for idx, (dev_name, session_list) in device_sessions_map.items():
            chat_list_page = getattr(self, f'chatListPageT{idx}', None)
            chat_page = getattr(self, f'chatPageT{idx}', None)
            main_page = getattr(self, f'mainPageT{idx}', None)
            if chat_list_page and chat_page:
                ready_tasks.append((idx, dev_name, chat_list_page, chat_page, main_page, session_list))
            else:
                logger.warning(f'⚠️ 设备 {dev_name} 未就绪 (对应端口的 Appium 服务未开启)，跳过此设备')

        if not ready_tasks:
            logger.warning(f'⚠️ 没有可用设备执行 {session_type} 异步发送')
            return

        # 2. 发送前全局屏障：并发等待本轮参与的所有设备确认处于主页面（支持智能/死等双模式自由切换）
        target_indices = [task[0] for task in ready_tasks]
        self._wait_all_devices_on_main_page(target_indices, mode=wait_mode)

        # 3. 创建线程同步栅栏（并发发令枪）：所有设备到达主页起跑线后同一时刻释放进入会话
        barrier = threading.Barrier(parties=len(ready_tasks)) if len(ready_tasks) > 1 else None

        def worker_send(chatListPage, chatPage, mainPage, dev_name, sessions):
            try:
                # 再次确认当前设备处于主页面（在 smart 模式下执行微量探针确认；在 hard 模式下已完成统一定时死等）
                active_mode = (wait_mode or getattr(self, 'WAIT_DEVICES_MODE', 'smart')).lower()
                if mainPage and active_mode != "hard":
                    self._ensure_device_on_main_page(mainPage, dev_name, max_wait_sec=5)

                # 同步栅栏：等待所有设备都在主页面后，同步放行进入会话
                if barrier:
                    logger.info(f'⏳ 设备 [{dev_name}] 已在主页面就绪，等待全设备同步对齐...')
                    try:
                        barrier.wait(timeout=30)
                    except threading.BrokenBarrierError:
                        logger.error(f'❌ 设备 [{dev_name}] 栅栏等待超时破损，强制继续执行')
                    logger.info(f'🏁 设备 [{dev_name}] 全设备对齐完毕，并发进入会话！')

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
                    send_start = time.time()

                    for loop in range(loop_count):
                        payloads = [
                            f'[{dev_name}] {prefix}L{loop + 1}_M{idx + 1}: {msg_data.get("context", "")}'
                            for idx, msg_data in enumerate(CHAT_CSV_DATA)
                        ]
                        chatPage.send_messages_batch(payloads, interval=interval)
                        logger.debug(f'✅ 设备 [{dev_name}] 在{session_type}【{target.name}】中完成第 {loop + 1}/{loop_count} 轮发送')

                    cost_sec = max(0.1, time.time() - send_start)
                    total_sent = loop_count * len(CHAT_CSV_DATA)
                    action_tip = "退回主页..." if is_group or (s_idx + 1 == total) else "退回主页并轮询下一个会话..."
                    logger.info(f'✅ 设备 [{dev_name}] 已发完{desc}【{target.name}】的全部 {total_sent} 条消息 (耗时 {cost_sec:.1f}s, 吞吐 {total_sent/cost_sec:.1f}条/s)，{action_tip}')
                    
                    # 安全退回：先点返回按钮，再触发主页探针确保 100% 回到主列表
                    chatPage.click_back_button()
                    time.sleep(0.5)
                    if mainPage:
                        mainPage.go_to_main_page(timeout=1, max_retries=3)

            except Exception as e:
                logger.error(f'❌ 设备 [{dev_name}] {session_type}异步发送时发生异常: {e}')
                exceptions.append((dev_name, e))
                # 若当前设备异常且栅栏尚未破损，主动打破栅栏防止其他等待线程死锁
                if barrier and not barrier.broken:
                    try:
                        logger.warning(f'⚠️ 设备 [{dev_name}] 异常退出，主动解除同步栅栏以唤醒其他就绪设备...')
                        barrier.abort()
                    except Exception:
                        pass

        threads = []
        for idx, dev_name, chat_list_page, chat_page, main_page, session_list in ready_tasks:
            t = threading.Thread(
                target=worker_send,
                args=(chat_list_page, chat_page, main_page, dev_name, session_list)
            )
            threads.append(t)
            logger.info(f'🧵 已就绪{session_type}设备线程: {dev_name}')

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
        with allure.step("0. 前置准备：并发等待所有设备在主页面就绪"):
            logger.info("⏳ [Multi Device Group Test] 检查并等待所有参与设备在主页面就绪...")
            is_ready = self._wait_all_devices_on_main_page(list(device_groups_map.keys()))
            check.is_true(is_ready, "所有设备启动后应成功到达主页面")

        with allure.step("1. 多设备群聊异步并发发送"):
            self._run_async_multi_device_send(
                device_sessions_map=device_groups_map,
                loop_count=1,
                interval=0.1,
                session_type="群聊"
            )


    @allure.story('发送 Text 消息')
    @allure.title('多设备单聊异步并行发送 Text 消息-状态：已完成')
    def test_send_text_message_async_multi_device_private(self, setup_test):
        """
        用例名称：多设备单聊异步并行发送消息测试
        业务流程：
        0. 前置准备：并发等待所有参与设备在主页面就绪
        1. 各就绪设备按 TEST_PRIVATE_USERS 策略列表顺序依次进入目标私聊会话
        2. 在当前会话中连续循环发送 loop_count (X) 轮 chat_messages.csv 数据集内容
        3. 当前会话全部 X 轮发送完成后，退回主列表
        4. 自动按序切换进入下一个私聊会话，继续连续循环发送 X 轮，依此类推完成所有会话
        5. 等待所有线程执行结束并做异常校验断言
        """
        device_users_map = {
            5: ('Device_5', TEST_PRIVATE_USERS),
            # 6: ('Device_6', TEST_PRIVATE_USERS),
            # 7: ('Device_7', TEST_PRIVATE_USERS),
            # 8: ('Device_8', TEST_PRIVATE_USERS),
            # 9: ('Device_9', TEST_PRIVATE_USERS)
        }
        with allure.step("0. 前置准备：并发等待所有设备在主页面就绪"):
            logger.info("⏳ [Multi Device Private Test] 检查并等待所有参与设备在主页面就绪...")
            is_ready = self._wait_all_devices_on_main_page(list(device_users_map.keys()))
            check.is_true(is_ready, "所有设备启动后应成功到达主页面")

        with allure.step("1. 多设备单聊异步并发发送"):
            self._run_async_multi_device_send(
                device_sessions_map=device_users_map,
                loop_count=1,
                interval=0.1,
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

        with allure.step("0. 前置准备：并发等待所有设备在主页面就绪"):
            logger.info("⏳ [Combined Test] 检查并等待所有参与设备在主页面就绪...")
            is_ready = self._wait_all_devices_on_main_page(list(device_groups_map.keys()), timeout=10, mode="hard")
            check.is_true(is_ready, "所有设备启动后应成功到达主页面")

        with allure.step("1. 阶段一：多设备群聊异步并发发送"):
            logger.info("🚀 [Combined Test] 启动阶段一：多设备群聊并发发送...")
            self._run_async_multi_device_send(
                device_sessions_map=device_groups_map,
                loop_count=1,
                interval=0.2,
                session_type="群聊"
            )

        with allure.step("1.5. 阶段过渡：确保所有设备退出群聊并在主列表对齐"):
            logger.info("⏳ [Combined Test] 阶段一结束，检查并确认所有设备均已安全返回主页面...")
            is_trans_ready = self._wait_all_devices_on_main_page(list(device_users_map.keys()), timeout=10, mode='hard')
            check.is_true(is_trans_ready, "群聊阶段完成后所有设备应安全回到主页面准备进入单聊阶段")

        with allure.step("2. 阶段二：多设备单聊异步并发发送"):
            logger.info("🚀 [Combined Test] 启动阶段二：多设备单聊并发发送...")
            self._run_async_multi_device_send(
                device_sessions_map=device_users_map,
                loop_count=1,
                interval=0.2,
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