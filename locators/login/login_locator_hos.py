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

    # 登录表单全部输入框集合（原生 TextInput 直查：短信模式 1 个、密码模式 2 个，用于快速判定当前登录模式）
    FORM_INPUTS = HosBy.type_only("TextInput")

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

    # --------------------------------------------------------------------------
    # 短信验证码人机验证弹窗 (ArkUI Web 组件内部无障碍透传节点，类型为小驼峰)
    # --------------------------------------------------------------------------
    # 人机验证提示文案 (用于探测弹窗是否存在及兜底坐标锚点)
    HUMAN_VERIFY_TITLE = HosBy.text_regex("^(请点击按钮进行验证|点击左侧灰色按钮)$", "staticText")
    # 人机验证核心点击按钮 (Web 组件内的 labelText 按钮节点，原生直查避开全树 XML XPath)
    HUMAN_VERIFY_BTN = HosBy.type_only("labelText")
    # 人机验证指向按钮的左侧箭头图标
    HUMAN_VERIFY_ARROW_ICON = HosBy.type_text("image", "左侧箭头")
    # 人机验证弹窗 - 关闭按钮 (Web 透传小写 image，与 ArkUI 原生大写 Image 隔离)
    HUMAN_VERIFY_CLOSE_BTN = HosBy.type_text("image", "关闭")
    # 人机验证弹窗 - 刷新按钮
    HUMAN_VERIFY_REFRESH_BTN = HosBy.type_text("image", "刷新")

    # 协议同意勾选框（仅用表单内“密码验证登录/短信验证登录”与“我已阅读且同意”区间夹逼锁定勾选框 Image；
    # 严禁包含登录主页 NavBar 的“手机号登录/一键登录”，否则在 Navigation 栈中会先命中背景页按钮而误点顶部返回图标）
    AGREE_AND_LOGIN_BTN = HosBy.between_texts(
        after_text="^(密码验证登录|短信验证登录)$",
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
    # 协议拦截弹窗 - 标题文本（限定在 Dialog 弹窗内，避免命中底层 NavDestination 的同名 id="title"）
    AGREEMENT_POPUP_TITLE = (
        AppiumBy.XPATH,
        "//Dialog//Text[@id='title']",
    )
    AGREE_AND_CONTINUE_BTN = HosBy.type_text("Text", "同意并继续")
    CLOSE_BTN = (
        AppiumBy.XPATH, "//Stack[Text[@text='用户协议及隐私政策']]//Image"
    )
    USER_AGREEMENT_DESC = HosBy.id_only("prvacy_content")

    # 通用 Toast 提示（复用 _CommonLocatorHos，移除原先宽泛的 //Text[contains(@text, '验证码')] 防止误抓页面静态副标题）
    TOAST_MSG = _CommonLocatorHos.TOAST_MSG
    # 短信验证码流控提示（原生模糊包含直查，覆盖触发天极流控 / 触发天级流控 / 触发小时级流控）
    RATE_LIMIT_TOAST = HosBy.text_contains("流控", "Text")

    @staticmethod
    def get_dynamic_toast_msg(expected_toast: str) -> tuple[str, str]:
        """按预期提示文案原生精确直查 Toast（避免模糊包含误抓页面静态文本，如 '验证码已发送至(0086)...'）"""
        return HosBy.text(expected_toast)

    # ======================================================
    # 系统级弹窗 - 使用已保存的账号/使用其他账号/手动输入
    # ======================================================
    AUTO_SAVE_PWD_TITLE = HosBy.id_only("AutoFillDialog_auto_fill_use_recommended_account")
    AUTO_SAVE_PWD_CANCEL = HosBy.id_only("AutoFillDialog_auto_fill_use_other_account")
    AUTO_SAVE_PWD_SAVE = HosBy.id_only("AutoFillDialog_auto_fill_self_input")
