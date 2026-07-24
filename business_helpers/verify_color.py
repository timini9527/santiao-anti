import io
from PIL import Image
from core.logger_utils import logger


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
    def verify_btn_is_gray(btn_elem) -> bool:
        """
        通过颜色验证元素是否呈现为灰色（如日历中的灰色未激活日期）
        使用彩色占比与最暗无色像素均值相结合的综合检测算法。
        """
        try:
            # 1. 获取该控件的局部截图
            image_data = btn_elem.screenshot_as_png

            # 2. 将二进制数据转换为 PIL Image 并转为 RGB 模式
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            width, height = img.size

            # 3. 仅分析中心区域，排除边界线和相邻格子的干扰 (留 15% 的安全边距)
            margin_x = int(width * 0.15)
            margin_y = int(height * 0.15)
            
            brightness_list = []
            colored_pixels = 0
            total_center_pixels = 0

            for x in range(margin_x, width - margin_x):
                for y in range(margin_y, height - margin_y):
                    r, g, b = img.getpixel((x, y))
                    total_center_pixels += 1

                    # 如果红绿蓝通道最大差值大于 30，说明是具有明显色彩特征的像素（如今天日期的绿色背景或文字）
                    if max(r, g, b) - min(r, g, b) > 30:
                        colored_pixels += 1
                    else:
                        # 无色系（灰黑白）特征：三个通道差值很小
                        brightness_list.append((r + g + b) // 3)

            # 4. 特征一：彩色像素占比分析
            colored_ratio = colored_pixels / total_center_pixels
            logger.info(f"🎨 [ColorVerify] 中心区域彩色像素占比: {colored_ratio:.1%} (阈值: 5.0%)")
            
            # 如果彩色像素点比例超过 5%，说明元素是有彩色的（例如绿色的“今天”圆圈或高亮文字），直接认定为已激活（非灰色）
            if colored_ratio > 0.05:
                logger.info("🎨 [ColorVerify] 判定结果：非灰色（检测到彩色活跃元素，如绿色背景/文本） 🩵 (已激活)")
                return False

            if not brightness_list:
                logger.warning("⚠️ [ColorVerify] 未在元素中心区域提取到有效的无色系像素点，默认判定为非灰色")
                return False

            # 5. 特征二：无色系最暗像素亮度分析
            brightness_list.sort()
            # 取最暗的前 15 个像素（或前 1% 的像素，以过滤孤立噪点）
            sample_size = max(10, len(brightness_list) // 100)
            darkest_pixels = brightness_list[:sample_size]
            avg_darkest = sum(darkest_pixels) / len(darkest_pixels)

            logger.info(f"🎨 [ColorVerify] 无色系最暗像素样本均值亮度: {avg_darkest:.1f} (样本数: {len(darkest_pixels)})")

            # 💡 优化浅灰底深色字按钮的检测：
            # 如果虽然检测到深色字（最暗像素 < 120），但无色系像素中绝大多数（> 80%）都是亮度很高的灰白底（>= 200），
            # 且整个元素彩色像素占比极低（< 3.0%），说明该元素为未选中的浅灰/白底深字标签按钮，应判定为灰色。
            light_pixels = sum(1 for b in brightness_list if b >= 200)
            light_ratio = light_pixels / len(brightness_list) if brightness_list else 0
            logger.info(f"🎨 [ColorVerify] 浅色背景像素占比: {light_ratio:.1%} (阈值: 80.0%)")

            # 如果最暗的像素均值 >= 120，说明页面上只有白底和浅灰字，无深色/黑色字，即呈现为灰色（未激活）
            if avg_darkest >= 120 or (light_ratio > 0.8 and colored_ratio < 0.03):
                logger.info("🎨 [ColorVerify] 判定结果：灰色 🩶 (未激活/未选中)")
                return True
            else:
                logger.info("🎨 [ColorVerify] 判定结果：非灰色/黑色 🩵 (已激活/已选中)")
                return False
        except Exception as e:
            logger.error(f"❌ [ColorVerify] 分析灰色状态失败: {e}")
            return False


