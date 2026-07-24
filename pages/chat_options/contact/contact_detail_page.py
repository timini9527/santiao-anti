from typing import Literal
from pages.common.common_page import CommonPage
from pages.chat_options.contact.chat_contact_card_page import ChatContactCardPage
from locators.chat_options.contact.contact_detail_locator import ContactDetailLocator
from utils.cv_recognition.ocr_utils import OcrUtils
from core.logger_utils import logger
import time

class ContactDetailPage(CommonPage):
    """好友资料详情页面对象"""

    # 资料页 - 等待加载资料详情页
    def wait_for_detail_page_load(self, timeout: int = 10) -> bool:
        """ 资料页 - 等待资料详情页加载完成 """
        try:
            is_exist = self.is_element_exist(ContactDetailLocator.ST_ID, timeout=timeout)
            if is_exist:
                logger.info("✅ [Wait - ContactDetail] 资料详情页加载完成")
                return True
            else:
                logger.error(f"❌ [Wait - ContactDetail] 资料详情页加载超时")
                return False
        except Exception:
            logger.error(f"❌ [Wait - ContactDetail] 资料详情页加载超时")
            return False

    # 资料页 - 点击更多图标
    def click_iv_right(self):
        """ 资料页 - 点击更多图标 """
        self.click(ContactDetailLocator.IV_RIGHT)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击更多图标")

    # 资料页 - 点击返回按钮
    def click_iv_back(self):
        """ 资料页 - 点击返回按钮 """
        self.click(ContactDetailLocator.IV_BACK)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击返回按钮")

    # 资料页 - 获取资料页原始昵称
    def get_raw_nickname(self) -> str:
        """ 资料页 - 获取资料页原始昵称 """
        raw_nickname = self.get_attribute(ContactDetailLocator.TV_NAME_XPATH, "text")
        logger.info(f"🧐 [Action - ContactDetail] 资料详情页 - 获取原始昵称: {raw_nickname}")
        return raw_nickname

    # 资料页 - 获取资料页显示的昵称
    def get_contact_nickname(self, raise_exception: bool = True) -> str:
        """ 资料页 - 获取资料页显示的昵称 """
        nickname = self.get_attribute(ContactDetailLocator.INFO_NICKNAME, "text", raise_exception=raise_exception)
        logger.info(f"🧐 [Action - ContactDetail] 资料详情页 - 获取昵称: {nickname}")
        return nickname
    
    # 资料页 - 获取资料页显示的 St ID
    def get_st_id(self) -> str:
        """ 资料页 - 获取资料页显示的 St ID """
        stId = self.get_attribute(ContactDetailLocator.ST_ID, "text")
        logger.info(f"🧐 [Action - ContactDetail] 资料详情页 - 获取 St ID: {stId}")
        return stId

    # 资料页 - 获取资料页显示的所在地
    def get_location(self) -> str:
        """ 获取资料页显示的所在地 """
        location = self.get_attribute(ContactDetailLocator.LOCATION, "text")
        logger.info(f"🧐 [Action - ContactDetail] 资料详情页 - 获取所在地: {location}")
        return location

    # 资料页 - 点击设置备注
    def click_remark(self):
        """ 资料页 - 点击 [设置备注] 选项 """
        self.click(ContactDetailLocator.SET_REMARK_ITEM)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击 [设置备注]")

    # 资料页 - 点击推荐给朋友
    def click_recommend(self):
        """ 资料页 - 点击 [推荐给朋友] 选项 """
        self.click(ContactDetailLocator.RECOMMEND_ITEM)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击 [推荐给朋友]")

    # 资料页 - 点击动态
    def click_moments(self):
        """ 资料页 - 点击 [动态] 选项 """
        self.click(ContactDetailLocator.MOMENTS_ITEM)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击 [动态]")

    # 资料页 - 点击更多设置
    def click_more_settings(self):
        """ 资料页 - 点击 [更多] 选项 """
        self.click(ContactDetailLocator.MORE_ITEM)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击 [更多] 设置")
    
    # 资料页 - 点击发送消息
    def click_send_message(self):
        """ 资料页 - 点击 [发送消息] 按钮，通常会跳转回聊天页 """
        self.click(ContactDetailLocator.SEND_MSG_BTN)
        logger.info("🚀 [Action - ContactDetail] 资料详情页 - 点击 [发送消息]")
        # time.sleep(1)

    # 资料页 - 点击音视频通话
    def click_voice_video_call(self):
        """ 资料页 - 点击 [音视频通话] 按钮 """
        self.click(ContactDetailLocator.CALL_BTN)
        logger.info("📞 [Action - ContactDetail] 资料详情页 - 点击 [音视频通话]")

    # 非好友-点击申请加好友
    def click_add_friend(self):
        """ 非好友-点击 [申请加好友] 按钮 """
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

    # 好友资料 - 确认操作
    def confirm_two_btn_comment(self):
        """ 好友资料 - 确认操作 """
        self.click(ContactDetailLocator.CONFIRM_TWO_BTN)
        logger.info("⚙️ [Action - ContactDetail] 好友资料 - 确认操作")
    
    # 取消操作
    def cancel_two_btn_comment(self):
        """ 好友资料 - 取消操作 """
        if self.is_element_exist(ContactDetailLocator.CANCEL_TWO_BTN, timeout=1, expect_missing=True):
            self.click(ContactDetailLocator.CANCEL_TWO_BTN)
            logger.info("⚙️ [Action - ContactDetail] 好友资料 - 取消操作")
        else:
            logger.info("⚙️ [Action - ContactDetail] 好友资料 - 无需取消操作")

    # 好友资料 - 点击右上角更多并删除好友
    def delete_contact(self) -> bool:
        """ 好友资料 - 在好友详情页中，点击更多并删除好友 """
        try:
            self.click_iv_right()
            self.click_unfriend_tv_unfriend()
            self.confirm_two_btn_comment()
            logger.info("⚙️ [Action - ContactDetail] 好友资料 - 点击右上角更多并删除好友成功")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - ContactDetail] 好友资料 - 点击右上角更多并删除好友失败: {e}")
            return False

    # 好友资料 - 获取好友昵称并格式化
    def get_formatted_friend_name(self) -> str:
        """ 好友资料 - 获取好友详情页的显示名称并格式化 """
        raw_name = self.get_raw_nickname()
        if not raw_name:
            logger.error("❌ [Action - ContactDetail] 未获取到好友昵称")
            return ""
        formatted_name = self.clean_ui_text(raw_name)
        if not formatted_name:
            logger.error("❌ [Action - ContactDetail] 格式化后的好友昵称为空")
            return ""
        logger.info(f"🧐 [Action - ContactDetail] 获取到格式化后的好友昵称: {formatted_name}")
        return formatted_name
        
    # 好友资料 - 点击好友资料标题行
    def click_friend_detail_title_remark(self):
        """ 好友资料 - 点击好友资料标题行 """
        self.click(ContactDetailLocator.ADD_FRIEND_TITLE_REMARK)
        logger.info("⚙️ [Action - ContactDetail] 好友资料 - 点击好友资料标题行")

    # 好友资料 - 设置好友备注名
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

    # ==============================================================
    # 资料卡电话与呼叫弹窗功能
    # ==============================================================
    # 好友详情 - 点击 全部 获取号码
    def click_all_phone_numbers(self):
        """ 好友详情 - 点击 全部 获取号码 """
        result = OcrUtils(self.driver).click_text_by_ocr("全部", exact_match=False)
        if result:
            logger.info("⚙️ [Action - ContactDetail] 好友详情页 - 点击 全部 获取号码成功")
        else:
            logger.error("❌ [Action - ContactDetail] 好友详情页 - 点击 全部 获取号码失败")
        return result
    
    # 好友详情 - 等待电话资料卡加载出来
    def wait_for_phone_sheet_load(self, timeout=10):
        """ 好友详情 - 等待电话资料卡加载出来 """
        result = self.is_element_exist(ContactDetailLocator.DESIGN_BOTTOM_SHEET, timeout=timeout)
        if result:
            logger.info("⚙️ [Action - ContactDetail] 好友详情页 - 等待电话资料卡加载成功")
        else:
            logger.error("❌ [Action - ContactDetail] 好友详情页 - 等待电话资料卡加载失败")
        return result

    # 好友详情 - 点击资料卡电话行
    def click_row_profile_phone(self):
        """ 好友详情 - 点击资料卡电话行 """
        self.click(ContactDetailLocator.ROW_PROFILE_PHONE)
        logger.info("⚙️ [Action - ContactDetail] 好友详情页 - 点击资料卡电话行")
    
    # 好友详情 - 资料卡电话行是否存在
    def is_row_profile_phone(self) -> bool:
        """ 好友详情 - 资料卡电话行是否存在 """
        is_exist = self.is_element_exist(ContactDetailLocator.ROW_PROFILE_PHONE, timeout=1)
        if is_exist:
            logger.info("⚙️ [Action - ContactDetail] 好友详情页 - 资料卡电话行存在")
        else:
            logger.info("⚙️ [Action - ContactDetail] 好友详情页 - 资料卡电话行不存在")
        return is_exist

    # 好友详情 - 获取资料卡电话标签
    def get_profile_phone_label(self) -> str:
        """ 好友详情 - 获取资料卡电话标签 """
        label = self.get_attribute(ContactDetailLocator.TV_PROFILE_PHONE_LABEL, "text")
        logger.info(f"🧐 [Action - ContactDetail] 好友详情页 - 获取资料卡电话标签: {label}")
        return label

    # 好友详情 - 获取资料卡电话号码文本
    def get_profile_phone_value(self) -> list:
        """ 好友详情 - 获取资料卡电话号码文本 """
        val = self.get_attribute(ContactDetailLocator.TV_PROFILE_PHONE_VALUE, "text")
        val_list = val.split("、")
        logger.info(f"🧐 [Action - ContactDetail] 好友详情页 - 获取资料卡电话号码: {val_list}")
        return val_list

    # 电话资料卡 - 点击关闭按钮
    def click_phone_sheet_close(self):
        """ 电话资料卡 - 点击关闭按钮 """
        self.click(ContactDetailLocator.IV_CLOSE)
        logger.info("⚙️ [Action - ContactDetail] 电话资料卡弹窗 - 点击关闭按钮")

    # 电话资料卡 - 获取电话列表中的全部号码
    def get_sheet_phone_list(self) -> list:
        """ 电话资料卡 - 获取电话列表中的全部号码 """
        phones = []
        elems = self.find_elements(ContactDetailLocator.TV_PHONE)
        for el in elems:
            if el.text:
                phones.append(el.text)
        logger.info(f"🧐 [Action - ContactDetail] 电话资料卡弹窗 - 当前电话列表: {phones}")
        return phones

    # 电话资料卡 - 点击指定索引的复制按钮
    def click_sheet_copy(self, index: int = 0):
        """ 电话资料卡 - 点击指定索引的复制按钮 """
        icons = self.find_elements(ContactDetailLocator.IV_COPY)
        if index < len(icons):
            icons[index].click()
            logger.info(f"⚙️ [Action - ContactDetail] 电话资料卡弹窗 - 点击第 {index} 个复制按钮")

    # 电话资料卡 - 点击指定索引的拨号按钮
    def click_sheet_call(self, index: int = 0):
        """ 电话资料卡 - 点击指定索引的拨号按钮 """
        icons = self.find_elements(ContactDetailLocator.IV_CALL)
        if index < len(icons):
            icons[index].click()
            logger.info(f"⚙️ [Action - ContactDetail] 电话资料卡弹窗 - 点击第 {index} 个拨号按钮")

    # 呼叫弹窗1 - 获取显示的电话号码
    def get_call_popup1_number(self) -> str:
        """ 呼叫弹窗1 - 获取显示的电话号码 """
        num = self.get_attribute(ContactDetailLocator.TV_NUMBER, "text")
        logger.info(f"🧐 [Action - ContactDetail] 呼叫弹窗1 - 获取号码: {num}")
        return num

    # 呼叫弹窗1 - 点击拨号
    def click_call_popup1_call(self):
        """ 呼叫弹窗1 - 点击拨号 """
        self.click(ContactDetailLocator.TV_CALL)
        logger.info("⚙️ [Action - ContactDetail] 呼叫弹窗1 - 点击拨号")

    # 呼叫弹窗1 - 点击复制
    def click_call_popup1_copy(self):
        """ 呼叫弹窗1 - 点击复制 """
        self.click(ContactDetailLocator.TV_COPY)
        logger.info("⚙️ [Action - ContactDetail] 呼叫弹窗1 - 点击复制")

    # 呼叫弹窗1 - 点击取消
    def click_call_popup1_cancel(self):
        """ 呼叫弹窗1 - 点击取消 """
        self.click(ContactDetailLocator.TV_CANCEL)
        logger.info("⚙️ [Action - ContactDetail] 呼叫弹窗1 - 点击取消")

    # 呼叫弹窗2 - 点击呼叫
    def click_call_popup2_call(self):
        """ 呼叫弹窗2 - 点击呼叫 """
        self.click(ContactDetailLocator.CALL_TEXT)
        logger.info("⚙️ [Action - ContactDetail] 呼叫弹窗2 - 点击呼叫")

    # 呼叫弹窗2 - 点击取消
    def click_call_popup2_cancel(self):
        """ 呼叫弹窗2 - 点击取消 """
        self.click(ContactDetailLocator.CANCEL_TEXT)
        logger.info("⚙️ [Action - ContactDetail] 呼叫弹窗2 - 点击取消")


