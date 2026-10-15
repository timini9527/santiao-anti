import random
import time
from typing import Tuple, List, Optional
from selenium.webdriver.remote.webelement import WebElement

from business_helpers.avatar_comparison import AvatarComparator
from locators.personal.personal_locator import PersonalLocator
from pages.common.common_page import CommonPage
from core.logger_utils import logger, LogIcon
from pages.personal.personal_page import PersonalPage
from apis.personal_api import PersonalAPI
from locators.personal.avatar_locator import AvatarLocator


# 个人资料
class AvatarPage(PersonalPage, CommonPage):
    """个人资料头像页面对象"""

    # 头像 - 从头像大图预览中点击返回
    def click_back_avatar(self) -> None:
        """ 头像 - 从头像大图预览中点击返回 """
        logger.info(f"{LogIcon.SETUP} 从头像预览中点击返回")
        self.click_left_top_button()

    def push_local_image_to_gallery(self, local_image_path: str, remote_filename: Optional[str] = None) -> str:
        """
        将电脑本地图片推送到手机相机胶卷相册，并强制刷新系统媒体库索引，使其排在相机胶卷最前列
        :param local_image_path: 电脑本地图片路径
        :param remote_filename: 手机端保存的文件名，默认带时间戳防止重名
        :return: 手机上的绝对保存路径
        """
        import os
        import base64
        if not os.path.exists(local_image_path):
            raise FileNotFoundError(f"本地图片文件不存在: {local_image_path}")

        logger.info(f"{LogIcon.ACTION} 📤 [Action - Avatar] 准备将本地图片推送至设备相机胶卷: {local_image_path}")
        with open(local_image_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        # 规范化文件扩展名并采用标准相机照片命名前缀 (如 IMG_1726000000.jpg)
        _, ext = os.path.splitext(local_image_path)
        ext = ext.lower() if ext else ".png"
        filename = remote_filename or f"IMG_{int(time.time())}{ext}"
        if not filename.startswith("IMG_"):
            filename = f"IMG_{filename}"

        # 相机胶卷标准物理存储路径 (采用 /storage/emulated/0 避免符号链接导致媒体扫描器忽略)
        remote_dir = "/storage/emulated/0/DCIM/Camera"
        remote_path = f"{remote_dir}/{filename}"

        # 1. 推送文件至手机存储 (Appium 原生 push_file 自动处理目录创建)
        try:
            self.driver.push_file(remote_path, b64_data)
            logger.info(f"{LogIcon.SUCCESS} 本地图片已成功推送到相机胶卷目录: {remote_path}")
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 推送本地图片到设备失败: {e}")
            raise

        # 2. 媒体库核心注册：通过宿主机本地 ADB 触发 Android 系统 ContentProvider 官方 scan_file 入库
        # 这是 Android 10+ 官方提供的标准入库方式，彻底解决媒体库 datetaken 为 NULL、非重启不刷新的系统限制
        try:
            import subprocess
            udid = getattr(self.driver, "_factory_udid", None) or self.driver.capabilities.get("udid")
            adb_cmd = ["adb"]
            if udid:
                adb_cmd.extend(["-s", str(udid)])

            # 核心指令：直接唤醒系统的 MediaProvider 将新照片同步入库并生成当前时间戳
            subprocess.run(
                [*adb_cmd, "shell", "content", "call", "--uri", "content://media", "--method", "scan_file", "--arg", remote_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
            )
            # 刷新 mtime 确保相册按时间倒序排在首位
            subprocess.run([*adb_cmd, "shell", "touch", remote_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
            logger.info(f"{LogIcon.SUCCESS} 📡 [Action - Avatar] 已通过官方 scan_file 完成 MediaStore 实时入库: {remote_path}")
        except Exception as adb_err:
            logger.debug(f"{LogIcon.WARN} 官方 scan_file 入库执行跳过: {adb_err}")

        # 3. 辅助降级扩展调用：UiAutomator2 原生 scanMedia
        try:
            self.driver.execute_script("mobile: scanMedia", {"filepath": remote_path})
        except Exception:
            pass

        time.sleep(0.5)
        return remote_path

    # 头像 - 点击从相册选择
    def click_select_images(self) -> None:
        """ 头像 - 点击从相册选择 """
        logger.info(f"{LogIcon.SETUP} 点击从相册选择")
        self.click(AvatarLocator.PHOTO_ALBUM_ID, force_wait=True)

    # 头像 - 点击从相册返回
    def click_back_album(self) -> None:
        """ 头像 - 点击从相册返回 """
        logger.info(f"{LogIcon.SETUP} 点击从相册返回")
        self.click(AvatarLocator.PS_LEFT_BACK_ID)

    # 头像 - 点击从相册取消
    def click_cancel_album(self) -> None:
        """ 头像 - 点击从相册取消 """
        logger.info(f"{LogIcon.SETUP} 点击从相册取消")
        self.click(AvatarLocator.PS_RIGHT_CANCEL_ID)

    # 头像 - 获取相册标题判断是否显示
    def get_album_title(self) -> bool:
        """ 头像 - 获取相册标题判断是否显示 """
        title = self.get_attribute(AvatarLocator.PS_MIDDLE_TITLE_ID, 'text')
        if title:
            logger.info(f"{LogIcon.CAMERA} 获取相册标题: {title}")
            return True
        return False

    # 头像 - 选中照片后点击返回上一级
    def click_selected_album_back(self) -> None:
        """ 头像 - 选中照片后点击返回上一级 """
        logger.info(f"{LogIcon.SETUP} 选中照片后点击返回上一级")
        self.click(AvatarLocator.LEFT_BACK_LEVEL)

    # 头像 - 选中照片后点击剪裁
    def click_selected_crop(self) -> None:
        """ 头像 - 选中照片后点击剪裁 """
        logger.info(f"{LogIcon.SETUP} 选中照片后点击剪裁")
        self.click(AvatarLocator.RIGHT_CROP)
        time.sleep(1)

    # 头像 - 点击保存图片
    def click_save_image(self) -> None:
        """ 头像 - 点击保存图片 """
        logger.info(f"{LogIcon.SETUP} 点击保存图片")
        self.click(AvatarLocator.SAVE_IMAGE_ID)

    # 头像 - 保存图片并获取 Toast 提示
    def click_save_image_toast(self) -> str:
        """ 头像 - 保存图片并获取 Toast 提示 """
        toast = self.get_toast()
        logger.info(f"{LogIcon.FIND} 获取保存图片 Toast: {toast}")
        return toast

    # 头像 - 点击取消图片
    def click_cancel_image(self) -> None:
        """ 头像 - 点击取消图片 """
        logger.info(f"{LogIcon.SETUP} 点击取消图片")
        self.click_cancel_button()

    # 头像 - 获取图片列表
    def get_images(self) -> tuple[list[WebElement], int]:
        """
        获取头像图片列表
        Returns:
            tuple[list[WebElement], int]: (图片元素列表, 图片数量)
            如果未找到图片，返回空列表和 0
        """
        images = self.find_elements(AvatarLocator.IMAGE_ID)
        if images:
            logger.info(f"{LogIcon.CAMERA} 获取图片列表: {len(images)}")
            return images, len(images)
        return [], 0

    # 头像 - 点击相册照片 (0-第一张)
    def click_image(self, index: int) -> None:
        """ 头像 - 点击相册照片 (0-第一张) """
        logger.info(f"{LogIcon.SETUP} 准备点击相册第 {index + 1} 张照片")
        images_elems, num = self.get_images()
        if index < len(images_elems):
            logger.info(f"{LogIcon.SETUP} 执行点击相册第 {index + 1} 张照片")
            images_elems[index].click()

    # 头像 - 获取头像数据返回头像的哈希值
    def get_avatar_data(self) -> str:
        """ 头像 - 获取头像数据返回头像的哈希值 """
        avatar_elem = self.find_element(PersonalLocator.ME_INFO)
        avatar_hash = AvatarComparator.get_element_image_hash(avatar_elem)
        logger.info(f"{LogIcon.CAMERA} 获取头像数据, Hash: {avatar_hash}")
        return avatar_hash

    # 头像 - 根据策略模式选择相册中的图片
    def select_image_by_strategy(self, strategy: str) -> None:
        """
        根据策略模式选择相册中的图片
        :param strategy: "first", "second", "random", "current_last", "absolute_last"
        """
        logger.info(f"{LogIcon.CAMERA} 准备在相册中选取图片，策略为: [{strategy}]")

        # 1. 如果是绝对最后一张，先执行滑动触底逻辑
        if strategy == "absolute_last":
            self.swipe_page_quickly('up')

        elements, num = self.get_images()
        if not elements:
            raise RuntimeError("相册中未找到任何图片，请检查手机相册是否为空！")

        # 2. 策略分发执行点击
        if strategy == "first":
            logger.info(f"{LogIcon.SETUP} 点击第 1 张图片")
            elements[0].click()
        elif strategy == "second":
            if len(elements) < 2:
                logger.warning(f"{LogIcon.WARN} 相册图片不足2张，降级点击第1张")
                elements[0].click()
            else:
                logger.info(f"{LogIcon.SETUP} 点击第 2 张图片")
                elements[1].click()
        elif strategy == "random":
            random_element = random.choice(elements)
            logger.info(f"{LogIcon.SETUP} 随机点击图片")
            random_element.click()
        elif strategy in ["current_last", "absolute_last"]:
            logger.info(f"{LogIcon.SETUP} 点击最后一张图片 (策略: {strategy})")
            elements[-1].click()
        else:
            raise ValueError(f"未知的选图策略: {strategy}")

    # 头像 - 获取保存图片弹窗消息
    def get_save_image_toase(self) -> str:
        """ 头像 - 获取保存图片弹窗消息 """
        toast = self.get_toast()
        logger.info(f"{LogIcon.FIND} 获取保存图片弹窗消息: {toast}")
        return toast

    # 头像 - 获取用户头像信息
    @staticmethod
    def get_avatar() -> str:
        """ 头像 - 获取用户头像信息 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Avatar] 调用接口获取用户头像信息")
        return PersonalAPI().get_avatar_info()

    # 头像 - 轮询等待头像更新完成
    def wait_for_avatar_update(self, old_ava_id: str, timeout: int = 5, interval: float = 0.5) -> str:
        """
        轮询等待头像更新
        :param old_ava_id: 修改前的头像 ID
        :param timeout: 最大等待时间（秒）
        :param interval: 每次重试间隔（秒）
        :return: 新的头像 ID
        """
        logger.info(f"{LogIcon.WAIT} 轮询等待头像更新，原 ID: {old_ava_id}")
        end_time = time.time() + timeout
        while time.time() < end_time:
            new_ava_id = PersonalAPI().get_avatar_info()
            if new_ava_id != old_ava_id:
                logger.info(f"{LogIcon.SUCCESS} 头像更新成功！耗时: {time.time() - (end_time - timeout):.2f}s, 新ID: {new_ava_id}")
                return new_ava_id
            logger.info(f"{LogIcon.WAIT} 头像尚未更新，{interval}秒后重试...")
            time.sleep(interval)
        raise TimeoutError(f"❌ [Wait - Avatar] 头像更新超时！已等待 {timeout} 秒，但头像仍未更新。")

    # 头像 - 进入拍照
    def click_photo(self) -> None:
        """ 头像 - 进入拍照 """
        logger.info(f"{LogIcon.CAMERA} 进入拍照")
        self.click(self.PHOTO)

    # 头像 - 获取相机权限访问
    def get_camera_permission(self) -> None:
        """ 头像 - 获取相机权限访问 """
        logger.info(f"{LogIcon.CAMERA} 获取相机权限访问")

    # 头像 - 点击拍照快门按钮
    def photo_img_center(self) -> None:
        """ 头像 - 点击拍照快门按钮 """
        logger.info(f"{LogIcon.CAMERA} 点击拍照快门按钮")
        self.click(self.TAKE_PHOTO_CENTER)

    # 头像 - 取消拍照
    def photo_img_left(self) -> None:
        """ 头像 - 取消拍照 """
        logger.info(f"{LogIcon.CAMERA} 取消拍照")
        self.click(self.TAKE_PHOTO_LEFT)

    # 头像 - 切换前置摄像头
    def photo_img_right1(self) -> None:
        """ 头像 - 切换前置摄像头 """
        logger.info(f"{LogIcon.CAMERA} 检查并切换前置摄像头")
        desc = self.get_attribute(self.MULTI_FOCUS, 'content-desc')
        if desc is not None:
            logger.info(f"{LogIcon.CAMERA} 执行切换前置摄像头: {desc}")
            self.click(self.TAKE_PHOTO_RIGHT)

    # 头像 - 切换后置摄像头
    def photo_img_right2(self) -> None:
        """ 头像 - 切换后置摄像头 """
        logger.info(f"{LogIcon.CAMERA} 检查并切换后置摄像头")
        desc = self.get_attribute(self.MULTI_FOCUS, 'content-desc')
        if desc is None:
            logger.info(f"{LogIcon.CAMERA} 执行切换后置摄像头: {desc}")
            self.click(self.TAKE_PHOTO_RIGHT)

    # 头像 - 点击拍照完成
    def photo_img_done(self) -> None:
        """ 头像 - 点击拍照完成 """
        logger.info(f"{LogIcon.CAMERA} 点击拍照完成")
        self.click(self.TAKE_PHOTO_DONE)

    # 头像 - 点击取消返回重拍
    def photo_img_cancel(self) -> None:
        """ 头像 - 点击取消返回重拍 """
        logger.info(f"{LogIcon.CAMERA} 点击取消返回重拍")
        self.click(self.TAKE_PHOTO_CANCEL)

    # 头像 - 统计图片数量
    def count_photos(self) -> Tuple[List[WebElement], int]:
        """ 头像 - 统计图片数量 """
        elems_imgs_nums = self.find_elements(self.SELECT_BTNS)
        imgs_num = len(elems_imgs_nums)
        logger.info(f"{LogIcon.CAMERA} 统计图片数量: {imgs_num}")
        return elems_imgs_nums, imgs_num

    # 头像 - 随机选择一张图片
    def sj_select_image(self, elems_imgs_nums: list[WebElement], index: int = 0) -> None:
        """ 头像 - 随机选择一张图片 """
        logger.info(f"{LogIcon.CAMERA} 准备随机选择图片 (范围: 0-{index-1})")
        random_index = random.randint(0, index - 1)
        logger.info(f"{LogIcon.CAMERA} 执行点击随机图片索引: {random_index}")
        elems_imgs_nums[random_index].click()

    # 头像 - 找到已选图片并取消选中
    def sj_select_image_retry(self, elems_imgs_nums: list[WebElement]) -> bool:
        """ 头像 - 找到已选图片并取消选中 """
        logger.info(f"{LogIcon.CAMERA} 检查已选中的图片并尝试取消选中")
        time.sleep(0.2)
        for i, ele in enumerate(elems_imgs_nums):
            is_checked = ele.get_attribute('checked')
            if is_checked == 'true':
                logger.info(f"{LogIcon.CAMERA} 取消选中图片: {i}")
                ele.click()
                return True
        return False

    # 头像 - 点击预览大图
    def click_preview_image(self) -> None:
        """ 头像 - 点击预览大图 """
        logger.info(f"{LogIcon.SETUP} 点击预览大图")
        self.click(self.PREVIEW_IMAGE)

    # 头像 - 外部选择原图
    def click_origin_image_out(self, elems_imgs_nums: list[WebElement], index: int = 1, origin_status: bool = True, d: int = 0) -> None:
        """ 头像 - 外部选择原图 """
        logger.info(f"{LogIcon.SETUP} 外部选择原图 (目标状态: {origin_status})")
        check_st = self.get_attribute(self.ORIGIN_IMAGE_OUT, "checked") == "true"
        if origin_status != check_st and d == 1:
            logger.info(f"{LogIcon.CAMERA} 外部切换选择原图")
            elems_imgs_nums[index - 1].click()
        elif origin_status != check_st and d == 0:
            logger.info(f"{LogIcon.CAMERA} 外部选择原图点击")
            elems_imgs_nums[index - 1].click()

    # 头像 - 内部选择原图
    def click_origin_image_in(self, origin_status: bool = True, d: int = 0) -> None:
        """ 头像 - 内部选择原图 """
        time.sleep(0.5)
        logger.info(f"{LogIcon.CAMERA} 内部选择原图 (目标状态: {origin_status})")
        check_st = self.get_attribute(self.ORIGIN_IMAGE_IN, "checked") == "true"
        if origin_status != check_st:
            logger.info(f"{LogIcon.SETUP} 点击内部原图勾选框")
            self.click(self.ORIGIN_IMAGE_IN, force_wait=True)

    # 头像 - 获取指定的 Toast 消息
    def get_toast_message(self, toase) -> str:
        """ 头像 - 获取指定的 Toast 消息 """
        toast_message = self.find_element(toase, condition="presence", timeout=3)
        if toast_message is not None:
            text = toast_message.text
            logger.info(f"{LogIcon.FIND} 获取 Toast 消息: {text}")
            return text
        return ""

    # 头像 - 取消勾选框状态
    def cancel_checkbox(self, is_checked: bool = True) -> None:
        """ 头像 - 取消勾选框状态 """
        logger.info(f"{LogIcon.SETUP} 检查取消勾选 (期望当前状态: {is_checked})")
        checkbox = self.get_attribute(self.CANCEL_CHECK, "checked") == "true"
        if checkbox == is_checked:
            logger.info(f"{LogIcon.SETUP} 点击取消勾选")
            self.click(self.CANCEL_CHECK)

    # 头像 - 判断选择计数元素是否存在
    def is_checkbox_checked(self) -> Optional[WebElement]:
        """ 头像 - 判断选择计数元素是否存在 """
        logger.info(f"{LogIcon.FIND} 🧐 [Action - Avatar] 判断选择计数元素是否存在")
        return self.find_element(self.SELECT_COUNT)

    # 头像 - 判断个人头像页面和选择图片页面标题匹配
    def is_person_image(self, text: str = "") -> bool:
        """ 头像 - 个人头像页面 和 选择图片页面标题匹配 """
        sta = self.get_attribute(self.TITLE_TEXTVIEW, 'text') == text
        logger.info(f"{LogIcon.FIND} 校验标题: {text} -> {sta}")
        return sta

    # 头像 - 循环返回至个人头像主页面
    def back_person_avatar(self) -> bool:
        """ 头像 - 循环返回至个人头像主页面 """
        logger.info(f"{LogIcon.SETUP} 准备循环返回个人头像主页")
        for i in range(5):
            st = self.is_person_image(self.PRO_PIC_TEXT)
            if not st:
                logger.info(f"{LogIcon.SETUP} 第 {i+1} 次尝试返回")
                self.click_back()
            else:
                logger.info(f"{LogIcon.SUCCESS} 已处于个人头像主页面")
                return True
        return False

    # 头像 - 点击图片选择完成
    def click_image_done(self) -> None:
        """ 头像 - 点击图片选择完成 """
        logger.info(f"{LogIcon.SETUP} 点击图片选择完成")
        self.click(self.IMAGE_DONE)

    # 头像 - 点击从相册选取
    def select_images(self) -> None:
        """ 头像 - 点击从相册选取 """
        logger.info(f"{LogIcon.CAMERA} 点击从相册选取")
        self.click(self.SELECT_IMAGES)

    # 头像 - 重新进入拍照
    def take_photos_1_retry(self) -> None:
        """ 头像 - 重新进入拍照 """
        logger.info(f"{LogIcon.CAMERA} 重新进入拍照")
        if hasattr(self, 'click_sgd'):
            self.click_sgd()
        self.click_photo()

    # 头像 - 点击头像修改并拍照
    def take_photos_1(self) -> None:
        """ 头像 - 点击头像修改并拍照 """
        logger.info(f"{LogIcon.CAMERA} 准备点击头像并拍照")
        avatar = self.find_element(self.ME_AVATAR)
        if avatar is not None:
            logger.info(f"{LogIcon.CAMERA} 点击头像入口")
            self.click(self.ME_AVATAR)
        self.take_photos_1_retry()

    # 头像 - 重新从相册选取照片
    def take_select_photo_retry(self) -> None:
        """ 头像 - 重新从相册选取照片 """
        logger.info(f"{LogIcon.CAMERA} 重新从相册选取照片")
        if hasattr(self, 'click_sgd'):
            self.click_sgd()
        self.select_images()

    # 头像 - 点击头像修改并从相册选取
    def take_select_photo(self) -> None:
        """ 头像 - 点击头像修改并从相册选取 """
        logger.info(f"{LogIcon.CAMERA} 准备点击头像修改并从相册选图")
        avatar = self.find_element(self.ME_AVATAR)
        if avatar is not None:
            logger.info(f"{LogIcon.CAMERA} 点击头像入口")
            self.click(self.ME_AVATAR)
        self.take_select_photo_retry()

    # 头像 - 点击保存头像
    def click_save_avatar(self) -> None:
        """ 头像 - 点击保存头像 """
        logger.info(f"{LogIcon.SETUP} 点击保存头像")
        if hasattr(self, 'click_sgd'):
            self.click_sgd()
        self.click(self.SAVE_IMG)

    # 头像 - 点击取消
    def click_cancel(self) -> None:
        """ 头像 - 点击取消 """
        logger.info(f"{LogIcon.SETUP} 点击取消")
        self.click(self.CANCEL)

    # 头像 - 点击头像取消操作
    def click_cancel_avatar(self) -> None:
        """ 头像 - 点击头像取消操作 """
        logger.info(f"{LogIcon.SETUP} 点击头像取消操作")
        if hasattr(self, 'click_sgd'):
            self.click_sgd()
        self.click(self.CANCEL)
