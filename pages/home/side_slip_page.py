from locators.home.side_slip_locator import SideSlipLocator
from core.logger_utils import logger
from pages.home.home_page import HomePage




class SideSlipPage(HomePage):    
    """ 侧滑菜单页面操作 """

    # 检查侧滑菜单是否已展开
    def is_side_slip_open(self, timeout: int = 3) -> bool:
        """检查侧滑菜单是否已展开"""
        status = self.is_element_exist(SideSlipLocator.NAV_VIEW, timeout=timeout, raise_exception=False)
        if not status:
            logger.warning("[Warning] 侧滑菜单未展开, 请检查")
        logger.info(f"[Info] 侧滑菜单是否已展开: {status}")
        return status

    # 通过头像 进入个人信息页面
    def click_INFO(self) -> None:
        """点击头像进入个人信息页面"""
        logger.info("[Action] 点击头像")
        self.click(SideSlipLocator.IV_NAV_AVATAR, force_wait=True)
        self.driver.implicitly_wait(1)

    # 通过昵称进入个人信息页面
    def click_nickname(self) -> None:
        """点击昵称进入个人信息页面"""
        logger.info("[Action] 点击昵称")
        self.click(SideSlipLocator.NICK_LAYOUT, force_wait=True)

    # 点击二维码
    def click_qrcode(self) -> None:
        """点击二维码"""
        logger.info("[Action] 点击二维码")
        self.click(SideSlipLocator.IV_QR_CODE)

    # 点击动态
    def click_dynamic(self) -> None:
        """点击动态"""
        logger.info("[Action] 点击动态")
        self.click(SideSlipLocator.NAV_ITEM_DYNAMIC)

    # 点击我的收藏
    def click_my_collection(self) -> None:
        """点击我的收藏"""
        logger.info("[Action] 点击我的收藏")
        self.click(SideSlipLocator.NAV_ITEM_COLLECT)

    # 点击我的动态
    def click_my_dynamic(self) -> None:
        """点击我的动态"""
        logger.info("[Action] 点击我的动态")
        self.click(SideSlipLocator.NAV_ITEM_DYNAMIC)

    # 点击消息通知
    def click_notification(self) -> None:
        """点击消息通知（新版已收归至系统设置内）"""
        logger.info("[Action] 点击系统设置进入消息通知")
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)

    # 点击隐私防护
    def click_privacy(self) -> None:
        """点击隐私防护（新版已收归至系统设置内）"""
        logger.info("[Action] 点击系统设置进入隐私防护")
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)

    # 点击账号安全
    def click_security(self) -> None:
        """点击账号安全（新版已收归至系统设置内）"""
        logger.info("[Action] 点击系统设置进入账号安全")
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)

    # 点击通用设置
    def click_setting(self) -> None:
        """点击【设置】/【通用设置】"""
        logger.info("[Action] 点击通用设置")
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)

    # 点击VIP会员
    def click_vip(self) -> None:
        """点击【VIP会员】"""
        logger.info("[Action] 点击VIP会员")
        self.click(SideSlipLocator.NAV_ITEM_VIP)

    # 点击靓号商城
    def click_nice_no(self) -> None:
        """点击【靓号商城】/【靓号】"""
        logger.info("[Action] 点击靓号商城")
        self.click(SideSlipLocator.NAV_ITEM_NICE_NO)

