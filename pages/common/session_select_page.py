import time
from typing import Optional, List
from appium.webdriver.common.appiumby import AppiumBy
from pages.common.common_page import CommonPage
from locators.common.session_select_locator import SessionSelectLocator
from core.logger_utils import logger


class SessionSelectPage(CommonPage):
    """通用会话选择组件页面对象"""

    # 会话选择页 - 等待页面加载完成
    def wait_for_session_page_load(self, msg_type: int = 0, timeout: int = 10) -> bool:
        """
        等待页面加载完成
        :param msg_type: 消息类型 0: 文本/群聊/文件/视频/语音等 1: 图片
        :param timeout: 超时时间
        :return: 页面是否加载完成
        """
        logger.info(f"⏳ [Wait - SessionSelect] 会话选择页 - 等待页面加载 (消息类型: {msg_type}, 超时: {timeout}s)")
        if msg_type == 1:
            res = self.is_element_exist(SessionSelectLocator.FRIEND_RV, timeout=timeout)
        else:
            res = self.is_element_exist(SessionSelectLocator.SHARE_RV, timeout=timeout)
        logger.info(f"⏳ [Action - SessionSelect] 会话选择页 - 页面加载 {'成功' if res else '超时'} in {timeout}s")
        return res

    # 顶部 Bar 操作 - 点击返回
    def click_back_button(self) -> None:
        """ 点击返回按钮 """
        logger.info("🔙 [Action - SessionSelect] 会话选择页 - 点击返回")
        self.click(SessionSelectLocator.BACK_BUTTON, force_wait=True)

    # 顶部 Bar 操作 - 获取标题
    def get_title(self) -> str:
        """ 获取标题 """
        title = self.get_attribute(SessionSelectLocator.TITLE_TEXT, 'text')
        logger.info(f"📋 [Action - SessionSelect] 会话选择页 - 获取标题: {title}")
        return title

    # 会话选择页 - 点击确定按钮
    def click_finish_button(self, msg_type: int = 0, timeout: int = 2) -> None:
        """
        点击确定按钮
        :param msg_type: 消息类型 0: 文本/群聊/文件/视频/语音等 1: 图片
        :param timeout: 超时时间
        """
        logger.info(f"✅ [Action - SessionSelect] 会话选择页 - 点击确定 (类型: {msg_type})")
        if msg_type == 1:
            self.click(SessionSelectLocator.TOP_FB_ACTION_BTN, timeout=timeout)
        else:
            self.click(SessionSelectLocator.FINISH_BUTTON, timeout=timeout)
        time.sleep(1)

    # 会话选择页 - 点击勾选按钮(默认第一个)
    def click_checkbox_button(self) -> None:
        """ 点击勾选按钮 """
        logger.info("✅ [Action - SessionSelect] 会话选择页 - 点击勾选")
        self.click(SessionSelectLocator.SESSION_CHECKBOX)

    # 会话选择页 - 获取所有勾选按钮元素列表
    def get_all_checkbox_buttons(self) -> list:
        """ 获取所有勾选按钮 """
        checkbox_buttons = self.find_elements(SessionSelectLocator.SESSION_CHECKBOX)
        logger.info(f"✅ [Action - SessionSelect] 会话选择页 - 获取所有勾选按钮: {len(checkbox_buttons)}")
        return checkbox_buttons
    
    # 会话选择页 - 获取所有可见的会话名称
    def get_all_visible_session_names(self) -> list[str]:
        """ 获取所有可见的会话名称 """
        elements = self.find_elements(SessionSelectLocator.SESSION_NAME, timeout=3, expect_missing=True)
        names = [elem.text for elem in elements if elem.text]
        logger.info(f"📋 [Action - SessionSelect] 会话选择页 - 获取到 {len(names)} 个可见会话")
        return names

    # 会话选择页 - 通过名称选择会话
    def select_session_by_name(self, name: str, loop_max: int = 10) -> bool:
        """
        在会话列表中滑动查找并选中目标会话。
        :param name: 目标会话/群聊名称
        :param loop_max: 最大滑动次数
        :return: 是否成功选中
        """
        last_source = ""
        logger.info(f"🔍 [Action - SessionSelect] 会话选择页 - 开始寻找会话: [{name}]")

        for i in range(loop_max):
            elements = self.find_elements(SessionSelectLocator.get_session_by_name(name), timeout=2, expect_missing=True)
            if elements:
                logger.info(f"✅ [Action - SessionSelect] 会话选择页 - 成功点击目标会话: {name}")
                elements[0].click()
                time.sleep(0.5)
                return True

            is_changed, last_source = self.is_page_source_changed(last_source)
            if not is_changed:
                logger.warning(f"🛑 [Action - SessionSelect] 会话选择页 - 已滑动到底部，仍未找到会话: {name}")
                break

            logger.info(f"⏳ [Action - SessionSelect] 会话选择页 - 第 {i + 1} 次向下滑动寻找...")
            self.swipe_page(slid_type='up', duration=800)
            time.sleep(1)

        logger.error(f"❌ [Action - SessionSelect] 会话选择页 - 遍历结束或已到底部，未找到目标会话: {name}")
        return False

    # ==================== 分享/转发确认弹层相关操作 ====================

    # 分享弹层 - 等待分享确认弹层加载
    def wait_for_share_dialog_load(self, timeout: int = 5) -> bool:
        """ 等待分享/转发确认弹层出现 """
        logger.info(f"⏳ [Wait - SessionSelect] 会话选择页 - 等待分享弹层出现 (超时: {timeout}s)")
        res = self.is_element_exist(SessionSelectLocator.SEND_BUTTON, timeout=timeout)
        logger.info(f"⏳ [Action - SessionSelect] 会话选择页 - 分享确认弹层加载 {'成功' if res else '超时'} in {timeout}s")
        return res

    # 分享弹层 - 点击发送按钮
    def click_share_dialog_send(self, force_wait: bool = True) -> None:
        """ 点击分享确认弹层的【发送】按钮 """
        logger.info("✅ [Action - SessionSelect] 会话选择页 - 点击分享弹层发送按钮")
        self.click(SessionSelectLocator.SEND_BUTTON, force_wait=force_wait)

    # 分享弹层 - 点击发送并验证 Toast 提示
    def send_share_and_verify_toast(self, expected_toast: str = "转发成功", timeout: float = 3.0) -> bool:
        """ 点击分享确认弹层的发送按钮，并立即捕获校验 Toast 提示 """
        logger.info(f"⚙️ [Action - SessionSelect] 会话选择页 - 点击分享弹层发送并校验 Toast: {expected_toast}")
        self.click_share_dialog_send()
        return self.verify_toast_exist(expected_toast=expected_toast, timeout=timeout)

    # 分享弹层 - 点击取消关闭按钮
    def click_share_dialog_close(self, force_wait: bool = True) -> None:
        """ 点击分享确认弹层的【取消/关闭】按钮 """
        logger.info("🔙 [Action - SessionSelect] 会话选择页 - 点击分享弹层取消按钮")
        self.click(SessionSelectLocator.CLOSE, force_wait=force_wait)

    # 分享弹层 - 输入留言内容
    def input_share_dialog_comment(self, comment: str) -> None:
        """ 在分享确认弹层的输入框中输入留言内容 """
        logger.info(f"✏️ [Action - SessionSelect] 会话选择页 - 分享弹层输入留言: {comment}")
        self.send_keys(SessionSelectLocator.COMMENT_INPUT, comment)

    # 分享弹层 - 点击表情按钮
    def click_share_dialog_emoji(self, force_wait: bool = True) -> None:
        """ 点击分享确认弹层的表情按钮 """
        logger.info("😄 [Action - SessionSelect] 会话选择页 - 点击分享弹层表情按钮")
        self.click(SessionSelectLocator.EMOJI_BUTTON, force_wait=force_wait)

    # 分享弹层 - 确认分享业务流程
    def confirm_share(self, comment: Optional[str] = None, timeout: int = 5) -> bool:
        """
        高级业务组合方法：等待确认弹窗出现，可选输入留言，点击发送并完成分享
        :param comment: 可选的附带留言文本
        :param timeout: 最长等待超时时间
        :return: 是否成功完成确认分享
        """
        logger.info(f"⚙️ [Action - SessionSelect] 会话选择页 - 开始确认分享流程 (留言: {comment})")
        if not self.wait_for_share_dialog_load(timeout=timeout):
            logger.error("❌ [Action - SessionSelect] 会话选择页 - 未检测到分享确认弹层，无法确认发送")
            return False
        if comment:
            self.input_share_dialog_comment(comment)
        self.click_share_dialog_send()
        time.sleep(0.5)
        logger.info("🎉 [Action - SessionSelect] 会话选择页 - 成功确认并发送分享内容")
        return True
