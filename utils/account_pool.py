"""
验证码测试账号池轮转管理器

职责：
1. 按「业务环境 (app_env) × 平台 (platform)」维护持久化轮转游标，避免同一测试账号频繁发码触发
   「触发天极流控 / 触发小时级流控」或 60 秒发码冷却；
2. 状态文件写入 LOG_DIR 下的隐藏 JSON（已由 logs/ 忽略，不污染 Git），跨天自动归零；
3. 支持将已触发流控的账号加入当日熔断列表，后续用例与失败重跑自动跳过该账号。
"""

from __future__ import annotations

import json
import os
import threading
from datetime import date
from pathlib import Path

from config import LOG_DIR
from core.logger_utils import LogIcon, logger

DEFAULT_STATE_FILE: Path = LOG_DIR / ".verification_account_pool.json"
RATE_LIMIT_KEYWORDS: tuple[str, ...] = (
    "触发天级流控",
    "触发小时级流控",
    "流控",
)


def is_rate_limit_toast(toast_text: str | None) -> bool:
    """判断 Toast 提示文本是否命中短信流控（天极/小时级流控）。"""
    if not toast_text:
        return False
    return any(keyword in toast_text for keyword in RATE_LIMIT_KEYWORDS)


class VerificationAccountPool:
    """按「环境 × 平台」隔离的验证码账号池持久化轮转分配器。"""

    _lock = threading.Lock()

    @staticmethod
    def format_account(prefix: str, index: int, width: int = 4) -> str:
        """按号段前缀与补零宽度拼接完整手机号，例如 ('1920000', 101, 4) -> '19200000101'。"""
        return f"{prefix}{index:0{width}d}"

    @staticmethod
    def _today_str() -> str:
        """返回本地日期字符串 (YYYY-MM-DD)，用于每日自动重置轮转状态与熔断名单。"""
        return date.today().isoformat()

    @classmethod
    def _load_state(cls, state_file: Path, today: str) -> dict:
        """读取持久化游标状态；若文件缺失、损坏或已跨天，则自动重建当日干净状态。"""
        if state_file.exists():
            try:
                raw = json.loads(state_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and raw.get("date") == today and isinstance(raw.get("pools"), dict):
                    return raw
            except Exception as err:
                logger.warning(f"{LogIcon.WARN} [AccountPool] 状态文件读取失败，自动重建: {err}")
        return {"date": today, "pools": {}}

    @staticmethod
    def _save_state(state_file: Path, state: dict) -> None:
        """原子写回状态文件，避免并发或异常中断导致 JSON 半写损坏。"""
        state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = state_file.with_suffix(f"{state_file.suffix}.{os.getpid()}.tmp")
        tmp_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_file, state_file)

    @classmethod
    def acquire(
        cls,
        app_env: str,
        platform: str,
        prefix: str,
        start: int,
        end: int,
        width: int = 4,
        state_file: Path = DEFAULT_STATE_FILE,
    ) -> str:
        """
        从指定号池获取下一个可用账号并推进持久化游标（自动跳过当日已熔断账号）。

        :param app_env: 被测业务环境（如 gray / test）
        :param platform: 运行平台（harmonyos / android / ios）
        :param prefix: 手机号前缀（如 '1920000'）
        :param start: 起始序号（含）
        :param end: 结束序号（含）
        :param width: 序号补零宽度，默认 4 位
        :param state_file: 游标持久化文件路径
        :return: 分配到的手机号字符串
        """
        if start > end:
            raise ValueError(f"账号池配置无效: start({start}) > end({end})")

        pool_key = f"{app_env}:{platform}"
        total = end - start + 1
        today = cls._today_str()

        with cls._lock:
            state = cls._load_state(state_file, today)
            pools: dict = state["pools"]
            entry = pools.setdefault(pool_key, {"next_index": start, "blocked": []})

            blocked_list: list[str] = entry.get("blocked") if isinstance(entry.get("blocked"), list) else []
            blocked_set = set(blocked_list)

            cursor = entry.get("next_index", start)
            if not isinstance(cursor, int) or cursor < start or cursor > end:
                cursor = start

            for _ in range(total):
                candidate = cls.format_account(prefix, cursor, width)
                next_cursor = start if cursor >= end else cursor + 1
                if candidate not in blocked_set:
                    entry["next_index"] = next_cursor
                    entry["blocked"] = blocked_list
                    cls._save_state(state_file, state)
                    logger.info(
                        f"{LogIcon.SETUP} [AccountPool] 为 [{pool_key}] 分配验证码账号: {candidate} "
                        f"(号段 {start}-{end} | 今日已熔断 {len(blocked_set)} 个)"
                    )
                    return candidate
                cursor = next_cursor

            raise RuntimeError(
                f"号池 [{pool_key}] ({start}-{end}) 今日全部 {total} 个账号均已触发流控，"
                f"疑似设备或 IP 维度限流，请检查后端测试/灰度环境频控配置。"
            )

    @classmethod
    def mark_rate_limited(
        cls,
        app_env: str,
        platform: str,
        account: str,
        reason: str = "",
        state_file: Path = DEFAULT_STATE_FILE,
    ) -> None:
        """将触发天级/小时级流控的账号记入当日熔断名单，当日后续用例与重跑自动跳过。"""
        if not account:
            return

        pool_key = f"{app_env}:{platform}"
        today = cls._today_str()

        with cls._lock:
            state = cls._load_state(state_file, today)
            pools: dict = state["pools"]
            entry = pools.setdefault(pool_key, {"next_index": 0, "blocked": []})
            blocked_list: list[str] = entry.get("blocked") if isinstance(entry.get("blocked"), list) else []
            if account not in blocked_list:
                blocked_list.append(account)
                entry["blocked"] = blocked_list
                cls._save_state(state_file, state)
                logger.warning(
                    f"{LogIcon.WARN} [AccountPool] 账号 {account} 触发流控 ({reason or '未知流控提示'})，"
                    f"已加入 [{pool_key}] 今日熔断列表（当前已熔断 {len(blocked_list)} 个）"
                )
