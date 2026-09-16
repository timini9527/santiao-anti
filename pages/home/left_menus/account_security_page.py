from common.base_page import BasePage
from pages.common.common_page import CommonPage
from core.logger_utils import logger
from locators.home.left_menus.account_security_locator import AccountSecurityLocator
import time


class AccountSecurityPage(BasePage):
    """
    账号安全详情页面对象
    入口路径：首页侧边栏 -> 设置中心 (SettingsCenterPage) -> 账号安全 (item_account_security)
    主要功能：实名认证、解除账号限制、更换手机号、登录密码设置、设备锁管理、注销账号
    """

    # ==========================
    # 顶部导航
    # ==========================
    # 顶部导航 - 点击左上角返回按钮
    def click_back(self) -> None:
        """账号安全页面点击左上角返回按钮"""
        logger.info("⚙️ [Action-AccountSecurity] 账号安全页面点击左上角返回按钮")
        CommonPage(self.driver).click_iv_back_button()

    # 顶部导航 - 获取页面标题文本
    def get_page_title(self) -> str:
        """获取账号安全页面标题文本"""
        logger.info("🔍 [Action-AccountSecurity] 正在获取账号安全页面标题...")
        title = CommonPage(self.driver).get_top_middle_title()
        logger.info(f"⚙️ [Action-AccountSecurity] 获取账号安全页面标题: {title}")
        return title
    
    # 顶部导航 - 点击右上角操作按钮
    def click_action_button(self) -> None:
        """账号安全页面点击右上角操作按钮"""
        logger.info("⚙️ [Action-AccountSecurity] 账号安全页面点击右上角操作按钮")
        CommonPage(self.driver).click_action_button()

    # ==========================
    # 实名认证
    # ==========================
    # 实名认证 - 点击实名认证条目
    def click_realname(self) -> None:
        """点击'实名认证'条目"""
        logger.info("⚙️ [Action-AccountSecurity] 点击'实名认证'")
        self.click(AccountSecurityLocator.REALNAME_FRAME)

    # 实名认证 - 获取实名认证状态
    def get_realname_status(self) -> str:
        """获取实名认证状态 (如: '未认证' / '已认证')"""
        logger.info("🔍 [Action-AccountSecurity] 正在获取实名认证状态...")
        status = self.get_attribute(AccountSecurityLocator.REALNAME_STATUS, "text")
        logger.info(f"⚙️ [Action-AccountSecurity] 实名认证状态: {status}")
        return status

    # ==========================
    # 解除账号限制
    # ==========================
    # 解除限制 - 点击解除账号限制条目
    def click_lift_account_limit(self) -> None:
        """点击'解除账号限制'条目"""
        logger.info("⚙️ [Action-AccountSecurity] 点击'解除账号限制'")
        self.click(AccountSecurityLocator.LIFT_ACCOUNT_LIMIT_FRAME)

    # ==========================
    # 更换手机号码
    # ==========================
    # 更换手机 - 点击更换手机号码条目
    def click_change_phone(self) -> None:
        """点击'更换手机号码'条目"""
        logger.info("⚙️ [Action-AccountSecurity] 点击'更换手机号码'")
        self.click(AccountSecurityLocator.CHANGE_PHONE_FRAME)

    # ==========================
    # 登录密码
    # ==========================
    # 登录密码 - 点击登录密码条目
    def click_login_password(self) -> None:
        """点击'登录密码'条目"""
        logger.info("⚙️ [Action-AccountSecurity] 点击'登录密码'")
        self.click(AccountSecurityLocator.LOGIN_PASSWORD_FRAME)

    # 登录密码 - 获取登录密码设置状态
    def get_password_status(self) -> str:
        """获取登录密码状态 (如: '已设置' / '未设置')"""
        logger.info("🔍 [Action-AccountSecurity] 正在获取登录密码状态...")
        status = self.get_attribute(AccountSecurityLocator.LOGIN_PASSWORD_STATUS, "text")
        logger.info(f"⚙️ [Action-AccountSecurity] 登录密码状态: {status}")
        return status

    # ==========================
    # 设备锁
    # ==========================
    # 设备锁 - 点击设备锁条目
    def click_device_lock(self) -> None:
        """点击'设备锁'条目"""
        logger.info("⚙️ [Action-AccountSecurity] 点击'设备锁'")
        self.click(AccountSecurityLocator.DEVICE_LOCK_FRAME)

    # 设备锁 - 获取设备锁状态
    def get_device_lock_status(self) -> str:
        """获取设备锁状态 (如: '已关闭' / '已开启')"""
        logger.info("🔍 [Action-AccountSecurity] 正在获取设备锁状态...")
        status = self.get_attribute(AccountSecurityLocator.DEVICE_LOCK_STATUS, "text")
        logger.info(f"⚙️ [Action-AccountSecurity] 设备锁状态: {status}")
        return status

    # ==========================
    # 注销账号
    # ==========================
    # 注销账号 - 点击注销账号条目
    def click_delete_account(self) -> None:
        """点击'注销账号'条目"""
        logger.info("⚙️ [Action-AccountSecurity] 点击'注销账号'")
        self.click(AccountSecurityLocator.DELETE_ACCOUNT_FRAME)

    