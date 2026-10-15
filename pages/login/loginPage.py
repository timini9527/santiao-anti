from selenium.webdriver.common.by import By
from common.base_page import BasePage
from core.logger_utils import logger, LogIcon


# 登录页面封装
class LoginPage(BasePage):
    """登录页面对象"""

    # 元素定位器
    LOGIN_ENTRY = (By.ID, 'tv_login')
    CHECKBOX = (By.ID, 'agreement_checkbox')
    ACCOUNT_FIELD = (By.ID, 'account_edit')
    PWD_FIELD = (By.ID, 'pwd_edit')
    LOGIN_BTN = (By.ID, 'login_btn')
    IS_SHOW_PWD = (By.ID, 'iv_show_pass')

    ONE_CLICK_LOGIN = (By.ID, 'tv_one_click_login')  # 一键登录
    SMS_LOGIN = (By.ID, 'tv_sms_login')  # 短信登录
    ET_CODE = (By.ID, 'et_code')

    # 登录页 - 点击登录入口（若存在）
    def click_login_entry_if_exists(self) -> bool:
        """ 尝试点击登录入口按钮进入登录页 """
        logger.info(f"{LogIcon.SETUP} 尝试点击登录入口按钮")
        try:
            self.click(self.LOGIN_ENTRY)
            logger.info(f"{LogIcon.SUCCESS} 已成功点击登录入口")
            return True
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} 点击登录入口失败或已在登录页: {e}")
            return False  # 如果已经在登录页则忽略

    # 登录页 - 勾选用户协议
    def agree_protocol(self) -> None:
        """ 获取勾选状态，若未勾选则点击同意用户协议 """
        logger.info(f"{LogIcon.SETUP} 检查并勾选用户协议")
        if self.get_attribute(self.CHECKBOX, 'checked') == 'false':
            logger.info(f"{LogIcon.SETUP} 协议未勾选，执行点击勾选")
            self.click(self.CHECKBOX)

    # 登录页 - 切换显示密码明文
    def show_pwd(self) -> None:
        """ 显示密码，切换密文明文状态 """
        logger.info(f"{LogIcon.SETUP} 检查密码显示状态")
        if self.get_attribute(self.PWD_FIELD, 'password'):
            logger.info(f"{LogIcon.SETUP} 点击切换为明文显示密码")
            self.click(self.IS_SHOW_PWD)

    # 登录页 - 账号密码登录完整流程
    def login(self, username: str, password: str) -> None:
        """ 执行账号密码登录完整流程 """
        logger.info(f"{LogIcon.SETUP} 开始登录流程，账号: {username}")
        logger.info(f"{LogIcon.SETUP} 输入账号")
        self.send_keys(self.ACCOUNT_FIELD, username)
        logger.info(f"{LogIcon.SETUP} 输入密码")
        self.send_keys(self.PWD_FIELD, password)
        self.show_pwd()
        self.agree_protocol()
        logger.info(f"{LogIcon.SETUP} 点击登录按钮")
        self.click(self.LOGIN_BTN)

    # 登录页 - 检查是否仍处于登录页面
    def is_login_page_status(self) -> bool:
        """ 检查当前是否仍处于登录页面 """
        logger.info(f"{LogIcon.SETUP} 检查当前页面是否仍在登录页面")
        page_status = self.find_element(self.LOGIN_BTN, timeout=2, expect_missing=True)
        if page_status is not None:
            logger.info(f"{LogIcon.SUCCESS} 当前仍处于登录页面")
            return True
        else:
            logger.info(f"{LogIcon.SUCCESS} 当前已离开登录页面")
            return False