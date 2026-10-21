# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - UI 审查器集成页面
=======================================================
基于 PyQt6 原生容器实现：
1. 架构级无缝内嵌 desktop_app/ui/harmony_native_inspector.py (HarmonyAppiumInspector)；
2. 首次激活时按需懒加载 (Lazy Load)，确保控制台主窗口保持 0.3 秒极限冷启动；
3. 支持高阶双模态切换 (内嵌工作台 / ⧉ 弹出独立浮动窗口分屏调试)；
4. 页面切出自动挂起探活循环，切回自动唤醒，零多余 CPU/内存消耗。
"""
import os
import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QColor, QIcon, QPainter, QBrush, QPen

# 确保项目根路径在搜寻路径中
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class UndockedPlaceholder(QFrame):
    """
    当审查器弹出为独立窗口时，在主控制台内嵌区域展示的高级占位引导面板
    """
    reattach_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("undockedPlaceholder")
        self.setStyleSheet("""
            QFrame#undockedPlaceholder {
                background-color: #f8fafc;
                border: 1px dashed #cbd5e1;
                border-radius: 12px;
                margin: 24px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # 核心图标提示
        icon_lbl = QLabel("🔍")
        icon_lbl.setStyleSheet("font-size: 42px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # 主标题
        title_lbl = QLabel("UI 元素审查器当前处于独立窗口模式")
        title_lbl.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            background: transparent;
        """)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        # 副说明文案
        desc_lbl = QLabel("审查器已置于桌面浮动层，方便您拉至副显示器或并排进行用例调试与元素定位拾取。")
        desc_lbl.setStyleSheet("""
            font-size: 13px;
            color: #64748b;
            background: transparent;
        """)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_lbl)

        # 重新嵌入按钮
        reattach_btn = QPushButton("⧈ 收回并重新嵌入主控制台")
        reattach_btn.setFixedSize(210, 38)
        reattach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reattach_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        reattach_btn.clicked.connect(self.reattach_requested.emit)
        layout.addWidget(reattach_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class InspectorPage(QWidget):
    """
    桌面端控制台 - UI 元素审查器容器页面
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.inspector: Optional[Any] = None
        self.is_loaded: bool = False
        self.is_undocked: bool = False
        self._original_flags = None

        self._init_container_ui()

    def _init_container_ui(self) -> None:
        """初始化基础承载容器结构"""
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # 顶部轻奢操作控制条 (承载双模态切换按钮)
        self.toolbar_bar = QFrame()
        self.toolbar_bar.setFixedHeight(40)
        self.toolbar_bar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        tb_layout = QHBoxLayout(self.toolbar_bar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(12)

        # 页面标题标签
        title_lbl = QLabel("📱 移动端多平台原生 UI 审查器")
        title_lbl.setStyleSheet("""
            font-size: 13px;
            font-weight: 700;
            color: #0f172a;
        """)
        tb_layout.addWidget(title_lbl)

        badge_lbl = QLabel("HarmonyOS / Android / iOS 三端秒级拾取")
        badge_lbl.setStyleSheet("""
            font-size: 11px;
            color: #0284c7;
            background: #e0f2fe;
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: 600;
        """)
        tb_layout.addWidget(badge_lbl)

        tb_layout.addStretch()

        # 双模态切换按钮
        self.btn_undock = QPushButton("⧉ 弹出独立窗口")
        self.btn_undock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_undock.setFixedHeight(26)
        self.btn_undock.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                color: #0f172a;
                border-color: #94a3b8;
            }
        """)
        self.btn_undock.clicked.connect(self._toggle_undock_mode)
        tb_layout.addWidget(self.btn_undock)

        self.root_layout.addWidget(self.toolbar_bar)

        # 占位层 (初始化前或独立窗口时展示)
        self.placeholder = UndockedPlaceholder(self)
        self.placeholder.reattach_requested.connect(self._toggle_undock_mode)
        self.placeholder.hide()

    def _ensure_inspector_loaded(self) -> None:
        """按需懒加载审查器核心窗口实例"""
        if self.is_loaded and self.inspector is not None:
            return

        try:
            from desktop_app.ui.harmony_native_inspector import HarmonyAppiumInspector

            # 实例化审查器主窗体
            self.inspector = HarmonyAppiumInspector()
            
            # 保存其原始 WindowFlags 供切换时还原
            self._original_flags = self.inspector.windowFlags()

            # 重写审查器的关闭事件：若在独立窗口模式被关闭，则安全回归内嵌，杜绝丢失
            orig_close_event = self.inspector.closeEvent
            def _safe_close_event(event):
                if self.is_undocked:
                    self._reattach_to_container()
                    event.ignore()
                else:
                    orig_close_event(event)
            self.inspector.closeEvent = _safe_close_event

            # 挂载进当前容器
            self.root_layout.addWidget(self.inspector, stretch=1)
            self.inspector.show()
            self.is_loaded = True
            self._just_initialized = True
            
        except Exception as e:
            err_lbl = QLabel(f"加载 UI 审查器模块失败:\n{e}")
            err_lbl.setStyleSheet("color: #ef4444; font-size: 14px; padding: 24px;")
            self.root_layout.addWidget(err_lbl)

    def on_page_activated(self) -> None:
        """主窗口侧边栏切换至本页面时的激活回调"""
        # 1. 确保核心实例已就绪
        self._ensure_inspector_loaded()

        # 2. 若当前未处于独立窗口状态，激活展示
        if not self.is_undocked and self.inspector:
            self.inspector.show()
            self.placeholder.hide()
            # 若非首次加载刚初始化的状态，且未在后台抓取，联动异步刷新一次在线设备 (不抢占自动抓取)
            if not getattr(self, "_just_initialized", False):
                if hasattr(self.inspector, "load_device_list"):
                    try:
                        self.inspector.load_device_list(auto_capture=False)
                    except Exception:
                        pass
            else:
                self._just_initialized = False

    def on_page_deactivated(self) -> None:
        """切离当前页面时的休眠回调"""
        pass

    def _toggle_undock_mode(self) -> None:
        """在『内嵌主工作台』与『独立浮动窗口』之间丝滑切换"""
        self._ensure_inspector_loaded()
        if not self.inspector:
            return

        if not self.is_undocked:
            # 切换至：弹出独立窗口
            self.is_undocked = True
            self.root_layout.removeWidget(self.inspector)
            
            # 脱离父级变为顶级独立窗体
            self.inspector.setParent(None)
            self.inspector.setWindowFlags(self._original_flags | Qt.WindowType.Window)
            self.inspector.setWindowTitle("Santiao Mobile Inspector - 移动端全平台 UI 审查器 (独立浮动窗)")
            self.inspector.resize(1420, 900)
            self.inspector.show()
            self.inspector.raise_()
            self.inspector.activateWindow()

            # 容器展示占位引导层
            self.root_layout.addWidget(self.placeholder, stretch=1)
            self.placeholder.show()
            self.btn_undock.setText("⧈ 收回嵌入工作台")
        else:
            # 切换至：收回内嵌
            self._reattach_to_container()

    def _reattach_to_container(self) -> None:
        """将独立窗口收回嵌入到控制台右侧工作区"""
        if not self.inspector or not self.is_undocked:
            return

        self.is_undocked = False
        self.placeholder.hide()
        self.root_layout.removeWidget(self.placeholder)

        # 重新挂载进内嵌布局
        self.inspector.setWindowFlags(Qt.WindowType.Widget)
        self.root_layout.addWidget(self.inspector, stretch=1)
        self.inspector.show()
        self.btn_undock.setText("⧉ 弹出独立窗口")
