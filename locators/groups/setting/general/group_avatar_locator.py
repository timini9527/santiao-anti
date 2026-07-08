from appium.webdriver.common.appiumby import AppiumBy
from locators.groups.setting.general.group_setting_locator import GroupSettingLocator
from locators.system.common.album_locator import CommonAlbumLocator
from locators.system.common.common_locator import CommonLocator

class GroupAvatarLocator(GroupSettingLocator, CommonAlbumLocator):
    """群头像设置页面定位器"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID
    
    # 顶部及弹窗通用
    IV_BACK = CommonLocator.TOP_IV_BACK_BTN                             # 左上角返回按钮
    FB_ACTION = CommonLocator.TOP_FB_ACTION_BTN                         # 右上角完成按钮
    TITLE = CommonLocator.TOP_TV_TITLE                                  # 中间标题
    PS_IV_LEFT_BACK = (AppiumBy.ID, f"{PACKAGE_ID}/ps_iv_left_back")    # 相册内部左上角返回按钮

    # 群头像
    GROUP_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/group_header")  
        
    
    # 选择面板弹窗
    DESIGN_BOTTOM_SHEET = (AppiumBy.ID, f"{PACKAGE_ID}/design_bottom_sheet")
    
    # 拍照
    ACTION_TAKE_PHOTO = (AppiumBy.ID, f"{PACKAGE_ID}/action_take_photo")

    # 从相册选择
    ACTION_PICK_GALLERY = (AppiumBy.ID, f"{PACKAGE_ID}/action_pick_gallery")

    # 保存图片
    ACTION_SAVE_IMAGE = (AppiumBy.ID, f"{PACKAGE_ID}/action_save_image")

    # 取消
    ACTION_CANCEL = (AppiumBy.ID, f"{PACKAGE_ID}/action_cancel")


    # 选择相册页面
    RECYCLER = (AppiumBy.ID, f"{PACKAGE_ID}/recycler")          # 相册列表
    IMAGE_PICTURE = (AppiumBy.ID, f"{PACKAGE_ID}/ivPicture")    # 图片
    

    # 拍照内部
    BTN_CAPTURE = (AppiumBy.ID, f"{PACKAGE_ID}/btn_capture")                # 拍照按钮
    IV_CAMERA_SWITCH = (AppiumBy.ID, f"{PACKAGE_ID}/iv_camera_switch")      # 切换镜头按钮
    IV_ARROW_DOWN = (AppiumBy.ID, f"{PACKAGE_ID}/iv_arrow_down")            # 返回按钮
    IV_CONFIRM = (AppiumBy.ID, f"{PACKAGE_ID}/iv_confirm")                  # 确认按钮
    IV_CANCEL = (AppiumBy.ID, f"{PACKAGE_ID}/iv_cancel")                    # 取消按钮




