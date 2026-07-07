from appium.webdriver.common.appiumby import AppiumBy
from locators.chat.core.chat_locator import ChatLocator
from locators.common.common_locator import CommonLocator
from locators.chat.core.chat_panel_locator import ChatLocatorPanel


class ChatPositionLocator(CommonLocator):
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # ==================== 位置入口（加号面板内）====================
    LOCATION_SELECT_ROOT_ID = ChatLocatorPanel.MORE_ACTION_ROOT_ID
    LOCATION_SELECT_ROOT = ChatLocatorPanel.MORE_ACTION_ROOT
    LOCATION_SELECT_TEXT = ChatLocatorPanel.BTN_LOCATION

    # ==================== 位置选择页面 (地图页) ====================
    CANCEL_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/left_text') # 左上角取消按钮
    SEND_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/right_text') # 右上角发送按钮
    LOCATION_IVCENTERPIN = (AppiumBy.ID, f'{PACKAGE_ID}/ivCenterPin') # 地图展示当前的位置
    LOCATION_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/backLocation') # 定位当前位置按钮

    # 搜索区域
    LOCATION_SEARCH_AREA = (AppiumBy.ID, f'{PACKAGE_ID}/position_rv') # 搜索区域容器的 position_rv 控件 
    LOCATION_SEARCH_EDITTEXT = (AppiumBy.ID, f'{PACKAGE_ID}/edit_search') # 搜索区域的 edit_search 控件
    LOCATION_SEARCH_EDITTEXT_CLEAR = (AppiumBy.ID, f'{PACKAGE_ID}/edit_search') # 搜索区域的 edit_search 控件
    LOCATION_SEARCH_CANCLE = (AppiumBy.ID, f'{PACKAGE_ID}/position_cancel') # 搜索区域的取消按钮

    # 位置标题
    LOCATION_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/locationTitle')
    # 位置详细标题
    LOCATION_DETAIL_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/locationDetail')
    # 已选择位置图标
    LOCATION_SELECTED_ICON = (AppiumBy.ID, f'{PACKAGE_ID}/locationSelected')

    # === 下面3个元素暂时保留
    LOCATION_ZOOM_IN_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_zoomin')  # 放大按钮
    LOCATION_ZOOM_OUT_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_zoom_out')    # 缩小按钮
    LOCATION_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/bubble_title') # 位置名称标题
    

    # ==================== 聊天页面中的位置气泡 ====================
    SENT_LOCATION_ID = f'{PACKAGE_ID}/sent_location'
    SENT_LOCATION_ITEM = (AppiumBy.ID, SENT_LOCATION_ID) # 整个位置气泡框
    
    SENT_LOCATION_ADDRESS_ID = f'{PACKAGE_ID}/location_address'
    SENT_LOCATION_ADDRESS_ITEM = (AppiumBy.ID, SENT_LOCATION_ADDRESS_ID) # 位置气泡框的地址
    
    SENT_LOCATION_DETAIL_ADDRESS_ID = f'{PACKAGE_ID}/location_detail_address'
    SENT_LOCATION_DETAIL_ADDRESS_ITEM = (AppiumBy.ID, SENT_LOCATION_DETAIL_ADDRESS_ID) # 位置气泡框的详细地址
    
    SENT_LOCATION_IMG_ID = f'{PACKAGE_ID}/location_img'
    SENT_LOCATION_IMG_ITEM = (AppiumBy.ID, SENT_LOCATION_IMG_ID) # 位置气泡框的图片








