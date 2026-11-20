from rapidocr_onnxruntime import RapidOCR
from core.logger_utils import logger, LogIcon
from common.base_page import BasePage as BP
import threading
import time
import os
from typing import Optional


from config import SCREENSHOT_DIR


class OcrUtils:
    """基于 RapidOCR 的屏幕文字识别与坐标点击工具（全局懒加载单例复用 ONNX 模型）。"""

    _shared_ocr: Optional[RapidOCR] = None
    _ocr_lock = threading.Lock()

    def __init__(self, driver):
        self.driver = driver

    @property
    def ocr(self) -> RapidOCR:
        """首次真正调用 OCR 时再加载模型并全局复用，避免页面初始化阶段重复加载耗时。"""
        if OcrUtils._shared_ocr is None:
            with OcrUtils._ocr_lock:
                if OcrUtils._shared_ocr is None:
                    OcrUtils._shared_ocr = RapidOCR()  # 初始化使用默认参数避开 KeyError
        return OcrUtils._shared_ocr

    def _get_ocr_result(self, image_name: str, sub_dir: str = "ocr", **kwargs):
        """内部通用方法：截图并执行 OCR 识别"""
        screenshot_dir = os.path.join(str(SCREENSHOT_DIR), sub_dir)
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, image_name)
        
        self.driver.get_screenshot_as_file(screenshot_path)
        
        # 默认参数（防止高分屏图片缩放模糊，提高边缘字符敏感度）
        ocr_kwargs = {
            "det_limit_side_len": 1280, # 提升检测边长，防止高分屏图片缩放导致的模糊
            "det_db_thresh": 0.2,       # 降低检测阈值，提高对浅色/边缘字符的敏感度
            "det_db_box_thresh": 0.4    # 降低检测框过滤阈值，保留更多候选文字区域
        }
        ocr_kwargs.update(kwargs)
        
        result, elapse = self.ocr(screenshot_path, **ocr_kwargs)
        texts = [line[1] for line in result] if result else []
        # logger.info(f"OCR result: {result}")
        logger.info(f"{LogIcon.FIND} OCR 识别文本列表: {texts}")
        logger.info(f"{LogIcon.FIND} OCR 识别耗时: {elapse}s")
        return result

    # 截图OCR识别点击，默认模糊匹配（精确匹配）
    def click_text_by_ocr(self, ocr_text: str, match_index: int = 0, 
                          image_name: str = "click_by_ocr.png", 
                          sub_dir: str = "ocr", 
                          click_duration: int = 200,
                          exact_match: bool = False) -> bool:
        """
        通过 OCR 寻找目标文本并进行点击
        :param ocr_text: 目标查找文字
        :param match_index: 匹配结果索引
        :param image_name: 保存的截图名称
        :param sub_dir: 截图保存的子目录，默认 "ocr"
        :param click_duration: 点击持续按压时间（ms），默认 100ms
        :param exact_match: 是否完全匹配，默认 False（模糊匹配）
        """
        result = self._get_ocr_result(image_name, sub_dir)
        
        if result:
            matches = []
            
            for line in result:
                box, text, score = line[0], line[1], line[2]
                
                if exact_match:
                    # 1. 完全匹配（去除首尾空白）
                    if text.strip() == ocr_text.strip():
                        matches.append((box, text, len(ocr_text)))
                else:
                    # 2. 模糊匹配分支
                    # 2.1 完整包含：目标文字在 OCR 识别的一行文本中
                    if ocr_text in text:
                        matches.append((box, text, len(ocr_text)))
                        continue
                        
                # 2. 换行截断：因为屏幕边缘换行，OCR 将其分离。如果识别出的某行文本是目标文本的子串，
                # 且长度达到一定标准（>=4个字符以防误触通用短词）。我们取匹配到的最长片段。
                    if text in ocr_text and len(text) >= 4:
                        matches.append((box, text, len(text)))
                    
            if matches:
                # 提取最佳匹配长度的一组或者直接用索引
                if match_index != 0:
                    try:
                        best_match_box, best_text, _ = matches[match_index]
                    except IndexError:
                        logger.warning(f"{LogIcon.WARN} 要求的 index {match_index} 超出找到的匹配数量 {len(matches)}，将使用最后一个匹配")
                        best_match_box, best_text, _ = matches[-1]
                else:
                    # 原逻辑：找出匹配长度最大的
                    best_match = max(matches, key=lambda x: x[2])
                    best_match_box, best_text, _ = best_match

                # 默认计算最优匹配框的中心点坐标
                center_x = (best_match_box[0][0] + best_match_box[2][0]) / 2.0
                center_y = (best_match_box[0][1] + best_match_box[2][1]) / 2.0

                # 特殊处理：如果目标文本仅仅包含在这个被识别出的长串里面，中心点就会偏离目标。
                # 通过估算水平方向上字符占比，将点击坐标横向纠偏到我们要找的关键词正中心。
                if not exact_match and ocr_text in best_text and len(ocr_text) < len(best_text):
                    start_idx = best_text.find(ocr_text)
                    logger.info(f"{LogIcon.ACTION} OCR 目标关键词在整串字符中的相对索位: {start_idx}")
                    
                    prefix_str = best_text[:start_idx]
                    total_chars = len(best_text)
                    
                    # 统计中文字符和非中文字符数量进行加权估算像素占比
                    chinese_chars_len = len([c for c in prefix_str if '\u4e00' <= c <= '\u9fff'])
                    other_chars_len = len(prefix_str) - chinese_chars_len
                    
                    all_chinese_len = len([c for c in best_text if '\u4e00' <= c <= '\u9fff'])
                    all_other_len = total_chars - all_chinese_len
                    
                    total_weight = (all_chinese_len * 2.0) + (all_other_len * 1.0)
                    prefix_weight = (chinese_chars_len * 2.0) + (other_chars_len * 1.0)
                    
                    target_chinese = len([c for c in ocr_text if '\u4e00' <= c <= '\u9fff'])
                    target_other = len(ocr_text) - target_chinese
                    target_weight = (target_chinese * 2.0) + (target_other * 1.0)
                    
                    center_weight = prefix_weight + (target_weight / 2.0)
                    box_width = best_match_box[1][0] - best_match_box[0][0]
                    
                    center_x = best_match_box[0][0] + (center_weight / total_weight) * box_width
                    logger.warning(f"{LogIcon.WARN} 由于长句包含关键字，原中心已根据字符占比向 x 轴纠偏至: {int(center_x)}")
                
                center_x = int(center_x)
                center_y = int(center_y)
                
                # 使用安全的短点击时长（如 100ms/200ms）以防触发系统级长按
                BP(self.driver).tap_point(x=center_x, y=center_y, duration=click_duration)
                logger.info(f"{LogIcon.SUCCESS} RapidOCR 找到最佳匹配区域 '{best_text}'，用于目标 '{ocr_text}'，坐标({center_x}, {center_y})")
                return True
        logger.error(f"{LogIcon.FAIL} 屏幕上未能找到目标文字: {ocr_text}")
        return False


    # 截图OCR识别点击, 并根据指定文字的相对偏移量进行点击
    def click_text_with_offset(self, target_text: str, offset_x: float = 0, offset_y: float = 0, 
                               image_name: str = "offset_click.png", 
                               sub_dir: str = "ocr", 
                               click_duration: int = 100,
                               exact_match: bool = False) -> bool:
        """
        通过 OCR 寻找目标文本，并在相对该文本选框的指定偏移位置进行点击。
        极其适用于文字旁边带有独立单选框、滑块、同意按钮的情况。
        
        :param target_text: 目标验证文本
        :param offset_x: X 轴偏移量 (如 -85 表示向左偏移 85 像素)
        :param offset_y: Y 轴偏移量 (如 +10 表示向下偏移 10 像素)
        :param image_name: 截图文件名
        :param sub_dir: 截图保存的子目录，默认 "ocr"
        :param click_duration: 点击持续按压时间（ms），默认 100ms
        :param exact_match: 是否完全匹配，默认 False
        """
        result = self._get_ocr_result(image_name, sub_dir)

        if not result:
            logger.warning(f"{LogIcon.FAIL} 屏幕上未识别到任何文本")
            return False

        for line in result:
            box, text, score = line[0], line[1], line[2]
            
            # 判断匹配模式
            is_matched = False
            if exact_match:
                if text.strip() == target_text.strip():
                    is_matched = True
            else:
                if target_text in text:
                    is_matched = True
                    
            if is_matched:
                logger.info(f"{LogIcon.SUCCESS} 成功找到目标文本: '{text}' (置信度: {float(score):.2f})")
                
                # box[0] 是左上角, box[2] 是右下角
                base_x = box[0][0]
                base_y = box[2][1]
                
                target_x = base_x + offset_x
                target_y = base_y + offset_y
                
                logger.info(f"{LogIcon.FIND} 基准点({base_x}, {base_y}) | 偏移量({offset_x}, {offset_y}) -> 实际点击坐标({target_x}, {target_y})")
                
                BP(self.driver).tap_point(x=target_x, y=target_y, duration=click_duration)
                return True
                
        logger.error(f"{LogIcon.FAIL} 屏幕上未能找到目标文本: '{target_text}'")
        return False

    # 获取屏幕上识别到的所有文本列表
    def get_all_text(self, image_name: str = "ocr_verify.png") -> list[str]:
        """
        获取屏幕上识别到的所有文本列表
        """
        result = self._get_ocr_result(image_name)
        if not result:
            logger.warning(f"{LogIcon.WARN} OCR 未能在屏幕上识别到任何文字")
            return []
            
        texts = [line[1] for line in result]
        logger.info(f"{LogIcon.FIND} OCR 识别到全屏文字: {texts}")
        return texts













