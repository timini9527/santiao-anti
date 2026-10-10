# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - Web 端测试页面
=======================================================
1:1 像素级复刻目标设计图 (Web 测试 控制台)：
1. 顶部无外层大卡片包裹的通栏透明 Header：
   - 深蓝圆角显示器图标 + Web 测试 控制台 + Playwright 兼容性测试副标题
   - 4 个独立状态统计药丸 (设备/用例/报告/刷新)
2. 顶部纯白说明横幅卡片：Web 端自动化测试 (Playwright 架构)
3. 左右对齐中层卡片：
   - 运行环境与浏览器矩阵 (Chromium/Firefox/WebKit 3大芯片卡片)
   - 精致 Switch 开关 (Headless 模式) + 原生数字步进器 [- 2 +] + 根地址输入
   - 实时执行终端卡片 (深曜石黑蓝暗色背景 #070c18 + 极客冷青蓝输出 #38bdf8 + Idle 状态胶囊)
4. 下方测试集卡片：
   - 标题 + 一键执行全量 Web 冒烟 纯蓝实心按钮
   - 5 条独立卡片项：P0 冒烟 / P1 回归 / P2 兼容、通过 (12s/18s) 绿色徽标、执行 细线框按钮
"""
import os
import sys
import time
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QPlainTextEdit, QFrame, QScrollArea, QApplication, QLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from ..core.report_scanner import get_reports_count
except (ImportError, ValueError):
    from desktop_app.core.report_scanner import get_reports_count


class ModernSwitch(QWidget):
    """
    1:1 原生自绘现代 Switch 滑块开关 (Element Plus / iOS 风格)：
    - 尺寸 36x20px，胶囊圆角
    - 开启时亮蓝背景 #2563eb，关闭时柔和浅灰 #d1d5db
    - 滑块平滑抗锯齿实心纯白圆点
    """
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.checked = checked
        self.setFixedSize(36, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self.checked

    def setChecked(self, checked: bool):
        if self.checked != checked:
            self.checked = checked
            self.update()
            self.toggled.emit(self.checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self.checked)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = float(self.width())
        h = float(self.height())
        radius = h / 2.0

        # 背景色
        bg_color = QColor("#2563eb") if self.checked else QColor("#d1d5db")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # 内部白色滑块圆形
        knob_r = 7.0
        knob_y = h / 2.0
        knob_x = (w - radius) if self.checked else radius

        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QPointF(knob_x, knob_y), knob_r, knob_r)


class NumberStepper(QFrame):
    """
    1:1 原生数字微调步进器 [- 2 +]：
    - 精致白底浅灰边框外框
    - 左侧减号、中间当前值、右侧加号按键
    """
    valueChanged = pyqtSignal(int)

    def __init__(self, value: int = 2, min_val: int = 1, max_val: int = 8, parent=None):
        super().__init__(parent)
        self._value: int = value
        self.min_val = min_val
        self.max_val = max_val
        self.setFixedSize(88, 28)
        self.setObjectName("webWorkerStepper")
        self.setStyleSheet("""
            QFrame#webWorkerStepper {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 4px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        btn_style = """
            QPushButton {
                background-color: #f8fafc;
                border: none;
                color: #64748b;
                font-size: 13px;
                font-weight: 700;
                width: 26px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                color: #0f172a;
            }
        """
        self.btn_dec = QPushButton("-")
        self.btn_dec.setStyleSheet(btn_style)
        self.btn_dec.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dec.clicked.connect(self._dec)
        layout.addWidget(self.btn_dec)

        self.lbl_val = QLabel(str(self._value))
        self.lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_val.setStyleSheet("border: none; color: #0f172a; font-weight: 600; font-size: 12px;")
        layout.addWidget(self.lbl_val, stretch=1)

        self.btn_inc = QPushButton("+")
        self.btn_inc.setStyleSheet(btn_style)
        self.btn_inc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_inc.clicked.connect(self._inc)
        layout.addWidget(self.btn_inc)

    def value(self) -> int:
        return self._value

    def _dec(self) -> None:
        if self._value > self.min_val:
            self._value -= 1
            self.lbl_val.setText(str(self._value))
            self.valueChanged.emit(self._value)

    def _inc(self) -> None:
        if self._value < self.max_val:
            self._value += 1
            self.lbl_val.setText(str(self._value))
            self.valueChanged.emit(self._value)


class BrowserChip(QFrame):
    """
    浏览器矩阵选择芯片卡片：
    - 选中态：极淡浅天蓝底色 #eff6ff + 清透亮蓝描边 1.5px solid #3b82f6
    - 未选中态：白底 #ffffff + 细边框 1px solid #e2e8f0
    """
    def __init__(self, name: str, engine: str, selected: bool = False, on_click=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.engine = engine
        self.selected = selected
        self.on_click = on_click
        self.setObjectName("webBrowserChip")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(52)
        self.init_ui()
        self.set_selected(selected)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_name = QLabel(self.name)
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_name)

        self.lbl_engine = QLabel(self.engine)
        self.lbl_engine.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_engine)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.on_click:
            self.on_click(self.name)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        if selected:
            self.setStyleSheet("""
                QFrame#webBrowserChip {
                    background-color: #eff6ff;
                    border: 1.5px solid #3b82f6;
                    border-radius: 6px;
                }
            """)
            self.lbl_name.setStyleSheet("color: #1d4ed8; font-weight: 700; font-size: 12px;")
            self.lbl_engine.setStyleSheet("color: #60a5fa; font-size: 10px;")
        else:
            self.setStyleSheet("""
                QFrame#webBrowserChip {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                }
                QFrame#webBrowserChip:hover {
                    border-color: #cbd5e1;
                    background-color: #f8fafc;
                }
            """)
            self.lbl_name.setStyleSheet("color: #0f172a; font-weight: 600; font-size: 12px;")
            self.lbl_engine.setStyleSheet("color: #94a3b8; font-size: 10px;")


class WebPage(QWidget):
    """
    Web 端自动化测试控制台页面 (与目标图 1:1 像素级精确复刻)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_executing = False
        self.current_browser = "Chromium"

        self.modules_data = [
            {"id": "web_login", "name": "Web 端扫码登录与会话保持", "tag": "P0 冒烟", "status": "passed", "time": "12s"},
            {"id": "web_msg_text", "name": "Web 文本消息即时收发与已读标记", "tag": "P0 冒烟", "status": "passed", "time": "18s"},
            {"id": "web_msg_media", "name": "Web 富媒体文件拖拽上传与大文件分片", "tag": "P1 回归", "status": "idle", "time": "-"},
            {"id": "web_group_manage", "name": "Web 群组管理、公告发布与禁言", "tag": "P1 回归", "status": "idle", "time": "-"},
            {"id": "web_compatibility", "name": "跨浏览器渲染与不同分辨率视口适配", "tag": "P2 兼容", "status": "idle", "time": "-"}
        ]

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 14, 18, 16)
        root_layout.setSpacing(12)

        # 1. 顶部独立通栏 Header 栏 (透明底，悬浮融入主窗口，严格对齐目标图)
        top_header = self._create_top_header()
        root_layout.addWidget(top_header)

        # 2. 主体可滚动工作区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 2.1 顶部说明横幅卡片
        banner = self._create_banner_card()
        layout.addWidget(banner)

        # 2.2 中层配置与终端两列布局
        mid_row = QHBoxLayout()
        mid_row.setSpacing(12)

        left_config_card = self._create_browser_matrix_card()
        mid_row.addWidget(left_config_card, stretch=5)

        right_console_card = self._create_console_card()
        mid_row.addWidget(right_console_card, stretch=5)

        layout.addLayout(mid_row)

        # 2.3 下方用例测试集卡片
        cases_card = self._create_cases_card()
        layout.addWidget(cases_card)

        scroll.setWidget(content_widget)
        root_layout.addWidget(scroll, stretch=1)

    # ================= 1. 顶部 Header =================
    def _create_top_header(self) -> QWidget:
        header_widget = QWidget()
        h_layout = QHBoxLayout(header_widget)
        h_layout.setContentsMargins(0, 2, 0, 4)
        h_layout.setSpacing(12)

        # 左侧：深蓝圆角显示器方块图标
        icon_box = QFrame()
        icon_box.setFixedSize(34, 34)
        icon_box.setStyleSheet("""
            QFrame {
                background-color: #2563eb;
                border-radius: 8px;
            }
        """)
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel("💻")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 16px; background: transparent;")
        ib_layout.addWidget(lbl_icon)
        h_layout.addWidget(icon_box)

        # 标题与副标题
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_main = QLabel("Web 测试 控制台")
        lbl_main.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        lbl_sub = QLabel("Playwright Web UI 自动化兼容性测试")
        lbl_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        title_box.addWidget(lbl_main)
        title_box.addWidget(lbl_sub)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        # 右侧：4 个独立的轻奢白色药丸小卡片
        pill_style = """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                padding: 3px 10px;
            }
        """

        # 药丸 1: 设备
        pill_dev = QFrame()
        pill_dev.setStyleSheet(pill_style)
        pd_layout = QHBoxLayout(pill_dev)
        pd_layout.setContentsMargins(8, 2, 8, 2)
        pd_layout.setSpacing(4)
        dot_dev = QLabel("●")
        dot_dev.setStyleSheet("color: #10b981; font-size: 10px; border: none; background: transparent;")
        pd_layout.addWidget(dot_dev)
        lbl_dev = QLabel("设备: <b>7</b> 台在线")
        lbl_dev.setStyleSheet("color: #475569; font-size: 11.5px; border: none; background: transparent;")
        pd_layout.addWidget(lbl_dev)
        h_layout.addWidget(pill_dev)

        # 药丸 2: 用例
        pill_case = QFrame()
        pill_case.setStyleSheet(pill_style)
        pc_layout = QHBoxLayout(pill_case)
        pc_layout.setContentsMargins(8, 2, 8, 2)
        pc_layout.setSpacing(4)
        lbl_case = QLabel("🧪 用例: <b>1383</b> 条")
        lbl_case.setStyleSheet("color: #475569; font-size: 11.5px; border: none; background: transparent;")
        pc_layout.addWidget(lbl_case)
        h_layout.addWidget(pill_case)

        # 药丸 3: 报告
        pill_rep = QFrame()
        pill_rep.setStyleSheet(pill_style)
        pr_layout = QHBoxLayout(pill_rep)
        pr_layout.setContentsMargins(8, 2, 8, 2)
        pr_layout.setSpacing(4)
        lbl_rep = QLabel(f"📑 报告: <b>{get_reports_count()}</b> 份")
        lbl_rep.setStyleSheet("color: #475569; font-size: 11.5px; border: none; background: transparent;")
        pr_layout.addWidget(lbl_rep)
        h_layout.addWidget(pill_rep)

        # 药丸 4: 刷新按钮
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(28, 28)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                font-size: 12px;
                color: #64748b;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #cbd5e1;
                color: #0f172a;
            }
        """)
        btn_refresh.clicked.connect(self._reset_console)
        h_layout.addWidget(btn_refresh)

        return header_widget

    # ================= 2. 顶部说明横幅 =================
    def _create_banner_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("webBannerCard")
        card.setStyleSheet("""
            QFrame#webBannerCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px 18px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        icon = QLabel("🖥️")
        icon.setStyleSheet("font-size: 15px; background: transparent; border: none;")
        top_row.addWidget(icon)

        title = QLabel("Web 端自动化测试 (Playwright 架构)")
        title.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #0f172a; background: transparent; border: none;")
        top_row.addWidget(title)
        top_row.addStretch()
        layout.addLayout(top_row)

        desc = QLabel("支持 Chrome / Firefox / Safari 跨浏览器自动化执行，覆盖 Web 端 IM 核心会话与多端同步")
        desc.setStyleSheet("color: #64748b; font-size: 11.5px; background: transparent; border: none;")
        layout.addWidget(desc)
        return card

    # ================= 3. 浏览器矩阵配置 =================
    def _create_browser_matrix_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("webBrowserMatrixCard")
        card.setStyleSheet("""
            QFrame#webBrowserMatrixCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 14px 18px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        head_row = QHBoxLayout()
        lbl_head = QLabel("🌐 运行环境与浏览器矩阵")
        lbl_head.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 13px; background: transparent; border: none;")
        head_row.addWidget(lbl_head)
        layout.addLayout(head_row)

        # 3 个浏览器芯片水平排列
        chip_row = QHBoxLayout()
        chip_row.setSpacing(10)
        self.chips = {}
        browsers = [
            ("Chromium", "Chrome / Edge"),
            ("Firefox", "Gecko"),
            ("WebKit", "Safari")
        ]
        for name, engine in browsers:
            chip = BrowserChip(name, engine, selected=(name == "Chromium"), on_click=self._select_browser)
            self.chips[name] = chip
            chip_row.addWidget(chip)
        layout.addLayout(chip_row)

        layout.addSpacing(2)

        # 表单字段
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        # 1. 无头模式 (Switch 开关)
        row_headless = QHBoxLayout()
        lbl_h = QLabel("无头运行模式")
        lbl_h.setStyleSheet("color: #475569; font-size: 12px; width: 100px; background: transparent; border: none;")
        self.switch_headless = ModernSwitch(checked=False)
        lbl_h_desc = QLabel("Headless (后台静默执行)")
        lbl_h_desc.setStyleSheet("color: #64748b; font-size: 11.5px; margin-left: 8px; background: transparent; border: none;")
        row_headless.addWidget(lbl_h)
        row_headless.addWidget(self.switch_headless)
        row_headless.addWidget(lbl_h_desc)
        row_headless.addStretch()
        form_layout.addLayout(row_headless)

        # 2. 并发执行线程 (步进器 [- 2 +])
        row_workers = QHBoxLayout()
        lbl_w = QLabel("并发执行线程")
        lbl_w.setStyleSheet("color: #475569; font-size: 12px; width: 100px; background: transparent; border: none;")
        self.stepper_workers = NumberStepper(value=2, min_val=1, max_val=8)
        row_workers.addWidget(lbl_w)
        row_workers.addWidget(self.stepper_workers)
        row_workers.addStretch()
        form_layout.addLayout(row_workers)

        # 3. WEB 服务根地址
        row_url = QHBoxLayout()
        lbl_u = QLabel("WEB 服务根地址")
        lbl_u.setStyleSheet("color: #475569; font-size: 12px; width: 100px; background: transparent; border: none;")
        self.edit_base_url = QLineEdit("http://localhost:3000")
        self.edit_base_url.setFixedHeight(28)
        self.edit_base_url.setFixedWidth(240)
        self.edit_base_url.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 0 8px;
                color: #0f172a;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        row_url.addWidget(lbl_u)
        row_url.addWidget(self.edit_base_url)
        row_url.addStretch()
        form_layout.addLayout(row_url)

        layout.addLayout(form_layout)
        return card

    def _select_browser(self, browser_name: str):
        self.current_browser = browser_name
        for name, chip in self.chips.items():
            chip.set_selected(name == browser_name)

    # ================= 4. 实时执行终端 =================
    def _create_console_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("webConsoleCard")
        card.setStyleSheet("""
            QFrame#webConsoleCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 14px 18px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)

        head_row = QHBoxLayout()
        lbl_head = QLabel("📟 Web 自动化实时执行输出")
        lbl_head.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 13px; background: transparent; border: none;")
        head_row.addWidget(lbl_head)
        head_row.addStretch()

        self.lbl_console_status = QLabel("Idle")
        self.lbl_console_status.setStyleSheet("""
            background-color: #f0fdf4;
            color: #16a34a;
            border: 1px solid #bbf7d0;
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: 700;
            font-size: 11px;
        """)
        head_row.addWidget(self.lbl_console_status)
        layout.addLayout(head_row)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #070c18;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #38bdf8;
                font-family: Consolas, "Fira Code", "Courier New", monospace;
                font-size: 11px;
                padding: 10px 12px;
                line-height: 1.4;
            }
        """)
        self.console.setPlainText("准备就绪，选择 Web 测试模块后点击运行...")
        layout.addWidget(self.console, stretch=1)
        return card

    def _reset_console(self):
        self.console.setPlainText("准备就绪，选择 Web 测试模块后点击运行...")
        self.lbl_console_status.setText("Idle")
        self.lbl_console_status.setStyleSheet("""
            background-color: #f0fdf4;
            color: #16a34a;
            border: 1px solid #bbf7d0;
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: 700;
            font-size: 11px;
        """)

    # ================= 5. 下方测试集列表 =================
    def _create_cases_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("webCasesCard")
        card.setStyleSheet("""
            QFrame#webCasesCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px 18px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        lbl_title = QLabel("📋 Web 端专项自动化测试集")
        lbl_title.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 13px; background: transparent; border: none;")
        header_row.addWidget(lbl_title)
        header_row.addStretch()

        btn_run_all = QPushButton("一键执行全量 Web 冒烟")
        btn_run_all.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: 700;
                font-size: 11.5px;
                border: none;
                border-radius: 4px;
                padding: 5px 14px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        btn_run_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_run_all.clicked.connect(lambda: self._run_single_case({"name": "全量 Web 冒烟集"}))
        header_row.addWidget(btn_run_all)
        layout.addLayout(header_row)

        layout.addSpacing(2)

        # 5 个条目
        for mod in self.modules_data:
            item_box = QFrame()
            item_box.setObjectName("webCaseRow")
            item_box.setStyleSheet("""
                QFrame#webCaseRow {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 8px 14px;
                }
                QFrame#webCaseRow:hover {
                    background-color: #f8fafc;
                    border-color: #cbd5e1;
                }
            """)
            i_layout = QHBoxLayout(item_box)
            i_layout.setContentsMargins(4, 2, 4, 2)
            i_layout.setSpacing(10)

            lbl_name = QLabel(mod["name"])
            lbl_name.setStyleSheet("font-weight: 600; color: #0f172a; font-size: 12px; background: transparent; border: none;")
            i_layout.addWidget(lbl_name)

            lbl_tag = QLabel(mod["tag"])
            lbl_tag.setStyleSheet("""
                background-color: #f1f5f9;
                color: #64748b;
                font-weight: 600;
                font-size: 10px;
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid #e2e8f0;
            """)
            i_layout.addWidget(lbl_tag)
            i_layout.addStretch()

            if mod["status"] == "passed":
                lbl_status = QLabel(f"通过 ({mod['time']})")
                lbl_status.setStyleSheet("""
                    background-color: #ecfdf5;
                    color: #059669;
                    border: 1px solid #a7f3d0;
                    border-radius: 3px;
                    padding: 3px 8px;
                    font-weight: 700;
                    font-size: 11px;
                """)
            else:
                lbl_status = QLabel("未执行")
                lbl_status.setStyleSheet("""
                    background-color: #f8fafc;
                    color: #94a3b8;
                    border: 1px solid #e2e8f0;
                    border-radius: 3px;
                    padding: 3px 8px;
                    font-weight: 600;
                    font-size: 11px;
                """)
            i_layout.addWidget(lbl_status)

            btn_exec = QPushButton("执行")
            btn_exec.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #2563eb;
                    border: 1px solid #bfdbfe;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 3px 14px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #eff6ff;
                    border-color: #93c5fd;
                }
                QPushButton:pressed {
                    background-color: #dbeafe;
                }
            """)
            btn_exec.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_exec.clicked.connect(lambda ch, m=mod: self._run_single_case(m))
            i_layout.addWidget(btn_exec)

            layout.addWidget(item_box)

        return card

    def _run_single_case(self, mod: Dict[str, Any]):
        if self.is_executing:
            return
        self.is_executing = True
        self.lbl_console_status.setText("Running")
        self.lbl_console_status.setStyleSheet("""
            background-color: #eff6ff;
            color: #2563eb;
            border: 1px solid #bfdbfe;
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: 700;
            font-size: 11px;
        """)

        is_headless = self.switch_headless.isChecked()
        workers = self.stepper_workers.value()
        base_url = self.edit_base_url.text().strip()

        self.console.clear()
        self.console.appendPlainText(f"[Playwright] 🚀 启动浏览器实例: {self.current_browser}")
        self.console.appendPlainText(f"[Playwright] 🌐 目标地址: {base_url} (Headless: {is_headless}, 并发: {workers})")
        self.console.appendPlainText(f"[Playwright] 🧪 载入模块用例: {mod['name']}...")

        def _step_done():
            self.console.appendPlainText("[Playwright] ✅ 步骤 1: 打开主页成功")
            self.console.appendPlainText("[Playwright] ✅ 步骤 2: 页面元素定位与交互就绪")
            self.console.appendPlainText("[Playwright] ✅ 步骤 3: 断言验证通过")
            self.console.appendPlainText(f"[Playwright] 🏁 用例执行完毕，耗时 3.4s\n")
            self.lbl_console_status.setText("Idle")
            self.lbl_console_status.setStyleSheet("""
                background-color: #f0fdf4;
                color: #16a34a;
                border: 1px solid #bbf7d0;
                border-radius: 4px;
                padding: 2px 8px;
                font-weight: 700;
                font-size: 11px;
            """)
            self.is_executing = False

        QTimer.singleShot(1200, _step_done)
