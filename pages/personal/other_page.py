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


    # 点击昵称
    def click_nickname(self) -> None:
        """点击昵称"""
        # 点击昵称
        logger.info("[Action] 点击昵称编辑按钮")
        self.click_nickname_edit_btn()

    # 修改昵称
    def change_nickname(self, nickname: str) -> None:
        """修改昵称"""
        # 修改昵称
        logger.info(f"[Action] 修改昵称为: {nickname}")
        self.send_keys(OtherLocator.EDIT_NICKNAME, nickname)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    # 获取昵称
    def get_nickname(self) -> str:
        """获取昵称"""
        # 获取昵称
        logger.info("[Action] 获取个人资料昵称")
        nickname = self.get_attribute(PersonalLocator.ME_NICKNAME, 'text')
        logger.info(f"[Info] 昵称: {nickname}")
        return nickname

    # 空白昵称弹窗提示 和 其他弹窗提示
    def verify_toase(self, msg: str) -> bool:
        """空白昵称弹窗提示 和 其他弹窗提示"""
        # 空白昵称弹窗提示 和 其他弹窗提示
        logger.info(f"[Action] 验证弹窗 Toast 提示: {msg}")
        return self.get_toast(expected_toast=msg)

    # 验证前后修改昵称是否一致
    @staticmethod
    def verify_nickname(pre_nickname: str, aft_nickname: str) -> bool:
        """验证前后修改昵称是否一致"""
        # 验证前后修改昵称是否一致
        logger.info(f"[Action] 验证前后修改昵称: 修改前={pre_nickname}, 修改后={aft_nickname}")
        return True if aft_nickname != pre_nickname else False

    # 获取手机号
    def get_phone_num(self) -> str:
        """获取手机号"""
        # 获取手机号
        logger.info("[Action] 获取手机号")
        return self.get_detail_value(0)

    # 验证手机号显示正常
    @staticmethod
    def verify_phone_num_show(phone: str) -> bool:
        """验证手机号显示正常"""
        # 验证手机号显示正常
        # 必须全部是数字，不能有任何 * 或其他非数字字符
        # ^\d+$ 表示从头到尾都必须是数字
        logger.info(f"[Action] 验证手机号显示格式: {phone}")
        return bool(re.match(r"^\d+$", phone))

    # 获取三条ID
    def get_st_id(self) -> str:
        """获取三条ID"""
        # 获取三条ID
        logger.info("[Action] 获取三条ID")
        return self.get_detail_value(1)

    # 修改三条ID
    def change_st_id(self, new_id: str) -> None:
        """修改三条ID"""
        # 修改三条ID
        logger.info(f"[Action] 修改三条ID为: {new_id}")
        self.click(OtherLocator.CHANGE_ST_ID)
        self.send_keys(OtherLocator.EDIT_ST_ID, new_id)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    # 获取二维码昵称
    def get_qrcode_nickname(self) -> str:
        """获取二维码昵称"""
        # 获取二维码昵称
        logger.info("[Action] 获取二维码昵称")
        return self.get_attribute(OtherLocator.ME_QRCODE_NAME, 'text')

    # 获取二维码性别 通过验证进行判断
    def get_qrcode_sex(self) -> str:
        """获取二维码性别 通过验证进行判断"""
        # 获取二维码性别 通过验证进行判断
        logger.info("[Action] 获取二维码性别")
        elem = self.find_element(OtherLocator.ME_QRCODE_SEX, condition="visibility", timeout=5)
        sex = VerifyColor.verify_sex(elem)
        return sex

    # 点击保存二维码
    def click_save_qrcode(self) -> None:
        """点击保存二维码"""
        # 二维码
        logger.info("[Action] 点击保存二维码")
        self.click(OtherLocator.ME_QRCODE_SAVE)

    # 获取二维码保存成功弹窗提示
    def get_qrcode_toase(self) -> str:
        """获取二维码保存成功弹窗提示"""
        # 二维码保存成功弹窗
        logger.info("[Action] 获取二维码保存提示")
        return self.get_attribute(OtherLocator.TOASE_SAVE_QRCODE, 'text')

    # 二维码页面获取所有元素是否存在
    def find_all_qrcode_attr(self) -> bool:
        """二维码页面获取所有元素是否存在"""
        # 二维码页面获取所有元素是否存在
        logger.info("[Action] 检查二维码页面所有元素是否存在")
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

    # 获取性别
    def get_sex(self) -> str:
        """获取性别"""
        # 获取 性别
        logger.info("[Action] 获取性别")
        return self.get_detail_value(2)

    # 点击性别男
    def click_sex_b(self) -> None:
        """点击性别男"""
        # 性别男
        logger.info("[Action] 点击性别【男】")
        self.click(OtherLocator.MALE, force_wait=True)

    # 点击性别女
    def click_sex_g(self) -> None:
        """点击性别女"""
        # 性别女
        logger.info("[Action] 点击性别【女】")
        self.click(OtherLocator.FEMALE, force_wait=True)

    # 点击性别取消
    def click_sex_c(self) -> None:
        """点击性别取消"""
        # 性别取消
        logger.info("[Action] 点击取消选择性别")
        self.click_cancel_button()

    # 判断是否还在邮箱页面
    def is_email_page(self) -> bool:
        """判断是否还在邮箱页面"""
        # 判断是否还在邮箱页面
        logger.info("[Action] 判断是否处于设置邮箱页面")
        title = self.get_top_middle_title()
        if title == "设置邮箱" and title != "":
            return True
        return False

    # 获取邮箱
    def get_email(self) -> str:
        """获取邮箱"""
        # 获取邮箱
        logger.info("[Action] 获取邮箱")
        return self.get_detail_value(3)

    # 修改邮箱
    def change_email(self, email: str) -> None:
        """修改邮箱"""
        # 修改邮箱
        logger.info(f"[Action] 修改邮箱为: {email}")
        self.send_keys(OtherLocator.EDIT_EMAIL, email)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    # 选择地区
    def select_area(self, area_name: str, max_retry: int = 10) -> None:
        """点击列表中的某一项，选择地区"""
        # 选择地区
        logger.info(f"[Action] 准备选择地区: {area_name}")
        uiautomator = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{area_name}")')
        ele = self.find_element(uiautomator)
        if ele is None:
            # 设置最大滑动次数避免无限循环
            while max_retry > 0:
                self.swipe_page(slid_type='up', duration=500)
                are = self.find_element(uiautomator)
                if are is not None:
                    logger.info(f"[Action] 在列表已找到地区并点击: {area_name}")
                    are.click()
                    break
                max_retry -= 1
            else:
                # 如果达到最大滑动次数仍未找到元素，抛出异常
                logger.error(f"在列表中未找到地区: {area_name}，已滑到最底部")
                raise NoSuchElementException(f"在列表中未找到地区: {area_name}，已滑动 {max_retry} 次")
        else:
            logger.info(f"[Action] 点击当前可视区地区: {area_name}")
            ele.click()
        time.sleep(0.5)  # 等待转场

    # 获取地区名称
    def get_area_name(self) -> str:
        """获取地区名称"""
        logger.info("[Action] 获取地区名称")
        return self.get_detail_value(4)
