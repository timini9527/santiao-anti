from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_hos import _CommonLocatorHos
from locators.common.hos_by import HosBy


class _LoginLocatorHos(_CommonLocatorHos):
    """
    鸿蒙 NEXT 平台登录页面元素定位器 (HarmonyOS ArkUI 专享架构)
    底层原生对齐 ArkUI 控件树标签 (Button, Text, TextInput, Checkbox, Image, Dialog 等)
    全面覆盖手机号登录、验证码登录、密码登录、协议勾选及系统密码弹窗。
    """

    PACKAGE_ID = _CommonLocatorHos.PACKAGE_ID

    APPLICATION_LOGO = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Image")

    # 手机号登录入口 (登录主页文案唯一，改用原生 text 单条件直查，减少 HypiumBy 链式 On.type RPC 往返)
    LOGIN_ENTRANCE = HosBy.text("手机号登录")

    # 有SIM卡时，显示一键登录按钮与入口
    ONE_KEY_LOGIN_ENTRANCE = HosBy.type_text("Text", "一键登录")

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
        "//__Common__/Row/Image",
    )

    # 密码与验证码登录模式切换按钮
    PASSWORD_LOGIN_SWITCH = HosBy.type_text("Text", "密码验证登录")
    CODE_LOGIN_SWITCH = HosBy.type_text("Text", "短信验证登录")
    PWD_AND_CODE = HosBy.within_type(
        "Row",
        text="(密码验证登录|短信验证登录)",
        target_type="Text",
        match_pattern=HosBy.MATCH_REGEXP,
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
        "//__Common__/Text[@text='密码验证登录' or @text='短信验证登录']",
    )

    # 验证码页面组件
    PLEASE_ENTER_VERIFICATION_CODE = HosBy.type_text("Text", "请填写验证码")
    # 验证码已发送 title
    VERIFICATION_CODE_SENT = HosBy.text_contains("验证码已发送", "Text")
    # 发送验证码手机号
    SEND_VERIFICATION_CODE_PHONE = (
        AppiumBy.XPATH,
        "(//Column/Text[2])[1]",
    )
    # 收不到验证码 text
    CANNOT_RECEIVE_VERIFICATION_CODE = HosBy.text_contains("收不到验证码", "Text")
    # 验证码倒计时 60s
    VERIFICATION_CODE_COUNTDOWN = HosBy.text_contains("重新获取", "Text")

    # 获取所有的独立验证码输入框集合
    CODE_EDIT_TEXTS = (
        AppiumBy.XPATH,
        "//__Common__/Stack/Row/Stack/Text",
    )

    # 协议同意勾选框（用上方主按钮与下方“我已阅读且同意”区间夹逼锁定紧邻 Image，避免单用 isBefore 误命中顶部返回/清空图标）
    AGREE_AND_LOGIN_BTN = HosBy.between_texts(
        after_text="^(密码验证登录|短信验证登录|一键登录|手机号登录)$",
        before_text="我已阅读且同意",
        target_type="Image",
        after_pattern=HosBy.MATCH_REGEXP,
        before_pattern=HosBy.MATCH_CONTAINS,
    )
    # 账密和一键登录协议文本（原生包含直查，摆脱脆弱的 Column 层级 XPath）
    AGREE_AND_LOGIN_TEXT = HosBy.text_contains("我已阅读且同意", "Text")

    # 反馈按钮
    FEEDBACK_BTN = HosBy.text_contains("反馈", "Text")

    # 未勾选协议点击登录后弹出容器
    AGREEMENT_BOTTOM_SHEET = (
        AppiumBy.XPATH,
        "//Dialog//__Common__/RelativeContainer",
    )
    AGREE_AND_CONTINUE_BTN = HosBy.type_text("Text", "同意并继续")
    CLOSE_BTN = (
        AppiumBy.XPATH, "//Stack[Text[@text='用户协议及隐私政策']]//Image"
    )
    USER_AGREEMENT_DESC = HosBy.id_only("prvacy_content")

    # 通用 Toast 提示 (用于校验错误信息)
    TOAST_MSG = (
        AppiumBy.XPATH,
        "//Toast | //Prompt | //Text[contains(@text, '验证码') or contains(@text, '错误') or contains(@text, '成功') or contains(@text, '失败')]",
    )

    @staticmethod
    def get_dynamic_toast_msg(expected_toast: str) -> tuple[str, str]:
        """按预期提示文案原生模糊包含直查 Toast（提速至 ~0.1s，大幅提升短时 Toast 捕获率）"""
        return HosBy.text_contains(expected_toast)

    # ======================================================
    # 系统级弹窗 - 使用已保存的账号/使用其他账号/手动输入
    # ======================================================
    AUTO_SAVE_PWD_TITLE = HosBy.id_only("AutoFillDialog_auto_fill_use_recommended_account")
    AUTO_SAVE_PWD_CANCEL = HosBy.id_only("AutoFillDialog_auto_fill_use_other_account")
    AUTO_SAVE_PWD_SAVE = HosBy.id_only("AutoFillDialog_auto_fill_self_input")
