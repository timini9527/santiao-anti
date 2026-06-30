from __future__ import annotations

import platform
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import PROJECT_ROOT, TESTS_DIR, ensure_runtime_dirs
from .runner import runner
from .schemas import RunRequest, RunResponse, StopResponse, TestsResponse
from .test_discovery import build_test_tree, collect_tests


app = FastAPI(title="Santiao Web Console V2", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    ensure_runtime_dirs()


@app.get("/api/health")
def health() -> dict:
    return {
        "success": True,
        "project_root": str(PROJECT_ROOT),
        "tests_dir_exists": TESTS_DIR.exists(),
        "python": sys.version,
        "platform": platform.platform(),
    }


@app.get("/api/tests", response_model=TestsResponse)
def list_tests() -> TestsResponse:
    cases = collect_tests()
    return TestsResponse(
        project_root=str(PROJECT_ROOT),
        count=len(cases),
        cases=cases,
        tree=build_test_tree(cases),
    )


@app.post("/api/run", response_model=RunResponse)
def run_test(request: RunRequest) -> RunResponse:
    success, message, task_id, command = runner.start(request)
    status_code = 200 if success else 409
    if not success:
        raise HTTPException(status_code=status_code, detail={"message": message, "command": command})
    return RunResponse(success=True, message=message, task_id=task_id, command=command)


@app.get("/api/tasks")
def recent_tasks() -> dict:
    return {"success": True, "tasks": runner.recent_tasks()}


@app.get("/api/status/{task_id}")
def task_status(task_id: str):
    status = runner.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return status


@app.post("/api/stop/{task_id}", response_model=StopResponse)
def stop_task(task_id: str) -> StopResponse:
    success, message = runner.stop(task_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return StopResponse(success=True, message=message)


@app.get("/api/logs/stream/{task_id}")
def stream_logs(task_id: str) -> StreamingResponse:
    return StreamingResponse(
        runner.event_stream(task_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
