from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TestParam(BaseModel):
    index: int
    label: str
    nodeid: str


class TestCase(BaseModel):
    id: str
    nodeid: str
    display_name: str
    file: str
    module: str
    class_name: str | None = None
    function_name: str
    params: list[TestParam] = Field(default_factory=list)
    markers: list[str] = Field(default_factory=list)
    destructive: bool = False


class TestTreeNode(BaseModel):
    id: str
    label: str
    type: Literal["folder", "file", "class", "case"]
    children: list["TestTreeNode"] = Field(default_factory=list)
    case: TestCase | None = None


TestTreeNode.model_rebuild()


class TestsResponse(BaseModel):
    project_root: str
    count: int
    cases: list[TestCase]
    tree: list[TestTreeNode]


class RunRequest(BaseModel):
    nodeid: str
    env: str | None = None
    remote_appium: str | None = None
    remote_udid: str | None = None
    debug_mode: bool = False
    private_chat_name: str | None = None
    group_chat_name: str | None = None
    web_receipt_data: str | None = None
    allow_parallel: bool = False


class RunResponse(BaseModel):
    success: bool
    message: str
    task_id: str | None = None
    command: list[str] = Field(default_factory=list)


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["queued", "running", "finished", "stopped", "failed"]
    nodeid: str
    exit_code: int | None = None
    started_at: str
    finished_at: str | None = None
    report_dir: str | None = None
    command: list[str] = Field(default_factory=list)
    log_tail: list[str] = Field(default_factory=list)


class StopResponse(BaseModel):
    success: bool
    message: str
