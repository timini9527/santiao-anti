# -*- coding: utf-8 -*-
"""
移动端全平台原生 UI 审查器主窗口 (HarmonyAppiumInspector)：
整合左栏真机视窗、中栏 DOM 树（含 Ctrl+F 实时搜索）、右栏属性面板（原地单元格复用 + 按需长行测高）
以及独立查找器浮窗、三端设备切换、实时投屏与 iOS WDA 服务管理。
"""
import logging
import os
import re
import sys
import threading
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import QEvent, QSize, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QImage, QKeyEvent, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop_app.core.path_resolver import SmartPathResolver
from desktop_app.core.paths import REPORTS_DIR
from desktop_app.ui.inspector.common.dialogs import ModernMessageBox, ToastNotification
from desktop_app.ui.inspector.common.icons import (
    create_modern_app_icon,
    get_dom_tag_color,
    get_tech_icon,
)
from desktop_app.ui.inspector.common.widgets import ButtonSpinner, DeviceComboBox, FlowLayout
from desktop_app.ui.inspector.layout.dom_tree_builder import (
    apply_occluded_visibility_to_tree as _apply_occluded_visibility_to_tree,
    build_dom_tree_into_inspector,
    find_active_dialogs,
    format_dom_node_label,
)
from desktop_app.ui.inspector.layout.parser import get_layout_physical_size, parse_layout_file
from desktop_app.ui.inspector.platforms.ios import crop_ios_dvt_image, normalize_ios_screenshot_file
from desktop_app.ui.inspector.platforms.ios_service import (
    IosServiceActionWorker,
    IosWdaManager,
    check_ios_wda_services,
)
from desktop_app.ui.inspector.platforms.registry import DeviceController, DeviceScanWorker
from desktop_app.ui.inspector.views.dom_tree_view import DOMTreeWidget
from desktop_app.ui.inspector.views.screen_canvas import AppiumScreenView, InspectorMode
from desktop_app.ui.inspector.views.search_dialog import SearchElementDialog
from desktop_app.ui.inspector.workers.capture_worker import CaptureWorker
from desktop_app.ui.inspector.workers.screencast_worker import ScreenCastWorker

logger = logging.getLogger("Inspector")


class HarmonyAppiumInspector(QMainWindow):
    """三端一体化桌面 UI 审查器 (HarmonyOS / Android / iOS)"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Santiao Mobile Inspector - 移动端全平台 UI 审查器 (HarmonyOS / Android / iOS)")
        self.setWindowIcon(create_modern_app_icon())
        self.resize(1560, 960)
        self.setMinimumSize(950, 650)

        self.current_udid: str = ""
        self.current_platform: str = "harmony"
        self.flat_components: List[Dict[str, Any]] = []
        self.comp_map: Dict[str, Dict[str, Any]] = {}
        self.tree_item_map: Dict[str, QTreeWidgetItem] = {}
        self.xml_root: Optional[ET.Element] = None
        self.node_counter: int = 0
        self.search_dialog: Optional[SearchElementDialog] = None

        # DOM 树内置搜索高亮状态
        self.dom_search_matches: List[QTreeWidgetItem] = []
        self.dom_search_index: int = -1
        self.dom_search_original_styles: List[Tuple[QTreeWidgetItem, QColor, QBrush]] = []

        # 后台线程与投屏状态
        self.capture_worker: Optional[CaptureWorker] = None
        self.scan_worker: Optional[DeviceScanWorker] = None
        self.screencast_worker: Optional[ScreenCastWorker] = None
        self.is_screencasting: bool = False
        self.current_screenshot_path: str = ""
        self._worker_start_time: float = 0.0
        self._last_disk_cache_t: float = 0.0
        self._ios_service_running_action: bool = False
        self._ios_service_state: str = "stopped"

        # 右侧属性表与选中状态缓存（消除切节点重复刷新与全表换行测高风暴）
        self._last_panel_sig: Optional[Tuple[str, int, str]] = None
        self._last_breadcrumb_style: str = ""
        self._attr_long_rows: List[int] = []
        self._attr_key_bold_font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        self._attr_key_norm_font = QFont("Segoe UI", 9)
        self._attr_key_hl_color = QColor("#0284c7")
        self._attr_val_hl_color = QColor("#d97706")
        self._attr_key_norm_color = QColor("#64748b")
        self._attr_val_norm_color = QColor("#0f172a")

        self.toast = ToastNotification(self)

        # 独立超时守卫定时器
        self._timer_screencast = QTimer(self)
        self._timer_screencast.setSingleShot(True)
        self._timer_screencast.timeout.connect(self._on_screencast_timeout)

        self._timer_sync_screen = QTimer(self)
        self._timer_sync_screen.setSingleShot(True)
        self._timer_sync_screen.timeout.connect(self._on_sync_screen_timeout)

        self._timer_refresh = QTimer(self)
        self._timer_refresh.setSingleShot(True)
        self._timer_refresh.timeout.connect(self._on_refresh_timeout)

        # iOS WDA 服务状态定时巡检
        self.timer_ios_service = QTimer(self)
        self.timer_ios_service.setInterval(2500)
        self.timer_ios_service.timeout.connect(self._on_ios_service_timer_tick)
        self.timer_ios_service.start()

        self.apply_white_luxury_theme()
        self.init_ui()

        self.shortcut_dom_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_dom_search.activated.connect(self.toggle_dom_search)

        self.load_device_list(auto_capture=True)

    def apply_white_luxury_theme(self) -> None:
        self.setStyleSheet("""
            QMainWindow { background-color: #f8fafc; }
            QWidget {
                color: #0f172a;
                font-family: 'Segoe UI', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
                font-size: 12px;
            }
            QToolTip {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 0px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QFrame#topBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                min-height: 46px;
            }
            QLabel#topBrand { font-weight: 800; color: #0f172a; font-size: 14px; margin-right: 4px; }
            QLabel#platformBadge {
                background-color: #e0f2fe; color: #0284c7; font-weight: 700;
                font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bae6fd;
            }
            QComboBox {
                combobox-popup: 0;
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 1px 24px 1px 8px;
                font-weight: 500; font-size: 12px; min-height: 26px; max-height: 30px;
            }
            QComboBox:hover { border-color: #0284c7; }
            QComboBox:focus { border: 1px solid #0284c7; }
            QComboBox::drop-down {
                subcontrol-origin: padding; subcontrol-position: top right; width: 24px; border-left: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                selection-background-color: #e0f2fe; selection-color: #0284c7; padding: 4px; outline: none;
            }
            QPushButton.mode-btn {
                background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 8px; font-weight: 600; font-size: 12.5px;
                min-height: 30px; max-height: 30px; text-align: center;
            }
            QPushButton.mode-btn:hover { background-color: #f1f5f9; border-color: #0284c7; color: #0284c7; }
            QPushButton.mode-btn:checked {
                background-color: #0284c7; color: #ffffff; border: 1px solid #0284c7; font-weight: 700;
            }
            QPushButton.action-btn {
                background-color: #ffffff; color: #334155; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 8px; font-weight: 600; font-size: 12.5px;
                min-height: 30px; max-height: 30px; text-align: center;
            }
            QPushButton.action-btn:hover { background-color: #f8fafc; border-color: #0284c7; color: #0284c7; }
            QPushButton.action-btn:pressed { background-color: #f1f5f9; }
            QPushButton.sub-action-btn {
                background-color: #ffffff; color: #334155; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 8px; font-weight: 600; font-size: 11.5px;
                min-height: 28px; max-height: 28px; text-align: center;
            }
            QPushButton.sub-action-btn:hover { background-color: #f1f5f9; border-color: #0284c7; color: #0284c7; }
            QPushButton.sub-action-btn:pressed { background-color: #e2e8f0; }
            QPushButton.sub-action-btn:disabled {
                background-color: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0;
            }
            QSplitter::handle:horizontal { background-color: #e2e8f0; width: 3px; margin: 0px; border-radius: 1px; }
            QSplitter::handle:horizontal:hover { background-color: #0284c7; }
            QFrame.panel-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }
            QTreeWidget {
                background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 4px; color: #0f172a; font-family: 'JetBrains Mono', Consolas, monospace; font-size: 12px;
            }
            QTreeWidget::item { min-height: 22px; padding: 1px 4px; border-radius: 4px; margin-bottom: 1px; }
            QTreeWidget::item:hover { background-color: #f1f5f9; border: 1px solid #cbd5e1; }
            QTreeWidget::item:selected, QTreeWidget::item:selected:active, QTreeWidget::item:selected:!active {
                background-color: rgba(2, 132, 199, 0.08); border: 1px dashed #38bdf8;
            }
            QScrollBar:horizontal { background: transparent; height: 4px; margin: 0px; border: none; }
            QScrollBar::handle:horizontal { background: #cbd5e1; min-width: 20px; border-radius: 2px; }
            QScrollBar::handle:horizontal:hover { background: #94a3b8; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none; width: 0px; height: 0px; border: none;
            }
            QScrollBar:vertical { background: transparent; width: 4px; margin: 0px; border: none; }
            QScrollBar::handle:vertical { background: #cbd5e1; min-height: 20px; border-radius: 2px; }
            QScrollBar::handle:vertical:hover { background: #94a3b8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none; width: 0px; height: 0px; border: none;
            }
            QTableWidget {
                background-color: #ffffff; border: 1px solid #e2e8f0;
                border-radius: 6px; gridline-color: #f1f5f9; color: #0f172a; font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f8fafc; color: #475569; border: none;
                border-bottom: 1px solid #e2e8f0; padding: 6px 10px; font-weight: 700; font-size: 11px;
            }
            QLineEdit {
                background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px;
                padding: 2px 10px; color: #0f172a; font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 12px; selection-background-color: #0284c7; selection-color: #ffffff;
            }
            QLineEdit:focus { border: 1px solid #0284c7; }
            QLabel#breadcrumb {
                background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 6px 12px; color: #0284c7;
                font-family: 'JetBrains Mono', Consolas, monospace; font-size: 11px; line-height: 1.4;
            }
        """)

    def init_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 顶部操作栏
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        top_layout = FlowLayout(top_bar, margin=0, h_spacing=6, v_spacing=6)
        top_layout.setContentsMargins(12, 9, 12, 11)

        brand_widget = QWidget()
        brand_widget.setMinimumHeight(32)
        brand_widget.setStyleSheet("background: transparent;")
        brand_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(0, 1, 2, 1)
        brand_layout.setSpacing(6)

        lbl_logo = QLabel()
        lbl_logo.setPixmap(create_modern_app_icon().pixmap(22, 22))
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_layout.addWidget(lbl_logo)

        lbl_brand = QLabel("三条 UI 审查器")
        lbl_brand.setObjectName("topBrand")
        lbl_brand.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_layout.addWidget(lbl_brand)

        self.lbl_platform_badge = QLabel("HarmonyOS")
        self.lbl_platform_badge.setObjectName("platformBadge")
        self.lbl_platform_badge.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_layout.addWidget(self.lbl_platform_badge)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(brand_widget)

        dev_group = QWidget()
        dev_group.setMinimumHeight(32)
        dev_group.setStyleSheet("background: transparent;")
        dev_group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        dev_layout = QHBoxLayout(dev_group)
        dev_layout.setContentsMargins(0, 1, 2, 1)
        dev_layout.setSpacing(6)
        dev_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_dev = QLabel("设备:")
        lbl_dev.setStyleSheet("color: #64748b; font-weight: 600; font-size: 12.5px;")
        dev_layout.addWidget(lbl_dev)

        self.combo_devices = DeviceComboBox()
        self.combo_devices.setFixedHeight(30)
        self.combo_devices.setFixedWidth(270)
        self.combo_devices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_devices.currentIndexChanged.connect(self.on_device_changed)
        dev_layout.addWidget(self.combo_devices)

        self.btn_refresh_devices = QPushButton()
        self.btn_refresh_devices.setIcon(get_tech_icon("refresh", "#0284c7"))
        self.btn_refresh_devices.setIconSize(QSize(16, 16))
        self.btn_refresh_devices.setToolTip("点击获取并刷新当前已连接的设备列表")
        self.btn_refresh_devices.setProperty("class", "action-btn")
        self.btn_refresh_devices.setFixedSize(30, 30)
        self.btn_refresh_devices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_devices.clicked.connect(self.refresh_devices_action)
        dev_layout.addWidget(self.btn_refresh_devices)
        top_layout.addWidget(dev_group)

        btn_w, btn_h = 96, 30

        self.btn_mode_select = QPushButton("元素审查")
        self.btn_mode_select.setIcon(get_tech_icon("target", "#ffffff"))
        self.btn_mode_select.setIconSize(QSize(14, 14))
        self.btn_mode_select.setProperty("class", "mode-btn")
        self.btn_mode_select.setFixedSize(btn_w, btn_h)
        self.btn_mode_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_select.setCheckable(True)
        self.btn_mode_select.setChecked(True)
        self.btn_mode_select.clicked.connect(lambda: self.switch_mode(InspectorMode.SELECT))
        top_layout.addWidget(self.btn_mode_select)

        self.btn_mode_tap = QPushButton("坐标点击")
        self.btn_mode_tap.setIcon(get_tech_icon("tap", "#475569"))
        self.btn_mode_tap.setIconSize(QSize(14, 14))
        self.btn_mode_tap.setProperty("class", "mode-btn")
        self.btn_mode_tap.setFixedSize(btn_w, btn_h)
        self.btn_mode_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_tap.setCheckable(True)
        self.btn_mode_tap.clicked.connect(lambda: self.switch_mode(InspectorMode.TAP))
        top_layout.addWidget(self.btn_mode_tap)

        btn_search_modal = QPushButton("查找元素")
        btn_search_modal.setIcon(get_tech_icon("search", "#0284c7"))
        btn_search_modal.setIconSize(QSize(14, 14))
        btn_search_modal.setProperty("class", "action-btn")
        btn_search_modal.setObjectName("btnSearch")
        btn_search_modal.setFixedSize(btn_w, btn_h)
        btn_search_modal.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_modal.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_search_modal.clicked.connect(self.open_search_dialog)
        top_layout.addWidget(btn_search_modal)

        self.btn_ios_service = QPushButton("启动服务")
        self.btn_ios_service.setObjectName("btnIosService")
        self.btn_ios_service.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_ios_service.setIcon(get_tech_icon("play", "#475569"))
        self.btn_ios_service.setIconSize(QSize(14, 14))
        self.btn_ios_service.setFixedSize(btn_w, btn_h)
        self.btn_ios_service.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ios_service.clicked.connect(self.on_ios_service_btn_clicked)
        self.btn_ios_service.hide()
        top_layout.addWidget(self.btn_ios_service)
        self.spinner_ios_service = ButtonSpinner(self.btn_ios_service, "refresh", "#0284c7")

        right_actions = QWidget()
        right_actions.setMinimumHeight(btn_h + 2)
        right_actions.setStyleSheet("background: transparent;")
        right_actions_layout = QHBoxLayout(right_actions)
        right_actions_layout.setContentsMargins(0, 1, 0, 1)
        right_actions_layout.setSpacing(6)
        right_actions_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        btn_copy_xml = QPushButton("复制源码")
        btn_copy_xml.setIcon(get_tech_icon("copy", "#475569"))
        btn_copy_xml.setIconSize(QSize(14, 14))
        btn_copy_xml.setProperty("class", "action-btn")
        btn_copy_xml.setFixedSize(btn_w, btn_h)
        btn_copy_xml.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy_xml.clicked.connect(self.copy_xml_source)
        right_actions_layout.addWidget(btn_copy_xml)

        btn_save_shot = QPushButton("保存截图")
        btn_save_shot.setIcon(get_tech_icon("save", "#475569"))
        btn_save_shot.setIconSize(QSize(14, 14))
        btn_save_shot.setProperty("class", "action-btn")
        btn_save_shot.setFixedSize(btn_w, btn_h)
        btn_save_shot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save_shot.clicked.connect(self.save_screenshot)
        right_actions_layout.addWidget(btn_save_shot)

        top_layout.addWidgetRight(right_actions)
        main_layout.addWidget(top_bar)

        # 2. 三栏主区域
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # 左栏：真机视窗
        left_container = QFrame()
        left_container.setProperty("class", "panel-card")
        left_container.setMinimumWidth(220)
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        left_header = FlowLayout(margin=0, h_spacing=6, v_spacing=6)
        lbl_left_title = QLabel("真机实时视窗")
        lbl_left_title.setFixedHeight(28)
        lbl_left_title.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_left_title.setStyleSheet("color: #334155; font-weight: 700; font-size: 13px; padding-right: 4px;")
        left_header.addWidget(lbl_left_title)

        sub_btn_w = 88

        self.btn_screencast = QPushButton("实时投屏")
        self.btn_screencast.setIcon(get_tech_icon("cast", "#0284c7"))
        self.btn_screencast.setIconSize(QSize(13, 13))
        self.btn_screencast.setFixedSize(sub_btn_w, 28)
        self.btn_screencast.setToolTip("切换真机低延迟实时投屏 (0 截屏广播)")
        self.btn_screencast.setProperty("class", "sub-action-btn")
        self.btn_screencast.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_screencast.clicked.connect(self.toggle_screencast)
        left_header.addWidget(self.btn_screencast)

        self.btn_sync_screen = QPushButton("同步画面")
        self.btn_sync_screen.setIcon(get_tech_icon("sync", "#0284c7"))
        self.btn_sync_screen.setIconSize(QSize(13, 13))
        self.btn_sync_screen.setFixedSize(sub_btn_w, 28)
        self.btn_sync_screen.setToolTip("同步真机最新画面与 DOM 层级树")
        self.btn_sync_screen.setProperty("class", "sub-action-btn")
        self.btn_sync_screen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_screen.clicked.connect(self.refresh_screen_only)
        left_header.addWidget(self.btn_sync_screen)

        self.btn_refresh = QPushButton("刷新界面")
        self.btn_refresh.setIcon(get_tech_icon("refresh", "#0284c7"))
        self.btn_refresh.setIconSize(QSize(13, 13))
        self.btn_refresh.setFixedSize(sub_btn_w, 28)
        self.btn_refresh.setToolTip("仅刷新 DOM 控件树，保留当前画面底图")
        self.btn_refresh.setProperty("class", "sub-action-btn")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_screen_and_dom)
        left_header.addWidget(self.btn_refresh)

        self.spinner_dev_refresh = ButtonSpinner(self.btn_refresh_devices, "refresh", "#0284c7")
        self.spinner_screencast = ButtonSpinner(self.btn_screencast, "cast", "#0284c7")
        self.spinner_sync = ButtonSpinner(self.btn_sync_screen, "sync", "#0284c7")
        self.spinner_refresh = ButtonSpinner(self.btn_refresh, "refresh", "#0284c7")

        left_layout.addLayout(left_header)

        self.canvas = AppiumScreenView()
        self.canvas.element_selected.connect(self.on_canvas_element_selected)
        self.canvas.coordinate_tapped.connect(self.on_canvas_coordinate_tapped)
        self.canvas.coordinate_swiped.connect(self.on_canvas_coordinate_swiped)
        left_layout.addWidget(self.canvas, 1)
        self.splitter.addWidget(left_container)

        # 中栏：DOM 树
        mid_container = QFrame()
        mid_container.setProperty("class", "panel-card")
        mid_container.setMinimumWidth(240)
        mid_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mid_layout = QVBoxLayout(mid_container)
        mid_layout.setContentsMargins(14, 14, 14, 14)
        mid_layout.setSpacing(10)

        tree_header = QHBoxLayout()
        tree_header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_mid_title = QLabel("ArkUI 组件层级树")
        lbl_mid_title.setStyleSheet("color: #334155; font-weight: 700; font-size: 13.5px;")
        tree_header.addWidget(lbl_mid_title)
        tree_header.addStretch()

        btn_search_dom = QPushButton("搜索 (Ctrl+F)")
        btn_search_dom.setIcon(get_tech_icon("search", "#0284c7"))
        btn_search_dom.setIconSize(QSize(15, 15))
        btn_search_dom.setFixedHeight(30)
        btn_search_dom.setProperty("class", "sub-action-btn")
        btn_search_dom.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_dom.clicked.connect(self.toggle_dom_search)
        tree_header.addWidget(btn_search_dom)

        btn_expand = QPushButton("展开全部")
        btn_expand.setIcon(get_tech_icon("expand", "#475569"))
        btn_expand.setIconSize(QSize(14, 14))
        btn_expand.setFixedHeight(30)
        btn_expand.setProperty("class", "sub-action-btn")
        btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_expand.clicked.connect(lambda: self.tree_widget.expandAll())
        tree_header.addWidget(btn_expand)

        btn_collapse = QPushButton("折叠全部")
        btn_collapse.setIcon(get_tech_icon("collapse", "#475569"))
        btn_collapse.setIconSize(QSize(14, 14))
        btn_collapse.setFixedHeight(30)
        btn_collapse.setProperty("class", "sub-action-btn")
        btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_collapse.clicked.connect(lambda: self.tree_widget.collapseAll())
        tree_header.addWidget(btn_collapse)
        mid_layout.addLayout(tree_header)

        self.lbl_breadcrumb = QLabel("路径: Hierarchy (根节点)")
        self.lbl_breadcrumb.setObjectName("breadcrumb")
        self.lbl_breadcrumb.setWordWrap(True)
        mid_layout.addWidget(self.lbl_breadcrumb)

        # DOM 内置实时搜索栏
        self.dom_search_bar = QFrame()
        self.dom_search_bar.setObjectName("domSearchBar")
        self.dom_search_bar.setStyleSheet("""
            #domSearchBar {
                background-color: #f0fdf4; border: 1px solid #86efac;
                border-radius: 6px; padding: 3px 6px;
            }
        """)
        search_layout = QHBoxLayout(self.dom_search_bar)
        search_layout.setContentsMargins(4, 3, 4, 3)
        search_layout.setSpacing(6)

        lbl_s_icon = QLabel()
        lbl_s_icon.setPixmap(get_tech_icon("search", "#0284c7").pixmap(14, 14))
        lbl_s_icon.setStyleSheet("background: transparent; border: none;")
        search_layout.addWidget(lbl_s_icon)

        self.edit_dom_search = QLineEdit()
        self.edit_dom_search.setPlaceholderText("搜索 DOM 标签、ID、文本、属性 (Enter 下一个 / Shift+Enter 上一个 / Esc 关闭)...")
        self.edit_dom_search.setStyleSheet("""
            QLineEdit {
                background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px;
                padding: 3px 8px; font-size: 12px; color: #0f172a;
            }
            QLineEdit:focus { border: 1px solid #0284c7; }
        """)
        self.edit_dom_search.textChanged.connect(self.on_dom_search_text_changed)

        def search_key_press(event: QKeyEvent) -> None:
            if event.key() == Qt.Key.Key_Escape:
                self.close_dom_search()
                return
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                if event.key() == Qt.Key.Key_C:
                    self.btn_match_case.click()
                    return
                if event.key() == Qt.Key.Key_W:
                    self.btn_match_word.click()
                    return
                if event.key() == Qt.Key.Key_R:
                    self.btn_match_regex.click()
                    return
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.on_dom_search_prev()
                else:
                    self.on_dom_search_next()
                return
            QLineEdit.keyPressEvent(self.edit_dom_search, event)

        self.edit_dom_search.keyPressEvent = search_key_press  # type: ignore[method-assign]
        search_layout.addWidget(self.edit_dom_search, 1)

        btn_opt_style = """
            QPushButton {
                background-color: transparent; color: #475569; border: 1px solid transparent;
                border-radius: 4px; font-family: Consolas, "Segoe UI", monospace; font-size: 11px;
                font-weight: 700; min-width: 22px; max-width: 22px; height: 22px; padding: 0px;
            }
            QPushButton:hover { background-color: #dcfce7; border-color: #86efac; color: #15803d; }
            QPushButton:checked { background-color: #16a34a; border: 1px solid #15803d; color: #ffffff; }
            QPushButton:checked:hover { background-color: #15803d; }
        """

        self.btn_match_case = QPushButton("Aa")
        self.btn_match_case.setCheckable(True)
        self.btn_match_case.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_match_case.setToolTip("区分大小写 (Match Case - Alt+C)")
        self.btn_match_case.setStyleSheet(btn_opt_style)
        self.btn_match_case.toggled.connect(self._on_dom_search_option_toggled)
        search_layout.addWidget(self.btn_match_case)

        self.btn_match_word = QPushButton("ab")
        self.btn_match_word.setCheckable(True)
        self.btn_match_word.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_match_word.setToolTip("全字匹配 (Match Whole Word - Alt+W)")
        self.btn_match_word.setStyleSheet(btn_opt_style + "QPushButton { text-decoration: underline; }")
        self.btn_match_word.toggled.connect(self._on_dom_search_option_toggled)
        search_layout.addWidget(self.btn_match_word)

        self.btn_match_regex = QPushButton(".*")
        self.btn_match_regex.setCheckable(True)
        self.btn_match_regex.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_match_regex.setToolTip("使用正则表达式 (Use Regular Expression - Alt+R)")
        self.btn_match_regex.setStyleSheet(btn_opt_style)
        self.btn_match_regex.toggled.connect(self._on_dom_search_option_toggled)
        search_layout.addWidget(self.btn_match_regex)

        self.lbl_dom_search_count = QLabel("0/0")
        self.lbl_dom_search_count.setStyleSheet(
            "color: #0284c7; font-weight: 700; font-size: 11px; min-width: 40px; background: transparent; border: none;"
        )
        search_layout.addWidget(self.lbl_dom_search_count)

        nav_btn_qss = (
            "QPushButton { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; "
            "color: #0284c7; font-weight: bold; font-size: 12px; } "
            "QPushButton:hover { background: #e0f2fe; border-color: #0284c7; }"
        )
        btn_prev_match = QPushButton("↑")
        btn_prev_match.setToolTip("上一个匹配项 (Shift+Enter)")
        btn_prev_match.setFixedSize(24, 24)
        btn_prev_match.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prev_match.setStyleSheet(nav_btn_qss)
        btn_prev_match.clicked.connect(self.on_dom_search_prev)
        search_layout.addWidget(btn_prev_match)

        btn_next_match = QPushButton("↓")
        btn_next_match.setToolTip("下一个匹配项 (Enter)")
        btn_next_match.setFixedSize(24, 24)
        btn_next_match.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_next_match.setStyleSheet(nav_btn_qss)
        btn_next_match.clicked.connect(self.on_dom_search_next)
        search_layout.addWidget(btn_next_match)

        btn_close_search = QPushButton("✕")
        btn_close_search.setToolTip("关闭搜索 (Esc)")
        btn_close_search.setFixedSize(24, 24)
        btn_close_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close_search.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #64748b; font-weight: bold; font-size: 13px; } "
            "QPushButton:hover { color: #ef4444; }"
        )
        btn_close_search.clicked.connect(self.close_dom_search)
        search_layout.addWidget(btn_close_search)

        self.dom_search_bar.setVisible(False)
        mid_layout.addWidget(self.dom_search_bar)

        self.tree_widget = DOMTreeWidget()
        self.tree_widget.setIndentation(13)
        self.tree_widget.setHeaderLabels([""])
        self.tree_widget.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.tree_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_widget.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tree_widget.header().setStretchLastSection(False)
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree_widget.header().setMinimumHeight(32)

        tree_header_view = self.tree_widget.header()
        header_bar_layout = QHBoxLayout(tree_header_view)
        header_bar_layout.setContentsMargins(10, 0, 10, 0)
        header_bar_layout.setSpacing(12)

        lbl_tree_title = QLabel("ArkUI 组件层次结构")
        lbl_tree_title.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px; background: transparent;")
        header_bar_layout.addWidget(lbl_tree_title)

        chk_qss = """
            QCheckBox { color: #0369a1; font-size: 12px; font-weight: 600; background: transparent; }
            QCheckBox::indicator { width: 14px; height: 14px; }
            QCheckBox:hover { color: #0284c7; }
        """
        self.chk_show_occluded = QCheckBox("显示被遮挡元素")
        self.chk_show_occluded.setChecked(False)
        self.chk_show_occluded.setToolTip("默认隐藏看不见/被遮挡的底层元素；勾选后可查看被遮挡或隐藏的元素")
        self.chk_show_occluded.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_show_occluded.setStyleSheet(chk_qss)
        self.chk_show_occluded.stateChanged.connect(self.on_toggle_show_occluded)
        header_bar_layout.addWidget(self.chk_show_occluded)

        self.chk_show_full_type = QCheckBox("显示原生完整类型")
        self.chk_show_full_type.setChecked(False)
        self.chk_show_full_type.setToolTip("开启后，iOS 将呈现 XCUIElementTypeLink 等全类名，Android 将呈现 android.widget.TextView 等全类名")
        self.chk_show_full_type.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_show_full_type.setStyleSheet(chk_qss)
        self.chk_show_full_type.stateChanged.connect(self.on_toggle_show_full_type)
        header_bar_layout.addWidget(self.chk_show_full_type)
        header_bar_layout.addStretch()

        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        self.tree_widget.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        self.tree_widget.currentItemChanged.connect(self.on_tree_current_item_changed)
        mid_layout.addWidget(self.tree_widget, 1)
        self.splitter.addWidget(mid_container)

        # 右栏：Selected Element 面板
        right_container = QFrame()
        right_container.setProperty("class", "panel-card")
        right_container.setMinimumWidth(300)
        right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(12)

        self.input_sync_box = QFrame()
        self.input_sync_box.setObjectName("inputSyncBox")
        self.input_sync_box.setStyleSheet(
            "#inputSyncBox { background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }"
        )
        sync_layout = QVBoxLayout(self.input_sync_box)
        sync_layout.setContentsMargins(10, 8, 10, 8)
        sync_layout.setSpacing(6)

        lbl_sync_title = QLabel("输入框实时调试与下发")
        lbl_sync_title.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px; border: none; background: transparent;")
        sync_layout.addWidget(lbl_sync_title)

        row_sync = QHBoxLayout()
        row_sync.setContentsMargins(0, 0, 0, 0)
        row_sync.setSpacing(6)

        self.edit_live_input = QLineEdit()
        self.edit_live_input.setFixedHeight(30)
        self.edit_live_input.setStyleSheet("font-size: 12px; padding: 2px 8px;")
        self.edit_live_input.setPlaceholderText("在此输入文字，按回车或点同步即刻下发真机...")
        self.edit_live_input.returnPressed.connect(self.sync_live_input)
        row_sync.addWidget(self.edit_live_input, 1)

        self.btn_sync_send = QPushButton("实时下发")
        self.btn_sync_send.setIcon(get_tech_icon("send", "#ffffff"))
        self.btn_sync_send.setIconSize(QSize(13, 13))
        self.btn_sync_send.setFixedHeight(30)
        self.btn_sync_send.setFixedWidth(84)
        self.btn_sync_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_send.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; font-weight: 700; border: none; "
            "border-radius: 5px; font-size: 11px; padding: 0 4px;"
        )
        self.btn_sync_send.clicked.connect(self.sync_live_input)
        row_sync.addWidget(self.btn_sync_send)

        self.btn_sync_clear = QPushButton("清空")
        self.btn_sync_clear.setIcon(get_tech_icon("clear", "#475569"))
        self.btn_sync_clear.setIconSize(QSize(13, 13))
        self.btn_sync_clear.setFixedHeight(30)
        self.btn_sync_clear.setFixedWidth(60)
        self.btn_sync_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_clear.setStyleSheet(
            "background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1; "
            "border-radius: 5px; font-weight: 600; font-size: 11px;"
        )
        self.btn_sync_clear.clicked.connect(self.action_element_clear)
        row_sync.addWidget(self.btn_sync_clear)

        sync_layout.addLayout(row_sync)
        self.input_sync_box.setVisible(False)
        right_layout.addWidget(self.input_sync_box)

        loc_box = QFrame()
        loc_box.setObjectName("locBox")
        loc_box.setStyleSheet(
            "#locBox { background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }"
        )
        loc_layout = QVBoxLayout(loc_box)
        loc_layout.setContentsMargins(10, 8, 10, 8)
        loc_layout.setSpacing(6)

        lbl_loc_title = QLabel("自动化定位代码推荐 (一键复用)")
        lbl_loc_title.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px; border: none; background: transparent;")
        loc_layout.addWidget(lbl_loc_title)

        grid_loc = QGridLayout()
        grid_loc.setContentsMargins(0, 0, 0, 0)
        grid_loc.setHorizontalSpacing(6)
        grid_loc.setVerticalSpacing(6)

        def _create_loc_row(label_text: str, placeholder: str, row_idx: int) -> QLineEdit:
            lbl = QLabel(label_text)
            lbl.setFixedWidth(56)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(
                "color: #475569; font-weight: 700; font-size: 11px; "
                "font-family: 'JetBrains Mono', Consolas, monospace; border: none; background: transparent;"
            )
            txt = QLineEdit()
            txt.setFixedHeight(30)
            txt.setReadOnly(True)
            txt.setStyleSheet("font-size: 12px; padding: 2px 8px; font-family: 'JetBrains Mono', Consolas, monospace;")
            txt.setPlaceholderText(placeholder)

            btn = QPushButton("复制")
            btn.setIcon(get_tech_icon("copy", "#0284c7"))
            btn.setIconSize(QSize(13, 13))
            btn.setFixedHeight(30)
            btn.setFixedWidth(64)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background-color: #ffffff; color: #0284c7; border: 1px solid #bae6fd; "
                "border-radius: 5px; font-weight: 700; font-size: 11px; }"
                "QPushButton:hover { background-color: #0284c7; color: #ffffff; border-color: #0284c7; }"
            )
            btn.clicked.connect(lambda: self.copy_to_clip(txt.text()))

            grid_loc.addWidget(lbl, row_idx, 0)
            grid_loc.addWidget(txt, row_idx, 1)
            grid_loc.addWidget(btn, row_idx, 2)
            return txt

        self.txt_loc_id = _create_loc_row("id", "ID 定位代码: (该元素无 ID)", 0)
        self.txt_loc_class_chain = _create_loc_row("chain", "iOS Class Chain 类链表达式", 1)
        self.txt_loc_predicate = _create_loc_row("predicate", "iOS Predicate 谓词表达式", 2)
        self.txt_loc_xpath = _create_loc_row("xpath", "XPath 表达式", 3)
        self.txt_loc_py = _create_loc_row("python", "Python 语句", 4)

        loc_layout.addLayout(grid_loc)
        right_layout.addWidget(loc_box)

        lbl_attr_header = QLabel("详细属性清单 (Attributes)")
        lbl_attr_header.setStyleSheet("color: #334155; font-weight: 700; font-size: 13px; margin-top: 4px;")
        right_layout.addWidget(lbl_attr_header)

        self.table_attrs = QTableWidget()
        self.table_attrs.setColumnCount(2)
        self.table_attrs.setHorizontalHeaderLabels(["属性名称 (Attribute)", "属性值 (Value)"])
        self.table_attrs.setWordWrap(True)
        self.table_attrs.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.table_attrs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_attrs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # 垂直表头采用 Interactive + 默认 28px，仅对长文本/换行行按需测高
        v_header = self.table_attrs.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        v_header.setDefaultSectionSize(28)
        v_header.setMinimumSectionSize(26)
        self.table_attrs.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right_layout.addWidget(self.table_attrs, 1)
        self.splitter.splitterMoved.connect(lambda *_: self._resize_long_attr_rows())

        self.splitter.addWidget(right_container)
        self.splitter.setStretchFactor(0, 28)
        self.splitter.setStretchFactor(1, 50)
        self.splitter.setStretchFactor(2, 30)
        main_layout.addWidget(self.splitter, 1)

    # ------------------------------------------------------------------
    # 设备发现与平台切换
    # ------------------------------------------------------------------
    def load_device_list(self, auto_capture: bool = True) -> None:
        if self.scan_worker and self.scan_worker.isRunning():
            return
        if hasattr(self, "btn_refresh_devices"):
            self.btn_refresh_devices.setEnabled(False)
        if self.combo_devices.count() == 0:
            self.combo_devices.addItem("正在扫描已连接设备...", None)
        self.scan_worker = DeviceScanWorker()
        self.scan_worker.devices_ready.connect(lambda devs: self._on_devices_scanned(devs, auto_capture))
        self.scan_worker.start()

    def _on_devices_scanned(self, devices: List[Dict[str, Any]], auto_capture: bool) -> None:
        if hasattr(self, "spinner_dev_refresh"):
            self.spinner_dev_refresh.stop()
        if hasattr(self, "btn_refresh_devices"):
            self.btn_refresh_devices.setEnabled(True)

        self.combo_devices.blockSignals(True)
        self.combo_devices.clear()

        if devices:
            target_index = -1
            for idx, dev in enumerate(devices):
                item_text = f"[{dev['platform'].upper()}] {dev['name']}"
                self.combo_devices.addItem(item_text, dev)
                if dev["udid"] == self.current_udid:
                    target_index = idx

            if target_index >= 0:
                self.combo_devices.setCurrentIndex(target_index)
                self.combo_devices.setToolTip("")
                self.update_platform_badge()
                self.combo_devices.blockSignals(False)
            else:
                first = devices[0]
                was_screencasting = self.is_screencasting
                if self.screencast_worker:
                    self.stop_screencast()
                ScreenCastWorker.clear_cache()
                self.current_screenshot_path = ""
                if hasattr(self, "canvas") and self.canvas is not None:
                    self.canvas.clear_screen()
                self.current_udid = first["udid"]
                self.current_platform = first["platform"]
                self.combo_devices.setCurrentIndex(0)
                self.combo_devices.setToolTip("")
                self.update_platform_badge()
                self.combo_devices.blockSignals(False)
                if was_screencasting:
                    QTimer.singleShot(150, self.start_screencast)
                if auto_capture:
                    if was_screencasting:
                        QTimer.singleShot(1200, self.refresh_screen_and_dom)
                    else:
                        QTimer.singleShot(500, self.refresh_screen_only)
        else:
            self.combo_devices.addItem("未检测到在线设备 (请检查 USB/网络连接)", None)
            self.current_udid = ""
            self.current_platform = "harmony"
            self.combo_devices.setToolTip("")
            self.update_platform_badge()
            self.combo_devices.blockSignals(False)

    def refresh_devices_action(self) -> None:
        if hasattr(self, "spinner_dev_refresh"):
            self.spinner_dev_refresh.start()
        self.load_device_list(auto_capture=False)

    def on_device_changed(self, index: int) -> None:
        dev = self.combo_devices.currentData()
        if dev and isinstance(dev, dict):
            new_udid = dev.get("udid", "")
            new_plat = dev.get("platform", "harmony")
            self.combo_devices.setToolTip("")

            if new_plat == "ios":
                self.btn_ios_service.show()
                self.refresh_ios_service_status()
            else:
                self.btn_ios_service.hide()

            if new_udid != self.current_udid or new_plat != self.current_platform:
                was_screencasting = self.is_screencasting
                if self.screencast_worker:
                    old_worker = self.screencast_worker
                    self.stop_screencast()
                    if old_worker.isRunning():
                        old_worker.wait(800)
                IosWdaManager.kill_relays()
                ScreenCastWorker.release_all_tunnels()
                ScreenCastWorker.clear_cache()
                self.current_screenshot_path = ""
                self.canvas.clear_screen()
                self.current_udid = new_udid
                self.current_platform = new_plat
                self.update_platform_badge()
                if was_screencasting:
                    QTimer.singleShot(400, self.start_screencast)
                    QTimer.singleShot(1100, self.refresh_screen_and_dom)
                else:
                    QTimer.singleShot(350, self.refresh_screen_only)

    def update_platform_badge(self) -> None:
        if self.current_platform == "harmony":
            self.lbl_platform_badge.setText("HarmonyOS NEXT")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #e0f2fe; color: #0284c7; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bae6fd;"
            )
            self.btn_ios_service.hide()
        elif self.current_platform == "android":
            self.lbl_platform_badge.setText("Android")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #dcfce7; color: #16a34a; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #bbf7d0;"
            )
            self.btn_ios_service.hide()
        elif self.current_platform == "ios":
            self.lbl_platform_badge.setText("iOS")
            self.lbl_platform_badge.setStyleSheet(
                "background-color: #f1f5f9; color: #334155; font-weight: 700; "
                "font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #cbd5e1;"
            )
            self.btn_ios_service.show()
            self.refresh_ios_service_status()

    # ------------------------------------------------------------------
    # iOS WDA 服务巡检与启停
    # ------------------------------------------------------------------
    def refresh_ios_service_status(self, force_state: Optional[str] = None) -> None:
        if not hasattr(self, "btn_ios_service"):
            return
        if force_state is None and self._ios_service_running_action:
            return

        if force_state in ("running", "abnormal", "stopped"):
            target_state = force_state
        else:
            is_xcuitest, is_forward = check_ios_wda_services()
            if is_xcuitest and is_forward:
                target_state = "running"
            elif is_xcuitest or is_forward:
                target_state = "abnormal"
            else:
                target_state = "stopped"

        if target_state == "running":
            self._ios_service_state = "running"
            self.btn_ios_service.setText("正在运行")
            self.btn_ios_service.setIcon(get_tech_icon("check", "#ffffff"))
            self.btn_ios_service.setToolTip("iOS WDA 自动化服务与 8100 端口正常运行中 (点击可一键停止服务)")
            self.btn_ios_service.setStyleSheet("""
                QPushButton#btnIosService {
                    background-color: #10b981; color: #ffffff; border: 1px solid #059669;
                    border-radius: 6px; font-weight: 600; font-size: 12.5px; padding: 0 8px;
                }
                QPushButton#btnIosService:hover { background-color: #059669; }
                QPushButton#btnIosService:disabled { background-color: #6ee7b7; color: #f0fdf4; }
            """)
        elif target_state == "abnormal":
            self._ios_service_state = "abnormal"
            self.btn_ios_service.setText("重启服务")
            self.btn_ios_service.setIcon(get_tech_icon("refresh", "#ffffff"))
            self.btn_ios_service.setToolTip("检测到仅单项子服务运行 (状态异常)，点击一键停止并重启 WDA 服务")
            self.btn_ios_service.setStyleSheet("""
                QPushButton#btnIosService {
                    background-color: #f59e0b; color: #ffffff; border: 1px solid #d97706;
                    border-radius: 6px; font-weight: 600; font-size: 12.5px; padding: 0 8px;
                }
                QPushButton#btnIosService:hover { background-color: #d97706; }
                QPushButton#btnIosService:disabled { background-color: #fcd34d; color: #fffbeb; }
            """)
        else:
            self._ios_service_state = "stopped"
            self.btn_ios_service.setText("启动服务")
            self.btn_ios_service.setIcon(get_tech_icon("play", "#475569"))
            self.btn_ios_service.setToolTip("点击一键启动 iOS WDA 守护进程与 8100 端口透传")
            self.btn_ios_service.setStyleSheet("""
                QPushButton#btnIosService {
                    background-color: rgba(255, 255, 255, 0.9); color: #334155; border: 1px solid #cbd5e1;
                    border-radius: 6px; font-weight: 600; font-size: 12.5px; padding: 0 8px;
                }
                QPushButton#btnIosService:hover { background-color: #f1f5f9; border-color: #94a3b8; color: #0f172a; }
                QPushButton#btnIosService:disabled { background-color: #f8fafc; color: #94a3b8; }
            """)

    def _on_ios_service_timer_tick(self) -> None:
        if self.current_platform != "ios" or not self.btn_ios_service.isVisible() or self._ios_service_running_action:
            return
        self.refresh_ios_service_status()

    def on_ios_service_btn_clicked(self) -> None:
        if self._ios_service_running_action:
            return
        if self.toast:
            self.toast.hide()

        current_state = self._ios_service_state
        action = "stop" if current_state == "running" else "start_or_restart"
        loading_text = "正在停止..." if action == "stop" else "正在启动..."

        self._ios_service_running_action = True
        self.setFocus()
        self.btn_ios_service.setEnabled(False)
        self.spinner_ios_service.icon_color = "#ffffff" if current_state in ("running", "abnormal") else "#0284c7"
        self.spinner_ios_service.start(loading_text)

        self._ios_service_worker = IosServiceActionWorker(action, parent=self)
        self._ios_service_worker.finished_sig.connect(self._on_ios_service_action_finished)
        self._ios_service_worker.start()

    def _on_ios_service_action_finished(self, success: bool, message: str, action: str = "") -> None:
        self._ios_service_running_action = False
        self.spinner_ios_service.stop(restore_text=False)
        self.btn_ios_service.setEnabled(True)

        if action == "stop":
            self.refresh_ios_service_status(force_state="stopped")
            self.show_toast("✅ 服务已停止", duration_ms=1500)
        elif success:
            self.refresh_ios_service_status(force_state="running")
            self.show_toast("✅ 服务已启动", duration_ms=1500)
        else:
            self.refresh_ios_service_status()
            tip = f"⚠️ {message}" if message else "⚠️ 服务启动未完全就绪，请重试"
            self.show_toast(tip, duration_ms=3200)

    # ------------------------------------------------------------------
    # 抓取与投屏调度
    # ------------------------------------------------------------------
    def _reset_capture_buttons(self) -> None:
        self._timer_sync_screen.stop()
        self._timer_refresh.stop()
        self.spinner_sync.stop(restore_text=True)
        self.spinner_refresh.stop(restore_text=True)
        # 投屏进行中保持【同步画面】禁用态，防止刷新 DOM 结束后被 spinner_sync.stop() 误恢复
        self._update_sync_screen_btn_state()

    def _on_sync_screen_timeout(self) -> None:
        logger.warning("[UI审查器] 同步真机画面超时 (20s)")
        if self.capture_worker and self.capture_worker.isRunning():
            try:
                self.capture_worker.terminate()
            except Exception:
                pass
            self.capture_worker = None
        self._reset_capture_buttons()
        self.show_toast("⚠️ 同步真机画面超时 (20s)，已重置状态")

    def _on_refresh_timeout(self) -> None:
        logger.warning("[UI审查器] 刷新界面超时 (20s)")
        if self.capture_worker and self.capture_worker.isRunning():
            try:
                self.capture_worker.terminate()
            except Exception:
                pass
            self.capture_worker = None
        self._reset_capture_buttons()
        self.show_toast("⚠️ 刷新界面超时 (20s)，已重置状态")

    def _on_screencast_timeout(self) -> None:
        logger.warning("[UI审查器] 开启实时投屏超时 (15s)")
        self.stop_screencast()
        self._timer_screencast.stop()
        self._update_screencast_btn_style(False)
        self.show_toast("⚠️ 开启实时投屏超时 (15s)，投屏通道未响应，已自动复位")

    @staticmethod
    def _resolve_layout_viewport_size(local_png: str, layout_file: str, platform: str) -> Tuple[int, int]:
        if platform == "ios":
            logical_size = normalize_ios_screenshot_file(local_png, layout_file)
            return logical_size if logical_size else (390, 844)
        phys_w, phys_h = get_layout_physical_size(layout_file, 1084, 2412)
        pix = QPixmap(local_png) if (local_png and os.path.exists(local_png)) else QPixmap()
        if not pix.isNull() and pix.width() >= 800 and pix.height() >= 1200:
            return pix.width(), pix.height()
        return phys_w, phys_h

    def _rebuild_dom_state_from_layout(self, layout_file: str, platform: str, screen_w: int, screen_h: int) -> None:
        """统一重建 DOM 树、XML 与组件映射表（供纯 DOM 刷新与全量刷新共用）"""
        raw_tree = parse_layout_file(layout_file, platform, screen_w=screen_w, screen_h=screen_h)

        self.clear_dom_search_highlights()
        self.flat_components.clear()
        self.comp_map.clear()
        self.tree_item_map.clear()
        self.tree_widget.clear()
        self.node_counter = 0
        self._last_panel_sig = None

        has_active_dialog = find_active_dialogs(raw_tree)
        self.xml_root = ET.Element("Hierarchy", {"platform": platform, "udid": self.current_udid})
        self.build_dom_tree(
            raw_tree,
            None,
            self.xml_root,
            "/Hierarchy",
            depth=0,
            parent_visible=True,
            is_in_active_page=True,
            screen_w=screen_w,
            screen_h=screen_h,
            is_parent_occluded=False,
            has_active_dialog=has_active_dialog,
            is_in_dialog=False,
        )

        show_occluded = self.chk_show_occluded.isChecked() if hasattr(self, "chk_show_occluded") else False
        self.apply_occluded_visibility_to_tree(show_occluded)

    def _finish_dom_view_sync(self, prev_selected_id: str) -> None:
        self.tree_widget.expandToDepth(2)
        if self.dom_search_bar.isVisible() and self.edit_dom_search.text().strip():
            self.on_dom_search_text_changed(self.edit_dom_search.text())

        if prev_selected_id and prev_selected_id in self.comp_map:
            self.select_element_by_id(prev_selected_id)
        else:
            self.canvas.selected_node_id = ""
            self.canvas.hover_node_id = ""
            self.canvas.update()

        if self.search_dialog is not None:
            self.search_dialog.update_context(
                self.flat_components,
                self.xml_root,
                comp_map=self.comp_map,
                platform=self.current_platform,
            )

    def refresh_screen_and_dom(self) -> None:
        if not self.current_udid:
            ModernMessageBox.warning(self, "设备未连接", "未检测到在线移动设备，请确认开启 USB 调试并连接设备。")
            return

        if self.capture_worker and self.capture_worker.isRunning():
            if self._worker_start_time and (time.time() - self._worker_start_time > 6):
                try:
                    self.capture_worker.terminate()
                    self.capture_worker.wait(500)
                except Exception:
                    pass
            else:
                self.show_toast("⏳ 上一轮刷新仍在进行中，请稍候...", duration_ms=1200)
                return

        self._worker_start_time = time.time()
        self.btn_refresh.setEnabled(False)
        self.spinner_refresh.start(loading_text="正在刷新...")
        self._timer_refresh.start(20000)

        tmp_dir = self._get_inspector_cache_dir()

        self.capture_worker = CaptureWorker(self.current_udid, self.current_platform, tmp_dir, mode="dom_only")
        self.capture_worker.dom_finished.connect(self.on_dom_only_success)
        self.capture_worker.failed.connect(self.on_capture_failed)
        self.capture_worker.start()

    @staticmethod
    def _get_inspector_cache_dir() -> str:
        """获取审查器截屏与 DOM 缓存目录（统一归口至可写 REPORTS_DIR/inspector）。"""
        tmp_dir = os.path.normpath(os.path.abspath(os.path.join(REPORTS_DIR, "inspector")))
        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

    def on_dom_only_success(self, layout_file: str, platform: str) -> None:
        self._reset_capture_buttons()
        local_png = self.current_screenshot_path
        try:
            prev_selected_id = self.canvas.selected_node_id
            screen_w, screen_h = self._resolve_layout_viewport_size(local_png, layout_file, platform)
            if platform == "ios" and local_png and os.path.exists(local_png) and not self.is_screencasting:
                self.canvas.update_screen_pixmap(QPixmap(local_png), keep_components=True)

            self._rebuild_dom_state_from_layout(layout_file, platform, screen_w, screen_h)
            self.canvas.update_components_only(self.flat_components, layout_size=(screen_w, screen_h))
            self._finish_dom_view_sync(prev_selected_id)
            self.show_toast("✅ DOM 控件树已极速刷新 (真机画面保持不变)")
        except Exception as e:
            logger.error(f"[UI审查器] 刷新 DOM 树数据异常: {e}")

    def on_capture_success(self, local_png: str, layout_file: str, platform: str) -> None:
        self._reset_capture_buttons()
        is_real_shot = os.path.exists(local_png) and os.path.getsize(local_png) > 40000
        if is_real_shot:
            self.current_screenshot_path = local_png

        try:
            prev_selected_id = self.canvas.selected_node_id
            screen_w, screen_h = self._resolve_layout_viewport_size(local_png, layout_file, platform)
            self._rebuild_dom_state_from_layout(layout_file, platform, screen_w, screen_h)

            if is_real_shot:
                self.canvas.load_screenshot(local_png, self.flat_components, layout_size=(screen_w, screen_h))
            elif (
                ScreenCastWorker.latest_udid == self.current_udid
                and ScreenCastWorker.latest_image is not None
                and not ScreenCastWorker.latest_image.isNull()
            ):
                cast_img = (
                    crop_ios_dvt_image(ScreenCastWorker.latest_image, (screen_w, screen_h))
                    if platform == "ios"
                    else ScreenCastWorker.latest_image
                )
                self.canvas.update_screen_pixmap(QPixmap.fromImage(cast_img), keep_components=False)
                self.canvas.update_components_only(self.flat_components, layout_size=(screen_w, screen_h))
            elif os.path.exists(local_png):
                self.canvas.load_screenshot(local_png, self.flat_components, layout_size=(screen_w, screen_h))

            self._finish_dom_view_sync(prev_selected_id)
            self.show_toast("✅ 画面与 DOM 树已全部同步")
        except Exception as e:
            logger.error(f"[UI审查器] 处理界面现场数据异常: {e}")

    def on_capture_failed(self, err_msg: str) -> None:
        self._reset_capture_buttons()
        if self._ios_service_running_action:
            return
        if self.current_platform == "ios":
            self.show_toast(f"📱 iOS 提示: {err_msg}")
            return
        ModernMessageBox.critical(self, "抓取失败", f"无法获取设备现场界面与布局:\n{err_msg}")

    def refresh_screen_only(self) -> None:
        if not self.current_udid:
            ModernMessageBox.warning(self, "设备未连接", "未检测到在线设备，请先连接并选中设备。")
            return
        if self._is_screencast_locked():
            return

        if self.capture_worker and self.capture_worker.isRunning():
            if self._worker_start_time and (time.time() - self._worker_start_time > 8):
                try:
                    self.capture_worker.terminate()
                    self.capture_worker.wait(500)
                except Exception:
                    pass
            else:
                self.show_toast("⏳ 任务正在执行中，请勿重复点击", duration_ms=1200)
                return

        self._worker_start_time = time.time()
        tmp_dir = self._get_inspector_cache_dir()

        if self.current_platform == "ios" and (self.is_screencasting or ScreenCastWorker.is_active):
            mem_bytes = ScreenCastWorker.get_latest_jpeg_bytes(self.current_udid)
            if mem_bytes:
                try:
                    shot_path = os.path.join(tmp_dir, "screencast_last_ios.jpeg")
                    with open(shot_path, "wb") as f_s:
                        f_s.write(mem_bytes)
                    self.current_screenshot_path = shot_path
                except Exception:
                    pass

        self.btn_sync_screen.setEnabled(False)
        self.spinner_sync.start(loading_text="正在同步...")
        self._timer_sync_screen.start(20000)

        self.capture_worker = CaptureWorker(self.current_udid, self.current_platform, tmp_dir, mode="full")
        self.capture_worker.finished.connect(self.on_capture_success)
        self.capture_worker.failed.connect(self.on_capture_failed)
        self.capture_worker.start()

    def toggle_screencast(self) -> None:
        if self.is_screencasting:
            self.stop_screencast()
        else:
            self.start_screencast()

    def start_screencast(self) -> None:
        if not self.current_udid:
            ModernMessageBox.warning(self, "设备未连接", "未检测到在线设备，请先连接并选中设备。")
            return

        self.btn_screencast.setEnabled(False)
        self.spinner_screencast.start(loading_text="连接中...")
        self._update_sync_screen_btn_state(disabled=True)
        self._timer_screencast.start(15000)

        if self.capture_worker and self.capture_worker.isRunning():
            for sig in (
                self.capture_worker.finished,
                self.capture_worker.screen_finished,
                self.capture_worker.dom_finished,
                self.capture_worker.failed,
            ):
                try:
                    sig.disconnect()
                except Exception:
                    pass
            self.capture_worker.quit()
            self.capture_worker.wait(300)

        if self.screencast_worker:
            old_w = self.screencast_worker
            self.screencast_worker = None
            for sig in (old_w.frame_ready, old_w.state_changed, old_w.error_occurred):
                try:
                    sig.disconnect()
                except Exception:
                    pass
            old_w.stop()
            if old_w.isRunning():
                old_w.wait(1500)

        self.screencast_worker = ScreenCastWorker(self.current_udid, self.current_platform)
        self.screencast_worker.frame_ready.connect(self.on_screencast_frame)
        self.screencast_worker.state_changed.connect(self.on_screencast_state_changed)
        self.screencast_worker.error_occurred.connect(self.on_screencast_error)
        self.screencast_worker.start()

    def stop_screencast(self) -> None:
        self._timer_screencast.stop()
        self.is_screencasting = False
        self._update_screencast_btn_style(False)
        if self.screencast_worker:
            worker = self.screencast_worker
            self.screencast_worker = None
            try:
                worker.frame_ready.disconnect(self.on_screencast_frame)
                worker.state_changed.disconnect(self.on_screencast_state_changed)
                worker.error_occurred.disconnect(self.on_screencast_error)
            except Exception:
                pass
            worker.stop()

            def _async_cleanup() -> None:
                worker.wait(500)
                IosWdaManager.kill_relays()

            QTimer.singleShot(0, _async_cleanup)
        else:
            IosWdaManager.kill_relays()

    def on_screencast_frame(self, image: QImage, raw_bytes: bytes) -> None:
        try:
            if not image or image.isNull():
                return
            if not self.is_screencasting:
                self.is_screencasting = True
                self._timer_screencast.stop()
                self._update_screencast_btn_style(True)
            elif self._timer_screencast.isActive():
                self._timer_screencast.stop()

            if self.current_platform == "ios" and 250 <= self.canvas.layout_w <= 700 and 400 <= self.canvas.layout_h <= 1400:
                image = crop_ios_dvt_image(image, (self.canvas.layout_w, self.canvas.layout_h))

            self.canvas.update_screen_image(image, keep_components=True)

            now = time.time()
            if now - self._last_disk_cache_t > 1.5 and raw_bytes:
                self._last_disk_cache_t = now
                plat_snap = self.current_platform

                def _async_save() -> None:
                    try:
                        tmp_dir = self._get_inspector_cache_dir()
                        ext = "jpeg" if raw_bytes.startswith(b"\xff\xd8") else "png"
                        cached_file = os.path.join(tmp_dir, f"screencast_last_{plat_snap}.{ext}")
                        with open(cached_file, "wb") as f:
                            f.write(raw_bytes)
                        self.current_screenshot_path = cached_file
                    except Exception:
                        pass

                threading.Thread(target=_async_save, daemon=True).start()
        finally:
            if self.screencast_worker:
                self.screencast_worker.ui_ready = True

    def on_screencast_state_changed(self, is_running: bool, msg: str) -> None:
        self._timer_screencast.stop()
        self.is_screencasting = is_running
        self._update_screencast_btn_style(is_running)
        if is_running:
            tip = f"✅ {msg}" if msg else "✅ 实时投屏已启动"
            self.show_toast(tip)

    def on_screencast_error(self, err_msg: str) -> None:
        self._timer_screencast.stop()
        self.is_screencasting = False
        self._update_screencast_btn_style(False)
        self.show_toast(f"⚠️ 投屏提示: {err_msg}", duration_ms=4500)

    def _is_screencast_locked(self) -> bool:
        """判断当前是否处于实时投屏中或投屏建连中（三端统一判定）"""
        if self.is_screencasting:
            return True
        if self.screencast_worker is not None and self.screencast_worker.isRunning():
            return True
        return False

    def _update_sync_screen_btn_state(self, disabled: Optional[bool] = None) -> None:
        """按投屏状态统一控制【同步画面】按钮禁用/启用及置灰样式（HarmonyOS / Android / iOS 一致）"""
        if not hasattr(self, "btn_sync_screen"):
            return
        should_disable = self._is_screencast_locked() if disabled is None else bool(disabled)
        if should_disable:
            if hasattr(self, "spinner_sync"):
                self.spinner_sync.timer.stop()
            self.btn_sync_screen.setText("同步画面")
            self.btn_sync_screen.setIcon(get_tech_icon("sync", "#94a3b8"))
            self.btn_sync_screen.setEnabled(False)
            self.btn_sync_screen.setCursor(Qt.CursorShape.ForbiddenCursor)
            self.btn_sync_screen.setToolTip("实时投屏进行中已禁用同步画面，请点击【刷新界面】更新 DOM 树，或停止投屏后再使用")
        else:
            self.btn_sync_screen.setIcon(get_tech_icon("sync", "#0284c7"))
            self.btn_sync_screen.setEnabled(True)
            self.btn_sync_screen.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_sync_screen.setToolTip("同步真机最新画面与 DOM 层级树")

    def _update_screencast_btn_style(self, is_running: bool) -> None:
        if not hasattr(self, "btn_screencast"):
            return
        self.spinner_screencast.stop(restore_text=False)
        self.btn_screencast.setEnabled(True)
        self._update_sync_screen_btn_state(disabled=is_running)
        if is_running:
            self.btn_screencast.setText("停止投屏")
            self.btn_screencast.setIcon(get_tech_icon("cast", "#ef4444"))
            self.btn_screencast.setStyleSheet(
                "QPushButton { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 5px; "
                "color: #dc2626; font-size: 11px; font-weight: 700; padding: 0 10px; min-height: 26px; } "
                "QPushButton:hover { background: #fee2e2; border-color: #ef4444; }"
            )
        else:
            self.btn_screencast.setText("实时投屏")
            self.btn_screencast.setIcon(get_tech_icon("cast", "#0284c7"))
            self.btn_screencast.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px; "
                "color: #334155; font-size: 11px; font-weight: 600; padding: 0 10px; min-height: 26px; } "
                "QPushButton:hover { background: #f1f5f9; border-color: #0284c7; color: #0284c7; }"
            )

    # ------------------------------------------------------------------
    # DOM 树构建与内置搜索
    # ------------------------------------------------------------------
    def build_dom_tree(
        self,
        node: Dict[str, Any],
        parent_item: Optional[QTreeWidgetItem],
        xml_parent: ET.Element,
        current_xpath: str,
        depth: int = 0,
        parent_visible: bool = True,
        is_in_active_page: bool = True,
        screen_w: int = 1084,
        screen_h: int = 2412,
        is_parent_occluded: bool = False,
        has_active_dialog: bool = False,
        is_in_dialog: bool = False,
        covering_rects: Optional[List[Tuple[int, int, int, int]]] = None,
    ) -> bool:
        return build_dom_tree_into_inspector(
            self,
            node,
            parent_item,
            xml_parent,
            current_xpath,
            depth=depth,
            parent_visible=parent_visible,
            is_in_active_page=is_in_active_page,
            screen_w=screen_w,
            screen_h=screen_h,
            is_parent_occluded=is_parent_occluded,
            has_active_dialog=has_active_dialog,
            is_in_dialog=is_in_dialog,
            covering_rects=covering_rects,
        )

    def toggle_dom_search(self) -> None:
        if not self.dom_search_bar.isVisible():
            self.dom_search_bar.setVisible(True)
        self.edit_dom_search.setFocus()
        self.edit_dom_search.selectAll()

    def close_dom_search(self) -> None:
        self.clear_dom_search_highlights()
        self.edit_dom_search.setStyleSheet("""
            QLineEdit {
                background: #ffffff; border: 1px solid #bbf7d0; border-radius: 4px;
                padding: 3px 8px; font-size: 12px; color: #1e293b;
            }
            QLineEdit:focus { border: 1px solid #22c55e; }
        """)
        self.lbl_dom_search_count.setStyleSheet(
            "color: #15803d; font-weight: 700; font-size: 11px; min-width: 40px; background: transparent; border: none;"
        )
        self.dom_search_bar.setVisible(False)
        self.tree_widget.setFocus()

    def clear_dom_search_highlights(self) -> None:
        for item, orig_fg, orig_bg in self.dom_search_original_styles:
            try:
                item.setForeground(0, orig_fg)
                item.setBackground(0, orig_bg)
                font = item.font(0)
                if font.bold():
                    font.setBold(False)
                    item.setFont(0, font)
            except RuntimeError:
                pass
        self.dom_search_original_styles.clear()
        self.dom_search_matches.clear()
        self.dom_search_index = -1

    def _on_dom_search_option_toggled(self) -> None:
        self.on_dom_search_text_changed(self.edit_dom_search.text())

    def on_dom_search_text_changed(self, keyword: str) -> None:
        self.clear_dom_search_highlights()
        kw = keyword.strip()
        normal_input_qss = """
            QLineEdit {
                background: #ffffff; border: 1px solid #bbf7d0; border-radius: 4px;
                padding: 3px 8px; font-size: 12px; color: #1e293b;
            }
            QLineEdit:focus { border: 1px solid #22c55e; }
        """
        normal_cnt_qss = (
            "color: #15803d; font-weight: 700; font-size: 11px; min-width: 40px; background: transparent; border: none;"
        )
        if not kw:
            self.lbl_dom_search_count.setText("0/0")
            self.lbl_dom_search_count.setStyleSheet(normal_cnt_qss)
            self.edit_dom_search.setStyleSheet(normal_input_qss)
            return

        match_case = self.btn_match_case.isChecked()
        match_word = self.btn_match_word.isChecked()
        match_regex = self.btn_match_regex.isChecked()

        flags = 0 if match_case else re.IGNORECASE
        regex_obj = None

        if match_regex:
            try:
                pattern = r"\b(?:" + kw + r")\b" if match_word else kw
                regex_obj = re.compile(pattern, flags)
                self.edit_dom_search.setStyleSheet(normal_input_qss)
                self.lbl_dom_search_count.setStyleSheet(normal_cnt_qss)
            except re.error:
                self.edit_dom_search.setStyleSheet("""
                    QLineEdit {
                        background: #fef2f2; border: 1.5px solid #ef4444; border-radius: 4px;
                        padding: 3px 8px; font-size: 12px; color: #991b1b;
                    }
                """)
                self.lbl_dom_search_count.setText("无效正则")
                self.lbl_dom_search_count.setStyleSheet(
                    "color: #dc2626; font-weight: 700; font-size: 11px; min-width: 48px; background: transparent; border: none;"
                )
                return
        elif match_word:
            try:
                regex_obj = re.compile(r"\b" + re.escape(kw) + r"\b", flags)
            except re.error:
                regex_obj = None

        def is_matched(node_text: str) -> bool:
            if regex_obj is not None:
                return bool(regex_obj.search(node_text))
            return (kw in node_text) if match_case else (kw.lower() in node_text.lower())

        def collect_tree_items(parent_item: QTreeWidgetItem) -> List[QTreeWidgetItem]:
            items: List[QTreeWidgetItem] = []
            for i in range(parent_item.childCount()):
                ch = parent_item.child(i)
                items.append(ch)
                items.extend(collect_tree_items(ch))
            return items

        all_items: List[QTreeWidgetItem] = []
        for i in range(self.tree_widget.topLevelItemCount()):
            top = self.tree_widget.topLevelItem(i)
            all_items.append(top)
            all_items.extend(collect_tree_items(top))

        matches = [it for it in all_items if (not it.isHidden()) and is_matched(it.text(0))]
        self.dom_search_matches = matches

        if not matches:
            self.lbl_dom_search_count.setText("0/0")
            return

        for item in matches:
            self.dom_search_original_styles.append((item, item.foreground(0).color(), item.background(0)))
            item.setBackground(0, QBrush(QColor("#dcfce7")))
            item.setForeground(0, QColor("#15803d"))
            curr = item.parent()
            while curr:
                curr.setExpanded(True)
                curr = curr.parent()

        self.dom_search_index = 0
        self.highlight_current_dom_match()

    def highlight_current_dom_match(self) -> None:
        if not self.dom_search_matches:
            self.lbl_dom_search_count.setText("0/0")
            return

        total = len(self.dom_search_matches)
        idx = self.dom_search_index % total
        self.dom_search_index = idx
        self.lbl_dom_search_count.setText(f"{idx + 1}/{total}")

        for i, item in enumerate(self.dom_search_matches):
            font = item.font(0)
            if i == idx:
                item.setBackground(0, QBrush(QColor("#4ade80")))
                item.setForeground(0, QColor("#052e16"))
                font.setBold(True)
                item.setFont(0, font)

                h_bar = self.tree_widget.horizontalScrollBar()
                h_val = h_bar.value()
                self.tree_widget.blockSignals(True)
                self.tree_widget.setCurrentItem(item)
                self.tree_widget.blockSignals(False)
                self.tree_widget.scrollToItem(item, QAbstractItemView.ScrollHint.EnsureVisible)
                h_bar.setValue(h_val)

                node_id = item.data(0, Qt.ItemDataRole.UserRole)
                if node_id:
                    self._apply_selected_node(node_id)
            else:
                item.setBackground(0, QBrush(QColor("#dcfce7")))
                item.setForeground(0, QColor("#15803d"))
                if font.bold():
                    font.setBold(False)
                    item.setFont(0, font)

    def on_dom_search_next(self) -> None:
        if not self.dom_search_matches:
            return
        self.dom_search_index = (self.dom_search_index + 1) % len(self.dom_search_matches)
        self.highlight_current_dom_match()

    def on_dom_search_prev(self) -> None:
        if not self.dom_search_matches:
            return
        self.dom_search_index = (self.dom_search_index - 1) % len(self.dom_search_matches)
        self.highlight_current_dom_match()

    # ------------------------------------------------------------------
    # 工具栏动作与节点联动（含去重、属性表原地复用）
    # ------------------------------------------------------------------
    def switch_mode(self, mode: str) -> None:
        is_sel = mode == InspectorMode.SELECT
        self.btn_mode_select.setChecked(is_sel)
        self.btn_mode_tap.setChecked(not is_sel)
        self.btn_mode_select.setIcon(get_tech_icon("target", "#ffffff" if is_sel else "#475569"))
        self.btn_mode_tap.setIcon(get_tech_icon("tap", "#ffffff" if not is_sel else "#475569"))
        self.canvas.set_mode(mode)

    def copy_xml_source(self) -> None:
        if self.xml_root is not None:
            xml_str = ET.tostring(self.xml_root, encoding="utf-8").decode("utf-8")
            QApplication.clipboard().setText(xml_str)
            self.show_toast("✅ XML 源码已复制到剪贴板！", duration_ms=1000)

    def save_screenshot(self) -> None:
        """保存当前画布画面（同时兼容静态底图 QPixmap 与实时投屏直通帧 QImage）"""
        has_img = self.canvas.screen_image is not None and not self.canvas.screen_image.isNull()
        has_pix = self.canvas.pixmap is not None and not self.canvas.pixmap.isNull()
        if not has_img and not has_pix:
            self.show_toast("⚠️ 当前暂无可保存的设备画面", duration_ms=1500)
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存真机截图", f"{self.current_platform}_screen.png", "PNG Images (*.png)")
        if path:
            if has_img and self.canvas.screen_image is not None:
                self.canvas.screen_image.save(path, "PNG")
            elif self.canvas.pixmap is not None:
                self.canvas.pixmap.save(path, "PNG")
            ModernMessageBox.information(self, "保存成功", f"截图已保存至:\n{path}")

    def open_search_dialog(self) -> None:
        if self.search_dialog is None:
            self.search_dialog = SearchElementDialog(
                self.flat_components,
                self.xml_root,
                comp_map=self.comp_map,
                platform=self.current_platform,
                parent=self,
            )
            self.search_dialog.element_picked.connect(self.select_element_by_id)
            self.search_dialog.tap_requested.connect(self.direct_tap_element)
            self.search_dialog.send_keys_requested.connect(self.direct_send_keys_to_element)
        else:
            self.search_dialog.update_context(
                self.flat_components,
                self.xml_root,
                comp_map=self.comp_map,
                platform=self.current_platform,
            )

        if self.search_dialog.isMinimized():
            self.search_dialog.showNormal()
        else:
            self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def _resize_long_attr_rows(self) -> None:
        """仅对超长/多行属性行按需测高，避免 45+ 短行全表换行排版风暴"""
        row_count = self.table_attrs.rowCount()
        for row in self._attr_long_rows:
            if 0 <= row < row_count:
                self.table_attrs.resizeRowToContents(row)

    def _apply_selected_node(self, node_id: str, force_panel: bool = False) -> None:
        """统一节点选中联动入口：基于 (node_id, comp对象ID, text) 精确去重"""
        if not node_id:
            return
        comp = self.comp_map.get(node_id)
        sig = (node_id, id(comp) if comp is not None else 0, str(comp.get("text", "")) if comp else "")
        if not force_panel and node_id == self.canvas.selected_node_id and sig == self._last_panel_sig:
            return

        self.canvas.selected_node_id = node_id
        self.canvas.hover_node_id = ""
        self.canvas.update()
        self.update_selected_element_panel(node_id)

        if self.search_dialog and self.search_dialog.isVisible() and comp:
            self.search_dialog.sync_element_from_main(comp)

    def select_element_by_id(self, node_id: str) -> None:
        item = self.tree_item_map.get(node_id)
        if item:
            h_bar = self.tree_widget.horizontalScrollBar()
            h_val = h_bar.value()
            self.tree_widget.blockSignals(True)
            self.tree_widget.setCurrentItem(item)
            self.tree_widget.blockSignals(False)
            self.tree_widget.scrollToItem(item, QTreeWidget.ScrollHint.EnsureVisible)
            h_bar.setValue(h_val)
        self._apply_selected_node(node_id)

    def on_canvas_element_selected(self, node_id: str) -> None:
        self.select_element_by_id(node_id)

    def on_toggle_show_occluded(self, state: int) -> None:
        self.apply_occluded_visibility_to_tree(self.chk_show_occluded.isChecked())

    def on_toggle_show_full_type(self, state: int) -> None:
        is_full = self.chk_show_full_type.isChecked()
        for node_id, item in self.tree_item_map.items():
            comp = self.comp_map.get(node_id)
            if comp:
                item.setText(0, format_dom_node_label(self.current_platform, comp, is_full_type=is_full))

    def apply_occluded_visibility_to_tree(self, show_occluded: bool) -> None:
        _apply_occluded_visibility_to_tree(self.tree_widget, show_occluded)
        if self.dom_search_bar.isVisible() and self.edit_dom_search.text().strip():
            self.on_dom_search_text_changed(self.edit_dom_search.text())

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        h_bar = self.tree_widget.horizontalScrollBar()
        h_val = h_bar.value()
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self._apply_selected_node(node_id)
        h_bar.setValue(h_val)

    def on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        if not item:
            return
        h_bar = self.tree_widget.horizontalScrollBar()
        h_val = h_bar.value()
        self.tree_widget.blockSignals(True)
        self.tree_widget.setCurrentItem(item)
        item.setSelected(True)
        self.tree_widget.blockSignals(False)
        h_bar.setValue(h_val)

        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self._apply_selected_node(node_id)

    def on_tree_current_item_changed(
        self,
        current: Optional[QTreeWidgetItem],
        previous: Optional[QTreeWidgetItem],
    ) -> None:
        if not current:
            return
        node_id = current.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self._apply_selected_node(node_id)

    def _sync_after_device_action(self, delay_ms: int = 300) -> None:
        def _do_sync() -> None:
            if not self.current_udid:
                return
            if self.is_screencasting:
                if self.current_platform == "ios":
                    wda_ok, _ = IosWdaManager.get_wda_url(self.current_udid, allow_spawn=False)
                    if not wda_ok:
                        return
                self.refresh_screen_and_dom()
            else:
                self.refresh_screen_only()

        QTimer.singleShot(delay_ms, _do_sync)

    def on_canvas_coordinate_tapped(self, x: int, y: int) -> None:
        if self.current_udid:
            DeviceController.tap(self.current_platform, self.current_udid, x, y)
            self._sync_after_device_action(delay_ms=300)

    def on_canvas_coordinate_swiped(self, x1: int, y1: int, x2: int, y2: int) -> None:
        if self.current_udid:
            DeviceController.swipe(self.current_platform, self.current_udid, x1, y1, x2, y2, 600)
            self._sync_after_device_action(delay_ms=350)

    def update_selected_element_panel(self, node_id: str) -> None:
        """就地复用属性表单元格、缓存 QSS/显隐状态并仅对长文本行按需测高"""
        comp = self.comp_map.get(node_id)
        if not comp:
            return
        self._last_panel_sig = (node_id, id(comp), str(comp.get("text", "")))

        c_type = comp.get("type", "")
        c_text = comp.get("text", "")

        if self.edit_live_input.text() != c_text:
            self.edit_live_input.blockSignals(True)
            self.edit_live_input.setText(c_text)
            self.edit_live_input.blockSignals(False)

        is_input_or_text = (
            c_type in ("TextInput", "TextArea", "Search", "Text", "RichText", "Span", "TextField", "SecureTextField")
            or any(k in c_type.lower() for k in ("input", "edit", "text", "search", "field"))
            or bool(c_text and c_text.strip())
        )
        if self.input_sync_box.isVisible() != is_input_or_text:
            self.input_sync_box.setVisible(is_input_or_text)

        path_str = comp.get("xpath", "Hierarchy").replace("/", "  ›  ")
        scheme = get_dom_tag_color(c_type)
        self.lbl_breadcrumb.setText(f"📍 路径: {path_str}")
        new_bc_style = (
            f"background-color: {scheme['bg']}; color: {scheme['text']}; "
            f"border: 1px solid {scheme['border']}; border-radius: 6px; padding: 4px 8px; font-weight: 600;"
        )
        if new_bc_style != self._last_breadcrumb_style:
            self._last_breadcrumb_style = new_bc_style
            self.lbl_breadcrumb.setStyleSheet(new_bc_style)

        self.txt_loc_id.setText(comp.get("rec_id", ""))
        self.txt_loc_xpath.setText(comp.get("rec_xpath", ""))
        self.txt_loc_py.setText(comp.get("rec_py", ""))
        self.txt_loc_predicate.setText(comp.get("rec_predicate", ""))
        self.txt_loc_class_chain.setText(comp.get("rec_class_chain", ""))
        for field in (self.txt_loc_id, self.txt_loc_xpath, self.txt_loc_py, self.txt_loc_predicate, self.txt_loc_class_chain):
            field.setCursorPosition(0)

        raw = comp.get("raw") or comp.get("raw_attributes") or {}
        real_id_val = comp.get("id", "")
        dom_path_val = raw.get("dom_path", "")
        if real_id_val:
            id_show = real_id_val
        elif dom_path_val:
            id_show = f"(未显式声明 · 虚拟层级: {dom_path_val})"
        else:
            id_show = "-"

        full_type_val = comp.get("full_type") or comp.get("rec_class") or c_type
        display_attrs = [
            ("原生全类名 (Full Type)", full_type_val),
            ("精炼类型 (Type)", c_type),
            ("id / name / key", id_show),
            ("text / label / value", comp.get("text", "-")),
            ("Predicate (iOS谓词)", comp.get("rec_predicate", "-")),
            ("Class Chain (iOS类链)", comp.get("rec_class_chain", "-")),
            ("bounds (坐标范围)", f"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]"),
            ("size (尺寸宽高)", f"{comp['width']} × {comp['height']}"),
            ("clickable (可点击)", str(raw.get("clickable", "-"))),
            ("enabled (可用状态)", str(raw.get("enabled", "-"))),
            ("focusable (可获焦点)", str(raw.get("focusable", "-"))),
            ("focused (当前聚焦)", str(raw.get("focused", "-"))),
            ("scrollable (可滚动)", str(raw.get("scrollable", "-"))),
            ("visible (可见性)", str(raw.get("visible", "-"))),
            ("xpath (完整绝对路径)", comp.get("xpath", "-")),
        ]

        known_keys = {
            "id", "key", "text", "originalText", "type", "full_type", "bounds",
            "bundleName", "clickable", "enabled", "focusable", "focused", "scrollable", "visible",
        }
        for k, v in raw.items():
            if k not in known_keys:
                display_attrs.append((f"raw: {k}", str(v)))

        hl_keywords = ("Full Type", "Type", "id", "text", "Predicate", "Class Chain", "xpath", "bounds", "size")
        long_rows: List[int] = []
        default_row_h = 28

        self.table_attrs.setUpdatesEnabled(False)
        self.table_attrs.setRowCount(len(display_attrs))
        for row, (k, v) in enumerate(display_attrs):
            k_str = str(k)
            v_str = str(v)

            k_item = self.table_attrs.item(row, 0)
            if k_item is None:
                k_item = QTableWidgetItem(k_str)
                self.table_attrs.setItem(row, 0, k_item)
            elif k_item.text() != k_str:
                k_item.setText(k_str)

            v_item = self.table_attrs.item(row, 1)
            if v_item is None:
                v_item = QTableWidgetItem(v_str)
                self.table_attrs.setItem(row, 1, v_item)
            elif v_item.text() != v_str:
                v_item.setText(v_str)
            v_item.setToolTip(v_str)

            if any(key in k_str for key in hl_keywords):
                k_item.setForeground(self._attr_key_hl_color)
                v_item.setForeground(self._attr_val_hl_color)
                k_item.setFont(self._attr_key_bold_font)
            else:
                k_item.setForeground(self._attr_key_norm_color)
                v_item.setForeground(self._attr_val_norm_color)
                k_item.setFont(self._attr_key_norm_font)

            if len(v_str) > 26 or "\n" in v_str:
                long_rows.append(row)
            elif self.table_attrs.rowHeight(row) != default_row_h:
                self.table_attrs.setRowHeight(row, default_row_h)

        self._attr_long_rows = long_rows
        for row in long_rows:
            self.table_attrs.resizeRowToContents(row)
        self.table_attrs.setUpdatesEnabled(True)

    # ------------------------------------------------------------------
    # 实时输入同步
    # ------------------------------------------------------------------
    def sync_live_input(self) -> None:
        curr_id = self.canvas.selected_node_id
        if not curr_id:
            ModernMessageBox.information(self, "提示", "请先在左侧或 DOM 树中选择目标输入框/编辑框组件！")
            return
        self.direct_send_keys_to_element(curr_id, self.edit_live_input.text())

    def direct_tap_element(self, node_id: str) -> None:
        comp = self.comp_map.get(node_id)
        if comp and self.current_udid:
            DeviceController.tap(self.current_platform, self.current_udid, comp["center_x"], comp["center_y"])
            self._sync_after_device_action(delay_ms=300)

    def direct_send_keys_to_element(self, node_id: str, text: str) -> None:
        comp = self.comp_map.get(node_id)
        if not comp or not self.current_udid:
            return

        DeviceController.input_text(self.current_platform, self.current_udid, text, comp["center_x"], comp["center_y"])

        comp["text"] = text
        if "raw_attributes" in comp:
            comp["raw_attributes"]["text"] = text
            comp["raw_attributes"]["originalText"] = text

        c_type = comp.get("type", "Component")
        full_type = comp.get("full_type") or comp.get("rec_class") or c_type
        c_id = comp.get("id", "")
        if self.current_platform == "android":
            if c_id:
                rec_xpath = f"//*[@resource-id='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
            elif text:
                rec_xpath = f"//{full_type}[@text='{text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{full_type}[@text='{text}']\")"
            else:
                rec_xpath = comp.get("xpath", "")
                rec_py = f'driver.find_element(AppiumBy.XPATH, "{rec_xpath}")'
        elif self.current_platform == "ios":
            if c_id:
                rec_xpath = f"//{full_type}[@name='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ACCESSIBILITY_ID, '{c_id}')"
            elif text:
                rec_xpath = f"//{full_type}[@label='{text}']"
                rec_py = f"driver.find_element(AppiumBy.IOS_PREDICATE, 'type == \"{full_type}\" AND label == \"{text}\"')"
            else:
                rec_xpath = comp.get("xpath", "")
                rec_py = f'driver.find_element(AppiumBy.XPATH, "{rec_xpath}")'
        else:
            if c_id:
                rec_xpath = f"//{c_type}[@id='{c_id}']"
                rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
            elif text:
                rec_xpath = f"//{c_type}[@text='{text}']"
                rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{c_type}[@text='{text}']\")"
            else:
                rec_xpath = comp.get("xpath", "")
                rec_py = f'driver.find_element(AppiumBy.XPATH, "{rec_xpath}")'

        comp["rec_xpath"] = rec_xpath
        comp["rec_py"] = rec_py

        item = self.tree_item_map.get(node_id)
        if item:
            item.setText(0, format_dom_node_label(self.current_platform, comp, is_full_type=self.chk_show_full_type.isChecked()))

        self.update_selected_element_panel(node_id)
        if self._is_screencast_locked():
            self.refresh_screen_and_dom()
        else:
            self.refresh_screen_only()

    def action_element_clear(self) -> None:
        curr_id = self.canvas.selected_node_id
        comp = self.comp_map.get(curr_id)
        if comp and self.current_udid:
            DeviceController.clear_text(self.current_platform, self.current_udid, comp["center_x"], comp["center_y"])
            comp["text"] = ""
            if "raw_attributes" in comp:
                comp["raw_attributes"]["text"] = ""
                comp["raw_attributes"]["originalText"] = ""
            self.edit_live_input.setText("")
            self.update_selected_element_panel(curr_id)
            if self._is_screencast_locked():
                self.refresh_screen_and_dom()
            else:
                self.refresh_screen_only()

    def copy_to_clip(self, text: str) -> None:
        if text:
            QApplication.clipboard().setText(text)
            short_preview = text if len(text) <= 32 else text[:32] + "..."
            self.show_toast(f"✅ 已复制: {short_preview}", duration_ms=1000)

    def show_toast(self, message: str, duration_ms: int = 1000) -> None:
        if not hasattr(self, "toast") or self.toast is None:
            self.toast = ToastNotification(self)
        self.toast.show_message(message, duration_ms)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "toast") and self.toast and self.toast.isVisible():
            parent_rect = self.rect()
            self.toast.move(
                (parent_rect.width() - self.toast.width()) // 2,
                (parent_rect.height() - self.toast.height()) // 2,
            )

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            if not self.isMinimized() and self.search_dialog and self.search_dialog.isVisible() and not self.search_dialog.isMinimized():
                self.search_dialog.raise_()
        elif event.type() == QEvent.Type.ActivationChange:
            if self.search_dialog and self.search_dialog.isVisible():
                self.search_dialog._update_stay_on_top_state()
        super().changeEvent(event)

    def closeEvent(self, event) -> None:
        if self.screencast_worker is not None:
            try:
                self.screencast_worker.stop()
                self.screencast_worker.wait(500)
            except Exception:
                pass
        if self.search_dialog:
            self.search_dialog.close()
        super().closeEvent(event)


def main() -> None:
    """独立启动 UI 审查器入口"""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("santiao.im.autotest.harmony.inspector")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setWindowIcon(create_modern_app_icon())
    window = HarmonyAppiumInspector()
    window.show()
    sys.exit(app.exec())
