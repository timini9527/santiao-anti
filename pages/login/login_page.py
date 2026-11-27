import time
from typing import Optional
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from common.base_page import BasePage
from common.toast_enums import ToastMsg
from locators.login.login_locator import LoginLocator
from core.logger_utils import logger, LogIcon
from business_helpers.verify_color import VerifyColor
from pages.common.common_page import CommonPage
from utils.cv_recognition.ocr_utils import OcrUtils


class LoginPage(BasePage):
    """登录页面对象"""

    def __init__(self, driver):
        super().__init__(driver)
        self.commonPage = CommonPage(driver)
        self.ocrUtils = OcrUtils(driver)

    def _raw_driver(self) -> object:
        """获取底层真实 Driver 实例（兼容 RecoverableDriver，Session 重建时缓存自动失效）"""
        return getattr(self.driver, "_driver", self.driver)

    def _get_cached_password(self) -> Optional[str]:
        """读取当前表单周期缓存的密码（None 表示未知态，'' 表示已确认空框）"""
        return getattr(self._raw_driver(), "_last_login_password", None)

    def _set_cached_password(self, value: Optional[str]) -> None:
        """更新当前表单周期的密码缓存，供鸿蒙密文密码框实现同密码短路与已知空框免清空"""
        try:
            setattr(self._raw_driver(), "_last_login_password", value)
        except Exception:
            pass

    # ==========================
    # 页面状态检测
    # ==========================
    # 登录页 - 检测当前是否处于登录主页面
    def is_on_login_main_page(self, timeout: int = 2) -> bool:
        """
        检测当前是否处于登录主页面（优先命中高速入口按钮，避免鸿蒙直接触发 XPath 全树扫描）
        :param timeout: 显式等待超时时间 (默认 2s)
        :return: True(当前处于登录主页面) / False(不在登录主页面)
        """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 检测当前是否处于登录主页面 (超时: {timeout}s)")
        # 1. 优先判定高速登录主入口（鸿蒙走 HypiumBy 原生直查，Android/iOS 走 ID，约 1s 内返回）
        entrance = self.find_element(LoginLocator.LOGIN_ENTRANCE, timeout=timeout, expect_missing=True)
        if entrance:
            logger.info(f"{LogIcon.SUCCESS} [Action - Login] 识别到手机号登录主入口，当前处于登录主页面")
            return True

        fallback_timeout = min(1, timeout)
        one_key = self.find_element(LoginLocator.ONE_KEY_LOGIN_ENTRANCE, timeout=fallback_timeout, expect_missing=True)
        if one_key:
            logger.info(f"{LogIcon.SUCCESS} [Action - Login] 识别到一键登录主入口，当前处于登录主页面")
            return True

        # 2. 兜底判定：弱网或按钮未渲染完成时，再校验顶部应用主 Logo
        logo_elem = self.find_element(LoginLocator.APPLICATION_LOGO, timeout=fallback_timeout, expect_missing=True)
        if logo_elem:
            logger.info(f"{LogIcon.SUCCESS} [Action - Login] 识别到应用 Logo 元素，当前处于登录主页面")
            return True

        logger.warning(f"{LogIcon.FAIL} [Action - Login] 未能检测到登录主入口及应用 Logo，当前不处于登录主页面")
        return False

    # 登录页 - 检测当前是否处于手机号/账号密码登录表单页
    def is_on_phone_login_page(self, timeout: int | float = 2) -> bool:
        """
        检测当前是否处于手机号 / 账号密码 / 验证码登录表单页。
        密码切换与短信切换按钮互斥，因此优先检测双模式均常驻的手机号输入框与登录提交按钮，避免先查不存在的切换项白等超时。
        :param timeout: 显式等待超时时间 (默认 2s)
        :return: True(当前处于登录表单页) / False(不在登录表单页)
        """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 检测当前是否处于手机号/密码登录表单页 (超时: {timeout}s)")
        lookup_condition = "presence" if self._platform_name == "harmonyos" else "visibility"
        primary_timeout = max(0.5, float(timeout))
        fallback_timeout = max(0.3, min(0.8, float(timeout)))

        # 1. 优先判定双模式常驻核心特征：手机号输入框（密码登录与短信登录下均固定存在）
        if self.find_element(
            LoginLocator.PHONE_NUMBER_EDIT,
            condition=lookup_condition,
            timeout=primary_timeout,
            expect_missing=True,
        ):
            logger.info(f"{LogIcon.SUCCESS} [Action - Login] 识别到手机号输入框，当前处于登录表单页")
            return True

        # 2. 兜底判定双模式常驻提交按钮（避免依赖互斥的密码/短信切换按钮）
        if self.find_element(
            LoginLocator.VERIFY_AND_LOGIN_BTN,
            condition=lookup_condition,
            timeout=fallback_timeout,
            expect_missing=True,
        ):
            logger.info(f"{LogIcon.SUCCESS} [Action - Login] 识别到登录提交按钮，当前处于登录表单页")
            return True

        logger.warning(f"{LogIcon.FAIL} [Action - Login] 未能检测到登录表单特征元素，当前不处于登录表单页")
        return False

    # 登录页 - 自动返回直到检测到登录主页面
    def back_to_login_main_page(self, max_retries: int = 3, timeout: int = 1) -> bool:
        """
        自动返回直到检测到登录主页面 (通过 APPLICATION_LOGO 进行精准核验)
        
        如果当前不在登录主页面，则尝试点击左上角返回按钮 (或系统返回键)，
        直到检测到 APPLICATION_LOGO 为止，具备防死循环最大重试限制。
        
        :param max_retries: 最大返回尝试次数 (默认 3 次)
        :param timeout: 单次检测 Logo 超时时间 (默认 1s)
        :return: True(已成功处于登录主页面) / False(未能回到登录主页面)
        """
        logger.info(f"{LogIcon.WAIT} 检查并尝试返回登录主页面 (最大重试: {max_retries} 次)")
        for attempt in range(max_retries + 1):
            if self.is_on_login_main_page(timeout=timeout):
                logger.info(f"{LogIcon.SUCCESS} [Action - Login] 确认已处于登录主页面")
                return True
            if attempt < max_retries:
                logger.info(f"{LogIcon.ACTION} 当前不在登录主页面，第 {attempt + 1}/{max_retries} 次尝试点击返回...")
                back_btn = self.find_element(LoginLocator.TOP_IV_BACK_BTN, timeout=1, expect_missing=True)
                if back_btn and back_btn.is_displayed():
                    back_btn.click()
                else:
                    self.press_back()
                time.sleep(0.5)

        logger.warning(f"{LogIcon.FAIL} 达到最大重试次数 ({max_retries} 次)，仍未能回到登录主页面")
        return False
    


    # ==========================
    # 顶部导航类操作
    # ==========================
    # 登录页 - 点击界面左上角返回按钮
    def click_back_btn(self) -> None:
        """ 点击界面左上角的返回按钮 """
        logger.info(f"{LogIcon.SETUP} 点击左上角返回按钮")
        self._set_cached_password(None)
        self.click(LoginLocator.TOP_IV_BACK_BTN)

    # 登录页 - 获取顶部标题（手机号，密码，一键登录）
    def get_top_title(self) -> str:
        """ 登录功能 获取页面 top 标题 """
        title = self.commonPage.get_top_middle_title()
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 获取页面 top 标题: {title}")
        return title

    # ==========================
    # 核心入口与模式切换
    # ==========================
    # 登录页 - 点击进入手机号登录按钮
    def click_phone_login_button(self) -> None:
        """如果在启动页，点击进入‘手机号登录’界面的按钮（乐观直达，找不到再进入表单短路与返回自愈）。"""
        logger.info(f"{LogIcon.SETUP} 点击进入手机号登录主界面")
        # 鸿蒙端通过 HypiumBy 原生检索可视树并用坐标手势点击，跳过 is_displayed 与 Component.click 5s Idle 等待
        is_harmony = self._platform_name == "harmonyos"
        lookup_condition = "presence" if is_harmony else "visibility"

        # 1. 乐观直达：优先直接命中并点击登录入口（正常路径仅 1 次高速直查，消除多余 XPath 串行探测）
        entrance = self.find_element(
            LoginLocator.LOGIN_ENTRANCE,
            condition=lookup_condition,
            timeout=2,
            expect_missing=True,
        )
        if entrance:
            logger.info(f"{LogIcon.ACTION} 直接命中手机号登录入口，执行点击")
            self._set_cached_password(None)
            if is_harmony:
                self.tap_point(click_elem=entrance, duration=100)
            else:
                entrance.click()
            return

        # 2. 异常兜底-短路：若未找到登录入口，复用表单页常驻特征检测是否已处于手机号表单页
        if self.is_on_phone_login_page(timeout=0.8):
            logger.info(f"{LogIcon.SUCCESS} 当前已处于手机号输入界面，无需重复点击‘手机号登录’")
            return

        # 3. 异常兜底-状态自愈：不在登录主页也不在表单页，自动返回直到回到登录主页面后再点击
        logger.info(f"{LogIcon.ACTION} 当前不在登录主页面，执行自动返回自愈")
        self._set_cached_password(None)
        self.back_to_login_main_page()
        if is_harmony:
            entrance = self.find_element(LoginLocator.LOGIN_ENTRANCE, condition="presence", timeout=3)
            if entrance:
                self.tap_point(click_elem=entrance, duration=100)
                return
        self.click(LoginLocator.LOGIN_ENTRANCE, timeout=3)
    
    # 登录页 - 点击一键登录按钮
    def click_one_click_login_button(self) -> None:
        """ 点击一键登录按钮 """
        logger.info(f"{LogIcon.SETUP} 点击一键登录按钮")
        self.click(LoginLocator.ONE_KEY_LOGIN_ENTRANCE, force_wait=True)

    # 登录页 - 切换到密码登录模式
    def click_password_login_button(self) -> None:
        """ 点击‘密码登录’，如果当前是验证码等其他模式则切换 """
        logger.info(f"{LogIcon.SETUP} 检查并尝试切换到密码登录模式")
        if self._platform_name == "harmonyos":
            # 鸿蒙密码模式存在 2 个 TextInput（手机号 + 密码），短信模式仅 1 个；走定位器原生 type 直查规避 XPath 负向超时
            inputs = self.find_elements(
                LoginLocator.FORM_INPUTS,
                condition="presence",
                timeout=0.5,
                expect_missing=True,
            )
            if len(inputs) >= 2:
                logger.info(f"{LogIcon.SUCCESS} 当前已处于密码登录模式（检测到 {len(inputs)} 个输入框），无需切换")
                return
            pass_elem = self.find_element(LoginLocator.PASSWORD_LOGIN_SWITCH, condition="presence", timeout=2, expect_missing=True)
            if pass_elem:
                logger.info(f"{LogIcon.SETUP} 执行切换到密码登录模式")
                self._set_cached_password(None)
                self.tap_point(click_elem=pass_elem, duration=100)
                time.sleep(0.3)
            return

        pass_elem = self.find_element(LoginLocator.PASSWORD_LOGIN_SWITCH, timeout=2, expect_missing=True)
        if pass_elem:
            pwd_elem = self.find_element(LoginLocator.PASSWORD_EDIT, timeout=0.3, expect_missing=True)
            if not pwd_elem:
                logger.info(f"{LogIcon.SETUP} 执行切换到密码登录模式")
                self._set_cached_password(None)
                pass_elem.click()
                time.sleep(0.5)

    # 登录页 - 切换到验证码登录模式
    def click_code_login_button(self) -> None:
        """ 点击‘短信验证登录’，如果当前是密码登录模式则切换（跨端短路，避免已在短信模式时产生误导 ERROR 日志） """
        logger.info(f"{LogIcon.SETUP} 检查并尝试切换到验证码登录模式")
        if self._platform_name == "harmonyos":
            # 鸿蒙短信模式仅 1 个 TextInput（手机号），密码模式有 2 个；走定位器原生 type 直查规避 XPath 负向超时
            inputs = self.find_elements(
                LoginLocator.FORM_INPUTS,
                condition="presence",
                timeout=0.5,
                expect_missing=True,
            )
            if len(inputs) == 1:
                logger.info(f"{LogIcon.SUCCESS} 当前已处于验证码登录模式（检测到 1 个输入框），无需切换")
                return
            code_elem = self.find_element(LoginLocator.CODE_LOGIN_SWITCH, condition="presence", timeout=2, expect_missing=True)
            if code_elem:
                logger.info(f"{LogIcon.SETUP} 执行切换到验证码登录模式")
                self._set_cached_password(None)
                self.tap_point(click_elem=code_elem, duration=100)
                time.sleep(0.3)
            return

        code_elem = self.find_element(LoginLocator.CODE_LOGIN_SWITCH, timeout=1.5, expect_missing=True)
        if code_elem:
            pwd_elem = self.find_element(LoginLocator.PASSWORD_EDIT, timeout=0.3, expect_missing=True)
            if pwd_elem:
                logger.info(f"{LogIcon.SETUP} 执行切换到验证码登录模式")
                self._set_cached_password(None)
                code_elem.click()
                time.sleep(0.5)

    # ==========================
    # 账号/密码输入类操作
    # ==========================
    # 登录页 - 清空手机号输入框内容
    def clear_phone(self) -> None:
        """ 清空手机号输入框内容（鸿蒙端走一键全选秒清，避免逐字退格慢删） """
        logger.info(f"{LogIcon.SETUP} 准备清空手机号输入框")
        elem = self.find_element(LoginLocator.PHONE_NUMBER_EDIT, timeout=2)
        if elem:
            logger.info(f"{LogIcon.SETUP} 执行清空手机号输入框")
            self.clear_input_element(elem)

    # 登录页 - 输入手机号或账号
    def input_account(self, phone: str) -> None:
        """ 在手机号/账号输入框中输入内容（鸿蒙端自动升级原生 UiComponent，支持实时判同短路与原子清空） """
        logger.info(f"{LogIcon.SETUP} 输入账号/手机号: {phone}")
        if self._platform_name == "harmonyos":
            ele = self.find_element(LoginLocator.PHONE_NUMBER_EDIT, timeout=2)
            if not ele:
                self.send_keys(LoginLocator.PHONE_NUMBER_EDIT, phone, clear=True)
                return
            ele = self._resolve_native_harmony_input(ele)
            current_text = self.read_element_attr(ele, "text").strip()
            if current_text == str(phone).strip():
                logger.info(f"{LogIcon.SUCCESS} 手机号输入框已为目标账号 {phone}，跳过清空与重复输入")
                return
            if current_text:
                self.clear_input_element(ele)
            if phone:
                ele.send_keys(phone)
                logger.info(f"{LogIcon.ACTION} 输入消息: {phone}")
            return

        self.send_keys(LoginLocator.PHONE_NUMBER_EDIT, phone, clear=True)
    
    # 登录页 - 获取手机号输入框内容
    def get_phone_number(self) -> str:
        """ 获取手机号输入框中的内容 """
        phone_number = self.get_attribute(LoginLocator.PHONE_NUMBER_EDIT, "text")
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 获取手机号: {phone_number}")
        return phone_number

    # 登录页 - 点击一键清空手机号按钮
    def clear_phone_number(self) -> None:
        """ 点击手机号输入框右侧的 (x) 图标，一键清空内容 """
        logger.info(f"{LogIcon.SETUP} 准备一键清空当前输入的手机号")
        if self.is_element_exist(LoginLocator.CLEAR_PHONE_NUMBER, timeout=2):
            logger.info(f"{LogIcon.SETUP} 点击清空手机号图标")
            self.click(LoginLocator.CLEAR_PHONE_NUMBER)

    def _dismiss_harmony_secure_keyboard(self) -> None:
        """
        鸿蒙密文密码框获焦时会触发系统安全输入法防截屏黑屏保护（screenCap 全黑）。
        轻点顶部静态标题空白区（屏幕 50%, 14%，无交互控件）使密码框失焦并收起安全键盘，确保后续视觉颜色校验正常截屏。
        """
        if self._platform_name != "harmonyos":
            return
        try:
            raw_driver = self._raw_driver()
            win_size = getattr(raw_driver, "_cached_window_size", None)
            if not isinstance(win_size, dict) or not win_size.get("width") or not win_size.get("height"):
                win_size = self.driver.get_window_size()
            width = int(win_size.get("width", 0))
            height = int(win_size.get("height", 0))
            if width > 0 and height > 0:
                self.tap_point(x=width // 2, y=int(height * 0.05), duration=60)
                time.sleep(0.25)
        except Exception as err:
            logger.debug(f"{LogIcon.WARN} [HarmonyOS] 收起安全键盘失焦失败（不阻断流程）: {err}")

    # 登录页 - 清空密码输入框内容
    def clear_password(self) -> None:
        """ 清空密码输入框内容（兼容鸿蒙 ArkUI 密文密码框强清空，并同步密码缓存为空串） """
        logger.info(f"{LogIcon.SETUP} 准备清空密码输入框")
        elem = self.find_element(LoginLocator.PASSWORD_EDIT, timeout=2)
        if elem:
            logger.info(f"{LogIcon.SETUP} 执行清空密码输入框")
            self._set_cached_password(None)
            self.clear_input_element(elem, force_select_all=True)
            self._set_cached_password("")
            self._dismiss_harmony_secure_keyboard()

    # 登录页 - 输入密码
    def input_password(self, password: str) -> None:
        """
        在密码输入框中输入内容：
        - 鸿蒙端支持同密码短路（连续留在登录页且目标密码不变时 0ms 跳过）与已知空框免清空，
          最大限度规避 ArkUI 密文框禁止 Ctrl+A 触发原生逐字清空的耗时；
        - 输入/清空结束后自动轻点顶部静态标题区失焦收起安全键盘，解除系统防截屏黑屏保护；
        - Android / iOS 保持原有标准清空并输入逻辑。
        """
        logger.info(f"{LogIcon.SETUP} 输入登录密码: {password}")
        if self._platform_name == "harmonyos":
            target_pwd = "" if password is None else str(password)
            cached_pwd = self._get_cached_password()
            if cached_pwd is not None and cached_pwd == target_pwd:
                logger.info(f"{LogIcon.SUCCESS} [HarmonyOS] 密码框已为当前目标密码，跳过重复清空与输入")
                return

            # 执行前先置为未知，避免输入异常遗留脏缓存
            self._set_cached_password(None)
            need_clear = cached_pwd != ""
            self.send_keys(
                LoginLocator.PASSWORD_EDIT,
                target_pwd,
                clear=need_clear,
                force_select_all=True,
            )
            self._set_cached_password(target_pwd)
            self._dismiss_harmony_secure_keyboard()
            return

        self.send_keys(LoginLocator.PASSWORD_EDIT, password, clear=True, force_select_all=True)
    
    # 登录页 - 获取密码输入框内容
    def get_password(self) -> str:
        """ 获取密码输入框中的内容 """
        password = self.get_attribute(LoginLocator.PASSWORD_EDIT, "text")
        logger.info(f"{LogIcon.SUCCESS} 🧐 [Action - Login] 获取密码: {password}")
        return password
    
    # 登录页 - 获取密码输入框元素
    def get_password_element(self, expect_missing: bool = False) -> Optional[WebElement]:
        """ 获取密码输入框元素 """
        elem = self.find_element(LoginLocator.PASSWORD_EDIT, timeout=2, expect_missing=expect_missing)
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 获取密码输入框元素")
        return elem

    # 登录页 - 切换密码明文或密文显示状态
    def click_password_visible_btn(self) -> None:
        """ 点击密码输入框右侧的‘眼睛’图标，切换密码明文/密文显示状态 """
        logger.info(f"{LogIcon.SETUP} 切换密码可见状态")
        self.click(LoginLocator.PASSWORD_VISIBLE_BTN)
    
    # 登录页 - 获取登录模块 Toast 消息
    def get_login_toast_message(self) -> str:
        """ 获取 login 到 Toast 消息 """
        toast_message = self.commonPage.get_toast_message_common()
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 获取 login 到 Toast 消息: {toast_message}")
        return toast_message
    
    # 登录页 - 获取验证码倒计时文本
    def get_verification_code_countdown_text(self) -> str:
        """ 获取验证码倒计时文本 """
        time.sleep(1)
        countdown_text = self.get_attribute(LoginLocator.VERIFICATION_CODE_COUNTDOWN, "text")
        logger.info(f"{LogIcon.WAIT} 🧐 [Action - Login] 获取验证码倒计时: {countdown_text}")
        return countdown_text

    # 登录页 - 判断是否在验证码登录页面
    def is_on_verification_login_page(self, timeout: int | float = 2) -> bool:
        """
        判断当前是否处于验证码四宫格输入页面
        :param timeout: 超时时间
        :return: True(在验证码输入页面) / False(不在验证码输入页面)
        """
        logger.info(f"{LogIcon.WAIT} 🧐 [Action - Login] 判断当前是否处于验证码登录页面 (超时: {timeout}s)")
        lookup_condition = "presence" if self._platform_name == "harmonyos" else "visibility"
        return self.is_element_exist(LoginLocator.PLEASE_ENTER_VERIFICATION_CODE, timeout=timeout, condition=lookup_condition)

    # ==========================
    # 协议与底层弹窗操作
    # ==========================
    # 登录页 - 勾选用户协议
    def click_user_agreement(self) -> None:
        """ 检查登录页面的底部的协议复选框是否勾选，未勾选则直接点击已定位元素 """
        logger.info(f"{LogIcon.SETUP} 检查用户协议勾选状态")
        agren_elem = self.find_element(LoginLocator.AGREE_AND_LOGIN_BTN, timeout=2)
        if agren_elem:
            if not VerifyColor.verify_agree_btn(agren_elem):
                logger.info(f"{LogIcon.SETUP} 执行勾选用户协议复选框")
                if self._platform_name == "harmonyos":
                    self.tap_point(click_elem=agren_elem, duration=80)
                else:
                    self.click_element(agren_elem, "用户协议复选框")
    
    # 登录页 - 取消勾选用户协议
    def cancel_user_agreement(self) -> None:
        """ 检查登录页面的底部的协议复选框是否勾选，已勾选则直接点击已定位元素取消勾选 """
        logger.info(f"{LogIcon.SETUP} 检查用户协议勾选状态以取消勾选")
        agren_elem = self.find_element(LoginLocator.AGREE_AND_LOGIN_BTN, timeout=2)
        if agren_elem:
            if VerifyColor.verify_agree_btn(agren_elem):
                logger.info(f"{LogIcon.SETUP} 执行取消勾选用户协议")
                if self._platform_name == "harmonyos":
                    self.tap_point(click_elem=agren_elem, duration=80)
                else:
                    self.click_element(agren_elem, "用户协议复选框")

    # 登录页 - 处理协议拦截弹窗同意并继续
    def click_handle_agreement_popup(self) -> None:
        """ 处理因‘未勾选协议点击登录’而弹出的‘用户协议及隐私政策’底层弹窗，点击‘同意并继续’ """
        logger.info(f"{LogIcon.SETUP} 处理协议拦截弹窗，准备点击【同意并继续】")
        bottom_aggree_btn = self.find_element(LoginLocator.AGREE_AND_CONTINUE_BTN, timeout=3)
        if bottom_aggree_btn:
            logger.info(f"{LogIcon.SETUP} 点击【同意并继续】")
            bottom_aggree_btn.click()

    # 登录页 - 关闭协议底层弹窗
    def close_agreement_popup(self) -> None:
        """ 点击底层隐私协议弹窗右上角的 (X) 关闭按钮 """
        logger.info(f"{LogIcon.SETUP} 准备关闭隐私协议底层弹窗")
        close_btn = self.find_element(LoginLocator.CLOSE_BTN, timeout=2)
        if close_btn:
            logger.info(f"{LogIcon.SETUP} 点击关闭隐私协议弹窗")
            close_btn.click()
    
    # 登录页 - 获取隐私弹窗标题
    def get_agreement_popup_title(self) -> str:
        """ 获取‘用户协议及隐私政策’底层弹窗的标题（走弹窗专属定位器，避免鸿蒙端误抓底层页面同名 id='title'） """
        title = self.get_attribute(LoginLocator.AGREEMENT_POPUP_TITLE, "text") or ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 未勾选同意点击登录后，获取到隐私弹窗标题: {title}")
        return title
    
    # 登录页 - 获取协议文本
    def get_agreement_text(self) -> str:
        """ 获取登录页面底部的协议文本 """
        text = self.get_attribute(LoginLocator.AGREE_AND_LOGIN_TEXT, "text") or ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 获取到登录页面底部的协议文本: {text}")
        return text

    # 登录页 - 点击底部协议链接（仅 iOS 原生 Link 元素直点）
    def click_agreement_link(self, agreement_name: str = "《用户协议》") -> bool:
        """通过 iOS 原生超链接定位器直接点击指定协议链接"""
        link_map = {
            "《用户协议》": LoginLocator.USER_AGREEMENT_LINK,
            "《隐私政策》": LoginLocator.PRIVACY_POLICY_LINK,
            "《隐私协议》": LoginLocator.PRIVACY_POLICY_LINK,
            "《未成年人个人信息保护规则》": LoginLocator.CHILD_PROTECTION_LINK,
            "《支付协议》": LoginLocator.PAYMENT_AGREEMENT_LINK,
        }
        locator = link_map.get(agreement_name)
        if not locator:
            logger.warning(f"{LogIcon.WARN} 未找到协议 '{agreement_name}' 对应的原生定位器")
            return False
        logger.info(f"{LogIcon.ACTION} [iOS] 直接通过元素定位点击协议: {agreement_name}")
        try:
            self.click(locator, timeout=3)
            return True
        except NoSuchElementException:
            return False

    # ==========================
    # 登录提交与校验
    # ==========================
    # 登录页 - 自动处理系统保存密码弹窗
    def handle_save_password_popup(self, timeout: float = 2.0) -> bool:
        """
        自动检测并消除系统级‘自动保存账号密码’弹窗 (MIUI/HyperOS；iOS 系统密码框属独立进程不在 App 树内，直接跳过防空等)
        """
        if self._platform_name == "ios":
            return False
        cancel_btn = self.find_element(LoginLocator.AUTO_SAVE_PWD_CANCEL, timeout=timeout, expect_missing=True)
        if cancel_btn:
            logger.info(f"{LogIcon.SETUP} 检测到系统‘自动保存账号密码’弹窗，点击【取消】")
            try:
                cancel_btn.click()
                time.sleep(0.3)
                return True
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} 点击取消保存密码异常: {e}")
        return False

    # 登录页 - 点击登录或验证并登录按钮
    def click_login_button(self, auto_dismiss_save_pwd: bool = True) -> None:
        """ 执行最终的‘登录’或‘验证并登录’按钮点击动作 """
        logger.info(f"{LogIcon.SETUP} 点击 [验证并登录/登录] 按钮")
        self.click(LoginLocator.VERIFY_AND_LOGIN_BTN)
        if auto_dismiss_save_pwd:
            self.handle_save_password_popup(timeout=2)
        
    # 登录页 - 点击遇到问题反馈
    def click_feedback_btn(self) -> None:
        """ 点击‘遇到问题？点击反馈’按钮 """
        logger.info(f"{LogIcon.SETUP} 点击遇到问题反馈求助按钮")
        self.click(LoginLocator.FEEDBACK_BTN)

    # 登录页 - 判断登录是否成功
    def is_login_success(self) -> bool:
        """ 根据是否能找到主页特有元素判断登录是否成功，并自动关闭首次进入主页的布局引导弹窗 """
        from pages.home.home_page import HomePage
        home_page = HomePage(self.driver)
        if self._platform_name == "ios":
            if home_page.is_left_menu_visible(timeout=2):
                home_page.dismiss_layout_guide_if_present(timeout=0.5)
                logger.info(f"{LogIcon.SUCCESS} [iOS] 登录成功，已检测到主页左上角菜单按钮")
                return True
            if home_page.dismiss_layout_guide_if_present(timeout=0.8):
                if home_page.is_left_menu_visible(timeout=2):
                    logger.info(f"{LogIcon.SUCCESS} [iOS] 关闭主页布局引导弹窗后确认登录成功，已检测到主页左上角菜单按钮")
                    return True
            logger.info(f"{LogIcon.FAIL} [iOS] 登录未成功，未检测到主页左上角菜单按钮")
            return False

        title = home_page.get_top_middle_title(expect_missing=True)
        if '三条' in title:
            self._set_cached_password(None)
            home_page.dismiss_layout_guide_if_present(timeout=0.5)
            logger.info(f"{LogIcon.SUCCESS} 登录成功，获取到主页标题: {title}")
            return True

        # 引导弹窗抢占焦点窗口导致主页标题暂不可见时，关闭弹窗后复核主页标题
        if home_page.dismiss_layout_guide_if_present(timeout=0.8):
            title = home_page.get_top_middle_title(expect_missing=True)
            if '三条' in title:
                self._set_cached_password(None)
                logger.info(f"{LogIcon.SUCCESS} 关闭主页布局引导弹窗后确认登录成功，获取到主页标题: {title}")
                return True

        logger.info(f"{LogIcon.FAIL} 登录未成功，获取到主页标题: {title}")
        return False

    # 登录页 - 获取 Toast 提示
    def get_toast_text(
        self,
        timeout: float = 3.0,
        expected_toast: str = "",
        detect_rate_limit: bool = False,
    ) -> str:
        """
        获取页面弹出的系统级 Toast 或普通 TextView 错误提示。
        如果参数带有 expected_toast 预期文本，则开启预期文本驱动的全屏搜索，极大提升各类弹窗和红字提示的捕获率。
        当 detect_rate_limit=True 时，同步探测「触发天极流控 / 触发小时级流控」等流控提示，避免漏捕并空等超时。
        """
        logger.info(f"{LogIcon.WAIT} 开始监听提示 (超时: {timeout}s | 优先内容: '{expected_toast}')")

        end_time = time.time() + timeout
        text = ""
        while time.time() < end_time:
            try:
                # 1. 优先级策略：如果提供了预期文本，优先匹配预期提示
                if expected_toast:
                    dynamic_locator = LoginLocator.get_dynamic_toast_msg(expected_toast)
                    toast = self.find_element(dynamic_locator, timeout=0.2, condition="presence", expect_missing=True)
                    if toast:
                        text = self.read_element_attr(toast, "text")
                        if text:
                            logger.info(f"{LogIcon.SUCCESS} 通过文本匹配命中业务提示 Toast: {text}")
                            return text

                # 2. 匹配通用 Toast ID
                toast = self.find_element(LoginLocator.TOAST_MSG, timeout=0.2, condition="presence", expect_missing=True)
                if toast:
                    text = self.read_element_attr(toast, "text")
                    if text and text != ToastMsg.LOGGING_IN:
                        logger.info(f"{LogIcon.SUCCESS} 通过 ID 命中业务提示 Toast: {text}")
                        return text

                # 3. 短信发码场景同步探测流控提示（触发天极流控 / 触发小时级流控），命中后立即返回便于上层熔断切号
                if detect_rate_limit:
                    rate_limit_toast = self.find_element(
                        LoginLocator.RATE_LIMIT_TOAST,
                        timeout=0.1,
                        condition="presence",
                        expect_missing=True,
                    )
                    if rate_limit_toast:
                        text = self.read_element_attr(rate_limit_toast, "text")
                        if text:
                            logger.warning(f"{LogIcon.WARN} 捕获到短信流控提示 Toast: {text}")
                            return text
            except StaleElementReferenceException:
                continue
            time.sleep(0.05)
        logger.warning(f"{LogIcon.FAIL} 监听结束，在 {timeout}s 内未捕获到任何符合条件的提示内容 - 实际获取到的Toast: {text}")
        return ""
    
    # 登录页 - 等待无卡时登录首页
    def wait_for_login_success_no_card(self, timeout: int = 10) -> bool:
        """ 等待无卡时登录首页 """
        logger.info(f"{LogIcon.WAIT} 开始等待无卡登录首页 (超时: {timeout}s)")
        elem = self.find_element(LoginLocator.LOGIN_ENTRANCE, timeout=timeout)
        if elem:
            logger.info(f"{LogIcon.SUCCESS} 成功进入无卡登录首页")
            return True
        else:
            logger.warning(f"{LogIcon.FAIL} 未能在规定时间内进入无卡登录首页")
            return False

    # 登录页 - 显式等待验证是否处于登录页（同时兼容登录入口主页面与手机号/密码表单页）
    def wait_for_login_page(self, timeout: int | float = 2) -> bool:
        """
        显式等待验证当前是否处于登录页面（优先高速入口按钮直查，避免登出回到主页时先跑表单页 XPath 空等 11s）
        :param timeout: 显式等待超时时间 (默认 2s)
        :return: True(处于登录主页面或登录表单页) / False(均未命中)
        """
        logger.info(f"{LogIcon.WAIT} 开始等待确认处于登录页面 (超时: {timeout}s)")
        lookup_condition = "presence" if self._platform_name == "harmonyos" else "visibility"
        fast_timeout = max(0.5, min(1.5, float(timeout)))

        # 1. 优先高速直查登录主入口（鸿蒙走原生 text/HypiumBy 仅 ~0.1s，退出登录后默认即落在此页）
        if self.find_element(
            LoginLocator.LOGIN_ENTRANCE,
            condition=lookup_condition,
            timeout=fast_timeout,
            expect_missing=True,
        ):
            logger.info(f"{LogIcon.SUCCESS} 确认已回到登录主页面（识别到手机号登录入口）")
            return True

        if self.find_element(
            LoginLocator.ONE_KEY_LOGIN_ENTRANCE,
            condition=lookup_condition,
            timeout=0.5,
            expect_missing=True,
        ):
            logger.info(f"{LogIcon.SUCCESS} 确认已回到登录主页面（识别到一键登录入口）")
            return True

        # 2. 次级检测：退出后若直接停在账号密码/手机号表单页
        if self.is_on_phone_login_page(timeout=fast_timeout):
            logger.info(f"{LogIcon.SUCCESS} 确认已处于账号密码/手机号登录表单页")
            return True

        # 3. 最终兜底：弱网或入口按钮尚未渲染时校验顶部 Logo
        if self.find_element(
            LoginLocator.APPLICATION_LOGO,
            condition=lookup_condition,
            timeout=min(1.0, float(timeout)),
            expect_missing=True,
        ):
            logger.info(f"{LogIcon.SUCCESS} 确认已处于登录主页面（识别到应用 Logo）")
            return True

        logger.warning(f"{LogIcon.FAIL} 未能在规定时间内检测到登录主页面或登录表单页")
        return False
    
    # ==========================
    # 跨页面业务流转 (Business Flow)
    # ==========================
    # 登录页 - 退出登录业务流转
    # ==========================
    def logout_if_logged_in(self, wait_toast: bool = True) -> str:
        """
        退出登录业务流转 (对齐最新设置中心退出逻辑)
        :param wait_toast: 是否等待退出登录 Toast（仅 Android 端存在退出 Toast，iOS / 鸿蒙自动跳过轮询避免无效等待）
        """
        from pages.home.home_page import HomePage
        from pages.home.side_slip_page import SideSlipPage
        from pages.home.left_menus.settings_center_page import SettingsCenterPage

        logger.info(f"{LogIcon.ACTION} 开始执行退出登录流转...")
        self._set_cached_password(None)
        HomePage(self.driver).open_left_menu()
        SideSlipPage(self.driver).click_setting()
        should_wait_toast = wait_toast and self._platform_name == "android"
        msg = SettingsCenterPage(self.driver).click_logout_and_get_toast(wait_toast=should_wait_toast)
        return msg

    # 登录页 - 通过像素颜色特征验证登录按钮是否置灰
    def is_login_button_gray(self) -> bool:
        """
        通过按钮元素截图颜色特征判断登录按钮是否处于置灰（未激活）状态。
        登录按钮置灰时不具备原生 enabled 属性变化，统一使用跨平台像素颜色校验。
        :return: True(按钮呈灰色未激活状态) / False(按钮已激活或未定位到按钮)
        """
        lookup_condition = "presence" if self._platform_name == "harmonyos" else "visibility"
        login_btn = self.find_element(LoginLocator.VERIFY_AND_LOGIN_BTN, condition=lookup_condition, timeout=2)
        if not login_btn:
            logger.warning(f"{LogIcon.WARN} 未找到登录按钮，无法校验置灰状态")
            return False
        is_gray = VerifyColor.verify_btn_is_gray(login_btn)
        logger.info(f"{LogIcon.FIND} 登录按钮视觉状态校验: {'置灰(未激活)' if is_gray else '高亮(已激活)'}")
        return is_gray

    # ==========================
    # 验证码登录
    # ==========================
    # 登录页 - 判断是否弹出人机验证弹窗
    def is_human_verification_present(self, timeout: float = 2.0) -> bool:
        """
        跨端判断当前屏幕是否弹出短信验证码人机验证弹窗（Android / iOS / HarmonyOS 统一走 WebView 原生透传节点）。
        """
        return self.is_element_exist(
            LoginLocator.HUMAN_VERIFY_TITLE,
            timeout=timeout,
            condition="presence",
        )

    # 登录页 - 验证码登录人机验证弹窗
    def click_human_verification_button(self, timeout: float = 3.0) -> bool:
        """
        跨端处理验证码登录时出现的人机验证弹窗（Android / iOS / HarmonyOS 统一三层稳健策略）：
        1. 原生 DOM 优先：直接命中各端透传的左侧灰色按钮节点（iOS/鸿蒙走 tap_point 避开 occluded 校验与 5s Idle 等待）；
        2. 次级原生兜底：基于提示文案 Bounds 按真机校准比例 (x - 2.9*h, y + h) 推算左侧按钮圆心，脱离固定像素依赖；
        3. 终极视觉兜底：若特定机型 WebView 未暴露无障碍节点，自动降级至 OCR 偏移点击。
        """
        platform = self._platform_name
        logger.info(f"{LogIcon.SETUP} [{platform}] 处理验证码人机验证弹窗")

        # 1. 原生 DOM 优先：通过 presence 查找，兼容 iOS/鸿蒙 WebView 节点带 occluded="true" 的场景
        verify_btn = self.find_element(
            LoginLocator.HUMAN_VERIFY_BTN,
            timeout=timeout,
            condition="presence",
            expect_missing=True,
        )
        if verify_btn:
            # 短暂等待弹窗入场动画稳定，防止坐标偏移
            time.sleep(0.3)
            logger.info(f"{LogIcon.SUCCESS} [{platform}] 命中原生人机验证按钮，执行点击")
            if platform in ("ios", "harmonyos"):
                # iOS 节点常带 occluded="true"、鸿蒙原生 click 易触发 5s Idle，均优先走元素中心坐标手势点击
                self.tap_point(click_elem=verify_btn, duration=80)
            else:
                try:
                    verify_btn.click()
                except Exception as err:
                    logger.warning(f"{LogIcon.WARN} [{platform}] 原生 click 失败，改用元素中心坐标点击: {err}")
                    self.tap_point(click_elem=verify_btn, duration=80)
            time.sleep(0.8)
            return True

        # 2. 次级原生兜底：基于第一行提示文案的 Bounds 推算左侧圆形按钮圆心
        # 左侧按钮与右侧两行文案垂直居中，故圆心约位于 (title.x - 2.9 * title.h, title.y + title.h)
        title_elem = self.find_element(
            LoginLocator.HUMAN_VERIFY_TITLE,
            timeout=0.5,
            condition="presence",
            expect_missing=True,
        )
        if title_elem:
            rect = title_elem.rect
            if rect and rect.get("height", 0) > 0:
                click_x = max(10, int(rect["x"] - rect["height"] * 2.9))
                click_y = int(rect["y"] + rect["height"])
                logger.info(
                    f"{LogIcon.ACTION} [{platform}] 通过提示文案坐标动态推算验证按钮: ({click_x}, {click_y})"
                )
                self.tap_point(x=click_x, y=click_y, duration=80)
                time.sleep(0.8)
                return True

        # 3. 终极兜底：若目标机型 WebView 未暴露无障碍节点，降级至 OCR 偏移点击
        logger.warning(f"{LogIcon.WARN} [{platform}] 未检测到原生人机验证节点，降级使用 OCR 视觉偏移兜底")
        return self.ocrUtils.click_text_with_offset(
            target_text="请点击按钮进行验证",
            offset_x=-85,
            offset_y=10,
            image_name="human_verification.png",
        )

    # 登录页 - 关闭人机验证弹窗
    def close_human_verification_dialog(self, timeout: float = 2.0) -> bool:
        """跨端点击人机验证弹窗上的关闭按钮（Android / iOS / HarmonyOS）"""
        platform = self._platform_name
        close_btn = self.find_element(
            LoginLocator.HUMAN_VERIFY_CLOSE_BTN,
            timeout=timeout,
            condition="presence",
            expect_missing=True,
        )
        if not close_btn:
            logger.warning(f"{LogIcon.WARN} [{platform}] 未找到人机验证关闭按钮")
            return False
        logger.info(f"{LogIcon.ACTION} [{platform}] 点击关闭人机验证弹窗")
        if platform == "harmonyos":
            self.tap_point(click_elem=close_btn, duration=80)
        else:
            try:
                close_btn.click()
            except Exception as err:
                logger.warning(f"{LogIcon.WARN} [{platform}] 关闭按钮 click 失败，改用坐标点击: {err}")
                self.tap_point(click_elem=close_btn, duration=80)
        return True

    # 登录页 - 刷新人机验证弹窗
    def refresh_human_verification_dialog(self, timeout: float = 2.0) -> bool:
        """跨端点击人机验证弹窗上的刷新按钮（Android / iOS / HarmonyOS）"""
        platform = self._platform_name
        refresh_btn = self.find_element(
            LoginLocator.HUMAN_VERIFY_REFRESH_BTN,
            timeout=timeout,
            condition="presence",
            expect_missing=True,
        )
        if not refresh_btn:
            logger.warning(f"{LogIcon.WARN} [{platform}] 未找到人机验证刷新按钮")
            return False
        logger.info(f"{LogIcon.ACTION} [{platform}] 点击刷新人机验证弹窗")
        if platform == "harmonyos":
            self.tap_point(click_elem=refresh_btn, duration=80)
        else:
            try:
                refresh_btn.click()
            except Exception as err:
                logger.warning(f"{LogIcon.WARN} [{platform}] 刷新按钮 click 失败，改用坐标点击: {err}")
                self.tap_point(click_elem=refresh_btn, duration=80)
        return True
    
    # 登录页 - 稳健版输入分离式验证码
    def input_verify_code_robust(self, code: str) -> None:
        """
        输入分离式验证码：
        - HarmonyOS：单次点击首格聚焦后，纯数字验证码直接下发原生按键事件 (NUM_0=2000..NUM_9=2009)，
          规避逐格 XpathWidget 剪贴板粘贴耗时长达 7~8s 的性能瓶颈（压缩至 <1s）；
        - iOS：按横坐标排序锁定首格后，直接调用首格 send_keys(code)（底层走全系 iPhone 通用的 WDA FBTypeText
          60Hz 系统键盘事件流，自动顺次跳格，1 次请求完成全部输入，避免 iPadOS 专属 mobile: keys 静默失效）；
        - Android：保持逐格点击并输入的稳健逻辑。
        :param code: 验证码字符串，如 "9999"
        """
        logger.info(f"{LogIcon.ACTION} 准备输入验证码: {code}")
        if not code:
            return

        lookup_condition = "presence" if self._platform_name == "harmonyos" else "visibility"
        # 1. 找到这 4 个输入框
        edit_texts = self.find_elements(LoginLocator.CODE_EDIT_TEXTS, condition=lookup_condition, timeout=2)
        if not edit_texts:
            raise RuntimeError("❌ 未找到验证码输入框！")

        # 2. 校验框的数量和验证码长度是否匹配 (通常是 4 位或 6 位)
        if len(edit_texts) != len(code):
            logger.warning(f"{LogIcon.WARN} 验证码长度({len(code)})与输入框数量({len(edit_texts)})不一致！")

        # 3. 鸿蒙极速路径：聚焦首格一次 + 原生数字键直打（省去 4 轮剪贴板粘贴与重复点击）
        if self._platform_name == "harmonyos" and code.isdigit():
            self.tap_point(click_elem=edit_texts[0], duration=60)
            for i, digit in enumerate(code, 1):
                logger.info(f"{LogIcon.SETUP} [HarmonyOS] 原生按键输入第 {i} 位验证码: {digit}")
                self.driver.execute_script("mobile: pressKey", {"keycode": 2000 + int(digit)})
            return

        # 4. iOS 极速稳健路径：按缓存横坐标从左到右排序，单次 send_keys 整串 60Hz 键入并自动跳格
        if self._platform_name == "ios":
            if all(isinstance(getattr(el, "_ios_cached_rect", None), dict) for el in edit_texts):
                edit_texts = sorted(edit_texts, key=lambda el: float(el._ios_cached_rect.get("x", 0.0)))
            logger.info(f"{LogIcon.SETUP} [iOS] 首格单次整串输入验证码: {code}")
            edit_texts[0].send_keys(code)
            return

        # 5. Android 逐格输入路径
        for i, digit in enumerate(code):
            if i < len(edit_texts):
                try:
                    logger.info(f"{LogIcon.SETUP} 点击并输入第 {i+1} 个验证码字符: {digit}")
                    edit_texts[i].click()
                    edit_texts[i].send_keys(digit)
                    if i < len(code) - 1:
                        time.sleep(0.2)
                except Exception as e:
                    logger.error(f"{LogIcon.FAIL} 输入第 {i+1} 个验证码字符时失败: {e}")
                    raise
