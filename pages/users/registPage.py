import time

from selenium.webdriver.common.by import By
from common.base_page import BasePage
from core.logger_utils import logger


#   注册页面
class RegistPage(BasePage):
    LOGIN_ENTRY = (By.ID, 'tv_login')
    REGIST_ENTRY = (By.ID, 'tv_register')
    BACK_MAIN_PAGE = (By.ID, 'bt_back')
    RE_CHECK = (By.ID, 're_check_btn')
    SMS_REGIST = (By.ID, 'tv_tips') # 短信注册

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


    def click_regist_entry_if_exists(self) -> bool:
        """
        点击注册入口，没有找到注册按钮，从登录页面进去
        :return:
        """
        try:
            entry_points = self.click(self.LOGIN_ENTRY)
            print("已进入注册页面", entry_points)
            return  True
        except Exception as e:
            logger.error(f"没有找到注册入口: {str(e)}")
            return  False

    def entry_register_page(self):
        # 获取注册按钮
        self.click(self.SMS_REGIST)

    def is_show_pwd(self):
        # 显示密码，true-显示
        if self.get_attribute(self.PWD_FIELD, 'password'):
            self.click(self.IS_SHOW_PWD)
        if self.get_attribute(self.RE_PWD_FIELD, 'password'):
            self.click(self.IS_SHOW_RE_PWD)

    def agree_protocol(self):
        # 获取勾选状态，如果是 'false' 则点击
        if self.get_attribute(self.CHECKBOX, 'checked') == 'false':
            self.click(self.CHECKBOX)

    def sms_regist(self, username, password, re_password):
        # 注册
        self.send_keys(self.ACCOUNT_FIELD, username)
        self.send_keys(self.PWD_FIELD, password)
        self.send_keys(self.RE_PWD_FIELD, re_password)
        self.is_show_pwd()
        self.agree_protocol()
        self.click(self.REGIST_BTN)
        time.sleep(100)


    def slide_verify(self):
        # 滑块验证
        pass
