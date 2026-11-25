from appium.webdriver.common.appiumby import AppiumBy
from core.locator_manager import DynamicLocatorMeta
from locators.common.common_locator import CommonLocator
from locators.login.login_locator_hos import _LoginLocatorHos
from locators.login.login_locator_ios import _LoginLocatorIos


class _LoginLocatorAndroid(CommonLocator):
    """
    安卓 (Android) 登录页面元素定位器
    继承自 CommonLocator，统一管理登录入口、账号密码输入、验证码校验、协议弹窗及系统级自动填充弹窗定位。
    """

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # --------------------------------------------------------------------------
    # 1. 启动页与登录方式入口
    # --------------------------------------------------------------------------

    # 应用logo
    APPLICATION_LOGO = (AppiumBy.XPATH, f"//*[@resource-id='com.santiaotalk.im:id/iv_logo']")

    # 手机号登录入口按钮
    LOGIN_ENTRANCE = (AppiumBy.ID, f"{PACKAGE_ID}/fb_phone_login")
    # 一键登录入口按钮
    ONE_KEY_LOGIN_ENTRANCE = (AppiumBy.ID, f"{PACKAGE_ID}/one_key_login")

    # --------------------------------------------------------------------------
    # 2. 手机号与密码输入区域
    # --------------------------------------------------------------------------
    # 国家/地区区号选择按钮
    COUNTRY_CODE_PICKER = (AppiumBy.ID, f"{PACKAGE_ID}/cl_country_code")
    # 手机号输入框
    PHONE_NUMBER_EDIT = (AppiumBy.ID, f"{PACKAGE_ID}/et_phone")
    # 一键清空手机号按钮 (右侧 × 图标)
    CLEAR_PHONE_NUMBER = (AppiumBy.ID, f"{PACKAGE_ID}/iv_delete")
    # 密码输入框
    PASSWORD_EDIT = (AppiumBy.ID, f"{PACKAGE_ID}/et_password")
    # 密码明文/密文显示切换按钮 (右侧眼睛图标)
    PASSWORD_VISIBLE_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/iv_eye")

    # --------------------------------------------------------------------------
    # 3. 登录模式切换与提交操作
    # --------------------------------------------------------------------------
    # 切换至密码验证登录按钮
    PASSWORD_LOGIN_SWITCH = (AppiumBy.ID, f"{PACKAGE_ID}/tv_password_login")
    # 切换至短信验证码登录按钮
    CODE_LOGIN_SWITCH = (AppiumBy.ID, f"{PACKAGE_ID}/tv_code_login")
    # 登录/验证并登录提交按钮
    VERIFY_AND_LOGIN_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/fb_verify_login")
    # 登录遇到问题反馈按钮
    FEEDBACK_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/tv_question")

    # --------------------------------------------------------------------------
    # 4. 短信验证码校验页面组件
    # --------------------------------------------------------------------------
    # 请填写验证码主标题
    PLEASE_ENTER_VERIFICATION_CODE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_big_title")
    # 验证码已发送副标题
    VERIFICATION_CODE_SENT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_sub_title")
    # 接收验证码的目标手机号文本
    SEND_VERIFICATION_CODE_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_sub_phone")
    # 收不到验证码求助入口文本
    CANNOT_RECEIVE_VERIFICATION_CODE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_cannot_receive")
    # 验证码重新获取倒计时文本 (60s)
    VERIFICATION_CODE_COUNTDOWN = (AppiumBy.ID, f"{PACKAGE_ID}/tv_regain")
    # 验证码输入框父级容器 ID 与定位器
    VERIFICATION_CODE_INPUT_CONTAINER_ID = f"{PACKAGE_ID}/view_input_code"
    VERIFICATION_CODE_INPUT_CONTAINER = (AppiumBy.ID, VERIFICATION_CODE_INPUT_CONTAINER_ID)
    # 分离式验证码独立输入框列表
    CODE_EDIT_TEXTS = (
        AppiumBy.XPATH,
        f"//*[@resource-id='{VERIFICATION_CODE_INPUT_CONTAINER_ID}']//android.widget.EditText",
    )

    # --------------------------------------------------------------------------
    # 5. 用户协议勾选与底部协议拦截弹窗
    # --------------------------------------------------------------------------
    # 登录页底部用户协议勾选框
    AGREE_AND_LOGIN_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/cb_agree_privacy")
    # 登录页底部用户协议与隐私政策说明文本
    AGREE_AND_LOGIN_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_agree_privacy")
    # 未勾选协议点击登录后弹出的底部弹窗容器
    AGREEMENT_BOTTOM_SHEET = (AppiumBy.ID, f"{PACKAGE_ID}/design_bottom_sheet")
    # 协议拦截弹窗 - 同意并继续按钮
    AGREE_AND_CONTINUE_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/fb_agree_continue")
    # 协议拦截弹窗 - 右上角关闭按钮
    CLOSE_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/iv_close")
    # 协议拦截弹窗 - 协议正文描述文本 (弹窗标题复用 CommonLocator.TOP_TV_TITLE)
    USER_AGREEMENT_DESC = (AppiumBy.ID, f"{PACKAGE_ID}/tv_desc")

    # --------------------------------------------------------------------------
    # 6. 业务 Toast 提示与系统级密码填充弹窗
    # --------------------------------------------------------------------------
    # 通用 Toast 提示 (复用 CommonLocator)
    TOAST_MSG = CommonLocator.TOAST_MSG

    @staticmethod
    def get_dynamic_toast_msg(expected_toast: str) -> tuple[str, str]:
        """根据预期文本生成动态模糊匹配的 Toast 定位器"""
        return (
            AppiumBy.XPATH,
            f"//*[contains(@text, '{expected_toast}') or contains(@content-desc, '{expected_toast}')]",
        )

    # 系统级自动保存账号密码弹窗标题 (MIUI / HyperOS / 原生 Android)
    AUTO_SAVE_PWD_TITLE = (
        AppiumBy.XPATH,
        '//*[@resource-id="miuix.stub:id/alertTitle" or @text="自动保存账号密码"]',
    )
    # 系统级自动保存账号密码弹窗 - 取消按钮
    AUTO_SAVE_PWD_CANCEL = (
        AppiumBy.XPATH,
        '//*[@resource-id="android:id/button2" and @text="取消"]',
    )
    # 系统级自动保存账号密码弹窗 - 存储按钮
    AUTO_SAVE_PWD_SAVE = (
        AppiumBy.XPATH,
        '//*[@resource-id="android:id/button1" and @text="存储"]',
    )


# ==============================================================================
# 跨端通用定位器透明代理 (自动识别 Android / HarmonyOS NEXT / iOS)
# ==============================================================================
class LoginLocator(_LoginLocatorHos, _LoginLocatorAndroid, _LoginLocatorIos, metaclass=DynamicLocatorMeta):
    """跨端登录页面定位器（支持 IDE Ctrl + 鼠标左键直接跳转定义，运行时按设备平台动态分发）"""

    _android_cls = _LoginLocatorAndroid
    _harmony_cls = _LoginLocatorHos
    _ios_cls = _LoginLocatorIos
