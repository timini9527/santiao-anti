import time
from typing import List, Optional
from appium.webdriver.webelement import WebElement
from common.base_page import BasePage
from locators.friend.tag_group.contact_tag_group_locator import ContactTagGroupLocator
from core.logger_utils import logger


class ContactTagGroupPage(BasePage):
    """通讯录好友分组/标签管理页面对象"""

    # =========================================================================
    # 等待 - 页面等待与通用导航
    # =========================================================================
    # 等待 - 页面等待与通用导航
    def wait_for_group_list_page_load(self, timeout: int = 10, page_title: str = "0", raise_exception: bool = True) -> bool:
        """ 等待 - 等待好友分组/标签列表页面加载完成 """
        titles = {
            "0": "分组",
            "1": "管理分组"
        }
        title = titles.get(page_title)
        if not title:
            logger.error(f"❌ [Wait - TagGroup] 无效的页面标题参数: {page_title}")
            return False
        logger.info(f"⏳ [Wait - TagGroup] 等待好友分组/标签列表页加载 (标题: '{title}', 超时: {timeout}s)")
        is_loaded = self.wait_for_element_text(ContactTagGroupLocator.TV_TITLE, expected_text=title, timeout=timeout, raise_exception=raise_exception)
        if is_loaded:
            logger.info(f"⏳ [Wait - TagGroup] 好友分组/标签列表页加载完成 - 页面标题: '{title}'")
        else:
            logger.warning(f"⚠️ [Wait - TagGroup] 好友分组/标签列表页加载超时 - 页面标题: '{title}'")
        return is_loaded

    # 分组页面 - 点击顶部返回按钮
    def click_iv_back(self) -> None:
        """ 分组页面 - 点击顶部返回按钮 """
        logger.info("🔙 [Action - TagGroup] 点击顶部【返回】按钮")
        self.click(ContactTagGroupLocator.IV_BACK)

    # 分组页面 - 点击右上角保存按钮
    def click_save_group(self) -> None:
        """ 分组页面 - 点击右上角保存/完成按钮 """
        logger.info("⚙️ [Action - TagGroup] 点击右上角【保存/完成】按钮")
        self.click(ContactTagGroupLocator.TV_ACTION_SAVE)

    # =========================================================================
    # 2. 首页分组列表交互
    # =========================================================================
    # 管理分组页面 - 点击添加分组
    def click_add_subgroup(self) -> None:
        """ 管理分组页面 - 点击【添加分组】按钮 """
        logger.info("⚙️ [Action - TagGroup] 点击【添加分组】按钮")
        self.click(ContactTagGroupLocator.ADD_SUBGROUP)

    # 管理分组页面 - 获取列表展现的所有分组/标签名称
    def get_group_names(self, timeout: int = 5) -> list[str]:
        """ 管理分组页面 - 获取列表展现的所有分组/标签名称 """
        logger.info(f"📋 [Action - TagGroup] 获取分组名称列表 (超时: {timeout}s)")
        elems = self.find_elements(ContactTagGroupLocator.GROUP_ITEM_TV, timeout=timeout)
        if not elems:
            logger.warning("⚠️ [Action - TagGroup] 管理分组页面 - 未找到任何分组或标签")
            return []
        names = [e.text for e in elems if e.text]
        logger.info(f"📋 [Action - TagGroup] 管理分组页面 - 获取到分组名称列表: {names}")
        return names

    # 管理分组页面 - 获取分组标签名称
    def get_group_tag_names(self, timeout: int = 2, raise_exception: bool = True) -> list[str]:
        """ 管理分组页面 - 获取分组标签名称 """
        logger.info(f"📋 [Action - TagGroup] 获取分组标签名称 (超时: {timeout}s)")
        elems = self.find_elements(ContactTagGroupLocator.GROUP_ITEM_TV, timeout=timeout, raise_exception=raise_exception)
        if not elems:
            logger.warning("⚠️ [Action - TagGroup] 管理分组页面 - 未找到任何分组或标签")
            return []
        names = [e.text for e in elems if e.text]
        logger.info(f"📋 [Action - TagGroup] 管理分组页面 - 获取到分组名称列表: {names}")
        return names
    
    # 管理分组页面 - 根据名称点击对应分组条目
    def click_group_by_name(self, group_name: str) -> None:
        """ 管理分组页面 - 根据名称点击对应分组条目 """
        logger.info(f"⚙️ [Action - TagGroup] 管理分组页面 - 点击分组: '{group_name}'")
        locator = ContactTagGroupLocator.get_group_item_by_name(group_name)
        self.click(locator)

    # 管理分组页面 - 获取分组编辑按钮
    def get_group_edit_buttons(self, timeout: int = 2, raise_exception: bool = True) -> list[WebElement]:
        """ 管理分组页面 - 获取分组编辑按钮 """
        logger.info(f"📋 [Action - TagGroup] 获取分组编辑按钮列表 (超时: {timeout}s)")
        elems = self.find_elements(ContactTagGroupLocator.GROUP_ITEM_EDIT, timeout=timeout, raise_exception=raise_exception)
        if not elems:
            logger.warning("⚠️ [Action - TagGroup] 管理分组页面 - 未找到任何分组编辑按钮")
            return []
        logger.info(f"📋 [Action - TagGroup] 管理分组页面 - 获取到分组编辑按钮列表数量: {len(elems)}")
        return elems
    
    # 管理分组页面 - 点击指定索引的分组编辑按钮
    def click_group_edit_by_index(self, group_index: int = 0, raise_exception: bool = True) -> bool:
        """ 管理分组页面 - 点击指定索引的分组编辑按钮 """
        logger.info(f"⚙️ [Action - TagGroup] 管理分组页面 - 尝试点击索引为 {group_index} 的分组编辑按钮")
        gebs = self.get_group_edit_buttons(raise_exception=raise_exception)
        if not gebs:
            logger.warning(f"⚠️ [Action - TagGroup] 管理分组页面 - 未找到任何分组编辑按钮")
            return False
        if group_index < 0 or group_index >= len(gebs):
            logger.warning(f"⚠️ [Action - TagGroup] 管理分组页面 - 索引 {group_index} 超出范围")
            return False
        gebs[group_index].click()
        logger.info(f"✅ [Action - TagGroup] 成功点击索引为 {group_index} 的分组编辑按钮")
        return True
    
    # 管理分组页面 - 根据分组名称点击其右侧的【编辑】按钮
    def click_group_edit_by_name(self, group_name: str) -> bool:
        """ 管理分组页面 - 根据分组名称点击其右侧的【编辑】按钮 """
        logger.info(f"⚙️ [Action - TagGroup] 管理分组页面 - 尝试点击分组 '{group_name}' 的【编辑】按钮")
        locator = ContactTagGroupLocator.get_group_item_edit_by_name(group_name)
        if self.is_element_exist(locator, timeout=3):
            self.click(locator)
            logger.info(f"✅ [Action - TagGroup] 成功点击分组 '{group_name}' 的【编辑】按钮")
            return True
        logger.error(f"❌ [Action - TagGroup] 未能找到分组 '{group_name}' 的编辑按钮")
        return False

    # 管理分组页面 - 二次确认
    def click_confirm_dialog(self) -> bool:
        """ 管理分组页面 - 二次确认删除分组 """
        logger.info("⚙️ [Action - TagGroup] 管理分组页面 - 尝试确认删除分组")
        if self.is_element_exist(ContactTagGroupLocator.DIALOG_CONFIRM_BTN, timeout=3):
            self.click(ContactTagGroupLocator.DIALOG_CONFIRM_BTN)
            logger.info("✅ [Action - TagGroup] 确认删除分组")
            return True
        logger.error("❌ [Action - TagGroup] 未找到删除二次确认弹窗")
        return False
    
    # 管理分组页面 - 二次取消
    def click_cancel_dialog(self) -> bool:
        """ 管理分组页面 - 二次取消删除分组 """
        logger.info("⚙️ [Action - TagGroup] 管理分组页面 - 尝试取消删除分组")
        if self.is_element_exist(ContactTagGroupLocator.DIALOG_CANCEL_BTN, timeout=3):
            self.click(ContactTagGroupLocator.DIALOG_CANCEL_BTN)
            logger.info("✅ [Action - TagGroup] 取消删除分组")
            return True
        logger.error("❌ [Action - TagGroup] 未找到取消二次确认弹窗")
        return False

    # =========================================================================
    # 3. 新建/管理分组详情页交互
    # =========================================================================
    # 管理分组页面 - 输入分组名称
    def input_subgroup_name(self, name: str) -> None:
        """ 管理分组页面 - 新建分组 - 在分组名称编辑框中输入文本 """
        logger.info(f"✍️ [Action - TagGroup] 管理分组页面 - 新建分组 - 输入分组名称: '{name}'")
        self.send_keys(ContactTagGroupLocator.CREATE_SUBGROUP_EDIT, name)

    # 管理分组页面 - 获取分组名称编辑框当前的输入内容
    def get_subgroup_name_input_text(self) -> str:
        """ 管理分组页面 - 新建分组 - 获取分组名称编辑框当前的输入内容 """
        logger.info("🔍 [Action - TagGroup] 获取分组名称编辑框文本")
        text = self.get_attribute(ContactTagGroupLocator.CREATE_SUBGROUP_EDIT, "text")
        logger.info(f"🔍 [Action - TagGroup] 管理分组页面 - 新建分组 - 获取分组名称编辑框文本: '{text}'")
        return text if text else ""

    # 管理分组页面 - 删除分组名称
    def click_delete_group_name(self) -> None:
        """ 管理分组页面 - 新建分组 - 删除分组名称 """
        logger.info("⚙️ [Action - TagGroup] 管理分组页面 - 新建分组 - 点击【删除分组名称】按钮")
        self.click(ContactTagGroupLocator.IV_DELETE)

    # 管理分组页面 - 添加成员
    def click_add_member(self) -> None:
        """ 管理分组页面 - 新建分组 - 点击【添加成员】按钮 """
        logger.info("⚙️ [Action - TagGroup] 管理分组页面 - 新建分组 - 点击【添加成员】按钮")
        self.click(ContactTagGroupLocator.CREATE_SUBGROUP_ADD_MEMBER)

    # 管理分组页面 - 获取分组成员列表中的好友昵称集合
    def get_member_names(self, timeout: int = 5) -> list[str]:
        """ 管理分组页面 - 新建分组 - 获取分组成员列表中的好友昵称集合 """
        logger.info(f"📋 [Action - TagGroup] 获取组内成员昵称 (超时: {timeout}s)")
        elems = self.find_elements(ContactTagGroupLocator.FRIEND_NAME_XPATH, timeout=timeout)
        names = [e.text for e in elems if e.text]
        logger.info(f"📋 [Action - TagGroup] 管理分组页面 - 新建分组 - 获取到组内成员昵称: {names}")
        return names

    # 管理分组页面 - 删除分组
    def click_delete_subgroup(self) -> None:
        """ 管理分组页面 - 新建分组 - 点击【删除分组】按钮 """
        logger.info("⚙️ [Action - TagGroup] 管理分组页面 - 新建分组 - 点击【删除分组】按钮")
        if self.is_element_exist(ContactTagGroupLocator.FB_DELETE, timeout=3):
            self.click(ContactTagGroupLocator.FB_DELETE)
            logger.info("✅ [Action - TagGroup] 成功点击【删除分组】按钮")
        else:
            logger.warning("⚠️ [Action - TagGroup] 管理分组页面 - 未找到【删除分组】按钮，请检查分组是否已删除")

    # 管理分组页面 - 删除分组完整交互流程
    def delete_group_flow(self) -> bool:
        """ 管理分组页面 - 新建分组 - 删除分组完整交互流程（点击删除按钮 -> 弹窗二次确认并等待切回列表页） """
        logger.info("⚙️ [Action - TagGroup] 管理分组页面 - 新建分组 - 执行删除分组完整流程")
        self.click_delete_subgroup()
        return self.click_confirm_dialog()

    # 管理分组页面 - 指定删除分组或删除全部
    def delete_group_or_all_groups_flow(self, group_name: Optional[str] = None, is_all: bool = False) -> bool:
        """ 
        管理分组页面 - 删除指定分组或批量清空全部分组
        :param group_name: 指定要删除的分组名称（当 is_all=False 时必填）
        :param is_all: 是否循环删除列表中展示的所有分组（有多少个删除多少个，直到清空为止）
        """
        if not is_all:
            if not group_name:
                logger.error("❌ [Action - TagGroup] 未指定 group_name，且 is_all 为 False，无法执行删除操作")
                return False
            logger.info(f"⚙️ [Action - TagGroup] 准备删除指定分组: '{group_name}'")
            if not self.click_group_edit_by_name(group_name):
                logger.error(f"❌ [Action - TagGroup] 未能找到分组 '{group_name}' 的编辑按钮，删除操作终止")
                return False
            res = self.delete_group_flow()
            if res:
                self.wait_for_group_list_page_load(raise_exception=False)
            return res
        else:
            logger.info("⚙️ [Action - TagGroup] 准备循环删除列表中所有的分组")
            deleted_count = 0
            while True:
                if not self.click_group_edit_by_index(group_index=0, raise_exception=False):
                    logger.warning("⚠️ [Action - TagGroup] 未找到分组编辑按钮，全部分组已清空完毕")
                    break
                if self.delete_group_flow():    
                    deleted_count += 1
                    self.wait_for_group_list_page_load(page_title="0", raise_exception=False)
                    time.sleep(0.5)
                    logger.info(f"⚙️ [Action - TagGroup] 批量删除中 - 已删除 {deleted_count} 个分组")
                else:
                    logger.error("❌ [Action - TagGroup] 批量删除中途删除失败，中断循环")
                    return False
            logger.info(f"✅ [Action - TagGroup] 批量清空分组完成，共删除 {deleted_count} 个分组")
            return True



