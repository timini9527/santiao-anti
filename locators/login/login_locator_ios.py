from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_ios import CommonLocatorIos


class LoginLocatorIos:
    """
    iOS 平台登录页面元素定位器 (XCUITest / WebDriverAgent 原生架构)

    定位策略优先级 (按 XCUITest 查询性能与稳定性排序)：
    1. ACCESSIBILITY_ID：对应 accessibilityIdentifier，哈希索引直达，研发补齐埋点后优先替换为该策略；
    2. IOS_PREDICATE：NSPredicate 原生谓词，按 type + label/name/value 组合过滤，不依赖层级；
    3. IOS_CLASS_CHAIN：轻量层级链，用于“输入框内系统清除按钮”等具备稳定父子关系的场景；
    4. XPATH：仅保留给 following-sibling / 祖先容器等谓词无法表达的低频场景。

    注意：本类不继承 CommonLocator。DynamicLocatorProxy 在类定义（导入）阶段即解析基类，
    此时尚无 driver 上下文，会固化为 Android 基类，导致 iOS 页面继承到 resource-id 定位器。
    """

    # iOS 应用 Bundle ID (与 config/devices.yaml 中 appium:bundleId 保持一致)
    PACKAGE_ID = CommonLocatorIos.PACKAGE_ID

    # 静态文本类控件类型集合 (自定义 Label 与富文本 TextView 均可能承载文案)
    _TEXT_TYPES = "{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}"
    # 可点击类控件类型集合 (研发可能以 Button 或带手势的 StaticText 实现入口)
    _TAP_TYPES = "{'XCUIElementTypeButton', 'XCUIElementTypeStaticText'}"
    # 协议拦截底部弹窗容器 XPath (以“同意并继续”按钮反向锚定最内层容器)
    _AGREEMENT_SHEET_XPATH = (
        "(//XCUIElementTypeOther[.//XCUIElementTypeButton[@label='同意并继续']"
        " and .//*[contains(@label, '协议')]])[last()]"
    )

    # --------------------------------------------------------------------------
    # 0. 通用导航
    # --------------------------------------------------------------------------
    # 顶部导航返回按钮 (覆盖 Android 回退的 resource-id 定位器，iOS 必须显式定义)
    TOP_IV_BACK_BTN = (AppiumBy.IOS_PREDICATE, "//NavigationBar/Button")

    # --------------------------------------------------------------------------
    # 1. 启动页与登录方式入口
    # --------------------------------------------------------------------------
    # 应用 logo (iOS 图片 name 为资源名，按 logo 关键字匹配)
    APPLICATION_LOGO = (AppiumBy.ACCESSIBILITY_ID, "launch_icon_santiao_text")
    # 手机号登录入口按钮
    LOGIN_ENTRANCE = (AppiumBy.ACCESSIBILITY_ID, f"手机号登录",)
    # 一键登录入口按钮 (有 SIM 卡时展示)
    ONE_KEY_LOGIN_ENTRANCE = (AppiumBy.ACCESSIBILITY_ID, f"一键登录")

    # --------------------------------------------------------------------------
    # 2. 手机号与密码输入区域
    # --------------------------------------------------------------------------
    # 国家/地区区号选择按钮 (文案形如 “+86”)
    COUNTRY_CODE_PICKER = (
        AppiumBy.XPATH,
        f"//Other[1]/Other/TextField",
    )
    # 手机号输入框 (登录页首个明文输入框)
    PHONE_NUMBER_EDIT = (AppiumBy.XPATH, "//Other[2]/Other/TextField")
    # 一键清空手机号按钮 (UITextField 系统 clearButton 为输入框子节点，与系统语言无关)
    CLEAR_PHONE_NUMBER = (
        AppiumBy.ACCESSIBILITY_ID,  "ic delete 48"
    )
    # 密码输入框 (密文态为 SecureTextField；切换明文后变为第二个 TextField，两态统一覆盖)
    PASSWORD_EDIT = (
        AppiumBy.XPATH,
        "//Other/Other/SecureTextField",
    )
    # 密码明文/密文显示切换按钮 (紧随密码输入框的同级按钮)
    PASSWORD_VISIBLE_BTN = (
        AppiumBy.XPATH,
        "//Other/Other/SecureTextField/Button"
    )

    # --------------------------------------------------------------------------
    # 3. 登录模式切换与提交操作
    # --------------------------------------------------------------------------
    # 一键免费注册
    ONE_REGIST = (Appium.ACCESSIBILITY_ID, '一键免费注册 ›')
    # 切换至密码验证登录
    PASSWORD_LOGIN_SWITCH = (
        AppiumBy.ACCESSIBILITY_ID,
        f"密码验证登录"
    )
    # 切换至短信验证码登录
    CODE_LOGIN_SWITCH = (
        AppiumBy.ACCESSIBILITY_ID,
        f"短信验证登录"
    )
    # 当前可见的登录模式切换入口 (密码 / 短信二选一)
    PWD_AND_CODE = (
        AppiumBy.XPATH,
        "//Button[1][@name=' 短信验证登录' or @name='密码验证登录']",
    )
    # 登录/验证并登录提交按钮 (排除模式切换、手机号登录与一键登录入口，防止误点)
    VERIFY_AND_LOGIN_BTN = (AppiumBy.IOS_PREDICATE, "name IN {'密码验证登录', '短信验证登录'} OR label IN {'密码验证登录', '短信验证登录'}")
    # 登录遇到问题反馈入口
    FEEDBACK_BTN = (
        AppiumBy.XPATH,
        f"//Button[contains(@name,'反馈')]",
    )

    # --------------------------------------------------------------------------
    # 4. 短信验证码校验页面组件
    # --------------------------------------------------------------------------
    # 请填写验证码主标题
    PLEASE_ENTER_VERIFICATION_CODE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND label == '请填写验证码'",
    )
    # 验证码已发送副标题
    VERIFICATION_CODE_SENT = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND label CONTAINS '验证码已发送'",
    )
    # 接收验证码的目标手机号文本 (验证码页无区号选择器，以 “+” 开头的文本唯一)
    SEND_VERIFICATION_CODE_PHONE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND label BEGINSWITH '+'",
    )
    # 收不到验证码求助入口
    CANNOT_RECEIVE_VERIFICATION_CODE = (
        AppiumBy.IOS_PREDICATE,
        f"type IN {_TAP_TYPES} AND label CONTAINS '收不到验证码'",
    )
    # 验证码重新获取倒计时文本 (60s)
    VERIFICATION_CODE_COUNTDOWN = (
        AppiumBy.IOS_PREDICATE,
        f"type IN {_TAP_TYPES} AND label CONTAINS '重新获取'",
    )
    # 分离式验证码独立输入框集合 (find_elements 按文档顺序返回，与验证码位次一一对应)
    CODE_EDIT_TEXTS = (AppiumBy.IOS_CLASS_CHAIN, "**/XCUIElementTypeTextField")

    # --------------------------------------------------------------------------
    # 5. 用户协议勾选与底部协议拦截弹窗
    # --------------------------------------------------------------------------
    # 登录页底部协议勾选框 (iOS 无原生 Checkbox，以选中态图片按钮实现)
    AGREE_AND_LOGIN_BTN = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton'"
        " AND (name CONTAINS[c] 'check' OR name CONTAINS[c] 'agree' OR name CONTAINS[c] 'select')",
    )
    # 登录页底部用户协议与隐私政策说明文本
    AGREE_AND_LOGIN_TEXT = (
        AppiumBy.IOS_PREDICATE,
        f"type IN {_TEXT_TYPES} AND label CONTAINS '同意' AND label CONTAINS '协议'",
    )
    # 未勾选协议点击登录后弹出的底部弹窗容器
    AGREEMENT_BOTTOM_SHEET = (AppiumBy.XPATH, _AGREEMENT_SHEET_XPATH)
    # 协议拦截弹窗 - 同意并继续按钮
    AGREE_AND_CONTINUE_BTN = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND label == '同意并继续'",
    )
    # 协议拦截弹窗 - 关闭按钮
    CLOSE_BTN = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND (label == '×' OR name CONTAINS[c] 'close')",
    )
    # 协议拦截弹窗 - 协议正文 (限定在弹窗容器内，避免命中底层登录页协议文本)
    USER_AGREEMENT_DESC = (
        AppiumBy.XPATH,
        f"{_AGREEMENT_SHEET_XPATH}//*[(self::XCUIElementTypeStaticText or self::XCUIElementTypeTextView)"
        " and contains(@label, '协议')]",
    )

    # --------------------------------------------------------------------------
    # 6. 业务 Toast 提示与系统级密码存储弹窗
    # --------------------------------------------------------------------------
    # 业务 Toast (iOS 无系统 Toast，应用内浮层以 StaticText 呈现)
    TOAST_MSG = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (label CONTAINS '验证码' OR label CONTAINS '错误'"
        " OR label CONTAINS '成功' OR label CONTAINS '失败')",
    )

    @staticmethod
    def get_dynamic_toast_msg(expected_toast: str) -> tuple[str, str]:
        """根据预期文本生成 Toast 谓词定位器 (单引号转义，防止谓词语法被文案截断)"""
        safe_text = expected_toast.replace("\\", "\\\\").replace("'", "\\'")
        return (
            AppiumBy.IOS_PREDICATE,
            f"type IN {LoginLocatorIos._TEXT_TYPES} AND label CONTAINS '{safe_text}'",
        )

    # iOS 系统“存储密码”弹窗标题 (AuthenticationServices 钥匙串弹窗)
    AUTO_SAVE_PWD_TITLE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (label CONTAINS '存储密码' OR label CONTAINS '保存密码')",
    )
    # iOS 系统“存储密码”弹窗 - 以后 / 暂不
    AUTO_SAVE_PWD_CANCEL = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND label IN {'以后', '不是现在', 'Not Now'}",
    )
    # iOS 系统“存储密码”弹窗 - 存储
    AUTO_SAVE_PWD_SAVE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND label IN {'存储密码', '保存密码', 'Save Password'}",
    )
