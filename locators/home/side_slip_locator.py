from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator



""" 左边侧滑页面 """
class SideSlipLocator:
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 头像
    ME_INFO = (AppiumBy.ID, f'{PACKAGE_ID}/iv_nav_avatar')

    # 昵称
    ME_NICKNAME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_nav_nickname')

    # 编辑
    ME_EDIT = (AppiumBy.ID, f'{PACKAGE_ID}/iv_nav_edit')

    # 二维码
    ME_QRCODE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_qr_code')

    # 动态整个框
    ME_DYNAMIC_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/cl_nav_moments')
    # 动态
    ME_DYNAMIC = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("动态")')

    # 我的收藏整个框
    ME_COLLECTION_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_collect')
    # 我的收藏图标
    ME_COLLECTION_ICON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_menu_icon')
    # 我的收藏
    ME_COLLECTION = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("我的收藏")')

    # 我的动态整个框
    ME_MY_DYNAMIC_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_dynamic')
    # 我的动态
    ME_MY_DYNAMIC = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("我的动态")')

    # 消息通知整个框
    ME_NOTIFICATION_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_notice')
    # 消息通知
    ME_NOTIFICATION = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("消息通知")')

    # 隐私防护整个框
    ME_PRIVACY_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_privacy')
    # 隐私防护
    ME_PRIVACY = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("隐私防护")')

    # 账号安全整个框
    ME_SECURITY_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_security')
    # 账号安全
    ME_SECURITY = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("账号安全")')

    # 通用设置整个框
    ME_SETTING_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_setting')
    # 通用设置
    ME_SETTING = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("通用设置")')

    # 图标
    ME_MENU_ICON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_menu_icon')
    # 文案标题
    ME_MENU_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_menu_title')










