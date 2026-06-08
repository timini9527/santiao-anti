import os
import time
from datetime import datetime
from PIL import Image
from dateutil import parser
from selenium.webdriver.remote.webelement import WebElement

from common.base_page import BasePage
from pages.chat.chat_page import ChatPage
from core.logger_utils import logger



class ChatCollectionSourcePage(BasePage):

    PACKAGE_ID = BasePage.PACKAGE_ID


    # 消息页面查询有多少个对话框, 发送、接收, 图片, 视频消息条数
    def query_content_count(self, locator: tuple) -> int:
        # 获取所有对话框
        contents = self.find_elements(locator)
        count = len(contents)
        logger.info(f" 💬 查询数据数量: {count}")
        return count

    # 点击第一个对话框进入消息页面
    def click_enter_first_content(self):
        count = self.query_content_count(ChatPage.CONTENT_ITEM)
        if count == 1:
            logger.info(f" 💬 进入只有一个对话框: {count}")
            self.click(ChatPage.CONTENT_ITEM)
        elif count > 1:
            logger.info(f" 💬 进入有多个对话框: {count}")
            self.click_by_id_instance(ChatPage.CONTENT_ID, 0)
        else:
            logger.info(f" 💬 没有对话框", count)
            raise Exception("没有对话框")

    # 长按点击收藏
    def click_collection(self, ele: WebElement):
        self.long_press_action(ele)
        self.click(ChatPage.COLLECTION_TEXT)  # 点击收藏
        logger.info(" 💬 点击收藏")

    # 获取消息页面文本
    def get_message_common(self, locator: tuple, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement | None, str | None] | tuple[list[WebElement], list[str]]:
        """
        [底层复用] 获取消息元素的通用逻辑
        :param locator: 元素定位符
        :param index: 索引 (仅在 return_all=False 时生效)
        :param return_all: 是否返回列表所有数据
        :return:
            - 成功(单条): (WebElement, str)
            - 成功(多条): ([WebElement], [str])
            - 失败/未找到: None, None
        """
        # 1. 查找元素
        elements = self.find_elements(locator)

        # 2. 判空检查
        if not elements or len(elements) == 0:
            logger.error(f"❌ 未找到消息元素: {locator}")
            # raise NoSuchElementException(f"在页面中未找到元素: {locator}")
            return None, None

        # 3. 模式 A: 返回所有数据
        if return_all:
            texts = [ele.text for ele in elements]  # 或者 ele.get_attribute("text")
            logger.info(f" 💬 找到 {len(texts)} 条消息: {texts}")
            return elements, texts

        # 4. 模式 B: 返回指定单条数据 (越界检查)
        if index > len(elements):
            error_msg = f"❌ 索引越界: 共找到 {len(elements)} 条, 无法获取索引 {index}"
            logger.error(error_msg)
            raise IndexError(error_msg)

        # 5. 提取单条
        elem = elements[index]
        text = elem.get_attribute("text")

        # 兼容处理: 有时候 text 属性为空，尝试取 text 内容
        if text is None:
            text = elem.text

        logger.info(f"✅ 找到第 {index + 1} 条消息 : {text}")
        return elem, text

    # 获取发送消息当前页面的文本条数
    def get_sent_text_count(self) -> int:
        return self.query_content_count(ChatPage.SENT_GROUP_ITEM)

    # 发送消息: 文本
    def get_sent_text(self, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement, str | None] | tuple[list[WebElement], list[str]]:
        """
        获取发送的消息元素和内容。
        逻辑优化：统一处理单条和多条的情况，减少 Appium 交互次数。
        :param index: 指定获取第几条发送的消息，默认为 0（最新的一条或第一条），1 多条
        :param return_all: 如果为 True，忽略 index，返回所有接收消息的列表
        :return: (WebElement, text_content)
        """
        # 收藏页面第一条发送消息
        return self.get_message_common(ChatPage.SENT_GROUP_TEXT_ITEM, index, return_all)

    # 发送消息: 图片
    def get_sent_image(self, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement, str | None] | tuple[list[WebElement], list[str]]:
        # 收藏页面第一条发送图片
        return self.get_message_common(ChatPage.SENT_IMAGE_ITEM, index, return_all)

    # 接收消息: 文本
    def get_received_text(self, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement, str | None] | tuple[list[WebElement], list[str]]:
        """
        获取接收的消息元素和内容。
        逻辑优化：统一处理单条和多条的情况，减少 Appium 交互次数。
        :param index: 指定获取第几条接收的消息，默认为 0（最新的一条或第一条）
        :param return_all: 如果为 True，忽略 index，返回所有接收消息的列表
        :return: (WebElement, text_content)
        """
        # 收藏页面第一条接收消息
        return self.get_message_common(ChatPage.RECEIVED_GROUP_TEXT_ITEM, index, return_all)

    # 接收消息: 图片
    def get_received_image(self, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement, str | None] | tuple[list[WebElement], list[str]]:
        # 收藏页面第一条接收图片
        return self.get_message_common(ChatPage.RECEIVED_IMAGE_ITEM, index, return_all)

    IMG_PRE = f"data/images/collection_pre/collect_pre_"  # 图片前缀
    IMG_AFT = f"data/images/collection_aft/"  # 图片后缀

    # 截图片：通过坐标
    def get_image_screenshot_coord(self, image_name_path: str, rect: dict):
        x, y, w, h = rect["x"], rect["y"], rect["width"], rect["height"]
        logger.info(f" 💬 {os.uname()} 获取图片坐标: {x, y, w, h}")
        img = Image.open(image_name_path)
        screen = img.crop((x, y, x + w, y + h))  # crop((left, top, right, bottom))
        screen.save(image_name_path)

    # 截图接收消息的图片：通过坐标
    def get_received_image_screenshot(self, index: int = 0):
        # 名称定义
        image_name_time = int(time.time())
        logger.info(f" 💬 获取图片名称: {image_name_time}")
        image_name_path = f"{self.IMG_PRE}{image_name_time}.png"
        self.driver.get_screenshot_as_file(image_name_path)

        receive_image = self.find_element(ChatPage.RECEIVED_IMAGE_ITEM)
        receive_rect = receive_image.rect
        self.get_image_screenshot_coord(image_name_path, receive_rect)
        return image_name_time

    # 获取长按弹窗坐标，弹窗 [107,621][970,963] 左上角坐标， 右下角坐标
    def get_long_press_alert_coordinate(self) -> tuple[dict, dict]:
        long_press_bounds = self.find_element(ChatPage.PREE_ALERT_ID)
        long_press_rect = long_press_bounds.rect
        logger.info(f" 💬 获取长按弹窗 bounds: {long_press_rect}")
        # 获取转发坐标
        forward_bounds = self.find_element(ChatPage.FORWARD_TEXT)
        forward_rect = forward_bounds.rect
        # 返回弹窗坐标 和 转发坐标
        return long_press_rect, forward_rect

    # 获取第一个长按弹窗项
    def get_first_collection_item(self, elem: WebElement) -> str:
        self.long_press_action(elem)
        # 第一个子元素坐标 [279,621][452,792] width=173, height=171
        # 第二排第一个子元素坐标 [451,621][624,792] width=173, height=171
        long_press_rect, forward_rect = self.get_long_press_alert_coordinate()
        # 第一个元素坐标
        first_x = long_press_rect['x'] + forward_rect['width'] * 0.5
        first_y = long_press_rect['y'] + forward_rect['height'] * 0.5
        logger.info(f" 💬 获取第一个长按弹窗项坐标: {first_x, first_y}")
        self.driver.tap([(first_x, first_y)])  # 点击第一个元素
        # 2. 获取点击后的设备时间
        click_time = self.driver.get_device_time(format="YYYY/MM/DD HH:mm:ss")
        logger.info(f" ✅ 获取点击前的设备时间: {click_time}")
        return click_time

    def get_clicked_time(self) -> str:
        # 2. 获取点击后的设备时间
        click_time = self.driver.get_device_time(format="YYYY/MM/DD HH:mm:ss")
        return click_time

    # 将字符串转换成时间戳
    def str_to_dtime(self, dt_str: str, index: int = 0) -> datetime:
        # 2. 将字符串转换为 datetime 对象
        # dt_coll = datetime.strptime(dt_str, "%Y/%m/%d %H:%M:%S")
        dt_coll = parser.parse(dt_str)
        logger.info(f" ✅ 将字符串转换成时间戳: {dt_coll}")
        return dt_coll









