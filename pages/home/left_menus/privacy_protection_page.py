import time
from typing import Optional
from common.base_page import BasePage
from core.logger_utils import logger, LogIcon
from locators.home.left_menus.privacy_protection_locator import PrivacyProtectionLocator


class PrivacyProtectionPage(BasePage):
    """
    隐私防护详情页面对象 (Page Object)
    入口路径：首页侧边栏 -> 设置中心 (SettingsCenterPage) -> 隐私防护 (item_privacy_protection)
    主要功能：
      1. 顶部导航：返回、获取页面标题
      2. 4 大开关控制 (获取开关状态、点击切换)：
         - 允许手机号码搜索
         - 允许三条ID搜索
         - 群邀请确认
         - 断网屏保
      3. 4 大核心安全条目跳转：
         - 聊天密码、锁屏密码、黑名单、青少年模式
    """

    # =========================================================================
    # 1. 顶部导航
    # =========================================================================
    def click_back(self) -> None:
        """点击左上角返回按钮"""
        logger.info(f"{LogIcon.SETUP} 点击左上角返回按钮")
        self.click(PrivacyProtectionLocator.TOP_IV_BACK_BTN)

    def get_page_title(self) -> str:
        """获取页面顶部标题文本"""
        logger.info(f"{LogIcon.FIND} 正在获取页面标题...")
        title = self.get_attribute(PrivacyProtectionLocator.TOP_TV_TITLE, "text")
        logger.info(f"{LogIcon.SETUP} 页面标题: {title}")
        return title

    # =========================================================================
    # 2. 开关控件
    # =========================================================================
    # --- 允许手机号码搜索 ---
    def get_switch_phone_search_status(self) -> str:
        """获取【允许手机号码搜索】开关状态"""
        logger.info(f"{LogIcon.FIND} 正在获取【允许手机号码搜索】开关状态...")
        status = self.get_attribute(PrivacyProtectionLocator.SWITCH_PHONE_SEARCH, "checked")
        logger.info(f"{LogIcon.SETUP} 【允许手机号码搜索】开关状态: {status}")
        return status

    def click_switch_phone_search(self, enable: str = "true") -> None:
        """点击切换【允许手机号码搜索】开关"""
        logger.info(f"{LogIcon.SETUP} 点击切换【允许手机号码搜索】开关")
        if str(self.get_switch_phone_search_status()).lower() == str(enable).lower():
            logger.info(f"{LogIcon.ACTION} 【允许手机号码搜索】开关状态已是预期状态，无需操作")
        else:
            logger.info(f"{LogIcon.ACTION} 【允许手机号码搜索】开关状态与预期状态不符，正在点击切换")
            self.click(PrivacyProtectionLocator.SWITCH_PHONE_SEARCH)

    # --- 允许三条ID搜索 ---
    def get_switch_stid_search_status(self) -> str:
        """获取【允许三条ID搜索】开关状态"""
        logger.info(f"{LogIcon.FIND} 正在获取【允许三条ID搜索】开关状态...")
        status = self.get_attribute(PrivacyProtectionLocator.SWITCH_STID_SEARCH, "checked")
        logger.info(f"{LogIcon.SETUP} 【允许三条ID搜索】开关状态: {status}")
        return status

    def click_switch_stid_search(self, enable: str = "true") -> None:
        """点击切换【允许三条ID搜索】开关"""
        logger.info(f"{LogIcon.SETUP} 点击切换【允许三条ID搜索】开关")
        if str(self.get_switch_stid_search_status()).lower() == str(enable).lower():
            logger.info(f"{LogIcon.ACTION} 【允许三条ID搜索】开关状态已是预期状态，无需操作")
        else:
            logger.info(f"{LogIcon.ACTION} 【允许三条ID搜索】开关状态与预期状态不符，正在点击切换")
            self.click(PrivacyProtectionLocator.SWITCH_STID_SEARCH)

    # --- 群邀请确认 ---
    def get_switch_group_invite_confirm_status(self) -> str:
        """获取【群邀请确认】开关状态"""
        logger.info(f"{LogIcon.FIND} 正在获取【群邀请确认】开关状态...")
        status = self.get_attribute(PrivacyProtectionLocator.SWITCH_GROUP_INVITE_CONFIRM, "checked")
        logger.info(f"{LogIcon.SETUP} 【群邀请确认】开关状态: {status}")
        return status

    def click_switch_group_invite_confirm(self, enable: str = "true") -> None:
        """点击切换【群邀请确认】开关"""
        logger.info(f"{LogIcon.SETUP} 点击切换【群邀请确认】开关")
        if str(self.get_switch_group_invite_confirm_status()).lower() == str(enable).lower():
            logger.info(f"{LogIcon.ACTION} 【群邀请确认】开关状态已是预期状态，无需操作")
        else:
            logger.info(f"{LogIcon.ACTION} 【群邀请确认】开关状态与预期状态不符，正在点击切换")
            self.click(PrivacyProtectionLocator.SWITCH_GROUP_INVITE_CONFIRM)

    # --- 断网屏保 ---
    def get_switch_offline_screensaver_status(self) -> str:
        """获取【断网屏保】开关状态"""
        logger.info(f"{LogIcon.FIND} 正在获取【断网屏保】开关状态...")
        status = self.get_attribute(PrivacyProtectionLocator.SWITCH_OFFLINE_SCREENSAVER, "checked")
        logger.info(f"{LogIcon.SETUP} 【断网屏保】开关状态: {status}")
        return status

    def click_switch_offline_screensaver(self, enable: str = "true") -> None:
        """点击切换【断网屏保】开关"""
        logger.info(f"{LogIcon.SETUP} 点击切换【断网屏保】开关")
        if str(self.get_switch_offline_screensaver_status()).lower() == str(enable).lower():
            logger.info(f"{LogIcon.ACTION} 【断网屏保】开关状态已是预期状态，无需操作")
        else:
            logger.info(f"{LogIcon.ACTION} 【断网屏保】开关状态与预期状态不符，正在点击切换")
            self.click(PrivacyProtectionLocator.SWITCH_OFFLINE_SCREENSAVER)

    # =========================================================================
    # 3. 核心功能条目跳转
    # =========================================================================
    def click_chat_password(self) -> None:
        """点击进入【聊天密码】设置页面"""
        logger.info(f"{LogIcon.SETUP} 点击进入【聊天密码】")
        self.click(PrivacyProtectionLocator.ITEM_CHAT_PWD)

    def click_lock_password(self) -> None:
        """点击进入【锁屏密码】设置页面"""
        logger.info(f"{LogIcon.SETUP} 点击进入【锁屏密码】")
        self.click(PrivacyProtectionLocator.ITEM_LOCK_PWD)

    def click_blacklist(self) -> None:
        """点击进入【黑名单】列表页面"""
        logger.info(f"{LogIcon.SETUP} 点击进入【黑名单】")
        self.click(PrivacyProtectionLocator.ITEM_BLACKLIST)

    def click_teen_mode(self) -> None:
        """点击进入【青少年模式】设置页面"""
        logger.info(f"{LogIcon.SETUP} 点击进入【青少年模式】")
        self.click(PrivacyProtectionLocator.ITEM_TEEN_MODE)
