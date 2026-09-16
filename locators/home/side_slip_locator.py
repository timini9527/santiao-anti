from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator



""" 左边侧滑页面定位器 """
class SideSlipLocator(CommonLocator):
    """
    首页左侧侧滑抽屉页面 (Navigation Drawer) 元素定位器
    基于最新 UI 树结构对齐 (DrawerLayout -> nav_view -> ScrollView)
    包含：
      1. 个人信息头部区域 (头像/二维码/昵称/ID)
      2. 核心功能菜单项 (会员中心/靓号商城/我的动态/我的收藏/设置中心)
      3. 动态菜单项文本定位能力
    """
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # =========================================================================
    # 1. 侧滑栏基础容器 (Drawer Layout & Container)
    # =========================================================================
    DRAWER_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/drawer_layout')                   # 侧滑抽屉主根容器
    NAV_VIEW = (AppiumBy.ID, f'{PACKAGE_ID}/nav_view')                             # 侧滑导航抽屉视图容器 (LinearLayout)
    NAV_SCROLL_VIEW = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/nav_view"]//android.widget.ScrollView')  # 侧滑滚动列表容器

    # =========================================================================
    # 2. 个人信息头部区域 (Profile Header)
    # =========================================================================
    IV_NAV_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_nav_avatar')                   # 个人头像 (ImageView)
    IV_QR_CODE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_qr_code')                         # 个人名片二维码图标 (ImageView)
    
    # 昵称区域 (注意: UI 树中 nick_layout 内的 TextView 无独立 resource-id)
    NICK_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/nick_layout')                       # 昵称整行容器 (LinearLayout)
    TV_NAV_NICKNAME = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/nick_layout"]//android.widget.TextView') # 昵称文本控件
    
    # ID/三条号区域 (nav_id_layout -> tv_nav_id)
    NAV_ID_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/nav_id_layout')                   # 三条号整行容器 (LinearLayout)
    TV_NAV_ID = (AppiumBy.ID, f'{PACKAGE_ID}/tv_nav_id')                           # 三条号文本 (TextView, 格式如: "ID:444455")

    # =========================================================================
    # 3. 核心功能菜单项容器 (Navigation Menu Items)
    # =========================================================================
    NAV_ITEM_VIP = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_vip')                     # 【会员中心】条目
    NAV_ITEM_NICE_NO = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_nice_no')             # 【靓号商城】条目
    NAV_ITEM_DYNAMIC = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_dynamic')             # 【我的动态】条目
    NAV_ITEM_COLLECT = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_collect')             # 【我的收藏】条目
    NAV_ITEM_SETTINGS = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_settings')           # 【设置中心】条目

    # 通用菜单项文本 ID
    TV_MENU_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_menu_title')                   # 通用标题 ID

    # =========================================================================
    # 4. 专属菜单标题定位器 (可直接用于获取文本或断言)
    # =========================================================================
    def _title(item_id: str) -> tuple:
        return (AppiumBy.XPATH, f'//*[@resource-id="{CommonLocator.PACKAGE_ID}/{item_id}"]//*[@resource-id="{CommonLocator.PACKAGE_ID}/tv_menu_title"]')

    TV_VIP_TITLE = _title('nav_item_vip')                                           # 【会员中心】标题 ("会员中心")
    TV_NICE_NO_TITLE = _title('nav_item_nice_no')                                   # 【靓号商城】标题 ("靓号商城")
    TV_DYNAMIC_TITLE = _title('nav_item_dynamic')                                   # 【我的动态】标题 ("我的动态")
    TV_COLLECT_TITLE = _title('nav_item_collect')                                   # 【我的收藏】标题 ("我的收藏")
    TV_SETTINGS_TITLE = _title('nav_item_settings')                                 # 【设置中心】标题 ("设置中心")

    # =========================================================================
    # 5. 动态菜单辅助检索 (Dynamic Helpers)
    # =========================================================================
    @classmethod
    def get_menu_title_locator(cls, item_key: str) -> tuple:
        """动态获取指定菜单项的标题定位器 (item_key 可传 'vip', 'settings' 或完整 ID)"""
        item_id = item_key if item_key.startswith("nav_item_") else f"nav_item_{item_key}"
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.PACKAGE_ID}/{item_id}"]//*[@resource-id="{cls.PACKAGE_ID}/tv_menu_title"]')

    @classmethod
    def get_menu_item_by_text(cls, menu_text: str) -> tuple:
        """根据菜单文案动态检索侧滑菜单项容器或文本"""
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.PACKAGE_ID}/nav_view"]//*[contains(@text, "{menu_text}")]')










