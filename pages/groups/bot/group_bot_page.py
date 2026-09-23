from typing import Optional
from core.logger_utils import logger
from common.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement
from locators.groups.bot.group_bot_locator import GroupBotLocator
import time


class GroupBotPage(BasePage):
    """群助手页面操作类，涵盖禁发关键词、发言管理、自动清理、入群验证、入群欢迎语、定时消息、自动清理群成员等功能域"""

    # 禁言时长档位（顺序与 picker 滚轮从上到下一致），页面与测试参数化共用，避免重复维护
    MUTE_DURATION_OPTIONS = ["10分钟", "30分钟", "2小时", "1天", "7天", "30天", "永久禁言"]

    # =============================================================================
    # 页面进入与基本导航
    # =============================================================================
    # 从群详情/群管理页进入群助手页面
    def wait_for_group_bot_page_load(self, timeout=10) -> bool:
        """从群详情/群管理页进入群助手页面"""
        bot_list = self.find_elements(GroupBotLocator.GROUP_BOT_RECYCLER_VIEW, timeout=timeout)
        if not bot_list:
            logger.warning(f"⚠️ [Action-GroupBotPage] 未找到群助手功能页面,等待超时 {timeout} 秒")
            raise Exception("未找到群助手功能页面")
        logger.info(f"✅ [Action-GroupBotPage] 成功进入【群助手功能页面】,共找到 {len(bot_list)} 个群助手功能")
        return True
    
    # 校验是否具有群助手权限
    def has_group_assistant_permission(self) -> bool:
        """校验是否具有群助手权限"""
        res = self.is_element_exist(GroupBotLocator.HAS_GROUP_BOT_PERMISSION, timeout=2, raise_exception=False)
        if res:
            logger.info(f"✅ [Action-GroupBotPage] 具有群助手权限")
        else:
            logger.warning(f"⚠️ [Action-GroupBotPage] 不具有群助手权限")
        return res

    # 进入【禁发关键词检测】设置页面
    def enter_keyword_block(self) -> None:
        """进入【禁发关键词检测】设置页面"""
        logger.info("⏳ [Action-GroupBotPage] 进入【禁发关键词检测】设置页")
        self.click(GroupBotLocator.KEYWORD_BLOCK_ENTRY)

    # 进入【发言管理】设置页面
    def enter_speech_manage(self) -> None:
        """进入【发言管理】设置页面"""
        logger.info("⏳ [Action-GroupBotPage] 进入【发言管理】设置页")
        self.click(GroupBotLocator.SPEECH_MANAGE_ENTRY)

    # 进入【自动清理成员】设置页面
    def enter_auto_clean(self) -> None:
        """进入【自动清理成员】页面"""
        logger.info("⏳ [Action-GroupBotPage] 进入【自动清理成员】页")
        self.click(GroupBotLocator.AUTO_CLEAN_ENTRY)

    # 进入【入群验证】设置页面
    def enter_join_verify(self) -> None:
        """进入【入群验证】设置页面"""
        logger.info("⏳ [Action-GroupBotPage] 进入【入群验证】设置页")
        self.click(GroupBotLocator.JOIN_VERIFY_ENTRY)

    # =============================================================================
    # 通用开关与保存/确认操作
    # =============================================================================
    # 获取当前页面主功能的 Switch 开关状态
    def get_switch_state(self) -> bool:
        """获取当前页面主功能的 Switch 开关状态"""
        checked = self.get_attribute(GroupBotLocator.SWITCH_BTN, "checked")
        state = str(checked).lower() == 'true'
        logger.info(f"⚙️ [Action-GroupBotPage] 获取 Switch 开关状态: {state}")
        return state
    
    # 主开关管理工具切换，在页面未加载完成时调用
    def toggle_main_switch(self, enable: bool, locator: tuple) -> None:
        """主开关管理工具切换，在页面未加载完成时调用"""
        logger.info(f"⚙️ [Action-GroupBotPage] 准备检查并切换开关状态: {locator} -> {enable}")
        checked = self.get_attribute(locator, "checked")
        current_state = str(checked).lower() == 'true'
        if current_state != enable:
            logger.info(f"⚙️ [Action-GroupBotPage] 切换 {locator} 开关状态 -> {enable}")
            self.click(locator)
        else:
            logger.info(f"⚙️ [Action-GroupBotPage] {locator} 开关状态已为 {enable}，无需切换")

    # 切换当前页面主 Switch 开关状态
    def toggle_switch(self, enable: bool) -> None:
        """切换当前页面主 Switch 开关状态（默认使用 GroupBotLocator.SWITCH_BTN）"""
        logger.info(f"⚙️ [Action-GroupBotPage] 切换当前页面主 Switch 开关状态 -> {enable}")
        self.toggle_main_switch(enable, GroupBotLocator.SWITCH_BTN)

    # 点击左上角返回图标
    def click_back(self) -> None:
        """点击左上角返回图标"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【返回】")
        self.click(GroupBotLocator.IV_BACK)

    # 点击右上角保存
    def click_save(self) -> None:
        """点击右上角保存"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【保存】")
        self.click(GroupBotLocator.SAVE_BTN)

    # 点击弹窗确认按钮
    def click_confirm(self) -> None:
        """点击弹窗确认按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击弹窗【确认】")
        self.click(GroupBotLocator.CONFIRM_BTN)

    # 点击弹窗取消按钮
    def click_cancel(self) -> None:
        """点击弹窗取消按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击弹窗【取消】")
        self.click(GroupBotLocator.CANCEL_BTN)
    
    def click_confirm_btn(self) -> None:
        """点击弹窗确认按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击弹窗【确认】")
        self.click(GroupBotLocator.BTN_CONFIRM)
    
    def click_cancel_btn(self) -> None:
        """点击弹窗取消按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击弹窗【取消】")
        self.click(GroupBotLocator.BTN_CANCEL)


    # =============================================================================
    # 禁发关键词检测页面细化操作
    # =============================================================================
    # 切换禁发关键词检测功能 Switch 开关状态
    def toggle_keyword_detection_switch(self, enable: bool) -> None:
        """切换禁发关键词检测功能 Switch 开关状态"""
        logger.info(f"⚙️ [Action-GroupBotPage] 切换禁发关键词检测功能 Switch 开关状态 -> {enable}")
        self.toggle_main_switch(enable, GroupBotLocator.SWITCH_BTN)
    
    # 关键词-点击关键词行进入关键词列表配置页
    def click_keyword_row(self) -> None:
        """关键词-点击关键词行进入关键词列表配置页"""
        logger.info("⚙️ [Action-GroupBotPage] 点击进入【关键词】配置列表")
        self.click(GroupBotLocator.KEYWORD_ENTRY)
    
    # 关键词-检查当前是否处于关键词列表页
    def is_in_keyword_list_page(self, timeout: float = 2) -> bool:
        """检查当前是否处于关键词配置列表页（存在新增关键词布局）"""
        return self.is_element_exist(GroupBotLocator.LAYOUT_ADD_KEYWORD, timeout=timeout, raise_exception=False)

    # 关键词-检查当前是否处于群助手禁发关键词配置页
    def is_in_keyword_config_page(self, timeout: float = 2) -> bool:
        """检查当前是否处于禁发关键词功能配置页（存在关键词入口行）"""
        return self.is_element_exist(GroupBotLocator.KEYWORD_ENTRY, timeout=timeout, raise_exception=False)

    # 关键词-获取关键词列表配置状态
    def get_keyword_summary(self) -> str:
        """关键词-获取关键词列表配置状态"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取关键词配置状态...")
        text = self.get_attribute(GroupBotLocator.KEYWORD_SUMMARY, 'text')
        logger.info(f"⚙️ [Action-GroupBotPage] 获取关键词配置状态: {text}")
        return text

    # 关键词-获取当前关键词输入框的元素
    def get_keywords_element(self, timeout: int = 2) -> WebElement:
        """关键词-获取当前关键词输入框的元素（优先匹配ID，兜底匹配EditText通用控件）"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取关键词输入框元素...")
        element = self.find_element(GroupBotLocator.ET_KEYWORDS, timeout=timeout, raise_exception=False)
        if not element:
            raise Exception("未找到新增关键词弹窗中的输入框")   
        logger.info(f"⚙️ [Action-GroupBotPage] 获取关键词输入框成功: {element}")
        return element
    
    # 关键词-清空关键词输入框
    def clear_keywords(self) -> None:
        """关键词-清空关键词输入框"""
        logger.info("⚙️ [Action-GroupBotPage] 清空关键词输入框")
        self.get_keywords_element().clear()

    # 关键词-若弹窗处于显示状态则取消关闭
    def cancel_keyword_dialog_if_displayed(self) -> None:
        """关键词-如果新增关键词弹窗仍处于显示状态，则点击取消关闭弹窗"""
        if self.is_element_exist(GroupBotLocator.ET_KEYWORDS, timeout=1, raise_exception=False):
            logger.info("⚙️ [Action-GroupBotPage] 检测到新增关键词弹窗未关闭，执行取消关闭")
            self.click_cancel_btn()

    # 关键词-点击新增关键词按钮
    def click_keyword_add_btn(self) -> None:
        """关键词-点击新增关键词按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【新增】关键词")
        self.click(GroupBotLocator.LAYOUT_ADD_KEYWORD)

    # 关键词-获取关键词输入框中的文本
    def get_keywords_text(self) -> str:
        """关键词-获取关键词输入框中的文本"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取关键词输入框中文本...")
        element = self.get_keywords_element()
        text = element.get_attribute("text")
        logger.info(f"⚙️ [Action-GroupBotPage] 获取关键词输入框中文本: {text}")
        return text

    # 关键词-向关键词输入框填入文本
    def input_keywords(self, text: str) -> None:
        """关键词-向关键词输入框填入文本"""
        logger.info(f"⚙️ [Action-GroupBotPage] 向关键词输入框填入文本: {text}")
        element = self.get_keywords_element()
        element.clear()
        element.send_keys(text)
    
    # 关键词-获取所有关键词所在的行（包含删除图标）的WebElement列表
    def get_keyword_row_element(self, timeout: float | int = 2, raise_exception: bool = True) -> list[WebElement]:
        """关键词-获取所有关键词所在的行（包含删除图标）的WebElement列表"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取所有关键词所在的行元素列表...")
        tv_keyword_list = self.find_elements(GroupBotLocator.TV_KEYWORD_NUMBER, timeout=timeout, raise_exception=raise_exception)
        if not tv_keyword_list:
            logger.warning("⚙️ [Action-GroupBotPage] 未找到关键词")
            return []
        logger.info(f"⚙️ [Action-GroupBotPage] 获取所有关键词所在行元素: {len(tv_keyword_list)}个")
        return tv_keyword_list
    
    # 关键词-获取所有关键词所在的行（包含删除图标）的数量
    def get_keyword_row_count(self, timeout: int | float = 1) -> int:
        """关键词-获取所有关键词所在的行（包含删除图标）的数量"""
        logger.info("⚙️ [Action-GroupBotPage] 正在统计关键词行数量...")
        return len(self.get_keyword_row_element(timeout, raise_exception=False))
    
    # 关键词-获取当前配置的所有关键词列表
    def get_keyword_list(self, timeout: int | float = 2) -> list[str]:
        """关键词-获取当前配置的所有关键词文本列表"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取关键词列表...")
        elements = self.get_keyword_row_element(timeout, raise_exception=False)
        if not elements:
            logger.warning("⚙️ [Action-GroupBotPage] 未找到关键词")
            return []
        keywords = [elem.text.strip() for elem in elements if elem.text and elem.text.strip()]
        logger.info(f"⚙️ [Action-GroupBotPage] 成功获取关键词列表 ({len(keywords)}个): {keywords}")
        return keywords

    # 关键词-保存关键词配置
    def save_keywords_config(self) -> None:
        """关键词-保存关键词配置"""
        logger.info("⚙️ [Action-GroupBotPage] 点击保存非空关键词配置")
        self.click(GroupBotLocator.TV_SAVE)

    # 关键词-获取删除图标元素
    def get_keyword_delete_icon_list(self, timeout: int | float = 2, raise_exception: bool = True) -> list[WebElement]:
        """关键词-获取关键词删除图标元素列表"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取关键词删除图标列表...")
        icons = self.find_elements(GroupBotLocator.DELETE_KEYWORD_ICON, timeout=timeout, raise_exception=raise_exception)
        if not icons:
            logger.warning("⚙️ [Action-GroupBotPage] 未找到关键词")
            return []
        logger.info(f"⚙️ [Action-GroupBotPage] 获取删除图标列表: {len(icons)}个")
        return icons

    # 关键词-获取删除图标数量
    def get_keyword_delete_icon_count(self, timeout: int | float = 1) -> int:
        """关键词-获取关键词删除图标数量"""
        return len(self.get_keyword_delete_icon_list(timeout, raise_exception=False))

    # 关键词-点击指定索引的删除图标
    def click_delete_keyword_icon(self, index: int = 0) -> None:
        """关键词-点击指定索引位置的删除图标"""
        logger.info(f"⚙️ [Action-GroupBotPage] 点击第 {index} 个关键词删除图标")
        icons = self.get_keyword_delete_icon_list()
        if not icons or len(icons) <= index:
            raise Exception(f"未找到索引为 {index} 的关键词删除图标，当前图标数量: {len(icons)}")
        icons[index].click()
    
    # 关键词-获取二次确认框中
    def get_confirm_dialog(self) -> bool:
        """关键词-获取二次确认框中的元素"""
        logger.info("⚙️ [Action-GroupBotPage] 正在检测删除二次确认框...")
        dialog = self.find_element(GroupBotLocator.MESSAGE_BOX, timeout=5)
        if not dialog:
            logger.warning("⚙️ [Action-GroupBotPage] 未找到二次确认框")
            return False
        logger.info("⚙️ [Action-GroupBotPage] 获取二次确认框成功")
        return True

    # 关键词-点击删除关键词二次确认框中的确认按钮
    def click_keyword_delete_confirm_btn(self) -> None:
        """关键词-点击删除关键词二次确认框中的【确认】按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【确认】删除关键词")
        self.click(GroupBotLocator.POSITIVE_BUTTON)
    
    # 关键词-点击删除关键词二次确认框中的取消按钮
    def click_keyword_delete_cancel_btn(self) -> None:
        """关键词-点击删除关键词二次确认框中的【取消】按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【取消】删除关键词")
        self.click(GroupBotLocator.NEGATIVE_BUTTON)

    # 关键词-清空已配置的关键词
    def clear_all_keywords(self, count: Optional[int] = None) -> None:
        """清空已配置的关键词，恢复到默认空状态。如果指定了 count，则只删除对应数量的关键词"""
        msg = "全部" if count is None else f"{count} 个"
        logger.info(f"⚙️ [Action-GroupBotPage] 开始动态删除关键词，目标数量: {msg}")
        deleted = 0
        while self.is_element_exist(GroupBotLocator.DELETE_KEYWORD_ICON, timeout=1, raise_exception=False):
            if count is not None and deleted >= count:
                logger.info(f"⚙️ [Action-GroupBotPage] 已达到指定删除数量 {count}，停止删除")
                break
            logger.info(f"⚙️ [Action-GroupBotPage] 动态获取删除图标并点击删除 (已删 {deleted} 个)")
            self.click(GroupBotLocator.DELETE_KEYWORD_ICON)
            self.click_keyword_delete_confirm_btn()
            deleted += 1
            time.sleep(0.1)
        # self.save_keywords_config()

    # 关键词-弹窗批量添加关键词
    def add_keywords(self, keywords: list[str] | str) -> int:
        """关键词-在关键词列表页通过弹窗批量录入关键词并确认添加

        支持传入列表或空格分隔的字符串，利用弹窗原生空格批量录入功能：
        单个关键词最多10个字，批量添加用空格分隔，点击【确定】完成添加。
        """
        if not keywords:
            return 0
        keyword_list = self.get_keyword_list()
        if any(key in keyword_list for key in keywords):
            logger.info(f"⚙️ [Action-GroupBotPage] 关键词已存在: {keywords}")
            return len(keywords)
        
        if isinstance(keywords, list):
            kw_list = [str(k).strip() for k in keywords if str(k).strip()]
            text = " ".join(kw_list)
        else:
            text = str(keywords).strip()
            kw_list = [k for k in text.split() if k]
        logger.info(f"⚙️ [Action-GroupBotPage] 准备通过新增关键词弹窗批量添加: {kw_list}")
        self.click_keyword_add_btn()
        self.input_keywords(text)
        self.click_confirm_btn()
        logger.info(f"✅ [Action-GroupBotPage] 弹窗批量添加关键词完成，共计 {len(kw_list)} 个")
        return len(kw_list)

    # 关键词-设置新的关键词列表（保持与旧调用的兼容性）
    def set_keywords(self, keywords: list[str] | str) -> int:
        """关键词-设置/添加关键词列表（智能识别弹窗状态并完成批量录入）"""
        if not keywords:
            return 0

        if isinstance(keywords, list):
            kw_list = [str(k).strip() for k in keywords if str(k).strip()]
            text = " ".join(kw_list)
        else:
            text = str(keywords).strip()
            kw_list = [k for k in text.split() if k]

        logger.info(f"⚙️ [Action-GroupBotPage] 准备填入关键词列表: {kw_list}")
        dialog_input = self.find_element((AppiumBy.CLASS_NAME, "android.widget.EditText"), timeout=1, raise_exception=False)
        if not dialog_input:
            self.click_keyword_add_btn()

        self.input_keyword(text)
        self.click_confirm()
        time.sleep(0.5)
        logger.info(f"✅ [Action-GroupBotPage] 关键词列表添加完成，共计 {len(kw_list)} 个")
        return len(kw_list)

    # 关键词-选择处置规则: 警告、禁言、移除群聊、仅撤回
    def select_action_rule(self, rule_name: str) -> None:
        """关键词-选择处置规则: 警告、禁言、移出群聊、仅撤回"""
        logger.info(f"⚙️ [Action-GroupBotPage] 准备选择处置规则: {rule_name}")
        action_rule_list = {
            "仅撤回": GroupBotLocator.RULE_REVOKE,
            "警告": GroupBotLocator.RULE_WARN,
            "禁言": GroupBotLocator.RULE_MUTE,
            "移出群聊": GroupBotLocator.RULE_KICK,
        }
        if rule_name in action_rule_list:
            logger.info(f"⚙️ [Action-GroupBotPage] 选择处置规则: {rule_name}")
            self.click(action_rule_list[rule_name])
        else:
            logger.warning(f"不支持的处置规则: {rule_name}")
            raise ValueError(f"不支持的处置规则: {rule_name}")

    # 关键词-获取警告语文本
    def get_warning_msg_text(self) -> Optional[str]:
        """关键词-获取警告语文本"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取警告语文本...")
        warning_msg = self.get_attribute(GroupBotLocator.TV_CONTENT, "text")
        if not warning_msg:
            logger.warning("⚙️ [Action-GroupBotPage] 未获取到警告语文本")
            return None
        logger.info(f"⚙️ [Action-GroupBotPage] 获取警告语文本: {warning_msg}")
        return warning_msg
    
    # 关键词-点击警告语设置进入警告语页面
    def click_warning_msg_setting(self) -> None:
        """关键词-点击警告语设置进入警告语页面"""
        is_exist = self.find_element(GroupBotLocator.TV_CONTENT, timeout=2)
        if not is_exist:
            self.select_action_rule(rule_name="警告")
        logger.info("⚙️ [Action-GroupBotPage] 点击进入【警告语】配置列表")
        self.click(GroupBotLocator.TV_CONTENT)

    # 关键词-等待警告语面板加载
    def wait_warning_msg_panel(self, timeout: int = 10) -> WebElement | None:
        """关键词-等待警告语面板加载,并返回面板元素"""
        element = self.find_element(GroupBotLocator.DESIGN_BOTTOM_SHEET, timeout=timeout)
        if not element:
            logger.warning(f"⚙️ [Action-GroupBotPage] 警告语面板在 {timeout}s 内未加载")
            return None
        logger.info("⚙️ [Action-GroupBotPage] 警告语面板已加载")
        return element
    
    # 关键词-检查警告语面板是否显示
    def is_warning_msg_panel_displayed(self, timeout: int = 1) -> bool:
        """关键词-检查警告语面板是否显示"""
        return self.wait_warning_msg_panel(timeout=timeout) is not None
    
    # 关键词-获取当前可见的警告语元素
    def get_visible_warning_msg_elements(self, timeout: int = 2) -> list[WebElement]:
        """关键词-获取当前可见的警告语所在行元素"""
        elements = self.find_elements(GroupBotLocator.TV_CONTENT, timeout=timeout)
        if not elements:
            logger.warning(f"⚙️ [Action-GroupBotPage] 当前屏幕未找到警告语元素 (timeout: {timeout}s)")
            return []
        return elements
    
    # 关键词-获取当前页面的警告语文案
    def get_current_page_warning_msg_texts(self, timeout: int = 2) -> list[str]:
        """关键词-获取当前页面的警告语文案"""
        elements = self.get_visible_warning_msg_elements(timeout=timeout)
        if not elements:
            logger.warning("⚙️ [Action-GroupBotPage] 当前屏幕未找到警告语元素")
            return []
        return [el.text for el in elements]
    
    # 关键词-滑动并获取所有警告语文案（去重）
    def get_all_warning_msg_texts(self, swipe_max: int = 5) -> list[str]:
        """关键词-滑动面板获取所有警告语的文本，并自动去重"""
        msg_texts = []
        seen_texts = set()
        consecutive_no_new_count = 0 
        
        elem = self.wait_warning_msg_panel()
        if not elem:
            logger.warning("⚙️ [Action-GroupBotPage] 警告语面板未加载")
            return msg_texts
            
        panel_rect = elem.rect
        
        while swipe_max > 0:
            current_elements = self.get_visible_warning_msg_elements(timeout=2)
            if not current_elements:
                logger.warning("⚙️ [Action-GroupBotPage] 当前屏幕未找到警告语元素")
                break
                
            new_found_in_this_swipe = False
            for el in current_elements:
                try:
                    raw_text = el.text
                    if raw_text:
                        clean_text = self.clean_ui_text(raw_text.strip())
                        if clean_text and clean_text not in seen_texts:
                            seen_texts.add(clean_text)
                            msg_texts.append(clean_text)
                            new_found_in_this_swipe = True
                except Exception as e:
                    logger.warning(f"⚠️ [Action-GroupBotPage] 获取文本异常(元素可能已失效): {e}")
            
            if not new_found_in_this_swipe:
                consecutive_no_new_count += 1
                if consecutive_no_new_count >= 2:
                    logger.info("⚙️ [Action-GroupBotPage] 连续滑动未发现新数据，已到达底部")
                    break
            else:
                consecutive_no_new_count = 0
                
            self.swipe_to_distance(slid_type="up", rect=panel_rect, duration=100)
            swipe_max -= 1
        
        # self.swipe_page_quickly(element=elem, slid_type="down")
        # if not self.is_warning_msg_panel_displayed(timeout=2):
        #     self.click_warning_msg_setting()
        logger.info(f"⚙️ [Action-GroupBotPage] 警告语收集完毕，共获取 {len(msg_texts)} 条去重数据: {msg_texts}")
        return msg_texts

    # 关键词-获取警告语数量
    def get_warning_msg_count(self) -> int:
        """关键词-获取警告语数量"""
        return len(self.get_all_warning_msg_texts())
    
    # 关键词-点击自定义按钮
    def click_custom_warning_msg_btn(self) -> None:
        """关键词-点击自定义按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击进入【自定义警告语】配置页面")
        self.click(GroupBotLocator.TV_CUSTOM)
    
    # 关键词-点击编辑按钮
    def click_custom_warning_msg_edit_btn(self) -> None:
        """关键词-点击编辑按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【编辑】按钮")
        self.click(GroupBotLocator.TV_EDIT)

    # 关键词-编辑框输入警告语获取
    def get_warning_msg_input_element(self) -> Optional[WebElement]:
        """关键词-获取警告语输入框元素"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取警告语输入框元素...")
        element = self.find_element(GroupBotLocator.ET_WARNING_MSG)
        if not element:
            logger.warning("⚙️ [Action-GroupBotPage] 未获取到警告语输入框元素")
            return None
        logger.info("⚙️ [Action-GroupBotPage] 已获取警告语输入框元素")
        return element
    
    # 关键词-编辑框输入警告语
    def set_custom_warning_msg_input(self, msg: str) -> None:
        """关键词-编辑框输入警告语"""
        logger.info(f"⚙️ [Action-GroupBotPage] 输入自定义警告语: {msg}")
        element = self.get_warning_msg_input_element()
        if element:
            element.clear()
            element.send_keys(msg)
    
    # 关键词-点击确认按钮
    def click_custom_warning_msg_confirm_btn(self) -> None:
        """关键词-点击确认按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击自定义警告语确认按钮")
        self.click(GroupBotLocator.BTN_CONFIRM)
    
    # 关键词-点击取消按钮
    def click_custom_warning_msg_cancel_btn(self) -> None:
        """关键词-点击取消按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击自定义警告语取消按钮")
        self.click(GroupBotLocator.BTN_CANCEL)
    
    # 关键词-设置自定义警告语
    def set_custom_warning_msg(self, msgs: Optional[list[str]]) -> None:
        """关键词-设置自定义警告语"""
        if msgs is None:
            logger.info("⚙️ [Action-GroupBotPage] 空文本警告语测试：未输入任何文本直接确认")
            self.click_custom_warning_msg_btn()
            self.click_custom_warning_msg_confirm_btn()
            return

        logger.info(f"⚙️ [Action-GroupBotPage] 准备设置自定义警告语列表(共 {len(msgs)} 条)...")
        count = 0
        for msg in msgs:
            self.click_custom_warning_msg_btn()
            self.set_custom_warning_msg_input(msg)
            self.click_custom_warning_msg_confirm_btn()
            count += 1
            if count == len(msgs):
                logger.info("⚙️ [Action-GroupBotPage] 已添加的自定义警告语数量达到预期。")
                break
            self.click_warning_msg_setting()
            self.wait_warning_msg_panel()
            time.sleep(0.5)
    
    # 关键词-批量清理多余警告语至保留条数（默认保留系统底线的 1 条）
    def clear_extra_warning_msgs(self, target_remain: int = 1, nums: int = 0, max_cleanup_rounds: int = 10) -> bool:
        """关键词-批量清理多余警告语至指定数量（默认清理到仅剩 1 条系统底线）
        
        :param target_remain: 期望保留的最小条数（系统规则通常至少保留 1 条）
        :param max_cleanup_rounds: 防止死循环的最大清理轮数
        :return: bool 是否成功清理到目标数量
        """
        logger.info(f"⚙️ [Action-GroupBotPage] 准备清理多余警告语(目标保留: {target_remain} 条)...")
        elements = self.get_visible_warning_msg_elements()
        rounds = 0
        
        while nums > target_remain and rounds < max_cleanup_rounds:
            rounds += 1
            logger.info(f"⚙️ [Action-GroupBotPage] 正在执行第 {rounds} 轮清理 (当前剩余: {nums} 条)...")
            elements[0].click()
            self.click_custom_warning_msg_edit_btn()
            edit_element = self.get_warning_msg_input_element()
            if not edit_element:
                logger.warning("⚙️ [Action-GroupBotPage] 未找到编辑框，中止多余项清理")
                return False
            edit_element.clear()
            self.click_custom_warning_msg_confirm_btn()
            nums -= 1
            self.click_warning_msg_setting()
            if not self.wait_warning_msg_panel():
                logger.warning("⚙️ [Action-GroupBotPage] 清理后警告语面板未正常加载")
                return False
            elements = self.get_visible_warning_msg_elements()
            
        success = len(elements) <= target_remain
        if success:
            logger.info(f"⚙️ [Action-GroupBotPage] 多余警告语清理完毕，当前保留: {len(elements)} 条")
        else:
            logger.warning(f"⚠️ [Action-GroupBotPage] 清理达到最大轮数上限，当前剩余: {len(elements)} 条")
        return success

    # 关键词-删除警告语
    def delete_warning_msg(self, index: int = 1, auto_confirm: bool = False) -> bool:
        """关键词-删除/触发删除指定索引的警告语
        
        :param index: 目标警告语索引（0-based）
        :param auto_confirm: 是否自动点击确认保存。
                             - False: 仅进入编辑并清空文本，停留在弹窗供用例断言拦截 Toast 或点击取消
                             - True: 清空后自动点击确认按钮完成删除闭环
        :return: bool 是否成功触发或完成操作
        """
        logger.info(f"⚙️ [Action-GroupBotPage] 准备删除警告语(目标索引: {index}, 自动确认: {auto_confirm})...")
        elements = self.get_visible_warning_msg_elements()
        
        if not (0 <= index < len(elements)):
            logger.error(f"❌ [Action-GroupBotPage] 索引 {index} 超出警告语列表范围 (总长: {len(elements)})")
            return False

        elements[index].click()
        self.click_custom_warning_msg_edit_btn()
        edit_element = self.get_warning_msg_input_element()
        if not edit_element:
            logger.error("❌ [Action-GroupBotPage] 未找到警告语编辑框元素")
            return False
        edit_element.clear()
        
        if auto_confirm:
            self.click_custom_warning_msg_confirm_btn()
            time.sleep(0.5)
            self.click_warning_msg_setting()
            self.wait_warning_msg_panel()
            logger.info(f"⚙️ [Action-GroupBotPage] 已成功删除并确认索引为 {index} 的警告语")
        else:
            logger.info(f"⚙️ [Action-GroupBotPage] 已点击并清空索引为 {index} 的警告语，保持弹窗等待用例后续操作")
        return True

    # 关键词-警告语列表向下滑动
    def scroll_warning_msg_list_down(self) -> None:
        """关键词-警告语列表向下滑动"""
        logger.info("⚙️ [Action-GroupBotPage] 准备向下滑动警告语列表...")
        elem = self.wait_warning_msg_panel()
        if not elem:
            logger.warning("⚙️ [Action-GroupBotPage] 警告语面板未加载")
            return

        self.swipe_to_distance(slid_type="down", rect=elem.rect, duration=100)
        logger.info("⚙️ [Action-GroupBotPage] 警告语列表向下滑动完成")

    # 关键词-获取设置禁言时长文本
    def get_mute_duration_summary(self) -> Optional[str]:
        """关键词-获取设置禁言时长文本"""
        logger.info("⚙️ [Action-GroupBotPage] 正在获取当前设置的禁言时长文本...")
        time.sleep(1)
        if not self.is_element_exist(GroupBotLocator.TV_SUMMARY, timeout=2):
            logger.info("⚙️ [Action-GroupBotPage] 未显示禁言时长 summary 元素，可能当前未选择禁言规则")
            return None
        txt = self.get_attribute(GroupBotLocator.TV_SUMMARY, "text")
        logger.info(f"⚙️ [Action-GroupBotPage] 当前设置禁言时长为: {txt}")
        return txt

    # 关键词-设置禁言时长
    def select_mute_duration(self, rule_time: str = "10分钟", old_summary: str = None) -> bool:
        """关键词-通过滚轮选择器滑动设置指定的禁言时长
        :param rule_time: 目标禁言时长，默认 '10分钟'
        :param old_summary: 当前已设置时长（用于计算相对滑动步长）
        :return: 是否设置成功
        """
        logger.info(f"⚙️ [Action-GroupBotPage] 正在设置禁言时长为: {rule_time} (当前页面旧值: {old_summary})")

        # 检查滚轮选择器是否已经显示
        picker_visible = self.is_element_exist(GroupBotLocator.PICKER_DURATION, timeout=2)

        if old_summary and rule_time == old_summary:
            if picker_visible:
                self.click_custom_warning_msg_confirm_btn()
                logger.info("⚙️ [Action-GroupBotPage] 禁言时长与当前设置相同，且弹窗已显示，直接点击确认关闭")
            else:
                logger.info("⚙️ [Action-GroupBotPage] 禁言时长与当前设置相同，且无弹窗显示，无需操作")
            return True

        # 如果选择器未显示，点击 TV_SUMMARY 以唤起滚轮选择弹窗
        if not picker_visible:
            logger.info("⚙️ [Action-GroupBotPage] 滚轮选择器未显示，尝试点击 TV_SUMMARY 展开")
            if self.is_element_exist(GroupBotLocator.TV_SUMMARY, timeout=2):
                self.click(GroupBotLocator.TV_SUMMARY)
                picker_visible = self.is_element_exist(GroupBotLocator.PICKER_DURATION, timeout=5)

        if not picker_visible:
            logger.error("❌ 找不到禁言时长选择器 picker_duration")
            return False

        picker_element = self.find_element(GroupBotLocator.PICKER_DURATION)
        options = self.MUTE_DURATION_OPTIONS

        if rule_time not in options:
            rule_time = options[0]
        target_index = options.index(rule_time)

        rect = picker_element.rect
        slide_distance = int(rect['height'] * 0.18)  # 一格行高约占控件高度 18%

        # 1. 确定当前滚轮位置：未知时重置归零至顶端【10分钟】
        if old_summary in options:
            current_index = options.index(old_summary)
        else:
            logger.info("🔄 首次或未记录旧时间，执行环境重置：向下滑动至顶端【10分钟】...")
            for _ in range(len(options)):
                self.swipe_by_offset(rect=rect, y_offset=slide_distance, duration=300)
                time.sleep(0.1)
            current_index = 0

        # 2. 增量相对滑动：根据当前位置直接滑动 x 格到达目标位置
        diff = target_index - current_index
        if diff > 0:
            logger.info(f"🔄 目标时间【{rule_time}】在下方，向上滑动 {diff} 格...")
            for _ in range(diff):
                self.swipe_by_offset(rect=rect, y_offset=-slide_distance, duration=400)
                time.sleep(0.15)
        elif diff < 0:
            logger.info(f"🔄 目标时间【{rule_time}】在上方，向下滑动 {abs(diff)} 格...")
            for _ in range(abs(diff)):
                self.swipe_by_offset(rect=rect, y_offset=slide_distance, duration=400)
                time.sleep(0.15)
        else:
            logger.info(f"ℹ️ 当前已在目标时间【{rule_time}】，无需额外滑动")
        self.click_custom_warning_msg_confirm_btn()
        logger.info(f"✅ 禁言时长已切换为【{rule_time}】并点击确定保存")
        return True


    # =========================================================================
    # 发言管理页面细化操作
    # =========================================================================
    # 发言管理-点击发言管理总开关
    def toggle_speech_manage_switch(self, enable: bool) -> None:
        """发言管理-点击发言管理总开关"""
        logger.info(f"⚙️ [Action-GroupBotPage] 点击发言管理总开关, 设置状态为 -> {enable}")
        self.toggle_main_switch(enable, GroupBotLocator.SB_STATUS)
    
    # 发言管理-一键全部开启或关闭子菜单开关
    def toggle_all_limit_items(self, origin_enable: bool, target_enable: bool, max_swipes: int = 5) -> None:
        """发言管理-一键全部开启或关闭子控开关（支持滚动扫描与去重）"""
        logger.info(f"⚙️ [Action-GroupBotPage] 准备一键将所有限制项状态切换为: {target_enable}")
        
        locator = GroupBotLocator.sb_option_unchecked_by_status(origin_enable)
        for swipe_idx in range(max_swipes):
            switches = self.find_elements(locator, timeout=2, raise_exception=False)
            if switches:
                for switch in switches:
                    try:
                        checked = switch.get_attribute("checked")
                        current_state = str(checked).lower() == 'true'
                        if current_state != target_enable:
                            logger.info(f"⚙️ [Action-GroupBotPage] 切换限制项状态 -> {target_enable}")
                            switch.click()
                            time.sleep(0.1)
                    except Exception as e:
                        logger.warning(f"⚠️ 处理限制项时发生异常: {e}")
            else:
                logger.info("ℹ️ 当前视图中未找到需要切换的限制项，继续滑动扫描")
            
            last_source = self.driver.page_source
            self.swipe_page(slid_type='up', duration=500)
            time.sleep(0.5)
            current_source = self.driver.page_source
            if current_source == last_source:
                logger.info("✅ 页面已滚动至最底部，停止扫描")
                break

        if swipe_idx == max_swipes:
            logger.warning(f"⚠️ 扫描达到最大次数({max_swipes})，可能还有未处理的限制项")
    
    # 对指定的限制类型或传播限制进行勾选/取消勾选
    def toggle_limit_item(self, item_name: str, enable: bool) -> None:
        """对指定的限制类型或传播限制进行勾选/取消勾选"""
        logger.info(f"⚙️ [Action-GroupBotPage] 设置限制项【{item_name}】状态为: {enable}")
        locator = GroupBotLocator.SPEECH_MANAGE_SWITCH(item_name)
        self.scroll_to_element(locator, max_swipes=2)
        is_checked = self.get_attribute(locator, "checked")
        state = str(is_checked).lower() == 'true'
        if state != enable:
            logger.info(f"⚙️ [Action-GroupBotPage] 成功切换限制项【{item_name}】至 {enable}")
            self.click(locator)
        else:
            logger.info(f"⚙️ [Action-GroupBotPage] 限制项【{item_name}】状态已为 {enable}，无需点击")

    # ============================================================================
    # 自动清理成员页面细化操作
    # ============================================================================

    # 切换自动清理功能 Switch 开关状态
    def toggle_auto_clean_switch(self, enable: bool) -> None:
        """切换自动清理功能 Switch 开关状态"""
        logger.info(f"⚙️ [Action-GroupBotPage] 切换自动清理功能 Switch 开关状态 -> {enable}")
        self.toggle_main_switch(enable, GroupBotLocator.SWITCH_BTN)

    # 进入清理规则设置页面
    def enter_clean_rules(self) -> None:
        """进入清理规则设置页面"""
        logger.info("⚙️ [Action-GroupBotPage] 点击进入【清理规则设置】")
        self.click(GroupBotLocator.CLEAN_RULES_ENTRY)

    # 配置清理条件
    def toggle_clean_condition(self, cond_name: str, enable: bool) -> None:
        """配置清理条件"""
        logger.info(f"⚙️ [Action-GroupBotPage] 设置清理条件【{cond_name}】状态为: {enable}")
        locators_map = {
            "从未发言": GroupBotLocator.COND_NEVER_SPEAK,
            "超90天未发言": GroupBotLocator.COND_NO_SPEAK_90,
            "超60天未查看群消息": GroupBotLocator.COND_NO_VIEW_60,
            "账号已注销或因违规被封禁": GroupBotLocator.COND_BANNED
        }
        if cond_name not in locators_map:
            raise ValueError(f"未知的清理条件: {cond_name}")
            
        locator = locators_map[cond_name]
        is_checked = self.get_attribute(locator, "checked")
        state = str(is_checked).lower() == 'true'
        
        if state != enable:
            self.click(locator)

    # 配置保护规则
    def toggle_protect_rule(self, prot_name: str, enable: bool) -> None:
        """配置保护规则"""
        logger.info(f"⚙️ [Action-GroupBotPage] 设置保护规则【{prot_name}】状态为: {enable}")
        locators_map = {
            "入群不足90天的成员": GroupBotLocator.PROT_NEW_MEMBER,
            "自定义成员": GroupBotLocator.PROT_CUSTOM
        }
        if prot_name not in locators_map:
            raise ValueError(f"未知的保护规则: {prot_name}")
            
        locator = locators_map[prot_name]
        is_checked = self.get_attribute(locator, "checked")
        state = str(is_checked).lower() == 'true'
        
        if state != enable:
            self.click(locator)

    # 选择清理模式: 手动确认、自动清理
    def select_clean_mode(self, mode_name: str) -> None:
        """选择清理模式: 手动确认、自动清理"""
        logger.info(f"⚙️ [Action-GroupBotPage] 选择清理模式为: {mode_name}")
        if mode_name == "手动确认":
            self.click(GroupBotLocator.MODE_MANUAL)
        elif mode_name == "自动清理":
            self.click(GroupBotLocator.MODE_AUTO)
        else:
            raise ValueError(f"不支持的清理模式: {mode_name}")

    # 点击完成按钮
    def click_finish(self) -> None:
        """点击右上角/底部的完成按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【完成】以保存清理规则")
        self.click(GroupBotLocator.FINISH_BTN)

    # 在任务记录/通知中确认清理名单
    def confirm_clean_task(self) -> None:
        """在任务记录/通知中确认清理名单"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【确认名单】")
        self.click(GroupBotLocator.CONFIRM_CLEAN_LIST)
        self.click_confirm()

    # 放弃本次清理
    def cancel_clean_task(self) -> None:
        """放弃本次清理"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【放弃本次清理】")
        self.click(GroupBotLocator.CANCEL_CLEAN_TASK)
        self.click_confirm()

    # ============================================================================
    # 入群验证页面细化操作
    # ============================================================================
    # 切换入群验证功能 Switch 开关状态
    def toggle_join_verify_switch(self, enable: bool) -> None:
        """切换入群验证功能 Switch 开关状态"""
        logger.info(f"⚙️ [Action-GroupBotPage] 切换入群验证功能 Switch 开关状态 -> {enable}")
        self.toggle_main_switch(enable, GroupBotLocator.SWITCH_BTN)

    # 一键配置入群验证规则
    def configure_join_verify(self, action_type: str = "仅移出群组", verify_time: str = "5min") -> None:
        """一键配置入群验证规则"""
        logger.info(f"⚙️ [Action-GroupBotPage] 配置入群验证: 方式=点验, 时间={verify_time}, 处理={action_type}")
        
        # 1. 选择验证方式为点验
        self.click(GroupBotLocator.VERIFY_MODE_CLICK)
        
        # 2. 设置验证时间
        self.click(GroupBotLocator.VERIFY_TIME_ROW)
        time_option = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{verify_time}")')
        self.click(time_option)
        
        # 3. 设置处理方式
        if action_type == "仅移出群组":
            self.click(GroupBotLocator.VERIFY_ACTION_KICK)
        elif action_type == "移除并拉黑":
            self.click(GroupBotLocator.VERIFY_ACTION_BLOCK)
        
        # 4. 默认验证所有新成员
        self.click(GroupBotLocator.VERIFY_SCOPE_ALL)

    # 新成员待验证态点击去验证按钮
    def go_verify(self) -> None:
        """新成员待验证态点击去验证按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【去验证】")
        self.click(GroupBotLocator.GO_VERIFY_BTN)

    # =============================================================================
    # 进群欢迎语页面操作
    # =============================================================================

    # 进入【进群欢迎语】设置页
    def enter_welcome(self) -> None:
        """进入【进群欢迎语】设置页"""
        logger.info("⏳ [Action-GroupBotPage] 进入【进群欢迎语】设置页")
        self.click(GroupBotLocator.WELCOME_ENTRY)

    # 配置并完成进群欢迎语
    def configure_welcome(self, content: str) -> None:
        """配置并完成进群欢迎语"""
        logger.info(f"⚙️ [Action-GroupBotPage] 配置进群欢迎语: {content}")
        
        # 尝试点击“添加欢迎语”或“修改欢迎语”
        try:
            add_btn = self.find_elements(GroupBotLocator.WELCOME_ADD_BTN, timeout=2)
            if add_btn:
                logger.info("⚙️ [Action-GroupBotPage] 点击【添加欢迎语】")
                self.click(add_btn[0])
            else:
                edit_btn = self.find_elements(GroupBotLocator.WELCOME_EDIT_BTN, timeout=2)
                if edit_btn:
                    logger.info("⚙️ [Action-GroupBotPage] 点击【修改欢迎语】")
                    self.click(edit_btn[0])
        except Exception as e:
            logger.warning(f"⚠️ [Action-GroupBotPage] 查找添加/修改按钮异常: {e}")

        # 清空并输入欢迎语内容
        input_field = self.find_element(GroupBotLocator.WELCOME_INPUT)
        input_field.clear()
        if content:
            input_field.send_keys(content)

        # 点击完成保存
        logger.info("⚙️ [Action-GroupBotPage] 点击【完成】保存欢迎语")
        self.click(GroupBotLocator.WELCOME_FINISH_BTN)

    # ============================================================================
    # 定时消息页面操作
    # ============================================================================

    # 进入【定时消息】页
    def enter_timed_msg(self) -> None:
        """进入【定时消息】页"""
        logger.info("⏳ [Action-GroupBotPage] 进入【定时消息】页")
        self.click(GroupBotLocator.TIMED_MSG_ENTRY)

    # 添加定时消息
    def add_timed_msg(self, content: str) -> None:
        """添加定时消息"""
        logger.info(f"⚙️ [Action-GroupBotPage] 准备添加定时消息: {content}")
        self.click(GroupBotLocator.ADD_TIMED_MSG_BTN)

        # 输入文本
        input_field = self.find_element(GroupBotLocator.TIMED_MSG_INPUT)
        input_field.clear()
        input_field.send_keys(content)

        # 设置时间
        self.click(GroupBotLocator.TIMED_MSG_TIME_ROW)
        self.click_confirm()  # 时间确认弹窗

        # 确认添加
        self.click(GroupBotLocator.TIMED_MSG_CONFIRM_BTN)
        self.click_confirm()  # 二次确认

    # 根据内容模糊匹配删除定时消息任务
    def delete_timed_msg(self, content_pattern: str) -> None:
        """根据内容模糊匹配删除定时消息任务"""
        logger.info(f"⚙️ [Action-GroupBotPage] 准备删除定时消息，内容匹配: {content_pattern}")
        # 点击指定条目的修改按钮进入编辑页
        modify_btn_loc = (AppiumBy.ANDROID_UIAUTOMATOR, 
                          f'new UiSelector().textContains("{content_pattern}").fromParent(new UiSelector().text("修改"))')
        try:
            self.click(modify_btn_loc)
            self.click(GroupBotLocator.TIMED_MSG_DELETE_BTN)
            self.click_confirm()
            logger.info("⚙️ [Action-GroupBotPage] 成功删除定时消息")
        except Exception as e:
            logger.warning(f"⚠️ [Action-GroupBotPage] 删除定时消息异常: {e}")
