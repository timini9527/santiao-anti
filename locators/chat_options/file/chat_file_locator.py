from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator




def _build_doc_xpath(
    *res_ids: str,
    extra: list[str] | None = None,
    prefix: str = "",
    text: str = ""
) -> str:
    """
    全自动跨品牌文件系统 XPath 构造器：
    自动将候选 ID 列表与各大厂商包名（AOSP、Google、OPPO ColorOS、OPlus 等）组合生成 OR 表达式，
    支持可选的 prefix 前缀与 text 文本精确/模糊匹配。
    """
    pkgs = [
        'com.android.documentsui:id',
        'com.google.android.documentsui:id',
        'com.coloros.filemanager:id',
        'com.oplus.filemanager:id',
    ]
    conditions = [f"@resource-id='{pkg}/{r_id}'" for r_id in res_ids for pkg in pkgs]
    if extra:
        conditions.extend(extra)
    
    id_clause = " or ".join(conditions)
    if text:
        text_clause = f"@text='{text}' or contains(@text, '{text}') or contains(@content-desc, '{text}')"
        inner = f"*[({id_clause}) and ({text_clause})]" if id_clause else f"*[{text_clause}]"
    else:
        inner = f"*[{id_clause}]"
    
    return f"{prefix}//{inner}" if prefix else f"//{inner}"


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
    # 文档选择器的包名（标准版 / Google 原生版 / OPPO ColorOS 版 / 一加 Realme OPlus 版）
    DOC_PACKAGE_ID = 'com.android.documentsui:id'
    GOOGLE_DOC_PACKAGE_ID = 'com.google.android.documentsui:id'
    COLOROS_DOC_PACKAGE_ID = 'com.coloros.filemanager:id'
    OPLUS_DOC_PACKAGE_ID = 'com.oplus.filemanager:id'
    
    # 跨平台 OR 运算的 XPath 模板（兼容 .format 调用）
    DOC_OR_GOO = _build_doc_xpath('{0}')

    # 顶部 Bar
    TOP_BAR_XPATH = DOC_OR_GOO.format('toolbar')
    # 左上角抽屉菜单
    DRAWER_MENU_BTN = (AppiumBy.XPATH, '//android.widget.ImageButton[@content-desc = "显示根目录"]')
    # 顶部 Toolbar 上的目录/面包屑文本 
    TOOLBAR_DIR_NAME = (AppiumBy.XPATH, f'{TOP_BAR_XPATH}/android.widget.TextView')
    # 搜索按钮（自适应 AOSP / Google / OPPO ColorOS / OPlus / content-desc）
    SEARCH_BTN = (
        AppiumBy.XPATH,
        _build_doc_xpath(
            'option_menu_search', 'action_search', 'search',
            extra=["@content-desc='搜索'", "@text='搜索'"]
        )
    )
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

    # 列表 ITEM（自适应原生 item_root 与 OPPO search_item_root
    DIR_LIST_ITEM_XPATH = _build_doc_xpath('item_root', 'search_item_root')
    DIR_LIST_ITEM = (AppiumBy.XPATH, DIR_LIST_ITEM_XPATH)

    
    # ==================== 文件列表 ====================
    # 文件夹和文件名称（自适应原生 android:id/title 与 OPPO file_list_item_title）
    DIR_NAME = (
        AppiumBy.XPATH,
        _build_doc_xpath(
            'file_list_item_title',
            extra=[f"@resource-id='{TITLE_ID}'", "contains(@resource-id, 'file_list_item_title')"],
            prefix=DIR_LIST_ITEM_XPATH
        )
    )

    # 预览按钮
    PREVIEW_ICON_XPATH = _build_doc_xpath('preview_icon', 'file_list_item_icon', 'icon')
    PREVIEW_ICON = (AppiumBy.XPATH, PREVIEW_ICON_XPATH)

    # 文件详细信息（自适应原生 line2/metadata 与 OPPO mark_file_list_item_detail）
    LINE2_INFO = (AppiumBy.XPATH, _build_doc_xpath('line2', 'mark_file_list_item_detail'))
    METADATA_XPATH = _build_doc_xpath('metadata', 'mark_file_list_item_detail')
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


    # 最近页面-顶部导航栏
    @classmethod
    def get_recently_page_top_nav_bar(cls, title: str = '图片'):
        """ 最近页面-顶部导航栏 """
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{title}")')

    # ==================== 搜索功能 ====================
    # 搜索输入框（自适应 AOSP / Google / OPPO ColorOS / 厂商定制 / EditText）
    SEARCH_INPUT = (
        AppiumBy.XPATH,
        _build_doc_xpath(
            'search_src_text', 'search_text', 'search_input', 'input_search',
            extra=["contains(@resource-id, 'search_src_text')", "@class='android.widget.EditText'"]
        )
    )

    # 根据完整/部分文件名定位元素（全品牌通用：精准匹配文件名文本）
    @classmethod
    def get_file_by_name(cls, file_name: str):
        """ 根据完整/部分文件名精准定位（自适应全品牌文件管理器） """
        return (
            AppiumBy.XPATH,
            _build_doc_xpath(
                'file_list_item_title',
                extra=[f"@resource-id='{cls.TITLE_ID}'", "contains(@resource-id, 'file_list_item_title')"],
                text=file_name
            )
        )

