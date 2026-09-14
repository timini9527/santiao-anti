import time
from typing import Optional
from core.logger_utils import logger
from common.base_page import BasePage
from locators.groups.setting.manager.group_manager_locator import GroupManagerLocator
from selenium.webdriver.remote.webelement import WebElement


class GroupManagerPage(BasePage):
    """群管理页面操作类"""

    # 等待页面加载
    def wait_for_page_load(self, timeout: int = 10) -> bool:
        """等待群管理页面加载完成"""
        res = self.wait_for_element_text(GroupManagerLocator.TV_TITLE, expected_text="群管理", timeout=timeout)
        if res:
            logger.info(f"⏳ [Action-groupManagerPage] 群管理页面 - 加载完成")
        else:
            logger.error(f"❌ [Action-groupManagerPage] 群管理页面 - 未加载完成")
        return res

    # 顶部-点击返回按钮
    def click_iv_back_button(self) -> None:
        """顶部-点击顶部返回按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 点击顶部【返回】按钮")
        self.click(GroupManagerLocator.IV_BACK)
    
    # 顶部-点击确定按钮
    def click_confirm_button(self) -> None:
        """顶部-点击确定按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 点击顶部【确定】按钮")
        self.click(GroupManagerLocator.FB_BTN)

    # 顶部-点击编辑完成按钮
    def click_edit_finish_button(self) -> None:
        """顶部-点击编辑完成按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 点击编辑【完成】按钮")
        self.click(GroupManagerLocator.EDIT_TO_BTN)

    # =========================================================================
    # 智能滚动查找辅助方法 (Scroll Helpers)
    # =========================================================================
    # 智能滚动查找元素辅助方法
    def _scroll_find_element(self, locator: tuple, max_swipes: int = 3, slid_type: str = 'up') -> Optional[WebElement]:
        """智能滚动查找元素：先探测当前屏，未找到则按指定方向滑动探测"""
        logger.info(f"🔍 [Scroll] 智能滚动查找元素: {locator}")
        element = self.find_element(locator, timeout=1, raise_exception=False)
        if element:
            return element
        for i in range(max_swipes):
            self.swipe_page_quickly(slid_type=slid_type, duration=300)
            element = self.find_element(locator, timeout=1, raise_exception=False)
            if element:
                logger.info(f"🔍 [Scroll] 滑动第 {i + 1} 次成功找到元素: {locator}")
                return element
        logger.warning(f"⚠️ [Scroll] 滑动 {max_swipes} 次后仍未找到目标元素: {locator}")
        return None

    # 群管理-点击升级群组
    def click_upgrade_group(self) -> None:
        """群管理-点击升级群组"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【升级群组】")
        self.click(GroupManagerLocator.VIEW_UPDATE_GROUP)

    # 群管理-点击管理员
    def click_administrators(self) -> None:
        """群管理-点击管理员"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【管理员】")
        self.click(GroupManagerLocator.IT_GROUP_MANAGER)

    # 群管理-点击进群申请
    def click_join_to_group_apply(self) -> None:
        """群管理-点击进群申请"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【进群申请】")
        self.click(GroupManagerLocator.JOIN_TO_GROUP_APPLY)

    # 群管理-点击指定成员禁言
    def click_mute_member(self) -> None:
        """群管理-点击指定成员禁言"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【指定成员禁言】")
        self.click(GroupManagerLocator.GROUP_MEMBER_MUTE)

    # 群管理-点击群黑名单
    def click_group_black_member(self) -> None:
        """群管理-点击群黑名单"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【群黑名单】")
        self.click(GroupManagerLocator.GROUP_BLACK_MEMBER)

    # 群管理-点击转让群主
    def click_group_give(self) -> None:
        """群管理-点击转让群主（智能滚动至底部查找）"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【转让群主】")
        element = self._scroll_find_element(GroupManagerLocator.GROUP_GIVE)
        if element:
            element.click()
            logger.info("✅ [Action-groupManagerPage] 成功点击【转让群主】")
        else:
            logger.error("❌ [Action-groupManagerPage] 未找到【转让群主】按钮")

    # 群管理-点击解散群组
    def click_dismiss_group(self) -> None:
        """点击解散群组（智能滚动至底部查找）"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【解散群组】")
        element = self._scroll_find_element(GroupManagerLocator.DISMISS_GROUP)
        if element:
            element.click()
            logger.info("✅ [Action-groupManagerPage] 成功点击【解散群组】")
        else:
            logger.error("❌ [Action-groupManagerPage] 未找到【解散群组】按钮")


    # ===================================================================================
    # 管理员列表相关
    # ===================================================================================
    # 管理员-等待管理员列表页面加载完成
    def wait_for_admin_page_load(self, timeout: int = 10) -> bool:
        """管理员-等待管理员列表页面加载完成"""
        logger.info(f"⏳ [Action-groupManagerPage] 等待管理员列表页面加载 (超时: {timeout}s)")
        res = self.wait_for_element_text(GroupManagerLocator.TV_TITLE, expected_text="群管理员", timeout=timeout)
        if res:
            logger.info(f"⏳ [Action-groupManagerPage] 管理员列表页面 - 加载完成")
        else:
            logger.error(f"❌ [Action-groupManagerPage] 管理员列表页面 - 未加载完成")
        return res

    # 管理员-点击新增管理员按钮
    def click_add_admin(self) -> None:
        """管理员-点击新增管理员按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【新增管理员】按钮")
        self.click(GroupManagerLocator.IT_ADD_FRIEND)

    # 管理员-在管理员搜索框输入关键字
    def input_admin_search_keyword(self, keyword: str) -> None:
        """管理员-在管理员搜索框输入关键字"""
        logger.info(f"✍️ [Action-groupManagerPage] 管理员搜索框输入: '{keyword}'")
        self.send_keys(GroupManagerLocator.EDIT_SEARCH, keyword)

    # 管理员-在成员搜索输入框输入关键字
    def input_member_search_keyword(self, keyword: str) -> None:
        """管理员-在成员搜索输入框输入关键字"""
        logger.info(f"✍️ [Action-groupManagerPage] 成员搜索输入框输入: '{keyword}'")
        self.send_keys(GroupManagerLocator.SEARCH_EDIT_TEXT, keyword)

    # 管理员-获取当前列表展示的所有成员姓名
    def get_member_names(self) -> list[str]:
        """管理员-获取当前列表展示的所有成员姓名"""
        logger.info("📋 [Action-groupManagerPage] 获取当前列表展示的所有成员姓名")
        elements = self.find_elements(GroupManagerLocator.TV_FRIEND_NAME)
        if not elements:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到列表中的成员姓名")
            return []
        names = [el.get_attribute("text") for el in elements]
        logger.info(f"✅ [Action-groupManagerPage] 获取成员姓名成功: {names}")
        return names

    # 管理员-根据姓名点击列表中的某个成员
    def click_member_by_name(self, name: str) -> None:
        """管理员-根据姓名点击列表中的某个成员"""
        logger.info(f"⚙️ [Action-groupManagerPage] 点击列表中姓名为【{name}】的成员")
        locator = GroupManagerLocator.get_member_by_text(name)
        self.click(locator)
        time.sleep(0.5)
    
    # 管理员-先通过搜索，再点击搜索结果中的某个成员
    def click_member_by_search_keyword(self, name: str) -> None:
        """管理员-先通过搜索，再点击搜索结果中的某个成员"""
        logger.info(f"⚙️ [Action-groupManagerPage] 点击搜索结果中的【{name}】成员")
        self.input_member_search_keyword(name)
        self.click_member_by_name(name)

    # 管理员-获取管理员/群成员标签标识文本
    def get_member_type(self) -> str:
        """管理员-获取管理员/群成员标签标识文本"""
        logger.info("📋 [Action-groupManagerPage] 获取管理员/群成员标签标识文本")
        res = self.get_attribute(GroupManagerLocator.MEMBER_TYPE, "text", raise_exception=False)
        logger.info(f"✅ [Action-groupManagerPage] 获取角色标签: {res}")
        return res or ""
    
    # 管理员-点击移除管理员按钮
    def click_sure_button(self) -> None:
        """管理员-点击移除管理员按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【移除管理员】按钮")
        self.click(GroupManagerLocator.SURE_BTN)

    # 管理员-点击二次弹窗移除按钮
    def click_sure_content_button(self) -> None:
        """管理员-点击二次弹窗移除按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 点击【移除】按钮")
        self.click(GroupManagerLocator.TV_CONTENT)


    # =========================================================================================
    # Switch 开关类操作
    # =========================================================================================

    # Switch - 获取群ID搜索开关
    def get_group_id_search_state(self) -> str:
        """Switch - 获取【群ID搜索】开关状态"""
        logger.info("⚙️ [Action-groupManagerPage] 获取【群ID搜索】开关状态")
        res = self.get_attribute(GroupManagerLocator.GROUP_ID_SEARCH_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【群ID搜索】开关状态结果: {res}")
        return str(res).lower()
    
    # Switch - 点击群ID搜索开关
    def click_group_id_search_switch(self, checked_str: str) -> None:
        """Switch - 点击【群ID搜索】开关"""
        logger.info(f"⚙️ [Action-groupManagerPage] 准备设置【群ID搜索】开关为: {checked_str}")
        init_state = self.get_group_id_search_state()
        if init_state == checked_str:
            logger.info(f"⚙️ [Action-groupManagerPage] 【群ID搜索】开关状态已经是{checked_str},无需点击")
        else:
            self.click(GroupManagerLocator.GROUP_ID_SEARCH_SWITCH)
            time.sleep(1)
            logger.info(f"⚙️ [Action-groupManagerPage] 将【群ID搜索】开关设置为{checked_str}")

    # Switch - 获取进群验证开关
    def get_join_group_verify_state(self) -> str:
        """Switch - 获取【进群验证】开关状态"""
        logger.info("⚙️ [Action-groupManagerPage] 获取【进群验证】开关状态")
        res = self.get_attribute(GroupManagerLocator.JOIN_TO_GROUP_VERIFY_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【进群验证】开关状态结果: {res}")
        return str(res).lower()
    
    # Switch - 点击进群验证开关
    def click_join_group_verify_switch(self, checked_str: str) -> bool:
        """Switch - 点击【进群验证】开关"""
        logger.info(f"⚙️ [Action-groupManagerPage] 准备设置【进群验证】开关为: {checked_str}")
        init_state = self.get_join_group_verify_state()
        if init_state == checked_str:
            logger.info(f"⚙️ [Action-groupManagerPage] 【进群验证】开关状态已经是{checked_str},无需点击")
            return False
        else:
            self.click(GroupManagerLocator.JOIN_TO_GROUP_VERIFY_SWITCH)
            time.sleep(1)
            logger.info(f"⚙️ [Action-groupManagerPage] 将【进群验证】开关设置为{checked_str}")
            return True
    
    # Switch - 获取全员禁言开关
    def get_all_member_mute_state(self) -> str:
        """Switch - 获取【全员禁言】开关状态"""
        logger.info("⚙️ [Action-groupManagerPage] 获取【全员禁言】开关状态")
        res = self.get_attribute(GroupManagerLocator.ALL_MEMBER_MUTE_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【全员禁言】开关状态结果: {res}")
        return str(res).lower()
    
    # Switch - 点击全员禁言开关
    def click_all_member_mute_switch(self, checked_str: str) -> bool:
        """Switch - 点击【全员禁言】开关"""
        logger.info(f"⚙️ [Action-groupManagerPage] 准备设置【全员禁言】开关为: {checked_str}")
        init_state = self.get_all_member_mute_state()
        if init_state == checked_str:
            logger.info(f"⚙️ [Action-groupManagerPage] 【全员禁言】开关状态已经是{checked_str},无需点击")
            return False
        else:
            self.click(GroupManagerLocator.ALL_MEMBER_MUTE_SWITCH)
            time.sleep(1)
            logger.info(f"⚙️ [Action-groupManagerPage] 将【全员禁言】开关设置为{checked_str}")
            return True
    
    # Switch - 获取禁止群成员互相加好友开关
    def get_un_add_friend_each_other_state(self) -> str:
        """Switch - 获取【禁止群成员互相加好友】开关状态"""
        logger.info("⚙️ [Action-groupManagerPage] 获取【禁止群成员互相加好友】开关状态")
        res = self.get_attribute(GroupManagerLocator.UN_ADD_FRIEND_EACH_OTHER_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【禁止群成员互相加好友】开关状态结果: {res}")
        return str(res).lower()

    # Switch - 点击禁止群成员互相加好友开关
    def click_un_add_friend_each_other_switch(self, checked_str: str) -> bool:
        """Switch - 点击【禁止群成员互相加好友】开关"""
        logger.info(f"⚙️ [Action-groupManagerPage] 准备设置【禁止群成员互相加好友】开关为: {checked_str}")
        init_state = self.get_un_add_friend_each_other_state()
        if init_state == checked_str:
            logger.info(f"⚙️ [Action-groupManagerPage] 【禁止群成员互相加好友】开关状态已经是{checked_str},无需点击")
            return False
        else:
            self.click(GroupManagerLocator.UN_ADD_FRIEND_EACH_OTHER_SWITCH)
            time.sleep(1)
            logger.info(f"⚙️ [Action-groupManagerPage] 将【禁止群成员互相加好友】开关设置为{checked_str}")
            return True
            
    # Switch - 获取 switch item 列表（支持状态过滤）
    def get_switch_items(self, checked_str: str = None, raise_exception: bool = True) -> list[WebElement]:
        """Switch - 获取 switch item 列表（可按 checked_str "true"/"false" 过滤，None 表示获取全部）"""
        if checked_str is None:
            locator = GroupManagerLocator.SWITCH_BTN
            desc = "全部"
        else:
            locator = GroupManagerLocator.get_switch_by_checked_value(checked_str)
            desc = "已开启" if checked_str == "true" else "未开启"

        logger.info(f"⚙️ [Action-groupManagerPage] 获取【{desc}】的 switch item 列表")
        switch_item_list = self.find_elements(locator, timeout=2, raise_exception=raise_exception)
        if not switch_item_list:
            logger.warning(f"⚠️ [Action-groupManagerPage] 未找到【{desc}】的 switch item")
            return []
        logger.info(f"✅ [Action-groupManagerPage] 获取【{desc}】的 switch item 列表, 共找到 {len(switch_item_list)} 个")
        return switch_item_list
    
    # Switch - 开启/关闭全部指定状态的 switch
    def click_all_switch(self, checked_str: str = "true", max_swipes: int = 5) -> None:
        """Switch - 开启/关闭全部指定状态的 switch（支持滑动遍历，checked_str=None 表示不分状态点击全部）"""
        swipes = 0
        desc = "全部" if checked_str is None else ("已开启" if checked_str == "true" else "未开启")
        last_source = ""
        logger.info(f"⚙️ [Action-groupManagerPage] 开始切换【{desc}】开关 (最大滑动 {max_swipes} 次)")

        while swipes <= max_swipes:
            is_changed, last_source = self.is_page_source_changed(last_source)
            if swipes > 0 and not is_changed:
                logger.info("⚙️ [Action-groupManagerPage] 滑动后页面 DOM 无变化，已达底部边界，退出切换")
                break

            current_elements = self.get_switch_items(checked_str=checked_str, raise_exception=False)
            if current_elements:
                num_to_click = len(current_elements)
                for _ in range(num_to_click):
                    fresh_elements = self.get_switch_items(checked_str=checked_str, raise_exception=False)
                    if not fresh_elements:
                        break
                    elem = fresh_elements[0]
                    try:
                        logger.info(f"⚙️ [Action-groupManagerPage] 准备点击切换【{desc}】开关")
                        elem.click()
                        time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"⚠️ [Action-groupManagerPage] 点击开关失败: {e}")
                        break
            
            if swipes < max_swipes:
                logger.info(f"⚙️ [Action-groupManagerPage] 向下滚动寻找更多开关... (当前已滑动 {swipes} 次)")
                _, last_source = self.is_page_source_changed("")
                self.swipe_page(slid_type="up")
                time.sleep(0.5)
            else:
                break
            
            swipes += 1


    # ===================================================================================
    # 进群验证/申请相关（管理员操作+普通成员操作）
    # ===================================================================================
    # 等待进群申请页面加载
    def wait_for_join_apply_page_load(self, timeout: int = 10) -> bool:
        """等待进群申请页面加载完成"""
        logger.info(f"⏳ [Action-groupManagerPage] 等待进群申请页面加载 (超时: {timeout}s)")
        res = self.wait_for_element_text(GroupManagerLocator.TV_TITLE, expected_text="进群申请", timeout=timeout)
        if res:
            logger.info(f"⏳ [Action-groupManagerPage] 进群申请页面 - 加载完成")
        else:
            logger.error(f"❌ [Action-groupManagerPage] 进群申请页面 - 未加载完成")
        return res
    
    # 进群申请-进群申请横幅
    def get_join_apply_banner_text(self) -> str:
        """进群申请-进群申请横幅"""
        logger.info("📋 [Action-groupManagerPage] 获取进群申请横幅")
        res = self.get_text(GroupManagerLocator.TV_TITLE)
        logger.info(f"✅ [Action-groupManagerPage] 获取进群申请横幅结果: {res}")
        return res or ""

    # 进群申请-获取Tips
    def get_join_apply_tips(self) -> str:
        """进群申请-获取Tips"""
        logger.info("📋 [Action-groupManagerPage] 获取进群申请Tips")
        res = self.get_attribute(GroupManagerLocator.ERROR_TIPS_TITLE, "text")
        logger.info(f"✅ [Action-groupManagerPage] 获取Tips结果: {res}")
        return res or ""
    
    # 进群申请-获取同意按钮（可根据下标取）
    def get_agree_buttons(self) -> list[WebElement]:
        """进群申请-获取同意按钮（可根据下标取）"""
        logger.info("📋 [Action-groupManagerPage] 获取进群申请同意按钮列表")
        res = self.find_elements(GroupManagerLocator.GROUP_VERIFY_AGREE)
        if not res:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到同意按钮")
            return []
        logger.info(f"✅ [Action-groupManagerPage] 获取同意按钮共 {len(res)} 个")
        return res
    
    # 进群申请-点击同意按钮
    def click_agree_button(self, index: int = 0) -> None:
        """进群申请-点击同意按钮（可根据下标取）"""
        logger.info(f"✅ [Action-groupManagerPage] 点击第 {index + 1} 个同意按钮")
        buttons = self.get_agree_buttons()
        if index < len(buttons):
            buttons[index].click()
        else:
            logger.warning(f"⚠️ [Action-groupManagerPage] 同意按钮索引越界: {index}")
    
    # 进群申请-获取拒绝按钮（可根据下标取）
    def get_disagree_buttons(self) -> list[WebElement]:
        """进群申请-获取拒绝按钮（可根据下标取）"""
        logger.info("📋 [Action-groupManagerPage] 获取进群申请拒绝按钮列表")
        res = self.find_elements(GroupManagerLocator.GROUP_VERIFY_DISAGREE)
        if not res:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到拒绝按钮")
            return []
        logger.info(f"✅ [Action-groupManagerPage] 获取拒绝按钮共 {len(res)} 个")
        return res
    
    # 进群申请-点击拒绝按钮
    def click_disagree_button(self, index: int = 0) -> None:
        """进群申请-点击拒绝按钮（可根据下标取）"""
        logger.info(f"✅ [Action-groupManagerPage] 点击第 {index + 1} 个拒绝按钮")
        buttons = self.get_disagree_buttons()
        if index < len(buttons):
            buttons[index].click()
        else:
            logger.warning(f"⚠️ [Action-groupManagerPage] 拒绝按钮索引越界: {index}")

    # ===================================================================================
    # 群成员禁言相关（全员禁言+指定成员禁言）
    # ===================================================================================
    # 等待指定禁言页面加载
    def wait_for_specify_mute_page_load(self, timeout: int = 10) -> bool:
        """等待指定禁言页面加载完成"""
        logger.info(f"⏳ [Action-groupManagerPage] 等待指定禁言页面加载 (超时: {timeout}s)")
        res = self.get_attribute(GroupManagerLocator.TV_TITLE, "text") == "指定成员禁言"
        logger.info(f"⏳ [Action-groupManagerPage] 指定禁言页面 - 加载{'成功' if res else '超时'}")
        time.sleep(0.5)
        return res
    
    # 禁言-获取已禁言列表的布局元素Item
    def get_muted_member_items(self) -> list[WebElement]:
        """禁言-获取已禁言列表的布局元素Item"""
        logger.info("📋 [Action-groupManagerPage] 获取已禁言列表的布局元素Item")
        res_list = self.find_elements(GroupManagerLocator.MUTED_MEMBER)
        if not res_list:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到已禁言的群成员Item")
            return []
        logger.info(f"✅ [Action-groupManagerPage] 成功获取已禁言的群成员Item,共找到 {len(res_list)} 个")
        return res_list
            
    # 禁言-获取已禁言的群成员昵称列表
    def get_muted_member_names(self) -> list[WebElement]:
        """禁言-获取已禁言的群成员昵称列表"""
        logger.info("📋 [Action-groupManagerPage] 获取已禁言的群成员昵称列表")
        res_list = self.find_elements(GroupManagerLocator.RECYCLE_VIEW_MEMBER_TV_NAME)
        if not res_list:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到已禁言的群成员")
            return []
        logger.info(f"✅ [Action-groupManagerPage] 成功获取已禁言的群成员,共找到 {len(res_list)} 个")
        return res_list
    
    # 禁言-点击解除禁言的按钮
    def click_unmute_button(self) -> None:
        """禁言-点击解除禁言的按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击解除禁言的按钮")
        self.click(GroupManagerLocator.TV_CANCEL_MUTE)
        time.sleep(0.5)
    
    # 禁言-获取移除禁言后的二次弹窗信息
    def get_unmute_dialog_message(self) -> str:
        """禁言-获取移除禁言后的二次弹窗信息"""
        logger.info("📋 [Action-groupManagerPage] 获取移除禁言后的二次弹窗信息")
        res = self.get_attribute(GroupManagerLocator.TV_DIALOG_MSG, "text")
        if not res:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到移除禁言后的二次弹窗信息")
            return ""
        logger.info(f"✅ [Action-groupManagerPage] 禁言-获取移除禁言后的二次弹窗信息: {res}")
        return res
    
    # 禁言-点击移除禁言后的二次弹窗确认按钮
    def click_unmute_dialog_confirm(self) -> None:
        """禁言-点击移除禁言后的二次弹窗确认按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击移除禁言后的二次弹窗确认按钮")
        self.click(GroupManagerLocator.POSITIVE_BUTTON)
    
    # 禁言-点击移除禁言后的二次弹窗取消按钮
    def click_unmute_dialog_cancel(self) -> None:
        """禁言-点击移除禁言后的二次弹窗取消按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击移除禁言后的二次弹窗取消按钮")
        self.click(GroupManagerLocator.NEGATIVE_BUTTON)
    
    # 禁言-点击移除禁言后的二次弹窗确认按钮
    def click_mute_confirm_btn(self) -> None:
        """禁言-点击移除禁言后的二次弹窗确认按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击确认禁言按钮")
        self.click(GroupManagerLocator.MUTE_CONFIRM_BTN)
    
    # 禁言-点击移除禁言后的二次弹窗取消按钮
    def click_mute_cancel_btn(self) -> None:
        """禁言-点击移除禁言后的二次弹窗取消按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击取消禁言按钮")
        self.click(GroupManagerLocator.MUTE_CANCEL_BTN)

    # 指定禁言-永久禁言
    def click_cb_1(self) -> None:
        """指定禁言-永久禁言"""
        logger.info("⚙️ [Action-groupManagerPage] 指定禁言-勾选永久禁言")
        self.click(GroupManagerLocator.CB_1)
    
    # 指定禁言-临时禁言
    def click_cb_2(self) -> None:
        """指定禁言-临时禁言"""
        logger.info("⚙️ [Action-groupManagerPage] 指定禁言-勾选临时禁言")
        self.click(GroupManagerLocator.CB_2)
    
    # 指定禁言-临时禁言，获取禁言时间
    def get_temp_mute_time(self) -> str:
        """指定禁言-临时禁言，获取禁言时间"""
        logger.info("📋 [Action-groupManagerPage] 获取临时禁言时间")
        res = self.get_attribute(GroupManagerLocator.TV_TIME, "text")
        if not res:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到禁言时间")
            return ""
        logger.info(f"✅ [Action-groupManagerPage] 成功获取禁言时间: {res}")
        return res

    # 指定禁言-临时禁言，点击禁言时间
    def click_temp_mute_time(self) -> None:
        """指定禁言-临时禁言，点击禁言时间"""
        logger.info("⚙️ [Action-groupManagerPage] 指定禁言-临时禁言，点击禁言时间")
        self.click(GroupManagerLocator.TV_TIME)

    # 指定禁言-临时禁言-点击确定选择时间
    def click_select_time(self) -> None:
        """指定禁言-临时禁言-点击确定选择时间"""
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击确定选择时间")
        self.click(GroupManagerLocator.TV_SURE)

    # 指定禁言-临时禁言-选择时长，并且支持切换禁言时长选项
    def click_set_mute_duration(self, rule_time: str, old_summary: str = "10分钟") -> bool:
        """指定禁言-临时禁言-选择并切换指定的禁言时长"""
        MUTE_DURATION_OPTIONS = ["10分钟", "30分钟", "2小时", "1天", "3天", "7天", "30天"]
        logger.info(f"⚙️ [Action-groupManagerPage] 正在设置禁言时长为: {rule_time} (当前页面旧值: {old_summary})")

        if old_summary and rule_time == old_summary:
            self.click_select_time()
            return True

        picker_element = self.find_element(GroupManagerLocator.LOOP_SELECTOR, timeout=5)
        options = MUTE_DURATION_OPTIONS

        old_index = options.index(old_summary) if old_summary in options else len(options)
        rule_time = rule_time if rule_time in options else options[0]
        target_index = options.index(rule_time)

        rect = picker_element.rect
        slide_distance = int(rect['height'] * 0.18)  # 经验值：一格行高约占控件高度 18%

        if old_index > 0:
            logger.info(f"🔄 正在重置选择器至顶端（滑动回退步数: {old_index}）...")
            for _ in range(old_index):
                self.swipe_by_offset(rect=rect, y_offset=slide_distance, duration=400)
                time.sleep(0.1)

        if target_index > 0:
            logger.info(f"🔄 向上滚动选择器以选择【{rule_time}】...")
            for _ in range(target_index):
                self.swipe_by_offset(rect=rect, y_offset=-slide_distance, duration=400)
                time.sleep(0.15)

        self.click_select_time()
        logger.info("✅ 禁言时长选择完毕并点击确定")
        return True

    # 禁言-获取指定成员禁言状态
    def get_mute_status(self, name: str) -> str:
        """禁言-获取指定成员禁言状态"""
        logger.info(f"📋 [Action-groupManagerPage] 获取【{name}】的禁言状态")
        status_locator = GroupManagerLocator.get_mute_status_by_name(name)
        res = self.get_attribute(status_locator, "text")
        logger.info(f"✅ [Action-groupManagerPage] 成功获取【{name}】的禁言状态: {res}")
        return res or ""

    # 禁言-解除某一个成员禁言
    def click_cancel_mute(self, name: str) -> None:
        """禁言-解除某一个成员禁言"""
        logger.info(f"⚙️ [Action-groupManagerPage] 禁言-准备解除【{name}】的禁言")
        view_elem = self.find_element(GroupManagerLocator.get_member_by_name(name), timeout=2)
        if not view_elem:
            logger.warning(f"⚠️ [Action-groupManagerPage] 未找到已禁言成员【{name}】，无法解除禁言")
            return
        self.swipe_on_element(view_elem, slid_type="left", duration=500)
        self.click_unmute_button()
        self.click_unmute_dialog_confirm()
        logger.info(f"✅ [Action-groupManagerPage] 禁言-已完成解除【{name}】的禁言")

    # 禁言-解除所有成员禁言
    def click_cancel_all_mute(self) -> None:
        """禁言-解除所有成员禁言"""
        logger.info("⚙️ [Action-groupManagerPage] 禁言-准备解除所有成员禁言")
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


    # ================================================================================
    # 群黑名单相关
    # ================================================================================         
    # 群黑名单-等待群黑名单页面加载完成
    def wait_for_group_blacklist_page_load(self, timeout: int = 10) -> bool:
        """群黑名单-等待群黑名单页面加载完成"""
        logger.info(f"⏳ [Action-groupManagerPage] 等待群黑名单页面加载 (超时: {timeout}s)")
        res = self.get_attribute(GroupManagerLocator.TV_TITLE, "text") == "群黑名单"
        logger.info(f"⏳ [Action-groupManagerPage] 群黑名单页面 - 加载{'成功' if res else '超时'}")
        time.sleep(0.5)
        return res

    # 群黑名单-点击添加黑名单成员
    def click_add_black_member(self) -> None:
        """群黑名单-点击添加黑名单成员"""
        logger.info("⚙️ [Action-groupManagerPage] 群黑名单-点击添加黑名单成员")
        self.click(GroupManagerLocator.ADD_MEMBER_LL)

    # 群黑名单-移除黑名单成员
    def click_black_remove_member(self, name: str) -> None:
        """群黑名单-点击移除黑名单成员"""
        logger.info(f"⚙️ [Action-groupManagerPage] 群黑名单-移除【{name}】的黑名单")
        self.click(GroupManagerLocator.get_black_remove_member(name))

    # 群黑名单-获取当前列表展示的某一个成员姓名
    def is_black_member_name_exist(self, name: str) -> bool:
        """群黑名单-获取当前列表展示的某一个成员姓名"""
        logger.info(f"📋 [Action-groupManagerPage] 检查群黑名单是否存在成员姓名: {name}")
        black_list = self.find_elements(GroupManagerLocator.get_member_by_text(name), timeout=1)
        if not black_list:
            logger.warning(f"⚠️ [Action-groupManagerPage] 未找到列表中的成员姓名: {name}")
            return False
        logger.info(f"✅ [Action-groupManagerPage] 获取成员姓名: {name}")
        return True

    # 群黑名单-获取当前列表展示的所有成员姓名
    def get_black_member_names(self) -> list[str]:
        """群黑名单-获取当前列表展示的所有成员姓名"""
        logger.info("📋 [Action-groupManagerPage] 获取群黑名单展示的所有成员姓名")
        elements = self.find_elements(GroupManagerLocator.TV_FRIEND_NAME)
        if not elements:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到列表中的成员姓名")
            return []
        names = [el.get_attribute("text") for el in elements]
        logger.info(f"✅ [Action-groupManagerPage] 获取成员姓名成功: {names}")
        return names

    # 群黑名单-二次确认-点击确认按钮
    def click_black_remove_member_confirm(self) -> None:
        """群黑名单-二次确认-点击确认按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 群黑名单-二次确认-点击确认按钮")
        self.click(GroupManagerLocator.TEXT_CONFIRM_BTN)
        time.sleep(0.5)
    
    # 群黑名单-二次确认-点击取消按钮
    def click_black_remove_member_cancel(self) -> None:
        """群黑名单-二次确认-点击取消按钮"""
        logger.info("⚙️ [Action-groupManagerPage] 群黑名单-二次确认-点击取消按钮")
        self.click(GroupManagerLocator.TEXT_CANCEL_BTN)
        time.sleep(0.5)


    # ==================================================================================
    # 转让群主相关
    # ==================================================================================
    # 群管理-等待转让群主页面加载完成
    def wait_for_transfer_group_owner_page_load(self, timeout: int = 10) -> bool:
        """等待转让群主页面加载完成"""
        logger.info(f"⏳ [Action-groupManagerPage] 等待转让群主页面加载 (超时: {timeout}s)")
        res = self.get_attribute(GroupManagerLocator.TV_TITLE, "text") == "转让群主"
        logger.info(f"⏳ [Action-groupManagerPage] 转让群主页面 - 加载{'成功' if res else '超时'}")
        time.sleep(0.5)
        return res

    # 群管理-获取已拥有的权限名称
    def get_has_permissions_names(self) -> list[str]:
        """群管理-获取已拥有的权限名称"""
        logger.info("📋 [Action-groupManagerPage] 获取已拥有的权限名称")
        elements = self.find_elements(GroupManagerLocator.TITLE_TV)
        if not elements:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到已拥有的权限名称")
            return []
        names = [el.get_attribute("text") for el in elements]
        logger.info(f"✅ [Action-groupManagerPage] 获取已拥有的权限名称成功: {names}")
        return names





