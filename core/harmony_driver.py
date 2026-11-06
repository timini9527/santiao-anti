import json
import logging
import math
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from typing import Any, Dict, List, Optional, Tuple, Union

from lxml import etree
from selenium.common.exceptions import (
    InvalidSelectorException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.logger_utils import LogIcon, logger


# ==============================================================================
# 0. 模块环境探测与 HMNextAuto 核心驱动载入
# ==============================================================================
try:
    from hmnextauto.driver import Driver as HMDriver

    HAVE_HMNEXTAUTO = True
    HMNEXTAUTO_IMPORT_ERROR: Optional[ImportError] = None

    # 仅调整 HMNextAuto 自带的 stderr 控制台处理器，避免误改 FileHandler 等日志输出。
    _hm_logger = logging.getLogger("hmnextauto")
    _hm_logger.setLevel(logging.INFO)
    for _handler in _hm_logger.handlers:
        if (
            isinstance(_handler, logging.StreamHandler)
            and not isinstance(_handler, logging.FileHandler)
            and getattr(_handler, "stream", None) is sys.stderr
        ):
            _handler.setStream(sys.stdout)
            _handler.setLevel(logging.INFO)
except ImportError as import_error:
    HAVE_HMNEXTAUTO = False
    HMNEXTAUTO_IMPORT_ERROR = import_error
    HMDriver = None


class HarmonyDriverError(WebDriverException):
    """鸿蒙驱动基础异常，供上层按 WebDriver 异常统一处理。"""


class HarmonyTransportError(HarmonyDriverError):
    """HDC、设备或底层自动化服务发生可恢复的通信异常。"""

    recoverable_transport_error = True


class HarmonyCommandError(HarmonyDriverError):
    """设备命令已明确执行失败，不应伪装成元素不存在。"""


class HarmonyCommandOutcomeUnknown(HarmonyDriverError):
    """有副作用的命令响应丢失，结果未知时禁止自动重复执行。"""

    command_outcome_unknown = True


class HarmonyLayoutError(HarmonyDriverError):
    """界面树抓取、结构校验或转换失败。"""


# ==============================================================================
# 1. 鸿蒙主驱动生命周期类 (按启动顺序与执行调用链严格排序)
#    启动流程: __init__ -> 唤醒设备 -> 拉起应用 -> 树检索 -> 查找元素 -> 交互手势 -> 截图/探活 -> 会话退出
# ==============================================================================

class HarmonyDriver:
    """
    鸿蒙原生自动化驱动适配器。

    方法按实际调用顺序排列：驱动连接与设备准备、应用生命周期、界面树定位、
    设备交互、截图与健康检查、兼容属性和资源释放。
    """

    _is_harmony_driver = True
    supports_native_gestures = True
    _LOCK_SCREEN_MARKERS = (
        "ScreenLockRootComponent",
        "MainPageView_Screen_Lock",
        "LockIcon_Image_lock",
    )
    _TRANSPORT_ERROR_MARKERS = (
        "target not found",
        "device not found",
        "no devices",
        "hdc server",
        "daemon not running",
        "connection refused",
        "connection reset",
        "offline",
        "channel is being established",
        "e000004",
        "e001005",
    )

    # --------------------------------------------------------------------------
    # 第一阶段：驱动挂载与设备冷启动
    # --------------------------------------------------------------------------

    def __init__(self, desired_caps: Dict[str, Any]):
        """
        步骤 1：读取会话配置，连接设备，然后依次完成设备准备和应用启动。
        """
        if not isinstance(desired_caps, dict):
            raise TypeError("desired_caps 必须是字典")

        self.caps: Dict[str, Any] = dict(desired_caps)
        self.udid = str(self.caps.get("udid", "")).strip()
        self.bundle_name = str(
            self.caps.get("bundleName")
            or self.caps.get("appium:appPackage")
            or "com.santiaohms.im"
        ).strip()
        self.ability_name = str(self.caps.get("abilityName") or "EntryAbility").strip()
        self.module_name = str(self.caps.get("moduleName") or "phone").strip()
        # 读取会话超时配置（单位：秒）
        self.hdc_timeout = self._get_capability_timeout("hdcExecTimeout", default_seconds=20.0)
        self.unlock_timeout = self._get_capability_timeout("unlockTimeout", default_seconds=5.0)
        self._session_id = f"harmony_session_{uuid.uuid4().hex}"
        self._command_lock = threading.RLock()  # 全局命令互斥锁，保证并发安全
        self._implicit_wait = 0.0
        self._closed = False
        self._window_size_cache: Optional[Dict[str, int]] = None
        self.hm: Optional[Any] = None
        self.d: Optional[Any] = None

        logger.info(
            f"{LogIcon.SETUP} [HarmonyDriver] 正在初始化鸿蒙驱动，"
            f"目标设备: {self.udid or '自动识别'}, 应用: {self.bundle_name}"
        )

        self._connect_backend()
        self._wait_for_device_ready()
        self._prepare_device()
        self.activate_app(self.bundle_name)

    def _get_capability_timeout(self, capability_name: str, default_seconds: float) -> float:
        """读取毫秒制 capability，并转换为有下限的秒数。"""
        raw_value = self.caps.get(capability_name)
        if raw_value is None:
            return default_seconds
        try:
            return max(0.1, float(raw_value) / 1000.0)
        except (TypeError, ValueError):
            logger.warning(
                f"{LogIcon.WARN} [HarmonyDriver] {capability_name}={raw_value!r} "
                f"无效，使用默认值 {default_seconds}s"
            )
            return default_seconds

    def _connect_backend(self) -> None:
        """优先连接 HMNextAuto；不可用时显式切换到 HDC 兜底通道。"""
        if HAVE_HMNEXTAUTO and HMDriver:
            try:
                self.hm = HMDriver(serial=self.udid or None)
                self.udid = str(getattr(self.hm, "serial", self.udid)).strip()
                logger.info(
                    f"{LogIcon.SUCCESS} [HarmonyDriver] 已连接 HMNextAuto "
                    f"(设备: {self.udid})"
                )
            except Exception as error:
                logger.warning(
                    f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto 连接失败，"
                    f"将尝试 HDC 兜底通道: {type(error).__name__}: {error}"
                )
        else:
            logger.warning(
                f"{LogIcon.WARN} [HarmonyDriver] 未加载 HMNextAuto，"
                f"使用 HDC 兜底通道: {HMNEXTAUTO_IMPORT_ERROR}"
            )

        if not self.hm and not self.udid:
            targets = self.execute_hdc(("list", "targets"))
            target_list = [
                line.strip().split()[0]
                for line in targets.splitlines()
                if line.strip() and "empty" not in line.lower()
            ]
            if len(target_list) != 1:
                raise HarmonyDriverError(
                    "HDC 兜底模式必须配置 udid，或主机只能连接一台鸿蒙设备"
                )
            self.udid = target_list[0]

        self.d = self.hm

    def _wait_for_device_ready(self, timeout: float = 8.0) -> None:
        """设备探活与通道就绪检查，确保进入测试前 HDC 通信链路已完全打通。"""
        deadline = time.monotonic() + max(1.0, timeout)
        while time.monotonic() < deadline:
            try:
                # 尝试通过轻量 shell 指令探测设备响应
                output = self.execute_hdc_shell("echo ready", timeout=2.0)
                if "ready" in output.lower():
                    logger.info(f"{LogIcon.SUCCESS} [HarmonyDriver] 鸿蒙设备通信通道已成功就绪 ({self.udid})")
                    return
            except HarmonyTransportError as e:
                err_text = str(e).lower()
                if "channel is being established" in err_text or "e000004" in err_text:
                    time.sleep(1.0)
                    continue
                if time.monotonic() >= deadline:
                    raise
                time.sleep(1.0)
        # 最后执行一次探活验证
        self.execute_hdc_shell("echo ready", timeout=2.0)

    def _build_hdc_command(self, command_args: Sequence[str]) -> List[str]:
        """构造不经过 shell 拼接的 HDC 参数列表，避免路径空格被拆分。"""
        full_command = ["hdc"]
        if self.udid:
            full_command.extend(["-t", self.udid])
        full_command.extend(str(argument) for argument in command_args)
        return full_command

    def _run_hdc(self, command_args: Sequence[str], *, timeout: Optional[float] = None, sensitive: bool = False, max_retries: int = 3) -> str:
        """执行 HDC 命令；通道建立中自动平滑重试；超时、非零退出码和错误输出均抛出明确异常。"""
        if self._closed:
            raise HarmonyDriverError("鸿蒙驱动已关闭，不能继续执行 HDC 命令")
        if not command_args:
            raise ValueError("HDC 命令参数不能为空")

        full_command = self._build_hdc_command(command_args)
        effective_timeout = timeout if timeout is not None else self.hdc_timeout
        command_for_log = "<敏感命令已隐藏>" if sensitive else " ".join(full_command)

        for attempt in range(max_retries):
            with self._command_lock:
                try:
                    result = subprocess.run(
                        full_command,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=max(0.1, effective_timeout),
                        check=False,
                    )
                except subprocess.TimeoutExpired as error:
                    transport_error = HarmonyTransportError(
                        f"Harmony HDC 通信超时 ({effective_timeout:.1f}s): {command_for_log}"
                    )
                    if sensitive:
                        raise transport_error from None
                    raise transport_error from error
                except OSError as error:
                    transport_error = HarmonyTransportError(
                        f"Harmony HDC 通信失败: {command_for_log} | {error}"
                    )
                    if sensitive:
                        raise transport_error from None
                    raise transport_error from error

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            combined_output = "\n".join(part for part in (stdout, stderr) if part)
            lowered_output = combined_output.lower()

            # 通道正在建立中 (E000004)，进行自愈等待重试
            if ("channel is being established" in lowered_output or "e000004" in lowered_output) and attempt < max_retries - 1:
                logger.warning(
                    f"{LogIcon.WARN} [HarmonyDriver] HDC 握手通道建立中，等待 1.5 秒后自动重试 ({attempt + 1}/{max_retries})..."
                )
                time.sleep(1.5)
                continue

            has_error_output = "error:" in lowered_output or "[fail]" in lowered_output
            if result.returncode != 0 or has_error_output:
                error_detail = "<敏感输出已隐藏>" if sensitive else combined_output
                error_class = (
                    HarmonyTransportError
                    if any(marker in lowered_output for marker in self._TRANSPORT_ERROR_MARKERS)
                    else HarmonyCommandError
                )
                extra_hint = ""
                if "e001005" in lowered_output or "device not found" in lowered_output or "channel is being established" in lowered_output:
                    extra_hint = (
                        "\n💡【排查指引】鸿蒙真机连接未就绪或未授权 USB 调试：\n"
                        "  1. 请点亮并解锁鸿蒙手机屏幕；\n"
                        "  2. 拔插 USB 数据线，在手机弹出的【是否允许 USB 调试】窗口中勾选【始终允许这台计算机进行调试】并点击确定；\n"
                        "  3. 进入手机【设置】->【系统和更新】->【开发人员选项】，开启【USB 调试】和【'仅充电'模式下允许 USB 调试】，并将 USB 连接模式切换为【传输文件】；\n"
                        "  4. 如仍报错，可在终端执行 `hdc kill -r` 重启 HDC 服务后，执行 `hdc list targets -v` 验证设备状态。"
                    )
                raise error_class(
                    f"HDC 命令执行失败 (exit={result.returncode}): "
                    f"{command_for_log} | {error_detail or '无错误输出'}{extra_hint}"
                )
            return stdout
        return ""

    def execute_hdc(self, command: Union[str, Sequence[str]], *, timeout: Optional[float] = None, sensitive: bool = False) -> str:
        """执行基础 HDC 指令；内部调用优先传入参数序列以保留路径空格。"""
        command_args = (
            shlex.split(command, posix=False)
            if isinstance(command, str)
            else list(command)
        )
        return self._run_hdc(command_args, timeout=timeout, sensitive=sensitive)

    def execute_hdc_shell(self, shell_command: str, *, timeout: Optional[float] = None, sensitive: bool = False) -> str:
        """执行设备端 shell 指令，并保留整条远端命令的参数边界。"""
        return self._run_hdc(("shell", shell_command), timeout=timeout, sensitive=sensitive)

    @staticmethod
    def _remaining_timeout(deadline: float) -> float:
        """返回剩余命令预算，避免一次轮询突破上层总超时。"""
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise HarmonyTransportError("HDC 操作超过总超时预算")
        return remaining

    def _dump_layout_via_hdc(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """通过唯一临时文件抓取界面树，并确保远端临时文件得到清理。"""
        total_timeout = timeout if timeout is not None else self.hdc_timeout
        deadline = time.monotonic() + max(0.1, total_timeout)
        # 使用 uuid 确保多设备并行执行时不产生文件命名冲突
        remote_path = f"/data/local/tmp/santiao_layout_{uuid.uuid4().hex}.json"
        json_content = ""

        with self._command_lock:
            try:
                self.execute_hdc_shell(
                    f"uitest dumpLayout -p {remote_path}",
                    timeout=self._remaining_timeout(deadline),
                )
                json_content = self.execute_hdc_shell(
                    f"cat {remote_path}",
                    timeout=self._remaining_timeout(deadline),
                )
            finally:
                # 无论抓取是否成功，强制清理远端临时文件
                try:
                    self.execute_hdc_shell(
                        f"rm -f {remote_path}",
                        timeout=min(1.0, max(0.1, deadline - time.monotonic())),
                    )
                except HarmonyDriverError as cleanup_error:
                    logger.debug(
                        f"{LogIcon.WARN} [HarmonyDriver] 清理布局临时文件失败: "
                        f"{cleanup_error}"
                    )

        if not json_content:
            raise HarmonyLayoutError("HDC 已返回成功，但界面树内容为空")
        try:
            layout_data = json.loads(json_content)
        except json.JSONDecodeError as error:
            raise HarmonyLayoutError(
                f"鸿蒙界面树不是有效 JSON: {error}"
            ) from error
        if not isinstance(layout_data, dict):
            raise HarmonyLayoutError(
                f"鸿蒙界面树根节点类型无效: {type(layout_data).__name__}"
            )
        return layout_data

    def _get_layout_data(self) -> Dict[str, Any]:
        """优先通过 HMNextAuto 纯内存通道获取界面树；失败时安全回退至 HDC 文件抓取。"""
        with self._command_lock:
            if self.hm:
                try:
                    layout_data = self.hm.dump_hierarchy()
                    if isinstance(layout_data, dict) and layout_data:
                        return layout_data
                    logger.debug(
                        f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto 返回空界面树，"
                        "改用 HDC 重新抓取"
                    )
                except Exception as error:
                    logger.debug(
                        f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto 界面树抓取失败，"
                        f"改用 HDC: {type(error).__name__}: {error}"
                    )
            return self._dump_layout_via_hdc()

    def _execute_side_effect(
        self,
        action_name: str,
        hm_action: Optional[Callable[[], Any]],
        hdc_shell_command: str,
        *,
        sensitive: bool = False,
    ) -> None:
        """
        执行有副作用的设备动作。
        HMNextAuto 响应异常或 HDC 通信中断时，设备端可能已经执行成功，
        因此不能自动切换通道或触发整条用例重放。
        工业级防线：
        1. 状态守卫：驱动已关闭时立即拒绝，防止在退出与清理阶段误报未决未知异常；
        2. 异常隔离：确定性错误（参数错误、主动校验异常）直接抛出，仅通信断连/超时才转为未知结果；
        3. 防重放保障：通信中断后严格禁止通道自动切换或二次重放，杜绝重复点击与脏消息。
        """
        if self._closed:
            raise HarmonyDriverError(f"鸿蒙驱动已关闭，无法执行设备动作: {action_name}")

        with self._command_lock:
            if self.hm and hm_action:
                try:
                    hm_action()
                    return
                except (HarmonyDriverError, ValueError, TypeError):
                    raise
                except Exception as error:
                    error_detail = (
                        "<敏感错误详情已隐藏>"
                        if sensitive
                        else f"{type(error).__name__}: {error}"
                    )
                    outcome_error = HarmonyCommandOutcomeUnknown(
                        f"{action_name}响应异常，设备端执行结果未知，已停止自动重放: "
                        f"{error_detail}"
                    )
                    if sensitive:
                        raise outcome_error from None
                    raise outcome_error from error
            try:
                self.execute_hdc_shell(
                    hdc_shell_command,
                    sensitive=sensitive,
                )
            except HarmonyTransportError as error:
                raise HarmonyCommandOutcomeUnknown(
                    f"{action_name}通信异常，设备端执行结果未知，已停止自动重放: "
                    f"{error}"
                ) from error

    def _press_key_event(self, key_code: int) -> None:
        """通过当前后端派发一个鸿蒙 KeyCode。"""
        self._execute_side_effect(
            f"派发 KeyCode {key_code}",
            (lambda: self.hm.press_key(key_code)) if self.hm else None,
            f"uitest uiInput keyEvent {key_code}",
        )

    @staticmethod
    def _quote_hdc_text(text: str) -> str:
        """转义 HDC shell 文本参数；禁止空字符进入远端命令，换行符平滑清洗。"""
        if "\x00" in text:
            raise ValueError("HDC 文本输入不支持空字符 (Null byte)")
        cleaned = text.replace("\r", "")
        escaped = (
            cleaned.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("$", "\\$")
            .replace("`", "\\`")
            .replace("\n", " ")  # 兜底命令行中换行转为空格，避免破坏远端 Shell 语法
        )
        return f'"{escaped}"'

    def _input_focused_text(self, text: str, x: int, y: int) -> None:
        """向已聚焦输入框写入文本，日志和异常均不输出明文内容（保障安全合规）。"""
        target_x = int(x)
        target_y = int(y)

        # 1. 构建主通道闭包：通过 HMNextAuto 高速 Socket 通道原生传递富文本（完美支持多行/换行）
        hm_action = None
        if self.hm:
            if hasattr(self.hm, "_invoke"):
                hm_action = lambda: self.hm._invoke(
                    "Driver.inputText",
                    args=[{"x": target_x, "y": target_y}, text],
                )
            elif hasattr(self.hm, "input_text"):
                hm_action = lambda: self.hm.input_text(text)

        # 2. 构造 HDC 兜底命令
        quoted_text = self._quote_hdc_text(text)
        self._execute_side_effect(
            "输入文本",
            hm_action,
            f"uitest uiInput inputText {target_x} {target_y} {quoted_text}",
            sensitive=True,
        )

    def _is_device_locked(self, layout_data: Dict[str, Any]) -> bool:
        """根据系统锁屏组件标识判断当前是否处于锁屏界面。"""
        if not layout_data:
            raise HarmonyLayoutError("界面树为空，无法判断设备锁屏状态")
        layout_text = json.dumps(layout_data, ensure_ascii=False)
        return any(marker in layout_text for marker in self._LOCK_SCREEN_MARKERS)

    def _wait_until_unlocked(self, timeout: float) -> bool:
        """在限定时间内轮询可观察的锁屏组件状态。"""
        deadline = time.monotonic() + max(0.1, timeout)
        while time.monotonic() < deadline:
            if not self._is_device_locked(self._get_layout_data()):
                return True
            time.sleep(0.2)
        return False

    def unlock_device(self, password: Optional[str] = None) -> bool:
        """
        步骤 2：唤醒设备并按可观察的锁屏状态完成解锁。

        未显式传入密码时读取 capability 中的 lock_password 或 unlock_password；
        不再使用默认密码，避免配置遗漏时连续输入错误 PIN。
        """
        configured_password = self.caps.get("lock_password") or self.caps.get(
            "unlock_password"
        )
        pwd = str(
            configured_password if password is None else password
        ).strip() if (configured_password is not None or password is not None) else ""

        if self.hm:
            try:
                if not getattr(self.hm, "is_screen_on", True):
                    logger.info(
                        f"{LogIcon.ACTION} [HarmonyDriver] 设备处于息屏状态，"
                        "正在点亮屏幕"
                    )
                    self.hm.screen_on()
            except Exception as error:
                logger.warning(
                    f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto 唤醒失败，"
                    f"使用幂等 HDC 唤醒命令: {type(error).__name__}: {error}"
                )
                self.execute_hdc_shell("power-shell wakeup")
        else:
            self.execute_hdc_shell("power-shell wakeup")
        time.sleep(0.2)

        layout = self._get_layout_data()
        if not self._is_device_locked(layout):
            logger.debug(
                f"{LogIcon.SUCCESS} [HarmonyDriver] 设备当前未处于锁屏状态"
            )
            return True

        logger.info(
            f"{LogIcon.ACTION} [HarmonyDriver] 检测到锁屏界面，正在呼出解锁输入区"
        )
        window_size = self.get_window_size()
        width = window_size["width"]
        height = window_size["height"]
        middle_x = width // 2
        start_y = int(height * 0.85)
        end_y = int(height * 0.15)
        self._execute_side_effect(
            "上滑解锁",
            (
                lambda: self.hm.swipe(
                    middle_x,
                    start_y,
                    middle_x,
                    end_y,
                    speed=6000,
                )
            )
            if self.hm
            else None,
            f"uitest uiInput swipe {middle_x} {start_y} {middle_x} {end_y} 6000",
        )
        time.sleep(0.2)

        if not pwd:
            if self._wait_until_unlocked(timeout=min(1.0, self.unlock_timeout)):
                return True
            raise HarmonyDriverError(
                "设备需要锁屏密码，但 capability 未配置 lock_password"
            )

        logger.info(
            f"{LogIcon.ACTION} [HarmonyDriver] 正在输入锁屏密码 "
            f"(长度: {len(pwd)} 位)"
        )
        if pwd.isdigit():
            # 鸿蒙数字键 KeyCode：0 对应 2000，1~9 对应 2001~2009。
            for digit in pwd:
                self._press_key_event(2000 + int(digit))
                time.sleep(0.06)
        else:
            self._input_focused_text(pwd, middle_x, height // 2)

        if self._wait_until_unlocked(timeout=self.unlock_timeout):
            logger.info(
                f"{LogIcon.SUCCESS} [HarmonyDriver] 已确认设备退出锁屏界面"
            )
            return True

        logger.info(
            f"{LogIcon.ACTION} [HarmonyDriver] 锁屏仍存在，补发一次 Enter 后复核"
        )
        self._press_key_event(2054)
        if self._wait_until_unlocked(timeout=min(2.0, self.unlock_timeout)):
            logger.info(
                f"{LogIcon.SUCCESS} [HarmonyDriver] 已确认设备退出锁屏界面"
            )
            return True
        raise HarmonyDriverError("锁屏密码输入后仍检测到锁屏界面，设备解锁失败")

    def _prepare_device(self) -> None:
        """
        步骤 3：准备设备；只有确认解锁后才允许继续启动应用。
        """
        if not self.unlock_device():
            raise HarmonyDriverError("鸿蒙设备准备失败：未能确认设备已解锁")

    def activate_app(self, bundle_id: Optional[str] = None) -> None:
        """
        步骤 4：启动或拉起目标应用。

        此方法只负责确认启动命令成功下发；页面渲染完成仍由 Page Object 显式等待。
        """
        target_bundle = bundle_id or self.bundle_name
        logger.info(
            f"{LogIcon.ACTION} [HarmonyDriver] 启动鸿蒙应用: "
            f"{target_bundle}/{self.ability_name}"
        )
        self._execute_side_effect(
            "启动应用",
            (
                lambda: self.hm.start_app(
                    target_bundle,
                    page_name=self.ability_name,
                )
            )
            if self.hm
            else None,
            f"aa start -b {target_bundle} -a {self.ability_name} "
            f"-m {self.module_name}",
        )
        time.sleep(0.2)

    def terminate_app(self, bundle_id: Optional[str] = None) -> None:
        """终止目标鸿蒙应用进程。"""
        target_bundle = bundle_id or self.bundle_name
        logger.info(f"{LogIcon.ACTION} [HarmonyDriver] 终止鸿蒙应用: {target_bundle}")
        self._execute_side_effect(
            "终止应用",
            (lambda: self.hm.stop_app(target_bundle)) if self.hm else None,
            f"aa force-stop {target_bundle}",
        )
        time.sleep(0.1)

    def is_app_installed(self, bundle_id: Optional[str] = None) -> bool:
        """检查目标鸿蒙应用是否已安装（优先读取 HMNextAuto，兜底走 bm dump）。"""
        target_bundle = (bundle_id or self.bundle_name).strip()
        if self.hm and hasattr(self.hm, "has_app"):
            try:
                return bool(self.hm.has_app(target_bundle))
            except Exception as error:
                logger.debug(f"{LogIcon.WARN} [HarmonyDriver] has_app 查询异常: {error}")
        output = self.execute_hdc_shell(f"bm dump -n {target_bundle}")
        return target_bundle in output and "error" not in output.lower()

    def install_app(self, app_path: str) -> None:
        """安装指定路径的鸿蒙应用包 (HAP)。"""
        logger.info(f"{LogIcon.ACTION} [HarmonyDriver] 安装应用: {app_path}")
        if self.hm and hasattr(self.hm, "install_app"):
            try:
                self.hm.install_app(app_path)
                return
            except Exception as error:
                logger.debug(f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto 安装失败，回退 HDC: {error}")
        self.execute_hdc(("install", os.path.abspath(app_path)))

    def remove_app(self, bundle_id: Optional[str] = None) -> None:
        """卸载目标应用（兼容 Appium remove_app 接口）。"""
        target_bundle = (bundle_id or self.bundle_name).strip()
        logger.info(f"{LogIcon.ACTION} [HarmonyDriver] 卸载应用: {target_bundle}")
        if self.hm and hasattr(self.hm, "uninstall_app"):
            try:
                self.hm.uninstall_app(target_bundle)
                return
            except Exception as error:
                logger.debug(f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto 卸载失败，回退 HDC: {error}")
        self.execute_hdc(("uninstall", target_bundle))

    def uninstall_app(self, bundle_id: Optional[str] = None) -> None:
        """卸载目标应用（规范别名）。"""
        self.remove_app(bundle_id)

    def open_url(self, url: str) -> None:
        """唤起指定 DeepLink 或标准 Web 链接。"""
        logger.info(f"{LogIcon.ACTION} [HarmonyDriver] 打开链接: {url}")
        if self.hm and hasattr(self.hm, "open_url"):
            try:
                self.hm.open_url(url)
                return
            except Exception as error:
                logger.debug(f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto open_url 失败，回退 HDC: {error}")
        self.execute_hdc_shell(f"aa start -U {shlex.quote(url)}")

    def get(self, url: str) -> None:
        """Selenium/Appium 标准导航方法，打开指定链接。"""
        self.open_url(url)

    def get_toast(self, timeout: float = 3.0) -> Optional[str]:
        """优先利用 HMNextAuto 原生 toast_watcher 监听并捕获系统 Toast 消息。"""
        if self.hm and hasattr(self.hm, "toast_watcher"):
            try:
                self.hm.toast_watcher.start()
                toast = self.hm.toast_watcher.get_toast(timeout=int(timeout))
                if toast:
                    logger.info(f"{LogIcon.SUCCESS} [HarmonyDriver] 原生 Toast 捕获成功: {toast}")
                    return str(toast)
            except Exception as error:
                logger.debug(f"{LogIcon.WARN} [HarmonyDriver] toast_watcher 捕获异常: {error}")
        return None

    @staticmethod
    def _find_layout_attribute(node: Dict[str, Any], attribute_name: str) -> Optional[str]:
        """递归读取界面树中首个非空属性值（深度优先遍历）。"""
        attributes = node.get("attributes", {})
        if isinstance(attributes, dict):
            value = attributes.get(attribute_name)
            if value:
                return str(value)
        children = node.get("children", [])
        if not isinstance(children, list):
            return None
        for child in children:
            if not isinstance(child, dict):
                continue
            value = HarmonyDriver._find_layout_attribute(child, attribute_name)
            if value:
                return value
        return None

    @property
    def current_package(self) -> str:
        """获取实际前台应用包名，不能直接返回目标配置值造成假阳性。"""
        if self.hm:
            try:
                package_name, _ = self.hm.current_app()
                if package_name:
                    return str(package_name)
            except Exception as error:
                logger.debug(
                    f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto 前台应用查询失败，"
                    f"改从界面树读取: {type(error).__name__}: {error}"
                )
        layout_data = self._get_layout_data()
        return self._find_layout_attribute(layout_data, "bundleName") or ""

    def query_app_state(self, bundle_id: Optional[str] = None) -> int:
        """
        查询目标应用运行状态（兼容 Appium 状态码约定：4=前台运行，1=后台或未前台运行）。
        """
        target_bundle = (bundle_id or self.bundle_name).strip()
        try:
            if self.current_package == target_bundle:
                return 4
        except Exception as error:
            logger.debug(
                f"{LogIcon.WARN} [HarmonyDriver] 查询应用状态异常: {type(error).__name__}: {error}"
            )
        return 1

    def execute_script(self, script: str, *args: Any) -> Any:
        """兼容 Appium 扩展脚本指令（如 mobile: startActivity、mobile: replaceElementValue、mobile: deepLink、mobile: shell）。"""
        cmd = str(script or "").strip()
        payload = args[0] if args and isinstance(args[0], dict) else {}
        if cmd == "mobile: startActivity":
            intent = str(payload.get("intent") or "")
            pkg = intent.split("/")[0].strip() if "/" in intent else self.bundle_name
            self.activate_app(pkg or self.bundle_name)
            return True
        if cmd == "mobile: replaceElementValue":
            text = str(payload.get("text") or "")
            self.input_text(text)
            return True
        if cmd == "mobile: deepLink":
            url = str(payload.get("url") or "")
            if url:
                self.open_url(url)
                return True
        if cmd == "mobile: shell":
            command = str(
                payload.get("command")
                or (args[0] if args and isinstance(args[0], str) else "")
            )
            if command:
                return self.execute_hdc_shell(command)
        logger.debug(f"{LogIcon.WARN} [HarmonyDriver] 忽略未适配的 execute_script 指令: {cmd}")
        return None

    # --------------------------------------------------------------------------
    # 第二阶段：界面树解析与元素定位检索 (用例执行主通道)
    # --------------------------------------------------------------------------

    @staticmethod
    def _safe_xml_name(name: Any, prefix: str) -> str:
        """将 ArkUI 标签或属性名转换为合法且稳定的 XML 名称。"""
        cleaned_name = re.sub(r"[^\w\.-]", "_", str(name or ""))
        if not cleaned_name or not (
            cleaned_name[0].isalpha() or cleaned_name[0] == "_"
        ):
            cleaned_name = f"{prefix}_{cleaned_name or 'unknown'}"
        if cleaned_name.lower().startswith("xml"):
            cleaned_name = f"{prefix}_{cleaned_name}"
        return cleaned_name

    @staticmethod
    def _normalized_node_attributes(node: Dict[str, Any]) -> Dict[str, str]:
        """规范化节点属性，并补齐 BasePage 常用的 Appium 属性别名（如 resource-id 与 content-desc）。"""
        raw_attributes = node.get("attributes", {})
        if not isinstance(raw_attributes, dict):
            raise HarmonyLayoutError("界面树节点 attributes 必须是字典")

        attributes: Dict[str, str] = {}
        for key, value in raw_attributes.items():
            if isinstance(value, bool):
                attributes[str(key)] = "true" if value else "false"
            elif isinstance(value, (str, int, float)):
                attributes[str(key)] = str(value)

        # 映射常用属性别名，确保 Appium 传统测试用例无缝运行
        node_id = attributes.get("id") or attributes.get("key")
        if node_id:
            attributes.setdefault("resource-id", node_id)
        description = (
            attributes.get("content-desc")
            or attributes.get("description")
            or attributes.get("accessibilityText")
        )
        if description:
            attributes.setdefault("content-desc", description)
        return attributes

    def _build_xml_tree(self, layout_root: Dict[str, Any], *, include_node_index: bool) -> Tuple[Any, List[Dict[str, Any]]]:
        """构建 XPath 与 page_source 共用的标准 XML 树，并映射原始节点索引。"""
        if not isinstance(layout_root, dict):
            raise HarmonyLayoutError("界面树根节点必须是字典")

        node_map: List[Dict[str, Any]] = []
        hierarchy = etree.Element("Hierarchy", attrib={"platform": "HarmonyOS"})

        def append_node(node: Dict[str, Any], parent: Any) -> None:
            if not isinstance(node, dict):
                raise HarmonyLayoutError("界面树子节点必须是字典")

            attributes = self._normalized_node_attributes(node)
            tag_name = self._safe_xml_name(
                attributes.get("type") or "Component",
                "comp",
            )
            xml_attributes = {
                self._safe_xml_name(key, "attr"): value
                for key, value in attributes.items()
            }
            if include_node_index:
                xml_attributes["_node_idx"] = str(len(node_map))
            node_map.append(node)
            element = etree.SubElement(
                parent,
                tag_name,
                attrib=xml_attributes,
            )

            children = node.get("children", [])
            if children is None:
                return
            if not isinstance(children, list):
                raise HarmonyLayoutError("界面树节点 children 必须是列表")
            for child in children:
                append_node(child, element)

        append_node(layout_root, hierarchy)
        return hierarchy, node_map

    def _find_by_xpath(self, layout_root: Dict[str, Any], xpath_expression: str) -> List[Dict[str, Any]]:
        """使用 lxml 引擎执行 W3C XPath 1.0 查询，支持层级轴、谓词索引和属性匹配。"""
        hierarchy, node_map = self._build_xml_tree(
            layout_root,
            include_node_index=True,
        )
        try:
            results = hierarchy.xpath(xpath_expression)
        except etree.XPathError as error:
            raise InvalidSelectorException(
                f"无效的鸿蒙 XPath: {xpath_expression} | {error}"
            ) from error

        matched_nodes: List[Dict[str, Any]] = []
        for result in results:
            if not isinstance(result, etree._Element):
                continue
            node_index = result.get("_node_idx")
            if node_index is not None:
                matched_nodes.append(node_map[int(node_index)])
        return matched_nodes

    def _search_nodes_by_strategy(
        self,
        root_node: Dict[str, Any],
        by: str,
        value: str,
    ) -> List[Dict[str, Any]]:
        """在指定节点子树中按定位策略检索匹配节点（纯内存检索，零额外 IPC 开销）。"""
        if not root_node:
            return []

        if by == By.XPATH:
            return self._find_by_xpath(root_node, value)

        supported_strategies = {
            By.ID,
            By.CLASS_NAME,
            By.TAG_NAME,
            By.NAME,
            By.LINK_TEXT,
            By.PARTIAL_LINK_TEXT,
            "accessibility id",
        }
        if by not in supported_strategies:
            raise InvalidSelectorException(f"鸿蒙驱动暂不支持定位策略: {by}")

        matched_nodes: List[Dict[str, Any]] = []

        def search_node(node: Dict[str, Any]) -> None:
            attributes = self._normalized_node_attributes(node)
            hit = False

            if by == By.ID:
                clean_target = value.split("/")[-1].split(":")[-1]
                node_id = attributes.get("id", "")
                node_key = attributes.get("key", "")
                resource_id = attributes.get("resource-id", "")
                if value in (node_id, node_key, resource_id) or clean_target in (
                    node_id,
                    node_key,
                    resource_id,
                ):
                    hit = True
            elif by in (By.CLASS_NAME, By.TAG_NAME):
                if attributes.get("type") == value:
                    hit = True
            elif by in (By.NAME, By.LINK_TEXT):
                if value in (
                    attributes.get("text"),
                    attributes.get("originalText"),
                    attributes.get("name"),
                ):
                    hit = True
            elif by == By.PARTIAL_LINK_TEXT:
                text_value = attributes.get("originalText") or attributes.get(
                    "text",
                    "",
                )
                hit = value in text_value
            elif by == "accessibility id":
                hit = attributes.get("content-desc") == value

            if hit:
                matched_nodes.append(node)

            children = node.get("children", []) or []
            if not isinstance(children, list):
                raise HarmonyLayoutError("界面树节点 children 必须是列表")
            for child in children:
                if isinstance(child, dict):
                    search_node(child)

        search_node(root_node)
        return matched_nodes

    def find_elements(self, by: str, value: str) -> List["HarmonyWebElement"]:
        """
        步骤 5：根据定位策略查找当前屏幕内的所有匹配节点。
        """
        layout_root = self._get_layout_data()
        if not layout_root:
            return []

        matched_nodes = self._search_nodes_by_strategy(layout_root, by, value)
        return [
            HarmonyWebElement(self, node, layout_root=layout_root)
            for node in matched_nodes
        ]

    def find_element(self, by: str, value: str) -> "HarmonyWebElement":
        """
        步骤 6：返回首个匹配元素；合法定位无结果时抛出 NoSuchElementException。
        """
        elements = self.find_elements(by, value)
        if not elements:
            raise NoSuchElementException(f"在鸿蒙界面中无法通过 {by}='{value}' 定位到元素")
        return elements[0]

    @property
    def page_source(self) -> str:
        """返回与 XPath 查询使用同一规范化规则生成的 XML 页面源。"""
        data = self._get_layout_data()
        if not data:
            return "<Hierarchy />"
        hierarchy, _ = self._build_xml_tree(
            data,
            include_node_index=False,
        )
        return etree.tostring(hierarchy, encoding="unicode")

    # --------------------------------------------------------------------------
    # 第三阶段：设备级交互与全局手势
    # --------------------------------------------------------------------------

    def tap(self, positions: List[Tuple[int, int]], duration: Optional[int] = None) -> None:
        """按顺序点击屏幕坐标；较长 duration 按长按处理。"""
        for x, y in positions:
            if duration is not None and duration >= 500:
                self.long_click(int(x), int(y))
            else:
                self._execute_side_effect(
                    "点击屏幕",
                    (lambda: self.hm.click(int(x), int(y))) if self.hm else None,
                    f"uitest uiInput click {int(x)} {int(y)}",
                )

    def double_click(self, x: int, y: int) -> None:
        """双击指定屏幕坐标。"""
        self._execute_side_effect(
            "双击屏幕",
            (lambda: self.hm.double_click(x, y)) if self.hm else None,
            f"uitest uiInput doubleClick {x} {y}",
        )

    def long_click(self, x: int, y: int) -> None:
        """长按指定屏幕坐标。"""
        self._execute_side_effect(
            "长按屏幕",
            (lambda: self.hm.long_click(x, y)) if self.hm else None,
            f"uitest uiInput longClick {x} {y}",
        )

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 800) -> None:
        """按欧氏距离与目标耗时动态计算像素速度 (px/s) 执行滑动。"""
        distance = math.hypot(end_x - start_x, end_y - start_y)
        duration_seconds = max(0.001, duration / 1000.0)
        speed = max(200, min(40000, int(distance / duration_seconds)))  # 限制在系统安全速度区间 [200, 40000]
        self._execute_side_effect(
            "滑动屏幕",
            (
                lambda: self.hm.swipe(
                    start_x,
                    start_y,
                    end_x,
                    end_y,
                    speed=speed,
                )
            )
            if self.hm
            else None,
            f"uitest uiInput swipe {start_x} {start_y} {end_x} {end_y} {speed}",
        )
        time.sleep(0.1)

    def back(self) -> None:
        """触发一次系统返回键；响应异常时不自动重放。"""
        logger.debug(f"{LogIcon.ACTION} [HarmonyDriver] 触发系统返回键")
        self._execute_side_effect(
            "系统返回",
            (lambda: self.hm.press_back()) if self.hm else None,
            "uitest uiInput keyEvent 2",
        )
        time.sleep(0.1)

    def press_keycode(self, keycode: int) -> None:
        """兼容 BasePage 常用 Android KeyCode，并映射为鸿蒙 KeyCode (Back:4->2, Enter:66->2054, Del:67->2055)。"""
        keycode_mapping = {
            4: 2,       # Back 返回键
            66: 2054,   # Enter 回车键
            67: 2055,   # Backspace 退格删除键
        }
        self._press_key_event(keycode_mapping.get(keycode, keycode))

    def input_text(self, text: str, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """向当前焦点输入文本；若未指定坐标则自动取屏幕几何中心点。"""
        if x is None or y is None:
            window_size = self.get_window_size()
            x = window_size["width"] // 2
            y = window_size["height"] // 2
        logger.info(
            f"{LogIcon.ACTION} [HarmonyDriver] 输入文本 (长度: {len(text)})"
        )
        self._input_focused_text(text, x, y)

    def clear_text(self, character_count: int = 30) -> None:
        """通过受限次数的退格清空当前输入框，避免无上限循环（单次最多 200 次）。"""
        delete_count = max(1, min(200, character_count))
        for _ in range(delete_count):
            self._press_key_event(2055)

    def get_window_size(self, windowHandle: str = "current") -> Dict[str, int]:
        """获取物理屏幕尺寸（带会话级缓存，避免高频滑动与定位时重复触发 IPC 查询）。"""
        _ = windowHandle
        if self._window_size_cache is not None:
            return dict(self._window_size_cache)

        if self.hm:
            try:
                display_size = self.hm.display_size
                if display_size and len(display_size) >= 2:
                    width = int(display_size[0])
                    height = int(display_size[1])
                    if width > 0 and height > 0:
                        self._window_size_cache = {"width": width, "height": height}
                        return dict(self._window_size_cache)
            except Exception as error:
                logger.debug(
                    f"{LogIcon.WARN} [HarmonyDriver] HMNextAuto 屏幕尺寸探测失败，"
                    f"改用 HDC: {type(error).__name__}: {error}"
                )

        output = self.execute_hdc_shell("hidumper -s RenderService -a screen")
        active_mode = re.search(
            r"activeMode:\s*(\d+)x(\d+)",
            output,
        )
        if active_mode:
            self._window_size_cache = {
                "width": int(active_mode.group(1)),
                "height": int(active_mode.group(2)),
            }
            return dict(self._window_size_cache)

        display_rect = re.search(
            r"displayRect:\s*\[(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\]",
            output,
        )
        if display_rect:
            left, top, right, bottom = map(int, display_rect.groups())
            width = right - left
            height = bottom - top
            if width > 0 and height > 0:
                self._window_size_cache = {"width": width, "height": height}
                return dict(self._window_size_cache)

        configured_width = self.caps.get("screenWidth")
        configured_height = self.caps.get("screenHeight")
        if configured_width and configured_height:
            width = int(configured_width)
            height = int(configured_height)
            if width > 0 and height > 0:
                logger.warning(
                    f"{LogIcon.WARN} [HarmonyDriver] 使用 capability 中配置的"
                    f"屏幕尺寸: {width}x{height}"
                )
                self._window_size_cache = {"width": width, "height": height}
                return dict(self._window_size_cache)
        raise HarmonyCommandError("无法获取有效的鸿蒙设备屏幕尺寸")

    # --------------------------------------------------------------------------
    # 第四阶段：截图捕获与设备健康监测 (用例断言与报告保障)
    # --------------------------------------------------------------------------

    @staticmethod
    def _read_png_file(file_path: str) -> bytes:
        """读取并校验 PNG 文件，若底层拉取为 JPEG 则自动无损转换为标准 PNG 数据。"""
        try:
            with open(file_path, "rb") as image_file:
                image_data = image_file.read()
        except OSError as error:
            raise HarmonyCommandError(f"读取截图文件失败: {error}") from error

        if not image_data:
            raise HarmonyCommandError("截图文件为空")

        # 1. 规范 PNG 格式直接返回
        if image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            return image_data

        # 2. 若底层通过 snapshot_display 产出了 JPEG 格式，自适应无损转换为标准 PNG
        if image_data.startswith(b"\xff\xd8"):
            try:
                from PIL import Image
                import io

                with Image.open(io.BytesIO(image_data)) as img:
                    png_buf = io.BytesIO()
                    img.save(png_buf, format="PNG")
                    png_data = png_buf.getvalue()
                    try:
                        with open(file_path, "wb") as f_out:
                            f_out.write(png_data)
                    except Exception:
                        pass
                    return png_data
            except Exception as conv_err:
                logger.debug(
                    f"{LogIcon.WARN} [HarmonyDriver] JPEG 转 PNG 兼容处理异常: {conv_err}"
                )

        raise HarmonyCommandError("截图文件不是有效的 PNG 或 JPEG 图像数据")

    def _capture_screenshot_via_hdc(self, local_path: str) -> None:
        """通过 HDC 抓取截图，优先采用底层 snapshot_display 静默截屏，若不可用则平滑降级至 uitest screenCap 兜底。"""
        uid = uuid.uuid4().hex
        # 1. 优先尝试显存直接静默截屏 (snapshot_display 规范要求后缀必须为 .jpeg)
        remote_shot = f"/data/local/tmp/santiao_screen_{uid}.jpeg"
        try:
            self.execute_hdc_shell(f"snapshot_display -f {remote_shot}")
            self.execute_hdc(
                ("file", "recv", remote_shot, os.path.abspath(local_path))
            )
            if os.path.exists(local_path) and os.path.getsize(local_path) > 100:
                return
        except Exception:
            pass
        finally:
            try:
                self.execute_hdc_shell(
                    f"rm -f {remote_shot}",
                    timeout=min(1.0, self.hdc_timeout),
                )
            except Exception:
                pass

        # 2. 备用静默截屏 (显式指定主屏 0)
        remote_shot = f"/data/local/tmp/santiao_screen_{uid}_d0.jpeg"
        try:
            self.execute_hdc_shell(f"snapshot_display -d 0 -f {remote_shot}")
            self.execute_hdc(
                ("file", "recv", remote_shot, os.path.abspath(local_path))
            )
            if os.path.exists(local_path) and os.path.getsize(local_path) > 100:
                return
        except Exception:
            pass
        finally:
            try:
                self.execute_hdc_shell(
                    f"rm -f {remote_shot}",
                    timeout=min(1.0, self.hdc_timeout),
                )
            except Exception:
                pass

        # 3. 终极安全兜底方案：uitest screenCap
        remote_path = f"/data/local/tmp/santiao_screen_{uid}_cap.png"
        try:
            self.execute_hdc_shell(f"uitest screenCap -p {remote_path}")
            self.execute_hdc(
                ("file", "recv", remote_path, os.path.abspath(local_path))
            )
        finally:
            try:
                self.execute_hdc_shell(
                    f"rm -f {remote_path}",
                    timeout=min(1.0, self.hdc_timeout),
                )
            except HarmonyDriverError as cleanup_error:
                logger.debug(
                    f"{LogIcon.WARN} [HarmonyDriver] 清理截图临时文件失败: "
                    f"{cleanup_error}"
                )

    def get_screenshot_as_png(self) -> bytes:
        """截取当前屏幕并返回 PNG 字节流（优先使用 HDC snapshot_display 静默截屏，避免触发 IM 截屏系统通知）。"""
        with tempfile.TemporaryDirectory(prefix="santiao_harmony_") as temp_dir:
            local_path = os.path.join(temp_dir, "screen.png")
            try:
                self._capture_screenshot_via_hdc(local_path)
                if os.path.exists(local_path) and os.path.getsize(local_path) > 100:
                    return self._read_png_file(local_path)
            except Exception as hdc_error:
                logger.debug(
                    f"{LogIcon.WARN} [HarmonyDriver] HDC 静默截图失败，回退至 HMNextAuto: {hdc_error}"
                )

            if self.hm:
                with self._command_lock:
                    self.hm.screenshot(local_path, method="screenCap")
                return self._read_png_file(local_path)

            raise HarmonyCommandError("无法完成鸿蒙屏幕截图")

    def get_screenshot_as_file(self, filename: str) -> bool:
        """截取当前屏幕并将有效 PNG 数据保存到指定本地路径。"""
        absolute_path = os.path.abspath(filename)
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        screenshot_data = self.get_screenshot_as_png()
        try:
            with open(absolute_path, "wb") as image_file:
                image_file.write(screenshot_data)
        except OSError as error:
            raise HarmonyCommandError(f"保存截图文件失败: {error}") from error
        return True

    def is_healthy(self, timeout: float = 2.0) -> bool:
        """在总超时内检查设备在线状态与 UiTest 界面树服务。"""
        if self._closed:
            return False

        try:
            deadline = time.monotonic() + max(0.1, float(timeout))
            targets = self.execute_hdc(
                ("list", "targets"),
                timeout=self._remaining_timeout(deadline),
            )
            target_list = {
                line.strip().split()[0]
                for line in targets.splitlines()
                if line.strip() and "empty" not in line.lower()
            }
            if self.udid and self.udid not in target_list:
                return False
            if not self.udid and not target_list:
                return False

            # 优先走高速内存界面树通道，不可用时平滑降级走 HDC 文件抓取
            layout_data = self._get_layout_data()
            return bool(layout_data)
        except (HarmonyDriverError, TypeError, ValueError) as error:
            logger.debug(
                f"{LogIcon.WARN} [HarmonyDriver] 健康检查失败: "
                f"{type(error).__name__}: {error}"
            )
            return False

    # --------------------------------------------------------------------------
    # 第五阶段：会话兼容属性与退出销毁 (Teardown)
    # --------------------------------------------------------------------------

    @property
    def capabilities(self) -> Dict[str, Any]:
        """返回 Capabilities 副本，避免调用方意外修改会话配置。"""
        return dict(self.caps)

    @property
    def session_id(self) -> str:
        """返回会话唯一标识符"""
        return self._session_id

    @property
    def w3c(self) -> bool:
        """当前适配器不实现 Selenium W3C Actions 的 execute 协议。"""
        return False

    @property
    def raw_driver(self) -> "HarmonyDriver":
        """获取底层原生驱动对象引用"""
        return self

    def implicitly_wait(self, time_to_wait: float) -> None:
        """保存兼容等待值，并同步下发至 HMNextAuto 客户端配置。"""
        wait_seconds = float(time_to_wait)
        if wait_seconds < 0 or not math.isfinite(wait_seconds):
            raise ValueError("隐式等待时间必须是非负有限数值")
        self._implicit_wait = wait_seconds
        if self.hm and hasattr(self.hm, "implicitly_wait"):
            try:
                self.hm.implicitly_wait(wait_seconds)
            except Exception as error:
                logger.debug(f"{LogIcon.WARN} [HarmonyDriver] 同步 implicitly_wait 异常: {error}")

    def quit(self) -> None:
        """幂等关闭会话，并释放 HMNextAuto 按设备维护的单例实例。"""
        if self._closed:
            return

        logger.info(f"{LogIcon.SETUP} [HarmonyDriver] 退出鸿蒙测试会话 (设备: {self.udid})")
        harmony_backend = self.hm
        try:
            if harmony_backend:
                try:
                    harmony_backend.close()
                except Exception as error:
                    # close 异常时仍尝试解除 HMNextAuto 单例，避免恢复时复用坏连接。
                    unregister = getattr(
                        harmony_backend,
                        "_unregister_singleton_if_self",
                        None,
                    )
                    if callable(unregister):
                        try:
                            unregister()
                        except Exception as unregister_error:
                            logger.debug(
                                f"{LogIcon.WARN} [HarmonyDriver] 解除 HMNextAuto "
                                f"单例失败: {unregister_error}"
                            )
                    logger.warning(
                        f"{LogIcon.WARN} [HarmonyDriver] 关闭 HMNextAuto 会话失败: "
                        f"{type(error).__name__}: {error}"
                    )
        finally:
            self.hm = None
            self.d = None
            self._closed = True


# ==============================================================================
# 2. 鸿蒙元素代理对象类 (按元素查找到交互调用的顺序排列)
#    交互流程: __init__ -> 坐标解析 -> 状态与属性查询 -> 点击/长按/输入/清理
# ==============================================================================

class HarmonyWebElement:
    """
    鸿蒙原生 UI 元素轻量适配对象。

    仅实现项目 BasePage 已使用的 WebElement 接口；元素交互统一回到 Driver，
    使通信异常能够经过 RecoverableDriver 处理。
    """

    _is_harmony_element = True

    # --------------------------------------------------------------------------
    # 第一阶段：实例构造与矩形边界计算
    # --------------------------------------------------------------------------

    def __init__(
        self,
        driver: Any,
        node_data: Dict[str, Any],
        layout_root: Optional[Dict[str, Any]] = None,
    ):
        """步骤 1：绑定 Driver，并保存当前界面树快照中的节点属性与上下文根树。"""
        self._raw_driver = driver
        self.driver = driver
        self.node_data = node_data
        self._layout_root = layout_root
        self.attributes = HarmonyDriver._normalized_node_attributes(node_data)
        self._init_bounds()

    def _bind_command_driver(self, driver: Any) -> "HarmonyWebElement":
        """将元素动作绑定到可恢复代理，而不是固定在旧的底层 Driver。"""
        self.driver = driver
        return self

    def _collect_descendant_ids(self) -> set[int]:
        """收集当前节点下的所有严格后代节点内存 ID，用于子元素检索过滤。"""
        descendant_ids: set[int] = set()

        def walk(node: Dict[str, Any]) -> None:
            for child in node.get("children", []) or []:
                if isinstance(child, dict):
                    descendant_ids.add(id(child))
                    walk(child)

        walk(self.node_data)
        return descendant_ids

    def find_elements(self, by: str, value: str) -> List["HarmonyWebElement"]:
        """
        在当前元素子树内检索匹配的子元素（纯内存快照检索，支持相对路径与全路径 XPath 过滤）。
        """
        descendant_ids = self._collect_descendant_ids()
        if not descendant_ids:
            return []

        raw_driver: HarmonyDriver = getattr(self, "_raw_driver", self.driver)
        candidates = raw_driver._search_nodes_by_strategy(self.node_data, by, value)
        matched = [node for node in candidates if id(node) in descendant_ids]

        if not matched and by == By.XPATH and self._layout_root is not None:
            full_candidates = raw_driver._search_nodes_by_strategy(
                self._layout_root, by, value
            )
            matched = [node for node in full_candidates if id(node) in descendant_ids]

        return [
            HarmonyWebElement(
                raw_driver,
                node,
                layout_root=self._layout_root,
            )._bind_command_driver(self.driver)
            for node in matched
        ]

    def find_element(self, by: str, value: str) -> "HarmonyWebElement":
        """在当前元素子树内查找首个匹配子元素，未找到时抛出 NoSuchElementException。"""
        elements = self.find_elements(by, value)
        if not elements:
            raise NoSuchElementException(
                f"在当前鸿蒙父元素({self.tag_name})下无法通过 {by}='{value}' 定位到子元素"
            )
        return elements[0]

    def _init_bounds(self) -> None:
        """步骤 2：解析 `[left,top][right,bottom]` 矩形边界并计算几何中心点坐标。"""
        bounds_value = self.attributes.get("bounds", "[0,0][0,0]")
        match = re.fullmatch(
            r"\[\s*(-?\d+)\s*,\s*(-?\d+)\s*\]"
            r"\[\s*(-?\d+)\s*,\s*(-?\d+)\s*\]",
            str(bounds_value),
        )
        if match:
            self.left, self.top, self.right, self.bottom = map(
                int,
                match.groups(),
            )
        else:
            self.left = self.top = self.right = self.bottom = 0

        # 计算点击中心点与组件宽高尺寸
        self.center_x = (self.left + self.right) // 2
        self.center_y = (self.top + self.bottom) // 2
        self.width = max(0, self.right - self.left)
        self.height = max(0, self.bottom - self.top)

    def _ensure_interactable(self) -> None:
        """拒绝对无有效边界的节点注入坐标，避免误触屏幕左上角。"""
        if self.width <= 0 or self.height <= 0:
            raise HarmonyCommandError(
                f"元素缺少有效 bounds，无法执行交互: {self.tag_name}"
            )

    @staticmethod
    def _as_bool(value: Any, default: bool) -> bool:
        """兼容界面树中的布尔值与字符串布尔值。"""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() not in {
            "",
            "0",
            "false",
            "none",
            "null",
        }

    # --------------------------------------------------------------------------
    # 第二阶段：状态与属性读取 (用例断言通道)
    # --------------------------------------------------------------------------

    @property
    def id(self) -> str:
        """返回组件唯一标识 ID（遵循 W3C WebDriver / Selenium / Appium WebElement.id 规范）。"""
        return (
            str(self.attributes.get("id") or "").strip()
            or str(self.attributes.get("resource-id") or "").strip()
            or f"harmony_elem_{hex(id(self))}"
        )

    @property
    def _id(self) -> str:
        """兼容老版本客户端与私有属性 _id 访问。"""
        return self.id

    @property
    def text(self) -> str:
        """获取控件文本，优先读取 originalText，若为空读取 text"""
        return self.attributes.get("originalText") or self.attributes.get(
            "text",
            "",
        )

    @property
    def tag_name(self) -> str:
        """组件类型名，如 Text, Button, Row, Column, Stack 等"""
        return self.attributes.get("type", "Component")

    @property
    def location(self) -> Dict[str, int]:
        """元素左上角物理坐标 {'x': left, 'y': top}"""
        return {"x": self.left, "y": self.top}

    @property
    def size(self) -> Dict[str, int]:
        """元素尺寸大小 {'width': width, 'height': height}"""
        return {"width": self.width, "height": self.height}

    @property
    def rect(self) -> Dict[str, int]:
        """返回 BasePage 计算元素中心点所需的标准矩形结构。"""
        return {
            "x": self.left,
            "y": self.top,
            "width": self.width,
            "height": self.height,
        }

    def is_displayed(self) -> bool:
        """判断组件是否在屏幕可见区域展示"""
        return self._as_bool(self.attributes.get("visible"), True) and (
            self.width > 0 and self.height > 0
        )

    def is_enabled(self) -> bool:
        """判断组件是否处于可用激活状态"""
        return self._as_bool(self.attributes.get("enabled"), True)

    def is_selected(self) -> bool:
        """判断单选、复选或可选组件是否处于选中状态。"""
        selected_value = self.attributes.get("selected")
        if selected_value is None:
            selected_value = self.attributes.get("checked")
        return self._as_bool(selected_value, False)

    def get_attribute(self, name: str) -> Optional[str]:
        """获取组件特定的指定属性值"""
        aliases = {
            "class": "type",
            "contentDescription": "content-desc",
            "resourceId": "resource-id",
        }
        attribute_name = aliases.get(name, name)
        if attribute_name == "text":
            return self.text
        return self.attributes.get(attribute_name)

    @property
    def screenshot_as_png(self) -> bytes:
        """截取当前元素矩形区域的 PNG 字节流，兼容图像比对与头像哈希校验。"""
        self._ensure_interactable()
        full_png = self.driver.get_screenshot_as_png()
        from PIL import Image
        import io

        with Image.open(io.BytesIO(full_png)) as img:
            crop_box = (
                max(0, self.left),
                max(0, self.top),
                min(img.width, self.right),
                min(img.height, self.bottom),
            )
            cropped = img.crop(crop_box)
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            return buf.getvalue()

    # --------------------------------------------------------------------------
    # 第三阶段：交互动作执行 (事件注入)
    # --------------------------------------------------------------------------

    def click(self) -> None:
        """通过 Driver 在元素中心点执行单击。"""
        self._ensure_interactable()
        logger.debug(
            f"{LogIcon.ACTION} [HarmonyWebElement] 点击元素 "
            f"({self.center_x}, {self.center_y}) - {self.tag_name}"
        )
        self.driver.tap([(self.center_x, self.center_y)])
        time.sleep(0.1)

    def double_click(self) -> None:
        """通过 Driver 在元素中心点执行双击。"""
        self._ensure_interactable()
        self.driver.double_click(self.center_x, self.center_y)
        time.sleep(0.15)

    def long_click(self) -> None:
        """通过 Driver 在元素中心点执行长按。"""
        self._ensure_interactable()
        self.driver.long_click(self.center_x, self.center_y)
        time.sleep(0.2)

    def send_keys(self, *values: Any) -> None:
        """向控件输入文本，并转换常用 Selenium 特殊按键（如 Enter/Backspace）。"""
        input_value = "".join(str(value) for value in values)
        if not input_value:
            return

        # 1. 快速通道：普通文本直接整串注入，杜绝逐字符拆装循环
        special_keys = (Keys.ENTER, Keys.RETURN, Keys.BACKSPACE)
        if not any(key in input_value for key in special_keys):
            self.driver.input_text(input_value, self.center_x, self.center_y)
            time.sleep(0.1)
            return

        # 2. 包含特殊功能键时，按键与普通文本分段派发
        text_buffer: List[str] = []

        def flush_text_buffer() -> None:
            if not text_buffer:
                return
            plain_text = "".join(text_buffer)
            self.driver.input_text(
                plain_text,
                self.center_x,
                self.center_y,
            )
            text_buffer.clear()

        for character in input_value:
            if character in (Keys.ENTER, Keys.RETURN):
                flush_text_buffer()
                self.driver.press_keycode(66)  # 派发回车
            elif character == Keys.BACKSPACE:
                flush_text_buffer()
                self.driver.press_keycode(67)  # 派发退格
            else:
                text_buffer.append(character)
        flush_text_buffer()
        time.sleep(0.1)

    def clear(self) -> None:
        """仅在有文本时按实际长度执行受限退格清理，避免空输入框连续误删，不触发点击弹出键盘。"""
        current_len = len(self.text or "")
        if current_len == 0:
            return
        self.driver.clear_text(min(current_len + 3, 50))
