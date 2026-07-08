from locators.system.home.side_slip_locator import SideSlipLocator
from core.logger_utils import logger
from pages.system.home.home_page import HomePage

class SideSlipPage(HomePage):

    # 通过头像 进入个人信息页面
    def click_INFO(self):
        self.click(SideSlipLocator.ME_INFO, force_wait=True)
        logger.info("[Action] 点击头像")
        self.driver.implicitly_wait(1)

    # 通过昵称进入个人信息页面
    def click_nickname(self):
        self.click(SideSlipLocator.ME_NICKNAME, force_wait=True)
        logger.info("[Action] 点击昵称")

    # 点击二维码
    def click_qrcode(self):
        self.click(SideSlipLocator.ME_QRCODE)
        logger.info("[Action] 点击二维码")

    # 点击动态
    def click_dynamic(self):
        self.click(SideSlipLocator.ME_DYNAMIC)
        logger.info("[Action] 点击动态")

    # 点击我的收藏
    def click_my_collection(self):
        self.click(SideSlipLocator.ME_COLLECTION)
        logger.info("[Action] 点击我的收藏")

    # 点击我的动态
    def click_my_dynamic(self):
        self.click(SideSlipLocator.ME_MY_DYNAMIC)
        logger.info("[Action] 点击我的动态")

    # 点击消息通知
    def click_notification(self):
        self.click(SideSlipLocator.ME_NOTIFICATION)
        logger.info("[Action] 点击消息通知")

    # 点击隐私防护
    def click_privacy(self):
        self.click(SideSlipLocator.ME_PRIVACY)
        logger.info("[Action] 点击隐私防护")

    # 点击账号安全
    def click_security(self):
        self.click(SideSlipLocator.ME_SECURITY)
        logger.info("[Action] 点击账号安全")

    # 点击通用设置
    def click_setting(self):
        self.click(SideSlipLocator.ME_SETTING)
        logger.info("[Action] 点击通用设置")


    


