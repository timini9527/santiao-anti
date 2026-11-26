import hashlib
import io
import os
import time
from dataclasses import dataclass
from typing import Optional, Protocol, Literal, Union, List
from PIL import Image
import imagehash

from core.logger_utils import logger, LogIcon

# ==========================================
# 协议定义：解除与具体 Driver/Element 的耦合
# ==========================================

class _DriverLike(Protocol):
    """
    Driver 协议接口：
    鸭子类型设计。只要传入的对象拥有 get_screenshot_as_png 方法即可，
    解除工具类对 Selenium/Appium 底层库的强耦合。
    """
    def get_screenshot_as_png(self) -> bytes: ...

class _ElementLike(Protocol):
    """
    Element 协议接口：
    要求传入的对象具备 rect 属性(获取坐标宽高)和 screenshot_as_png 属性(获取局部截图)。
    """
    @property
    def rect(self) -> dict: ...
    
    @property
    def screenshot_as_png(self) -> bytes: ...

# ==========================================
# 数据模型：裁剪区域
# ==========================================

@dataclass(frozen=True)
class CropRect:
    """
    裁剪区域数据类 (不可变)：
    用于封装从 driver 截图中二次裁剪的坐标和宽高。
    """
    x: int
    y: int
    width: int
    height: int

    @classmethod
    def from_rect_dict(cls, rect: Optional[dict] = None, scale: float = 1.0) -> "CropRect":
        """
        工厂方法：从 Appium/Selenium 标准的 rect 字典构造 CropRect。
         引入 scale(缩放比例) 参数并增加 None 防御。
        :param rect: 包含 x, y, width, height 的字典
        :param scale: 屏幕的像素缩放比 (物理分辨率 / 逻辑分辨率)，默认 1.0
        """
        r = rect or {}
        return cls(
            x=int(r.get("x", 0) * scale),
            y=int(r.get("y", 0) * scale),
            width=int(r.get("width", 0) * scale),
            height=int(r.get("height", 0) * scale),
        )



# ==========================================
# 核心工具类：截图与指纹提取
# ==========================================

class ScreenshotUtils:
    """
    底层视图截图与数字指纹工具类：
    提供全屏截图、控件截图及基于坐标的二次裁剪，
    并支持生成抗噪的图片特征码（dHash/MD5）。
    """

    # --- 平台与坐标适配辅助方法 ---
    @staticmethod
    def _resolve_driver(element: object) -> Optional[_DriverLike]:
        """从元素对象中推断所属的 Driver 实例（兼容 Appium/Selenium/Playwright/自定义驱动）。"""
        for attr in ("parent", "driver", "page"):
            candidate = getattr(element, attr, None)
            if candidate is not None and hasattr(candidate, "get_screenshot_as_png"):
                return candidate
        return None

    @staticmethod
    def _is_harmonyos_driver(driver: Optional[object]) -> bool:
        """判断当前 Driver 是否为鸿蒙驱动（appium-harmonyos-driver 未实现原生元素级截图接口）。"""
        if driver is None:
            return False
        platform_name = str(getattr(driver, "_platform_name", "") or "").strip().lower()
        if platform_name in ("harmonyos", "harmony", "hos", "ohos"):
            return True
        caps = getattr(driver, "capabilities", None)
        if isinstance(caps, dict):
            cap_platform = str(caps.get("platformName", "") or "").strip().lower()
            cap_automation = str(
                caps.get("automationName") or caps.get("appium:automationName") or ""
            ).strip().lower()
            if cap_platform in ("harmonyos", "harmony", "hos", "ohos") or "harmony" in cap_automation:
                return True
        return False

    @staticmethod
    def _is_not_implemented_error(exc: Exception) -> bool:
        """判断异常是否属于驱动未实现元素截图接口（避免吞掉断连或元素失效异常）。"""
        if isinstance(exc, NotImplementedError):
            return True
        msg = str(exc).lower()
        return any(
            keyword in msg
            for keyword in (
                "not yet been implemented",
                "not implemented",
                "unknown command",
                "unknown method",
                "unsupported command",
            )
        )

    @staticmethod
    def _resolve_screenshot_scale(driver: object, img_width: int, img_height: int) -> tuple[float, float]:
        """
        计算全屏截图物理像素与元素 rect 坐标系的缩放比例。
        优先复用 Driver 上缓存的窗口尺寸，避免每次截图都发起额外的 get_window_size RPC。
        """
        win_size = getattr(driver, "_cached_window_size", None)
        if isinstance(win_size, dict):
            win_w = win_size.get("width", 0) or 0
            win_h = win_size.get("height", 0) or 0
            # 若发生横竖屏切换导致宽高方向不一致，刷新一次窗口尺寸缓存
            if win_w > 0 and win_h > 0 and (img_width >= img_height) != (win_w >= win_h):
                win_size = None

        if not isinstance(win_size, dict) and hasattr(driver, "get_window_size"):
            try:
                win_size = driver.get_window_size()
                if isinstance(win_size, dict):
                    try:
                        setattr(driver, "_cached_window_size", win_size)
                    except Exception:
                        pass
            except Exception as e:
                logger.debug(f"{LogIcon.WARN} 获取窗口尺寸失败，默认按 1:1 物理像素裁剪: {e}")
                return 1.0, 1.0

        if isinstance(win_size, dict):
            win_w = float(win_size.get("width", 0) or 0)
            win_h = float(win_size.get("height", 0) or 0)
            if win_w > 0 and win_h > 0 and (img_width >= img_height) == (win_w >= win_h):
                return img_width / win_w, img_height / win_h
        return 1.0, 1.0

    @staticmethod
    def _crop_element_image(driver: _DriverLike, element: _ElementLike) -> Image.Image:
        """基于全屏截图与 element.rect 精准裁剪元素图像，供鸿蒙端及原生截图降级使用。"""
        rect = element.rect or {}
        x = float(rect.get("x", 0))
        y = float(rect.get("y", 0))
        width = float(rect.get("width", 0))
        height = float(rect.get("height", 0))
        if width <= 0 or height <= 0:
            raise ValueError(f"元素矩形区域宽高无效，无法裁剪截图: {rect}")

        full_bytes = ScreenshotUtils.full_png(driver)
        with Image.open(io.BytesIO(full_bytes)) as full_img:
            img_width, img_height = full_img.size
            scale_x, scale_y = ScreenshotUtils._resolve_screenshot_scale(driver, img_width, img_height)

            raw_left = int(round(x * scale_x))
            raw_top = int(round(y * scale_y))
            raw_right = int(round((x + width) * scale_x))
            raw_bottom = int(round((y + height) * scale_y))

            if raw_right <= 0 or raw_bottom <= 0 or raw_left >= img_width or raw_top >= img_height:
                raise ValueError(
                    f"元素区域超出当前屏幕可见范围: rect={rect}, screen=({img_width}, {img_height})"
                )

            left = max(0, min(raw_left, img_width - 1))
            top = max(0, min(raw_top, img_height - 1))
            right = max(left + 1, min(raw_right, img_width))
            bottom = max(top + 1, min(raw_bottom, img_height))
            return full_img.crop((left, top, right, bottom)).copy()

    @staticmethod
    def _crop_element_png(driver: _DriverLike, element: _ElementLike) -> bytes:
        """基于全屏截图与 element.rect 裁剪元素区域并返回 PNG 字节流。"""
        cropped = ScreenshotUtils._crop_element_image(driver, element)
        out = io.BytesIO()
        cropped.save(out, format="PNG")
        return out.getvalue()

    # --- 基础截图方法 ---
    @staticmethod
    def full_png(driver: _DriverLike) -> bytes:
        """获取当前屏幕全屏截图的原始字节流"""
        return driver.get_screenshot_as_png()

    @staticmethod
    def element_png(element: _ElementLike, driver: Optional[_DriverLike] = None) -> bytes:
        """
        跨平台获取元素级 PNG 截图字节流：
        - Android / iOS：直走 Appium 原生 element.screenshot_as_png（零额外开销，仅在驱动未实现接口时降级裁剪）；
        - HarmonyOS：直走全屏截图 + element.rect 裁剪，避免触发 appium-harmonyos-driver 的 NotYetImplementedError。
        """
        resolved_driver = driver or ScreenshotUtils._resolve_driver(element)
        if resolved_driver is not None and ScreenshotUtils._is_harmonyos_driver(resolved_driver):
            return ScreenshotUtils._crop_element_png(resolved_driver, element)

        try:
            return element.screenshot_as_png
        except Exception as e:
            if resolved_driver is not None and ScreenshotUtils._is_not_implemented_error(e):
                logger.warning(f"{LogIcon.WARN} 驱动未实现原生元素截图接口，自动降级为全屏坐标裁剪: {e}")
                return ScreenshotUtils._crop_element_png(resolved_driver, element)
            raise

    @staticmethod
    def element_image(
        element: _ElementLike,
        driver: Optional[_DriverLike] = None,
        mode: str = "RGB",
    ) -> Image.Image:
        """
        跨平台获取元素级 PIL Image 对象：
        - Android / iOS：复用 Appium 原生元素截图并转换为指定色彩模式；
        - HarmonyOS：直接从全屏截图裁剪得到图像对象，省去一次多余的 PNG 编解码开销。
        """
        resolved_driver = driver or ScreenshotUtils._resolve_driver(element)
        if resolved_driver is not None and ScreenshotUtils._is_harmonyos_driver(resolved_driver):
            return ScreenshotUtils._crop_element_image(resolved_driver, element).convert(mode)

        png_bytes = ScreenshotUtils.element_png(element, driver=resolved_driver)
        with Image.open(io.BytesIO(png_bytes)) as img:
            return img.convert(mode)

    @staticmethod
    def crop_png(driver: _DriverLike, rect: CropRect) -> bytes:
        """
        通过 PIL 库按给定坐标，对 Driver 全屏截图进行二次手动裁剪。
        适用于无法通过原生方式定位、或需要局部偏移截取的场景。
        """
        if rect.width <= 0 or rect.height <= 0:
            logger.warning(f"{LogIcon.WARN} 裁剪区域宽高不合法(<=0)，降级返回全屏截图")
            return ScreenshotUtils.full_png(driver)

        # 1. 拿到全屏图片并读取进内存
        img = Image.open(io.BytesIO(ScreenshotUtils.full_png(driver)))
        img_width, img_height = img.size

        # 2. 计算裁剪边界并确保护不在边界溢出
        left = max(rect.x, 0)
        top = max(rect.y, 0)
        right = min(max(left + rect.width, left + 1), img_width)
        bottom = min(max(top + rect.height, top + 1), img_height)

        # 3. 图像剪裁并转回 PNG 格式字节流
        cropped = img.crop((left, top, right, bottom))
        out = io.BytesIO()
        cropped.save(out, format="PNG")
        return out.getvalue()

    # --- 指纹计算方法 ---
    @staticmethod
    def md5_of_bytes(data: bytes) -> str:
        """计算图片二进制流的 32 位 MD5 签名（适用于二进制级别的完全相同校验）"""
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def dhash_of_bytes(data: bytes) -> str:
        """
        获取抗噪差异哈希 (dHash)：
        通过计算相邻像素的亮度差异生成 64 位特征指纹。
        适用于 UI 自动化中判断“内容是否相似”，能有效过滤微小色差和压缩伪影。
        """
        img = Image.open(io.BytesIO(data)).convert('L').resize((9, 8), Image.Resampling.LANCZOS)
        p = list(img.getdata())
        # 逐行比较相邻像素亮度 (9x8 转换为 8x8 特征)
        diff = [(p[i] > p[i + 1]) for i in range(len(p)) if (i + 1) % 9 != 0]
        
        # 将位图转换为 16 进制字符串格式
        decimal_value = 0
        for value in diff:
            decimal_value = (decimal_value << 1) | value
        return format(decimal_value, '016x')

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """
        计算两个哈希值之间的汉明距离（Hamming Distance）。
        距离越小表示越相似，0 为完全一致。UI 波动建议阈值设为 5。
        """
        if len(hash1) != len(hash2):
            return 999  # 长度不同直接判定为不同
        
        # 异或运算后统计位中 1 的个数
        h1 = int(hash1, 16)
        h2 = int(hash2, 16)
        return bin(h1 ^ h2).count('1')

    @staticmethod
    def get_signature_auto(
        driver: Optional[_DriverLike] = None, 
        element: Optional[_ElementLike] = None, 
        rect: Optional[CropRect] = None,
        method: Literal['md5', 'dhash'] = 'dhash'
    ) -> str:
        """
        【全能签名获取】：自动根据优先级选择截图源，并应用指定指纹算法。
        优先级：原生 Element > 坐标 Rect > 全屏 Full
        """
        data = None
        
        # 尝试从 element 中推断 driver (Appium/Selenium 有 parent, Playwright 有 page)
        if driver is None and element is not None:
            if hasattr(element, 'parent'):
                driver = element.parent
            elif hasattr(element, 'page'):
                driver = element.page
            
        if driver is None and element is None:
            raise ValueError("❌ 必须提供 driver 或 element，否则无法进行截图兜底！")
        
        # 1. 尝试原生控件截图（鸿蒙端自动路由至全屏坐标裁剪）
        if element is not None:
            try:
                data = ScreenshotUtils.element_png(element, driver=driver)
                logger.debug(f"{LogIcon.ACTION} Element 截图，大小: {len(data)} 字节")
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} Element 截图失败，降级至坐标裁切: {e}")

        # 2. 尝试按坐标切图
        if not data and rect is not None:
            data = ScreenshotUtils.crop_png(driver, rect)
            logger.debug(f"{LogIcon.ACTION} {rect} 裁切截图，大小: {len(data)} 字节")
 
        # 3. 兜底：全屏截图
        if not data:
            data = ScreenshotUtils.full_png(driver)
            logger.debug(f"{LogIcon.ACTION} {len(data)} 字节")

        # 4. 执行特征提取
        if method == 'dhash':
            signature = ScreenshotUtils.dhash_of_bytes(data)
            logger.info(f"{LogIcon.CAMERA} dHash 指纹成功: {signature}")
            return signature
            
        signature = ScreenshotUtils.md5_of_bytes(data)
        logger.info(f"{LogIcon.CAMERA} MD5 签名成功: {signature}")
        return signature

    # 快捷方法别名
    @staticmethod
    def md5_auto(driver: Optional[_DriverLike] = None, element=None, rect=None) -> str:
        """
        获取 MD5 签名（自动选源）
        
        :param driver: 驱动实例。如果传入了 element，则可省略此参数（自动推断）。若仅传入 rect，则必填。
        :param element: 要截图的原生 UI 控件
        :param rect: 坐标裁切范围
        """
        return ScreenshotUtils.get_signature_auto(driver, element, rect, method='md5')

    @staticmethod
    def dhash_auto(driver: Optional[_DriverLike] = None, element=None, rect=None) -> str:
        """
        获取抗噪 dHash 签名（自动选源）
        
        :param driver: 驱动实例。如果传入了 element，则可省略此参数（自动推断）。若仅传入 rect，则必填。
        :param element: 要截图的原生 UI 控件
        :param rect: 坐标裁切范围
        """
        return ScreenshotUtils.get_signature_auto(driver, element, rect, method='dhash')



# ==========================================
# 相似度比较器：面向业务层的验证组件
# ==========================================

class ImageComparator:
    """
    高级图像比较器：
    封装基于感知哈希（pHash/dHash）的模糊匹配能力，包含调试图像归档逻辑。
    """

    @staticmethod
    def is_hash_similar(hash1: str, hash2: str, threshold: int = 10) -> bool:
        """
        对比两个 dHash/pHash 字符串的相似度（基于汉明距离）。
        :param hash1: 第一个哈希字符串
        :param hash2: 第二个哈希字符串
        :param threshold: 容错阈值。0 为完全一致，通常 UI 场景建议 5-10。
        :return: 是否相似
        """
        if not hash1 or not hash2:
            logger.warning(f"{LogIcon.WARN} 其中一个哈希值为空，无法比对")
            return False
            
        distance = ScreenshotUtils.hamming_distance(hash1, hash2)
        is_similar = distance <= threshold
        
        if is_similar:
            logger.info(f"{LogIcon.SUCCESS} 图像指纹比对通过 | 汉明距离: {distance} (阈值: {threshold})")
        else:
            logger.warning(f"{LogIcon.FAIL} 图像指纹差异过大 | 汉明距离: {distance} (阈值: {threshold})")
            
        return is_similar

    @staticmethod
    def sample_hashes(driver: _DriverLike, element=None, rect=None, sample_count: int = 8, interval: float = 0.1) -> List[str]:
        """
        在给定的时间段内对目标元素连续截取多帧，并返回这些帧的 dHash 签名列表。
        
        :param driver: Driver 实例
        :param element: 目标元素
        :param rect: 裁剪区域坐标
        :param sample_count: 采样帧数，建议 6-10 帧以覆盖完整动画周期
        :param interval: 帧间隔采样时间（秒），默认 0.1 秒（100毫秒）
        :return: 帧 dHash 列表
        """
        hashes = []
        for i in range(sample_count):
            try:
                h = ScreenshotUtils.dhash_auto(driver, element=element, rect=rect)
                if h:
                    hashes.append(h)
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} [Sample] 采集第 {i+1} 帧图像指纹异常: {e}")
            if i < sample_count - 1:
                time.sleep(interval)
        logger.info(f"{LogIcon.SUCCESS} [Sample] 完成多帧图像采集 | 成功采样: {len(hashes)}/{sample_count} 帧")
        return hashes

    @staticmethod
    def compare_multi_hashes(hashes1: List[str], hashes2: List[str], threshold: int = 8) -> bool:
        """
        将两个多帧采样哈希集合进行交叉排队匹配（方案二）。
        只要其中任意一对帧的汉明距离 <= 静态阈值，即判定为同一个表情包在不同时间点展现出的相同帧，从而比对通过。
        
        :param hashes1: 第一个采样的哈希值列表
        :param hashes2: 第二个采样的哈希值列表
        :param threshold: 判定相同单帧的静态阈值（汉明距离），推荐 5-10
        :return: 是否匹配成功
        """
        if not hashes1 or not hashes2:
            logger.warning(f"{LogIcon.WARN} 采样哈希集合为空，无法进行交叉比对")
            return False

        min_distance = 999
        best_pair = (None, None)

        for i, h1 in enumerate(hashes1):
            for j, h2 in enumerate(hashes2):
                distance = ScreenshotUtils.hamming_distance(h1, h2)
                if distance < min_distance:
                    min_distance = distance
                    best_pair = (i, j)
                
                # 只要任意一对低于或等于阈值，即刻短路返回比对成功
                if distance <= threshold:
                    logger.info(f"{LogIcon.SUCCESS} 交叉多帧比对成功！第一组第 {i+1} 帧 与 第二组第 {j+1} 帧 匹配成功 | 汉明距离: {distance} (阈值: {threshold})")
                    return True

        logger.warning(f"{LogIcon.FAIL} 交叉多帧比对失败 | 最小汉明距离: {min_distance} (阈值: {threshold})，出现在第一组第 {best_pair[0]+1} 帧与第二组第 {best_pair[1]+1} 帧之间")
        return False


    
    @staticmethod
    def _save_debug_image(img: Image.Image, name_prefix: str):
        """保存对比失败时的现场图片，协助定位 UI 差异"""
        debug_dir = "./screenshots/debug"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        path = os.path.join(debug_dir, f"{name_prefix}_{int(time.time())}.png")
        img.save(path)
        logger.info(f"{LogIcon.CAMERA} 调试图像已归档：{path}")

    @staticmethod
    def compare_similarity(image_bytes_1: bytes, image_bytes_2: bytes, threshold: int = 10) -> bool:
        """
        对比两张图片的感知相似度 (使用 pHash 算法)。
        :param image_bytes_1: 图片 1 的二进制数据
        :param image_bytes_2: 图片 2 的二进制数据
        :param threshold: 容错阈值（汉明距离），建议 5-15。
        """
        try:
            img1 = Image.open(io.BytesIO(image_bytes_1))
            img2 = Image.open(io.BytesIO(image_bytes_2))

            # 强制归一化处理：转灰度，消除色彩噪音
            img1_gray = img1.convert("L")
            img2_gray = img2.convert("L")

            # 计算感知哈希 (pHash)
            hash1 = imagehash.phash(img1_gray)
            hash2 = imagehash.phash(img2_gray)

            # 计算核心差异指标
            distance = hash1 - hash2
            logger.info(f"{LogIcon.FIND} 🖼️ 图像对比判定 | 汉明距离: {distance} (阈值上限: {threshold})")

            if distance <= threshold:
                return True
            else:
                logger.warning(f"{LogIcon.FAIL} 图像相似度过低，距离 {distance} 已跃出阈值范围 {threshold}")
                ImageComparator._save_debug_image(img1, "mismatch_expected")
                ImageComparator._save_debug_image(img2, "mismatch_actual")
                return False
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 图像相似度对比过程由于由于 IO 或解析异常而中断: {e}")
            return False
