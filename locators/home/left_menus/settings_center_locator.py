from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class SettingsCenterLocator(CommonLocator):
    """
    设置中心页面元素定位器
    入口路径：首页侧边栏 -> 设置中心 (nav_item_settings)
    基于最新 UI 树层级构建：
      - 顶部栏: iv_back, tv_title ("设置中心")
      - 滚动列表: content_scroll
      - 核心功能项: 账号安全, 消息通知, 隐私防护, 通用设置, 版本信息, 意见反馈, 联系我们
      - 底部操作项: 切换账号, 退出登录
    """
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # =========================================================================
    # 1. 顶部导航栏 (Top Bar)
    # =========================================================================
    BACK_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/iv_back')                               # 左上角返回按钮
    TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_title')                                 # 页面顶部标题 ("设置中心")

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
    LOGOUT_CONFIRM_BTN = CommonLocator.DIALOG_CONFIRM_BTN                              # 确认退出按钮
    LOGOUT_CANCEL_BTN = CommonLocator.DIALOG_CANCEL_BTN                                # 取消退出按钮
    LOGOUT_SUCCESS_MSG = CommonLocator.TOAST_MSG                                       # 退出成功 Toast 消息
