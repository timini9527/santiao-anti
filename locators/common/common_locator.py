
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By


class CommonLocator:

    PACKAGE_ID = 'com.santiaotalk.im:id'

    # 顶部左上角按钮返回
    LEFT_TOP_BUTTON_ID = (AppiumBy.ID, f'{PACKAGE_ID}/action_back')

    # 顶部中间标题
    TOP_MIDDLE_TITLE_HOME = (AppiumBy.ID, f'{PACKAGE_ID}/set_name')
    
    # 顶部右上角按钮
    RIGHT_TOP_BUTTON_ID = (AppiumBy.ID, f'{PACKAGE_ID}/action_send')

    # 底部弹窗取消按钮
    CANCEL_BUTTON_ID = (AppiumBy.ID, f'{PACKAGE_ID}/cancel')

    # 其他页面的顶部按钮
    # 左上角返回按钮 通用
    TOP_IV_BACK_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/iv_back')
    # 右上角完成按钮 通用
    TOP_FB_ACTION_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/fb_action')
    # 中间标题 通用
    TOP_TV_TITLE_ID = f'{PACKAGE_ID}/tv_title'
    TOP_TV_TITLE = (AppiumBy.ID, TOP_TV_TITLE_ID)

    # Toast 提示 (兼容应用内 ID 定位和系统级级 Toast 定位)
    TOAST_MSG = (AppiumBy.XPATH, f"//*[@resource-id='{PACKAGE_ID}/toast_message' or @class='android.widget.Toast']")

    # 弹窗/对话框 确认与取消按钮 (来自重构移植)
    DIALOG_CONFIRM_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/btn_positive')
    DIALOG_CANCEL_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/btn_negative')

    # 文本确认与取消按钮 (来自重构移植)
    TV_CONFIRM_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/tv_confirm')
    TV_CANCEL_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/tv_cancel')

    # 顶部返回按钮
    TOP_BACK_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/back_bnt')

    # TOPBar 3个控件通用定位
    # 左上角返回按钮 通用
    TOP_BAR_BACK_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/back')
    # 右上角完成按钮 通用
    TOP_BAR_EDIT_TO_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/edit_to')
    # 中间标题 通用
    TOP_BAR_TITLE_TV = (AppiumBy.ID, f'{PACKAGE_ID}/title_tv')


# class HomeLocatorIOS(HomeLocatorBase):
#     """iOS 专属定位"""
#     SEARCH_BTN = (AppiumBy.ACCESSIBILITY_ID, "SearchButton")
#     EMOJI_BTN = (AppiumBy.ACCESSIBILITY_ID, "EmojiButton")
#     MESSAGE_LIST = (AppiumBy.IOS_CLASS_CHAIN, "**/XCUIElementTypeTable[`name == 'MessageList'`]")
#     HOME_TAB = (AppiumBy.IOS_PREDICATE, "label == '首页' AND type == 'XCUIElementTypeButton'")
#
# class HomeLocatorHarmony(HomeLocatorBase):
#     """
#     鸿蒙 (HarmonyOS) 专属定位
#     鸿蒙的 Appium 驱动 (appium-ohos-driver) 通常依赖 id 或 componentType
#     """
#     SEARCH_BTN = (AppiumBy.ID, "search_btn")
#     EMOJI_BTN = (AppiumBy.ID, "emoji_btn")
#     MESSAGE_LIST = (AppiumBy.ID, "message_list")
#     HOME_TAB = (AppiumBy.XPATH, "//Text[@text='首页']")










