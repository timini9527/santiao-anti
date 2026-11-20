# -*- coding: utf-8 -*-
"""
iOS 平台设置中心页面元素定位器 (XCUITest / WebDriverAgent 原生架构)
按 XCUITest 定位优先级组织，确保查询速度与稳定性：
  1. ACCESSIBILITY_ID：有唯一 name 属性的菜单项及功能入口直接哈希直达
  2. IOS_PREDICATE / IOS_CLASS_CHAIN：原生引擎过滤集合、按钮与滚动容器
  3. XPATH：仅用于需要同级/上下文锚定的版本号等动态文本节点
"""
from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_ios import _CommonLocatorIos


class _SettingsCenterLocatorIos(_CommonLocatorIos):
    """
    iOS 平台设置中心页面元素定位器
    入口路径：首页侧边栏 -> 设置中心 (NAV_ITEM_SETTINGS)
    涵盖：
      - 顶部栏: TOP_IV_BACK_BTN, TOP_TV_TITLE ("设置中心")
      - 滚动列表: ScrollView / Table
      - 核心功能项: 账号安全, 消息通知, 隐私防护, 通用设置, 版本信息, 意见反馈, 联系我们
      - 底部操作项: 切换账号, 退出登录
    """
    PACKAGE_ID = _CommonLocatorIos.PACKAGE_ID

    # =========================================================================
    # 1. 顶部导航栏 (Top Bar)
    # =========================================================================
    TOP_IV_BACK_BTN = _CommonLocatorIos.TOP_IV_BACK_BTN                              # 左上角返回按钮
    TOP_TV_TITLE = _CommonLocatorIos.TOP_TV_TITLE                                    # 页面顶部标题 ("设置中心")

    # =========================================================================
    # 2. 主内容滚动容器 (Main Scroll Content)
    # =========================================================================
    CONTENT_SCROLL = (                                                               # 滚动内容容器 (ScrollView / Table)
        AppiumBy.IOS_CLASS_CHAIN,
        "**/XCUIElementTypeScrollView",
    )                 

    # =========================================================================
    # 3. 核心功能条目 (原生 ACCESSIBILITY_ID 极速直达)
    # =========================================================================
    ITEM_ACCOUNT_SECURITY = (AppiumBy.ACCESSIBILITY_ID, "账号安全")                   # 【账号安全】条目
    ITEM_MESSAGE_NOTIFICATION = (AppiumBy.ACCESSIBILITY_ID, "消息通知")               # 【消息通知】条目
    ITEM_PRIVACY_PROTECTION = (AppiumBy.ACCESSIBILITY_ID, "隐私防护")                 # 【隐私防护】条目
    ITEM_GENERAL_SETTING = (AppiumBy.ACCESSIBILITY_ID, "通用设置")                    # 【通用设置】条目

    # 版本信息区域
    VERSION_CONTAINER = (                                                            # 版本信息外部容器
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[XCUIElementTypeStaticText[@name='版本信息' or @label='版本信息']]"
        )
    ITEM_VERSION = (AppiumBy.ACCESSIBILITY_ID, "版本信息")                            # 【版本信息】条目
    VERSION_VALUE = (                                                                # 版本号展示文本 (如 "11.1.20")
        AppiumBy.XPATH,
        "//XCUIElementTypeStaticText[@name='版本信息' or @label='版本信息']/following-sibling::XCUIElementTypeOther/XCUIElementTypeStaticText[1]",
    )                                                                               

    ITEM_FEEDBACK = (AppiumBy.ACCESSIBILITY_ID, "意见反馈")                          # 【意见反馈】条目
    ITEM_CONTACT_US = (AppiumBy.ACCESSIBILITY_ID, "联系我们")                        # 【联系我们】条目

    # 条目内部通用标题
    TV_MENU_TITLE = (                                                               # 条目标题通用谓词
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name IN {'账号安全', '消息通知', '隐私防护', '通用设置', '版本信息', '意见反馈', '联系我们'}",
    )                          

    # =========================================================================
    # 4. 底部账号操作按钮 (兼容 Button 与 StaticText 实现)
    # =========================================================================
    SWITCH_ACCOUNT_BTN = (                                                          # 【切换账号】按钮
        AppiumBy.IOS_CLASS_CHAIN,
        "**/XCUIElementTypeButton[`name == '切换账号'`]",
    )                     
    LOGOUT_BTN = (                                                                  # 【退出登录】按钮
        AppiumBy.IOS_CLASS_CHAIN,
        "**/XCUIElementTypeButton[`name == '退出登录'`]",
    )            

    # 退出登录二次确认弹窗
    LOGOUT_CONFIRM_BTN = _CommonLocatorIos.DIALOG_CONFIRM_BTN                        # 确认退出按钮
    LOGOUT_CANCEL_BTN = _CommonLocatorIos.DIALOG_CANCEL_BTN                          # 取消退出按钮
    LOGOUT_SUCCESS_MSG = _CommonLocatorIos.TOAST_MSG                                 # 退出成功 Toast 消息
