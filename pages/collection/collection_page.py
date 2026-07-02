import io
import os
import time
from dateutil import parser
from datetime import datetime
import imagehash
from PIL import Image
from locators.collection.collection_locator import CollectionLocator
from selenium.common import StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement
from pages.collection.chat_collection_page import ChatCollectionPage
from core.logger_utils import logger


class CollectionPage(ChatCollectionPage):

    # 将字符串转换成时间戳
    def str_to_dtime(self, dt_str: str, index: int = 0) -> datetime:
        dt_coll = parser.parse(dt_str)
        logger.info(f" ✅ 将字符串转换成时间戳: {dt_coll}")
        return dt_coll

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





    # ================================================================
    # 收藏页面相关
    # ================================================================
    # 收藏页面-获取收藏页面时间
    def get_collection_page_time(self) -> str:
        """  获取收藏页面时间  """
        try:
            device_time = self.driver.get_device_time()
            dt = parser.parse(device_time)
            formatted_time = dt.strftime("%Y/%m/%d %H:%M:%S")
            logger.info(f"⏳ [Action] 获取设备时间：{device_time}，格式化成功：{formatted_time}")
            return formatted_time
        except Exception as e:
            logger.error(f"❌ [Action] 获取或解析设备时间失败: {e}")
            formatted_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            logger.info(f"⏳ [Action] 采用本地时间格式化降级: {formatted_time}")
            return formatted_time

    # 收藏页面-获取收藏的用户+时间
    def get_collection_user_time(self, index: int = 0) -> str:
        """  获取收藏的用户+时间  """
        items = self.get_collection_items()
        content = items[index].find_element(*CollectionLocator.COLL_META).get_attribute('text')
        logger.info(f"⏳ [Action] 获取收藏的用户+时间: {content}")
        return content

    # 收藏页面-获取收藏的时间
    def get_collection_time(self, index: int = 0) -> str:
        """  获取收藏的时间  """
        content = self.get_collection_user_time(index)
        if not content:
            logger.warning("⚠️ 收藏的用户与时间内容为空")
            return ""
        # 提取时间部分：时间格式固定为 'YYYY/MM/DD HH:mm:ss'，长度为 19 位，且位于最右侧
        time_part = content[-19:].strip()
        logger.info(f"⏳ [Action] 从内容 '{content}' 中分离出时间: '{time_part}'")
        return time_part

    # 收藏页面-验证收藏的时间
    def verify_collection_time(self, now_time: str, coll_time: str, max_diff_seconds: float = 60.0) -> bool:
        """  验证收藏的时间  """
        logger.info(f"⏳ [Action] 正在验证收藏时间，当前设备时间: {now_time}, 收藏显示时间: {coll_time}")
        try:
            dt_now = parser.parse(now_time)
            dt_coll = parser.parse(coll_time)
            diff = abs((dt_now - dt_coll).total_seconds())
            logger.info(f"⏳ [Action] 时间差值为 {diff} 秒, 允许的最大误差为 {max_diff_seconds} 秒")
            is_valid = diff <= max_diff_seconds
            assert is_valid, f"❌ 收藏时间验证不匹配！当前时间: {now_time}, 收藏时间: {coll_time}, 差值: {diff}s"
            logger.info("✅ 收藏时间验证通过！")
            return is_valid
        except Exception as e:
            logger.error(f"❌ 收藏时间验证发生异常: {e}")
            raise e    



