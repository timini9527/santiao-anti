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
    工业级设备平台状态感知中枢：
    支持调用栈上下文感知、线程级环境隔离、系统环境变量、devices.yaml 配置文件多重感知。
    完美支持单设备与多设备（跨端混合交互/并发）场景。
    """
    _current_platform: Optional[str] = None
    _config_platform_cache: Optional[str] = None

    @classmethod
    def get_thread_platform(cls) -> Optional[str]:
        """获取当前线程绑定的平台"""
        return getattr(_thread_local, "platform", None)

    @classmethod
    def set_thread_platform(cls, platform: Optional[str]) -> None:
        """为当前线程独立绑定平台（适用于多线程并发场景）"""
        _thread_local.platform = platform.strip().lower() if platform else None

    @classmethod
    def detect_caller_platform(cls) -> Optional[str]:
        """
        调用栈上下文主动嗅探：
        向上遍历调用帧，探测调用方 Page 实例绑定的 self.driver 平台。
        加入防重入锁与 __dict__ 安全检测，严禁触发 __getattr__ 导致无限递归死循环。
        """
        # 1. 防重入保护：若已在嗅探中，直接退出，彻底斩断无限递归
        if getattr(_thread_local, "_detecting_active", False):
            return None

        _thread_local._detecting_active = True
        try:
            frame = inspect.currentframe()
            # 向上检查调用链（最多探测 5 层栈帧）
            for _ in range(5):
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

                driver = caller_dict.get("driver")
                if driver is None:
                    continue

                # 显式平台标记判断
                p_attr = getattr(driver, "_platform_name", None)
                if p_attr:
                    return str(p_attr).strip().lower()

                # 鸿蒙原生驱动判断
                if hasattr(driver, "is_healthy") or "harmony" in type(driver).__name__.lower():
                    return "harmonyos"

                # Appium Capabilities 判断
                caps = getattr(driver, "capabilities", None) or getattr(driver, "caps", None)
                if isinstance(caps, dict):
                    p_cap = caps.get("platformName")
                    if p_cap:
                        p_str = str(p_cap).strip().lower()
                        if p_str in ("harmonyos", "openharmony", "hos"):
                            return "harmonyos"
                        elif p_str in ("android",):
                            return "android"
                        elif p_str in ("ios", "apple"):
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
          1. 调用栈 Page 上下文 Driver 探测 (多设备交替调用最高优先级)
          2. 当前线程绑定的独立平台 (多设备并发隔离)
          3. 运行时全局已激活的平台状态
          4. 系统环境变量 PLATFORM
          5. devices.yaml 中配置的 current_platform / platformName (内存单次缓存)
          6. 默认回退 'android'
        """
        # 1. 优先从调用栈当前操作的 Page.driver 探测
        caller_plat = cls.detect_caller_platform()
        if caller_plat:
            return caller_plat

        # 2. 读取当前线程独立绑定的平台
        thread_plat = cls.get_thread_platform()
        if thread_plat:
            return thread_plat

        # 3. 运行时全局激活状态
        if cls._current_platform:
            return cls._current_platform

        # 4. 读取系统环境变量
        env_plat = os.environ.get("PLATFORM")
        if env_plat:
            return env_plat.strip().lower()

        # 5. 读取 devices.yaml 配置（优先读取内存缓存，避免在用例收集阶段反复高频读盘与 YAML 解析）
        if cls._config_platform_cache:
            return cls._config_platform_cache

        try:
            data = load_yaml_data("devices.yaml")
            top_plat = data.get("current_platform")
            if top_plat:
                cls._config_platform_cache = str(top_plat).strip().lower()
                return cls._config_platform_cache
            env_key = data.get("current_env", "dev")
            device_cfg = data.get("devices", {}).get(env_key, {}).get("sender", {})
            platform = str(device_cfg.get("platformName", "Android")).strip().lower()
            cls._config_platform_cache = platform
            return cls._config_platform_cache
        except Exception as e:
            logger.debug(f"{LogIcon.WARN} [LocatorManager] 读取 devices.yaml 平台配置异常: {e}")

        # 6. 兜底默认平台
        return "android"

    @classmethod
    def set_current_platform(cls, platform: str) -> None:
        """在 Driver 实例化或多设备环境切换时动态注入当前设备平台"""
        if platform:
            clean_plat = platform.strip().lower()
            cls.set_thread_platform(clean_plat)
            cls._config_platform_cache = clean_plat
            if cls._current_platform != clean_plat:
                cls._current_platform = clean_plat
                logger.info(f"{LogIcon.SETUP} [LocatorManager] 当前元素定位平台已动态切换为: {clean_plat}")

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
        """重置平台缓存状态"""
        cls._current_platform = None
        cls._config_platform_cache = None
        cls.set_thread_platform(None)


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

    def __getattr__(self, name: str) -> Any:
        target_cls = self._resolve_target_cls()

        # 1. 优先从当前平台的专属 Locator 中获取属性或方法
        if hasattr(target_cls, name):
            attr = getattr(target_cls, name)
            return attr

        # 2. 优雅回退：若专属 Locator 未特别覆盖，安全回退至 Android 基础定位器
        if hasattr(self._android_cls, name):
            return getattr(self._android_cls, name)

        raise AttributeError(
            f"跨端元素定位器代理错误: 平台 '{LocatorPlatformManager.get_current_platform()}' 对应的 "
            f"[{target_cls.__name__}] 及基础类 [{self._android_cls.__name__}] 均未定义属性或方法: '{name}'"
        )

    def __dir__(self):
        target_cls = self._resolve_target_cls()
        attrs = set(dir(target_cls)) | set(dir(self._android_cls))
        return sorted(attrs)

    def __repr__(self) -> str:
        try:
            target_cls = self._resolve_target_cls()
            return f"<DynamicLocatorProxy(active_class='{target_cls.__name__}')>"
        except Exception:
            return f"<DynamicLocatorProxy(base='{self._android_cls.__name__}')>"
