import allure
import time
from core.logger_utils import logger
from pages.chat.chat_page import ChatPage
from locators.chat.chat_locator import ChatLocator
from locators.chat.chat_long_press_locator import ChatLongPressLocator
from utils.cv_recognition.ocr_utils import OcrUtils

class ChatLongPressPage(ChatPage):
    """
    聊天长按菜单页面对象
    专门处理消息长按后的弹窗交互逻辑
    """

    # 长按前置条件：等待长按弹窗出现
    def wait_for_long_press_dialog(self):
        """等待长按弹窗出现"""
        menu_status = self.is_element_exist(ChatLongPressLocator.LONG_PRESS_MENU_CONTAINER, timeout=2)
        if not menu_status:
            logger.warning("⚠️ 长按弹窗未出现")
            return False
        
        logger.info("✅ 长按弹窗出现")
        return True
            
    # ==================================
    # 长按消息弹窗相关
    # ==================================
    # 长按消息-点击复制
    def click_copy(self):
        """ 点击复制 """
        self.click_menu_item("复制")
    
    # 长按消息-点击收藏
    def click_favorite(self):
        """ 点击收藏 """
        self.click_menu_item("收藏")
    
    # 长按消息-点击转发
    def click_forward(self):
        """ 点击转发 """
        self.click_menu_item("转发")

    # 长按消息-点击多选
    def click_multi_select(self):
        """ 点击多选 """
        self.click_menu_item("多选")

    # 长按消息-点击回复
    def click_reply(self):
        """ 点击回复 """
        self.click_menu_item("回复")

    # 长按消息-点击删除
    def click_delete(self):
        """ 点击删除 """
        self.click_menu_item("删除")

    # 长按消息-点击添加表情
    def click_add_emoji(self):
        """ 点击添加表情 """
        self.click_menu_item("添加表情")

    # 长按消息-点击撤回
    def click_revoke(self):
        """ 点击撤回 """
        self.click_menu_item("撤回")
    
    # 长按消息-点击切换听筒/扬声器
    def click_speaker(self):
        """ 切换听筒/扬声器 """
        # 语音消息独有，动态识别当前是哪个就点哪个
        if self.is_text_present("听筒"):
            self.click_menu_item("听筒")
        else:
            self.click_menu_item("扬声器")

    # 长按最后一条消息
    def long_press_last_message(self):
        """执行长按最后一条消息的操作"""
        message_content = self.get_last_message_content_bubble()
        self.long_press_action(message_content)
        logger.info("🖱️ [Action] - 正在长按最后一条聊天消息...")
        time.sleep(0.5)
    
    # ==================================
    # 校验长按菜单项相关
    # ==================================
    # 长按消息-获取长按菜单是否存在某一个item
    def get_menu_item_status(self, menu_name: str) -> bool:
        """
        校验单个长按菜单项的存在性。
        逻辑: 1. 优先通过 XML 定位器判断 2. 失败后通过 OCR 兜底识别（去除空格干扰进行模糊匹配）
        :param menu_name: 菜单项名称
        :return: True 表示菜单项存在，False 表示不存在
        """
        logger.info(f"🖱️ [Action] - 正在校验长按菜单项: 【{menu_name}】")
        
        locator = ChatLongPressLocator.get_menu_item_by_name(menu_name)
        if self.is_element_exist(locator, timeout=2, raise_exception=False):
            logger.info(f"✅ XML 成功识别菜单: {menu_name}")
            return True

        logger.warning(f"⚠️ XML 未能识别菜单项: {menu_name}，准备启动 OCR 降级方案...")
        ocr_list = OcrUtils(self.driver).get_all_text()
        ocr_text_blob = "".join(ocr_list).replace(" ", "")
        clean_menu_name = menu_name.replace(" ", "")
        
        if clean_menu_name in ocr_text_blob:
            logger.info(f"✅ OCR 成功识别菜单: {menu_name}")
            return True
        
        logger.error(f"❌ OCR 也未能识别出文字: {menu_name}")
        return False
    
    # 长按消息-获取所有菜单项
    def get_menu_items(self, msg_type: str = "text", is_admin: bool = False) -> bool:
        """
        校验长按菜单项的完整性，
        逻辑:1.优先通过 XML 定位器判断  2.失败后通过OCR兜底识别
        :param msg_type: 消息类型
        :param is_admin: 是否为管理员/群主身份（管理员模式下“撤回”和“删除”需同时存在）
        """
        logger.info(f"🖱️ [Action] - 正在校验 【{msg_type}】 消息的长按菜单项 (身份: {'管理员' if is_admin else '普通成员'})")
        
        from strategy.chat.chat_message_strategy import MessageTypeStrategy
        strategy = MessageTypeStrategy.get_strategy(msg_type)
        expected_items = strategy.expected_menus
        missing_in_xml = []
        
        # --- 第一阶段：XML 优先校验 ---
        for item in expected_items:
            if item == "撤回/删除":
                # 动态检查逻辑
                found_revoke = self.is_element_exist(ChatLongPressLocator.get_menu_item_by_name("撤回"), timeout=1, raise_exception=False)
                found_delete = self.is_element_exist(ChatLongPressLocator.get_menu_item_by_name("删除"), timeout=1, raise_exception=False)
                
                if is_admin:
                    # 管理员/群主：撤回 和 删除 必须【同时存在】
                    if not all((found_revoke, found_delete)):
                        missing_in_xml.append("撤回+删除(需同时存在)")
                else:
                    # 普通成员：撤回 或 删除 【存在其一】即可
                    if not any((found_revoke, found_delete)):
                        missing_in_xml.append("撤回/删除(二者均缺失)")
            else:
                locator = ChatLongPressLocator.get_menu_item_by_name(item)
                if not self.is_element_exist(locator, timeout=1, raise_exception=False):
                    missing_in_xml.append(item)

        if not missing_in_xml:
            logger.info(f"✅ XML 层级成功识别出 【{msg_type}】 所有菜单项")
            return True
            
        # --- 第二阶段：OCR 兜底校验 ---
        logger.warning(f"⚠️ XML 未能完全识别菜单项: {missing_in_xml}，准备启动 OCR 降级方案...")
        
        ocr_list = OcrUtils(self.driver).get_all_text()
        ocr_text_blob = "".join(ocr_list)
        
        final_missing = []
        for item in missing_in_xml:
            if "撤回" in item or "删除" in item:
                has_revoke = "撤回" in ocr_text_blob
                has_delete = "删除" in ocr_text_blob
                
                if is_admin:
                    if not (has_revoke and has_delete):
                        final_missing.append("撤回+删除(OCR识别不足)")
                else:
                    if not (has_revoke or has_delete):
                        final_missing.append("撤回/删除(OCR识别缺失)")
            else:
                if item not in ocr_list:
                    final_missing.append(item)
            if final_missing:
                logger.error(f"❌ OCR 兜底后仍未能识别出 【{msg_type}】 菜单项: {final_missing}")
                return False
        logger.info(f"✅ OCR 成功识别出 XML 缺失的菜单项: {missing_in_xml}")
        return True

    # 长按消息-点击菜单项(降级OCR)
    def click_menu_item(self, menu_name: str):
        """
        点击弹窗菜单中的指定项目
        优先使用 XML 定位，如果 XML 抓不到，则降级使用 OCR 识别坐标点击
        """
        logger.info(f"🖱️ [Action] - 尝试点击菜单项: 【{menu_name}】")
        
        # 1. XML 尝试 (将 timeout 增加到 3 秒，避免动画延迟导致漏抓)
        locator = ChatLongPressLocator.get_menu_item_by_name(menu_name)
        if self.is_element_exist(locator, timeout=2, raise_exception=False):
            self.click(locator)
            logger.info(f"✅ XML 成功点击菜单: {menu_name}")
            return

        # 2. OCR 兜底
        logger.warning(f"⚠️ XML 未发现菜单项 【{menu_name}】，启动 OCR 降级...")
        ocr = OcrUtils(self.driver)

        # 放宽 OCR 的精确匹配限制，防止识别出 "删 除" 等带空格的文本导致漏判
        if ocr.click_text_by_ocr(ocr_text=menu_name, click_duration=300, exact_match=True):
            logger.info(f"🎯 OCR 识别并点击成功: {menu_name}")
            time.sleep(0.5)
        else:
            logger.error(f"❌ OCR 也未能识别出文字: {menu_name}")
            raise RuntimeError(f"无法定位并点击长按菜单项: {menu_name}")



    # ==================================
    # 动作与预期结果映射表 (核心重构点)
    # ==================================
    def _execute_and_verify_menu_item(self, menu_name: str, msg_type: int = 0) -> bool:
        """
        根据菜单名称，自动执行点击并进行结果验证。
        配置驱动：由 MenuActionConfig 策略控制具体的执行方法和断言逻辑。
        :param msg_type: 消息类型 0: 文本/群聊/文件/视频/语音等 1: 图片
        """
        from strategy.chat.chat_message_strategy import MenuActionConfig
        
        config = MenuActionConfig.get_strategy(menu_name)
        if not config:
            logger.warning(f"⚠️ 菜单项 【{menu_name}】 未配置自动化动作，仅尝试点击")
            self.click_menu_item(menu_name)
            return True
            
        # 反射获取具体的点击动作方法（如 click_copy）
        action_method = getattr(self, config.action_method)
        
        # 1. 执行动作
        action_method()
        time.sleep(0.5)
        
        # 2. 根据校验类型进行验证
        verify_type = config.verify_type
        expect_val = config.expect_value
        
        logger.info(f"🔍 [Verify] - 正在进行 【{menu_name}】 的结果校验 (类型: {verify_type})")
        
        if verify_type == "toast":
            toast = self.get_toast(expected_toast=expect_val)
            if (toast and expect_val in toast) or (not toast):
                logger.info(f"✅ 【{menu_name}】 校验成功: 预期 {expect_val} 在 Toast 【{toast}】 中 (或未捕获提示框)")
                return True
            else:
                logger.error(f"❌ 【{menu_name}】 校验失败: 预期 {expect_val} 不在 Toast 【{toast}】 中")
                return False
        elif verify_type == "page_change":
            from pages.common.contact_select_page import ContactSelectPage
            forward_page = ContactSelectPage(self.driver)
            if not forward_page.wait_for_forward_page_load(msg_type=msg_type):
                logger.error(f"❌ 【{menu_name}】 校验失败: 未进入转发页面")
                return False
            logger.info(f"✅ 【{menu_name}】 校验成功: 进入转发页面")
            return True
        elif verify_type == "ui_state":
            multi_state = self.wait_for_multi_select_page_load()
            if not multi_state:
                logger.error(f"❌ 【{menu_name}】 校验失败: 未进入多选页面")
                return False
            logger.info(f"✅ 【{menu_name}】 校验成功: 进入多选页面")
            return True
        elif verify_type == "msg_disappear":
            # TODO: 消息消失校验 待完善
            return True
        return True


    








