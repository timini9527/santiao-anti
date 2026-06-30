from __future__ import annotations

import os
from pathlib import Path


def resolve_project_root() -> Path:
    configured = os.getenv("SANTIAO_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[3]


PROJECT_ROOT = resolve_project_root()
TESTS_DIR = PROJECT_ROOT / "tests"
RUNTIME_DIR = PROJECT_ROOT / "web_console_v2" / "runtime"
REPORTS_DIR = RUNTIME_DIR / "reports"


def ensure_runtime_dirs() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
