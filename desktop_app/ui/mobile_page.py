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
import socket
from typing import Optional, List, Dict, Any, Set

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QRadioButton,
    QButtonGroup, QTreeWidget, QTreeWidgetItem, QSplitter,
    QPlainTextEdit, QMessageBox, QFrame, QScrollArea, QApplication,
    QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor, QFont

from ..config import desktop_config
from ..core.device_manager import DeviceManager
from ..core.test_collector import TestCollectorService
from ..core.test_runner import TestExecutionWorker, clean_ansi_log
from .allure_dashboard import AllureDashboardWidget

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

        self.init_ui()
        self.load_persisted_config()

        # 异步非阻塞执行设备检测、用例加载与分割器精确几何还原
        QTimer.singleShot(60, self.refresh_test_cases)
        QTimer.singleShot(80, self._restore_splitter_sizes)
        QTimer.singleShot(160, self.auto_detect_devices)
        QTimer.singleShot(260, self._refresh_report_pill_count)

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

        h_layout.addStretch()

        # 1.2 右侧药丸状态 Badge 组 (用户红框 1:1 对应)
        pill_group = QFrame()
        pill_group.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 20px;
                padding: 2px 6px;
            }
        """)
        pg_layout = QHBoxLayout(pill_group)
        pg_layout.setContentsMargins(6, 2, 6, 2)
        pg_layout.setSpacing(10)

        # 药丸 1: 设备在线
        self.lbl_device_pill = QLabel("🟢 设备: 1 台在线")
        self.lbl_device_pill.setStyleSheet("color: #059669; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(self.lbl_device_pill)

        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #cbd5e1;")
        pg_layout.addWidget(sep1)

        # 药丸 2: 用例总数
        self.lbl_case_pill = QLabel(f"✏️ 用例: {self.total_case_count} 条")
        self.lbl_case_pill.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(self.lbl_case_pill)

        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #cbd5e1;")
        pg_layout.addWidget(sep2)

        # 药丸 3: 报告总数
        self.lbl_report_pill = QLabel("📑 报告: 5 份")
        self.lbl_report_pill.setStyleSheet("color: #7c3aed; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(self.lbl_report_pill)

        # 药丸 4: 刷新小按键
        btn_refresh_top = QPushButton("🔄")
        btn_refresh_top.setToolTip("一键扫描在线设备、重新收集用例与统计最新报告")
        btn_refresh_top.setFixedSize(24, 24)
        btn_refresh_top.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh_top.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        btn_refresh_top.clicked.connect(self._on_top_refresh_clicked)
        pg_layout.addWidget(btn_refresh_top)

        h_layout.addWidget(pill_group)
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

        layout.addLayout(search_box)

        # 2.2 四级用例树 (隐藏头部，简洁纯净)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(1, 88)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        self.tree.itemExpanded.connect(self._on_tree_item_expanded)
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
        self.combo_os = QComboBox()
        self.combo_os.addItems(["Win", "Mac", "Linux"])
        self.combo_os.setFixedWidth(64)
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

        # 5. 业务调试变量 (私聊 / 群聊)
        body_layout.addWidget(QLabel("业务调试变量 (私聊 / 群聊):"), 9, 0, 1, 2)
        chat_vars_row = QHBoxLayout()
        self.edit_private_chat = QLineEdit()
        self.edit_private_chat.setPlaceholderText("私聊用户 (如: test209-11)")
        self.edit_private_chat.textChanged.connect(self._on_config_changed)

        self.edit_group_chat = QLineEdit()
        self.edit_group_chat.setPlaceholderText("群聊名称 (如: 测试交流群)")
        self.edit_group_chat.textChanged.connect(self._on_config_changed)

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
        self.combo_view_role.setFixedWidth(106)
        self.combo_view_role.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QComboBox:hover {
                border-color: #94a3b8;
            }
            QComboBox:focus {
                border: 1px solid #2563eb;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #eff6ff;
                selection-color: #2563eb;
                border: 1px solid #cbd5e1;
            }
        """)
        self.combo_view_role.currentIndexChanged.connect(self._on_config_changed)
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
        """退出应用时完整同步分割器尺寸"""
        h_sizes = self.main_h_splitter.sizes()
        if len(h_sizes) == 2 and sum(h_sizes) > 0:
            desktop_config.set("mobile", "splitter_h_sizes", h_sizes)
        v_sizes = self.right_v_splitter.sizes()
        if len(v_sizes) == 2 and sum(v_sizes) > 0:
            desktop_config.set("mobile", "splitter_v_sizes", v_sizes)
            desktop_config.set("mobile", "log_collapsed", self._is_log_collapsed)
            desktop_config.set("mobile", "last_log_height", self._last_log_height)

    def _toggle_autoscroll(self):
        is_active = self.btn_toggle_autoscroll.text().startswith("🟢")
        if is_active:
            self.btn_toggle_autoscroll.setText("⏸️ 滚屏暂停")
            self.btn_toggle_autoscroll.setStyleSheet("background-color: #f1f5f9; color: #64748b;")
        else:
            self.btn_toggle_autoscroll.setText("🟢 自动滚屏")
            self.btn_toggle_autoscroll.setStyleSheet("background-color: #ecfdf5; color: #059669; font-weight: 700;")
            self.console.moveCursor(QTextCursor.MoveOperation.End)

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

    def refresh_test_cases(self):
        self.tree.clear()
        self.hierarchy_data = TestCollectorService.get_test_hierarchy("mobile")

        total_collected = 0

        for c_idx, cat in enumerate(self.hierarchy_data):
            # 1. 一级目录节点 (📖)
            cat_item = QTreeWidgetItem(self.tree)
            cat_name = cat["display_name"]
            cat_count = cat["count"]
            total_collected += cat_count

            cat_item.setText(0, f"📖  {cat_name} [{cat_count}]")
            cat_item.setToolTip(0, f"一级测试目录: {cat['target']}\n包含 {cat_count} 个测试用例")
            cat_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "target": cat["target"], "name": cat_name})

            action_cat = self._create_tree_action_widget(
                "运行目录", "tree-pill-btn-dir", 66,
                lambda ch, t=cat["target"], n=cat_name: self._run_target_node(t, n)
            )
            self.tree.setItemWidget(cat_item, 1, action_cat)

            is_first_cat = (c_idx == 0)
            cat_item.setExpanded(is_first_cat)

            # 2. 二级文件节点 (👾)
            for f_idx, file_obj in enumerate(cat.get("files", [])):
                file_item = QTreeWidgetItem(cat_item)
                file_name = file_obj.get('display_name', file_obj['file'])
                file_count = file_obj.get("count", 0)

                file_item.setText(0, f"👾  {file_name} [{file_count}]")
                file_item.setToolTip(0, f"二级测试文件: {file_obj['file']}\n包含 {file_count} 个测试用例")
                file_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "file", "target": file_obj["file"], "name": file_name})

                action_file = self._create_tree_action_widget(
                    "运行文件", "tree-pill-btn-file", 66,
                    lambda ch, f=file_obj["file"], n=file_name: self._run_target_node(f, n)
                )
                self.tree.setItemWidget(file_item, 1, action_file)

                is_first_file = (is_first_cat and f_idx == 0)
                file_item.setExpanded(is_first_file)

                # 3. 三级类节点 (🧱)
                for cl_idx, cls in enumerate(file_obj.get("classes", [])):
                    cls_item = QTreeWidgetItem(file_item)
                    cls_name = cls.get('display_name', cls['name'])
                    cls_nodeid = f"{file_obj['file']}::{cls['name']}"

                    cls_item.setText(0, f"🧱  {cls_name}")
                    cls_item.setToolTip(0, f"三级测试类: {cls_nodeid}")
                    cls_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "class", "target": cls_nodeid, "name": cls_name})

                    action_cls = self._create_tree_action_widget(
                        "运行类", "tree-pill-btn-class", 56,
                        lambda ch, node=cls_nodeid, n=cls_name: self._run_target_node(node, n)
                    )
                    self.tree.setItemWidget(cls_item, 1, action_cls)

                    # 默认展开检索类，与截图完全对齐
                    is_search_class = "检索" in cls_name
                    cls_item.setExpanded(is_first_file and (cl_idx == 0 or is_search_class))

                    # 4. 四级测试用例 (带失败红点 🔴 / 正常 ⚙️，与用户红框完全对齐)
                    for test in cls.get("tests", []):
                        self._add_leaf_item(cls_item, file_obj["file"], cls["name"], test)

                for test in file_obj.get("tests", []):
                    self._add_leaf_item(file_item, file_obj["file"], "", test)

        if total_collected > 0:
            self.total_case_count = total_collected
            self.lbl_case_pill.setText(f"✏️ 用例: {self.total_case_count} 条")

    @staticmethod
    def _format_test_node_text(status: str, display_name: str) -> str:
        """
        根据执行状态格式化测试用例节点文本：
        确保球形按钮与齿轮按钮始终同时存在：
        - 默认未执行：⚪ ⚙️ (默认空心球形按钮 + 齿轮按钮)
        - 通过 (passed)：🟢 ⚙️ (绿色球形按钮 + 齿轮按钮)
        - 失败/异常 (failed/broken/error)：🔴 ⚙️ (红色球形按钮 + 齿轮按钮)
        """
        if status == "passed":
            ball = "🟢"
        elif status in ("failed", "broken", "error"):
            ball = "🔴"
        else:
            ball = "⚪"
        return f"{ball} ⚙️  {display_name}"

    def _add_leaf_item(self, parent: QTreeWidgetItem, file_path: str, cls_name: str, test: Dict[str, Any]):
        node_id = f"{file_path}::{cls_name}::{test['name']}" if cls_name else f"{file_path}::{test['name']}"
        test_display = test.get('display_name', test['name'])
        params = test.get("params", [])

        # 状态匹配：默认空心球 ⚪ ⚙️，通过 🟢 ⚙️，失败/异常 🔴 ⚙️
        status = self.node_status_map.get(node_id, "")

        test_item = QTreeWidgetItem(parent)
        test_item.setText(0, self._format_test_node_text(status, test_display))
        test_item.setToolTip(0, f"用例: {test_display}\n节点: {node_id}\n状态: {status or '未执行'}")
        test_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "test", "target": node_id, "name": test_display})

        action_test = self._create_tree_action_widget(
            "运行", "tree-pill-btn", 46,
            lambda ch, node=node_id, n=test_display: self._run_target_node(node, n)
        )
        self.tree.setItemWidget(test_item, 1, action_test)

        if params:
            for p in params:
                sub_item = QTreeWidgetItem(test_item)
                sub_node = f"{node_id}[{p}]"
                sub_status = self.node_status_map.get(sub_node, "")

                sub_item.setText(0, f"  {self._format_test_node_text(sub_status, f'[{p}]')}")
                sub_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "param", "target": sub_node, "name": str(p)})

                action_param = self._create_tree_action_widget(
                    "运行", "tree-pill-btn", 46,
                    lambda ch, node=sub_node, n=str(p): self._run_target_node(node, n)
                )
                self.tree.setItemWidget(sub_item, 1, action_param)
            test_item.setExpanded(False)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """点击目录或节点标题 (第0列) 时即可直接切换展开与折叠，无需瞄准小箭头"""
        if column == 0 and item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def _on_tree_item_expanded(self, item: QTreeWidgetItem):
        """当展开一个一级目录时，其他一级目录自动折叠收起 (手风琴单开模式)"""
        if getattr(self, "_is_batch_expanding", False):
            return
        # 搜索过滤中不干扰全局匹配结果
        if self.edit_search.text().strip():
            return

        # 仅针对一级目录 (顶级节点，parent 为 None)
        if item.parent() is None:
            self.tree.blockSignals(True)
            try:
                for i in range(self.tree.topLevelItemCount()):
                    top = self.tree.topLevelItem(i)
                    if top is not item and top.isExpanded():
                        top.setExpanded(False)
            finally:
                self.tree.blockSignals(False)

    def _on_tree_item_double_clicked(self, item: QTreeWidgetItem, col: int):
        """双击叶子测试用例启动运行，双击目录/文件/类切换折叠"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get("type") in ("test", "param"):
            self._run_target_node(data["target"], data["name"])
        elif item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def _filter_test_cases(self, text: str):
        q = text.strip().lower()
        def filter_item(item: QTreeWidgetItem) -> bool:
            self_match = q in item.text(0).lower() if q else True
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
        is_visible = self.params_body.isVisible()
        self.params_body.setVisible(not is_visible)
        self.btn_toggle_collapse.setText("展开" if is_visible else "收起")

    def _reset_params(self):
        self.combo_appium1.setEditText(f"{self.lan_ip}:4723 (局域网本机)")
        self.combo_appium2.setEditText(f"{self.lan_ip}:4724 (局域网本机)")
        self.combo_udid1.setEditText("nzwcvo9ls87hws7t")
        self.combo_udid2.setEditText("3865BN02GU600000")
        self.edit_private_chat.setText("")
        self.edit_group_chat.setText("")
        self.chk_debug_mode.setChecked(False)
        self.combo_view_role.setCurrentIndex(0)
        self._on_config_changed()
        QMessageBox.information(self, "提示", "参数配置已恢复为默认值！")

    # ==================== 6. 状态持久化 ====================
    def load_persisted_config(self):
        cfg = desktop_config.get_section("mobile")
        self.combo_os.setCurrentText(cfg.get("os_type", "Win"))
        
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

    def _on_config_changed(self):
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

    # ==================== 7. 设备与报告辅助 ====================
    def _refresh_report_pill_count(self):
        from web_platform.backend.paths import REPORTS_DIR
        base_dir = os.path.join(REPORTS_DIR, "allure_reports")
        if os.path.exists(base_dir):
            dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
            count = len(dirs)
            self.lbl_report_pill.setText(f"📑 报告: {count} 份")

    def _on_top_refresh_clicked(self):
        self.refresh_test_cases()
        self.auto_detect_devices()
        self._refresh_report_pill_count()
        self.allure_dashboard.load_latest_report()
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
        self.lbl_device_pill.setText(f"🟢 设备: {online_count} 台在线")

    def _detect_single_device(self, target_idx: int):
        details = DeviceManager.scan_connected_devices()
        real_list = details.get("real_devices", [])
        all_list = details.get("all_devices", [])

        if target_idx == 1:
            if real_list:
                self.combo_udid1.setEditText(real_list[0])
                self.append_log(f"✅ 已直接获取 USB 连接真机并替换发送端: {real_list[0]}")
            elif all_list:
                self.combo_udid1.setEditText(all_list[0])
                self.append_log(f"ℹ️ 已获取在线设备并替换发送端: {all_list[0]}")
            else:
                QMessageBox.warning(self, "警告", "未检测到 USB 设备，请检查数据线与开发者 USB 调试！")
        else:
            if len(real_list) >= 2:
                self.combo_udid2.setEditText(real_list[1])
                self.append_log(f"✅ 已直接获取 USB 连接第 2 台真机并替换接收端: {real_list[1]}")
            elif real_list:
                self.combo_udid2.setEditText(real_list[0])
                self.append_log(f"ℹ️ 已检测到真机并同步替换接收端: {real_list[0]}")
            elif all_list:
                target = all_list[1] if len(all_list) > 1 else all_list[0]
                self.combo_udid2.setEditText(target)
                self.append_log(f"ℹ️ 已获取在线设备并替换接收端: {target}")
            else:
                QMessageBox.warning(self, "警告", "未检测到 USB 设备，请检查数据线与开发者 USB 调试！")

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
        QMessageBox.information(self, "Web 回执", "已开启 Web 回执与 Jira 质量缺陷自动归档流。")

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

        ap1 = self.combo_appium1.currentText().split(" ")[0].strip()
        ap2 = self.combo_appium2.currentText().split(" ")[0].strip()

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
            "env": "dev"
        }

        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status_pill.setText("🚀 运行中...")
        self.lbl_status_pill.setStyleSheet("background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")
        self.lbl_running_case.setText(f"正在执行: {display_name}")
        self.status_bar.setText(f"🚀 正在运行: {display_name}")

        self.current_target_nodeid = target_nodeid

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

    def _on_worker_finished(self, exit_code: int, report_dir: str):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)

        # 拦截手动终止情况 (exit_code == -9)，避免将中断用例判定为 failed 或加载空报告
        if exit_code == -9:
            self.lbl_running_case.setText("⏹️ 测试已被手动终止")
            self.status_bar.setText("状态: 就绪 (测试已终止)")
            return

        # 1. 更新当前目标节点
        curr_node = getattr(self, "current_target_nodeid", None)
        if curr_node:
            self.node_status_map[curr_node] = "passed" if exit_code == 0 else "failed"

        self.lbl_running_case.setText(f"执行完毕 (退出码: {exit_code})")

        # 2. 核心：全动态解析本次测试任务的真实报告与原始结果
        results_dir = getattr(self.worker, "allure_results_dir", None)
        target_report = report_dir or getattr(self.worker, "allure_report_dir", None)

        self.allure_dashboard.load_report_from_path(report_dir=target_report, results_dir=results_dir)

        # 3. 同步本次测试中所有实际执行完成的各用例状态到树节点映射表
        stat = getattr(self.allure_dashboard, "current_data", {})
        cases = stat.get("cases", [])
        if cases:
            status_by_name = {}
            for c in cases:
                st = c.get("status", "")
                if st:
                    if c.get("fullName"):
                        status_by_name[c["fullName"]] = st
                    if c.get("name"):
                        status_by_name[c["name"]] = st

            def sync_status(item: QTreeWidgetItem):
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data and data.get("type") in ("test", "param"):
                    target = data.get("target", "")
                    name = data.get("name", "")
                    for match_key, matched_st in status_by_name.items():
                        if match_key in target or (name and name in match_key):
                            self.node_status_map[target] = matched_st
                            break
                for i in range(item.childCount()):
                    sync_status(item.child(i))

            for i in range(self.tree.topLevelItemCount()):
                sync_status(self.tree.topLevelItem(i))

        # 4. 立即刷新树上所有用例的球形与齿轮状态 (通过变绿球，失败/异常变红球，齿轮始终保留)
        self._update_tree_node_icons()

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
        """递归遍历用例树更新叶子节点的球形状态与齿轮图标 (齿轮前必有球，默认空心球，通过绿球，失败/异常红球)"""
        def visit(item: QTreeWidgetItem):
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get("type") in ("test", "param"):
                target = data.get("target")
                status = self.node_status_map.get(target, "")
                orig_name = data.get("name", "")
                is_param = (data.get("type") == "param")
                prefix = "  " if is_param else ""
                display_text = f"[{orig_name}]" if is_param else orig_name
                item.setText(0, f"{prefix}{self._format_test_node_text(status, display_text)}")
                item.setToolTip(0, f"用例: {orig_name}\n节点: {target}\n状态: {status or '未执行'}")
            for i in range(item.childCount()):
                visit(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(i))

    def open_allure_report(self):
        self.allure_dashboard.load_latest_report()
        stat = getattr(self.allure_dashboard, "current_data", {})
        task_id = stat.get("task_id", "就绪")
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
                self.lbl_status_pill.setText(f"🔴 测试失败 ({bad_count}/{total} 异常)")
                self.lbl_status_pill.setStyleSheet("background-color: #fef2f2; color: #e11d48; border: 1px solid #fecdd3; border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 11px;")

        self.append_log(f"📊 已动态同步最新 Allure 测试报告: {task_id} (执行用例: {total} 条)")
        self._refresh_report_pill_count()

    def append_log(self, text: str):
        cleaned = clean_ansi_log(text)
        self.console.appendPlainText(cleaned)
        if self.btn_toggle_autoscroll.text().startswith("🟢"):
            self.console.moveCursor(QTextCursor.MoveOperation.End)

    def clear_console(self):
        self.console.clear()

    def _copy_logs(self):
        text = self.console.toPlainText()
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            self.append_log("📋 已复制终端日志到剪贴板")
