from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_hos import _CommonLocatorHos
from locators.common.hos_by import HosBy


class _SettingsCenterLocatorHos(_CommonLocatorHos):
    """
    鸿蒙 NEXT 平台设置中心页面元素定位器 (HarmonyOS ArkUI 专享架构)
    入口路径：首页侧边栏 -> 设置中心 (NAV_ITEM_SETTINGS)
    对齐通用 ArkUI 组件树层级结构：
      - 顶部栏: TOP_IV_BACK_BTN, TOP_TV_TITLE ("设置中心")
      - 滚动列表: Scroll
      - 核心功能项: 账号安全, 消息通知, 隐私防护, 通用设置, 版本信息, 意见反馈, 联系我们
      - 底部操作项: 切换账号, 退出登录
    """
    PACKAGE_ID = _CommonLocatorHos.PACKAGE_ID

    # =========================================================================
    # 1. 顶部导航栏 (Top Bar)
    # =========================================================================
    TOP_IV_BACK_BTN = _CommonLocatorHos.TOP_IV_BACK_BTN                              # 左上角返回按钮
    TOP_TV_TITLE = _CommonLocatorHos.TOP_TV_TITLE                                    # 页面顶部标题 ("设置中心")

    # =========================================================================
    # 2. 主内容滚动容器 (Main Scroll Content)
    # =========================================================================
    CONTENT_SCROLL = HosBy.type_only("Scroll")                                        # 滚动内容容器 (原生 type 直查)

    # =========================================================================
    # 3. 核心功能条目 (采用 HosBy 原生文本直查，物理点击自动冒泡至整行容器，绕过 XPath 整树 Dump)
    # =========================================================================
    ITEM_ACCOUNT_SECURITY = HosBy.type_text("Text", "账号安全")                       # 【账号安全】条目
    ITEM_MESSAGE_NOTIFICATION = HosBy.type_text("Text", "消息通知")                   # 【消息通知】条目
    ITEM_PRIVACY_PROTECTION = HosBy.type_text("Text", "隐私防护")                     # 【隐私防护】条目
    ITEM_GENERAL_SETTING = HosBy.type_text("Text", "通用设置")                        # 【通用设置】条目

    # 版本信息区域
    VERSION_CONTAINER = (
        AppiumBy.XPATH,
        "//Row[.//Text[@text='版本信息']] | //Column[.//Text[@text='版本信息']]",
    )                                                                                # 版本信息外部容器
    ITEM_VERSION = HosBy.type_text("Text", "版本信息")                                # 【版本信息】条目
    VERSION_VALUE = HosBy.after_text("版本信息", "Text")                              # 版本号展示文本 (原生 isAfter 锚定，如 "11.1.20")

    ITEM_FEEDBACK = HosBy.type_text("Text", "意见反馈")                               # 【意见反馈】条目
    ITEM_CONTACT_US = HosBy.type_text("Text", "联系我们")                             # 【联系我们】条目

    # 条目内部通用标题
    TV_MENU_TITLE = (
        AppiumBy.XPATH,
        "//Text[@text='账号安全' or @text='消息通知' or @text='隐私防护' or @text='通用设置' or @text='版本信息' or @text='意见反馈' or @text='联系我们']",
    )                                                                                # 条目标题通用匹配

    # =========================================================================
    # 4. 底部账号操作按钮
    # =========================================================================
    SWITCH_ACCOUNT_BTN = HosBy.text("切换账号")                                       # 【切换账号】按钮
    LOGOUT_BTN = HosBy.text("退出登录")                                               # 【退出登录】按钮 (原生 text 直查)

    # 退出登录二次确认弹窗
    LOGOUT_CONFIRM_BTN = _CommonLocatorHos.DIALOG_CONFIRM_BTN                        # 确认退出按钮
    LOGOUT_CANCEL_BTN = _CommonLocatorHos.DIALOG_CANCEL_BTN                          # 取消退出按钮
    LOGOUT_SUCCESS_MSG = _CommonLocatorHos.TOAST_MSG                                 # 退出成功 Toast 消息
