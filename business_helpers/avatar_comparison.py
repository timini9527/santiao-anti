import hashlib
from appium.webdriver import WebElement
from core.logger_utils import logger, LogIcon
from utils.cv_recognition.screenshot_utils import ScreenshotUtils



# 头像比较器类
class AvatarComparator:
    """ 头像图片比较器 """

    @staticmethod
    def get_element_image_hash(imageElement: WebElement) -> str:
        """
        获取某个元素的图片内容的 MD5 哈希值
        """
        # 截取该元素区域的 PNG 二进制流（Android/iOS 走 Appium 原生截图，鸿蒙自动全屏裁剪）
        img_bytes = ScreenshotUtils.element_png(imageElement)

        # 计算 MD5
        md5_hash = hashlib.md5(img_bytes).hexdigest()
        logger.info(f"{LogIcon.CAMERA} 获取到元素 {imageElement} 的图片 Hash: {md5_hash}")
        return md5_hash



