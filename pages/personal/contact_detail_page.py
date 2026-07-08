from typing import Literal
from pages.system.common.common_page import CommonPage
from pages.chat_options.contact.chat_contact_card_page import ChatContactCardPage
from locators.personal.contact_detail_locator import ContactDetailLocator
from core.logger_utils import logger
import time

class ContactDetailPage(CommonPage):
    """好友资料详情页面对象"""

    # 等待加载资料详情页
    def wait_for_detail_page_load(self, timeout: int = 10) -> bool:
        """
        等待资料详情页加载完成
        Args:
            timeout: 超时时间
        Returns:
            bool: True 表示加载成功，False 表示超时
        """
        logger.info(f"⏳ [Wait] 等待资料详情页加载完成，超时时间 {timeout} 秒")
        try:
            self.find_element(ContactDetailLocator.INFO_NICKNAME, timeout=timeout)
            logger.info("✅ [Wait] 资料详情页加载完成")
            return True
        except Exception:
            logger.error(f"❌ [Wait] 资料详情页加载超时")
            return False

    # 获取资料页显示的昵称
    def get_contact_nickname(self) -> str:
        """获取资料页显示的昵称"""
        nickname = self.get_attribute(ContactDetailLocator.INFO_NICKNAME, "text")
        logger.info(f"🧐 [Action] 资料详情页 - 获取昵称: {nickname}")
        return nickname
    
    # 获取资料页显示的 St ID
    def get_st_id(self) -> str:
        """获取资料页显示的 St ID"""
        stId = self.get_attribute(ContactDetailLocator.ST_ID, "text")
        logger.info(f"🧐 [Action] 资料详情页 - 获取 St ID: {stId}")
        return stId

    # 获取资料页显示的所在地
    def get_location(self) -> str:
        """获取资料页显示的所在地"""
        location = self.get_attribute(ContactDetailLocator.LOCATION, "text")
        logger.info(f"🧐 [Action] 资料详情页 - 获取所在地: {location}")
        return location

    # 点击设置备注
    def click_remark(self):
        """点击 [设置备注] 选项"""
        self.click(ContactDetailLocator.SET_REMARK_ITEM)
        logger.info("⚙️ [Action] 资料详情页 - 点击 [设置备注]")

    # 点击推荐给朋友
    def click_recommend(self):
        """点击 [推荐给朋友] 选项"""
        self.click(ContactDetailLocator.RECOMMEND_ITEM)
        logger.info("⚙️ [Action] 资料详情页 - 点击 [推荐给朋友]")

    # 点击动态
    def click_moments(self):
        """点击 [动态] 选项"""
        self.click(ContactDetailLocator.MOMENTS_ITEM)
        logger.info("⚙️ [Action] 资料详情页 - 点击 [动态]")

    # 点击更多设置
    def click_more_settings(self):
        """点击 [更多] 选项"""
        self.click(ContactDetailLocator.MORE_ITEM)
        logger.info("⚙️ [Action] 资料详情页 - 点击 [更多] 设置")
    
    # 点击发送消息
    def click_send_message(self):
        """点击 [发送消息] 按钮，通常会跳转回聊天页"""
        self.click(ContactDetailLocator.SEND_MSG_BTN)
        logger.info("🚀 [Action] 资料详情页 - 点击 [发送消息]")
        # time.sleep(1)

    # 点击音视频通话
    def click_voice_video_call(self):
        """点击 [音视频通话] 按钮"""
        self.click(ContactDetailLocator.CALL_BTN)
        logger.info("📞 [Action] 资料详情页 - 点击 [音视频通话]")

    # 非好友-点击申请加好友
    def click_add_friend(self):
        """点击 [申请加好友] 按钮"""
        self.click(ContactDetailLocator.WHITE_UNFRIEND)
        logger.info("🚀 [Action] 资料详情页 - 点击 [申请加好友]")

    # 非好友-验证当前页面是否存在申请按钮
    def has_add_friend_button(self) -> bool:
        """非好友-验证当前页面是否存在申请按钮"""
        res = self.is_element_exist(ContactDetailLocator.WHITE_UNFRIEND, timeout=1)
        if res:
            logger.info("✅ [Action] 资料详情页 - 申请加好友按钮存在")
        else:
            logger.warning("⚠️ [Action] 资料详情页 - 申请加好友按钮不存在")
        return res
    

    
    # ======================================================================
    # 逻辑相关
    # ======================================================================
    # 验证当前是否在资料详情页
    def verify_is_on_detail_page(self, card_info: dict, msgType: Literal['friend', 'group'] = 'friend') -> bool:
        """验证当前是否在资料详情页"""
        self.wait_for_detail_page_load()

        if msgType == 'friend':
            nickName = self.get_contact_nickname()
            stId = self.get_st_id()
            if card_info['name'] in nickName and card_info['stId'] in stId:
                logger.info("✅ [Action] 资料详情页(好友) - 页面信息匹配成功")
                return True
            else:
                logger.error(f"❌ [Action] 资料详情页(好友) - 页面信息匹配失败，预期: {card_info['name']}, {card_info.get('stId', '')}, 实际: {nickName}, {stId}")
                return False
        elif msgType == 'group':
            group_name = ChatContactCardPage(self.driver).get_group_name()
            if card_info['name'] in group_name:
                logger.info("✅ [Action] 资料详情页(群聊) - 页面信息匹配成功")
                return True
            else:
                logger.error(f"❌ [Action] 资料详情页(群聊) - 页面信息匹配失败，预期名称: {card_info['name']}, 实际: {group_name}")
                return False
        return False
