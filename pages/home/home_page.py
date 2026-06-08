import re
import time
from selenium.webdriver.remote.webelement import WebElement
from common.base_page import BasePage
from core.logger_utils import logger
from locators.home.home_locator import HomeLocator


class HomePage(BasePage):

    # 等待 home page 完全加载
    def wait_home_page(self, timeout: int = 10) -> bool:
        """
        等待 home page 完全加载
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

    # 打开侧边栏
    def open_left_menu(self):
        self.click(HomeLocator.LEFT_MENU)
        logger.info("[Action-Home] 点击打开侧边栏")
        time.sleep(1.5)

    # 点击主页标题
    def click_home_title(self):
        self.click(HomeLocator.MIDDLE_TITLE, force_wait=True)
        logger.info("[Action-Home] 点击主页标题")

    # 主页获取顶部中间标题 三条标题
    def get_top_middle_title(self) -> str:
        title = self.get_attribute(HomeLocator.MIDDLE_TITLE, 'text')
        logger.info(f"[Action-Home] 获取顶部中间标题: {title}")
        return title

    # 点击 + 号按钮
    def click_add_button(self):
        self.click(HomeLocator.RIGHT_MENU, force_wait=True)
        logger.info("[Action-Home] 点击 + 号（右上角菜单）按钮")

    # 点击 发起群聊
    def click_start_group_chat(self):
        self.click(HomeLocator.EXPAND_START_GROUP_CHAT, force_wait=True)
        logger.info("[Action-Home] 点击 发起群聊")

    # 点击 添加朋友
    def click_add_friend(self):
        self.click(HomeLocator.EXPAND_ADD_FRIEND, force_wait=True)
        logger.info("[Action-Home] 点击 添加朋友")

    # 点击 扫一扫
    def click_scan(self):
        self.click(HomeLocator.EXPAND_SCAN, force_wait=True)
        logger.info("[Action-Home] 点击 扫一扫")

    # 点击搜索
    def click_search(self):
        self.click(HomeLocator.SEARCH, force_wait=True)
        logger.info("[Action-Home] 点击搜索")

    # 点击搜索清除
    def click_search_clear(self):
        self.click(HomeLocator.SEARCH_CLEAR, force_wait=True)
        logger.info("[Action-Home] 点击清理搜索")

    # 点击底部扩展菜单
    def click_bottom_expand_menu(self):
        if "三条" not in self.get_top_middle_title():
            self.click(HomeLocator.EXPAND_MENU, force_wait=True)
            logger.info("[Action-Home] 点击底部扩展菜单")

    # 点击好友
    def click_friend(self):
        self.click(HomeLocator.FRIEND, force_wait=True)
        logger.info("[Action-Home] 点击好友")

    # 点击群聊
    def click_group(self):
        self.click(HomeLocator.GROUP, force_wait=True)
        logger.info("[Action-Home] 点击群聊")

    # 点击动态
    def click_dynamic(self):
        self.click(HomeLocator.DYNAMIC, force_wait=True)
        logger.info("[Action-Home] 点击动态")

    # 点击第一个会话
    def click_conversation(self, index=0):
        self.click(HomeLocator.CONVERSATION_ITEM, force_wait=True)
        logger.info("[Action-Home] 点击第一个会话")

    # 获取页面所有会话列表
    def get_conversation_list(self):
        result = self.find_elements(HomeLocator.CONVERSATION_ITEM)
        logger.info(f"[Action-Home] 获取页面所有会话列表数量: {len(result)}")
        return result

    # 获取会话数量
    def get_conversation_count(self):
        count = len(self.get_conversation_list())
        logger.info(f"[Action-Home] 获取会话数量: {count}")
        return count

    # 获取第一个会话名称
    def get_conversation_name(self, index=0):
        name = self.get_attribute(HomeLocator.CONVERSATION_NAME, 'text')
        logger.info(f"[Action-Home] 获取第一个会话名称: {name}")
        return name

    # 获取页面所有会话名称
    def get_conversation_names(self):
        elements = self.find_elements(HomeLocator.CONVERSATION_NAME)
        names = [element.get_attribute('text') for element in elements]
        logger.info(f"[Action-Home] 获取页面所有会话名称: {names}")
        return names
    
    # 获取特定名称会话
    def get_conversation_by_name(self, name: str):
        result = self.find_element(HomeLocator.get_conver_by_name(name), timeout=2)
        logger.info(f"[Action-Home] 获取特定名称会话: {name}")
        return result

    # 获取第一个会话时间
    def get_conversation_time(self, index=0):
        time_text = self.get_attribute(HomeLocator.CONVERSATION_TIME, 'text')
        logger.info(f"[Action-Home] 获取第一个会话时间: {time_text}")
        return time_text

    # 获取页面所有会话时间
    def get_conversation_times(self):
        elements = self.find_elements(HomeLocator.CONVERSATION_TIME)
        times = [element.get_attribute('text') for element in elements]
        logger.info(f"[Action-Home] 获取页面所有会话时间数量: {len(times)}")
        return times

    # 获取第一个会话内容
    def get_conversation_content(self, index=0):
        content = self.get_attribute(HomeLocator.CONVERSATION_CONTENT, 'text')
        logger.info(f"[Action-Home] 获取第一个会话内容: {content}")
        return content

    # 获取页面所有会话内容
    def get_conversation_contents(self):
        elements = self.find_elements(HomeLocator.CONVERSATION_CONTENT)
        contents = [element.get_attribute('text') for element in elements]
        logger.info(f"[Action-Home] 获取页面所有会话内容数量: {len(contents)}")
        return contents

    # 获取第一个会话未读消息数
    def get_conversation_unread_count(self, index=0):
        count = self.get_attribute(HomeLocator.CONVERSATION_UNREAD_COUNT, 'text')
        logger.info(f"[Action-Home] 获取第一个会话未读消息数: {count}")
        return count

    # 获取第一个会话未读消息数内部
    def get_conversation_unread_count_inner(self, index=0):
        count = self.get_attribute(HomeLocator.CONVERSATION_UNREAD_COUNT_INNER, 'text')
        logger.info(f"[Action-Home] 获取第一个会话内部未读消息数: {count}")
        return count

    # 通过好友昵称获取他的会话下面有没有消息内容
    def get_message_by_name(self, name: str):
        content = self.get_attribute(HomeLocator.get_message_by_name(name), 'text')
        logger.info(f"[Action-Home] 通过好友昵称[{name}]获取他的消息内容: {content}")
        return content

    # 会话静音
    def click_conversation_mute(self):
        self.click(HomeLocator.CONVERSATION_MUTE, force_wait=True)
        logger.info("[Action-Home] 点击会话静音")

    # 会话置顶
    def click_conversation_top(self):
        self.click(HomeLocator.CONVERSATION_TOP, force_wait=True)
        logger.info("[Action-Home] 点击会话置顶")

    # 会话删除
    def click_conversation_delete(self):
        self.click(HomeLocator.CONVERSATION_DELETE, force_wait=True)
        logger.info("[Action-Home] 点击会话删除")

    # 会话删除弹窗 清空聊天记录
    def click_conversation_delete_dialog_clear_chat_record(self):
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CLEAR_CHAT_RECORD, force_wait=True)
        logger.info("[Action-Home] 在删除会话弹窗勾选 清空聊天记录")

    # 会话删除弹窗 确认删除
    def click_conversation_delete_dialog_confirm(self):
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CONFIRM, force_wait=True)
        logger.info("[Action-Home] 在删除会话弹窗点击 确认")

    # 会话删除弹窗 取消
    def click_conversation_delete_dialog_cancel(self):
        self.click(HomeLocator.CONVERSATION_DELETE_DIALOG_CANCEL, force_wait=True)
        logger.info("[Action-Home] 在删除会话弹窗点击 取消")

    # 会话获取草稿状态
    def get_remind_status(self):
        status = self.get_attribute(HomeLocator.CONVERSATION_DRAFT, 'text')
        logger.info(f"[Action-Home] 获取会话草稿状态: {status}")
        return status

    # 会话获取未读/已读状态
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
    
    # 会话获取停用状态
    def get_disable_status(self, name: str) -> bool:
        """
        获取指定会话的停用状态
        :param name: 会话名称
        :return: True 如果会话被停用=True,正常=False
        """
        is_disabled = self.find_element(HomeLocator.get_disable_by_name(name), timeout=2) is not None
        logger.info(f"[Action-Home] 获取指定会话 [{name}] 停用状态: {is_disabled}")
        return is_disabled

    # 会话安全点击列表项，防止被底部悬浮栏遮挡
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

    # ---- 置顶折叠相关 ----
    def is_fold_entry_visible(self) -> bool:
        """检查置顶折叠入口是否可见"""
        result = self.is_element_exist(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=3)
        logger.info(f"📌 折叠入口可见: {result}")
        return result

    # 当折叠入户被隐藏时，需要下滑需寻找如何获取折叠数量 
    def is_fold_count_visible(self, max_attempts=5) -> WebElement | None:
        """
        当折叠入口被隐藏时，需要下滑需寻找如何获取折叠数量 
        Args:
            max_attempts: 最大尝试次数
        Returns:
            WebElement: 折叠入口元素
        """
        while max_attempts > 0:
            fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=3)
            if fold_elem:
                return fold_elem
            max_attempts -= 1
            self.swipe_page('up', duration=500)
        return None

    # 获取折叠入口显示的置顶数量
    def get_fold_count(self) -> int:
        """
        获取折叠入口显示的置顶数量 
        Args:
            None
        Returns:
            int: 折叠数量
        """
        fold_elem = self.is_fold_count_visible()
        text = fold_elem.get_attribute('text') if fold_elem else ""
        self.swipe_page_quickly(slid_type='down', duration=200)
        if not text:
            return 0
        # 提取数字
        nums = re.findall(r'\d+', text)
        count = int(nums[0]) if nums else 0
        logger.info(f"📌 折叠数量文案: [{text}], 解析数量: {count}")
        return count

    # 点击折叠入口（优先点击整个 ViewGroup，兼容图标和文本）
    def click_fold_entry(self, first_name: str = None, max_retries=3):
        """
        点击折叠入口（优先点击整个 ViewGroup，兼容图标和文本）
        Args:
            first_name: 第一个好友昵称
            max_retries: 最大尝试次数
        Returns:
            bool: True 表示点击成功，False 表示超时
        """
        name_locator = HomeLocator.get_conver_by_name(first_name)

        for attempt in range(max_retries):
            logger.info(f"👉 准备点击折叠入口 (第 {attempt + 1}/{max_retries} 次尝试)")

            try:
                fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_VIEWGROUP, timeout=2)
            except Exception:
                fold_elem = self.find_element(HomeLocator.CONVERSATION_FOLD_COUNT_TEXT, timeout=2)

            if not fold_elem:
                raise RuntimeError("❌ 未找到折叠入口元素")

            self.tap_point(click_elem=fold_elem)
            aft_name = self.get_attribute(name_locator, 'text')
            if first_name != aft_name:
                logger.info(f"✅ 点击成功且 UI 已响应！没有找到 {first_name}")
                return True
            else:
                logger.warning(f"⚠️ 置顶会话折叠失败，点击了但 UI 没反应 折叠前 {first_name}, 折叠后 {aft_name}，准备重试...")
                time.sleep(1)
        raise RuntimeError(f"❌ 连续 {max_retries} 次点击折叠入口，UI 均无响应！")


    # 输入聊天密码
    def input_chat_password(self, password: str = "111111", index: int = 0) -> None:
        """
        输入聊天密码 
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

        




