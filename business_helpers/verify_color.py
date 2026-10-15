import io
import math
from dataclasses import dataclass
from PIL import Image
from core.logger_utils import logger, LogIcon


@dataclass(frozen=True)
class _ColorFeatures:
    """元素截图的通用颜色特征。只保存特征，不包含具体页面语义。"""

    colored_ratio: float                # 彩色像素占比 (0.0~1.0)
    green_ratio: float                  # 绿色像素占比 (0.0~1.0)
    light_ratio: float                  # 高光/浅色像素占比 (0.0~1.0)
    avg_darkest: float | None           # 最暗像素平均亮度 (0~255)
    avg_text_brightness: float | None   # 文本笔画平均亮度 (0~255)


class FigmaDesignColor:
    """Figma 设计规范标准色值 Token 表"""
    TEXT_DISABLE = "#9D9D9D"                # 灰色通用 - 日期(置灰无消息)
    TEXT_DATE_MSG = "#0A0A0A"               # 黑色通用 - 日期(有消息)
    TEXT_DATE_TODAY = "#20C064"             # 浅绿通用 - 日期(今天)
    MALE_BLUE = "#468BFF"                   # 男性标识蓝
    FEMALE_PINK = "#FD4E4E"                 # 女性标识红


# 颜色验证工具类
class VerifyColor:
    """ 颜色验证工具类 """
    @staticmethod
    def verify_sex(gender_elem) -> str | None:
        """通过性别图片颜色验证性别"""
        try:
            gender_icon = gender_elem

            # 2. 仅获取该控件的局部截图 (返回 PNG 的二进制格式)
            image_data = gender_icon.screenshot_as_png

            # 3. 将二进制数据转换为 PIL Image 对象
            img = Image.open(io.BytesIO(image_data))

            # 将图片转换为 RGB 模式（排除透明度 Alpha 通道的干扰）
            img = img.convert("RGB")

            # 4. 获取图片的宽高，并提取中心点的 RGB 颜色
            width, height = img.size
            center_x, center_y = width // 2, height // 2
            r, g, b = img.getpixel((center_x, center_y))

            # 5. 颜色逻辑判断
            # 蓝色图标通常 Blue 值会明显大于 Red 值
            # 如果女性是粉色/红色图标，则 Red 值会比较高
            if b > r + 20:
                logger.info(f"{LogIcon.FIND} 判断结果：男 (中心点RGB: {r}, {g}, {b})")
                return '男'
            elif r > b + 20:
                logger.info(f"{LogIcon.FIND} 判断结果：女 (中心点RGB: {r}, {g}, {b})")
                return '女'
            else:
                logger.info(f"{LogIcon.FIND} 判断结果：未知/可能是灰色 (中心点RGB: {r}, {g}, {b})")
                return '未知'
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 找不到元素或截图失败: {e}")
            return  None

    @staticmethod
    def verify_agree_btn(btn_elem) -> bool:
        """
        通过按钮颜色验证是否同意勾选。
        勾选时图标呈绿色，未勾选时为灰白空心圈。
        使用像素统计避免勾号中间白色像素造成的干扰。
        """
        try:
            # 1. 仅获取该控件的局部截图 (返回 PNG 的二进制格式)
            image_data = btn_elem.screenshot_as_png

            # 2. 将二进制数据转换为 PIL Image 对象并转为 RGB 模式
            img = Image.open(io.BytesIO(image_data)).convert("RGB")

            # 3. 统计图片中的绿色像素点
            width, height = img.size
            green_pixels = 0
            total_pixels = width * height
            
            for x in range(width):
                for y in range(height):
                    r, g, b = img.getpixel((x, y))
                    # 绿色通道明显大于红色和蓝色通道，即可判定为绿色像素
                    if g > r + 30 and g > b + 30:
                        green_pixels += 1

            # 4. 颜色逻辑判断
            # 如果绿色像素占比超过 5%，说明按钮呈现绿色(被勾选)
            green_ratio = green_pixels / total_pixels
            if green_ratio > 0.05:
                logger.info(f"{LogIcon.SUCCESS} 判断同意按钮状态：已勾选 ✅ (绿色占比: {green_ratio:.1%})")
                return True
            else:
                logger.info(f"{LogIcon.FIND} 判断同意按钮状态：未勾选 ❎ (绿色占比: {green_ratio:.1%})")
                return False
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 分析勾选按钮状态失败: {e}")
            return False

    @staticmethod
    def _extract_color_features(element) -> _ColorFeatures:
        """提取元素截图的颜色特征，供不同页面的语义判断复用。"""
        image_data = element.screenshot_as_png
        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        width, height = img.size

        # 排除元素边缘，避免把相邻控件或边界线算入结果。
        margin_x = min(int(width * 0.15), max((width - 1) // 2, 0))
        margin_y = min(int(height * 0.15), max((height - 1) // 2, 0))

        brightness_list = []
        colored_pixels = 0
        green_pixels = 0
        total_pixels = 0

        for y in range(margin_y, height - margin_y):
            for x in range(margin_x, width - margin_x):
                r, g, b = img.getpixel((x, y))
                total_pixels += 1

                # 绿色用于标签“已选中”状态，单独统计而不是把所有彩色都当成选中。
                if g > r + 20 and g > b + 20:
                    green_pixels += 1

                if max(r, g, b) - min(r, g, b) > 30:
                    colored_pixels += 1
                else:
                    brightness_list.append((r + g + b) // 3)

        if total_pixels == 0:
            raise ValueError("元素截图中心区域为空")

        brightness_list.sort()
        if brightness_list:
            # 至少取 10 个像素；元素过小时限制不超过实际像素数量。
            sample_size = min(len(brightness_list), max(10, len(brightness_list) // 100))
            avg_darkest = sum(brightness_list[:sample_size]) / sample_size
            light_ratio = sum(1 for value in brightness_list if value >= 200) / len(brightness_list)
            
            # 剥离纯白背景像素(亮度>=225)，专门抽取日期数字文字笔画像素的平均亮度
            text_pixels = [b for b in brightness_list if b < 225]
            if text_pixels:
                avg_text_brightness = sum(text_pixels) / len(text_pixels)
            else:
                avg_text_brightness = None
        else:
            avg_darkest = None
            light_ratio = 0.0
            avg_text_brightness = None

        return _ColorFeatures(
            colored_ratio=colored_pixels / total_pixels,
            green_ratio=green_pixels / total_pixels,
            light_ratio=light_ratio,
            avg_darkest=avg_darkest,
            avg_text_brightness=avg_text_brightness,
        )

    @staticmethod
    def verify_calendar_day_is_gray(day_elem) -> bool:
        """判断日历日期文字是否为灰色不可用状态。"""
        try:
            features = VerifyColor._extract_color_features(day_elem)
            logger.info(
                f"{LogIcon.ACTION} 彩色占比: {features.colored_ratio:.1%}, "
                f"{LogIcon.ACTION} 绿色占比: {features.green_ratio:.1%}, "
                f"{LogIcon.ACTION} 文字笔画平均亮度: {features.avg_text_brightness if features.avg_text_brightness is not None else 'N/A'}, "
                f"{LogIcon.ACTION} 最暗像素亮度: {features.avg_darkest if features.avg_darkest is not None else 'N/A'}"
            )

            # 今天等日期可能带绿色背景/文字 (如25日 "今天")，直接视为激活/可用 (非灰色)。
            if features.colored_ratio > 0.05 or features.green_ratio > 0.02:
                logger.info(f"{LogIcon.ACTION} 判定结果：非灰色 (检测到绿色/彩色活跃元素，如今天)")
                return False

            # 未提取到任何非白色文字像素，说明是空白日期格，视为不可点/灰色。
            if features.avg_text_brightness is None:
                logger.info(f"{LogIcon.ACTION} 判定结果：灰色 (未提取到文字笔画像素，空白格)")
                return True

            # 黑色/深色文字 (有消息/可点) 笔画亮度一般在 30~90 之间；
            # 浅灰色文字 (无消息/不可点) 笔画亮度一般在 140~210 之间；
            # 以 125 为分割阈值：>= 125 判定为灰色不可用，< 125 判定为黑色可用。
            is_gray = features.avg_text_brightness >= 125
            logger.info(
                f"{LogIcon.ACTION} 判定结果：{'灰色 🩶 (不可点/无记录)' if is_gray else '黑色 🩵 (可点/有记录)'} "
                f"{LogIcon.ACTION} (文字平均亮度: {features.avg_text_brightness:.1f}, 阈值: 125.0)"
            )
            return is_gray
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [CalendarColor] 分析日期颜色失败: {e}")
            return False

    @staticmethod
    def verify_tag_is_selected(tag_elem) -> bool:
        """判断标签是否为绿色选中状态。"""
        try:
            features = VerifyColor._extract_color_features(tag_elem)
            # 绿色文字可能只占 TextView 截图的一小部分，阈值低于通用彩色判断。
            is_selected = features.green_ratio >= 0.01
            logger.info(
                f"{LogIcon.ACTION} [TagColor] 绿色像素占比: {features.green_ratio:.1%}, "
                f"{LogIcon.FIND} 判定为{'已选中' if is_selected else '未选中'}"
            )
            return is_selected
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [TagColor] 分析标签颜色失败: {e}")
            return False

    @staticmethod
    def verify_btn_is_gray(btn_elem) -> bool:
        """
        兼容旧调用：判断元素是否呈现为灰色。

        新的页面代码应优先使用语义明确的
        ``verify_calendar_day_is_gray`` 或 ``verify_tag_is_selected``，
        不要让不同页面共用同一个业务判定规则。
        """
        try:
            features = VerifyColor._extract_color_features(btn_elem)
            logger.info(f"{LogIcon.ACTION} [ColorVerify] 中心区域彩色像素占比: {features.colored_ratio:.1%} (阈值: 5.0%)")

            if features.colored_ratio > 0.05:
                logger.info(f"{LogIcon.ACTION} [ColorVerify] 判定结果：非灰色（检测到彩色活跃元素，如绿色背景/文本） 🩵 (已激活)")
                return False

            if features.avg_darkest is None:
                logger.warning(f"{LogIcon.WARN} [ColorVerify] 未在元素中心区域提取到有效的无色系像素点，默认判定为非灰色")
                return False

            # 保留旧调用的背景兼容规则；日期页面不再使用本方法。
            if features.avg_darkest >= 120 or (
                features.light_ratio > 0.8 and features.colored_ratio < 0.03
            ):
                logger.info(f"{LogIcon.ACTION} [ColorVerify] 判定结果：灰色 🩶 (未激活/未选中)")
                return True
            else:
                logger.info(f"{LogIcon.ACTION} [ColorVerify] 判定结果：非灰色/黑色 🩵 (已激活/已选中)")
                return False
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [ColorVerify] 分析灰色状态失败: {e}")
            return False



class FigmaColorToken:
    # ======================================
    # 核心工具方法
    # ======================================
    @staticmethod
    def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
        """将 Figma 的 HEX 颜色代码（如 '#07C160'）转换为 (R, G, B) 元组"""
        clean_hex = hex_str.lstrip('#')
        if len(clean_hex) != 6:
            raise ValueError(f"不合法的 HEX 颜色格式: {hex_str}")
        return (
            int(clean_hex[0:2], 16),
            int(clean_hex[2:4], 16),
            int(clean_hex[4:6], 16)
        )

    @staticmethod
    def color_distance(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
        """计算两个 RGB 颜色的欧氏色差距离（数值越小说明颜色越接近）"""
        return math.sqrt(
            (rgb1[0] - rgb2[0]) ** 2 +
            (rgb1[1] - rgb2[1]) ** 2 +
            (rgb1[2] - rgb2[2]) ** 2
        )

    @classmethod
    def verify_element_color_match(
        cls,
        element,
        target_hex: str,
        tolerance: float = 35.0,
        min_ratio: float = 0.02
    ) -> bool:
        """
        根据 Figma UI 设计规范中的 HEX 颜色直接进行断言校验。
        :param element: Appium WebElement 对象
        :param target_hex: Figma 标注中的 16 进制颜色代码（如 '#07C160' 或 '#CCCCCC'）
        :param tolerance: 色差容差范围（默认 35.0，兼容 GPU 渲染抗锯齿与色彩空间微调）
        :param min_ratio: 目标颜色像素占元素中心区域的最小比例（默认 2.0%）
        :return: 是否匹配 Figma 设计规范
        """
        try:
            target_rgb = cls.hex_to_rgb(target_hex)
            image_data = element.screenshot_as_png
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            width, height = img.size

            margin_x = min(int(width * 0.15), max((width - 1) // 2, 0))
            margin_y = min(int(height * 0.15), max((height - 1) // 2, 0))

            matched_pixels = 0
            total_pixels = 0

            for y in range(margin_y, height - margin_y):
                for x in range(margin_x, width - margin_x):
                    pixel_rgb = img.getpixel((x, y))
                    total_pixels += 1
                    if cls.color_distance(pixel_rgb, target_rgb) <= tolerance:
                        matched_pixels += 1

            if total_pixels == 0:
                return False

            ratio = matched_pixels / total_pixels
            is_matched = ratio >= min_ratio
            logger.info(
                f"{LogIcon.ACTION} [FigmaColor] 目标 HEX: {target_hex} (RGB: {target_rgb}), "
                f"{LogIcon.FIND} 匹配像素占比: {ratio:.1%} (期望阈值: {min_ratio:.1%}, 色差容差: {tolerance}) -> "
                f"{LogIcon.SUCCESS} 判定: {'符合设计规范 ✅' if is_matched else '不匹配 ❌'}"
            )
            return is_matched
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [FigmaColor] Figma 颜色匹配校验异常: {e}")
            return False

    # ==================================================================================================
    # 基于 Figma 设计规范 (FigmaDesignColor) 的全新语义断言方法
    # ==================================================================================================
    @classmethod
    def verify_sex_figma(cls, gender_elem) -> str | None:
        """通过 Figma 蓝色/粉色 Token 校验性别图标"""
        try:
            if cls.verify_element_color_match(gender_elem, FigmaDesignColor.MALE_BLUE):
                logger.info(f"{LogIcon.ACTION} [FigmaSex] 匹配 Figma 男性蓝色 Token -> 判定为: 男")
                return '男'
            elif cls.verify_element_color_match(gender_elem, FigmaDesignColor.FEMALE_PINK):
                logger.info(f"{LogIcon.ACTION} [FigmaSex] 匹配 Figma 女性粉色 Token -> 判定为: 女")
                return '女'
            else:
                logger.info(f"{LogIcon.ACTION} [FigmaSex] 未匹配性别颜色 Token -> 判定为: 未知")
                return '未知'
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [FigmaSex] 校验性别颜色失败: {e}")
            return None

    @classmethod
    def verify_agree_btn_figma(cls, btn_elem) -> bool:
        """通过 Figma 浅绿 Token 校验同意勾选按钮"""
        try:
            is_agreed = cls.verify_element_color_match(btn_elem, FigmaDesignColor.TEXT_DATE_TODAY)
            logger.info(f"{LogIcon.ACTION} [FigmaAgree] 同意勾选按钮判定: {'已勾选 ✅' if is_agreed else '未勾选 ❎'}")
            return is_agreed
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [FigmaAgree] 分析勾选按钮状态失败: {e}")
            return False

    @classmethod
    def verify_calendar_day_is_gray_figma(cls, day_elem) -> bool:
        """根据 Figma 日期颜色 Token 判断日历日期是否为灰色无消息状态"""
        try:
            # 1. 优先校验是否为今天浅绿色背景/文字 (如25日 "今天") -> 属于激活状态 (非灰色)
            if cls.verify_element_color_match(day_elem, FigmaDesignColor.TEXT_DATE_TODAY):
                logger.info(f"{LogIcon.ACTION} [FigmaCalendar] 匹配 Figma 今天绿色 Token -> 判定为: 非灰色/已激活")
                return False

            # 2. 校验是否匹配置灰无消息文字 Token (#9D9D9D)
            is_gray = cls.verify_element_color_match(day_elem, FigmaDesignColor.TEXT_DISABLE)
            logger.info(f"{LogIcon.ACTION} [FigmaCalendar] 校验置灰 Token ({FigmaDesignColor.TEXT_DISABLE}) -> 判定为: {'灰色 🩶 (无消息/不可点)' if is_gray else '黑色 🩵 (有消息/可点)'}")
            return is_gray
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [FigmaCalendar] 分析日历日期颜色失败: {e}")
            return False

    @classmethod
    def verify_tag_is_selected_figma(cls, tag_elem) -> bool:
        """根据 Figma 绿色 Token 判断标签是否为已选中状态"""
        try:
            is_selected = cls.verify_element_color_match(tag_elem, FigmaDesignColor.TEXT_DATE_TODAY)
            logger.info(f"{LogIcon.ACTION} [FigmaTag] 标签选中校验: {'已选中 ✅' if is_selected else '未选中 ❎'}")
            return is_selected
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [FigmaTag] 分析标签颜色失败: {e}")
            return False

    @classmethod
    def verify_btn_is_gray_figma(cls, btn_elem) -> bool:
        """根据 Figma 置灰 Token 判断按钮是否呈现灰色未激活状态"""
        try:
            is_gray = cls.verify_element_color_match(btn_elem, FigmaDesignColor.TEXT_DISABLE)
            logger.info(f"{LogIcon.ACTION} [FigmaBtn] 按钮置灰校验: {'灰色未激活 🩶' if is_gray else '活跃正常 🩵'}")
            return is_gray
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [FigmaBtn] 分析按钮置灰状态失败: {e}")
            return False


