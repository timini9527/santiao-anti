import time
import allure
from appium.webdriver.webelement import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from pages.common.common_page import CommonPage
from locators.common.contact_select_locator import ContactSelectLocator
from core.logger_utils import logger

class ContactSelectPage(CommonPage):
    """通用好友/群聊选择组件页面对象"""
    
    # 等待转发页面加载
    def wait_for_forward_page_load(self, msg_type: int = 0, timeout=10):
        """等待转发页面加载完成（以创建群聊按钮出现为准）
        :param msg_type: 消息类型 0: 文本/群聊/文件/视频/语音等 1: 图片
        """
        if msg_type == 1:
            locator = ContactSelectLocator.RECYCLER_VIEW
        else:
            locator = ContactSelectLocator.CREATE_GROUP
        
        res = self.is_element_exist(locator, timeout=timeout)
        if not res:
            logger.error(f"⏳ [Action] 【好友和转发】选择页 - 页面加载超时")
            return False
        logger.info(f"✅ [Action] 【好友和转发】选择页 - 页面加载成功")
        return True
    
    # 等待好友/群组 选择页加载
    def wait_for_contact_and_group_select_page_load(self, timeout=10):
        """
        等待好友/群组 选择页加载完成（以创建群聊按钮出现为准）
        :param msg_type: 消息类型 0: 文本/群聊/文件/视频/语音等 1: 图片
        """
        res = self.is_element_exist(ContactSelectLocator.RV_FRIENDS, timeout=timeout)
        if not res:
            logger.error(f"⏳ [Action] 【好友和转发】选择页 - 页面加载超时")
            return False
        logger.info(f"✅ [Action] 【好友和转发】选择页 - 页面加载成功")
        return True

    # 获取页面标题
    def get_page_title(self) -> str:
        """获取页面标题"""
        title = self.get_attribute(ContactSelectLocator.TITLE_TEXT, "text")
        logger.info(f"🏷️ [Action] 好友选择页 - 当前标题: {title}")
        return title

    # 点击返回按钮
    def click_back(self):
        """点击返回按钮"""
        self.click(ContactSelectLocator.BACK_BUTTON)
        logger.info("🔙 [Action] 好友选择页 - 点击返回")
    
    # 等待好友选择页面加载
    def wait_for_contact_select_page_load(self, timeout=10):
        """等待好友选择页面加载完成（以列表容器出现为准）"""
        res = self.is_element_exist(ContactSelectLocator.CONTACT_LIST_RV, timeout=timeout)
        logger.info(f"⏳ [Action] 好友选择页 - 页面加载{'成功' if res else '超时'}")
        return res
    
    # 输入搜索关键字
    def input_search_keyword(self, keyword: str):
        """输入搜索关键字"""
        self.send_keys(ContactSelectLocator.SEARCH_EDIT, keyword)
        logger.info(f"🔎 [Action] 好友选择页 - 输入关键字: {keyword}")
        time.sleep(1)
    
    # 清除搜索内容
    def click_clear_search(self):
        """点击清除搜索内容"""
        self.click(ContactSelectLocator.SEARCH_CLEAR)
        logger.info("🧹 [Action] 好友选择页 - 清除搜索内容")

    # 获取当前页面可见的所有好友名称
    def get_contact_names(self) -> list:
        """获取当前页面可见的所有好友名称"""
        elements = self.find_elements(ContactSelectLocator.CONTACT_NAME, timeout=3)
        names = [elem.text for elem in elements]
        logger.info(f"📋 [Action] 好友选择页 - 获取到 {len(names)} 个好友名称")
        return names

    # 获取转发页面可见的好友列表
    def get_forward_contact_names(self) -> list:
        """获取转发页面可见的好友列表"""
        if not self.wait_for_forward_page_load(timeout=5):
            logger.warning("⚠️ [Action] 转发选择页 - 页面未加载完成，无法获取好友列表")
            return []
        
        elements = self.find_elements(ContactSelectLocator.FRIEND_NAME, timeout=2)
        names = [elem.text for elem in elements]
        logger.info(f"📋 [Action] 转发选择页 - 获取到 {len(names)} 个好友名称")
        return names

    # 获取二次弹窗的标题
    def get_second_dialog_title(self) -> str:
        """获取二次弹窗的标题"""
        title = self.get_attribute(ContactSelectLocator.SECOND_DIALOG_TITLE, "text")
        logger.info(f"🏷️ [Action] 好友选择页 - 二次弹窗标题: {title}")
        return title

    # 点击确认按钮
    def click_confirm(self):
        """点击确认"""
        self.click(ContactSelectLocator.SECOND_DIALOG_CONFIRM_BUTTON, force_wait=True)
        logger.info("✅ [Action] 好友选择页 - 点击确认")
        time.sleep(1)

    # 点击取消按钮
    def click_cancel(self):
        """点击取消"""
        self.click(ContactSelectLocator.SECOND_DIALOG_CANCEL_BUTTON, force_wait=True)
        logger.info("❌ [Action] 好友选择页 - 点击取消")
        
    # 获取好友页面未勾选的按钮
    def get_unselected_contacts(self) -> list:
        """获取好友页面未勾选的按钮"""
        elements = self.find_elements(ContactSelectLocator.CB_SELECT_NO_CHECK, timeout=2)
        logger.info(f"📋 [Action] 好友选择页 - 获取到 {len(elements)} 个未勾选的按钮")
        return elements
    
    # 获取好友页面已勾选的按钮
    def get_selected_contacts(self) -> list:
        """获取好友页面已勾选的按钮"""
        elements = self.find_elements(ContactSelectLocator.CB_SELECT_CHECKED, timeout=2)
        logger.info(f"📋 [Action] 好友选择页 - 获取到 {len(elements)} 个已勾选的按钮")
        return elements


    # =======================================================
    # 逻辑层
    # =======================================================
    
    # 分享/转发页面通过名称查找好友
    def select_contact_by_name(self, name: str, select_type: str = "share") -> WebElement | None:
        """通过名称查找好友"""
        if select_type == "share":
            elem_name = self.find_element(ContactSelectLocator.get_contact_by_name(name), timeout=2)
        elif select_type == "forward":
            elem_name = self.find_element(ContactSelectLocator.get_forward_contact_by_name(name), timeout=2)
        else:
            logger.warning(f"⚠️ [Action] 未知的选择类型: {select_type}")
            return None
        
        if not elem_name:
            logger.warning(f"❌ [Action] 当前选择好友页 - 未找到好友，尝试进行搜索寻找该好友: {name}")
            return None
        logger.info(f"✅ [Action] 当前选择好友页 - 找到好友可尝试点击选中: {name}")
        return elem_name


    # 通过名称点击选中好友（包含搜索）
    def click_contact_by_name(self, name: str, select_type: str = "share") -> bool:
        """通过名称选择好友"""
        elem_name = self.select_contact_by_name(name=name, select_type=select_type)
        if not elem_name:
            self.input_search_keyword(name)
            search_elem_name = self.select_contact_by_name(name, select_type=select_type)
            if not search_elem_name:
                logger.warning(f"❌ [Action] 好友选择页 - 未找到好友: {name}")
                return False
            search_elem_name.click()
            time.sleep(1)
            logger.info(f"✅ [Action] 好友选择页 - 搜索后找到好友并点击选中: {name}")
            return True
        
        elem_name.click()
        time.sleep(1)
        logger.info(f"✅ [Action] 好友选择页 - 找到好友并点击选中: {name}")
        return True


    # 检查搜索结果是否为空
    def is_empty_result(self) -> bool:
        """检查搜索结果是否为空"""
        count = len(self.find_elements(ContactSelectLocator.CONTACT_ITEM_ROW, timeout=3))
        status = count == 0
        logger.info(f"❓ [Action] 好友选择页 - 搜索结果是否为空: {status}")
        return status


    # 转发-选择好友页面
    def forward_select_contact_by_name(self, name: str, msg_type: int = 0) -> bool:
        """转发-选择好友
        :param msg_type: 消息类型 0: 文本/群聊/文件/视频/语音等 1: 图片
        """
        if msg_type == 1:
            elem_name = self.select_contact_by_name(name=name, select_type="share")
        else:
            elem_name = self.select_contact_by_name(name=name, select_type="forward")
        
        if not elem_name:
            max_scroll_times = 10 
            scroll_count = 0     

            while scroll_count < max_scroll_times:
                self.swipe_page(slid_type='up', duration=800, times=1)
                scroll_count += 1
                elem_name = self.select_contact_by_name(name=name, select_type="forward")
                if elem_name:
                    logger.info(f"✅ [Action] 转发选择页 - 滚动后找到好友: {name}")
                    break
            if not elem_name:
                logger.warning(f"❌ [Action] 转发选择页 - 滚动 {max_scroll_times} 次后仍未找到好友: {name}")
                return False
        
        elem_name.click()
        logger.info(f"✅ [Action] 转发选择页 - 找到好友并点击选中: {name}")
        return True


    # 随机选择 x 个好友，排除群聊
    def select_x_random_friends(self, x: int = 0, batch_type: int = 0, loop_max: int = 100) -> int:
        """
        在会话列表中随机选择 x 个好友，排除群聊。
        :param x: 需要选择的好友数量
        :param batch_type: 0: 不分组, 1: 分组(49个一组)
        :param loop_max: 最大滑动次数
        :return: 成功选择的好友数量
        """
        logger.info(f"🔍 [Action] 好友选择页 - 开始寻找会话: [{x} 个好友] | 分组：{batch_type}")
        
        last_source = ""
        selected_contacts = 0
        BATCH_SIZE = 0

        for i in range(loop_max):
            elements = self.get_unselected_contacts()
            if len(elements) == 0:
                logger.warning(f"🛑 [Action] 好友选择页 - 无法找到未勾选的按钮")
                break

            for elem in elements:
                if elem:
                    elem.click()
                    time.sleep(0.1)
                    selected_contacts += 1
                    
                    logger.info(f"✅ [Action] 好友选择页 - 成功点击目标会话，已选择 {selected_contacts} 个好友")
                    if batch_type == 1:
                        BATCH_SIZE += 1
                        if BATCH_SIZE == 49:
                            logger.info(f"✅ [Action] 好友选择页 - 成功选择 {x} 个好友")
                            return selected_contacts
                    else:
                        if selected_contacts == x:
                            logger.info(f"✅ [Action] 好友选择页 - 成功选择 {x} 个好友")
                            return selected_contacts

            is_changed, last_source = self.is_page_source_changed(last_source)
            if not is_changed:
                logger.warning(f"🛑 [Action] 好友选择页 - 已滑动到底部，仍未找到目标")
                break

            logger.info(f"⏳ [Action] 好友选择页 - 第 {i + 1} 次向下滑动寻找...")
            self.swipe_page(slid_type='up', duration=800)
            time.sleep(0.5)

        logger.warning(f"⚠️ [Action] 好友选择页 - 遍历结束，期望选择 {x} 个，实际只选择了 {selected_contacts} 个")
        return selected_contacts
    

    # 通过首个好友名称获取它的首字母
    def get_first_contact_initial(self) -> str:
        """通过首个好友名称获取它的首字母（A-Z 或 #）"""
        import pypinyin

        names = self.get_contact_names()
        if not names:
            return "#"
            
        first_char = names[0]
        
        # 1. 纯英文字母直接返回大写
        if 'A' <= first_char <= 'Z' or 'a' <= first_char <= 'z':
            return first_char.upper()
            
        # 2. 中文字符使用 pypinyin 提取首字母
        if '\u4e00' <= first_char <= '\u9fa5':
            pinyin = pypinyin.lazy_pinyin(first_char)[0]
            if pinyin:
                return pinyin[0].upper()
                
        # 3. 其他非字母、特殊符号、数字均归为 #
        return "#"



