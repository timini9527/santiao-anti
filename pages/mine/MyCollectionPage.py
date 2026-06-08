import io
import os
import time
import imagehash
from PIL import Image
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common import StaleElementReferenceException

from common.base_page import BasePage
from pages.mine.mine_page import MinePage
from core.logger_utils import logger



class MyCollectionPage(BasePage):

    PACKAGE_ID = BasePage.PACKAGE_ID

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
    # DELETE_ITEM_SWIPE_RIGHT = (AppiumBy.XPATH, f'{SWIPE_RIGHT}/*[last()]') # last() 函数，可以直接定位到最后一个子节点

    REACHED_BOTTOM_ID = (AppiumBy.ID, 'refreshlistview_footer_hint_textview')  # 已经到达底部

    # 回到主页面
    def back_to_main(self):
        self.back()

    # 进入我的收藏页面
    def enter_my_collection(self):
        self.click(MinePage.MENU_MINE)
        # time.sleep(1)
        self.click(self.MINE_COLLECTION, True)

    # 获取收藏页面最新 collect_details() 数据
    def get_collection_details_data(self, item_type: str = 'text', index: int = 0, max_scrolls: int = 100) \
            -> list[dict] | dict | None:
        """
        获取收藏页面 所有数据 被收藏人和时间 并返回
        :param index: 获取数量 (0表示取第一条，>0表示取前N条)
        :param item_type: 'text' 或 'image'。如果指定，会滚动查找该类型的元素并返回其详情。
        :param max_scrolls: 最大重试次数
        """
        # 定义定位符策略
        locator_map = {
            'text': self.COLLECTION_ITEM_TEXT,
            'image': self.COLLECTION_ITEM_IMAGE,
            'all': self.SWIPE_CONTENT_ITEM  # 如果不指定类型，直接找详情
        }
        search_locator = locator_map.get(item_type)
        if not search_locator: raise ValueError("无效类型")

        logger.info(f"🔎 开始查找 {item_type} 类型的详情 (目标数量: {index + 1})...")

        details_results = []
        # --- 滚动查找 ---
        for i in range(max_scrolls):
            swipe_elems = self.find_elements(self.SWIPE_CONTENT_ITEM)
            logger.info(f" 🔎 滚动查找第 {i + 1}   {swipe_elems} 页...")
            if not swipe_elems:
                logger.info(f"⚠️ 第 {i + 1} 屏未找到任何列表元素 (swipe_elems 为空)")
                return None

            for sw, swipe_elem in enumerate(swipe_elems):
                elem_count = swipe_elem.find_elements(*search_locator)
                # 2. 查找所有元素 (如所有的 文本框 或 图片框)
                # parents_elems = self.find_elements(search_locator)
                # 3. 判断数量是否足够 (我们要找第 index 个)
                if elem_count and len(elem_count) > 0:
                    try:
                        detail_elem = swipe_elem.find_element(*self.COLLECTION_DETAILS)
                        text_content = detail_elem.text
                        if not text_content:
                            logger.warning("详情元素文本为空")
                            continue
                        text_lists = text_content.split('  ')
                        if len(text_lists) < 2:
                            # 兼容处理，防止 split 失败
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
                            print(f" 💬 找到数据: {collected_details}")
                        details_results.append(collected_details)
                        logger.info(f" ✅ 找到第 {i} 条数据: {collected_details}")

                        # 数量满足判断 (Exit Condition)
                        if index != -1 and len(details_results) >= index:
                            logger.info(f"🎉 目标数量 {index} 已达成，停止查找， 数据集：{details_results}")
                            # 如果只要 1 条，直接返回 dict，方便调用方使用
                            if index == 0:
                                return details_results[0]
                            return details_results
                    except Exception as e:
                        logger.error(f" ❌ 获取详情元素文本失败: {e}")

            # 6. 如果当前页没找到，或者数量不够 index，则滑动
            logger.info(f"🔄 当前屏未满足条件，上滑查找... ({i + 1}/{max_scrolls})")
            source_before = self.driver.page_source
            self.swipe_page('up', duration=500)
            time.sleep(0.5)
            if source_before == self.driver.page_source:
                logger.warning("🛑 已滑到底部，未找到指定元素")
                break
        # 循环结束后的返回
        if index == 1:
            logger.info(f" 🎉 没有找到数据: {details_results}")
            return None
        return details_results

    # 获取当前页面时间及被收藏人 重构排序
    def get_sort_time(self, detail_list: list[dict[str, str]]):
        """
        获取当前页面时间及被收藏人 重构排序
        :param detail_list:
        :return:
        """
        pastimes = []
        for i, detail in enumerate(detail_list):
            pastimes.append(detail["collected_time"])
        pastimes = sorted(pastimes, reverse=True)  # False - 升序排序, True - 降序排序
        print(f" 💬 获取当前页面时间及被收藏人 重构排序: {pastimes}")
        return pastimes

    # 获取收藏当前页面所有 text 数据
    def get_collection_text_data(self, index: int = 0) -> list[str]:
        """ 获取收藏当前页面所有所有文本并返回列表 """
        elems = self.find_elements(self.COLLECTION_ITEM_TEXT)
        # 使用列表推导式 (List Comprehension) 一行搞定，性能最优
        texts = [elem.text for elem in elems]
        # for i, text in enumerate(texts):
        #     print(f" 💬 收藏页面第 {i+1} 条数据: {text}")
        if index == 0:
            return texts  # 返回所有数据
        elif index <= len(texts):
            return texts[0:index:1]  # 返回指定数量的数据
        else:
            # 获取所有数据
            texts = self.get_all_my_collection_text_data(index)
            logger.info(f" 💬 获取收藏页面的数据: {texts[0:index:1]}")
            print(f" 💬 获取收藏页面的数据: {texts[0:index:1]}")
            return texts[0:index:1]

    @staticmethod
    def calculate_overlap(list_a: list, list_b: list) -> int:
        """
        计算两个列表的相同元素个数, 计算 list_a 的尾部与 list_b 的头部的最大重叠长度
        :param list_a: 上一页的完整数据
        :param list_b: 当前页的完整数据
        :return: 相同元素个数
        """
        # 最大的可能重叠长度是两个列表中较短的那个的长度
        max_possible_overlap = min(len(list_a), len(list_b))

        # 从最大可能重叠开始递减尝试
        # 比如 max=5, 尝试匹配 list_a后5个 和 list_b前5个, 不行就尝试 4个... 3个...
        for size in range(max_possible_overlap, 0, -1):
            # 尝试匹配 list_a 后 size 个 和 list_b 前 size 个
            suffix_a = list_a[-size:]  # list_a 的最后 size 个
            prefix_b = list_b[:size]  # list_b 的开头 size 个
            if suffix_a == prefix_b:
                return size  # 找到匹配，返回长度
        return 0  # 没有匹配, 没有重叠

    # 获取我的收藏页面所有 text 数据
    def get_all_my_collection_text_data(self, index: int = 0, max_scrolls: int = 10) -> list[str]:
        """
        滑动获取所有文本数据（支持重复文本，智能拼接）
        :param index: 返回数据的切片截止位置 (0 代表返回全部)
        :param max_scrolls: 最大滑动次数，防止死循环
        """
        # 1. 初始化总数据列表
        all_data_texts = []

        # 2. 记录上一页的完整数据，用于计算重叠
        prev_page_texts = []

        # 3. 循环滑动抓取
        for i in range(max_scrolls):
            # 获取当前屏幕可见的所有元素文本
            # 注意：这里不过滤空文本，因为空文本可能也是列表的一部分占位
            elems = self.find_elements(self.COLLECTION_ITEM_TEXT)
            curr_page_texts = [elem.text for elem in elems]
            logger.info(f"🔄 第 {i + 1} 次扫描，当前屏数据: {curr_page_texts}")

            if i == 0:
                # 第一页，直接全部加入
                all_data_texts.extend(curr_page_texts)
            else:
                # --- 核心算法：计算重叠并拼接 ---
                # 计算上一页结尾 和 当前页开头 的重叠部分
                overlap_count = self.calculate_overlap(prev_page_texts, curr_page_texts)

                # 如果重叠长度等于当前页长度，说明页面完全没变（到底了或者滑不动了）
                if overlap_count == len(curr_page_texts):
                    logger.info("🛑 数据与上一页完全重叠，判定已到底部")
                    break

                # 截取掉重叠部分，只取新增的数据
                # 例如：Overlap=2, curr=[C, D, E, F] -> new=[E, F]
                new_data = curr_page_texts[overlap_count:]

                if not new_data:
                    # 双重检查：如果没有新数据，且源码也没变，那才是到底
                    # 避免极端情况（例如连续20个'A'导致误判）
                    logger.info("🛑 未检测到新数据序列，停止滑动")
                    break

                logger.info(f"   ↳ 识别重叠 {overlap_count} 条，新增: {new_data}")
                all_data_texts.extend(new_data)

            # 更新上一页数据
            prev_page_texts = curr_page_texts

            # 执行上滑加载更多
            self.swipe_page('up', 500)
            # 必须等待滚动惯性结束，否则获取的元素列表不准
            time.sleep(0.5)

        # 4. 打印结果
        logger.info(f"✅ 最终获取全量数据 ({len(all_data_texts)}条): {all_data_texts}")
        print(f" ✅ 最终获取全量数据 ({len(all_data_texts)}条): {all_data_texts}")
        # for i, text in enumerate(all_data_texts):
        #     print(f" 💬 列表第 {i + 1} 条: {text}")

        # 5. 根据 index 参数返回
        if index == 0:
            return all_data_texts
        elif index <= len(all_data_texts):
            return all_data_texts[:index]  # 切片返回前 index 条
        else:
            return all_data_texts

    # 获取收藏当前页面所有 chat_option 数据
    def get_all_collection_image_data(self, max_scrolls=10) -> tuple[int, list[str]]:
        """ 获取收藏当前页面所有图片并返回列表 """
        # 用于去重的哈希集合
        saved_hashes = set()
        # 用于保存图片名称的列表
        images_names = []

        logger.info(f"📸 开始全量抓取图片，保存至: {self.IMG_AFT}")
        total_captures = 0

        for i in range(max_scrolls):
            logger.info(f"🔄 正在扫描第 {i + 1} 屏 ...")
            # 1. 截取当前全屏 (只截一次，性能优化)
            # 获取二进制数据，不落盘，速度快
            screen_png = self.driver.get_screenshot_as_png()
            full_screen_img = Image.open(io.BytesIO(screen_png))

            # 2. 获取当前屏所有可见图片元素
            elems = self.find_elements(self.COLLECTION_ITEM_IMAGE)

            if not elems:
                logger.warning("❌ 找不到图片元素，请检查页面元素是否正确")

            # 3. 遍历元素进行裁剪
            current_page_count = 0
            for idx, elem in enumerate(elems):
                try:
                    rect = elem.rect
                    # 过滤掉不可见或尺寸异常的元素 (例如高度为0)
                    if rect['height'] < 10 or rect['width'] < 10:
                        continue

                    left, top, right, bottom = rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect[
                        "height"]

                    # 执行裁剪
                    # box = (left, top, right, bottom)
                    elem_img = full_screen_img.crop((left, top, right, bottom))

                    # 4. 去重检查 (基于内容)
                    img_hash = imagehash.phash(elem_img)
                    if img_hash in saved_hashes:
                        logger.debug(f"   ↳ 图片已存在，跳过 (Hash: {img_hash})")
                        print(f"图片已存在 (Hash: {img_hash})")
                        continue

                    saved_hashes.add(img_hash)
                    print(f"添加了图片 (Hash: {img_hash})")
                    print(f"哈希集合： (saved_hashes: {saved_hashes})")

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

            # 6. 滑动到底判断
            # 如果当前页没有捕获任何新图，且元素数量也没变，可能到底了
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
        """
        左滑只针对我的收藏中的左滑操作 (安全版)
        :param rect: 目标元素对象 坐标
        :param slider_type: 滑动方向 "left"(左滑出现菜单), "right"(右滑)
        :param duration: 滑动持续时间，建议 800ms-1000ms，太快容易变成点击
        :param collection_type: 我的收藏页面，文本和图片的控制，其他的滑动不做
        """
        # 1. 【关键】深拷贝 rect，防止修改影响外部引用
        rect = rect.copy()

        # 元素中心 Y 坐标 (保持在行内滑动)
        center_y = rect['y'] + rect['height'] * 0.5

        if collection_type == "image":
            # 改变图片宽度，以便能够左滑
            rect['width'] = rect['width'] * 2

        # 定义 X 轴的起点和终点  左滑: 从元素的右侧(80%) 滑到 左侧(20%)
        if slider_type.lower() == "left":
            start_x = rect['x'] + rect['width'] * 0.8
            end_x = rect['x'] + rect['width'] * 0.2
        else:
            raise ValueError(f"不支持滑动方向: {slider_type}")
        # 执行滑动
        self.swipe(start_x, center_y, end_x, center_y, duration)

    # 删除收藏页面进行一个文本、图片删除
    def del_collection_item(self, del_type: str = 'text', index: int = 0) -> int | None:
        # 1. 策略模式：根据类型选择对应的定位符
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
        """
        清空收藏页面指定类型的数据
        :param locator:
        :param del_type: 删除类型 ('text', 'image', 'all')
        :param max_items: 最大删除数量，防止未知 Bug 导致的死循环
        """
        logger.info(f"🗑️ 开始全量清空操作 (类型: {del_type})")

        index = 0
        has_refresh = False  # 是否执行过刷新兜底
        re_enter_retries = 1  # 标记：允许“退出重进”的次数 (1次)

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
                    # 滚动查找
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
                            # 兜底策略：如果到底了，尝试一次下拉刷新，万一有数据没同步
                            logger.info("⚠️ 尝试执行【下拉刷新】以同步数据...")
                            self.swipe_page_quickly()
                            # time.sleep(1)
                            has_refresh = True  # 标记已刷新，防止死循环刷新
                            self.find_elements(locator)
                            continue
                        # 刷新也没用 -> 尝试退出重进
                        elif re_enter_retries > 0:
                            # 兜底策略：如果刷新也没用，尝试退出重进
                            self.back()
                            self.enter_my_collection()
                            re_enter_retries -= 1
                            logger.info("🔄 已重新进入页面，开始最终扫描...")
                            continue
                        else:
                            # 刷新过了，也滑到底了，确实没数据了
                            logger.info("✅ 列表已彻底清空")
                            return len(elems)
                except Exception as e:
                    logger.warning(f"⚠️ 刷新失败: {e}")
                    raise e
        return None

    # 收藏页面进行删除图片匹配








