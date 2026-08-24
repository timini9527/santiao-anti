import io
from dataclasses import dataclass
from PIL import Image
from core.logger_utils import logger


@dataclass(frozen=True)
class _ColorFeatures:
    """元素截图的通用颜色特征。只保存特征，不包含具体页面语义。"""

    colored_ratio: float
    green_ratio: float
    light_ratio: float
    avg_darkest: float | None


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
                logger.info(f"判断结果：男 (中心点RGB: {r}, {g}, {b})")
                return '男'
            elif r > b + 20:
                logger.info(f"判断结果：女 (中心点RGB: {r}, {g}, {b})")
                return '女'
            else:
                logger.info(f"判断结果：未知/可能是灰色 (中心点RGB: {r}, {g}, {b})")
                return '未知'
        except Exception as e:
            logger.error(f"找不到元素或截图失败: {e}")
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
                logger.info(f"判断同意按钮状态：已勾选 ✅ (绿色占比: {green_ratio:.1%})")
                return True
            else:
                logger.info(f"判断同意按钮状态：未勾选 ❎ (绿色占比: {green_ratio:.1%})")
                return False
        except Exception as e:
            logger.error(f"分析勾选按钮状态失败: {e}")
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
        else:
            avg_darkest = None
            light_ratio = 0.0

        return _ColorFeatures(
            colored_ratio=colored_pixels / total_pixels,
            green_ratio=green_pixels / total_pixels,
            light_ratio=light_ratio,
            avg_darkest=avg_darkest,
        )

    @staticmethod
    def verify_calendar_day_is_gray(day_elem) -> bool:
        """判断日历日期文字是否为灰色不可用状态。"""
        try:
            features = VerifyColor._extract_color_features(day_elem)
            logger.info(
                f"🎨 [CalendarColor] 彩色占比: {features.colored_ratio:.1%}, "
                f"最暗文字亮度: {features.avg_darkest if features.avg_darkest is not None else 'N/A'}"
            )

            # 今天等日期可能带绿色背景/文字，直接视为可用。
            if features.colored_ratio > 0.05:
                return False

            # 日期 TextView 截图包含大量白色背景，不能用白色背景占比判断灰色。
            if features.avg_darkest is None:
                logger.warning("⚠️ [CalendarColor] 未提取到日期文字像素，按不可判定处理")
                return False

            return features.avg_darkest >= 120
        except Exception as e:
            logger.error(f"❌ [CalendarColor] 分析日期颜色失败: {e}")
            return False

    @staticmethod
    def verify_tag_is_selected(tag_elem) -> bool:
        """判断标签是否为绿色选中状态。"""
        try:
            features = VerifyColor._extract_color_features(tag_elem)
            # 绿色文字可能只占 TextView 截图的一小部分，阈值低于通用彩色判断。
            is_selected = features.green_ratio >= 0.01
            logger.info(
                f"🎨 [TagColor] 绿色像素占比: {features.green_ratio:.1%}, "
                f"判定为{'已选中' if is_selected else '未选中'}"
            )
            return is_selected
        except Exception as e:
            logger.error(f"❌ [TagColor] 分析标签颜色失败: {e}")
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
            logger.info(f"🎨 [ColorVerify] 中心区域彩色像素占比: {features.colored_ratio:.1%} (阈值: 5.0%)")

            if features.colored_ratio > 0.05:
                logger.info("🎨 [ColorVerify] 判定结果：非灰色（检测到彩色活跃元素，如绿色背景/文本） 🩵 (已激活)")
                return False

            if features.avg_darkest is None:
                logger.warning("⚠️ [ColorVerify] 未在元素中心区域提取到有效的无色系像素点，默认判定为非灰色")
                return False

            # 保留旧调用的背景兼容规则；日期页面不再使用本方法。
            if features.avg_darkest >= 120 or (
                features.light_ratio > 0.8 and features.colored_ratio < 0.03
            ):
                logger.info("🎨 [ColorVerify] 判定结果：灰色 🩶 (未激活/未选中)")
                return True
            else:
                logger.info("🎨 [ColorVerify] 判定结果：非灰色/黑色 🩵 (已激活/已选中)")
                return False
        except Exception as e:
            logger.error(f"❌ [ColorVerify] 分析灰色状态失败: {e}")
            return False


