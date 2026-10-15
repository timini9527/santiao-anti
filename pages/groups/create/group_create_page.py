import time
import re
from core.logger_utils import logger, LogIcon
from common.base_page import BasePage
from locators.groups.create.group_create_locator import GroupCreateLocator
from appium.webdriver.webelement import WebElement
from pages.groups.setting.general.group_setting_page import GroupSettingPage


class GroupCreatePage(GroupSettingPage):
    """发起群聊setting页面操作类"""

    # ==========================
    # 勾选好友操作
    # ==========================
    # 点击进入好友选择页-下一步按钮
    def click_edit_to_next(self) -> None:
        """点击进入好友选择页-下一步"""
        logger.info(f"{LogIcon.ACTION} GroupCreatePage 群详情页 - 点击【进入好友选择页-下一步】")
        self.click(GroupCreateLocator.EDIT_TO_IV)
        time.sleep(0.5)
    
    # 获取未勾选的好友
    def get_unselected_friends(self, timeout: int = 2, raise_exception: bool = True) -> list[WebElement]:
        """获取未勾选的好友"""
        elements = self.find_elements(GroupCreateLocator.UNSELECTED_CHECKBOX_SYSTEM_USER, timeout=timeout, raise_exception=raise_exception)
        if not elements:
            logger.warning(f"{LogIcon.WARN} GroupCreatePage 群详情页 - 未获取到未勾选的好友")
            return []
        logger.info(f"{LogIcon.SUCCESS} GroupCreatePage 群详情页 - 获取未勾选的好友成功，共 {len(elements)} 个")
        return elements

    # 获取已勾选的好友
    def get_selected_friends(self) -> list[WebElement]:
        """获取已勾选的好友"""
        elements = self.find_elements(GroupCreateLocator.SELECTED_CHECKBOX, timeout=2)
        if not elements:
            logger.warning(f"{LogIcon.WARN} GroupCreatePage 群详情页 - 未获取到已勾选的好友")
            return []
        logger.info(f"{LogIcon.SUCCESS} GroupCreatePage 群详情页 - 获取已勾选的好友成功，共 {len(elements)} 个")
        return elements

    # 获取 MESSAGE_TEXT 消息文本
    def get_message_text_elements(self) -> list[str]:
        """获取群聊页面消息文本"""
        elements = self.find_elements(GroupCreateLocator.MESSAGE_TEXT, condition='presence', raise_exception=False)
        if not elements:
            logger.warning(f"{LogIcon.WARN} GroupCreatePage 群详情页 - 未获取到消息文本")
            return []
        logger.info(f"{LogIcon.SUCCESS} GroupCreatePage 群详情页 - 获取消息文本成功，共 {len(elements)} 个")
        return [element.get_attribute("text") for element in elements]

    # =======================================
    # 逻辑功能
    # =======================================
    # 是否是群聊验证
    def is_chat_group(self, group_title: str) -> bool | int:
        """判断当前是否是群聊页面"""
        match = re.search(r'\((\d+)\)', group_title)
        if match:
            logger.info(f"{LogIcon.SUCCESS} 已匹配群聊名称: {match}, 群聊人数: {match.group(1)}")
            return int(match.group(1))
        logger.warning(f"{LogIcon.WARN} 未匹配群聊名称: {group_title}, 不是群聊页面")
        return False
    
    # 获取没有进入群聊的异常用户
    def get_abnormal_users(self, message_texts: list[str]) -> list[str]:
        """获取没有进入群聊的异常用户"""
        if not message_texts:
            logger.warning(f"{LogIcon.WARN} GroupCreatePage 群详情页 - 未获取到消息文本")
            return []

        # 支持过滤多种异常情况的正则列表
        patterns = [
            r'(.*?)\s*状态异常，功能被禁止，待解禁后重试',
            r'(.*?)\s*(?:好友)?开启了邀请入群确认[,，]待好友确认后入群'
        ]
        
        abnormal_users = []
        # 倒序遍历，优先匹配到
        for message in message_texts[::-1]:
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    user = match.group(1).strip()
                    if user and user not in abnormal_users:
                        abnormal_users.append(user)        
        return abnormal_users

    # 随机选择 x 个好友，带排除名称功能（用于分批建群）
    def select_x_friends_with_exclusion(self, x: int, exclude_names: list[str] | None = None, initial: str = "#", loop_max: int = 100) -> tuple[int, list[str], str]:
        """
        在会话列表中随机选择 x 个好友，排除指定名称的好友。
        :param x: 需要选择的好友数量
        :param exclude_names: 需要排除的好友名称列表
        :param initial: 初始位置
        :param loop_max: 最大滑动次数
        :return: (成功选择的好友数量, 本次选中的好友名称列表)
        """
        if exclude_names is None:
            exclude_names = []
            
        logger.info(f"{LogIcon.FIND} 好友选择页 - 开始寻找会话: [需选 {x} 个] | 需排除 {len(exclude_names)} 个")
        
        last_source = ""
        selected_contacts = 0
        clicked_names = []

        logger.info(f"{LogIcon.ACTION} 好友选择页 - 点击字母索引栏: {initial}")
        self.click(GroupCreateLocator.get_index_bar_text(initial))
        for i in range(loop_max):
            elements = self.get_unselected_friends(timeout=1, raise_exception=False)
            initial_letter = self.get_first_contact_initial([elem.get_attribute("text") for elem in elements])
            for elem in elements:
                try:
                    name = elem.get_attribute("text")
                    if name in exclude_names or name in clicked_names:
                        logger.info(f"{LogIcon.STEP} 好友选择页 - 已选择好友: {name}，跳过")
                        continue
                    logger.info(f"{LogIcon.ACTION} 好友选择页 - 准备点击好友: {name}")
                    elem.click()
                    time.sleep(0.1)
                    selected_contacts += 1
                    clicked_names.append(name)
                    
                    # logger.info(f"{LogIcon.SUCCESS} 好友选择页 - 成功点击好友: {name}，已选择 {selected_contacts} 个")
                    if selected_contacts == x:
                        logger.info(f"{LogIcon.SUCCESS} 好友选择页 - 成功完成本批次选择，共 {selected_contacts} 个")
                        return selected_contacts, clicked_names, initial_letter
                except Exception as e:
                    continue

            is_changed, last_source = self.is_page_source_changed(last_source)
            if not is_changed:
                logger.warning(f"{LogIcon.FAIL} 好友选择页 - 已滑动到底部，仍未找到足够目标")
                break

            logger.info(f"{LogIcon.WAIT} 好友选择页 - 第 {i + 1} 次向下滑动寻找...")
            self.swipe_page(slid_type='up', duration=500)
            time.sleep(0.5)

        logger.warning(f"{LogIcon.WARN} 好友选择页 - 遍历结束，期望选择 {x} 个，实际只选择了 {selected_contacts} 个")
        return selected_contacts, clicked_names, initial_letter

    # 通过首个好友名称获取它的首字母
    def get_first_contact_initial(self, names: list) -> str:
        """通过首个好友名称获取它的首字母（A-Z 或 #）"""
        import pypinyin

        if not names:
            logger.warning(f"{LogIcon.WARN} GroupCreatePage 群详情页 - 未获取到好友名称")
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

