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
from appium.webdriver.common.appiumby import AppiumBy


class CollectionPage(ChatCollectionPage):

    IMG_PRE = "data/images/collection_pre/collect_pre_"
    IMG_AFT = "data/images/collection_aft/"

    # 将字符串转换成时间戳
    def str_to_dtime(self, dt_str: str, index: int = 0) -> datetime:
        dt_coll = parser.parse(dt_str)
        logger.info(f" ✅ 将字符串转换成时间戳: {dt_coll}")
        return dt_coll

    # 进入我的收藏页面
    def enter_my_collection(self):
        from pages.mine.mine_page import MinePage
        self.click(MinePage.MENU_MINE)
        self.click(CollectionLocator.MINE_COLLECTION_ENTRANCE, force_wait=True)

    # 获取收藏页面最新 collect_details() 数据
    def get_collection_details_data(self, item_type: str = 'text', index: int = 0, max_scrolls: int = 10) -> list[dict] | dict | None:
        locator_map = {
            'text': CollectionLocator.COLL_CONTENT_TEXT,
            'image': CollectionLocator.COLL_CONTENT_IMAGE,
            'all': CollectionLocator.COLL_CONTENT_CONTAINER
        }
        search_locator = locator_map.get(item_type)
        if not search_locator:
            raise ValueError("无效类型")

        logger.info(f"🔎 开始查找 {item_type} 类型的详情 (目标数量: {index+1})...")

        details_results = []
        for i in range(max_scrolls):
            # 重用已有的 get_collection_items() 封装
            swipe_elems = self.get_collection_items()
            logger.info(f" 🔎 滚动查找第 {i + 1} 页...")
            if not swipe_elems:
                logger.info(f"⚠️ 第 {i+1} 屏未找到任何列表元素")
                return None

            for sw, swipe_elem in enumerate(swipe_elems):
                elem_count = swipe_elem.find_elements(*search_locator)
                if elem_count and len(elem_count) > 0:
                    try:
                        detail_elem = swipe_elem.find_element(*CollectionLocator.COLL_META)
                        text_content = detail_elem.text
                        if not text_content:
                            logger.warning("详情元素文本为空")
                            continue
                        
                        # 重用空格分割+合并时间的统一策略
                        parts = text_content.split(' ')
                        if len(parts) >= 2:
                            collected_details = {
                                "collected_person": parts[0],
                                "collected_time": " ".join(parts[1:])
                            }
                        else:
                            collected_details = {
                                "collected_person": "Unknown",
                                "collected_time": text_content
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
        pastimes = [detail["collected_time"] for detail in detail_list]
        pastimes = sorted(pastimes, reverse=True)
        logger.info(f"[Action] 获取当前页面时间及被收藏人 重构排序: {pastimes}")
        return pastimes

    # 获取收藏当前页面所有 text 数据
    def get_collection_text_data(self, index: int = 0) -> list[str]:
        elems = self.get_collection_texts()
        texts = [elem.text for elem in elems]
        if index == 0:
            logger.info(f" 💬 获取收藏页面的数据: {texts}")
            return texts
        elif index <= len(texts):
            logger.info(f" 💬 获取收藏页面的数据: {texts[0:index:1]}")
            return texts[0:index:1]
        else:
            texts = self.get_all_my_collection_text_data(index)
            logger.info(f" 💬 获取收藏页面的数据: {texts[0:index:1]}")
            return texts[0:index:1]

    @staticmethod
    def calculate_overlap(list_a: list, list_b: list) -> int:
        """
        计算两个列表尾部与头部的重叠长度
        Args:
            list_a: 第一个列表（当前页面数据，列表尾部是最新数据）
            list_b: 第二个列表（上滑后的历史数据，列表头部是最新数据）
        Returns:
            重叠的长度，如果没有重叠返回 0
        """
        max_possible_overlap = min(len(list_a), len(list_b))
        for size in range(max_possible_overlap, 0, -1):
            if list_a[-size:] == list_b[:size]:
                return size
        return 0

    # 获取我的收藏页面所有 text 数据
    def get_all_my_collection_text_data(self, index: int = 0, max_scrolls: int = 10) -> list[str]:
        all_data_texts = []
        prev_page_texts = []

        for i in range(max_scrolls):
            # 重用 get_collection_texts() 封装
            elems = self.get_collection_texts()
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

    # 获取收藏当前页面所有图片数据
    def get_all_collection_image_data(self, max_scrolls: int = 10) -> tuple[int, list[str]]:
        saved_hashes = set()
        images_names = []

        logger.info(f"📸 开始全量抓取图片，保存至: {self.IMG_AFT}")
        total_captures = 0

        for i in range(max_scrolls):
            logger.info(f"🔄 正在扫描第 {i + 1} 屏 ...")
            screen_png = self.driver.get_screenshot_as_png()
            full_screen_img = Image.open(io.BytesIO(screen_png))

            # 重用已有的 get_collection_images() 封装
            elems = self.get_collection_images()
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


    # 分享收藏页面的文本或图片条目
    def share_collection_item(self, share_type: str = 'text', index: int = 0) -> bool:
        """ 分享收藏页面指定索引的条目 """
        if share_type == 'text':
            elem = self.get_collection_text_element(index)
        elif share_type == 'image':
            elem = self.get_collection_image_element(index)
        else:
            items = self.get_collection_items()
            elem = items[index] if items and index < len(items) else None

        if not elem:
            logger.warning(f"⚠️ 未找到 {share_type} 类型的元素，无法执行分享")
            return False

        try:
            self.swipe_on_element(elem, slid_type='left', duration=400)
            self.click(CollectionLocator.SWIPE_RIGHT_SHARE_ITEM)
            logger.info(f"✅ 第 {index} 条 {share_type} 收藏数据分享按钮点击成功")
            return True
        except Exception as e:
            logger.error(f"❌ 第 {index} 条 {share_type} 收藏数据分享失败: {e}")
            raise e




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
            formatted_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            logger.info(f"⏳ [Action] 采用本地时间格式化降级: {formatted_time}")
            return formatted_time

    # 收藏页面-获取收藏的用户+时间
    def get_collection_user_time(self, index: int = 0) -> str:
        """  获取收藏的用户+时间  """
        items = self.get_collection_items()
        content = items[index].find_element(*CollectionLocator.COLL_META).get_attribute('text')
        logger.info(f"⏳ [Action] 获取收藏的用户+时间: {content}")
        return content

    # 收藏页面-获取收藏的时间与用户昵称
    def get_collection_time(self, index: int = 0) -> tuple[str, str]:
        """  获取收藏的用户昵称和时间  """
        content = self.get_collection_user_time(index)
        if not content:
            logger.warning("⚠️ 收藏的用户与时间内容为空")
            return "", ""
        parts = content.split(' ')
        user_part = parts[0]
        time_part = " ".join(parts[1:])
        logger.info(f"⏳ [Action] 从内容中分割出用户昵称: '{user_part}', 时间: '{time_part}'")
        return user_part, time_part

    # 收藏页面-验证收藏的时间
    def verify_collection_time(self, now_time: str, coll_time: str, max_diff_seconds: float = 60.0) -> bool:
        """  验证收藏的时间  """
        logger.info(f"⏳ [Action] 正在验证收藏时间，当前设备时间: {now_time}, 收藏显示时间: {coll_time}")
        try:
            dt_now = parser.parse(now_time)
            dt_coll = parser.parse(coll_time)
            diff = abs((dt_now - dt_coll).total_seconds())
            logger.info(f"⏳ [Action] 时间差值为 {diff} 秒, 允许的最大误差为 {max_diff_seconds} 秒")

            if diff > max_diff_seconds:
                logger.error(f"❌ 收藏时间验证不匹配！当前时间: {now_time}, 收藏时间: {coll_time}, 差值: {diff}s")
                return False
            return True
        except Exception as e:
            logger.error(f"❌ 收藏时间验证发生异常: {e}")
            raise e


    # 删除收藏-删除指定索引的文本/图片条目
    def del_collection_item(self, del_type: str = "text", index: int = 0) -> bool:
        """删除收藏页面中指定索引的条目"""

        if del_type == "text":
            elem = self.get_collection_text_element(index)
        elif del_type == "image":
            elem = self.get_collection_image_element(index)
        elif del_type == "all":
            items = self.get_collection_items()
            elem = items[index] if index < len(items) else None
        else:
            raise ValueError(f"不支持的收藏类型: {del_type}")

        if not elem:
            logger.warning(f"⚠️ 未找到第 {index} 条 {del_type} 类型收藏，无法执行删除")
            return False

        try:
            # 使用相对路径向上查找直接父级容器（不限制 resource-id，兼容 image 的非标准祖先树结构）
            container = elem.find_element(AppiumBy.XPATH, "./parent::*")
            self.swipe_on_element(container, slid_type="left", duration=400)
            self.click(CollectionLocator.SWIPE_RIGHT_DELETE_ITEM)
            logger.info(f"✅ 第 {index} 条 {del_type} 收藏删除成功")
            return True
        except StaleElementReferenceException as e:
            logger.warning(f"⚠️ 第 {index} 条 {del_type} 收藏元素引用过期，删除失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 第 {index} 条 {del_type} 收藏删除失败: {e}")
            raise

    # 删除收藏-删除所有文本/图片条目
    def del_collection_all_item(self, del_type: str = 'text', max_items: int = 100) -> int:
        ''' 删除收藏页面中所有文本/图片条目 并返回被删除的数量 '''
        
        logger.info(f"🗑️ 开始全量清空操作 (类型: {del_type})")
 
        index = 0
        last_source = None
 
        while max_items > 0:
            if del_type == 'text':
                elems = self.get_collection_texts()
            elif del_type == 'image':
                elems = self.get_collection_images()
            else:
                elems = self.get_collection_items()

            if elems:
                try:
                    self.swipe_on_element(elems[0], slid_type='left', duration=400)
                    self.click(CollectionLocator.SWIPE_RIGHT_DELETE_ITEM)
                    index += 1
                    max_items -= 1
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
                    self.swipe_page_quickly(slid_type='up', duration=600, max_swipes=1)
                    
                    is_changed, last_source = self.is_page_source_changed(last_source)
                    
                    if is_changed:
                        logger.info("🔄 页面已滚动，重新扫描...")
                        continue
                    else:
                        logger.warning("🛑 页面已滑到底部 (源码未变)")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ 翻页检测失败: {e}")
                    raise e
        return None


