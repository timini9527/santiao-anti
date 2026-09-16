import time
from typing import Dict, List, Optional
from common.base_page import BasePage
from core.logger_utils import logger
from locators.groups.public_group.public_group_locator import PublicGroupLocator


class PublicGroupPage(BasePage):
    """公开群聊业务页面对象 (宿主位于添加朋友页面中)"""

    # =========================================================================
    # 1. 区域加载与可见性判断
    # =========================================================================
    def wait_for_public_group_loaded(self, timeout: int = 10) -> bool:
        """等待公开群聊模块与列表加载完成"""
        logger.info(f"⏳ [Wait-PublicGroup] 等待公开群聊列表加载完成 (超时: {timeout}s)")
        res = self.is_element_exist(PublicGroupLocator.RV_GROUP_RANK, timeout=timeout, raise_exception=False)
        if not res:
            res = self.is_element_exist(PublicGroupLocator.TV_RANK_TITLE, timeout=1, raise_exception=False)
        logger.info(f"⏳ [Wait-PublicGroup] 公开群聊列表加载状态: {'成功' if res else '超时'}")
        return res

    def is_public_group_visible(self, timeout: int = 3) -> bool:
        """判断公开群聊模块是否可见"""
        return self.wait_for_public_group_loaded(timeout=timeout)

    def get_rank_title(self) -> str:
        """获取公开群聊区域标题文本 (默认: '公开群聊')"""
        logger.info("📋 [Action-PublicGroup] 获取公开群聊区域标题文本")
        title = self.get_attribute(PublicGroupLocator.TV_RANK_TITLE, "text", raise_exception=False)
        logger.info(f"✅ [Action-PublicGroup] 获取到公开群聊标题: '{title}'")
        return title or ""

    # =========================================================================
    # 2. 控制按钮交互
    # =========================================================================
    def click_change_batch(self) -> None:
        """点击【换一批】按钮刷新公开群推荐列表"""
        logger.info("⚙️ [Action-PublicGroup] 点击【换一批】按钮")
        self.click(PublicGroupLocator.CL_CHANGE_BATCH)
        time.sleep(1)

    def click_rules(self) -> None:
        """点击【规则】按钮"""
        logger.info("⚙️ [Action-PublicGroup] 点击【规则】按钮")
        self.click(PublicGroupLocator.CL_RULES)

    # =========================================================================
    # 3. 列表数据查询与群项操作
    # =========================================================================
    def get_public_group_names(self) -> List[str]:
        """获取当前可见的所有公开群名称列表"""
        logger.info("📋 [Action-PublicGroup] 获取当前展示的所有公开群名称")
        elements = self.find_elements(PublicGroupLocator.RANK_ITEM_TV_NAME, timeout=3, raise_exception=False)
        if not elements:
            logger.warning("⚠️ [Action-PublicGroup] 未找到公开群名称列表")
            return []
        names = [elem.get_attribute("text") for elem in elements if elem.get_attribute("text")]
        logger.info(f"✅ [Action-PublicGroup] 成功获取公开群名称列表共 {len(names)} 个: {names}")
        return names

    def is_group_exist(self, name: str, timeout: int = 2) -> bool:
        """检查指定群名称的公开群是否存在于当前列表"""
        logger.info(f"🔍 [Action-PublicGroup] 检查公开群【{name}】是否存在于列表中")
        locator = PublicGroupLocator.get_group_item_by_name(name)
        res = self.is_element_exist(locator, timeout=timeout, raise_exception=False)
        logger.info(f"✅ [Action-PublicGroup] 公开群【{name}】存在状态: {res}")
        return res

    def get_group_info(self, name: str) -> Dict[str, str]:
        """
        获取指定公开群的卡片详细信息
        :param name: 群名称
        :return: 包含 name, active_value, member_num, group_id 的属性字典
        """
        logger.info(f"📋 [Action-PublicGroup] 获取公开群【{name}】的详细属性")
        info = {
            "name": name,
            "active_value": self.get_attribute(PublicGroupLocator.get_group_active_value_by_name(name), "text", raise_exception=False) or "",
            "member_num": self.get_attribute(PublicGroupLocator.get_group_member_num_by_name(name), "text", raise_exception=False) or "",
            "group_id": self.get_attribute(PublicGroupLocator.get_group_id_by_name(name), "text", raise_exception=False) or "",
        }
        logger.info(f"✅ [Action-PublicGroup] 获取公开群【{name}】信息结果: {info}")
        return info

    def click_join_group(self, name: str) -> None:
        """点击指定公开群的【加入】按钮"""
        logger.info(f"⚙️ [Action-PublicGroup] 点击公开群【{name}】的【加入】按钮")
        locator = PublicGroupLocator.get_group_join_btn_by_name(name)
        self.click(locator)

    def find_and_join_target_group(self, target_group: str, max_batches: int = 5) -> bool:
        """
        在公开群聊推荐列表中寻找指定目标群聊并点击【加入】
        若当前屏未展示，自动点击【换一批】进行多轮刷新匹配
        :param target_group: 指定目标群聊名称
        :param max_batches: 若当前列表未出现，最大尝试【换一批】刷新的次数
        :return: 是否成功在列表中匹配到目标群并点击【加入】
        """
        logger.info(f"🔍 [Action-PublicGroup] 准备在公开群列表中检索目标群: 【{target_group}】(最大换一批次数: {max_batches})")
        for attempt in range(max_batches + 1):
            if self.is_group_exist(target_group, timeout=2):
                logger.info(f"✅ [Action-PublicGroup] 成功在公开群列表匹配到目标群【{target_group}】(换一批尝试: {attempt}次)")
                self.click_join_group(target_group)
                return True
            if attempt < max_batches:
                logger.info(f"🔄 [Action-PublicGroup] 当前列表未见目标群【{target_group}】，点击【换一批】重试 ({attempt + 1}/{max_batches})")
                self.click_change_batch()
                time.sleep(1)
        logger.warning(f"⚠️ [Action-PublicGroup] 经过 {max_batches} 次换一批仍未在公开群推荐列表中找到目标群: 【{target_group}】")
        return False

    def click_copy_group_id(self, name: str) -> None:
        """点击指定公开群的【复制】群ID按钮"""
        logger.info(f"⚙️ [Action-PublicGroup] 点击公开群【{name}】的【复制群ID】按钮")
        locator = PublicGroupLocator.get_group_copy_btn_by_name(name)
        self.click(locator)

    def get_group_id(self, name: str) -> str:
        """获取指定公开群的群 ID（如 'ID 264312026'）"""
        logger.info(f"📋 [Action-PublicGroup] 获取公开群【{name}】的群ID")
        res = self.get_attribute(PublicGroupLocator.get_group_id_by_name(name), "text", raise_exception=False)
        logger.info(f"✅ [Action-PublicGroup] 公开群【{name}】群ID文本: '{res}'")
        return res or ""

    # =========================================================================
    # 4. 公开群详情页面 (Group Detail Page) 交互
    # =========================================================================
    def wait_for_detail_page_loaded(self, timeout: int = 10) -> bool:
        """等待公开群详情页面加载完成"""
        logger.info(f"⏳ [Wait-PublicGroupDetail] 等待公开群详情页加载 (超时: {timeout}s)")
        res = self.is_element_exist(PublicGroupLocator.GROUP_NAME, timeout=timeout, raise_exception=False)
        if not res:
            res = self.is_element_exist(PublicGroupLocator.GROUP_ADD, timeout=1, raise_exception=False)
        logger.info(f"⏳ [Wait-PublicGroupDetail] 公开群详情页加载状态: {'成功' if res else '超时'}")
        return res

    def get_detail_group_name(self) -> str:
        """获取详情页展示的群名称"""
        logger.info("📋 [Action-PublicGroupDetail] 获取详情页群名称")
        res = self.get_attribute(PublicGroupLocator.GROUP_NAME, "text", raise_exception=False)
        logger.info(f"✅ [Action-PublicGroupDetail] 详情页群名称: '{res}'")
        return res or ""

    def get_detail_group_id_text(self) -> str:
        """获取详情页展示的群ID文本 (如 '群ID:979666985')"""
        logger.info("📋 [Action-PublicGroupDetail] 获取详情页群ID文本")
        res = self.get_attribute(PublicGroupLocator.GROUP_ID_TEXT, "text", raise_exception=False)
        logger.info(f"✅ [Action-PublicGroupDetail] 详情页群ID文本: '{res}'")
        return res or ""

    def click_detail_copy_group_id(self) -> None:
        """点击详情页群ID后面的【复制】图标按钮"""
        logger.info("⚙️ [Action-PublicGroupDetail] 点击详情页复制群ID按钮")
        self.click(PublicGroupLocator.GROUP_ID_COPY)

    def get_detail_action_btn_text(self) -> str:
        """获取详情页底部操作按钮文本 (如 '发送消息' / '申请加入' / '加入')"""
        logger.info("📋 [Action-PublicGroupDetail] 获取详情页操作按钮文本")
        res = self.get_attribute(PublicGroupLocator.GROUP_ADD, "text", raise_exception=False)
        logger.info(f"✅ [Action-PublicGroupDetail] 详情页操作按钮文本: '{res}'")
        return res or ""

    def click_detail_action_button(self) -> None:
        """点击详情页底部操作按钮 (如 '发送消息' / '申请加入' / '加入')"""
        btn_text = self.get_detail_action_btn_text()
        logger.info(f"⚙️ [Action-PublicGroupDetail] 点击详情页操作按钮: '{btn_text}'")
        self.click(PublicGroupLocator.GROUP_ADD)

