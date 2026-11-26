from appium.webdriver.common.appiumby import AppiumBy
from locators.common.hos_by import HosBy


class _SideSlipLocatorHos:
    """
    鸿蒙 NEXT 平台侧滑体系元素定位器 (HarmonyOS ArkUI 专享架构)
    深度对齐 HarmonyOS NEXT 真机 Hierarchy 实际组件树结构：
    涵盖两大核心侧滑业务域：
      Part 1: 首页左侧抽屉侧滑栏 (Navigation Drawer - 个人信息与设置中心等菜单项)
      Part 2: 会话列表项侧滑快捷菜单 (Conversation Swipe Actions - 静音/置顶/删除)
    """

    # =========================================================================
    # Part 1: 首页左侧侧滑抽屉 (Navigation Drawer)
    # =========================================================================

    # 1. 侧滑栏基础容器 (Drawer Layout & Container & Mask)
    DRAWER_LAYOUT = (
        AppiumBy.XPATH,
        "//Column[.//Text[@text='设置中心']] | //Scroll[.//Text[@text='设置中心']] | //*[@id='drawer_layout' or @id='nav_view']"
    )

    # 侧滑导航抽屉内容视图容器 (用于 is_side_slip_open 状态探查)
    NAV_VIEW = (
        AppiumBy.XPATH,
        "//Column[.//Text[@text='设置中心']] | //*[@id='nav_view' or @id='drawer_layout'] | //Text[@text='设置中心']/ancestor::Column[last()]"
    )

    # 侧滑滚动列表容器 (支持菜单列表溢出上下滚动)
    NAV_SCROLL_VIEW = (
        AppiumBy.XPATH,
        "//Scroll[.//Text[@text='设置中心']] | //List[.//Text[@text='设置中心']] | //Column[.//Text[@text='设置中心']]"
    )

    # 抽屉右侧半透明遮罩背景 (点击遮罩可平滑关闭抽屉)
    DRAWER_MASK = (
        AppiumBy.XPATH,
        "//Stack/*[@clickable='true' and not(.//Text[@text='设置中心'])]"
    )

    # 2. 个人信息头部区域 (Profile Header - 基于语义锚点高稳定位)
    # 个人头像 (锁定抽屉头部区域首张图片或三条号/昵称前驱图片)
    IV_NAV_AVATAR = (AppiumBy.XPATH, "//Column//Row/Column/Stack/Image")

    # 个人名片二维码图标 (位于三条号/ID 区域右侧的可点击图标)
    IV_QR_CODE = (AppiumBy.XPATH, "//Row/Column/following-sibling::Image")

    # 昵称整行区域 (点击可跳转个人信息主页)
    NICK_LAYOUT = (AppiumBy.XPATH, "//Column//Row/Column/Row[1]")

    # 昵称文本控件 (通过三条号/ID 文本向上检索前驱节点，杜绝绝对索引漂移)
    TV_NAV_NICKNAME = (AppiumBy.XPATH, "//Column//Row/Column/Row[1]/Text")

    # 昵称区域-编辑图标/VIP标识（是会员则为会员标识，不是会员则为编辑图标）
    TV_NAV_NICKNAME_ICON = (AppiumBy.XPATH, "//Column//Row/Column/Row[1]/Image")

    # ID/三条号整行容器
    NAV_ID_LAYOUT = (AppiumBy.XPATH, "//Column//Row/Column/Row[2]")

    # ID/三条号文本控件 (匹配 "ID: xxx" 或 "三条号: xxx")
    TV_NAV_ID = (AppiumBy.XPATH, "//Column//Row/Column/Row[2]/Text")

    # ID区域-箭头图标/靓号图标（不是会员则为箭头图标，是会员则为靓号图标）
    TV_NAV_ID_ICON = (AppiumBy.XPATH, "//Column//Row/Column/Row[2]/Image")

    # 3. 核心功能菜单项 (采用 HosBy 原生文本直查，绕过整树 XPath 扫描，ArkUI 点击自动冒泡至整行容器)
    # 【会员中心】条目整行
    NAV_ITEM_VIP = HosBy.type_text("Text", "会员中心")

    # 【靓号商城】条目整行
    NAV_ITEM_NICE_NO = HosBy.type_text("Text", "靓号商城")

    # 【我的动态】条目整行
    NAV_ITEM_DYNAMIC = HosBy.type_text("Text", "我的动态")

    # 【我的收藏】条目整行
    NAV_ITEM_COLLECT = HosBy.type_text("Text", "我的收藏")

    # 【设置中心】条目整行
    NAV_ITEM_SETTINGS = HosBy.type_text("Text", "设置中心")

    # 【安全中心】条目整行
    NAV_ITEM_SECURITY = HosBy.type_text("Text", "安全中心")

    # 4. 专属菜单标题定位器 (可直接用于断言文案与可见性)
    TV_VIP_TITLE = HosBy.type_text("Text", "会员中心")
    TV_NICE_NO_TITLE = HosBy.type_text("Text", "靓号商城")
    TV_DYNAMIC_TITLE = HosBy.type_text("Text", "我的动态")
    TV_COLLECT_TITLE = HosBy.type_text("Text", "我的收藏")
    TV_SETTINGS_TITLE = HosBy.type_text("Text", "设置中心")
    TV_SECURITY_TITLE = HosBy.type_text("Text", "安全中心")
    TV_MENU_TITLE = (AppiumBy.XPATH, "//Text[@text='会员中心' or @text='靓号商城' or @text='我的动态' or @text='我的收藏' or @text='设置中心' or @text='安全中心']")


    # =========================================================================
    # 动态参数化精准元素定位器工厂 (Parameterized Helpers)
    # =========================================================================
    # 菜单键名与中文界面文案映射表 (统一维护，杜绝多处冗余定义)
    MENU_NAME_MAP: dict[str, str] = {
        "vip": "会员中心",
        "nice_no": "靓号商城",
        "dynamic": "我的动态",
        "collect": "我的收藏",
        "settings": "设置中心",
        "security": "安全中心",
    }

    @classmethod
    def _resolve_menu_text(cls, menu_text: str) -> str:
        """统一解析菜单标识或文本为规范的界面文案 (支持大小写容错与 nav_item_ 前缀剥离)"""
        if not menu_text:
            return ""
        clean = menu_text.strip()
        key = clean.lower().replace("nav_item_", "")
        return cls.MENU_NAME_MAP.get(key, clean)

    @classmethod
    def get_menu_title_locator(cls, menu_text: str) -> tuple[str, str]:
        """动态获取指定抽屉菜单项的标题定位器（原生 HypiumBy 文本直查）"""
        target_text = cls._resolve_menu_text(menu_text)
        return HosBy.type_text("Text", target_text)

    @classmethod
    def get_menu_item_by_text(cls, menu_text: str) -> tuple[str, str]:
        """根据菜单文案动态检索抽屉菜单条目（原生 HypiumBy 文本直查，点击事件自动冒泡至行容器）"""
        target_text = cls._resolve_menu_text(menu_text)
        return HosBy.type_text("Text", target_text)

