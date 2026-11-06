import time
from typing import Optional
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException
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

    # ==========================
    # 页面状态检测
    # ==========================
    # 登录页 - 检测当前是否处于登录主页面
    def is_on_login_main_page(self, timeout: int = 2) -> bool:
        """
        检测当前是否处于登录主页面 (通过 APPLICATION_LOGO 进行核心检测与状态断言优化)
        :param timeout: 显式等待超时时间 (默认 2s)
        :return: True(当前处于登录主页面) / False(不在登录主页面)
        """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 检测当前是否处于登录主页面 (Logo: APPLICATION_LOGO, 超时: {timeout}s)")
        # 1. 核心特征判定：页面顶部标志性的应用主 Logo (支持 Android / HarmonyOS 跨端动态代理)
        logo_elem = self.find_element(LoginLocator.APPLICATION_LOGO, timeout=timeout)
        if logo_elem and logo_elem.is_displayed():
            logger.info(f"{LogIcon.SUCCESS} [Action - Login] 成功识别到应用 Logo 元素，当前处于登录主页面")
            return True

        # 2. 状态兜底：若弱网或转场动画未完成，交叉验证登录主入口 (手机号登录/一键登录)
        entrance = self.find_element(LoginLocator.LOGIN_ENTRANCE, timeout=1) or self.find_element(LoginLocator.ONE_KEY_LOGIN_ENTRANCE, timeout=1)
        if entrance and entrance.is_displayed():
            logger.info(f"{LogIcon.SUCCESS} [Action - Login] 辅助识别到登录主入口按钮，确认处于登录主页面")
            return True

        logger.warning(f"{LogIcon.FAIL} [Action - Login] 未能检测到应用 Logo 及登录主入口，当前不处于登录主页面")
        return False
    


    # ==========================
    # 顶部导航类操作
    # ==========================
    # 登录页 - 点击界面左上角返回按钮
    def click_back_btn(self) -> None:
        """ 点击界面左上角的返回按钮 """
        logger.info(f"{LogIcon.SETUP} 点击左上角返回按钮")
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
        """ 如果在启动页，点击进入‘手机号登录’界面的按钮 """
        logger.info(f"{LogIcon.SETUP} 点击进入手机号登录主界面")
        self.click(LoginLocator.LOGIN_ENTRANCE)
    
    # 登录页 - 点击一键登录按钮
    def click_one_click_login_button(self) -> None:
        """ 点击一键登录按钮 """
        logger.info(f"{LogIcon.SETUP} 点击一键登录按钮")
        self.click(LoginLocator.ONE_KEY_LOGIN_ENTRANCE, force_wait=True)

    # 登录页 - 切换到密码登录模式
    def click_password_login_button(self) -> None:
        """ 点击‘密码登录’，如果当前是验证码等其他模式则切换 """
        logger.info(f"{LogIcon.SETUP} 检查并尝试切换到密码登录模式")
        pass_elem = self.find_element(LoginLocator.PASSWORD_LOGIN_SWITCH, timeout=2)
        pwd_elem = self.get_password_element(expect_missing=True)
        if pass_elem and not pwd_elem:
            logger.info(f"{LogIcon.SETUP} 执行切换到密码登录模式")
            pass_elem.click()
            time.sleep(0.5)

    # 登录页 - 切换到验证码登录模式
    def click_code_login_button(self) -> None:
        """ 点击‘验证码登录’，切换到验证码模式 """
        logger.info(f"{LogIcon.SETUP} 检查并尝试切换到验证码登录模式")
        code_elem = self.find_element(LoginLocator.CODE_LOGIN_SWITCH, timeout=2)
        pwd_elem = self.get_password_element()
        if code_elem and pwd_elem:
            logger.info(f"{LogIcon.SETUP} 执行切换到验证码登录模式")
            code_elem.click()
            time.sleep(1)

    # ==========================
    # 账号/密码输入类操作
    # ==========================
    # 登录页 - 清空手机号输入框内容
    def clear_phone(self) -> None:
        """ 清空手机号输入框内容 (使用 element.clear()) """
        logger.info(f"{LogIcon.SETUP} 准备清空手机号输入框")
        elem = self.find_element(LoginLocator.PHONE_NUMBER_EDIT, timeout=2)
        if elem:
            logger.info(f"{LogIcon.SETUP} 执行清空手机号输入框")
            elem.clear()

    # 登录页 - 输入手机号或账号
    def input_account(self, phone: str) -> None:
        """ 在手机号/账号输入框中输入内容 """
        logger.info(f"{LogIcon.SETUP} 输入账号/手机号: {phone}")
        self.clear_phone()
        self.send_keys(LoginLocator.PHONE_NUMBER_EDIT, phone)
    
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

    # 登录页 - 清空密码输入框内容
    def clear_password(self) -> None:
        """ 清空密码输入框内容 (使用 element.clear()) """
        logger.info(f"{LogIcon.SETUP} 准备清空密码输入框")
        elem = self.find_element(LoginLocator.PASSWORD_EDIT, timeout=2)
        if elem:
            logger.info(f"{LogIcon.SETUP} 执行清空密码输入框")
            elem.clear()

    # 登录页 - 输入密码
    def input_password(self, password: str) -> None:
        """ 在密码输入框中输入内容 """
        logger.info(f"{LogIcon.SETUP} 输入登录密码: {password}")
        self.clear_password()
        self.send_keys(LoginLocator.PASSWORD_EDIT, password)
    
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
        countdown_text = self.get_attribute(LoginLocator.VERIFICATION_CODE_COUNTDOWN, "text")
        logger.info(f"{LogIcon.WAIT} 🧐 [Action - Login] 获取验证码倒计时: {countdown_text}")
        return countdown_text

    # 登录页 - 判断是否在验证码登录页面
    def is_on_verification_login_page(self, timeout: int = 2) -> bool:
        """
        判断当前是否处于验证码登录页面
        :param timeout: 超时时间
        :return: True(在验证码登录页面) / False(不在验证码登录页面)
        """
        logger.info(f"{LogIcon.WAIT} 🧐 [Action - Login] 判断当前是否处于验证码登录页面 (超时: {timeout}s)")
        return self.is_element_exist(LoginLocator.PLEASE_ENTER_VERIFICATION_CODE, timeout=timeout, condition="visibility")

    # ==========================
    # 协议与底层弹窗操作
    # ==========================
    # 登录页 - 勾选用户协议
    def click_user_agreement(self) -> None:
        """ 检查登录页面的底部的协议复选框是否勾选，未勾选则点击 """
        logger.info(f"{LogIcon.SETUP} 检查用户协议勾选状态")
        agren_elem = self.find_element(LoginLocator.AGREE_AND_LOGIN_BTN, timeout=2)
        if agren_elem:
            if not VerifyColor.verify_agree_btn(agren_elem):
                logger.info(f"{LogIcon.SETUP} 执行勾选用户协议复选框")
                self.click(LoginLocator.AGREE_AND_LOGIN_BTN)
    
    # 登录页 - 取消勾选用户协议
    def cancel_user_agreement(self) -> None:
        """ 检查登录页面的底部的协议复选框是否勾选，已勾选则取消勾选 """
        logger.info(f"{LogIcon.SETUP} 检查用户协议勾选状态以取消勾选")
        agren_elem = self.find_element(LoginLocator.AGREE_AND_LOGIN_BTN, timeout=2)
        if agren_elem:
            if VerifyColor.verify_agree_btn(agren_elem):
                logger.info(f"{LogIcon.SETUP} 执行取消勾选用户协议")
                self.click(LoginLocator.AGREE_AND_LOGIN_BTN)

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
        """ 获取‘用户协议及隐私政策’底层弹窗的标题 """
        title = self.commonPage.get_top_middle_title()
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 未勾选同意点击登录后，获取到隐私弹窗标题: {title}")
        return title
    
    # 登录页 - 获取协议文本
    def get_agreement_text(self) -> str:
        """ 获取登录页面底部的协议文本 """
        text = self.get_attribute(LoginLocator.AGREE_AND_LOGIN_TEXT, "text")
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Login] 获取到登录页面底部的协议文本: {text}")
        return text

    # ==========================
    # 登录提交与校验
    # ==========================
    # 登录页 - 自动处理系统保存密码弹窗
    def handle_save_password_popup(self, timeout: float = 10) -> bool:
        """
        自动检测并消除系统级‘自动保存账号密码’弹窗 (MIUI/HyperOS)
        """
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
            self.handle_save_password_popup(timeout=5)
        
    # 登录页 - 点击遇到问题反馈
    def click_feedback_btn(self) -> None:
        """ 点击‘遇到问题？点击反馈’按钮 """
        logger.info(f"{LogIcon.SETUP} 点击遇到问题反馈求助按钮")
        self.click(LoginLocator.FEEDBACK_BTN)

    # 登录页 - 判断登录是否成功
    def is_login_success(self) -> bool:
        """ 根据是否能找到主页特有元素判断登录是否成功 """
        from pages.home.home_page import HomePage
        title = HomePage(self.driver).get_top_middle_title()
        if '三条' in title:
            logger.info(f"{LogIcon.SUCCESS} 登录成功，获取到主页标题: {title}")
            return True
        else:
            logger.info(f"{LogIcon.FAIL} 登录未成功，获取到主页标题: {title}")
            return False

    # 登录页 - 获取 Toast 提示
    def get_toast_text(self, timeout: float = 3.0, expected_toast: str = "") -> str:
        """
        获取页面弹出的系统级 Toast 或普通 TextView 错误提示。
        如果参数带有 expected_toast 预期文本，则开启预期文本驱动的全屏搜索，极大提升各类弹窗和红字提示的捕获率。
        """
        logger.info(f"{LogIcon.WAIT} 开始监听提示 (超时: {timeout}s | 优先内容: '{expected_toast}')")

        end_time = time.time() + timeout
        text = ""
        while time.time() < end_time:
            # 1. 优先级策略：如果提供了预期文本，强制执行全屏模糊文本匹配
            if expected_toast:
                dynamic_locator = LoginLocator.get_dynamic_toast_msg(expected_toast)
                toast = self.find_element(dynamic_locator, timeout=0.2, condition="presence", expect_missing=True)
                if toast:
                    text = toast.get_attribute("text")
                    logger.info(f"{LogIcon.SUCCESS} 通过文本匹配命中业务提示 Toast: {text}")
                    return text

            # 2. 匹配通用 Toast ID
            toast = self.find_element(LoginLocator.TOAST_MSG, timeout=0.2, condition="presence", expect_missing=True)
            if toast:
                text = toast.get_attribute("text")
                if text and text != ToastMsg.LOGGING_IN:
                    logger.info(f"{LogIcon.SUCCESS} 通过 ID 命中业务提示 Toast: {text}")
                    return text
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

    # 登录页 - 显式等待验证是否处于登录主页面
    def wait_for_login_page(self, timeout: int = 10) -> bool:
        """ 显式等待验证是否处于登录主页面 (通过 APPLICATION_LOGO 进行检测优化) """
        logger.info(f"{LogIcon.WAIT} 开始等待返回登录主页面 (超时: {timeout}s)")
        elem = self.is_on_login_main_page(timeout=timeout)
        if elem:
            logger.info(f"{LogIcon.SUCCESS} 成功回到登录主页面")
            return True
        else:
            logger.warning(f"{LogIcon.FAIL} 未能在规定时间内返回登录主页面")
            return False
    
    # ==========================
    # 跨页面业务流转 (Business Flow)
    # ==========================
    # 登录页 - 退出登录业务流转
    # ==========================
    def logout_if_logged_in(self) -> str:
        """ 退出登录业务流转 (对齐最新设置中心退出逻辑) """
        from pages.home.home_page import HomePage
        from pages.home.side_slip_page import SideSlipPage
        from pages.home.left_menus.settings_center_page import SettingsCenterPage

        logger.info(f"{LogIcon.ACTION} 开始执行退出登录流转...")
        HomePage(self.driver).open_left_menu()
        SideSlipPage(self.driver).click_setting()
        msg = SettingsCenterPage(self.driver).click_logout_and_get_toast()
        return msg

    # 登录页 - 验证登录按钮是否置灰
    def is_login_button_enabled(self) -> bool:
        """ 验证登录按钮是否有效（未置灰） """
        login_btn = self.find_element(LoginLocator.VERIFY_AND_LOGIN_BTN, timeout=2)
        if login_btn:
            is_enabled = login_btn.is_enabled()
            if is_enabled:
                logger.info(f"{LogIcon.SETUP} 登录按钮处于置灰状态")
                return True
            else:
                logger.info(f"{LogIcon.SETUP} 登录按钮处于激活状态（未置灰）")
                return False
        else:
            logger.warning(f"{LogIcon.WARN} 未找到登录按钮")
            return False

    # ==========================
    # 验证码登录
    # ==========================
    # 登录页 - 验证码登录人机验证弹窗
    def click_human_verification_button(self) -> bool:
        """ 处理验证码登录时出现的人机验证拖动/点击滑块 """
        logger.info(f"{LogIcon.SETUP} 处理验证码人机验证弹窗")
        time.sleep(2)  # 等待弹窗和滑块动画渲染
        return self.ocrUtils.click_text_with_offset(
            target_text="请点击按钮进行验证",
            offset_x=-85,
            offset_y=10,
            image_name="human_verification.png"
        )
    
    # 登录页 - 稳健版输入分离式验证码
    def input_verify_code_robust(self, code: str) -> None:
        """
        输入分离式验证码（稳健版：逐个框输入）
        :param code: 验证码字符串，如 "1234"
        """
        logger.info(f"{LogIcon.ACTION} 准备输入验证码: {code}")
        
        # 1. 找到这 4 个输入框
        edit_texts = self.find_elements(LoginLocator.CODE_EDIT_TEXTS, timeout=3)
        if not edit_texts:
            raise RuntimeError("❌ 未找到验证码输入框！")
            
        # 2. 校验框的数量和验证码长度是否匹配 (通常是 4 位或 6 位)
        if len(edit_texts) != len(code):
            logger.warning(f"{LogIcon.WARN} 验证码长度({len(code)})与输入框数量({len(edit_texts)})不一致！")

        # 3. 逐个提取字符并输入
        for i, digit in enumerate(code):
            if i < len(edit_texts):
                try:
                    logger.info(f"{LogIcon.SETUP} 点击并输入第 {i+1} 个验证码字符: {digit}")
                    edit_texts[i].click() 
                    edit_texts[i].send_keys(digit)
                    time.sleep(0.2) 
                except Exception as e:
                    logger.error(f"{LogIcon.FAIL} 输入第 {i+1} 个验证码字符时失败: {e}")
