from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_hos import CommonLocatorHos


class LoginLocatorHos(CommonLocatorHos):
    """
    鸿蒙 NEXT 平台登录页面元素定位器 (HarmonyOS ArkUI 专享架构)
    底层原生对齐 ArkUI 控件树标签 (Button, Text, TextInput, Checkbox, Image, Dialog 等)
    全面覆盖手机号登录、验证码登录、密码登录、协议勾选及系统密码弹窗。
    """

    PACKAGE_ID = CommonLocatorHos.PACKAGE_ID

    APPLICATION_LOGO = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Image")

    # 手机号登录入口
    LOGIN_ENTRANCE = (
        AppiumBy.XPATH,
        "//Button[contains(@text, '手机号登录')] | //*[contains(@text, '手机号登录')]",
    )

    # 有SIM卡时，显示一键登录按钮与入口
    ONE_KEY_LOGIN_ENTRANCE = (
        AppiumBy.XPATH,
        "//*[@id='loginBtn'] | //Button[@text='一键登录'] | //Text[@text='一键登录']",
    )

    # 国家区域手机号开头
    COUNTRY_CODE_PICKER = (
        AppiumBy.XPATH,
        "//__Common__/Row/Row",
    )

    # 手机号输入框与一键清空
    PHONE_NUMBER_EDIT = (
        AppiumBy.XPATH,
        "//__Common__/Row/TextInput",
    )
    # 一键清空手机号按钮
    CLEAR_PHONE_NUMBER = (
        AppiumBy.XPATH,
        "//__Common__/Row/Image | //Row[TextInput]//Image",
    )

    # 密码与验证码登录模式切换按钮
    PASSWORD_LOGIN_SWITCH = (
        AppiumBy.XPATH,
        "//Text[@text='密码验证登录']",
    )
    CODE_LOGIN_SWITCH = (
        AppiumBy.XPATH,
        "//Text[@text='短信验证登录']",
    )
    PWD_AND_CODE = (
        AppiumBy.XPATH,
        "//Row/Text[contains(@text,'密码验证登录') or contains(@text,'短信验证登录')]",
    )

    # 密码输入框与可见性切换
    PASSWORD_EDIT = (
        AppiumBy.XPATH,
        "//Column/Row/TextInput",
    )
    # 密码显示隐藏按钮
    PASSWORD_VISIBLE_BTN = (
        AppiumBy.XPATH,
        "//Column/Row/TextInput/following-sibling::Image",
    )

    # 验证并登录按钮 (合并密码与验证码状态)
    VERIFY_AND_LOGIN_BTN = (
        AppiumBy.XPATH,
        "//__Common__/Text[@text='密码验证登录' or @text='短信验证登录'] | //Text[@text='密码验证登录' or @text='短信验证登录']",
    )

    # 验证码页面组件
    PLEASE_ENTER_VERIFICATION_CODE = (
        AppiumBy.XPATH,
        "//Text[@text='请填写验证码']",
    )
    # 验证码已发送 title
    VERIFICATION_CODE_SENT = (AppiumBy.XPATH, "//Text[contains(@text, '验证码已发送')]")
    # 发送验证码手机号
    SEND_VERIFICATION_CODE_PHONE = (
        AppiumBy.XPATH,
        "(//Column/Text[2])[1]",
    )
    # 收不到验证码 text
    CANNOT_RECEIVE_VERIFICATION_CODE = (AppiumBy.XPATH, "//Text[contains(@text, '收不到验证码')]")
    # 验证码倒计时 60s
    VERIFICATION_CODE_COUNTDOWN = (
        AppiumBy.XPATH,
        "//Text[contains(@text, '重新获取')]",
    )

    # 获取所有的独立验证码输入框集合
    CODE_EDIT_TEXTS = (
        AppiumBy.XPATH,
        "//__Common__/Stack/Row/Stack/Text",
    )

    # 协议同意按钮与说明
    AGREE_AND_LOGIN_BTN = (
        AppiumBy.XPATH,
        "//Checkbox[@text='privacyCb'] | //Checkbox",
    )
    # 账密和一键登录协议文本
    AGREE_AND_LOGIN_TEXT = (
        AppiumBy.XPATH,
        "//*[@id='clause_text'] | //Column/Column/Column/Row/Text",
    )

    # 反馈按钮
    FEEDBACK_BTN = (AppiumBy.XPATH, "//Text[contains(@text, '反馈')]")

    # 未勾选协议点击登录后弹出容器
    AGREEMENT_BOTTOM_SHEET = (
        AppiumBy.XPATH,
        "//Dialog//__Common__/RelativeContainer",
    )
    AGREE_AND_CONTINUE_BTN = (
        AppiumBy.XPATH,
        "//Dialog//__Common__/RelativeContainer//Text[@text='同意并继续'] | //Text[@text='同意并继续']",
    )
    CLOSE_BTN = (
        AppiumBy.XPATH,
        "//Dialog//__Common__/RelativeContainer/Text[@text='×']",
    )
    USER_AGREEMENT_DESC = (
        AppiumBy.XPATH,
        "//Dialog//__Common__/RelativeContainer//Text[@id='prvacy_content']",
    )

    # 通用 Toast 提示 (用于校验错误信息)
    TOAST_MSG = (
        AppiumBy.XPATH,
        "//Toast | //Prompt | //Text[contains(@text, '验证码') or contains(@text, '错误') or contains(@text, '成功') or contains(@text, '失败')]",
    )

    @staticmethod
    def get_dynamic_toast_msg(expected_toast: str):
        return (AppiumBy.XPATH, f"//*[contains(@text, '{expected_toast}') or contains(@content-desc, '{expected_toast}')]")

    # ======================================================
    # 系统级弹窗 - 使用已保存的账号/使用其他账号/手动输入
    # ======================================================
    AUTO_SAVE_PWD_TITLE = (
        AppiumBy.XPATH,
        "//Button[@id='AutoFillDialog_auto_fill_use_recommended_account']",
    )
    AUTO_SAVE_PWD_CANCEL = (
        AppiumBy.XPATH,
        "//Button[@id='AutoFillDialog_auto_fill_use_other_account']",
    )
    AUTO_SAVE_PWD_SAVE = (
        AppiumBy.XPATH,
        "//Button[@id='AutoFillDialog_auto_fill_self_input']",
    )
