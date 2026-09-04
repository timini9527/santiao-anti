import time
import random
from selenium.common import NoSuchElementException
from common.base_page import BasePage
from core.logger_utils import logger
from appium.webdriver.common.appiumby import AppiumBy
from locators.chat.core.chat_locator import ChatLocator
from locators.chat_options.images.chat_image_locator import ChatImageLocator
from pages.chat.core.chat_page import ChatPage
from utils.cv_recognition.screenshot_utils import ScreenshotUtils, CropRect

class ChatImagePage(ChatPage):
    """聊天面板-相册内部相关操作：从相册选图、预览大图、勾选原图、确认发送等"""

    # 等待图片选择页面加载
    def wait_for_image_page_load(self, timeout: int = 10):
        """等待图片选择页面加载"""
        container = self.find_elements(ChatImageLocator.PHOTO_CONTAINER, timeout=timeout)
        if not container:
            logger.warning("❌ 图片选择页面加载失败")
            return False
        logger.info("✅ 图片选择页面加载成功")
        return True

    # 点击图片图标进入相册
    def click_image_button(self):
        """点击图片按钮进入图片选择页面"""
        self.click(ChatImageLocator.IMAGE_SELECT_ROOT)
        logger.info("🚀 点击图片按钮进入图片选择页面")
    
    # 返回按钮
    def click_back_button(self):
        """点击返回按钮"""
        self.click(ChatImageLocator.TOP_BACK_BUTTON)
        logger.info("🚀 点击返回按钮")
    
    # 标题文本
    def get_title_text(self):
        """获取标题文本"""
        return self.get_attribute(ChatImageLocator.TOP_TITLE_TEXT, 'text')
    
    # 点击标题切换相册分类
    def click_title_to_switch_category(self):
        """点击标题切换相册分类"""
        self.click(ChatImageLocator.TOP_TITLE_TEXT)
        logger.info("🚀 点击标题切换相册分类")
    
    # 展开后的相册分类展示
    def open_category_list(self):
        """展开相册分类列表"""
        category_list = self.find_elements(ChatImageLocator.TOP_CATEGORY_TEXT)
        if not category_list or len(category_list) == 0:
            logger.error("没有找到相册分类列表")
            raise NoSuchElementException("没有找到相册分类列表")
        return category_list
    
    # 获取 PHOTO_CONTAINER 的容器
    def get_photo_container(self):
        """获取 PHOTO_CONTAINER 整个相册 的容器"""
        container = self.find_element(ChatImageLocator.PHOTO_CONTAINER, timeout=3)
        logger.info(" PHOTO_CONTAINER 整个相册 的容器")
        return container
        
    # 获取所有图片
    def get_all_image_items(self):
        """获取所有图片"""
        items = self.find_elements(ChatImageLocator.PHOTO_ITEM, timeout=3)
        logger.info(f"获取所有图片，共{len(items)}张")
        return items
    
    # 获取所有图片的勾选按钮
    def get_all_image_check_button(self):
        """获取所有图片的勾选按钮"""
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON, timeout=3)
        logger.info(f"获取所有图片的勾选按钮，共{len(buttons)}个")
        return buttons
    
    # 获取 仅纯图片(png/jpg) 不包含其他格式图片
    def get_only_image_items(self):
        """获取仅纯图片(png/jpg) 不包含其他格式图片"""
        items = self.find_elements(ChatImageLocator.PHOTO_ONLY_IMAGE_ITEM, timeout=3)
        logger.info(f"获取仅纯图片(png/jpg) 不包含其他格式图片，共{len(items)}张")
        return items
    
    # 获取仅不包含视频的元素
    def get_not_video_items(self):
        """获取仅不包含视频的元素"""
        items = self.find_elements(ChatImageLocator.PHOTO_NOT_VIDEO_ITEM, timeout=3)
        logger.info(f"获取仅不包含视频的元素，共{len(items)}张")
        return items

    # 获取仅不包含视频的勾选按钮
    def get_not_video_check_button(self):
        """获取仅不包含视频的勾选按钮"""
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON_NOT_VIDEO, timeout=3)
        logger.info(f"获取仅不包含视频的勾选按钮，共{len(buttons)}个")
        return buttons
    
    # 获取不包含视频、长图、webp、gif等媒体文件的勾选按钮
    def get_not_media_check_button(self):
        """获取不包含视频、长图、webp、gif等媒体文件的勾选按钮"""
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON_NOT_MEDIA, timeout=3)
        logger.info(f"获取不包含视频、长图、webp、gif等媒体文件的勾选按钮，共{len(buttons)}个")
        return buttons

    # 获取仅长图、webp、gif
    def get_only_long_image_items(self):
        """获取仅长图、webp、gif"""
        items = self.find_elements(ChatImageLocator.PHOTO_IMAGE_LONG_WEBP_GIF_ITEM, timeout=3)
        logger.info(f"获取仅长图、webp、gif，共{len(items)}张")
        return items

    # 获取仅长图、webp、gif的勾选按钮
    def get_only_long_image_check_button(self):
        """获取仅长图的勾选按钮"""
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON_LONG_WEBP_GIF, timeout=3)
        logger.info(f"获取仅长图、webp、gif的勾选按钮，共{len(buttons)}个")
        return buttons

    # 获取 仅视频
    def get_only_video_items(self):
        """获取仅视频"""
        items = self.find_elements(ChatImageLocator.PHOTO_ONLY_VIDEO_ITEM, timeout=3)
        logger.info(f"获取仅视频，共{len(items)}张")
        return items

    # 获取仅视频的勾选按钮
    def get_only_video_check_button(self, raise_exception=True):
        """获取仅视频的勾选按钮"""
        buttons = self.find_elements(ChatImageLocator.PHOTO_CHECK_BUTTON_VIDEO, timeout=3, raise_exception=raise_exception)
        logger.info(f"获取仅视频的勾选按钮，共{len(buttons)}个")
        return buttons
    
    # 点击预览按钮
    def click_preview_button(self):
        """点击预览按钮"""
        self.click(ChatImageLocator.PHOTO_PREVIEW_TEXT)
        logger.info("🚀 点击左下角【预览】按钮，跳转至大图预览全屏页")
        time.sleep(0.5)
    
    # 点击原图按钮
    def click_original_image_button(self):
        """点击原图按钮"""
        self.click(ChatImageLocator.PHOTO_ORIGINAL_TEXT)
        logger.info("🚀 点击相片底部的【原图】字样，勾选无损发送选项")
    
    # 获取原图按钮状态
    def get_original_image_button_status(self):
        """获取原图按钮状态"""
        status = self.get_attribute(ChatImageLocator.PHOTO_ORIGINAL_TEXT, 'checked')
        logger.info(f"原图按钮状态: {status}")
        return status
    
    # 获取发送前所勾选的图片/视频数量
    def get_selected_image_count(self, raise_exception=True):
        """获取发送前所勾选的图片数量"""
        selected_text = self.get_attribute(ChatImageLocator.PHOTO_SELECTED_COUNT_TEXT, 'text', timeout=2, raise_exception=raise_exception)
        if selected_text and str(selected_text).isdigit():
            logger.info(f"✅ 已勾选 {selected_text} 张图片")
            return int(selected_text)
        logger.info(f"未获取到已勾选图片数量")
        return 0
    
    # 点击发送按钮
    def click_send_button(self):
        """点击发送按钮"""
        self.click(ChatImageLocator.PHOTO_SEND_TEXT)
        logger.info("✅ 敲击了【确定发送】按钮，正在将位图切片推入聊天流...")
        time.sleep(0.5)
        
    # 预览界面 点击勾选大图按钮
    def click_preview_check_button(self):
        """点击预览界面勾选大图按钮"""
        self.click(ChatImageLocator.PHOTO_PREVIEW_CHECK_BOX)
        logger.info("✅ 点击预览界面勾选大图按钮")
    
    # 点击底部原图复选框
    def click_original_image_checkbox(self):
        """点击底部原图复选框，确保照片原画质高精度传输"""
        self.click(ChatImageLocator.PHOTO_ORIGINAL_TEXT)
        logger.info("✅ 点击相片底部的【原图】字样，勾选无损发送选项")

    # 点击发送按钮（有角标）
    def click_send_image(self):
        """点击相册界面或预览界面最右下角的『发送』大按钮"""
        # 发送前防御性校验：只有勾选了图片，右上角有角标时发送按钮才有效亮起
        check_boxs = self.find_elements(ChatImageLocator.PHOTO_SELECTED_COUNT_TEXT, timeout=2)
        if not check_boxs:
            logger.error("✖️ 发送键呈灰色阻断，因为没有检测到任何已选中的角标数字 (可能刚选的图片太小被你拦截了或者是空窗)")
            raise NoSuchElementException("未选中图片时发送按钮物理不可点")
            
        self.click_send_button()
        time.sleep(0.5)

    # 选中超过10张的弹窗 - 获取 Toast
    def get_toast_content(self):
        """获取Toast内容"""
        return self.get_attribute(ChatImageLocator.TV_CONTENT, 'text')

    # 选中超过10张的弹窗 - 点击确认按钮
    def click_ok_button(self):
        """点击确认按钮"""
        self.click(ChatImageLocator.BTN_OK, force_wait=True)
        logger.info("✅ 选中超过10张的弹窗 - 点击确认按钮")

    # 打开面板-进入相册
    def open_panel_to_album(self):
        """点击图片按钮进入图片选择页面"""
        self.click_add_button()
        self.click_image_button()
    
    # 校验默认页面加载状态
    def verify_default_page_load_status(self):
        """校验默认页面加载状态"""
        original_status = self.get_original_image_button_status()
        selected_count = self.get_selected_image_count(raise_exception=False)
        if original_status == 'false' and selected_count == 0:
            logger.info("✔️ 默认页面加载状态正常")
            self.click_back_button()
            return True
        else:
            logger.error("✖️ 默认页面加载状态异常")
            return False

    # 校验底部已选数量是否符合预期
    def verify_selected_count(self, expected_count: int) -> bool:
        """校验底部已选数量是否符合预期"""
        current_count = self.get_selected_image_count()
        is_match = current_count == expected_count
        logger.info(f"已选数量校验: current={current_count}, expected={expected_count}, result={is_match}")
        return is_match

    # 选择单张图片
    def select_single_image(self, mode: int = 1) -> bool:
        """
        在当前的相册网格页面选择单张图片
        :param mode: 0-选择后取消(点两次), 1-第一张, 2-随机一张, 3-滑到底部最后一张, 4-第9张(不够则下滑寻找，仍不足则选最后一张)
        :return: 成功选中返回 True；mode=0 时选后取消也返回 True
        """
        only_image_check_buttons = self.get_not_media_check_button()
        if not only_image_check_buttons or len(only_image_check_buttons) == 0:
            logger.error("✖️ 当前相册没有找到任何纯图片的勾选按钮")
            raise NoSuchElementException("当前相册为空或未检测到可用图片，请确保设备里有照片")

        if mode == 0:
            # 选择第一张后再点击取消，模拟"反悔"场景
            only_image_check_buttons[0].click()
            logger.info("✔️ 选中第一张图片")
            time.sleep(0.3)
            only_image_check_buttons[0].click()
            logger.info("✔️ 再次点击取消勾选，模拟选后反悔")
            return True
        elif mode == 1:
            only_image_check_buttons[0].click()
            logger.info("✔️ 成功选中相册中的第一张纯图片")
            return True
        elif mode == 2:
            idx = random.randint(0, len(only_image_check_buttons) - 1)
            only_image_check_buttons[idx].click()
            logger.info(f"✔️ 成功随机选中当前视图中的第 {idx + 1} 张纯图片")
            return True
        elif mode == 3:
            # 快速滑到底部，重新获取元素列表后选中末尾那张
            self.swipe_page_quickly(slid_type='up', duration=300)
            time.sleep(0.5)
            only_image_check_buttons = self.get_not_media_check_button()
            if not only_image_check_buttons or len(only_image_check_buttons) == 0:
                logger.error("✖️ 滑到底部后仍未找到可选图片")
                raise NoSuchElementException("滑到底部后相册为空")
            only_image_check_buttons[-1].click()
            logger.info("✔️ 成功滑到底部并选中最后一张纯图片")
            return True
        elif mode == 4:
            # 尝试选中第 9 张纯图片，当前页面不够则下滑继续累积查找
            target_index = 8  # 第 9 张，0-indexed
            seen_count = len(only_image_check_buttons)
            max_swipe = 5  # 最多下滑 5 次，防止无限循环
            swipe_times = 0

            while seen_count <= target_index and swipe_times < max_swipe:
                logger.info(f"当前可见纯图片 {seen_count} 张，不足 {target_index + 1} 张，第 {swipe_times + 1} 次下滑")
                self.swipe_page(slid_type='up', duration=300)
                time.sleep(0.5)
                only_image_check_buttons = self.get_not_media_check_button()
                seen_count = len(only_image_check_buttons) if only_image_check_buttons else 0
                swipe_times += 1

            if not only_image_check_buttons or len(only_image_check_buttons) == 0:
                raise NoSuchElementException("下滑多次后仍未找到任何可选纯图片")

            if len(only_image_check_buttons) > target_index:
                only_image_check_buttons[target_index].click()
                logger.info(f"✔️ 成功选中第 {target_index + 1} 张纯图片")
            else:
                # 图片总数不足 9 张，回退选最后一张
                only_image_check_buttons[-1].click()
                logger.warning(f"⚠️ 纯图片总数仅 {len(only_image_check_buttons)} 张，不足 9 张，已回退选中最后一张")
            return True
        else:
            raise ValueError(f"✖️ 不支持的单选模式: {mode}，可选值为 0/1/2/3/4")

    # 在相册网格中连续勾选多张纯图片进行发送。
    def select_multiple_images(self, count: int = 3, max_limit: int = 9, max_swipes: int = 10) -> tuple[int, str]:
        """
        在相册网格中连续勾选多张纯图片进行发送。
        :param count: 计划勾选张数
        :param max_limit: 单次最多可选张数（默认 9 张）
        :param max_swipes: 可用于补齐数量的最大下滑次数
        :return: (实际成功勾选张数, 超限弹窗 Toast 内容)
        """
        target_count = count
        selected_count = self.get_selected_image_count(raise_exception=False)
        last_source = ""
        full_toast = ""

        for swipe_index in range(max_swipes + 1):
            if selected_count >= target_count:
                break

            check_buttons = self.get_not_video_check_button()
            if not check_buttons:
                logger.warning("当前页未找到可勾选的图片按钮")
                break

            for button in check_buttons:
                if selected_count >= target_count:
                    logger.info(f"已达到目标勾选数量: {target_count}")
                    break

                before_count = self.get_selected_image_count(raise_exception=False)
                button.click()

                # 处理超过上限的阻断弹窗（如第 10 张）
                if before_count >= max_limit:
                    full_toast = self.get_toast_content()
                    self.click_ok_button()
                    target_count = max_limit
                    break

                after_count = self.get_selected_image_count(raise_exception=False)
                
                # 滑动后若误点到了上一页已勾选的图片导致反选，立即重新点击恢复
                if after_count < before_count:
                    logger.warning("⚠️ 误点了已勾选图片导致取消，重新点击以恢复勾选")
                    button.click()
                    continue

                if after_count > before_count:
                    selected_count = after_count
                    logger.info(f"已勾选图片 {selected_count}/{target_count}")

            if selected_count >= target_count:
                logger.info(f"已达到目标勾选数量: {target_count}")
                break

            is_changed, last_source = self.is_element_source_changed(ChatImageLocator.PHOTO_CONTAINER, last_source)
            if not is_changed:
                logger.warning("相册列表已无更多内容，停止补齐勾选")
                break

            self.swipe_page(slid_type='up', duration=400)
            time.sleep(0.5)
            logger.info(f"批量选图未满目标({selected_count}/{target_count})，第 {swipe_index + 1} 次下滑继续查找")

        logger.info(f"✅ 批量勾选完成，目标 {target_count} 张，实际 {selected_count} 张")
        return selected_count, full_toast

    # 判断当前是否已进入预览页
    def is_in_preview_mode(self) -> bool:
        """判断当前是否已进入预览页"""
        is_preview = self.find_element(ChatImageLocator.PHOTO_PREVIEW_CHECK_BOX, timeout=2, raise_exception=False) is not None
        logger.info(f"✅ 判断预览页状态: {'进入成功' if is_preview else '未进入'}")
        return is_preview

    # 获取预览页抗噪指纹
    def get_preview_signature(self) -> str:
        """
        获取预览页图片抗噪指纹。
        使用 dHash 自动提取中心 50% 纯净区域，精准避开顶部状态栏/页码与底部操作栏的系统噪音。
        """
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
        logger.info(f"♏ 获取预览页指纹(dHash/Center): {image_hash}")
        return image_hash

    # 预览页左滑查看下一张图片
    def swipe_preview_left(self):
        """预览页左滑查看下一张图片"""
        self.swipe_page(slid_type='left', duration=400)
        time.sleep(0.5)

    # 预览页右滑返回上一张图片
    def swipe_preview_right(self):
        """预览页右滑返回上一张图片"""
        self.swipe_page(slid_type='right', duration=400)
        time.sleep(0.5)
    
    # 点击最后一张发送的图片
    def click_last_sent_image(self):
        """
        点击最后一张发送的图片
        """
        image_elems = self.get_message_elements('image', side='sent')
        if not image_elems:
            raise NoSuchElementException("未找到发送的图片")
        image_elems[-1].click()
        logger.info(f"🚀 点击最后一张发送的图片, 进行预览验证")
        time.sleep(0.5)






