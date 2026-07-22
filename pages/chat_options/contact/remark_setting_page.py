from common.base_page import BasePage
from locators.chat_options.contact.contact_detail_locator import ContactDetailLocator
from core.logger_utils import logger
from appium.webdriver.common.appiumby import AppiumBy
import time

class RemarkSettingPage(BasePage):
    """设置备注页与标签页页面对象"""

    # =========================================================================
    # 备注页操作
    # =========================================================================
    
    # 好友资料页 - 等待设置备注页/好友资料页加载完成
    def wait_friend_detail_page(self, timeout: int = 10) -> bool:
        """ 好友详情页面 - 等待好友资料页加载完成 """
        if self.get_attribute(ContactDetailLocator.TV_TITLE, "text", timeout=timeout) == "好友资料":
            logger.info(" 🧐 [Action - ContactDetail] 好友详情页面 - 加载完成")
            return True
        else:
            logger.error(" ❌ [Action - ContactDetail] 好友详情页面 - 未加载完成")
            return False

    # 好友资料页- 点击备注名
    def click_remark_name(self):
        """ 好友资料页 - 点击备注名 """
        self.click(ContactDetailLocator.REMARK_NAME_ITEM)
        logger.info("⚙️ [Action - RemarkSetting] 好友资料页 - 点击备注名")

    # 好友资料页- 输入备注名
    def input_remark_name(self, remark_name: str):
        """ 好友资料页 - 输入备注名 """
        self.send_keys(ContactDetailLocator.ET_REMARK, remark_name)
        logger.info(f"⚙️ [Action - RemarkSetting] 好友资料页 - 输入备注名: {remark_name}")

    # 好友资料页 - 清空备注名
    def clear_remark_name(self):
        """ 好友资料页 - 清空备注名 """
        try:
            self.click(ContactDetailLocator.IV_REMARK_CLEAR)
        except Exception:
            self.clear(ContactDetailLocator.ET_REMARK)
        logger.info("⚙️ [Action - RemarkSetting] 好友资料页 - 清空备注名")

    # 好友资料页- 获取备注名
    def get_remark_name(self) -> str:
        """ 好友资料页 - 获取备注名 """
        txt = self.get_attribute(ContactDetailLocator.ET_REMARK, "text")
        logger.info(f"🧐 [Action - RemarkSetting] 好友资料页 - 获取备注名: {txt}")
        return txt
    
    # 好友资料页 - 点击电话
    def click_phone_item(self):
        """ 好友资料页 - 点击电话 """
        self.click(ContactDetailLocator.ITEM_PHONE)
        logger.info("⚙️ [Action - RemarkSetting] 好友资料页 - 点击电话")

    # 好友资料页 - 获取已添加的手机号码列表
    def get_phone_numbers(self) -> list:
        """ 好友资料页 - 获取已添加的手机号码列表 """
        str_phone_numbers = self.get_attribute(ContactDetailLocator.TV_PHONE_VALUE, "text")
        if str_phone_numbers:
            phone_numbers = str_phone_numbers.split("，")
            logger.info(f"🧐 [Action - RemarkSetting] 好友资料页 - 获取已添加的手机号码列表: {phone_numbers}")
            return phone_numbers
        return []

    # 好友资料页 - 点击添加电话
    def click_add_phone(self) -> bool:
        """ 好友资料页 - 点击添加电话 """
        try:
            self.click(ContactDetailLocator.IV_ADD_PHONE)
            logger.info("⚙️ [Action - RemarkSetting] 好友资料页 - 点击添加电话")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 好友资料页 - 点击添加电话失败: {e}")
            return False

    # 好友资料页 - 输入电话号码
    def input_phone(self, phone: str, index: int = 0, by_action: bool = False):
        """ 
        好友资料页 - 在指定索引的电话框中输入号码 
        :param phone: 电话号码文本
        :param index: 输入框索引
        :param by_action: 是否使用底层 W3C ActionChains 模拟真实键盘按键流输入
        """
        try:
            elems = self.find_elements(ContactDetailLocator.ET_PHONE_VALUE)
            if index < len(elems):
                elem = elems[index]
                elem.click()
                elem.clear()
                if by_action:
                    self.send_keys_by_actions(elem, phone)
                else:
                    elem.send_keys(phone)
                logger.info(f"⚙️ [Action - RemarkSetting] 好友资料页 - 输入电话[{index}]: {phone}")
                return True
            logger.error(f"❌ [Action - RemarkSetting] 好友资料页 - 电话输入框索引溢出: {index} >= {len(elems)}")
            return False
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 好友资料页 - 输入电话失败: {e}")
            return False

    # 好友资料页 - 获取电话号码列表
    def get_phones(self, raise_exception: bool = False) -> list:
        """ 好友资料页 - 获取已输入的所有纯数字电话号码（兼容 ET_PHONE_VALUE 与 TV_PHONE_VALUE） """
        phones = []
        try:
            elems = self.find_elements(ContactDetailLocator.ET_PHONE_VALUE, timeout=2, raise_exception=raise_exception)
            if not elems:
                elems = self.find_elements(ContactDetailLocator.TV_PHONE_VALUE, timeout=2, raise_exception=raise_exception)
            
            for el in elems:
                val = el.text
                # 过滤空字符串和非纯数字字符串
                if val and val.isdigit():
                    phones.append(val)
        except Exception as e:
            logger.warning(f"⚠️ [Action - RemarkSetting] 获取电话列表失败: {e}")
        logger.info(f"🧐 [Action - RemarkSetting] 当前电话列表: {phones}")
        return phones

    # 好友资料页 - 清除电话号码
    def clear_phone(self, index: int = 0):
        """ 好友资料页 - 清除指定索引的电话号码 """
        try:
            icons = self.find_elements(ContactDetailLocator.IV_PHONE_LEFT)
            if index < len(icons):
                icons[index].click()
                logger.info(f"⚙️ [Action - RemarkSetting] 点击第 {index} 个电话左侧删除按钮")
                time.sleep(0.5)
                return True
            elems = self.find_elements(ContactDetailLocator.ET_PHONE_VALUE)
            if index < len(elems):
                elems[index].clear()
                logger.info(f"⚙️ [Action - RemarkSetting] 清空第 {index} 个电话输入框")
                return True
            logger.error(f"❌ [Action - RemarkSetting] 电话清除索引溢出: {index}")
            return False
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 清除电话失败: {e}")
            return False
    
    # 好友资料页 - 删除已添加的所有电话号码
    def delete_all_phones(self) -> bool:
        """ 好友资料页 - 删除已添加的所有电话号码 """
        try:
            icons = self.find_elements(ContactDetailLocator.IV_PHONE_LEFT, raise_exception=False)
            count = len(icons)
            for i in range(count):
                self.click(ContactDetailLocator.IV_PHONE_LEFT, force_wait=True)
                self.click(ContactDetailLocator.BTN_DELETE_PHONE, force_wait=True)
                time.sleep(0.5)
                logger.info(f"⚙️ [Action - RemarkSetting] 已删除第 {i+1} 个电话")
            logger.info("⚙️ [Action - RemarkSetting] 已删除所有电话号码")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 删除所有电话号码失败: {e}")
            return False
    

    # 好友资料页 - 检查添加电话按钮是否可见
    def is_add_phone_visible(self, raise_exception: bool = True) -> bool:
        """ 好友资料页 - 检查添加电话按钮是否可见 """
        try:
            elem = self.find_element(ContactDetailLocator.IV_ADD_PHONE, timeout=2, raise_exception=raise_exception)
            return elem.is_displayed()
        except Exception:
            return False

    # 好友资料页 - 点击标签入口
    def click_tags(self):
        """ 好友资料页 - 点击标签入口 """
        self.click(ContactDetailLocator.ROW_ADD_TAG)
        logger.info("⚙️ [Action - RemarkSetting] 好友资料页 - 点击标签入口")

    # 好友资料页 - 输入备注描述
    def input_note(self, note: str):
        """ 好友资料页 - 输入备注描述 """
        try:
            self.send_keys(ContactDetailLocator.CARD_MEMO, note)
        except Exception:
            locator = (AppiumBy.XPATH, f'//*[@resource-id="{ContactDetailLocator.CARD_MEMO[1]}"]//android.widget.EditText')
            self.send_keys(locator, note)
        logger.info(f"⚙️ [Action - RemarkSetting] 好友资料页 - 输入备注描述: {note}")

    # 好友资料页 - 清空备注描述
    def clear_note(self):
        """ 好友资料页 - 清空备注描述 """
        try:
            self.click(ContactDetailLocator.IV_MEMO_CLEAR)
        except Exception:
            try:
                self.clear(ContactDetailLocator.CARD_MEMO)
            except Exception:
                locator = (AppiumBy.XPATH, f'//*[@resource-id="{ContactDetailLocator.CARD_MEMO[1]}"]//android.widget.EditText')
                self.clear(locator)
        logger.info("⚙️ [Action - RemarkSetting] 好友资料页 - 清空备注描述")

    # 好友资料页 - 获取备注描述内容
    def get_note(self) -> str:
        """ 好友资料页 - 获取备注描述内容 """
        try:
            txt = self.get_attribute(ContactDetailLocator.CARD_MEMO, "text")
        except Exception:
            locator = (AppiumBy.XPATH, f'//*[@resource-id="{ContactDetailLocator.CARD_MEMO[1]}"]//android.widget.EditText')
            txt = self.get_attribute(locator, "text")
        logger.info(f"🧐 [Action - RemarkSetting] 好友资料页 - 获取备注描述: {txt}")
        return txt

    # 好友资料页 - 点击保存
    def click_save(self):
        """ 好友资料页 - 点击保存 """
        self.click(ContactDetailLocator.FB_DONE)
        logger.info("⚙️ [Action - RemarkSetting] 好友资料页 - 点击保存")
        time.sleep(1)


    # =========================================================================
    # 标签页操作
    # =========================================================================
    
    # 标签 - 等待标签页加载完成
    def wait_for_tag_page_load(self, timeout: int = 10) -> bool:
        """ 标签 - 等待标签选择页加载完成 """
        try:
            self.find_element(ContactDetailLocator.ET_SEARCH, timeout=timeout)
            logger.info("✅ [Wait - RemarkSetting] 标签选择页加载完成")
            return True
        except Exception:
            logger.error("❌ [Wait - RemarkSetting] 标签选择页加载超时")
            return False

    # 标签 - 在标签搜索框中输入
    def search_tag(self, keyword: str):
        """ 标签 - 在标签搜索框中输入 """
        self.send_keys(ContactDetailLocator.ET_SEARCH, keyword)
        logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 搜索标签: {keyword}")

    # 标签 - 点击新建标签
    def click_add_new_tag(self):
        """ 标签 - 点击新建标签 """
        try:
            self.click(ContactDetailLocator.LL_CREATE_TAG)
        except Exception:
            self.click(ContactDetailLocator.TV_CREATE_TAG)
        logger.info("⚙️ [Action - RemarkSetting] 标签 - 点击新建标签")

    # 标签 - 创建并选中标签流
    def create_tag_flow(self, tag_name: str):
        """ 标签 - 创建并选中标签流 (利用新定位器组件) """
        self.search_tag(tag_name)
        time.sleep(1)
        self.click_add_new_tag()
        time.sleep(1)
        self.send_keys(ContactDetailLocator.ET_TAG_NAME, tag_name)
        self.click(ContactDetailLocator.FB_CREATE_DONE)
        logger.info(f"⚙️ [Action - RemarkSetting] 创建并绑定标签完成: {tag_name}")
        time.sleep(1)

    # 标签 - 根据名称点击选择或取消选择已有标签
    def select_tag_by_name(self, tag_name: str) -> bool:
        """ 标签 - 根据名称点击选择或取消选择已有标签 """
        try:
            locator = (AppiumBy.XPATH, f'//*[@text="{tag_name}"]')
            self.click(locator)
            logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 点击选择/反选标签: {tag_name}")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 标签 - 查找标签项失败: {tag_name}, {e}")
            return False


    # =========================================================================
    # 共同群聊页操作
    # =========================================================================
    # 共同群聊 - 获取共同群聊展示的数量
    def get_common_groups_count(self) -> int:
        """ 共同群聊 - 获取共同群聊展示的数量 """
        try:
            txt = self.get_attribute(ContactDetailLocator.TV_COMMON_GROUPS_VALUE, "text")
            logger.info(f"🧐 [Action - RemarkSetting] 共同群聊数量文本: {txt}")
            import re
            nums = re.findall(r'\d+', txt)
            return int(nums[0]) if nums else 0
        except Exception as e:
            logger.warning(f"⚠️ [Action - RemarkSetting] 获取共同群聊数量失败: {e}")
            return 0

    # 共同群聊 - 点击共同群聊入口
    def click_common_groups(self):
        """ 共同群聊 - 点击共同群聊入口 """
        self.click(ContactDetailLocator.ITEM_COMMON_GROUPS)
        logger.info("⚙️ [Action - RemarkSetting] 共同群聊 - 点击共同群聊入口")

    # 共同群聊 - 等待共同群聊详情页加载完成
    def wait_for_common_groups_page_load(self, timeout: int = 10) -> bool:
        """ 共同群聊 - 等待共同群聊详情页加载完成 """
        try:
            self.find_element(ContactDetailLocator.TV_SEARCH_HINT, timeout=timeout)
            logger.info("✅ [Wait - RemarkSetting] 共同群聊页加载完成")
            return True
        except Exception:
            logger.error("❌ [Wait - RemarkSetting] 共同群聊页加载超时")
            return False

    # 共同群聊 - 输入关键字过滤共同群聊
    def search_common_group(self, keyword: str):
        """ 共同群聊 - 输入关键字过滤共同群聊 """
        try:
            self.click(ContactDetailLocator.TV_SEARCH_HINT)
            time.sleep(0.5)
        except Exception:
            pass
        self.send_keys(ContactDetailLocator.ET_SEARCH, keyword)
        logger.info(f"⚙️ [Action - RemarkSetting] 搜索共同群聊: {keyword}")

    # 共同群聊 - 点击指定名称的共同群聊
    def click_common_group_by_name(self, group_name: str) -> bool:
        """ 共同群聊 - 点击指定名称的共同群聊 """
        try:
            locator = (AppiumBy.XPATH, f'//*[@resource-id="{ContactDetailLocator.TV_NAME[1]}" and @text="{group_name}"]')
            self.click(locator)
            logger.info(f"⚙️ [Action - RemarkSetting] 共同群聊 - 点击共同群聊: {group_name}")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 未找到共同群聊: {group_name}, {e}")
            return False

    # 共同群聊 - 获取当前共同群聊列表展示的个数
    def get_common_groups_list_count(self) -> int:
        """ 共同群聊 - 获取当前共同群聊列表展示的个数 """
        try:
            elems = self.find_elements(ContactDetailLocator.TV_NAME)
            logger.info(f"🧐 [Action - RemarkSetting] 列表展示的群聊个数: {len(elems)}")
            return len(elems)
        except Exception:
            return 0

