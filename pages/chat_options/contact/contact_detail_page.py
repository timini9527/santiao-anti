from typing import Literal
from pages.common.common_page import CommonPage
from pages.chat_options.contact.chat_contact_card_page import ChatContactCardPage
from locators.chat_options.contact.contact_detail_locator import ContactDetailLocator
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
        try:
            self.find_element(ContactDetailLocator.ST_ID, timeout=timeout)
            logger.info("✅ [Wait - ContactDetail] 资料详情页加载完成")
            return True
        except Exception:
            logger.error(f"❌ [Wait - ContactDetail] 资料详情页加载超时")
            return False

    # 点击更多图标
    def click_iv_right(self):
        """点击更多图标"""
        self.click(ContactDetailLocator.IV_RIGHT)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击更多图标")

    # 点击返回按钮
    def click_iv_back(self):
        """点击返回按钮"""
        self.click(ContactDetailLocator.IV_BACK)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击返回按钮")

    # 获取资料页显示的昵称
    def get_contact_nickname(self) -> str:
        """获取资料页显示的昵称"""
        nickname = self.get_attribute(ContactDetailLocator.INFO_NICKNAME, "text")
        logger.info(f"🧐 [Action - ContactDetail] 资料详情页 - 获取昵称: {nickname}")
        return nickname
    
    # 获取资料页显示的 St ID
    def get_st_id(self) -> str:
        """获取资料页显示的 St ID"""
        stId = self.get_attribute(ContactDetailLocator.ST_ID, "text")
        logger.info(f"🧐 [Action - ContactDetail] 资料详情页 - 获取 St ID: {stId}")
        return stId

    # 获取资料页显示的所在地
    def get_location(self) -> str:
        """获取资料页显示的所在地"""
        location = self.get_attribute(ContactDetailLocator.LOCATION, "text")
        logger.info(f"🧐 [Action - ContactDetail] 资料详情页 - 获取所在地: {location}")
        return location

    # 点击设置备注
    def click_remark(self):
        """点击 [设置备注] 选项"""
        self.click(ContactDetailLocator.SET_REMARK_ITEM)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击 [设置备注]")

    # 点击推荐给朋友
    def click_recommend(self):
        """点击 [推荐给朋友] 选项"""
        self.click(ContactDetailLocator.RECOMMEND_ITEM)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击 [推荐给朋友]")

    # 点击动态
    def click_moments(self):
        """点击 [动态] 选项"""
        self.click(ContactDetailLocator.MOMENTS_ITEM)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击 [动态]")

    # 点击更多设置
    def click_more_settings(self):
        """点击 [更多] 选项"""
        self.click(ContactDetailLocator.MORE_ITEM)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击 [更多] 设置")
    
    # 点击发送消息
    def click_send_message(self):
        """点击 [发送消息] 按钮，通常会跳转回聊天页"""
        self.click(ContactDetailLocator.SEND_MSG_BTN)
        logger.info("🚀 [Action - ContactDetail] 资料详情页 - 点击 [发送消息]")
        # time.sleep(1)

    # 点击音视频通话
    def click_voice_video_call(self):
        """点击 [音视频通话] 按钮"""
        self.click(ContactDetailLocator.CALL_BTN)
        logger.info("📞 [Action - ContactDetail] 资料详情页 - 点击 [音视频通话]")

    # 非好友-点击申请加好友
    def click_add_friend(self):
        """点击 [申请加好友] 按钮"""
        self.click(ContactDetailLocator.WHITE_UNFRIEND)
        logger.info("🚀 [Action - ContactDetail] 资料详情页 - 点击 [申请加好友]")

    # 非好友-验证当前页面是否存在申请按钮
    def has_add_friend_button(self) -> bool:
        """非好友-验证当前页面是否存在申请按钮"""
        res = self.is_element_exist(ContactDetailLocator.WHITE_UNFRIEND, timeout=1)
        if res:
            logger.info("✅ [Action - ContactDetail] 资料详情页 - 申请加好友按钮存在")
        else:
            logger.warning("⚠️ [Action - ContactDetail] 资料详情页 - 申请加好友按钮不存在")
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
                logger.info("✅ [Action - ContactDetail] 资料详情页(好友) - 页面信息匹配成功")
                return True
            else:
                logger.error(f"❌ [Action - ContactDetail] 资料详情页(好友) - 页面信息匹配失败，预期: {card_info['name']}, {card_info.get('stId', '')}, 实际: {nickName}, {stId}")
                return False
        elif msgType == 'group':
            group_name = ChatContactCardPage(self.driver).get_group_name()
            if card_info['name'] in group_name:
                logger.info("✅ [Action - ContactDetail] 资料详情页(群聊) - 页面信息匹配成功")
                return True
            else:
                logger.error(f"❌ [Action - ContactDetail] 资料详情页(群聊) - 页面信息匹配失败，预期名称: {card_info['name']}, 实际: {group_name}")
                return False
        return False

    # =================================================================================
    # 他人/非好友资料卡相关业务方法
    # =================================================================================
    # 添加好友详情 - 获取添加好友详情页的昵称
    def get_add_friend_name(self) -> str:
        """ 获取添加好友详情页的昵称 """
        name = self.get_attribute(ContactDetailLocator.ADD_FRIEND_TV_NAME_XPATH, "text")
        if name:
            logger.info(f" 🧐 [Action - ContactDetail] 获取添加好友页面昵称: {name}")
        else:
            logger.error(f" ❌ [Action - ContactDetail] 未找到添加好友页面昵称")
        return name

    # 添加好友详情 - 获取添加好友详情页的所在地
    def get_add_friend_location(self) -> str:
        """ 添加好友详情 - 获取添加好友详情页的所在地 """
        location = self.get_attribute(ContactDetailLocator.ADD_FRIEND_TV_LOCATION, "text")
        if location:
            logger.info(f" 🧐 [Action - ContactDetail] 获取添加好友页面所在地: {location}")
        else:
            logger.error(f" ❌ [Action - ContactDetail] 未找到添加好友页面所在地")
        return location

    # 添加好友详情 - 点击好友动态
    def click_add_friend_moments(self):
        """ 添加好友详情 - 点击好友动态 """
        self.click(ContactDetailLocator.ADD_FRIEND_TITLE_MOMENTS)
        logger.info("⚙️ [Action - ContactDetail] 点击添加好友详情页的好友动态")

    # 添加好友详情 - 获取资料卡标题
    def get_add_friend_profile_card_title(self) -> str:
        """ 添加好友详情 - 获取资料卡标题 """
        title = self.get_attribute(ContactDetailLocator.ADD_FRIEND_TV_PROFILE_CARD_TITLE, "text")
        if title:
            logger.info(f" 🧐 [Action - ContactDetail] 获取添加好友页面资料卡标题: {title}")
        else:
            logger.error(f" ❌ [Action - ContactDetail] 未找到添加好友页面资料卡标题")
        return title

    # 添加好友详情 - 获取资料卡描述
    def get_add_friend_profile_card_desc(self) -> str:
        """ 添加好友详情 - 获取资料卡描述 """
        desc = self.get_attribute(ContactDetailLocator.ADD_FRIEND_TV_PROFILE_CARD_DESC, "text")
        if desc:
            logger.info(f" 🧐 [Action - ContactDetail] 获取添加好友页面资料卡描述: {desc}")
        else:
            logger.error(f" ❌ [Action - ContactDetail] 未找到添加好友页面资料卡描述")
        return desc

    # 添加好友详情 - 检查是否显示为未添加好友
    def is_add_friend_unfriend_visible(self) -> bool:
        """ 添加好友详情 - 检查是否显示为未添加好友 """
        res = self.is_element_exist(ContactDetailLocator.ADD_FRIEND_TV_ADD_FRIEND_XPATH)
        if res:
            logger.info(f" 🧐 [Action - ContactDetail] 添加好友页面 - 显示为未添加好友")
        else:
            logger.error(f" ❌ [Action - ContactDetail] 添加好友页面 - 未显示未添加好友")
        return res

    # 添加好友详情 - 点击添加好友按钮
    def click_add_friend_button(self):
        """ 添加好友详情 - 点击添加好友按钮 """
        if not self.is_add_friend_unfriend_visible():
            logger.error(f" ❌ [Action - ContactDetail] 添加好友页面 - 未显示未添加好友")
            return
        self.click(ContactDetailLocator.ADD_FRIEND_TV_ADD_FRIEND_XPATH)
        logger.info("⚙️ [Action - ContactDetail] 添加好友详情页 - 点击添加好友按钮")

    
    # ==============================================================
    # 好友详情页面
    # ==============================================================
    # 好友详情页面 - 点击解除好友关系
    def click_unfriend_tv_unfriend(self):
        """好友详情页面 - 点击解除好友关系"""
        self.click(ContactDetailLocator.UNFRIEND_TV_UNFRIEND)
        logger.info("⚙️ [Action - ContactDetail] 好友详情页 - 点击解除好友关系")

    # 确认删除
    def confirm_delete_comment(self):
        """确认删除"""
        self.click(ContactDetailLocator.CONFIRM_TWO_BTN)
        logger.info("⚙️ [Action - ContactDetail] 确认删除")

    # 点击右上角更多并删除好友
    def delete_contact(self) -> bool:
        """ 在好友详情页中，点击更多并删除该好友 """
        try:
            self.click_iv_right()
            self.click_unfriend_tv_unfriend()
            self.confirm_delete_comment()
            logger.info("⚙️ [Action - ContactDetail] 点击右上角更多并删除好友成功")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - ContactDetail] 删除好友失败: {e}")
            return False

    # 设置好友备注名
    def set_contact_remark(self, remark_name: str) -> bool:
        """
        在好友详情页中，设置好友备注名
        Returns:
            bool: 是否操作成功
        """
        from appium.webdriver.common.appiumby import AppiumBy
        try:
            logger.info(f"⚙️ [Action - ContactDetail] 准备设置备注为: {remark_name}")
            # 1. 点击设置备注项
            self.click_remark()
            time.sleep(1)
            
            # 2. 定位备注名输入框输入内容
            remark_input_locator = (
                AppiumBy.XPATH,
                '//android.widget.EditText'
            )
            self.send_keys(remark_input_locator, remark_name)
            
            # 3. 点击完成/保存按钮
            save_btn_locator = (
                AppiumBy.XPATH,
                '//*[@text="完成" or @text="保存" or @text="确定"]'
            )
            self.click(save_btn_locator)
            logger.info("✅ [Action - ContactDetail] 设置好友备注成功")
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"❌ [Action - ContactDetail] 设置好友备注失败: {e}")
            return False

