# -*- coding: utf-8 -*-
"""
iOS 平台登录页面元素定位器 (XCUITest / WebDriverAgent 原生架构)
全面规范化为 Apple 官方 XCUIElementType* 元素类型与高效定位策略 (Predicate / Class Chain / Accessibility ID)
"""
from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_ios import _CommonLocatorIos


class _LoginLocatorIos:
    """
    iOS 平台登录页面元素定位器 (XCUITest / WebDriverAgent 原生架构)

    定位策略优先级 (按 XCUITest 原生性能与稳定性排序)：
    1. ACCESSIBILITY_ID：对应 accessibilityIdentifier，哈希索引直达，最稳定首选；
    2. IOS_PREDICATE：NSPredicate 原生谓词，组合 XCUIElementType 与 label/name/value 过滤，不依赖视图层级；
    3. IOS_CLASS_CHAIN：原生层级链，用于精准父子/后代遍历 (如导航栏首按钮、输入框内部清除按钮)；
    4. XPATH：规范使用 XCUIElementType* 前缀，仅用于复杂祖先/跨分支反向锚定场景。

    注意：本类不继承 CommonLocator。DynamicLocatorProxy 在类定义阶段解析基类，
    若继承会固化为 Android 基类，导致 iOS 页面继承到 resource-id 定位器。
    """

    # iOS 应用 Bundle ID (与 config/devices.yaml 中 appium:bundleId 保持一致)
    PACKAGE_ID = _CommonLocatorIos.PACKAGE_ID

    
    # --------------------------------------------------------------------------
    # 0. 通用导航
    # --------------------------------------------------------------------------
    # 顶部导航返回按钮 (使用原生 Class Chain 精确定位导航栏首个按钮，替代原错误的 Predicate XPath 写法)
    TOP_IV_BACK_BTN = (
        AppiumBy.IOS_CLASS_CHAIN,
        "//XCUIElementTypeNavigationBar/XCUIElementTypeButton[1]",
    )

    # --------------------------------------------------------------------------
    # 1. 启动页与登录方式入口
    # --------------------------------------------------------------------------
    # 应用 logo (iOS 图片 name 为资源名，按 logo 关键字匹配)
    APPLICATION_LOGO = (AppiumBy.ACCESSIBILITY_ID, "launch_icon_santiao_text")
    # 手机号登录入口按钮 (支持 Accessibility ID 与 Button 谓词)
    LOGIN_ENTRANCE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name == '手机号登录'",
    )
    # 一键登录入口按钮 (有 SIM 卡时展示)
    ONE_KEY_LOGIN_ENTRANCE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name == '一键登录'",
    )

    # --------------------------------------------------------------------------
    # 2. 手机号与密码输入区域
    # --------------------------------------------------------------------------
    # 国家/地区区号选择按钮 (匹配形如 '+86' 的输入框/选择器，脱离对 fragile 容器层级的依赖)
    COUNTRY_CODE_PICKER = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeTextField' AND (value BEGINSWITH '+' OR label BEGINSWITH '+' OR name BEGINSWITH '+')",
    )
    # 手机号输入框 (登录页手机号输入组件)
    PHONE_NUMBER_EDIT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[2]/XCUIElementTypeOther/XCUIElementTypeTextField | (//XCUIElementTypeTextField)[last()]",
    )
    # 一键清空手机号按钮 (UITextField 系统清除按钮，name 标识为 'ic delete 48')
    CLEAR_PHONE_NUMBER = (
        AppiumBy.ACCESSIBILITY_ID,
        "ic delete 48",
    )
    # 密码输入框 (iOS 原生密文输入框 XCUIElementTypeSecureTextField)
    PASSWORD_EDIT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeSecureTextField",
    )
    # 密码明文/密文显示切换按钮 (紧随密码输入框内部或同级的切换按钮)
    PASSWORD_VISIBLE_BTN = (
        AppiumBy.ACCESSIBILITY_ID,
        "login pw hide",
    )

    # --------------------------------------------------------------------------
    # 3. 登录模式切换与提交操作
    # --------------------------------------------------------------------------
    # 一键免费注册入口 (兼容 XCUIElementTypeLink / Button / StaticText，支持 '>' 与 '›')
    ONE_REGIST = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeLink' AND name == '一键免费注册'",
    )
    # 切换至密码验证登录
    PASSWORD_LOGIN_SWITCH = (
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeButton'} AND (name == ' 密码验证登录')",
    )
    # 切换至短信验证码登录
    CODE_LOGIN_SWITCH = (
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeButton'} AND (name == '短信验证登录')",
    )
    # 当前可见的登录模式切换入口 (密码 / 短信二选一)
    PWD_AND_CODE = (
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeButton'} AND (name IN {' 密码验证登录', ' 短信验证登录'})",
    )
    # 登录/验证并登录提交按钮 (限定为 XCUIElementTypeButton，精准命中按钮避免误点子级 StaticText)
    VERIFY_AND_LOGIN_BTN = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND (name IN {'密码验证登录', '短信验证登录'})",
    )
    # 登录遇到问题反馈入口
    FEEDBACK_BTN = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name CONTAINS '反馈')",
    )

    # --------------------------------------------------------------------------
    # 4. 短信验证码校验页面组件
    # --------------------------------------------------------------------------
    # 请填写验证码主标题
    PLEASE_ENTER_VERIFICATION_CODE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name == '请填写验证码')",
    )
    # 验证码已发送副标题
    VERIFICATION_CODE_SENT = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name CONTAINS '验证码已发送')",
    )
    # 接收验证码的目标手机号文本 (以 '+' 开头的手机号文本)
    SEND_VERIFICATION_CODE_PHONE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name BEGINSWITH '验证码已发送')",
    )
    # 收不到验证码求助入口
    CANNOT_RECEIVE_VERIFICATION_CODE = (
        AppiumBy.IOS_PREDICATE,
        f"type IN {'XCUIElementTypeStaticText'} AND (name CONTAINS '收不到验证码')",
    )
    # 验证码重新获取倒计时文本 (60s)
    VERIFICATION_CODE_COUNTDOWN = (
        AppiumBy.IOS_PREDICATE,
        f"type IN {'XCUIElementTypeStaticText'} AND (name CONTAINS '重新获取')",
    )
    # 分离式验证码独立输入框集合 (find_elements 按文档顺序返回，与验证码位次一一对应)
    CODE_EDIT_TEXTS = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeTextField'",
    )

    # --------------------------------------------------------------------------
    # 5. 用户协议勾选与底部协议拦截弹窗
    # --------------------------------------------------------------------------
    # 登录页底部协议勾选框 (iOS 无原生 Checkbox，以选中态图片按钮实现)
    AGREE_AND_LOGIN_BTN = (
        AppiumBy.ACCESSIBILITY_ID,
        "ic choice default 32",
    )
    # 登录页底部用户协议与隐私政策说明文本
    AGREE_AND_LOGIN_TEXT = (
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeTextView'} AND (name CONTAINS '我已阅读且同意')",
    )
    # 登录页底部 - 《用户协议》超链接入口
    USER_AGREEMENT_LINK = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeLink' AND (name CONTAINS '用户协议')",
    )
    # 登录页底部 - 《隐私政策》超链接入口
    PRIVACY_POLICY_LINK = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeLink' AND (name CONTAINS '隐私政策')",
    )
    # 登录页底部 - 《未成年人个人信息保护规则》超链接入口
    CHILD_PROTECTION_LINK = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeLink' AND (name CONTAINS '未成年人个人信息保护规则')",
    )
    # 登录页底部 - 《支付协议》超链接入口
    PAYMENT_AGREEMENT_LINK = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeLink' AND (name CONTAINS '支付协议')",
    )
    
    # 未勾选协议点击登录后弹出的底部弹窗容器
    AGREEMENT_BOTTOM_SHEET = (
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[XCUIElementTypeStaticText[@text='用户协议及隐私政策']]",
    )
    # 协议拦截弹窗 - 同意并继续按钮
    AGREE_AND_CONTINUE_BTN = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND (name == '同意并继续')",
    )
    # 协议拦截弹窗 - 关闭按钮
    CLOSE_BTN = (
        AppiumBy.ACCESSIBILITY_ID,
        "ic top temporary prompt close",
    )
    # 协议拦截弹窗 - 协议正文描述
    USER_AGREEMENT_DESC = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeTextView' AND (name CONTAINS '我已阅读且同意')",
    )


    # --------------------------------------------------------------------------
    # 6. 业务 Toast 提示与系统级密码存储弹窗
    # --------------------------------------------------------------------------
    # 业务 Toast 提示 (基于 iOS 原生 Toast 浮层结构特征锚定：支持带 ic_toast_* 图标的提示框及通用弹窗文本)
    TOAST_MSG = (
        AppiumBy.XPATH,
        (
            "//XCUIElementTypeImage[contains(@name, 'toast')]/following-sibling::XCUIElementTypeStaticText"
            " | //XCUIElementTypeOther[XCUIElementTypeImage[contains(@name, 'toast')]]//XCUIElementTypeStaticText"
            " | //XCUIElementTypeAlert//XCUIElementTypeStaticText"
        ),
    )

    @staticmethod
    def get_dynamic_toast_msg(expected_toast: str) -> tuple[str, str]:
        """根据预期文本生成业务 Toast 谓词定位器 (安全转义单引号防语法截断)"""
        safe_text = expected_toast.replace("\\", "\\\\").replace("'", "\\'")
        return (
            AppiumBy.IOS_PREDICATE,
            f"type == 'XCUIElementTypeStaticText' AND (name CONTAINS '{safe_text}' OR value CONTAINS '{safe_text}')",
        )

    # iOS 系统“存储密码”钥匙串弹窗标题 (AuthenticationServices 弹窗)
    AUTO_SAVE_PWD_TITLE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name CONTAINS '存储密码' OR name CONTAINS '保存密码')",
    )
    # iOS 系统“存储密码”钥匙串弹窗 - 以后/暂不按钮
    AUTO_SAVE_PWD_CANCEL = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name IN {'以后', '不是现在', 'Not Now'}",
    )
    # iOS 系统“存储密码”钥匙串弹窗 - 存储密码按钮
    AUTO_SAVE_PWD_SAVE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name IN {'存储密码', '保存密码', 'Save Password'}",
    )
