import os
import time
import inspect
import re
from functools import wraps
import allure
from selenium.common.exceptions import TimeoutException
from core.logger_utils import logger


# ==========================================
# 辅助函数：抽取独立的截图逻辑，保持装饰器整洁
# ==========================================
def _take_screenshot_on_failure(driver, locator):
    """发生异常时，保存本地截图并附加到 Allure 报告"""
    try:
        # 1. 生成安全的文件名 (去掉特殊符号)
        clean_locator = re.sub(r'[^a-zA-Z0-9_]', '_', str(locator))
        nowtime = time.strftime("%Y-%m-%d_%H%M%S")
        file_name = f"Error_{nowtime}_{clean_locator[:30]}.png"  # 限制文件名长度

        # 2. 附加到 Allure 报告 (直接取二进制，不用存本地也能传)
        png_data = driver.get_screenshot_as_png()
        allure.attach(png_data, name=f"失败截图: {clean_locator}", attachment_type=allure.attachment_type.PNG)

        # 3. 保存到本地 (可选，根据你的需求保留)
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)  # Python 3.2+ 更优雅的创建目录方式
        file_path = os.path.join(screenshot_dir, file_name)
        driver.save_screenshot(file_path)

        logger.info(f"📸 已保存异常截图至: {file_path}")
    except Exception as e:
        logger.warning(f"❌ 自动截图失败: {e}")


# ==========================================
# 内部辅助函数：从被装饰函数的参数中解析公共参数
# ==========================================
def _extract_common_args(func, self_arg, args, kwargs):
    """
    统一解析被装饰方法的参数，提取 locator / raise_exception / expect_missing
    :param func: 被装饰的原始函数
    :param self_arg: 实例对象 (即 self)
    :param args: 位置参数
    :param kwargs: 关键字参数
    :return: (locator, raise_exception, expect_missing) 元组
    """
    sig = inspect.signature(func)
    bound_args = sig.bind(self_arg, *args, **kwargs)
    bound_args.apply_defaults()

    locator = bound_args.arguments.get('locator', '未知定位符')
    raise_err = bound_args.arguments.get('raise_exception', True)
    expect_missing = bound_args.arguments.get('expect_missing', False)

    return locator, raise_err, expect_missing


# ==========================================
# 装饰器 1：查找单个元素异常捕获
# ==========================================
def catch_exception(func):
    """
    用于包裹 find_element 类方法
    功能：发生异常时自动截图、记录日志；并根据 raise_exception / expect_missing 决定行为

    参数行为矩阵:
    ┌──────────────────┬────────────────┬───────────────────────────────────────┐
    │ raise_exception  │ expect_missing │ 行为                                  │
    ├──────────────────┼────────────────┼───────────────────────────────────────┤
    │ True (默认)      │ False (默认)   │ ERROR 日志 + 截图 + 返回 None        │
    │ False            │ False          │ WARNING 日志 (静默模式) + 返回 None   │
    │ 任意             │ True           │ INFO 日志 (预期缺失) + 返回 None     │
    └──────────────────┴────────────────┴───────────────────────────────────────┘
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        locator, raise_err, expect_missing = _extract_common_args(func, self, args, kwargs)

        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # 场景 1：预期元素不存在 (断言 "不应该出现" 的场景)
            #   → 找不到是正确的，记 INFO，不截图，返回 None
            if expect_missing:
                logger.info(f"✅ 元素预期不存在，验证通过: {locator}")
                return None

            # 场景 2：静默模式 (raise_exception=False)
            #   → 探测性查找，不确定有没有，找不到也正常，记 WARNING
            if not raise_err:
                logger.warning(f"⚠️ 元素未找到 (静默模式开启): {locator}")
                return None

            # 场景 3：默认模式 → 真正的异常，记 ERROR + 截图
            logger.error(f"❌ 查找元素失败: {locator} | 原因: {type(e).__name__}")
            if hasattr(self, 'driver') and self.driver:
                _take_screenshot_on_failure(self.driver, locator)
            return None
    return wrapper


# ==========================================
# 装饰器 2：查找元素列表异常捕获
# ==========================================
def catch_elements_exception(func):
    """
    用于包裹 find_elements 类方法
    功能：失败时根据 expect_missing / raise_exception 决定日志级别和返回值

    参数行为矩阵: (同 catch_exception，返回值为 [] 而非 None)
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        locator, raise_err, expect_missing = _extract_common_args(func, self, args, kwargs)

        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # 场景 1：预期元素不存在
            if expect_missing:
                logger.info(f"✅ 元素列表预期为空，验证通过: {locator}")
                return []

            # 场景 2：静默模式
            if not raise_err:
                logger.warning(f"⚠️ 未找到元素列表 (静默模式): {locator}， 详情: {str(e)}")
                return []

            # 场景 3：默认模式 → 真正的异常
            logger.error(f"❌ 查找元素列表失败: {locator}")
            if hasattr(self, 'driver') and self.driver:
                _take_screenshot_on_failure(self.driver, locator)
            return []
    return wrapper


# ==========================================
# 装饰器 3：检查元素是否存在 (返回 Bool)
# ==========================================
def check_element_status(func):
    """
    专门用于包裹 is_element_exist 类方法
    功能：找到返回 True，超时/找不到返回 False，不中断测试

    此装饰器天然适合"验证元素不存在"的场景，返回 False 即代表断言成功，
    日志级别始终为 WARNING (正常超时) 或 ERROR (意外异常)
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()
        locator = bound_args.arguments.get('locator', '未知定位符')
        try:
            result = func(self, *args, **kwargs)
            return True if result is None else result
        except TimeoutException:
            logger.warning(f"⏱️ 元素不存在 (正常超时): {locator}")
            return False
        except Exception as e:
            logger.error(f"❌ 检查元素时发生意外异常: {locator} | 详情: {str(e)}")
            return False
    return wrapper
