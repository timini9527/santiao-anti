from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator



""" 左边侧滑页面 """
class SideSlipLocator(CommonLocator):
    """
    首页左侧侧滑抽屉页面 (Navigation Drawer) 元素定位器
    基于最新 UI 树结构规范重构 (DrawerLayout -> nav_view -> ScrollView)
    包含：个人信息头部 (头像/二维码/昵称/ID)、VIP会员、靓号、我的动态、我的收藏、系统设置
    """
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # =========================================================================
    # 1. 侧滑栏基础容器 (Drawer Layout & Container)
    # =========================================================================
    DRAWER_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/drawer_layout')                   # 侧滑抽屉主根容器
    NAV_VIEW = (AppiumBy.ID, f'{PACKAGE_ID}/nav_view')                             # 侧滑导航抽屉视图容器
    NAV_SCROLL_VIEW = (AppiumBy.CLASS_NAME, 'android.widget.ScrollView')           # 侧滑滚动列表容器

    # =========================================================================
    # 2. 个人信息头部区域 (Profile Header)
    # =========================================================================
    IV_NAV_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_nav_avatar')                   # 个人头像
    IV_QR_CODE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_qr_code')                         # 个人名片二维码图标
    NICK_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/nick_layout')                       # 昵称整体布局区域
    NAV_ID_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/nav_id_layout')                   # 三条号/用户ID整体布局区域

    # 昵称与ID文本（兼容布局内查找与ID查找）
    TV_NAV_NICKNAME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_nav_nickname')               # 昵称文本
    TV_NAV_ID = (AppiumBy.ID, f'{PACKAGE_ID}/tv_nav_id')                           # 三条号文本
    IV_NAV_EDIT = (AppiumBy.ID, f'{PACKAGE_ID}/iv_nav_edit')                       # 编辑个人信息图标

    # =========================================================================
    # 3. 核心功能菜单项容器 (Navigation Menu Items - ViewGroup)
    # =========================================================================
    NAV_ITEM_VIP = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_vip')                     # 【VIP会员】整个条目
    NAV_ITEM_NICE_NO = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_nice_no')             # 【靓号商城/靓号】整个条目
    NAV_ITEM_DYNAMIC = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_dynamic')             # 【我的动态】整个条目
    NAV_ITEM_COLLECT = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_collect')             # 【我的收藏】整个条目
    NAV_ITEM_SETTINGS = (AppiumBy.ID, f'{PACKAGE_ID}/nav_item_settings')           # 【设置/通用设置】整个条目 (最新ID带s)

    # =========================================================================
    # 4. 菜单项内部通用子控件 (Item Children)
    # =========================================================================
    IV_MENU_ICON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_menu_icon')                     # 菜单项左侧图标
    TV_MENU_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_menu_title')                   # 菜单项文案标题

    # =========================================================================
    # 5. 动态菜单辅助检索 (Dynamic Helpers)
    # =========================================================================
    @classmethod
    def get_menu_item_by_text(cls, menu_text: str) -> tuple:
        """根据菜单文案动态检索侧滑菜单项容器"""
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.PACKAGE_ID}/nav_view"]//*[contains(@text, "{menu_text}")]')










