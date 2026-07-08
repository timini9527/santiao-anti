from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


""" 更新头像元素 """
class AvatarLocator:

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 拍照相关
    PHOTO_ID = (AppiumBy.ID, f'{PACKAGE_ID}/tv_take_photo')
    #

    # 从相册选择
    PHOTO_ALBUM_ID = (AppiumBy.ID, f'{PACKAGE_ID}/tv_select_from_album')
    # 每一张图片元素
    IMAGE_ID = (AppiumBy.ID, f'{PACKAGE_ID}/ivPicture')
    # 左上角返回
    PS_LEFT_BACK_ID = (AppiumBy.ID, f'{PACKAGE_ID}/ps_iv_left_back')
    # 右上角取消
    PS_RIGHT_CANCEL_ID = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_cancel')
    # 中间标题 可以切换相册
    PS_MIDDLE_TITLE_ID = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_title')
    # 左上角 转到上一层级
    LEFT_BACK_LEVEL = (AppiumBy.ACCESSIBILITY_ID, '转到上一层级')
    # 右上角 剪裁
    RIGHT_CROP = (AppiumBy.ID, f'{PACKAGE_ID}/menu_crop')
    # 中间标题 移动和缩放
    MIDDLE_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/toolbar_title')


    # 保存图片
    SAVE_IMAGE_ID = (AppiumBy.ID, f'{PACKAGE_ID}/tv_save_image')








