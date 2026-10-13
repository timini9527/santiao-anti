import time
from typing import Optional, Literal
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webelement import WebElement
from selenium.webdriver.common.by import By
from common.base_page import BasePage 
from pages.home.home_page import HomePage
from locators.home.home_locator import HomeLocator as HL
from pages.chat.core.chat_page import ChatPage
import allure
from core.logger_utils import logger


# 会话列表页（负责进入会话）
@allure.story("会话列表页")
@allure.feature("会话列表页")
class ChatListPage(ChatPage):

    # 等待聊天会话列表页加载
    def wait_chat_list_page_load(self, timeout: int = 10) -> bool:
        """等待聊天会话列表页加载"""
        logger.info("⏳ 正在等待聊天会话列表页加载...")
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
    def _quick_slide_to_top(self) -> None:
        """快速向下滑动回顶部"""
        logger.info("执行快速下滑回顶部...")
        self.swipe_page_quickly(slid_type='down', duration=100)

    # 快速下滑一直到底部
    def _quick_slide_to_bottom(self) -> None:
        """快速向上滑动到底部"""
        logger.info("执行快速滑动到底部...")
        self.swipe_page_quickly(slid_type='up', duration=100)

    # 在当前列表视图中查找特定名称的会话元素
    def _find_session_element_in_list(self, target_name: str, match_type: str = "exact", timeout: int = 3) -> Optional[WebElement]:
        """
        [内部辅助方法] 在当前列表视图中查找特定名称的会话元素
        :param target_name: 目标会话名称
        :param match_type: 匹配模式，"exact" (完全匹配) 或 "partial" (部分匹配/包含)
        :param timeout: 超时时间
        :return: 找到的 WebElement 对象 或 None
        """
        logger.info(f"🔍 正在当前列表中检索会话元素: 【{target_name}】(模式: {match_type})...")
        end_time = time.time() + timeout
        while time.time() <= end_time:
            session_elems = self.find_elements(HL.CONVERSATION_NAME, timeout=1, raise_exception=True)
            if session_elems:
                for elem in session_elems:
                    try:
                        elem_text = self.clean_ui_text(elem.text.strip())
                        target_name_clean = self.clean_ui_text(target_name.strip())
                        if match_type == "exact" and target_name_clean == elem_text:
                            return elem
                        elif match_type == "partial" and target_name_clean in elem_text:
                            return elem
                    except Exception:
                        pass
            time.sleep(0.5)
        logger.debug(f"超时 {timeout}s 后，仍未在当前列表找到会话: {target_name}")
        return None

    # 判断指定会话是否存在于当前列表中
    def is_session_exist_in_list(self, target_name: str, match_type: str = "exact", timeout: int = 2) -> bool:
        """
        判断指定会话是否存在于当前列表中
        :param target_name: 目标会话名称
        :param match_type: 匹配模式，"exact" (完全匹配) 或 "partial" (部分匹配/包含)
        :param timeout: 超时时间
        :return: bool (True: 存在, False: 不存在)
        """
        return self._find_session_element_in_list(target_name, match_type=match_type, timeout=timeout) is not None

    # 会话左滑设置
    def _get_row_element_by_name(self, target_name: str, match_type: str = "exact") -> Optional[WebElement]:
        """
        [内部辅助方法] 获取包含该名字的整行容器元素（用于侧滑）
        :param target_name: 目标会话名称
        :param match_type: 匹配模式，"exact" (完全匹配) 或 "partial" (部分匹配/包含)
        """
        logger.info(f"🔍 正在获取会话整行容器元素: 【{target_name}】...")
        chat_rows = self.find_elements(HL.CONVERSATION_ITEM, timeout=3)
        for row in chat_rows:
            try:
                name_elem = row.find_element(*HL.CONVERSATION_NAME)
                elem_text = name_elem.text.strip()
                if match_type == "exact" and elem_text == target_name:
                    return row
                elif match_type == "partial" and target_name in elem_text:
                    return row
            except Exception:
                continue
        return None

    # 进入指定会话
    def enter_session(self, session_name: str, match_type: str = "exact", timeout: int = 2) -> bool:
        """进入指定的会话
        :param match_type: "exact" (精确匹配) 或 "partial" (部分匹配)
        :param timeout: 超时时间
        """
        logger.info(f"👉 准备检索并进入会话: 【{session_name}】(匹配模式: {match_type})...")
        content_elem = self._find_session_element_in_list(session_name, match_type, timeout)
        if content_elem:
            logger.info(f"👉 点击会话元素: 【{session_name}】...")
            content_elem.click()
            self.wait_for_chat_page_load()
            logger.info(f"✅ 进入会话完成: {session_name} (匹配模式: {match_type})")
            return True
        logger.warning(f"❌ 未找到会话: {session_name}")
        return False

    # 进入私聊或群聊通用 方法
    def common_enter_chat(self, chat_name: str, result_locator: Optional[tuple] = None, match_type: str = "exact", timeout: int = 3) -> None:
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
        logger.info("点击搜索框并输入关键词...")
        self.click(HL.SEARCH_INPUT)
        logger.info(f"向搜索框输入会话名: 【{chat_name}】...")
        self.send_keys(HL.SEARCH_INPUT, chat_name)
        time.sleep(0.5)

        # 场景 A：如果你传了特定的搜索结果定位器
        if result_locator:
            try:
                logger.info(f"准备点击指定的搜索结果定位符: {result_locator}...")
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
                    logger.info(f"点击文本定位匹配的会话: 【{chat_name}】...")
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
        """校验顶部标题是否包含好友名称"""
        logger.info(f"校验顶部标题是否包含好友名称: 【{friend_name}】...")
        return True if friend_name in self.get_top_name() else False

    # 进入会话
    def enter_chat(self, session_name: Optional[str] = None, match_type: str = "exact", timeout: int = 3) -> None:
        """
        统一的进入会话方法
        :param session_name: 目标会话名称
        :param match_type: 匹配模式，"exact" (精确匹配) 或 "partial" (部分匹配)
        :param timeout: 超时时间
        """
        self.common_enter_chat(chat_name=session_name, match_type=match_type, timeout=timeout)

    # 进入私聊会话
    def enter_private_chat(self, session_name: Optional[str] = None, match_type: str = "exact", timeout: int = 3) -> None:
        """进入私聊 (使用类属性中的默认名称) 从列表进入特定好友的聊天窗 """
        self.common_enter_chat(chat_name=session_name, match_type=match_type, timeout=timeout)

    # 进入群聊会话
    def enter_group_chat(self, session_name: Optional[str] = None, match_type: str = "exact", timeout: int = 3) -> None:
        """进入群聊 (使用类属性中的默认名称)"""
        self.common_enter_chat(chat_name=session_name, match_type=match_type, timeout=timeout)

    # 通用逻辑，侧滑会话并点击指定菜单
    def common_set_left_menu(self, session_name: str, menu_locator: tuple, slide_action: Optional[str] = None) -> str:
        """
        侧滑会话并点击指定菜单 (支持智能校验与盲点)
        :param session_name: 目标会话名称
        :param menu_locator: 侧滑后要点击的元素定位符 (如: 置顶、删除、静音)
        :param slide_action: (可选) 如果传入此值，则只有 menu_text == slide_action 时才点击；否则安全收起菜单。
        :return: 返回侧滑菜单上实际显示的按钮文案
        """
        logger.info(f"👉 准备对会话【{session_name}】执行左滑操作...")
        session_row = self._get_row_element_by_name(session_name)
        if not session_row:
            raise ValueError(f"❌ 在列表中未找到会话: {session_name}，无法执行侧滑操作")

        # 1. 执行左滑手势并自适应容错
        self.swipe_on_element(session_row, slid_type='left', duration=300, toptime=500)
        menu_text = (self.get_attribute(menu_locator, 'text') or "").strip()

        # 滑动未成功暴露菜单时的轻量补偿重试
        if not menu_text:
            logger.warning(f"⚠️ 首次左滑未获取到菜单文案，尝试补偿左滑...")
            refreshed_row = self._get_row_element_by_name(session_name) or session_row
            self.swipe_on_element(refreshed_row, slid_type='left', duration=300, toptime=500)
            menu_text = (self.get_attribute(menu_locator, 'text') or "").strip()

        if not menu_text:
            raise RuntimeError(f"侧滑会话【{session_name}】后，未能获取到菜单按钮的文案！")
        logger.info(f"👉 侧滑【{session_name}】获取到按钮文案: [{menu_text}]")

        # 2. 根据目标动作执行点击或安全收起
        if slide_action:
            if menu_text == slide_action:
                logger.info(f"👉 准备执行点击动作: 【{slide_action}】...")
                self.click(menu_locator, force_wait=True)
                logger.info(f"✅ 执行点击动作完成: 【{slide_action}】")
            else:
                logger.info(f"🚫 当前按钮为[{menu_text}]，无需执行[{slide_action}]，安全右滑收起侧滑菜单。")
                try:
                    row_to_close = self._get_row_element_by_name(session_name) or session_row
                    self.swipe_on_element(row_to_close, slid_type='right', duration=200, toptime=50)
                except Exception as e:
                    logger.debug(f"右滑收起侧滑异常 (忽略): {e}")
        else:
            # 盲点模式（不传 slide_action 时直接点击）
            logger.info(f"👉 准备执行侧滑菜单点击: [{menu_text}] (盲点模式)...")
            self.click(menu_locator, force_wait=True)
            logger.info(f"✅ (盲点模式) 对 {session_name} 点击了侧滑菜单完成: [{menu_text}]")
        return menu_text

    # 设置通知
    def set_notice(self, session_name: Optional[str] = None, slider_locator: Optional[tuple] = None, slider_action: Optional[str] = None) -> str:
        """设置会话免打扰通知状态"""
        logger.info(f"⚙️ 设置会话通知状态: 【{session_name}】...")
        return self.common_set_left_menu(session_name, slider_locator, slider_action)

    # 设置置顶
    def set_top(self, session_name: Optional[str] = None, slider_locator: Optional[tuple] = None) -> str:
        """设置会话置顶状态"""
        logger.info(f"⚙️ 设置会话置顶状态: 【{session_name}】...")
        return self.common_set_left_menu(session_name, slider_locator)

    # 侧滑置顶会话 (业务级封装，屏蔽 Locator)
    def slide_top_session(self, session_name: str, action: str = "置顶") -> str:
        """
        侧滑指定会话并执行置顶或取消置顶，对用例层完全屏蔽底层 Locator
        :param session_name: 目标会话名称
        :param action: 操作文案 ('置顶' 或 '取消置顶')
        :return: 侧滑按钮实际显示的文案
        """
        logger.info(f"⚙️ 对会话【{session_name}】执行侧滑【{action}】操作...")
        return self.common_set_left_menu(session_name, HL.CONVERSATION_TOP_TEXT, slide_action=action)

    # 侧滑删除会话 (业务级封装，屏蔽 Locator)
    def slide_delete_session(self, session_name: str) -> str:
        """
        侧滑指定会话并点击删除按钮，唤起二次确认弹窗，对用例层完全屏蔽底层 Locator
        :param session_name: 目标会话名称
        :return: 侧滑按钮实际显示的文案 (如: '删除')
        """
        logger.info(f"🗑️ 对会话【{session_name}】执行侧滑删除操作...")
        return self.common_set_left_menu(session_name, HL.CONVERSATION_DELETE_TEXT)

    # 轮询等待顶部首项会话
    def wait_for_first_session_name(self, expect_name: str, timeout: float = 5.0) -> bool:
        """
        轮询等待列表顶部首个会话成为目标会话，解决滑动惯性与置顶重排动画延迟
        :param expect_name: 预期置顶后的会话名称
        :param timeout: 超时时间 (秒)
        :return: bool 是否匹配成功
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            elements = self.find_elements(HL.CONVERSATION_NAME, timeout=1, raise_exception=False)
            if elements:
                names = self.clean_ui_text([e.get_attribute("text") for e in elements if e])
                if names and names[0] == expect_name:
                    return True
            time.sleep(0.3)
        return False
