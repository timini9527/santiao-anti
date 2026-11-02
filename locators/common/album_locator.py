from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class CommonAlbumLocator:
    """系统相册、拍照、图片裁剪通用 UI 定位器"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部及弹窗通用
    TOP_IV_BACK_BTN = CommonLocator.TOP_IV_BACK_BTN             # 左上角返回按钮
    TOP_IV_ACTION_BTN = CommonLocator.TOP_IV_ACTION_BTN         # 右上角完成按钮
    TOP_TV_TITLE = CommonLocator.TOP_TV_TITLE                  # 中间标题


    # ==================================================================================================================
    # 顶部导航栏
    # ==================================================================================================================
    TOP_BACK_BUTTON         = CommonLocator.TOP_IV_BACK_BTN    # 返回按钮
    TOP_TITLE_TEXT          = CommonLocator.TOP_TV_TITLE        # 标题文本（点击可切换文件夹）
    TOP_CATEGORY_FIRST_IMAGE = (AppiumBy.ID, f'{PACKAGE_ID}/first_image')       # 分类列表：第一张预览缩略图
    TOP_CATEGORY_TEXT       = (AppiumBy.ID, f'{PACKAGE_ID}/tv_folder_name')     # 分类列表：目录名称

    # ==================================================================================================================
    # 相册内容网格
    # ==================================================================================================================
    PHOTO_CONTAINER             = (AppiumBy.ID, f'{PACKAGE_ID}/recycler')                   # 整个相册列表容器
    PHOTO_ITEM_ID               = f'{PACKAGE_ID}/ivPicture'
    PHOTO_ITEM                  = (AppiumBy.ID, PHOTO_ITEM_ID)                              # 照片/视频缩略图本身
    PHOTO_VIDEO_DURATTON_VIEW_ID = f'{PACKAGE_ID}/tv_duration'
    PHOTO_VIDEO_DURATION_VIEW   = (AppiumBy.ID, PHOTO_VIDEO_DURATTON_VIEW_ID)               # 视频时长标签（仅视频可见）
    PHOTO_LONG_IMAGE_VIEW_ID    = f'{PACKAGE_ID}/tv_media_tag'
    PHOTO_LONG_IMAGE_VIEW       = (AppiumBy.ID, PHOTO_LONG_IMAGE_VIEW_ID)                   # 媒体类型标签（如"长图"）
    PHOTO_CHECK_BUTTON_CONTAINER = (AppiumBy.ID, f'{PACKAGE_ID}/btnCheck')                  # 勾选按钮的可点击容器
    PHOTO_CHECK_BUTTON_ID       = f'{PACKAGE_ID}/tvCheck'
    PHOTO_CHECK_BUTTON          = (AppiumBy.ID, PHOTO_CHECK_BUTTON_ID)                      # 勾选按钮（数字圈）

    # ==================================================================================================================
    # 底部操作栏
    # ==================================================================================================================
    PHOTO_PREVIEW_TEXT       = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_preview')      # 预览文本按钮
    PHOTO_ORIGINAL_TEXT      = (AppiumBy.ID, f'{PACKAGE_ID}/cb_original')        # 原图 CheckBox/文本
    PHOTO_SEND_CONTAINER     = (AppiumBy.ID, f'{PACKAGE_ID}/ps_complete_select') # 发送按钮容器
    PHOTO_SELECTED_COUNT_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_select_num')  # 已选数量（数字角标）
    PHOTO_SEND_TEXT          = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_complete')     # 发送/完成文本按钮

    # ==================================================================================================================
    # 预览详情页
    # ==================================================================================================================
    PHOTO_PREVIEW_CHECK_BOX  = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_selected')     # 预览页右上角勾选按钮

    # 选中超过10张的弹窗
    TV_CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_content')      # 选中超过10张的弹窗内容
    BTN_OK = (AppiumBy.ID, f'{PACKAGE_ID}/btnOk')               # 确认按钮


    # ==================================================================================================================
    # 定向过滤媒体定位器（纯图片、不含视频、仅视频、长图/WebP/GIF等）
    # ==================================================================================================================
    # 仅纯图片元素
    PHOTO_ONLY_IMAGE_ITEM = (AppiumBy.XPATH, f'//*[./*[@resource-id="{PHOTO_ITEM_ID}"]'
                                            f'and not(./*[@resource-id="{PHOTO_VIDEO_DURATTON_VIEW_ID}"])'
                                            f'and not(./*[@resource-id="{PHOTO_LONG_IMAGE_VIEW_ID}"])]'
                                            f'/*[@resource-id="{PHOTO_ITEM_ID}"]')
    # 仅纯图片勾选按钮
    PHOTO_CHECK_BUTTON_NOT_MEDIA = (AppiumBy.XPATH, f'//*[./*[@resource-id="{PHOTO_ITEM_ID}"]'
                                                    f' and not(./*[@resource-id="{PHOTO_VIDEO_DURATTON_VIEW_ID}"])'
                                                    f' and not(./*[@resource-id="{PHOTO_LONG_IMAGE_VIEW_ID}"])]'
                                                    f'/*[@resource-id="{PHOTO_CHECK_BUTTON_ID}"]')

    # 仅不包含视频元素
    PHOTO_NOT_VIDEO_ITEM = (AppiumBy.XPATH, f'//*[./*[@resource-id="{PHOTO_ITEM_ID}"]'
                                            f'and not(./*[@resource-id="{PHOTO_VIDEO_DURATTON_VIEW_ID}"])]'
                                            f'/*[@resource-id="{PHOTO_ITEM_ID}"]')
    # 仅不包含视频的勾选按钮
    PHOTO_CHECK_BUTTON_NOT_VIDEO = (AppiumBy.XPATH, f'//*[./*[@resource-id="{PHOTO_ITEM_ID}"]'
                                                    f' and not(./*[@resource-id="{PHOTO_VIDEO_DURATTON_VIEW_ID}"])]'
                                                    f'/*[@resource-id="{PHOTO_CHECK_BUTTON_ID}"]')

    # 仅视频元素
    PHOTO_VIDEO_ITEM = (AppiumBy.XPATH,     f'//*[@resource-id="{PHOTO_VIDEO_DURATTON_VIEW_ID}"]'
                                            f'/preceding-sibling::*[@resource-id="{PHOTO_ITEM_ID}"]')
    # 仅视频勾选按钮
    PHOTO_CHECK_BUTTON_VIDEO      = (AppiumBy.XPATH, f'//*[@resource-id="{PHOTO_VIDEO_DURATTON_VIEW_ID}"]'
                                                     f'/preceding-sibling::*[@resource-id="{PHOTO_CHECK_BUTTON_ID}"]')
    
    # 仅长图、webp图片、gif图片元素
    PHOTO_IMAGE_LONG_WEBP_GIF_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{PHOTO_LONG_IMAGE_VIEW_ID}"]'
                                            f'/preceding-sibling::*[@resource-id="{PHOTO_ITEM_ID}"]')
    # 仅长图、webp图片、gif图片勾选按钮
    PHOTO_CHECK_BUTTON_IMAGE_LONG_WEBP_GIF = (AppiumBy.XPATH, f'//*[@resource-id="{PHOTO_LONG_IMAGE_VIEW_ID}"]'
                                                     f'/preceding-sibling::*[@resource-id="{PHOTO_CHECK_BUTTON_ID}"]')

    PHOTO_CHECK_BUTTON_LONG_WEBP_GIF = PHOTO_CHECK_BUTTON_IMAGE_LONG_WEBP_GIF
    PHOTO_ONLY_VIDEO_ITEM = PHOTO_VIDEO_ITEM
