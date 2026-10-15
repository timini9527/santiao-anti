import time
import random
from typing import Optional, Literal
from selenium.common import NoSuchElementException
from common.base_page import BasePage
from core.logger_utils import logger, LogIcon
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webelement import WebElement
from locators.chat.core.chat_locator import ChatLocator
from locators.chat_options.images.chat_image_locator import ChatImageLocator
from pages.chat.core.chat_page import ChatPage
from utils.cv_recognition.screenshot_utils import ScreenshotUtils, CropRect


class ChatImagePage(ChatPage):
    """聊天面板-相册内部相关操作：从相册选图、预览大图、勾选原图、确认发送等"""

    # 等待图片选择页面加载
    def wait_for_image_page_load(self, timeout: int = 10) -> bool:
        """等待图片选择页面加载"""
        logger.info(f"{LogIcon.WAIT} 正在等待图片选择页面加载...")
        container = self.find_elements(ChatImageLocator.PHOTO_CONTAINER, timeout=timeout)
        if not container:
            logger.warning(f"{LogIcon.FAIL} 图片选择页面加载失败")
            return False
        logger.info(f"{LogIcon.SUCCESS} 图片选择页面加载成功")
        return True

    # 点击图片图标进入相册
    def click_image_button(self) -> None:
        """点击图片按钮进入图片选择页面"""
        logger.info(f"{LogIcon.ACTION} 准备点击图片按钮进入图片选择页面...")
        self.click(ChatImageLocator.IMAGE_SELECT_ROOT)
        logger.info(f"{LogIcon.ACTION} 点击图片按钮已完成")
    
    # 返回按钮
    def click_back_button(self) -> None:
        """点击返回按钮"""
        logger.info(f"{LogIcon.ACTION} 准备点击返回按钮...")
        self.click(ChatImageLocator.TOP_BACK_BUTTON)
        logger.info(f"{LogIcon.ACTION} 点击返回按钮已完成")
    
    # 标题文本
    def get_title_text(self) -> str:
        """获取标题文本"""
        logger.info(f"{LogIcon.FIND} 获取相册标题文本...")
        return self.get_attribute(ChatImageLocator.TOP_TITLE_TEXT, 'text')
    
    # 点击标题切换相册分类
    def click_title_to_switch_category(self) -> None:
        """点击标题切换相册分类"""
        logger.info(f"{LogIcon.ACTION} 准备点击标题切换相册分类...")
        self.click(ChatImageLocator.TOP_TITLE_TEXT)
        logger.info(f"{LogIcon.ACTION} 点击标题切换相册分类已完成")
    
    # 展开后的相册分类展示
    def open_category_list(self) -> list[WebElement]:
        """展开相册分类列表"""
        logger.info(f"{LogIcon.FIND} 检索展开后的相册分类列表...")
        category_list = self.find_elements(ChatImageLocator.TOP_CATEGORY_TEXT)
        if not category_list or len(category_list) == 0:
            logger.error(f"{LogIcon.FAIL} 没有找到相册分类列表")
            raise NoSuchElementException("没有找到相册分类列表")
        return category_list
    
    # 获取 PHOTO_CONTAINER 的容器
    def get_photo_container(self) -> WebElement:
        """获取 PHOTO_CONTAINER 整个相册 的容器"""
        logger.info(f"{LogIcon.FIND} 获取 PHOTO_CONTAINER 整个相册容器...")
        container = self.find_element(ChatImageLocator.PHOTO_CONTAINER, timeout=3)
        return container
        
    # 获取所有图片
    def get_all_image_items(self) -> list[WebElement]:
        """获取所有图片"""
        logger.info(f"{LogIcon.FIND} 获取相册中所有图片元素...")
        items = self.find_elements(ChatImageLocator.PHOTO_ITEM, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取所有图片，共{len(items)}张")
        return items
    
    # 获取所有图片的勾选按钮
    def get_all_image_check_button(self) -> list[WebElement]:
        """获取所有图片的勾选按钮"""
        logger.info(f"{LogIcon.FIND} 获取所有图片的勾选按钮...")
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取所有图片的勾选按钮，共{len(buttons)}个")
        return buttons
    
    # 获取 仅纯图片(png/jpg) 不包含其他格式图片
    def get_only_image_items(self) -> list[WebElement]:
        """获取仅纯图片(png/jpg) 不包含其他格式图片"""
        logger.info(f"{LogIcon.FIND} 获取仅纯图片(png/jpg)列表...")
        items = self.find_elements(ChatImageLocator.PHOTO_ONLY_IMAGE_ITEM, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取仅纯图片(png/jpg) 不包含其他格式图片，共{len(items)}张")
        return items
    
    # 获取仅不包含视频的元素
    def get_not_video_items(self) -> list[WebElement]:
        """获取仅不包含视频的元素"""
        logger.info(f"{LogIcon.FIND} 获取仅不包含视频的元素列表...")
        items = self.find_elements(ChatImageLocator.PHOTO_NOT_VIDEO_ITEM, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取仅不包含视频的元素，共{len(items)}张")
        return items

    # 获取仅不包含视频的勾选按钮
    def get_not_video_check_button(self) -> list[WebElement]:
        """获取仅不包含视频的勾选按钮"""
        logger.info(f"{LogIcon.FIND} 获取仅不包含视频的勾选按钮...")
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON_NOT_VIDEO, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取仅不包含视频的勾选按钮，共{len(buttons)}个")
        return buttons
    
    # 获取不包含视频、长图、webp、gif等媒体文件的勾选按钮
    def get_not_media_check_button(self) -> list[WebElement]:
        """获取不包含视频、长图、webp、gif等媒体文件的勾选按钮"""
        logger.info(f"{LogIcon.FIND} 获取不包含特殊媒体文件的纯图片勾选按钮...")
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON_NOT_MEDIA, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取不包含视频、长图、webp、gif等媒体文件的勾选按钮，共{len(buttons)}个")
        return buttons

    # 获取仅长图、webp、gif
    def get_only_long_image_items(self) -> list[WebElement]:
        """获取仅长图、webp、gif"""
        logger.info(f"{LogIcon.FIND} 获取仅长图、webp、gif元素列表...")
        items = self.find_elements(ChatImageLocator.PHOTO_IMAGE_LONG_WEBP_GIF_ITEM, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取仅长图、webp、gif，共{len(items)}张")
        return items

    # 获取仅长图、webp、gif的勾选按钮
    def get_only_long_image_check_button(self) -> list[WebElement]:
        """获取仅长图的勾选按钮"""
        logger.info(f"{LogIcon.FIND} 获取仅长图/动图的勾选按钮...")
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON_LONG_WEBP_GIF, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取仅长图、webp、gif的勾选按钮，共{len(buttons)}个")
        return buttons

    # 获取 仅视频
    def get_only_video_items(self) -> list[WebElement]:
        """获取仅视频"""
        logger.info(f"{LogIcon.FIND} 获取仅视频元素列表...")
        items = self.find_elements(ChatImageLocator.PHOTO_ONLY_VIDEO_ITEM, timeout=3)
        logger.info(f"{LogIcon.FIND} 获取仅视频，共{len(items)}张")
        return items

    # 获取仅视频的勾选按钮
    def get_only_video_check_button(self, raise_exception: bool = True) -> list[WebElement]:
        """获取仅视频的勾选按钮"""
        logger.info(f"{LogIcon.FIND} 获取仅视频的勾选按钮...")
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON_VIDEO, timeout=3, raise_exception=raise_exception)
        logger.info(f"{LogIcon.FIND} 获取仅视频的勾选按钮，共{len(buttons)}个")
        return buttons
    
    # 点击预览按钮
    def click_preview_button(self) -> None:
        """点击预览按钮"""
        logger.info(f"{LogIcon.ACTION} 准备点击左下角【预览】按钮...")
        self.click(ChatImageLocator.PHOTO_PREVIEW_TEXT)
        logger.info(f"{LogIcon.ACTION} 已点击左下角【预览】按钮，跳转至大图预览全屏页")
        time.sleep(0.5)
    
    # 点击原图按钮
    def click_original_image_button(self) -> None:
        """点击原图按钮"""
        logger.info(f"{LogIcon.ACTION} 准备点击相片底部的【原图】按钮...")
        self.click(ChatImageLocator.PHOTO_ORIGINAL_TEXT)
        logger.info(f"{LogIcon.ACTION} 点击相片底部的【原图】字样完成")
    
    # 获取原图按钮状态
    def get_original_image_button_status(self) -> str:
        """获取原图按钮状态"""
        logger.info(f"{LogIcon.FIND} 获取原图按钮状态...")
        status = self.get_attribute(ChatImageLocator.PHOTO_ORIGINAL_TEXT, 'checked')
        logger.info(f"{LogIcon.ACTION} 原图按钮状态: {status}")
        return status
    
    # 获取发送前所勾选的图片/视频数量
    def get_selected_image_count(self, raise_exception: bool = True) -> int:
        """获取发送前所勾选的图片数量"""
        logger.info(f"{LogIcon.FIND} 获取已勾选图片数量...")
        selected_text = self.get_attribute(ChatImageLocator.PHOTO_SELECTED_COUNT_TEXT, 'text', timeout=1, raise_exception=raise_exception)
        if selected_text and str(selected_text).isdigit():
            logger.info(f"{LogIcon.SUCCESS} 已勾选 {selected_text} 张图片")
            return int(selected_text)
        logger.info(f"{LogIcon.FIND} 未获取到已勾选图片数量")
        return 0
    
    # 点击发送按钮
    def click_send_button(self) -> None:
        """点击发送按钮"""
        logger.info(f"{LogIcon.SUCCESS} 准备点击【确定发送】按钮...")
        self.click(ChatImageLocator.PHOTO_SEND_TEXT)
        logger.info(f"{LogIcon.SUCCESS} 已点击【确定发送】按钮，正在将位图切片推入聊天流...")
        time.sleep(0.5)
        
    # 预览界面 点击勾选大图按钮
    def click_preview_check_button(self) -> None:
        """点击预览界面勾选大图按钮"""
        logger.info(f"{LogIcon.SUCCESS} 准备点击预览界面勾选大图按钮...")
        self.click(ChatImageLocator.PHOTO_PREVIEW_CHECK_BOX)
        logger.info(f"{LogIcon.SUCCESS} 点击预览界面勾选大图按钮完成")
    
    # 点击底部原图复选框
    def click_original_image_checkbox(self) -> None:
        """点击底部原图复选框，确保照片原画质高精度传输"""
        logger.info(f"{LogIcon.SUCCESS} 准备点击相片底部的【原图】字样...")
        self.click(ChatImageLocator.PHOTO_ORIGINAL_TEXT)
        logger.info(f"{LogIcon.SUCCESS} 点击相片底部的【原图】字样完成，勾选无损发送选项")

    # 点击发送按钮（有角标）
    def click_send_image(self) -> None:
        """点击相册界面或预览界面最右下角的『发送』大按钮"""
        logger.info(f"{LogIcon.FIND} 检查发送按钮前置角标状态...")
        # 发送前防御性校验：只有勾选了图片，右上角有角标时发送按钮才有效亮起
        check_boxs = self.find_elements(ChatImageLocator.PHOTO_SELECTED_COUNT_TEXT, timeout=2)
        if not check_boxs:
            logger.error(f"{LogIcon.FAIL} 发送键呈灰色阻断，因为没有检测到任何已选中的角标数字 (可能刚选的图片太小被你拦截了或者是空窗)")
            raise NoSuchElementException("未选中图片时发送按钮物理不可点")
            
        self.click_send_button()
        time.sleep(0.5)

    # 选中超过10张的弹窗 - 获取 Toast
    def get_toast_content(self) -> str:
        """获取Toast内容"""
        logger.info(f"{LogIcon.FIND} 获取弹窗Toast内容...")
        return self.get_attribute(ChatImageLocator.TV_CONTENT, 'text')

    # 选中超过10张的弹窗 - 点击确认按钮
    def click_ok_button(self) -> None:
        """点击确认按钮"""
        logger.info(f"{LogIcon.SUCCESS} 准备点击确认按钮...")
        self.click(ChatImageLocator.BTN_OK, force_wait=True)
        logger.info(f"{LogIcon.SUCCESS} 选中超过10张的弹窗 - 点击确认按钮完成")

    # 打开面板-进入相册
    def open_panel_to_album(self) -> None:
        """点击图片按钮进入图片选择页面"""
        logger.info(f"{LogIcon.ACTION} 准备从面板进入相册...")
        self.click_add_button()
        self.click_image_button()
    
    # 校验默认页面加载状态
    def verify_default_page_load_status(self) -> bool:
        """校验默认页面加载状态"""
        logger.info(f"{LogIcon.FIND} 校验默认相册页面加载状态...")
        original_status = self.get_original_image_button_status()
        selected_count = self.get_selected_image_count(raise_exception=False)
        if original_status == 'false' and selected_count == 0:
            logger.info(f"{LogIcon.SUCCESS} 默认页面加载状态正常")
            self.click_back_button()
            return True
        else:
            logger.error(f"{LogIcon.FAIL} 默认页面加载状态异常")
            return False

    # 校验底部已选数量是否符合预期
    def verify_selected_count(self, expected_count: int) -> bool:
        """校验底部已选数量是否符合预期"""
        logger.info(f"{LogIcon.FIND} 校验底部已选数量，预期: {expected_count}...")
        current_count = self.get_selected_image_count()
        is_match = current_count == expected_count
        logger.info(f"{LogIcon.FIND} 已选数量校验: current={current_count}, expected={expected_count}, result={is_match}")
        return is_match

    # 选择单张图片
    def select_single_image(self, mode: int = 1) -> bool:
        """
        在当前的相册网格页面选择单张图片
        :param mode: 0-选择后取消(点两次), 1-第一张, 2-随机一张, 3-滑到底部最后一张, 4-第9张(不够则下滑寻找，仍不足则选最后一张)
        :return: 成功选中返回 True；mode=0 时选后取消也返回 True
        """
        logger.info(f"{LogIcon.FIND} 准备选择单张图片，模式: {mode}...")
        only_image_check_buttons = self.get_not_media_check_button()
        if not only_image_check_buttons or len(only_image_check_buttons) == 0:
            logger.error(f"{LogIcon.FAIL} 当前相册没有找到任何纯图片的勾选按钮")
            raise NoSuchElementException("当前相册为空或未检测到可用图片，请确保设备里有照片")

        if mode == 0:
            # 选择第一张后再点击取消，模拟"反悔"场景
            logger.info(f"{LogIcon.SUCCESS} 准备选中第一张图片...")
            only_image_check_buttons[0].click()
            logger.info(f"{LogIcon.SUCCESS} 选中第一张图片完成")
            time.sleep(0.3)
            logger.info(f"{LogIcon.SUCCESS} 准备再次点击取消勾选，模拟选后反悔...")
            only_image_check_buttons[0].click()
            logger.info(f"{LogIcon.SUCCESS} 再次点击取消勾选完成")
            return True
        elif mode == 1:
            logger.info(f"{LogIcon.SUCCESS} 准备选中相册中的第一张纯图片...")
            only_image_check_buttons[0].click()
            logger.info(f"{LogIcon.SUCCESS} 成功选中相册中的第一张纯图片")
            return True
        elif mode == 2:
            idx = random.randint(0, len(only_image_check_buttons) - 1)
            logger.info(f"{LogIcon.SUCCESS} 准备随机选中当前视图中的第 {idx + 1} 张纯图片...")
            only_image_check_buttons[idx].click()
            logger.info(f"{LogIcon.SUCCESS} 成功随机选中当前视图中的第 {idx + 1} 张纯图片")
            return True
        elif mode == 3:
            # 快速滑到底部，重新获取元素列表后选中末尾那张
            logger.info(f"{LogIcon.ACTION} 执行快速滑动到底部...")
            self.swipe_page_quickly(slid_type='up', duration=300)
            time.sleep(0.5)
            only_image_check_buttons = self.get_not_media_check_button()
            if not only_image_check_buttons or len(only_image_check_buttons) == 0:
                logger.error(f"{LogIcon.FAIL} 滑到底部后仍未找到可选图片")
                raise NoSuchElementException("滑到底部后相册为空")
            logger.info(f"{LogIcon.SUCCESS} 准备选中末尾纯图片...")
            only_image_check_buttons[-1].click()
            logger.info(f"{LogIcon.SUCCESS} 成功滑到底部并选中最后一张纯图片")
            return True
        elif mode == 4:
            # 尝试选中第 9 张纯图片，当前页面不够则下滑继续累积查找
            target_index = 8  # 第 9 张，0-indexed
            seen_count = len(only_image_check_buttons)
            max_swipe = 5  # 最多下滑 5 次，防止无限循环
            swipe_times = 0

            while seen_count <= target_index and swipe_times < max_swipe:
                logger.info(f"{LogIcon.FIND} 当前可见纯图片 {seen_count} 张，不足 {target_index + 1} 张，第 {swipe_times + 1} 次下滑")
                self.swipe_page(slid_type='up', duration=300)
                time.sleep(0.5)
                only_image_check_buttons = self.get_not_media_check_button()
                seen_count = len(only_image_check_buttons) if only_image_check_buttons else 0
                swipe_times += 1

            if not only_image_check_buttons or len(only_image_check_buttons) == 0:
                raise NoSuchElementException("下滑多次后仍未找到任何可选纯图片")

            if len(only_image_check_buttons) > target_index:
                logger.info(f"{LogIcon.SUCCESS} 准备选中第 {target_index + 1} 张纯图片...")
                only_image_check_buttons[target_index].click()
                logger.info(f"{LogIcon.SUCCESS} 成功选中第 {target_index + 1} 张纯图片")
            else:
                # 图片总数不足 9 张，回退选最后一张
                logger.warning(f"{LogIcon.WARN} 纯图片总数仅 {len(only_image_check_buttons)} 张，不足 9 张，准备选中最后一张...")
                only_image_check_buttons[-1].click()
                logger.warning(f"{LogIcon.WARN} 纯图片总数仅 {len(only_image_check_buttons)} 张，不足 9 张，已回退选中最后一张")
            return True
        else:
            raise ValueError(f"✖️ 不支持的单选模式: {mode}，可选值为 0/1/2/3/4")

    # 在相册网格中连续勾选多张纯图片进行发送。
    def select_multiple_images(self, count: int = 3, max_limit: int = 9, max_swipes: int = 10) -> tuple[int, str]:
        """
        在相册网格中连续勾选多张纯图片（极速流水线版，内建零开销物理触底探测）
        :param count: 计划勾选张数
        :param max_limit: 单次最多可选张数（默认 9 张）
        :param max_swipes: 可用于补齐数量的最大下滑次数（默认 10 次）
        :return: (实际成功勾选张数, 超限弹窗 Toast 内容)
        """
        logger.info(f"{LogIcon.ACTION} [Fast-Select] 启动极速流水线选图: 计划勾选 {count} 张 (上限 {max_limit} 张)")
        target_count = count
        selected_count = self.get_selected_image_count(raise_exception=False)
        full_toast = ""
        last_bottom_fingerprint = None  # 记录末项物理指纹用于触底判定

        for swipe_index in range(max_swipes + 1):
            if selected_count >= target_count:
                logger.info(f"{LogIcon.FIND} 已达到目标勾选数量: {target_count}")
                break

            check_buttons = self.get_not_video_check_button()
            if not check_buttons:
                logger.warning(f"{LogIcon.WARN} 当前页未找到可勾选的图片按钮")
                break

            # 🌟 零开销触底探测：比对末尾元素物理坐标，若滑动前后未发生任何位移，说明已达相册最底部
            try:
                current_bottom_fingerprint = (check_buttons[-1].rect['x'], check_buttons[-1].rect['y'])
            except Exception:
                current_bottom_fingerprint = None

            if swipe_index > 0 and current_bottom_fingerprint and current_bottom_fingerprint == last_bottom_fingerprint:
                logger.warning(f"{LogIcon.WARN} [Fast-Select] 探测到相册列表物理触底（无更多新图片），已选 {selected_count} 张，提前终止")
                break
            last_bottom_fingerprint = current_bottom_fingerprint

            need = target_count - selected_count
            # 过滤掉当前已经选中的按钮（带有选中数字文本）
            unselected_buttons = []
            for btn in check_buttons:
                try:
                    btn_text = btn.text or btn.get_attribute('text') or ""
                    if not btn_text.isdigit():
                        unselected_buttons.append(btn)
                except Exception:
                    unselected_buttons.append(btn)

            if not unselected_buttons:
                logger.info(f"{LogIcon.FIND} 当前屏可见图片已全部被勾选，需翻页寻找更多未选图片")
            else:
                batch_to_click = unselected_buttons[:need]
                logger.info(f"{LogIcon.ACTION} [Fast-Select] 第 {swipe_index} 轮: 尚缺 {need} 张，流水线批量点击当前屏 {len(batch_to_click)} 个按钮...")

                for btn in batch_to_click:
                    try:
                        # 处理超过上限的阻断弹窗（如勾选第 10 张）
                        if selected_count >= max_limit and target_count > max_limit:
                            logger.info(f"{LogIcon.WARN} 尝试点击第 {selected_count + 1} 张图片以触发上限弹窗")
                            btn.click()
                            time.sleep(0.3)
                            full_toast = self.get_toast_content()
                            self.click_ok_button()
                            selected_count = max_limit
                            target_count = max_limit
                            break

                        logger.info(f"{LogIcon.ACTION} 准备点击图片勾选框...")
                        btn.click()
                        time.sleep(0.05)
                        selected_count += 1
                    except Exception as e:
                        logger.warning(f"{LogIcon.WARN} 点击图片勾选按钮异常: {e}")

                # 批处理点击完成后，单次从底部读取实际已选数量进行同步校准
                actual_count = self.get_selected_image_count(raise_exception=False)
                if actual_count > 0:
                    selected_count = actual_count
                logger.info(f"{LogIcon.ACTION} [Fast-Select] 当前已选进度校准: {selected_count}/{target_count}")

            if selected_count >= target_count:
                logger.info(f"{LogIcon.FIND} 已达到目标勾选数量: {target_count}")
                break

            # 仍未满足且未达最大滑动次数，平滑下滑一屏继续寻找
            if swipe_index < max_swipes:
                logger.info(f"{LogIcon.ACTION} [Fast-Select] 当前数量未达标({selected_count}/{target_count})，下滑相册翻页...")
                self.swipe_page(slid_type='up', duration=300)
                time.sleep(0.3)

        logger.info(f"{LogIcon.SUCCESS} [Fast-Select] 批量选图完成: 目标 {count} 张，实际选中 {selected_count} 张")
        return selected_count, full_toast

    # 判断当前是否已进入预览页
    def is_in_preview_mode(self) -> bool:
        """判断当前是否已进入预览页"""
        logger.info(f"{LogIcon.FIND} 判断当前是否已进入预览页...")
        is_preview = self.find_element(ChatImageLocator.PHOTO_PREVIEW_CHECK_BOX, timeout=2, raise_exception=False) is not None
        logger.info(f"{LogIcon.SUCCESS} 判断预览页状态: {'进入成功' if is_preview else '未进入'}")
        return is_preview

    # 获取预览页抗噪指纹
    def get_preview_signature(self) -> str:
        """
        获取预览页图片抗噪指纹。
        使用 dHash 自动提取中心 50% 纯净区域，精准避开顶部状态栏/页码与底部操作栏的系统噪音。
        """
        logger.info(f"{LogIcon.FIND} 正在计算预览页抗噪指纹...")
        # 定义绝对居中对称的安全区域（水平居中 60%，垂直居中 50%）
        size = self.driver.get_window_size()
        w, h = size['width'], size['height']
        rect = {
            'x': int(w * 0.2), 
            'y': int(h * 0.25), 
            'width': int(w * 0.6), 
            'height': int(h * 0.5)
        }
        safe_rect = CropRect.from_rect_dict(rect)
        
        # 直接一键获取 dHash 签名
        image_hash = ScreenshotUtils.dhash_auto(self.driver, rect=safe_rect)
        logger.info(f"{LogIcon.FIND} ♏ 获取预览页指纹(dHash/Center): {image_hash}")
        return image_hash

    # 预览页左滑查看下一张图片
    def swipe_preview_left(self) -> None:
        """预览页左滑查看下一张图片"""
        logger.info(f"{LogIcon.ACTION} 执行预览页左滑查看下一张图片...")
        self.swipe_page(slid_type='left', duration=400)
        time.sleep(0.5)

    # 预览页右滑返回上一张图片
    def swipe_preview_right(self) -> None:
        """预览页右滑返回上一张图片"""
        logger.info(f"{LogIcon.ACTION} 执行预览页右滑返回上一张图片...")
        self.swipe_page(slid_type='right', duration=400)
        time.sleep(0.5)
    
    # 点击最后一张发送的图片
    def click_last_sent_image(self) -> None:
        """
        点击最后一张发送的图片
        """
        logger.info(f"{LogIcon.FIND} 检索最后一张发送的图片...")
        image_elems = self.get_message_elements('image', side='sent')
        if not image_elems:
            raise NoSuchElementException("未找到发送的图片")
        logger.info(f"{LogIcon.ACTION} 准备点击最后一张发送的图片, 进行预览验证...")
        image_elems[-1].click()
        logger.info(f"{LogIcon.ACTION} 点击最后一张发送的图片完成")
        time.sleep(0.5)
