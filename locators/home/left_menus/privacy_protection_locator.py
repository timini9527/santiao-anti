from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class PrivacyProtectionLocator(CommonLocator):
    """
    隐私防护页面元素定位器
    入口路径：首页侧边栏 -> 设置中心 (SettingsCenterPage) -> 隐私防护 (item_privacy_protection)
    """

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # =========================================================================
    # 1. 顶部导航栏 (复用全局通用定位)
    # =========================================================================
    TOP_IV_BACK_BTN = CommonLocator.TOP_IV_BACK_BTN                                  # 左上角返回按钮 (iv_back)
    TOP_TV_TITLE = CommonLocator.TOP_TV_TITLE                                        # 页面顶部标题 ("隐私防护")

    # =========================================================================
    # 2. 开关控件 (基于业务文本锚点严格定位紧邻的首个 Switch，规避同名 switchWidget 冲突)
    # =========================================================================
    @staticmethod
    def _get_switch_text(text: str) -> tuple:
        """获取开关文本"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{CommonLocator.PACKAGE_ID}/tvTitle' and @text='{text}']")

    @staticmethod
    def _get_switch_next_sibling(text: str) -> tuple:
        return (
            AppiumBy.XPATH,
            f"//*[@text='{text}']/following-sibling::*[@resource-id='{CommonLocator.PACKAGE_ID}/switchWidget'][1]",
        )

    # 允许手机号码搜索
    SWITCH_PHONE_SEARCH_TEXT = _get_switch_text("允许手机号码搜索")
    SWITCH_PHONE_SEARCH = _get_switch_next_sibling("允许手机号码搜索")

    # 允许三条ID搜索
    SWITCH_STID_SEARCH_TEXT = _get_switch_text("允许三条ID搜索")
    SWITCH_STID_SEARCH = _get_switch_next_sibling("允许三条ID搜索")

    # 群邀请确认
    SWITCH_GROUP_INVITE_CONFIRM_TEXT = _get_switch_text("群邀请确认")
    SWITCH_GROUP_INVITE_CONFIRM = _get_switch_next_sibling("群邀请确认")

    # 断网屏保
    SWITCH_OFFLINE_SCREENSAVER_TEXT = _get_switch_text("断网屏保")
    SWITCH_OFFLINE_SCREENSAVER = _get_switch_next_sibling("断网屏保")

    # =========================================================================
    # 3. 核心功能条目容器 (FrameLayout 原生 ID 直达，完整点击热区且检索性能最优)
    # =========================================================================
    ITEM_CHAT_PWD = (AppiumBy.ID, f"{PACKAGE_ID}/itemChatPwd")           # 聊天密码条目
    ITEM_LOCK_PWD = (AppiumBy.ID, f"{PACKAGE_ID}/itemLockPwd")           # 锁屏密码条目
    ITEM_BLACKLIST = (AppiumBy.ID, f"{PACKAGE_ID}/itemBlacklist")        # 黑名单条目
    ITEM_TEEN_MODE = (AppiumBy.ID, f"{PACKAGE_ID}/itemTeenMode")         # 青少年模式条目
