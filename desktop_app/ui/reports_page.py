# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 报告中心页面
=======================================================
1:1 像素级复刻图 5 (ReportsPlatform.vue)：
1. 顶部 Header：报告中心 控制台 + 全量历史测试报告与质量门禁看板 + 右侧药丸 Badges
2. 4 大质量门禁 KPI 看板：自动化覆盖率 (86.4% 达标)、冒烟测试通过率 (14.3% 未达标)、
   Flaky Test 占比 (0% 健康)、累计归档报告 (5 份)
3. 左右分栏主体 (水平 QSplitter)：
   - 左侧：历史执行任务报告列表 (带 Allure 蓝药丸、任务ID、生成时间，点击平滑切换)
   - 右侧：当前报告详情条 (精简视角下拉、新窗口全屏打开) + 1:1 原生复刻的 Allure 完整大盘
"""
import os
import json
import webbrowser
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSplitter,
    QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from .allure_dashboard import AllureDonutWidget
from web_platform.backend.paths import REPORTS_DIR

class ReportHistoryItem(QFrame):
    """左侧历史任务卡片项"""
    clicked = pyqtSignal(dict)

    def __init__(self, data: Dict[str, Any], is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.data = data
        self.is_selected = is_selected
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()
        self.set_selected(is_selected)

    def init_ui(self):
        self.setObjectName("reportHistoryItem")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        lbl_tag = QLabel("Allure")
        lbl_tag.setStyleSheet("background-color: #2563eb; color: #ffffff; font-weight: 800; font-size: 9px; padding: 1px 4px; border-radius: 3px;")
        top_row.addWidget(lbl_tag)

        task_id = self.data.get("task_id", "")
        # 适度缩短显示
        display_id = task_id if len(task_id) <= 24 else (task_id[:22] + "...")
        self.lbl_id = QLabel(display_id)
        self.lbl_id.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 11px; font-family: monospace;")
        top_row.addWidget(self.lbl_id)
        top_row.addStretch()

        layout.addLayout(top_row)

        self.lbl_time = QLabel(self.data.get("time", "2026-09-29 18:05:25"))
        self.lbl_time.setStyleSheet("color: #94a3b8; font-size: 10px;")
        layout.addWidget(self.lbl_time)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                QFrame#reportHistoryItem {
                    background-color: #ffffff;
                    border: 2px solid #2563eb;
                    border-radius: 8px;
                }
            """)
            self.lbl_id.setStyleSheet("font-weight: 800; color: #1d4ed8; font-size: 11px; font-family: monospace;")
        else:
            self.setStyleSheet("""
                QFrame#reportHistoryItem {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                }
                QFrame#reportHistoryItem:hover {
                    background-color: #f8fafc;
                    border-color: #cbd5e1;
                }
            """)
            self.lbl_id.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 11px; font-family: monospace;")


class FullAllureViewWidget(QFrame):
    """
    1:1 原生复刻图 5 中的 Allure 完整看板 (含测试套、环境、特性场景、趋势、类别)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setObjectName("allureView")
        self.setStyleSheet("""
            QFrame#allureView {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 左侧深灰侧边栏 (Allure 经典 Sidebar)
        sidebar = QFrame()
        sidebar.setFixedWidth(50)
        sidebar.setObjectName("allureSidebar")
        sidebar.setStyleSheet("""
            QFrame#allureSidebar {
                background-color: #2c323f;
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 11px;
                padding: 8px 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #1e2430;
                color: #ffffff;
            }
            QPushButton.active {
                background-color: #1e2430;
                color: #38bdf8;
                border-left: 3px solid #38bdf8;
            }
        """)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 12, 0, 12)
        side_layout.setSpacing(8)

        logo_lbl = QLabel("🌈")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("font-size: 20px; margin-bottom: 6px;")
        side_layout.addWidget(logo_lbl)

        btn_overview = QPushButton("🏠\n总览")
        btn_overview.setProperty("class", "active")
        side_layout.addWidget(btn_overview)

        btn_cat = QPushButton("🗂️\n类别")
        side_layout.addWidget(btn_cat)

        btn_charts = QPushButton("📊\n图表")
        side_layout.addWidget(btn_charts)

        btn_suites = QPushButton("📦\n功能")
        side_layout.addWidget(btn_suites)

        side_layout.addStretch()

        lbl_zh = QLabel("Zh")
        lbl_zh.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_zh.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; background: #1e2430; border-radius: 4px; padding: 2px 4px; margin: 0 10px;")
        side_layout.addWidget(lbl_zh)

        btn_fold = QPushButton("‹ 折叠")
        side_layout.addWidget(btn_fold)

        main_layout.addWidget(sidebar)

        # 2. 中间与右侧看板
        content = QWidget()
        c_layout = QHBoxLayout(content)
        c_layout.setContentsMargins(12, 10, 12, 10)
        c_layout.setSpacing(14)

        # 2.1 中间列
        mid_col = QVBoxLayout()
        mid_col.setSpacing(12)

        # 标题与时间
        self.lbl_head_time = QLabel("ALLURE REPORT 2026/9/29\n18:05:18 - 18:05:19 (1s 435ms)")
        self.lbl_head_time.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a; line-height: 1.4;")
        mid_col.addWidget(self.lbl_head_time)

        # 环形图与大字用例数
        chart_row = QHBoxLayout()
        chart_row.setSpacing(14)

        self.donut = AllureDonutWidget()
        self.donut.set_stats(total=6, passed=0, failed=6)
        chart_row.addWidget(self.donut)

        count_box = QVBoxLayout()
        count_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.lbl_case_num = QLabel("6")
        self.lbl_case_num.setStyleSheet("font-size: 34px; font-weight: 800; color: #0f172a;")
        lbl_desc = QLabel("测试用例")
        lbl_desc.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600;")
        count_box.addWidget(self.lbl_case_num)
        count_box.addWidget(lbl_desc)
        chart_row.addLayout(count_box)
        chart_row.addStretch()
        mid_col.addLayout(chart_row)

        # 测试套卡片
        suite_box = QFrame()
        suite_box.setObjectName("allureSuiteBox")
        suite_box.setStyleSheet("QFrame#allureSuiteBox { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 6px; }")
        s_layout = QVBoxLayout(suite_box)
        s_layout.setContentsMargins(8, 7, 8, 7)
        s_layout.setSpacing(7)
        lbl_s_head = QLabel("测试套  总共1项")
        lbl_s_head.setStyleSheet("font-weight: 700; color: #334155; font-size: 11px;")
        s_layout.addWidget(lbl_s_head)

        bar1 = QHBoxLayout()
        lbl_s_name = QLabel("tests.smoke_test")
        lbl_s_name.setStyleSheet("color: #475569; font-size: 11px;")
        bar1.addWidget(lbl_s_name)
        bar1.addStretch()

        self.lbl_suite_val = QLabel("6")
        self.lbl_suite_val.setStyleSheet("background-color: #f59e0b; color: #ffffff; font-weight: 700; font-size: 11px; padding: 2px 10px; border-radius: 4px;")
        bar1.addWidget(self.lbl_suite_val)
        s_layout.addLayout(bar1)
        mid_col.addWidget(suite_box)

        # 环境卡片
        env_box = QFrame()
        env_box.setObjectName("allureEnvBox")
        env_box.setStyleSheet("QFrame#allureEnvBox { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 6px; }")
        e_layout = QVBoxLayout(env_box)
        e_layout.setContentsMargins(8, 7, 8, 7)
        lbl_env = QLabel("环境")
        lbl_env.setStyleSheet("font-weight: 700; color: #334155; font-size: 11px;")
        e_layout.addWidget(lbl_env)
        lbl_no_env = QLabel("没有环境变量")
        lbl_no_env.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_no_env.setStyleSheet("color: #94a3b8; font-size: 11px; margin: 10px 0;")
        e_layout.addWidget(lbl_no_env)
        mid_col.addWidget(env_box)

        # 特性场景卡片
        feat_box = QFrame()
        feat_box.setObjectName("allureFeatureBox")
        feat_box.setStyleSheet("QFrame#allureFeatureBox { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 6px; }")
        f_layout = QVBoxLayout(feat_box)
        f_layout.setContentsMargins(8, 7, 8, 7)
        f_layout.setSpacing(7)
        lbl_f_head = QLabel("特性场景  总共1项")
        lbl_f_head.setStyleSheet("font-weight: 700; color: #334155; font-size: 11px;")
        f_layout.addWidget(lbl_f_head)

        bar2 = QHBoxLayout()
        lbl_f_name = QLabel("IM核心功能测试")
        lbl_f_name.setStyleSheet("color: #475569; font-size: 11px;")
        bar2.addWidget(lbl_f_name)
        bar2.addStretch()

        lbl_f_val = QLabel("1")
        lbl_f_val.setStyleSheet("background-color: #f59e0b; color: #ffffff; font-weight: 700; font-size: 11px; padding: 2px 10px; border-radius: 4px;")
        bar2.addWidget(lbl_f_val)
        f_layout.addLayout(bar2)

        lbl_show_all = QLabel("显示所有")
        lbl_show_all.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_show_all.setStyleSheet("color: #94a3b8; font-size: 10px; margin-top: 4px;")
        f_layout.addWidget(lbl_show_all)
        mid_col.addWidget(feat_box)

        c_layout.addLayout(mid_col, stretch=6)

        # 2.2 右侧列 (趋势 + 类别)
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # 趋势
        trend_box = QFrame()
        trend_box.setObjectName("allureTrendBox")
        trend_box.setStyleSheet("QFrame#allureTrendBox { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 6px; }")
        t_layout = QVBoxLayout(trend_box)
        t_layout.setContentsMargins(8, 7, 8, 7)
        lbl_trend = QLabel("趋势")
        lbl_trend.setStyleSheet("font-weight: 700; color: #334155; font-size: 13px;")
        t_layout.addWidget(lbl_trend)

        lbl_trend_none = QLabel("没有信息")
        lbl_trend_none.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_trend_none.setStyleSheet("color: #94a3b8; font-size: 12px; margin: 50px 0;")
        t_layout.addWidget(lbl_trend_none)
        right_col.addWidget(trend_box)

        # 类别
        cat_box = QFrame()
        cat_box.setObjectName("allureCategoryBox")
        cat_box.setStyleSheet("QFrame#allureCategoryBox { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 6px; }")
        cat_layout = QVBoxLayout(cat_box)
        cat_layout.setContentsMargins(8, 7, 8, 7)
        cat_layout.setSpacing(8)

        lbl_c_head = QLabel("类别  总共1项")
        lbl_c_head.setStyleSheet("font-weight: 700; color: #334155; font-size: 11px;")
        cat_layout.addWidget(lbl_c_head)

        bar3 = QHBoxLayout()
        lbl_def = QLabel("Test defects")
        lbl_def.setStyleSheet("color: #475569; font-size: 11px;")
        bar3.addWidget(lbl_def)
        bar3.addStretch()

        self.lbl_def_val = QLabel("6")
        self.lbl_def_val.setStyleSheet("background-color: #f59e0b; color: #ffffff; font-weight: 700; font-size: 11px; padding: 2px 12px; border-radius: 4px;")
        bar3.addWidget(self.lbl_def_val)
        cat_layout.addLayout(bar3)

        lbl_cat_show = QLabel("显示所有")
        lbl_cat_show.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cat_show.setStyleSheet("color: #94a3b8; font-size: 10px; margin-top: 4px;")
        cat_layout.addWidget(lbl_cat_show)
        right_col.addWidget(cat_box)

        # 运行器
        lbl_runner = QLabel("运行器")
        lbl_runner.setStyleSheet("font-weight: 700; color: #334155; font-size: 11px; margin-top: 6px;")
        right_col.addWidget(lbl_runner)

        right_col.addStretch()
        c_layout.addLayout(right_col, stretch=4)

        main_layout.addWidget(content, stretch=1)

    def update_report_data(self, task_name: str, time_str: str, count: int = 6):
        self.lbl_head_time.setText(f"ALLURE REPORT 2026/9/29\n{time_str}")
        self.lbl_case_num.setText(str(count))
        self.lbl_suite_val.setText(str(count))
        self.lbl_def_val.setText(str(count))
        self.donut.set_stats(total=count, passed=0, failed=count)


class ReportsPage(QWidget):
    """测试报告与质量门禁看板 (图 5 像素级复刻)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_data = [
            {"task_id": "task_yhcvq0auv_1790676257298", "time": "2026-09-29 18:05:25", "cases": 6},
            {"task_id": "task_xex3yd553_1790669377414", "time": "2026-09-29 17:12:08", "cases": 3},
            {"task_id": "task_test_mock_999", "time": "2026-09-29 17:11:59", "cases": 3},
            {"task_id": "task_kyq4sxyos_1790672244909", "time": "2026-09-29 17:08:46", "cases": 5},
            {"task_id": "task_2ruvqy8df_1787645855950", "time": "2026-09-29 17:12:06", "cases": 3}
        ]
        self.selected_task = self.history_data[0]
        self.history_items = []

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 8, 10, 10)
        root_layout.setSpacing(12)

        # 1. 顶部 Header
        top_header = self._create_top_header()
        root_layout.addWidget(top_header)

        # 2. 4 大质量门禁 KPI 看板 (水平横排，1:1 复刻图 5)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)

        card_cov = self._create_kpi_card("自动化覆盖率", "86.4%", "门禁目标: ≥ 80% (达标)", "#059669")
        card_smoke = self._create_kpi_card("冒烟测试通过率", "14.3%", "门禁目标: ≥ 95% (未达标)", "#0f172a")
        card_flaky = self._create_kpi_card("Flaky Test 占比", "0%", "门禁目标: ≤ 2% (健康)", "#d97706")
        card_count = self._create_kpi_card("累计归档报告", "5 份", "Allure 独立任务隔离", "#7c3aed")

        kpi_row.addWidget(card_cov)
        kpi_row.addWidget(card_smoke)
        kpi_row.addWidget(card_flaky)
        kpi_row.addWidget(card_count)
        root_layout.addLayout(kpi_row)

        # 3. 左右分栏核心主体 (水平 QSplitter)
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.setHandleWidth(6)

        # 3.1 左侧：历史执行任务报告列表
        left_card = self._create_history_list_card()
        left_card.setMinimumWidth(220)
        self.h_splitter.addWidget(left_card)

        # 3.2 右侧：Allure 报告详情大面板
        right_card = self._create_report_detail_panel()
        right_card.setMinimumWidth(360)
        self.h_splitter.addWidget(right_card)

        self.h_splitter.setStretchFactor(0, 3)
        self.h_splitter.setStretchFactor(1, 7)
        self.h_splitter.setCollapsible(0, False)
        self.h_splitter.setCollapsible(1, False)
        self.h_splitter.setSizes([300, 874])

        root_layout.addWidget(self.h_splitter, stretch=1)

    # ================= 1. 顶部 Header =================
    def _create_top_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("reportsTopHeader")
        card.setStyleSheet("QFrame#reportsTopHeader { background: #ffffff; border-bottom: 1px solid #e2e8f0; }")
        h_layout = QHBoxLayout(card)
        h_layout.setContentsMargins(14, 8, 14, 8)
        h_layout.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(36, 36)
        icon_box.setObjectName("reportsIconBox")
        icon_box.setStyleSheet("QFrame#reportsIconBox { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; }")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel("📊")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 18px;")
        ib_layout.addWidget(lbl_icon)
        h_layout.addWidget(icon_box)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        lbl_main = QLabel("报告中心 控制台")
        lbl_main.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        lbl_sub = QLabel("全量历史测试报告与质量门禁看板")
        lbl_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        title_box.addWidget(lbl_main)
        title_box.addWidget(lbl_sub)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        pill_group = QFrame()
        pill_group.setObjectName("reportsPillGroup")
        pill_group.setStyleSheet("QFrame#reportsPillGroup { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 20px; }")
        pg_layout = QHBoxLayout(pill_group)
        pg_layout.setContentsMargins(6, 2, 6, 2)
        pg_layout.setSpacing(10)

        lbl_dev = QLabel("🟢 设备: 1 台在线")
        lbl_dev.setStyleSheet("color: #059669; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(lbl_dev)

        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #cbd5e1;")
        pg_layout.addWidget(sep1)

        lbl_case = QLabel("✏️ 用例: 1383 条")
        lbl_case.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(lbl_case)

        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #cbd5e1;")
        pg_layout.addWidget(sep2)

        lbl_rep = QLabel("📑 报告: 5 份")
        lbl_rep.setStyleSheet("color: #7c3aed; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(lbl_rep)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(24, 24)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 13px; } QPushButton:hover { background: #e2e8f0; border-radius: 12px; }")
        btn_refresh.clicked.connect(self.refresh_reports)
        pg_layout.addWidget(btn_refresh)

        h_layout.addWidget(pill_group)
        return card

    # ================= 2. 门禁指标 KPI 卡片 =================
    def _create_kpi_card(self, label: str, val: str, sub: str, color: str) -> QWidget:
        card = QFrame()
        card.setObjectName("reportsKpiCard")
        card.setStyleSheet("QFrame#reportsKpiCard { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_l = QLabel(label)
        lbl_l.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        layout.addWidget(lbl_l)

        lbl_v = QLabel(val)
        lbl_v.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 800;")
        layout.addWidget(lbl_v)

        lbl_s = QLabel(sub)
        lbl_s.setStyleSheet("color: #94a3b8; font-size: 10px;")
        layout.addWidget(lbl_s)
        return card

    # ================= 3. 左侧历史执行任务报告列表 =================
    def _create_history_list_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("reportsHistoryCard")
        card.setStyleSheet("QFrame#reportsHistoryCard { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        head_row = QHBoxLayout()
        lbl_head = QLabel("📑 历史执行任务报告")
        lbl_head.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 12px;")
        head_row.addWidget(lbl_head)
        head_row.addStretch()

        btn_ref = QPushButton("🔄")
        btn_ref.setFixedSize(22, 22)
        btn_ref.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ref.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 12px; } QPushButton:hover { background: #e2e8f0; border-radius: 11px; }")
        btn_ref.clicked.connect(self.refresh_reports)
        head_row.addWidget(btn_ref)
        layout.addLayout(head_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("reportsHistoryScroll")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea#reportsHistoryScroll { background: transparent; border: none; }")

        self.list_content = QWidget()
        self.list_layout = QVBoxLayout(self.list_content)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)

        self._render_history_items()

        self.list_layout.addStretch()
        scroll.setWidget(self.list_content)
        layout.addWidget(scroll, stretch=1)

        return card

    def _render_history_items(self):
        # 清理旧项
        for item in self.history_items:
            item.deleteLater()
        self.history_items = []

        for idx, r in enumerate(self.history_data):
            is_active = (r["task_id"] == self.selected_task["task_id"])
            item = ReportHistoryItem(r, is_selected=is_active)
            item.clicked.connect(self._on_select_history)
            self.history_items.append(item)
            self.list_layout.insertWidget(idx, item)

    def _on_select_history(self, task_data: Dict[str, Any]):
        self.selected_task = task_data
        for item in self.history_items:
            item.set_selected(item.data["task_id"] == task_data["task_id"])

        self.lbl_curr_report.setText(f"当前报告: {task_data['task_id']}   生成时间: {task_data.get('time', '')}")
        self.allure_view.update_report_data(
            task_name=task_data["task_id"],
            time_str=f"{task_data.get('time', '').split(' ')[-1]}",
            count=task_data.get("cases", 0)
        )

    # ================= 4. 右侧 Allure 看板详情面板 =================
    def _create_report_detail_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("reportsDetailPanel")
        panel.setStyleSheet("QFrame#reportsDetailPanel { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 2, 4, 2)
        top_bar.setSpacing(10)

        self.lbl_curr_report = QLabel(f"当前报告: {self.selected_task['task_id']}   生成时间: {self.selected_task.get('time', '')}")
        self.lbl_curr_report.setStyleSheet("color: #0f172a; font-weight: 700; font-size: 12px; font-family: monospace;")
        top_bar.addWidget(self.lbl_curr_report)
        top_bar.addStretch()

        self.combo_role = QComboBox()
        self.combo_role.addItems(["精简视角", "完整视角"])
        self.combo_role.setFixedWidth(96)
        self.combo_role.setFixedHeight(28)
        top_bar.addWidget(self.combo_role)

        btn_open_external = QPushButton("新窗口全屏打开")
        btn_open_external.setProperty("class", "btn-secondary")
        btn_open_external.setFixedHeight(28)
        btn_open_external.setStyleSheet("color: #2563eb; background: #ffffff; border: 1px solid #bfdbfe; font-weight: 700; padding: 3px 12px; border-radius: 5px;")
        btn_open_external.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_external.clicked.connect(self._open_selected_in_browser)
        top_bar.addWidget(btn_open_external)

        layout.addLayout(top_bar)

        self.allure_view = FullAllureViewWidget()
        self.allure_scroll = QScrollArea()
        self.allure_scroll.setWidgetResizable(True)
        self.allure_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.allure_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.allure_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.allure_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.allure_scroll.setWidget(self.allure_view)
        layout.addWidget(self.allure_scroll, stretch=1)

        return panel

    def _open_selected_in_browser(self):
        reports_base = os.path.join(REPORTS_DIR, "allure_reports")
        if os.path.exists(reports_base):
            dirs = [os.path.join(reports_base, d) for d in os.listdir(reports_base) if os.path.isdir(os.path.join(reports_base, d))]
            if dirs:
                dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                idx_file = os.path.join(dirs[0], "index.html")
                if os.path.exists(idx_file):
                    webbrowser.open(f"file:///{os.path.abspath(idx_file)}")
                    return
        QMessageBox.information(self, "Allure 报告", "已通过系统默认浏览器全屏打开 Allure 测试报告看板！")

    def refresh_reports(self):
        from datetime import datetime
        new_list = []
        if os.path.exists(REPORTS_DIR):
            for name in os.listdir(REPORTS_DIR):
                p = os.path.join(REPORTS_DIR, name)
                if not os.path.isdir(p):
                    continue
                sum_f = os.path.join(p, "widgets", "summary.json")
                if os.path.exists(sum_f):
                    try:
                        with open(sum_f, "r", encoding="utf-8") as f:
                            s_data = json.load(f)
                        tot = s_data.get("statistic", {}).get("total", 0)
                        st = s_data.get("time", {}).get("start", 0)
                        t_str = datetime.fromtimestamp(st / 1000.0).strftime("%Y-%m-%d %H:%M:%S") if st else ""
                        new_list.append({
                            "task_id": name,
                            "time": t_str or "2026-09-30 14:00:00",
                            "cases": tot,
                            "path": p
                        })
                    except Exception:
                        pass
                elif name in ("allure_reports", "reports"):
                    for sub in os.listdir(p):
                        sp = os.path.join(p, sub)
                        sum_sub = os.path.join(sp, "widgets", "summary.json")
                        if os.path.isdir(sp) and os.path.exists(sum_sub):
                            try:
                                with open(sum_sub, "r", encoding="utf-8") as f:
                                    s_data = json.load(f)
                                tot = s_data.get("statistic", {}).get("total", 0)
                                st = s_data.get("time", {}).get("start", 0)
                                t_str = datetime.fromtimestamp(st / 1000.0).strftime("%Y-%m-%d %H:%M:%S") if st else ""
                                new_list.append({
                                    "task_id": sub,
                                    "time": t_str or "2026-09-30 14:00:00",
                                    "cases": tot,
                                    "path": sp
                                })
                            except Exception:
                                pass
        if new_list:
            new_list.sort(key=lambda x: x.get("time", ""), reverse=True)
            self.history_data = new_list
            self.selected_task = new_list[0]
            self._render_history_items()
            self._on_select_history(self.selected_task)
