import time
from core.logger_utils import logger
from common.base_page import BasePage
from appium.webdriver.webelement import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from locators.groups.setting.group_setting_locator import GroupSettingLocator
from locators.common.common_locator import CommonLocator

class GroupSettingPage(BasePage):
    """群聊设置（群信息/群管理）页面操作类"""

    # 等待群聊setting页面加载
    def wait_for_setting_page_load(self, timeout=10) -> bool:
        """等待发起群聊setting页面加载"""
        res = self.get_attribute(GroupSettingLocator.TOP_TV_TITLE, "text") == "群详情"
        logger.info(f"⏳ [Action-groupSettingPage] GroupSettingPage 发起群聊setting页 - 页面加载{'成功' if res else '超时'}")
        return res

    # 点击返回
    def click_iv_back_button(self):
        """通用 Common 点击返回按钮"""
        self.click(CommonLocator.TOP_IV_BACK_BTN)
        logger.info("通用 Common 点击返回按钮")


    # ==========================
    # 成员区域操作
    # ==========================
    # 获取群聊页面群成员头像列表
    def get_friend_headers(self) -> list['WebElement']:
        """获取群聊页面群成员头像列表"""
        elements = self.find_elements(GroupSettingLocator.FRIEND_HEADER, timeout=2)
        if not elements:
            logger.warning("⚠️ [Action-groupSettingPage] 群聊设置页 - 获取群成员头像失败")
            return []
        logger.info(f"✅ [Action-groupSettingPage] 群聊设置页 - 获取群成员头像成功，共 {len(elements)} 个")
        return elements

    # 点击群成员头像（默认为群助手/群主）
    def click_friend_header(self):
        """点击群成员头像（默认为群助手/群主）"""
        self.click(GroupSettingLocator.FRIEND_HEADER)
        logger.info("⚙️ [Action-groupSettingPage] 群聊设置页 - 点击【群成员头像】")

    # 点击群成员名称（默认为群助手/群主）
    def click_friend_name(self):
        """点击群成员名称（默认为群助手/群主）"""
        self.click(GroupSettingLocator.FRIEND_NAME)
        logger.info("⚙️ [Action-groupSettingPage] 群聊设置页 - 点击【群成员名称】")

    # 获取群聊页面群成员名称列表
    def get_friend_names(self) -> list[str]:
        """获取群聊页面群成员名称"""
        elements = self.find_elements(GroupSettingLocator.FRIEND_NAME, timeout=2)
        if not elements:
            logger.warning("⚠️ [Action-groupSettingPage] 群聊设置页 - 获取群成员名称失败")
            return []
        logger.info(f"✅ [Action-groupSettingPage] 群聊设置页 - 获取群成员名称成功，共 {len(elements)} 个")
        return [element.get_attribute("text") for element in elements]


    # ==========================
    # 设置项操作
    # ==========================
    # 点击群二维码
    def click_group_qr_code(self):
        """点击群二维码"""
        self.click(GroupSettingLocator.SETTING_CHAT_GROUP_CODE)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【群二维码】")

    # 点击群公告
    def click_group_notice(self):
        """点击群公告"""
        self.click(GroupSettingLocator.SETTING_CHAT_GROUP_ANNOUNCEMENT)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【群公告】")
    
    # 点击群备注
    def click_group_remark(self):
        """点击群备注"""
        self.click(GroupSettingLocator.SETTING_CHAT_GROUP_REMARKS)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【群备注】")

    # 点击群管理
    def click_group_manager(self):
        """点击群管理"""
        self.click(GroupSettingLocator.SETTING_CHAT_GROUP_MANAGER)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【群管理】")

    # 点击群头像
    def click_group_avatar(self):
        """点击群头像"""
        self.click(GroupSettingLocator.SETTING_CHAT_GROUP_HEADER)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【群头像】")

    # 点击群聊名称
    def click_group_name(self):
        """点击群聊名称"""
        self.click(GroupSettingLocator.SETTING_CHAT_GROUP_NAME)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【群聊名称】")

    # 点击查找聊天记录
    def click_search_chat_record(self):
        """点击查找聊天记录"""
        self.click(GroupSettingLocator.SETTING_SEARCH_GROUPCHATMESSAGE)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【查找聊天记录】")

    # 点击免打扰
    def click_chat_dnd(self):
        """点击免打扰"""
        self.click(GroupSettingLocator.SETTING_CHAT_DND)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【免打扰】")

    # 点击置顶聊天
    def click_chat_settop(self):
        """点击置顶聊天"""
        self.click(GroupSettingLocator.SETTING_CHAT_SETTOP)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【置顶聊天】")

    # 点击聊天密码
    def click_chat_pwd(self):
        """点击聊天密码"""
        self.click(GroupSettingLocator.SETTING_CHAT_PWD)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【聊天密码】")

    # 点击设置群聊名称(针对自己)
    def click_chat_name_forme(self):
        """点击设置群聊名称(针对自己)"""
        self.click(GroupSettingLocator.SETTING_CHAT_NAME_FORME)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【设置群聊名称(针对自己)】")

    # 点击显示群成员名称
    def click_chat_show_member_name(self):
        """点击显示群成员名称"""
        self.click(GroupSettingLocator.SETTING_CHAT_SHOW_MEMBER_NAME)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【显示群成员名称】")

    # ==========================
    # 底部危险操作
    # ==========================
    # 点击清空聊天记录
    def click_clear_group_chat_message(self):
        """点击清空聊天记录"""
        self.swipe_page_quickly(slid_type='up')
        self.click(GroupSettingLocator.SETTING_CLEAR_GROUPCHATMESSAGE)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【清空聊天记录】")

    # 点击删除并退出
    def click_delete_and_out(self):
        """点击删除并退出"""
        self.click(GroupSettingLocator.SETTING_GROUP_DELETE_AND_OUT)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【删除并退出】")

    # 点击解散群聊
    def click_dismiss_group(self):
        """点击解散群聊"""
        self.click(GroupSettingLocator.SETTING_GROUP_DISMISS)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【解散群聊】")

    # 点击确认按钮
    def click_confirm_button(self):
        """点击确认按钮(通用于二次弹窗)"""
        self.click(GroupSettingLocator.TV_CONFIRM)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击弹窗【确认】")

    # 点击取消按钮
    def click_cancel_button(self):
        """点击取消按钮(通用于二次弹窗)"""
        self.click(GroupSettingLocator.TV_CANCEL)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击弹窗【取消】")
    
    # 获取switch_btn状态
    def get_switch_btn_state(self) -> bool:
        """获取switch_btn状态"""
        res = self.get_attribute(GroupSettingLocator.SWITCH_BTN, "checked")
        logger.info(f"✅ [Action-groupSettingPage] 群聊设置页 - 获取switch_btn状态: {res}")
        return res
    
    # 获取各个特定设置项的开关状态
    def get_dnd_switch_state(self) -> bool:
        """获取免打扰开关状态"""
        res = self.get_attribute(GroupSettingLocator.SETTING_CHAT_DND_SWITCH, "checked")
        logger.info(f"✅ [Action-groupSettingPage] 群聊设置页 - 获取免打扰开关状态: {res}")
        return str(res).lower() == 'true'

    def get_settop_switch_state(self) -> bool:
        """获取置顶聊天开关状态"""
        res = self.get_attribute(GroupSettingLocator.SETTING_CHAT_SETTOP_SWITCH, "checked")
        logger.info(f"✅ [Action-groupSettingPage] 群聊设置页 - 获取置顶聊天开关状态: {res}")
        return str(res).lower() == 'true'

    def get_pwd_switch_state(self) -> bool:
        """获取聊天密码开关状态"""
        res = self.get_attribute(GroupSettingLocator.SETTING_CHAT_PWD_SWITCH, "checked")
        logger.info(f"✅ [Action-groupSettingPage] 群聊设置页 - 获取聊天密码开关状态: {res}")
        return str(res).lower() == 'true'

    def get_show_member_name_switch_state(self) -> bool:
        """获取显示群成员昵称开关状态"""
        res = self.get_attribute(GroupSettingLocator.SETTING_CHAT_SHOW_MEMBER_NAME_SWITCH, "checked")
        logger.info(f"✅ [Action-groupSettingPage] 群聊设置页 - 获取显示群成员昵称开关状态: {res}")
        return str(res).lower() == 'true'

    # 修改“我在本群昵称”的文本输入操作
    def change_my_group_nickname(self, nickname: str):
        """修改我在本群昵称"""
        # 点击“我在本群昵称”行
        self.click_chat_name_forme()
        # 使用 CommonPage/BasePage 继承的方法清空并输入
        # 我们假设输入框是页面的 EditText，可以使用 common 的 EDITING_INPUT_FIELD
        from locators.personal.other_locator import OtherLocator
        self.send_keys(OtherLocator.EDIT_NICKNAME, nickname)
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass
        # 点击完成 (DONE)
        from locators.personal.personal_locator import PersonalLocator
        self.click(PersonalLocator.DONE)
        logger.info(f"✅ [Action-groupSettingPage] 修改【我在本群昵称】为: {nickname}")

    # 获取当前“我在本群昵称”右侧显示的昵称文本
    def get_my_group_nickname(self) -> str:
        """获取当前我在本群昵称的值"""
        # 通常行右侧的昵称是 tv_value，或者是特定 ID，
        # 我们可以通过定位 SETTING_CHAT_NAME_FORME 后代元素或者兄弟元素来获取，
        # 在 Android 下 setting_chat_name_forMe 是一个 RelativeLayout，包含标题和右侧值。
        # 让我们使用相对于该行的 tv_value 进行定位
        locator = (AppiumBy.XPATH, "//*[contains(@resource-id, 'setting_chat_name_forMe')]//*[contains(@resource-id, 'tv_value') or @class='android.widget.TextView']")
        res = self.get_attribute(locator, "text")
        logger.info(f"✅ [Action-groupSettingPage] 获取当前【我在本群昵称】文本: {res}")
        return res
    
    # 点击switch_btn
    def click_switch_btn(self):
        """点击switch_btn"""
        self.click(GroupSettingLocator.SWITCH_BTN)
        logger.info("✅ [Action-groupSettingPage] 群聊设置页 - 点击【switch_btn】")

    # 获取页面提示 Toast
    def get_toast(self):
        """获取页面提示 Toast"""
        return super().get_toast()
