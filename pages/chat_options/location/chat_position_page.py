import random
import re
import time
from typing import Any, List, Union, Tuple, Optional
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement
from common.base_page import BasePage
from core.logger_utils import logger
from pages.chat.core.chat_page import ChatPage
from locators.chat_options.location.chat_position_locator import ChatPositionLocator
from pages.chat.core.chat_panel_page import ChatPanelPage


class ChatPositionPage(ChatPage):
    """聊天面板-位置发送与定位相关页面对象"""

    # 聊天页面位置 - 点击位置图标进入位置选择页面
    def click_location_button(self) -> None:
        """聊天页面位置 - 点击位置按钮进入位置选择页面"""
        logger.info("🚀 准备点击位置按钮进入位置选择页面...")
        self.click(ChatPositionLocator.LOCATION_SELECT_BTN)
        logger.info("🚀 点击位置按钮进入位置选择页面完成")
    
    # 聊天页面位置 - 点击左上角取消按钮
    def click_cancel_button(self) -> None:
        """聊天页面位置 - 点击左上角取消按钮"""
        logger.info("🚀 准备点击左上角取消按钮...")
        self.click(ChatPositionLocator.CANCEL_BUTTON)
        logger.info("🚀 聊天页面位置 - 点击左上角取消按钮完成")
        time.sleep(1)
    
    # 聊天页面位置 - 点击右上角发送按钮
    def click_send_button(self) -> None:
        """聊天页面位置 - 点击右上角发送按钮"""
        logger.info("🚀 准备点击右上角发送按钮...")
        self.click(ChatPositionLocator.SEND_BUTTON)
        logger.info("🚀 聊天页面位置 - 点击右上角发送按钮完成")

    # 聊天页面位置 - 点击定位当前所在位置
    def click_current_location_button(self) -> None:
        """聊天页面位置 - 点击定位当前所在位置"""
        logger.info("🚀 准备点击定位当前所在位置按钮...")
        self.click(ChatPositionLocator.LOCATION_BUTTON)
        logger.info("🚀 聊天页面位置 - 点击定位当前所在位置完成")
    
    # 聊天页面位置 - 获取地图上定位的图标
    def get_location_icon(self) -> WebElement:
        """聊天页面位置 - 获取地图上定位的图标"""
        logger.info("🔍 获取地图上定位的图标...")
        elem = self.find_element(ChatPositionLocator.LOCATION_IVCENTERPIN)
        if not elem:
            logger.error("聊天页面位置 - 未获取到地图上定位的图标")
            raise Exception("聊天页面位置 - 未获取到地图上定位的图标")
        logger.info("🚀 聊天页面位置 - 获取到地图上定位的图标")
        return elem
    
    # 聊天页面位置 - 输入搜索内容
    def input_search_content(self, content: str) -> None:
        """聊天页面位置 - 输入搜索内容"""
        logger.info(f"🚀 准备输入搜索内容: {content}...")
        self.send_keys(ChatPositionLocator.LOCATION_SEARCH_EDITTEXT, content)
        logger.info(f"🚀 输入搜索内容完成: {content}")
        time.sleep(1)
    
    # 聊天页面位置 - 点击搜索区域的取消按钮
    def click_search_cancel_button(self) -> None:
        """聊天页面位置 - 点击搜索区域的取消按钮"""
        logger.info("🚀 准备点击搜索区域的取消按钮...")
        self.click(ChatPositionLocator.LOCATION_SEARCH_CANCLE)
        logger.info("🚀 聊天页面位置 - 点击搜索区域的取消按钮完成")
    
    # 聊天页面位置 - 获取搜索结果后的容器
    def get_search_result_container(self) -> WebElement:
        """聊天页面位置 - 获取搜索结果后的容器"""
        logger.info("🔍 获取搜索结果后的容器...")
        container = self.find_element(ChatPositionLocator.LOCATION_SEARCH_AREA)
        if not container:
            logger.error("聊天页面位置 - 未获取到搜索结果容器")
            raise Exception("聊天页面位置 - 未获取到搜索结果容器")
        logger.info("🚀 聊天页面位置 - 获取搜索结果后的容器")
        return container
    
    # 聊天页面位置 - 获取位置标题
    def get_location_title(self) -> str:
        """聊天页面位置 - 获取位置标题"""
        logger.info("🔍 获取当前选中的位置标题...")
        return self.get_attribute(ChatPositionLocator.LOCATION_TITLE, attr='text')
    
    # 聊天页面位置 - 获取页面所有位置标题
    def get_all_location_titles(self) -> Tuple[List[WebElement], List[str]]:
        """聊天页面位置 - 获取页面所有位置标题"""
        logger.info("🔍 获取页面所有位置标题...")
        elements = self.find_elements(ChatPositionLocator.LOCATION_TITLE, timeout=1)
        return elements, [elem.get_attribute('text') for elem in elements]

    # 聊天页面位置 - 获取位置详细标题
    def get_location_detail_title(self) -> str:
        """聊天页面位置 - 获取位置详细标题"""
        logger.info("🔍 获取当前选中的位置详细标题...")
        return self.get_attribute(ChatPositionLocator.LOCATION_DETAIL_TITLE, attr='text')
    
    # 聊天页面位置 - 获取位置详细标题列表
    def get_all_location_detail_titles(self) -> Tuple[List[WebElement], List[str]]:
        """聊天页面位置 - 获取位置详细标题列表"""
        logger.info("🔍 获取页面所有位置详细标题列表...")
        elements = self.find_elements(ChatPositionLocator.LOCATION_DETAIL_TITLE, timeout=1)
        return elements, [elem.get_attribute('text') for elem in elements]
    
    # 聊天页面位置 - 获取被选中后的图标
    def get_selected_location_icon(self) -> int:
        """聊天页面位置 - 获取被选中后的图标"""
        logger.info("🔍 获取被选中后的图标...")
        elements = self.find_elements(ChatPositionLocator.LOCATION_SELECTED_ICON, timeout=2)
        if not elements:
            logger.error("聊天页面位置 - 未获取到被选中后的图标")
            return 0
        logger.info("🚀 聊天页面位置 - 获取到被选中后的图标")
        return len(elements)

    # 聊天页面位置 - 打开面板进入位置选择页面
    def open_panel_enter_location_page(self) -> None:
        """聊天页面位置 - 打开面板进入位置选择页面"""
        logger.info("🚀 准备从面板进入位置选择页面...")
        self.click_add_button()
        ChatPanelPage(self.driver).click_location()
        logger.info("🚀 聊天页面位置 - 打开面板进入位置选择页面完成")

    # 聊天页面位置 - 获取位置标题和详细标题
    def get_selected_location_info(self) -> tuple[Optional[str], Optional[str]]:
        """聊天页面位置 - 获取位置标题和详细标题（默认第一个位置）"""
        logger.info("🔍 获取位置标题和详细标题...")
        location_title = self.get_location_title()
        location_detail_title = self.get_location_detail_title()
        if not location_title and not location_detail_title:
            logger.error("聊天页面位置 - 未获取到位置标题或详细标题")
            return None, None
        logger.info(f"🚀 聊天页面位置 - 获取到位置标题: {location_title}, 详细标题: {location_detail_title}")
        return location_title, location_detail_title
    
    # 聊天页面位置 - 获取页面所有位置的标题和详细标题
    def get_all_location_info(self) -> tuple[Optional[list[str]], Optional[list[str]]]:
        """聊天页面位置 - 获取页面所有位置的标题和详细标题"""
        logger.info("🔍 获取页面所有位置的标题和详细标题...")
        elements_title, location_titles = self.get_all_location_titles()
        elements_detail, location_detail_titles = self.get_all_location_detail_titles()
        if not elements_title and not location_titles:
            logger.error("聊天页面位置 - 未获取到位置标题或详细标题")
            return None, None
        logger.info(f"🚀 聊天页面位置 - 获取到位置标题: {location_titles}, 详细标题: {location_detail_titles}")
        return location_titles, location_detail_titles
    
    # 聊天页面位置 - 获取搜索后的结果并点击第一个
    def get_search_result_and_click(self) -> None:
        """聊天页面位置 - 获取搜索后的结果并点击第一个"""
        logger.info("🔍 检索搜索结果并准备点击第一项...")
        elements_title, location_titles = self.get_all_location_titles()
        if not elements_title:
            logger.error("聊天页面位置 - 未获取到搜索结果")
            raise Exception("聊天页面位置 - 未获取到搜索结果")
        
        target_name = location_titles[0]
        logger.info(f"🚀 聊天页面位置 - 准备选中搜索结果第一项: {target_name}...")
        elements_title[0].click()
        logger.info(f"🚀 聊天页面位置 - 选中搜索结果第一项完成: {target_name}")
    
    # 聊天页面位置 - 验证地图内部显示的地址是否一致
    def verify_map_location_info(self, expected_title: str, expected_detail: str) -> bool:
        """
        聊天页面位置 - 验证地图内部显示的地址信息是否与预期一致（通过 OCR 识别图文）
        采用智能多层级匹配策略：
        1. 完整字符串直接包含 (Exact Substring)
        2. POI 核心主名称匹配 (剔除栋/号/座/期等末尾单元后缀)
        3. 详细地址分段关键词匹配 (匹配区/街道/路等行政特征词)
        4. 字符重合度/相似度匹配 (>= 70% 汉字字符覆盖)
        """
        logger.info(f"🧐 准备校验地图详情内容: 预期标题='{expected_title}', 详细地址='{expected_detail}'...")
        from utils.cv_recognition.ocr_utils import OcrUtils
        ocr_tool = OcrUtils(self.driver)
        
        # 获取当前地图页面的所有文字
        screen_texts = ocr_tool.get_all_text(image_name="map_detail_page_ocr.png")
        
        # 将识别到的文字合并为一个大字符串，并去除常见空白
        all_text_combined = "".join(screen_texts).replace(" ", "").replace("\n", "")
        
        clean_title = (expected_title or "").replace(" ", "")
        clean_detail = (expected_detail or "").replace(" ", "")
        
        logger.info(f"🧐 正在校验地图详情内容... 预期标题: '{clean_title}', 详细地址: '{clean_detail}'")
        
        # 1. 完整字符串直接包含
        if clean_title and clean_title in all_text_combined:
            logger.info(f"✅ 地图内容校验通过 (完整标题命中): {clean_title}")
            return True
            
        if clean_detail and clean_detail in all_text_combined:
            logger.info(f"✅ 地图内容校验通过 (完整详细地址命中): {clean_detail}")
            return True
            
        # 2. 提取 POI 核心主名称（去除末尾的 '5栋', 'A座', '1号楼', '2期', '(在建)' 等尾缀）
        # 例如: '北大资源财富森林5栋' -> '北大资源财富森林'
        core_title = re.sub(r'[\(\（].*?[\)\）]|\d+[栋幢座期号楼单元层室]|#\d+|[A-Za-z]座', '', clean_title).strip()
        if len(core_title) >= 2 and core_title in all_text_combined:
            logger.info(f"✅ 地图内容校验通过 (POI 核心主名称命中): '{core_title}' (原标题: '{clean_title}')")
            return True

        # 3. 详细地址分段关键词匹配 (如提取: '两江新区', '鸳鸯街道', '财富森林' 等子串)
        matched_segments = []
        segments = re.findall(r'[\u4e00-\u9fa5]{3,}', clean_detail)
        for seg in segments:
            if seg in all_text_combined:
                matched_segments.append(seg)
        if len(matched_segments) >= 1:
            logger.info(f"✅ 地图内容校验通过 (详细地址特征片段命中: {matched_segments})")
            return True

        # 4. 汉字字符集覆盖率判定 (当 OCR 偶发字符切分误差时，计算汉字命中率)
        title_chars = [c for c in clean_title if '\u4e00' <= c <= '\u9fa5']
        if title_chars:
            matched_char_count = sum(1 for c in title_chars if c in all_text_combined)
            char_ratio = matched_char_count / len(title_chars)
            if char_ratio >= 0.70:
                logger.info(f"✅ 地图内容校验通过 (标题汉字覆盖率达标: {char_ratio:.1%}, 匹配字符数: {matched_char_count}/{len(title_chars)})")
                return True
        logger.error(f"❌ 地图内容校验失败！预期标题: '{clean_title}', 详细地址: '{clean_detail}', 核心提取词: '{core_title}', 实际 OCR 结果: {all_text_combined}")
        return False

    # 通过 省 或 市 进行截取
    def extract_region_prefix(self, address_text: str) -> str:
        """
        智能提取行政区域前缀
        逻辑：
        1. 优先截取到 '省' (如: 广东省深圳市 -> 广东省)
        2. 如果没省，截取到 '市' (如: 北京市朝阳区 -> 北京市)
        3. 如果都没，返回原字符串 (如: 香港特别行政区)
        :param address_text: 完整的地址字符串
        :return: 截取后的区域字符串
        """
        logger.info(f"🔍 智能提取行政区域前缀: {address_text}...")
        if not address_text:
            logger.error("未获取到地址信息")
            raise ValueError("未获取到地址信息")
        # 正则解释：
        # .+?   : 匹配任意字符 (非贪婪模式，尽可能少匹配)
        # [省市] : 遇到 '省' 或 '市' 任意一个字符就停止
        pattern = r'(.+?[省市])'
        match = re.search(pattern, address_text)
        if match:
            # group(1) 返回匹配到的内容，例如 "广东省" 或 "上海市"
            return match.group(1)
        # 如果没有省或市（例如海外地址），返回原文本供后续模糊匹配
        return address_text
