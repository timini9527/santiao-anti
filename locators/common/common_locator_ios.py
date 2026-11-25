# -*- coding: utf-8 -*-
"""
iOS 平台通用公共元素定位器 (XCUITest / WebDriverAgent 原生架构)
涵盖全局顶部导航栏、返回按钮、标题系统、右上角操作按钮、弹窗确认/取消、Toast 提示及动态参数化定位工厂。
"""
from typing import Tuple
from appium.webdriver.common.appiumby import AppiumBy


class _CommonLocatorIos:
    """
    iOS 平台通用公共元素定位器 (XCUITest / WebDriverAgent 原生架构)
    底层原生支持 Apple XCUITest 自动化定位体系，全面覆盖 iOS 原生 NavigationBar、
    系统及业务弹窗 (Alert / ActionSheet / Sheet)、Toast 浮层与动态参数化查找。
    """

    # iOS 应用 Bundle ID (与 config/devices.yaml 中 appium:bundleId 保持一致)
    PACKAGE_ID = "com.baimo.santiao"

    # 静态文本类控件类型集合
    _TEXT_TYPES = "{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}"
    # 可点击类控件类型集合
    _TAP_TYPES = "{'XCUIElementTypeButton', 'XCUIElementTypeStaticText'}"

    # --------------------------------------------------------------------------
    # 1. 顶部全局导航栏与通用返回键 (Top Navigation Bar & Back Actions)
    # --------------------------------------------------------------------------
    # 顶部左上角全局返回按钮 (兼顾 NavigationBar 首个按钮及 label/name 匹配)
    LEFT_TOP_BUTTON_ID = (
        AppiumBy.XPATH,
        (
            "//XCUIElementTypeNavigationBar/XCUIElementTypeButton[1]"
            " | //XCUIElementTypeButton[@name='ic home left drawer close']"
            
        ),
    )

    # 通用左上角返回按钮
    TOP_IV_BACK_BTN = LEFT_TOP_BUTTON_ID
    TOP_BACK_BTN = LEFT_TOP_BUTTON_ID
    TOP_BAR_BACK_BTN = LEFT_TOP_BUTTON_ID

    # --------------------------------------------------------------------------
    # 2. 顶部中间标题体系 (Top Header Titles)
    # --------------------------------------------------------------------------
    # 主页顶部中间标题 (应用名 "三条" 或会话状态)
    TOP_MIDDLE_TITLE_HOME = (
        AppiumBy.XPATH,
        "//NavigationBar/StaticText",
    )
    # 主页中间标题消息总条数
    TOP_MESSAGE_COUNT_TEXT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar//XCUIElementTypeStaticText[contains(@name, '三条') or contains(@label, '三条')]/following-sibling::XCUIElementTypeStaticText",
    )

    # 子页面/通用页面顶部标题 (如 "聊天信息"、"联系人详情"、"设置中心")
    TOP_TV_TITLE = (
        AppiumBy.XPATH,
        "//XCUIElementTypeNavigationBar/XCUIElementTypeStaticText[@visible='true'][1]"
        " | //XCUIElementTypeOther/XCUIElementTypeStaticText[@visible='true']"
    )
    TOP_BAR_TITLE_TV = TOP_TV_TITLE

    # --------------------------------------------------------------------------
    # 3. 顶部右上角功能/操作按钮 (Top Right Action Buttons)
    # --------------------------------------------------------------------------
    # 顶部右上角通用操作按钮 (发送、完成、保存、确定等)
    RIGHT_TOP_BUTTON_ID = (
        AppiumBy.XPATH,
        (
            "(//XCUIElementTypeNavigationBar//XCUIElementTypeButton)[last()]"
            " | //XCUIElementTypeNavigationBar//XCUIElementTypeButton[@name='确定' or @name='完成' or @name='发送' or @name='保存' or @label='确定' or @label='完成' or @label='发送' or @label='保存']"
        ),
    )

    # 操作/确认按钮
    TOP_IV_ACTION_BTN = RIGHT_TOP_BUTTON_ID
    TOP_IV_CONFIRM_BTN = RIGHT_TOP_BUTTON_ID
    TOP_FB_ACTION_BTN = RIGHT_TOP_BUTTON_ID
    TOP_BAR_EDIT_TO_BTN = RIGHT_TOP_BUTTON_ID

    # --------------------------------------------------------------------------
    # 4. 弹窗/对话框确认与取消按钮 (Dialogs Confirm / Cancel - 原生 Class Chain + Predicate 极速架构)
    # --------------------------------------------------------------------------
    # 消极/取消类按钮通用谓词 (限定 visible == 1，防止后台隐藏页面的“关闭/取消”按钮抢占 [-1] 锚点)
    _DIALOG_CANCEL_PRED = (
        "type == 'XCUIElementTypeButton' AND visible == 1 AND ("
        "label IN {'取消', '关闭'} "
        "OR name IN {'取消', '关闭'}"
        ")"
    )
    # 确认/积极类按钮通用谓词 (用于系统单按钮弹窗等无消极按钮兜底)
    _DIALOG_CONFIRM_PRED = (
        "type == 'XCUIElementTypeButton' AND visible == 1 AND ("
        "label IN {'确定', '确认', '删除', '退出登录'} "
        "OR name IN {'确定', '确认', '删除', '退出登录'}"
        ")"
    )

    # 最内层自定义确认弹窗容器：通过 [$...$] 子孙谓词锁定包含取消类按钮的最内层卡片 Other ([-1])
    _CUSTOM_DIALOG_CHAIN = f"**/XCUIElementTypeOther[${_DIALOG_CANCEL_PRED}$][-1]"

    DIALOG_ID = _CUSTOM_DIALOG_CHAIN
    # 自定义业务确认弹窗根容器 (IOS_CLASS_CHAIN 原生引擎直达，免整树 XML 序列化)
    DIALOG_CONTAINER = (AppiumBy.IOS_CLASS_CHAIN, _CUSTOM_DIALOG_CHAIN)
    # 系统原生 Alert / ActionSheet / Sheet 容器
    SYSTEM_DIALOG_CONTAINER = (
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeAlert', 'XCUIElementTypeActionSheet', 'XCUIElementTypeSheet'}",
    )

    # 通用弹窗标题 (命中自定义弹窗容器下首个 TextView；若弹窗采用 StaticText 或 Alert，推荐走 CommonPage.get_dialog_title)
    DIALOG_CONFIRM_TITLE = (
        AppiumBy.IOS_CLASS_CHAIN,
        f"{_CUSTOM_DIALOG_CHAIN}/XCUIElementTypeTextView[1]",
    )

    # 通用弹窗确认按钮：直接取最顶层可见确认按钮 [-1]（iOS 模态弹窗恒位于底层页面之后，免全树 Other[$...$] 子树回溯且不点穿底层）
    DIALOG_CONFIRM_BTN = (
        AppiumBy.IOS_CLASS_CHAIN,
        "**/XCUIElementTypeButton[`visible == 1 AND (label IN {'确定', '确认', '删除', '退出登录'} OR name IN {'确定', '确认', '删除', '退出登录'})`][-1]",
    )
    # 系统弹窗 / 单按钮提示弹窗确认按钮兜底
    SYSTEM_DIALOG_CONFIRM_BTN = (AppiumBy.IOS_PREDICATE, _DIALOG_CONFIRM_PRED)
    BTN_CONFIRM = DIALOG_CONFIRM_BTN
    TV_CONFIRM_BTN = DIALOG_CONFIRM_BTN

    # 弹窗取消/消极按钮
    DIALOG_CANCEL_BTN = (AppiumBy.IOS_PREDICATE, _DIALOG_CANCEL_PRED)
    CANCEL_BUTTON_ID = DIALOG_CANCEL_BTN
    BTN_CANCEL = DIALOG_CANCEL_BTN
    TV_CANCEL_BTN = DIALOG_CANCEL_BTN

    # 容器内子元素定位器 (配合 CommonPage 先锁容器再查子元素，彻底隔离底层页面同名按钮)
    DIALOG_CHILD_TITLE = (
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeTextView', 'XCUIElementTypeStaticText'} AND visible == 1",
    )
    DIALOG_CHILD_BUTTONS = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND visible == 1",
    )

    @classmethod
    def get_dialog_child_button_by_text(cls, btn_text: str) -> Tuple[str, str]:
        """构造弹窗容器内部按按钮文案匹配的 Predicate 定位器"""
        return (
            AppiumBy.IOS_PREDICATE,
            f"type == 'XCUIElementTypeButton' AND visible == 1 AND (name == '{btn_text}' OR label == '{btn_text}')",
        )

    # --------------------------------------------------------------------------
    # 5. 全局轻量浮层与 Toast 提示
    # --------------------------------------------------------------------------
    # Toast 提示 (覆盖带 ic_toast_* 图标的悬浮提示框、顶层 Window 浮层及系统级 Alert 提示)
    TOAST_MSG = (
        AppiumBy.XPATH,
        (
            "//XCUIElementTypeImage[contains(@name, 'toast')]/following-sibling::XCUIElementTypeStaticText"
            " | //XCUIElementTypeOther[XCUIElementTypeImage[contains(@name, 'toast')]]//XCUIElementTypeStaticText"
            " | //XCUIElementTypeAlert//XCUIElementTypeStaticText"
            " | //XCUIElementTypeWindow[last()]//XCUIElementTypeStaticText"
        ),
    )

    # --------------------------------------------------------------------------
    # 6. 动态参数化精准元素定位器工厂 (Parameterized Locators)
    # --------------------------------------------------------------------------

    @classmethod
    def get_title_by_text(cls, title_text: str) -> Tuple[str, str]:
        """
        根据指定标题文本精准定位导航栏或页面中的标题元素
        :param title_text: 页面标题文本内容
        :return: (AppiumBy.IOS_PREDICATE, predicate_expression)
        """
        return (
            AppiumBy.IOS_PREDICATE,
            f"type IN {cls._TEXT_TYPES} AND (name == '{title_text}' OR label == '{title_text}')",
        )

    @classmethod
    def get_button_by_text(cls, btn_text: str) -> Tuple[str, str]:
        """
        根据文本精准定位通用按钮 (支持 Button 与具备交互语义的 StaticText)
        :param btn_text: 按钮显示文本
        :return: (AppiumBy.IOS_PREDICATE, predicate_expression)
        """
        return (
            AppiumBy.IOS_PREDICATE,
            f"type IN {cls._TAP_TYPES} AND (name == '{btn_text}' OR label == '{btn_text}')",
        )

    @classmethod
    def get_dialog_action_by_text(cls, action_text: str) -> Tuple[str, str]:
        """
        精准定位指定弹窗内部的操作按钮或文本
        :param action_text: 操作项文本 (如 '清空聊天记录', '确认删除')
        :return: (AppiumBy.XPATH, xpath_expression)
        """
        return (
            AppiumBy.XPATH,
            f"(//XCUIElementTypeAlert | //XCUIElementTypeActionSheet | //XCUIElementTypeSheet)//XCUIElementTypeButton[@name='{action_text}' or @label='{action_text}']",
        )

    @classmethod
    def get_dynamic_toast_msg(cls, expected_toast: str) -> Tuple[str, str]:
        """
        根据预期文本动态模糊匹配 Toast 提示内容
        :param expected_toast: 预期的 Toast 文本片段
        :return: (AppiumBy.IOS_PREDICATE, predicate_expression)
        """
        return (
            AppiumBy.IOS_PREDICATE,
            f"type IN {cls._TEXT_TYPES} AND (label CONTAINS '{expected_toast}' OR name CONTAINS '{expected_toast}' OR value CONTAINS '{expected_toast}')",
        )
