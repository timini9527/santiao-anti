"""
跨端定位器动态加载与智能分发中枢 (Cross-Platform Locator Manager)
根据当前设备类型 (Android / HarmonyOS NEXT / iOS) 自动透明路由元素定位器
"""
import inspect
import threading
import os
from contextlib import contextmanager
from typing import Any, Type, Optional
from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import load_yaml_data

_thread_local = threading.local()


class LocatorPlatformManager:
    """
    工业级设备平台状态感知中枢 (Driver-Bound 实例级线程隔离架构)：
    核心设计准则：
    1. 彻底废除进程级全局单例状态，严禁跨设备、跨线程污染；
    2. 优先感知当前线程绑定的独立平台 (Thread-Local)，支持多端异构并发；
    3. 调用栈上下文安全嗅探：精确探测正在调用的 Page 实例或 Driver 属性；
    4. 严格安全的基线回退机制：在脱离任何 Driver 或上下文的裸调用场景下，
       默认安全回退到基线平台 'android'，坚决杜绝全局环境变量配置对纯安卓设备的隐式串扰。
    """
    _config_platform_cache: Optional[str] = None

    @classmethod
    def get_thread_platform(cls) -> Optional[str]:
        """获取当前线程绑定的独立平台"""
        return getattr(_thread_local, "platform", None)

    @classmethod
    def set_thread_platform(cls, platform: Optional[str]) -> None:
        """为当前线程独立绑定平台（严格线程隔离，互不干扰）"""
        _thread_local.platform = platform.strip().lower() if platform else None

    @classmethod
    def detect_caller_platform(cls) -> Optional[str]:
        """
        调用栈上下文主动嗅探：
        向上遍历调用帧，探测调用方 Page 实例绑定的 self._platform_name 或 self.driver。
        加入防重入保护，严禁触发 __getattr__ 导致死循环。
        """
        if getattr(_thread_local, "_detecting_active", False):
            return None

        _thread_local._detecting_active = True
        try:
            frame = inspect.currentframe()
            for _ in range(6):
                if frame is None:
                    break
                frame = frame.f_back
                if frame is None:
                    break
                caller_self = frame.f_locals.get("self")
                if caller_self is None:
                    continue

                # 2. 核心防御：若是定位器代理本身，严禁访问其属性，直接跳过！
                if type(caller_self).__name__ == "DynamicLocatorProxy":
                    continue

                # 3. 安全获取 driver：直接查对象的 __dict__，绝不触发任何动态 __getattr__
                caller_dict = getattr(caller_self, "__dict__", None)
                if not isinstance(caller_dict, dict):
                    continue

                # 1. 优先直接获取 BasePage 绑定的平台标识
                p_page = caller_dict.get("_platform_name")
                if p_page:
                    return str(p_page).strip().lower()

                driver = caller_dict.get("driver")
                if driver is None:
                    continue

                # 2. 显式平台标记判断
                p_attr = getattr(driver, "_platform_name", None)
                if p_attr:
                    return str(p_attr).strip().lower()

                # 3. 鸿蒙原生驱动判断
                if hasattr(driver, "is_healthy") or "harmony" in type(driver).__name__.lower():
                    return "harmonyos"

                # 4. Appium Capabilities 判断
                caps = getattr(driver, "capabilities", None) or getattr(driver, "caps", None)
                if isinstance(caps, dict):
                    p_cap = caps.get("platformName") or caps.get("automationName")
                    if p_cap:
                        p_str = str(p_cap).strip().lower()
                        if p_str in ("harmonyos", "openharmony", "hos"):
                            return "harmonyos"
                        elif p_str in ("android", "uiautomator2"):
                            return "android"
                        elif p_str in ("ios", "apple", "xcuitest"):
                            return "ios"
        except Exception:
            pass
        finally:
            _thread_local._detecting_active = False
        return None

    @classmethod
    def get_current_platform(cls) -> str:
        """
        获取当前执行的被测平台标识 (小写：'android' / 'harmonyos' / 'ios')
        优先级：
          1. 当前线程绑定的独立平台 (多设备并发隔离，最高优先级)
          2. 调用栈 Page 上下文 Driver 探测 (多设备单线程交替调用)
          3. 默认安全基线回退 'android' (彻底斩断全局环境变量串扰)
        """
        # 1. 优先读取当前线程独立绑定的平台 (Thread-Local 隔离)
        thread_plat = cls.get_thread_platform()
        if thread_plat:
            return thread_plat

        # 2. 调用栈当前操作的 Page 实例探测
        caller_plat = cls.detect_caller_platform()
        if caller_plat:
            return caller_plat

        # 3. 严格安全的基线回退：坚决杜绝全局环境变量 PLATFORM 对无上下文调用的隐式串扰
        return "android"

    @classmethod
    def set_current_platform(cls, platform: str) -> None:
        """兼容保留接口：仅更新当前线程的绑定，禁止修改全局进程状态"""
        if platform:
            clean_plat = platform.strip().lower()
            cls.set_thread_platform(clean_plat)

    @classmethod
    @contextmanager
    def use_platform(cls, platform: str):
        """上下文管理器：安全临时切换定位器平台，退出后自动还原"""
        old_thread = cls.get_thread_platform()
        cls.set_thread_platform(platform)
        try:
            yield
        finally:
            cls.set_thread_platform(old_thread)

    @classmethod
    def reset(cls) -> None:
        """重置当前线程平台缓存状态"""
        cls.set_thread_platform(None)


class DynamicLocatorMeta(type):
    """
    工业级跨端定位器元类 (Metaclass)：
    1. 彻底消除 `if TYPE_CHECKING:` 与 `else: XxxLocator = DynamicLocatorProxy(...)` 的双分支定义冲突，
       让跨端定位器直接声明为标准 Python 类（如 `class ChatLocator(ChatLocatorIos, _ChatLocatorAndroid, ChatLocatorHos, metaclass=DynamicLocatorMeta):`），
       使 IDE 的 Ctrl + 鼠标左键 100% 原生直达对应平台定位器文件中的变量定义位置；
    2. 运行时在 __new__ 阶段自动将代理类的物理基类重置为 (object,)，杜绝多继承静态属性遮蔽与 MRO 冲突；
    3. 运行时通过元类 __getattr__ 拦截所有定位器属性与方法访问，根据当前设备平台实时透明路由。
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        if "_android_cls" in namespace:
            return super().__new__(mcs, name, (object,), namespace)

        resolved_bases = tuple(
            b._resolve_target_cls()
            if isinstance(b, DynamicLocatorMeta) and "_android_cls" in b.__dict__
            else b
            for b in bases
        )
        return type(name, resolved_bases, namespace)

    def _resolve_target_cls(cls) -> Type:
        android_cls = type.__getattribute__(cls, "_android_cls")
        harmony_cls = type.__getattribute__(cls, "_harmony_cls")
        ios_cls = type.__getattribute__(cls, "_ios_cls")
        plat = LocatorPlatformManager.get_current_platform()
        if plat in ("harmonyos", "openharmony", "hos"):
            return harmony_cls or android_cls
        elif plat in ("ios", "apple"):
            return ios_cls or android_cls
        return android_cls

    def __getattr__(cls, name: str) -> Any:
        target_cls = cls._resolve_target_cls()
        android_cls = type.__getattribute__(cls, "_android_cls")

        if hasattr(target_cls, name):
            return getattr(target_cls, name)

        if hasattr(android_cls, name):
            return getattr(android_cls, name)

        target_name = getattr(target_cls, "__name__", str(target_cls))
        base_name = getattr(android_cls, "__name__", str(android_cls))
        raise AttributeError(
            f"跨端元素定位器代理错误: 平台 '{LocatorPlatformManager.get_current_platform()}' 对应的 "
            f"[{target_name}] 及基础类 [{base_name}] 均未定义属性或方法: '{name}'"
        )

    def __dir__(cls):
        target_cls = cls._resolve_target_cls()
        android_cls = type.__getattribute__(cls, "_android_cls")
        attrs = set(dir(target_cls)) | set(dir(android_cls))
        return sorted(attrs)

    def __repr__(cls) -> str:
        try:
            target_cls = cls._resolve_target_cls()
            target_name = getattr(target_cls, "__name__", str(target_cls))
            return f"<DynamicLocatorMeta(active_class='{target_name}')>"
        except Exception:
            return super().__repr__()


class DynamicLocatorProxy:
    """
    工业级通用元素定位器透明代理类：
    1. 动态拦截属性或方法访问，根据当前平台无感路由至对应的平台定位器实现；
    2. 支持静态元组定位器 (By, Value) 与动态参数化定位器方法 (classmethod)；
    3. 支持优雅回退机制：当定制平台定位器尚未覆盖时，自动平滑回退至 Android 通用定位器；
    4. 完整暴露 dir() 与 docstring，全面保障 IDE 智能提示与静态类型检查。
    """
    def __init__(self, android_cls: Type, harmony_cls: Optional[Type] = None, ios_cls: Optional[Type] = None):
        self._android_cls = android_cls
        self._harmony_cls = harmony_cls
        self._ios_cls = ios_cls

    def _resolve_target_cls(self) -> Type:
        plat = LocatorPlatformManager.get_current_platform()
        if plat in ("harmonyos", "openharmony", "hos"):
            return self._harmony_cls or self._android_cls
        elif plat in ("ios", "apple"):
            return self._ios_cls or self._android_cls
        return self._android_cls

    def __mro_entries__(self, bases):
        """
        PEP 560 标准继承协议：
        当子类定位器显式继承 DynamicLocatorProxy 实例（如 class _LoginLocatorAndroid(CommonLocator):）时，
        将其平滑解析为真实的底层物理基类，彻底杜绝 Python 将 DynamicLocatorProxy 误作为元类 (metaclass) 调用的隐患。
        """
        target_cls = self._resolve_target_cls()
        return (target_cls,)

    def __getattr__(self, name: str) -> Any:
        target_cls = self._resolve_target_cls()

        # 1. 优先从当前平台的专属 Locator 中获取属性或方法
        if hasattr(target_cls, name):
            attr = getattr(target_cls, name)
            return attr

        # 2. 优雅回退：若专属 Locator 未特别覆盖，安全回退至 Android 基础定位器
        if hasattr(self._android_cls, name):
            return getattr(self._android_cls, name)

        target_name = getattr(target_cls, "__name__", str(target_cls))
        base_name = getattr(self._android_cls, "__name__", str(self._android_cls))
        raise AttributeError(
            f"跨端元素定位器代理错误: 平台 '{LocatorPlatformManager.get_current_platform()}' 对应的 "
            f"[{target_name}] 及基础类 [{base_name}] 均未定义属性或方法: '{name}'"
        )

    def __dir__(self):
        target_cls = self._resolve_target_cls()
        attrs = set(dir(target_cls)) | set(dir(self._android_cls))
        return sorted(attrs)

    def __repr__(self) -> str:
        try:
            target_cls = self._resolve_target_cls()
            target_name = getattr(target_cls, "__name__", str(target_cls))
            return f"<DynamicLocatorProxy(active_class='{target_name}')>"
        except Exception:
            base_name = getattr(self._android_cls, "__name__", str(self._android_cls))
            return f"<DynamicLocatorProxy(base='{base_name}')>"
