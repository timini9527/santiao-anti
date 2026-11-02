
from typing import Tuple
from appium.webdriver.common.appiumby import AppiumBy


class CommonLocatorHos:
    """
    鸿蒙 NEXT 平台通用公共元素定位器 (HarmonyOS ArkUI 专享架构)
    底层深度原生对齐 ArkUI 组件树标签 (Navigation, NavDestination, Stack, Column, Row, Text, Button, Image, Dialog 等)
    全面覆盖顶部导航条、全局返回键、主页/子页面标题、操作按钮、系统与业务弹窗确认/取消、Toast 提示及动态参数化定位工厂。
    """

    # --------------------------------------------------------------------------
    # 1. 顶部全局导航栏与通用返回键 (Top Navigation Bar & Back Actions)
    # --------------------------------------------------------------------------

    # 顶部左上角全局返回按钮 (兼顾 Navigation / NavDestination 容器与多级嵌套树)
    # (//NavDestinationContent/Stack/Column/Row/Image)[1] | (//NavDestinationContent/Column/__Common__/Stack/Row/Column/Row/Stack/Image)[1] | (//NavDestinationContent/Stack/__Common__/Stack/Row/Column/Row/Stack/Image)[1] | (//NavDestinationContent/Stack/Column/Stack/Row/Column/Row/Stack/Image)[1] | (//NavDestinationContent/Stack/Row/Image)[1] | (//NavDestinationContent/Column/Stack/Row/Column/Row/Stack/Image)[1] | (//NavDestinationContent/Stack/Stack/__Common__/Stack/Row/Column/Row/Image)[1]
    LEFT_TOP_BUTTON_ID = (
        AppiumBy.XPATH,
        (
            "(//NavDestinationContent/Stack/Column/Row/Image)[1]"
            " | (//NavDestinationContent/Column/__Common__/Stack/Row/Column/Row/Stack/Image)[1]"
            " | (//NavDestinationContent/Stack/__Common__/Stack/Row/Column/Row/Stack/Image)[1]"
            " | (//NavDestinationContent/Stack/Column/Stack/Row/Column/Row/Stack/Image)[1]"
            " | (//NavDestinationContent/Stack/Row/Image)[1]"
            " | (//NavDestinationContent/Column/Stack/Row/Column/Row/Stack/Image)[1]"
            " | (//NavDestinationContent/Stack/Stack/__Common__/Stack/Row/Column/Row/Image)[1]"
        ),
    )

    # 通用左上角返回图标 (子页面与标准导航栏统一映射)
    TOP_IV_BACK_BTN = LEFT_TOP_BUTTON_ID
    TOP_BACK_BTN = LEFT_TOP_BUTTON_ID
    TOP_BAR_BACK_BTN = LEFT_TOP_BUTTON_ID

    # --------------------------------------------------------------------------
    # 2. 顶部标题体系 (Top Header Titles)
    # --------------------------------------------------------------------------

    # 主页顶部中间标题 (应用名 "三条" 或会话状态)
    TOP_MIDDLE_TITLE_HOME = (
        AppiumBy.XPATH,
        "//Navigation//Text[contains(@text, '三条')]",
    )
    # 主页中间标题消息总条数
    TOP_MESSAGE_COUNT_TEXT = (
        AppiumBy.XPATH,
        "//Navigation//Text[@text='三条']/following-sibling::Text",
    )

    # 子页面/通用页面顶部标题 (如 "聊天信息"、"联系人详情"、"设置中心")
    TOP_TV_TITLE = (
        AppiumBy.XPATH,
        "(//NavDestination//Swiper//RelativeContainer/Text)[1] | //*[@id='title']",
    )
    TOP_BAR_TITLE_TV = TOP_TV_TITLE

    # --------------------------------------------------------------------------
    # 3. 顶部右上角功能/操作按钮 (Top Right Action Buttons)
    # --------------------------------------------------------------------------

    # 顶部右上角通用功能按钮 (如发送、完成、保存、更多菜单等)
    # (//NavDestination//Row[1]//Image)[last()] | (//Navigation//Row[1]//Image)[last()] | //NavDestinationContent//Stack/Row//Text[@text='确定']
    RIGHT_TOP_BUTTON_ID = (
        AppiumBy.XPATH,
        "(//NavDestination//Row[1]//Image)[last()] "
        "| (//Navigation//Row[1]//Image)[last()] "
        "| //NavDestinationContent//Stack/Row//Text[@text='确定']",
    )
    TOP_IV_CONFIRM_BTN = RIGHT_TOP_BUTTON_ID
    TOP_FB_ACTION_BTN = RIGHT_TOP_BUTTON_ID
    TOP_BAR_EDIT_TO_BTN = RIGHT_TOP_BUTTON_ID


    # --------------------------------------------------------------------------
    # 4. 通用弹窗与对话框交互 (Dialogs & Confirm/Cancel Buttons)
    # --------------------------------------------------------------------------
    # 二次弹窗
    DIALOG_ID = "//Dialog/Column/Stack/Column"
    DIALOG_CONTAINER = (AppiumBy.XPATH, f"//Dialog/Column/Stack/Column")

    # 二次弹窗标题
    DIALOG_CONFIRM_TITLE = (AppiumBy.XPATH, "//Dialog//Column/Text")
    # 二次弹窗确认按钮 (如 "确定"、"确认"、"删除")
    DIALOG_CONFIRM_BTN = (
        AppiumBy.XPATH,
        "//Dialog//Row/Text[@text='确定' or @text='确认' or @text='删除']",
    )
    BTN_CONFIRM = DIALOG_CONFIRM_BTN
    TV_CONFIRM_BTN = DIALOG_CONFIRM_BTN

    # 二次弹窗取消按钮 (如 "取消"、"关闭")
    DIALOG_CANCEL_BTN = (
        AppiumBy.XPATH,
        "//Dialog//Text[@text='取消' or @text='关闭']",
    )
    CANCEL_BUTTON_ID = DIALOG_CANCEL_BTN
    BTN_CANCEL = DIALOG_CANCEL_BTN
    TV_CANCEL_BTN = DIALOG_CANCEL_BTN


    # --------------------------------------------------------------------------
    # 5. 全局轻量浮层与 Toast 提示 (Toast & PromptAction)
    # --------------------------------------------------------------------------

    # 鸿蒙 ArkUI 原生 Toast / PromptAction 提示信息
    TOAST_MSG = (
        AppiumBy.XPATH,
        "//PromptAction//Text | //Toast//Text | //*[@type='PromptAction' or @type='Toast']//Text | //*[@id='toast_message']",
    )

    # --------------------------------------------------------------------------
    # 6. 动态参数化精准元素定位器工厂 (Parameterized Locators)
    # --------------------------------------------------------------------------

    @classmethod
    def get_title_by_text(cls, title_text: str) -> Tuple[str, str]:
        """
        根据指定标题文本精准定位导航栏或页面中的标题 Text 元素
        :param title_text: 页面标题文本内容
        :return: (AppiumBy.XPATH, xpath_expression)
        """
        return (
            AppiumBy.XPATH,
            f"//NavDestination//Text[@text='{title_text}'] | //Navigation//Text[@text='{title_text}'] | //Text[@text='{title_text}']",
        )

    @classmethod
    def get_button_by_text(cls, btn_text: str) -> Tuple[str, str]:
        """
        根据文本精准定位通用按钮 (支持 Button 与具备交互语义的 Text 组件)
        :param btn_text: 按钮显示文本
        :return: (AppiumBy.XPATH, xpath_expression)
        """
        return (
            AppiumBy.XPATH,
            f"//Button[@text='{btn_text}'] | //Text[@text='{btn_text}' and (@clickable='true' or parent::Button)]",
        )

    @classmethod
    def get_dialog_action_by_text(cls, action_text: str) -> Tuple[str, str]:
        """
        精准定位指定弹窗 (Dialog) 内部的操作按钮或文本，避免误触底层页面元素
        :param action_text: 操作项文本 (如 '清空聊天记录', '确认删除')
        :return: (AppiumBy.XPATH, xpath_expression)
        """
        return (
            AppiumBy.XPATH,
            f"//Dialog//Button[@text='{action_text}'] | //Dialog//Text[@text='{action_text}'] | //Dialog//Column[@clickable='true' and .//Text[@text='{action_text}']]",
        )











