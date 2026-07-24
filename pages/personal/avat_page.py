import random
import time
from typing import Tuple, List
from selenium.webdriver.remote.webelement import WebElement

from business_helpers.avatar_comparison import AvatarComparator
from locators.personal.personal_locator import PersonalLocator
from pages.common.common_page import CommonPage
from core.logger_utils import logger
from pages.personal.personal_page import PersonalPage
from apis.personal_api import PersonalAPI
from locators.personal.avatar_locator import AvatarLocator


#   个人资料
class AvatarPage(PersonalPage, CommonPage):

    # 从头像中点击返回
    def click_back_avatar(self):
        self.click_left_top_button()

    # 点击从相册选择
    def click_select_images(self):
        self.click(AvatarLocator.PHOTO_ALBUM_ID, force_wait=True)

    # 点击从相册返回
    def click_back_album(self):
        self.click(AvatarLocator.PS_LEFT_BACK_ID)

    # 点击从相册取消
    def click_cancel_album(self):
        self.click(AvatarLocator.PS_RIGHT_CANCEL_ID)

    # 从相册获取标题
    def get_album_title(self) -> bool:
        title = self.get_attribute(AvatarLocator.PS_MIDDLE_TITLE_ID, 'text')
        if title:
            logger.info(f" 📸 获取相册标题: {title}")
            return True
        return  False

    # 选中照片后点击返回
    def click_selected_album_back(self):
        self.click(AvatarLocator.LEFT_BACK_LEVEL)

    # 选中照片后点击剪裁
    def click_selected_crop(self):
        self.click(AvatarLocator.RIGHT_CROP)
        time.sleep(1)

    # 点击保存图片
    def click_save_image(self):
        self.click(AvatarLocator.SAVE_IMAGE_ID)

    # 点击保存图片获取弹窗
    def click_save_image_toast(self):
        return self.get_toast()

    # 点击取消
    def click_cancel_image(self):
        self.click_cancel_button()

    # 获取图片列表
    def get_images(self) -> tuple[list[WebElement], int]:
        """
        获取头像图片列表
        Returns:
            tuple[list[WebElement], int]: (图片元素列表, 图片数量)
            如果未找到图片，返回空列表和 0
        """
        images = self.find_elements(AvatarLocator.IMAGE_ID)
        if images:
            logger.info(f" 📸 获取图片列表: {len(images)}")
            return images, len(images)
        return [], 0

    # 点击相册照片 0-第一张
    def click_image(self, index: int):
        images_elems, num = self.get_images()
        images_elems[index].click()

    # 获取头像数据返回头像的哈希值
    def get_avatar_data(self):
        avatar_elem = self.find_element(PersonalLocator.ME_INFO)
        avatar_hash = AvatarComparator.get_element_image_hash(avatar_elem)
        logger.info(f" 📸 获取头像数据, Hash: {avatar_hash}")
        return avatar_hash

    # ========= 核心：策略模式实现相册选择 =========
    def select_image_by_strategy(self, strategy: str):
        """
        根据策略模式选择相册中的图片
        :param strategy: "first", "second", "random", "current_last", "absolute_last"
        """
        logger.info(f"📸 准备在相册中选取图片，策略为: [{strategy}]")

        # 1. 如果是绝对最后一张，先执行滑动触底逻辑
        if strategy == "absolute_last":
            self.swipe_page_quickly('up')

        elements, num = self.get_images()
        if not elements:
            raise RuntimeError("相册中未找到任何图片，请检查手机相册是否为空！")

        # 2. 策略分发执行点击
        if strategy == "first":
            elements[0].click()
        elif strategy == "second":
            if len(elements) < 2:
                logger.warning("相册图片不足2张，降级点击第1张")
                elements[0].click()
            else:
                elements[1].click()
        elif strategy == "random":
            random_element = random.choice(elements)
            random_element.click()
        elif strategy == "current_last" or strategy == "absolute_last":
            elements[-1].click()
        else:
            raise ValueError(f"未知的选图策略: {strategy}")

    # 获取保存图片弹窗消息
    def get_save_image_toase(self) -> str:
        return self.get_toast()

    @staticmethod
    def get_avatar():
        # 获取用户头像信息
        return PersonalAPI().get_avatar_info()

    def wait_for_avatar_update(self, old_ava_id, timeout=5, interval=0.5):
        """
        轮询等待头像更新
        :param old_ava_id: 修改前的头像 ID
        :param timeout: 最大等待时间（秒）
        :param interval: 每次重试间隔（秒）
        :return: 新的头像 ID
        """
        end_time = time.time() + timeout
        # print(f"end_time: {end_time}, {time.time()}")
        while time.time() < end_time:
            new_ava_id = PersonalAPI().get_avatar_info()
            # 新ID 不等于 旧ID，说明服务器更新完成了
            if new_ava_id != old_ava_id:
                logger.info(f"✅ 头像更新成功！耗时: {time.time() - (end_time - timeout):.2f}s")
                print(f"✅ 头像更新成功！耗时: {time.time() - (end_time - timeout):.2f}s")
                print(old_ava_id, new_ava_id)
                return new_ava_id

            # 没更新，稍等一下再试
            print(f"⏳ 头像尚未更新，{interval}秒后重试...")
            time.sleep(interval)
        raise TimeoutError(f"❌ 头像更新超时！已等待 {timeout} 秒，但头像仍未更新。")


    #   进入拍照相关
    def click_photo(self):
        logger.info(" 📸 进入拍照")
        print(" 📸 进入拍照")
        self.click(self.PHOTO)

    #   获取相机权限访问
    def get_camera_permission(self):
        logger.info(" 📸 获取相机权限访问")
        pass

    def photo_img_center(self):
        logger.info(" 📸 点击拍照")
        print(" 📸 点击拍照")
        self.click(self.TAKE_PHOTO_CENTER)
        # pot_bottom = self.find_element(self.TAKE_PHOTO_BOTTOM)
        # pot_bottom = pot_bottom.rect    # 底部坐标
        # print(f" 📸 底部坐标: {pot_bottom}")

    def photo_img_left(self):
        logger.info(" 📸 取消拍照")
        print(" 📸 取消拍照")
        self.click(self.TAKE_PHOTO_LEFT)

    def photo_img_right1(self):
        desc = self.get_attribute(self.MULTI_FOCUS, 'content-desc')
        if desc is not None:
            logger.info(f" 📸 切换前置摄像头: {desc}")
            print(f" 📸 切换前置摄像头: {desc}")
            self.click(self.TAKE_PHOTO_RIGHT)

    def photo_img_right2(self):
        desc = self.get_attribute(self.MULTI_FOCUS, 'content-desc')
        if desc is None:
            logger.info(f" 📸 切换后置摄像头: {desc}")
            print(f" 📸 切换后置摄像头: {desc}")
            self.click(self.TAKE_PHOTO_RIGHT)

    def photo_img_done(self):
        logger.info(" 📸 点击拍照完成")
        print(" 📸 点击拍照完成")
        self.click(self.TAKE_PHOTO_DONE)

    def photo_img_cancel(self):
        logger.info(" 📸 点击取消返回重拍")
        print(" 📸 点击取消返回重拍")
        self.click(self.TAKE_PHOTO_CANCEL)

    # 图片相关
    def count_photos(self) -> Tuple[List[WebElement], int]:
        # 统计图片
        elems_imgs_nums = self.find_elements(self.SELECT_BTNS)
        imgs_num = len(elems_imgs_nums)
        logger.info(f" 📸 统计图片数量:  {imgs_num}")
        print(f" 📸 统计图片数量:  {imgs_num}")
        return elems_imgs_nums, imgs_num

    # 按顺序选择一张图片

    # 随机选择一张图片
    def sj_select_image(self, elems_imgs_nums, index: int = 0):
        random_index = random.randint(0, index - 1)
        logger.info(f" 📸 随机选择图片:  {random_index}")
        print(f" 📸 随机选择图片:  {random_index}")
        elems_imgs_nums[random_index].click()

    # 找到那一张图片被选中，取消，重新选择一张
    def sj_select_image_retry(self, elems_imgs_nums) -> bool:
        time.sleep(0.2)
        for i, ele in enumerate(elems_imgs_nums):
            is_checked = ele.get_attribute('checked')
            if is_checked == 'true':
                print(f" 📸 随机选择图片:  {i} -> {is_checked}")
                # elems_imgs_nums[i].click()
                ele.click()
                # self.sj_select_image(elems_imgs_nums, nums)
                return True
        return  False

    def click_preview_image(self):
        self.click(self.PREVIEW_IMAGE)

    def click_origin_image_out(self, elems_imgs_nums, index: int = 1, origin_status: bool = True, d: int = 0):
        # 外部选择原图
        check_st = self.get_attribute(self.ORIGIN_IMAGE_OUT, "checked") == "true"
        if origin_status != check_st and d == 1:
            logger.info(" 📸 外部选择原图")
            elems_imgs_nums[index - 1].click()
        elif origin_status != check_st and d == 0:
            elems_imgs_nums[index - 1].click()

    def click_origin_image_in(self, origin_status: bool = True, d = 0):
        # 内部选择原图
        time.sleep(0.5)
        logger.info(" 📸 内部选择原图")
        check_st = self.get_attribute(self.ORIGIN_IMAGE_IN, "checked") == "true"
        if origin_status != check_st and d == 1:
            self.click(self.ORIGIN_IMAGE_IN, force_wait= True)
        elif origin_status != check_st and d == 0:
            self.click(self.ORIGIN_IMAGE_IN, force_wait=True)

    def get_toast_message(self, toase) -> str:
        # 获取toast信息
        toast_message = self.find_element(toase, condition="presence", timeout=3)
        if toast_message is not None:
            text = toast_message.text
            logger.info(f" 💬 获取toast信息:  {text}")
            print(f" 💬 获取toast信息:  {text}")
            return text
        return ""

    def cancel_checkbox(self, is_checked: bool = True):
        # 取消勾选
        checkbox = self.get_attribute(self.CANCEL_CHECK, "checked") == "true"
        if checkbox == is_checked:
            self.click(self.CANCEL_CHECK)

    def is_checkbox_checked(self) -> WebElement:
        # 判断是否被选中
        return self.find_element(self.SELECT_COUNT)

    def is_person_image(self, text: str = "") -> bool:
        # 个人头像页面 和 选择图片页面
        sta = self.get_attribute(self.TITLE_TEXTVIEW, 'text') == text
        logger.info(f"🔎 获取标题: {text} -> {sta}")
        print(f"🔎 获取标题: {text} -> {sta}")
        return sta

    def back_person_avatar(self) -> bool:
        # 返回个人头像页面
        for i in range(5):
            st = self.is_person_image(self.PRO_PIC_TEXT)
            if not st:
                self.click_back()
            else:
                return True
        return  False

    def click_image_done(self):
        # 点击图片完成
        self.click(self.IMAGE_DONE)

    def select_images(self):
        logger.info(" 📸 点击从相册选")
        print(" 📸 点击从相册选")
        self.click(self.SELECT_IMAGES)


    def take_photos_1_retry(self):
        # 重新拍照
        self.click_sgd()
        self.click_photo()

    def take_photos_1(self):
        # 点击头像及修改
        avatar = self.find_element(self.ME_AVATAR)
        print(f" 📸 头像是否存在:  {avatar}")
        if avatar is not None:
            self.click(self.ME_AVATAR)
        self.take_photos_1_retry()

    def take_select_photo_retry(self):
        # 重新拍照
        self.click_sgd()
        self.select_images()  # 从相册选

    def take_select_photo(self):
        # 点击头像及修改
        avatar = self.find_element(self.ME_AVATAR)
        print(f" 📸 头像是否存在:  {avatar}")
        if avatar is not None:
            self.click(self.ME_AVATAR)
        self.take_select_photo_retry()

    def click_save_avatar(self):
        # 点击头像保存
        # self.click(self.ME_AVATAR)
        self.click_sgd()
        self.click(self.SAVE_IMG)

    def click_cancel(self):
        # 点击取消
        self.click(self.CANCEL)

    def click_cancel_avatar(self):
        # 点击头像取消
        # self.click(self.ME_AVATAR)
        self.click_sgd()
        self.click(self.CANCEL)

