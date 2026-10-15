import time
import random
from typing import Tuple, List, Optional
from core.logger_utils import logger, LogIcon
from selenium.webdriver.remote.webelement import WebElement
from locators.chat_options.emojis.chat_emoji_locator import ChatEmojiLocator
from pages.chat_options.emojis.chat_emoji_panel_base import ChatEmojiPanelBase


class ChatEmojiManagePage(ChatEmojiPanelBase):
    """
    专门负责表情包管理界面（设置页）内的状态获取与删除业务
    """
    # 点击返回按钮
    def click_back_btn(self) -> None:
        """ 点击返回按钮 """
        logger.info(f"{LogIcon.ACTION} 【Action】manage - 准备点击返回按钮...")
        self.click(ChatEmojiLocator.COLLECT_BACK_BTN)
        logger.info(f"{LogIcon.SUCCESS} 【Action】manage - 点击返回按钮完成")
    
    # 点击右上角 整理/取消 按钮
    def click_right_btn(self) -> None:
        """ 点击右上角 整理/取消 按钮 """
        logger.info(f"{LogIcon.ACTION} 【Action】manage - 准备点击右上角 整理/取消 按钮...")
        self.click(ChatEmojiLocator.COLLECT_RIGHT_BTN)
        logger.info(f"{LogIcon.SUCCESS} 【Action】manage - 点击右上角 整理/取消 按钮完成")
    
    # 点击移动按钮
    def click_move_btn(self) -> None:
        """ 点击移动按钮 """
        logger.info(f"{LogIcon.ACTION} 【Action】manage - 准备点击移动按钮...")
        self.click(ChatEmojiLocator.COLLECT_MOVE_BTN)
        logger.info(f"{LogIcon.SUCCESS} 【Action】manage - 点击移动按钮完成")
    
    # 点击删除按钮
    def click_del_btn(self) -> None:
        """ 点击删除按钮 """
        logger.info(f"{LogIcon.ACTION} 【Action】manage - 准备点击删除按钮...")
        self.click(ChatEmojiLocator.COLLECT_DEL_BTN)
        logger.info(f"{LogIcon.SUCCESS} 【Action】manage - 点击删除按钮完成")
    
    # 点击二次删除确认按钮
    def click_del_confirm_btn(self) -> None:
        """ 点击二次删除确认按钮 """
        logger.info(f"{LogIcon.ACTION} 【Action】manage - 准备点击二次删除确认按钮...")
        self.click(ChatEmojiLocator.COLLECT_DEL_CONFIRM_BTN)
        logger.info(f"{LogIcon.SUCCESS} 【Action】manage - 点击二次删除确认按钮完成")
    
    # 点击二次删除取消按钮
    def click_del_cancel_btn(self) -> None:
        """ 点击二次删除取消按钮 """
        logger.info(f"{LogIcon.ACTION} 【Action】manage - 准备点击二次删除取消按钮...")
        self.click(ChatEmojiLocator.COLLECT_DEL_CANCEL_BTN)
        logger.info(f"{LogIcon.SUCCESS} 【Action】manage - 点击二次删除取消按钮完成")

    # 【内部方法】 获取管理页面所有已添加的表情包数量
    def get_manage_all_added_emoji_packages_count(self) -> tuple[list[WebElement], int]:
        """
        获取管理页面所有已添加的表情包数量。
        Returns:
            tuple[list[WebElement], int]: (表情包列表, 表情包数量)
        """
        logger.info(f"{LogIcon.FIND} 获取管理页面所有已添加的表情包数量...")
        # 1. 获取布局度量数据
        metrics = self.get_grid_layout_metrics(
            ChatEmojiLocator.COLLECT_LIST_CONTAINER, 
            ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM
        )
        if not metrics:
            return [], 0
            
        pkg_count = metrics['max_per_screen']
        stride_y = metrics['stride_y']
        list_container_rect = metrics['container_rect']
        item_height = metrics['item_height']
        logger.info(f"{LogIcon.FIND} 计算屏幕可显示表情包数量: {pkg_count}")

        added_pkg_items = self.find_elements(ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM)

        if len(added_pkg_items) < pkg_count:
            logger.info(f"{LogIcon.FIND} 计算出的表情包数量: {len(added_pkg_items)}")
            return added_pkg_items[1:], len(added_pkg_items) - 1
        else:
            logger.info(f"{LogIcon.FIND} 计算出的表情包数量: {pkg_count}, 需要下滑寻找剩余表情包")
            last_source = ""
            max_swipes = 32
            swipe_count = 0
            for step in range(max_swipes):
                # 2. 检测页面变化以判断是否触底
                is_changed, last_source = self.is_page_source_changed(last_source)
                if not is_changed:
                    logger.info(f"{LogIcon.ACTION} 管理页列表已到达底部，停止滑动")
                    break
                
                # 3. 步进式滑动：从容器底部向顶部滑（内容上移）
                logger.debug(f"{LogIcon.FIND} Step {step+1}: 向上步进滑动 {stride_y}px")
                self.swipe_by_offset(rect=list_container_rect, x_offset=0, y_offset=-stride_y, duration=600)
                time.sleep(0.5)
                added_pkg_items_news = self.find_elements(ChatEmojiLocator.COLLECT_EMOJI_PKG_ITEM)
                swipe_count += len(added_pkg_items_news)
            self.swipe_page_quickly(slid_type='up')
            final_total = swipe_count + len(added_pkg_items) - 1
            logger.info(f"{LogIcon.SUCCESS} 动态滑动统计完成，去重后总量为: {final_total}")
            return added_pkg_items[1:], final_total
        
    # 【核心方法】 表情包管理页面批量删除指定类型的表情包
    def delete_manage_emoji_packages(self, emoji_type: str, count: int) -> bool:
        """
        在收藏表情管理页面批量删除表情包。
        核心优化：解决连续点击导致 DOM 刷新产生的 StaleElementReferenceException
        """
        logger.info(f"{LogIcon.ACTION} 准备批量删除表情包: 类型={emoji_type}, 数量={count}...")
        # 1. 仅获取当前总数，用来计算我们要点击哪些【索引】
        _, current_count = self.get_manage_all_added_emoji_packages_count()

        if current_count == 0:
            logger.warning(f"{LogIcon.WARN} 当前没有任何表情包")
            return False

        # 2. 根据策略生成目标【索引列表】（注意：这里存的是数字 [0, 1, 2]，而不是元素对象）
        actual_count = min(count, current_count)
        if emoji_type == 'sequential':
            target_indices = list(range(actual_count))
        elif emoji_type == 'random':
            target_indices = random.sample(range(current_count), actual_count)
        elif emoji_type == 'all' or count == 0:
            target_indices = list(range(current_count))
        else:
            target_indices = []
            
        if not target_indices:
            logger.warning(f"{LogIcon.WARN} 当前没有可供删除的目标表情包")
            return True

        # 3. 遍历索引进行点击
        for i, idx in enumerate(target_indices):
            try:
                # 🌟 每次循环开始前，强制重新获取一次页面上最新的所有元素！
                fresh_items, _ = self.get_manage_all_added_emoji_packages_count()
                if idx < len(fresh_items):
                    logger.info(f"{LogIcon.ACTION} manage - 准备点击选取表情包 - {i+1}/{len(target_indices)}...")
                    fresh_items[idx].click()
                    logger.info(f"{LogIcon.ACTION} manage - 点击选取表情包完成 - {i+1}/{len(target_indices)}")
                    time.sleep(0.3) 
                else:
                    logger.warning(f"{LogIcon.WARN} 索引 {idx} 超出当前页面元素总数！")

            except Exception as e:
                logger.error(f"{LogIcon.FAIL} 选取元素(索引:{idx})失败: {e}")

        self.click_del_btn()
        self.click_del_confirm_btn()
        time.sleep(0.5)

        _, aft_count = self.get_manage_all_added_emoji_packages_count()
        expected_count = current_count - len(target_indices)
        
        del_result = (aft_count == expected_count)
        
        logger.info(f"{LogIcon.ACTION} 批量删除执行完毕。结果: {del_result} (删除前: {current_count}, 期望剩余: {expected_count}, 实际剩余: {aft_count})")
        return del_result

    # 【复合操作】 一键清空所有收藏表情
    def clear_all_collection_emojis(self) -> bool:
        """
        清空所有收藏表情，专门用于自动化测试环境的数据清理与还原。
        封装了进入面板、判断是否为空、全选删除及后退的完整业务流。
        :return: bool 是否成功清理（如果原本就为空，也返回 True）
        """
        logger.info(f"{LogIcon.ACTION} 准备一键清空所有收藏表情...")
        pkg_elems = self.get_collection_empkg_container()
        if not pkg_elems:
            logger.info(f"{LogIcon.SUCCESS} 收藏表情包为空，不需要进行删除操作，直接返回")
            return True
        
        self.enter_manage_page()
        self.open_coll_emoji_pkg_setting_detail()
        
        self.click_right_btn()
        is_delete = self.delete_manage_emoji_packages(emoji_type="all", count=0)
        
        if not is_delete:
            logger.error(f"{LogIcon.FAIL} 清理收藏表情包失败")
            return False

        logger.info(f"{LogIcon.SUCCESS} 成功清理所有收藏表情包")
        self.click_back_btn()
        return True