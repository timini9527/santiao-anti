# -*- coding: utf-8 -*-
"""
iOS 平台左边侧滑页面定位器 (XCUITest / WebDriverAgent 原生架构)
严格对标 _SideSlipLocatorAndroid 结构、分块与方法签名，并依据 iOS 真机 XML 树优化查询速度：
  1. 有唯一 name 属性的元素全部使用 ACCESSIBILITY_ID（iOS 原生 ID，10~30ms 直达）
  2. 无固定 name 但有类型/前缀特征的元素使用 IOS_PREDICATE / IOS_CLASS_CHAIN（原生引擎，20~80ms）
  3. 仅无标识的动态结构锚点保留精简 XPath
"""
from appium.webdriver.common.appiumby import AppiumBy


class _SideSlipLocatorIos:
    """
    iOS 平台首页左侧侧滑抽屉页面 (Navigation Drawer) 元素定位器
    对齐 UI 树结构与业务域：
      1. 个人信息头部区域 (头像/二维码/昵称/ID)
      2. 核心功能菜单项 (会员中心/靓号商城/我的动态/我的收藏/设置中心)
      3. 动态菜单项文本定位能力
    """

    # =========================================================================
    # 1. 侧滑栏基础容器 (Drawer Layout & Container)
    # =========================================================================
    # 侧滑抽屉主根滚动容器
    DRAWER_LAYOUT = (                                                               
        AppiumBy.IOS_CLASS_CHAIN,
        "**/XCUIElementTypeScrollView/XCUIElementTypeOther[3]",
    )
    # 侧滑导航抽屉视图探查锚点
    NAV_VIEW = (
        AppiumBy.IOS_CLASS_CHAIN, 
        "**/XCUIElementTypeScrollView/XCUIElementTypeOther[3]/XCUIElementTypeOther[2]"
    )                             
    # 侧滑滚动列表容器 (ScrollView) 
    NAV_SCROLL_VIEW = DRAWER_LAYOUT                                                 

    # =========================================================================
    # 2. 个人信息头部区域 (Profile Header)
    # =========================================================================
    IV_NAV_AVATAR = (AppiumBy.ACCESSIBILITY_ID, "ic_avatar_decoration_default")     # 个人头像 (居中重合于头像本体，原生 ID 直达)
    IV_QR_CODE = (                                                                  # 个人名片二维码按钮 (头部唯一可见 Button)
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND visible == 1",
    )

    # 昵称区域 (动态昵称无固定 ID，通过编辑/VIP 图标精准锚定整行与文本)
    NICK_LAYOUT = (                                                                 # 昵称整行容器
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[XCUIElementTypeStaticText and XCUIElementTypeOther[XCUIElementTypeImage[@name='ic_slide_mine_edit_profile']]]",
    )
    TV_NAV_NICKNAME = (                                                             # 昵称文本控件
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[XCUIElementTypeOther[XCUIElementTypeImage[@name='ic_slide_mine_edit_profile']]]/XCUIElementTypeStaticText[1]",
    )

    # ID/三条号区域 (例如: "ID:imid_PzhYN3fwHoyjucE")
    NAV_ID_LAYOUT = (                                                               # 三条号整行容器
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[XCUIElementTypeOther[XCUIElementTypeStaticText[starts-with(@name, 'ID:')]]]",
    )
    TV_NAV_ID = (                                                                   # 三条号文本 (原生 Predicate 前缀匹配)
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name BEGINSWITH 'ID:')"
    )
    BAR_ID = (                                                                      # id箭头图标
        AppiumBy.ACCESSIBILITY_ID, "ic_r_arrow_sm"
    )

    # =========================================================================
    # 3. 核心功能菜单项容器 (Navigation Menu Items - 原生 ACCESSIBILITY_ID 极速直达)
    # =========================================================================
    NAV_ITEM_VIP = (AppiumBy.ACCESSIBILITY_ID, "会员中心")                          # 【会员中心】条目
    NAV_ITEM_NICE_NO = (AppiumBy.ACCESSIBILITY_ID, "靓号商城")                      # 【靓号商城】条目
    NAV_ITEM_DYNAMIC = (AppiumBy.ACCESSIBILITY_ID, "我的动态")                      # 【我的动态】条目
    NAV_ITEM_COLLECT = (AppiumBy.ACCESSIBILITY_ID, "我的收藏")                      # 【我的收藏】条目
    NAV_ITEM_SETTINGS = (AppiumBy.ACCESSIBILITY_ID, "设置中心")                     # 【设置中心】条目
    NAV_ITEM_SECURITY = (AppiumBy.ACCESSIBILITY_ID, "安全中心")                     # 【安全中心】条目

    # 通用菜单项文本定位
    TV_MENU_TITLE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name IN {'会员中心', '靓号商城', '我的动态', '我的收藏', '设置中心', '安全中心'}",
    )

    # =========================================================================
    # 4. 专属菜单标题定位器 (可直接用于获取文本或断言)
    # =========================================================================
    TV_VIP_TITLE = NAV_ITEM_VIP                                                     # 【会员中心】标题 ("会员中心")
    TV_NICE_NO_TITLE = NAV_ITEM_NICE_NO                                             # 【靓号商城】标题 ("靓号商城")
    TV_DYNAMIC_TITLE = NAV_ITEM_DYNAMIC                                             # 【我的动态】标题 ("我的动态")
    TV_COLLECT_TITLE = NAV_ITEM_COLLECT                                             # 【我的收藏】标题 ("我的收藏")
    TV_SETTINGS_TITLE = NAV_ITEM_SETTINGS                                           # 【设置中心】标题 ("设置中心")
    TV_SECURITY_TITLE = NAV_ITEM_SECURITY                                           # 【安全中心】标题 ("安全中心")

    # =========================================================================
    # 5. 动态菜单辅助检索 (Dynamic Helpers)
    # =========================================================================
    _MENU_NAME_MAP: dict[str, str] = {
        "vip": "会员中心",
        "nice_no": "靓号商城",
        "dynamic": "我的动态",
        "collect": "我的收藏",
        "settings": "设置中心",
        "security": "安全中心",
    }

    @classmethod
    def _resolve_menu_name(cls, key_or_text: str) -> str:
        """解析菜单 key 或中文名称，统一映射为 iOS 界面 name"""
        clean = (key_or_text or "").strip()
        key = clean.lower().replace("nav_item_", "")
        return cls._MENU_NAME_MAP.get(key, clean)

    @classmethod
    def get_menu_title_locator(cls, item_key: str) -> tuple[str, str]:
        """动态获取指定菜单项的标题定位器 (item_key 可传 'vip', 'settings' 或完整 ID)"""
        return (AppiumBy.ACCESSIBILITY_ID, cls._resolve_menu_name(item_key))

    @classmethod
    def get_menu_item_by_text(cls, menu_text: str) -> tuple[str, str]:
        """根据菜单文案动态检索侧滑菜单项 (原生 ACCESSIBILITY_ID 直达)"""
        return (AppiumBy.ACCESSIBILITY_ID, cls._resolve_menu_name(menu_text))
