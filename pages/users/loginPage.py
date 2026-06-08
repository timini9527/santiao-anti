from selenium.webdriver.common.by import By
from common.base_page import BasePage


#   登录页面封装
class LoginPage(BasePage):
    # 元素定位器
    LOGIN_ENTRY = (By.ID, 'tv_login')
    CHECKBOX = (By.ID, 'agreement_checkbox')
    ACCOUNT_FIELD = (By.ID, 'account_edit')
    PWD_FIELD = (By.ID, 'pwd_edit')
    LOGIN_BTN = (By.ID, 'login_btn')
    IS_SHOW_PWD = (By.ID, 'iv_show_pass')

    ONE_CLICK_LOGIN = (By.ID, 'tv_one_click_login') # 一键登录
    SMS_LOGIN = (By.ID, 'tv_sms_login') # 短信登录
    ET_CODE = (By.ID, 'et_code')


    def click_login_entry_if_exists(self) -> bool:
        try:
            entry_points = self.click(self.LOGIN_ENTRY)
            print("已进入登录页面", entry_points)
            return True
        except Exception as e:
            print("异常", str(e))
            return False# 如果已经在登录页则忽略

    def agree_protocol(self):
        # 获取勾选状态，如果是 'false' 则点击
        if self.get_attribute(self.CHECKBOX, 'checked') == 'false':
            self.click(self.CHECKBOX)

    def show_pwd(self):
        # 显示密码，true-显示
        if self.get_attribute(self.PWD_FIELD, 'password'):
        # print("显示密码：", self.get_attribute(self.PWD_FIELD, 'password'))
            self.click(self.IS_SHOW_PWD)

    def login(self, username, password):
        self.send_keys(self.ACCOUNT_FIELD, username)
        self.send_keys(self.PWD_FIELD, password)
        self.show_pwd()
        self.agree_protocol()
        self.click(self.LOGIN_BTN)

    def is_login_page_status(self):
        # 是否还在登录页面
        page_status = self.find_element(self.LOGIN_BTN)
        if page_status is not None:
            print("还在登录页面", self.find_element(self.LOGIN_BTN))
            return True
        else: return False

    #   本机号码一键登录