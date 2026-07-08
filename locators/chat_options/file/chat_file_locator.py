from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class ChatFileLocator:
    """聊天-文件功能定位器"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # ==================== 聊天页 ====================
    # +号面板中的“文件”按钮
    FILE_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/imFileIcon')

    FILE_ROOT_ID = f'{PACKAGE_ID}/more_action_root'
    FILE_CONTENT_ID = f'{PACKAGE_ID}/more_action_content'
    FILE_ROOT = (AppiumBy.XPATH, f'//*[@resource-id="{FILE_ROOT_ID}" and .//*[@text="文件"]]')

    # ==================== 顶部元素 ====================
    # 文档选择器的包名（标准版）
    DOC_PACKAGE_ID = 'com.android.documentsui:id'
    # 文档选择器的包名（Google 版）
    GOOGLE_DOC_PACKAGE_ID = 'com.google.android.documentsui:id'
    
    # 巧妙利用 Python 字符串格式化，生成包含 OR 运算的 XPath 模板
    DOC_OR_GOO = '//*[@resource-id="com.android.documentsui:id/{0}" or @resource-id="com.google.android.documentsui:id/{0}"]'

    # 顶部 Bar
    TOP_BAR_XPATH = DOC_OR_GOO.format('toolbar')
    # 左上角抽屉菜单
    DRAWER_MENU_BTN = (AppiumBy.XPATH, '//android.widget.ImageButton[@content-desc = "显示根目录"]')
    # 顶部 Toolbar 上的目录/面包屑文本 
    TOOLBAR_DIR_NAME = (AppiumBy.XPATH, f'{TOP_BAR_XPATH}/android.widget.TextView')
    # 搜索按钮
    SEARCH_BTN = (AppiumBy.XPATH, DOC_OR_GOO.format('option_menu_search'))
    # 右上角更多选项
    MORE_OPTIONS_BTN = (AppiumBy.XPATH, f'//android.widget.ImageView[@content-desc="更多选项"]')
    
    # ==================== 抽屉菜单 ====================
    # 菜单选项容器
    DRAWER_MENU_FILE_ITEM = (AppiumBy.XPATH, DOC_OR_GOO.format('drawer_roots'))
    # 菜单根目录容器
    CONTAINER_ROOTS_XPATH = DOC_OR_GOO.format('container_roots')
    CONTAINER_ROOTS = (AppiumBy.XPATH, CONTAINER_ROOTS_XPATH)
    # 菜单图标、文件图标、文件夹图标
    FOLDER_ICON = (AppiumBy.XPATH, DOC_OR_GOO.format('icon'))
    # 菜单名称、文件夹名称
    TITLE_ID = 'android:id/title'
    FOLDER_NAME = (AppiumBy.XPATH, f'{DOC_OR_GOO.format("roots_list")}//*[@resource-id="{TITLE_ID}"]')

    # ==================== 文件选择页面 ====================
    # 已选择菜单名称
    BREADCRUMB_TEXT = (AppiumBy.XPATH, DOC_OR_GOO.format('breadcrumb_text'))
    # 搜索芯片组容器
    SEARCH_CHIP_GROUP_XPATH = DOC_OR_GOO.format('search_chip_group')
    SEARCH_CHIP_GROUP = (AppiumBy.XPATH, SEARCH_CHIP_GROUP_XPATH)
    # 搜索芯片
    SEARCH_CHIP = (AppiumBy.XPATH, f'{SEARCH_CHIP_GROUP_XPATH}/android.widget.CompoundButton')
    # 头部标题
    HEADER_TITLE = (AppiumBy.XPATH, DOC_OR_GOO.format('header_title'))
    # 视图切换按钮（包含网络视图和列表视图）
    VIEW_SWITCH_BTN = (AppiumBy.XPATH, DOC_OR_GOO.format('sub_menu'))
    # 网络视图
    NETWORK_VIEW = (AppiumBy.XPATH, DOC_OR_GOO.format('sub_menu_grid'))
    # 列表视图
    LIST_VIEW = (AppiumBy.XPATH, DOC_OR_GOO.format('sub_menu_list'))
    # 视图名称（网络视图/列表视图）
    VIEW_NAME = (AppiumBy.XPATH, f'{DOC_OR_GOO.format("sub_menu")}/android.widget.TextView')
    
    # 目录列表
    DIR_LIST_XPATH = DOC_OR_GOO.format('dir_list')
    DIR_LIST = (AppiumBy.XPATH, DIR_LIST_XPATH)

    # 列表 ITEM
    DIR_LIST_ITEM_XPATH = DOC_OR_GOO.format('item_root')
    DIR_LIST_ITEM = (AppiumBy.XPATH, DIR_LIST_ITEM_XPATH)

    
    # ==================== 文件列表 ====================
    # 文件夹和文件名称
    DIR_NAME = (AppiumBy.XPATH, f'{DIR_LIST_ITEM_XPATH}//*[@resource-id="{TITLE_ID}"]')

    # 预览按钮
    PREVIEW_ICON_XPATH = DOC_OR_GOO.format('preview_icon')
    PREVIEW_ICON = (AppiumBy.XPATH, PREVIEW_ICON_XPATH)

    # 文件详细信息
    LINE2_INFO = (AppiumBy.XPATH, DOC_OR_GOO.format('line2'))
    METADATA_XPATH = DOC_OR_GOO.format('metadata')
    METADATA = (AppiumBy.XPATH, METADATA_XPATH)


    # ==================== 多选状态 ====================
    # 关闭多选模式的按钮
    ACTION_MODE_CLOSE_BUTTON = (AppiumBy.XPATH, DOC_OR_GOO.format('action_mode_close_button'))
    # 标题
    ACTION_BAR_TITLE = (AppiumBy.XPATH, DOC_OR_GOO.format('action_bar_title'))
    # 确认/完成按钮
    ACTION_MENU_SELECT = (AppiumBy.XPATH, DOC_OR_GOO.format('action_menu_select'))

    # 已选择文件左边的打勾
    ICON_CHECK = (AppiumBy.XPATH, DOC_OR_GOO.format('icon_check'))



