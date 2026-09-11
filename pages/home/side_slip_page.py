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
    def click_INFO(self):
        """点击头像"""
        self.click(SideSlipLocator.IV_NAV_AVATAR, force_wait=True)
        logger.info("[Action] 点击头像")
        self.driver.implicitly_wait(1)

    # 通过昵称进入个人信息页面
    def click_nickname(self):
        """点击昵称"""
        self.click(SideSlipLocator.NICK_LAYOUT, force_wait=True)
        logger.info("[Action] 点击昵称")

    # 点击二维码
    def click_qrcode(self):
        """点击二维码"""
        self.click(SideSlipLocator.IV_QR_CODE)
        logger.info("[Action] 点击二维码")

    # 点击动态
    def click_dynamic(self):
        """点击动态"""
        self.click(SideSlipLocator.NAV_ITEM_DYNAMIC)
        logger.info("[Action] 点击动态")

    # 点击我的收藏
    def click_my_collection(self):
        """点击我的收藏"""
        self.click(SideSlipLocator.NAV_ITEM_COLLECT)
        logger.info("[Action] 点击我的收藏")

    # 点击我的动态
    def click_my_dynamic(self):
        """点击我的动态"""
        self.click(SideSlipLocator.NAV_ITEM_DYNAMIC)
        logger.info("[Action] 点击我的动态")

    # 点击消息通知
    def click_notification(self):
        """点击消息通知（新版已收归至系统设置内）"""
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)
        logger.info("[Action] 点击系统设置进入消息通知")

    # 点击隐私防护
    def click_privacy(self):
        """点击隐私防护（新版已收归至系统设置内）"""
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)
        logger.info("[Action] 点击系统设置进入隐私防护")

    # 点击账号安全
    def click_security(self):
        """点击账号安全（新版已收归至系统设置内）"""
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)
        logger.info("[Action] 点击系统设置进入账号安全")

    # 点击通用设置
    def click_setting(self):
        """点击【设置】/【通用设置】"""
        self.click(SideSlipLocator.NAV_ITEM_SETTINGS)
        logger.info("[Action] 点击通用设置")

    # 点击VIP会员
    def click_vip(self):
        """点击【VIP会员】"""
        self.click(SideSlipLocator.NAV_ITEM_VIP)
        logger.info("[Action] 点击VIP会员")

    # 点击靓号商城
    def click_nice_no(self):
        """点击【靓号商城】/【靓号】"""
        self.click(SideSlipLocator.NAV_ITEM_NICE_NO)
        logger.info("[Action] 点击靓号商城")

