import time
from typing import Optional
from core.logger_utils import logger
from common.base_page import BasePage
from appium.webdriver.webelement import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from locators.groups.setting.general.group_setting_locator import GroupSettingLocator

class GroupSettingPage(BasePage):
    """新版群聊设置（群信息/群管理）页面操作类"""

    # =========================================================================
    # 1. 页面加载与基础导航
    # =========================================================================
    # 等待群聊设置/群详情页面加载完成
    def wait_for_setting_page_load(self, timeout: int = 10) -> bool:
        """等待群聊设置/群详情页面加载完成（以顶部群二维码及群信息为特征锚点）"""
        logger.info(f"⏳ [Action-groupSettingPage] 等待群聊设置页加载完成 (超时: {timeout}s)")
        res = self.is_element_exist(GroupSettingLocator.TOP_GROUP_CODE, timeout=timeout)
        if not res:
            res = self.is_element_exist(GroupSettingLocator.GROUP_NAME_ROW, timeout=timeout)
        logger.info(f"⏳ [Action-groupSettingPage] 群聊设置页 - 页面加载{'成功' if res else '超时'}")
        return res

    # 顶部栏 - 点击返回
    def click_iv_back_button(self) -> None:
        """通用点击返回按钮"""
        logger.info("🔙 [Action-groupSettingPage] 通用 Common 点击返回按钮")
        self.click(GroupSettingLocator.IV_BACK_BUTTON)

    # 顶部栏 - 点击顶部返回按钮
    def click_back_button(self) -> None:
        """点击顶部返回按钮"""
        logger.info("🔙 [Action-groupSettingPage] 点击顶部返回按钮")
        self.click(GroupSettingLocator.BACK)

    # 顶部栏 - 点击顶部群二维码
    def click_group_qr_code(self) -> None:
        """点击顶部群二维码"""
        logger.info("✅ [Action-groupSettingPage] 点击顶部【群二维码】")
        self.click(GroupSettingLocator.TOP_GROUP_CODE)

    # 顶部栏 - 点击顶部群分享按钮
    def click_group_share(self) -> None:
        """点击顶部群分享按钮"""
        logger.info("✅ [Action-groupSettingPage] 点击顶部【群分享】")
        self.click(GroupSettingLocator.TOP_GROUP_SHARE)

    # =========================================================================
    # 2. 成员区域操作
    # =========================================================================
    # 群成员-获取群成员头像元素列表
    def get_friend_headers(self) -> list[WebElement]:
        """获取群成员头像元素列表"""
        logger.info("📋 [Action-groupSettingPage] 获取群成员头像元素列表")
        elements = self.find_elements(GroupSettingLocator.FRIEND_HEADER, timeout=2)
        if not elements:
            logger.warning("⚠️ [Action-groupSettingPage] 获取群成员头像失败或为空")
            return []
        logger.info(f"✅ [Action-groupSettingPage] 获取群成员头像成功，共 {len(elements)} 个")
        return elements

    # 群成员-点击群成员头像【+】按钮 (friend_headers 倒数第二个为 + 号)
    def click_add_friend_header(self) -> None:
        """点击群成员【+】添加成员按钮 (friend_headers 倒数第二个为 + 号)"""
        logger.info("⚙️ [Action-groupSettingPage] 点击群成员【+】添加成员按钮")
        headers = self.get_friend_headers()
        if len(headers) >= 2:
            headers[-2].click()
            logger.info("✅ [Action-groupSettingPage] 已点击群成员【+】添加成员按钮")
        else:
            logger.warning("⚠️ [Action-groupSettingPage] 群成员头像数量不足，未能点击【+】按钮")

    # 群成员-点击群成员头像（默认为群助手/群主）
    def click_friend_header(self) -> None:
        """点击首个群成员头像（默认为群主/自己）"""
        logger.info("⚙️ [Action-groupSettingPage] 点击【群成员头像】")
        self.click(GroupSettingLocator.FRIEND_HEADER)

    # 群成员-点击群成员名称（默认为群助手/群主）
    def click_friend_name(self) -> None:
        """点击首个群成员名称"""
        logger.info("⚙️ [Action-groupSettingPage] 点击【群成员名称】")
        self.click(GroupSettingLocator.FRIEND_NAME)

    # 群成员-获取群聊页面群成员名称列表
    def get_friend_names(self) -> list[str]:
        """获取可见的群成员名称文本列表"""
        logger.info("📋 [Action-groupSettingPage] 获取群成员名称列表")
        elements = self.find_elements(GroupSettingLocator.FRIEND_NAME, timeout=2)
        if not elements:
            logger.warning("⚠️ [Action-groupSettingPage] 获取群成员名称列表失败")
            return []
        names = [element.get_attribute("text") for element in elements if element.get_attribute("text")]
        logger.info(f"✅ [Action-groupSettingPage] 获取群成员名称成功: {names}")
        return names

    # 群成员-根据成员名称定位其头像并点击
    def click_member_avatar_by_name(self, name: str) -> None:
        """根据成员名称定位其头像并点击"""
        logger.info(f"⚙️ [Action-groupSettingPage] 点击成员【{name}】的头像")
        self.click(GroupSettingLocator.get_member_avatar_by_name(name), timeout=2)

    # 群成员-判断是否存在删除群成员按钮
    def is_delete_member_btn_visible(self, index: int = -1) -> bool:
        """判断是否存在删除群成员【-】按钮"""
        logger.info(f"🔍 [Action-groupSettingPage] 检查是否存在删除群成员【-】按钮 (索引: {index})")
        from utils.file_reader.data_loader import find_file
        from utils.cv_recognition.screenshot_utils import ScreenshotUtils, ImageComparator

        headers = self.get_friend_headers()
        if not headers or abs(index) > len(headers):
            logger.warning("⚠️ [Action-groupSettingPage] 群成员头像列表为空或索引溢出")
            return False

        del_btn = headers[index]
        template_path = find_file(filename="images/delbtn.png")

        if template_path is None or not template_path.exists():
            logger.error(f"❌ 找不到本地模板图片: {template_path}")
            return False

        try:
            element_bytes = ScreenshotUtils.element_png(del_btn)
            with open(template_path, "rb") as f:
                template_bytes = f.read()
            res = ImageComparator.compare_similarity(template_bytes, element_bytes, threshold=30)
            logger.info(f"⚙️ [Action-groupSettingPage] 对比删除按钮截图结果: {res}")
            return res
        except Exception as e:
            logger.error(f"❌ 对比删除按钮截图失败: {e}")
            return False

    # =========================================================================
    # 3. 基础信息设置项 (群头像、群名称、群备注)
    # =========================================================================
    # 基础信息-点击群头像
    def click_group_avatar(self) -> None:
        """点击群头像"""
        logger.info("✅ [Action-groupSettingPage] 点击【群头像】")
        self.click(GroupSettingLocator.GROUP_HEADER)

    # 基础信息-点击群聊名称行
    def click_group_name(self) -> None:
        """点击群聊名称行"""
        logger.info("✅ [Action-groupSettingPage] 点击【群聊名称】行")
        self.click(GroupSettingLocator.GROUP_NAME_ROW)

    # 基础信息-获取当前显示的群聊名称
    def get_nva_group_name(self) -> str:
        """获取当前显示的群聊名称"""
        logger.info("📋 [Action-groupSettingPage] 获取当前显示的群聊名称")
        time.sleep(0.5)
        res = self.get_attribute(GroupSettingLocator.GROUP_NAME_HEADER, 'text', timeout=2)
        if not res:
            logger.warning("❌ [Action-groupSettingPage] 获取群聊名称失败")
            return ""
        logger.info(f"✅ [Action-groupSettingPage] 获取当前群聊名称: '{res}'")
        return res

    # 基础信息-点击群备注行
    def click_group_remark(self) -> None:
        """点击群备注行"""
        logger.info("✅ [Action-groupSettingPage] 点击【群备注】行")
        self.click(GroupSettingLocator.GROUP_REMARK_ROW)

    # 基础信息-获取当前显示的群备注文本
    def get_group_remark(self) -> str:
        """获取当前显示的群备注文本（自动剥离‘备注：’前缀）"""
        logger.info("📋 [Action-groupSettingPage] 获取当前【群备注】文本")
        time.sleep(0.5)
        res = self.get_attribute(GroupSettingLocator.GROUP_REMARK_HEADER, "text", raise_exception=False)
        if res:
            cleaned = res.replace("备注：", "").replace("备注:", "").strip()
            logger.info(f"📖 [Action-groupSettingPage] 获取当前【群备注】文本: '{cleaned}' (原始展示: '{res}')")
            return cleaned
        logger.warning("❌ [Action-groupSettingPage] 获取当前【群备注】文本失败")
        return ""

    # =========================================================================
    # 4. 快捷操作区域 (Quick Actions)
    # =========================================================================
    # 快捷操作-点击快捷【查找聊天记录】
    def click_search_chat_record(self) -> None:
        """点击快捷【查找聊天记录】"""
        logger.info("✅ [Action-groupSettingPage] 点击快捷【查找聊天记录】")
        self.click(GroupSettingLocator.GROUP_QUICK_SEARCH)

    # 快捷操作-点击快捷【置顶】
    def click_chat_settop(self) -> None:
        """点击快捷【置顶】"""
        logger.info("✅ [Action-groupSettingPage] 点击快捷【置顶】")
        self.click(GroupSettingLocator.GROUP_QUICK_PIN)

    # 快捷操作-获取群聊快捷置顶状态
    def get_switch_top_status(self) -> str:
        """获取群聊快捷置顶状态：'取消置顶' 返回 'true'，'置顶聊天' 返回 'false'"""
        logger.info("📋 [Action-groupSettingPage] 获取群聊快捷置顶状态")
        text = self.get_attribute(GroupSettingLocator.GROUP_QUICK_PIN_TEXT, 'text', raise_exception=False)
        if text == "取消置顶":
            logger.info("🚀[Action-groupSettingPage] 群聊快捷置顶当前为【取消置顶】，状态为: true")
            return 'true'
        elif text == "置顶聊天":
            logger.info("🚀[Action-groupSettingPage] 群聊快捷置顶当前为【置顶聊天】，状态为: false")
            return 'false'
        logger.warning(f"⚠️ [Action-groupSettingPage] 未知群聊置顶文本: {text}")
        return text or ""

    # 快捷操作-点击快捷【群管理】
    def click_group_manager(self) -> None:
        """点击快捷【群管理】"""
        logger.info("✅ [Action-groupSettingPage] 点击快捷【群管理】")
        self.click(GroupSettingLocator.GROUP_QUICK_MANAGE)

    # 群功能项-群管理是否存在
    def is_group_manager_visible(self) -> bool:
        """判断快捷【群管理】是否存在"""
        logger.info("🔍 [Action-groupSettingPage] 检查快捷【群管理】是否存在")
        res = self.is_element_exist(GroupSettingLocator.GROUP_QUICK_MANAGE, timeout=1)
        if not res:
            logger.warning("❌ [Action-groupSettingPage] 快捷【群管理】不存在")
            return False
        logger.info(f"✅ [Action-groupSettingPage] 快捷【群管理】是否可见: {res}")
        return res

    # 快捷操作-点击快捷【更多】操作菜单
    def click_quick_more(self) -> None:
        """点击快捷【更多】操作菜单"""
        logger.info("✅ [Action-groupSettingPage] 点击快捷【更多】按钮")
        self.click(GroupSettingLocator.GROUP_QUICK_MORE)

    # =========================================================================
    # 5. 更多操作弹出项 (清空聊天记录、删除并退出、举报)
    # =========================================================================
    # 更多操作-点击【清空聊天记录】
    def click_clear_group_chat_message(self) -> None:
        """点击【清空聊天记录】（若未展示可先点击更多菜单）"""
        logger.info("✅ [Action-groupSettingPage] 点击【清空聊天记录】")
        if not self.is_element_exist(GroupSettingLocator.GROUP_MORE_CLEAR_CHAT, timeout=2):
            self.click_quick_more()
        self.click(GroupSettingLocator.GROUP_MORE_CLEAR_CHAT)

    # 更多操作-点击【删除并退出】
    def click_delete_and_out(self) -> None:
        """点击【删除并退出】（若未展示可先点击更多菜单）"""
        logger.info("✅ [Action-groupSettingPage] 点击【删除并退出】")
        if not self.is_element_exist(GroupSettingLocator.GROUP_MORE_DELETE_EXIT, timeout=2):
            self.click_quick_more()
        self.click(GroupSettingLocator.GROUP_MORE_DELETE_EXIT)

    # 更多操作-点击【举报】群聊
    def click_report_group(self) -> None:
        """点击【举报】群聊"""
        logger.info("✅ [Action-groupSettingPage] 点击【举报】群聊")
        if not self.is_element_exist(GroupSettingLocator.GROUP_MORE_REPORT, timeout=2):
            self.click_quick_more()
        self.click(GroupSettingLocator.GROUP_MORE_REPORT)

    # =========================================================================
    # 6. 公告与活跃度卡片
    # =========================================================================
    # 公告与活跃度-点击【群公告】卡片
    def click_group_notice(self) -> None:
        """点击【群公告】卡片"""
        logger.info("✅ [Action-groupSettingPage] 点击【群公告】卡片")
        self.click(GroupSettingLocator.GROUP_ANNOUNCEMENT_CARD)

    # 公告与活跃度-获取群公告卡片展示的标题文本
    def get_group_announcement_title(self) -> str:
        """获取群公告卡片展示的标题文本"""
        logger.info("📋 [Action-groupSettingPage] 获取群公告标题")
        res = self.get_attribute(GroupSettingLocator.GROUP_ANNOUNCEMENT_TITLE, 'text')
        logger.info(f"✅ [Action-groupSettingPage] 获取群公告标题: '{res}'")
        return res or ""

    # 公告与活跃度-获取群活跃度数值
    def get_group_active_value(self) -> str:
        """获取群活跃度数值"""
        logger.info("📋 [Action-groupSettingPage] 获取群活跃度数值")
        res = self.get_attribute(GroupSettingLocator.GROUP_ACTIVE_VALUE, 'text', raise_exception=False)
        logger.info(f"✅ [Action-groupSettingPage] 获取群活跃度: '{res}'")
        return res or ""

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

    # =========================================================================
    # 通用开关操作辅助方法 (Switch Helpers)
    # =========================================================================
    # 通用获取开关状态辅助方法
    def _get_switch_state(self, locator: tuple, name: str = "开关") -> bool:
        """通用获取开关状态（支持智能滚动查找）"""
        logger.info(f"⚙️ [Action-groupSettingPage] 获取【{name}】开关状态")
        element = self._scroll_find_element(locator)
        if element:
            res = str(element.get_attribute("checked")).lower() == 'true'
            logger.info(f"✅ [Action-groupSettingPage] 获取【{name}】开关状态结果: {res}")
            return res
        logger.warning(f"❌ [Action-groupSettingPage] 未找到【{name}】开关元素")
        return False

    # 通用切换或设置开关状态辅助方法
    def _toggle_or_set_switch(self, locator: tuple, name: str = "开关", target_state: Optional[bool] = None) -> bool:
        """
        通用切换或设置开关状态（单次查找，支持指定目标状态实现幂等操作）
        :param locator: 开关元素定位器
        :param name: 开关名称（日志输出）
        :param target_state: 目标状态。True/False 表示确保达到该状态；None 表示无条件反转点击
        """
        logger.info(f"⚙️ [Action-groupSettingPage] 准备切换或设置【{name}】开关状态 (目标: {target_state})")
        element = self._scroll_find_element(locator)
        if not element:
            logger.error(f"❌ [Action-groupSettingPage] 未找到【{name}】开关，无法执行点击")
            return False

        current_state = str(element.get_attribute("checked")).lower() == 'true'
        if target_state is not None:
            if current_state == target_state:
                logger.info(f"⚙️ [Action-groupSettingPage] 【{name}】已为目标状态 ({target_state})，无需重复点击")
                return True
            logger.info(f"⚙️ [Action-groupSettingPage] 【{name}】当前为 {current_state}，执行点击切换至 {target_state}")
        else:
            logger.info(f"⚙️ [Action-groupSettingPage] 【{name}】执行反转点击 (当前: {current_state})")

        element.click()
        logger.info(f"✅ [Action-groupSettingPage] 成功点击【{name}】开关")
        return True

    # =========================================================================
    # 7. 开关设置项业务方法 (免打扰、聊天密码、显示群昵称)
    # =========================================================================
    # 开关设置项-获取【消息免打扰】开关状态
    def get_dnd_switch_state(self) -> bool:
        """获取【消息免打扰】开关状态"""
        return self._get_switch_state(GroupSettingLocator.GROUP_DND_SWITCH_BTN, "消息免打扰")

    # 开关设置项-切换【消息免打扰】开关
    def click_chat_dnd(self, target_state: Optional[bool] = None) -> bool:
        """切换【消息免打扰】开关"""
        return self._toggle_or_set_switch(GroupSettingLocator.GROUP_DND_SWITCH_BTN, "消息免打扰", target_state)

    # 开关设置项-获取【聊天密码】开关状态
    def get_pwd_switch_state(self) -> bool:
        """获取【聊天密码】开关状态"""
        return self._get_switch_state(GroupSettingLocator.GROUP_PWD_SWITCH_BTN, "聊天密码")

    # 开关设置项-切换【聊天密码】开关
    def click_chat_pwd(self, target_state: Optional[bool] = None) -> bool:
        """切换【聊天密码】开关"""
        return self._toggle_or_set_switch(GroupSettingLocator.GROUP_PWD_SWITCH_BTN, "聊天密码", target_state)

    # 开关设置项-点击【设置名称(针对自己)】行
    def click_chat_name_forme(self) -> None:
        """点击【设置名称(针对自己)】行（智能滑动查找）"""
        logger.info("✅ [Action-groupSettingPage] 点击【设置名称(针对自己)】")
        element = self._scroll_find_element(GroupSettingLocator.GROUP_NAME_FORME_TITLE_TV)
        if element:
            element.click()
            logger.info("✅ [Action-groupSettingPage] 成功点击【设置名称(针对自己)】")
        else:
            logger.error("❌ [Action-groupSettingPage] 未找到【设置名称(针对自己)】行")

    # 开关设置项-获取【显示群成员昵称】开关状态
    def get_show_member_name_switch_state(self) -> bool:
        """获取【显示群成员昵称】开关状态"""
        return self._get_switch_state(GroupSettingLocator.GROUP_SHOW_MEMBER_NAME_SWITCH_BTN, "显示群成员昵称")

    # 开关设置项-切换【显示群成员昵称】开关状态
    def click_show_member_name_switch(self, target_state: Optional[bool] = None) -> bool:
        """切换【显示群成员昵称】开关状态"""
        return self._toggle_or_set_switch(GroupSettingLocator.GROUP_SHOW_MEMBER_NAME_SWITCH_BTN, "显示群成员昵称", target_state)

    # =========================================================================
    # 8. 通用确认/取消弹窗
    # =========================================================================
    # 通用弹窗-点击弹窗【确认】按钮
    def click_tv_confirm_button(self) -> None:
        """点击弹窗【确认】按钮"""
        logger.info("✅ [Action-groupSettingPage] 点击弹窗【确认】")
        self.click(GroupSettingLocator.TV_CONFIRM)

    # 通用弹窗-点击弹窗【取消】按钮
    def click_tv_cancel_button(self) -> None:
        """点击弹窗【取消】按钮"""
        logger.info("✅ [Action-groupSettingPage] 点击弹窗【取消】")
        self.click(GroupSettingLocator.TV_CANCEL)

    # =========================================================================
    # 9. 群头像弹窗交互
    # =========================================================================
    # 群头像弹窗-点击拍照
    def click_group_avatar_take_photo(self) -> None:
        """群头像弹窗 - 点击拍照"""
        logger.info("✅ [Action-groupSettingPage] 群头像弹窗 - 点击【拍照】")
        self.click(GroupSettingLocator.ACTION_TAKE_PHOTO)

    # 群头像-点击从相册选择
    def click_group_avatar_pick_gallery(self) -> None:
        """群头像弹窗 - 点击从相册选择"""
        logger.info("✅ [Action-groupSettingPage] 群头像弹窗 - 点击【从相册选择】")
        self.click(GroupSettingLocator.ACTION_PICK_GALLERY)

    # 群头像弹窗-判断相册选择弹窗是否显示
    def is_album_dialog_displayed(self, timeout: int = 2) -> bool:
        """群头像弹窗 - 判断相册选择弹窗是否显示"""
        logger.info(f"🔍 [Action-groupSettingPage] 检查相册选择弹窗是否显示 (超时: {timeout}s)")
        res = self.is_element_exist(GroupSettingLocator.ACTION_PICK_GALLERY, timeout=timeout)
        logger.info(f"✅ [Action-groupSettingPage] 群头像弹窗是否显示: {res}")
        return res

    # 群头像-点击保存图片
    def click_group_avatar_save_image(self) -> None:
        """群头像弹窗 - 点击保存图片"""
        logger.info("✅ [Action-groupSettingPage] 群头像弹窗 - 点击【保存图片】")
        self.click(GroupSettingLocator.ACTION_SAVE_IMAGE)

    # 群头像-点击取消按钮
    def click_group_avatar_cancel(self) -> None:
        """群头像弹窗 - 点击取消"""
        logger.info("✅ [Action-groupSettingPage] 群头像弹窗 - 点击【取消】")
        self.click(GroupSettingLocator.ACTION_CANCEL)

    # =========================================================================
    # 10. 群公告编辑与提示
    # =========================================================================
    # 群公告-等待群公告编辑页加载完成
    def wait_for_notice_dialog_load(self, timeout: int = 5) -> bool:
        """等待群公告编辑页加载完成"""
        logger.info(f"⏳ [Action-groupSettingPage] 等待群公告编辑页加载 (超时: {timeout}s)")
        res = self.get_attribute(GroupSettingLocator.TV_TITLE, 'text') == '群公告'
        logger.info(f"✅ [Action-groupSettingPage] 群公告页面加载状态: {res}")
        return res

    # 群公告编辑页-检查【@所有人】按钮是否存在
    def is_at_all_displayed(self) -> bool:
        """群公告编辑页 - 检查【@所有人】按钮是否存在"""
        logger.info("🔍 [Action-groupSettingPage] 检查【@所有人】按钮是否存在")
        res = self.is_element_exist(GroupSettingLocator.LL_AT_ALL, timeout=2)
        logger.info(f"✅ [Action-groupSettingPage] @所有人按钮是否存在: {res}")
        return res

    # =========================================================================
    # 11. 群名称修改弹窗与权限提示
    # =========================================================================
    # 群名称修改-获取群名称修改弹窗的说明/权限提示文本
    def get_group_name_dialog_message(self) -> str:
        """获取群名称修改弹窗的说明/权限提示文本"""
        logger.info("📋 [Action-groupSettingPage] 获取群名称修改弹窗提示文本")
        res = self.get_attribute(GroupSettingLocator.TV_SECOND, 'text', raise_exception=False)
        if not res:
            res = self.get_attribute(GroupSettingLocator.TV_MESSAGE, 'text', raise_exception=False)
        logger.info(f"✅ [Action-groupSettingPage] 获取群名称修改提示信息: '{res}'")
        return res or ""

    # =========================================================================
    # 12. 群备注修改弹窗
    # =========================================================================
    # 群备注-等待群备注/修改名称输入弹窗加载
    def wait_for_remark_dialog_load(self, nva_text: str = "群备注") -> bool:
        """等待群备注/修改名称输入弹窗加载"""
        logger.info(f"⏳ [Action-groupSettingPage] 等待群备注/修改名称输入弹窗加载: '{nva_text}'")
        title = self.get_attribute(GroupSettingLocator.REMARK_DIALOG_TITLE, 'text', timeout=2, raise_exception=False)
        res = (nva_text in title) if title else False
        logger.info(f"✅ [Action-groupSettingPage] 弹窗加载状态: {res}, 当前标题: '{title}'")
        return res

    # 群备注-输入群备注/名称文本内容
    def input_remark_content(self, text: str) -> None:
        """输入群备注/名称文本内容"""
        logger.info(f"✍️ [Action-groupSettingPage] 输入备注/名称内容: '{text}'")
        self.send_keys(GroupSettingLocator.REMARK_DIALOG_INPUT, text)

    # =========================================================================
    # 13. 我在本群昵称修改业务流
    # =========================================================================
    # 我在本群昵称-修改我在本群昵称业务流
    def change_my_group_nickname(self, nickname: str, action: str = "confirm") -> None:
        """修改我在本群昵称业务流（支持 confirm 确认或 cancel 取消）"""
        logger.info(f"⚙️ [Action-groupSettingPage] 准备修改【我在本群昵称】为: '{nickname}', 操作: 【{action}】")
        self.click_chat_name_forme()
        self.wait_for_remark_dialog_load(nva_text="我在本群")
        self.input_remark_content(nickname)
        if action == "confirm":
            self.click_tv_confirm_button()
        else:
            self.click_tv_cancel_button()
        logger.info(f"✅ [Action-groupSettingPage] 完成修改【我在本群昵称】为: '{nickname}', 执行【{action}】")

    # 我在本群昵称-获取当前【我在本群昵称】显示的文本
    def get_my_group_nickname(self) -> str:
        """获取当前【我在本群昵称】显示的文本"""
        logger.info("📋 [Action-groupSettingPage] 获取当前【我在本群昵称】显示的文本")
        time.sleep(0.25)
        element = self._scroll_find_element(GroupSettingLocator.GROUP_NAME_FORME_NVA_TV)
        if element:
            res = element.get_attribute("text")
            logger.info(f"✅ [Action-groupSettingPage] 获取当前【我在本群昵称】文本: '{res}'")
            return res or ""
        logger.warning("❌ [Action-groupSettingPage] 未找到【我在本群昵称】元素")
        return ""




