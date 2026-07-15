from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


""" 个人详情信息页面 """
class PersonalLocator:

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 公用编辑框、清空和完成按钮
    # EDIT = (AppiumBy.ID, f'{PACKAGE_ID}/edit_email')   # 编辑
    CLEAR = (AppiumBy.ID, f'{PACKAGE_ID}/btn_clear')   # 清空
    DONE = CommonLocator.TOP_FB_ACTION_BTN   # 完成按钮

    # 返回按钮
    BACK = CommonLocator.TOP_IV_BACK_BTN

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
    ME_ST_ID_CONFIRM = CommonLocator.TEXT_CONFIRM_BTN


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


    # 添加好友页面 - 头像
    ADD_FRIEND_IV_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_avatar')
    # 添加好友页面 - 昵称
    ADD_FRIEND_TV_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_name')
    ADD_FRIEND_TV_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/tv_name"]//android.widget.TextView')
    # 添加好友页面 - 所在地
    ADD_FRIEND_TV_LOCATION = (AppiumBy.ID, f'{PACKAGE_ID}/tv_location')
    # 添加好友页面 - 好友资料容器
    ADD_FRIEND_LL= (AppiumBy.ID, f'{PACKAGE_ID}/ll')
    # 好友资料容器 - 备注容器
    ADD_FRIEND_TV_REMARK = (AppiumBy.ID, f'{PACKAGE_ID}/title_remark')
    # 好友资料容器 - 资料卡标题容器
    ADD_FRIEND_TV_PROFILE_CARD_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/profile_card_title')
    # 好友资料容器 - 资料卡描述容器
    ADD_FRIEND_TV_PROFILE_CARD_DESC = (AppiumBy.ID, f'{PACKAGE_ID}/profile_card_desc')

    # 添加好友页面 - 好友动态
    ADD_FRIEND_TITLE_MOMENTS = (AppiumBy.ID, f'{PACKAGE_ID}/title_moments')  
    ADD_FRIEND_TITLE_TV = (AppiumBy.ID, f'{PACKAGE_ID}/title_tv')

    # 添加好友页面 - 未添加好友
    ADD_FRIEND_TV_NOT_FRIENDS = (AppiumBy.ID, f'{PACKAGE_ID}/cl_un_friends')
    ADD_FRIEND_TV_ADD_FRIEND = (AppiumBy.ID, f'{PACKAGE_ID}/add_friend')
    ADD_FRIEND_TV_ADD_FRIEND_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/add_friend"]//android.widget.TextView')




