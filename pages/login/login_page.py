import time
from common.base_page import BasePage
from locators.login.login_locator import LoginLocator
from core.logger_utils import logger
from business_helpers.verify_color import VerifyColor
from pages.common.common_page import CommonPage
from selenium.common.exceptions import TimeoutException
from utils.cv_recognition.ocr_utils import OcrUtils

class LoginPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver)
        self.commonPage = CommonPage(driver)
        self.ocrUtils = OcrUtils(driver)

    # ==========================
    # 顶部导航类操作
    # ==========================
    def click_back_btn(self):
        """点击界面左上角的返回按钮"""
        self.click(LoginLocator.TOP_IV_BACK_BTN)
        logger.info("点击了左上角返回按钮")

    # 获取顶部标题（手机号，密码，一键登录）
    def get_top_title(self) -> str:
        """登录功能 获取页面 top 标题:"""
        title = self.commonPage.get_top_middle_title()
        logger.info(f"login 获取页面 top 标题: {title}")
        return title

    # ==========================
    # 核心入口与模式切换
    # ==========================
    def click_phone_login_button(self):
        """如果在启动页，点击进入‘手机号登录’界面的按钮"""
        self.click(LoginLocator.LOGIN_ENTRANCE)
        logger.info("点击进入了手机号登录主界面")
    
    def click_one_click_login_button(self):
        """点击一键登录按钮"""
        self.click(LoginLocator.ONE_KEY_LOGIN_ENTRANCE, force_wait=True)
        logger.info("点击了一键登录按钮")

    def click_password_login_button(self):
        """点击‘密码登录’，如果当前是验证码等其他模式则切换"""
        pass_elem = self.find_element(LoginLocator.PASSWORD_LOGIN_SWITCH, timeout=2)
        pwd_elem = self.get_password_element(expect_missing=True)
        if pass_elem and not pwd_elem:
            pass_elem.click()
            logger.info("切换到了密码登录模式")
            time.sleep(0.5)

    def click_code_login_button(self):
        """点击‘验证码登录’，切换到验证码模式"""
        code_elem = self.find_element(LoginLocator.CODE_LOGIN_SWITCH, timeout=2)
        pwd_elem = self.get_password_element()
        if code_elem and pwd_elem:
            code_elem.click()
            logger.info("切换到了验证码登录模式")
            time.sleep(1)

    # ==========================
    # 账号/密码输入类操作
    # ==========================
    def clear_phone(self):
        """清空手机号输入框内容 (使用 element.clear())"""
        elem = self.find_element(LoginLocator.PHONE_NUMBER_EDIT, timeout=2)
        if elem:
            elem.clear()
            logger.info("已清空手机号输入框")

    def input_account(self, phone: str):
        """在手机号/账号输入框中输入内容"""
        self.clear_phone()
        self.send_keys(LoginLocator.PHONE_NUMBER_EDIT, phone)
        logger.info(f"输入了账号/手机号: {phone}")
    
    def get_phone_number(self):
        """获取手机号输入框中的内容"""
        phone_number = self.get_attribute(LoginLocator.PHONE_NUMBER_EDIT, "text")
        logger.info(f"获取手机号: {phone_number}")
        return phone_number

    def clear_phone_number(self):
        """点击手机号输入框右侧的 (x) 图标，一键清空内容"""
        if self.is_element_exist(LoginLocator.CLEAR_PHONE_NUMBER, timeout=2):
            self.click(LoginLocator.CLEAR_PHONE_NUMBER)
            logger.info("一键清空了当前输入的手机号")

    def clear_password(self):
        """清空密码输入框内容 (使用 element.clear())"""
        elem = self.find_element(LoginLocator.PASSWORD_EDIT, timeout=2)
        if elem:
            elem.clear()
            logger.info("已清空密码输入框")

    def input_password(self, password: str):
        """在密码输入框中输入内容"""
        self.clear_password()
        self.send_keys(LoginLocator.PASSWORD_EDIT, password)
        logger.info(f"输入了登录密码: {password}")
    
    def get_password(self):
        """获取密码输入框中的内容"""
        password = self.get_attribute(LoginLocator.PASSWORD_EDIT, "text")
        logger.info(f"获取密码: {password}")
        return password
    
    # 获取密码元素
    def get_password_element(self, expect_missing=False):
        """获取密码输入框元素"""
        elem = self.find_element(LoginLocator.PASSWORD_EDIT, timeout=2, expect_missing=expect_missing)
        logger.info("获取密码输入框元素")
        return elem

    def click_password_visible_btn(self):
        """点击密码输入框右侧的‘眼睛’图标，切换密码明文/密文显示状态"""
        self.click(LoginLocator.PASSWORD_VISIBLE_BTN)
        logger.info("切换了密码的可见状态")
    
    # 获取登录模块 Toast
    def get_login_toast_message(self):
        """获取 login 到 Toast 消息"""
        toast_message = self.commonPage.get_toast_message_common()
        logger.info(f"获取 login 到 Toast 消息: {toast_message}")
        return toast_message
    
    # 获取验证码倒计时 text
    def get_verification_code_countdown_text(self):
        """获取验证码倒计时文本"""
        countdown_text = self.get_attribute(LoginLocator.VERIFICATION_CODE_COUNTDOWN, "text")
        logger.info(f"获取验证码倒计时: {countdown_text}")
        return countdown_text

    # 判断是否在验证码页面
    def is_on_verification_login_page(self, timeout: int = 2) -> bool:
        """
        判断当前是否处于验证码登录页面
        :param timeout: 超时时间
        :return: True(在验证码登录页面) / False(不在验证码登录页面)
        """
        return self.is_element_exist(LoginLocator.PLEASE_ENTER_VERIFICATION_CODE, timeout=timeout, condition="visibility")

    # ==========================
    # 协议与底层弹窗操作
    # ==========================
    def click_user_agreement(self):
        """检查登录页面的底部的协议复选框是否勾选，未勾选则点击"""
        agren_elem = self.find_element(LoginLocator.AGREE_AND_LOGIN_BTN, timeout=2)
        if agren_elem:
            if not VerifyColor.verify_agree_btn(agren_elem):
                self.click(LoginLocator.AGREE_AND_LOGIN_BTN)
                logger.info("点击用户协议复选框")
    
    # 取消勾选用户协议
    def cancel_user_agreement(self):
        """检查登录页面的底部的协议复选框是否勾选，已勾选则取消勾选"""
        agren_elem = self.find_element(LoginLocator.AGREE_AND_LOGIN_BTN, timeout=2)
        if agren_elem:
            if VerifyColor.verify_agree_btn(agren_elem):
                self.click(LoginLocator.AGREE_AND_LOGIN_BTN)
                logger.info("取消勾选用户协议")

    def click_handle_agreement_popup(self):
        """处理因‘未勾选协议点击登录’而弹出的‘用户协议及隐私政策’底层弹窗，点击‘同意并继续’"""
        bottom_aggree_btn = self.find_element(LoginLocator.AGREE_AND_CONTINUE_BTN, timeout=3)
        if bottom_aggree_btn:
            bottom_aggree_btn.click()
            logger.info("处理了隐私政策拦截弹窗，点击了‘同意并继续’")

    def close_agreement_popup(self):
        """点击底层隐私协议弹窗右上角的 (X) 关闭按钮"""
        close_btn = self.find_element(LoginLocator.CLOSE_BTN, timeout=2)
        if close_btn:
            close_btn.click()
            logger.info("关闭了‘用户协议及隐私政策’底层弹窗")
    
    def get_agreement_popup_title(self):
        """ 获取‘用户协议及隐私政策’底层弹窗的标题 """
        title = self.commonPage.get_top_middle_title()
        logger.info(f"未勾选同意，点击登录后，获取到隐私弹窗标题: {title}")
        return title
    
    def get_agreement_text(self):
        """获取登录页面底部的协议文本"""
        text = self.get_attribute(LoginLocator.AGREE_AND_LOGIN_TEXT, "text")
        logger.info(f"获取到登录页面底部的协议文本: {text}")
        return text

    # ==========================
    # 登录提交与校验
    # ==========================
    def click_login_button(self):
        """执行最终的‘登录’或‘验证并登录’按钮点击动作"""
        self.click(LoginLocator.VERIFY_AND_LOGIN_BTN)
        logger.info("点击了 [验证并登录/登录] 按钮")
        
    def click_feedback_btn(self):
        """点击‘遇到问题？点击反馈’按钮"""
        self.click(LoginLocator.FEEDBACK_BTN)
        logger.info("点击了登录反馈求助按钮")

    def is_login_success(self) -> bool:
        """
        根据是否能找到主页特有元素判断登录是否成功
        """
        from pages.home.home_page import HomePage
        title = HomePage(self.driver).get_top_middle_title()
        if '三条' in title:
            logger.info(f"登录成功，获取到主页标题: {title}")
            return True
        else:
            logger.info(f"登录失败，获取到主页标题: {title}")
            return False

    def get_toast_text(self, timeout=3, expected_toast="") -> str:
        """
        获取页面弹出的系统级 Toast 或普通 TextView 错误提示。
        如果参数带有 expected_toast 预期文本，则开启预期文本驱动的全屏搜索，极大提升各类弹窗和红字提示的捕获率。
        """
        logger.info(f"⏳ 开始监听提示 (超时: {timeout}s | 优先内容: '{expected_toast}')")

        end_time = time.time() + timeout
        while time.time() < end_time:
            # 1. 优先级策略：如果提供了预期文本，强制执行全屏模糊文本匹配
            if expected_toast:
                dynamic_locator = LoginLocator.get_dynamic_toast_msg(expected_toast)
                toast = self.find_element(dynamic_locator, timeout=0.2, condition="presence", expect_missing=True)
                if toast:
                    text = toast.get_attribute("text")
                    logger.info(f"✅ 通过 文本匹配 命中业务提示 Toast: {text}")
                    return text

            # 2. 匹配通用 Toast ID
            toast = self.find_element(LoginLocator.TOAST_MSG, timeout=0.2, condition="presence", expect_missing=True)
            if toast:
                text = toast.get_attribute("text")
                if text and text != '登录中...':
                    logger.info(f"✅ 通过 ID 命中业务提示 Toast: {text}")
                    return text
            time.sleep(0.05)
        logger.warning(f"❌ 监听结束，在 {timeout}s 内未捕获到任何符合条件的提示内容 - 实际获取到的Toast: {text}")
        return ""

    # 验证是否处于登录页
    def wait_for_login_page(self, timeout=10) -> bool:
        """显式等待验证是否处于登录页"""
        logger.info(f"⏳ 开始等待返回登录页面 (超时: {timeout}s)")
        # 这里用登录按钮或者手机号输入框作为登录页面的标志
        elem = self.find_element(LoginLocator.VERIFY_AND_LOGIN_BTN, timeout=timeout)
        if elem:
            logger.info("✅ 成功回到登录页面")
            return True
        else:
            logger.warning("❌ 未能在规定时间内返回登录页面")
            return False
    
    # ==========================
    # 跨页面业务流转 (Business Flow)
    # ==========================
    def logout_if_logged_in(self) -> str:
        """
        退出登录业务流转
        """
        from pages.home.home_page import HomePage
        from pages.home.side_slip_page import SideSlipPage
        from pages.left_menus.account_security_page import AccountSecurityPage

        logger.info("👉 开始执行退出登录流转...")
        HomePage(self.driver).open_left_menu()
        SideSlipPage(self.driver).click_security()
        msg = AccountSecurityPage(self.driver).click_logout_and_get_toast()
        return msg

    # 验证登录按钮是否置灰
    def is_login_button_enabled(self) -> bool:
        """ 验证登录按钮是否有效（未置灰） """
        login_btn = self.find_element(LoginLocator.VERIFY_AND_LOGIN_BTN, timeout=2)
        if login_btn:
            is_enabled = login_btn.is_enabled()
            if is_enabled:
                logger.info("登录按钮处于置灰状态")
                return True
            else:
                logger.info("登录按钮处于激活状态（未置灰）")
                return False
        else:
            logger.warning("未找到登录按钮")
            return False

    # ==========================
    # 验证码登录
    # ==========================
    # 验证码登录人机验证弹窗
    def click_human_verification_button(self) -> bool:
        """ 处理验证码登录时出现的人机验证拖动/点击滑块 """
        time.sleep(2)  # 等待弹窗和滑块动画渲染
        return self.ocrUtils.click_text_with_offset(
            target_text="请点击按钮进行验证",
            offset_x=-85,
            offset_y=10,
            image_name="human_verification.png"
        )
    
    def input_verify_code_robust(self, code: str):
        """
        输入分离式验证码（稳健版：逐个框输入）
        :param code: 验证码字符串，如 "1234"
        """
        logger.info(f"👉 准备输入验证码: {code}")
        
        # 1. 找到这 4 个输入框
        edit_texts = self.find_elements(LoginLocator.CODE_EDIT_TEXTS, timeout=3)
        if not edit_texts:
            raise RuntimeError("❌ 未找到验证码输入框！")
            
        # 2. 校验框的数量和验证码长度是否匹配 (通常是 4 位或 6 位)
        if len(edit_texts) != len(code):
            logger.warning(f"⚠️ 验证码长度({len(code)})与输入框数量({len(edit_texts)})不一致！")

        # 3. 逐个提取字符并输入
        for i, digit in enumerate(code):
            if i < len(edit_texts):
                try:
                    edit_texts[i].click() 
                    edit_texts[i].send_keys(digit)
                    logger.debug(f"已输入第 {i+1} 个数字: {digit}")
                    time.sleep(0.2) 
                except Exception as e:
                    logger.error(f"❌ 输入第 {i+1} 个验证码字符时失败: {e}")









