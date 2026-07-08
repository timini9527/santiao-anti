import time
from selenium.webdriver.remote.webelement import WebElement
from core.logger_utils import logger
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from locators.groups.setting.general.group_avatar_locator import GroupAvatarLocator
from utils.cv_recognition.screenshot_utils import ScreenshotUtils


class GroupAvatarPage(GroupSettingPage):
    """群头像设置与修改页面操作类"""
    
    # 群头像-等待群头像页面加载完成
    def wait_group_avatar_page_load(self, timeout: int = 5) -> bool:
        """   群头像-等待群头像页面加载完成   """
        state = self.is_element_exist(GroupAvatarLocator.GROUP_HEADER, timeout=timeout)
        if state:
            logger.info("⏳ [Action-GroupAvatarPage] 等待群头像页面加载完成")
        else:
            logger.warning("⚠️ [Action-GroupAvatarPage] 群头像页面加载超时")
        return state

    # 群头像-点击左上角返回键
    def click_back_to_group_setting(self):
        """   群头像-点击左上角返回键   """
        self.click(GroupAvatarLocator.IV_BACK)
        logger.info("🔙 [Action-GroupAvatarPage] 返回到群设置页面")

    # 群头像-点击相册内部左上角返回按钮
    def click_back_to_group_avatar_page(self):
        """   群头像-点击相册内部左上角返回按钮   """
        self.click(GroupAvatarLocator.PS_IV_LEFT_BACK)
        logger.info("🔙 [Action-GroupAvatarPage] 返回到群头像页面")

    # 群头像-点击右上角“完成”按钮（确认）
    def click_confirm_change_group_avatar(self):
        """   群头像-点击右上角“完成”按钮，确认修改群头像   """
        self.click(GroupAvatarLocator.FB_ACTION, timeout=2)
        logger.info("✅ [Action-GroupAvatarPage] 点击右上角【完成】确认群头像修改")

    # 群头像-获取当前群头像的图片哈希值
    def get_group_avatar_hash(self) -> str:
        """
        获取当前群头像的图片哈希值（用于断言修改前后头像是否发生了物理改变）
        Returns:
            str: 图像的 dhash 哈希值，若未找到则返回空字符串
        """
        logger.info("📸 [Action-GroupAvatarPage] 开始获取群头像元素的 dhash 哈希值")
        avatar_ele = self.find_element(GroupAvatarLocator.GROUP_HEADER, timeout=2)
        if not avatar_ele:
            logger.warning("⚠️ [Action-GroupAvatarPage] 未能在页面中找到群头像 ImageView")
            return ""
        try:
            img_hash = ScreenshotUtils.dhash_auto(element=avatar_ele)
            logger.info(f"✅ [Action-GroupAvatarPage] 成功获取群头像 hash: {img_hash}")
            return img_hash
        except Exception as e:
            logger.error(f"❌ [Action-GroupAvatarPage] 获取群头像 hash 出现异常: {e}")
            return ""

    # 群头像-等待选择面板弹窗
    def wait_for_album_dialog(self, timeout: int = 5) -> bool:
        """   群头像-等待选择面板弹窗   """
        state = self.is_element_exist(GroupAvatarLocator.DESIGN_BOTTOM_SHEET, timeout=timeout)
        if state:
            logger.info("⏳ [Action-GroupAvatarPage] 等待选择面板弹窗加载完成")
        else:
            logger.warning("⚠️ [Action-GroupAvatarPage] 选择面板弹窗加载超时")
        return state

    # 群头像-点击拍照
    def click_group_avatar_take_photo(self):
        """   群头像-点击拍照   """
        self.click(GroupAvatarLocator.ACTION_TAKE_PHOTO)
        logger.info("📸 [Action-GroupAvatarPage] 点击拍照")

    # 群头像-点击从相册选择
    def click_group_avatar_pick_gallery(self):
        """   群头像-点击从相册选择   """
        self.click(GroupAvatarLocator.ACTION_PICK_GALLERY)
        logger.info("🖼️ [Action-GroupAvatarPage] 点击从相册选择")

    # 群头像-点击保存图片
    def click_group_avatar_save_image(self):
        """   群头像-点击保存图片   """
        self.click(GroupAvatarLocator.ACTION_SAVE_IMAGE)
        logger.info("💾 [Action-GroupAvatarPage] 点击保存图片")

    # 群头像-点击取消
    def click_group_avatar_cancel(self):
        """   群头像-点击取消   """
        self.click(GroupAvatarLocator.ACTION_CANCEL)
        logger.info("❌ [Action-GroupAvatarPage] 点击取消")

    # 群头像-等待相册选择面板加载完成
    def wait_album_panel_load(self, timeout: int = 5) -> bool:
        """   群头像-等待相册选择面板加载完成   """
        state = self.is_element_exist(GroupAvatarLocator.RECYCLER, timeout=timeout)
        if state:
            logger.info("⏳ [Action-GroupAvatarPage] 等待相册选择面板加载完成")
        else:
            logger.warning("⚠️ [Action-GroupAvatarPage] 相册选择面板加载超时")
        return state

    # 群头像-获取相册页面Item
    def get_album_page_item(self, timeout: int = 5) -> list[WebElement]:
        """   群头像-获取相册页面Item   """
        elements = self.find_elements(GroupAvatarLocator.IMAGE_PICTURE, timeout=timeout)
        if not elements:
            logger.warning("⚠️ [Action-GroupAvatarPage] 未获取到任何相册页面Item")
            return []
        logger.info(f"✅ [Action-GroupAvatarPage] 成功获取 {len(elements)} 个相册页面Item")
        return elements

    # 群头像-选择相册-点击第一张图片
    def click_album_image_by_index(self, index: int = 0):
        """   群头像-选择相册-点击第index张图片，默认第一张   """
        elements = self.get_album_page_item()
        if not elements:
            logger.warning("⚠️ [Action-GroupAvatarPage] 未获取到任何相册页面Item")
            return
        if index >= len(elements):
            logger.warning(f"⚠️ [Action-GroupAvatarPage] 索引越界，当前共 {len(elements)} 张图片，请求索引 {index}")
            return
        elements[index].click()
        logger.info(f"🖼️ [Action-GroupAvatarPage] 点击第 {index + 1} 张图片")


    # 群头像-拍照内部
    def wait_capture_page_load(self, timeout: int = 5) -> bool:
        """   群头像-拍照内部-等待拍照页面加载完成   """
        state = self.is_element_exist(GroupAvatarLocator.BTN_CAPTURE, timeout=timeout)
        if state:
            logger.info("⏳ [Action-GroupAvatarPage] 等待拍照页面加载完成")
        else:
            logger.warning("⚠️ [Action-GroupAvatarPage] 拍照页面加载超时")
        return state

    # 群头像-拍照内部-点击拍照按钮
    def click_capture_photo(self):
        """   群头像-拍照内部-点击拍照按钮   """
        self.click(GroupAvatarLocator.BTN_CAPTURE)
        logger.info("📸 [Action-GroupAvatarPage] 点击拍照按钮")
    
    # 群头像-拍照内部-点击确认按钮
    def click_confirm(self):
        """   群头像-拍照内部-点击确认按钮   """
        self.click(GroupAvatarLocator.IV_CONFIRM)
        logger.info("✅ [Action-GroupAvatarPage] 点击确认按钮")
    
    # 群头像-拍照内部-点击取消按钮
    def click_cancel(self):
        """   群头像-拍照内部-点击取消按钮   """
        self.click(GroupAvatarLocator.IV_CANCEL)
        logger.info("❌ [Action-GroupAvatarPage] 点击取消按钮")

    # 群头像-拍照内部-点击切换镜头按钮
    def click_camera_switch(self):
        """   群头像-拍照内部-点击切换镜头按钮   """
        self.click(GroupAvatarLocator.IV_CAMERA_SWITCH)
        logger.info("🔄 [Action-GroupAvatarPage] 点击切换镜头按钮")

    # 群头像-拍照内部-点击返回按钮
    def click_capture_back(self):
        """   群头像-拍照内部-点击返回按钮   """
        self.click(GroupAvatarLocator.IV_ARROW_DOWN)
        logger.info("🔙 [Action-GroupAvatarPage] 点击返回按钮")

