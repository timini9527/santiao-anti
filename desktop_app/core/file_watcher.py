# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 - 文件自动热同步监视引擎 (LiveSyncWatcher)
=======================================================
架构设计：
1. 采用 Qt 原生 QFileSystemWatcher，零第三方依赖，极致轻量，低 CPU 开销；
2. 深度递归监控 tests/ 与 config/ 目录下的测试文件与配置文件；
3. 内置 350ms 智能事件防抖 (Debounce)，彻底避免编辑器连续写盘引发频繁重扫；
4. 动态自愈拓扑：当检测到新增子目录或文件时，自动追加至监视列表；
5. 提供统一 PyQt 信号 tests_changed，无缝协同 UI 树热更新。
"""
import os
import sys
from typing import Optional, Set
from PyQt6.QtCore import QObject, QFileSystemWatcher, QTimer, pyqtSignal

from desktop_app.config import PROJECT_ROOT


class LiveSyncWatcher(QObject):
    """项目核心测试资源自动热同步监听器"""

    # 当检测到测试文件或配置变动时触发，传递变更摘要信息
    tests_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None, debounce_ms: int = 350):
        super().__init__(parent)
        self.debounce_ms = debounce_ms
        self._watcher = QFileSystemWatcher(self)
        self._watched_paths: Set[str] = set()

        # 防抖定时器，避免 IDE 自动保存时高频连击
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(self.debounce_ms)
        self._debounce_timer.timeout.connect(self._on_debounced_change)

        self._pending_reason = "文件变更"
        self._init_watcher()

    def _init_watcher(self) -> None:
        """初始化监听路径：递归加载 tests/ 目录与 config/ 关键文件"""
        self._watcher.directoryChanged.connect(self._on_directory_changed)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self.refresh_watch_paths()

    def refresh_watch_paths(self) -> None:
        """重新扫描并刷新待监视的目录与文件集合"""
        tests_dir = os.path.join(PROJECT_ROOT, "tests")
        config_dir = os.path.join(PROJECT_ROOT, "config")

        new_paths: Set[str] = set()

        # 1. 递归加载 tests/ 目录与测试文件
        if os.path.isdir(tests_dir):
            new_paths.add(tests_dir)
            for root, dirs, files in os.walk(tests_dir):
                # 排除缓存与临时文件夹
                dirs[:] = [d for d in dirs if d not in ('__pycache__', '.pytest_cache', 'allure_results', 'allure_report')]
                for d in dirs:
                    new_paths.add(os.path.join(root, d))
                for f in files:
                    if (f.startswith("test_") or f.endswith("_test.py")) and f.endswith(".py"):
                        new_paths.add(os.path.join(root, f))

        # 2. 加载 config/ 与根目录关键配置
        for conf_item in ["config", "pytest.ini"]:
            p = os.path.join(PROJECT_ROOT, conf_item)
            if os.path.exists(p):
                new_paths.add(p)

        # 差量注册，防止重复监听
        to_add = new_paths - self._watched_paths
        to_remove = self._watched_paths - new_paths

        if to_remove:
            valid_remove = [p for p in to_remove if p in self._watcher.directories() or p in self._watcher.files()]
            if valid_remove:
                self._watcher.removePaths(valid_remove)

        if to_add:
            valid_add = [p for p in to_add if os.path.exists(p)]
            if valid_add:
                self._watcher.addPaths(valid_add)

        self._watched_paths = new_paths

    def _on_directory_changed(self, path: str) -> None:
        """目录结构发生变更（新增/删除文件或子目录）"""
        self._pending_reason = f"目录变动: {os.path.basename(path)}"
        # 重新增量刷新监听列表，确保新建的文件立即被纳管
        self.refresh_watch_paths()
        self._debounce_timer.start()

    def _on_file_changed(self, path: str) -> None:
        """单个文件发生修改或覆写"""
        # Windows 部分编辑器保存文件时采用“先删后写”，可能导致 watcher 丢失监听，需动态补录
        if os.path.exists(path) and path not in self._watcher.files():
            self._watcher.addPath(path)
        self._pending_reason = f"代码变动: {os.path.basename(path)}"
        self._debounce_timer.start()

    def _on_debounced_change(self) -> None:
        """防抖时间窗口结束，正式对外发射热同步信号"""
        self.tests_changed.emit(self._pending_reason)
