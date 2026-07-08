from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator


class OtherLocator:

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 昵称编辑框
    EDIT_NICKNAME = (AppiumBy.ID, f'{PACKAGE_ID}/edit_name')

    # 三条ID 去修改按钮
    CHANGE_ST_ID = (AppiumBy.ID, f'{PACKAGE_ID}/go_modify')
    # 三条ID 编辑框
    EDIT_ST_ID = (AppiumBy.ID, f'{PACKAGE_ID}/edit_id')

    # 我的二维码页面的内部元素
    ME_QRCODE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_qrcode')    # 二维码
    ME_QRCODE_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_avatar') # 头像
    ME_QRCODE_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_name') # 昵称
    ME_QRCODE_SEX = (AppiumBy.ID, f'{PACKAGE_ID}/iv_gender')   # 性别
    ME_QRCODE_SAVE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_save_qrcode')  # 保存二维码按钮
    # 保存二维码弹窗消息
    TOASE_SAVE_QRCODE = CommonLocator.TOAST_MSG

    # 性别元素
    MALE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_male')   # 男
    FEMALE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_female') # 女

    # 邮箱编辑框
    EDIT_EMAIL = (AppiumBy.ID, f'{PACKAGE_ID}/edit_email')


