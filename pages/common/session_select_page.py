import time
from appium.webdriver.common.appiumby import AppiumBy
from pages.common.common_page import CommonPage
from locators.common.session_select_locator import SessionSelectLocator
from core.logger_utils import logger

class SessionSelectPage(CommonPage):
    """通用会话选择组件页面对象"""

    # 等待页面加载完成
    def wait_for_session_page_load(self, msg_type: int = 0, timeout=10):
        """等待页面加载完成
        :param msg_type: 消息类型 0: 文本/群聊/文件/视频/语音等 1: 图片
        """
        if msg_type == 1:
            res = self.is_element_exist(SessionSelectLocator.RV_FRIENDS, timeout=timeout)
        else:
            res = self.is_element_exist(SessionSelectLocator.SHARE_RV, timeout=timeout)
        logger.info(f"⏳ [Action] 会话选择页 - 页面加载 {'成功' if res else '超时'} in {timeout}s")
        return res

    # 顶部 Bar 操作
    # 点击返回    
    def click_back_button(self):
        """点击返回按钮"""
        self.click(SessionSelectLocator.BACK_BUTTON, force_wait=True)
        logger.info("🔙 [Action] 会话选择页 - 点击返回")

    # 获取标题    
    def get_title(self) -> str:
        """获取标题"""
        title = self.get_attribute(SessionSelectLocator.TITLE_TEXT, 'text')
        logger.info(f"📋 [Action] 会话选择页 - 获取标题: {title}")
        return title

    # 点击确定
    def click_finish_button(self, msg_type: int = 0, timeout=2):
        """点击确定按钮
        :param msg_type: 消息类型 0: 文本/群聊/文件/视频/语音等 1: 图片
        """
        if msg_type == 1:
            self.click(SessionSelectLocator.TOP_FB_ACTION_BTN, timeout=timeout)
        else:
            self.click(SessionSelectLocator.FINISH_BUTTON, timeout=timeout)
        logger.info("✅ [Action] 会话选择页 - 点击确定")
        time.sleep(1)

    # 点击勾选按钮-默认第一个
    def click_checkbox_button(self):
        """点击勾选按钮"""
        self.click(SessionSelectLocator.SESSION_CHECKBOX)
        logger.info("✅ [Action] 会话选择页 - 点击勾选")

    # 获取所有勾选按钮
    def get_all_checkbox_buttons(self) -> list:
        """获取所有勾选按钮"""
        checkbox_buttons =   self.find_elements(SessionSelectLocator.SESSION_CHECKBOX)
        logger.info(f"✅ [Action] 会话选择页 - 获取所有勾选按钮: {len(checkbox_buttons)}")
        return checkbox_buttons
    
    # 获取所有会话名称
    def get_all_visible_session_names(self) -> list:
        """获取所有可见的会话名称"""
        elements = self.find_elements(SessionSelectLocator.SESSION_NAME, timeout=3, expect_missing=True)
        names = [elem.text for elem in elements]
        logger.info(f"📋 [Action] 会话选择页 - 获取到 {len(names)} 个可见会话")
        return names
    

    # 通过名称选择会话
    def select_session_by_name(self, name: str, loop_max: int = 10) -> bool:
        """
        在会话列表中滑动查找并选中目标会话。
        :param name: 目标会话/群聊名称
        :param loop_max: 最大滑动次数
        :return: 是否成功选中
        """
        last_source = ""
        logger.info(f"🔍 [Action] 会话选择页 - 开始寻找会话: [{name}]")

        for i in range(loop_max):
            elements = self.find_elements(SessionSelectLocator.get_session_by_name(name), timeout=2, expect_missing=True)
            if elements:
                elements[0].click()
                logger.info(f"✅ [Action] 会话选择页 - 成功点击目标会话: {name}")
                time.sleep(1)
                return True

            is_changed, last_source = self.is_page_source_changed(last_source)
            if not is_changed:
                logger.warning(f"🛑 [Action] 会话选择页 - 已滑动到底部，仍未找到会话: {name}")
                break

            logger.info(f"⏳ [Action] 会话选择页 - 第 {i + 1} 次向下滑动寻找...")
            self.swipe_page(slid_type='up', duration=800)
            time.sleep(1)

        logger.error(f"❌ [Action] 会话选择页 - 遍历结束或已到底部，未找到目标会话: {name}")
        return False


    








