import random
import time
from typing import List, Tuple
from selenium.webdriver.remote.webelement import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from common.base_page import BasePage
from core.logger_utils import logger
from locators.common.album_locator import CommonAlbumLocator


class CommonAlbumPage(BasePage):
    """系统相册与图片/视频选择的通用页面操作类 (可用于个人头像、群头像、聊天发图、发朋友圈等)"""

    # 相册-获取当前屏幕显示的所有相册照片/视频缩略图元素列表
    def get_album_images(self) -> List[WebElement]:
        """
        获取当前屏幕显示的所有相册照片/视频缩略图元素列表
        Returns:
            List[WebElement]: 图片元素列表
        """
        images = self.find_elements(CommonAlbumLocator.PHOTO_ITEM, timeout=3, expect_missing=True)
        logger.info(f"📸 [CommonAlbumPage] 获取到相册图片数量: {len(images)}")
        return images if images else []

    # 相册-获取当前已选中的图片数量
    def get_selected_count(self) -> int:
        """
        获取当前已选中的图片数量
        Returns:
            int: 选中的数量
        """
        if self.is_element_exist(CommonAlbumLocator.PHOTO_SELECTED_COUNT_TEXT, timeout=2):
            text = self.get_attribute(CommonAlbumLocator.PHOTO_SELECTED_COUNT_TEXT, "text")
            try:
                count = int(text)
                logger.info(f"📊 [CommonAlbumPage] 当前已选图片数量: {count}")
                return count
            except ValueError:
                pass
        return 0

    # 相册-按照索引直接点击选择相册中的某张图片（点击图片本身会进入大图预览或裁剪）
    def click_album_image_by_index(self, index: int = 0) -> None:
        """
        按照索引直接点击选择相册中的某张图片（点击图片本身会进入大图预览或裁剪）
        Args:
            index: 图片索引，0 为第一张
        """
        logger.info(f"📸 [CommonAlbumPage] 准备点击相册中的第 {index + 1} 张图片")
        images = self.get_album_images()
        if not images:
            raise RuntimeError("❌ [CommonAlbumPage] 未能在相册中获取到任何图片元素！")
        if abs(index) >= len(images):
            logger.warning(f"⚠️ [CommonAlbumPage] 索引 {index} 溢出，降级点击第一张图片")
            index = 0
        logger.info(f"✅ [CommonAlbumPage] 执行点击相册第 {index + 1} 张图片")
        images[index].click()
        time.sleep(1)

    # 相册-按照索引点击勾选按钮（即数字圈，用于多图选择发送）
    def click_photo_checkbox_by_index(self, index: int = 0) -> None:
        """
        按照索引点击勾选按钮（即数字圈，用于多图选择发送）
        Args:
            index: 图片索引，0 为第一张
        """
        logger.info(f"⚙️ [CommonAlbumPage] 准备勾选相册中的第 {index + 1} 张图片")
        locator = CommonAlbumLocator.PHOTO_CHECK_BUTTON
        if self.is_element_exist(CommonAlbumLocator.PHOTO_CHECK_BUTTON_CONTAINER, timeout=1):
            locator = CommonAlbumLocator.PHOTO_CHECK_BUTTON_CONTAINER
            
        check_btns = self.find_elements(locator, timeout=2, expect_missing=True)
        if not check_btns:
            raise RuntimeError("❌ [CommonAlbumPage] 未能在相册中找到任何勾选数字圈！")
            
        if abs(index) >= len(check_btns):
            logger.warning(f"⚠️ [CommonAlbumPage] 勾选索引 {index} 溢出，降级勾选第一张")
            index = 0
        logger.info(f"✅ [CommonAlbumPage] 执行勾选相册第 {index + 1} 张图片")
        check_btns[index].click()
        time.sleep(0.5)

    # 相册-使用策略模式在相册中选取并点击图片
    def select_image_by_strategy(self, strategy: str = "first") -> None:
        """
        使用策略模式在相册中选取并点击图片
        Args:
            strategy: "first" (第一张) / "second" (第二张) / "random" (随机) / "current_last" (当前屏最后一张) / "absolute_last" (滑动到底部最后一张)
        """
        logger.info(f"📸 [CommonAlbumPage] 准备选取相册图片，选图策略为: [{strategy}]")
        
        if strategy == "absolute_last":
            self.swipe_page_quickly(slid_type='up', max_swipes=5)
            time.sleep(0.5)

        images = self.get_album_images()
        if not images:
            raise RuntimeError("❌ [CommonAlbumPage] 选图失败，相册中没有可点击的图片！")

        if strategy == "first":
            logger.info("✅ [CommonAlbumPage] 点击第 1 张图片")
            images[0].click()
        elif strategy == "second":
            if len(images) < 2:
                logger.warning("相册图片不足 2 张，降级点击第 1 张")
                images[0].click()
            else:
                logger.info("✅ [CommonAlbumPage] 点击第 2 张图片")
                images[1].click()
        elif strategy == "random":
            target = random.choice(images)
            logger.info("✅ [CommonAlbumPage] 随机点击图片")
            target.click()
        elif strategy in ["current_last", "absolute_last"]:
            logger.info(f"✅ [CommonAlbumPage] 点击最后一张图片 (策略: {strategy})")
            images[-1].click()
        else:
            raise ValueError(f"❌ [CommonAlbumPage] 未知的选图策略: {strategy}")
        
        time.sleep(1)

    # 相册-控制是否勾选“原图”发送
    def toggle_original_image(self, status: bool = True) -> None:
        """
        控制是否勾选“原图”发送
        Args:
            status: True 表示勾选，False 表示取消勾选
        """
        logger.info(f"⚙️ [CommonAlbumPage] 准备切换“原图”状态为: {status}")
        if not self.is_element_exist(CommonAlbumLocator.PHOTO_ORIGINAL_TEXT, timeout=2):
            logger.warning("⚠️ [CommonAlbumPage] 当前页面不存在“原图”勾选控件，跳过设置")
            return
            
        current_status = str(self.get_attribute(CommonAlbumLocator.PHOTO_ORIGINAL_TEXT, "checked")).lower() == 'true'
        if current_status != status:
            logger.info(f"🔄 [CommonAlbumPage] 执行切换“原图”勾选状态为: {status}")
            self.click(CommonAlbumLocator.PHOTO_ORIGINAL_TEXT)
        else:
            logger.info(f"✏️ [CommonAlbumPage] “原图”状态已为 {status}，无需重复点击")
        time.sleep(0.5)

    # 相册-点击右下角“发送/完成”按钮提交选择
    def click_send_or_complete(self) -> None:
        """ 点击右下角“发送/完成”按钮提交选择 """
        logger.info("💾 [CommonAlbumPage] 点击【发送/完成】按钮")
        locator = CommonAlbumLocator.PHOTO_SEND_TEXT
        if not self.is_element_exist(locator, timeout=2):
            locator = CommonAlbumLocator.PHOTO_SEND_CONTAINER

        if self.is_element_exist(locator, timeout=1):
            self.click(locator)
        else:
            raise RuntimeError("❌ [CommonAlbumPage] 未找到【发送/完成】按钮")
        time.sleep(1)

    # 相册-点击左下角预览
    def click_preview_button(self) -> None:
        """ 点击左下角“预览”进入预览页 """
        logger.info("🔍 [CommonAlbumPage] 点击左下角【预览】")
        self.click(CommonAlbumLocator.PHOTO_PREVIEW_TEXT, timeout=2)
        time.sleep(1)

    # 相册-执行图片裁剪确认或保存图片
    def confirm_crop_action(self) -> None:
        """ 执行图片裁剪确认或保存图片 """
        logger.info("✂️ [CommonAlbumPage] 确认图片裁剪或保存图片")
        
        # 1. 优先尝试点击右上角完成/操作按钮 (FB_ACTION)
        if self.is_element_exist(CommonAlbumLocator.FB_ACTION, timeout=2):
            logger.info("✅ [CommonAlbumPage] 点击右上角完成/操作按钮")
            self.click(CommonAlbumLocator.FB_ACTION)
        else:
            # 2. 兜底尝试点击系统或第三方裁剪库的确认按钮
            system_crop = (AppiumBy.XPATH, "//*[@text='确定' or @text='完成' or @text='保存' or contains(@resource-id, 'ok') or contains(@resource-id, 'confirm') or contains(@resource-id, 'save')]")
            if self.is_element_exist(system_crop, timeout=2):
                logger.info("✅ [CommonAlbumPage] 点击系统裁剪确认按钮")
                self.click(system_crop)
            else:
                logger.warning("⚠️ [CommonAlbumPage] 未检测到明显的裁剪确认或保存按钮，跳过直接进行下一步")
        time.sleep(1)

    # 相册-取消图片裁剪操作
    def cancel_crop_action(self) -> None:
        """ 取消图片裁剪操作 """
        logger.info("🔙 [CommonAlbumPage] 准备取消图片裁剪")
        system_cancel = (AppiumBy.XPATH, "//*[@text='取消' or contains(@resource-id, 'cancel')]")
        if self.is_element_exist(system_cancel, timeout=2):
            logger.info("✅ [CommonAlbumPage] 点击裁剪取消按钮")
            self.click(system_cancel)
        else:
            logger.info("✅ [CommonAlbumPage] 未找到取消按钮，执行物理 Back 返回")
            self.back()
        time.sleep(1)

    # 相册-在相册图片选择界面点击取消返回
    def click_album_cancel(self) -> None:
        """ 在相册图片选择界面点击取消返回 """
        logger.info("🔙 [CommonAlbumPage] 点击取消/返回退出相册选择")
        if self.is_element_exist(CommonAlbumLocator.TOP_BACK_BUTTON, timeout=2):
            logger.info("✅ [CommonAlbumPage] 点击左上角返回按钮")
            self.click(CommonAlbumLocator.TOP_BACK_BUTTON)
        elif self.is_element_exist(CommonAlbumLocator.IV_BACK, timeout=2):
            logger.info("✅ [CommonAlbumPage] 点击通用返回按钮")
            self.click(CommonAlbumLocator.IV_BACK)
        else:
            logger.info("✅ [CommonAlbumPage] 执行物理 Back 返回")
            self.back()
        time.sleep(1)

    # 相册-处理超过张数限制（例如选择超过10张）的弹窗警告
    def handle_overlimit_dialog(self) -> Tuple[bool, str]:
        """
        处理超过张数限制（例如选择超过10张）的弹窗警告
        Returns:
            Tuple[bool, str]: (是否成功拦截并点击确认, 弹窗提示信息)
        """
        logger.info("⚙️ [CommonAlbumPage] 检测是否存在限额弹窗警告")
        if self.is_element_exist(CommonAlbumLocator.TV_CONTENT, timeout=2):
            msg = self.get_attribute(CommonAlbumLocator.TV_CONTENT, "text")
            logger.warning(f"⚠️ [CommonAlbumPage] 检测到限额弹窗警告: '{msg}'")
            logger.info("✅ [CommonAlbumPage] 点击限额弹窗确认按钮")
            self.click(CommonAlbumLocator.BTN_OK)
            return True, msg
        return False, ""

    # ==================================================================================================================
    # 定向过滤媒体选择优化方法
    # ==================================================================================================================
    # 相册-仅获取相册中的纯图片元素列表
    def get_album_only_images(self) -> List[WebElement]:
        """ 仅获取相册中的纯图片元素列表 """
        images = self.find_elements(CommonAlbumLocator.PHOTO_ONLY_IMAGE_ITEM, timeout=3, expect_missing=True)
        logger.info(f"📸 [CommonAlbumPage] 获取到仅图片元素数量: {len(images)}")
        return images if images else []

    # 相册-仅获取相册中的视频元素列表
    def get_album_only_videos(self) -> List[WebElement]:
        """ 仅获取相册中的视频元素列表 """
        videos = self.find_elements(CommonAlbumLocator.PHOTO_ONLY_VIDEO_ITEM, timeout=3, expect_missing=True)
        logger.info(f"🎥 [CommonAlbumPage] 获取到仅视频元素数量: {len(videos)}")
        return videos if videos else []

    # 相册-仅勾选纯图片按钮
    def click_only_photo_checkbox_by_index(self, index: int = 0) -> None:
        """
        按照索引仅勾选纯图片按钮
        Args:
            index: 纯图片索引，0 为第一张
        """
        logger.info(f"⚙️ [CommonAlbumPage] 准备勾选纯图片第 {index + 1} 张")
        check_btns = self.find_elements(CommonAlbumLocator.PHOTO_CHECK_BUTTON_NOT_MEDIA, timeout=3, expect_missing=True)
        if not check_btns:
            raise RuntimeError("❌ [CommonAlbumPage] 未能在相册中找到任何仅纯图片勾选圈！")
            
        if abs(index) >= len(check_btns):
            logger.warning(f"⚠️ [CommonAlbumPage] 勾选仅图片索引 {index} 溢出，降级勾选第一张")
            index = 0
        logger.info(f"✅ [CommonAlbumPage] 执行勾选第 {index + 1} 张纯图片")
        check_btns[index].click()
        time.sleep(0.1)

    # 相册-仅勾选视频按钮
    def click_only_video_checkbox_by_index(self, index: int = 0) -> None:
        """
        按照索引仅勾选视频按钮
        Args:
            index: 视频索引，0 为第一个
        """
        logger.info(f"⚙️ [CommonAlbumPage] 准备勾选视频第 {index + 1} 个")
        check_btns = self.find_elements(CommonAlbumLocator.PHOTO_CHECK_BUTTON_VIDEO, timeout=3, expect_missing=True)
        if not check_btns:
            raise RuntimeError("❌ [CommonAlbumPage] 未能在相册中找到任何仅视频勾选圈！")
            
        if abs(index) >= len(check_btns):
            logger.warning(f"⚠️ [CommonAlbumPage] 勾选仅视频索引 {index} 溢出，降级勾选第一个")
            index = 0
        logger.info(f"✅ [CommonAlbumPage] 执行勾选第 {index + 1} 个视频")
        check_btns[index].click()
        time.sleep(0.1)

    # 相册-勾选不含视频的媒体勾选圈
    def click_photo_checkbox_not_video_by_index(self, index: int = 0) -> None:
        """
        按照索引勾选非视频（包含图片、长图、webp、gif等）的媒体勾选圈
        Args:
            index: 非视频元素索引
        """
        logger.info(f"⚙️ [CommonAlbumPage] 准备勾选非视频媒体第 {index + 1} 个")
        check_btns = self.find_elements(CommonAlbumLocator.PHOTO_CHECK_BUTTON_NOT_VIDEO, timeout=3, expect_missing=True)
        if not check_btns:
            raise RuntimeError("❌ [CommonAlbumPage] 未能在相册中找到任何非视频媒体勾选圈！")
            
        if abs(index) >= len(check_btns):
            logger.warning(f"⚠️ [CommonAlbumPage] 勾选非视频索引 {index} 溢出，降级勾选第一个")
            index = 0
        logger.info(f"✅ [CommonAlbumPage] 执行勾选第 {index + 1} 个非视频媒体")
        check_btns[index].click()
        time.sleep(0.5)

    # 相册-仅勾选长图、webp、gif等勾选圈
    def click_photo_checkbox_long_webp_gif_by_index(self, index: int = 0) -> None:
        """
        按照索引勾选长图、webp、gif等非普通图片的勾选圈
        Args:
            index: 长图/WebP/GIF元素索引
        """
        logger.info(f"⚙️ [CommonAlbumPage] 准备勾选长图/WebP/GIF媒体第 {index + 1} 个")
        check_btns = self.find_elements(CommonAlbumLocator.PHOTO_CHECK_BUTTON_LONG_WEBP_GIF, timeout=3, expect_missing=True)
        if not check_btns:
            raise RuntimeError("❌ [CommonAlbumPage] 未能在相册中找到任何长图/WebP/GIF等特定勾选圈！")
            
        if abs(index) >= len(check_btns):
            logger.warning(f"⚠️ [CommonAlbumPage] 勾选长图/WebP/GIF索引 {index} 溢出，降级勾选第一个")
            index = 0
        logger.info(f"✅ [CommonAlbumPage] 执行勾选第 {index + 1} 个长图/WebP/GIF媒体")
        check_btns[index].click()
        time.sleep(0.5)
