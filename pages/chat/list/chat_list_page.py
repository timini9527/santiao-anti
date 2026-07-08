import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from common.base_page import BasePage 
from pages.system.home.home_page import HomePage
from locators.system.home.home_locator import HomeLocator as HL
from pages.chat.core.chat_page import ChatPage
import allure
from core.logger_utils import logger


# 会话列表页（负责进入会话）
@allure.story("会话列表页")
@allure.feature("会话列表页")
class ChatListPage(ChatPage):

    # 等待聊天会话列表页加载
    def wait_chat_list_page_load(self, timeout=10) -> bool:
        """等待聊天会话列表页加载"""
        end_time = time.time() + timeout
        while time.time() <= end_time:
            home_title = self.get_attribute(HL.MIDDLE_TITLE, 'text')
            if home_title and "三条" in home_title:
                logger.info(f"✅ 进入会话列表")
                return True
            time.sleep(0.2)
        logger.warning(f"❌ 未找到会话列表项")
        return False

    # 快速下滑避免页面不是原始页面
    def _quick_slide_to_top(self):
        self.swipe_page_quickly(slid_type='down', duration=200)

    # 快速下滑一直到底部
    def _quick_slide_to_bottom(self):
        self.swipe_page_quickly(slid_type='up', duration=200)

    def _find_session_element_in_list(self, target_name: str, match_type: str = "exact", timeout: int = 3):
        """
        [内部辅助方法] 在当前列表视图中查找特定名称的会话元素
        :param target_name: 目标会话名称
        :param match_type: 匹配模式，"exact" (完全匹配) 或 "partial" (部分匹配/包含)
        :param timeout: 超时时间
        :return: 找到的 WebElement 对象 或 None
        """
        end_time = time.time() + timeout
        while time.time() <= end_time:
            # 获取当前屏幕可见的所有会话名称元素 (设短超时，避免找不到时卡住)
            session_elems = self.find_elements(HL.CONVERSATION_NAME, timeout=1, raise_exception=True)
            
            if session_elems:
                # 遍历匹配文本
                for elem in session_elems:
                    try:
                        # 增加 clean_ui_text 过滤不可见零宽字符，确保匹配准确
                        elem_text = self.clean_ui_text(elem.text.strip())
                        target_name_clean = self.clean_ui_text(target_name.strip())
                        if match_type == "exact" and target_name_clean == elem_text:
                            return elem
                        elif match_type == "partial" and target_name_clean in elem_text:
                            return elem
                    except Exception:
                        pass
            
            time.sleep(0.5)  # 等待 0.5s 后重新获取元素列表进行判断

        logger.debug(f"超时 {timeout}s 后，仍未在当前列表找到会话: {target_name}")
        return None

    # 会话左滑设置
    def _get_row_element_by_name(self, target_name: str, match_type: str = "exact"):
        """
        [内部辅助方法] 获取包含该名字的整行容器元素（用于侧滑）
        :param target_name: 目标会话名称
        :param match_type: 匹配模式，"exact" (完全匹配) 或 "partial" (部分匹配/包含)
        """
        chat_rows = self.find_elements(HL.CONVERSATION_ITEM, timeout=3)
        for row in chat_rows:
            try:
                name_elem = row.find_element(*HL.CONVERSATION_NAME)
                elem_text = name_elem.text.strip()
                if match_type == "exact" and elem_text == target_name:
                    return row
                elif match_type == "partial" and target_name in elem_text:
                    return row
            except Exception as e:
                continue
        return None

    # 进入指定会话
    def enter_session(self, session_name: str, match_type: str = "exact", timeout: int = 3) -> bool:
        """进入指定的会话
        :param match_type: "exact" (精确匹配) 或 "partial" (部分匹配)
        :param timeout: 超时时间
        """
        content_elem = self._find_session_element_in_list(session_name, match_type, timeout)
        if content_elem:
            content_elem.click()
            self.wait_for_chat_page_load()
            logger.info(f"✅ 进入会话: {session_name} (匹配模式: {match_type})")
            return True
        logger.warning(f"❌ 未找到会话: {session_name}")
        return False

    # 进入私聊或群聊通用 方法
    def common_enter_chat(self, chat_name, result_locator=None, match_type: str = "exact", timeout: int = 3):
        """
        [通用逻辑] 进入会话：优先列表查找 -> 失败则走搜索栏搜索
        :param chat_name: 目标名称 (私聊名 或 群聊名)
        :param result_locator: 搜索结果的点击定位符 (如果不传，默认尝试点击包含名字的元素)
        :param match_type: "exact" (精确匹配) 或 "partial" (部分匹配)
        :param timeout: 超时时间
        """
        logger.info(f"👉 准备进入会话: 【{chat_name}】")
        # 1. 尝试在列表直接点击
        if self.enter_session(chat_name, match_type=match_type, timeout=timeout):
            logger.info(f"✅ 在首页列表中找到并成功进入: {chat_name}")
            return

        logger.info(f"列表未找到 {chat_name}，执行搜索...")
        self.click(HL.SEARCH_INPUT)
        self.send_keys(HL.SEARCH_INPUT, chat_name)
        time.sleep(0.5)

        # 场景 A：如果你传了特定的搜索结果定位器
        if result_locator:
            try:
                self.click(result_locator, force_wait=True)
                logger.info(f"✅ 通过指定的 {result_locator} 成功进入: {chat_name}")
                time.sleep(1)
                return
            except Exception as e:
                logger.error(f"使用 {result_locator} 点击搜索结果失败: {e}")
        # 场景 B：默认复用名称匹配逻辑去点击
        else:
            if self.enter_session(chat_name, match_type=match_type, timeout=timeout):
                logger.info(f"✅ 在搜索列表中找到并成功进入: {chat_name}")
                return
            
            # 备用兜底逻辑：如果复用 enter_session 没匹配到，直接使用 UiSelector 按文本查找并点击
            logger.info(f"⚠️ [场景B] enter_session 查找失败，开始尝试使用文本直接定位点击会话: {chat_name}")
            try:
                text_locator = HL.get_conver_by_name(chat_name)
                if self.is_element_exist(text_locator, timeout=timeout):
                    self.click(text_locator, force_wait=True)
                    self.wait_for_chat_page_load()
                    logger.info(f"✅ [备用兜底] 通过文本直接定位并成功进入: {chat_name}")
                    return
            except Exception as e:
                logger.warning(f"⚠️ [备用兜底] 通过文本直接定位点击失败: {e}")

        # 如果首页没有，搜也搜不到，必须抛出异常阻断测试，防止后续步骤乱点！
        error_msg = f"❌ 严重错误：无法在首页及搜索结果中找到会话【{chat_name}】"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # 获取聊天页面好友名称
    def get_friend_name(self, friend_name: str) -> bool:
        return True if friend_name in self.get_top_name() else False

    # 进入会话
    def enter_chat(self, session_name: str = None, match_type: str = "exact", timeout: int = 3):
        """
        统一的进入会话方法
        :param session_name: 策略对象，包含 chat_type 和 name
        :param match_type: 匹配模式，"exact" (精确匹配) 或 "partial" (部分匹配)
        :param timeout: 超时时间
        """
        self.common_enter_chat(chat_name=session_name, match_type=match_type, timeout=timeout)

    # 进入私聊会话
    def enter_private_chat(self, session_name: str = None, match_type: str = "exact", timeout: int = 3):
        """进入私聊 (使用类属性中的默认名称) 从列表进入特定好友的聊天窗 """
        self.common_enter_chat(chat_name=session_name, match_type=match_type, timeout=timeout)

    # 进入群聊会话
    def enter_group_chat(self, session_name: str = None, match_type: str = "exact", timeout: int = 3):
        """进入群聊 (使用类属性中的默认名称)"""
        self.common_enter_chat(chat_name=session_name, match_type=match_type, timeout=timeout)

    # 通用逻辑，侧滑会话并点击指定菜单
    def common_set_left_menu(self, session_name: str, menu_locator: tuple, slide_action: str = None) -> str:
        """
        侧滑会话并点击指定菜单 (支持智能校验与盲点)
        :param session_name: 目标会话名称
        :param menu_locator: 侧滑后要点击的元素定位符 (如: 置顶、删除、静音)
        :param slide_action: (可选) 如果传入此值，则只有 menu_text == slide_action 时才点击；否则收起菜单。
        :return: 返回侧滑菜单上实际显示的按钮文案
        """
        session_row = self._get_row_element_by_name(session_name)
        if not session_row:
            raise ValueError(f"❌ 在列表中未找到会话: {session_name}，无法执行侧滑操作")

        self.swipe_on_element(session_row, slid_type='left', duration=300)
        # time.sleep(0.8)

        # 2. 获取侧滑按钮文案并点击
        menu_text = self.get_attribute(menu_locator, 'text')
        if not menu_text:
            raise RuntimeError(f"侧滑会话【{session_name}】后，未能获取到菜单按钮的文案！")
        logger.info(f"👉 侧滑【{session_name}】获取到按钮文案: [{menu_text}]")

        if slide_action:
            if menu_text == slide_action:
                self.click(menu_locator, force_wait=True)
                logger.info(f"✅ 执行点击动作: 【{slide_action}】")
                time.sleep(0.5)
            else:
                logger.info(f"🚫 当前按钮为[{menu_text}]，不需要执行[{slide_action}]，取消点击。")
                # self.swipe_on_element(session_row, slider_type='right', duration=300)
                session_row.click()
        else:
            # 盲点模式（不传 slide_action 时，无脑点）
            self.click(menu_locator, force_wait=True)
            logger.info(f"✅ (盲点模式) 对 {session_name} 点击了侧滑菜单: [{menu_text}]")
            time.sleep(0.8)
        return menu_text

    # 设置通知
    def set_notice(self, session_name: str = None, slider_locator: tuple = None, slider_action: str = None):
        return self.common_set_left_menu(session_name, slider_locator, slider_action)

    # 设置置顶
    def set_top(self, session_name: str = None, slider_locator: tuple = None):
        return self.common_set_left_menu(session_name, slider_locator)








