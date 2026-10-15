import time
import allure
import pytest
import threading
import concurrent.futures
from typing import List, Dict, Tuple, Any, Optional
import pytest_check as check
from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import load_csv_data
from pages.main.main_page import MainPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.chat_options.images.chat_image_page import ChatImagePage
from pages.chat_options.location.chat_position_page import ChatPositionPage
from strategy.chat.chat_strategy import TEST_GROUPS, GROUP_STRATEGY


CHAT_CSV_DATA = load_csv_data('chat/chat_messages.csv')


@allure.epic('IM核心功能测试')
@allure.feature('群聊模块-多设备并发特殊场景')
class TestGroupSpecialMultiDevice:
    """
    群聊模块多设备异步并发特殊用例测试套件
    支持同时调度 5 台设备 (Device_5 ~ Device_9) 执行高并发、竞态条件与多端协同等极端测试
    """
    _in_chat = False
    _chat_target = None
    _class_driver = None

    # 设备启动等待探针模式：
    # - "smart": 智能动态并发探针模式（就绪即放行，平均 2~3 秒，支持异常自愈）
    # - "hard" : 固定硬等模式（强制 time.sleep(60)，满足特殊挂机/极端冷启动放置需求）
    WAIT_DEVICES_MODE: str = "smart"

    @classmethod
    def teardown_class(cls):
        """
        测试类执行完毕后的全局清理保障：
        释放会话状态锁并引导主设备安全返回主页
        """
        if cls._in_chat and cls._class_driver:
            try:
                logger.info(f'{LogIcon.SETUP} [Class Teardown] 群聊多设备特殊用例测试结束，安全返回主页')
                cls._in_chat = False
                cls._chat_target = None
                main_page = MainPage(cls._class_driver)
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f'{LogIcon.FAIL} [Class Teardown] 返回主页异常: {e}')

    def _ensure_device_on_main_page(self, main_page: MainPage, dev_name: str, max_wait_sec: int = 60) -> bool:
        """
        单设备主页面稳定探测与防误退恢复机制
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
                    logger.info(f"{LogIcon.SUCCESS} 🍏 [{dev_name}] 安全退回成功，当前处于主页面 (耗时 {time.time() - start_time:.1f}s)")
                    return True
            except Exception as e:
                logger.error(f"{LogIcon.FAIL} [{dev_name}] 执行返回主页面异常: {e}")
        logger.error(f"{LogIcon.FAIL} [{dev_name}] 超过最大等待上限 {max_wait_sec}s，未能进入主页面")
        return False

    def _wait_all_devices_on_main_page(
        self,
        device_indices=None,
        timeout: int = 60,
        mode: str = "smart"
    ) -> bool:
        """
        并发等待所有指定设备均稳定处于主页面
        """
        class_mode = getattr(self, 'WAIT_DEVICES_MODE', 'smart').lower()
        current_mode = mode.lower() if mode.lower() != "smart" else class_mode

        if current_mode == "hard":
            logger.info(f"{LogIcon.WAIT} 强制等待 {timeout} 秒...")
            time.sleep(timeout)
            return True

        if device_indices is None:
            device_indices = range(5, 10)

        active_devices = []
        for idx in device_indices:
            mp = getattr(self, f'mainPageT{idx}', None)
            if mp:
                active_devices.append((idx, f'Device_{idx}', mp))

        if not active_devices:
            logger.warning(f'{LogIcon.WARN} 未检测到任何已初始化的设备页面对象')
            return True

        logger.info(f"{LogIcon.WAIT} 并发等待 {len(active_devices)} 台设备在主页面就绪...")
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
                    logger.error(f"{LogIcon.FAIL} 设备 [{dev_name}] 发生异常: {e}")
                    dev_results[dev_name] = False

        failed = [d for d, success in dev_results.items() if not success]
        if failed:
            logger.error(f"{LogIcon.FAIL} 以下设备未能在主页面就绪: {failed}")
            return False
        logger.info(f"{LogIcon.SUCCESS} 所有设备已全部在主页面就绪！")
        return True

    @pytest.fixture(autouse=False)
    def setup_special_env(self, request):
        """初始化 5 台设备 (Device_5 ~ Device_9) 的驱动及对应群聊全套 Page Object 实例"""
        for idx in range(5, 10):
            try:
                driver = request.getfixturevalue(f'driver_device{idx}')
                if driver:
                    setattr(self, f'mainPageT{idx}', MainPage(driver))
                    setattr(self, f'chatPageT{idx}', ChatPage(driver))
                    setattr(self, f'chatListPageT{idx}', ChatListPage(driver))
                    setattr(self, f'groupSettingPageT{idx}', GroupSettingPage(driver))
                    setattr(self, f'groupManagerPageT{idx}', GroupManagerPage(driver))
                    setattr(self, f'emojiPageT{idx}', ChatEmojiPage(driver))
                    setattr(self, f'chatImagePageT{idx}', ChatImagePage(driver))
                    setattr(self, f'chatPositionPageT{idx}', ChatPositionPage(driver))
                    self.__class__._class_driver = driver
            except Exception as e:
                logger.warning(f'{LogIcon.WARN} 设备 driver_device{idx} 启动失败: {e}')

        self.__class__._in_chat = False
        self.__class__._chat_target = None

        # 确保 5 台设备全部到达主页面起跑线
        self._wait_all_devices_on_main_page(range(5, 10))

        yield
        try:
            self._wait_all_devices_on_main_page(range(5, 10))
        except Exception as e:
            logger.error(f'{LogIcon.FAIL} Teardown 返回主页面失败: {e}')

    # 内部调度方法-多设备异步并发执行进出【更多/群设置】详情页操作
    def _run_async_multi_device_toggle_detail(
        self,
        device_groups_map: dict,
        loop_count: int = 5,
        interval: float = 0.2
    ) -> None:
        """
        多设备异步并发执行进出【更多/群设置】详情页统一调度执行器
        :param device_groups_map: 设备序号与群策略映射 {idx: (dev_name, [group_list])}
        :param loop_count: 循环执行轮数
        :param interval: 每轮进出间隔（秒）
        """
        ready_tasks = []
        for idx, (dev_name, group_list) in device_groups_map.items():
            clp = getattr(self, f'chatListPageT{idx}', None)
            cp = getattr(self, f'chatPageT{idx}', None)
            gsp = getattr(self, f'groupSettingPageT{idx}', None)
            if clp and cp:
                ready_tasks.append((idx, dev_name, clp, cp, gsp, group_list))
            else:
                logger.warning(f'{LogIcon.WARN} 设备 {dev_name} 未就绪，跳过此设备')

        if not ready_tasks:
            logger.warning(f'{LogIcon.WARN} 没有可用设备执行群聊特殊用例并发测试')
            return

        barrier = threading.Barrier(parties=len(ready_tasks)) if len(ready_tasks) > 1 else None
        exceptions = []

        def worker_toggle_detail(idx: int, dev_name: str, chat_list_page: ChatListPage, chat_page: ChatPage, group_setting_page: Optional[GroupSettingPage], group_list: list):
            try:
                g_setting_page = group_setting_page or GroupSettingPage(chat_page.driver)
                target_group = group_list[0] if isinstance(group_list, list) else group_list
                group_name = target_group.name if hasattr(target_group, 'name') else str(target_group)

                # 1. 各设备进入各自目标群聊
                logger.info(f"{LogIcon.ACTION} 📍 [{dev_name}] 正在进入目标群聊【{group_name}】...")
                chat_list_page.enter_chat(group_name)
                is_loaded = chat_page.wait_for_chat_page_load(timeout=10)
                check.is_true(is_loaded, f"[{dev_name}] 进入目标群聊页面加载超时")

                # 2. 线程同步栅栏：等待所有设备在群聊起跑线就绪后同一瞬间放行
                if barrier:
                    logger.info(f"{LogIcon.WAIT} [{dev_name}] 已在群聊窗口就绪，等待全设备同步对齐...")
                    try:
                        barrier.wait(timeout=10)
                    except threading.BrokenBarrierError:
                        logger.error(f"{LogIcon.FAIL} [{dev_name}] 栅栏等待超时破损，强制继续执行")
                logger.info(f"{LogIcon.ACTION} [{dev_name}] 栅栏放行！开始高频并发重复执行【进出群详情设置】(共 {loop_count} 轮)...")

                # 3. 循环重复执行：点击右上角更多 -> 返回群聊页面
                for cycle in range(1, loop_count + 1):
                    logger.info(f"{LogIcon.ACTION} [{dev_name}] [第 {cycle}/{loop_count} 轮] 点击右上角【更多】进入群设置详情...")
                    chat_page.click_more_button()
                    setting_loaded = g_setting_page.wait_for_setting_page_load(timeout=5)
                    check.is_true(setting_loaded, f"[{dev_name}] 第 {cycle} 轮进入群设置详情页未加载完成")

                    logger.info(f"{LogIcon.ACTION} [{dev_name}] [第 {cycle}/{loop_count} 轮] 点击返回群聊页面...")
                    g_setting_page.click_iv_back_button()
                    chat_loaded = chat_page.wait_for_chat_page_load(timeout=5)
                    check.is_true(chat_loaded, f"[{dev_name}] 第 {cycle} 轮返回群聊页面未加载完成")

                    time.sleep(interval)
                logger.info(f"{LogIcon.SUCCESS} [{dev_name}] 全部 {loop_count} 轮高频进出群详情动作执行完成！")
                # 4. 执行完成后退回主会话列表
                chat_page.back_to_chat_list_page()
            except Exception as e:
                logger.error(f"{LogIcon.FAIL} [{dev_name}] 高频进出群详情发生异常: {e}")
                exceptions.append((dev_name, str(e)))

        threads = []
        for item in ready_tasks:
            t = threading.Thread(
                target=worker_toggle_detail,
                args=(item[0], item[1], item[2], item[3], item[4], item[5]),
                name=f"Thread_{item[1]}_ToggleDetail"
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        if exceptions:
            err_details = "\n".join([f"设备 [{d}]: {err}" for d, err in exceptions])
            pytest.fail(f"❌ 5台设备并发高频进出群详情过程中发生异常:\n{err_details}")


    # =========================================================================
    # 特殊用例 1：5台设备同时进入群聊并高频并发进出【更多/群设置】详情页
    # =========================================================================
    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('群聊高频进出群设置详情')
    @allure.title('5台设备同时进入群聊并高频并发进出【更多/群设置】详情页压测-状态：未完成')
    def test_group_simultaneous_toggle_detail_multi_device(self, setup_special_env):
        """
        用例名称：5台设备同时进入群聊并高频并发进出【更多/群设置】详情页压测
        业务流程：
        0. 前置准备：并发等待所有设备在主页面就绪
        1. 5台设备多端异步并发执行进出群详情设置操作：
           - 各设备进入各自指定群聊（测试群001）
           - 同步栅栏对齐后统一触发
           - 点击右上角【更多】进入群设置详情页
           - 点击顶部返回按钮退回到群聊页面
           - 循环重复执行上述进出动作（默认 5 轮）
           - 执行完毕安全退回主页面
        """
        dev5_groups = [TEST_GROUPS[0]]
        dev6_groups = [TEST_GROUPS[0]]
        dev7_groups = [TEST_GROUPS[0]]
        dev8_groups = [TEST_GROUPS[0]]
        dev9_groups = [TEST_GROUPS[0]]
        device_groups_map = {
            5: ('Device_5', dev5_groups),
            6: ('Device_6', dev6_groups),
            7: ('Device_7', dev7_groups),
            8: ('Device_8', dev8_groups),
            9: ('Device_9', dev9_groups)
        }

        with allure.step("0. 前置准备：并发等待所有设备在主页面就绪"):
            logger.info(f"{LogIcon.WAIT} [Multi Device Group Special Test] 检查并等待所有参与设备在主页面就绪...")
            is_ready = self._wait_all_devices_on_main_page(list(device_groups_map.keys()))
            check.is_true(is_ready, "所有设备启动后应成功到达主页面")

        with allure.step("1. 5台设备多端异步并发执行进出群详情设置操作"):
            self._run_async_multi_device_toggle_detail(
                device_groups_map=device_groups_map,
                loop_count=10000,
                interval=0.0001
            )

    # =========================================================================
    # 特殊用例 2：群主全员禁言与多成员并发发言的临界竞态
    # =========================================================================
    @allure.story('群禁言竞态拦截')
    @allure.title('群主全员禁言瞬间4台成员设备并发尝试发言竞态拦截校验-状态：已完成')
    @pytest.mark.skip("未完成")
    def test_group_mute_race_condition_multi_device(self, setup_special_env):
        """
        用例名称：群主全员禁言瞬间4台成员设备并发尝试发言竞态拦截校验
        核心场景：
        1. 设备 5 作为群主进入【群管理】页面准备操作【全员禁言】开关；
        2. 设备 6 ~ 9 作为普通群成员提前进入该群聊天界面，输入框处于就绪状态；
        3. 栅栏协同触发：设备 5 开启【全员禁言】，设备 6 ~ 9 几乎同一时刻尝试点击发送消息；
        4. 验证点：
           - 禁言指令下发后，所有成员设备在接收到广播后输入框应实时被禁用，并出现“禁言中”标识；
           - 处于禁言状态下的消息发送应被服务端/客户端彻底拦截；
           - 恢复环境：群主关闭【全员禁言】开关，校验成员端输入框恢复正常可用状态。
        """
        target_group_name = GROUP_STRATEGY.name

        owner_idx = 5
        member_indices = [6, 7, 8, 9]

        owner_chat_page = getattr(self, f'chatPageT{owner_idx}', None)
        owner_setting_page = getattr(self, f'groupSettingPageT{owner_idx}', None)
        owner_manager_page = getattr(self, f'groupManagerPageT{owner_idx}', None)
        owner_list_page = getattr(self, f'chatListPageT{owner_idx}', None)

        if not (owner_chat_page and owner_setting_page and owner_manager_page and owner_list_page):
            pytest.skip(f"群主设备 Device_{owner_idx} 未完全就绪，跳过全员禁言竞态用例")

        # 筛选就绪的成员设备
        active_members = []
        for m_idx in member_indices:
            cp = getattr(self, f'chatPageT{m_idx}', None)
            clp = getattr(self, f'chatListPageT{m_idx}', None)
            if cp and clp:
                active_members.append((m_idx, f"Device_{m_idx}", clp, cp))

        if not active_members:
            pytest.skip("没有可用的成员设备执行禁言竞态测试，跳过")

        # 1. 群主进入群管理界面准备就绪
        with allure.step("1. 群主端进入目标群聊的【群管理】页面"):
            owner_list_page.enter_chat(target_group_name)
            owner_chat_page.wait_for_chat_page_load(timeout=10)
            owner_chat_page.click_more_button()
            owner_setting_page.wait_for_setting_page_load()
            owner_setting_page.click_group_manager()
            owner_manager_page.wait_for_group_manager_page_load()
            logger.info(f"{LogIcon.ACTION} 👑 群主端已在【群管理】页面就绪")

        # 2. 成员设备进入群聊聊天窗口
        with allure.step("2. 所有普通成员设备进入目标群聊聊天界面"):
            for _, m_name, m_clp, m_cp in active_members:
                m_clp.enter_chat(target_group_name)
                m_cp.wait_for_chat_page_load(timeout=10)
                logger.info(f"{LogIcon.SUCCESS} 👤 成员 [{m_name}] 已进入群聊等待发令")

        # 3. 并发发令枪：群主开禁言，成员并发点击发送
        barrier = threading.Barrier(parties=1 + len(active_members))
        race_exceptions = []

        def owner_action():
            try:
                barrier.wait(timeout=15)
                logger.info(f"{LogIcon.ACTION} 👑 [Race Trigger] 群主端触发：开启【全员禁言】开关！")
                owner_manager_page.click_all_member_mute_switch(checked_str='true')
            except Exception as e:
                logger.error(f"{LogIcon.FAIL} 👑 群主端开启禁言异常: {e}")
                race_exceptions.append(("Owner_Device_5", str(e)))

        def member_action(m_idx: int, m_name: str, m_cp: ChatPage):
            try:
                barrier.wait(timeout=15)
                # 稍作微小延迟模拟竞态临界点发言
                time.sleep(0.05 * (m_idx - 5))
                logger.info(f"{LogIcon.ACTION} 👤 [{m_name}] 正在尝试并发发送发言测试消息...")
                m_cp.send_message(f"【禁言竞态尝试】来自 {m_name}")
            except Exception as e:
                logger.info(f"{LogIcon.FAIL} ℹ️ [{m_name}] 发送被拦截或异常: {e}")

        threads = [threading.Thread(target=owner_action, name="Thread_Owner_Mute")]
        for m_idx, m_name, _, m_cp in active_members:
            threads.append(
                threading.Thread(target=member_action, args=(m_idx, m_name, m_cp), name=f"Thread_{m_name}_Speak")
            )

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 4. 验证成员端状态同步被禁用
        with allure.step("3. 校验各成员设备输入框在全员禁言后已处于禁用状态"):
            time.sleep(1.5)  # 等待服务端全员禁言 CMD 广播抵达各端
            for _, m_name, _, m_cp in active_members:
                title, _ = m_cp.get_input_disabled_info()
                is_disabled = m_cp.is_input_disabled()
                logger.info(f"{LogIcon.FIND} 校验成员 [{m_name}] 禁言标识: title='{title}', is_disabled={is_disabled}")
                check.is_true(is_disabled or bool(title), f"[{m_name}] 全员禁言后输入框应被禁用")

        # 5. 环境恢复：群主关闭全员禁言，并校验成员端恢复正常
        with allure.step("4. 环境复原：群主关闭【全员禁言】并校验成员端输入框恢复可用"):
            owner_manager_page.click_all_member_mute_switch(checked_str='false')
            time.sleep(1.5)
            for _, m_name, _, m_cp in active_members:
                is_disabled_after = m_cp.is_input_disabled()
                check.is_false(is_disabled_after, f"[{m_name}] 关闭全员禁言后，输入框应恢复可用")
                m_cp.back_to_chat_list_page()

            owner_manager_page.click_iv_back_button()
            owner_setting_page.click_iv_back_button()
            owner_chat_page.back_to_chat_list_page()

        if race_exceptions:
            pytest.fail(f"❌ 禁言竞态执行发生异常: {race_exceptions}")

    # =========================================================================
    # 特殊用例 3：5台设备同群富媒体消息并发混合风暴 (文本+表情+图片+位置)
    # =========================================================================
    @allure.story('富媒体混合风暴')
    @allure.title('5台设备同群富媒体消息并发混合发送(文本+表情+图片+位置)-状态：未完成')
    @pytest.mark.skip("未完成")
    def test_group_multi_media_storm_multi_device(self, setup_special_env):
        """
        用例名称：5台设备同群富媒体消息并发混合发送
        核心场景：
        1. 5 台设备同时进入同一群聊（GROUP_STRATEGY.name）；
        2. 分工并发分发不同类型载荷：
           - Device_5: 密集长文本/特殊符号测试
           - Device_6: 表情包/Emoji 连续发送
           - Device_7: 相册/图片上传发送
           - Device_8: 位置共享/定位卡片发送
           - Device_9: 模板文本批量群发
        3. 验证混合通道多路复用时，富媒体分片与长连接消息不发生死锁或错乱。
        """
        target_group_name = GROUP_STRATEGY.name
        ready_indices = []
        for idx in range(5, 10):
            clp = getattr(self, f'chatListPageT{idx}', None)
            cp = getattr(self, f'chatPageT{idx}', None)
            if clp and cp:
                ready_indices.append(idx)

        if len(ready_indices) < 3:
            pytest.skip("就绪设备不足 3 台，跳过多媒体混合风暴用例")

        barrier = threading.Barrier(parties=len(ready_indices))
        exceptions = []

        def worker_media(idx: int):
            dev_name = f"Device_{idx}"
            chat_list_page: ChatListPage = getattr(self, f'chatListPageT{idx}')
            chat_page: ChatPage = getattr(self, f'chatPageT{idx}')
            emoji_page: ChatEmojiPage = getattr(self, f'emojiPageT{idx}', None)
            image_page: ChatImagePage = getattr(self, f'chatImagePageT{idx}', None)
            position_page: ChatPositionPage = getattr(self, f'chatPositionPageT{idx}', None)

            try:
                chat_list_page.enter_chat(target_group_name)
                chat_page.wait_for_chat_page_load(timeout=10)
                logger.info(f"{LogIcon.ACTION} [{dev_name}] 已进入群聊，等待富媒体并发栅栏放行...")

                barrier.wait(timeout=30)
                logger.info(f"{LogIcon.ACTION} [{dev_name}] 富媒体并发启动！")

                # 根据设备编号执行差异化富媒体发送动作
                if idx == 5:
                    # 设备 5：长文本与特殊字符组合
                    chat_page.send_message("【混合风暴-文本通道】并发压测核心流水校验数据...")
                    chat_page.send_message("🎉🎊🎈🎁 Special Unicode Symbols: 🚀⚡🔥")
                elif idx == 6 and emoji_page:
                    # 设备 6：发送表情
                    try:
                        chat_page.click_emoji_button()
                        emoji_page.send_first_emoji()
                        logger.info(f"{LogIcon.SUCCESS} 😃 [{dev_name}] 发送表情成功")
                    except Exception as e:
                        logger.warning(f"{LogIcon.WARN} [{dev_name}] 发送表情降级为文本: {e}")
                        chat_page.send_message("【混合风暴-表情模拟】[微笑][大笑]")
                elif idx == 7 and image_page:
                    # 设备 7：发送图片 (若支持图片库选择)
                    try:
                        chat_page.click_more_options_button()
                        image_page.send_first_album_image()
                        logger.info(f"{LogIcon.SUCCESS} 🖼️ [{dev_name}] 发送相册图片成功")
                    except Exception as e:
                        logger.warning(f"{LogIcon.WARN} [{dev_name}] 发送图片降级为文本: {e}")
                        chat_page.send_message("【混合风暴-图片模拟】IMG_DATA_HASH_7788")
                elif idx == 8 and position_page:
                    # 设备 8：发送位置
                    try:
                        chat_page.click_more_options_button()
                        position_page.send_current_position()
                        logger.info(f"{LogIcon.SUCCESS} 📍 [{dev_name}] 发送地理位置成功")
                    except Exception as e:
                        logger.warning(f"{LogIcon.WARN} [{dev_name}] 发送位置降级为文本: {e}")
                        chat_page.send_message("【混合风暴-位置模拟】北京市海淀区中关村南大街")
                else:
                    # 设备 9：常规高频短文本
                    chat_page.send_message(f"【混合风暴-广播通道】Device_{idx} 实时数据同步汇报")

                time.sleep(1)
                chat_page.back_to_chat_list_page()
            except Exception as e:
                logger.error(f"{LogIcon.FAIL} [{dev_name}] 富媒体发送异常: {e}")
                exceptions.append((dev_name, str(e)))

        threads = [threading.Thread(target=worker_media, args=(idx,), name=f"Thread_Dev{idx}_Media") for idx in ready_indices]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        if exceptions:
            pytest.fail(f"❌ 富媒体混合并发风暴中发生异常: {exceptions}")

    # =========================================================================
    # 特殊用例 4：5台设备分别对5个不同群聊同时进行并发群发广播
    # =========================================================================
    @allure.story('多群并行广播')
    @allure.title('5台设备分别对5个不同群聊同时进行持续广播压测-状态：未完成')
    @pytest.mark.skip("未完成")
    def test_group_multi_target_parallel_broadcast_multi_device(self, setup_special_env):
        """
        用例名称：5台设备分别对5个不同群聊同时进行持续广播压测
        核心场景：
        1. 设备 5 ~ 9 分别分配 TEST_GROUPS 中的 5 个不同群聊策略（测试群001 ~ 测试群005）；
        2. 各设备独立、并行地在各自目标群聊中连续发送多条 CSV 文本数据；
        3. 验证长连接多会话状态下的数据路由隔离与吞吐吞吐能力。
        """
        ready_tasks = []
        for idx in range(5, 10):
            clp = getattr(self, f'chatListPageT{idx}', None)
            cp = getattr(self, f'chatPageT{idx}', None)
            group_strategy = TEST_GROUPS[idx - 5] if (idx - 5) < len(TEST_GROUPS) else TEST_GROUPS[0]
            if clp and cp:
                ready_tasks.append((idx, f"Device_{idx}", clp, cp, group_strategy))

        if not ready_tasks:
            pytest.skip("无就绪设备，跳过5群并行广播测试")

        barrier = threading.Barrier(parties=len(ready_tasks))
        exceptions = []

        def worker_parallel_broadcast(idx: int, dev_name: str, clp: ChatListPage, cp: ChatPage, group_target):
            try:
                # 1. 各设备进入各自目标群聊
                clp.enter_chat(group_target.name)
                cp.wait_for_chat_page_load(timeout=10)
                logger.info(f"{LogIcon.WAIT} 📢 [{dev_name}] 进入指定群聊【{group_target.name}】，等待并发发令...")

                # 2. 栅栏同步放行
                barrier.wait(timeout=30)
                logger.info(f"{LogIcon.ACTION} [{dev_name}] 开始向【{group_target.name}】并发广播发送...")

                # 3. 发送测试内容
                for loop in range(1, 4):
                    msg = f"[{dev_name}] 并行广播消息_批次{loop}_{group_target.name}"
                    cp.send_message(msg)
                    time.sleep(0.15)

                logger.info(f"{LogIcon.SUCCESS} [{dev_name}] 群聊【{group_target.name}】广播发送完成，验证消息存在")
                count = cp.get_total_message_count()
                check.greater(count, 0, f"[{dev_name}] 群聊【{group_target.name}】消息数应大于 0")

                # 4. 退回主列表
                cp.back_to_chat_list_page()
            except Exception as e:
                logger.error(f"{LogIcon.FAIL} [{dev_name}] 广播发送发生异常: {e}")
                exceptions.append((dev_name, str(e)))

        threads = [
            threading.Thread(
                target=worker_parallel_broadcast,
                args=(item[0], item[1], item[2], item[3], item[4]),
                name=f"Thread_Broadcast_{item[1]}"
            )
            for item in ready_tasks
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        if exceptions:
            pytest.fail(f"❌ 多群并行广播发送出现异常: {exceptions}")
