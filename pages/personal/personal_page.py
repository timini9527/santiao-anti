from common.base_page import BasePage
from core.logger_utils import logger, LogIcon
from locators.personal.personal_locator import PersonalLocator


class PersonalPage(BasePage):
    """个人信息主页面对象"""

    # 个人信息 - 点击清空
    def click_clear(self) -> None:
        """ 点击清空按钮 """
        logger.info(f"{LogIcon.SETUP} 点击清空按钮")
        self.click(PersonalLocator.CLEAR, force_wait=True)

    # 个人信息 - 点击完成
    def click_done(self) -> None:
        """ 点击完成按钮 """
        logger.info(f"{LogIcon.SETUP} 点击完成按钮")
        self.click(PersonalLocator.DONE, force_wait=True)

    # 个人信息 - 点击返回
    def click_back(self) -> None:
        """ 点击返回按钮 """
        logger.info(f"{LogIcon.SETUP} 点击返回按钮")
        self.click(PersonalLocator.ACTION_DETAIL_BACK, force_wait=True)

    # 个人信息 - 点击头像
    def click_avatar(self) -> None:
        """ 点击头像 """
        logger.info(f"{LogIcon.SETUP} 点击头像")
        self.click(PersonalLocator.ME_INFO)

    # 个人信息 - 点击昵称
    def click_nickname(self) -> None:
        """ 点击昵称 """
        logger.info(f"{LogIcon.SETUP} 点击昵称")
        self.click(PersonalLocator.ME_NICKNAME, force_wait=True)

    # 个人信息 - 点击昵称编辑按钮
    def click_nickname_edit_btn(self) -> None:
        """ 点击昵称编辑按钮 """
        logger.info(f"{LogIcon.SETUP} 点击昵称编辑按钮")
        self.click(PersonalLocator.ME_EDIT)

    # 个人信息 - 点击手机号
    def click_phone(self) -> None:
        """ 点击手机号 """
        logger.info(f"{LogIcon.SETUP} 点击手机号")
        self.click(PersonalLocator.ME_PHONE_TEXT)

    # 个人信息 - 点击手机号眼睛
    def click_phone_eyes(self) -> None:
        """ 点击手机号眼睛 点击隐藏或显示按钮 """
        logger.info(f"{LogIcon.SETUP} 点击手机号眼睛")
        self.click(PersonalLocator.ME_PHONE_EYES)

    # 个人信息 - 点击三条ID
    def click_st_id(self) -> None:
        """ 点击三条ID """
        logger.info(f"{LogIcon.SETUP} 点击三条ID")
        self.click(PersonalLocator.ME_ST_ID_TEXT)

    # 个人信息 - 点击我的二维码
    def click_my_qrcode(self) -> None:
        """ 点击我的二维码 """
        logger.info(f"{LogIcon.SETUP} 点击我的二维码")
        self.click(PersonalLocator.ME_QRCODE_TEXT)

    # 个人信息 - 点击二维码图标
    def click_qrcode(self) -> None:
        """ 点击二维码 """
        logger.info(f"{LogIcon.SETUP} 点击二维码")
        self.click(PersonalLocator.ME_QRCODE)

    # 个人信息 - 点击性别
    def click_sex(self) -> None:
        """ 点击性别 """
        logger.info(f"{LogIcon.SETUP} 点击性别")
        self.click(PersonalLocator.ME_SEX_TEXT)

    # 个人信息 - 点击邮箱
    def click_email(self) -> None:
        """ 点击邮箱 """
        logger.info(f"{LogIcon.SETUP} 点击邮箱")
        self.click(PersonalLocator.ME_EMAIL_TEXT)

    # 个人信息 - 点击所在地
    def click_location(self) -> None:
        """ 点击所在地 """
        logger.info(f"{LogIcon.SETUP} 点击所在地")
        self.click(PersonalLocator.ME_LOCATION_TEXT)

    # 个人信息 - 获取详细值 0-手机号，1-三条ID，2-二维码，3-性别，4-邮箱，5-所在地
    def get_detail_value(self, index: int) -> str:
        """ 获取详细值 0-手机号，1-三条ID，2-二维码，3-性别，4-邮箱，5-所在地 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Personal] 获取详细值 [index={index}]")
        try:
            values = self.find_elements(PersonalLocator.DETAIL_VALUE, timeout=1.5)

            if not values:
                logger.error(f"{LogIcon.FIND} 未找到任何详细值元素")
                raise ValueError("未找到详细值元素")

            if index < 0 or index >= len(values):
                logger.error(f"{LogIcon.FIND} 索引 {index} 越界，有效范围：0-{len(values)-1}")
                raise IndexError(f"索引 {index} 越界，可用元素数量：{len(values)}")

            value_element = values[index]
            value = value_element.text if value_element else ""
            value = "" if value == "None" or value is None else value
            logger.info(f"{LogIcon.FIND} 获取详细值 [{index}]: '{value}' (共 {len(values)} 个元素)")
            return value
        except Exception as e:
            logger.error(f"{LogIcon.FIND} 获取详细值失败 [index={index}]: {str(e)}")
            raise

    # 个人信息 - 从任何子页面退回到个人信息主页
    def back_to_personal_info(self, max_retry: int = 5) -> bool:
        """ 从任何子页面（如大图查看页）退回到个人信息主页 """
        logger.info(f"{LogIcon.SETUP} 尝试退回到个人信息主页")
        while max_retry > 0:
            if len(self.find_elements(PersonalLocator.ME_NICKNAME, timeout=2, expect_missing=False)) > 0:
                logger.info(f"{LogIcon.SUCCESS} 已成功处于个人信息主页")
                return True
            logger.info(f"{LogIcon.SETUP} 未检测到个人信息主页特征元素，执行返回")
            self.back()
            max_retry -= 1
        logger.warning(f"{LogIcon.WARN} 超出最大重试次数，未能成功退回到个人信息主页")
        return False
