from typing import Optional
from common.base_page import BasePage
from locators.common.common_locator import CommonLocator
from core.logger_utils import logger, LogIcon


class CommonPage(BasePage):
    """通用页面对象"""

    # 通用 - 点击顶部左上角按钮
    def click_left_top_button(self) -> None:
        """ 点击顶部左上角按钮 """
        logger.info(f"{LogIcon.SETUP} 点击顶部左上角按钮")
        self.click(CommonLocator.TOP_IV_BACK_BTN, force_wait=True)

    # 通用 - 点击顶部右上角按钮
    def click_right_top_button(self) -> None:
        """ 点击顶部右上角按钮 """
        logger.info(f"{LogIcon.SETUP} 点击顶部右上角按钮")
        self.click(CommonLocator.TOP_IV_ACTION_BTN, force_wait=True)

    # 通用 - 获取主页顶部中间标题
    def get_home_top_middle_title(self) -> str:
        """ 获取主页顶部中间标题 """
        title = self.get_attribute(CommonLocator.TOP_TV_TITLE, "text") or ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Common] 获取主页顶部中间标题: {title}")
        return title

    # 通用 - 点击取消按钮
    def click_cancel_button(self) -> None:
        """ 点击取消按钮 """
        logger.info(f"{LogIcon.SETUP} 点击取消按钮")
        self.click(CommonLocator.CANCEL_BUTTON_ID)

    # 通用 - 获取顶部中间标题
    def get_top_middle_title(self) -> str:
        """ 获取顶部中间标题 通用 """
        title = self.get_attribute(CommonLocator.TOP_TV_TITLE, "text") or ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Common] 获取顶部中间标题: {title}")
        return title

    # 通用 - 左上角返回按钮
    def click_iv_back_button(self) -> None:
        """ 左上角返回按钮 通用 """
        logger.info(f"{LogIcon.SETUP} 点击返回按钮")
        self.click(CommonLocator.TOP_IV_BACK_BTN)
    
    # 通用 - 右上角操作按钮
    def click_action_button(self) -> None:
        """ 右上角操作按钮 通用 """
        logger.info(f"{LogIcon.SETUP} 点击操作按钮")
        self.click(CommonLocator.TOP_IV_ACTION_BTN)
    
    # 通用 - 获取 Toast 通用
    def get_toast_message_common(self) -> str:
        """ 通用 获取 Toast 消息 """
        toast = self.get_attribute(CommonLocator.TOAST_MSG, 'text') or ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Common] 获取 Toast 消息: {toast}")
        return toast

    # --------------------------------------------------------------------------
    # 通用弹窗容器作用域操作 (定位细节全收口至 CommonLocator，容器检索能力由 BasePage 统一提供)
    # --------------------------------------------------------------------------
    def _find_ios_dialog_container(self, timeout: float = 2.0):
        """在 iOS 上优先锁定自定义弹窗容器，未命中时再兜底系统 Alert / ActionSheet"""
        container = self.find_element(CommonLocator.DIALOG_CONTAINER, timeout=timeout, expect_missing=True)
        if container is not None:
            return container
        sys_loc = getattr(CommonLocator, "SYSTEM_DIALOG_CONTAINER", None)
        if sys_loc:
            return self.find_element(sys_loc, timeout=0.5, expect_missing=True)
        return None

    def get_dialog_title(self, timeout: float = 3.0) -> str:
        """通用获取当前弹窗标题 (无需硬编码标题文案，兼容 TextView / StaticText / Alert)"""
        if self._platform_name == "ios":
            container = self._find_ios_dialog_container(timeout=timeout)
            child_title_loc = getattr(CommonLocator, "DIALOG_CHILD_TITLE", None)
            if container is not None and child_title_loc:
                for child in self.find_child_elements(container, child_title_loc):
                    title = self.read_element_attr(child, "text").strip()
                    if title:
                        logger.info(f"{LogIcon.FIND} 🧐 [Action - Common] 获取弹窗标题: {title}")
                        return title
            return ""

        title_loc = getattr(CommonLocator, "DIALOG_CONFIRM_TITLE", None)
        if not title_loc:
            return ""
        title = self.get_attribute(title_loc, "text", timeout=int(max(1, timeout)), expect_missing=True) or ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Common] 获取弹窗标题: {title}")
        return title

    def confirm_dialog(self, btn_text: Optional[str] = None, timeout: float = 3.0) -> None:
        """
        通用点击当前弹窗确认按钮:
        - iOS 先锁定弹窗容器再定位子按钮，防止点穿到底层页面同名按钮
        - Android / 鸿蒙直接复用平台 DIALOG_CONFIRM_BTN
        """
        if self._platform_name == "ios":
            container = self._find_ios_dialog_container(timeout=timeout)
            if container is not None:
                if btn_text and hasattr(CommonLocator, "get_dialog_child_button_by_text"):
                    btns = self.find_child_elements(container, CommonLocator.get_dialog_child_button_by_text(btn_text))
                    target_btn = btns[0] if btns else None
                else:
                    btns = self.find_child_elements(container, CommonLocator.DIALOG_CHILD_BUTTONS)
                    target_btn = btns[-1] if btns else None
                if target_btn is not None:
                    self.click_element(target_btn, desc=f"弹窗确认按钮{f' ({btn_text})' if btn_text else ''}")
                    return

            sys_btn = getattr(CommonLocator, "SYSTEM_DIALOG_CONFIRM_BTN", CommonLocator.DIALOG_CONFIRM_BTN)
            logger.info(f"{LogIcon.SETUP} 回退点击系统/单按钮弹窗确认按钮")
            self.click(sys_btn, timeout=int(max(1, timeout)))
            return

        logger.info(f"{LogIcon.SETUP} 点击弹窗确认按钮")
        self.click(CommonLocator.DIALOG_CONFIRM_BTN, timeout=int(max(1, timeout)))

    def cancel_dialog(self, timeout: float = 3.0) -> None:
        """通用点击当前弹窗取消/关闭按钮"""
        if self._platform_name == "ios":
            container = self._find_ios_dialog_container(timeout=timeout)
            if container is not None:
                cancel_btns = self.find_child_elements(container, CommonLocator.DIALOG_CANCEL_BTN)
                if cancel_btns:
                    self.click_element(cancel_btns[0], desc="弹窗取消按钮")
                    return
        logger.info(f"{LogIcon.SETUP} 点击弹窗取消按钮")
        self.click(CommonLocator.DIALOG_CANCEL_BTN, timeout=int(max(1, timeout)))
