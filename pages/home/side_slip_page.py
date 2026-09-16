from locators.home.side_slip_locator import SideSlipLocator
from core.logger_utils import logger
from pages.home.home_page import HomePage




class SideSlipPage(HomePage):    
    """ 侧滑菜单页面操作 """

    # 检查侧滑菜单是否已展开
    def is_side_slip_open(self, timeout: int = 3) -> bool:
        """ 检查侧滑抽屉菜单是否已展开 """
        status = self.is_element_exist(SideSlipLocator.NAV_VIEW, timeout=timeout, raise_exception=False)
        if not status:
            logger.warning("⚠️ [SideSlip] 侧滑菜单未展开，请检查")
        logger.info(f"🧐 [SideSlip] 侧滑菜单展开状态: {status}")
        return status

    # =========================================================================
    # 个人信息与头部区域操作
    # =========================================================================
    # 通过头像进入个人信息页面
    def click_INFO(self) -> None:
        """ 点击侧边栏个人头像，进入个人信息主页面 """
        logger.info("⚙️ [Action - SideSlip] 点击头像进入个人信息主页")
        self.click(SideSlipLocator.IV_NAV_AVATAR, force_wait=True)

    # 通过昵称进入个人信息页面
    def click_nickname(self) -> None:
        """ 点击昵称整行区域，进入个人信息页面 """
        logger.info("⚙️ [Action - SideSlip] 点击昵称区域进入个人信息页面")
        self.click(SideSlipLocator.NICK_LAYOUT, force_wait=True)

    # 获取当前侧边栏显示的昵称文本
    def get_nickname(self) -> str:
        """ 获取侧边栏当前显示的昵称文本 """
        nickname = self.get_attribute(SideSlipLocator.TV_NAV_NICKNAME, "text")
        logger.info(f"🧐 [Action - SideSlip] 获取到侧边栏昵称: {nickname}")
        return nickname

    # 获取当前侧边栏显示的 ID 文本
    def get_user_id(self) -> str:
        """ 获取侧边栏当前显示的 ID 文本 (例如 'ID:444455') """
        user_id_text = self.get_attribute(SideSlipLocator.TV_NAV_ID, "text")
        logger.info(f"🧐 [Action - SideSlip] 获取到侧边栏用户 ID: {user_id_text}")
        return user_id_text

    # 点击个人名片二维码
    def click_qrcode(self) -> None:
        """ 点击个人名片二维码图标 """
        logger.info("⚙️ [Action - SideSlip] 点击个人名片二维码图标")
        self.click(SideSlipLocator.IV_QR_CODE)

    # =========================================================================
    # 核心菜单项点击操作 (对齐最新 UI 树)
    # =========================================================================
    # 点击【会员中心】
    def click_vip(self) -> None:
        """ 点击侧边栏【会员中心】条目 """
        logger.info("⚙️ [Action - SideSlip] 点击【会员中心】")
        self.click(SideSlipLocator.NAV_ITEM_VIP)

    # 点击【靓号商城】
    def click_nice_no(self) -> None:
        """ 点击侧边栏【靓号商城】条目 """
        logger.info("⚙️ [Action - SideSlip] 点击【靓号商城】")
        self.click(SideSlipLocator.NAV_ITEM_NICE_NO)

    # 点击【我的动态】
    def click_dynamic(self) -> None:
        """ 点击侧边栏【我的动态】条目 """
        logger.info("⚙️ [Action - SideSlip] 点击【我的动态】")
        self.click(SideSlipLocator.NAV_ITEM_DYNAMIC)

    # 点击【我的收藏】
    def click_my_collection(self) -> None:
        """ 点击侧边栏【我的收藏】条目 """
        logger.info("⚙️ [Action - SideSlip] 点击【我的收藏】")
        self.click(SideSlipLocator.NAV_ITEM_COLLECT)

    # 点击【设置中心】
    def click_setting(self):
        """ 点击侧边栏【设置中心】条目，进入设置中心页面 """
        from pages.home.left_menus.settings_center_page import SettingsCenterPage
        logger.info("⚙️ [Action - SideSlip] 点击【设置中心】")
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)
        return SettingsCenterPage(self.driver)

    # =========================================================================
    # 标题文本获取能力
    # =========================================================================
    def get_menu_title(self, item_name: str) -> str:
        """
        获取指定菜单项的标题文本
        :param item_name: 可选 'vip'、'nice_no'、'dynamic'、'collect'、'settings'
        :return: 对应的标题文本内容（如 "会员中心"、"设置中心"）
        """
        locator = SideSlipLocator.get_menu_title_locator(item_name)
        title = self.get_attribute(locator, "text")
        logger.info(f"🧐 [Action - SideSlip] 获取到菜单【{item_name}】的标题文本: {title}")
        return title

