import re
import time
from selenium.webdriver.remote.webelement import WebElement
from common.base_page import BasePage
from core.logger_utils import logger
from locators.home.home_locator import HomeLocator


class HomePage(BasePage):

    # 主页 - 等待 home page 完全加载
    def wait_home_page(self, timeout: int = 10) -> bool:
        """
        主页 - 等待 home page 完全加载
        Args:
            timeout: 超时时间
        Returns:
            bool: True 表示加载成功，False 表示超时
        """
        if not self.find_elements(HomeLocator.LEFT_MENU, timeout=timeout):
            logger.error(f"❌ [Wait] - 未找到 home icon，超时时间 {timeout} 秒")
            return False
        logger.info(f"✅ [Wait] - home page 加载完成，超时时间 {timeout} 秒")
        return True

    # 主页 - 打开侧边栏
    def open_left_menu(self, timeout: int = 2):
        """ 主页 - 点击打开侧边栏 """
        self.click(HomeLocator.LEFT_MENU, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击打开侧边栏")
        time.sleep(1.5)

    # 主页 - 点击主页标题
    def click_home_title(self, timeout: int = 2):
        """ 主页 - 点击主页标题 """
        self.click(HomeLocator.MIDDLE_TITLE, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击主页标题")

    # 主页 - 获取顶部中间标题 三条标题
    def get_top_middle_title(self, timeout: int = 2) -> str:
        """ 主页 - 获取顶部中间标题 三条标题 """
        title = self.get_attribute(HomeLocator.MIDDLE_TITLE, 'text', timeout=timeout)
        logger.info(f"[Action-Home] 主页 - 获取顶部中间标题（{timeout} 秒内）: {title}")
        return title

    # 主页 - 点击 + 号按钮
    def click_add_button(self, timeout: int = 2):
        """ 主页 - 点击 + 号按钮 """
        self.click(HomeLocator.RIGHT_MENU, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击 + 号（右上角菜单）按钮")

    # 主页 - 点击 发起群聊
    def click_start_group_chat(self, timeout: int = 2):
        """ 主页 - 点击 发起群聊 """
        self.click(HomeLocator.EXPAND_START_GROUP_CHAT, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击 发起群聊")

    # 主页 - 点击 添加朋友
    def click_add_friend(self, timeout: int = 2):
        """ 主页 - 点击 添加朋友 """
        self.click(HomeLocator.EXPAND_ADD_FRIEND, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击 添加朋友")

    # 主页 - 点击 扫一扫
    def click_scan(self, timeout: int = 2):
        """ 主页 - 点击 扫一扫 """
        self.click(HomeLocator.EXPAND_SCAN, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击 扫一扫")

    # 主页 - 点击搜索
    def click_search(self, timeout: int = 2):
        """ 主页 - 点击搜索 """
        self.click(HomeLocator.SEARCH, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击搜索")

    # 主页 - 点击搜索清除
    def click_search_clear(self, timeout: int = 2):
        """ 主页 - 点击搜索清除 """
        self.click(HomeLocator.SEARCH_CLEAR, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击清理搜索")

    # 主页 - 点击底部展开按钮
    def click_bottom_expand_button(self, timeout: int = 2):
        """ 主页 - 点击底部展开按钮 """
        self.click(HomeLocator.EXPAND_MENU, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击底部展开按钮")

    # 主页 - 关闭底部扩展菜单
    def click_bottom_close_expand_button(self, timeout: int = 2):
        """ 主页 - 关闭底部扩展菜单 """
        if "三条" not in self.get_top_middle_title():
            self.click_bottom_expand_button(timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击底部关闭扩展菜单按钮")

    # 主页 - 点击好友
    def click_friend(self, timeout: int = 2):
        """ 主页 - 点击好友 """
        self.click(HomeLocator.FRIEND, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击好友")

    # 主页 - 点击群聊
    def click_group(self, timeout: int = 2):
        """ 主页 - 点击群聊 """
        self.click(HomeLocator.GROUP, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击群聊")

    # 主页 - 点击动态
    def click_dynamic(self, timeout: int = 2):
        """ 主页 - 点击动态 """
        self.click(HomeLocator.DYNAMIC, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击动态")
    
    # 主页 - 获取动态未读消息红点数量
    def get_dynamic_unread_msg_count(self):
        """ 主页 - 获取动态未读消息红点数量 """
        text = self.get_attribute(HomeLocator.DYNAMIC_UNREAD_MSG, 'text')
        logger.info(f"[Action-Home] 主页 - 动态未读消息红点数量: {text}")
        return text

    # 主页 - 点击第一个会话
    def click_conversation(self, index=0, timeout: int = 2):
        """ 主页 - 点击第一个会话 """
        self.click(HomeLocator.CONVERSATION_ITEM, force_wait=True, timeout=timeout)
        logger.info("[Action-Home] 主页 - 点击第一个会话")

    # 主页 - 获取页面所有会话列表
    def get_conversation_list(self):
        """ 主页 - 获取页面所有会话列表 """
        result = self.find_elements(HomeLocator.CONVERSATION_ITEM)
        logger.info(f"[Action-Home] 获取页面所有会话列表数量: {len(result)}")
        return result

    # 主页 - 获取会话数量
    def get_conversation_count(self):
        """ 主页 - 获取会话数量 """
        count = len(self.get_conversation_list())
        logger.info(f"[Action-Home] 主页 - 获取会话数量: {count}")
        return count

    # 主页 - 获取第一个会话名称
    def get_conversation_name(self, index=0):
        """ 主页 - 获取第一个会话名称 """
        name = self.get_attribute(HomeLocator.CONVERSATION_NAME, 'text')
        logger.info(f"[Action-Home] 主页 - 获取第一个会话名称: {name}")
        return name

    # 主页 - 获取页面所有会话名称
    def get_conversation_names(self):
        """ 主页 - 获取页面所有会话名称 """
        elements = self.find_elements(HomeLocator.CONVERSATION_NAME)
        names = [element.get_attribute('text') for element in elements]
        logger.info(f"[Action-Home] 主页 - 获取页面所有会话名称: {names}")
        return names
    
    # 主页 - 获取特定名称会话
    def get_conversation_by_name(self, name: str):
        """ 主页 - 获取特定名称会话 """
        result = self.find_element(HomeLocator.get_conver_by_name(name), timeout=2)
        logger.info(f"[Action-Home] 主页 - 获取特定名称会话: {name}")
        return result

    # 主页 - 获取第一个会话时间
    def get_conversation_time(self, index=0):
        """ 主页 - 获取第一个会话时间 """
        time_text = self.get_attribute(HomeLocator.CONVERSATION_TIME, 'text')
        logger.info(f"[Action-Home] 主页 - 获取第一个会话时间: {time_text}")
        return time_text

    # 主页 - 获取页面所有会话时间
    def get_conversation_times(self):
        """ 主页 - 获取页面所有会话时间 """
        elements = self.find_elements(HomeLocator.CONVERSATION_TIME)
        times = [element.get_attribute('text') for element in elements]
        logger.info(f"[Action-Home] 主页 - 获取页面所有会话时间数量: {len(times)}")
        return times

    # 主页 - 获取第一个会话内容
    def get_conversation_content(self, index=0):
        """ 主页 - 获取第一个会话内容 """
        content = self.get_attribute(HomeLocator.CONVERSATION_CONTENT, 'text')
        logger.info(f"[Action-Home] 主页 - 获取第一个会话内容: {content}")
        return content

    # 主页 - 获取页面所有会话内容
    def get_conversation_contents(self):
        """ 主页 - 获取页面所有会话内容 """
        elements = self.find_elements(HomeLocator.CONVERSATION_CONTENT)
        contents = [element.get_attribute('text') for element in elements]
        logger.info(f"[Action-Home] 主页 - 获取页面所有会话内容数量: {len(contents)}")
        return contents

    # 主页 - 获取第一个会话未读消息数
    def get_conversation_unread_count(self, index=0):
        """ 主页 - 获取第一个会话未读消息数 """
        count = self.get_attribute(HomeLocator.CONVERSATION_UNREAD_COUNT, 'text')
        logger.info(f"[Action-Home] 主页 - 获取第一个会话未读消息数: {count}")
        return count

    # 主页 - 获取第一个会话未读消息数内部
    def get_conversation_unread_count_inner(self, index=0):
        """ 主页 - 获取第一个会话未读消息数内部 """
        count = self.get_attribute(HomeLocator.CONVERSATION_UNREAD_COUNT_INNER, 'text')
        logger.info(f"[Action-Home] 主页 - 获取第一个会话内部未读消息数: {count}")
        return count

    # 主页 - 通过好友昵称获取他的会话下面有没有消息内容
    def get_message_by_name(self, name: str, expected_text: str = None, timeout: int = 1) -> str:
        """
        主页 - 通过好友昵称获取他的会话下面有没有消息内容
        :param name: 好友或群聊名称
        :param expected_text: 可选预期包含文本，若传入则在 timeout 时间内轮询等待刷新
        :param timeout: 超时时间（秒）
        :return: 会话消息内容文本
        """
        end_time = time.time() + timeout
        content = ""
        while time.time() <= end_time:
            content = self.get_attribute(HomeLocator.get_message_by_name(name), 'text', timeout=timeout, raise_exception=False)
            if content:
                if expected_text is None or expected_text in content:
                    logger.info(f"[Action-Home] 主页 - 通过会话名称[{name}]获取到消息内容: {content}")
                    return content
        logger.info(f"[Action-Home] 主页 - 通过会话名称[{name}]获取到消息内容(最终): {content}")
        return content or ""

    # 主页 - 会话静音
    def click_conversation_mute(self):
        """ 主页 - 会话静音 """
        self.click(HomeLocator.CONVERSATION_MUTE, force_wait=True)
        logger.info("[Action-Home] 主页 - 点击会话静音")

    # 主页 - 会话置顶
    def click_conversation_top(self):
        """ 主页 - 会话置顶 """
        self.click(HomeLocator.CONVERSATION_TOP, force_wait=True)
        logger.info("[Action-Home] 主页 - 点击会话置顶")

    # 主页 - 会话删除
    def click_conversation_delete(self):
        """ 主页 - 会话删除 """
        self.click(HomeLocator.CONVERSATION_DELETE, force_wait=True)
        logger.info("[Action-Home] 主页 - 点击会话删除")

    # 主页 - 会话删除弹窗 清空聊天记录
    def click_conversation_delete_dialog_clear_chat_record(self):
        """ 主页 - 会话删除弹窗 清空聊天记录 """
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CLEAR_CHAT_RECORD, force_wait=True)
        logger.info("[Action-Home] 主页 - 在删除会话弹窗勾选 清空聊天记录")
    
    # 主页 - 会话删除弹窗 隐藏
    def click_conversation_delete_dialog_hide(self):
        """ 主页 - 会话删除弹窗 隐藏 """
        self.click(HomeLocator.CONVERSATION_HIDE, force_wait=True)
        logger.info("[Action-Home] 主页 - 在删除会话弹窗勾选 隐藏")

    # 主页 - 会话删除弹窗 确认删除
    def click_conversation_delete_dialog_confirm(self):
        """ 主页 - 会话删除弹窗 确认删除 """
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CONFIRM, force_wait=True)
        logger.info("[Action-Home] 主页 - 在删除会话弹窗点击 确认")

    # 主页 - 会话删除弹窗 取消
    def click_conversation_delete_dialog_cancel(self):
        """ 主页 - 会话删除弹窗 取消 """
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CANCEL, force_wait=True)
        logger.info("[Action-Home] 主页 - 在删除会话弹窗点击 取消")

    # 主页 - 会话获取草稿状态
    def get_remind_status(self, timeout: int = 1, raise_exception: bool = True):
        """ 主页 - 会话获取草稿状态 """
        status = self.get_attribute(HomeLocator.CONVERSATION_DRAFT, 'text', timeout=timeout, raise_exception=raise_exception)
        logger.info(f"[Action-Home] 主页 - 获取会话草稿状态: {status}")
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
        elem = self.find_element(
            HomeLocator.get_remind_status_by_name(name), 
            timeout=timeout, 
            raise_exception=False, 
            expect_missing=True
        )
        status = elem.text.strip() if elem else ""
        logger.info(f"[Action-Home] 获取指定会话 [{name}] 强提醒状态 (tv_user_name): '{status}'")
        return status

    # 主页 - 会话获取未读/已读状态
    def get_unread_status(self, name: str) -> str:
        """
        获取指定会话列表的消息阅读状态
        :param name: 会话名称
        :return: 状态文本，如 "未读" 或 "已读"
        """
        elem = self.find_element(HomeLocator.get_read_status_by_name(name), timeout=2)
        status = elem.text if elem else ""
        logger.info(f"[Action-Home] 获取指定会话 [{name}] 阅读状态: {status}")
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
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_status = self.get_unread_status(name)
            if expected_status in current_status:
                logger.info(f"[Action-Home] 会话 [{name}] 成功匹配目标阅读状态: 【{expected_status}】")
                return True
            time.sleep(0.5)
        logger.warning(f"[Action-Home] 等待会话 [{name}] 状态为 【{expected_status}】 超时({timeout}s)")
        return False
    
    # 主页 - 会话获取停用状态
    def get_disable_status(self, name: str) -> bool:
        """
        获取指定会话的停用状态
        :param name: 会话名称
        :return: True 如果会话被停用=True,正常=False
        """
        is_disabled = self.find_element(HomeLocator.get_disable_by_name(name), timeout=2) is not None
        logger.info(f"[Action-Home] 获取指定会话 [{name}] 停用状态: {is_disabled}")
        return is_disabled

    # 主页 - 会话安全点击列表项，防止被底部悬浮栏遮挡
    def ensure_item_safe_visible(self, session_name: str, allow_swipe: bool = True) -> bool:
        """
        检测列表项是否完全在可视区域内（未被底部菜单遮挡）。
        如果被遮挡或不在当前页：
            - allow_swipe = True: 自动向上滑动直到元素完全露出。
            - allow_swipe = False: 直接返回 False，不执行任何滑动操作。

        :param session_name: 会话名称
        :param allow_swipe: 是否允许滑动查找/微调
        :return: bool (True: 元素安全可用 / False: 元素被遮挡或不存在)
        """
        locator = HomeLocator.get_session_by_name(session_name)
        max_attempts = 5 if allow_swipe else 1

        for attempt in range(max_attempts):
            session_item = self.find_element(locator, timeout=5)

            if not session_item:
                if allow_swipe:
                    logger.info(f"未找到会话【{session_name}】，向上滑动查找... (尝试 {attempt + 1}/{max_attempts})")
                    self.swipe_page('up', duration=500)
                    continue

                logger.info(f"当前页未找到会话【{session_name}】，且已限制滑动，跳过。")
                return False

            # 2. 获取底部悬浮窗的位置来计算安全边界
            bottom_item = self.find_element(HomeLocator.EXPAND_MENU, timeout=2)
            if bottom_item:
                # 存在底部菜单：取其顶部 Y 坐标作为“安全边界”
                safe_bottom_boundary = bottom_item.rect['y']
            else:
                # 不存在底部菜单：取屏幕总高度作为“安全边界”
                safe_bottom_boundary = self.driver.get_window_size()['height']

            # 3. 计算目标元素的底部位置
            element_rect = session_item.rect
            element_bottom_y = element_rect['y'] + element_rect['height']

            # 4. 判断是否被遮挡
            if element_bottom_y > safe_bottom_boundary:
                logger.info(f"会话【{session_name}】被底部悬浮栏遮挡。")
                if allow_swipe:
                    logger.info("执行微调滑动以露出元素...")
                    self.swipe_page('up', duration=500)
                    continue

                logger.info("已限制滑动，放弃操作被遮挡的会话。")
                return False
            logger.info(f"✅ 会话【{session_name}】在安全可视区域内。")
            return True
        logger.warning(f"❌ 超过最大尝试次数 ({max_attempts})，仍未能使会话【{session_name}】安全暴露。")
        return False 

    # 主页 - 置顶折叠相关
    def is_fold_entry_visible(self, timeout=1, raise_exception=False) -> bool:
        """ 主页 - 检查置顶折叠入口是否可见 """
        result = self.is_element_exist(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=timeout, raise_exception=raise_exception)
        logger.info(f"📌 主页 - 折叠入口可见: {result}")
        return result

    # 主页 - 当折叠入户被隐藏时，需要下滑需寻找如何获取折叠数量 
    def is_fold_count_visible(self, max_attempts=5) -> WebElement | None:
        """
        主页 - 当折叠入口被隐藏时，需要下滑需寻找如何获取折叠数量 
        Args:
            max_attempts: 最大尝试次数
        Returns:
            WebElement: 折叠入口元素
        """
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
        fold_elem = self.is_fold_count_visible()
        text = fold_elem.get_attribute('text') if fold_elem else ""
        self.swipe_page_quickly(slid_type='down', duration=200)
        if not text:
            return 0
        # 提取数字
        nums = re.findall(r'\d+', text)
        count = int(nums[0]) if nums else 0
        logger.info(f"📌 主页 - 折叠数量文案: [{text}], 解析数量: {count}")
        return count

    # 主页 - 点击折叠入口
    def click_fold_entry(self, *args, timeout: int = 2, **kwargs) -> bool:
        """
        主页 - 点击置顶会话折叠入口条
        :param timeout: 查找折叠入口元素的超时时间（秒）
        :return: bool 是否成功点击
        """
        fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_VIEWGROUP, timeout=timeout, raise_exception=False)
        if not fold_elem:
            fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=timeout, raise_exception=False)
        if not fold_elem:
            fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_ENTRY, timeout=timeout, raise_exception=False)

        if not fold_elem:
            logger.warning("⚠️ [Action-Home] 未找到置顶折叠入口元素，无法执行点击")
            return False

        logger.info("👉 [Action-Home] 点击置顶折叠入口条...")
        fold_elem.click()
        time.sleep(0.5)
        return True

    def get_top_fold_state(self, sample_pinned_name: str = None) -> str:
        """
        【工业级多维探测】智能判定置顶会话折叠条当前状态（展开展示 vs 折叠收起）
        采用多维策略矩阵判定：
        1. 属性嗅探层（0ms）：检查右侧箭头 (CONVERSATION_FOLD_ENTRY) 的 selected、checked、content-desc 属性；
        2. 业务样本拓扑层：若传入了样本置顶好友名 sample_pinned_name，直接判断其在可视列表中是否呈现；
        3. 零配置拓扑差分层：比对当前可视列表中第一个会话项与折叠入口的相对位置与可见性。
        :param sample_pinned_name: (可选) 已知的某个置顶好友/群聊名称
        :return: 'expanded' (展开展示) | 'collapsed' (折叠收起) | 'none' (未出现折叠条)
        """
        fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=2, raise_exception=False)
        if not fold_elem:
            logger.info("ℹ️ [Fold State] 当前消息列表不存在置顶折叠入口条")
            return "none"

        # 维度 1：原生属性极速嗅探 (0ms)
        try:
            arrow_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_ENTRY, timeout=1, raise_exception=False)
            if arrow_elem:
                selected = arrow_elem.get_attribute('selected')
                if selected in ['true', 'false']:
                    state = 'expanded' if selected == 'true' else 'collapsed'
                    logger.info(f"🍏 [Fold State] 原生属性命中 (selected={selected}) -> 状态: 【{state}】")
                    return state

                desc = arrow_elem.get_attribute('content-desc') or ""
                if any(k in desc for k in ['收起', '展开']):
                    state = 'collapsed' if '展开' in desc else 'expanded'
                    logger.info(f"🍏 [Fold State] 描述属性命中 (content-desc={desc}) -> 状态: 【{state}】")
                    return state
        except Exception as e:
            logger.debug(f"属性嗅探异常 (忽略): {e}")

        # 维度 2：业务列表拓扑感知判定 (100% 稳定可靠)
        visible_names = self.clean_ui_text(self.get_conversation_names())

        # 方式 A：如果调用方指定了样本置顶好友名称
        if sample_pinned_name:
            is_expanded = sample_pinned_name in visible_names
            state = "expanded" if is_expanded else "collapsed"
            logger.info(f"📌 [Fold State] 业务样本拓扑命中 (好友={sample_pinned_name}, 可见={is_expanded}) -> 状态: 【{state}】")
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
                logger.debug(f"折叠条 bottom: {fold_bottom}, 首个会话 y: {first_y}, 置顶数: {fold_count}")
        except Exception:
            pass

        # 兜底：如果列表可见会话总数大于 0 且包含较多会话，通常认为处于展开态；否则为收起态
        logger.info(f"📌 [Fold State] 通用模式判定完成 (可见会话数: {len(visible_names)}, 折叠数量: {fold_count})")
        return "collapsed" if len(visible_names) <= 1 else "expanded"

    def is_top_fold_expanded(self, sample_pinned_name: str = None) -> bool:
        """ 快捷方法：当前置顶折叠条是否处于展开展示状态 """
        return self.get_top_fold_state(sample_pinned_name=sample_pinned_name) == "expanded"

    def ensure_top_fold_state(self, target_state: str = "expanded", sample_name: str = None) -> bool:
        """
        【工业级幂等控制器】确保置顶折叠条达到期望的指定状态
        :param target_state: 目标状态 'expanded' (展开展示) 或 'collapsed' (折叠收起)
        :param sample_name: (可选) 校验用样本好友名
        :return: 操作后是否成功处于目标状态
        """
        current_state = self.get_top_fold_state(sample_pinned_name=sample_name)
        if current_state == target_state:
            logger.info(f"🍏 当前折叠条已稳定处于【{target_state}】状态，无需点击，直接放行！")
            return True

        if current_state == "none":
            logger.warning("⚠️ 当前页面未出现置顶折叠条，无法执行状态切换")
            return False

        logger.info(f"🔄 当前状态【{current_state}】与期望【{target_state}】不一致，执行点击切换...")
        self.click_fold_entry()

        # 切换后二次断言校验
        new_state = self.get_top_fold_state(sample_pinned_name=sample_name)
        if new_state != target_state:
            logger.warning(f"⚠️ 一次点击后状态未变为【{target_state}】(当前: {new_state})，执行二次幂等补偿尝试...")
            self.click_fold_entry()
            new_state = self.get_top_fold_state(sample_pinned_name=sample_name)

        logger.info(f"🎉 成功切换并确认置顶条处于【{new_state}】状态！")
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
            is_exist = self.get_attribute(HomeLocator.TV_TITLE, 'text', timeout=timeout, raise_exception=raise_exception) == '好友'
        except Exception:
            is_exist = False

        if not quiet:
            if is_exist:
                logger.info("✅ 好友页面加载完成")
            else:
                logger.warning("⚠️ 当前页面不是好友页面")
        return is_exist

    # 好友页面 - 等待好友页面加载完成（带 Log 输出）
    def wait_for_friend_page_load(self, timeout: int = 10, raise_exception: bool = True) -> bool:
        """ 好友页面 - 等待好友页面加载完成 """
        return self.is_on_friend_page(timeout=timeout, quiet=False, raise_exception=raise_exception)

    # 好友页面 - 导航进入好友/通讯录页面
    def go_to_friend_page(self, timeout: int = 10, raise_exception: bool = True) -> bool:
        """ 导航进入好友/通讯录页面（若当前已处于好友页则自动直接返回） """
        if self.is_on_friend_page(timeout=1, raise_exception=raise_exception):
            logger.info("🍏 当前已处于好友/通讯录页面，无需重复跳转")
            return True
        self.click_bottom_expand_button()
        self.click_friend()
        return self.wait_for_friend_page_load(timeout=timeout, raise_exception=raise_exception)


    
    # 好友页面 - 新的朋友文本
    def get_new_friend_text(self) -> str:
        """ 好友页面 - 获取新的朋友文本 """
        text = self.get_attribute(HomeLocator.NEW_FRIEND_TV, 'text')
        logger.info(f"🆕 [Action - Home] 好友页面 - 新的朋友: {text}")
        return text

    # 好友页面 - 点击新的朋友
    def click_new_friend(self):
        """ 好友页面 - 点击新的朋友 """
        self.click(HomeLocator.NEW_FRIEND_TV)
        logger.info("🆕 [Action - Home] 好友页面 - 点击新的朋友")
    
    # 获取新朋友未读消息数
    def get_new_friend_unread_count(self, raise_exception: bool = True, timeout: int = 2) -> int:
        """ 好友页面 - 获取新朋友未读消息数 """
        elem = self.find_element(HomeLocator.NEW_FRIEND_FB_BADGE_COUNT_XPATH, timeout=timeout, raise_exception=raise_exception)
        if not elem:
            return 0
        text = elem.get_attribute('text')
        logger.info(f"🆕 [Action - Home] 好友页面 - 新的朋友未读消息数: {text}")
        return int(text)

    # 分组管理 - 获取分组管理文本
    def get_category_manager_text(self) -> str:
        """ 分组管理 - 获取分组管理文本 """
        text = self.get_attribute(HomeLocator.CATEGORY_MANAGER_TV, 'text')
        logger.info(f"🆕 [Action - Home] 分组管理 - 分组管理: {text}")
        return text

    # 分组管理 - 点击分组管理
    def click_category_manager(self):
        """ 分组管理 - 点击分组管理 """
        self.click(HomeLocator.CATEGORY_MANAGER_TV)
        logger.info("🆕 [Action - Home] 分组管理 - 点击分组管理")    

    # 好友页面 - 根据好友姓名点击好友项进入资料详情
    def click_contact_by_name(self, name: str) -> bool:
        """
        好友页面 - 根据好友姓名点击好友项进入资料详情
        Args:
            name: 好友姓名/昵称
        Returns:
            bool: 是否操作成功
        """
        from appium.webdriver.common.appiumby import AppiumBy
        locator = (AppiumBy.XPATH, f'//*[@resource-id="{HomeLocator.PACKAGE_ID}/tv_name" and @text="{name}"]')
        try:
            self.click(locator, timeout=5)
            logger.info(f"👤 [Action - Home] 好友页面 - 找到并点击好友: {name}")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - Home] 好友页面 - 未找到好友项: {name}, 错误: {e}")
            return False

    
