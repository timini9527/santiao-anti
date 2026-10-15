import random
import re
import time
from typing import List

from selenium.webdriver.remote.webelement import WebElement
from core.logger_utils import logger, LogIcon
from locators.chat_options.emojis.chat_emoji_locator import ChatEmojiLocator
from pages.chat_options.emojis.chat_emoji_panel_base import ChatEmojiPanelBase


class ChatEmojiPage(ChatEmojiPanelBase):
    """
    负责系统默认发黄脸表情、最近使用的表情及表情字符解析
    """

    # [内部方法] 获取当前面板中可见的所有表情列表
    def _get_all_emoji(self) -> list[WebElement]:
        """ 获取所有表情中表情 """
        logger.info(f"{LogIcon.FIND} 获取所有表情中可见的表情列表...")
        all_emoji_list = self.find_elements(ChatEmojiLocator.EMOJI_ALL_ITEM_IN, 'visibility', timeout=3)
        if not all_emoji_list:
            raise RuntimeError("当前页面未找到任何表情元素")
        logger.info(f"{LogIcon.ACTION} 初始状态下，当前可见所有表情总数: {len(all_emoji_list)}")
        return all_emoji_list

    # 最近表情 - 获取表情面板中可见的最近使用表情元素
    def _get_late_emoji(self) -> list[WebElement]:
        """  查找最近使用的表情   """
        logger.info(f"{LogIcon.FIND} 查找最近使用的表情...")
        late_emoji_list = self.find_elements(ChatEmojiLocator.EMOJI_RECENT_ITEM_IN, 'visibility', timeout=3)
        if not late_emoji_list:
            raise RuntimeError("当前页面未找到最近使用的表情元素")
        logger.info(f"{LogIcon.ACTION} 初始状态下，当前可见最近使用的表情总数: {len(late_emoji_list)}")
        return late_emoji_list

    # 所有表情 - 发送表情面板中所有表情
    def _send_all_emojis_by_paging(self, max_slide: int = 20, duration: int = 500) -> int:
        """ 发送所有表情 (一行一行地发送与滑动), 分页全量发送表情 """
        logger.info(f"{LogIcon.ACTION} 准备按行分页发送表情...")
        # 1. 获取表情面板布局度量数据
        metrics = self.get_grid_layout_metrics(
            ChatEmojiLocator.EMOJI_ALL, 
            ChatEmojiLocator.EMOJI_ALL_ITEM_OUT
        )

        if not metrics:
            logger.error(f"{LogIcon.FAIL} 无法获取表情布局指标，发送终止")
            return 0
            
        container_rect = metrics['container_rect']
        stride_y = metrics['stride_y'] + 0                  # 精准的一行滑动距离
        pkg_per_row = metrics['pkg_per_row'] - 1            # 每一行显示的个数
        container_top_y = metrics['container_top_y']

        logger.info(f"{LogIcon.ACTION} 开启全量表情步进发送：每行 {pkg_per_row} 个，步进距离 {stride_y}px")
        total_clicked = 0
        last_source = ""

        out_elem = self.find_element(ChatEmojiLocator.EMOJI_ALL_ITEM_OUT, 'visibility', timeout=2)
        out_elem_height = out_elem.rect['height']
        logger.info(f"{LogIcon.ACTION} 第一行表情元素初始高度: {out_elem_height}px")

        last_y_signature = []        # 用于判定单行是否滑动的指纹
        last_bottom_signature = []   # 用于判定是否触底的指纹
        
        for step in range(max_slide):
            emoji_elems = self.find_elements(ChatEmojiLocator.EMOJI_ALL_ITEM_IN, 'visibility', timeout=1)
            if not emoji_elems:
                logger.warning(f"{LogIcon.WARN} 未找到可见表情元素")
                break

            # 1. 触底检测指纹：对网格里的“第一个表情”进行截图。如果滑动成功，第一个表情图片也会变！
            try:
                current_bottom_signature = emoji_elems[0].screenshot_as_base64
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} 获取表情截图指纹失败: {e}")
                current_bottom_signature = f"error_{step}"

            is_changed = (current_bottom_signature != last_bottom_signature)
            
            # 2. 单行滑动检测指纹：如果当前可见元素的所有 Y 坐标集合没变，说明这一步滑动没生效
            current_y_signature = [e.rect['y'] for e in emoji_elems]
            
            if is_changed or current_y_signature != last_y_signature:
                out_elem_new = self.find_element(ChatEmojiLocator.EMOJI_ALL_ITEM_OUT, 'visibility', timeout=2, raise_exception=False)
                if out_elem_new:
                    out_elem_new_height = out_elem_new.rect['height']
                    is_height_valid = (abs(out_elem_new_height - out_elem_height) <= 25) or (out_elem_new_height >= 80)
                    is_position_valid = out_elem_new.rect['y'] >= (container_top_y - 20)
                    if is_height_valid and is_position_valid:
                        click_items = emoji_elems[:pkg_per_row]
                    else:
                        logger.warning(f"{LogIcon.WARN} Step {step + 1}: 首排处于边缘残缺区域，跳过以待滑动对齐，当前高度：{out_elem_new_height}px, Y={out_elem_new.rect['y']}")
                        click_items = []
                else:
                    out_elem_new_height = out_elem_height
                    click_items = emoji_elems[:pkg_per_row]
            else:
                out_elem_new_height = out_elem_height
                logger.info(f"{LogIcon.FIND} 🚩 检测到已到达面板底部，发送剩余所有表情...")
                click_items = emoji_elems[pkg_per_row:] if len(emoji_elems) > pkg_per_row else []
            
            last_bottom_signature = current_bottom_signature
            last_y_signature = current_y_signature
           
            # 动态判断是否为模拟器，设置补偿值
            udid = str(self.driver.capabilities.get("deviceUDID", self.driver.capabilities.get("udid", ""))).lower()
            logger.info(f"{LogIcon.ACTION} 由于滑动表情到达底部，设置补偿值：设备UDID: {udid}")
            is_emulator = "emulator" in udid or "127.0.0.1" in udid
            if is_emulator:
                slop_compensation = 15   # 模拟器补偿
                duration = 600           # 模拟器滑动时间
                watime = 0.05            # 模拟器点击间隔
            else:
                slop_compensation = 28   # 真机补偿
                duration = 500           # 真机滑动时间
                watime = 0.1             # 真机点击间隔
                
            wucha = out_elem_new_height - out_elem_height
            actual_swipe_distance = out_elem_new_height + slop_compensation

            for i, elem in enumerate(click_items, start=1):
                try:
                    logger.info(f"{LogIcon.ACTION} 准备点击第 {i} 个表情...")
                    elem.click()
                    total_clicked += 1
                    time.sleep(watime)
                except Exception as e:
                    logger.warning(f"{LogIcon.WARN} 点击第 {i} 个表情失败: {e}")

            if not is_changed:
                logger.info(f"{LogIcon.SUCCESS} 全量发送任务完成，共点击 {total_clicked} 个表情")
                break            

            logger.info(f"{LogIcon.STEP} 执行第 {step+1} 轮表情步进滑动: "
                        f"原始步距={out_elem_height}px, "
                        f"第一行元素高度={out_elem_new_height}px, "
                        f"补偿={slop_compensation}px, "
                        f"误差={wucha}px, "
                        f"实际滑动距离=-{actual_swipe_distance}px, "
                        f"滑动耗时={duration}ms")

            self.swipe_by_offset(rect=container_rect, x_offset=0, y_offset=-actual_swipe_distance, duration=duration)
            time.sleep(0.1)
        return total_clicked

    # 发送表情 - 发送第一排基础表情
    def sent_first_row_emoji(self, count: int = 8) -> None:
        """发送第一排基础表情（快速发送第一排指定数量表情，避免全量滑动耗时）"""
        logger.info(f"{LogIcon.ACTION} 快速发送第一排表情 (数量: {count})")
        self.sent_emoji(emoji_type="sequential", count=count)

    # 发送表情 - 发送并全量验证当前面板全部表情功能
    def sent_all_emoji(self) -> None:
        """发送并全量验证当前面板全部表情功能"""
        logger.info(f"{LogIcon.ACTION} 准备全量发送面板内所有的展示表情")
        panel_elem, _ = self._find_panel()
        # 1. 自动对齐到顶部
        grid_emoji_elem, _ = self._swipe_to_distance_exact(panel_elem)
        
        if grid_emoji_elem is None:
            raise ValueError("未能将表情对齐到顶部")

        self._send_all_emojis_by_paging()
    

    # 表情 - 滑动到绝对底部
    def _scroll_to_absolute_bottom(self, panel_elem: WebElement, max_slide: int = 15) -> list[WebElement]:
        """ 滑动到表情面板的最底部。利用 BasePage 的局部 XML 探测机制，自动识别边界。 """
        logger.info(f"{LogIcon.ACTION} 准备滑动到表情面板最底部...")
        last_source = ""
        for i in range(max_slide):
            is_changed, last_source = self.is_element_source_changed(
                ChatEmojiLocator.EMOJI_ALL, 
                last_source
            )
            if not is_changed:
                logger.info(f"{LogIcon.SUCCESS} 经过 {i} 次滑动，已到达表情面板最底部")
                return self.find_elements(ChatEmojiLocator.EMOJI_ALL_ITEM_IN, 'visibility', timeout=2)
            self.swipe_on_element(panel_elem, slid_type='up', duration=400)
            time.sleep(0.3)
        logger.warning(f"{LogIcon.WARN} 达到最大滑动次数 {max_slide}，可能未到绝对底部")
        return self.find_elements(ChatEmojiLocator.EMOJI_ALL_ITEM_IN)

    # 表情 - 根据策略获取目标表情元素列表
    def _get_target_elements(self, emoji_type: str, count: int, emoji_list: list[WebElement], panel_elem: WebElement) -> list[WebElement]:
        """ 根据策略获取目标表情元素列表,返回: List[WebElement] (无论多少个，统统返回列表) """
        if not emoji_list:
            raise RuntimeError("当前页面未找到可用的表情元素")

        single_target_strategies = {
            "first": lambda items: items[0],
            "eight": lambda items: items[7] if len(items) >= 8 else items[-1],
            "current_last": lambda items: items[-1],
        }

        if emoji_type in single_target_strategies:
            target = single_target_strategies[emoji_type](emoji_list)
            logger.info(f"{LogIcon.ACTION} 单个表情策略【{emoji_type}】已命中目标元素")
            return [target]

        if emoji_type == "absolute_last":
            bottom_emoji_list = self._scroll_to_absolute_bottom(panel_elem)
            if not bottom_emoji_list:
                raise RuntimeError("滑动到底部后，未能重新定位到表情元素")
            logger.info(f"{LogIcon.ACTION} 单个表情策略【absolute_last】已定位到底部最后一个表情")
            return [bottom_emoji_list[-1]]

        actual_count = min(count, len(emoji_list))
        if actual_count <= 0:
            logger.warning(f"{LogIcon.WARN} 策略【{emoji_type}】请求数量无效: {count}")
            return []

        if emoji_type == "random":
            logger.info(f"{LogIcon.ACTION} 随机选择 {actual_count} 个表情")
            return random.sample(emoji_list, actual_count)

        if emoji_type == "sequential":
            logger.info(f"{LogIcon.ACTION} 从第 1 个表情开始，顺序点击 {actual_count} 个表情")
            if actual_count < count:
                logger.warning(f"{LogIcon.WARN} 屏幕可见表情仅剩 {actual_count} 个，无法满足点击 {count} 个的要求")
            return emoji_list[:actual_count]

        raise ValueError(f"未知用例测试表情类型: {emoji_type}")

    
    # 发送表情 - 发送单个或多个表情
    def sent_emoji(self, emoji_type: str = "first", count: int = 1) -> int:
        """
        统一发送表情的 API（支持单个/多个）
        :param emoji_type: 策略("first", "sequential", "random", "absolute_last", "eight", "current_last" 等)
        :param count: 需要发送的个数（仅对 sequential 和 random 策略生效）
        :return: 实际成功点击的表情数量
        """
        logger.info(f"{LogIcon.ACTION} 执行发送普通表情, 策略: {emoji_type}, 数量: {count}")
        panel_elem, _ = self._find_panel()
        emoji_list = self._get_all_emoji()
        target_elems = self._get_target_elements(emoji_type, count, emoji_list, panel_elem)

        logger.info(f"{LogIcon.FIND} 策略【{emoji_type}】要求点击 {count} 个，实际准备点击 {len(target_elems)} 个")
        clicked_count = 0
        for elem in target_elems:
            try:
                self._click_single_emoji(elem)
                clicked_count += 1
                if len(target_elems) > 1:
                    time.sleep(0.2)
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} 点击表情元素失败，跳过当前项: {e}")
        return clicked_count

    # 发送表情 - 发送最近使用过的历史表情
    def sent_late_emoji(self, emoji_type: str = "first", count: int = 1) -> int:
        """
        发送最近使用过的历史表情
        :param emoji_type: 策略标识（保持与 sent_emoji API 风格统一）
        :param count: 计划点击的最近表情数量
        :return: 实际成功点击的表情数量
        """
        logger.info(f"{LogIcon.ACTION} 执行发送最近使用表情, 策略: {emoji_type}, 首选数量: {count}")
        self._find_panel()
        late_emoji_elems = self._get_late_emoji()
        target_elems = late_emoji_elems[:count] if late_emoji_elems else []
        logger.info(
            f"{LogIcon.FIND} 验证最近表情: 发送策略为【{emoji_type}】，"
            f"{LogIcon.FIND} 计划点击前 {count} 个，实际准备点击 {len(target_elems)} 个"
        )
        clicked_count = 0
        for index in range(len(target_elems)):
            try:
                logger.info(f"{LogIcon.FIND} 正在点击最近使用表情，第 {index + 1}/{len(target_elems)} 个")
                current_late_emojis = self._get_late_emoji()
                if index >= len(current_late_emojis):
                    logger.warning(f"{LogIcon.WARN} UI 刷新后最近表情数量变动，跳出点击循环")
                    break
                fresh_elem = current_late_emojis[index]
                self._click_single_emoji(fresh_elem)
                clicked_count += 1
                if len(target_elems) > 1:
                    time.sleep(0.1)
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} 点击最近表情元素失败，跳过: {e}")

        return clicked_count

    # 反转表情数据
    @staticmethod
    def str_to_emoji_list(input_text: str) -> list[str]:
        """
        A = "[呵呵][嘻嘻][大笑][爱你][晕][泪][馋嘴]"
        B = "[馋嘴][泪][晕][爱你][大笑][嘻嘻][呵呵]"
        :param input_text:
        :return: ['[呵呵]', '[嘻嘻]', '[大笑]', ...]
        """
        emoji_list = re.findall(r'\[(.*?)\]', input_text)
        logger.info(f"{LogIcon.ACTION} 输入的表情数据为: {input_text}, 列表为: {emoji_list}")
        return emoji_list
