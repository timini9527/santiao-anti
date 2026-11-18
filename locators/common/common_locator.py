from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By


class _CommonLoactroAndroid:
    """
    安卓 (Android) 平台通用公共元素定位器
    底层原生支持 Appium 自动化定位体系，兼顾沉浸式 TopBar、ActionBar 与通用子页面；
    采用高韧性 (Resilient) 多 ID 联合自愈定位机制，杜绝因页面重构或组件 ID 差异导致的查找失败。
    """

    PACKAGE_ID = 'com.santiaotalk.im:id'

    # --------------------------------------------------------------------------
    # 1. 顶部全局导航栏与通用返回键 (全量自愈定位)
    # --------------------------------------------------------------------------
    # 顶部左上角全局返回按钮 (兼顾 ActionBar、iv_back、back、back_bnt、ps_iv_left_back 等多页面返回组件)
    LEFT_TOP_BUTTON_ID = (
        AppiumBy.XPATH,
        (
            f"//*[@resource-id='{PACKAGE_ID}/action_back'"
            f" or @resource-id='{PACKAGE_ID}/iv_back'"
            f" or @resource-id='{PACKAGE_ID}/back'"
            f" or @resource-id='{PACKAGE_ID}/back_bnt'"
            f" or @resource-id='{PACKAGE_ID}/action_detail_back'"
            f" or @resource-id='{PACKAGE_ID}/ps_iv_left_back'"
            f" or @resource-id='{PACKAGE_ID}/bt_back'"
            f" or @content-desc='转到上一层级']"
        ),
    )

    # 通用左上角返回按钮
    TOP_IV_BACK_BTN = LEFT_TOP_BUTTON_ID

    # --------------------------------------------------------------------------
    # 2. 顶部中间标题体系 (Top Header Titles - 全量自愈定位)
    # --------------------------------------------------------------------------
    TOP_TV_TITLE_ID = f'{PACKAGE_ID}/tv_title'
    TOP_TV_TITLE = (
        AppiumBy.XPATH,
        (
            f"//*[@resource-id='{PACKAGE_ID}/tv_title'"
            f" or @resource-id='{PACKAGE_ID}/title_tv'"
            f" or @resource-id='{PACKAGE_ID}/title'"
            f" or @resource-id='{PACKAGE_ID}/set_name'"
            f" or @resource-id='{PACKAGE_ID}/toolbar_title'"
            f" or @resource-id='{PACKAGE_ID}/ps_tv_title']"
        ),
    )

    # --------------------------------------------------------------------------
    # 3. 顶部右上角功能/操作按钮 (Top Right Action Buttons - 确定/完成/发送/保存通用定位)
    # --------------------------------------------------------------------------
    # 顶部右上角通用操作按钮 (发送、完成、保存、确定等)
    RIGHT_TOP_BUTTON_ID = (
        AppiumBy.XPATH,
        (
            f"//*[@resource-id='{PACKAGE_ID}/action_send'"
            f" or @resource-id='{PACKAGE_ID}/action_btn'"
            f" or @resource-id='{PACKAGE_ID}/fb_action'"
            f" or @resource-id='{PACKAGE_ID}/edit_to'"
            f" or @resource-id='{PACKAGE_ID}/tv_save_qrcode']"
        ),
    )

    # 操作/确认按钮
    TOP_IV_ACTION_BTN = RIGHT_TOP_BUTTON_ID

    # --------------------------------------------------------------------------
    # 4. 弹窗/对话框确认与取消按钮 (Dialogs Confirm / Cancel)
    # --------------------------------------------------------------------------
    # 弹窗确认/积极按钮 (btn_positive / tv_confirm / btn_confirm)
    DIALOG_CONFIRM_BTN = (
        AppiumBy.XPATH,
        (
            f"//*[@resource-id='{PACKAGE_ID}/btn_positive'"
            f" or @resource-id='{PACKAGE_ID}/tv_confirm'"
            f" or @resource-id='{PACKAGE_ID}/btn_confirm']"
        ),
    )
    BTN_CONFIRM = DIALOG_CONFIRM_BTN
    TV_CONFIRM_BTN = DIALOG_CONFIRM_BTN

    # 弹窗取消/消极按钮 (cancel / btn_negative / tv_cancel / btn_cancel)
    DIALOG_CANCEL_BTN = (
        AppiumBy.XPATH,
        (
            f"//*[@resource-id='{PACKAGE_ID}/cancel'"
            f" or @resource-id='{PACKAGE_ID}/btn_negative'"
            f" or @resource-id='{PACKAGE_ID}/tv_cancel'"
            f" or @resource-id='{PACKAGE_ID}/btn_cancel']"
        ),
    )
    CANCEL_BUTTON_ID = DIALOG_CANCEL_BTN
    BTN_CANCEL = DIALOG_CANCEL_BTN
    TV_CANCEL_BTN = DIALOG_CANCEL_BTN

    # --------------------------------------------------------------------------
    # 5. 全局轻量浮层与 Toast 提示
    # --------------------------------------------------------------------------
    # Toast 提示 (兼容应用内自定义 Toast 与系统级 Toast)
    TOAST_MSG = (
        AppiumBy.XPATH,
        f"//*[@resource-id='{PACKAGE_ID}/toast_message' or @class='android.widget.Toast']",
    )


from core.locator_manager import DynamicLocatorMeta
from locators.common.common_locator_hos import _CommonLocatorHos
from locators.common.common_locator_ios import _CommonLocatorIos


class CommonLocator(_CommonLocatorIos, _CommonLoactroAndroid, _CommonLocatorHos, metaclass=DynamicLocatorMeta):
    """跨端公共定位器（支持 IDE Ctrl + 鼠标左键直接跳转定义，运行时按设备平台动态分发）"""

    _android_cls = _CommonLoactroAndroid
    _harmony_cls = _CommonLocatorHos
    _ios_cls = _CommonLocatorIos




