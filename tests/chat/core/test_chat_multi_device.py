import time
import allure
import pytest
import threading
import concurrent.futures
import pytest_check as check
from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import load_csv_data
from pages.main.main_page import MainPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat_options.location.chat_position_page import ChatPositionPage
from strategy.chat.chat_strategy import TEST_GROUPS, TEST_PRIVATE_USERS


CHAT_CSV_DATA = load_csv_data('chat/chat_messages.csv')


@allure.epic('IM核心功能测试')
@allure.feature('聊天模块-多设备并发')
class TestChatMultiDevice:
    """
    多设备异步并发消息发送测试集
    覆盖群聊、单聊以及混合场景下的多设备并发吞吐能力
    """
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
                logger.info(f'{LogIcon.SETUP} [Class Teardown] 多设备测试类执行结束，强制释放会话锁并退回主页')
                cls._in_chat = False
                cls._chat_target = None
                main_page = MainPage(cls._class_driver)
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f'{LogIcon.FAIL} [Class Teardown] 最终返回主页失败: {e}')


    def _ensure_device_on_main_page(self, main_page: MainPage, dev_name: str, max_wait_sec: int = 60) -> bool:
        """
        单设备主页面等待与防误退恢复保障：
        1. 首轮平滑等待主页面渲染就绪（避免 App 冷启动渲染期间误按 Back 键导致退至后台）；
        2. 若首阶段未检测到主页，则调用安全退回机制（清除残留弹窗或历史会话页）；
        3. 在最大超时时间窗口内动态轮询探测，就绪即刻返回，超时才判定失败。
        """
        start_time = time.time()
        smooth_wait = min(15, max_wait_sec)
        logger.info(f"{LogIcon.WAIT} [{dev_name}] 正在检测是否处于主页面（平滑检测上限 {smooth_wait}s）...")
        while time.time() - start_time < smooth_wait:
            try:
                if main_page.is_in_main_page(timeout=1):
                    logger.info(f"{LogIcon.ACTION} 🍏 [{dev_name}] 确认已稳定处于主页面 (耗时 {time.time() - start_time:.1f}s)")
                    return True
            except Exception:
                pass

        logger.warning(f"{LogIcon.WARN} [{dev_name}] 初始阶段未检测到主页面，启动安全退回机制...")
        while time.time() - start_time < max_wait_sec:
            try:
                main_page.go_to_main_page(timeout=1, max_retries=3)
                if main_page.is_in_main_page(timeout=1):
                    logger.info(f"{LogIcon.SUCCESS} 🍏 [{dev_name}] 安全退回成功，当前已稳定处于主页面 (耗时 {time.time() - start_time:.1f}s)")
                    return True
            except Exception as e:
                logger.error(f"{LogIcon.FAIL} [{dev_name}] 执行返回主页面异常: {e}")
        logger.error(f"{LogIcon.FAIL} [{dev_name}] 超过最大等待上限 {max_wait_sec}s，仍未能进入主页面")
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
        class_mode = getattr(self, 'WAIT_DEVICES_MODE', 'smart').lower()
        current_mode = mode.lower() if mode.lower() != "smart" else class_mode

        if current_mode == "hard":
            logger.info(f"{LogIcon.WAIT} 已启用固定死等策略，强制挂机等待 {timeout} 秒 (time.sleep({timeout}))...")
            time.sleep(timeout)
            logger.info(f"{LogIcon.WAIT} ⏰ [Wait Devices Mode: HARD] 强制死等 {timeout} 秒已结束，开始继续执行后续发送流程！")
            return True

        logger.info(f"{LogIcon.ACTION} 已启用智能动态并发探针策略 (最大超时上限: {timeout}s，就绪即刻放行)...")
        if device_indices is None:
            device_indices = range(5, 10)

        active_devices = []
        for idx in device_indices:
            mp = getattr(self, f'mainPageT{idx}', None)
            if mp:
                active_devices.append((idx, f'Device_{idx}', mp))

        if not active_devices:
            logger.warning(f'{LogIcon.WARN} 未检测到任何已初始化的设备页面对象，跳过主页面等待')
            return True

        logger.info(f"{LogIcon.WAIT} 开始并发等待 {len(active_devices)} 台设备统一在主页面就绪: {[name for _, name, _ in active_devices]}...")
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
                    logger.error(f"{LogIcon.FAIL} 设备 [{dev_name}] 等待主页面发生未捕获异常: {e}")
                    dev_results[dev_name] = False

        failed = [d for d, success in dev_results.items() if not success]
        if failed:
            logger.error(f"{LogIcon.FAIL} 以下设备未能在主页面就绪: {failed}")
            return False
        logger.info(f"{LogIcon.SUCCESS} 所有参与设备 ({list(dev_results.keys())}) 已全部在主页面就绪！")
        return True


    @pytest.fixture(autouse=False)
    def setup_test(self, request):
        """初始化多设备 (Device_5 ~ Device_9) 驱动及对应的 Page Object 实例"""
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
                logger.warning(f'{LogIcon.WARN} 设备 driver_device{idx} 启动失败 (对应的 Appium 服务可能未开启): {e}')

        self.__class__._in_chat = False
        self.__class__._chat_target = None

        # 多设备初始化完成后，并发等待所有已启动设备就绪并进入主页面
        self._wait_all_devices_on_main_page(range(5, 10))

        yield
        if self.__class__._in_chat:
            logger.info(f'{LogIcon.SETUP} 🔒 [Teardown] 保持在当前与 {self.__class__._chat_target} 的聊天会话中，跳过返回主页')
            return
        try:
            # 优雅对所有就绪的多设备并发安全退回主页面
            self._wait_all_devices_on_main_page(range(5, 10))
        except Exception as e:
            logger.error(f'{LogIcon.FAIL} Teardown 失败，未能返回首页: {e}')


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
                logger.warning(f'{LogIcon.WARN} 设备 {dev_name} 未就绪 (对应端口的 Appium 服务未开启)，跳过此设备')

        if not ready_tasks:
            logger.warning(f'{LogIcon.WARN} 没有可用设备执行 {session_type} 异步发送')
            return

        # 2. 发送前全局屏障：并发等待本轮参与的所有设备确认处于主页面
        target_indices = [task[0] for task in ready_tasks]
        self._wait_all_devices_on_main_page(target_indices, mode=wait_mode)

        # 3. 创建线程同步栅栏（并发发令枪）：所有设备到达主页起跑线后同一时刻释放进入会话
        barrier = threading.Barrier(parties=len(ready_tasks)) if len(ready_tasks) > 1 else None

        def worker_send(chatListPage, chatPage, mainPage, dev_name, sessions):
            try:
                active_mode = (wait_mode or getattr(self, 'WAIT_DEVICES_MODE', 'smart')).lower()
                if mainPage and active_mode != "hard":
                    self._ensure_device_on_main_page(mainPage, dev_name, max_wait_sec=5)

                # 同步栅栏：等待所有设备都在主页面后，同步放行进入会话
                if barrier:
                    logger.info(f'{LogIcon.WAIT} 设备 [{dev_name}] 已在主页面就绪，等待全设备同步对齐...')
                    try:
                        barrier.wait(timeout=30)
                    except threading.BrokenBarrierError:
                        logger.error(f'{LogIcon.FAIL} 设备 [{dev_name}] 栅栏等待超时破损，强制继续执行')
                    logger.info(f'{LogIcon.SUCCESS} 设备 [{dev_name}] 全设备对齐完毕，并发进入会话！')

                # 兼容单一策略对象或列表；群聊取首个指定群，私聊按序轮询多会话
                session_list = sessions if isinstance(sessions, list) else [sessions]
                targets = [session_list[0]] if session_type == "群聊" else session_list
                total = len(targets)
                is_group = (session_type == "群聊")

                for s_idx, target in enumerate(targets):
                    desc = "指定群聊" if is_group else f"第 {s_idx + 1}/{total} 个单聊"
                    prefix = "" if is_group else f"U{s_idx + 1}_"

                    chatListPage.enter_chat(target.name)
                    logger.info(f'{LogIcon.ACTION} 设备 [{dev_name}] 进入{desc}【{target.name}】，开始连续批量发送 {loop_count} 轮...')
                    send_start = time.time()

                    for loop in range(loop_count):
                        payloads = [
                            f'[{dev_name}] {prefix}L{loop + 1}_M{idx + 1}: {msg_data.get("context", "")}'
                            for idx, msg_data in enumerate(CHAT_CSV_DATA)
                        ]
                        chatPage.send_messages_batch(payloads, interval=interval)
                        logger.debug(f'{LogIcon.SUCCESS} 设备 [{dev_name}] 在{session_type}【{target.name}】中完成第 {loop + 1}/{loop_count} 轮发送')

                    cost_sec = max(0.1, time.time() - send_start)
                    total_sent = loop_count * len(CHAT_CSV_DATA)
                    action_tip = "退回主页..." if is_group or (s_idx + 1 == total) else "退回主页并轮询下一个会话..."
                    logger.info(f'{LogIcon.SUCCESS} 设备 [{dev_name}] 已发完{desc}【{target.name}】的全部 {total_sent} 条消息 (耗时 {cost_sec:.1f}s, 吞吐 {total_sent/cost_sec:.1f}条/s)，{action_tip}')

                    chatPage.click_back_button()
                    if mainPage:
                        mainPage.go_to_main_page(timeout=1, max_retries=3)
            except Exception as e:
                logger.error(f'{LogIcon.FAIL} 设备 [{dev_name}] {session_type}异步发送时发生异常: {e}')
                exceptions.append((dev_name, e))
                if barrier and not barrier.broken:
                    try:
                        logger.warning(f'{LogIcon.WARN} 设备 [{dev_name}] 异常退出，主动解除同步栅栏以唤醒其他就绪设备...')
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
            logger.info(f'{LogIcon.ACTION} 🧵 已就绪{session_type}设备线程: {dev_name}')

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



    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
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
            logger.info(f"{LogIcon.WAIT} [Multi Device Group Test] 检查并等待所有参与设备在主页面就绪...")
            is_ready = self._wait_all_devices_on_main_page(list(device_groups_map.keys()))
            check.is_true(is_ready, "所有设备启动后应成功到达主页面")

        with allure.step("1. 多设备群聊异步并发发送"):
            self._run_async_multi_device_send(
                device_sessions_map=device_groups_map,
                loop_count=1,
                interval=0.1,
                session_type="群聊"
            )



    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
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
            6: ('Device_6', TEST_PRIVATE_USERS),
            7: ('Device_7', TEST_PRIVATE_USERS),
            8: ('Device_8', TEST_PRIVATE_USERS),
            9: ('Device_9', TEST_PRIVATE_USERS)
        }
        with allure.step("0. 前置准备：并发等待所有设备在主页面就绪"):
            logger.info(f"{LogIcon.WAIT} [Multi Device Private Test] 检查并等待所有参与设备在主页面就绪...")
            is_ready = self._wait_all_devices_on_main_page(list(device_users_map.keys()))
            check.is_true(is_ready, "所有设备启动后应成功到达主页面")

        with allure.step("1. 多设备单聊异步并发发送"):
            self._run_async_multi_device_send(
                device_sessions_map=device_users_map,
                loop_count=5,
                interval=0.1,
                session_type="单聊"
            )



    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
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
            logger.info(f"{LogIcon.WAIT} [Combined Test] 检查并等待所有参与设备在主页面就绪...")
            is_ready = self._wait_all_devices_on_main_page(list(device_groups_map.keys()))
            check.is_true(is_ready, "所有设备启动后应成功到达主页面")

        with allure.step("1. 阶段一：多设备群聊异步并发发送"):
            logger.info(f"{LogIcon.ACTION} [Combined Test] 启动阶段一：多设备群聊并发发送...")
            self._run_async_multi_device_send(
                device_sessions_map=device_groups_map,
                loop_count=20,
                interval=0.2,
                session_type="群聊"
            )

        with allure.step("1.5. 阶段过渡：确保所有设备退出群聊并在主列表对齐"):
            logger.info(f"{LogIcon.WAIT} [Combined Test] 阶段一结束，检查并确认所有设备均已安全返回主页面...")
            is_trans_ready = self._wait_all_devices_on_main_page(list(device_users_map.keys()))
            check.is_true(is_trans_ready, "群聊阶段完成后所有设备应安全回到主页面准备进入单聊阶段")

        with allure.step("2. 阶段二：多设备单聊异步并发发送"):
            logger.info(f"{LogIcon.ACTION} [Combined Test] 启动阶段二：多设备单聊并发发送...")
            self._run_async_multi_device_send(
                device_sessions_map=device_users_map,
                loop_count=20,
                interval=0.2,
                session_type="单聊"
            )
