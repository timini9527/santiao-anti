# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 移动端测试页面
=======================================================
与 Web 端 (MobilePlatform.vue) 1:1 像素级复刻：
1. 顶部 Header：移动 IM 控制台 + 右侧药丸状态 Badge 组 (设备在线、用例总数、报告份数、刷新)
2. 水平主分栏 (main_h_splitter)：
   - 左侧：搜索框、四级用例树 (支持失败红点、运行各级胶囊按钮)、下方远程调试与参数配置折叠卡片
   - 右侧 (垂直分割器 right_v_splitter)：
     - 上半部：Allure 可视化测试报告看板 (状态药丸、精简视角、刷新报告、原生复刻 Allure 环形看板)
     - 下半部：终端实时执行日志 (自动滚屏、复制日志、清空终端，支持向上/向下拖拽吸底折叠/展开)
3. 零 WebView、纯原生 PyQt6 极速渲染、全量配置永久持久化
"""
import os
import sys
import re
import json
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QRadioButton,
    QButtonGroup, QTreeWidget, QTreeWidgetItem, QSplitter,
    QPlainTextEdit, QMessageBox, QFrame, QScrollArea, QApplication,
    QHeaderView, QSizePolicy, QDialog, QTextBrowser, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QTextCursor, QFont, QTextDocument, QTextCharFormat, QColor, QKeySequence, QShortcut

# 工业级运行时环境自愈：自适应注入项目根路径，同时完美兼容主程序模块化导入与独立脚本运行调试
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from ..config import desktop_config
    from ..core.device_manager import DeviceManager
    from ..core.test_collector import TestCollectorService
    from ..core.test_runner import TestExecutionWorker, clean_ansi_log
    from ..core.path_resolver import SmartPathResolver
    from ..core.report_scanner import get_reports_count
    from .allure_dashboard import AllureDashboardWidget
    from .receipt_dialog import WebReceiptDialog
    from .widgets import TopStatusPillWidget
except (ImportError, ValueError):
    from desktop_app.config import desktop_config
    from desktop_app.core.device_manager import DeviceManager
    from desktop_app.core.test_collector import TestCollectorService
    from desktop_app.core.test_runner import TestExecutionWorker, clean_ansi_log
    from desktop_app.core.path_resolver import SmartPathResolver
    from desktop_app.core.report_scanner import get_reports_count
    from desktop_app.ui.allure_dashboard import AllureDashboardWidget
    from desktop_app.ui.receipt_dialog import WebReceiptDialog
    from desktop_app.ui.widgets import TopStatusPillWidget

def _detect_local_lan_ip() -> str:
    """获取本机真实有效局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class MarkdownDocDialog(QDialog):
    """测试用例文档说明专用对话框"""
    def __init__(self, doc_path: str, title_name: str, parent=None):
        super().__init__(parent)
        self.doc_path = doc_path
        self.setWindowTitle(f"用例文档说明 - {title_name}")
        self.resize(780, 580)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 头部栏
        header_bar = QHBoxLayout()
        header_bar.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(36, 36)
        icon_box.setStyleSheet("""
            background-color: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
        """)
        ib_l = QVBoxLayout(icon_box)
        ib_l.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel("📖")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 18px;")
        ib_l.addWidget(lbl_icon)
        header_bar.addWidget(icon_box)

        title_info = QVBoxLayout()
        title_info.setSpacing(2)
        lbl_title = QLabel(f"用例文档: {os.path.basename(doc_path)}")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        lbl_path = QLabel(f"绝对路径: {doc_path}")
        lbl_path.setStyleSheet("font-size: 11px; color: #64748b;")
        title_info.addWidget(lbl_title)
        title_info.addWidget(lbl_path)
        header_bar.addLayout(title_info)

        header_bar.addStretch()

        btn_open_external = QPushButton("在系统外部打开 ↗")
        btn_open_external.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_external.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }
        """)
        btn_open_external.clicked.connect(self._open_in_system)
        header_bar.addWidget(btn_open_external)
        layout.addLayout(header_bar)

        # Markdown 渲染内容展示区
        text_view = QTextBrowser()
        text_view.setStyleSheet("""
            QTextBrowser {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 14px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 13px;
                line-height: 1.6;
                color: #1e293b;
            }
        """)
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
            text_view.setMarkdown(content)
        except Exception as e:
            text_view.setPlainText(f"读取文档内容异常: {e}")
        layout.addWidget(text_view, stretch=1)

        # 底部按钮区
        btn_close = QPushButton("关闭")
        btn_close.setFixedWidth(88)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_close.clicked.connect(self.accept)

        b_box = QHBoxLayout()
        b_box.addStretch()
        b_box.addWidget(btn_close)
        layout.addLayout(b_box)

    def _open_in_system(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.doc_path)
            else:
                subprocess.Popen(["xdg-open", self.doc_path])
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"调用系统程序打开文档失败:\n{e}")


class SyncProgressDialog(QDialog):
    """测试用例同步专属 Loading 进度模态弹窗 (极简科技轻奢风)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(390, 160)

        # 核心纯白卡片容器
        card = QFrame(self)
        card.setGeometry(0, 0, 390, 160)
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)

        # 顶部标题与百分比行
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        self.lbl_title = QLabel("🔄 正在同步测试用例...")
        self.lbl_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a; border: none;")
        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setStyleSheet("font-size: 13px; font-weight: 700; color: #2563eb; border: none;")
        title_row.addWidget(self.lbl_title)
        title_row.addStretch()
        title_row.addWidget(self.lbl_pct)
        layout.addLayout(title_row)

        # 状态描述文案
        self.lbl_status = QLabel("🔍 检索 tests/ 目录测试文件结构...")
        self.lbl_status.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500; border: none;")
        layout.addWidget(self.lbl_status)

        # 科技蓝双色渐变进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f1f5f9;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #06b6d4);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

    def set_progress(self, val: int, status_text: str, title_text: Optional[str] = None):
        """实时更新弹窗状态与进度百分比"""
        self.progress_bar.setValue(val)
        self.lbl_pct.setText(f"{val}%")
        self.lbl_status.setText(status_text)
        if title_text:
            self.lbl_title.setText(title_text)
        QApplication.processEvents()


class MobilePage(QWidget):
    """移动端自动化测试核心工作台 (1:1 像素级复刻 Web 端)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[TestExecutionWorker] = None
        self.catalog_data: List[Dict[str, Any]] = []
        self.last_report_dir: Optional[str] = None
        
        # 记录各节点执行状态：'failed', 'passed', '' (初始纯净就绪态，所有用例均展示默认空心球 ⚪ ⚙️)
        self.node_status_map: Dict[str, str] = {}

        self.lan_ip = _detect_local_lan_ip()
        self.total_case_count = 1383
        self._is_log_collapsed = False
        self._last_log_height = 240
        self._auto_scroll = True
        self.web_receipt_fields: List[Dict[str, str]] = []
        self._log_search_matches: List[QTextCursor] = []
        self._log_search_index: int = -1
        self._search_timer_pending: bool = False

        self._is_loading_config = True
        self.init_ui()
        self.load_persisted_config()
        self._is_loading_config = False

        # 异步非阻塞错峰调度：优先极速呈现骨架与分割器，随后渐进加载用例、历史执行状态与设备检测
        QTimer.singleShot(40, self._restore_splitter_sizes)
        QTimer.singleShot(120, self.refresh_test_cases)
        QTimer.singleShot(260, self._restore_last_run_state)
        QTimer.singleShot(380, self.auto_detect_devices)
        QTimer.singleShot(520, self._refresh_report_pill_count)

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(10)

        # 1. 顶部主控制台 Header 栏 (标题 + 右侧药丸状态 Badge 组)
        top_header = self._create_top_header()
        root_layout.addWidget(top_header)

        # 2. 左右核心大水平分割器 (main_h_splitter) - 极致纤细4px手柄，视觉干净无突兀粗条
        self.main_h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_h_splitter.setHandleWidth(4)

        # 2.1 左边栏：用例搜索、用例树与参数配置
        left_sidebar = self._create_left_sidebar()
        self.main_h_splitter.addWidget(left_sidebar)

        # 2.2 右边栏：垂直分割器 (上半部 Allure 报告展示区 + 下半部 终端实时执行日志)
        right_panel = self._create_right_panel()
        self.main_h_splitter.addWidget(right_panel)

        # 设置左边栏与右边栏的初始宽度比例 (约 35% : 65%)
        self.main_h_splitter.setStretchFactor(0, 4)
        self.main_h_splitter.setStretchFactor(1, 6)
        self.main_h_splitter.setCollapsible(0, False)
        self.main_h_splitter.setCollapsible(1, False)
        self.main_h_splitter.splitterMoved.connect(self._on_h_splitter_moved)

        # 赋予水平手柄平滑左右调节光标 (↔)
        h_handle = self.main_h_splitter.handle(1)
        if h_handle:
            h_handle.setCursor(Qt.CursorShape.SplitHCursor)

        root_layout.addWidget(self.main_h_splitter, stretch=1)

    # ==================== 1. 顶部主 Header 构建 ====================
    def _create_top_header(self) -> QWidget:
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(14, 8, 14, 8)
        h_layout.setSpacing(12)

        # 1.1 左侧品牌与模块标题 (同图中 1:1)
        icon_box = QFrame()
        icon_box.setFixedSize(36, 36)
        icon_box.setStyleSheet("""
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
        """)
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel("📱")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 18px;")
        ib_layout.addWidget(lbl_icon)
        h_layout.addWidget(icon_box)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        lbl_main_title = QLabel("移动 IM 控制台")
        lbl_main_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        lbl_sub_title = QLabel("Appium 移动端自动化测试")
        lbl_sub_title.setStyleSheet("font-size: 11px; color: #64748b;")
        title_box.addWidget(lbl_main_title)
        title_box.addWidget(lbl_sub_title)
        h_layout.addLayout(title_box)

        # 1.2 标题右侧紧邻：Appium 服务集群与设备检测控制区
        svc_btn_group = QFrame()
        svc_btn_group.setObjectName("svcBtnGroup")
        svc_btn_group.setStyleSheet("""
            QFrame#svcBtnGroup {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        svc_layout = QHBoxLayout(svc_btn_group)
        svc_layout.setContentsMargins(4, 3, 4, 3)
        svc_layout.setSpacing(6)

        # 按钮 1: 启动服务 (打开 start_appium_batch.bat)
        btn_start_svc = QPushButton("▶ 启动服务")
        btn_start_svc.setToolTip("在独立终端窗口执行 start_appium_batch.bat 批处理文件，启动 Appium 服务集群")
        btn_start_svc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_start_svc.setStyleSheet("""
            QPushButton {
                background-color: #f0fdf4;
                color: #15803d;
                border: 1px solid #bbf7d0;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #dcfce7;
                border-color: #86efac;
                color: #166534;
            }
            QPushButton:pressed {
                background-color: #bbf7d0;
                border-color: #4ade80;
            }
        """)
        btn_start_svc.clicked.connect(self._start_appium_service)
        svc_layout.addWidget(btn_start_svc)

        # 按钮 2: 关闭服务 (关闭 Appium 服务与对应端口)
        btn_stop_svc = QPushButton("⏹ 关闭服务")
        btn_stop_svc.setToolTip("终止后台所有 Appium 服务进程并释放 4723-4731 端口")
        btn_stop_svc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stop_svc.setStyleSheet("""
            QPushButton {
                background-color: #fef2f2;
                color: #b91c1c;
                border: 1px solid #fecdd3;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                border-color: #fda4af;
                color: #991b1b;
            }
            QPushButton:pressed {
                background-color: #fecdd3;
                border-color: #f43f5e;
            }
        """)
        btn_stop_svc.clicked.connect(self._stop_appium_service)
        svc_layout.addWidget(btn_stop_svc)

        # 按钮 3: 检测服务 (通过 adb kill-server 和 adb devices -l 深度检查是否有设备连接)
        btn_check_svc = QPushButton("🔍 检测服务")
        btn_check_svc.setToolTip("执行 adb kill-server、adb start-server 和 adb devices -l 检查是否有设备连接成功")
        btn_check_svc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_check_svc.setStyleSheet("""
            QPushButton {
                background-color: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #dbeafe;
                border-color: #93c5fd;
                color: #1e40af;
            }
            QPushButton:pressed {
                background-color: #bfdbfe;
                border-color: #3b82f6;
            }
        """)
        btn_check_svc.clicked.connect(self._check_appium_and_devices)
        svc_layout.addWidget(btn_check_svc)

        h_layout.addWidget(svc_btn_group)
        h_layout.addStretch()

        # 1.3 右侧药丸状态 Badge 组 (与报告中心完全公用统一通用控件)
        self.top_status_pill = TopStatusPillWidget(parent=header_card)
        self.lbl_device_pill = self.top_status_pill.lbl_device
        self.lbl_case_pill = self.top_status_pill.lbl_case
        self.lbl_report_pill = self.top_status_pill.lbl_report
        self.top_status_pill.refresh_clicked.connect(self._on_top_refresh_clicked)
        h_layout.addWidget(self.top_status_pill)
        return header_card

    # ==================== 2. 左边栏构建 (上部用例树 + 下部参数配置) ====================
    def _create_left_sidebar(self) -> QWidget:
        container = QFrame()
        container.setProperty("class", "panel-card")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 2.1 搜索输入框与 展开/折叠
        search_box = QHBoxLayout()
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("🔍 输入关键字模糊搜索用例...")
        self.edit_search.textChanged.connect(self._filter_test_cases)
        search_box.addWidget(self.edit_search)

        btn_expand = QPushButton("展开")
        btn_expand.setProperty("class", "btn-mini")
        btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_expand.clicked.connect(self._expand_all)
        search_box.addWidget(btn_expand)

        lbl_slash = QLabel("/")
        lbl_slash.setStyleSheet("color: #94a3b8;")
        search_box.addWidget(lbl_slash)

        btn_collapse = QPushButton("折叠")
        btn_collapse.setProperty("class", "btn-mini")
        btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_collapse.clicked.connect(self._collapse_all)
        search_box.addWidget(btn_collapse)

        lbl_slash2 = QLabel("/")
        lbl_slash2.setStyleSheet("color: #94a3b8;")
        search_box.addWidget(lbl_slash2)

        self.btn_sync = QPushButton("同步")
        self.btn_sync.setProperty("class", "btn-mini")
        self.btn_sync.setToolTip("强制全量扫描本地 tests 目录，实时同步新增或修改的测试用例（无需重新打包编译）")
        self.btn_sync.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync.clicked.connect(self._trigger_live_sync)
        search_box.addWidget(self.btn_sync)

        layout.addLayout(search_box)

        # 2.2 四级用例树 (隐藏头部，简洁纯净)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(1, 142)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        self.tree.itemExpanded.connect(self._on_tree_item_expanded)
        self.tree.itemCollapsed.connect(self._on_tree_item_collapsed)
        self.tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        layout.addWidget(self.tree, stretch=1)

        # 2.3 底部：远程测试与参数配置面板 (可折叠，支持独立滚动)
        params_wrapper = self._create_params_panel_wrapper()
        layout.addWidget(params_wrapper)

        return container

    def _create_params_panel_wrapper(self) -> QWidget:
        """参数面板容器 (自适应内容高度与滚动)"""
        self.params_card = QFrame()
        self.params_card.setStyleSheet("""
            QFrame#paramsCard {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        self.params_card.setObjectName("paramsCard")
        card_layout = QVBoxLayout(self.params_card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(6)

        # 标题栏
        header_row = QHBoxLayout()
        lbl_icon = QLabel("🔌")
        lbl_icon.setStyleSheet("font-size: 13px;")
        header_row.addWidget(lbl_icon)

        lbl_params_title = QLabel("远程测试与参数配置")
        lbl_params_title.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 12px;")
        header_row.addWidget(lbl_params_title)
        header_row.addStretch()

        btn_reset = QPushButton("重置")
        btn_reset.setProperty("class", "btn-mini")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self._reset_params)
        header_row.addWidget(btn_reset)

        self.btn_toggle_collapse = QPushButton("收起")
        self.btn_toggle_collapse.setProperty("class", "btn-mini")
        self.btn_toggle_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_collapse.clicked.connect(self._toggle_params_collapse)
        header_row.addWidget(self.btn_toggle_collapse)

        card_layout.addLayout(header_row)

        # 表单主体 (Form Body)
        self.params_body = QWidget()
        body_layout = QGridLayout(self.params_body)
        body_layout.setContentsMargins(0, 4, 0, 0)
        body_layout.setHorizontalSpacing(8)
        body_layout.setVerticalSpacing(6)

        # 1. Appium 1 (发送端)
        lbl_box1 = QHBoxLayout()
        lbl_box1.addWidget(QLabel("APPIUM 1 地址 (发送端):"))
        lbl_box1.addStretch()
        btn_start_appium1 = QPushButton("启动")
        btn_start_appium1.setProperty("class", "btn-mini")
        btn_start_appium1.clicked.connect(lambda: self._trigger_start_appium(4723))
        btn_detect_appium1 = QPushButton("探测")
        btn_detect_appium1.setProperty("class", "btn-mini")
        btn_detect_appium1.clicked.connect(lambda: self._detect_appium_port(self.combo_appium1, 4723))
        lbl_box1.addWidget(btn_start_appium1)
        lbl_box1.addWidget(btn_detect_appium1)
        body_layout.addLayout(lbl_box1, 0, 0, 1, 2)

        row1_input = QHBoxLayout()
        current_host_os = "Win" if sys.platform == "win32" else ("Mac" if sys.platform == "darwin" else "Linux")
        self.combo_os = QComboBox()
        self.combo_os.addItems(["Win", "Mac", "Linux"])
        self.combo_os.setCurrentText(current_host_os)
        self.combo_os.setFixedWidth(88)
        self.combo_os.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                font-weight: 600;
                padding-left: 8px;
                padding-right: 24px;
            }
        """)
        self.combo_os.currentIndexChanged.connect(self._on_config_changed)

        self.combo_appium1 = QComboBox()
        self.combo_appium1.setEditable(True)
        self.combo_appium1.addItem(f"{self.lan_ip}:4723 (局域网本机)")
        self.combo_appium1.addItem("127.0.0.1:4723 (本地)")
        self.combo_appium1.currentTextChanged.connect(self._on_config_changed)

        row1_input.addWidget(self.combo_os)
        row1_input.addWidget(self.combo_appium1, stretch=1)
        body_layout.addLayout(row1_input, 1, 0, 1, 2)

        # 2. Appium 2 (接收端)
        lbl_box2 = QHBoxLayout()
        lbl_box2.addWidget(QLabel("APPIUM 2 地址 (接收端):"))
        lbl_box2.addStretch()
        btn_start_appium2 = QPushButton("启动")
        btn_start_appium2.setProperty("class", "btn-mini")
        btn_start_appium2.clicked.connect(lambda: self._trigger_start_appium(4724))
        btn_detect_appium2 = QPushButton("探测")
        btn_detect_appium2.setProperty("class", "btn-mini")
        btn_detect_appium2.clicked.connect(lambda: self._detect_appium_port(self.combo_appium2, 4724))
        lbl_box2.addWidget(btn_start_appium2)
        lbl_box2.addWidget(btn_detect_appium2)
        body_layout.addLayout(lbl_box2, 2, 0, 1, 2)

        self.combo_appium2 = QComboBox()
        self.combo_appium2.setEditable(True)
        self.combo_appium2.addItem(f"{self.lan_ip}:4724 (局域网本机)")
        self.combo_appium2.addItem("127.0.0.1:4724 (本地)")
        self.combo_appium2.currentTextChanged.connect(self._on_config_changed)
        body_layout.addWidget(self.combo_appium2, 3, 0, 1, 2)

        # 3. 第一部手机 UDID (发送端)
        lbl_box_udid1 = QHBoxLayout()
        lbl_box_udid1.addWidget(QLabel("第一部手机 UDID (发送端):"))
        lbl_box_udid1.addStretch()
        btn_detect_udid1 = QPushButton("检测真机")
        btn_detect_udid1.setProperty("class", "btn-mini")
        btn_detect_udid1.setStyleSheet("background-color: #059669; color: #ffffff; border-radius: 4px; font-weight: 700;")
        btn_detect_udid1.clicked.connect(lambda: self._detect_single_device(1))
        lbl_box_udid1.addWidget(btn_detect_udid1)
        body_layout.addLayout(lbl_box_udid1, 4, 0, 1, 2)

        self.combo_udid1 = QComboBox()
        self.combo_udid1.setEditable(True)
        self.combo_udid1.currentTextChanged.connect(self._on_config_changed)
        body_layout.addWidget(self.combo_udid1, 5, 0, 1, 2)

        # 互换按钮 (右对齐)
        swap_box = QHBoxLayout()
        swap_box.addStretch()
        btn_swap = QPushButton("↑↓ 互换发送与接收手机")
        btn_swap.setProperty("class", "btn-mini")
        btn_swap.setStyleSheet("color: #2563eb; background: transparent; border: none; font-weight: 600;")
        btn_swap.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_swap.clicked.connect(self._swap_devices)
        swap_box.addWidget(btn_swap)
        body_layout.addLayout(swap_box, 6, 0, 1, 2)

        # 4. 第二部手机 UDID (接收端)
        lbl_box_udid2 = QHBoxLayout()
        lbl_box_udid2.addWidget(QLabel("第二部手机 UDID (接收端):"))
        lbl_box_udid2.addStretch()
        btn_detect_udid2 = QPushButton("检测真机")
        btn_detect_udid2.setProperty("class", "btn-mini")
        btn_detect_udid2.setStyleSheet("background-color: #059669; color: #ffffff; border-radius: 4px; font-weight: 700;")
        btn_detect_udid2.clicked.connect(lambda: self._detect_single_device(2))
        lbl_box_udid2.addWidget(btn_detect_udid2)
        body_layout.addLayout(lbl_box_udid2, 7, 0, 1, 2)

        self.combo_udid2 = QComboBox()
        self.combo_udid2.setEditable(True)
        self.combo_udid2.currentTextChanged.connect(self._on_config_changed)
        body_layout.addWidget(self.combo_udid2, 8, 0, 1, 2)

        # 5. 业务调试变量 (私聊 / 群聊) - 配备保存与清空操作按钮，支持全局记忆模式
        lbl_box_chat = QHBoxLayout()
        lbl_box_chat.setSpacing(8)
        lbl_box_chat.addWidget(QLabel("业务调试变量 (私聊 / 群聊):"))
        lbl_box_chat.addStretch()

        self.btn_save_chat = QPushButton("保存")
        self.btn_save_chat.setProperty("class", "btn-mini")
        self.btn_save_chat.setToolTip("保存当前私聊用户与群聊名称，开启持久化记忆模式")
        self.btn_save_chat.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: 1px solid #1d4ed8;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.btn_save_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_chat.clicked.connect(self._save_chat_vars)

        self.btn_clear_chat = QPushButton("清空")
        self.btn_clear_chat.setProperty("class", "btn-mini")
        self.btn_clear_chat.setToolTip("清空输入框内容并同步重置持久化数据")
        self.btn_clear_chat.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #64748b;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                border-color: #fca5a5;
                color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #fecdd3;
            }
        """)
        self.btn_clear_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_chat.clicked.connect(self._clear_chat_vars)

        lbl_box_chat.addWidget(self.btn_save_chat)
        lbl_box_chat.addSpacing(6)
        lbl_box_chat.addWidget(self.btn_clear_chat)
        body_layout.addLayout(lbl_box_chat, 9, 0, 1, 2)

        chat_vars_row = QHBoxLayout()
        self.edit_private_chat = QLineEdit()
        self.edit_private_chat.setPlaceholderText("私聊用户 (如: test209-11)")
        self.edit_private_chat.textChanged.connect(self._on_config_changed)
        self.edit_private_chat.returnPressed.connect(self._save_chat_vars)

        self.edit_group_chat = QLineEdit()
        self.edit_group_chat.setPlaceholderText("群聊名称 (如: 测试交流群)")
        self.edit_group_chat.textChanged.connect(self._on_config_changed)
        self.edit_group_chat.returnPressed.connect(self._save_chat_vars)

        chat_vars_row.addWidget(self.edit_private_chat)
        chat_vars_row.addWidget(self.edit_group_chat)
        body_layout.addLayout(chat_vars_row, 10, 0, 1, 2)

        # 6. 调试模式
        self.chk_debug_mode = QCheckBox("🐞 调试模式 (用例失败保持现场)")
        self.chk_debug_mode.toggled.connect(self._on_config_changed)
        body_layout.addWidget(self.chk_debug_mode, 11, 0, 1, 2)

        card_layout.addWidget(self.params_body)
        return self.params_card

    # ==================== 3. 右边栏构建 (垂直分割器：上方报告 + 下方终端) ====================
    def _create_right_panel(self) -> QWidget:
        # 右侧使用垂直分割器，完美实现日志吸底隐藏与向上自由拖动调节大小 (纤细4px手柄)
        self.right_v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_v_splitter.setHandleWidth(4)

        # 3.1 上半部分：Allure 测试报告展示区
        report_section = self._create_report_section()
        self.right_v_splitter.addWidget(report_section)

        # 3.2 下半部分：终端实时执行日志区
        terminal_section = self._create_terminal_section()
        self.right_v_splitter.addWidget(terminal_section)

        # 设置比例：报告区 55%，日志区 45% (保证充裕的初始视野)
        self.right_v_splitter.setStretchFactor(0, 5)
        self.right_v_splitter.setStretchFactor(1, 5)
        self.right_v_splitter.setCollapsible(0, False)
        self.right_v_splitter.setCollapsible(1, True)
        self.right_v_splitter.splitterMoved.connect(self._on_right_splitter_moved)

        # 赋予垂直把手明显的调整大小光标 (上下双向箭头 ↕)
        handle = self.right_v_splitter.handle(1)
        if handle:
            handle.setCursor(Qt.CursorShape.SplitVCursor)

        # 初始尺寸分配 (报告区 450px，终端区 230px，随时自由向上向下拖动改变大小)
        self.right_v_splitter.setSizes([450, 230])

        return self.right_v_splitter

    def _create_report_section(self) -> QWidget:
        panel = QFrame()
        panel.setProperty("class", "panel-card")
        # 允许自由压缩至 60px，彻底解除 QSplitter 向上拖动的硬性尺寸死锁
        panel.setMinimumHeight(60)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # 顶部工具栏 (绝无溢出，只放核心控制项)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(2, 0, 2, 0)
        header_row.setSpacing(10)

        lbl_title = QLabel("📊 测试报告展示 (Allure 可视化面板)")
        lbl_title.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 13px;")
        header_row.addWidget(lbl_title)

        # 状态胶囊药丸 (默认准备就绪)
        self.lbl_status_pill = QLabel("🟢 准备就绪")
        self.lbl_status_pill.setStyleSheet("""
            background-color: #ecfdf5;
            color: #059669;
            border: 1px solid #a7f3d0;
            border-radius: 12px;
            padding: 3px 10px;
            font-weight: 700;
            font-size: 11px;
        """)
        header_row.addWidget(self.lbl_status_pill)

        header_row.addStretch()

        # 1. 填写 Web 回执
        btn_receipt = QPushButton("📝 填写 Web 回执")
        btn_receipt.setStyleSheet("""
            QPushButton {
                background-color: #ecfdf5;
                color: #059669;
                border: 1px solid #a7f3d0;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #d1fae5;
                color: #047857;
                border-color: #6ee7b7;
            }
            QPushButton:pressed {
                background-color: #a7f3d0;
            }
        """)
        btn_receipt.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_receipt.clicked.connect(self._on_click_receipt)
        header_row.addWidget(btn_receipt)

        # 2. 视角切换下拉框 (精简视角 / 完整视角)
        self.combo_view_role = QComboBox()
        self.combo_view_role.addItem("精简视角", "business")
        self.combo_view_role.addItem("完整视角", "tech")
        self.combo_view_role.setFixedWidth(132)
        self.combo_view_role.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                font-weight: 600;
                padding-left: 10px;
                padding-right: 28px;
            }
        """)
        self.combo_view_role.currentIndexChanged.connect(self._on_role_view_changed)
        header_row.addWidget(self.combo_view_role)

        # 3. 刷新报告 (纯白底 / 极速科技蓝文字与边框，超高对比清晰度)
        self.btn_refresh_report = QPushButton("🔄 刷新报告")
        self.btn_refresh_report.setToolTip("在应用内刷新 Allure 可视化报告")
        self.btn_refresh_report.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #2563eb;
                border: 1.5px solid #2563eb;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #eff6ff;
                border-color: #1d4ed8;
                color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #dbeafe;
            }
        """)
        self.btn_refresh_report.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_report.clicked.connect(self.open_allure_report)
        header_row.addWidget(self.btn_refresh_report)

        # 4. 核心运行按钮 (实心科技蓝，白字高对比度)
        self.btn_run = QPushButton("🚀 运行选中")
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: 1px solid #1d4ed8;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #1e40af;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            QPushButton:disabled {
                background-color: #bfdbfe;
                color: #ffffff;
                border-color: #bfdbfe;
            }
        """)
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.clicked.connect(self.run_selected_tests)
        header_row.addWidget(self.btn_run)

        # 5. 终止按钮 (霓虹红，启用实心红白字，禁用柔和灰字浅边框)
        self.btn_stop = QPushButton("⏹️ 终止")
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #e11d48;
                color: #ffffff;
                border: 1px solid #be123c;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #be123c;
            }
            QPushButton:pressed {
                background-color: #9f1239;
            }
            QPushButton:disabled {
                background-color: #f8fafc;
                color: #94a3b8;
                border: 1px solid #e2e8f0;
            }
        """)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_current_test)
        header_row.addWidget(self.btn_stop)

        layout.addLayout(header_row)

        # 嵌入 1:1 原生自绘的 Allure 看板 (默认初始就绪，不展示旧历史假数据)
        self.allure_dashboard = AllureDashboardWidget()
        layout.addWidget(self.allure_dashboard, stretch=1)

        return panel

    def _create_terminal_section(self) -> QWidget:
        panel = QFrame()
        panel.setProperty("class", "panel-card")
        panel.setMinimumHeight(35)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # 终端顶部工具栏 (滚屏、复制、清屏固定在此，彻底消灭顶栏拥挤)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(2, 0, 2, 0)
        header_row.setSpacing(8)

        lbl_term_title = QLabel("📟 终端实时执行日志")
        lbl_term_title.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 12px;")
        header_row.addWidget(lbl_term_title)

        # 正在执行状态提示
        self.lbl_running_case = QLabel("等待启动测试任务")
        self.lbl_running_case.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 6px;")
        header_row.addWidget(self.lbl_running_case)

        header_row.addStretch()

        # 日志检索胶囊工具框 (搜索输入、匹配统计、上/下导航键)
        search_box = QFrame()
        search_box.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            QFrame:hover {
                border-color: #3b82f6;
            }
        """)
        s_layout = QHBoxLayout(search_box)
        s_layout.setContentsMargins(4, 1, 4, 1)
        s_layout.setSpacing(3)

        self.edit_log_search = QLineEdit()
        self.edit_log_search.setPlaceholderText("🔍 搜索日志...")
        self.edit_log_search.setFixedWidth(120)
        self.edit_log_search.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 11px;
                color: #0f172a;
                padding: 1px 2px;
            }
        """)
        self.edit_log_search.textChanged.connect(self._on_log_search_changed)
        self.edit_log_search.returnPressed.connect(self._search_log_next)
        s_layout.addWidget(self.edit_log_search)

        self.lbl_log_search_count = QLabel("0/0")
        self.lbl_log_search_count.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600; min-width: 28px; border: none; background: transparent;")
        self.lbl_log_search_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.addWidget(self.lbl_log_search_count)

        btn_search_prev = QPushButton("▲")
        btn_search_prev.setToolTip("定位到上一个匹配项 (Shift+Enter)")
        btn_search_prev.setFixedSize(18, 18)
        btn_search_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_prev.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #475569;
                font-size: 9px;
                font-weight: bold;
                border-radius: 2px;
            }
            QPushButton:hover {
                background: #e2e8f0;
                color: #0f172a;
            }
        """)
        btn_search_prev.clicked.connect(self._search_log_prev)
        s_layout.addWidget(btn_search_prev)

        btn_search_next = QPushButton("▼")
        btn_search_next.setToolTip("定位到下一个匹配项 (Enter)")
        btn_search_next.setFixedSize(18, 18)
        btn_search_next.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_next.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #475569;
                font-size: 9px;
                font-weight: bold;
                border-radius: 2px;
            }
            QPushButton:hover {
                background: #e2e8f0;
                color: #0f172a;
            }
        """)
        btn_search_next.clicked.connect(self._search_log_next)
        s_layout.addWidget(btn_search_next)

        header_row.addWidget(search_box)

        # 自动滚屏胶囊按钮
        self.btn_toggle_autoscroll = QPushButton("🟢 自动滚屏")
        self.btn_toggle_autoscroll.setProperty("class", "btn-mini")
        self.btn_toggle_autoscroll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_autoscroll.clicked.connect(self._toggle_autoscroll)
        header_row.addWidget(self.btn_toggle_autoscroll)

        btn_copy = QPushButton("📋 复制日志")
        btn_copy.setProperty("class", "btn-mini")
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.clicked.connect(self._copy_logs)
        header_row.addWidget(btn_copy)

        btn_clear = QPushButton("清空终端")
        btn_clear.setProperty("class", "btn-mini")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(self.clear_console)
        header_row.addWidget(btn_clear)

        # 终端折叠胶囊按键
        self.btn_collapse_terminal = QPushButton("▾ 收起")
        self.btn_collapse_terminal.setProperty("class", "btn-mini")
        self.btn_collapse_terminal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_collapse_terminal.clicked.connect(self.toggle_terminal_visibility)
        header_row.addWidget(self.btn_collapse_terminal)

        layout.addLayout(header_row)

        # 极客黑底终端屏幕
        self.console = QPlainTextEdit()
        self.console.setProperty("class", "console-log")
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(40)
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.console.setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: transparent;
                height: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #cbd5e1;
                min-width: 24px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #94a3b8;
            }
            QScrollBar::handle:horizontal:pressed {
                background: #64748b;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                height: 0px;
                background: transparent;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 24px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        # 默认展示专业的引擎就绪日志提示
        default_log_text = (
            "[系统准备就绪] 三条 IM 原生移动自动化测试引擎已初始化。\n"
            "[操作说明] 1. 在左侧用例树选择用例，点击【运行目录】、【运行文件】、【运行类】或单条用例的【运行】。\n"
            "           2. 或直接点击顶部【🚀 运行选中】启动测试。\n"
            "           3. 测试执行期间控制台将实时输出日志，测试完成后右侧看板将自动实时动态解析并呈现最新测试报告。\n"
        )
        self.console.setPlainText(default_log_text)
        layout.addWidget(self.console, stretch=1)

        # 底部状态行
        self.status_bar = QLabel("就绪 - 随时可以启动测试任务")
        self.status_bar.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.status_bar)

        return panel

    # ==================== 4. 垂直与水平分割器拖拽折叠与记忆恢复 ====================
    def _on_h_splitter_moved(self, pos: int, index: int):
        """左右主布局分割器拖拽调整时，实时持久化尺寸记忆"""
        sizes = self.main_h_splitter.sizes()
        if len(sizes) == 2 and sum(sizes) > 0:
            desktop_config.set("mobile", "splitter_h_sizes", sizes)

    def _on_right_splitter_moved(self, pos: int, index: int):
        """当下半部分高度拖动到最底部（<= 30px）时吸底折叠隐藏，向上拖动恢复"""
        sizes = self.right_v_splitter.sizes()
        if len(sizes) > 1:
            bottom_h = sizes[1]
            if bottom_h <= 30:
                self._is_log_collapsed = True
                self.btn_collapse_terminal.setText("▴ 展开")
            else:
                self._is_log_collapsed = False
                self._last_log_height = max(bottom_h, 180)
                self.btn_collapse_terminal.setText("▾ 收起")
            desktop_config.set("mobile", "splitter_v_sizes", sizes)
            desktop_config.set("mobile", "log_collapsed", self._is_log_collapsed)
            desktop_config.set("mobile", "last_log_height", self._last_log_height)

    def toggle_terminal_visibility(self):
        """一键平滑折叠或展开下半部分日志终端"""
        sizes = self.right_v_splitter.sizes()
        total = sum(sizes)
        if self._is_log_collapsed:
            target_h = getattr(self, "_last_log_height", 230)
            self.right_v_splitter.setSizes([total - target_h, target_h])
            self._is_log_collapsed = False
            self.btn_collapse_terminal.setText("▾ 收起")
        else:
            if len(sizes) > 1 and sizes[1] > 30:
                self._last_log_height = sizes[1]
            self.right_v_splitter.setSizes([total, 0])
            self._is_log_collapsed = True
            self.btn_collapse_terminal.setText("▴ 展开")
        desktop_config.set("mobile", "splitter_v_sizes", self.right_v_splitter.sizes())
        desktop_config.set("mobile", "log_collapsed", self._is_log_collapsed)
        desktop_config.set("mobile", "last_log_height", self._last_log_height)

    def _restore_splitter_sizes(self):
        """在首屏几何布局稳定后二次精确应用分割器尺寸，确保像素级还原"""
        cfg = desktop_config.get_section("mobile")
        h_sizes = cfg.get("splitter_h_sizes", None)
        if h_sizes and isinstance(h_sizes, list) and len(h_sizes) == 2 and sum(h_sizes) > 0:
            self.main_h_splitter.setSizes(h_sizes)

        v_sizes = cfg.get("splitter_v_sizes", None)
        if v_sizes and isinstance(v_sizes, list) and len(v_sizes) == 2 and sum(v_sizes) > 0:
            if not getattr(self, "_is_log_collapsed", False):
                self.right_v_splitter.setSizes(v_sizes)

    def save_layout_state(self):
        """退出应用时完整同步分割器尺寸与调试变量"""
        h_sizes = self.main_h_splitter.sizes()
        if len(h_sizes) == 2 and sum(h_sizes) > 0:
            desktop_config.set("mobile", "splitter_h_sizes", h_sizes)
        v_sizes = self.right_v_splitter.sizes()
        if len(v_sizes) == 2 and sum(v_sizes) > 0:
            desktop_config.set("mobile", "splitter_v_sizes", v_sizes)
            desktop_config.set("mobile", "log_collapsed", self._is_log_collapsed)
            desktop_config.set("mobile", "last_log_height", self._last_log_height)

        if hasattr(self, 'edit_private_chat') and hasattr(self, 'edit_group_chat'):
            desktop_config.set("mobile", "private_chat_name", self.edit_private_chat.text().strip())
            desktop_config.set("mobile", "group_chat_name", self.edit_group_chat.text().strip())

        if hasattr(self, 'params_body'):
            desktop_config.set("mobile", "params_collapsed", not self.params_body.isVisible())

        self._save_tree_state()

    def _set_autoscroll_state(self, enabled: bool):
        """设置自动滚屏（向下滚动）状态与 UI 展现 (True: 启动向下滚动, False: 停止向下滚动)"""
        self._auto_scroll = bool(enabled)
        if self._auto_scroll:
            self.btn_toggle_autoscroll.setText("🟢 自动滚屏")
            self.btn_toggle_autoscroll.setStyleSheet("background-color: #ecfdf5; color: #059669; font-weight: 700; border: 1px solid #a7f3d0; border-radius: 4px;")
            self.btn_toggle_autoscroll.setToolTip("当前状态: 已开启向下自动滚屏 (新日志产生时自动向下滚动至最底部)")
            self._scroll_to_bottom()
        else:
            self.btn_toggle_autoscroll.setText("⚪ 滚屏暂停")
            self.btn_toggle_autoscroll.setStyleSheet("background-color: #f1f5f9; color: #64748b; font-weight: 500; border: 1px solid #cbd5e1; border-radius: 4px;")
            self.btn_toggle_autoscroll.setToolTip("当前状态: 已关闭向下自动滚屏 (可随意向上翻阅排查历史日志)")

    def _scroll_to_bottom(self):
        """向下滚动日志终端至最底部"""
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        scrollbar = self.console.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def _toggle_autoscroll(self):
        """切换自动向下滚屏状态，并持久化写入配置 (启动为 True，未启动为 False)"""
        new_state = not getattr(self, "_auto_scroll", True)
        self._set_autoscroll_state(new_state)
        desktop_config.set("mobile", "auto_scroll_log", self._auto_scroll)

    # ==================== 5. 用例树构建与状态呈现 (1:1 复刻红框与红点) ====================
    def _create_tree_action_widget(self, text: str, btn_class: str, width: int, on_click) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        btn = QPushButton(text)
        btn.setProperty("class", btn_class)
        btn.setFixedSize(width, 22)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(on_click)

        layout.addWidget(btn)
        return container

    def _update_node_action_button(self, item: QTreeWidgetItem, status: str):
        """
        右侧操作按钮保持全局统一的空心透明胶囊风格，不随测试用例执行结果改变颜色；
        悬浮 (hover) 态统一在全局 QSS 中高亮为翡翠绿，不需要区分对待。
        """
        widget = self.tree.itemWidget(item, 1)
        if not widget:
            return
        buttons = widget.findChildren(QPushButton)
        for btn in buttons:
            if btn.styleSheet():
                btn.setStyleSheet("")

    def _create_file_node_actions(self, file_path: str, display_name: str) -> QWidget:
        """为二级文件节点创建【📄 文档】与【运行文件】双胶囊按钮组件"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 1. 📄 文档按钮 (点击打开 test_docs 对应文档)
        btn_doc = QPushButton("📄 文档")
        btn_doc.setProperty("class", "tree-pill-btn-doc")
        btn_doc.setToolTip(f"查看【{display_name}】对应的测试用例文档说明")
        btn_doc.setFixedSize(54, 22)
        btn_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_doc.clicked.connect(lambda ch, f=file_path, n=display_name: self._open_test_doc(f, n))
        layout.addWidget(btn_doc)

        # 2. 运行文件按钮
        btn_run = QPushButton("运行文件")
        btn_run.setProperty("class", "tree-pill-btn-file")
        btn_run.setToolTip(f"批量执行【{display_name}】中的全部测试用例")
        btn_run.setFixedSize(66, 22)
        btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_run.clicked.connect(lambda ch, f=file_path, n=display_name: self._run_target_node(f, n))
        layout.addWidget(btn_run)

        return container

    def _find_test_doc_path(self, file_path_or_target: str, display_name: str) -> Optional[Path]:
        """
        智能解析测试文件对应的文档说明路径：
        1. 动态获取 test_docs 根目录（兼顾开发态与打包安装态，无写死路径）
        2. 基于测试文件名 stem 深度全量检索匹配
        3. 基于 display_name 中文关键词深度模糊检索匹配
        """
        project_root = Path(SmartPathResolver.get_project_root())
        candidates = [
            project_root / "test_docs",
            Path(sys.executable).parent / "test_docs",
            Path.cwd() / "test_docs"
        ]
        doc_root: Optional[Path] = None
        for c in candidates:
            if c.is_dir():
                doc_root = c
                break

        if not doc_root:
            return None

        # 提取文件基本名称，例如 test_smoke_chat.py -> test_smoke_chat
        file_stem = Path(file_path_or_target).stem.lower()

        # 优先级 1: 文档名中精确包含测试文件 stem (例如 【冒烟测试-单聊-基础与设置】test_smoke_chat.md)
        for p in doc_root.rglob("*.md"):
            p_name = p.stem.lower()
            if p_name.endswith(file_stem) or f"{file_stem}" in p_name:
                return p

        # 优先级 2: 文档名中包含中文 display_name (如 "单聊-基础与设置")
        clean_display = re.sub(r"[^\w\u4e00-\u9fa5]", "", display_name)
        if clean_display:
            for p in doc_root.rglob("*.md"):
                p_clean = re.sub(r"[^\w\u4e00-\u9fa5]", "", p.stem)
                if clean_display in p_clean or p_clean in clean_display:
                    return p

        return None

    def _open_test_doc(self, file_path: str, display_name: str):
        """点击文档按钮，弹出对应的测试用例文档说明"""
        doc_path = self._find_test_doc_path(file_path, display_name)
        if not doc_path or not doc_path.is_file():
            self.append_log(f"⚠ 未在 test_docs 目录下找到与【{display_name}】({file_path}) 对应的用例文档。")
            QMessageBox.warning(
                self, "未找到文档",
                f"未在 test_docs 目录中检索到与以下用例对应的说明文档：\n\n• 模块: {display_name}\n• 文件: {file_path}"
            )
            return

        self.append_log(f"📖 正在打开用例文档说明: {doc_path.name}")
        dialog = MarkdownDocDialog(str(doc_path), display_name, self)
        dialog.exec()

    def _trigger_live_sync(self):
        """触发用例实时同步，弹出专属 Loading 进度模态弹窗"""
        # 1. 禁用同步按钮防抖
        if hasattr(self, 'btn_sync'):
            self.btn_sync.setEnabled(False)
            self.btn_sync.setText("同步中...")

        # 2. 居中展示专属 Loading 进度弹窗
        dialog = SyncProgressDialog(self)
        if self.window():
            geo = self.window().geometry()
            x = geo.x() + (geo.width() - dialog.width()) // 2
            y = geo.y() + (geo.height() - dialog.height()) // 2
            dialog.move(max(0, x), max(0, y))
        dialog.show()
        dialog.set_progress(15, "🔍 检索 tests/ 目录测试文件结构...", "🔄 正在同步测试用例...")
        self.append_log("🚀 [Sync] 正在启动测试用例实时同步...")

        # 3. 阶段 2 (45%): AST 语法分析
        def step_ast():
            dialog.set_progress(45, "🧩 运行 AST 引擎提取用例类、方法与参数...")
            QTimer.singleShot(70, step_collect)

        # 4. 阶段 3 (80%): 写入索引并重构树视图
        def step_collect():
            dialog.set_progress(80, "📊 写入 tests_catalog.json 索引并重构树视图...")
            self.refresh_test_cases(force_refresh=True)
            QTimer.singleShot(80, step_done)

        # 5. 阶段 4 (100%): 完成反馈与自动关闭弹窗
        def step_done():
            dialog.set_progress(100, f"✅ 已成功收录 {self.total_case_count} 条测试用例", "✅ 测试用例同步完成！")
            if hasattr(self, 'btn_sync'):
                self.btn_sync.setText("已同步")
            self.append_log(f"✨ [Sync] 用例全量同步完成！目录树已更新就绪（共收录 {self.total_case_count} 条测试用例）")
            # 600ms 后自动关闭弹窗并复位按钮
            QTimer.singleShot(600, step_finish)

        def step_finish():
            dialog.accept()
            if hasattr(self, 'btn_sync'):
                self.btn_sync.setText("同步")
                self.btn_sync.setEnabled(True)

        QTimer.singleShot(60, step_ast)

    def refresh_test_cases(self, force_refresh: bool = False):
        self.tree.clear()
        self.hierarchy_data = TestCollectorService.get_test_hierarchy("mobile", force_refresh=force_refresh)

        total_collected = 0
        if force_refresh:
            self.append_log("🔄 已完成 tests/ 本地用例目录实时全量扫描，用例目录树已同步至最新！")

        has_memory = bool(getattr(self, "expanded_targets", None))
        self._is_batch_expanding = True

        try:
            for c_idx, cat in enumerate(self.hierarchy_data):
                # 1. 一级目录节点 (📖) - 挂载【运行目录】操作按钮，前缀纯净无状态球
                cat_item = QTreeWidgetItem(self.tree)
                cat_name = cat["display_name"]
                cat_count = cat["count"]
                total_collected += cat_count

                cat_item.setText(0, f"📖  {cat_name} [{cat_count}]")
                cat_item.setToolTip(0, f"一级测试目录: {cat['target']}\n包含 {cat_count} 个测试用例")
                cat_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "target": cat["target"], "name": cat_name, "count": cat_count})

                action_cat = self._create_tree_action_widget(
                    "运行目录", "tree-pill-btn-dir", 66,
                    lambda ch, t=cat["target"], n=cat_name: self._run_target_node(t, n)
                )
                self.tree.setItemWidget(cat_item, 1, action_cat)

                cat_expanded = (cat["target"] in self.expanded_targets) if has_memory else (c_idx == 0)
                cat_item.setExpanded(cat_expanded)

                # 2. 二级文件节点 (👾) - 挂载【📄 文档】与【运行文件】双按钮，前缀纯净无状态球
                for f_idx, file_obj in enumerate(cat.get("files", [])):
                    file_item = QTreeWidgetItem(cat_item)
                    file_name = file_obj.get('display_name', file_obj['file'])
                    file_count = file_obj.get("count", 0)

                    file_item.setText(0, f"👾  {file_name} [{file_count}]")
                    file_item.setToolTip(0, f"二级测试文件: {file_obj['file']}\n包含 {file_count} 个测试用例")
                    file_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "file", "target": file_obj["file"], "name": file_name, "count": file_count})

                    action_file = self._create_file_node_actions(file_obj["file"], file_name)
                    self.tree.setItemWidget(file_item, 1, action_file)

                    file_expanded = (file_obj["file"] in self.expanded_targets) if has_memory else (c_idx == 0 and f_idx == 0)
                    file_item.setExpanded(file_expanded)

                    # 3. 三级类节点 (🧱)
                    for cl_idx, cls in enumerate(file_obj.get("classes", [])):
                        cls_item = QTreeWidgetItem(file_item)
                        cls_name = cls.get('display_name', cls['name'])
                        cls_nodeid = f"{file_obj['file']}::{cls['name']}"

                        cls_item.setText(0, f"🧱  {cls_name}")
                        cls_item.setToolTip(0, f"三级测试类: {cls_nodeid}")
                        cls_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "class", "target": cls_nodeid, "name": cls_name, "count": 0})

                        action_cls = self._create_tree_action_widget(
                            "运行类", "tree-pill-btn-class", 56,
                            lambda ch, node=cls_nodeid, n=cls_name: self._run_target_node(node, n)
                        )
                        self.tree.setItemWidget(cls_item, 1, action_cls)

                        is_search_class = "检索" in cls_name
                        cls_expanded = (cls_nodeid in self.expanded_targets) if has_memory else (c_idx == 0 and f_idx == 0 and (cl_idx == 0 or is_search_class))
                        cls_item.setExpanded(cls_expanded)

                        # 4. 四级测试用例 (带失败红点 🔴 / 正常 ⚙️，与用户红框完全对齐)
                        for test in cls.get("tests", []):
                            self._add_leaf_item(cls_item, file_obj["file"], cls["name"], test)

                    for test in file_obj.get("tests", []):
                        self._add_leaf_item(file_item, file_obj["file"], "", test)
        finally:
            self._is_batch_expanding = False

        if total_collected > 0:
            self.total_case_count = total_collected
            if hasattr(self, 'top_status_pill'):
                self.top_status_pill.update_case_count(self.total_case_count)
            else:
                self.lbl_case_pill.setText(f"✏️ 用例: {self.total_case_count} 条")

        # 初始化应用全树自底向上状态球
        self._update_tree_node_icons()

    @staticmethod
    def _get_priority_desc(priority: str) -> str:
        """获取用例优先级的业务标准语义说明"""
        mapping = {
            "P0": "P0 (核心阻断 / 冒烟用例，MR/PR 门禁必跑)",
            "P1": "P1 (关键业务 / 核心功能用例)",
            "P2": "P2 (常规验证 / 基础功能用例)",
            "P3": "P3 (次要边缘 / 异常容错用例)",
            "P4": "P4 (轻微琐碎 / 辅助提示用例)",
        }
        return mapping.get(priority.upper(), f"{priority} (未定义级别)") if priority else "P2 (默认常规)"

    @staticmethod
    def _format_node_display_text(status: str, node_type: str, name: str, count: int = 0, priority: str = "") -> str:
        """
        统一格式化各级节点的文本：
        - param (参数项)：  ⚪/🟢/🔴 ⚙️  [P0] [私聊模式]
        - test (测试函数)：⚪/🟢/🔴 ⚙️  [P0] 发送基础 Text 消息
        - class (测试类)：⚪/🟢/🔴 🧱  聊天模块-文本消息收发
        - file (测试文件)：👾  聊天模块-文本消息收发 [13] (纯净导航，无状态球)
        - category (目录)：📖  chat [13] (纯净导航，无状态球)
        """
        if status == "passed":
            ball = "🟢"
        elif status == "failed":
            ball = "🔴"
        elif status in ("broken", "error"):
            ball = "🟠"
        elif status in ("skipped", "ignored", "canceled"):
            ball = "⚪"
        else:
            ball = "⚪"

        p_tag = f"[{priority.upper()}] " if priority else ""

        if node_type == "param":
            return f"  {ball} ⚙️  {p_tag}[{name}]"
        elif node_type == "test":
            return f"{ball} ⚙️  {p_tag}{name}"
        elif node_type == "class":
            return f"{ball} 🧱  {name}"
        elif node_type == "file":
            cnt_str = f" [{count}]" if count else ""
            return f"{ball} 👾  {name}{cnt_str}"
        elif node_type == "category":
            cnt_str = f" [{count}]" if count else ""
            return f"📖  {name}{cnt_str}"
        return f"{name}"

    @staticmethod
    def _format_test_node_text(status: str, display_name: str, priority: str = "") -> str:
        """保持原有测试函数格式化方法兼容"""
        return MobilePage._format_node_display_text(status, "test", display_name, priority=priority)

    def _add_leaf_item(self, parent: QTreeWidgetItem, file_path: str, cls_name: str, test: Dict[str, Any]):
        node_id = f"{file_path}::{cls_name}::{test['name']}" if cls_name else f"{file_path}::{test['name']}"
        test_display = test.get('display_name', test['name'])
        priority = test.get("priority", "P2")
        params = test.get("params", [])

        # 状态匹配：默认空心球 ⚪ ⚙️，通过 🟢 ⚙️，失败 🔴 ⚙️，异常 🟠 ⚙️，跳过 ⚪ ⚙️
        status = self.node_status_map.get(node_id, "")

        test_item = QTreeWidgetItem(parent)
        test_item.setText(0, self._format_test_node_text(status, test_display, priority=priority))
        p_desc = self._get_priority_desc(priority)
        status_desc = "通过" if status == "passed" else ("失败" if status == "failed" else ("异常" if status in ("broken", "error") else ("跳过" if status in ("skipped", "ignored", "canceled") else "未执行")))
        test_item.setToolTip(0, f"用例: {test_display}\n节点: {node_id}\n优先级: {p_desc}\n状态: {status_desc}")
        test_item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": "test",
            "target": node_id,
            "name": test_display,
            "priority": priority
        })

        # 区分层级：若该测试节点包含参数化子项(孙子用例)，按钮文字显示为 "运行函数"
        btn_test_label = "运行函数" if params else "运行"
        btn_test_width = 58 if params else 46
        action_test = self._create_tree_action_widget(
            btn_test_label, "tree-pill-btn", btn_test_width,
            lambda ch, node=node_id, n=test_display: self._run_target_node(node, n)
        )
        self.tree.setItemWidget(test_item, 1, action_test)

        if params:
            for p in params:
                sub_item = QTreeWidgetItem(test_item)
                sub_node = f"{node_id}[{p}]"
                sub_status = self.node_status_map.get(sub_node, "")
                sub_status_desc = "通过" if sub_status == "passed" else ("失败" if sub_status == "failed" else ("异常" if sub_status in ("broken", "error") else ("跳过" if sub_status in ("skipped", "ignored", "canceled") else "未执行")))

                sub_item.setText(0, self._format_node_display_text(sub_status, "param", str(p), priority=priority))
                sub_item.setToolTip(0, f"参数项: {p}\n父用例: {test_display}\n节点: {sub_node}\n优先级: {p_desc}\n状态: {sub_status_desc}")
                sub_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "param",
                    "target": sub_node,
                    "name": str(p),
                    "priority": priority
                })

                action_param = self._create_tree_action_widget(
                    "运行", "tree-pill-btn", 46,
                    lambda ch, node=sub_node, n=str(p): self._run_target_node(node, n)
                )
                self.tree.setItemWidget(sub_item, 1, action_param)
            test_expanded = (node_id in self.expanded_targets) if getattr(self, "expanded_targets", None) else False
            test_item.setExpanded(test_expanded)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """点击目录或节点标题 (第0列) 时即可直接切换展开与折叠，无需瞄准小箭头"""
        if column == 0 and item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def _on_tree_item_expanded(self, item: QTreeWidgetItem):
        """当节点展开时，记录展开记忆并在非批量时执行手风琴模式"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and "target" in data:
            if not hasattr(self, "expanded_targets"):
                self.expanded_targets = set()
            self.expanded_targets.add(data["target"])

        if getattr(self, "_is_batch_expanding", False):
            return
        # 搜索过滤中不干扰全局匹配结果
        if self.edit_search.text().strip():
            return

        # 针对一级目录 (顶级节点，parent 为 None) 执行手风琴单开模式
        if item.parent() is None:
            self.tree.blockSignals(True)
            try:
                for i in range(self.tree.topLevelItemCount()):
                    top = self.tree.topLevelItem(i)
                    if top is not item and top.isExpanded():
                        top.setExpanded(False)
                        top_data = top.data(0, Qt.ItemDataRole.UserRole)
                        if top_data and "target" in top_data and top_data["target"] in self.expanded_targets:
                            self.expanded_targets.discard(top_data["target"])
            finally:
                self.tree.blockSignals(False)

    def _on_tree_item_collapsed(self, item: QTreeWidgetItem):
        """当节点折叠时，同步移除展开记忆"""
        if getattr(self, "_is_batch_expanding", False):
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and "target" in data and hasattr(self, "expanded_targets"):
            self.expanded_targets.discard(data["target"])

    def _collect_expanded_targets(self) -> List[str]:
        """递归遍历整棵测试树，收集当前所有处于展开状态的节点 target"""
        expanded_list = []
        def visit(item: QTreeWidgetItem):
            if item.isExpanded():
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data and "target" in data:
                    expanded_list.append(data["target"])
                for i in range(item.childCount()):
                    visit(item.child(i))
        for i in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(i))
        return expanded_list

    def _save_tree_state(self):
        """持久化保存用例执行状态映射与树节点展开记忆，实现全局记忆模式"""
        try:
            # 1. 持久化用例状态映射 (⚪/🟢/🔴)
            if hasattr(self, "node_status_map") and self.node_status_map:
                desktop_config.set("mobile", "node_status_map", dict(self.node_status_map))
            # 2. 持久化树节点展开状态
            expanded = self._collect_expanded_targets()
            if expanded:
                desktop_config.set("mobile", "expanded_targets", expanded)
            desktop_config.save()
        except Exception:
            pass

    def _on_tree_item_double_clicked(self, item: QTreeWidgetItem, col: int):
        """
        双击树节点仅用于展开/折叠，不直接触发运行测试用例 (防误触设计)；
        运行操作统一由右侧对应的操作按钮触发。
        """
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def _filter_test_cases(self, text: str):
        q = text.strip().lower()
        def filter_item(item: QTreeWidgetItem) -> bool:
            data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            item_priority = str(data.get("priority", "")).lower()
            self_match = (q in item.text(0).lower() or (item_priority and q == item_priority)) if q else True
            child_match = False
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    child_match = True
            is_visible = self_match or child_match
            item.setHidden(not is_visible)
            if q and child_match:
                item.setExpanded(True)
            return is_visible

        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))

    def _expand_all(self):
        self._is_batch_expanding = True
        try:
            self.tree.expandAll()
        finally:
            self._is_batch_expanding = False

    def _collapse_all(self):
        self.tree.collapseAll()

    def _toggle_params_collapse(self):
        """一键展开/收起远程测试与参数配置面板，并持久化状态记忆"""
        is_visible = self.params_body.isVisible()
        new_visible = not is_visible
        self.params_body.setVisible(new_visible)
        self.btn_toggle_collapse.setText("收起" if new_visible else "展开")
        desktop_config.set("mobile", "params_collapsed", not new_visible)
        desktop_config.save()

    def _reset_params(self):
        self.combo_appium1.setEditText(f"{self.lan_ip}:4723 (局域网本机)")
        self.combo_appium2.setEditText(f"{self.lan_ip}:4724 (局域网本机)")
        self.combo_udid1.setEditText("nzwcvo9ls87hws7t")
        self.combo_udid2.setEditText("3865BN02GU600000")
        self.edit_private_chat.setText("")
        self.edit_group_chat.setText("")
        self.chk_debug_mode.setChecked(False)
        self.combo_view_role.setCurrentIndex(0)
        self._set_autoscroll_state(True)
        desktop_config.set("mobile", "auto_scroll_log", True)
        self.params_body.setVisible(True)
        self.btn_toggle_collapse.setText("收起")
        desktop_config.set("mobile", "params_collapsed", False)
        self._on_config_changed()
        QMessageBox.information(self, "提示", "参数配置已恢复为默认值！")

    # ==================== 6. 状态持久化 ====================
    def load_persisted_config(self):
        cfg = desktop_config.get_section("mobile")
        current_host_os = "Win" if sys.platform == "win32" else ("Mac" if sys.platform == "darwin" else "Linux")
        saved_os = cfg.get("os_type")
        self.combo_os.setCurrentText(saved_os if saved_os in ["Win", "Mac", "Linux"] else current_host_os)
        
        ap1 = cfg.get("remote_appium", f"{self.lan_ip}:4723 (局域网本机)")
        ap2 = cfg.get("remote_appium2", f"{self.lan_ip}:4724 (局域网本机)")
        self.combo_appium1.setEditText(ap1)
        self.combo_appium2.setEditText(ap2)

        u1 = cfg.get("remote_udid", "nzwcvo9ls87hws7t")
        u2 = cfg.get("remote_udid2", "3865BN02GU600000")
        self.combo_udid1.setEditText(u1)
        self.combo_udid2.setEditText(u2)

        self.edit_private_chat.setText(cfg.get("private_chat_name", ""))
        self.edit_group_chat.setText(cfg.get("group_chat_name", ""))
        self.chk_debug_mode.setChecked(bool(cfg.get("debug_mode", False)))

        role = cfg.get("role", "business")
        idx = 0 if role == "business" else 1
        self.combo_view_role.setCurrentIndex(idx)
        if hasattr(self, "allure_dashboard") and self.allure_dashboard:
            self.allure_dashboard.set_role_view(role)

        # 加载持久化的 Web 回执字段列表
        self.web_receipt_fields = cfg.get("web_receipt_fields", [
            {"key": "设备1", "val": ""},
            {"key": "私聊用户1", "val": ""},
            {"key": "私聊用户2", "val": ""},
            {"key": "群聊名称1", "val": ""},
            {"key": "群聊名称2", "val": ""},
        ])

        # 恢复用例执行状态记忆与树节点展开记忆
        self.node_status_map = dict(cfg.get("node_status_map", {}))
        self.expanded_targets = set(cfg.get("expanded_targets", []))

        # 恢复左右与上下分割器布局尺寸记忆
        h_sizes = cfg.get("splitter_h_sizes", None)
        if h_sizes and isinstance(h_sizes, list) and len(h_sizes) == 2 and sum(h_sizes) > 0:
            self.main_h_splitter.setSizes(h_sizes)

        v_sizes = cfg.get("splitter_v_sizes", None)
        if v_sizes and isinstance(v_sizes, list) and len(v_sizes) == 2 and sum(v_sizes) > 0:
            self.right_v_splitter.setSizes(v_sizes)

        self._is_log_collapsed = bool(cfg.get("log_collapsed", False))
        self._last_log_height = cfg.get("last_log_height", 230)
        if self._is_log_collapsed:
            total = sum(self.right_v_splitter.sizes())
            self.right_v_splitter.setSizes([total, 0])
            self.btn_collapse_terminal.setText("▴ 展开")
        else:
            self.btn_collapse_terminal.setText("▾ 收起")

        # 恢复自动向下滚屏记忆 (启动为 True，未启动为 False，默认 True)
        saved_autoscroll = cfg.get("auto_scroll_log", True)
        self._set_autoscroll_state(saved_autoscroll)

        # 恢复远程测试与参数配置面板的折叠/展开记忆
        params_collapsed = bool(cfg.get("params_collapsed", False))
        if hasattr(self, 'params_body') and hasattr(self, 'btn_toggle_collapse'):
            self.params_body.setVisible(not params_collapsed)
            self.btn_toggle_collapse.setText("展开" if params_collapsed else "收起")

    def _on_role_view_changed(self, index: int):
        """视角切换响应槽：动态联动 Allure 看板视角过滤并在日志区提示"""
        role = self.combo_view_role.currentData() or ("business" if index == 0 else "tech")
        desktop_config.set("mobile", "role", role)
        if hasattr(self, "allure_dashboard") and self.allure_dashboard:
            self.allure_dashboard.set_role_view(role)
        role_desc = "💼 业务精简视角 (智能隐藏底层Suites，聚焦业务概览与缺陷排查)" if role == "business" else "🛠️ 开发完整视角 (全量展开4大导航与耗时节点)"
        self.append_log(f"👁️ Allure 可视化看板已切换为: {role_desc}")

    def _on_config_changed(self):
        if getattr(self, "_is_loading_config", False):
            return
        role = self.combo_view_role.currentData() or "business"
        desktop_config.set("mobile", "os_type", self.combo_os.currentText())
        desktop_config.set("mobile", "remote_appium", self.combo_appium1.currentText().strip())
        desktop_config.set("mobile", "remote_appium2", self.combo_appium2.currentText().strip())
        desktop_config.set("mobile", "remote_udid", self.combo_udid1.currentText().strip())
        desktop_config.set("mobile", "remote_udid2", self.combo_udid2.currentText().strip())
        desktop_config.set("mobile", "private_chat_name", self.edit_private_chat.text().strip())
        desktop_config.set("mobile", "group_chat_name", self.edit_group_chat.text().strip())
        desktop_config.set("mobile", "debug_mode", self.chk_debug_mode.isChecked())
        desktop_config.set("mobile", "role", role)
        if hasattr(self, "allure_dashboard") and self.allure_dashboard:
            self.allure_dashboard.set_role_view(role)

    def _save_chat_vars(self):
        """保存私聊和群聊变量至本地配置，确保再次启动后数据完整恢复（记忆模式）"""
        pri = self.edit_private_chat.text().strip()
        grp = self.edit_group_chat.text().strip()
        desktop_config.set("mobile", "private_chat_name", pri)
        desktop_config.set("mobile", "group_chat_name", grp)
        desktop_config.save()

        pri_desc = pri if pri else "<未设置>"
        grp_desc = grp if grp else "<未设置>"
        self.append_log(f"💾 [记忆模式] 业务调试变量已保存：私聊=[{pri_desc}], 群聊=[{grp_desc}]，下次启动将自动还原！")

        # 按钮即时变绿高亮反馈 1.5 秒
        self.btn_save_chat.setText("✅ 已保存")
        self.btn_save_chat.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                border: 1px solid #047857;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 700;
            }
        """)
        QTimer.singleShot(1500, self._restore_save_chat_btn_style)

    def _restore_save_chat_btn_style(self):
        if hasattr(self, 'btn_save_chat') and self.btn_save_chat:
            self.btn_save_chat.setText("保存")
            self.btn_save_chat.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    color: #ffffff;
                    border: 1px solid #1d4ed8;
                    border-radius: 4px;
                    padding: 2px 10px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #1d4ed8;
                }
                QPushButton:pressed {
                    background-color: #1e40af;
                }
            """)

    def _clear_chat_vars(self):
        """清空私聊和群聊输入框，并同步清空持久化存储"""
        self.edit_private_chat.blockSignals(True)
        self.edit_group_chat.blockSignals(True)
        try:
            self.edit_private_chat.clear()
            self.edit_group_chat.clear()
        finally:
            self.edit_private_chat.blockSignals(False)
            self.edit_group_chat.blockSignals(False)

        desktop_config.set("mobile", "private_chat_name", "")
        desktop_config.set("mobile", "group_chat_name", "")
        desktop_config.save()
        self.append_log("🗑️ 业务调试变量 (私聊 / 群聊) 已清空，持久化配置已同步重置！")

    # ==================== 7. 设备与报告辅助 ====================
    def _refresh_report_pill_count(self):
        """实时同步报告中心当前实际存在的有效测试报告总份数"""
        try:
            count = get_reports_count()
            if hasattr(self, 'top_status_pill'):
                self.top_status_pill.update_report_count(count)
            else:
                self.lbl_report_pill.setText(f"📑 报告: {count} 份")
        except Exception:
            pass

    def _on_top_refresh_clicked(self):
        self._trigger_live_sync()
        self.auto_detect_devices()
        self._refresh_report_pill_count()
        self.allure_dashboard.load_latest_report()
        stat = getattr(self.allure_dashboard, "current_data", {})
        cases = stat.get("cases", [])
        if cases:
            self._sync_cases_to_tree_status(cases, scope_checker=None)
            self._update_tree_node_icons()
            self._save_tree_state()
            if hasattr(self, 'allure_dashboard') and self.allure_dashboard:
                self.allure_dashboard._render_cases_detail_list()
        self.append_log("🔄 顶栏已完成全量设备、用例集与报告指标的实时同步！")

    def auto_detect_devices(self):
        details = DeviceManager.scan_connected_devices()
        all_devs = details.get("all_devices", [])
        
        cfg = desktop_config.get_section("mobile")
        d1 = cfg.get("remote_udid", "nzwcvo9ls87hws7t")
        d2 = cfg.get("remote_udid2", "3865BN02GU600000")

        self.combo_udid1.clear()
        self.combo_udid2.clear()

        items = all_devs.copy()
        for d in [d1, d2, "nzwcvo9ls87hws7t", "3865BN02GU600000", "QFF0219A11009305", "20a5fa17"]:
            if d and d not in items:
                items.append(d)

        self.combo_udid1.addItems(items)
        self.combo_udid2.addItems(items)
        self.combo_udid1.setEditText(d1)
        self.combo_udid2.setEditText(d2)

        # 更新右上角设备在线药丸
        online_count = len(all_devs) if all_devs else 1
        if hasattr(self, 'top_status_pill'):
            self.top_status_pill.update_device_count(online_count)
        else:
            self.lbl_device_pill.setText(f"🟢 设备: {online_count} 台在线")

    def _detect_single_device(self, target_idx: int):
        """
        单端极速真机检测与自动绑定：
        支持跨 Windows 与 macOS，深度检测 iOS (tidevice/idevice_id/xcrun)、
        鸿蒙 HarmonyOS NEXT (hdc) 与 Android (adb) 物理硬件真机。
        """
        self.append_log("--------------------------------------------------")
        self.append_log(f"🔍 [检测真机] 正在深度扫描移动端物理真机 (iOS / 鸿蒙 / Android)...")
        QApplication.processEvents()

        details = DeviceManager.scan_connected_devices()
        device_items = details.get("device_items", [])
        real_list = details.get("real_devices", [])
        all_list = details.get("all_devices", [])

        # 建立设备 UDID 到属性的快速映射
        dev_map = {item.get("udid"): item for item in device_items}

        # 内存同步下拉选项
        for udid in all_list:
            if self.combo_udid1.findText(udid) == -1:
                self.combo_udid1.addItem(udid)
            if self.combo_udid2.findText(udid) == -1:
                self.combo_udid2.addItem(udid)

        # 同步更新顶部药丸计数
        total_online = len(all_list)
        if hasattr(self, 'top_status_pill'):
            self.top_status_pill.update_device_count(total_online)
        elif hasattr(self, 'lbl_device_pill'):
            self.lbl_device_pill.setText(f"🟢 设备: {total_online} 台在线" if total_online else "⚪ 设备: 0 台在线")

        if target_idx == 1:
            if real_list:
                chosen_udid = real_list[0]
                item = dev_map.get(chosen_udid, {})
                plat = item.get("platform", "移动端")
                self.combo_udid1.setEditText(chosen_udid)
                self.append_log(f"✅ [发送端] 成功识别并绑定 USB 物理真机 [{plat}]: {chosen_udid}")
            elif all_list:
                chosen_udid = all_list[0]
                item = dev_map.get(chosen_udid, {})
                plat = item.get("platform", "移动端")
                self.combo_udid1.setEditText(chosen_udid)
                self.append_log(f"ℹ️ [发送端] 暂无物理真机，已自动绑定在线设备 [{plat}]: {chosen_udid}")
            else:
                self.append_log("❌ [发送端] 未检测到任何物理真机或模拟器连接！")
                QMessageBox.warning(self, "未检测到真机", "未检测到任何 USB 硬件真机！\n\n请确认：\n1. iOS 设备：已信任此电脑并在后台保持连接 (tidevice/Xcode)\n2. 鸿蒙设备：已开启开发者选项与 USB 调试 (hdc list targets)\n3. Android 设备：已开启 USB 调试 (adb devices)")
        else:
            if len(real_list) >= 2:
                chosen_udid = real_list[1]
                item = dev_map.get(chosen_udid, {})
                plat = item.get("platform", "移动端")
                self.combo_udid2.setEditText(chosen_udid)
                self.append_log(f"✅ [接收端] 成功识别并绑定第 2 台物理真机 [{plat}]: {chosen_udid}")
            elif real_list:
                chosen_udid = real_list[0]
                item = dev_map.get(chosen_udid, {})
                plat = item.get("platform", "移动端")
                self.combo_udid2.setEditText(chosen_udid)
                self.append_log(f"ℹ️ [接收端] 仅检测到 1 台物理真机 [{plat}]，已同步绑定接收端: {chosen_udid}")
            elif all_list:
                target = all_list[1] if len(all_list) > 1 else all_list[0]
                item = dev_map.get(target, {})
                plat = item.get("platform", "移动端")
                self.combo_udid2.setEditText(target)
                self.append_log(f"ℹ️ [接收端] 暂无物理真机，已自动绑定在线设备 [{plat}]: {target}")
            else:
                self.append_log("❌ [接收端] 未检测到任何物理真机或模拟器连接！")
                QMessageBox.warning(self, "未检测到真机", "未检测到任何 USB 硬件真机！\n\n请确认设备已通过数据线连接并开启开发者调试权限。")

    def _swap_devices(self):
        t = self.combo_udid1.currentText()
        self.combo_udid1.setEditText(self.combo_udid2.currentText())
        self.combo_udid2.setEditText(t)
        self._on_config_changed()
        self.append_log(f"🔄 已对调：发送端[{self.combo_udid1.currentText()}] ⇄ 接收端[{self.combo_udid2.currentText()}]")

    def _detect_appium_port(self, combo: QComboBox, default_port: int):
        text = combo.currentText().strip()
        port = default_port
        if ":" in text:
            try:
                part = text.split(":")[1].split(" ")[0].strip()
                port = int(part)
            except Exception:
                port = default_port
        alive, url = DeviceManager.check_appium(port)
        if alive:
            combo.setEditText(f"{url} (服务在线)")
            self.append_log(f"✅ Appium (端口 {port}) 探测成功，服务在线: {url}")
        else:
            self.append_log(f"⚠️ Appium (端口 {port}) 未响应，请确保 Appium 服务已启动。")

    def _trigger_start_appium(self, port: int):
        from web_platform.backend.devices import start_appium_server
        os_text = self.combo_os.currentText().lower()
        os_type = "windows" if "win" in os_text else ("mac" if "mac" in os_text else "linux")
        ok = start_appium_server(os_type=os_type, port=port)
        if ok:
            self.append_log(f"🚀 已向后台发送启动 Appium (端口 {port}) 信号...")
        else:
            self.append_log(f"⚠️ 启动 Appium 失败")

    def _on_click_receipt(self):
        """弹出 1:1 像素级复刻的 Web 回执配置模态表单，并将数据实时同步保存与传参到底层"""
        dlg = WebReceiptDialog(self.web_receipt_fields, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.web_receipt_fields = dlg.get_receipt_fields()
            desktop_config.set("mobile", "web_receipt_fields", self.web_receipt_fields)
            desktop_config.save()

            r_dict = dlg.get_receipt_dict()

            # 联动数据回显至控制台输入框（保持视觉与数据双向一致性）
            dev1 = r_dict.get("设备1", "").strip()
            if dev1 and dev1 != self.combo_udid2.currentText().strip():
                self.combo_udid2.setEditText(dev1)

            priv1 = r_dict.get("私聊用户1", "").strip()
            if priv1 and not self.edit_private_chat.text().strip():
                self.edit_private_chat.setText(priv1)

            grp1 = r_dict.get("群聊名称1", "").strip()
            if grp1 and not self.edit_group_chat.text().strip():
                self.edit_group_chat.setText(grp1)

            self.append_log(f"💾 Web 回执配置已成功保存更新！(已同步 {len(self.web_receipt_fields)} 项表单参数，执行时自动生效)")
            QMessageBox.information(
                self, "保存成功",
                f"💾 验收测试 Web 回执配置已保存更新！\n\n"
                f"• 已同步 {len(self.web_receipt_fields)} 项回执字段；\n"
                f"• 执行测试时将自动注入环境变量 WEB_RECEIPT_DATA 并传参到底层驱动与策略。"
            )

    # ==================== 8. 执行控制与状态联动 ====================
    def run_selected_tests(self):
        curr = self.tree.currentItem()
        if curr:
            data = curr.data(0, Qt.ItemDataRole.UserRole)
            if data:
                self._run_target_node(data["target"], data["name"])
                return
        self._run_target_node(None, "全量测试用例")

    def _run_target_node(self, target_nodeid: Optional[str], display_name: str):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "提示", "已有测试任务正在执行中，请先等待或终止！")
            return

        # 若下半部分终端处于吸底折叠隐藏状态，执行测试时自动向上展开
        if getattr(self, "_is_log_collapsed", False):
            self.toggle_terminal_visibility()

        # 启动新测试用例前，自动清空终端历史日志记录
        self.clear_console()

        ap1 = self.combo_appium1.currentText().split(" ")[0].strip()
        ap2 = self.combo_appium2.currentText().split(" ")[0].strip()

        # 组装回执数据字典并序列化为 JSON 字符串，供底层 DriverFactory 与 ChatStrategy 动态读取
        receipt_dict = {
            item["key"].strip(): item["val"].strip()
            for item in getattr(self, "web_receipt_fields", [])
            if item.get("key", "").strip()
        }
        receipt_json = json.dumps(receipt_dict, ensure_ascii=False) if receipt_dict else ""

        cfg = {
            "nodeid": target_nodeid,
            "remote_appium": ap1,
            "remote_appium2": ap2,
            "remote_udid": self.combo_udid1.currentText().strip(),
            "remote_udid2": self.combo_udid2.currentText().strip(),
            "private_chat_name": self.edit_private_chat.text().strip(),
            "group_chat_name": self.edit_group_chat.text().strip(),
            "debug_mode": self.chk_debug_mode.isChecked(),
            "role": self.combo_view_role.currentData() or "business",
            "env": "dev",
            "web_receipt_data": receipt_json
        }

        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status_pill.setText("🚀 运行中...")
        self.lbl_status_pill.setStyleSheet("background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")
        self.lbl_running_case.setText(f"正在执行: {display_name}")
        self.status_bar.setText(f"🚀 正在运行: {display_name}")

        self.current_target_nodeid = target_nodeid
        if target_nodeid and "[" in target_nodeid and target_nodeid.endswith("]"):
            self.current_run_type = "single_param"
            self.current_parent_func_node = target_nodeid[:target_nodeid.find("[")]
        elif target_nodeid and "::" in target_nodeid:
            self.current_run_type = "run_func"
            self.current_parent_func_node = None
        elif target_nodeid and target_nodeid.endswith(".py"):
            self.current_run_type = "run_file"
            self.current_parent_func_node = None
        else:
            self.current_run_type = "run_all" if not target_nodeid else "run_other"
            self.current_parent_func_node = None

        # 看板展示动态实时运行中状态
        self.allure_dashboard.set_running_state(display_name)

        self.worker = TestExecutionWorker(cfg)
        self.worker.log_signal.connect(self.append_log)
        self.worker.status_signal.connect(self._on_worker_status)
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def stop_current_test(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.append_log("\n🛑 正在向进程树发送强制终止信号...")

    def _on_worker_status(self, status: str, msg: str):
        self.status_bar.setText(f"状态: {msg}")

    @staticmethod
    def _match_single_case_status(
        target: str,
        node_type: str,
        node_name: str,
        cases: List[Dict[str, Any]],
        has_children: bool = False
    ) -> str:
        """
        工业级多维精准对齐算法：
        将测试用例树节点 (target / node_name) 与 Allure 报告中的真实执行用例进行多维特征映射，
        精准提取其独立运行状态 (passed / failed / broken / skipped)，杜绝参数化子用例相互覆盖与污染。
        """
        if not cases:
            return ""

        # 1. 拥有子项的父测试函数节点：其状态由子项在 _update_tree_node_icons 中自底向上精准聚合
        if node_type == "test" and has_children:
            return ""

        # 2. 提取 target 的函数名与核心标识
        raw_target = target.split("[")[0].strip()
        func_name = raw_target.split("::")[-1].strip()
        class_name = ""
        parts = raw_target.split("::")
        if len(parts) >= 2 and parts[-2].startswith("Test"):
            class_name = parts[-2]

        # 3. 候选 cases 过滤：必须归属于同一个测试函数
        candidates = []
        for c in cases:
            fn = c.get("fullName", "")
            c_func = fn.split("#")[-1].split("[")[0].strip()
            if c_func == func_name:
                candidates.append(c)

        if not candidates:
            # 容错降级：按函数名模糊包含过滤
            candidates = [c for c in cases if func_name in c.get("fullName", "") or func_name in c.get("name", "")]

        if not candidates:
            return ""

        # 4. 独立单测函数节点 (无参数化子项)
        if node_type == "test" and not has_children:
            for c in candidates:
                if c.get("name") == node_name:
                    return c.get("status", "")
            if len(candidates) == 1:
                return candidates[0].get("status", "")

        # 5. 参数化子节点精准映射 (node_type == 'param' 或 target 携带参数方括号)
        param_str = ""
        if "[" in target and target.endswith("]"):
            param_str = target[target.find("[") + 1 : -1].strip()
        elif node_type == "param":
            param_str = node_name.strip()

        if param_str:
            # 优先使用 TestCatalogIndex 进行高精度正交特征推断与互斥消解匹配
            try:
                from desktop_app.ui.allure_dashboard import TestCatalogIndex
                for c in candidates:
                    matched_p, _ = TestCatalogIndex.match_case_to_param(func_name, class_name, c)
                    if matched_p and (matched_p == param_str or matched_p == node_name):
                        return c.get("status", "")
            except Exception:
                pass

            # 兜底：特征加权评分匹配
            tokens = [t.strip().lower() for t in re.split(r"[-_,/ \[\]]+", param_str) if t.strip()]
            best_case = None
            best_score = -999.0

            for c in candidates:
                c_name = c.get("name", "").lower()
                c_segments = [s.strip().lower() for s in re.split(r"[|\-_/, \[\]]+", c_name) if s.strip()]
                p_items = [
                    (
                        p.get("name", "").lower(),
                        str(p.get("value", "")).strip("'\"").lower(),
                        str(p.get("value", "")).lower(),
                    )
                    for p in c.get("parameters", [])
                ]
                clean_vals = [item[1] for item in p_items]
                all_p_text = " ".join([item[2] for item in p_items])

                # 互斥特征校验：防止私聊与群聊混淆
                if ("私聊" in param_str or "private" in param_str.lower()) and "群聊" in all_p_text and "私聊" not in all_p_text:
                    continue
                if ("群聊" in param_str or "group" in param_str.lower()) and "私聊" in all_p_text and "群聊" not in all_p_text:
                    continue

                score = 0.0
                for t in tokens:
                    if t in clean_vals:
                        score += 25.0
                    elif t in c_segments:
                        score += 15.0
                    elif t in all_p_text:
                        score += 10.0
                    elif t in c_name:
                        score += 2.0

                if score > best_score:
                    best_score = score
                    best_case = c

            if best_case and best_score > 0:
                best_case["sub_name"] = node_name
                return best_case.get("status", "")

        return ""

    def _sync_cases_to_tree_status(
        self,
        cases: List[Dict[str, Any]],
        scope_checker: Optional[Callable[[str], bool]] = None
    ):
        """
        遍历整棵用例树，将 Allure 报告中的真实执行结果多维精准对齐并同步到树节点的 node_status_map 中：
        支持高精度双向映射缓存，确保 failed / broken / passed / skipped 状态 100% 精准无遗漏同步。
        """
        if not cases:
            return

        # 1. 建立基于 Allure 实际执行结果的 1:1 展示标题与状态映射字典
        title_to_status: Dict[str, str] = {}
        allure_matched_cache: Dict[str, str] = {}
        try:
            from desktop_app.ui.allure_dashboard import TestCatalogIndex
            for c in cases:
                st = c.get("status", "")
                c_title = ""
                if hasattr(self, 'allure_dashboard') and self.allure_dashboard:
                    c_title = self.allure_dashboard._format_case_full_title(c)
                if not c_title:
                    c_title = c.get("name", "")
                raw_n = c.get("name", "")
                if raw_n:
                    title_to_status[raw_n] = st
                    m_b = re.search(r"\[([^\]]+)\](?:\s*$)?", raw_n)
                    if m_b:
                        title_to_status[m_b.group(1).strip()] = st
                if c_title:
                    title_to_status[c_title] = st
                    # 同时保留无优先级前缀版本，保证双向百分百兼容
                    c_clean = re.sub(r"^\[P[0-4]\]\s*", "", c_title).strip()
                    title_to_status[c_clean] = st
                    m_b2 = re.search(r"\[([^\]]+)\](?:\s*$)?", c_clean)
                    if m_b2:
                        title_to_status[m_b2.group(1).strip()] = st

                fn = c.get("fullName", "")
                func_name = ""
                class_name = ""
                if "#" in fn:
                    left, func_name = fn.split("#", 1)
                    class_name = left.split(".")[-1]
                elif "::" in fn:
                    p = fn.split("::")
                    func_name = p[-1]
                    if len(p) >= 2:
                        class_name = p[-2]
                func_name = func_name.split("[")[0].strip()

                matched_p, _ = TestCatalogIndex.match_case_to_param(func_name, class_name, c)
                if matched_p:
                    allure_matched_cache[f"{func_name}::[{matched_p}]"] = st
                    allure_matched_cache[f"{class_name}::{func_name}::[{matched_p}]"] = st
                else:
                    allure_matched_cache[func_name] = st
                    allure_matched_cache[f"{class_name}::{func_name}"] = st
        except Exception:
            pass

        def sync_item(item: QTreeWidgetItem):
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get("type") in ("test", "param"):
                target = data.get("target", "")
                node_type = data.get("type", "")
                node_name = data.get("name", "")
                priority = data.get("priority", "P2")
                has_children = item.childCount() > 0

                if scope_checker is None or scope_checker(target):
                    matched = ""
                    # 规则 1：核心优先依据——每一个测试用例展示的标题是什么，就按一模一样的标题直接同步状态
                    node_title = f"[{priority}] [{node_name}]" if node_type == "param" else f"[{priority}] {node_name}"
                    if node_title in title_to_status:
                        matched = title_to_status[node_title]
                    elif f"[{node_name}]" in title_to_status:
                        matched = title_to_status[f"[{node_name}]"]
                    elif node_name in title_to_status:
                        matched = title_to_status[node_name]

                    # 规则 2：若标题未直接命中，通过函数名与参数标识反向缓存精准对齐
                    if not matched:
                        raw_target = target.split("[")[0].strip()
                        f_name = raw_target.split("::")[-1].strip()
                        c_name = ""
                        parts = raw_target.split("::")
                        if len(parts) >= 2 and parts[-2].startswith("Test"):
                            c_name = parts[-2]

                        if node_type == "param":
                            k1 = f"{f_name}::[{node_name}]"
                            k2 = f"{c_name}::{f_name}::[{node_name}]"
                            matched = allure_matched_cache.get(k2) or allure_matched_cache.get(k1, "")
                        elif node_type == "test" and not has_children:
                            k1 = f_name
                            k2 = f"{c_name}::{f_name}"
                            matched = allure_matched_cache.get(k2) or allure_matched_cache.get(k1, "")

                    # 规则 3：若仍未命中，调用通用匹配算法兜底
                    if not matched:
                        matched = self._match_single_case_status(
                            target, node_type, node_name, cases, has_children=has_children
                        )

                    if matched:
                        self.node_status_map[target] = matched

            for i in range(item.childCount()):
                sync_item(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            sync_item(self.tree.topLevelItem(i))

    def _on_worker_finished(self, exit_code: int, report_dir: str):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)

        # 拦截手动终止情况 (exit_code == -9)，避免将中断用例判定为 failed 或加载空报告
        if exit_code == -9:
            self.lbl_running_case.setText("⏹️ 测试已被手动终止")
            self.status_bar.setText("状态: 就绪 (测试已终止)")
            return

        # 1. 记录当前目标节点
        curr_node = getattr(self, "current_target_nodeid", None)
        self.lbl_running_case.setText(f"执行完毕 (退出码: {exit_code})")

        # 2. 核心：全动态解析本次测试任务的真实报告与原始结果
        results_dir = getattr(self.worker, "allure_results_dir", None)
        target_report = report_dir or getattr(self.worker, "allure_report_dir", None)

        self.allure_dashboard.load_report_from_path(report_dir=target_report, results_dir=results_dir)

        # 3. 工业级多维归一化同步本次测试中实际执行完成的各用例状态
        stat = getattr(self.allure_dashboard, "current_data", {})
        cases = stat.get("cases", [])

        def is_in_scope(node_target: str) -> bool:
            """判断目标节点是否落在本次测试任务的真实执行作用域内"""
            if not curr_node:
                # 全量测试：整棵用例树均在执行作用域内
                return True
            if node_target == curr_node:
                return True
            # 参数化子用例属于函数：curr_node="...::func", node_target="...::func[p]"
            if node_target.startswith(f"{curr_node}["):
                return True
            # 类下的函数属于类：curr_node="...::Class", node_target="...::Class::func"
            if node_target.startswith(f"{curr_node}::"):
                return True
            # 文件下的类与函数属于文件：curr_node="tests/.../test_xxx.py", node_target="tests/.../test_xxx.py::..."
            if node_target.startswith(f"{curr_node}::") or node_target.startswith(f"{curr_node}/"):
                return True
            return False

        run_type = getattr(self, "current_run_type", "")
        parent_func = getattr(self, "current_parent_func_node", None)

        if run_type == "single_param" and curr_node:
            # 规则 1：运行单个测试用例时，运行结果状态只需要修改当前运行的用例是否通过的状态，运行函数按钮颜色就是运行单个测试用例颜色
            single_st = ""
            if cases:
                single_st = self._match_single_case_status(curr_node, "param", "", cases)
            if not single_st:
                single_st = "passed" if exit_code == 0 else "failed"

            self.node_status_map[curr_node] = single_st
            if parent_func:
                self.node_status_map[parent_func] = single_st

            if hasattr(self, 'allure_dashboard') and self.allure_dashboard:
                self.allure_dashboard._render_cases_detail_list()
        else:
            # 规则 2 & 规则 3：运行函数、运行文件或全量运行时，清除单跑锁定，全量对齐报告中的全部用例
            self.current_parent_func_node = None
            if cases:
                self._sync_cases_to_tree_status(cases, scope_checker=None)
                if hasattr(self, 'allure_dashboard') and self.allure_dashboard:
                    self.allure_dashboard._render_cases_detail_list()
            elif curr_node:
                self.node_status_map[curr_node] = "passed" if exit_code == 0 else "failed"

        # 4. 立即刷新树上所有用例的球形与操作按钮状态 (含自底向上精准聚合与按钮颜色联动)
        self._update_tree_node_icons()

        # 实时持久化各用例执行状态与树展开记忆，实现全局记忆模式
        self._save_tree_state()

        # 根据真实执行指标更新状态胶囊
        total = stat.get("total", 0)
        passed = stat.get("passed", 0)
        failed = stat.get("failed", 0)
        broken = stat.get("broken", 0)
        bad_count = failed + broken

        if total > 0:
            if bad_count == 0:
                self.lbl_status_pill.setText(f"🎉 全部通过 ({passed}/{total})")
                self.lbl_status_pill.setStyleSheet("background-color: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")
            else:
                self.lbl_status_pill.setText(f"🔴 测试失败 ({bad_count}/{total} 异常, 退出码:{exit_code})")
                self.lbl_status_pill.setStyleSheet("background-color: #fef2f2; color: #e11d48; border: 1px solid #fecdd3; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")
        else:
            if exit_code == 0:
                self.lbl_status_pill.setText("🎉 测试完成")
                self.lbl_status_pill.setStyleSheet("background-color: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")
            else:
                self.lbl_status_pill.setText(f"🔴 测试失败 (退出码:{exit_code})")
                self.lbl_status_pill.setStyleSheet("background-color: #fef2f2; color: #e11d48; border: 1px solid #fecdd3; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")

        self.status_bar.setText(f"测试完成 (退出码: {exit_code})")
        if report_dir and os.path.exists(report_dir):
            self.last_report_dir = report_dir

        self._refresh_report_pill_count()

    def _update_tree_node_icons(self):
        """
        递归遍历整棵测试树，自底向上全链路聚合并更新各级节点 (目录/文件/类/函数/参数) 的球形状态与操作按钮颜色：
        1. 叶子节点 (单测或具体参数) 保持其独立状态；
        2. 拥有子节点的层级 (函数/类/文件/目录) 自动自底向上聚合所有子节点状态 (Rollup)：
           - 包含任一未通过 (failed / broken / error) -> 聚合为失败 🔴 (按钮显示红色，绝非绿色)；
           - 只有全部子项已执行且全部通过 -> 聚合为通过 🟢 (按钮显示绿色)；
           - 存在未执行用例 -> 聚合为未执行 ⚪ (按钮恢复默认中立状态)。
        3. 特殊规则：运行单个测试用例时，运行函数按钮颜色直接等于运行单个测试用例颜色。
        """
        def visit(item: QTreeWidgetItem) -> str:
            # 1. 递归优先后序遍历所有子节点，收集各子节点状态
            child_statuses = []
            for i in range(item.childCount()):
                c_st = visit(item.child(i))
                if c_st:
                    child_statuses.append(c_st)

            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data:
                return ""

            node_type = data.get("type", "")
            target = data.get("target", "")
            name = data.get("name", "")
            count = data.get("count", 0)
            priority = data.get("priority", "")

            # 2. 计算当前节点状态：若有子节点，由子节点状态精准聚合
            if item.childCount() > 0:
                # 规则 1：若当前是单跑单个测试用例，且当前节点是该用例所属的父函数节点，直接采纳该单用例状态
                locked_parent = getattr(self, "current_parent_func_node", None)
                run_type = getattr(self, "current_run_type", "")
                if run_type == "single_param" and locked_parent and target == locked_parent:
                    curr_status = self.node_status_map.get(target, "")
                elif child_statuses:
                    # 规则 1：只要包含任一失败 -> 聚合为失败 🔴
                    if any(s == "failed" for s in child_statuses):
                        curr_status = "failed"
                    # 规则 2：无失败但包含任一异常中断 -> 聚合为异常 🟠
                    elif any(s in ("broken", "error") for s in child_statuses):
                        curr_status = "broken"
                    # 规则 3：全部子项已执行且全部通过 -> 聚合为通过 🟢
                    elif len(child_statuses) == item.childCount() and all(s == "passed" for s in child_statuses):
                        curr_status = "passed"
                    # 规则 4：全部子项已执行且全部跳过 -> 聚合为跳过 ⚪
                    elif len(child_statuses) == item.childCount() and all(s in ("skipped", "ignored", "canceled") for s in child_statuses):
                        curr_status = "skipped"
                    # 规则 5：包含通过且其余全部为跳过 -> 聚合为通过 🟢
                    elif child_statuses and all(s in ("passed", "skipped", "ignored", "canceled") for s in child_statuses) and any(s == "passed" for s in child_statuses):
                        curr_status = "passed"
                    else:
                        curr_status = ""
                    self.node_status_map[target] = curr_status
                else:
                    curr_status = self.node_status_map.get(target, "")
            else:
                curr_status = self.node_status_map.get(target, "")

            # 3. 统一应用各层级节点文本与提示
            item.setText(0, self._format_node_display_text(curr_status, node_type, name, count, priority=priority))
            if node_type == "category":
                item.setToolTip(0, f"一级测试目录: {target}\n包含 {count} 个测试用例")
            elif node_type == "file":
                status_desc = "通过" if curr_status == "passed" else ("失败" if curr_status == "failed" else ("异常" if curr_status in ("broken", "error") else ("跳过" if curr_status in ("skipped", "ignored", "canceled") else "未执行")))
                item.setToolTip(0, f"二级测试文件: {target}\n名称: {name}\n包含 {count} 个测试用例\n状态: {status_desc}")
            else:
                status_desc = "通过" if curr_status == "passed" else ("失败" if curr_status == "failed" else ("异常" if curr_status in ("broken", "error") else ("跳过" if curr_status in ("skipped", "ignored", "canceled") else "未执行")))
                p_desc_str = f"\n优先级: {self._get_priority_desc(priority)}" if priority else ""
                item.setToolTip(0, f"类型: {node_type}\n名称: {name}\n节点: {target}{p_desc_str}\n状态: {status_desc}")

            # 4. 确保右侧操作按钮保持空心透明胶囊风格，悬浮统一为绿色
            self._update_node_action_button(item, curr_status)

            return curr_status

        for i in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(i))

    def _restore_last_run_state(self):
        """
        启动时自愈与状态恢复：
        1. 载入本地最新的 Allure 测试报告与指标；
        2. 若 Allure 报告中存在 cases，全树自底向上进行多维精准对齐并纠偏 node_status_map；
        3. 刷新全树节点球形状态；
        4. 同步更新状态胶囊药丸 (🎉 全部通过 / 🔴 测试失败)。
        """
        try:
            if hasattr(self, 'allure_dashboard') and self.allure_dashboard:
                self.allure_dashboard.load_latest_report()
                stat = getattr(self.allure_dashboard, "current_data", {})
                cases = stat.get("cases", [])
                total = stat.get("total", 0)
                passed = stat.get("passed", 0)
                failed = stat.get("failed", 0)
                broken = stat.get("broken", 0)
                bad_count = failed + broken

                # 启动时根据本地最新 Allure 报告对全树进行精准自愈与同步
                if cases:
                    self._sync_cases_to_tree_status(cases, scope_checker=None)
                    if hasattr(self, 'allure_dashboard') and self.allure_dashboard:
                        self.allure_dashboard._render_cases_detail_list()

                if total > 0:
                    if bad_count == 0:
                        self.lbl_status_pill.setText(f"🎉 全部通过 ({passed}/{total})")
                        self.lbl_status_pill.setStyleSheet("background-color: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")
                    else:
                        self.lbl_status_pill.setText(f"🔴 测试失败 ({bad_count}/{total} 异常)")
                        self.lbl_status_pill.setStyleSheet("background-color: #fef2f2; color: #e11d48; border: 1px solid #fecdd3; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")

            # 刷新整棵树的状态球显示 (使上次跑通过的变绿球 🟢，失败的变红球 🔴)
            self._update_tree_node_icons()
        except Exception:
            pass

    def open_allure_report(self):
        self.allure_dashboard.load_latest_report()
        stat = getattr(self.allure_dashboard, "current_data", {})
        task_id = stat.get("task_id", "就绪")
        cases = stat.get("cases", [])
        total = stat.get("total", 0)
        passed = stat.get("passed", 0)
        failed = stat.get("failed", 0)
        broken = stat.get("broken", 0)
        bad_count = failed + broken

        if cases:
            self._sync_cases_to_tree_status(cases, scope_checker=None)
            self._update_tree_node_icons()
            self._save_tree_state()
            if hasattr(self, 'allure_dashboard') and self.allure_dashboard:
                self.allure_dashboard._render_cases_detail_list()

        if total > 0:
            if bad_count == 0:
                self.lbl_status_pill.setText(f"🎉 全部通过 ({passed}/{total})")
                self.lbl_status_pill.setStyleSheet("background-color: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")
            else:
                self.lbl_status_pill.setText(f"🔴 测试失败 ({bad_count}/{total} 异常)")
                self.lbl_status_pill.setStyleSheet("background-color: #fef2f2; color: #e11d48; border: 1px solid #fecdd3; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")

        self.append_log(f"📊 已动态同步最新 Allure 测试报告: {task_id} (执行用例: {total} 条)")
        self._refresh_report_pill_count()

    def append_log(self, text: str):
        cleaned = clean_ansi_log(text)
        self.console.appendPlainText(cleaned)
        if getattr(self, "_auto_scroll", True):
            self._scroll_to_bottom()
        # 若当前搜索框有内容，延迟重新搜一次以更新计数
        if hasattr(self, "edit_log_search") and self.edit_log_search.text().strip():
            if not getattr(self, "_search_timer_pending", False):
                self._search_timer_pending = True
                QTimer.singleShot(300, self._re_evaluate_log_search)

    def _re_evaluate_log_search(self):
        self._search_timer_pending = False
        if hasattr(self, "edit_log_search"):
            txt = self.edit_log_search.text().strip()
            if txt:
                self._on_log_search_changed(txt)

    def clear_console(self):
        self.console.clear()
        self._log_search_matches = []
        self._log_search_index = -1
        if hasattr(self, "lbl_log_search_count"):
            self.lbl_log_search_count.setText("0/0")
        if hasattr(self, "console"):
            self.console.setExtraSelections([])

    def _on_log_search_changed(self, text: str):
        """搜索日志内容变化响应槽"""
        text = text.strip()
        self._log_search_matches = []
        self._log_search_index = -1

        if not text:
            if hasattr(self, "lbl_log_search_count"):
                self.lbl_log_search_count.setText("0/0")
            if hasattr(self, "console"):
                self.console.setExtraSelections([])
            return

        doc = self.console.document()
        cursor = QTextCursor(doc)
        matches = []
        while True:
            cursor = doc.find(text, cursor)
            if cursor.isNull():
                break
            matches.append(QTextCursor(cursor))

        self._log_search_matches = matches
        if matches:
            self._log_search_index = 0
            self._apply_log_search_selection()
        else:
            if hasattr(self, "lbl_log_search_count"):
                self.lbl_log_search_count.setText("0/0")
            if hasattr(self, "console"):
                self.console.setExtraSelections([])

    def _apply_log_search_selection(self):
        """高亮并定位当前搜索项到日志视窗"""
        total = len(self._log_search_matches)
        if total == 0 or self._log_search_index < 0:
            if hasattr(self, "lbl_log_search_count"):
                self.lbl_log_search_count.setText("0/0")
            if hasattr(self, "console"):
                self.console.setExtraSelections([])
            return

        idx = self._log_search_index
        if hasattr(self, "lbl_log_search_count"):
            self.lbl_log_search_count.setText(f"{idx + 1}/{total}")

        # 所有匹配项浅色高亮
        fmt_all = QTextCharFormat()
        fmt_all.setBackground(QColor("#fef08a"))
        fmt_all.setForeground(QColor("#0f172a"))

        # 当前匹配项亮橙色醒目高亮
        fmt_curr = QTextCharFormat()
        fmt_curr.setBackground(QColor("#f59e0b"))
        fmt_curr.setForeground(QColor("#ffffff"))
        fmt_curr.setFontWeight(QFont.Weight.Bold)

        selections = []
        for i, cur in enumerate(self._log_search_matches):
            sel = QTextEdit.ExtraSelection()
            sel.cursor = cur
            sel.format = fmt_curr if i == idx else fmt_all
            selections.append(sel)

        self.console.setExtraSelections(selections)

        curr_cursor = self._log_search_matches[idx]
        self.console.setTextCursor(curr_cursor)
        self.console.ensureCursorVisible()

    def _search_log_next(self):
        """定位下一个匹配项"""
        if not getattr(self, "_log_search_matches", None):
            txt = self.edit_log_search.text().strip() if hasattr(self, "edit_log_search") else ""
            if txt:
                self._on_log_search_changed(txt)
            return
        self._log_search_index = (self._log_search_index + 1) % len(self._log_search_matches)
        self._apply_log_search_selection()

    def _search_log_prev(self):
        """定位上一个匹配项"""
        if not getattr(self, "_log_search_matches", None):
            txt = self.edit_log_search.text().strip() if hasattr(self, "edit_log_search") else ""
            if txt:
                self._on_log_search_changed(txt)
            return
        self._log_search_index = (self._log_search_index - 1 + len(self._log_search_matches)) % len(self._log_search_matches)
        self._apply_log_search_selection()

    def _copy_logs(self):
        text = self.console.toPlainText()
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            self.append_log("📋 已复制终端日志到剪贴板")

    # ==================== 7. Appium 服务集群控制与设备状态深度检测 ====================
    def _probe_appium_port(self, port: int) -> Tuple[bool, str]:
        """快速探测指定端口的 Appium 服务是否在监听并存活"""
        # 1. 尝试通过 Socket 快速探测端口是否处于监听状态 (毫秒级即时探测)
        is_listening = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    is_listening = True
        except Exception:
            pass

        if not is_listening:
            return False, "🔴 离线 (端口未开放)"

        # 2. 进一步通过 HTTP 探测 Appium status 状态
        try:
            alive, url = DeviceManager.check_appium(port)
            if alive:
                return True, f"🟢 在线 ({url})"
        except Exception:
            pass

        return True, "🟢 端口已监听 (服务就绪)"

    def _start_appium_service(self):
        """启动 Appium 服务集群 (支持 Windows / macOS 跨平台原生后台纯静默拉起，确保日志 100% 写入 logs/appium_*.log)"""
        self.append_log("==================================================")
        self.append_log("▶ [启动服务] 正在准备拉起 Appium 集群服务 (跨平台原生模式)...")

        # 严格优先从安装包文件夹目录 (应用主程序目录) 与工程根目录获取
        app_dir = Path(sys.executable).parent
        project_root = Path(SmartPathResolver.get_project_root())
        logs_dir = project_root / "logs"
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        # 方案 1: 优先直接检测系统环境中的 appium 命令进行原生静默直启 (跨 Win/Mac 自动感知)
        appium_bin = shutil.which("appium.cmd") or shutil.which("appium")
        if not appium_bin and sys.platform == "darwin":
            mac_candidates = [
                "/opt/homebrew/bin/appium",
                "/usr/local/bin/appium",
                os.path.expanduser("~/.nvm/versions/node/current/bin/appium"),
            ]
            for c in mac_candidates:
                if os.path.isfile(c) and os.access(c, os.X_OK):
                    appium_bin = c
                    break

        if appium_bin:
            mode_str = f"原生直启模式 ({'Windows 静默' if sys.platform == 'win32' else 'macOS 后台守护'})"
            self.append_log(f"  • 执行命令: {appium_bin}")
            self.append_log(f"  • 运行模式: {mode_str}")
            self.append_log("  • 目标端口: 4723 (主设备), 4724 (从设备)")
            self.append_log(f"  • 日志目录: {logs_dir.resolve()}")

            try:
                for port in [4723, 4724]:
                    log_file = logs_dir / f"appium_{port}.log"
                    if sys.platform == "win32":
                        cmd = f'"{appium_bin}" -p {port} -a 0.0.0.0 --log "{log_file}"'
                        subprocess.Popen(
                            cmd,
                            cwd=str(project_root),
                            shell=True,
                            creationflags=create_no_window
                        )
                    else:
                        # macOS / Linux 下采用独立会话守护进程启动，输出重定向至日志文件
                        cmd_args = [appium_bin, "-p", str(port), "-a", "0.0.0.0", "--log", str(log_file)]
                        subprocess.Popen(
                            cmd_args,
                            cwd=str(project_root),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                    self.append_log(f"  • 端口 {port}: 已启动后台服务 -> {log_file.name}")

                self.append_log("✅ [启动成功] Appium 服务集群已成功拉起，运行日志已生成！")
                self.append_log("==================================================")
                QMessageBox.information(
                    self, "启动成功",
                    f"✅ Appium 服务集群已成功启动！\n\n"
                    f"• 运行模式: {mode_str}\n"
                    f"• 监听端口: 4723 (主设备), 4724 (从设备)\n"
                    f"• 运行日志:\n  • {logs_dir / 'appium_4723.log'}\n  • {logs_dir / 'appium_4724.log'}\n\n"
                    f"💡 提示: 服务初始化通常需 2~3 秒，随后可点击【🔍 检测服务】验证服务端口连通性。"
                )
                return
            except Exception as e:
                self.append_log(f"⚠️ 原生启动出现异常 ({e})，正在回退尝试外部脚本启动...")

        # 方案 2: 回退模式，通过外部脚本拉起 (兼容 Windows批处理 与 macOS shell)
        candidates = [
            app_dir / "start_appium_batch.bat",
            project_root / "start_appium_batch.bat",
            Path.cwd() / "start_appium_batch.bat",
            app_dir / "start_appium_batch.sh",
            project_root / "start_appium_batch.sh",
            Path.cwd() / "start_appium_batch.sh",
            app_dir / "start_appium_silent.vbs",
            project_root / "start_appium_silent.vbs",
            Path.cwd() / "start_appium_silent.vbs"
        ]
        launch_file: Optional[Path] = None
        for p in candidates:
            if p.is_file():
                launch_file = p
                break

        if not launch_file:
            err_msg = "未找到 Appium 运行环境及启动脚本！"
            self.append_log(f"❌ [启动失败] {err_msg}")
            self.append_log("==================================================")
            hint = "请在 Mac 终端执行 npm i -g appium 安装，或配置 PATH 环境变量。" if sys.platform == "darwin" else "请确认系统已安装 Node.js 与 Appium (npm i -g appium)。"
            QMessageBox.warning(
                self, "启动失败",
                f"未找到 Appium 运行环境！\n\n{hint}"
            )
            return

        mode_str = "脚本托管模式"
        self.append_log(f"  • 启动脚本: {launch_file.name} ({launch_file.resolve()})")
        self.append_log(f"  • 运行模式: {mode_str}")
        self.append_log("  • 目标端口: 4723 (主设备), 4724 (从设备)")
        self.append_log(f"  • 运行日志: {logs_dir / 'appium_4723.log'}, {logs_dir / 'appium_4724.log'}")

        try:
            work_dir = str(launch_file.parent)
            if sys.platform == "win32":
                if launch_file.suffix.lower() == ".vbs":
                    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
                    wscript_bin = shutil.which("wscript") or os.path.join(sys_root, "System32", "wscript.exe")
                    subprocess.Popen([wscript_bin, str(launch_file)], cwd=work_dir)
                else:
                    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
                    cmd_bin = shutil.which("cmd") or os.path.join(sys_root, "System32", "cmd.exe")
                    subprocess.Popen([cmd_bin, "/c", str(launch_file)], cwd=work_dir, creationflags=create_no_window)
            else:
                subprocess.Popen(["bash", str(launch_file)], cwd=work_dir, start_new_session=True)

            self.append_log(f"✅ [启动成功] Appium 服务集群已成功派发至系统后台启动！")
            self.append_log("==================================================")
            QMessageBox.information(
                self, "启动成功",
                f"✅ Appium 服务集群已成功启动！\n\n"
                f"• 脚本文件: {launch_file.name}\n"
                f"• 运行模式: {mode_str}\n"
                f"• 目标端口: 4723 (主设备), 4724 (从设备)\n"
                f"• 运行日志: logs/appium_*.log\n\n"
                f"💡 提示: 服务初始化通常需 2~3 秒，随后可点击【🔍 检测服务】验证服务端口连通性。"
            )
        except Exception as e:
            self.append_log(f"❌ [启动失败] 启动 Appium 服务脚本异常: {e}")
            self.append_log("==================================================")
            QMessageBox.critical(self, "启动失败", f"启动 Appium 服务脚本时出现异常:\n\n{e}")

    def _stop_appium_service(self):
        """关闭 Appium 批量服务 (跨 Windows / macOS 双端支持，精准释放 4723~4731 端口并清理后台服务)"""
        self.append_log("==================================================")
        self.append_log("⏹ [关闭服务] 正在扫描并终止 Appium 服务进程 (端口 4723~4731)...")
        killed_pids: Set[str] = set()
        ports_closed: List[int] = []

        if sys.platform == "win32":
            try:
                # Windows 平台：通过 netstat 精确定位监听状态的 PID 并强制终止
                for port in range(4723, 4732):
                    cmd = f"netstat -ano | findstr :{port}"
                    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if proc.stdout:
                        for line in proc.stdout.strip().splitlines():
                            parts = line.split()
                            if len(parts) >= 5 and "LISTENING" in parts:
                                pid = parts[-1]
                                if pid.isdigit() and int(pid) > 0 and pid not in killed_pids:
                                    killed_pids.add(pid)
                                    ports_closed.append(port)
                                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
                                    self.append_log(f"  - 已终止 Windows 进程 PID: {pid} (占用端口: {port})")
            except Exception as e:
                self.append_log(f"❌ [关闭失败] 释放 Appium 端口进程出现异常: {e}")
                self.append_log("==================================================")
                QMessageBox.critical(self, "关闭失败", f"关闭 Appium 服务进程时发生异常:\n\n{e}")
                return
        else:
            # macOS / Linux 平台：通过 lsof -ti :<port> 扫描并杀掉占用端口的进程
            try:
                for port in range(4723, 4732):
                    cmd = ["lsof", "-ti", f":{port}"]
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    if proc.stdout:
                        for pid_str in proc.stdout.strip().splitlines():
                            pid = pid_str.strip()
                            if pid.isdigit() and int(pid) > 0 and pid not in killed_pids:
                                killed_pids.add(pid)
                                ports_closed.append(port)
                                subprocess.run(["kill", "-9", pid], capture_output=True)
                                self.append_log(f"  - 已终止 macOS 进程 PID: {pid} (占用端口: {port})")
                # 兜底清理残留的 appium node 孤儿进程
                subprocess.run(["pkill", "-f", "appium"], capture_output=True)
            except Exception as e:
                self.append_log(f"❌ [关闭失败] 释放 Appium 端口进程出现异常: {e}")
                self.append_log("==================================================")
                QMessageBox.critical(self, "关闭失败", f"关闭 Appium 服务进程时发生异常:\n\n{e}")
                return

        if killed_pids:
            ports_str = ", ".join(map(str, sorted(set(ports_closed))))
            pids_str = ", ".join(sorted(killed_pids))
            self.append_log(f"✅ [关闭成功] 已成功终止 {len(killed_pids)} 个后台服务进程 (PID: {pids_str})，释放端口: {ports_str}")
            self.append_log("==================================================")
            QMessageBox.information(
                self, "关闭成功",
                f"✅ Appium 服务已成功关闭并释放资源！\n\n"
                f"• 终止服务进程: {len(killed_pids)} 个 (PID: {pids_str})\n"
                f"• 释放监听端口: {ports_str}"
            )
        else:
            self.append_log("ℹ [关闭完成] 4723~4731 端口均处于空闲状态，未检测到活跃的 Appium 服务进程。")
            self.append_log("==================================================")
            QMessageBox.information(
                self, "服务已是关闭状态",
                "✅ 4723~4731 端口当前均处于空闲状态！\n\n未检测到正在运行的 Appium 服务进程，无需重复关闭。"
            )

    def _check_appium_and_devices(self):
        """
        检测服务与设备连接状态 (跨平台 + 多端 Android / HarmonyOS / iOS 统一体检)：
        1. 探测 Appium 服务监听状态 (4723 与 4724 端口)
        2. 全面扫描移动设备连接 (Android ADB / 鸿蒙 HDC / iOS tidevice 与原生调试通道)
        3. 刷新顶部药丸计数并输出多端设备分布报告
        """
        self.append_log("==================================================")
        self.append_log("🔍 [检测服务] 开始进行 Appium 集群与多端设备综合体检 (iOS / 鸿蒙 / Android)...")

        # ---------------- 步骤 1: 探测 Appium 端口状态 ----------------
        self.append_log("  [1/2] 正在探测 Appium 核心服务端口...")
        appium_status: Dict[int, Tuple[bool, str]] = {}
        for port in [4723, 4724]:
            ok, desc = self._probe_appium_port(port)
            appium_status[port] = (ok, desc)
            self.append_log(f"    • 端口 {port}: {desc}")

        appium_all_alive = all(ok for ok, _ in appium_status.values())
        appium_any_alive = any(ok for ok, _ in appium_status.values())

        # ---------------- 步骤 2: 深度探测多端移动设备 ----------------
        self.append_log("  [2/2] 正在深度检测移动硬件设备 (Android + 鸿蒙 + iOS)...")
        QApplication.processEvents()

        details = DeviceManager.scan_connected_devices()
        device_items = details.get("device_items", [])
        real_devices = details.get("real_devices", [])
        all_devices = details.get("all_devices", [])

        # 分类汇总设备
        ios_devs = [item for item in device_items if item.get("platform") == "iOS"]
        harmony_devs = [item for item in device_items if item.get("platform") == "HarmonyOS"]
        android_devs = [item for item in device_items if item.get("platform") == "Android"]

        # 同步更新下拉选项
        for udid in all_devices:
            if self.combo_udid1.findText(udid) == -1:
                self.combo_udid1.addItem(udid)
            if self.combo_udid2.findText(udid) == -1:
                self.combo_udid2.addItem(udid)

        # 自动同步发送端和接收端
        if real_devices:
            self.combo_udid1.setEditText(real_devices[0])
            if len(real_devices) > 1:
                self.combo_udid2.setEditText(real_devices[1])
        elif all_devices:
            self.combo_udid1.setEditText(all_devices[0])
            if len(all_devices) > 1:
                self.combo_udid2.setEditText(all_devices[1])

        # 更新顶部状态药丸
        total_count = len(all_devices)
        if hasattr(self, 'top_status_pill'):
            self.top_status_pill.update_device_count(total_count)
        elif hasattr(self, 'lbl_device_pill'):
            self.lbl_device_pill.setText(f"🟢 设备: {total_count} 台在线" if total_count else "⚪ 设备: 0 台在线")

        # 格式化详细日志输出
        self.append_log(f"    - 检测到移动设备总数: {total_count} 台 (真机: {len(real_devices)} 台)")
        if ios_devs:
            self.append_log(f"      🍎 iOS 设备 ({len(ios_devs)} 台):")
            for dev in ios_devs:
                self.append_log(f"        • {dev['udid']} ({dev['desc']})")
        if harmony_devs:
            self.append_log(f"      🔴 鸿蒙 HarmonyOS 设备 ({len(harmony_devs)} 台):")
            for dev in harmony_devs:
                self.append_log(f"        • {dev['udid']} ({dev['desc']})")
        if android_devs:
            self.append_log(f"      🤖 Android 设备 ({len(android_devs)} 台):")
            for dev in android_devs:
                self.append_log(f"        • {dev['udid']} ({dev['desc']})")

        QApplication.processEvents()

        # ---------------- 步骤 3: 综合评估与弹窗报告 ----------------
        appium_report_lines = [f"• 端口 {p}: {desc}" for p, (_, desc) in appium_status.items()]
        appium_report_str = "\n".join(appium_report_lines)

        dev_report_lines = []
        if ios_devs:
            dev_report_lines.append(f"【🍎 iOS 设备 ({len(ios_devs)} 台)】\n" + "\n".join(f"• {d['udid']} ({d['desc']})" for d in ios_devs))
        if harmony_devs:
            dev_report_lines.append(f"【🔴 鸿蒙设备 ({len(harmony_devs)} 台)】\n" + "\n".join(f"• {d['udid']} ({d['desc']})" for d in harmony_devs))
        if android_devs:
            dev_report_lines.append(f"【🤖 Android 设备 ({len(android_devs)} 台)】\n" + "\n".join(f"• {d['udid']} ({d['desc']})" for d in android_devs))

        dev_report_str = "\n\n".join(dev_report_lines) if dev_report_lines else "• 暂无任何设备连接"

        if appium_any_alive and all_devices:
            self.append_log("✅ [检测成功] Appium 服务与移动设备全部就绪，随时可启动自动化测试！")
            self.append_log("==================================================")
            QMessageBox.information(
                self, "检测成功",
                f"✅ 服务与多端设备检测全部正常！\n\n"
                f"【Appium 服务状态】\n{appium_report_str}\n\n"
                f"{dev_report_str}"
            )
        elif not appium_any_alive and all_devices:
            self.append_log("⚠️ [检测提示] 移动设备已就绪，但 Appium 服务未启动。")
            self.append_log("==================================================")
            QMessageBox.warning(
                self, "服务未启动",
                f"⚠️ 移动设备已就绪，但 Appium 服务未启动 (4723/4724 离线)！\n\n"
                f"【Appium 服务状态】\n{appium_report_str}\n\n"
                f"{dev_report_str}\n\n"
                f"💡 建议: 请点击左侧【▶ 启动服务】按钮启动 Appium 集群。"
            )
        elif appium_any_alive and not all_devices:
            self.append_log("⚠️ [检测提示] Appium 服务已就绪，但未检测到连接的移动设备。")
            self.append_log("==================================================")
            QMessageBox.warning(
                self, "未检测到移动设备",
                f"⚠️ Appium 服务正常，但当前没有检测到已连接的移动设备！\n\n"
                f"【Appium 服务状态】\n{appium_report_str}\n\n"
                f"💡 建议: 请确认设备数据线已连接，并开启对应权限 (Android开启USB调试、鸿蒙开启开发者模式、iOS信任此电脑)。"
            )
        else:
            self.append_log("❌ [检测失败] Appium 服务与移动设备均未就绪。")
            self.append_log("==================================================")
            QMessageBox.critical(
                self, "服务与设备均未就绪",
                f"❌ Appium 服务离线，且未检测到移动设备！\n\n"
                f"【Appium 服务状态】\n{appium_report_str}\n\n"
                f"💡 建议: 请先连接真机并点击【▶ 启动服务】启动 Appium 集群。"
            )


