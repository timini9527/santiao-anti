import random
import time
from typing import Optional, Tuple
from selenium.common import NoSuchElementException
from locators.chat.chat_options.videos.chat_video_locator import ChatVideoLocator
from pages.chat.chat_options.images.chat_image_page import ChatImagePage

from core.logger_utils import logger
import time

class ChatVideoPage(ChatImagePage):
    """ 视频选择页面：支持多种模式的单选与多选，复用相册基础组件逻辑 """
    
    def select_single_video(self, mode: int = 1) -> bool:
        """
        在当前的相册网格页面选择单张视频
        :param mode: 0-选择后取消(点两次), 1-第一张, 2-随机一张, 3-滑到底部最后一张, 4-第9张(不够则下滑寻找，仍不足则选最后一张)
        :return: 成功选中返回 True；mode=0 时选后取消也返回 True
        """
        only_video_check_buttons = self.get_only_video_check_button()
        if not only_video_check_buttons or len(only_video_check_buttons) == 0:
            logger.error("✖️ 当前相册没有找到任何纯视频的勾选按钮")
            raise NoSuchElementException("当前相册为空或未检测到可用视频，请确保设备里有照片")

        if mode == 0:
            # 选择第一张后再点击取消，模拟"反悔"场景
            only_video_check_buttons[0].click()
            logger.info("✔️ 选中第一张视频")
            time.sleep(0.3)
            only_video_check_buttons[0].click()
            logger.info("✔️ 再次点击取消勾选，模拟选后反悔")
            return True
        elif mode == 1:
            only_video_check_buttons[0].click()
            logger.info("✔️ 成功选中相册中的第一张纯视频")
            return True
        elif mode == 2:
            idx = random.randint(0, len(only_video_check_buttons) - 1)
            only_video_check_buttons[idx].click()
            logger.info(f"✔️ 成功随机选中当前视图中的第 {idx + 1} 张纯视频")
            return True
        elif mode == 3:
            # 快速滑到底部，重新获取元素列表后选中末尾那张
            self.swipe_page_quickly(slid_type='up', duration=300)
            time.sleep(0.5)
            only_video_check_buttons = self.get_only_video_check_button(raise_exception=False)
            if not only_video_check_buttons or len(only_video_check_buttons) == 0:
                logger.warning("⚠️ 滑到底部后仍未找到可选视频")
                self.swipe_page_quickly(slid_type='down', duration=300)
                only_video_check_buttons = self.get_only_video_check_button()
                if not only_video_check_buttons or len(only_video_check_buttons) == 0:
                    logger.error("✖️ 当前相册没有找到任何纯视频的勾选按钮")
                    raise NoSuchElementException("滑到底部后相册为空")
            only_video_check_buttons[-1].click()
            logger.info("✔️ 成功滑到底部并选中最后一张纯视频")
            return True
        elif mode == 4:
            # 尝试选中第 9 张纯视频，当前页面不够则下滑继续累积查找
            target_index = 8  # 第 9 张，0-indexed
            seen_count = len(only_video_check_buttons)
            max_swipe = 5 
            swipe_times = 0

            while seen_count <= target_index and swipe_times < max_swipe:
                logger.info(f"当前可见纯视频 {seen_count} 张，不足 {target_index + 1} 张，第 {swipe_times + 1} 次下滑")
                self.swipe_page(slid_type='up', duration=300)
                time.sleep(0.5)
                only_video_check_buttons = self.get_only_video_check_button()
                seen_count = len(only_video_check_buttons) if only_video_check_buttons else 0
                swipe_times += 1

            if not only_video_check_buttons or len(only_video_check_buttons) == 0:
                raise NoSuchElementException("下滑多次后仍未找到任何可选纯视频")

            if len(only_video_check_buttons) > target_index:
                only_video_check_buttons[target_index].click()
                logger.info(f"✔️ 成功选中第 {target_index + 1} 张纯视频")
            else:
                # 视频总数不足 9 张，回退选最后一张
                only_video_check_buttons[-1].click()
                logger.warning(f"⚠️ 纯视频总数仅 {len(only_video_check_buttons)} 张，不足 9 张，已回退选中最后一张")
            return True
        else:
            raise ValueError(f"✖️ 不支持的单选模式: {mode}，可选值为 0/1/2/3/4")

    def select_multiple_videos(self, count: int = 3, max_limit: int = 9, max_swipes: int = 10) -> Tuple[int, str]:
        """
        在相册网格中连续勾选多张纯视频进行发送。
        :param count: 计划勾选张数
        :param max_limit: 单次最多可选张数
        :param max_swipes: 可用于补齐数量的最大下滑次数
        :return: (实际成功勾选张数, 如果触发了上限则包含 Toast/弹窗内容)
        """
        target_count = count
        selected_count = self.get_selected_image_count(raise_exception=False)
        last_source = ""
        full_toast = ""

        for swipe_index in range(max_swipes + 1):
            if selected_count >= target_count:
                break

            video_checks = self.get_only_video_check_button(raise_exception=False)
            if not video_checks:
                logger.warning("当前页未找到可勾选的视频按钮")
                break

            for check in video_checks:
                if selected_count >= target_count:
                    break

                before_count = self.get_selected_image_count(raise_exception=False)

                if before_count >= max_limit and target_count > max_limit:
                    logger.info(f"⚠️ 尝试点击第 {before_count + 1} 张视频以触发上限弹窗")
                    check.click()
                    time.sleep(0.5)
                    full_toast = self.get_toast_content()
                    self.click_ok_button()
                    target_count = max_limit
                    selected_count = max_limit
                    break

                check.click()
                time.sleep(0.2)
                after_count = self.get_selected_image_count(raise_exception=False)

                if after_count > before_count:
                    selected_count = after_count
                    logger.info(f"已勾选视频 {selected_count}/{target_count}")

            if selected_count >= target_count:
                break

            is_changed, last_source = self.is_element_source_changed(ChatVideoLocator.PHOTO_CONTAINER, last_source)
            if not is_changed:
                logger.warning("视频列表已无更多内容，停止补齐勾选")
                break

            self.swipe_page(slid_type='up', duration=400)
            time.sleep(0.5)
            logger.info(f"批量选视频未满目标，第 {swipe_index + 1} 次下滑继续查找")

        logger.info(f"✅ 批量勾选视频完成，目标 {target_count} 张，实际 {selected_count} 张")
        return selected_count, full_toast

    def is_video_preview_ready(self) -> bool:
        """ 校验预览页是否成功加载视频播放层 """
        title_text = self.get_title_text()
        if '.mp4' in title_text or '视频' in title_text:
            logger.info(f"✅ 视频预览页标题检测通过: {title_text}")
            return True
        logger.warning(f"❌ 视频预览页标题未包含视频标识: {title_text}")
        return False
    

    













