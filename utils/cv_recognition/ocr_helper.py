import os
import time
from cnocr import CnOcr
from core.logger_utils import logger, LogIcon

# 引入 cv2 进行模板匹配
try:
    import cv2
    import numpy as np
except ImportError:
    logger.warning(f"{LogIcon.WARN} 未检测到 opencv-python 库，模板匹配功能将无法使用")


class OCRHelper:
    _instance = None
    _ocr = None

    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    copy = os.path.join(_BASE_DIR, 'resources', 'action_long_press', 'copy.png')
    collection = os.path.join(_BASE_DIR, 'resources', 'action_long_press', 'collection.png')
    long_press = os.path.join(_BASE_DIR, 'resources', 'action_long_press', 'long_press.png')

    def __new__(cls):
        """
        整合单例初始化：在首次实例化时尝试预加载 CnOcr 引擎
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            # 初始化 CnOcr
            try:
                cls._ocr = CnOcr(det_model_name='en_PP-OCRv3_det', rec_model_name='densenet_lite_136-gru')
                logger.info(f"{LogIcon.SUCCESS} CnOcr 引擎预加载成功")
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} CnOcr 引擎加载失败: {e}")
                
        return cls._instance

    # cnocr 识别文字
    def find_text_coordinates_cnocr(self, image_path: str, target_text: str):
        """  cnocr 识别 在图片中查找文字，返回中心坐标 (x, y) """
        start_time = time.time()
        # 识别图片
        result = self._ocr.ocr(image_path)
        logger.info(f"{LogIcon.FIND} cnocr -> 识别结果: {result}，开始遍历")

        for item in result:
            # item 结构: {'text': '复制', 'position': [[x1, y1], [x2, y1], [x2, y2], [x1, y2]], 'score': 0.9}
            text = item['text']
            logger.info(f"{LogIcon.FIND} cnocr -> 识别文字: {text}")

            # 模糊匹配，只要包含 "复制" 即可
            if target_text in text:
                position = item['position']
                # 获取文字中心坐标  计算矩形中心点
                center_x = (position[0][0] + position[2][0]) / 2
                center_y = (position[0][1] + position[2][1]) / 2

                logger.info(f"{LogIcon.FIND} OCR 耗时: {time.time() - start_time:.2f}s | 找到 '{target_text}' 坐标: ({center_x}, {center_y})")
                return center_x, center_y

        logger.warning(f"{LogIcon.WARN} OCR 未找到文字: {target_text}")
        return None, None


    # OpenCV 模板匹配识别
    def find_image_coordinates_by_template(self, image_path: str, template_path: str, threshold: float = 0.8) \
        -> tuple[int, int] | tuple[None, None]:
        """
        使用 OpenCV 多尺度模板匹配在图片中查找子图，返回匹配区域的中心坐标 (x, y)
        
        :param image_path: 大图路径 (如当前屏幕截屏)
        :param template_path: 待查找的模板小图路径 (如"删除"红色垃圾桶图标)
        :param threshold: 相似度阈值 (0~1)，低于此阈值认为未成功匹配
        :return: (center_x, center_y) 或 (None, None)
        """
        if not os.path.exists(image_path):
            logger.error(f"{LogIcon.FAIL} 大图文件不存在: {image_path}")
            return None, None
        if not os.path.exists(template_path):
            logger.error(f"{LogIcon.FAIL} 模板图片文件不存在: {template_path}")
            return None, None

        start_time = time.time()
        try:
            # 读取灰度图像提升查找准确度与速度
            img_rgb = cv2.imread(image_path)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.imread(template_path, 0)
            
            orig_w, orig_h = template_gray.shape[::-1]
            img_h, img_w = img_gray.shape[:2]

            best_match_val = -1.0
            best_match_loc = None
            best_scale_w = orig_w
            best_scale_h = orig_h

            # 多尺度等比缩放因子，兼容各种分辨率适配
            scales = np.linspace(0.5, 1.6, 12)

            for scale in scales:
                resized_w = int(orig_w * scale)
                resized_h = int(orig_h * scale)

                # 排除异常边界和过大模板
                if resized_w <= 0 or resized_h <= 0 or resized_w > img_w or resized_h > img_h:
                    continue

                # 缩放模板小图
                resized_template = cv2.resize(template_gray, (resized_w, resized_h), interpolation=cv2.INTER_AREA)

                # 执行匹配
                res = cv2.matchTemplate(img_gray, resized_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val > best_match_val:
                    best_match_val = max_val
                    best_match_loc = max_loc
                    best_scale_w = resized_w
                    best_scale_h = resized_h

            if best_match_val >= threshold:
                center_x = int(best_match_loc[0] + best_scale_w / 2)
                center_y = int(best_match_loc[1] + best_scale_h / 2)
                logger.info(f"{LogIcon.SUCCESS} [Multi-Scale Template Matching] 成功匹配到模板: {template_path} | 最佳相似度: {best_match_val:.4f} (阈值: {threshold}) | 最佳尺寸: {best_scale_w}x{best_scale_h} -> 坐标: ({center_x}, {center_y}) | 耗时: {time.time() - start_time:.4f}s")
                return center_x, center_y

            logger.warning(f"{LogIcon.FAIL} [Multi-Scale Template Matching] 最佳相似度仍低于阈值: {best_match_val:.4f} < {threshold}")
            return None, None
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 执行多尺度模板匹配过程中发生异常: {e}")
            return None, None


    # 统一对外定位匹配接口
    def find_coordinates(self, image_path: str, target: str, method: str = "cnocr", **kwargs) \
        -> tuple[int, int] | tuple[None, None]:
        """
        统一定位与匹配识别接口
        
        :param image_path: 需要识别的大图路径 (如截屏图片)
        :param target: 匹配目标（当使用 OCR 时为目标文本，如 '删除'；当使用模板匹配时为子图模板路径，如 'delete.png'）
        :param method: 指定方法，可选：'template' (模板匹配) | 'cnocr' (CnOcr)
        """
        if method == "template":
            threshold = kwargs.get("threshold", 0.8)
            return self.find_image_coordinates_by_template(image_path, target, threshold)
        elif method == "cnocr":
            return self.find_text_coordinates_cnocr(image_path, target)
        else:
            logger.error(f"{LogIcon.FAIL} 不支持的识别方法类型: {method}")
            return None, None


# OCRHelper().find_text_coordinates_cnocr(OCRHelper.copy, '复制')
# OCRHelper().find_text_coordinates_cnocr(OCRHelper.long_press, '复制')