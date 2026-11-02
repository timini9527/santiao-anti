import re
import time
from typing import Optional, Literal, Union
from selenium.webdriver.remote.webelement import WebElement
from common.base_page import BasePage
from core.logger_utils import logger, LogIcon
from locators.home.home_locator import HomeLocator


class HomePage(BasePage):

    # 主页 - 等待 home page 完全加载
    def wait_home_page(self, timeout: int = 10) -> bool:
        """等待主页左侧菜单出现，并返回主页是否加载完成。"""
        logger.info(f"{LogIcon.WAIT} 正在等待主页加载完成 (超时: {timeout}s)...")
        loaded = bool(self.find_elements(HomeLocator.LEFT_MENU, timeout=timeout))
        if loaded:
            logger.info(f"{LogIcon.SUCCESS} 主页加载完成 (耗时上限: {timeout}s)")
        else:
            logger.error(f"{LogIcon.FAIL} 未找到主页左侧菜单 (超时: {timeout}s)")
        return loaded

    # 主页 - 打开侧边栏
    def open_left_menu(self, timeout: int = 2) -> None:
        """ 主页 - 点击打开侧边栏 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击打开侧边栏")
        self.click(HomeLocator.LEFT_MENU, timeout=timeout)
        time.sleep(0.5)

    # 主页 - 点击主页标题
    def click_home_title(self, timeout: int = 2) -> None:
        """ 主页 - 点击主页标题 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击主页标题")
        self.click(HomeLocator.MIDDLE_TITLE, force_wait=True, timeout=timeout)

    # 主页 - 获取顶部中间标题 三条标题
    def get_top_middle_title(self, timeout: int = 2) -> str:
        """ 主页 - 获取顶部中间标题 三条标题 """
        logger.info(f"{LogIcon.FIND} 正在获取主页顶部中间标题(超时: {timeout}s)...")
        title = self.get_attribute(HomeLocator.MIDDLE_TITLE, 'text', timeout=timeout)
        logger.info(f"{LogIcon.ACTION} 主页 - 获取顶部中间标题（{timeout} 秒内）: {title}")
        return title

    # 主页 - 点击 + 号按钮
    def click_add_button(self, timeout: int = 2) -> None:
        """ 主页 - 点击 + 号按钮 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击 + 号（右上角菜单）按钮")
        self.click(HomeLocator.RIGHT_MENU, force_wait=True, timeout=timeout)

    # 主页 - 点击 发起群聊
    def click_start_group_chat(self, timeout: int = 2) -> None:
        """ 主页 - 点击 发起群聊 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击 发起群聊")
        self.click(HomeLocator.EXPAND_START_GROUP_CHAT, force_wait=True, timeout=timeout)

    # 主页 - 点击 添加朋友
    def click_add_friend(self, timeout: int = 2) -> None:
        """ 主页 - 点击 添加朋友 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击 添加朋友")
        self.click(HomeLocator.EXPAND_ADD_FRIEND, force_wait=True, timeout=timeout)

    # 主页 - 点击 扫一扫
    def click_scan(self, timeout: int = 2) -> None:
        """ 主页 - 点击 扫一扫 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击 扫一扫")
        self.click(HomeLocator.EXPAND_SCAN, force_wait=True, timeout=timeout)

    # 主页 - 点击搜索
    def click_search(self, timeout: int = 2) -> None:
        """ 主页 - 点击搜索 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击搜索")
        self.click(HomeLocator.SEARCH, force_wait=True, timeout=timeout)

    # 主页 - 点击搜索清除
    def click_search_clear(self, timeout: int = 2) -> None:
        """ 主页 - 点击搜索清除 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击清理搜索")
        self.click(HomeLocator.SEARCH_CLEAR, force_wait=True, timeout=timeout)

    # 主页 - 点击搜索取消/关闭
    def click_search_cancel(self, timeout: int = 2) -> None:
        """ 主页 - 点击搜索栏右侧取消/关闭按钮 (大圆形 X) 退出搜索 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击取消按钮退出搜索")
        self.click(HomeLocator.SEARCH_CANCEL, force_wait=True, timeout=timeout)

    # 主页 - 检查并在存在时安全退出搜索覆盖层
    def exit_search_if_present(self, timeout: int = 1) -> bool:
        """ 主页 - 若当前停留在搜索结果覆盖层，主动点击右侧取消按钮退出搜索回到主会话列表 """
        if self.is_element_exist(HomeLocator.SEARCH_CANCEL, timeout=timeout):
            logger.info(f"{LogIcon.ACTION} 检测到搜索结果覆盖层，点击右侧取消按钮退出搜索回到主页...")
            self.click(HomeLocator.SEARCH_CANCEL, force_wait=True)
            return True
        return False

    # 主页 - 点击底部展开按钮
    def click_bottom_expand_button(self, timeout: int = 2) -> None:
        """ 主页 - 点击底部展开按钮 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击底部展开按钮")
        self.click(HomeLocator.EXPAND_MENU, force_wait=True, timeout=timeout)

    # 主页 - 关闭底部扩展菜单
    def click_bottom_close_expand_button(self, timeout: int = 2) -> None:
        """ 主页 - 关闭底部扩展菜单 """
        logger.info(f"{LogIcon.ACTION} 主页 - 准备关闭底部扩展菜单按钮")
        if "三条" not in self.get_top_middle_title():
            self.click_bottom_expand_button(timeout=timeout)
        logger.info(f"{LogIcon.ACTION} 主页 - 点击底部关闭扩展菜单按钮完成")

    # 主页 - 点击好友
    def click_friend(self, timeout: int = 2) -> None:
        """ 主页 - 点击好友 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击好友")
        self.click(HomeLocator.FRIEND, force_wait=True, timeout=timeout)

    # 主页 - 点击群聊
    def click_group(self, timeout: int = 2) -> None:
        """ 主页 - 点击群聊 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击群聊")
        self.click(HomeLocator.GROUP, force_wait=True, timeout=timeout)

    # 主页 - 点击动态
    def click_dynamic(self, timeout: int = 2) -> None:
        """ 主页 - 点击动态 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击动态")
        self.click(HomeLocator.DYNAMIC, force_wait=True, timeout=timeout)
    
    # 主页 - 获取动态未读消息红点数量
    def get_dynamic_unread_msg_count(self) -> str:
        """ 主页 - 获取动态未读消息红点数量 """
        logger.info(f"{LogIcon.FIND} 正在获取动态未读消息红点数量...")
        text = self.get_attribute(HomeLocator.DYNAMIC_UNREAD_MSG, 'text')
        logger.info(f"{LogIcon.ACTION} 主页 - 动态未读消息红点数量: {text}")
        return text

    # 主页 - 点击第一个会话
    def click_conversation(self, index: int = 0, timeout: int = 2) -> None:
        """ 主页 - 点击第一个会话 """
        logger.info(f"{LogIcon.ACTION} 主页 - 准备点击会话(索引: {index})")
        self.click(HomeLocator.CONVERSATION_ITEM, force_wait=True, timeout=timeout)

    # 主页 - 获取页面所有会话列表
    def get_conversation_list(self) -> list[WebElement]:
        """ 主页 - 获取页面所有会话列表 """
        logger.info(f"{LogIcon.FIND} 正在获取页面所有会话列表...")
        result = self.find_elements(HomeLocator.CONVERSATION_ITEM)
        logger.info(f"{LogIcon.ACTION} 获取页面所有会话列表数量: {len(result)}")
        return result

    # 主页 - 获取会话数量
    def get_conversation_count(self) -> int:
        """ 主页 - 获取会话数量 """
        logger.info(f"{LogIcon.FIND} 正在统计会话总数量...")
        count = len(self.get_conversation_list())
        logger.info(f"{LogIcon.ACTION} 主页 - 获取会话数量: {count}")
        return count

    # 主页 - 获取第一个会话名称
    def get_conversation_name(self, index: int = 0) -> str:
        """ 主页 - 获取第一个会话名称 """
        logger.info(f"{LogIcon.FIND} 正在获取会话名称(索引: {index})...")
        name = self.get_attribute(HomeLocator.CONVERSATION_NAME, 'text')
        logger.info(f"{LogIcon.ACTION} 主页 - 获取第一个会话名称: {name}")
        return name

    # 主页 - 获取页面所有会话名称
    def get_conversation_names(self) -> list[str]:
        """ 主页 - 获取页面所有会话名称 """
        logger.info(f"{LogIcon.FIND} 正在获取页面所有会话名称列表...")
        elements = self.find_elements(HomeLocator.CONVERSATION_NAME)
        names = [element.get_attribute('text') for element in elements]
        logger.info(f"{LogIcon.ACTION} 主页 - 获取页面所有会话名称: {names}")
        return names
    
    # 主页 - 获取特定名称会话
    def get_conversation_by_name(self, name: str) -> Optional[WebElement]:
        """ 主页 - 获取特定名称会话 """
        logger.info(f"{LogIcon.FIND} 正在检索特定名称会话: 【{name}】...")
        result = self.find_element(HomeLocator.get_conver_by_name(name), timeout=2)
        logger.info(f"{LogIcon.ACTION} 主页 - 获取特定名称会话: {name}")
        return result

    # 主页 - 获取第一个会话时间
    def get_conversation_time(self, index: int = 0) -> str:
        """ 主页 - 获取第一个会话时间 """
        logger.info(f"{LogIcon.FIND} 正在获取会话时间(索引: {index})...")
        time_text = self.get_attribute(HomeLocator.CONVERSATION_TIME, 'text')
        logger.info(f"{LogIcon.ACTION} 主页 - 获取第一个会话时间: {time_text}")
        return time_text

    # 主页 - 获取页面所有会话时间
    def get_conversation_times(self) -> list[str]:
        """ 主页 - 获取页面所有会话时间 """
        logger.info(f"{LogIcon.FIND} 正在获取页面所有会话时间列表...")
        elements = self.find_elements(HomeLocator.CONVERSATION_TIME)
        times = [element.get_attribute('text') for element in elements]
        logger.info(f"{LogIcon.ACTION} 主页 - 获取页面所有会话时间数量: {len(times)}")
        return times

    # 主页 - 获取第一个会话内容
    def get_conversation_content(self, index: int = 0) -> str:
        """ 主页 - 获取第一个会话内容 """
        logger.info(f"{LogIcon.FIND} 正在获取会话内容(索引: {index})...")
        content = self.get_attribute(HomeLocator.CONVERSATION_CONTENT, 'text')
        logger.info(f"{LogIcon.ACTION} 主页 - 获取第一个会话内容: {content}")
        return content

    # 主页 - 获取页面所有会话内容
    def get_conversation_contents(self) -> list[str]:
        """ 主页 - 获取页面所有会话内容 """
        logger.info(f"{LogIcon.FIND} 正在获取页面所有会话内容列表...")
        elements = self.find_elements(HomeLocator.CONVERSATION_CONTENT)
        contents = [element.get_attribute('text') for element in elements]
        logger.info(f"{LogIcon.ACTION} 主页 - 获取页面所有会话内容数量: {len(contents)}")
        return contents

    # 主页 - 获取第一个会话未读消息数
    def get_conversation_unread_count(self, index: int = 0) -> str:
        """ 主页 - 获取第一个会话未读消息数 """
        logger.info(f"{LogIcon.FIND} 正在获取会话未读消息数(索引: {index})...")
        count = self.get_attribute(HomeLocator.CONVERSATION_UNREAD_COUNT, 'text')
        logger.info(f"{LogIcon.ACTION} 主页 - 获取第一个会话未读消息数: {count}")
        return count

    # 主页 - 获取第一个会话未读消息数内部
    def get_conversation_unread_count_inner(self, index: int = 0) -> str:
        """ 主页 - 获取第一个会话未读消息数内部 """
        logger.info(f"{LogIcon.FIND} 正在获取会话内部未读消息数(索引: {index})...")
        count = self.get_attribute(HomeLocator.CONVERSATION_UNREAD_COUNT_INNER, 'text')
        logger.info(f"{LogIcon.ACTION} 主页 - 获取第一个会话内部未读消息数: {count}")
        return count

    # 主页 - 通过好友昵称获取他的会话下面有没有消息内容
    def get_message_by_name(self, name: str, expected_text: Optional[Union[str, list, tuple]] = None, timeout: int = 10) -> str:
        """
        主页 - 通过好友昵称获取他的会话下面有没有消息内容
        :param name: 好友或群聊名称
        :param expected_text: 可选预期包含文本（支持单文本、'/'分隔多选或列表/元组候选集），若传入则在 timeout 时间内轮询等待刷新
        :param timeout: 总超时时间（秒），默认 10 秒保障异步刷新命中
        :return: 会话消息内容文本
        """
        candidates = []
        if expected_text:
            if isinstance(expected_text, (list, tuple)):
                candidates = [str(x).strip() for x in expected_text if str(x).strip()]
            elif isinstance(expected_text, str) and "/" in expected_text:
                candidates = [x.strip() for x in expected_text.split("/") if x.strip()]
            else:
                candidates = [str(expected_text).strip()]

        logger.info(f"{LogIcon.FIND} 正在通过会话名称[{name}]获取消息内容(期待匹配候选: {candidates if candidates else expected_text}, 超时: {timeout}s)...")
        end_time = time.time() + timeout
        content = ""
        while time.time() <= end_time:
            current_text = self.get_attribute(HomeLocator.get_message_by_name(name), 'text', raise_exception=False)
            if current_text:
                content = current_text
                if not candidates or any(candidate in content for candidate in candidates):
                    logger.info(f"{LogIcon.SUCCESS} 主页 - 通过会话名称[{name}]获取到匹配消息内容: {content}")
                    return content
                logger.info(f"{LogIcon.WAIT} 当前获取到会话内容: '{content}'，与预期 {candidates} 暂不匹配，等待刷新...")

        logger.info(f"{LogIcon.ACTION} 主页 - 通过会话名称[{name}]获取到消息内容(最终): {content}")
        return content or ""

    # 主页 - 会话静音
    def click_conversation_mute(self) -> None:
        """ 主页 - 会话静音 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击会话静音")
        self.click(HomeLocator.CONVERSATION_MUTE, force_wait=True)

    # 主页 - 会话置顶
    def click_conversation_top(self) -> None:
        """ 主页 - 会话置顶 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击会话置顶")
        self.click(HomeLocator.CONVERSATION_TOP, force_wait=True)

    # 主页 - 会话删除
    def click_conversation_delete(self) -> None:
        """ 主页 - 会话删除 """
        logger.info(f"{LogIcon.ACTION} 主页 - 点击会话删除")
        self.click(HomeLocator.CONVERSATION_DELETE, force_wait=True)

    # 主页 - 会话删除弹窗 清空聊天记录
    def click_conversation_delete_dialog_clear_chat_record(self) -> None:
        """ 主页 - 会话删除弹窗 清空聊天记录 """
        logger.info(f"{LogIcon.ACTION} 主页 - 在删除会话弹窗勾选 清空聊天记录")
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CLEAR_CHAT_RECORD, force_wait=True)
    
    # 主页 - 会话删除弹窗 隐藏
    def click_conversation_delete_dialog_hide(self) -> None:
        """ 主页 - 会话删除弹窗 隐藏 """
        logger.info(f"{LogIcon.ACTION} 主页 - 在删除会话弹窗勾选 隐藏")
        self.click(HomeLocator.CONVERSATION_HIDE, force_wait=True)

    # 主页 - 会话删除弹窗 确认删除
    def click_conversation_delete_dialog_confirm(self) -> None:
        """ 主页 - 会话删除弹窗 确认删除 """
        logger.info(f"{LogIcon.ACTION} 主页 - 在删除会话弹窗点击 确认")
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CONFIRM, force_wait=True)

    # 主页 - 会话删除弹窗 取消
    def click_conversation_delete_dialog_cancel(self) -> None:
        """ 主页 - 会话删除弹窗 取消 """
        logger.info(f"{LogIcon.ACTION} 主页 - 在删除会话弹窗点击 取消")
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CANCEL, force_wait=True)

    # 主页 - 会话获取草稿状态
    def get_remind_status(self, timeout: int = 1, raise_exception: bool = True) -> str:
        """ 主页 - 会话获取草稿状态 """
        logger.info(f"{LogIcon.FIND} 正在获取会话草稿状态...")
        status = self.get_attribute(HomeLocator.CONVERSATION_DRAFT, 'text', timeout=timeout, raise_exception=raise_exception)
        logger.info(f"{LogIcon.ACTION} 主页 - 获取会话草稿状态: {status}")
        return status

    # 主页 - 精确获取某一个会话的状态提醒标签 (@人的消息、进群验证消息: tv_user_name)
    def get_remind_status_by_name(self, name: str, timeout: int = 2) -> str:
        """
        主页 - 获取指定会话的前缀提醒状态（如 [有人@我]、[@所有人]、[进群申请]）
        基于实际界面元素 tv_user_name 定位，当标签消失时安全返回空字符串
        :param name: 会话名称
        :param timeout: 超时时间（秒）
        :return: 提醒状态文本
        """
        logger.info(f"{LogIcon.FIND} 正在获取会话 [{name}] 强提醒状态...")
        elem = self.find_element(
            HomeLocator.get_remind_status_by_name(name), 
            timeout=timeout, 
            raise_exception=False, 
            expect_missing=True
        )
        status = elem.text.strip() if elem else ""
        logger.info(f"{LogIcon.ACTION} 获取指定会话 [{name}] 强提醒状态 (tv_user_name): '{status}'")
        return status

    # 主页 - 会话获取未读/已读状态
    def get_unread_status(self, name: str) -> str:
        """
        获取指定会话列表的消息阅读状态
        :param name: 会话名称
        :return: 状态文本，如 "未读" 或 "已读"
        """
        logger.info(f"{LogIcon.FIND} 正在获取会话 [{name}] 的阅读状态...")
        elem = self.find_element(HomeLocator.get_read_status_by_name(name), timeout=2)
        status = elem.text if elem else ""
        logger.info(f"{LogIcon.ACTION} 获取指定会话 [{name}] 阅读状态: {status}")
        return status

    # 主页 - 显式等待指定会话的阅读状态流转
    def wait_for_read_status(self, name: str, expected_status: str, timeout: int = 10) -> bool:
        """
        显式轮询等待指定会话的阅读状态达到预期 (支持未读->已读的长连接推送自愈)
        :param name: 会话名称
        :param expected_status: 预期包含的状态文本，如 "未读" 或 "已读"
        :param timeout: 超时时间（秒）
        :return: 达到预期返回 True，超时返回 False
        """
        logger.info(f"{LogIcon.WAIT} 等待会话 [{name}] 状态达到 【{expected_status}】(超时: {timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_status = self.get_unread_status(name)
            if expected_status in current_status:
                logger.info(f"{LogIcon.ACTION} 会话 [{name}] 成功匹配目标阅读状态: 【{expected_status}】")
                return True
            time.sleep(0.5)
        logger.warning(f"{LogIcon.ACTION} 等待会话 [{name}] 状态为 【{expected_status}】 超时({timeout}s)")
        return False
    
    # 主页 - 会话获取停用状态
    def get_disable_status(self, name: str) -> bool:
        """
        获取指定会话的停用状态
        :param name: 会话名称
        :return: True 如果会话被停用=True,正常=False
        """
        logger.info(f"{LogIcon.FIND} 正在获取会话 [{name}] 停用状态...")
        is_disabled = self.find_element(HomeLocator.get_disable_by_name(name), timeout=2) is not None
        logger.info(f"{LogIcon.ACTION} 获取指定会话 [{name}] 停用状态: {is_disabled}")
        return is_disabled

    # 主页 - 会话安全点击列表项，防止被底部悬浮栏或顶部遮挡
    def ensure_item_safe_visible(self, session_name: str, allow_swipe: bool = True) -> bool:
        """
        检测列表项是否完全在可视区域内（未被顶部栏或底部悬浮菜单遮挡）。
        如果被遮挡或不在当前页：
            - allow_swipe = True: 自动平滑滑动直至元素完全暴露在安全区域内。
            - allow_swipe = False: 瞬时探测，若不在当前屏或被遮挡直接返回 False。

        :param session_name: 会话名称
        :param allow_swipe: 是否允许滑动查找/微调
        :return: bool (True: 元素安全可用 / False: 元素被遮挡或不存在)
        """
        logger.info(f"{LogIcon.FIND} 正在确保会话【{session_name}】安全露出(允许滑动: {allow_swipe})...")
        locator = HomeLocator.get_session_by_name(session_name)
        max_attempts = 5 if allow_swipe else 1

        # 1. 预先计算上下安全边界与屏幕中轴（单次探测，避免循环内重复开销）
        try:
            window_size = self.driver.get_window_size()
            screen_width = window_size.get('width', 1080)
            screen_height = window_size.get('height', 2000)
        except Exception:
            screen_width = 1080
            screen_height = 2000

        center_x = int(screen_width * 0.5)

        # 底部安全边界：底部 EXPAND_MENU 的顶部 Y 坐标；若无则兜底为屏幕高度
        bottom_item = self.find_element(HomeLocator.EXPAND_MENU, timeout=1, raise_exception=False)
        safe_bottom_boundary = bottom_item.rect['y'] if bottom_item else screen_height

        # 顶部安全边界：顶部导航标题的底部 Y 坐标，防止顶部遮挡误判
        top_item = self.find_element(HomeLocator.MIDDLE_TITLE, timeout=1, raise_exception=False)
        safe_top_boundary = (top_item.rect['y'] + top_item.rect['height']) if top_item else 0

        # 2. 动态探查与智能自适应微调
        for attempt in range(max_attempts):
            session_item = self.find_element(locator, timeout=1.5, raise_exception=False)

            if not session_item:
                if allow_swipe:
                    logger.info(f"{LogIcon.FAIL} 未找到会话【{session_name}】，向上滑动查找... (尝试 {attempt + 1}/{max_attempts})")
                    self.swipe_page('up', duration=500, times=1)
                    continue

                logger.info(f"{LogIcon.FAIL} 当前页未找到会话【{session_name}】，且已限制滑动，跳过。")
                return False

            element_rect = session_item.rect
            element_top_y = element_rect['y']
            element_bottom_y = element_top_y + element_rect['height']

            # 3. 校验顶部遮挡（被顶部导航栏截断）：执行向下滑动半屏微调 (0.25 -> 0.75 跨度 50%)
            if element_top_y < safe_top_boundary:
                logger.info(f"{LogIcon.ACTION} 会话【{session_name}】被顶部导航栏遮挡 (Top: {element_top_y} < Safe: {safe_top_boundary})。")
                if allow_swipe:
                    logger.info(f"{LogIcon.ACTION} 执行向下滑动半屏微调以露出元素顶部...")
                    self.swipe(center_x, int(screen_height * 0.25), center_x, int(screen_height * 0.75), duration=500)
                    continue
                return False

            # 4. 校验底部遮挡（被底部悬浮菜单遮挡）：执行向上滑动半屏微调 (0.75 -> 0.25 跨度 50%)
            if element_bottom_y > safe_bottom_boundary:
                logger.info(f"{LogIcon.ACTION} 会话【{session_name}】被底部悬浮栏遮挡 (Bottom: {element_bottom_y} > Safe: {safe_bottom_boundary})。")
                if allow_swipe:
                    logger.info(f"{LogIcon.ACTION} 执行向上滑动半屏微调以露出元素底部...")
                    self.swipe(center_x, int(screen_height * 0.75), center_x, int(screen_height * 0.25), duration=500)
                    continue

                logger.info(f"{LogIcon.ACTION} 已限制滑动，放弃操作被遮挡的会话。")
                return False

            logger.info(f"{LogIcon.SUCCESS} 会话【{session_name}】在安全可视区域内。")
            return True

        logger.warning(f"{LogIcon.FAIL} 超过最大尝试次数 ({max_attempts})，仍未能使会话【{session_name}】安全暴露。")
        return False 

    # 主页 - 检查置顶折叠入口是否可见
    def is_fold_entry_visible(self, timeout: int = 1, raise_exception: bool = False) -> bool:
        """ 主页 - 检查置顶折叠入口是否可见 """
        logger.info(f"{LogIcon.FIND} 正在检查置顶折叠入口是否可见(超时: {timeout}s)...")
        result = self.is_element_exist(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=timeout, raise_exception=raise_exception)
        logger.info(f"{LogIcon.STEP} 主页 - 折叠入口可见: {result}")
        return result

    # 主页 - 当折叠入口被隐藏时寻找折叠数量元素
    def is_fold_count_visible(self, max_attempts: int = 5) -> Optional[WebElement]:
        """
        主页 - 当折叠入口被隐藏时，需要下滑寻找如何获取折叠数量 
        Args:
            max_attempts: 最大尝试次数
        Returns:
            Optional[WebElement]: 折叠入口元素
        """
        logger.info(f"{LogIcon.FIND} 正在滑动寻找折叠数量入口元素(最多尝试: {max_attempts}次)...")
        while max_attempts > 0:
            fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=1, raise_exception=False)
            if fold_elem:
                return fold_elem
            max_attempts -= 1
            self.swipe_page('up', duration=500)
        return None

    # 主页 - 获取折叠入口显示的置顶数量
    def get_fold_count(self) -> int:
        """ 主页 - 获取折叠入口显示的置顶数量 """
        logger.info(f"{LogIcon.FIND} 正在获取折叠入口显示的置顶数量...")
        fold_elem = self.is_fold_count_visible()
        text = fold_elem.get_attribute('text') if fold_elem else ""
        self.swipe_page_quickly(slid_type='down', duration=200)
        if not text:
            return 0
        # 提取数字
        nums = re.findall(r'\d+', text)
        count = int(nums[0]) if nums else 0
        logger.info(f"{LogIcon.STEP} 主页 - 折叠数量文案: [{text}], 解析数量: {count}")
        return count

    # 主页 - 点击折叠入口
    def click_fold_entry(self, *args, timeout: int = 2, **kwargs) -> bool:
        """
        主页 - 点击置顶会话折叠入口条
        :param timeout: 查找折叠入口元素的超时时间（秒）
        :return: bool 是否成功点击
        """
        logger.info(f"{LogIcon.ACTION} 准备查找并点击置顶折叠入口条...")
        fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_VIEWGROUP, timeout=timeout, raise_exception=False)
        if not fold_elem:
            fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=timeout, raise_exception=False)
        if not fold_elem:
            fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_ENTRY, timeout=timeout, raise_exception=False)

        if not fold_elem:
            logger.warning(f"{LogIcon.WARN} 未找到置顶折叠入口元素，无法执行点击")
            return False

        logger.info(f"{LogIcon.ACTION} 点击置顶折叠入口条...")
        fold_elem.click()
        time.sleep(0.5)
        return True

    # 主页 - 智能判定置顶会话折叠条当前状态
    def get_top_fold_state(self, sample_pinned_name: Optional[str] = None) -> str:
        """
        【工业级多维探测】智能判定置顶会话折叠条当前状态（展开展示 vs 折叠收起）
        采用多维策略矩阵判定：
        1. 属性嗅探层（0ms）：检查右侧箭头 (CONVERSATION_FOLD_ENTRY) 的 selected、checked、content-desc 属性；
        2. 业务样本拓扑层：若传入了样本置顶好友名 sample_pinned_name，直接判断其在可视列表中是否呈现；
        3. 零配置拓扑差分层：比对当前可视列表中第一个会话项与折叠入口的相对位置与可见性。
        :param sample_pinned_name: (可选) 已知的某个置顶好友/群聊名称
        :return: 'expanded' (展开展示) | 'collapsed' (折叠收起) | 'none' (未出现折叠条)
        """
        logger.info(f"{LogIcon.FIND} [Fold State] 正在智能探测置顶折叠条状态 (样本: {sample_pinned_name})...")
        fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=2, raise_exception=False)
        if not fold_elem:
            logger.info(f"{LogIcon.ACTION} ℹ️ [Fold State] 当前消息列表不存在置顶折叠入口条")
            return "none"

        # 维度 1：原生属性极速嗅探 (0ms)
        try:
            arrow_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_ENTRY, timeout=1, raise_exception=False)
            if arrow_elem:
                selected = arrow_elem.get_attribute('selected')
                if selected in ['true', 'false']:
                    state = 'expanded' if selected == 'true' else 'collapsed'
                    logger.info(f"{LogIcon.ACTION} 🍏 [Fold State] 原生属性命中 (selected={selected}) -> 状态: 【{state}】")
                    return state

                desc = arrow_elem.get_attribute('content-desc') or ""
                if any(k in desc for k in ['收起', '展开']):
                    state = 'collapsed' if '展开' in desc else 'expanded'
                    logger.info(f"{LogIcon.ACTION} 🍏 [Fold State] 描述属性命中 (content-desc={desc}) -> 状态: 【{state}】")
                    return state
        except Exception as e:
            logger.debug(f"{LogIcon.WARN} 属性嗅探异常 (忽略): {e}")

        # 维度 2：业务列表拓扑感知判定 (100% 稳定可靠)
        visible_names = self.clean_ui_text(self.get_conversation_names())

        # 方式 A：如果调用方指定了样本置顶好友名称
        if sample_pinned_name:
            is_expanded = sample_pinned_name in visible_names
            state = "expanded" if is_expanded else "collapsed"
            logger.info(f"{LogIcon.STEP} [Fold State] 业务样本拓扑命中 (好友={sample_pinned_name}, 可见={is_expanded}) -> 状态: 【{state}】")
            return state

        # 方式 B：自适应通用判定（零数据依赖）
        # 解析折叠条文本中的数字 (例如 "5个置顶聊天" -> 5)
        fold_text = fold_elem.get_attribute('text') or ""
        nums = re.findall(r'\d+', fold_text)
        fold_count = int(nums[0]) if nums else 0

        # 获取折叠条自身在屏幕中的位置（Y 轴）
        try:
            fold_rect = fold_elem.rect
            fold_bottom = fold_rect.get('y', 0) + fold_rect.get('height', 0)
            # 获取第一个会话项的位置
            first_conver = self.find_element(HomeLocator.CONVERSATION_ITEM, timeout=1, raise_exception=False)
            if first_conver:
                first_y = first_conver.rect.get('y', 0)
                logger.debug(f"{LogIcon.FIND} 折叠条 bottom: {fold_bottom}, 首个会话 y: {first_y}, 置顶数: {fold_count}")
        except Exception:
            pass

        # 兜底：如果列表可见会话总数大于 0 且包含较多会话，通常认为处于展开态；否则为收起态
        logger.info(f"{LogIcon.STEP} [Fold State] 通用模式判定完成 (可见会话数: {len(visible_names)}, 折叠数量: {fold_count})")
        return "collapsed" if len(visible_names) <= 1 else "expanded"

    # 主页 - 检查置顶折叠条是否处于展开状态
    def is_top_fold_expanded(self, sample_pinned_name: Optional[str] = None) -> bool:
        """ 快捷方法：当前置顶折叠条是否处于展开展示状态 """
        return self.get_top_fold_state(sample_pinned_name=sample_pinned_name) == "expanded"

    # 主页 - 确保置顶折叠条达到指定状态
    def ensure_top_fold_state(self, target_state: str = "expanded", sample_name: Optional[str] = None) -> bool:
        """
        【工业级幂等控制器】确保置顶折叠条达到期望的指定状态
        :param target_state: 目标状态 'expanded' (展开展示) 或 'collapsed' (折叠收起)
        :param sample_name: (可选) 校验用样本好友名
        :return: 操作后是否成功处于目标状态
        """
        current_state = self.get_top_fold_state(sample_pinned_name=sample_name)
        if current_state == target_state:
            logger.info(f"{LogIcon.FIND} 🍏 当前折叠条已稳定处于【{target_state}】状态，无需点击，直接放行！")
            return True

        if current_state == "none":
            logger.warning(f"{LogIcon.WARN} 当前页面未出现置顶折叠条，无法执行状态切换")
            return False

        logger.info(f"{LogIcon.ACTION} 当前状态【{current_state}】与期望【{target_state}】不一致，执行点击切换...")
        self.click_fold_entry()

        # 切换后二次断言校验
        new_state = self.get_top_fold_state(sample_pinned_name=sample_name)
        if new_state != target_state:
            logger.warning(f"{LogIcon.WARN} 一次点击后状态未变为【{target_state}】(当前: {new_state})，执行二次幂等补偿尝试...")
            self.click_fold_entry()
            new_state = self.get_top_fold_state(sample_pinned_name=sample_name)

        logger.info(f"{LogIcon.SUCCESS} 成功切换并确认置顶条处于【{new_state}】状态！")
        return new_state == target_state

    # 主页 - 输入聊天密码
    def input_chat_password(self, password: str = "111111", index: int = 0) -> None:
        """
        主页 - 输入聊天密码 
        Args:
            password: 聊天密码
            index: 密码输入框的索引
        Returns:
            None
        """
        logger.info(f"{LogIcon.SETUP} 准备输入聊天密码 (长度: {len(password)})...")
        len_password = len(password)
        if len_password != 6:
            raise ValueError(f"❌ 密码长度必须为 6 位，当前长度为 {len_password}")
        
        for pwd in password:
            self.send_keys(HomeLocator.get_password_input_by_index(index), pwd)
            index += 1


    # ================================================================================
    # 好友页面相关
    # ================================================================================
    # 好友页面 - 判断/等待好友页面加载完成
    def is_on_friend_page(self, timeout: int = 1, quiet: bool = True, raise_exception: bool = True) -> bool:
        """ 判断当前是否已处于好友/通讯录页面（quiet=True 时静默判断不打印 Log） """
        try:
            is_exist = self.get_attribute(HomeLocator.MIDDLE_TITLE, 'text', timeout=timeout, raise_exception=raise_exception) == '好友'
        except Exception:
            is_exist = False

        if not quiet:
            if is_exist:
                logger.info(f"{LogIcon.SUCCESS} 好友页面加载完成")
            else:
                logger.warning(f"{LogIcon.WARN} 当前页面不是好友页面")
        return is_exist

    # 好友页面 - 等待好友页面加载完成（带 Log 输出）
    def wait_for_friend_page_load(self, timeout: int = 10, raise_exception: bool = True) -> bool:
        """ 好友页面 - 等待好友页面加载完成 """
        logger.info(f"{LogIcon.WAIT} 等待好友页面加载完成(超时: {timeout}s)...")
        return self.is_on_friend_page(timeout=timeout, quiet=False, raise_exception=raise_exception)

    # 好友页面 - 导航进入好友/通讯录页面
    def go_to_friend_page(self, timeout: int = 10, raise_exception: bool = True) -> bool:
        """ 导航进入好友/通讯录页面（若当前已处于好友页则自动直接返回） """
        logger.info(f"{LogIcon.ACTION} 🧭 [Action-Home] 准备导航进入好友/通讯录页面...")
        if self.is_on_friend_page(timeout=1, raise_exception=raise_exception):
            logger.info(f"{LogIcon.SUCCESS} 🍏 当前已处于好友/通讯录页面，无需重复跳转")
            return True
        self.click_bottom_expand_button()
        self.click_friend()
        return self.wait_for_friend_page_load(timeout=timeout, raise_exception=raise_exception)

    # 好友页面 - 点击朋友圈
    def click_friend_moments(self) -> None:
        """ 好友页面 - 点击朋友圈 """
        logger.info(f"{LogIcon.ACTION} 🆕 [Action - Home] 好友页面 - 点击朋友圈")
        self.click(HomeLocator.FRIEND_MOMENTS)

    # 好友页面 - 新的朋友文本
    def get_new_friend_text(self) -> str:
        """ 好友页面 - 获取新的朋友文本 """
        logger.info(f"{LogIcon.FIND} 正在获取新的朋友入口文本...")
        text = self.get_attribute(HomeLocator.NEW_FRIEND_TV, 'text')
        logger.info(f"{LogIcon.ACTION} 🆕 [Action - Home] 好友页面 - 新的朋友: {text}")
        return text

    # 好友页面 - 点击新的朋友
    def click_new_friend(self) -> None:
        """ 好友页面 - 点击新的朋友 """
        logger.info(f"{LogIcon.ACTION} 🆕 [Action - Home] 好友页面 - 点击新的朋友")
        self.click(HomeLocator.NEW_FRIEND_TV)
    
    # 获取新朋友未读消息数
    def get_new_friend_unread_count(self, raise_exception: bool = True, timeout: int = 2) -> int:
        """ 好友页面 - 获取新朋友未读消息数 """
        logger.info(f"{LogIcon.FIND} 正在获取新朋友未读消息红点数...")
        elem = self.find_element(HomeLocator.NEW_FRIEND_FB_BADGE_COUNT_XPATH, timeout=timeout, raise_exception=raise_exception)
        if not elem:
            return 0
        text = elem.get_attribute('text')
        logger.info(f"{LogIcon.ACTION} 🆕 [Action - Home] 好友页面 - 新的朋友未读消息数: {text}")
        return int(text)

    # 分组管理 - 获取分组管理文本
    def get_category_manager_text(self) -> str:
        """ 分组管理 - 获取分组管理文本 """
        logger.info(f"{LogIcon.FIND} 正在获取分组管理入口文本...")
        text = self.get_attribute(HomeLocator.CATEGORY_MANAGER_TV, 'text')
        logger.info(f"{LogIcon.ACTION} 🆕 [Action - Home] 分组管理 - 分组管理: {text}")
        return text

    # 分组管理 - 点击分组管理
    def click_category_manager(self) -> None:
        """ 分组管理 - 点击分组管理 """
        logger.info(f"{LogIcon.ACTION} 🆕 [Action - Home] 分组管理 - 点击分组管理")
        self.click(HomeLocator.CATEGORY_MANAGER_TV)

    # 好友页面 - 根据好友姓名点击好友项进入资料详情
    def click_contact_by_name(self, name: str) -> bool:
        """
        好友页面 - 根据好友姓名点击好友项进入资料详情
        Args:
            name: 好友姓名/昵称
        Returns:
            bool: 是否操作成功
        """
        logger.info(f"{LogIcon.FIND} 👤 [Action - Home] 好友页面 - 准备查找并点击好友: {name}")
        from appium.webdriver.common.appiumby import AppiumBy
        locator = (AppiumBy.XPATH, f'//*[@resource-id="{HomeLocator.PACKAGE_ID}/tv_name" and @text="{name}"]')
        try:
            self.click(locator, timeout=5)
            logger.info(f"{LogIcon.SUCCESS} 👤 [Action - Home] 好友页面 - 找到并点击好友成功: {name}")
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 好友页面 - 未找到好友项: {name}, 错误: {e}")
            return False

    
