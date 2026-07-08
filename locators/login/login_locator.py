from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator

class LoginLocator(CommonLocator):
    """登录页面元素定位器"""
    
    PACKAGE_ID = 'com.santiaotalk.im:id'
    
    # 手机号登录入口
    LOGIN_ENTRANCE = (AppiumBy.ID, f'{PACKAGE_ID}/fb_phone_login') # 按钮
    LOGIN_ENTRANCE_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("手机号登录")') # 文本

    # 国家区域手机号开头
    COUNTRY_CODE_PICKER = (AppiumBy.ID, f'{PACKAGE_ID}/cl_country_code') # 按钮

    # 手机号输入框
    PHONE_NUMBER_EDIT = (AppiumBy.ID, f'{PACKAGE_ID}/et_phone')
    # 一键清空手机号按钮
    CLEAR_PHONE_NUMBER = (AppiumBy.ID, f'{PACKAGE_ID}/iv_delete')

    # 密码登录切换按钮
    PASSWORD_LOGIN_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/tv_password_login')
    # 密码输入框
    PASSWORD_EDIT = (AppiumBy.ID, f'{PACKAGE_ID}/et_password')
    # 密码显示隐藏按钮
    PASSWORD_VISIBLE_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/iv_eye')

    # 验证码登录切换按钮
    CODE_LOGIN_SWITCH = (AppiumBy.ID, f'{PACKAGE_ID}/tv_code_login')

    # 验证并登录按钮 和 登录按钮
    VERIFY_AND_LOGIN_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/fb_verify_login')
    # 验证并登录按钮文本 和 登录按钮文本
    VERIFY_AND_LOGIN_BTN_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("验证并登录")')
    LOGIN_BTN_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("登录")')

    # 请填写验证码文本 title
    PLEASE_ENTER_VERIFICATION_CODE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_big_title')
    # 验证码已发送 title
    VERIFICATION_CODE_SENT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_sub_title')
    # 发送验证码手机号
    SEND_VERIFICATION_CODE_PHONE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_sub_phone')
    # 收不到验证码 text
    CANNOT_RECEIVE_VERIFICATION_CODE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_cannot_receive')
    # 验证码倒计时 60s
    VERIFICATION_CODE_COUNTDOWN = (AppiumBy.ID, f'{PACKAGE_ID}/tv_regain')

    # 验证码输入框父级容器 ID
    VERIFICATION_CODE_INPUT_CONTAINER_ID = f'{PACKAGE_ID}/view_input_code'
    VERIFICATION_CODE_INPUT_CONTAINER = (AppiumBy.ID, VERIFICATION_CODE_INPUT_CONTAINER_ID)
    # 获取所有的独立输入框 (返回一个列表)
    CODE_EDIT_TEXTS = (AppiumBy.XPATH, f'//*[@resource-id="{VERIFICATION_CODE_INPUT_CONTAINER_ID}"]//android.widget.EditText')
    
    
    # 一键登录入口
    ONE_KEY_LOGIN_ENTRANCE = (AppiumBy.ID, f'{PACKAGE_ID}/one_key_login') # 按钮
    ONE_KEY_LOGIN_ENTRANCE_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("一键登录")') # 文本

    # 协议同意按钮
    AGREE_AND_LOGIN_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/cb_agree_privacy')
    # 协议文本
    AGREE_AND_LOGIN_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_agree_privacy')
    
    # 反馈按钮
    FEEDBACK_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/tv_question')

    # 未勾选协议点击登录后弹出容器
    # 底部容器标识
    AGREEMENT_BOTTOM_SHEET = (AppiumBy.ID, f'{PACKAGE_ID}/design_bottom_sheet')
    # 同意并继续按钮
    AGREE_AND_CONTINUE_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/fb_agree_continue')
    # 同意并继续按钮文本
    AGREE_AND_CONTINUE_BTN_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("同意并继续")')
    # 关闭按钮
    CLOSE_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/iv_close')
    # 用户协议及隐私政策 标题 使用CommonLocator.TOP_TV_TITLE
    # 我已阅读且同意《用户协议》《隐私协议》《未成年人个人信息保护规则》。
    USER_AGREEMENT_DESC = (AppiumBy.ID, f'{PACKAGE_ID}/tv_desc')

    # 通用 Toast 提示 (用于校验错误信息)
    # TOAST_MSG = (AppiumBy.XPATH, "//android.widget.Toast")
    TOAST_MSG = CommonLocator.TOAST_MSG
    
    @staticmethod
    def get_dynamic_toast_msg(expected_toast: str):
        return (AppiumBy.XPATH, f"//*[contains(@text, '{expected_toast}') or contains(@content-desc, '{expected_toast}')]")
