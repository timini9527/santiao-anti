from typing import Union, List, Optional
from common.base_page import BasePage
from locators.friend.profile.contact_detail_locator import ContactDetailLocator
from core.logger_utils import logger, LogIcon
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
        logger.info(f"{LogIcon.WAIT} 🧐 [Action - ContactDetail] 等待好友详情页面加载 (预期标题: {titles}, 超时: {timeout}s)")
        wait_finish = self.wait_for_element_text(ContactDetailLocator.TV_TITLE, expected_text=titles, timeout=timeout)
        if wait_finish:
            logger.info(f"{LogIcon.SUCCESS} 🧐 [Action - ContactDetail] 好友详情页面 - 加载完成")
        else:
            logger.error(f"{LogIcon.FAIL} 好友详情页面 - 未加载完成")
        return wait_finish

    
    # 资料页 - 点击取消按钮
    def click_tv_cancel(self) -> None:
        """ 资料页 - 点击取消按钮 """
        logger.info(f"{LogIcon.SETUP} 资料详情页 - 点击取消按钮")
        self.click(ContactDetailLocator.TV_CANCEL)

    # 好友资料页- 点击备注名
    def click_remark_name(self) -> None:
        """ 好友资料页 - 点击备注名 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 点击备注名")
        self.click(ContactDetailLocator.REMARK_NAME_ITEM)

    # 好友资料页- 输入备注名
    def input_remark_name(self, remark_name: str) -> None:
        """ 好友资料页 - 输入备注名 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 输入备注名: {remark_name}")
        self.send_keys(ContactDetailLocator.ET_REMARK, remark_name)

    # 好友资料页 - 清空备注名
    def clear_remark_name(self) -> None:
        """ 好友资料页 - 清空备注名 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 清空备注名")
        try:
            self.click(ContactDetailLocator.IV_REMARK_CLEAR)
        except Exception:
            self.clear(ContactDetailLocator.ET_REMARK)

    # 好友资料页- 获取备注名
    def get_remark_name(self) -> str:
        """ 好友资料页 - 获取备注名 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取备注名")
        txt = self.get_attribute(ContactDetailLocator.ET_REMARK, "text")
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 好友资料页 - 获取备注名: {txt}")
        return txt or ""
        
    # 好友资料页 - 点击保存
    def click_save(self) -> None:
        """ 好友资料页 - 点击保存 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 点击保存")
        self.click(ContactDetailLocator.FB_DONE)
        time.sleep(0.5)
    
    # =========================================================================
    # 电话相关操作
    # =========================================================================
    # 好友资料页 - 点击电话
    def click_phone_item(self) -> None:
        """ 好友资料页 - 点击电话 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 点击电话")
        self.click(ContactDetailLocator.ITEM_PHONE)

    # 好友资料页 - 获取已添加的手机号码列表
    def get_phone_numbers(self) -> list[str]:
        """ 好友资料页 - 获取已添加的手机号码列表 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取已添加的手机号码列表")
        str_phone_numbers = self.get_attribute(ContactDetailLocator.TV_PHONE_VALUE, "text")
        if str_phone_numbers:
            phone_numbers = str_phone_numbers.split("，")
            logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 好友资料页 - 获取已添加的手机号码列表: {phone_numbers}")
            return phone_numbers
        return []

    # 好友资料页 - 点击添加电话
    def click_add_phone(self) -> bool:
        """ 好友资料页 - 点击添加电话 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 点击添加电话")
        try:
            self.click(ContactDetailLocator.IV_ADD_PHONE)
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 好友资料页 - 点击添加电话失败: {e}")
            return False

    # 好友资料页 - 输入电话号码
    def input_phone(self, phone: str, index: int = 0, by_action: bool = False) -> bool:
        """ 
        好友资料页 - 在指定索引的电话框中输入号码 
        :param phone: 电话号码文本
        :param index: 输入框索引
        :param by_action: 是否使用底层 W3C ActionChains 模拟真实键盘按键流输入
        """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 输入电话[{index}]: {phone}")
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
                return True
            logger.error(f"{LogIcon.FAIL} 好友资料页 - 电话输入框索引溢出: {index} >= {len(elems)}")
            return False
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 好友资料页 - 输入电话失败: {e}")
            return False

    # 好友资料页 - 获取电话号码列表
    def get_phones(self, raise_exception: bool = False) -> list[str]:
        """ 好友资料页 - 获取已输入的所有纯数字电话号码（兼容 ET_PHONE_VALUE 与 TV_PHONE_VALUE） """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取已输入的所有电话号码列表")
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
            logger.warning(f"{LogIcon.WARN} 获取电话列表失败: {e}")
        logger.info(f"{LogIcon.ACTION} 🧐 [Action - RemarkSetting] 当前电话列表: {phones}")
        return phones

    # 好友资料页 - 清除电话号码
    def clear_phone(self, index: int = 0) -> bool:
        """ 好友资料页 - 清除指定索引的电话号码 """
        logger.info(f"{LogIcon.SETUP} 准备清除第 {index} 个电话号码")
        try:
            icons = self.find_elements(ContactDetailLocator.IV_PHONE_LEFT, raise_exception=False)
            if index < len(icons):
                icons[index].click()
                logger.info(f"{LogIcon.SETUP} 点击第 {index} 个电话左侧删除图标")
                time.sleep(0.3)
                self.click(ContactDetailLocator.BTN_DELETE_PHONE, force_wait=True)
                logger.info(f"{LogIcon.SETUP} 点击电话删除确认按钮")
                return True
            logger.error(f"{LogIcon.FAIL} 电话清除索引溢出: {index}")
            return False
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 清除电话失败: {e}")
            return False
    
    # 好友资料页 - 删除已添加的所有电话号码
    def delete_all_phones(self) -> bool:
        """ 好友资料页 - 删除已添加的所有电话号码 """
        logger.info(f"{LogIcon.SETUP} 准备删除所有电话号码")
        try:
            icons = self.find_elements(ContactDetailLocator.IV_PHONE_LEFT, raise_exception=False)
            count = len(icons)
            for i in range(count):
                self.click(ContactDetailLocator.IV_PHONE_LEFT, force_wait=True)
                self.click(ContactDetailLocator.BTN_DELETE_PHONE, force_wait=True)
                time.sleep(0.5)
                logger.info(f"{LogIcon.SETUP} 已删除第 {i+1} 个电话")
            logger.info(f"{LogIcon.SETUP} 已删除所有电话号码")
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 删除所有电话号码失败: {e}")
            return False
    
    # 好友资料页 - 检查添加电话按钮是否可见
    def is_add_phone_visible(self, raise_exception: bool = True) -> bool:
        """ 好友资料页 - 检查添加电话按钮是否可见 """
        logger.info(f"{LogIcon.FIND} 检查添加电话按钮是否可见")
        try:
            elem = self.find_element(ContactDetailLocator.IV_ADD_PHONE, timeout=2, raise_exception=raise_exception)
            return elem.is_displayed()
        except Exception:
            return False

    # =========================================================================
    # 标签相关操作
    # =========================================================================
    # 好友资料页 - 点击标签容器
    def click_tag_container(self) -> None:
        """ 好友资料页 - 点击标签容器 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 点击标签容器")
        self.click(ContactDetailLocator.ITEM_TAG, timeout=2)

    # 好友资料页 - 获取标签的值
    def get_tag_values(self) -> list[str]:
        """ 好友资料页 - 获取标签的值 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取好友资料页标签值")
        tag_values = self.get_attribute(ContactDetailLocator.TV_TAG_VALUE, "text")
        if tag_values:
            tag_list = tag_values.split('，')
            logger.info(f"{LogIcon.SETUP} 好友资料页 - 获取标签的值: {tag_list}")
            return tag_list
        else:
            logger.info(f"{LogIcon.SETUP} 好友资料页 - 未设置标签")
            return []

    # 好友资料页 - 点击标签入口
    def click_tags(self) -> None:
        """ 好友资料页 - 点击标签入口 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 点击标签入口")
        self.click(ContactDetailLocator.ITEM_TAG)
    
    # 标签 - 等待标签页加载完成
    def wait_for_tag_page_load(self, timeout: int = 10) -> bool:
        """ 标签 - 等待标签选择页加载完成 """
        logger.info(f"{LogIcon.WAIT} 等待标签选择页加载 (超时: {timeout}s)")
        is_exist = self.is_element_exist(ContactDetailLocator.CHIP_GROUP, timeout=timeout)
        if is_exist:
            logger.info(f"{LogIcon.SUCCESS} 标签选择页加载完成")
        else:
            logger.error(f"{LogIcon.FAIL} 标签选择页加载超时")
        return is_exist

    # 标签 - 获取标签页面的标签值
    def get_tag_page_values(self, tag_type: int = 0, split_type: int = 0) -> list[str]:
        """ 标签 - 获取标签页面的标签值 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取标签页面的标签值 (tag_type: {tag_type}, split_type: {split_type})")
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
            logger.info(f"{LogIcon.SETUP} 标签 - 获取标签页面的标签值: {tag_list}")
            return tag_list
        logger.warning(f"{LogIcon.SETUP} 标签 - 未设置标签")
        return []

    # 标签 - 获取指定标签名称的 WebElement (或列表)
    def get_tag_elem(self, tag_type: int = 0, tag_name: str = None, timeout: int = 2, raise_exception: bool = False) -> Union[WebElement, list, None]:
        """
        标签选择页 - 获取指定标签文本的 WebElement
        tag_type = 0: 返回所有的 TextView 标签元素列表
        tag_type = 1: 返回指定 tag_name 的单个 WebElement 元素
        """
        logger.info(f"{LogIcon.FIND} 获取标签元素 (tag_type: {tag_type}, tag_name: '{tag_name}')")
        if tag_type == 0:
            elems = self.find_elements(
                ContactDetailLocator.CHIP_GROUP_TAG_TEXTVIEWS,
                timeout=timeout,
                raise_exception=raise_exception,
            )
            if elems:
                logger.info(f"{LogIcon.SUCCESS} 标签 - 获取到标签列表，共 {len(elems)} 个")
            else:
                logger.warning(f"{LogIcon.WARN} 标签 - 未找到标签列表")
            return elems

        locator = ContactDetailLocator.get_tag_element(tag_name)
        elems = self.find_element(locator, timeout=timeout, raise_exception=raise_exception)
        if elems:
            logger.info(f"{LogIcon.SUCCESS} 标签 - 获取到 [{tag_name}] 标签的 WebElement")
        else:
            logger.warning(f"{LogIcon.WARN} 标签 - 未找到 [{tag_name}] 标签的 WebElement")
        return elems
    
    # 标签 - 获取标签名称 (或列表)
    def get_tag_names(self, timeout: int = 2) -> list[str]:
        """ 标签 - 获取指定标签名称的 WebElement """
        elems = self.get_tag_elem(timeout=timeout)
        if elems:
            tag_list = [elem.text for elem in elems]
            logger.info(f"{LogIcon.SUCCESS} 标签 - 获取到标签列表: {tag_list}")
            return tag_list
        logger.warning(f"{LogIcon.WARN} 标签 - 未找到标签列表")
        return []
    
    # 标签 - 验证选中标签是否被选中
    def is_tag_selected(self, tag_name: str) -> bool:
        """ 标签选择页 - 验证选中标签是否被选中 """
        elem = self.get_tag_elem(tag_type=1, tag_name=tag_name)
        if not elem:
            logger.warning(f"{LogIcon.WARN} 标签 - 未找到 [{tag_name}] 标签的 WebElement")
            return False
        is_selected = VerifyColor.verify_tag_is_selected(elem)
        if is_selected:
            logger.info(f"{LogIcon.SUCCESS} 标签 - [{tag_name}] 标签被选中")
        else:
            logger.warning(f"{LogIcon.WARN} 标签 - [{tag_name}] 标签未被选中")
        return is_selected

    # 标签 - 点击标签 (0-连续点击X个 / 1-按名称点击 / 2-按索引点击)
    def click_tag(self, tag_type: int = 0, target: Union[int, str] = 0) -> bool:
        """
        标签选择页 - 点击标签
        :param tag_type: 0-通过传入数字连续点击X个标签(默认), 1-通过标签名称点击, 2-通过索引点击单个标签
        :param target: tag_type=0(数量X), tag_type=1(名称str), tag_type=2(索引int)
        :return: 是否执行成功
        """
        logger.info(f"{LogIcon.SETUP} 标签 - 准备点击标签, 模式: {tag_type}, 目标: {target}")
        # 1-按标签名称点击单个元素
        if tag_type == 1:
            elem = self.get_tag_elem(tag_type=1, tag_name=str(target))
            if not elem:
                return False
            logger.info(f"{LogIcon.SETUP} 标签 - 按名称点击标签: {target}")
            elem.click()
            return True

        # 0 或 2 - 获取列表元素并切片提取待点击的目标列表
        elems = self.get_tag_elem(tag_type=0)
        if not elems:
            logger.error(f"{LogIcon.FAIL} 标签 - 点击失败，目标超出范围或无有效标签: {target}")
            return False

        if tag_type == 0:
            count = min(int(target), len(elems)) if str(target).isdigit() else len(elems)
            tag_names = [e.text for e in elems[:count] if e.text]

            for name in tag_names:
                elem = self.get_tag_elem(tag_type=1, tag_name=name)
                if elem:
                    logger.info(f"{LogIcon.SETUP} 标签 - 连续点击标签: {name}")
                    elem.click()
            return True

        elif tag_type == 2:
            idx = int(target) if str(target).isdigit() else 0
            if idx < len(elems):
                elem = elems[idx]
                tag_text = elem.text
                logger.info(f"{LogIcon.SETUP} 标签 - 按索引 [{idx}] 点击标签: {tag_text}")
                elem.click()
                return True
            else:
                logger.error(f"{LogIcon.FAIL} 标签 - 索引 [{idx}] 超出范围(共 {len(elems)} 个)")
                return False

    # 标签 - 清空所有已选择的标签或某一个标签
    def clear_tag(self, list_tags: Optional[List[str]] = None, tag_type: int = 0, tag_name: str = None) -> bool:
        """
        标签选择页 - 清空标签
        :param list_tags: tag_type=0 时要取消选中的标签名称；不传则清空当前全部已选标签
        :param tag_type: 0-清空所有已选择的标签, 1-清空某一个标签
        :return: 是否执行成功
        """
        logger.info(f"{LogIcon.SETUP} 标签 - 准备清空标签, 模式: {tag_type}, 指定名称: {tag_name}")
        if list_tags is None:
            logger.info(f"{LogIcon.SUCCESS} 标签 - 列表为空，无需清空")
            return True
        else:
            if tag_type not in (0, 1):
                logger.error(f"{LogIcon.FAIL} 标签 - 不支持的清空类型: {tag_type}")
                return False

            target_tags = [tag_name] if tag_type == 1 else list_tags
            if not target_tags:
                logger.warning(f"{LogIcon.WARN} 标签 - 未提供任何待清空的标签名称")
                return False

            logger.info(f"{LogIcon.SETUP} 标签 - 准备清空以下标签: {target_tags}")
            for name in target_tags:
                elem = self.get_tag_elem(tag_type=1, tag_name=name)
                if not elem:
                    logger.info(f"{LogIcon.FIND} 标签 - 界面未直接找到标签 [{name}]，尝试搜索查找")
                    self.input_search_tag(name)
                    elem = self.get_tag_elem(tag_type=1, tag_name=name, timeout=2)
                    if elem:
                        logger.info(f"{LogIcon.SUCCESS} 标签 - 通过搜索清空标签: {name}")
                        elem.click()
                    else:
                        logger.warning(f"{LogIcon.WARN} 标签 - 搜索后依然未找到指定标签: {name}")
                    self.click_tv_cancel()
                else:
                    logger.info(f"{LogIcon.SUCCESS} 标签 - 清空标签: {name}")
                    elem.click()
            time.sleep(0.3)
            self.click_save()
            return True
                    
    # 标签 - 点击标签资料卡
    def click_card_tag(self) -> None:
        """ 标签 - 点击标签资料卡 """
        logger.info(f"{LogIcon.SETUP} 标签 - 点击标签资料卡")
        self.click(ContactDetailLocator.CARD_TAG)
                
    # 标签 - 搜索框输入标签
    def input_search_tag(self, keyword: str) -> None:
        """ 标签 - 搜索框输入标签 """
        logger.info(f"{LogIcon.SETUP} 标签 - 搜索框输入标签: {keyword}")
        self.send_keys(ContactDetailLocator.ET_SEARCH, keyword)

    # 标签 - 点击新建标签
    def click_add_new_tag(self) -> None:
        """ 标签 - 点击新建标签 """
        logger.info(f"{LogIcon.SETUP} 标签 - 点击新建标签")
        self.click(ContactDetailLocator.LL_CREATE_TAG)

    # 标签 - 输入标签名称
    def input_tag_name(self, keyword: str) -> None:
        """ 标签 - 输入标签名称 """
        logger.info(f"{LogIcon.SETUP} 标签 - 输入标签名称: {keyword}")
        self.send_keys(ContactDetailLocator.ET_TAG_NAME, keyword)

    # 标签 - 确认创建标签
    def click_create_done(self) -> None:
        """ 标签 - 确认创建标签 """
        logger.info(f"{LogIcon.SETUP} 标签 - 确认创建标签")
        self.click(ContactDetailLocator.FB_CREATE_DONE)

    
    # =========================================================================
    # 备忘相关操作
    # =========================================================================
    # 好友资料页 - 点击备忘入口
    def click_memo(self) -> None:
        """ 好友资料页 - 点击备忘入口 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 点击备忘入口")
        self.click(ContactDetailLocator.ITEM_MEMO)
    
    # 好友资料页 - 输入备忘描述
    def input_note(self, note: str) -> None:
        """ 好友资料页 - 输入备忘描述 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 输入备忘描述: {note}")
        self.send_keys(ContactDetailLocator.ET_MEMO, note)

    # 好友资料页 - 清空备忘描述
    def clear_note(self) -> None:
        """ 好友资料页 - 清空备忘描述 """
        logger.info(f"{LogIcon.SETUP} 好友资料页 - 清空备忘描述")
        self.click(ContactDetailLocator.IV_MEMO_CLEAR)

    # 好友资料页/设置备注页 - 获取备忘描述内容
    def get_note(self, raise_exception: bool = False) -> str:
        """ 设置备注页 - 获取备忘描述内容 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取备忘描述内容")
        txt = self.get_attribute(ContactDetailLocator.TV_MEMO_VALUE, "text", raise_exception=raise_exception)
        if not txt:
            txt = self.get_attribute(ContactDetailLocator.ET_MEMO, "text", raise_exception=raise_exception)
        if not txt:
            logger.warning(f"{LogIcon.WARN} 设置备注页 - 未设置备忘描述")
            return ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 设置备注页 - 获取备忘描述: {txt}")
        return txt

    # 好友资料卡 - 获取资料卡页面展示的备忘描述文本
    def get_profile_memo_value(self, raise_exception: bool = False) -> str:
        """ 好友资料卡 - 获取资料卡页面展示的备忘描述文本 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取资料卡页面展示的备忘描述文本")
        txt = self.get_attribute(ContactDetailLocator.TV_PROFILE_MEMO_VALUE, "text", raise_exception=raise_exception)
        if not txt:
            logger.warning(f"{LogIcon.WARN} 资料卡 - 未展示备忘描述")
            return ""
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 资料卡 - 获取展示的备忘描述: {txt}")
        return txt

    # =========================================================================
    # 共同群聊页操作
    # =========================================================================
    # 共同群聊 - 获取共同群聊展示的数量
    def get_common_groups_count(self) -> int:
        """ 共同群聊 - 获取共同群聊展示的数量 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取共同群聊展示的数量")
        try:
            txt = self.get_attribute(ContactDetailLocator.TV_COMMON_GROUPS_VALUE, "text")
            logger.info(f"{LogIcon.ACTION} 🧐 [Action - RemarkSetting] 共同群聊数量文本: {txt}")
            import re
            nums = re.findall(r'\d+', txt or "")
            return int(nums[0]) if nums else 0
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} 获取共同群聊数量失败: {e}")
            return 0

    # 共同群聊 - 点击共同群聊入口
    def click_common_groups(self) -> None:
        """ 共同群聊 - 点击共同群聊入口 """
        logger.info(f"{LogIcon.SETUP} 共同群聊 - 点击共同群聊入口")
        self.click(ContactDetailLocator.ITEM_COMMON_GROUPS)

    # 共同群聊 - 等待共同群聊详情页加载完成
    def wait_for_common_groups_page_load(self, timeout: int = 10) -> bool:
        """ 共同群聊 - 等待共同群聊详情页加载完成 """
        logger.info(f"{LogIcon.WAIT} 等待共同群聊详情页加载 (超时: {timeout}s)")
        res = self.wait_for_element_text(ContactDetailLocator.TV_TITLE, "我们的共同群聊", timeout=timeout)
        if res:
            logger.info(f"{LogIcon.SUCCESS} 共同群聊页加载完成")
        else:
            logger.error(f"{LogIcon.FAIL} 共同群聊页加载超时")
        return res

    # 共同群聊 - 输入关键字过滤共同群聊
    def search_common_group(self, keyword: str) -> None:
        """ 共同群聊 - 输入关键字过滤共同群聊 """
        logger.info(f"{LogIcon.SETUP} 搜索共同群聊: '{keyword}'")
        self.send_keys(ContactDetailLocator.ET_SEARCH, keyword)

    # 共同群聊 - 点击指定名称的共同群聊
    def click_common_group_by_name(self, group_name: str) -> bool:
        """ 共同群聊 - 点击指定名称的共同群聊 """
        logger.info(f"{LogIcon.SETUP} 准备点击共同群聊: '{group_name}'")
        locator = ContactDetailLocator.get_common_group_by_name(group_name)
        if self.is_element_exist(locator, timeout=2):
            self.click(locator)
            logger.info(f"{LogIcon.SETUP} 共同群聊 - 成功点击共同群聊: '{group_name}'")
            return True
        logger.error(f"{LogIcon.FAIL} 未找到共同群聊: '{group_name}'")
        return False

    # 共同群聊 - 获取共同群聊群聊列表Item
    def get_common_group_items(self) -> list[WebElement]:
        """ 共同群聊 - 获取共同群聊群聊列表Item """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取共同群聊列表Item")
        elems = self.find_elements(ContactDetailLocator.TV_NAME, timeout=3, raise_exception=False)
        if not elems:
            logger.warning(f"{LogIcon.WARN} 共同群聊列表为空")
            return []
        logger.info(f"{LogIcon.ACTION} 🧐 [Action - RemarkSetting] 列表展示的群聊个数: {len(elems)}")
        return elems
    
    # 共同群聊 - 获取当前共同群聊列表展示的个数
    def get_common_groups_list_count(self) -> int:
        """ 共同群聊 - 获取当前共同群聊列表展示的个数 """
        count = len(self.get_common_group_items())
        logger.info(f"{LogIcon.ACTION} 🧐 [Action - RemarkSetting] 列表展示的群聊个数: {count}")
        return count

    # 共同群聊 - 获取当前共同群聊列表所有的群聊名称
    def get_common_group_names(self) -> list[str]:
        """ 共同群聊 - 获取当前共同群聊列表所有的群聊名称 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取共同群聊列表所有群聊名称")
        names = [e.text for e in self.get_common_group_items() if e.text]
        if not names:
            logger.warning(f"{LogIcon.WARN} 共同群聊列表为空")
            return []
        logger.info(f"{LogIcon.FIND} 🧐 [Action - RemarkSetting] 获取到共同群聊列表名称: {names}")
        return names
