from typing import Union, List, Optional
from common.base_page import BasePage
from locators.chat_options.contact.contact_detail_locator import ContactDetailLocator
from core.logger_utils import logger
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webelement import WebElement
from business_helpers.verify_color import VerifyColor
import time

class RemarkSettingPage(BasePage):
    """设置备注页与标签页页面对象"""

    # =========================================================================
    # 备注页操作
    # =========================================================================
    
    # 好友资料页 - 等待设置备注页/好友资料页加载完成
    def wait_friend_detail_page(self, timeout: int = 10, expected_title: str = "") -> bool:
        """ 好友详情页面 - 在一定时间内轮询获取标题，直到获取成功 """
        titles = [expected_title] if expected_title else ["好友资料"]
        wait_finish = self.wait_for_element_text(ContactDetailLocator.TV_TITLE, expected_text=titles, timeout=timeout)
        if wait_finish:
            logger.info(f" 🧐 [Action - ContactDetail] 好友详情页面 - 加载完成")
        else:
            logger.error(f" ❌ [Action - ContactDetail] 好友详情页面 - 未加载完成")
        return wait_finish

    
    # 资料页 - 点击取消按钮
    def click_tv_cancel(self):
        """ 资料页 - 点击取消按钮 """
        self.click(ContactDetailLocator.TV_CANCEL)
        logger.info("⚙️ [Action - ContactDetail] 资料详情页 - 点击取消按钮")

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
    def clear_phone(self, index: int = 0) -> bool:
        """ 好友资料页 - 清除指定索引的电话号码 """
        try:
            icons = self.find_elements(ContactDetailLocator.IV_PHONE_LEFT, raise_exception=False)
            if index < len(icons):
                icons[index].click()
                logger.info(f"⚙️ [Action - RemarkSetting] 点击第 {index} 个电话左侧删除图标")
                time.sleep(0.3)
                self.click(ContactDetailLocator.BTN_DELETE_PHONE, force_wait=True)
                logger.info(f"⚙️ [Action - RemarkSetting] 点击电话删除确认按钮")
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

    # 好友资料页 - 点击标签容器
    def click_tag_container(self):
        """ 好友资料页 - 点击标签容器 """
        self.click(ContactDetailLocator.ITEM_TAG, timeout=2)
        logger.info("⚙️ [Action - RemarkSetting] 好友资料页 - 点击标签容器")

    # 好友资料页 - 获取标签的值
    def get_tag_values(self) -> list[str]:
        """ 好友资料页 - 获取标签的值 """
        tag_values = self.get_attribute(ContactDetailLocator.TV_TAG_VALUE, "text")
        if tag_values:
            tag_list = tag_values.split('，')
            logger.info(f"⚙️ [Action - RemarkSetting] 好友资料页 - 获取标签的值: {tag_list}")
            return tag_list
        else:
            logger.info(f"⚙️ [Action - RemarkSetting] 好友资料页 - 未设置标签")
            return []

    # 好友资料页 - 点击标签入口
    def click_tags(self):
        """ 好友资料页 - 点击标签入口 """
        self.click(ContactDetailLocator.ITEM_TAG)
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
        time.sleep(0.5)


    # =========================================================================
    # 标签页操作
    # =========================================================================
    
    # 标签 - 等待标签页加载完成
    def wait_for_tag_page_load(self, timeout: int = 10) -> bool:
        """ 标签 - 等待标签选择页加载完成 """
        is_exist = self.is_element_exist(ContactDetailLocator.CHIP_GROUP, timeout=timeout)
        if is_exist:
            logger.info("✅ [Wait - RemarkSetting] 标签选择页加载完成")
        else:
            logger.error("❌ [Wait - RemarkSetting] 标签选择页加载超时")
        return is_exist

    # 标签 - 获取标签页面的标签值
    def get_tag_page_values(self, tag_type: int = 0, split_type: int = 0) -> str:
        """ 标签 - 获取标签页面的标签值 """
        if tag_type == 0:
            locator = ContactDetailLocator.TV_TAG_VALUE
        elif tag_type == 1:
            locator = ContactDetailLocator.TV_PROFILE_TAG_VALUE
        elif tag_type == 2:
            locator = ContactDetailLocator.TV_ADD_TAG
        else:
            raise ValueError(f"❌ [Action - RemarkSetting] 标签类型不合法: {tag_type}")
        tags = self.get_attribute(locator, "text")
        if tags:
            split_str = '，' if split_type == 0 else '、'
            tag_list = tags.split(split_str)
            logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 获取标签页面的标签值: {tag_list}")
            return tag_list
        logger.warning("⚙️ [Action - RemarkSetting] 标签 - 未设置标签")
        return []

    # 标签 - 获取指定标签名称的 WebElement (或列表)
    def get_tag_elem(self, tag_type: int = 0, tag_name: str = None, timeout: int = 2, raise_exception: bool = False) -> Union[WebElement, list, None]:
        """
        标签选择页 - 获取指定标签文本的 WebElement
        tag_type = 0: 返回所有的 TextView 标签元素列表
        tag_type = 1: 返回指定 tag_name 的单个 WebElement 元素
        """
        if tag_type == 0:
            elems = self.find_elements(
                ContactDetailLocator.CHIP_GROUP_TAG_TEXTVIEWS,
                timeout=timeout,
                raise_exception=raise_exception,
            )
            if elems:
                logger.info(f"✅ [Action - RemarkSetting] 标签 - 获取到标签列表，共 {len(elems)} 个")
            else:
                logger.warning(f"⚠️ [Action - RemarkSetting] 标签 - 未找到标签列表")
            return elems

        locator = ContactDetailLocator.get_tag_element(tag_name)
        elems = self.find_element(locator, timeout=timeout, raise_exception=raise_exception)
        if elems:
            logger.info(f"✅ [Action - RemarkSetting] 标签 - 获取到 [{tag_name}] 标签的 WebElement")
        else:
            logger.warning(f"⚠️ [Action - RemarkSetting] 标签 - 未找到 [{tag_name}] 标签的 WebElement")
        return elems
    
    # 标签 - 获取标签名称 (或列表)
    def get_tag_names(self, timeout: int = 2) -> list[str]:
        """ 标签 - 获取指定标签名称的 WebElement """
        elems = self.get_tag_elem(timeout=timeout)
        if elems:
            tag_list = [elem.text for elem in elems]
            logger.info(f"✅ [Action - RemarkSetting] 标签 - 获取到标签列表: {tag_list}")
            return tag_list
        logger.warning("⚠️ [Action - RemarkSetting] 标签 - 未找到标签列表")
        return []
    
    # 标签 - 验证选中标签是否被选中
    def is_tag_selected(self, tag_name: str) -> bool:
        """ 标签选择页 - 验证选中标签是否被选中 """
        elem = self.get_tag_elem(tag_type=1, tag_name=tag_name)
        if not elem:
            logger.warning(f"⚠️ [Action - RemarkSetting] 标签 - 未找到 [{tag_name}] 标签的 WebElement")
            return False
        is_gray = VerifyColor.verify_btn_is_gray(elem)
        if is_gray:
            logger.info(f"✅ [Action - RemarkSetting] 标签 - [{tag_name}] 标签被选中")
        else:
            logger.warning(f"⚠️ [Action - RemarkSetting] 标签 - [{tag_name}] 标签未被选中")
        return is_gray

    # 标签 - 点击标签 (0-连续点击X个 / 1-按名称点击 / 2-按索引点击)
    def click_tag(self, tag_type: int = 0, target: Union[int, str] = 0) -> bool:
        """
        标签选择页 - 点击标签
        :param tag_type: 0-通过传入数字连续点击X个标签(默认), 1-通过标签名称点击, 2-通过索引点击单个标签
        :param target: tag_type=0(数量X), tag_type=1(名称str), tag_type=2(索引int)
        :return: 是否执行成功
        """
        # 1-按标签名称点击单个元素
        if tag_type == 1:
            elem = self.get_tag_elem(tag_type=1, tag_name=str(target))
            if not elem:
                return False
            elem.click()
            logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 按名称点击标签: {target}")
            return True

        # 0 或 2 - 获取列表元素并切片提取待点击的目标列表
        elems = self.get_tag_elem(tag_type=0)
        if not elems:
            logger.error(f"❌ [Action - RemarkSetting] 标签 - 点击失败，目标超出范围或无有效标签: {target}")
            return False

        if tag_type == 0:
            count = min(int(target), len(elems)) if str(target).isdigit() else len(elems)
            tag_names = [e.text for e in elems[:count] if e.text]

            for name in tag_names:
                elem = self.get_tag_elem(tag_type=1, tag_name=name)
                if elem:
                    elem.click()
                    logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 连续点击标签: {name}")
            return True

        elif tag_type == 2:
            idx = int(target) if str(target).isdigit() else 0
            if idx < len(elems):
                elem = elems[idx]
                tag_text = elem.text
                elem.click()
                logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 按索引 [{idx}] 点击标签: {tag_text}")
                return True
            else:
                logger.error(f"❌ [Action - RemarkSetting] 标签 - 索引 [{idx}] 超出范围(共 {len(elems)} 个)")
                return False

    # 标签 - 清空所有已选择的标签或某一个标签
    def clear_tag(self, list_tags: Optional[List[str]] = None, tag_type: int = 0, tag_name: str = None) -> bool:
        """
        标签选择页 - 清空标签
        :param list_tags: tag_type=0 时要取消选中的标签名称；不传则清空当前全部已选标签
        :param tag_type: 0-清空所有已选择的标签, 1-清空某一个标签
        :return: 是否执行成功
        """
        if list_tags is None:
            logger.info("✅ [Action - RemarkSetting] 标签 - 列表为空，无需清空")
            return True
        else:
            if tag_type not in (0, 1):
                logger.error(f"❌ [Action - RemarkSetting] 标签 - 不支持的清空类型: {tag_type}")
                return False

            target_tags = [tag_name] if tag_type == 1 else list_tags
            if not target_tags:
                logger.warning("⚠️ [Action - RemarkSetting] 标签 - 未提供任何待清空的标签名称")
                return False

            logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 准备清空以下标签: {target_tags}")
            for name in target_tags:
                elem = self.get_tag_elem(tag_type=1, tag_name=name)
                if elem:
                    elem.click()
                    logger.info(f"✅ [Action - RemarkSetting] 标签 - 清空标签: {name}")
                else:
                    logger.warning(f"⚠️ [Action - RemarkSetting] 标签 - 未找到指定标签: {name}")
            time.sleep(0.5)
            self.click_save()
            return True
                    
    # 标签 - 点击标签资料卡
    def click_card_tag(self):
        """ 标签 - 点击标签资料卡 """
        self.click(ContactDetailLocator.CARD_TAG)
        logger.info("⚙️ [Action - RemarkSetting] 标签 - 点击标签资料卡")
                
    # 标签 - 搜索框输入标签
    def input_search_tag(self, keyword: str):
        """ 标签 - 搜索框输入标签 """
        self.send_keys(ContactDetailLocator.ET_SEARCH, keyword)
        logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 搜索框输入标签: {keyword}")

    # 标签 - 点击新建标签
    def click_add_new_tag(self):
        """ 标签 - 点击新建标签 """
        self.click(ContactDetailLocator.LL_CREATE_TAG)
        logger.info("⚙️ [Action - RemarkSetting] 标签 - 点击新建标签")

    # 标签 - 输入标签名称
    def input_tag_name(self, keyword: str):
        """ 标签 - 输入标签名称 """
        self.send_keys(ContactDetailLocator.ET_TAG_NAME, keyword)
        logger.info(f"⚙️ [Action - RemarkSetting] 标签 - 输入标签名称: {keyword}")

    # 标签 - 确认创建标签
    def click_create_done(self):
        """ 标签 - 确认创建标签 """
        self.click(ContactDetailLocator.FB_CREATE_DONE)
        logger.info("⚙️ [Action - RemarkSetting] 标签 - 确认创建标签")

    # 标签



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
