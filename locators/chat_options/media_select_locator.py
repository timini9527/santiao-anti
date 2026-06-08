from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class MediaSelectLocator:
    """图片和视频选择面板的通用定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    IMAGE_SELECT_ROOT_ID = f'{PACKAGE_ID}/more_action_root'
    IMAGE_SELECT_CONTENT_ID = f'{PACKAGE_ID}/more_action_content'
    IMAGE_SELECT_ROOT = (AppiumBy.XPATH, f'//*[@resource-id="{IMAGE_SELECT_ROOT_ID}" and .//*[@text="图片"]]')

    # ==================== 顶部导航栏 ====================
    TOP_BACK_BUTTON         = (AppiumBy.ID, f'{PACKAGE_ID}/ps_iv_left_back')    # 返回按钮
    TOP_TITLE_TEXT          = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_title')        # 标题文本（点击可切换文件夹）
    TOP_CATEGORY_FIRST_IMAGE = (AppiumBy.ID, f'{PACKAGE_ID}/first_image')       # 分类列表：第一张预览缩略图
    TOP_CATEGORY_TEXT       = (AppiumBy.ID, f'{PACKAGE_ID}/tv_folder_name')     # 分类列表：目录名称

    # ==================== 相册内容网格 ====================
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

    # ==================== 底部操作栏 ====================
    PHOTO_PREVIEW_TEXT       = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_preview')      # 预览文本按钮
    PHOTO_ORIGINAL_TEXT      = (AppiumBy.ID, f'{PACKAGE_ID}/cb_original')        # 原图 CheckBox/文本
    PHOTO_SEND_CONTAINER     = (AppiumBy.ID, f'{PACKAGE_ID}/ps_complete_select') # 发送按钮容器
    PHOTO_SELECTED_COUNT_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_select_num')  # 已选数量（数字角标）
    PHOTO_SEND_TEXT          = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_complete')     # 发送/完成文本按钮

    # ==================== 预览详情页 ====================
    PHOTO_PREVIEW_CHECK_BOX  = (AppiumBy.ID, f'{PACKAGE_ID}/ps_tv_selected')     # 预览页右上角勾选按钮

    # 选中超过10张的弹窗
    TV_CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_content')     # 选中超过10张的弹窗内容
    BTN_OK = (AppiumBy.ID, f'{PACKAGE_ID}/btnOk')     # 确认按钮
