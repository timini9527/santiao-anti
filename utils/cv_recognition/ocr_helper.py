import os
import time
from cnocr import CnOcr

from core.logger_utils import logger

# 延迟导入，防止未安装库导致整个框架崩溃
try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError("请先安装 PaddleOCR: pip install paddlepaddle paddleocr")


class OCRHelper:
    _instance = None
    _ocr = None

    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    copy = os.path.join(_BASE_DIR, 'data', 'images', 'copy.png')
    collection = os.path.join(_BASE_DIR, 'data', 'images', 'collection.png')
    long_press = os.path.join(_BASE_DIR, 'data', 'images', 'long_press.png')

    # cnocr 识别
    def __new__(cls):
        # cnocr 识别
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 初始化模型，rec_model_name='densenet_lite_136-fc' 是轻量级模型，速度快
            # det_model_name='en_PP-OCRv3_det' 用于检测文字坐标
            cls._ocr = CnOcr(det_model_name='en_PP-OCRv3_det', rec_model_name='densenet_lite_136-gru')
        return cls._instance
        """
        # PaddleOCR 识别
        单例模式初始化，确保模型只加载一次
        """
        if cls._instance is None:
            cls._instance = super(OCRHelper, cls).__new__(cls)
            logger.info("🚀 正在初始化 PaddleOCR 引擎 (首次加载较慢，请稍候)...")
            start_t = time.time()
            # 初始化 PaddleOCR
            # use_angle_cls=True: 开启方向分类（应对文字旋转）
            # lang="ch": 中文模型
            # show_log=False: 关闭底层刷屏日志
            # use_gpu=False: 测试机通常无 GPU，强制 CPU 运行更稳
            cls._ocr_engine  = PaddleOCR(
                use_angle_cls=True,  # 【关键】在这里开启方向检测，后续调用不需要传 cls=True
                lang="ch",
                # use_gpu=False,
                # show_log=False,
                # --- 核心修复 ---
                # enable_mkldnn=False  # 禁用 Intel 加速库，解决 fused_conv2d 报错
            )

            logger.info(f"✅ PaddleOCR 引擎加载完成，耗时: {time.time() - start_t:.2f}s")
        return cls._instance

    # cnocr 识别文字
    def find_text_coordinates_cnocr(self, image_path: str, target_text: str):
        """
            cnocr 识别 在图片中查找文字，返回中心坐标 (x, y)
        """
        start_time = time.time()
        # 识别图片
        result = self._ocr.ocr(image_path)
        print("cnocr -> 识别结果: ", result)

        for item in result:
            # item 结构: {'text': '复制', 'position': [[x1, y1], [x2, y1], [x2, y2], [x1, y2]], 'score': 0.9}
            text = item['text']
            print(f"识别文字: {text}")

            # 模糊匹配，只要包含 "复制" 即可
            if target_text in text:
                position = item['position']
                # 获取文字中心坐标  计算矩形中心点
                center_x = (position[0][0] + position[2][0]) / 2
                center_y = (position[0][1] + position[2][1]) / 2

                print(f"OCR 耗时: {time.time() - start_time:.2f}s | 找到 '{target_text}' 坐标: ({center_x}, {center_y})")
                return center_x, center_y

        print(f"OCR 未找到文字: {target_text}")
        return None, None


    # PaddleOCR 识别
    def find_text_coordinates_paddle(self, image_path: str, target_text: str, confidence: float = 0.6) \
        -> tuple[int, int] | tuple[None, None]:
        """
           在图片中查找文字，返回中心坐标 (x, y)

           :param image_path: 图片路径
           :param target_text: 目标文字 (支持模糊匹配)
           :param confidence: 置信度阈值 (0~1)，低于此值的识别结果被忽略
           :return: (center_x, center_y) 或 (None, None)
        """
        if not os.path.exists(image_path):
            logger.error(f"❌ 图片文件不存在: {image_path}")
            return None, None

        start_time = time.time()

        # 执行识别
        # cls=True 开启方向纠正
        try:
            result = self._ocr_engine.ocr(image_path)
        except Exception as e:
            logger.error(f"OCR 识别过程发生异常: {e}")
            return None, None

        # PaddleOCR 返回 None 或 空列表的处理
        if not result or result[0] is None:
            logger.warning(f"OCR 未在图片中识别到任何文字: {target_text}")
            return None, None
        print(f"OCR 耗时: {time.time() - start_time:.2f}s | 识别结果: {result}")
        # 遍历结果
        # 标准结构通常是: [ [ [box], (text, score) ], ... ]
        # 但报错显示你的结构可能是: [ [ [box], "text" ], ... ]
        for line in result[0]:
            try:
                box = line[0]  # 坐标 [[x1,y1],...]
                element = line[1]  # 可能是元组 ('text', 0.99) 也可能是字符串 'text'

                text_content = ""
                score = 1.0  # 默认置信度 (如果结构里没有分数)

                # ✅ 架构师修复：防御性类型检查
                if isinstance(element, (tuple, list)):
                    # 标准情况: ('复制', 0.99)
                    text_content = element[0]
                    if len(element) > 1:
                        score = element[1]
                elif isinstance(element, str):
                    # 异常情况: 只有字符串 '复制'
                    text_content = element
                    score = 1.0  # 无法获取分数，默认置信度满分
                else:
                    logger.warning(f"⚠️ 未知的 OCR 结果格式: {type(element)} - {element}")
                    continue

                # 匹配逻辑
                if target_text in text_content and score >= confidence:
                    # 计算中心点
                    center_x = int((box[0][0] + box[2][0]) / 2)
                    center_y = int((box[0][1] + box[2][1]) / 2)

                    logger.info(f"✅ OCR 命中: '{text_content}' (score={score:.2f}) -> 坐标 ({center_x}, {center_y})")
                    return center_x, center_y

            except Exception as inner_e:
                # 防止单行解析错误导致整个流程崩溃
                logger.warning(f"⚠️ 解析单行 OCR 结果失败: {line} | Error: {inner_e}")
                continue

        logger.warning(f"❌ OCR 未找到目标文字: {target_text}")
        return None, None




# OCRHelper().find_text_coordinates_cnocr(OCRHelper.copy, '复制')
# OCRHelper().find_text_coordinates_cnocr(OCRHelper.long_press, '复制')
# OCRHelper().find_text_coordinates_paddle(OCRHelper.long_press, '复制')
# OCRHelper().find_text_coordinates_paddle(OCRHelper.copy, '复制')