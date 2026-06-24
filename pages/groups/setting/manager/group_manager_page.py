import time
from core.logger_utils import logger
from common.base_page import BasePage
from locators.groups.setting.manager.group_manager_locator import GroupManagerLocator
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

    # 顶部-点击返回按钮
    def click_back_button(self):
        """顶部-点击顶部返回按钮"""
        self.click(GroupManagerLocator.IV_BACK)
        logger.info("⚙️ [Action-groupManagerPage] 点击顶部【返回】按钮")
    
    # 顶部-点击确定按钮
    def click_confirm_button(self):
        """顶部-点击确定按钮"""
        self.click(GroupManagerLocator.FB_BTN)
        logger.info("⚙️ [Action-groupManagerPage] 点击顶部【确定】按钮")

    # 顶部-点击编辑完成按钮
    def click_edit_finish_button(self):
        """顶部-点击编辑完成按钮"""
        self.click(GroupManagerLocator.EDIT_TO_BTN)
        logger.info("⚙️ [Action-groupManagerPage] 点击编辑【完成】按钮")

    # 群管理-点击升级群组
    def click_upgrade_group(self):
        """群管理-点击升级群组"""
        self.click(GroupManagerLocator.VIEW_UPDATE_GROUP)
        logger.info("⚙️ [Action-groupManagerPage] 点击【升级群组】")

    # 群管理-点击管理员
    def click_administrators(self):
        """群管理-点击管理员"""
        self.click(GroupManagerLocator.IT_GROUP_MANAGER)
        logger.info("⚙️ [Action-groupManagerPage] 点击【管理员】")

    # 群管理-点击进群申请
    def click_join_to_group_apply(self):
        """群管理-点击进群申请"""
        self.click(GroupManagerLocator.JOIN_TO_GROUP_APPLY)
        logger.info("⚙️ [Action-groupManagerPage] 点击【进群申请】")

    # 群管理-点击指定成员禁言
    def click_mute_member(self):
        """群管理-点击指定成员禁言"""
        self.click(GroupManagerLocator.GROUP_MEMBER_MUTE)
        logger.info("⚙️ [Action-groupManagerPage] 点击【指定成员禁言】")

    # 群管理-点击群黑名单
    def click_group_black_member(self):
        """群管理-点击群黑名单"""
        self.click(GroupManagerLocator.GROUP_BLACK_MEMBER)
        logger.info("⚙️ [Action-groupManagerPage] 点击【群黑名单】")

    # 群管理-点击转让群主
    def click_group_give(self):
        """群管理-点击转让群主"""
        self.click(GroupManagerLocator.GROUP_GIVE)
        logger.info("⚙️ [Action-groupManagerPage] 点击【转让群主】")

    # 群管理-点击解散群组
    def click_dismiss_group(self):
        """点击解散群组"""
        self.click(GroupManagerLocator.DISMISS_GROUP)
        logger.info("⚙️ [Action-groupManagerPage] 点击【解散群组】")


    # ===================================================================================
    # 管理员列表相关
    # ===================================================================================
    # 管理员-等待管理员列表页面加载完成
    def wait_for_admin_page_load(self, timeout: int = 10) -> bool:
        """管理员-等待管理员列表页面加载完成"""
        res = self.get_attribute(GroupManagerLocator.TITLE_TV, "text") == "群管理员"
        logger.info(f"⏳ [Action-groupManagerPage] 管理员列表页面 - 加载{'成功' if res else '超时'}")
        time.sleep(0.5)
        return res

    # 管理员-点击新增管理员按钮
    def click_add_admin(self):
        """管理员-点击新增管理员按钮"""
        self.click(GroupManagerLocator.IT_ADD_FRIEND)
        logger.info("⚙️ [Action-groupManagerPage] 点击【新增管理员】按钮")

    # 管理员-在管理员搜索框输入关键字
    def input_admin_search_keyword(self, keyword: str):
        """管理员-在管理员搜索框输入关键字"""
        self.send_keys(GroupManagerLocator.EDIT_SEARCH, keyword)
        logger.info(f"✍️ [Action-groupManagerPage] 管理员搜索框输入: '{keyword}'")

    # 管理员-在成员搜索输入框输入关键字
    def input_member_search_keyword(self, keyword: str):
        """管理员-在成员搜索输入框输入关键字"""
        self.send_keys(GroupManagerLocator.search_edit_text, keyword)
        logger.info(f"✍️ [Action-groupManagerPage] 成员搜索输入框输入: '{keyword}'")

    # 管理员-获取当前列表展示的所有成员姓名
    def get_member_names(self) -> list[str]:
        """管理员-获取当前列表展示的所有成员姓名"""
        elements = self.find_elements(GroupManagerLocator.TV_FRIEND_NAME)
        if not elements:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到列表中的成员姓名")
            return []
        names = [el.get_attribute("text") for el in elements]
        logger.info(f"✅ [Action-groupManagerPage] 获取成员姓名成功: {names}")
        return names

    # 管理员-根据姓名点击列表中的某个成员
    def click_member_by_name(self, name: str):
        """管理员-根据姓名点击列表中的某个成员"""
        locator = GroupManagerLocator.get_member_by_text(name)
        self.click(locator)
        logger.info(f"⚙️ [Action-groupManagerPage] 点击列表中姓名为【{name}】的成员")
        time.sleep(0.5)

    # 管理员-获取管理员/群成员标签标识文本
    def get_member_type(self) -> str:
        """管理员-获取管理员/群成员标签标识文本"""
        res = self.get_attribute(GroupManagerLocator.MEMBER_TYPE, "text", raise_exception=False)
        logger.info(f"✅ [Action-groupManagerPage] 获取角色标签: {res}")
        return res
    
    # 管理员-点击移除管理员按钮
    def click_sure_button(self):
        """管理员-点击移除管理员按钮"""
        self.click(GroupManagerLocator.SURE_BTN)
        logger.info("⚙️ [Action-groupManagerPage] 点击【移除管理员】按钮")

    # 管理员-点击二次弹窗移除按钮
    def click_sure_content_button(self):
        """管理员-点击二次弹窗移除按钮"""
        self.click(GroupManagerLocator.TV_CONTENT)
        logger.info("⚙️ [Action-groupManagerPage] 点击【移除】按钮")


    # =========================================================================================
    # Switch 开关类操作
    # =========================================================================================
    
    # Switch - 获取群ID搜索开关
    def get_group_id_search_state(self) -> str:
        """Switch - 获取【群ID搜索】开关状态"""
        res = self.get_attribute(GroupManagerLocator.GROUP_ID_SEARCH_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【群ID搜索】开关状态: {res}")
        return str(res).lower()
    
    # Switch - 点击群ID搜索开关
    def click_group_id_search_switch(self, checked_str):
        """Switch - 点击【群ID搜索】开关"""
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
        res = self.get_attribute(GroupManagerLocator.JOIN_TO_GROUP_VERIFY_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【进群验证】开关状态: {res}")
        return str(res).lower()
    
    # Switch - 点击进群验证开关
    def click_join_group_verify_switch(self, checked_str):
        """Switch - 点击【进群验证】开关"""
        init_state = self.get_join_group_verify_state()
        if init_state == checked_str:
            logger.info(f"⚙️ [Action-groupManagerPage] 【进群验证】开关状态已经是{checked_str},无需点击")
        else:
            self.click(GroupManagerLocator.JOIN_TO_GROUP_VERIFY_SWITCH)
            time.sleep(1)
            logger.info(f"⚙️ [Action-groupManagerPage] 将【进群验证】开关设置为{checked_str}")
    
    # Switch - 获取全员禁言开关
    def get_all_member_mute_state(self) -> str:
        """Switch - 获取【全员禁言】开关状态"""
        res = self.get_attribute(GroupManagerLocator.ALL_MEMBER_MUTE_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【全员禁言】开关状态: {res}")
        return str(res).lower()
    
    # Switch - 点击全员禁言开关
    def click_all_member_mute_switch(self, checked_str):
        """Switch - 点击【全员禁言】开关"""
        init_state = self.get_all_member_mute_state()
        if init_state == checked_str:
            logger.info(f"⚙️ [Action-groupManagerPage] 【全员禁言】开关状态已经是{checked_str},无需点击")
        else:
            self.click(GroupManagerLocator.ALL_MEMBER_MUTE_SWITCH)
            time.sleep(1)
            logger.info(f"⚙️ [Action-groupManagerPage] 将【全员禁言】开关设置为{checked_str}")

    # Switch - 获取禁止群成员互相加好友开关
    def get_un_add_friend_each_other_state(self) -> str:
        """Switch - 获取【禁止群成员互相加好友】开关状态"""
        res = self.get_attribute(GroupManagerLocator.UN_ADD_FRIEND_EACH_OTHER_SWITCH, "checked")
        logger.info(f"⚙️ [Action-groupManagerPage] 获取【禁止群成员互相加好友】开关状态: {res}")
        return str(res).lower()

    # Switch - 点击禁止群成员互相加好友开关
    def click_un_add_friend_each_other_switch(self, checked_str):
        """Switch - 点击【禁止群成员互相加好友】开关"""
        init_state = self.get_un_add_friend_each_other_state()
        if init_state == checked_str:
            logger.info(f"⚙️ [Action-groupManagerPage] 【禁止群成员互相加好友】开关状态已经是{checked_str},无需点击")
        else:
            self.click(GroupManagerLocator.UN_ADD_FRIEND_EACH_OTHER_SWITCH)
            time.sleep(1)
            logger.info(f"⚙️ [Action-groupManagerPage] 将【禁止群成员互相加好友】开关设置为{checked_str}")

    # Switch - 获取 switch item 列表（支持状态过滤）
    def get_switch_items(self, checked_str: str = None) -> list[WebElement]:
        """Switch - 获取 switch item 列表（可按 checked_str "true"/"false" 过滤，None 表示获取全部）"""
        if checked_str is None:
            locator = GroupManagerLocator.SWITCH_BTN
            desc = "全部"
        else:
            locator = GroupManagerLocator.get_switch_by_checked_value(checked_str)
            desc = "已开启" if checked_str == "true" else "未开启"

        switch_item_list = self.find_elements(locator)
        if not switch_item_list:
            logger.warning(f"⚠️ [Action-groupManagerPage] 未找到【{desc}】的 switch item")
            return []
        logger.info(f"✅ [Action-groupManagerPage] 获取【{desc}】的 switch item 列表, 共找到 {len(switch_item_list)} 个")
        return switch_item_list
    
    # Switch - 开启/关闭全部指定状态的 switch
    def click_all_switch(self, checked_str: str = "true", max_swipes: int = 5):
        """Switch - 开启/关闭全部指定状态的 switch（支持滑动遍历，checked_str=None 表示不分状态点击全部）"""
        swipes = 0
        desc = "全部" if checked_str is None else ("已开启" if checked_str == "true" else "未开启")
        last_source = ""

        while swipes <= max_swipes:
            is_changed, last_source = self.is_page_source_changed(last_source)
            if swipes > 0 and not is_changed:
                logger.info("⚙️ [Action-groupManagerPage] 滑动后页面 DOM 无变化，已达底部边界，退出切换")
                break

            current_elements = self.get_switch_items(checked_str=checked_str)
            if current_elements:
                for elem in current_elements:
                    try:
                        elem.click()
                        logger.info(f"⚙️ [Action-groupManagerPage] 已点击切换【{desc}】开关")
                        time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"⚠️ [Action-groupManagerPage] 点击开关失败: {e}")
            
            if swipes < max_swipes:
                logger.info(f"⚙️ [Action-groupManagerPage] 向下滚动寻找更多开关... (当前已滑动 {swipes} 次)")
                _, last_source = self.is_page_source_changed("")
                self.swipe_page(slid_type="up")
                time.sleep(0.5)
            else:
                break
            
            swipes += 1



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
    
    # 指定禁言-临时禁言，获取禁言时间
    def get_temp_mute_time(self) -> str:
        """指定禁言-临时禁言，获取禁言时间"""
        res = self.get_attribute(GroupManagerLocator.TV_TIME, "text")
        if not res:
            logger.warning("⚠️ [Action-groupManagerPage] 未找到禁言时间")
            return ""
        logger.info(f"✅ [Action-groupManagerPage] 成功获取禁言时间: {res}")
        return res

    # 指定禁言-临时禁言-点击确定选择时间
    def click_select_time(self):
        """指定禁言-临时禁言-点击确定选择时间"""
        self.click(GroupManagerLocator.TV_SURE)
        logger.info("⚙️ [Action-groupManagerPage] 禁言-点击确定选择时间")

    # 指定禁言-临时禁言-选择时长，并且支持切换禁言时长选项
    def click_time(self, rule_time: str, old_summary: str = "10分钟"):
        """指定禁言-临时禁言-选择并切换指定的禁言时长"""
        
        MUTE_DURATION_OPTIONS = ["10分钟", "30分钟", "2小时", "1天", "7天", "30天", "永久禁言"]
        logger.info(f"⚙️ [Action-groupManagerPage] 正在设置禁言时长为: {rule_time} (当前页面旧值: {old_summary})")

        # 检查滚轮选择器是否已经显示
        picker_visible = self.is_element_exist(GroupManagerLocator.LOOP_SELECTOR, timeout=2)

        if old_summary and rule_time == old_summary:
            if picker_visible:
                self.click_select_time()
                logger.info("⚙️ [Action-groupManagerPage] 禁言时长与当前设置相同，且弹窗已显示，直接点击确认关闭")
            else:
                logger.info("⚙️ [Action-groupManagerPage] 禁言时长与当前设置相同，且无弹窗显示，无需操作")
            return True

        # 如果选择器未显示，点击 TV_SUMMARY 以唤起滚轮选择弹窗
        if not picker_visible:
            logger.info("⚙️ [Action-groupManagerPage] 滚轮选择器未显示，尝试点击 TV_TIME 展开")
            if self.is_element_exist(GroupManagerLocator.TV_TIME, timeout=2):
                self.click(GroupManagerLocator.TV_TIME)
                picker_visible = self.is_element_exist(GroupManagerLocator.LOOP_SELECTOR, timeout=5)

        if not picker_visible:
            logger.error("❌ 找不到禁言时长选择器 LOOP_SELECTOR")
            return False

        picker_element = self.find_element(GroupManagerLocator.LOOP_SELECTOR)
        options = MUTE_DURATION_OPTIONS

        if old_summary in options:
            old_index = options.index(old_summary)
        else:
            old_index = len(options)

        if rule_time not in options:
            rule_time = options[0]
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









