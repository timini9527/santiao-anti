import random
import time
from typing import Optional, Tuple
from selenium.common import NoSuchElementException
from locators.chat_options.videos.chat_video_locator import ChatVideoLocator
from pages.chat_options.images.chat_image_page import ChatImagePage
from core.logger_utils import logger


class ChatVideoPage(ChatImagePage):
    """ 视频选择页面：支持多种模式的单选与多选，复用相册基础组件逻辑 """
    
    # 在当前的相册网格页面选择单张视频
    def select_single_video(self, mode: int = 1, max_swipes: int = 5) -> bool:
        """
        在当前的相册网格页面选择单张视频
        :param mode: 0-选择后取消(点两次), 1-第一张, 2-随机一张, 3-滑到底部最后一张, 4-第9张(不够则下滑寻找，仍不足则选最后一张)
        :param max_swipes: 滑动探测与回溯的最大次数（默认 5 次）
        :return: 成功选中返回 True；mode=0 时选后取消也返回 True
        """
        logger.info(f"🔍 准备选择单张视频，模式: {mode}...")
        only_video_check_buttons = self.get_only_video_check_button(raise_exception=False) or []
        if not only_video_check_buttons:
            logger.warning("⚠️ 当前相册首屏没有立即检测到纯视频勾选按钮")

        # 统一处理向上回溯探测
        def _recover_upward(swipes_limit: int) -> bool:
            """统一处理：触底当前屏全为照片时的自适应向上回溯探测与首屏保底"""
            logger.warning(f"⚠️ 触底当前屏全为照片，启动自适应向上回溯探测 (最大回溯 {swipes_limit} 次)...")
            for back_swipe in range(swipes_limit):
                self.swipe_page(slid_type='down', duration=300)
                time.sleep(0.4)
                rec_buttons = self.get_only_video_check_button(raise_exception=False) or []
                if rec_buttons:
                    logger.info("准备点击离底部最近的纯视频...")
                    rec_buttons[-1].click()
                    logger.info(f"✔️ 向上回溯第 {back_swipe + 1}/{swipes_limit} 次成功选中离底部最近的纯视频")
                    return True

            if only_video_check_buttons:
                logger.warning("⚠️ 底部深处无任何视频素材，平滑回退选用首屏保底视频")
                self.swipe_page_quickly(slid_type='down', duration=400)
                time.sleep(0.5)
                cur_buttons = self.get_only_video_check_button(raise_exception=False) or only_video_check_buttons
                logger.info("准备点击首屏保底视频...")
                cur_buttons[0].click()
                return True
            logger.error("✖️ 相册中未检测到任何可用纯视频")
            return False

        if mode == 0:
            buttons = only_video_check_buttons
            if not buttons:
                self.swipe_page(slid_type='up', duration=300)
                time.sleep(0.3)
                buttons = self.get_only_video_check_button(raise_exception=False) or []
            if not buttons:
                logger.error("✖️ 相册中无可用视频，无法模拟反悔操作")
                return False
            logger.info("准备点击选中第一张视频...")
            buttons[0].click()
            logger.info("✔️ 选中第一张视频完成")
            logger.info("准备再次点击取消勾选，模拟选后反悔...")
            buttons[0].click()
            logger.info("✔️ 再次点击取消勾选完成，模拟选后反悔")
            return True
        elif mode == 1:
            buttons = only_video_check_buttons
            if not buttons:
                logger.info("相册首屏未见视频，微幅向下滑动寻找相册第一条视频...")
                for _ in range(3):
                    self.swipe_page(slid_type='up', duration=300)
                    time.sleep(0.3)
                    buttons = self.get_only_video_check_button(raise_exception=False) or []
                    if buttons:
                        break
            if not buttons:
                logger.error("✖️ 深度探索后相册中仍未检测到任何可用纯视频")
                return False
            logger.info("准备点击选中第一张纯视频...")
            buttons[0].click()
            logger.info("✔️ 成功选中相册中的第一张纯视频")
            return True
        elif mode == 2:
            buttons = only_video_check_buttons
            if not buttons:
                self.swipe_page(slid_type='up', duration=300)
                time.sleep(0.3)
                buttons = self.get_only_video_check_button(raise_exception=False) or []
            if not buttons:
                logger.error("✖️ 相册中未检测到可用纯视频，无法随机选中")
                return False
            idx = random.randint(0, len(buttons) - 1)
            logger.info(f"准备随机选中当前视图中的第 {idx + 1} 张纯视频...")
            buttons[idx].click()
            logger.info(f"✔️ 成功随机选中当前视图中的第 {idx + 1} 张纯视频")
            return True
        elif mode == 3:
            logger.info("执行快速滑动到底部...")
            self.swipe_page_quickly(slid_type='up', duration=300)
            time.sleep(0.5)
            bottom_buttons = self.get_only_video_check_button(raise_exception=False) or []
            if bottom_buttons:
                logger.info("准备选中最后一张纯视频...")
                bottom_buttons[-1].click()
                logger.info("✔️ 成功滑到底部并选中最后一张纯视频")
                return True
            return _recover_upward(max_swipes)

        elif mode == 4:
            target_index = 8
            last_bottom_fingerprint = None
            actual_down_swipes = 0 

            for swipe_index in range(max_swipes):
                cur_buttons = self.get_only_video_check_button(raise_exception=False) or []
                if len(cur_buttons) > target_index:
                    logger.info(f"准备选中第 {target_index + 1} 张纯视频...")
                    cur_buttons[target_index].click()
                    logger.info(f"✔️ 成功选中当前屏第 {target_index + 1} 张纯视频")
                    return True

                try:
                    current_fingerprint = (cur_buttons[-1].rect['x'], cur_buttons[-1].rect['y']) if cur_buttons else None
                except Exception:
                    current_fingerprint = None

                if swipe_index > 0 and current_fingerprint and current_fingerprint == last_bottom_fingerprint:
                    logger.warning(f"⚠️ [Mode 4] 探测到相册物理触底 (累计有效下滑 {actual_down_swipes} 次)，停止盲目下滑")
                    break
                last_bottom_fingerprint = current_fingerprint
                self.swipe_page(slid_type='up', duration=300)
                actual_down_swipes += 1
                time.sleep(0.4)

            final_buttons = self.get_only_video_check_button(raise_exception=False) or []
            if final_buttons:
                logger.info("准备选中最末尾可见纯视频...")
                final_buttons[-1].click()
                logger.info(f"✔️ 纯视频总数不足 9 张，已兜底选中最末尾可见纯视频 (当前屏共 {len(final_buttons)} 条)")
                return True
            return _recover_upward(actual_down_swipes + 1)
        else:
            raise ValueError(f"✖️ 不支持的单选模式: {mode}，可选值为 0/1/2/3/4")

    # 在相册网格中连续勾选多张纯视频
    def select_multiple_videos(self, count: int = 3, max_limit: int = 9, max_swipes: int = 10) -> Tuple[int, str]:
        """
        在相册网格中连续勾选多张纯视频（极速流水线版，内建零开销物理触底探测）
        :param count: 计划勾选张数
        :param max_limit: 单次最多可选张数
        :param max_swipes: 可用于补齐数量的最大下滑次数
        :return: (实际成功勾选张数, 如果触发了上限则包含 Toast/弹窗内容)
        """
        logger.info(f"⚡ [Fast-Select-Video] 启动极速流水线选视频: 计划勾选 {count} 条 (上限 {max_limit} 条)")
        target_count = count
        selected_count = self.get_selected_image_count(raise_exception=False)
        full_toast = ""
        last_bottom_fingerprint = None

        for swipe_index in range(max_swipes + 1):
            if selected_count >= target_count:
                logger.info(f"已达到目标勾选数量: {target_count}")
                break

            video_checks = self.get_only_video_check_button(raise_exception=False)
            if not video_checks:
                logger.warning("当前页未找到可勾选的视频按钮")
                break

            # 🌟 零开销触底探测：比对末尾视频按钮物理坐标，若滑动前后未发生任何位移，说明已达列表最底部
            try:
                current_bottom_fingerprint = (video_checks[-1].rect['x'], video_checks[-1].rect['y'])
            except Exception:
                current_bottom_fingerprint = None

            if swipe_index > 0 and current_bottom_fingerprint and current_bottom_fingerprint == last_bottom_fingerprint:
                logger.warning(f"⚠️ [Fast-Select-Video] 探测到视频列表物理触底（无更多视频），已选 {selected_count} 条，提前终止")
                break
            last_bottom_fingerprint = current_bottom_fingerprint

            need = target_count - selected_count
            unselected_buttons = []
            for btn in video_checks:
                try:
                    btn_text = btn.text or btn.get_attribute('text') or ""
                    if not btn_text.isdigit():
                        unselected_buttons.append(btn)
                except Exception:
                    unselected_buttons.append(btn)

            if not unselected_buttons:
                logger.info("当前屏可见视频已全部被勾选，需翻页寻找更多未选视频")
            else:
                batch_to_click = unselected_buttons[:need]
                logger.info(f"⚡ [Fast-Select-Video] 第 {swipe_index} 轮: 尚缺 {need} 条，流水线批量点击当前屏 {len(batch_to_click)} 个按钮...")

                for btn in batch_to_click:
                    try:
                        if selected_count >= max_limit and target_count > max_limit:
                            logger.info(f"⚠️ 尝试点击第 {selected_count + 1} 张视频以触发上限弹窗")
                            btn.click()
                            time.sleep(0.3)
                            full_toast = self.get_toast_content()
                            self.click_ok_button()
                            target_count = max_limit
                            selected_count = max_limit
                            break

                        logger.info("准备点击视频勾选框...")
                        btn.click()
                        time.sleep(0.05)
                        selected_count += 1
                    except Exception as e:
                        logger.warning(f"点击视频勾选按钮异常: {e}")

                # 批处理点击完成后，单次从底部读取实际已选数量进行同步校准
                actual_count = self.get_selected_image_count(raise_exception=False)
                if actual_count > 0:
                    selected_count = actual_count
                logger.info(f"⚡ [Fast-Select-Video] 当前已选进度校准: {selected_count}/{target_count}")

            if selected_count >= target_count:
                logger.info(f"已达到目标勾选数量: {target_count}")
                break

            # 数量未满足时，平滑下滑翻页
            if swipe_index < max_swipes:
                logger.info(f"⚡ [Fast-Select-Video] 当前视频数量未达标({selected_count}/{target_count})，下滑翻页...")
                self.swipe_page(slid_type='up', duration=300)
                time.sleep(0.3)

        logger.info(f"✅ [Fast-Select-Video] 批量选视频完成，目标 {target_count} 张，实际 {selected_count} 张")
        return selected_count, full_toast

    # 校验视频预览页是否成功加载就绪
    def is_video_preview_ready(self, timeout: int = 8) -> bool:
        """
        校验预览页是否成功加载就绪（显式等待转场动画与播放器图层初始化完成）
        多重信号融合探测：中央播放按钮 -> 预览页结构 -> 视频大小标签 -> 视频标题特征
        :param timeout: 最长等待超时时间（秒，默认 8 秒）
        :return: 成功进入预览且视频播放层就绪返回 True，超时返回 False
        """
        logger.info(f"⏳ [Video-Preview] 等待视频预览页加载就绪 (最长 {timeout}s)...")
        end_time = time.time() + timeout

        while time.time() < end_time:
            # 1. 预览通用特征：检测右上角选中按钮 (ps_tv_selected) 或 视频体积标签 (tv_video_size)
            if self.is_in_preview_mode() or self.find_element(ChatVideoLocator.VIDEO_SIZE_TEXT, timeout=0.3, raise_exception=False):
                logger.info("✅ [Video-Preview] 成功检测到视频预览页结构/体积信息")
                return True

            # 2. 辅助特征：标题文本中包含常见视频后缀或索引
            try:
                title_text = self.get_title_text() or ""
                if any(ext in title_text.lower() for ext in ['.mp4', '.mov', '.m4v', '.3gp', '视频', '1/']):
                    logger.info(f"✅ [Video-Preview] 视频预览页标题特征匹配成功: {title_text}")
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        logger.warning(f"⚠️ [Video-Preview] 视频预览页在 {timeout}s 内未成功就绪")
        return False
