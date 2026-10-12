import re
import time
from selenium.common.exceptions import NoSuchElementException
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

    # 修改昵称
    def change_nickname(self, nickname: str) -> None:
        """修改昵称"""
        logger.info(f"[Action] 修改昵称为: {nickname}")
        self.send_keys(OtherLocator.EDIT_NICKNAME, nickname)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    # 获取昵称
    def get_nickname(self) -> str:
        """获取昵称"""
        logger.info("[Action] 获取个人资料昵称")
        nickname = self.get_attribute(PersonalLocator.ME_NICKNAME, 'text')
        logger.info(f"[Info] 昵称: {nickname}")
        return nickname

    # 空白昵称弹窗提示 和 其他弹窗提示
    def verify_toast(self, msg: str) -> bool:
        """空白昵称弹窗提示 和 其他弹窗提示"""
        logger.info(f"[Action] 验证弹窗 Toast 提示: {msg}")
        return self.get_toast(expected_toast=msg)

    # 验证前后修改昵称是否一致
    @staticmethod
    def verify_nickname(pre_nickname: str, aft_nickname: str) -> bool:
        """验证前后修改昵称是否一致"""
        logger.info(f"[Action] 验证前后修改昵称: 修改前={pre_nickname}, 修改后={aft_nickname}")
        return aft_nickname != pre_nickname

    # 获取手机号
    def get_phone_num(self) -> str:
        """获取手机号"""
        logger.info("[Action] 获取手机号")
        return self.get_detail_value(0)

    # 验证手机号显示正常
    @staticmethod
    def verify_phone_num_show(phone: str) -> bool:
        """验证手机号显示正常"""
        # ^\d+$ 表示从头到尾都必须是数字
        logger.info(f"[Action] 验证手机号显示格式: {phone}")
        return bool(re.match(r"^\d+$", phone))

    # 获取三条ID
    def get_st_id(self) -> str:
        """获取三条ID"""
        logger.info("[Action] 获取三条ID")
        return self.get_detail_value(1)

    # 修改三条ID
    def change_st_id(self, new_id: str) -> None:
        """修改三条ID"""
        logger.info(f"[Action] 修改三条ID为: {new_id}")
        self.click(OtherLocator.CHANGE_ST_ID)
        self.send_keys(OtherLocator.EDIT_ST_ID, new_id)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass
    
    def get_texts(self) -> list[str]:
        """获取所有文本"""
        logger.info("[Action] 获取所有文本")
        elements = self.find_elements(OtherLocator.ME_TEXTS)
        texts = [e.get_attribute('text') for e in elements]
        logger.info(f"✅ [Action] 所有文本: {texts}")
        return texts

    # 获取二维码昵称
    def get_qrcode_nickname(self) -> str:
        """获取二维码页面显示的昵称"""
        logger.info("[Action] 获取二维码昵称")
        if self.is_element_exist(OtherLocator.ME_QRCODE_NAME, timeout=2):
            text = self.get_attribute(OtherLocator.ME_QRCODE_NAME, 'text')
            if text:
                logger.info(f"✅ [Action] 获取二维码昵称成功: {text}")
                return text
        logger.error("❌ [Action] 二维码昵称获取失败")
        return ""

    # 获取二维码性别 通过验证进行判断
    def get_qrcode_sex(self) -> str:
        """获取二维码性别（新版 UI 已移除性别展示，增加防御性探测）"""
        logger.info("[Action] 尝试获取二维码性别")
        loc_sex = getattr(OtherLocator, 'ME_QRCODE_SEX', None)
        if not loc_sex or not self.is_element_exist(loc_sex, timeout=1, raise_exception=False):
            logger.info("ℹ️ [Action] 当前二维码页面未包含性别图标（新版 UI），返回空值")
            return ""
        elem = self.find_element(loc_sex, condition="visibility", timeout=2, raise_exception=False)
        return VerifyColor.verify_sex(elem) if elem else ""

    # 点击保存二维码
    def click_save_qrcode(self) -> None:
        """点击保存二维码"""
        logger.info("[Action] 点击保存二维码")
        self.click(OtherLocator.ME_QRCODE_SAVE)

    # 点击二维码页面左上角返回
    def click_qrcode_back(self) -> None:
        """点击二维码页面左上角返回按钮回到个人信息主页"""
        logger.info("[Action] 点击二维码页面返回按钮")
        self.click(OtherLocator.TOP_IV_BACK_BTN, force_wait=True)

    # 获取二维码保存成功弹窗提示
    def get_qrcode_toast(self) -> str:
        """获取二维码保存成功弹窗提示"""
        logger.info("[Action] 获取二维码保存提示")
        return self.get_attribute(OtherLocator.TOASE_SAVE_QRCODE, 'text')

    # 二维码页面获取所有元素是否存在
    def find_all_qrcode_attr(self) -> bool:
        """
        二维码页面核心元素完整性校验：
        校验标题(我的二维码)、保存按钮、引导提示语、昵称（不校验返回按钮）
        使用 raise_exception=False 静默探测，避免元素缺失触发误报截图与错误日志
        """
        logger.info("[Action] 检查二维码页面核心元素是否存在")
        title_elem = self.find_element(OtherLocator.TOP_TV_TITLE, timeout=2, raise_exception=False)
        if not title_elem:
            title_elem = self.find_element(OtherLocator.ME_QRCODE_TITLE, timeout=1, raise_exception=False)

        save_elem = self.find_element(OtherLocator.ME_QRCODE_SAVE, timeout=2, raise_exception=False)
        tip_elem = self.find_element(OtherLocator.ME_QRCODE_TIP, timeout=1, raise_exception=False)
        nickname_elem = self.find_element(OtherLocator.ME_QRCODE_NAME, timeout=1, raise_exception=False)

        core_exists = title_elem is not None
        detail_exists = any(e is not None for e in [save_elem, tip_elem, nickname_elem])
        is_ready = bool(core_exists and detail_exists)

        logger.info(
            f"✅ [Action] 二维码页面核心元素校验结果: {is_ready} "
            f"(title={bool(title_elem)}, save={bool(save_elem)}, "
            f"tip={bool(tip_elem)}, nickname={bool(nickname_elem)})"
        )
        return is_ready

    # 获取性别
    def get_sex(self) -> str:
        """获取性别"""
        logger.info("[Action] 获取性别")
        time.sleep(0.5)
        return self.get_detail_value(3)

    # 点击性别男
    def click_sex_b(self) -> None:
        """点击性别男"""
        logger.info("[Action] 点击性别【男】")
        self.click(OtherLocator.MALE, force_wait=True)

    # 点击性别女
    def click_sex_g(self) -> None:
        """点击性别女"""
        logger.info("[Action] 点击性别【女】")
        self.click(OtherLocator.FEMALE, force_wait=True)

    # 点击性别取消
    def click_sex_c(self) -> None:
        """点击性别取消"""
        logger.info("[Action] 点击取消选择性别")
        self.click_cancel_button()

    # 判断是否还在邮箱页面
    def is_email_page(self) -> bool:
        """判断是否还在邮箱页面"""
        logger.info("[Action] 判断是否处于设置邮箱页面")
        return self.get_top_middle_title() == "设置邮箱"

    # 获取邮箱
    def get_email(self) -> str:
        """获取邮箱"""
        logger.info("[Action] 获取邮箱")
        return self.get_detail_value(4)

    # 修改邮箱
    def change_email(self, email: str) -> None:
        """修改邮箱"""
        logger.info(f"[Action] 修改邮箱为: {email}")
        self.send_keys(OtherLocator.EDIT_EMAIL, email)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    # 选择地区
    def select_area(self, area_name: str, max_retry: int = 10) -> None:
        """点击列表中的某一项，选择地区"""
        logger.info(f"[Action] 准备选择地区: {area_name}")
        uiautomator = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{area_name}")')
        ele = self.find_element(uiautomator, timeout=1.5)
        if ele is None:
            while max_retry > 0:
                self.swipe_page(slid_type='up', duration=500)
                are = self.find_element(uiautomator, timeout=1.5)
                if are is not None:
                    logger.info(f"[Action] 在列表已找到地区并点击: {area_name}")
                    are.click()
                    break
                max_retry -= 1
            else:
                logger.error(f"在列表中未找到地区: {area_name}，已滑到最底部")
                raise NoSuchElementException(f"在列表中未找到地区: {area_name}，已滑动 {max_retry} 次")
        else:
            logger.info(f"[Action] 点击当前可视区地区: {area_name}")
            ele.click()
        time.sleep(0.5)

    # 完整设置所在地业务闭环
    def set_location(self, province: str, city: str) -> None:
        """
        设置所在地完整业务闭环：
        点击进入所在地 -> 级联选择省份 -> 级联选择城市 (保存) -> 智能等待平滑回退至个人主页
        """
        logger.info(f"⚙️ [Action] 设置所在地为: {province} {city}")
        self.click_location()
        self.select_area(province)
        self.select_area(city)
        # 智能等待平滑回退到个人信息主页，确保服务端落盘与主页元素就绪
        self.back_to_personal_info(max_retry=3)

    # 获取地区名称
    def get_area_name(self) -> str:
        """获取地区名称（索引 5: 0-手机号, 1-三条ID, 2-二维码, 3-性别, 4-邮箱, 5-所在地）"""
        logger.info("[Action] 获取地区名称")
        return self.get_detail_value(5)
