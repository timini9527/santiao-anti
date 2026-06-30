from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import PROJECT_ROOT, REPORTS_DIR, ensure_runtime_dirs
from .schemas import RunRequest, TaskStatus


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Task:
    task_id: str
    nodeid: str
    status: str
    started_at: str
    command: list[str]
    report_dir: Path
    process: subprocess.Popen | None = None
    exit_code: int | None = None
    finished_at: str | None = None
    logs: list[str] = field(default_factory=list)
    events: queue.Queue[str | None] = field(default_factory=queue.Queue)


class TaskRunner:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()

    def recent_tasks(self) -> list[TaskStatus]:
        with self._lock:
            tasks = list(self._tasks.values())[-30:]
        return [self._to_status(task) for task in reversed(tasks)]

    def get_status(self, task_id: str) -> TaskStatus | None:
        with self._lock:
            task = self._tasks.get(task_id)
        return self._to_status(task) if task else None

    def has_running_task(self) -> bool:
        with self._lock:
            return any(task.status == "running" for task in self._tasks.values())

    def start(self, request: RunRequest) -> tuple[bool, str, str | None, list[str]]:
        ensure_runtime_dirs()
        if self.has_running_task() and not request.allow_parallel:
            return False, "当前已有任务在执行，请等待完成或先停止任务", None, []

        task_id = uuid.uuid4().hex[:12]
        report_dir = REPORTS_DIR / task_id / "allure-results"
        if report_dir.exists():
            shutil.rmtree(report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)

        command = [
            sys.executable,
            "-m",
            "pytest",
            request.nodeid,
            "-vs",
            "--color=yes",
            f"--alluredir={report_dir}",
        ]
        if request.env:
            command.extend(["--env", request.env])
        if request.debug_mode:
            command.append("--pdb")

        task = Task(
            task_id=task_id,
            nodeid=request.nodeid,
            status="running",
            started_at=utc_now(),
            command=command,
            report_dir=report_dir,
        )
        with self._lock:
            self._tasks[task_id] = task

        env = self._build_env(request)
        try:
            proc = subprocess.Popen(
                command,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                bufsize=0,
            )
            task.process = proc
        except Exception as exc:
            task.status = "failed"
            task.finished_at = utc_now()
            self._append_log(task, f"启动失败: {exc}")
            task.events.put(None)
            return False, f"启动失败: {exc}", task_id, command

        thread = threading.Thread(target=self._stream_process, args=(task,), daemon=True)
        thread.start()
        self._append_log(task, f"任务已启动: {request.nodeid}")
        return True, "测试已启动", task_id, command

    def stop(self, task_id: str) -> tuple[bool, str]:
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return False, "任务不存在"
        if task.status != "running" or not task.process:
            return False, "任务未在运行中"
        task.process.terminate()
        task.status = "stopped"
        task.finished_at = utc_now()
        self._append_log(task, "任务已请求停止")
        task.events.put(None)
        return True, "已请求停止任务"

    def event_stream(self, task_id: str):
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            yield self._format_sse({"type": "error", "message": "任务不存在"})
            return

        for line in task.logs[-200:]:
            yield self._format_sse({"type": "log", "line": line})

        while True:
            try:
                item = task.events.get(timeout=15)
            except queue.Empty:
                yield self._format_sse({"type": "heartbeat"})
                continue
            if item is None:
                yield self._format_sse({"type": "status", "status": task.status, "exit_code": task.exit_code})
                break
            yield self._format_sse({"type": "log", "line": item})

    def _build_env(self, request: RunRequest) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        pairs = {
            "REMOTE_APPIUM_URL": request.remote_appium,
            "REMOTE_UDID": request.remote_udid,
            "ENV": request.env,
            "TEST_ENV": request.env,
            "PRIVATE_CHAT_NAME": request.private_chat_name,
            "GROUP_CHAT_NAME": request.group_chat_name,
            "WEB_RECEIPT_DATA": request.web_receipt_data,
        }
        for key, value in pairs.items():
            if value:
                env[key] = value
        if request.debug_mode:
            env["DEBUG_MODE"] = "1"
        return env

    def _stream_process(self, task: Task) -> None:
        assert task.process is not None
        assert task.process.stdout is not None
        for raw_line in iter(task.process.stdout.readline, b""):
            if not raw_line:
                break
            line = self._decode_line(raw_line)
            self._append_log(task, line)
        exit_code = task.process.wait()
        if task.status != "stopped":
            task.status = "finished" if exit_code == 0 else "failed"
        task.exit_code = exit_code
        task.finished_at = utc_now()
        self._append_log(task, f"任务结束，退出码: {exit_code}")
        task.events.put(None)

    def _append_log(self, task: Task, line: str) -> None:
        text = line.rstrip("\r\n")
        task.logs.append(text)
        if len(task.logs) > 5000:
            del task.logs[:1000]
        task.events.put(text)

    def _to_status(self, task: Task) -> TaskStatus:
        return TaskStatus(
            task_id=task.task_id,
            status=task.status,  # type: ignore[arg-type]
            nodeid=task.nodeid,
            exit_code=task.exit_code,
            started_at=task.started_at,
            finished_at=task.finished_at,
            report_dir=str(task.report_dir),
            command=task.command,
            log_tail=task.logs[-50:],
        )

    @staticmethod
    def _decode_line(raw_line: bytes) -> str:
        for encoding in ("utf-8", "gbk"):
            try:
                return raw_line.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw_line.decode("utf-8", errors="ignore")

    @staticmethod
    def _format_sse(payload: dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


runner = TaskRunner()
