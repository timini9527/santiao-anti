from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class AccountSecurityLocator:
    """
    账号安全页面元素定位器
    入口路径：首页侧边栏 -> 账号安全
    """
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # ==========================================
    # 顶部导航栏 (view_title / top_bar)
    # ==========================================
    # 左上角返回按钮
    TOP_IV_BACK_BTN = CommonLocator.TOP_IV_BACK_BTN  # iv_back
    # 右上角操作按钮（当前无具体功能）
    TOP_IV_ACTION_BTN = CommonLocator.TOP_IV_ACTION_BTN  # fb_action

    # ==========================================
    # 上部区域 (top) — 实名认证 & 解除账号限制
    # ==========================================
    # 实名认证 整行容器 (可点击)
    REALNAME_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/layout_realname')
    # 实名认证 文本标题 (无 resource-id，使用文本匹配)
    REALNAME_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("实名认证")')
    # 实名认证 状态值 ("未认证" / "已认证")
    REALNAME_STATUS = (AppiumBy.ID, f'{PACKAGE_ID}/realname_authentication')

    # 解除账号限制 整行容器 (可点击)
    LIFT_ACCOUNT_LIMIT_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/layout_lift_account_limit')
    # 解除账号限制 文本标题
    LIFT_ACCOUNT_LIMIT_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/liftAccountRestrictions')

    # ==========================================
    # 中部区域 — 更换手机号码 (middle_1)
    # ==========================================
    # 更换手机号码 整行容器 (可点击)
    CHANGE_PHONE_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/middle_1')
    # 更换手机号码 文本标题
    CHANGE_PHONE_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/changePhoneNumber')

    # ==========================================
    # 中部区域 — 登录密码 (middle_2)
    # ==========================================
    # 登录密码 整行容器 (可点击)
    LOGIN_PASSWORD_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/middle_2')
    # 登录密码 文本标题
    LOGIN_PASSWORD_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/changeLoginPassword')
    # 登录密码 状态值 ("已设置" / "未设置")
    LOGIN_PASSWORD_STATUS = (AppiumBy.ID, f'{PACKAGE_ID}/text_password_status')

    # ==========================================
    # 中部区域 — 设备锁 (middle_3)
    # ==========================================
    # 设备锁 整行容器 (可点击)
    DEVICE_LOCK_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/middle_3')
    # 设备锁 文本标题
    DEVICE_LOCK_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/equipmentLock')
    # 设备锁 状态描述 ("已关闭" / "已开启")
    DEVICE_LOCK_STATUS = (AppiumBy.ID, f'{PACKAGE_ID}/text_discribe_equipmentLock')

    # ==========================================
    # 底部区域 — 注销账号 (bottom)
    # ==========================================
    # 注销账号 整行容器 (可点击)
    DELETE_ACCOUNT_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/bottom')
    # 注销账号 文本标题
    DELETE_ACCOUNT_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/deleteAccount')


