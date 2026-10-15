import time
from selenium.webdriver.common.by import By
from common.base_page import BasePage
from core.logger_utils import logger, LogIcon


# 注册页面
class RegistPage(BasePage):
    """注册页面对象"""

    LOGIN_ENTRY = (By.ID, 'tv_login')
    REGIST_ENTRY = (By.ID, 'tv_register')
    BACK_MAIN_PAGE = (By.ID, 'bt_back')
    RE_CHECK = (By.ID, 're_check_btn')
    SMS_REGIST = (By.ID, 'tv_tips')  # 短信注册

    ACCOUNT_FIELD = (By.ID, 'account_edit')
    PWD_FIELD = (By.ID, 'pwd_edit')
    RE_PWD_FIELD = (By.ID, 'confirm_pwd_edit')
    CHECKBOX = (By.ID, 'agreement_checkbox')
    IS_SHOW_PWD = (By.ID, 'iv_show_pass')
    IS_SHOW_RE_PWD = (By.ID, 'iv_show_confirm_pass')
    REGIST_BTN = (By.ID, 'register_btn')

    # 滑块
    SEEKBAR = (By.ID, 'seekbar')
    SLIDE_VERIFY = (By.ID, 'slide_verify')

    # 注册页 - 点击注册入口
    def click_regist_entry_if_exists(self) -> bool:
        """
        点击注册入口，没有找到注册按钮，从登录页面进去
        :return: 是否成功点击注册入口
        """
        logger.info(f"{LogIcon.SETUP} 尝试点击注册入口按钮")
        try:
            self.click(self.LOGIN_ENTRY)
            logger.info(f"{LogIcon.SUCCESS} 已成功进入注册页面")
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 没有找到注册入口: {str(e)}")
            return False

    # 注册页 - 获取并点击短信注册按钮进入注册页
    def entry_register_page(self) -> None:
        """ 获取并点击短信注册按钮进入注册页 """
        logger.info(f"{LogIcon.SETUP} 点击短信注册按钮")
        self.click(self.SMS_REGIST)

    # 注册页 - 切换显示密码
    def is_show_pwd(self) -> None:
        """ 显示密码，true-显示 """
        logger.info(f"{LogIcon.SETUP} 检查并切换密码显示明文状态")
        if self.get_attribute(self.PWD_FIELD, 'password'):
            logger.info(f"{LogIcon.SETUP} 点击显示密码明文")
            self.click(self.IS_SHOW_PWD)
        if self.get_attribute(self.RE_PWD_FIELD, 'password'):
            logger.info(f"{LogIcon.SETUP} 点击显示确认密码明文")
            self.click(self.IS_SHOW_RE_PWD)

    # 注册页 - 勾选用户协议
    def agree_protocol(self) -> None:
        """ 获取勾选状态，如果是 'false' 则点击 """
        logger.info(f"{LogIcon.SETUP} 检查协议勾选状态")
        if self.get_attribute(self.CHECKBOX, 'checked') == 'false':
            logger.info(f"{LogIcon.SETUP} 点击勾选用户协议")
            self.click(self.CHECKBOX)

    # 注册页 - 短信注册提交
    def sms_regist(self, username: str, password: str, re_password: str) -> None:
        """ 短信注册流程 """
        logger.info(f"{LogIcon.SETUP} 开始注册流程，账号: {username}")
        logger.info(f"{LogIcon.SETUP} 输入账号")
        self.send_keys(self.ACCOUNT_FIELD, username)
        logger.info(f"{LogIcon.SETUP} 输入密码")
        self.send_keys(self.PWD_FIELD, password)
        logger.info(f"{LogIcon.SETUP} 输入确认密码")
        self.send_keys(self.RE_PWD_FIELD, re_password)
        self.is_show_pwd()
        self.agree_protocol()
        logger.info(f"{LogIcon.SETUP} 点击注册按钮")
        self.click(self.REGIST_BTN)

    # 注册页 - 滑块验证
    def slide_verify(self) -> None:
        """ 滑块验证 """
        logger.info(f"{LogIcon.SETUP} 执行滑块验证")
        pass
