import io
import os
import time
from datetime import datetime
import imagehash
from PIL import Image
from appium.webdriver.common.appiumby import AppiumBy
from dateutil import parser
from selenium.common import StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

from common.base_page import BasePage
from pages.mine.mine_page import MinePage
from core.logger_utils import logger


class CollectionPage(BasePage):
    PACKAGE_ID = 'com.santiaotalk.im:id'

    CONTENT_ID = f'{PACKAGE_ID}/content'
    CONTENT_ITEM = (AppiumBy.ID, CONTENT_ID)  # 消息页面每个对话框

    # 接收消息
    RECEIVED_GROUP_ID = f'{PACKAGE_ID}/group'
    RECEIVED_GROUP_ITEM = (AppiumBy.ID, RECEIVED_GROUP_ID)
    RECEIVED_GROUP_TEXT_ID = f'{PACKAGE_ID}/received_text'
    RECEIVED_GROUP_TEXT_ITEM = (AppiumBy.ID, RECEIVED_GROUP_TEXT_ID)
    RECEIVED_IMAGE_ID = f'{PACKAGE_ID}/received_image'
    RECEIVED_IMAGE_ITEM = (AppiumBy.ID, RECEIVED_IMAGE_ID)

    # 发送消息
    SENT_GROUP_ID = f'{PACKAGE_ID}/sent_group'
    SENT_GROUP_ITEM = (AppiumBy.ID, SENT_GROUP_ID)
    SENT_GROUP_TEXT_ID = f'{PACKAGE_ID}/sent_text'
    SENT_GROUP_TEXT_ITEM = (AppiumBy.ID, SENT_GROUP_TEXT_ID)
    SENT_IMAGE_ID = f'{PACKAGE_ID}/sent_image'
    SENT_IMAGE_ITEM = (AppiumBy.ID, SENT_IMAGE_ID)

    # 长按消息弹窗
    PREE_ALERT_ID = (AppiumBy.ID, 'gv_menu')
    COLLECTION_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("收藏")')
    FORWARD_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("转发")')
    MULTI_SELECT_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("多选")')
    REPLY_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("回复")')
    DELETE_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("删除")')

    # 我的收藏
    MINE_COLLECTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的收藏")')
    LAYOUT_ID = (AppiumBy.ID, f'{PACKAGE_ID}/fLayout')  # text和image公用元素
    SWIPE_CONTENT_ID = f'{PACKAGE_ID}/swipe_content'
    SWIPE_CONTENT_ITEM = (AppiumBy.ID, SWIPE_CONTENT_ID)
    COLLECTION_ITEM_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/collet_content')
    COLLECTION_ITEM_IMAGE_ID = f'{PACKAGE_ID}/collect_img'
    COLLECTION_ITEM_IMAGE = (AppiumBy.ID, f'{PACKAGE_ID}/collect_img')
    COLLECTION_DETAILS = (AppiumBy.ID, f'{PACKAGE_ID}/collect_details')
    SWIPE_RIGHT = f'//*[@resource-id="{PACKAGE_ID}/swipe_right"]'
    SWIPE_RIGHT_SHARE_ITEM = (AppiumBy.XPATH, f'{SWIPE_RIGHT}/*[1]')  # 分享
    SWIPE_RIGHT_DELETE_ITEM = (AppiumBy.XPATH, f'{SWIPE_RIGHT}/*[2]')  # 删除

    REACHED_BOTTOM_ID = (AppiumBy.ID, 'refreshlistview_footer_hint_textview')  # 已经到达底部

    # 消息页面查询有多少个对话框, 发送、接收, 图片, 视频消息条数
    def query_content_count(self, locator: tuple) -> int:
        contents = self.find_elements(locator)
        count = len(contents)
        logger.info(f" 💬 查询数据数量: {count}")
        return count

    # 点击第一个对话框进入消息页面
    def click_enter_first_content(self):
        count = self.query_content_count(self.CONTENT_ITEM)
        if count == 1:
            logger.info(f" 💬 进入只有一个对话框: {count}")
            self.click(self.CONTENT_ITEM)
        elif count > 1:
            logger.info(f" 💬 进入有多个对话框: {count}")
            self.click_by_id_instance(self.CONTENT_ID, 0)
        else:
            logger.info(" 💬 没有对话框", count)
            raise Exception("没有对话框")

    # 长按点击收藏
    def click_collection(self, ele: WebElement):
        self.long_press_action(ele)
        self.click(self.COLLECTION_TEXT)  # 点击收藏
        logger.info(" 💬 点击收藏")

    # 获取消息页面文本
    def get_message_common(self, locator: tuple, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement | None, str | None] | tuple[list[WebElement], list[str]]:
        elements = self.find_elements(locator)

        if not elements or len(elements) == 0:
            logger.error(f"❌ 未找到消息元素: {locator}")
            return None, None

        if return_all:
            texts = [ele.text for ele in elements]
            logger.info(f" 💬 找到 {len(texts)} 条消息: {texts}")
            return elements, texts

        if index > len(elements):
            error_msg = f"❌ 索引越界: 共找到 {len(elements)} 条, 无法获取索引 {index}"
            logger.error(error_msg)
            raise IndexError(error_msg)

        elem = elements[index]
        text = elem.get_attribute("text")

        if text is None:
            text = elem.text

        logger.info(f"✅ 找到第 {index + 1} 条消息 : {text}")
        return elem, text

    # 获取发送消息当前页面的文本条数
    def get_sent_text_count(self) -> int:
        return self.query_content_count(self.SENT_GROUP_ITEM)

    # 发送消息: 文本
    def get_sent_text(self, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement, str | None] | tuple[list[WebElement], list[str]]:
        return self.get_message_common(self.SENT_GROUP_TEXT_ITEM, index, return_all)

    # 发送消息: 图片
    def get_sent_image(self, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement, str | None] | tuple[list[WebElement], list[str]]:
        return self.get_message_common(self.SENT_IMAGE_ITEM, index, return_all)

    # 接收消息: 文本
    def get_received_text(self, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement, str | None] | tuple[list[WebElement], list[str]]:
        return self.get_message_common(self.RECEIVED_GROUP_TEXT_ITEM, index, return_all)

    # 接收消息: 图片
    def get_received_image(self, index: int = 0, return_all: bool = False) \
            -> tuple[WebElement, str | None] | tuple[list[WebElement], list[str]]:
        return self.get_message_common(self.RECEIVED_IMAGE_ITEM, index, return_all)

    IMG_PRE = "data/images/collection_pre/collect_pre_"
    IMG_AFT = "data/images/collection_aft/"

    # 截图片：通过坐标
    def get_image_screenshot_coord(self, image_name_path: str, rect: dict):
        x, y, w, h = rect["x"], rect["y"], rect["width"], rect["height"]
        logger.info(f" 💬 获取图片坐标: {x, y, w, h}")
        img = Image.open(image_name_path)
        screen = img.crop((x, y, x + w, y + h))
        screen.save(image_name_path)

    # 截图接收消息的图片：通过坐标
    def get_received_image_screenshot(self, index: int = 0):
        image_name_time = int(time.time())
        logger.info(f" 💬 获取图片名称: {image_name_time}")
        image_name_path = f"{self.IMG_PRE}{image_name_time}.png"
        self.driver.get_screenshot_as_file(image_name_path)

        receive_image = self.find_element(self.RECEIVED_IMAGE_ITEM)
        receive_rect = receive_image.rect
        self.get_image_screenshot_coord(image_name_path, receive_rect)
        return image_name_time

    # 获取长按弹窗坐标
    def get_long_press_alert_coordinate(self) -> tuple[dict, dict]:
        long_press_bounds = self.find_element(self.PREE_ALERT_ID)
        long_press_rect = long_press_bounds.rect
        logger.info(f" 💬 获取长按弹窗 bounds: {long_press_rect}")
        forward_bounds = self.find_element(self.FORWARD_TEXT)
        forward_rect = forward_bounds.rect
        return long_press_rect, forward_rect

    # 获取第一个长按弹窗项
    def get_first_collection_item(self, elem: WebElement) -> str:
        self.long_press_action(elem)
        long_press_rect, forward_rect = self.get_long_press_alert_coordinate()
        first_x = long_press_rect['x'] + forward_rect['width'] * 0.5
        first_y = long_press_rect['y'] + forward_rect['height'] * 0.5
        logger.info(f" 💬 获取第一个长按弹窗项坐标: {first_x, first_y}")
        self.driver.tap([(first_x, first_y)])
        click_time = self.driver.get_device_time(format="YYYY/MM/DD HH:mm:ss")
        logger.info(f" ✅ 获取点击前的设备时间: {click_time}")
        return click_time

    def get_clicked_time(self) -> str:
        click_time = self.driver.get_device_time(format="YYYY/MM/DD HH:mm:ss")
        return click_time

    # 将字符串转换成时间戳
    def str_to_dtime(self, dt_str: str, index: int = 0) -> datetime:
        dt_coll = parser.parse(dt_str)
        logger.info(f" ✅ 将字符串转换成时间戳: {dt_coll}")
        return dt_coll

    # 回到主页面
    def back_to_main(self):
        self.back()

    # 进入我的收藏页面
    def enter_my_collection(self):
        self.click(MinePage.MENU_MINE)
        self.click(self.MINE_COLLECTION, True)

    # 获取收藏页面最新 collect_details() 数据
    def get_collection_details_data(self, item_type: str = 'text', index: int = 0, max_scrolls: int = 100) \
            -> list[dict] | dict | None:
        locator_map = {
            'text': self.COLLECTION_ITEM_TEXT,
            'image': self.COLLECTION_ITEM_IMAGE,
            'all': self.SWIPE_CONTENT_ITEM
        }
        search_locator = locator_map.get(item_type)
        if not search_locator:
            raise ValueError("无效类型")

        logger.info(f"🔎 开始查找 {item_type} 类型的详情 (目标数量: {index+1})...")

        details_results = []
        for i in range(max_scrolls):
            swipe_elems = self.find_elements(self.SWIPE_CONTENT_ITEM)
            logger.info(f" 🔎 滚动查找第 {i + 1} 页...")
            if not swipe_elems:
                logger.info(f"⚠️ 第 {i+1} 屏未找到任何列表元素")
                return None

            for sw, swipe_elem in enumerate(swipe_elems):
                elem_count = swipe_elem.find_elements(*search_locator)
                if elem_count and len(elem_count) > 0:
                    try:
                        detail_elem = swipe_elem.find_element(*self.COLLECTION_DETAILS)
                        text_content = detail_elem.text
                        if not text_content:
                            logger.warning("详情元素文本为空")
                            continue
                        text_lists = text_content.split('  ')
                        if len(text_lists) < 2:
                            collected_details = {
                                "collected_person": "Unknown",
                                "collected_time": text_content
                            }
                        else:
                            collected_details = {
                                "collected_person": text_lists[0],
                                "collected_time": text_lists[1]
                            }
                            logger.info(f" 💬 找到数据: {collected_details}")
                        details_results.append(collected_details)
                        logger.info(f" ✅ 找到第 {i} 条数据: {collected_details}")

                        if index != -1 and len(details_results) >= index:
                            logger.info(f"🎉 目标数量 {index} 已达成，停止查找")
                            if index == 0:
                                return details_results[0]
                            return details_results
                    except Exception as e:
                        logger.error(f" ❌ 获取详情元素文本失败: {e}")

            logger.info(f"🔄 当前屏未满足条件，上滑查找... ({i + 1}/{max_scrolls})")
            source_before = self.driver.page_source
            self.swipe_page('up', duration=500)
            time.sleep(0.5)
            if source_before == self.driver.page_source:
                logger.warning("🛑 已滑到底部，未找到指定元素")
                break
        if index == 1:
            logger.info(f" 🎉 没有找到数据: {details_results}")
            return None
        return details_results

    # 获取当前页面时间及被收藏人 重构排序
    def get_sort_time(self, detail_list: list[dict[str, str]]):
        pastimes = []
        for i, detail in enumerate(detail_list):
            pastimes.append(detail["collected_time"])
        pastimes = sorted(pastimes, reverse=True)
        print(f" 💬 获取当前页面时间及被收藏人 重构排序: {pastimes}")
        return pastimes

    # 获取收藏当前页面所有 text 数据
    def get_collection_text_data(self, index: int = 0) -> list[str]:
        elems = self.find_elements(self.COLLECTION_ITEM_TEXT)
        texts = [elem.text for elem in elems]
        if index == 0:
            return texts
        elif index <= len(texts):
            return texts[0:index:1]
        else:
            texts = self.get_all_my_collection_text_data(index)
            logger.info(f" 💬 获取收藏页面的数据: {texts[0:index:1]}")
            return texts[0:index:1]

    @staticmethod
    def calculate_overlap(list_a: list, list_b: list) -> int:
        max_possible_overlap = min(len(list_a), len(list_b))
        for size in range(max_possible_overlap, 0, -1):
            suffix_a = list_a[-size:]
            prefix_b = list_b[:size]
            if suffix_a == prefix_b:
                return size
        return 0

    # 获取我的收藏页面所有 text 数据
    def get_all_my_collection_text_data(self, index: int = 0, max_scrolls: int = 10) -> list[str]:
        all_data_texts = []
        prev_page_texts = []

        for i in range(max_scrolls):
            elems = self.find_elements(self.COLLECTION_ITEM_TEXT)
            curr_page_texts = [elem.text for elem in elems]
            logger.info(f"🔄 第 {i + 1} 次扫描，当前屏数据: {curr_page_texts}")

            if i == 0:
                all_data_texts.extend(curr_page_texts)
            else:
                overlap_count = self.calculate_overlap(prev_page_texts, curr_page_texts)
                if overlap_count == len(curr_page_texts):
                    logger.info("🛑 数据与上一页完全重叠，判定已到底部")
                    break

                new_data = curr_page_texts[overlap_count:]
                if not new_data:
                    logger.info("🛑 未检测到新数据序列，停止滑动")
                    break

                logger.info(f"   ↳ 识别重叠 {overlap_count} 条，新增: {new_data}")
                all_data_texts.extend(new_data)

            prev_page_texts = curr_page_texts
            self.swipe_page('up', 500)
            time.sleep(0.5)

        logger.info(f"✅ 最终获取全量数据 ({len(all_data_texts)}条): {all_data_texts}")
        if index == 0:
            return all_data_texts
        elif index <= len(all_data_texts):
            return all_data_texts[:index]
        else:
            return all_data_texts

    # 获取收藏当前页面所有 chat_option 数据
    def get_all_collection_image_data(self, max_scrolls=10) -> tuple[int, list[str]]:
        saved_hashes = set()
        images_names = []

        logger.info(f"📸 开始全量抓取图片，保存至: {self.IMG_AFT}")
        total_captures = 0

        for i in range(max_scrolls):
            logger.info(f"🔄 正在扫描第 {i + 1} 屏 ...")
            screen_png = self.driver.get_screenshot_as_png()
            full_screen_img = Image.open(io.BytesIO(screen_png))

            elems = self.find_elements(self.COLLECTION_ITEM_IMAGE)
            if not elems:
                logger.warning("❌ 找不到图片元素，请检查页面元素是否正确")

            current_page_count = 0
            for idx, elem in enumerate(elems):
                try:
                    rect = elem.rect
                    if rect['height'] < 10 or rect['width'] < 10:
                        continue

                    left, top, right, bottom = rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]
                    elem_img = full_screen_img.crop((left, top, right, bottom))

                    img_hash = imagehash.phash(elem_img)
                    if img_hash in saved_hashes:
                        logger.debug(f"   ↳ 图片已存在，跳过 (Hash: {img_hash})")
                        continue

                    saved_hashes.add(img_hash)
                    timestamp = int(time.time() * 1000)
                    filename = f"{timestamp}_{total_captures}.png"
                    save_path = os.path.join(self.IMG_AFT, filename)

                    images_names.append(filename)
                    elem_img.save(save_path)

                    total_captures += 1
                    current_page_count += 1
                    logger.info(f"   ✅ 捕获第 {total_captures} 张图片: {filename}")
                except Exception as e:
                    logger.warning(f"   ❌ 裁剪第 {idx} 个元素失败: {e}")

            source_before = self.driver.page_source
            self.swipe_page('up', 800)
            source_after = self.driver.page_source
            if source_before == source_after:
                logger.info("   ✅ 页面已滑动到底")
                break
        logger.info(f"🎉 抓取完成! 共保存 {total_captures} 张图片")
        return total_captures, images_names

    # 左滑只针对我的收藏中的左滑操作
    def swipe_on_element_collection(self, rect, slider_type: str = "left", duration: int = 500,
                                    collection_type: str = ""):
        rect = rect.copy()
        center_y = rect['y'] + rect['height'] * 0.5

        if collection_type == "image":
            rect['width'] = rect['width'] * 2

        if slider_type.lower() == "left":
            start_x = rect['x'] + rect['width'] * 0.8
            end_x = rect['x'] + rect['width'] * 0.2
        else:
            raise ValueError(f"不支持滑动方向: {slider_type}")
        self.swipe(start_x, center_y, end_x, center_y, duration)

    # 删除收藏页面进行一个文本、图片删除
    def del_collection_item(self, del_type: str = 'text', index: int = 0) -> int | None:
        locator_map = {
            'text': self.COLLECTION_ITEM_TEXT,
            'image': self.COLLECTION_ITEM_IMAGE,
            'all': self.SWIPE_CONTENT_ITEM
        }
        locator = locator_map.get(del_type)
        if not locator:
            raise ValueError("无效的删除类型")

        if index == 0:
            elem = self.find_element(locator)
            if not elem:
                logger.warning(f"⚠️ 未找到 {del_type} 类型的元素，无法执行删除")
                return None
            try:
                self.swipe_on_element_collection(elem.rect, slider_type='left', duration=200,
                                                 collection_type=del_type)
                self.click(self.SWIPE_RIGHT_DELETE_ITEM)
                logger.info(f"✅ 第 {index} 条数据 删除成功")
            except StaleElementReferenceException as e:
                logger.warning("⚠️ 元素引用过期，重试...")
            except Exception as e:
                logger.error(f"❌ 第 {index} 条数据 删除失败: {e}")
                self.back()
                raise
        else:
            return self.del_collection_all_item(del_type=del_type, locator=locator)

    # 删除收藏页面进行所有文本、图片匹配
    def del_collection_all_item(self, del_type: str = 'text', locator=None, max_items: int = 1000) -> int | None:
        logger.info(f"🗑️ 开始全量清空操作 (类型: {del_type})")

        index = 0
        has_refresh = False
        re_enter_retries = 1

        while max_items > 0:
            elems = self.find_elements(locator)
            if elems:
                try:
                    self.swipe_on_element_collection(elems[0].rect, slider_type='left', duration=100,
                                                     collection_type=del_type)
                    self.click(self.SWIPE_RIGHT_DELETE_ITEM)
                    index += 1
                    max_items -= 1
                    has_refresh = False
                    logger.info(f"✅ 第 {index} 条数据 删除成功")
                    continue
                except StaleElementReferenceException as e:
                    logger.warning("⚠️ 元素引用过期 (Stale)，DOM 已刷新，重新扫描...")
                    continue
                except Exception as e:
                    logger.error(f"❌ 第 {index} 条数据 删除失败: {e}")
                    raise e
            else:
                try:
                    logger.info("👀 当前屏已清空，尝试上滑查找更多...")
                    source_page = self.driver.page_source
                    self.swipe_page('up', duration=300)
                    time.sleep(0.5)
                    source_after = self.driver.page_source
                    if source_page != source_after:
                        logger.info("🔄 页面已滚动，重新扫描...")
                        continue
                    else:
                        logger.warning("🛑 页面已滑到底部 (源码未变)")
                        if not has_refresh:
                            logger.info("⚠️ 尝试执行【下拉刷新】以同步数据...")
                            self.swipe_page_quickly()
                            has_refresh = True
                            self.find_elements(locator)
                            continue
                        elif re_enter_retries > 0:
                            self.back()
                            self.enter_my_collection()
                            re_enter_retries -= 1
                            logger.info("🔄 已重新进入页面，开始最终扫描...")
                            continue
                        else:
                            logger.info("✅ 列表已彻底清空")
                            return len(elems)
                except Exception as e:
                    logger.warning(f"⚠️ 刷新失败: {e}")
                    raise e
        return None
