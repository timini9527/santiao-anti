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
    
    # 备注 - 等待设置备注页加载完成
    def wait_for_remark_page_load(self, timeout: int = 10) -> bool:
        """ 备注 - 等待设置备注和标签页面加载完成 """
        try:
            self.find_element(ContactDetailLocator.FB_DONE, timeout=timeout)
            logger.info("✅ [Wait - RemarkSetting] 设置备注和标签页面加载完成")
            return True
        except Exception:
            logger.error("❌ [Wait - RemarkSetting] 设置备注和标签页面加载超时")
            return False

    # 备注 - 兼容旧版等待方法
    def wait_friend_detail_page(self) -> bool:
        """ 兼容历史代码的等待备注页加载别名 """
        return self.wait_for_remark_page_load()

    # 备注- 点击备注名
    def click_remark_name(self):
        """ 备注 - 点击备注名 """
        self.click(ContactDetailLocator.REMARK_NAME_ITEM)
        logger.info("⚙️ [Action - RemarkSetting] 备注 - 点击备注名")

    # 备注 - 输入备注名
    def input_remark_name(self, remark_name: str):
        """ 备注 - 输入备注名 """
        self.send_keys(ContactDetailLocator.ET_REMARK, remark_name)
        logger.info(f"⚙️ [Action - RemarkSetting] 输入备注名: {remark_name}")

    # 备注 - 清空备注名
    def clear_remark_name(self):
        """ 备注 - 清空备注名 """
        try:
            self.click(ContactDetailLocator.IV_REMARK_CLEAR)
        except Exception:
            self.clear(ContactDetailLocator.ET_REMARK)
        logger.info("⚙️ [Action - RemarkSetting] 清空备注名")

    # 备注 - 获取备注名
    def get_remark_name(self) -> str:
        """ 备注 - 获取备注名 """
        txt = self.get_attribute(ContactDetailLocator.ET_REMARK, "text")
        logger.info(f"🧐 [Action - RemarkSetting] 获取备注名: {txt}")
        return txt
    
    # 备注 - 点击电话
    def click_phone_item(self):
        """ 备注 - 点击电话 """
        self.click(ContactDetailLocator.ITEM_PHONE)
        logger.info("⚙️ [Action - RemarkSetting] 备注 - 点击电话")

    # 备注 - 点击添加电话
    def click_add_phone(self) -> bool:
        """ 备注 - 点击添加电话 """
        try:
            self.click(ContactDetailLocator.IV_ADD_PHONE)
            logger.info("⚙️ [Action - RemarkSetting] 备注 - 点击添加电话")
            return True
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 备注 - 点击添加电话失败: {e}")
            return False

    # 备注 - 输入电话号码
    def input_phone(self, phone: str, index: int = 0):
        """ 备注 - 在指定索引的电话框中输入号码 (多电话号码场景) """
        try:
            elems = self.find_elements(ContactDetailLocator.TV_PHONE_VALUE)
            if index < len(elems):
                elems[index].click()
                elems[index].clear()
                elems[index].send_keys(phone)
                logger.info(f"⚙️ [Action - RemarkSetting] 备注 - 输入电话[{index}]: {phone}")
                return True
            logger.error(f"❌ [Action - RemarkSetting] 备注 - 电话输入框索引溢出: {index} >= {len(elems)}")
            return False
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 备注 - 输入电话失败: {e}")
            return False

    # 备注 - 获取电话号码列表
    def get_phones(self) -> list:
        """ 备注 - 获取已输入的所有电话号码 """
        phones = []
        try:
            elems = self.find_elements(ContactDetailLocator.TV_PHONE_VALUE)
            for el in elems:
                phones.append(el.text)
        except Exception as e:
            logger.warning(f"⚠️ [Action - RemarkSetting] 获取电话列表失败: {e}")
        logger.info(f"🧐 [Action - RemarkSetting] 当前电话列表: {phones}")
        return phones

    # 备注 - 清除电话号码
    def clear_phone(self, index: int = 0):
        """ 备注 - 清除指定索引的电话号码 """
        try:
            icons = self.find_elements(ContactDetailLocator.IV_PHONE_LEFT)
            if index < len(icons):
                icons[index].click()
                logger.info(f"⚙️ [Action - RemarkSetting] 点击第 {index} 个电话左侧删除按钮")
                time.sleep(0.5)
                return True
            elems = self.find_elements(ContactDetailLocator.TV_PHONE_VALUE)
            if index < len(elems):
                elems[index].clear()
                logger.info(f"⚙️ [Action - RemarkSetting] 清空第 {index} 个电话输入框")
                return True
            logger.error(f"❌ [Action - RemarkSetting] 电话清除索引溢出: {index}")
            return False
        except Exception as e:
            logger.error(f"❌ [Action - RemarkSetting] 清除电话失败: {e}")
            return False

    # 备注 - 检查添加电话按钮是否可见
    def is_add_phone_visible(self) -> bool:
        """ 备注 - 检查添加电话按钮是否可见 """
        try:
            elem = self.find_element(ContactDetailLocator.IV_ADD_PHONE, timeout=3)
            return elem.is_displayed()
        except Exception:
            return False

    # 备注 - 点击标签入口
    def click_tags(self):
        """ 备注 - 点击标签入口 """
        self.click(ContactDetailLocator.ROW_ADD_TAG)
        logger.info("⚙️ [Action - RemarkSetting] 备注 - 点击标签入口")

    # 备注 - 输入备注描述
    def input_note(self, note: str):
        """ 备注 - 输入备注描述 """
        try:
            self.send_keys(ContactDetailLocator.CARD_MEMO, note)
        except Exception:
            locator = (AppiumBy.XPATH, f'//*[@resource-id="{ContactDetailLocator.CARD_MEMO[1]}"]//android.widget.EditText')
            self.send_keys(locator, note)
        logger.info(f"⚙️ [Action - RemarkSetting] 备注 - 输入备注描述: {note}")

    # 备注 - 清空备注描述
    def clear_note(self):
        """ 备注 - 清空备注描述 """
        try:
            self.click(ContactDetailLocator.IV_MEMO_CLEAR)
        except Exception:
            try:
                self.clear(ContactDetailLocator.CARD_MEMO)
            except Exception:
                locator = (AppiumBy.XPATH, f'//*[@resource-id="{ContactDetailLocator.CARD_MEMO[1]}"]//android.widget.EditText')
                self.clear(locator)
        logger.info("⚙️ [Action - RemarkSetting] 备注 - 清空备注描述")

    # 备注 - 获取备注描述内容
    def get_note(self) -> str:
        """ 备注 - 获取备注描述内容 """
        try:
            txt = self.get_attribute(ContactDetailLocator.CARD_MEMO, "text")
        except Exception:
            locator = (AppiumBy.XPATH, f'//*[@resource-id="{ContactDetailLocator.CARD_MEMO[1]}"]//android.widget.EditText')
            txt = self.get_attribute(locator, "text")
        logger.info(f"🧐 [Action - RemarkSetting] 备注 - 获取备注描述: {txt}")
        return txt

    # 备注 - 点击保存
    def click_save(self):
        """ 备注 - 点击保存 """
        self.click(ContactDetailLocator.FB_DONE)
        logger.info("⚙️ [Action - RemarkSetting] 备注 - 点击保存")


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

