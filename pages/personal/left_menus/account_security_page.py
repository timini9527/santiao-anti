from common.base_page import BasePage
from pages.system.common.common_page import CommonPage
from core.logger_utils import logger
from locators.personal.left_menus.account_security_locator import AccountSecurityLocator
import time


class AccountSecurityPage(BasePage):
    """
    账号安全页面封装类
    入口路径：首页侧边栏 -> 账号安全
    """

    # ==========================
    # 顶部导航
    # ==========================
    def click_back(self):
        """账号安全页面点击左上角返回按钮"""
        CommonPage(self.driver).click_iv_back_button()
        logger.info("账号安全页面点击了左上角返回按钮")

    def get_page_title(self) -> str:
        """获取账号安全页面标题文本"""
        title = CommonPage(self.driver).get_top_middle_title()
        logger.info(f"获取账号安全页面标题: {title}")
        return title
    
    def click_action_button(self):
        """账号安全页面点击右上角操作按钮"""
        CommonPage(self.driver).click_action_button()
        logger.info("账号安全页面点击了右上角操作按钮")

    # ==========================
    # 实名认证
    # ==========================
    def click_realname(self):
        """点击'实名认证'条目"""
        self.click(AccountSecurityLocator.REALNAME_FRAME)
        logger.info("点击了'实名认证'")

    def get_realname_status(self) -> str:
        """获取实名认证状态 (如: '未认证' / '已认证')"""
        status = self.get_attribute(AccountSecurityLocator.REALNAME_STATUS, "text")
        logger.info(f"实名认证状态: {status}")
        return status

    # ==========================
    # 解除账号限制
    # ==========================
    def click_lift_account_limit(self):
        """点击'解除账号限制'条目"""
        self.click(AccountSecurityLocator.LIFT_ACCOUNT_LIMIT_FRAME)
        logger.info("点击了'解除账号限制'")

    # ==========================
    # 更换手机号码
    # ==========================
    def click_change_phone(self):
        """点击'更换手机号码'条目"""
        self.click(AccountSecurityLocator.CHANGE_PHONE_FRAME)
        logger.info("点击了'更换手机号码'")

    # ==========================
    # 登录密码
    # ==========================
    def click_login_password(self):
        """点击'登录密码'条目"""
        self.click(AccountSecurityLocator.LOGIN_PASSWORD_FRAME)
        logger.info("点击了'登录密码'")

    def get_password_status(self) -> str:
        """获取登录密码状态 (如: '已设置' / '未设置')"""
        status = self.get_attribute(AccountSecurityLocator.LOGIN_PASSWORD_STATUS, "text")
        logger.info(f"登录密码状态: {status}")
        return status

    # ==========================
    # 设备锁
    # ==========================
    def click_device_lock(self):
        """点击'设备锁'条目"""
        self.click(AccountSecurityLocator.DEVICE_LOCK_FRAME)
        logger.info("点击了'设备锁'")

    def get_device_lock_status(self) -> str:
        """获取设备锁状态 (如: '已关闭' / '已开启')"""
        status = self.get_attribute(AccountSecurityLocator.DEVICE_LOCK_STATUS, "text")
        logger.info(f"设备锁状态: {status}")
        return status

    # ==========================
    # 注销账号
    # ==========================
    def click_delete_account(self):
        """点击'注销账号'条目"""
        self.click(AccountSecurityLocator.DELETE_ACCOUNT_FRAME)
        logger.info("点击了'注销账号'")

    # ==========================
    # 退出登录
    # ==========================
    def click_logout_button(self):
        """点击'退出登录'按钮"""
        self.click(AccountSecurityLocator.LOGOUT_BTN)
        logger.info("点击了'退出登录'")

    # 退出登录二次确认弹窗 - 确认
    def click_logout_confirm_btn(self):
        """点击'退出登录'二次确认弹窗中的确认按钮"""
        self.click(AccountSecurityLocator.LOGOUT_CONFIRM_BTN)
        logger.info("点击了'退出登录'二次确认弹窗中的确认按钮")
        time.sleep(0.3)

    # 退出成功弹窗
    def get_logout_success_msg(self, target_text="已退出登录", timeout=5) -> str:
        """
        轮询获取退出登录后的 Toast 消息
        点击确认后会先出现"正在退出登录"，再变为"已退出登录"
        通过轮询机制等到目标文案出现后返回
        """
        end_time = time.time() + timeout
        last_text = ""
        while time.time() < end_time:
            elem = self.find_element(AccountSecurityLocator.LOGOUT_SUCCESS_MSG, timeout=0.5, expect_missing=True)
            if elem:
                try:
                    last_text = elem.get_attribute("text") or ""
                    logger.info(f"退出登录 Toast 文本: {last_text}")
                    if target_text in last_text:
                        return last_text
                except:
                    pass 
            time.sleep(0.1) # 快速轮询
        logger.warning(f"等待 {timeout}s 后仍未出现目标 Toast '{target_text}'，最后获取到: '{last_text}'")
        return last_text

    # 点击退出登录并获取toast提示
    def click_logout_and_get_toast(self) -> str:
        """点击'退出登录'按钮并获取Toast提示"""
        self.click_logout_button()
        self.click_logout_confirm_btn()
        toast = self.get_logout_success_msg()
        return toast

    