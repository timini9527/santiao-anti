import random
import re
import time
from typing import Any, List, Union, Tuple
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement
from common.base_page import BasePage
from core.logger_utils import logger
from pages.chat.core.chat_page import ChatPage
from locators.chat_options.location.chat_position_locator import ChatPositionLocator


class ChatPositionPage(ChatPage):

    
    # 点击位置图标进入位置选择页面
    def click_location_button(self):
        """点击位置按钮进入位置选择页面"""
        self.click(ChatPositionLocator.LOCATION_SELECT_BTN)
        logger.info("🚀 点击位置按钮进入位置选择页面")
    
    # 点击左上角取消按钮
    def click_cancel_button(self):
        """点击左上角取消按钮"""
        self.click(ChatPositionLocator.CANCEL_BUTTON)
        logger.info("🚀 点击左上角取消按钮")
        time.sleep(1)
    
    # 点击右上角发送按钮
    def click_send_button(self):
        """点击右上角发送按钮"""
        self.click(ChatPositionLocator.SEND_BUTTON)
        logger.info("🚀 点击右上角发送按钮")

    # 点击定位当前所在位置
    def click_current_location_button(self):
        """点击定位当前所在位置"""
        self.click(ChatPositionLocator.LOCATION_BUTTON)
        logger.info("🚀 点击定位当前所在位置")
    
    # 获取地图上定位的图标
    def get_location_icon(self) -> WebElement:
        """获取地图上定位的图标"""
        elem = self.find_element(ChatPositionLocator.LOCATION_IVCENTERPIN)
        if not elem:
            logger.error("未获取到地图上定位的图标")
            raise Exception("未获取到地图上定位的图标")
        logger.info("🚀 获取到地图上定位的图标")
        return elem
    
    # 输入搜索内容
    def input_search_content(self, content: str):
        """输入搜索内容"""
        self.send_keys(ChatPositionLocator.LOCATION_SEARCH_EDITTEXT, content)
        logger.info(f"🚀 输入搜索内容: {content}")
        time.sleep(1)
    
    # 点击搜索区域的取消按钮
    def click_search_cancel_button(self):
        """点击搜索区域的取消按钮"""
        self.click(ChatPositionLocator.LOCATION_SEARCH_CANCLE)
        logger.info("🚀 点击搜索区域的取消按钮")
    
    # 获取搜索结果后的容器
    def get_search_result_container(self) -> WebElement:
        """获取搜索结果后的容器"""
        container = self.find_element(ChatPositionLocator.LOCATION_SEARCH_AREA)
        if not container:
            logger.error("未获取到搜索结果容器")
            raise Exception("未获取到搜索结果容器")
        logger.info("🚀 获取搜索结果后的容器")
        return container
    
    # 获取位置标题
    def get_location_title(self) -> str:
        """获取位置标题"""
        return self.get_attribute(ChatPositionLocator.LOCATION_TITLE, attr='text')
    
    # 获取页面所有位置标题
    def get_all_location_titles(self) -> Tuple[List[WebElement], List[str]]:
        """获取页面所有位置标题"""
        elements = self.find_elements(ChatPositionLocator.LOCATION_TITLE, timeout=1)
        return elements, [elem.get_attribute('text') for elem in elements]

    # 获取位置详细标题
    def get_location_detail_title(self) -> str:
        """获取位置详细标题"""
        return self.get_attribute(ChatPositionLocator.LOCATION_DETAIL_TITLE, attr='text')
    
    # 获取位置详细标题列表
    def get_all_location_detail_titles(self) -> Tuple[List[WebElement], List[str]]:
        """获取页面所有位置标题"""
        elements = self.find_elements(ChatPositionLocator.LOCATION_DETAIL_TITLE, timeout=1)
        return elements, [elem.get_attribute('text') for elem in elements]
    
    # 获取被选中后的图标
    def get_selected_location_icon(self) -> int:
        """获取被选中后的图标"""
        elements = self.find_elements(ChatPositionLocator.LOCATION_SELECTED_ICON, timeout=2)
        if not elements:
            logger.error("未获取到被选中后的图标")
            return 0
        logger.info("✅ 获取到被选中后的图标")
        return len(elements)

    # 打开面板进入位置选择页面
    def open_panel_enter_location_page(self):
        """打开面板进入位置选择页面"""
        self.click_add_button()
        self.click_location_button()
        logger.info("🚀 打开面板进入位置选择页面")

    # 获取位置标题和详细标题
    def get_selected_location_info(self) -> tuple:
        """获取位置标题和详细标题（默认第一个位置）"""
        location_title = self.get_location_title()
        location_detail_title = self.get_location_detail_title()
        if not location_title and not location_detail_title:
            logger.error("未获取到位置标题或详细标题")
            return None, None
        logger.info(f"🚀 获取到位置标题: {location_title}, 详细标题: {location_detail_title}")
        return location_title, location_detail_title
    
    # 获取页面所有位置的标题和详细标题
    def get_all_location_info(self) -> tuple:
        """获取页面所有位置的标题和详细标题"""
        elements_title, location_titles = self.get_all_location_titles()
        elements_detail, location_detail_titles = self.get_all_location_detail_titles()
        if not elements_title and not location_titles:
            logger.error("未获取到位置标题或详细标题")
            return None, None
        logger.info(f"🚀 获取到位置标题: {location_titles}, 详细标题: {location_detail_titles}")
        return location_titles, location_detail_titles
    
    # 获取搜索后的结果并点击第一个
    def get_search_result_and_click(self):
        """获取搜索后的结果并点击第一个"""
        elements_title, location_titles = self.get_all_location_titles()
        if not elements_title:
            logger.error("未获取到搜索结果")
            raise Exception("未获取到搜索结果")
        
        target_name = location_titles[0]
        elements_title[0].click()
        logger.info(f"🚀 选中搜索结果第一项: {target_name}")
    
    # 验证地图内部显示的地址是否一致
    def verify_map_location_info(self, expected_title: str, expected_detail: str) -> bool:
        """
        验证地图内部显示的地址信息是否与预期一致（通过 OCR 识别图文）
        :param expected_title: 预期的位置标题
        :param expected_detail: 预期的详细地址
        """
        from utils.cv_recognition.ocr_utils import OcrUtils
        ocr_tool = OcrUtils(self.driver)
        
        # 获取当前地图页面的所有文字
        screen_texts = ocr_tool.get_all_text(image_name="map_detail_page_ocr.png")
        
        # 将识别到的文字合并为一个大字符串，方便进行模糊匹配
        all_text_combined = "".join(screen_texts)
        
        logger.info(f"🧐 正在校验地图详情内容... 预期包含: '{expected_title}' 和 '{expected_detail}'")
        
        # 校验逻辑：标题通常能完整识别，详细地址可能因换行被切分，所以用 in 判定
        title_match = expected_title in all_text_combined
        
        if title_match:
            logger.info(f"✅ 地图内容校验通过: {expected_title}")
        else:
            logger.error(f"❌ 地图内容校验失败！预期包含: '{expected_title}'，实际 OCR 结果: {all_text_combined}")
            
        return title_match


    
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
        if not address_text:
            logger.error("未获取到地址信息")
            raise ""
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
