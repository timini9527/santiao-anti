from common.base_page import BasePage
from locators.common.common_locator import CommonLocator
from core.logger_utils import logger


class CommonPage(BasePage):
    """通用页面对象"""

    # 通用 - 点击顶部左上角按钮
    def click_left_top_button(self) -> None:
        """ 点击顶部左上角按钮 """
        logger.info("⚙️ [Action - Common] 点击顶部左上角按钮")
        self.click(CommonLocator.LEFT_TOP_BUTTON_ID, force_wait=True)

    # 通用 - 点击顶部右上角按钮
    def click_right_top_button(self) -> None:
        """ 点击顶部右上角按钮 """
        logger.info("⚙️ [Action - Common] 点击顶部右上角按钮")
        self.click(CommonLocator.RIGHT_TOP_BUTTON_ID, force_wait=True)

    # 通用 - 获取主页顶部中间标题
    def get_home_top_middle_title(self) -> str:
        """ 获取主页顶部中间标题 """
        title = self.get_attribute(CommonLocator.TOP_MIDDLE_TITLE_HOME, 'text')
        logger.info(f"🧐 [Action - Common] 获取主页顶部中间标题: {title}")
        return title

    # 通用 - 点击取消按钮
    def click_cancel_button(self) -> None:
        """ 点击取消按钮 """
        logger.info("⚙️ [Action - Common] 点击取消按钮")
        self.click(CommonLocator.CANCEL_BUTTON_ID)

    # 通用 - 获取顶部中间标题
    def get_top_middle_title(self) -> str:
        """ 获取顶部中间标题 通用 """
        title = self.get_attribute(CommonLocator.TOP_TV_TITLE, 'text')
        logger.info(f"🧐 [Action - Common] 获取顶部中间标题: {title}")
        return title

    # 通用 - 左上角返回按钮
    def click_iv_back_button(self) -> None:
        """ 左上角返回按钮 通用 """
        logger.info("⚙️ [Action - Common] 点击返回按钮")
        self.click(CommonLocator.TOP_IV_BACK_BTN)
    
    # 通用 - 右上角操作按钮
    def click_action_button(self) -> None:
        """ 右上角操作按钮 通用 """
        logger.info("⚙️ [Action - Common] 点击操作按钮")
        self.click(CommonLocator.TOP_FB_ACTION_BTN)
    
    # 通用 - 获取 Toast 通用
    def get_toast_message_common(self) -> str:
        """ 通用 获取 Toast 消息 """
        toast = self.get_attribute(CommonLocator.TOAST_MSG, 'text')
        logger.info(f"🧐 [Action - Common] 获取 Toast 消息: {toast}")
        return toast
