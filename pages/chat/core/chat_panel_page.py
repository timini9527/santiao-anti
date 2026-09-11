import time
from enum import StrEnum
from common.base_page import BasePage
from locators.chat.core.chat_panel_locator import ChatPanelLocator
from core.logger_utils import logger
from appium.webdriver.webelement import WebElement


class CallType(StrEnum):
    """音视频通话类型枚举"""
    VOICE_CALL = "voice_call"      # 语音通话
    VIDEO_CALL = "video_call"      # 视频通话


class ChatPanelPage(BasePage):
    """聊天页面“+”号扩展面板 Page Object"""

    # 等待功能面板加载完成
    def wait_for_panel_load(self, timeout: int = 10) -> bool:
        """等待扩展面板加载完成"""
        logger.info(f"⏳ [Wait] 等待“+”号扩展面板加载，超时时间 {timeout} 秒")
        is_loaded = self.is_element_exist(ChatPanelLocator.INPUT_MORE_PAGER, timeout=timeout)
        if is_loaded:
            logger.info("✅ [Wait] “+”号扩展面板已成功加载")
        else:
            logger.error("❌ [Wait] “+”号扩展面板加载失败或超时")
        return is_loaded
    
    # 获取功能面板
    def get_function_panel(self) -> WebElement | None:
        """获取功能面板"""
        func_panel = self.find_element(ChatPanelLocator.LL_INPUT_MORE)
        if not func_panel:
            logger.error("❌ [Wait] 功能面板加载失败或超时")
            return None
        logger.info("🖱️ [Action-Panel] 获取功能面板")
        return func_panel

    # 根据名称点击扩展面板中的子功能按钮
    def click_panel_item(self, item_name: str):
        """根据名称点击扩展面板中的子功能按钮"""
        logger.info(f"🖱️ [Action-Panel] 尝试点击扩展面板按钮: 【{item_name}】")
        locator = ChatPanelLocator.get_panel_item_by_text(item_name)
        self.click(locator)
        time.sleep(0.5)

    # 点击‘文件’按钮
    def click_file(self):
        """点击‘文件’按钮"""
        logger.info("🖱️ [Action-Panel] 点击扩展面板中的【文件】")
        self.click(ChatPanelLocator.BTN_FILE)
        time.sleep(0.5)

    # 点击‘投票’按钮
    def click_vote(self):
        """点击‘投票’按钮"""
        logger.info("🖱️ [Action-Panel] 点击扩展面板中的【投票】")
        self.click(ChatPanelLocator.BTN_VOTE)
        time.sleep(0.5)

    # 点击‘接龙’按钮
    def click_solitaire(self):
        """点击‘接龙’按钮"""
        logger.info("🖱️ [Action-Panel] 点击扩展面板中的【接龙】")
        self.click(ChatPanelLocator.BTN_SOLITAIRE)
        time.sleep(0.5)

    # 点击‘名片’按钮
    def click_card(self):
        """点击‘名片’按钮"""
        logger.info("🖱️ [Action-Panel] 点击扩展面板中的【名片】")
        self.click(ChatPanelLocator.BTN_CARD)
        time.sleep(0.5)

    # 点击‘位置’按钮
    def click_location(self):
        """点击‘位置’按钮"""
        logger.info("🖱️ [Action-Panel] 点击扩展面板中的【位置】")
        self.click(ChatPanelLocator.BTN_LOCATION)
        time.sleep(0.5)

    # 点击‘通话’按钮
    def click_video_call(self):
        """点击‘通话’按钮"""
        logger.info("🖱️ [Action-Panel] 点击扩展面板中的【通话】")
        self.click(ChatPanelLocator.BTN_VIDEO_CALL)

    # 点击弹窗中的‘语音通话’按钮
    def click_pop_voice_call(self):
        """点击底部通话选择弹窗中的【语音通话】按钮"""
        logger.info("📞 [Action-Panel] 点击弹窗中的【语音通话】")
        self.click(ChatPanelLocator.BTN_POP_DIALOG_MORE_ONE2)

    # 点击弹窗中的‘视频通话’按钮
    def click_pop_video_call(self):
        """点击底部通话选择弹窗中的【视频通话】按钮"""
        logger.info("📞 [Action-Panel] 点击弹窗中的【视频通话】")
        self.click(ChatPanelLocator.BTN_POP_DIALOG_MORE_ONE1)

    # 动态发起音视频通话
    def initiate_call_by_type(self, call_type: CallType | str = CallType.VIDEO_CALL):
        """
        点击面板【通话】并基于枚举值匹配通话类型发起呼叫
        :param call_type: CallType 枚举值（CallType.VOICE_CALL / CallType.VIDEO_CALL）或对应的字符串
        """
        self.click_video_call()
        if call_type == CallType.VOICE_CALL:
            self.click_pop_voice_call()
        elif call_type == CallType.VIDEO_CALL:
            self.click_pop_video_call()
        else:
            logger.warning(f"⚠️ [Action-Panel] 未知通话类型枚举值: {call_type}，默认发起视频通话")
            self.click_pop_video_call()

    # 点击‘图片’按钮
    def click_album(self):
        """点击‘图片’（相册）按钮"""
        logger.info("🖱️ [Action-Panel] 点击扩展面板中的【图片】")
        self.click(ChatPanelLocator.BTN_ALBUM)
        time.sleep(0.5)

    # 点击‘拍摄’按钮
    def click_camera(self):
        """点击‘拍摄’（相机）按钮"""
        logger.info("🖱️ [Action-Panel] 点击扩展面板中的【拍摄】")
        self.click(ChatPanelLocator.BTN_CAMERA)
        time.sleep(0.5)



    # =========================================================================================
    # 扩展面板功能区相关
    # =========================================================================================
    # 动态获取并点击扩展面板功能区选项卡
    def click_panel_function_tab(self, tab_name: str):
        """动态获取并点击扩展面板功能区选项卡"""
        logger.info(f"🖱️ [Action-Panel] 尝试点击扩展面板功能区选项卡: 【{tab_name}】")
        if tab_name == "文件":
            pand_elem = self.get_function_panel()
            self.swipe_page_quickly(element=pand_elem, slid_type="left")
            time.sleep(0.5)
            
        locator = ChatPanelLocator.get_panel_item_by_text(tab_name)
        self.click(locator, force_wait=True)
        time.sleep(0.5)
    
