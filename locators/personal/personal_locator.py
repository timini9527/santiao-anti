from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


""" 个人详情信息页面 """
class PersonalLocator:

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 公用编辑框、清空和完成按钮
    # EDIT = (AppiumBy.ID, f'{PACKAGE_ID}/edit_email')   # 编辑
    CLEAR = (AppiumBy.ID, f'{PACKAGE_ID}/btn_clear')   # 清空
    DONE = CommonLocator.TOP_FB_ACTION_BTN   # 完成按钮

    # 个人详情页的列表容器
    RECYCLER_DETAIL_VIEW = (AppiumBy.ID, f'{PACKAGE_ID}/recycler_detail_view')
    # 详情页背景图片
    DETAIL_IV_BG = (AppiumBy.ID, f'{PACKAGE_ID}/detail_iv_bg')
    

    # 返回按钮
    BACK = CommonLocator.TOP_IV_BACK_BTN
    ACTION_DETAIL_BACK = (AppiumBy.ID, f'{PACKAGE_ID}/action_detail_back')

    # 头像
    ME_INFO = (AppiumBy.ID, f'{PACKAGE_ID}/detail_iv_avatar')

    # 昵称
    ME_NICKNAME = (AppiumBy.ID, f'{PACKAGE_ID}/detail_tv_nickname')
    # 编辑昵称按钮
    ME_EDIT = (AppiumBy.ID, f'{PACKAGE_ID}/detail_iv_change_nickname')

    # 整个框 The entire frame
    ENTIRE_FRAME = (AppiumBy.ID, f'{PACKAGE_ID}/root_layout')
    # 详细值 0-手机号，1-三条ID，2-性别，3-邮箱，4-所在地
    DETAIL_VALUE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_value')
    # 图标按钮包含：手机号眼睛是否隐藏、二维码
    ME_PHONE_EYES = (AppiumBy.ID, f'{PACKAGE_ID}/iv_extra_icon')

    # 手机号
    ME_PHONE_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("手机号")')

    # 三条ID
    ME_ST_ID_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("三条ID")')
    ME_ST_ID = (AppiumBy.ID, f'{PACKAGE_ID}/my_id')
    ME_ST_ID_CONFIRM = CommonLocator.TV_CONFIRM_BTN


    # 我的二维码
    ME_QRCODE_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("我的二维码")')
    ME_QRCODE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_qrcode')

    # 性别
    ME_SEX_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("性别")')

    # 邮箱
    ME_EMAIL_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("邮箱")')

    # 所在地
    ME_LOCATION_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("所在地")')
    ME_AREA_PROVINCE = (AppiumBy.ID, f'{PACKAGE_ID}/area_name') # 省区




