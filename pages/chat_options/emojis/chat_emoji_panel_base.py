import time
from typing import Any, List, Tuple, Union, Optional
from selenium.webdriver.remote.webelement import WebElement

from common.base_page import BasePage
from core.logger_utils import logger, LogIcon
from locators.chat_options.emojis.chat_emoji_locator import ChatEmojiLocator


class ChatEmojiPanelBase(BasePage):
    """
    底部表情面板的基础类
    专门负责：打开各类面板和设置窗口、返回、获取顶部Tab、提供公用的复杂滑动工具方法与元素点击计算方法。
    """
    # Tab 栏固定元素 3 个
    EMOJI_TOP_MENU_FIXED_COUNT = 3

    # 对齐滑动常量
    ALIGNMENT_THRESHOLD_PX = 6
    SLOP_COMPENSATION_PX = 15
    SWIPE_RETRY_DURATION_MS = 500
    SWIPE_POST_WAIT_SEC = 0.1
    SWIPE_START_OFFSET_Y = 20

    # 获取顶部Tab栏
    def get_top_tab_emoji(self) -> WebElement:
        """  获取顶部Tab栏   """
        logger.info(f"{LogIcon.FIND} 获取顶部Tab栏元素...")
        top_tab_emoji = self.find_element(ChatEmojiLocator.EMOJI_TOP_MENU)
        logger.info(f"{LogIcon.ACTION} 顶部Tab栏: {top_tab_emoji}")
        return top_tab_emoji

    # [内部方法] 获取表情主面板及尺寸范围数据
    def _find_panel(self) -> tuple[WebElement, dict]:
        """ 获取表情面板内部框数据 """
        logger.info(f"{LogIcon.FIND} 获取表情面板内部框数据...")
        panel_elem = self.find_element(ChatEmojiLocator.EMOJI_PANEL_IN, 'visibility', timeout=3)
        if not panel_elem:
            raise RuntimeError("表情面板未能加载")
        return panel_elem, panel_elem.rect

    # [内部方法] 获取已下载表情包容器
    def _get_package_container(self) -> WebElement:
        """
        获取已下载表情包容器
        :return: 贴图元素列表，无则为空列表
        """
        logger.info(f"{LogIcon.FIND} 获取已下载表情包容器...")
        package_container = self.find_element(ChatEmojiLocator.EMOJI_PACKAGE_CONTAINER, 'visibility', timeout=3)
        if not package_container:
            raise RuntimeError("已下载表情包容器未能加载")
        return package_container

    # 打开表情包商店
    def open_emoji_store(self) -> None:
        """  打开表情包商店   """
        logger.info(f"{LogIcon.ACTION} emoji_panel 准备打开表情包商店...")
        self.click(ChatEmojiLocator.EMOJI_STORE)
        logger.info(f"{LogIcon.ACTION} emoji_panel 打开表情包商店完成")

    # 打开管理表情包设置
    def open_emoji_package_setting(self) -> None:
        """  打开管理表情包设置   """
        logger.info(f"{LogIcon.ACTION} emoji_panel 准备打开管理表情包设置...")
        self.click(ChatEmojiLocator.EMOJI_SETTING)
        logger.info(f"{LogIcon.ACTION} emoji_panel 打开管理表情包设置完成")

    # 返回表情包商店
    def back_to_emoji_store(self) -> None:
        """  返回表情包商店   """
        logger.info(f"{LogIcon.ACTION} emoji_panel 准备返回表情包商店...")
        self.click(ChatEmojiLocator.EMOJI_BACK, force_wait=True, timeout=2)
        logger.info(f"{LogIcon.ACTION} emoji_panel 返回表情包商店完成")
    
    # 返回到聊天页面
    def back_to_chat_page(self) -> None:
        """  返回到聊天页面   """
        logger.info(f"{LogIcon.ACTION} emoji_panel 准备返回到聊天页面...")
        self.click(ChatEmojiLocator.EMOJI_BACK, force_wait=True, timeout=2)
        logger.info(f"{LogIcon.ACTION} emoji_panel 返回到聊天页面完成")

    # 表情面板-打开已添加表情包的管理列表
    def open_collection_emoji_manage(self) -> None:
        """  管理表情包和添加的表情包   """
        logger.info(f"{LogIcon.ACTION} emoji_panel 准备打开已添加表情包的管理列表...")
        self.click(ChatEmojiLocator.EMOJI_MANAGE, force_wait=True)
        logger.info(f"{LogIcon.ACTION} emoji_panel 打开已添加表情包的管理列表完成")
        time.sleep(1)
    
    # 表情面板-管理列表-获取表情包列表容器
    def get_collection_empkg_container(self) -> WebElement:
        """  获取已添加表情包列表框   """
        logger.info(f"{LogIcon.FIND} 获取已添加表情包列表框...")
        coll_empkg_container = self.find_element(ChatEmojiLocator.COLLECT_RECYCLER, 'visibility', timeout=2)
        if not coll_empkg_container:
            logger.warning(f"{LogIcon.WARN} 当前页面未找到已添加表情包列表框")
            raise RuntimeError("当前页面未找到已添加表情包列表框")
        logger.info(f"{LogIcon.ACTION} 已添加表情包列表框: {coll_empkg_container}")
        return coll_empkg_container
    
    # 表情面板-管理列表-进入管理页面
    def enter_manage_page(self) -> None:
        """  进入管理页面   """
        logger.info(f"{LogIcon.ACTION} emoji_panel 准备进入管理页面...")
        self.click(ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM)
        logger.info(f"{LogIcon.ACTION} emoji_panel 进入管理页面完成")

    # 表情面板-管理列表-item，动态查询所有表情包
    def get_collection_emoji_pkg_item(self) -> int:
        """  获取已添加表情包的管理列表item数量   """
        logger.info(f"{LogIcon.FIND} 获取已添加表情包的管理列表item数量...")
        coll_empkg_items = self.find_elements(ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM, 'visibility', timeout=2)
        if not coll_empkg_items:
            logger.warning(f"{LogIcon.WARN} 当前页面未找到已添加表情包的管理列表item")
            raise RuntimeError("当前页面未找到已添加表情包的管理列表item")
        logger.info(f"{LogIcon.ACTION} 已添加表情包的管理列表item: {len(coll_empkg_items)} 个")
        return int(len(coll_empkg_items))

    # 表情面板-管理列表-打开单个表情包的独立设置详情页
    def open_coll_emoji_pkg_setting_detail(self) -> None:
        """  打开管理表情包设置   """
        logger.info(f"{LogIcon.ACTION} emoji_panel 准备打开单个表情包的独立设置详情页...")
        self.click(ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM)
        logger.info(f"{LogIcon.ACTION} emoji_panel 打开单个表情包的独立设置详情页完成")

    # 表情面板-点击打开表情
    def open_emoji_page(self) -> None:
        """  打开表情页面 - 表情  """
        logger.info(f"{LogIcon.ACTION} emoji_panel 准备点击打开表情输入面板 - 表情...")
        self.click(ChatEmojiLocator.EMOJI_ITEM)
        logger.info(f"{LogIcon.ACTION} emoji_panel 点击打开表情输入面板 - 表情完成")

    # 获取当前面板中可见的所有表情列表，包括已添加的表情包
    def get_visible_emojis(self) -> list[WebElement]:
        """ 获取当前面板中可见的所有表情列表 """
        logger.info(f"{LogIcon.FIND} 获取当前面板中可见的所有表情列表...")
        emoji_list = self.find_elements(ChatEmojiLocator.EMOJI_ITEM)
        if not emoji_list:
            logger.warning(f"{LogIcon.WARN} 当前面板中未找到任何表情元素")
            raise RuntimeError("当前面板中未找到任何表情元素")
        logger.info(f"{LogIcon.ACTION} 当前面板中可见的所有表情列表: {len(emoji_list)} 个")
        return emoji_list

    # 循环尝试返回表情包面板页面
    def back_to_emoji_page(self, max_retry: int = 10) -> None:
        """  返回表情包页面   """
        logger.info(f"{LogIcon.ACTION} emoji_panel 尝试返回表情包面板页面")
        while max_retry > 0:
            logger.info(f"{LogIcon.ACTION} 执行返回操作...")
            self.back()
            max_retry -= 1
            if len(self.find_elements(ChatEmojiLocator.EMOJI_PANEL_CONTAINER)) > 0:
                logger.info(f"{LogIcon.ACTION} emoji_panel 成功返回表情包页面")
                return
            
    # [内部方法] 获取表情面板的顶部Tab栏 - 表情包个数
    def _get_top_tab_emoji_package_count(self) -> tuple[list[WebElement], int]:
        """ 获取表情面板的顶部Tab栏 - 表情包个数 """
        logger.info(f"{LogIcon.FIND} 获取表情面板的顶部Tab栏表情包个数...")
        tab_emoji_pkgs = self.find_elements(ChatEmojiLocator.EMOJI_TOP_MENU_ITEM)
        logger.info(f"{LogIcon.ACTION} 表情面板的顶部Tab栏 - 表情包个数: {int(len(tab_emoji_pkgs) - self.EMOJI_TOP_MENU_FIXED_COUNT)}")
        return tab_emoji_pkgs, int(len(tab_emoji_pkgs) - self.EMOJI_TOP_MENU_FIXED_COUNT)

    # [内部方法] 绝对坐标点击（用于精准点击表情）
    def _click_single_emoji(self, element: WebElement) -> None:
        """ 计算坐标并点击指定的表情元素 """
        rect = element.rect
        click_x = rect['x'] + 5
        click_y = rect['y'] + 5
        logger.info(f"{LogIcon.ACTION} 准备点击表情，坐标: ({click_x}, {click_y})")
        self.click_by_coordinate(click_x, click_y)

    # [内部方法] 动态对齐滑动（用于滑动表情）
    def _swipe_to_distance_exact(self, parent_elem: WebElement, duration: int = 500, max_adjust: int = 3) -> Tuple[Any, dict]:
        """
        彻底解决偏移的动态对齐滑动（内置 Touch Slop 动态补偿和反馈环），将所有表情中的第一行表情滑到表情框第一行
        :param parent_elem: 父元素对象 (WebElement)
        :param duration: 初始滑动时间
        :param max_adjust: 最大微调次数（防止死循环，通常1-2次即可完美对齐）
        :return: (子元素对象, 子元素区域字典)
        """
        logger.info(f"{LogIcon.FIND} 执行动态对齐滑动表情...")
        if parent_elem is None:
            raise ValueError("请提供有效的父元素和子元素对象")
        p_rect = parent_elem.rect

        # 获取所有表情外层容器元素与度量区域
        def get_grid_metrics() -> tuple[WebElement, dict]:
            """获取表情网格度量区域字典"""
            grid_emoji = self.find_element(ChatEmojiLocator.EMOJI_ALL_ITEM_OUT, 'visibility', timeout=2)
            if grid_emoji is None:
                raise ValueError("未定位到所有表情外层容器元素")
            c_rect = grid_emoji.rect
            logger.info(f"{LogIcon.ACTION} 父元素区域：{p_rect['x'], p_rect['y'], p_rect['width'], p_rect['height']}")
            logger.info(f"{LogIcon.ACTION} 子元素区域：{c_rect['x'], c_rect['y'], c_rect['width'], c_rect['height']}")
            return grid_emoji, c_rect

        _, c_rect = get_grid_metrics()
        distance = c_rect['y'] - p_rect['y']
        gu_size = c_rect.get('height')

        for attempt in range(max_adjust):
            distance = c_rect['y'] - p_rect['y']
            if abs(distance) <= 6:
                logger.info(f"{LogIcon.SUCCESS} [{attempt}] 对齐成功！最终偏差仅为: {distance}px")
                return grid_emoji, c_rect
            logger.info(f"{LogIcon.ACTION} [{attempt}] 当前偏差 {distance}px，执行滑动补偿...")

            # 动态判断是否为模拟器以分配不同的补偿值
            udid = str(self.driver.capabilities.get("deviceUDID", self.driver.capabilities.get("udid", ""))).lower()
            logger.info(f"{LogIcon.ACTION} 由于滑动表情到达底部要上滑所有表情，设置补偿值：设备UDID: {udid}")
            is_emulator = "emulator" in udid or "127.0.0.1" in udid
            if is_emulator:
                slop_compensation = 1
                duration = 600
            else:
                slop_compensation = 15
            finger_move_distance = distance + slop_compensation * (1 if distance > 0 else -1)
            self.swipe_by_offset(rect=p_rect, x_offset=0, y_offset=-finger_move_distance, duration=duration)
        
            grid_emoji, c_rect = get_grid_metrics()
        else:
            final_emoji = self.find_element(ChatEmojiLocator.EMOJI_ALL_ITEM_OUT, 'visibility', timeout=2)
            logger.warning(f"{LogIcon.WARN} 警告: 达到最大微调次数 {max_adjust}，可能仍有轻微偏差，偏移量: {distance}px")
            return final_emoji, final_emoji.rect if final_emoji else ({'x': 0, 'y': 0, 'width': 0, 'height': 0})

    # [内部方法] 基础滑动（用于滑动表情）
    def _swipe_to_distance_2(self, slid_type: str = "up", parent_rect: Optional[dict] = None, child_rect: Optional[dict] = None, duration: int = 400) -> None:
        """
        滑动到指定位置，并返回滑动后的元素对象
        :param slid_type: 滑动方向（up/down）
        :param parent_rect: 父元素区域
        :param child_rect: 子元素区域
        :param duration: 滑动持续时间
        :return: 滑动后的元素对象
        """
        logger.info(f"{LogIcon.ACTION} 执行表情基础距离滑动: {slid_type}...")
        size = self.driver.get_window_size()
        w = size['width']
        h = size['height']

        x, y, pw, ph = parent_rect['x'], parent_rect['y'], parent_rect['width'], parent_rect['height']
        x, y, cw, ch = child_rect['x'], child_rect['y'], child_rect['width'], child_rect['height']

        center_x = int(pw * 0.5)
        bottom_y = (h - ph) + int(ph) * 0.8

        start_x, start_y = center_x, bottom_y
        end_x, end_y = center_x, bottom_y - (ch + 13)
        if slid_type.lower() == "up":
            start_x, start_y = center_x, bottom_y
            end_x, end_y = center_x, bottom_y - (ch + 13)
        logger.info(f"{LogIcon.ACTION} 准备执行表情滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y})...")
        self.swipe(start_x, start_y, end_x, end_y, duration)

    # [内部方法] 获取未添加的表情包
    def _get_unadded_packages_on_screen(self, query_type: str = "both") -> List[dict]:
        """
        获取【当前屏幕】上的表情包信息。(重构版：绝对安全的同行 DOM 绑定)
        根据父容器相对查找，杜绝上下错位或按钮漏标引发的虚假数组匹配。
        """
        logger.info(f"{LogIcon.FIND} 获取当前屏幕上的表情包信息...")
        from appium.webdriver.common.appiumby import AppiumBy
        
        current_screen_items = []
        try:
            # 找到包含 Name 的容器父节点
            row_elems = self.find_elements((AppiumBy.XPATH, f'//*[@resource-id="{ChatEmojiLocator.EMOJI_NAME_ID}"]/..'), 'visibility', timeout=3)
            if not row_elems:
                return []
                
            for row in row_elems:
                try:
                    name_elem = row.find_element(AppiumBy.XPATH, f'.//*[@resource-id="{ChatEmojiLocator.EMOJI_NAME_ID}"]')
                    btn_elem = row.find_element(AppiumBy.XPATH, f'.//*[@resource-id="{ChatEmojiLocator.EMOJI_ADD_OR_DEL_ID}"]')
                    
                    name_str = name_elem.text
                    btn_text = btn_elem.text.strip()
                    
                    if query_type == "name" or btn_text in ["添加", "删除", "移除"]:
                        current_screen_items.append({
                            "name_str": name_str,
                            "name_elem": name_elem,
                            "btn_elem": btn_elem
                        })
                except Exception as e:
                    logger.debug(f"{LogIcon.WARN} 单行解析 DOM 异常（可能是未见或局部遮挡），已跳过: {e}")
                    
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} 获取屏幕表情包父节点结构失败: {e}")
             
        logger.info(f"{LogIcon.CAMERA} 安全获取到的当前屏表情包数据: [找到 {len(current_screen_items)} 个有效件]")
        return current_screen_items

    # [内部方法] 点击并获取标题（用于点击底栏图标）
    def _click_and_get_title(self, click_index: int, retry: int = 2) -> Optional[str]:
        """
        点击底栏指定 index 的图标并返回展开的表情包标题。
        内置重试以应对 StaleElementReferenceException。
        """
        logger.info(f"{LogIcon.FIND} 准备点击底栏第 {click_index + 1} 个表情包图标...")
        for attempt in range(retry + 1):
            try:
                icons = self.find_elements(ChatEmojiLocator.EMOJI_TOP_MENU_ITEM)
                if not icons:
                    logger.error(f"{LogIcon.FAIL} 未找到底栏表情包图标元素")
                    return None

                actual_index = click_index
                if actual_index >= len(icons):
                    actual_index = len(icons) - 1

                logger.info(f"{LogIcon.ACTION} 准备点击第 {actual_index + 1} 个底栏表情包图标...")
                icons[actual_index].click()
                time.sleep(0.5)
                return self.get_attribute(ChatEmojiLocator.EMOJI_PACKAGE_TITLE, "text")
            except Exception as e:
                if attempt < retry:
                    logger.warning(f"{LogIcon.WARN} 点击index={click_index}失败(第{attempt + 1}次): {e}，重试中...")
                    time.sleep(1)
                else:
                    logger.error(f"{LogIcon.FAIL} 点击index={click_index}彻底失败: {e}")
                    return None
        return None

    # 【内部方法】 滑动获取已添加的表情包数量
    def get_collection_emoji_pkg_all_items(self) -> int:
        """
        动态滑动统计已添加的表情包总量。
        采用与发包页面一致的“逐行步进”逻辑，确保不重不漏。
        """
        logger.info(f"{LogIcon.FIND} 开始在管理列表中动态滑动统计已添加的表情包总量...")
        
        # 1. 获取布局度量数据
        metrics = self.get_grid_layout_metrics(
            ChatEmojiLocator.COLLECT_RECYCLER, 
            ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM
        )
        
        if not metrics:
            return 0
        
        container_rect = metrics['container_rect']
        container_top_y = metrics['container_top_y']    
        pkg_height = metrics['item_height']
        pkg_per_row = metrics['pkg_per_row']
        stride_y = metrics['stride_y']
        max_per_screen = metrics['max_per_screen']
        
        # 2. 如果当前展示的数量明显不足一满屏，无需滑动，直接返回
        items = self.find_elements(ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM, 'visibility', timeout=3)
        if len(items) < max_per_screen:
            logger.info(f"{LogIcon.CAMERA} 可见表情数( {len(items)} )少于满屏容量( {max_per_screen} )，直接统计返回")
            return len(items) - 1
            
        # 3. 采用“逐行步进分页”逻辑进行全量统计
        total_count = 0
        last_source = ""
        max_retry = 50
        
        for step in range(max_retry):
            is_changed, last_source = self.is_page_source_changed(last_source)
            current_items = self.find_elements(ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM, 'visibility', timeout=3)
            
            if not current_items:
                break
                
            if is_changed:
                # 校验首排是否合格，合格则累加一行
                first_it = current_items[0]
                if abs(first_it.rect['height'] - pkg_height) <= 10 and first_it.rect['y'] >= container_top_y - 5:
                    new_found = len(current_items[:pkg_per_row])
                else:
                    logger.debug(f"{LogIcon.FIND} Step {step+1}: 首排边缘偏移，本轮不计数")
                    new_found = 0
            else:
                # 触底逻辑：统计除了第一排（上一轮已计入）之外的所有剩下元素
                logger.info(f"{LogIcon.ACTION} 已到达列表底部，正在核算剩余元素...")
                new_found = len(current_items[pkg_per_row:]) if len(current_items) > pkg_per_row else 0
                total_count += new_found
                break
                
            total_count += new_found
            # 执行滑动步进
            self.swipe_by_offset(rect=container_rect, x_offset=0, y_offset=-stride_y, duration=600)
            
        logger.info(f"{LogIcon.SUCCESS} 动态统计完成，计算到表情包总量为: {total_count}")
        return total_count - 1
