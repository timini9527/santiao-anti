from common.base_page import BasePage

from core.logger_utils import logger
from locators.personal.personal_locator import PersonalLocator

class PersonalPage(BasePage):

    # 点击编辑输入框并输入数据
    # def click_edit(self, text: str):
    #     self.send_keys(PersonalLocator.EDIT, text)
    #     self.click(PersonalLocator.EDIT, force_wait=True)

    # 点击清空
    def click_clear(self):
        logger.info(" 点击清空按钮 ")
        self.click(PersonalLocator.CLEAR, force_wait=True)

    # 点击完成
    def click_done(self):
        logger.info(" 点击完成按钮 ")
        self.click(PersonalLocator.DONE, force_wait=True)

    # 点击返回
    def click_back(self):
        logger.info(" 点击返回按钮 ")
        self.click(PersonalLocator.BACK, force_wait=True)

    # 点击头像
    def click_avatar(self):
        logger.info(" 点击头像 ")
        self.click(PersonalLocator.ME_INFO)

    # 点击昵称编辑按钮
    def click_nickname_edit_btn(self):
        logger.info(" 点击昵称编辑按钮 ")
        self.click(PersonalLocator.ME_EDIT)

    # 点击手机号
    def click_phone(self):
        logger.info(" 点击手机号 ")
        self.click(PersonalLocator.ME_PHONE_TEXT)

    # 点击手机号眼睛
    def click_phone_eyes(self):
        """点击手机号眼睛  点击隐藏或显示按钮"""
        logger.info(" 点击手机号眼睛 ")
        self.click(PersonalLocator.ME_PHONE_EYES)

    # 点击三条ID
    def click_st_id(self):
        logger.info(" 点击三条ID ")
        self.click(PersonalLocator.ME_ST_ID_TEXT)

    # 点击我的二维码
    def click_my_qrcode(self):
        logger.info(" 点击我的二维码 ")
        self.click(PersonalLocator.ME_QRCODE_TEXT)

    # 点击二维码
    def click_qrcode(self):
        logger.info(" 点击二维码 ")
        self.click(PersonalLocator.ME_QRCODE)

    # 点击性别
    def click_sex(self):
        logger.info(" 点击性别 ")
        self.click(PersonalLocator.ME_SEX_TEXT)

    # 点击邮箱
    def click_email(self):
        logger.info(" 点击邮箱 ")
        self.click(PersonalLocator.ME_EMAIL_TEXT)

    # 点击所在地
    def click_location(self):
        logger.info(" 点击所在地 ")
        self.click(PersonalLocator.ME_LOCATION_TEXT)

    # 获取详细值 0-手机号，1-三条ID，2-性别，3-邮箱，4-所在地
    def get_detail_value(self, index: int) -> str:
        try:
            values = self.find_elements(PersonalLocator.DETAIL_VALUE)

            if not values:
                logger.error(f"[Assert] 未找到任何详细值元素")
                raise ValueError("未找到详细值元素")

            if index < 0 or index >= len(values):
                logger.error(f"[Assert] 索引 {index} 越界，有效范围：0-{len(values)-1}")
                raise IndexError(f"索引 {index} 越界，可用元素数量：{len(values)}")

            value_element = values[index]
            value = value_element.text if value_element else ""
            value = "" if value == "None" or value is None else value
            logger.info(f"[Assert] 获取详细值 [{index}]: '{value}' (共 {len(values)} 个元素)")
            return value
        except Exception as e:
            logger.error(f"[Assert] 获取详细值失败 [index={index}]: {str(e)}")
            raise

    def back_to_personal_info(self, max_retry: int = 5) -> bool:
        """ 从任何子页面（如大图查看页）退回到个人信息主页"""
        while max_retry > 0:
            if len(self.find_elements(PersonalLocator.ME_NICKNAME, timeout=2)) > 0:
                return True
            self.back()
            max_retry -= 1
            logger.info(f"[Action] 获取元素 {PersonalLocator.ME_NICKNAME}  没有找到，返回")
        return False

    # =================================================================================
    # 添加好友详情卡片相关业务动作
    # =================================================================================
    # 添加好友详情 - 获取添加好友详情页的昵称
    def get_add_friend_name(self) -> str:
        """ 添加好友详情 - 获取添加好友详情页的昵称 """
        name = self.get_attribute(PersonalLocator.ADD_FRIEND_TV_NAME_XPATH, "text")
        if name:
            logger.info(f" 🧐 [Action - Personal] 获取添加好友页面昵称: {name}")
        else:
            logger.error(f" ❌ [Action - Personal] 未找到添加好友页面昵称")
        return name

    # 添加好友详情 - 获取添加好友详情页的所在地
    def get_add_friend_location(self) -> str:
        """ 添加好友详情 - 获取添加好友详情页的所在地 """
        location = self.get_attribute(PersonalLocator.ADD_FRIEND_TV_LOCATION, "text")
        if location:
            logger.info(f" 🧐 [Action - Personal] 获取添加好友页面所在地: {location}")
        else:
            logger.error(f" ❌ [Action - Personal] 未找到添加好友页面所在地")
        return location

    # 添加好友详情 - 点击好友动态
    def click_add_friend_moments(self):
        """ 添加好友详情 - 点击好友动态 """
        self.click(PersonalLocator.ADD_FRIEND_TITLE_MOMENTS)
        logger.info("⚙️ [Action - Personal] 点击添加好友详情页的好友动态")

    # 添加好友详情 - 获取资料卡标题
    def get_add_friend_profile_card_title(self) -> str:
        """ 添加好友详情 - 获取资料卡标题 """
        title = self.get_attribute(PersonalLocator.ADD_FRIEND_TV_PROFILE_CARD_TITLE, "text")
        if title:
            logger.info(f" 🧐 [Action - Personal] 获取添加好友页面资料卡标题: {title}")
        else:
            logger.error(f" ❌ [Action - Personal] 未找到添加好友页面资料卡标题")
        return title

    # 添加好友详情 - 获取资料卡描述
    def get_add_friend_profile_card_desc(self) -> str:
        """ 添加好友详情 - 获取资料卡描述 """
        desc = self.get_attribute(PersonalLocator.ADD_FRIEND_TV_PROFILE_CARD_DESC, "text")
        if desc:
            logger.info(f" 🧐 [Action - Personal] 获取添加好友页面资料卡描述: {desc}")
        else:
            logger.error(f" ❌ [Action - Personal] 未找到添加好友页面资料卡描述")
        return desc

    # 添加好友详情 - 共同好友页面 - 检查是否显示为未添加好友
    def is_add_friend_unfriend_visible(self) -> bool:
        """ 添加好友详情 - 共同好友页面 - 检查是否显示为未添加好友 """
        res = self.is_element_exist(PersonalLocator.ADD_FRIEND_TV_ADD_FRIEND_XPATH)
        if res:
            logger.info(f" 🧐 [Action - Personal] 添加好友页面 - 显示为未添加好友")
        else:
            logger.error(f" ❌ [Action - Personal] 添加好友页面 - 未显示未添加好友")
        return res

    # 添加好友详情 - 共同好友页面 - 点击添加好友按钮
    def click_add_friend_button(self):
        """ 添加好友详情 - 共同好友页面 - 点击添加好友按钮 """
        if not self.is_add_friend_unfriend_visible():
            logger.error(f" ❌ [Action - Personal] 添加好友页面 - 未显示未添加好友")
            return
        self.click(PersonalLocator.ADD_FRIEND_TV_ADD_FRIEND_XPATH)
        logger.info("⚙️ [Action - Personal] 点击添加好友按钮")

