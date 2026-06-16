import time
from core.logger_utils import logger
from common.base_page import BasePage
from locators.groups.setting.group_manager_locator import GroupManagerLocator
from selenium.webdriver.remote.webelement import WebElement


class GroupManagerPage(BasePage):
    """群管理页面操作类"""

    # 等待页面加载
    def wait_for_page_load(self, timeout: int = 10) -> bool:
        """等待群管理页面加载完成"""
        res = self.get_attribute(GroupManagerLocator.TV_TITLE, "text") == "群管理"
        logger.info(f"⏳ [Action-groupManagerPage] 群管理页面 - 加载{'成功' if res else '超时'}")
        time.sleep(0.5)
        return res

    # 点击返回按钮
    def click_back_button(self):
        """点击顶部返回按钮"""
        self.click(GroupManagerLocator.IV_BACK)
        logger.info("⚙️ [Action-groupManagerPage] 点击顶部【返回】按钮")

    # 点击升级群组
    def click_upgrade_group(self):
        """点击升级群组"""
        self.click(GroupManagerLocator.VIEW_UPDATE_GROUP)
        logger.info("⚙️ [Action-groupManagerPage] 点击【升级群组】")

    # 点击管理员
    def click_administrators(self):
        """点击管理员"""
        self.click(GroupManagerLocator.IT_GROUP_MANAGER)
        logger.info("⚙️ [Action-groupManagerPage] 点击【管理员】")

    # 点击进群申请
    def click_join_to_group_apply(self):
        """点击进群申请"""
        self.click(GroupManagerLocator.JOIN_TO_GROUP_APPLY)
        logger.info("⚙️ [Action-groupManagerPage] 点击【进群申请】")

    # 点击指定成员禁言
    def click_mute_member(self):
        """点击指定成员禁言"""
        self.click(GroupManagerLocator.GROUP_MEMBER_MUTE)
        logger.info("⚙️ [Action-groupManagerPage] 点击【指定成员禁言】")

    # 点击群黑名单
    def click_group_black_member(self):
        """点击群黑名单"""
        self.click(GroupManagerLocator.GROUP_BLACK_MEMBER)
        logger.info("⚙️ [Action-groupManagerPage] 点击【群黑名单】")

    # 点击转让群主
    def click_group_give(self):
        """点击转让群主"""
        self.click(GroupManagerLocator.GROUP_GIVE)
        logger.info("⚙️ [Action-groupManagerPage] 点击【转让群主】")

    # 点击解散群组
    def click_dismiss_group(self):
        """点击解散群组"""
        self.click(GroupManagerLocator.DISMISS_GROUP)
        logger.info("⚙️ [Action-groupManagerPage] 点击【解散群组】")

    # ==========================
    # Switch 开关类操作
    # ==========================
    # 1. 群ID搜索开关
    def get_group_id_search_state(self) -> bool:
        """获取【群ID搜索】开关状态"""
        res = self.get_attribute(GroupManagerLocator.GROUP_ID_SEARCH_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【群ID搜索】开关状态: {res}")
        return str(res).lower() == 'true'

    def click_group_id_search_switch(self):
        """点击【群ID搜索】开关"""
        self.click(GroupManagerLocator.GROUP_ID_SEARCH_SWITCH)
        logger.info("⚙️ [Action-groupManagerPage] 点击【群ID搜索】开关")

    # 2. 进群验证开关
    def get_join_group_verify_state(self) -> bool:
        """获取【进群验证】开关状态"""
        res = self.get_attribute(GroupManagerLocator.JOIN_TO_GROUP_VERIFY_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【进群验证】开关状态: {res}")
        return str(res).lower() == 'true'

    def click_join_group_verify_switch(self):
        """点击【进群验证】开关"""
        self.click(GroupManagerLocator.JOIN_TO_GROUP_VERIFY_SWITCH)
        logger.info("⚙️ [Action-groupManagerPage] 点击【进群验证】开关")

    # 3. 全员禁言开关
    def get_all_member_mute_state(self) -> bool:
        """获取【全员禁言】开关状态"""
        res = self.get_attribute(GroupManagerLocator.ALL_MEMBER_MUTE_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【全员禁言】开关状态: {res}")
        return str(res).lower() == 'true'

    def click_all_member_mute_switch(self):
        """点击【全员禁言】开关"""
        self.click(GroupManagerLocator.ALL_MEMBER_MUTE_SWITCH)
        logger.info("⚙️ [Action-groupManagerPage] 点击【全员禁言】开关")

    # 4. 禁止群成员互相加好友开关
    def get_un_add_friend_each_other_state(self) -> bool:
        """获取【禁止群成员互相加好友】开关状态"""
        res = self.get_attribute(GroupManagerLocator.UN_ADD_FRIEND_EACH_OTHER_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【禁止群成员互相加好友】开关状态: {res}")
        return str(res).lower() == 'true'

    def click_un_add_friend_each_other_switch(self):
        """点击【禁止群成员互相加好友】开关"""
        self.click(GroupManagerLocator.UN_ADD_FRIEND_EACH_OTHER_SWITCH)
        logger.info("⚙️ [Action-groupManagerPage] 点击【禁止群成员互相加好友】开关")



    # ===================================================================================
    # 群成员禁言相关（全员禁言+指定成员禁言）
    # ===================================================================================
    # 等待指定禁言页面加载
    def wait_for_specify_mute_page_load(self, timeout: int = 10) -> bool:
        """等待指定禁言页面加载完成"""
        res = self.get_attribute(GroupManagerLocator.TV_TITLE, "text") == "指定成员禁言"
        logger.info(f"⏳ [Action-groupManagerPage] 指定禁言页面 - 加载{'成功' if res else '超时'}")
        time.sleep(0.5)
        return res
    
    # 禁言-获取已禁言列表的布局元素Item
    def get_muted_member_items(self) -> list[WebElement]:
        """禁言-获取已禁言列表的布局元素Item"""
        res_list = self.find_elements(GroupManagerLocator.MUTED_MEMBER)
        if not res_list:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到已禁言的群成员Item")
            return []
        logger.info(f"✅ [Action-groupManagerPage] 成功获取已禁言的群成员Item,共找到 {len(res_list)} 个")
        return res_list
            
    # 禁言-获取已禁言的群成员昵称列表
    def get_muted_member_names(self) -> list[WebElement]:
        """禁言-获取已禁言的群成员昵称列表"""
        res_list = self.find_elements(GroupManagerLocator.RECYCLE_VIEW_MEMBER_TV_NAME)
        if not res_list:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到已禁言的群成员")
            return []
        logger.info(f"✅ [Action-groupManagerPage] 成功获取已禁言的群成员,共找到 {len(res_list)} 个")
        return res_list
    
    # 禁言-点击解除禁言的按钮
    def click_unmute_button(self):
        """禁言-点击解除禁言的按钮"""
        self.click(GroupManagerLocator.TV_CANCEL_MUTE)
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击解除禁言的按钮")
        time.sleep(0.5)
    
    # 禁言-获取移除禁言后的二次弹窗信息
    def get_unmute_dialog_message(self) -> str:
        """禁言-获取移除禁言后的二次弹窗信息"""
        res = self.get_attribute(GroupManagerLocator.TV_DIALOG_MSG, "text")
        if not res:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到移除禁言后的二次弹窗信息")
            return ""
        logger.info(f"✅ [Action-groupManagerPage] 禁言-获取移除禁言后的二次弹窗信息: {res}")
        return res
    
    # 禁言-点击移除禁言后的二次弹窗确认按钮
    def click_unmute_dialog_confirm(self):
        """禁言-点击移除禁言后的二次弹窗确认按钮"""
        self.click(GroupManagerLocator.POSITIVE_BUTTON)
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击移除禁言后的二次弹窗确认按钮")
    
    # 禁言-点击移除禁言后的二次弹窗取消按钮
    def click_unmute_dialog_cancel(self):
        """禁言-点击移除禁言后的二次弹窗取消按钮"""
        self.click(GroupManagerLocator.NEGATIVE_BUTTON)
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击移除禁言后的二次弹窗取消按钮")


    # 禁言-解除某一个成员禁言
    def click_cancel_mute(self, name: str):
        """禁言-解除某一个成员禁言"""
        view_elem = self.find_element(GroupManagerLocator.get_member_by_name(name), timeout=2)
        if not view_elem:
            logger.warning(f"⚠️ [Action-groupManagerPage] 未找到已禁言成员【{name}】，无法解除禁言")
            return
        self.swipe_on_element(view_elem, slid_type="left", duration=500)
        self.click_unmute_button()
        self.click_unmute_dialog_confirm()
        logger.info(f"⚙️ [Action-groupManagerPage] 禁言-解除【{name}】的禁言")

    # 禁言-解除所有成员禁言
    def click_cancel_all_mute(self):
        """禁言-解除所有成员禁言"""
        member_items = self.get_muted_member_items()
        if not member_items:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到已禁言的群成员")
            return

        while len(member_items) > 0:
            before_count = len(member_items)
            # member_name_text = self.get_muted_member_names()[0]
            self.swipe_on_element(member_items[0], slid_type="left", duration=500)
            self.click_unmute_button()
            self.click_unmute_dialog_confirm()
            logger.info(f"⚙️ [Action-groupManagerPage] 禁言-解除所有成员禁言 - 已解除禁言的成员: 第一个")
            member_items = self.get_muted_member_items()
            if len(member_items) >= before_count:
                logger.error(f"❌ [Action-groupManagerPage] 解禁第一个成员后列表未缩短({before_count}->{len(member_items)})，疑似解禁失败，中止")
                break








