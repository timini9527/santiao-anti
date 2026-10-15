import time
from selenium.webdriver.remote.webelement import WebElement
from core.logger_utils import logger, LogIcon
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from locators.groups.setting.general.group_avatar_locator import GroupAvatarLocator
from utils.cv_recognition.screenshot_utils import ScreenshotUtils


class GroupAvatarPage(GroupSettingPage):
    """群头像设置与修改页面操作类"""
    
    # 群头像-等待群头像页面加载完成
    def wait_group_avatar_page_load(self, timeout: int = 5) -> bool:
        """   群头像-等待群头像页面加载完成   """
        logger.info(f"{LogIcon.WAIT} 等待群头像页面加载完成 (超时: {timeout}s)")
        state = self.is_element_exist(GroupAvatarLocator.GROUP_HEADER, timeout=timeout)
        if state:
            logger.info(f"{LogIcon.SUCCESS} 群头像页面加载完成")
        else:
            logger.warning(f"{LogIcon.WARN} 群头像页面加载超时")
        return state

    # 群头像-点击左上角返回键
    def click_back_to_group_setting(self) -> None:
        """   群头像-点击左上角返回键   """
        logger.info(f"{LogIcon.ACTION} 返回到群设置页面")
        self.click(GroupAvatarLocator.IV_BACK)

    # 群头像-点击相册内部左上角返回按钮
    def click_back_to_group_avatar_page(self) -> None:
        """   群头像-点击相册内部左上角返回按钮   """
        logger.info(f"{LogIcon.ACTION} 返回到群头像页面")
        self.click(GroupAvatarLocator.PS_IV_LEFT_BACK)

    # 群头像-点击右上角“完成”按钮（确认）
    def click_confirm_change_group_avatar(self) -> None:
        """   群头像-点击右上角“完成”按钮，确认修改群头像   """
        logger.info(f"{LogIcon.SUCCESS} 点击右上角【完成】确认群头像修改")
        self.click(GroupAvatarLocator.FB_ACTION, timeout=2)

    # 群头像-获取当前群头像的图片哈希值
    def get_group_avatar_hash(self) -> str:
        """
        获取当前群头像的图片哈希值（用于断言修改前后头像是否发生了物理改变）
        Returns:
            str: 图像的 dhash 哈希值，若未找到则返回空字符串
        """
        logger.info(f"{LogIcon.CAMERA} 开始获取群头像元素的 dhash 哈希值")
        avatar_ele = self.find_element(GroupAvatarLocator.GROUP_HEADER, timeout=2)
        if not avatar_ele:
            logger.warning(f"{LogIcon.WARN} 未能在页面中找到群头像 ImageView")
            return ""
        try:
            img_hash = ScreenshotUtils.dhash_auto(element=avatar_ele)
            logger.info(f"{LogIcon.SUCCESS} 成功获取群头像 hash: {img_hash}")
            return img_hash
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 获取群头像 hash 出现异常: {e}")
            return ""

    # 群头像-等待选择面板弹窗
    def wait_for_album_dialog(self, timeout: int = 5) -> bool:
        """   群头像-等待选择面板弹窗   """
        logger.info(f"{LogIcon.WAIT} 等待选择面板弹窗 (超时: {timeout}s)")
        state = self.is_element_exist(GroupAvatarLocator.DESIGN_BOTTOM_SHEET, timeout=timeout)
        if state:
            logger.info(f"{LogIcon.SUCCESS} 选择面板弹窗加载完成")
        else:
            logger.warning(f"{LogIcon.WARN} 选择面板弹窗加载超时")
        return state

    # 群头像-点击拍照
    def click_group_avatar_take_photo(self) -> None:
        """   群头像-点击拍照   """
        logger.info(f"{LogIcon.CAMERA} 点击拍照")
        self.click(GroupAvatarLocator.ACTION_TAKE_PHOTO)

    # 群头像-点击从相册选择
    def click_group_avatar_pick_gallery(self) -> None:
        """   群头像-点击从相册选择   """
        logger.info(f"{LogIcon.ACTION} 🖼️ [Action-GroupAvatarPage] 点击从相册选择")
        self.click(GroupAvatarLocator.ACTION_PICK_GALLERY)

    # 群头像-点击保存图片
    def click_group_avatar_save_image(self) -> None:
        """   群头像-点击保存图片   """
        logger.info(f"{LogIcon.ACTION} 💾 [Action-GroupAvatarPage] 点击保存图片")
        self.click(GroupAvatarLocator.ACTION_SAVE_IMAGE)

    # 群头像-点击取消
    def click_group_avatar_cancel(self) -> None:
        """   群头像-点击取消   """
        logger.info(f"{LogIcon.FAIL} 点击取消")
        self.click(GroupAvatarLocator.ACTION_CANCEL)

    # 群头像-等待相册选择面板加载完成
    def wait_album_panel_load(self, timeout: int = 5) -> bool:
        """   群头像-等待相册选择面板加载完成   """
        logger.info(f"{LogIcon.WAIT} 等待相册选择面板加载完成 (超时: {timeout}s)")
        state = self.is_element_exist(GroupAvatarLocator.RECYCLER, timeout=timeout)
        if state:
            logger.info(f"{LogIcon.SUCCESS} 相册选择面板加载完成")
        else:
            logger.warning(f"{LogIcon.WARN} 相册选择面板加载超时")
        return state

    # 群头像-获取相册页面Item
    def get_album_page_item(self, timeout: int = 5) -> list[WebElement]:
        """   群头像-获取相册页面Item   """
        logger.info(f"{LogIcon.WAIT} 🖼️ [Action-GroupAvatarPage] 获取相册页面Item (超时: {timeout}s)")
        elements = self.find_elements(GroupAvatarLocator.IMAGE_PICTURE, timeout=timeout)
        if not elements:
            logger.warning(f"{LogIcon.WARN} 未获取到任何相册页面Item")
            return []
        logger.info(f"{LogIcon.SUCCESS} 成功获取 {len(elements)} 个相册页面Item")
        return elements

    # 群头像-选择相册-点击第一张图片
    def click_album_image_by_index(self, index: int = 0) -> None:
        """   群头像-选择相册-点击第index张图片，默认第一张   """
        logger.info(f"{LogIcon.ACTION} 🖼️ [Action-GroupAvatarPage] 点击相册第 {index + 1} 张图片")
        elements = self.get_album_page_item()
        if not elements:
            logger.warning(f"{LogIcon.WARN} 未获取到任何相册页面Item")
            return
        if index >= len(elements):
            logger.warning(f"{LogIcon.WARN} 索引越界，当前共 {len(elements)} 张图片，请求索引 {index}")
            return
        elements[index].click()

    # 群头像-拍照内部
    def wait_capture_page_load(self, timeout: int = 5) -> bool:
        """   群头像-拍照内部-等待拍照页面加载完成   """
        logger.info(f"{LogIcon.WAIT} 等待拍照页面加载完成 (超时: {timeout}s)")
        state = self.is_element_exist(GroupAvatarLocator.BTN_CAPTURE, timeout=timeout)
        if state:
            logger.info(f"{LogIcon.SUCCESS} 拍照页面加载完成")
        else:
            logger.warning(f"{LogIcon.WARN} 拍照页面加载超时")
        return state

    # 群头像-拍照内部-点击拍照按钮
    def click_capture_photo(self) -> None:
        """   群头像-拍照内部-点击拍照按钮   """
        logger.info(f"{LogIcon.CAMERA} 点击拍照按钮")
        self.click(GroupAvatarLocator.BTN_CAPTURE)
    
    # 群头像-拍照内部-点击确认按钮
    def click_confirm(self) -> None:
        """   群头像-拍照内部-点击确认按钮   """
        logger.info(f"{LogIcon.SUCCESS} 点击确认按钮")
        self.click(GroupAvatarLocator.IV_CONFIRM)
    
    # 群头像-拍照内部-点击取消按钮
    def click_cancel(self) -> None:
        """   群头像-拍照内部-点击取消按钮   """
        logger.info(f"{LogIcon.FAIL} 点击取消按钮")
        self.click(GroupAvatarLocator.IV_CANCEL)

    # 群头像-拍照内部-点击切换镜头按钮
    def click_camera_switch(self) -> None:
        """   群头像-拍照内部-点击切换镜头按钮   """
        logger.info(f"{LogIcon.ACTION} 点击切换镜头按钮")
        self.click(GroupAvatarLocator.IV_CAMERA_SWITCH)

    # 群头像-拍照内部-点击返回按钮
    def click_capture_back(self) -> None:
        """   群头像-拍照内部-点击返回按钮   """
        logger.info(f"{LogIcon.ACTION} 点击返回按钮")
        self.click(GroupAvatarLocator.IV_ARROW_DOWN)

