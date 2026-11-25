import time
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon
from locators.home.left_menus.settings_center_locator import SettingsCenterLocator
from pages.common.common_page import CommonPage


class SettingsCenterPage(CommonPage):
    """
    设置中心页面对象
    入口路径：首页侧边栏 -> 设置中心 (nav_item_settings)
    主要功能：
      - 导航与标题：返回、获取"设置中心"标题
      - 子功能入口：账号安全、消息通知、隐私防护、通用设置、意见反馈、联系我们
      - 版本信息查看：获取当前客户端版本号
      - 账号关键操作：切换账号、退出登录（含二次确认与 Toast 捕获）
    """

    # =========================================================================
    # 1. 顶部导航与状态查询
    # =========================================================================
    def click_back(self) -> None:
        """ 点击设置中心左上角返回按钮 """
        logger.info(f"{LogIcon.SETUP} 点击左上角返回按钮")
        self.click(SettingsCenterLocator.TOP_IV_BACK_BTN)

    def get_page_title(self) -> str:
        """ 获取设置中心页面顶部标题文本 """
        title = self.get_attribute(SettingsCenterLocator.TOP_TV_TITLE, "text") or ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - SettingsCenter] 获取页面标题: {title}")
        return title

    # =========================================================================
    # 2. 核心功能条目点击入口
    # =========================================================================
    def click_account_security(self) -> None:
        """ 点击【账号安全】条目，进入三级账号安全详情页面 """
        logger.info(f"{LogIcon.SETUP} 点击【账号安全】")
        self.click(SettingsCenterLocator.ITEM_ACCOUNT_SECURITY)

    def click_message_notification(self) -> None:
        """ 点击【消息通知】条目 """
        logger.info(f"{LogIcon.SETUP} 点击【消息通知】")
        self.click(SettingsCenterLocator.ITEM_MESSAGE_NOTIFICATION)

    def click_privacy_protection(self) -> None:
        """ 点击【隐私防护】条目 """
        logger.info(f"{LogIcon.SETUP} 点击【隐私防护】")
        self.click(SettingsCenterLocator.ITEM_PRIVACY_PROTECTION)

    def click_general_setting(self) -> None:
        """ 点击【通用设置】条目 """
        logger.info(f"{LogIcon.SETUP} 点击【通用设置】")
        self.click(SettingsCenterLocator.ITEM_GENERAL_SETTING)

    def click_feedback(self) -> None:
        """ 点击【意见反馈】条目 """
        logger.info(f"{LogIcon.SETUP} 点击【意见反馈】")
        self.click(SettingsCenterLocator.ITEM_FEEDBACK)

    def click_contact_us(self) -> None:
        """ 点击【联系我们】条目 """
        logger.info(f"{LogIcon.SETUP} 点击【联系我们】")
        self.click(SettingsCenterLocator.ITEM_CONTACT_US)

    # =========================================================================
    # 3. 版本信息获取
    # =========================================================================
    def get_version_value(self) -> str:
        """ 获取设置中心展示的版本号 (如 '11.1.20') """
        version = self.get_attribute(SettingsCenterLocator.VERSION_VALUE, "text") or ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - SettingsCenter] 获取当前版本号: {version}")
        return version

    # =========================================================================
    # 4. 底部账号操作（切换账号 / 退出登录）
    # =========================================================================
    def click_switch_account(self) -> None:
        """ 点击底部【切换账号】按钮 """
        logger.info(f"{LogIcon.SETUP} 点击【切换账号】")
        self.click(SettingsCenterLocator.SWITCH_ACCOUNT_BTN)

    def click_logout_button(self) -> None:
        """ 点击底部【退出登录】按钮，触发二次确认弹窗 """
        logger.info(f"{LogIcon.SETUP} 点击【退出登录】按钮")
        self.click(SettingsCenterLocator.LOGOUT_BTN)

    def get_logout_dialog_title(self, timeout: float = 3.0) -> str:
        """ 获取退出登录二次确认弹窗标题 """
        return self.get_dialog_title(timeout=timeout)

    def click_logout_confirm_btn(self) -> None:
        """ 点击退出登录二次确认弹窗中的【确认】按钮 (复用通用弹窗容器作用域防点穿) """
        logger.info(f"{LogIcon.SETUP} 点击退出登录二次确认【确认】按钮")
        self.confirm_dialog()

    def click_logout_cancel_btn(self) -> None:
        """ 点击退出登录二次确认弹窗中的【取消】按钮 (复用通用弹窗容器作用域) """
        logger.info(f"{LogIcon.SETUP} 点击退出登录二次确认【取消】按钮")
        self.cancel_dialog()

    def get_logout_success_msg(self, target_text: str = ToastMsg.LOGOUT_SUCCESS, timeout: int = 5) -> str:
        """
        轮询获取退出登录后的 Toast 提示
        :param target_text: 目标期望匹配文本 (默认 "已退出登录")
        :param timeout: 最大轮询等待超时 (秒)
        """
        logger.info(f"{LogIcon.WAIT} 等待退出登录 Toast (优先匹配: '{target_text}', 超时: {timeout}s)...")
        end_time = time.time() + timeout
        last_text = ""
        while time.time() < end_time:
            elem = self.find_element(SettingsCenterLocator.LOGOUT_SUCCESS_MSG, timeout=0.5, expect_missing=True)
            if elem:
                try:
                    last_text = self.read_element_attr(elem, "text")
                    if last_text:
                        logger.info(f"{LogIcon.FIND} 捕获到 Toast: {last_text}")
                    if target_text in last_text:
                        return last_text
                except Exception:
                    pass
            time.sleep(0.1)
        logger.warning(f"{LogIcon.WARN} {timeout}s 内未捕获到目标 Toast '{target_text}', 最后捕获: '{last_text}'")
        return last_text

    def click_logout_and_get_toast(self, timeout: int = 5, wait_toast: bool = True) -> str:
        """
        【标准一键退登链路】
        点击【退出登录】 -> 点击弹窗【确认】 -> 按需等待并返回 Toast 消息
        :param timeout: Toast 轮询最大超时时间（秒）
        :param wait_toast: 是否轮询捕获退出成功 Toast（纯环境清理场景可设为 False 跳过无效等待）
        """
        logger.info(f"{LogIcon.SETUP} 执行一键退出登录流水线...")
        self.click_logout_button()
        self.click_logout_confirm_btn()
        if not wait_toast:
            return ""
        return self.get_logout_success_msg(timeout=timeout)
