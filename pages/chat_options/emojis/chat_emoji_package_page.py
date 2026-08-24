import time
from typing import List
from core.logger_utils import logger
import random
from locators.chat_options.emojis.chat_emoji_locator import ChatEmojiLocator
from pages.chat_options.emojis.chat_emoji_panel_base import ChatEmojiPanelBase
from appium.webdriver.webelement import WebElement
from utils.cv_recognition.screenshot_utils import ScreenshotUtils, ImageComparator


class ChatEmojiPackagePage(ChatEmojiPanelBase):
    """
    负责第三方表情包贴图的发包业务及底栏多表情包切换逻辑
    """
    
    # ==================================================================================================
    # 切换模式：按索引精准点按指定表情包 Tab
    # ==================================================================================================
    def switch_to_emoji_package(self, index: int) -> bool:
        """
        按索引切换到指定的表情包 Tab，不循环遍历无关元素。
        :param index: 表情包序号
            - 正整数: 1(第一个), 2(第二个), 3(第三个)...
            - -1: 最后一个表情包
        """
        logger.info(f"[Action] 开始切换到底栏表情包 | 目标索引: {index}")

        if index == -1:
            logger.info("目标是最后一个表情包，快速滑动到底栏最右侧...")
            for _ in range(5):
                top_tab_emoji = self.get_top_tab_emoji()
                self.swipe_on_element(element=top_tab_emoji, slid_type='left', duration=200)
                time.sleep(0.2)
            title = self._click_and_get_title(-1)
            if title:
                logger.info(f"✅ 已成功切换到最后一个表情包: 【{title}】")
                return True
            else:
                logger.error("❌ 切换最后一个表情包失败，未探测到元素")
                return False

        elif index > 0:
            target_index = ChatEmojiLocator._FIXED_TAB_COUNT + index - 1
            logger.info(f"安全动态探测目标，绝对换算后期望UI位置为: {target_index}")

            # 采用 while 动态递减逼近策略代替硬编码除法公式（兼容折叠屏和小屏）
            current_virtual_index = target_index
            max_swipes = 10
            while current_virtual_index >= 6 and max_swipes > 0:
                top_tab_emoji = self.get_top_tab_emoji()
                self.swipe_on_element(element=top_tab_emoji, slid_type='left')
                time.sleep(0.5)
                # 针对不同机型，保守扣减我们要点击的相对坐标（即向左推移了 2 个可见图标）
                current_virtual_index -= 2
                max_swipes -= 1

            title = self._click_and_get_title(current_virtual_index)
            if title:
                logger.info(f"✅ 已成功切换到第 {index} 个表情包: 【{title}】")
                return True
            else:
                logger.error(f"❌ 切换失败，无法点击第 {index} 个表情包（可能目标下标越界）")
                return False

        else:
            logger.error(f"❌ 无效的表情包索引参数: {index}")
            return False

    # ==================================================================================================
    # 遍历模式：从左往右自动扫描所有表情包名称
    # ==================================================================================================
    def get_all_emoji_packages(self) -> List[str]:
        """
        自动自左向右点击遍历所有可见的表情包 Tab，返回包含所有包名的列表。
        :return: 所有读取到的表情包名称列表
        """
        logger.info("[Action] 开始自左向右遍历底栏所有表情包名称...")

        collected_titles: List[str] = []
        click_index = ChatEmojiLocator._FIXED_TAB_COUNT  # 从第一个表情包的坑位开始 (通常是 3)
        max_attempts = 50
        attempts = 0
        last_read_title = None
        duplicate_count = 0  # 连续读到重复表情包的次数

        while attempts < max_attempts:
            attempts += 1

            title = self._click_and_get_title(click_index)
            if not title:
                if click_index >= 4:
                    logger.debug("游标越界且无新元素，已到达列表最右侧")
                    break
                click_index += 1
                continue

            if title in collected_titles:
                if title == last_read_title:
                    duplicate_count += 1
                else:
                    duplicate_count = 1
                last_read_title = title

                if duplicate_count == 1:
                    logger.warning(f"检测到UI不再滑动(重复读取: {title})，尝试强制游标右移至 {click_index + 1}")
                    click_index += 1
                elif duplicate_count >= 2:
                    logger.info(f"👉 游标右推后依然读取到相同包({title})，判定已彻底到达最右侧！")
                    break
                time.sleep(0.5)
                continue

            duplicate_count = 0
            collected_titles.append(title)
            last_read_title = title
            logger.info(f"[{len(collected_titles)}] 读取到: 【{title}】")

            if click_index < 4:
                click_index += 1

        logger.info(f"✅ 遍历结束，共识别到 {len(collected_titles)} 个表情包。")
        return collected_titles
        
    # 发送表情包贴图
    def sent_emoji_package(self, strategy: str, count: int = 1) -> List[dict]:
        """
        在当前已切换的表情包 Tab 下，按策略发送表情包贴图。
        前置条件：调用前必须已通过 switch_to_emoji_package() 切换到目标表情包。
        :param strategy: 发送策略 ("first", "sequential", "random", "absolute_last", "spam")
        :param count: 发送数量
        :return: 已发送的表情信息列表 [{"index": 0, "strategy": "first"}, ...]
        """
        logger.info(f"[Action] 发送表情包贴图 | 策略: {strategy}, 数量: {count}")

        time.sleep(0.5)
        emoji_list = self.find_elements(ChatEmojiLocator.EMOJI_ITEM, 'visibility', timeout=5)
        if not emoji_list:
            logger.error("❌ 当前表情包面板未找到任何贴图元素")
            return []
        logger.info(f"当前表情包面板可见贴图数量: {len(emoji_list)}")

        sent_info: List[dict] = []

        if strategy == "spam":
            target = emoji_list[0]
            logger.info(f"极速连击策略: 将对第一个贴图连续点击 {count} 次")
            for i in range(count):
                try:
                    self._click_single_emoji(target)
                    sent_info.append({"index": 0, "attempt": i + 1, "strategy": "spam"})
                except Exception as e:
                    logger.warning(f"第 {i + 1} 次连击失败: {e}，重新获取元素...")
                    emoji_list = self.find_elements(ChatEmojiLocator.EMOJI_ITEM, 'visibility', timeout=3)
                    if emoji_list:
                        target = emoji_list[0]
                        self._click_single_emoji(target)
                        sent_info.append({"index": 0, "attempt": i + 1, "strategy": "spam"})
            logger.info(f"✅ 极速连击完成，共成功点击 {len(sent_info)} 次")
            return sent_info

        if strategy == "absolute_last":
            logger.info("滑动到表情包面板底部以获取最后一个贴图...")
            package_container = self._get_package_container()
            
            current_source = self.driver.page_source
            for _ in range(5):
                self.swipe_on_element(package_container, 'up', duration=500)
                new_source = self.driver.page_source
                if new_source == current_source:
                    logger.info("已到达面板底部，停止滑动")
                    break
                current_source = new_source
            bottom_emojis = self.find_elements(ChatEmojiLocator.EMOJI_ITEM, 'visibility', timeout=3)
            if not bottom_emojis:
                logger.error("❌ 滑动到底部后未找到任何贴图")
                return []
            target = bottom_emojis[-1]
            self._click_single_emoji(target)
            sent_info.append({"index": len(bottom_emojis) - 1, "strategy": "absolute_last"})
            logger.info(f"✅ 已发送最后一个贴图 (索引: {len(bottom_emojis) - 1})")
            return sent_info

        needed_count = min(count, len(emoji_list))
        target_elems = []
        if strategy == "first" or strategy == "sequential" or strategy == "single":
            target_elems = emoji_list[:needed_count]
        elif strategy == "random":
            target_elems = random.sample(emoji_list, needed_count)
            
        logger.info(f"策略【{strategy}】要求 {count} 个，实际准备点击 {len(target_elems)} 个贴图")
        for idx, elem in enumerate(target_elems):
            try:
                self._click_single_emoji(elem)
                sent_info.append({"index": idx, "strategy": strategy})
                logger.info(f"✅ 成功发送第 {idx + 1}/{len(target_elems)} 个贴图")
            except Exception as e:
                logger.warning(f"点击第 {idx + 1} 个贴图失败: {e}，尝试重新获取元素...")
                fresh_list = self.find_elements(ChatEmojiLocator.EMOJI_ITEM, 'visibility', timeout=3)
                if fresh_list and idx < len(fresh_list):
                    self._click_single_emoji(fresh_list[idx])
                    sent_info.append({"index": idx, "strategy": strategy})
            if len(target_elems) > 1:
                time.sleep(0.3)

        logger.info(f"✅ 表情包贴图发送完毕，共成功发送 {len(sent_info)} 个")
        return sent_info

    # 获取已添加的表情包状态数量
    def get_added_emoji_status(self) -> int:
        """  获取已添加的表情包状态数量   """
        added_emoji_list = self.find_elements(ChatEmojiLocator.EMOJI_PACKAGE_ADDED_ID)
        logger.info(f"已添加的表情包状态数量: {len(added_emoji_list)}")
        return len(added_emoji_list)
    
    # 根据名称获取已添加的表情包状态数量
    def get_added_emoji_status_by_name(self) -> int:
        """  根据名称获取已添加的表情包状态数量   """
        added_emoji_list = self.find_elements(ChatEmojiLocator.EMOJI_PACKAGE_ADDED_BY_NAME)
        logger.info(f"根据名称获取已添加的表情包状态数量: {len(added_emoji_list)}")
        return len(added_emoji_list)

    # 在表情包设置中心：移除/删除指定的表情包
    def delete_emoji_packages(self, emoji_type: str, count: int = 1) -> tuple[list[str], list[str], bool]:
        """
        在表情包设置页面执行删除操作
        :param emoji_type: 策略 ("del_signal" 删除单个, "sequential" 连续删除)
        :param count: 期望删除的数量 (0 表示删除全部)
        :return: (被删除前的表情包名称列表, 删除后的表情包名称列表, 删除是否全部成功)
        """
        logger.info(f"[Action] 进入表情包管理页面触发删除/移除操作, 删除策略: {emoji_type}, 计划删除卷宗数: {count}")
        del_pkg_names = [] 
        del_dict = {}

        max_attempts = 50
        attempts = 0
        target_count = count if count > 0 else 999

        initial_items_raw = self._get_unadded_packages_on_screen()
        if not initial_items_raw:
            logger.info("屏幕上未发现可删除的表情包，停止删除。")
            return [], [], True
        initial_names = [item["name_str"] for item in initial_items_raw]

        while len(del_pkg_names) < target_count and attempts < max_attempts:
            attempts += 1
            current_items = self._get_unadded_packages_on_screen()
            logger.info(f"当前屏幕可删除的表情包: {current_items}")

            if not current_items:
                logger.info("屏幕上未发现可删除的表情包，停止删除。")
                break

            target_item = current_items[0]
            pkg_name = target_item["name_str"]

            logger.info(f"准备删除表情包: 【{pkg_name}】")
            target_item["btn_elem"].click()

            del_pkg_names.append(pkg_name)
            time.sleep(0.5)  

            toast_text = "删除成功"
            aft_current_items = self._get_unadded_packages_on_screen()
            if not aft_current_items:
                del_status = True
            else:
                del_status = True if pkg_name != aft_current_items[0]["name_str"] else False
            del_dict[pkg_name] = del_status
            
            if del_status:
                logger.info(f"表情包【{pkg_name}】删除成功")
            else:
                logger.error(f"表情包【{pkg_name}】删除失败")

            if emoji_type == "del_signal":
                break

        if attempts >= max_attempts:
            logger.warning(f"达到最大循环次数 {max_attempts}，可能存在异常卡顿，强行退出删除逻辑。")

        logger.info(f"策略【{emoji_type}】 执行完毕，共尝试删除了 {len(del_pkg_names)} 个表情包。")
        
        final_items_raw = self._get_unadded_packages_on_screen()
        final_names = [item["name_str"] for item in final_items_raw]

        if del_dict and all(del_dict.values()):
            return del_pkg_names, final_names, True
        return del_pkg_names, final_names, False

    # 验证删除表情包
    def verify_delete_emoji_packages(self, target_names: list, final_names: list) -> bool:
        """
        验证表情包是否精准删除成功
        :param target_names: 目标要求被删除的表情包名称列表
        :param final_names: 删除后的当页剩余表情包列表
        :return: True 如果目标确实不再存在于剩余列表中
        """
        for pkg in target_names:
            if pkg in final_names:
                logger.error(f"验证失败: 期望删除的【{pkg}】，竟然还存在于列表中: {final_names}")
                return False
        logger.info(f"验证成功: 目标表情包 {target_names} 均不在剩余列表中。")
        return True


    # 表情包验证-简单验证
    def verify_emoji_message_rendered(self, expected_count: int = 1) -> bool:
        """
        验证聊天消息列表中是否成功渲染了大表情气泡。
        """
        logger.info(f"[Verify] 开始验证，确认最后一条消息是否为大表情气泡 (总计发送了 {expected_count} 个)")
        last_emoji_element = self.find_element(ChatEmojiLocator.CHAT_EMOJI_LAST_PACKAGE, 'visibility', timeout=3)
        if not last_emoji_element:
            logger.error(f"❌ 当前屏幕的最后一条消息不是大表情气泡")
            return False
        logger.info("✅ 成功验证当前屏幕的最后一条消息为大表情气泡")
        return True

    # 表情包验证-获取聊天页面中的表情包元素
    def get_emoji_package_message_elements(self, expect_missing: bool = False) -> tuple:
        """
        获取聊天页面中的所有表情包元素
        :return: (表情包元素列表, 元素数量)
        """
        empkg_elems = self.find_elements(ChatEmojiLocator.CHAT_EMOJI_PACKAGE, timeout=3, expect_missing=expect_missing)
        if expect_missing and not empkg_elems:
            logger.warning("⚠️ [Content] - 未获取到表情包元素")
            return [], 0
        if not empkg_elems:
            logger.error("❌ 当前聊天页面未找到任何表情包元素")
            return [], 0
        logger.info(f"当前聊天页面可见表情包元素数量: {len(empkg_elems)}")
        return empkg_elems, len(empkg_elems)
        
    # 表情包验证-长按表情包并点击添加表情
    def long_press_emoji_package_and_add(self, emoji_pkg_elems: List[WebElement], count: int = 1) -> tuple[int, dict]:
        """
        长按表情包并点击添加表情，针对多个目标提供独立校验闭环。
        :param emoji_pkg_elems: 表情包元素列表
        :param count: 期望添加的数量
        :return: (成功添加的个数, 每个 index 的状态字典 {"item_1": True, "item_2": False})
        """
        from pages.chat.core.chat_page import ChatPage
        from pages.common.common_page import CommonPage
        
        target_elems = emoji_pkg_elems[:count]
        logger.info(f"[Action] 准备长按添加表情，目标件数: {count}，实际可用件数: {len(target_elems)}")
        
        success_count = 0
        status_dict = {}
        
        for i, emoji_pkg_elem in enumerate(target_elems):
            try:
                # 1. 执行长按动作
                logger.info(f"正在长按处理第 {i+1}/{len(target_elems)} 个表情包...")
                self.long_press_action(emoji_pkg_elem)
                
                # 2. 点击添加到表情面板 (弹窗操作)
                ChatPage(self.driver).click_add_emoji()
                
                # 3. 结果验证机制：通过抓取 Toast 进行立即判定
                # 注意：如果 Toast 抛出异常没截取到，使用 try 保护以免整个 loop 被阻断
                try:
                    toast_text = CommonPage(self.driver).get_toast_message_common()
                except Exception as e:
                    toast_text = None
                    logger.debug(f"未能抓取到 Toast，可能是隐藏过快: {e}")
                
                if toast_text == "添加成功" or toast_text == "已添加" or toast_text == "该表情已添加" or toast_text == "":
                    logger.info(f"✅ 第 {i+1} 个表情包添加过关，提示: {toast_text}")
                    success_count += 1
                    status_dict[f"item_{i+1}"] = True
                else:
                    logger.warning(f"❌ 第 {i+1} 个表情包添加失败或未捕捉到成功Toast，提示为: {toast_text}")
                    status_dict[f"item_{i+1}"] = False
                
                # 给予缓冲，避免动作过于连贯导致系统拒绝响应或者 Toast 发生重叠
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"❌ 第 {i+1} 个表情包操作期间发生异常崩溃: {e}")
                status_dict[f"item_{i+1}"] = False
                
        logger.info(f"长按添加流程结束，累计成功: {success_count}/{len(target_elems)}。状态明细: {status_dict}")
        return success_count, status_dict

    # 表情包验证-验证添加的表情包是否成功
    def verify_added_empkg_status(self, coll_empkg_count_pre: int, coll_empkg_count_aft: int, add_count: int) -> bool:
        """
        验证新添加的表情包是否正确出现在 “收藏表情当中” 的底栏。
        自动滑到最右侧，从右往左逐个读取并与期望名称列表进行倒序比对。
        :param expected_names: 期望的表情包名称列表（按添加顺序，例如 ['包1', '包2', '包3']）
        :return: 验证通过返回 True，不匹配返回 False
        """
        logger.info(f"[Action] 开始验证底栏表情包 | 期望列表(添加顺序): {coll_empkg_count_pre + add_count} 个")

    # 全量发送并添加收藏逻辑
    def send_and_add_all_emojis_with_paging(self, max_steps: int = 50) -> tuple[int, int]:
        """
        全量发送并添加收藏逻辑（增强版）：
        结合坐标校验过滤残余行，引入异常保护防止 StaleElement 崩溃，并优化验证性能。
        """
        logger.info("[Action] 开始执行“极简逐行步进”全量处理逻辑")
        
        # 1. 获取布局度量数据
        metrics = self.get_grid_layout_metrics(
            ChatEmojiLocator.EMOJI_PACKAGE_CONTAINER, 
            ChatEmojiLocator.EMOJI_ITEM
        )
        if not metrics:
            return 0, 0

        pkg_height = metrics['item_height']
        pkg_per_row = metrics['pkg_per_row']
        stride_y = metrics['stride_y']
        container_top_y = metrics['container_top_y']
        container_rect = metrics['container_rect']

        total_success = 0
        total_tried = 0
        last_source = ""

        for step in range(max_steps):
            is_changed, last_source = self.is_page_source_changed(last_source)
            pkg_items = self.find_elements(ChatEmojiLocator.EMOJI_ITEM, 'visibility', timeout=3)
            
            if not pkg_items:
                break
            
            if is_changed:
                # 策略优化：同一排高度一致且对齐，只需校验首个元素即可决定是否处理整行
                first_it = pkg_items[0]
                if abs(first_it.rect['height'] - pkg_height) <= 10 and first_it.rect['y'] >= container_top_y - 5:
                    pkg_click_items = pkg_items[:pkg_per_row]
                else:
                    logger.info(f"Step {step+1}: 首排处于边缘区域，跳过以待滑动对齐")
                    pkg_click_items = []
            else:
                logger.info("页面未发生变化，已到达底部，处理所有剩余元素")
                pkg_click_items = pkg_items[pkg_per_row:]

            for pkg_click_item in pkg_click_items:
                try:
                    self._click_single_emoji(pkg_click_item)
                    total_tried += 1
                    time.sleep(0.15)
                    
                    last_msg = self.find_element(ChatEmojiLocator.CHAT_EMOJI_LAST_PACKAGE, 'visibility', timeout=2)
                    if last_msg:
                        self.long_press_emoji_package_and_add([last_msg], count=1)
                        total_success += 1
                except Exception as e:
                    logger.warning(f"操作表情包过程中发生非致命异常（可能元素失效）: {e}")
                    continue
            
            if not is_changed:
                break
            
            logger.info(f"Step {step+1}: 向下步进滑动 {stride_y}px")
            self.swipe_by_offset(rect=container_rect, x_offset=0, y_offset=-stride_y, duration=600)

        logger.info(f"✅ 处理结束，共尝试点击 {total_tried} 次，成功收藏 {total_success} 个")
        return total_success, total_tried


    # ==============================================================================
    # 长按功能验证逻辑
    # ==============================================================================

    # 根据 index 获取指定表情包，支持中文名称和纯数字（当做索引用）
    def get_emoji_by_index(self, index: int, expect_missing: bool = False) -> WebElement:
        """
        根据索引获取指定的表情包元素。
        Args:
            index: 表情包的索引值
        Returns:
            表情包的元素对象
        """
        pkg_elems, _ = self.get_emoji_package_message_elements(expect_missing=expect_missing)
        if expect_missing and not pkg_elems:
            logger.warning("⚠️ [Content] - 未获取到表情包元素")
            return None
        if not pkg_elems or len(pkg_elems) == 0:
            logger.error(f"❌ [Action] - 未找到索引为 {index} 的表情包")
            return None
            
        pkg_elem = pkg_elems[index]
        logger.info(f"✅ 获取索引为 {index} 的表情包: {pkg_elem}")
        return pkg_elem

    # 表情包 -> hashCode
    def get_emoji_hashcode(self, index: int = -1, expect_missing: bool = False) -> str:
        """
        获取表情包的hashCode。
        Args:
            index: 表情包的索引值
        Returns:
            表情包的hashCode值
        """
        pkg = self.get_emoji_by_index(index, expect_missing=expect_missing)
        if expect_missing and not pkg:
            logger.warning("⚠️ [Content] - 已知没有表情包，跳过该消息的断言")
            return ""
        if not pkg:
            logger.error(f"❌ [Action] - 未获取到表情包元素")
            return None
        hashcode = ScreenshotUtils.dhash_auto(element=pkg)

        logger.info(f"✅ 获取表情包的hashCode: {hashcode}")
        return hashcode 

    # 比较两个表情包的 hashCode
    def compare_emoji_hashcode(self, hashcode1: str, hashcode2: str) -> bool:
        """
        比较两个表情包的hashCode。
        Args:
            hashcode1: 表情包的hashCode值
            hashcode2: 表情包的hashCode值
        Returns:
            bool: True 表示hashCode相同，False 表示hashCode不同
        """
        return ImageComparator.is_hash_similar(hashcode1, hashcode2, threshold=22)
