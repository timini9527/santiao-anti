import re
import time
from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator
from pages.personal.personal_page import PersonalPage
from locators.personal.personal_locator import PersonalLocator
from locators.personal.other_locator import OtherLocator
from core.logger_utils import logger
from pages.common.common_page import CommonPage
from business_helpers.verify_color import VerifyColor


class OtherPage(PersonalPage, CommonPage):
    # MY_AREA = (By.ID, 'me_detail_my_area')
    # MY_AREA_OUT = (By.ID, 'me_detail_my_area_layout')
    # # 获取地区 - 多级区域选择
    # MY_MORE_AREA = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("重庆")')


    def click_nickname(self):
        # 点击昵称
        self.click_nickname_edit_btn()

    def change_nickname(self, nickname):
        # 修改昵称
        self.send_keys(OtherLocator.EDIT_NICKNAME, nickname)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    def get_nickname(self) -> str:
        # 获取昵称
        nickname = self.get_attribute(PersonalLocator.ME_NICKNAME, 'text')
        logger.info(f" 昵称: {nickname}")
        return nickname

    def verify_toase(self, msg: str) -> bool:
        # 空白昵称弹窗提示 和 其他弹窗提示
        toase = self.toast_message()
        return msg in toase

    @staticmethod
    def verify_nickname(pre_nickname, aft_nickname) -> bool:
        # 验证前后修改昵称是否一致
        return True if aft_nickname != pre_nickname else False

    def get_phone_num(self) -> str:
        # 获取手机号
        return self.get_detail_value(0)

    @staticmethod
    def verify_phone_num_show(phone: str):
        # 验证手机号显示正常
        # 必须全部是数字，不能有任何 * 或其他非数字字符
        # ^\d+$ 表示从头到尾都必须是数字
        return bool(re.match(r"^\d+$", phone))

    def get_st_id(self) -> str:
        # 获取三条ID
        return self.get_detail_value(1)

    def change_st_id(self, new_id: str):
        # 修改三条ID
        self.click(OtherLocator.CHANGE_ST_ID)
        self.send_keys(OtherLocator.EDIT_ST_ID, new_id)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    def get_qrcode_nickname(self) -> str:
        # 获取二维码昵称
        return self.get_attribute(OtherLocator.ME_QRCODE_NAME, 'text')

    def get_qrcode_sex(self) -> str:
        # 获取二维码性别 通过验证进行判断
        elem = self.find_element(OtherLocator.ME_QRCODE_SEX, condition="visibility", timeout=5)
        sex = VerifyColor.verify_sex(elem)
        return  sex

    def click_save_qrcode(self):
        # 二维码
        self.click(OtherLocator.ME_QRCODE_SAVE)

    def get_qrcode_toase(self):
        # 二维码保存成功弹窗
        return self.get_attribute(OtherLocator.TOASE_SAVE_QRCODE, 'text')

    def find_all_qrcode_attr(self):
        # 二维码页面获取所有元素是否存在
        elements = [
            self.find_element(CommonLocator.TOP_TV_TITLE),
            self.find_element(OtherLocator.ME_QRCODE),
            self.find_element(OtherLocator.ME_QRCODE_AVATAR),
            self.find_element(OtherLocator.ME_QRCODE_NAME),
            self.find_element(OtherLocator.ME_QRCODE_SEX),
            self.find_element(OtherLocator.ME_QRCODE_SAVE)
        ]
        # 检查所有元素是否都存在（不为None）
        return all(element is not None for element in elements)

    def get_sex(self) -> str:
        # 获取 性别
        return self.get_detail_value(2)

    def click_sex_b(self):
        # 性别男
        self.click(OtherLocator.MALE, force_wait= True)

    def click_sex_g(self):
        # 性别女
        self.click(OtherLocator.FEMALE, force_wait= True)

    def click_sex_c(self):
        # 性别取消
        self.click_cancel_button()

    def is_email_page(self) -> bool:
        # 判断是否还在邮箱页面
        title = self.get_top_middle_title()
        if title == "设置邮箱" and title != "":
            return True
        return False

    def get_email(self) -> str:
        # 获取邮箱
        return self.get_detail_value(3)

    def change_email(self, email):
        # 修改邮箱
        self.send_keys(OtherLocator.EDIT_EMAIL, email)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    def select_area(self, area_name, max_retry: int = 10):
        """ 点击列表中的某一项 """
        # 选择地区
        uiautomator = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{area_name}")')
        ele = self.find_element(uiautomator)
        if ele is None:
            # 设置最大滑动次数避免无限循环
            while max_retry > 0:
                self.swipe_page(slid_type='up', duration=500)
                are = self.find_element(uiautomator)
                if are is not None:
                    are.click()
                    logger.info(f"在列表已找到地区： {area_name}")
                    break
                max_retry -= 1
            else:
                # 如果达到最大滑动次数仍未找到元素，抛出异常
                logger.error(f"在列表中未找到地区: {area_name}，已滑到最底部")
                raise Exception(f"在列表中未找到地区: {area_name}，已滑动 {max_retry} 次")
        else: ele.click()
        time.sleep(0.5)  # 等待转场

    def get_area_name(self):
        return self.get_detail_value(4)
