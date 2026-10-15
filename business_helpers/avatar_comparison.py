import hashlib
from appium.webdriver import WebElement
from core.logger_utils import logger, LogIcon



# 头像比较器类
class AvatarComparator:
    """ 头像图片比较器 """

    @staticmethod
    def get_element_image_hash(imageElement: WebElement) -> str:
        """
        获取某个元素的图片内容的 MD5 哈希值
        """
        # 仅截取该元素区域的图片（返回二进制流）
        img_bytes = imageElement.screenshot_as_png

        # 计算 MD5
        md5_hash = hashlib.md5(img_bytes).hexdigest()
        logger.info(f"{LogIcon.CAMERA} 获取到元素 {imageElement} 的图片 Hash: {md5_hash}")
        return md5_hash



