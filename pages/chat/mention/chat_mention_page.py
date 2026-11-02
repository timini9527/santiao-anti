import time
from typing import Optional
from appium.webdriver.common.appiumby import AppiumBy
from common.base_page import BasePage
from locators.chat.mention.chat_mention_locator import ChatMentionLocator
from core.logger_utils import logger, LogIcon


class ChatMentionPage(BasePage):
    """
    群聊@强提醒选人页面 (Mention / At Member Picker) Page Object
    负责处理在聊天输入框键入 @ 之后唤起的成员选择界面的交互：
    1. 等待选人列表浮层/页面就绪与退出关闭
    2. 检查并点击【@所有人】
    3. 支持精准定位、UiScrollable 滑动检索、搜索框检索群成员
    4. 支持单选点击条目与多选勾选
    """

    # 等待选人列表加载就绪
    def wait_for_mention_page_load(self, timeout: int = 5) -> bool:
        """ 等待群聊@选人界面加载就绪 """
        logger.info(f"{LogIcon.WAIT} 等待群聊@选人页面加载就绪 (超时: {timeout}s)...")
        st = self.is_element_exist(ChatMentionLocator.MEMBER_LIST_RV, timeout=timeout, raise_exception=False)
        if not st:
            st = self.is_element_exist(ChatMentionLocator.LL_AT_ALL, timeout=2, raise_exception=False)
        logger.info(f"{LogIcon.SUCCESS} 选人页面就绪状态: {st}")
        return st

    # 等待选人列表退出关闭
    def wait_for_mention_page_close(self, timeout: int = 3) -> bool:
        """ 等待群聊@选人界面成功退出并销毁 """
        logger.info(f"{LogIcon.WAIT} 等待群聊@选人页面退出关闭 (超时: {timeout}s)...")
        res = self.wait_until_element_disappear(ChatMentionLocator.MEMBER_LIST_RV, timeout=timeout)
        logger.info(f"{LogIcon.SUCCESS} 选人页面关闭状态: {res}")
        return res

    # 顶部导航栏 - 点击返回/取消按钮
    def click_back_button(self) -> None:
        """ 点击顶部返回按钮取消@选人 """
        logger.info(f"{LogIcon.ACTION} 点击顶部返回按钮")
        self.click(ChatMentionLocator.TOP_IV_BACK_BTN)

    # 顶部导航栏 - 获取页面标题文本
    def get_title_text(self, timeout: int = 2) -> str:
        """ 获取选人页面顶部标题文本 """
        logger.info(f"{LogIcon.FIND} 📖 [Action-Mention] 获取选人页面顶部标题文本")
        title = self.get_attribute(ChatMentionLocator.TOP_TV_TITLE, "text", timeout=timeout, raise_exception=False)
        logger.info(f"{LogIcon.SUCCESS} 获取页面标题: '{title}'")
        return title or ""

    # 顶部导航栏 - 点击确认/完成按钮
    def click_confirm_btn(self) -> None:
        """ 点击右上角确认/完成按钮 """
        logger.info(f"{LogIcon.SETUP} 点击右上角确认/完成按钮")
        self.click(ChatMentionLocator.TOP_IV_ACTION_BTN)

    # 检查【@所有人】选项是否可见
    def is_at_all_displayed(self, timeout: int = 2) -> bool:
        """ 检查【@所有人】整行选项是否可见（用于群管理权限校验） """
        res = self.is_element_exist(ChatMentionLocator.LL_AT_ALL, timeout=timeout, raise_exception=False)
        logger.info(f"{LogIcon.FIND} 检查【@所有人】可见性: {res}")
        return res

    # 点击选择【@所有人】
    def click_at_all(self) -> None:
        """点击选择【@所有人】选项"""
        logger.info(f"{LogIcon.ACTION} 🔘 [Action-Mention] 点击选择【@所有人】选项")
        self.click(ChatMentionLocator.LL_AT_ALL, force_wait=True)

    # 在群成员列表中查找并点击选择指定成员
    def click_member_by_name(self, name: str) -> None:
        """在群成员列表中根据姓名选择指定群成员"""
        logger.info(f"{LogIcon.ACTION} 🔘 [Action-Mention] 在群成员列表中选择成员【{name}】")
        self.click(ChatMentionLocator.get_member_item_by_name(name), force_wait=True)

    # 统一选人入口
    def select_mention_target(self, target: str = "all", member_name: str = "") -> None:
        """
        群聊@选人统一业务入口：自适应选择【所有人】或指定群成员
        :param target: 目标类型，'at_all' / 'all' / '所有人' 代表全员，'at_me' / 'member' 代表指定群成员
        :param member_name: 当为指定成员时，传入成员昵称
        """
        self.wait_for_mention_page_load(timeout=5)
        if target in ("at_all", "all", "所有人"):
            self.click_at_all()
        else:
            name = member_name or target
            self.click_member_by_name(name)
        self.click_confirm_btn()
        self.wait_for_mention_page_close()