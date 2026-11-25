from appium.webdriver.common.appiumby import AppiumBy
from core.locator_manager import DynamicLocatorMeta
from locators.common.common_locator import _CommonLoactroAndroid
from locators.home.left_menus.settings_center_locator_hos import _SettingsCenterLocatorHos
from locators.home.left_menus.settings_center_locator_ios import _SettingsCenterLocatorIos


class _SettingsCenterLocatorAndroid(_CommonLoactroAndroid):
    """
    安卓 (Android) 平台设置中心页面元素定位器
    入口路径：首页侧边栏 -> 设置中心 (nav_item_settings)
    基于最新 UI 树层级构建：
      - 顶部栏: iv_back, tv_title ("设置中心")
      - 滚动列表: content_scroll
      - 核心功能项: 账号安全, 消息通知, 隐私防护, 通用设置, 版本信息, 意见反馈, 联系我们
      - 底部操作项: 切换账号, 退出登录
    """
    PACKAGE_ID = _CommonLoactroAndroid.PACKAGE_ID

    # =========================================================================
    # 1. 顶部导航栏 (Top Bar)
    # =========================================================================
    TOP_IV_BACK_BTN = _CommonLoactroAndroid.TOP_IV_BACK_BTN                         # 左上角返回按钮
    TOP_TV_TITLE = _CommonLoactroAndroid.TOP_TV_TITLE                               # 页面顶部标题 ("设置中心")

    # =========================================================================
    # 2. 主内容滚动容器 (Main Scroll Content)
    # =========================================================================
    CONTENT_SCROLL = (AppiumBy.ID, f'{PACKAGE_ID}/content_scroll')                  # 滚动内容容器 (ScrollView)

    # =========================================================================
    # 3. 核心功能条目容器 (ViewGroups)
    # =========================================================================
    ITEM_ACCOUNT_SECURITY = (AppiumBy.ID, f'{PACKAGE_ID}/item_account_security')            # 【账号安全】条目
    ITEM_MESSAGE_NOTIFICATION = (AppiumBy.ID, f'{PACKAGE_ID}/item_message_notification')    # 【消息通知】条目
    ITEM_PRIVACY_PROTECTION = (AppiumBy.ID, f'{PACKAGE_ID}/item_privacy_protection')        # 【隐私防护】条目
    ITEM_GENERAL_SETTING = (AppiumBy.ID, f'{PACKAGE_ID}/item_general_setting')              # 【通用设置】条目

    # 版本信息区域
    VERSION_CONTAINER = (AppiumBy.ID, f'{PACKAGE_ID}/version_container')                    # 版本信息外部容器 (FrameLayout)
    ITEM_VERSION = (AppiumBy.ID, f'{PACKAGE_ID}/item_version')                              # 【版本信息】条目容器 (ViewGroup)
    VERSION_VALUE = (AppiumBy.ID, f'{PACKAGE_ID}/version_value')                            # 版本号展示文本 (如 "11.1.20")

    ITEM_FEEDBACK = (AppiumBy.ID, f'{PACKAGE_ID}/item_feedback')                            # 【意见反馈】条目
    ITEM_CONTACT_US = (AppiumBy.ID, f'{PACKAGE_ID}/item_contact_us')                        # 【联系我们】条目

    # 条目内部通用标题 (各 ViewGroup 下的子 TextView)
    TV_MENU_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_menu_title')                            # 条目标题通用 ID

    # =========================================================================
    # 4. 底部账号操作按钮
    # =========================================================================
    SWITCH_ACCOUNT_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/switch_account')                 # 【切换账号】按钮 (TextView)
    LOGOUT_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/logout')                                 # 【退出登录】按钮 (TextView)

    # 退出登录二次确认弹窗
    LOGOUT_CONFIRM_BTN = _CommonLoactroAndroid.DIALOG_CONFIRM_BTN                      # 确认退出按钮
    LOGOUT_CANCEL_BTN = _CommonLoactroAndroid.DIALOG_CANCEL_BTN                        # 取消退出按钮
    LOGOUT_SUCCESS_MSG = _CommonLoactroAndroid.TOAST_MSG                               # 退出成功 Toast 消息


# =========================================================================
# 跨端通用定位器透明代理 (自动识别 Android / HarmonyOS NEXT / iOS)
# =========================================================================
class SettingsCenterLocator(_SettingsCenterLocatorHos, _SettingsCenterLocatorAndroid, _SettingsCenterLocatorIos, metaclass=DynamicLocatorMeta):
    """跨端设置中心页面定位器（支持 IDE Ctrl + 鼠标左键直接跳转定义，运行时按设备平台动态分发）"""

    _android_cls = _SettingsCenterLocatorAndroid
    _harmony_cls = _SettingsCenterLocatorHos
    _ios_cls = _SettingsCenterLocatorIos
