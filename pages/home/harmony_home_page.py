import time
from typing import List, Optional
from selenium.webdriver.remote.webelement import WebElement
from common.base_page import BasePage
from core.logger_utils import logger, LogIcon
from locators.home.home_locator_hos import HomeLocatorHos


class HarmonyHomePage(BasePage):
    """
    鸿蒙 NEXT 平台主页业务对象类 (HarmonyOS HomePage Page Object)
    封装主页导航、搜索体系、分类页签、会话列表流及侧滑快捷操作。
    """

    # --------------------------------------------------------------------------
    # 1. 主页加载感知与生命周期健康探查
    # --------------------------------------------------------------------------

    def wait_home_page(self, timeout: int = 10) -> bool:
        """
        等待鸿蒙主页面完全加载就绪：is_home_page_loaded 状态探查进行优雅轮询，确保界面完全就绪。
        """
        logger.info(f"{LogIcon.WAIT} 正在等待鸿蒙端主页渲染完成 (超时上限: {timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_home_page_loaded(timeout=0.3):
                logger.info(f"{LogIcon.SUCCESS} 鸿蒙端主页加载成功")
                return True
            time.sleep(0.2)

        logger.error(f"{LogIcon.FAIL} 等待鸿蒙端主页加载超时 ({timeout}s)")
        return False

    def is_home_page_loaded(self, timeout: float | int = 1.0, show_log: bool = False) -> bool:
        """
        快速判断当前是否已位于鸿蒙主页面 (高频静默探查，支持按需日志输出)
        :param timeout: 单次探查超时时间 (秒)
        :param show_log: 是否输出状态结论日志 (默认 False，避免在 while 轮询/自愈中刷屏)
        :return: True(已在主页) / False(未在主页)
        """
        is_loaded = bool(
            self.find_elements(HomeLocatorHos.LEFT_MENU, timeout=timeout, raise_exception=False, expect_missing=True)
            or self.find_elements(HomeLocatorHos.MIDDLE_TITLE, timeout=timeout, raise_exception=False, expect_missing=True)
        )
        if show_log:
            if is_loaded:
                logger.info(f"{LogIcon.SUCCESS} 鸿蒙主页面状态探查: 已就绪 (左侧菜单/主标题已呈现)")
            else:
                logger.warning(f"{LogIcon.WARN} 鸿蒙主页面状态探查: 未就绪")
        return is_loaded

    def ensure_in_home_page(self, max_retries: int = 3) -> bool:
        """
        鸿蒙原生主页轻量自愈：
        先探查当前是否已在主页；若不在（如侧边栏打开、弹窗或搜索层残留），则轻柔按返回键复位，确保停留在主页。
        """
        if self.is_home_page_loaded(timeout=0.5):
            return True
        logger.info(f"{LogIcon.ACTION} 检测到未处于鸿蒙主页，执行轻量自愈复位...")
        for i in range(max_retries):
            self.back()
            time.sleep(0.3)
            if self.is_home_page_loaded(timeout=0.5):
                logger.info(f"{LogIcon.SUCCESS} 鸿蒙主页面复位成功 (尝试次数: {i + 1})")
                return True
        logger.warning(f"{LogIcon.WARN} 鸿蒙主页面复位未完全就绪")
        return False

    def get_top_middle_title(self, timeout: int = 2) -> str:
        """获取主页顶部中间标题文本 (如 '三条' 或状态文本)"""
        logger.info(f"{LogIcon.FIND} 正在获取鸿蒙主页顶部中间标题...")
        title = self.get_attribute(HomeLocatorHos.MIDDLE_TITLE, "text", timeout=timeout) or ""
        logger.info(f"{LogIcon.ACTION} 获取到鸿蒙主页顶部标题: '{title}'")
        return title

    def click_home_title(self, timeout: int = 2) -> None:
        """点击主页顶部中间标题 (通常用于快速返回列表顶部或触发连接状态同步)"""
        logger.info(f"{LogIcon.ACTION} 点击鸿蒙主页顶部标题")
        self.click(HomeLocatorHos.MIDDLE_TITLE, force_wait=True, timeout=timeout)

    # --------------------------------------------------------------------------
    # 2. 顶部导航与拓展功能菜单
    # --------------------------------------------------------------------------

    def open_left_menu(self, timeout: int = 2) -> None:
        """点击顶部左上角侧边栏/个人中心抽屉菜单入口"""
        logger.info(f"{LogIcon.ACTION} 点击打开鸿蒙主页左侧抽屉菜单")
        self.click(HomeLocatorHos.LEFT_MENU, timeout=timeout)
        time.sleep(0.3)

    def click_add_button(self, timeout: int = 2) -> None:
        """点击主页顶部右上角 '+' 按钮展开功能菜单"""
        logger.info(f"{LogIcon.ACTION} 点击主页右上角 '+' 功能菜单")
        self.click(HomeLocatorHos.RIGHT_MENU, force_wait=True, timeout=timeout)
        time.sleep(0.3)

    def click_start_group_chat(self, timeout: int = 2) -> None:
        """点击展开菜单项：发起群聊"""
        logger.info(f"{LogIcon.ACTION} 点击 '+' 菜单项: 发起群聊")
        self.click(HomeLocatorHos.EXPAND_START_GROUP_CHAT, force_wait=True, timeout=timeout)

    def click_add_friend(self, timeout: int = 2) -> None:
        """点击 '+' 菜单项: 添加朋友"""
        logger.info(f"{LogIcon.ACTION} 点击 '+' 菜单项: 添加朋友")
        self.click(HomeLocatorHos.EXPAND_ADD_FRIEND, force_wait=True, timeout=timeout)

    def click_scan(self, timeout: int = 2) -> None:
        """点击 '+' 菜单项: 扫一扫"""
        logger.info(f"{LogIcon.ACTION} 点击 '+' 菜单项: 扫一扫")
        self.click(HomeLocatorHos.EXPAND_SCAN, force_wait=True, timeout=timeout)

    # --------------------------------------------------------------------------
    # 3. 搜索交互与状态自愈
    # --------------------------------------------------------------------------

    def click_search(self, timeout: int = 2) -> None:
        """点击主页全局搜索栏进入搜索模式"""
        logger.info(f"{LogIcon.ACTION} 点击鸿蒙主页搜索栏")
        self.click(HomeLocatorHos.SEARCH, force_wait=True, timeout=timeout)

    def input_search_text(self, text: str, timeout: int = 2) -> None:
        """向搜索框输入检索文本"""
        logger.info(f"{LogIcon.ACTION} 输入搜索关键字: '{text}'")
        self.send_keys(HomeLocatorHos.SEARCH_INPUT, text, timeout=timeout)

    def click_search_clear(self, timeout: int = 2) -> None:
        """点击搜索内容一键清空按钮"""
        logger.info(f"{LogIcon.ACTION} 点击清空搜索内容按钮")
        self.click(HomeLocatorHos.SEARCH_CLEAR, force_wait=True, timeout=timeout)

    def click_search_cancel(self, timeout: int = 2) -> None:
        """点击搜索栏右侧取消/退出按钮关闭搜索覆盖层"""
        logger.info(f"{LogIcon.ACTION} 点击取消按钮退出搜索")
        self.click(HomeLocatorHos.SEARCH_CANCEL, force_wait=True, timeout=timeout)

    def exit_search_if_present(self, timeout: float = 0.5) -> bool:
        """
        状态自愈：若当前处于搜索覆盖层页面，主动点击取消按钮退出搜索回到主会话列表
        """
        if self.is_element_exist(HomeLocatorHos.SEARCH_CANCEL, timeout=timeout):
            logger.info(f"{LogIcon.ACTION} 检测到搜索结果覆盖层，主动点击取消按钮复位回到主页")
            self.click(HomeLocatorHos.SEARCH_CANCEL, force_wait=True)
            time.sleep(0.3)
            return True
        return False

    # --------------------------------------------------------------------------
    # 4. 底部主导航栏与分类页签切换
    # --------------------------------------------------------------------------

    def click_bottom_expand_button(self, timeout: int = 2) -> None:
        """点击主页底部右侧展开菜单按钮"""
        logger.info(f"{LogIcon.ACTION} 点击主页底部展开菜单按钮")
        self.click(HomeLocatorHos.EXPAND_MENU, force_wait=True, timeout=timeout)

    def click_bottom_close_expand_button(self, timeout: int = 2) -> None:
        """主页 - 收起/关闭底部扩展菜单"""
        logger.info(f"{LogIcon.ACTION} 准备收起底部扩展菜单")
        if self.is_element_exist(HomeLocatorHos.FRIEND, timeout=0.5):
            self.click(HomeLocatorHos.COLLAPSE_MENU, force_wait=True, timeout=timeout)
            logger.info(f"{LogIcon.SUCCESS} 已点击收起底部扩展菜单")

    def ensure_bottom_menu_expanded(self, timeout: int = 2) -> None:
        """状态自愈探查：确保底部页签已处于展开可见状态；若未展开则自动点击展开"""
        if not self.is_element_exist(HomeLocatorHos.FRIEND, timeout=0.3):
            logger.info(f"{LogIcon.WAIT} 底部页签处于折叠状态，主动点击展开按钮...")
            self.click_bottom_expand_button(timeout=timeout)
            time.sleep(0.3)

    def click_friend(self, timeout: int = 2) -> None:
        """切换至底部 '好友' 分类页签 (自带智能展开自愈)"""
        logger.info(f"{LogIcon.ACTION} 切换至底部 '好友' 页签")
        self.ensure_bottom_menu_expanded(timeout=timeout)
        self.click(HomeLocatorHos.FRIEND, force_wait=True, timeout=timeout)

    def click_group(self, timeout: int = 2) -> None:
        """切换至底部 '群聊' 分类页签 (自带智能展开自愈)"""
        logger.info(f"{LogIcon.ACTION} 切换至底部 '群聊' 页签")
        self.ensure_bottom_menu_expanded(timeout=timeout)
        self.click(HomeLocatorHos.GROUP, force_wait=True, timeout=timeout)

    def click_dynamic(self, timeout: int = 2) -> None:
        """切换至底部 '动态' 朋友圈页签 (自带智能展开自愈)"""
        logger.info(f"{LogIcon.ACTION} 切换至底部 '动态' 页签")
        self.ensure_bottom_menu_expanded(timeout=timeout)
        self.click(HomeLocatorHos.DYNAMIC, force_wait=True, timeout=timeout)

    def get_dynamic_unread_msg_count(self) -> str:
        """获取底部 '动态' 页签未读消息红点角标数量"""
        logger.info(f"{LogIcon.FIND} 获取动态未读消息红点角标...")
        count = self.get_attribute(HomeLocatorHos.DYNAMIC_UNREAD_MSG, "text") or ""
        logger.info(f"{LogIcon.ACTION} 动态未读消息数: '{count}'")
        return count

    # --------------------------------------------------------------------------
    # 5. 会话列表管理与精准定位
    # --------------------------------------------------------------------------

    def get_conversation_list(self) -> List[WebElement]:
        """获取当前屏幕内渲染的所有会话卡片条目列表"""
        logger.info(f"{LogIcon.FIND} 获取当前屏幕内全部会话列表...")
        elements = self.find_elements(HomeLocatorHos.CONVERSATION_ITEM, raise_exception=False) or []
        logger.info(f"{LogIcon.SUCCESS} 当前已渲染会话卡片数量: {len(elements)}")
        return elements

    def get_conversation_count(self) -> int:
        """获取当前主页面可见会话卡片总数"""
        return len(self.get_conversation_list())

    def click_conversation_by_index(self, index: int = 0, timeout: int = 2) -> None:
        """按列表索引序号点击打开指定会话 (0-indexed)"""
        logger.info(f"{LogIcon.ACTION} 准备按索引点击会话 (序号: {index})")
        elements = self.find_elements(HomeLocatorHos.CONVERSATION_ITEM, timeout=timeout)
        if not elements or index >= len(elements):
            raise IndexError(f"会话列表索引越界: 目标索引 {index}, 当前仅存在 {len(elements) if elements else 0} 个会话")
        elements[index].click()

    def click_conversation_by_name(self, name: str, timeout: int = 3) -> bool:
        """按联系人或群聊名称精准检索并点击进入会话"""
        logger.info(f"{LogIcon.ACTION} 按名称定位并点击会话: '{name}'")
        loc = HomeLocatorHos.get_conver_by_name(name)
        elem = self.find_element(loc, timeout=timeout, raise_exception=False)
        if elem:
            elem.click()
            logger.info(f"{LogIcon.SUCCESS} 成功点击会话: '{name}'")
            return True
        logger.warning(f"{LogIcon.WARN} 未能在主页会话列表中找到目标: '{name}'")
        return False

    def is_conversation_exist(self, name: str, timeout: int = 2) -> bool:
        """检查指定名称的会话是否存在于当前会话列表"""
        loc = HomeLocatorHos.get_conver_by_name(name)
        return self.is_element_exist(loc, timeout=timeout)

    def get_conversation_last_message(self, name: str, timeout: int = 2) -> str:
        """获取指定会话条目所展示的最新一条消息摘要文本"""
        logger.info(f"{LogIcon.FIND} 正在获取会话 '{name}' 的最新消息预览...")
        loc = HomeLocatorHos.get_message_by_name(name)
        msg = self.get_attribute(loc, "text", timeout=timeout) or ""
        logger.info(f"{LogIcon.ACTION} 会话 '{name}' 最新消息: '{msg}'")
        return msg

    def get_conversation_unread_count(self, name: str, timeout: int = 2) -> str:
        """获取指定会话卡片上展示的未读消息计数气泡文本"""
        loc = HomeLocatorHos.get_unread_count_by_name(name)
        count = self.get_attribute(loc, "text", timeout=timeout) or ""
        logger.info(f"{LogIcon.FIND} 会话 '{name}' 未读消息数: '{count}'")
        return count

    def get_conversation_time(self, name: str, timeout: int = 2) -> str:
        """获取指定会话卡片右侧展示的最后更新时间 (如 '18:59' 或 '昨天')"""
        loc = HomeLocatorHos.get_time_by_name(name)
        time_text = self.get_attribute(loc, "text", timeout=timeout) or ""
        logger.info(f"{LogIcon.FIND} 会话 '{name}' 最后更新时间: '{time_text}'")
        return time_text

    def get_conversation_status_tag(self, name: str, tag: str = "", timeout: int = 2) -> str:
        """
        公用获取指定会话的前缀状态标签文本 (统一支持: 草稿、未读或已读、进群申请、@所有人、有人@我)
        :param name: 会话或联系人名称
        :param tag: 可选筛选特定状态类型 (如 '草稿'、'未读'、'已读'、'进群申请'、'@所有人'、'有人@我')；若留空则直接获取该会话当前展示的任意状态标签
        :param timeout: 超时等待时间 (秒)
        :return: 状态标签文本 (未匹配或不存在时返回空字符串 "")
        """
        loc = HomeLocatorHos.get_status_tag_by_name(name, tag=tag)
        text = self.get_attribute(loc, "text", timeout=timeout) or ""
        logger.info(f"{LogIcon.FIND} 会话 '{name}' 状态标签{f'[{tag}]' if tag else ''}: '{text}'")
        return text

    def has_conversation_status_tag(self, name: str, tag: str = "", timeout: float = 1.0) -> bool:
        """公用判断指定会话是否展示了某个状态标签 (草稿、未读/已读、进群申请、@所有人、有人@我)"""
        loc = HomeLocatorHos.get_status_tag_by_name(name, tag=tag)
        return self.is_element_exist(loc, timeout=timeout)

    def get_conversation_draft(self, name: str, timeout: int = 2) -> str:
        """获取指定会话条目中的 '[草稿]' 标识文本 (公用底层通用状态提取)"""
        return self.get_conversation_status_tag(name, tag="草稿", timeout=timeout)

    def get_conversation_remind_status(self, name: str, timeout: int = 2) -> str:
        """获取指定会话的状态强提醒标签 (如 [@所有人], [有人@我], [进群申请]) (公用底层通用状态提取)"""
        return self.get_conversation_status_tag(name, timeout=timeout)

    def scroll_to_conversation(self, name: str, max_swipes: int = 5, timeout: float = 1.0) -> bool:
        """
        在主页会话列表中自适应滚动查找目标会话：
        若当前屏幕未出现，平滑向上滑动屏幕检索直至目标会话进入视口。
        """
        logger.info(f"{LogIcon.FIND} 正在滚动检索会话: '{name}' (最大滑动尝试: {max_swipes}次)")
        loc = HomeLocatorHos.get_conver_by_name(name)
        for i in range(max_swipes + 1):
            if self.is_element_exist(loc, timeout=timeout):
                logger.info(f"{LogIcon.SUCCESS} 已找到目标会话: '{name}'")
                return True
            if i < max_swipes:
                logger.info(f"{LogIcon.ACTION} 当前屏未见 '{name}'，执行第 {i + 1} 次向上滚动...")
                window_size = self.driver.get_window_size()
                mid_x = window_size["width"] // 2
                start_y = int(window_size["height"] * 0.75)
                end_y = int(window_size["height"] * 0.35)
                self.swipe(mid_x, start_y, mid_x, end_y, duration=400)
                time.sleep(0.4)
        logger.warning(f"{LogIcon.WARN} 滚动检索结束，未能在会话列表中找到: '{name}'")
        return False

    # --------------------------------------------------------------------------
    # 6. 会话侧滑快捷动作与删除流程
    # --------------------------------------------------------------------------

    def swipe_conversation_left(self, name: str) -> bool:
        """
        向左轻扫指定会话卡片，呼出侧滑快捷菜单 (静音 / 置顶 / 删除)
        """
        logger.info(f"{LogIcon.ACTION} 侧滑打开会话快捷菜单: '{name}'")
        loc = HomeLocatorHos.get_conver_by_name(name)
        elem = self.find_element(loc, timeout=2, raise_exception=False)
        if not elem:
            logger.warning(f"{LogIcon.WARN} 未找到会话 '{name}'，无法执行侧滑操作")
            return False

        # 基于元素中心点向左轻扫 400px
        cx = getattr(elem, "center_x", None)
        cy = getattr(elem, "center_y", None)
        if cx is None or cy is None:
            loc_data = elem.location
            size_data = elem.size
            cx = loc_data["x"] + size_data["width"] // 2
            cy = loc_data["y"] + size_data["height"] // 2

        start_x = cx + 150
        end_x = max(20, cx - 350)
        self.swipe(start_x, cy, end_x, cy, duration=300)
        time.sleep(0.3)
        return True

    def mute_conversation(self, name: str) -> None:
        """侧滑并将指定会话设置为静音/免打扰"""
        self.swipe_conversation_left(name)
        logger.info(f"{LogIcon.ACTION} 点击会话 '{name}' 侧滑菜单项: 静音/免打扰")
        self.click(HomeLocatorHos.get_mute_action_by_name(name), force_wait=True, timeout=2)

    def top_conversation(self, name: str) -> None:
        """侧滑并将指定会话置顶/取消置顶"""
        self.swipe_conversation_left(name)
        logger.info(f"{LogIcon.ACTION} 点击会话 '{name}' 侧滑菜单项: 置顶/取消置顶")
        self.click(HomeLocatorHos.get_top_action_by_name(name), force_wait=True, timeout=2)

    def delete_conversation(self, name: str, clear_history: bool = False) -> None:
        """
        侧滑并彻底删除指定会话：
        :param name: 会话或联系人名称
        :param clear_history: 是否在弹窗中勾选清空历史记录并隐藏
        """
        self.swipe_conversation_left(name)
        logger.info(f"{LogIcon.ACTION} 点击会话 '{name}' 侧滑菜单项: 删除")
        self.click(HomeLocatorHos.get_delete_action_by_name(name), force_wait=True, timeout=2)

        if clear_history and self.is_element_exist(HomeLocatorHos.CONVERSATION_DELETE_DIALOG_CLEAR_CHAT_RECORD, timeout=1):
            logger.info(f"{LogIcon.ACTION} 勾选: 清空聊天记录并隐藏")
            self.click(HomeLocatorHos.CONVERSATION_DELETE_DIALOG_CLEAR_CHAT_RECORD, force_wait=True)

        logger.info(f"{LogIcon.ACTION} 点击弹窗确认删除按钮")
        self.click(HomeLocatorHos.CONVERSATION_DELETE_DIALOG_CONFIRM, force_wait=True, timeout=2)
        time.sleep(0.5)

    # --------------------------------------------------------------------------
    # 7. 置顶会话折叠交互
    # --------------------------------------------------------------------------

    def is_folded_entry_exist(self) -> bool:
        """检查主页会话列表中是否存在置顶折叠入口条目"""
        return self.is_element_exist(HomeLocatorHos.CONVERSATION_FOLD_ENTRY, timeout=0.5)

    def click_folded_entry(self) -> None:
        """点击置顶折叠入口条目展开或收起折叠列表"""
        logger.info(f"{LogIcon.ACTION} 点击置顶折叠入口条目")
        self.click(HomeLocatorHos.CONVERSATION_FOLD_ENTRY, force_wait=True, timeout=2)

    # --------------------------------------------------------------------------
    # 8. 聊天安全密码保护弹窗业务交互 (Chat Password Dialog)
    # --------------------------------------------------------------------------

    def is_chat_password_dialog_exist(self, timeout: float = 1.0) -> bool:
        """判断当前是否弹出了聊天安全密码保护对话框"""
        return self.is_element_exist(HomeLocatorHos.CHAT_PASSWORD_DIALOG_TITLE, timeout=timeout)

    def close_chat_password_dialog(self, timeout: int = 2) -> None:
        """关闭聊天安全密码对话框"""
        logger.info(f"{LogIcon.ACTION} 点击关闭聊天密码弹窗")
        self.click(HomeLocatorHos.CHAT_PASSWORD_DIALOG_CLOSE, force_wait=True, timeout=timeout)

    def input_chat_password(self, password: str, timeout: int = 3) -> bool:
        """
        向安全密码弹窗输入 6 位数字密码：
        优先尝试全局密码输入框，若为分格则按位派发。
        """
        logger.info(f"{LogIcon.ACTION} 正在输入聊天安全密码 (长度: {len(password)})")
        if not self.is_chat_password_dialog_exist(timeout=timeout):
            logger.warning(f"{LogIcon.WARN} 未检测到聊天密码弹窗")
            return False

        # 方式 1：尝试直接向通用密码输入组件下发
        if self.is_element_exist(HomeLocatorHos.CHAT_PASSWORD_INPUT, timeout=0.5):
            self.send_keys(HomeLocatorHos.CHAT_PASSWORD_INPUT, password)
            logger.info(f"{LogIcon.SUCCESS} 密码下发完成")
            return True

        # 方式 2：按格子索引输入 (1-indexed)
        for idx, char in enumerate(password):
            loc = HomeLocatorHos.get_password_input_by_index(idx)
            self.send_keys(loc, char)
            time.sleep(0.1)

        logger.info(f"{LogIcon.SUCCESS} 逐格密码输入完成")
        return True
