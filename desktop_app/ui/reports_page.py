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
import sys
import json
import webbrowser
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSplitter,
    QComboBox, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from .widgets import RedTrashButton, create_red_trash_icon, TopStatusPillWidget
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from .allure_dashboard import AllureDashboardWidget
except (ImportError, ValueError):
    from desktop_app.ui.allure_dashboard import AllureDashboardWidget
from desktop_app.core.paths import REPORTS_DIR
from desktop_app.core.report_scanner import scan_available_reports, get_reports_count

class ReportHistoryItem(QFrame):
    """左侧历史任务卡片项"""
    clicked = pyqtSignal(dict)
    delete_requested = pyqtSignal(dict)

    def __init__(self, data: Dict[str, Any], index: int = 1, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.data = data
        self.index = index
        self.data["index"] = index
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

        # 报告序号徽章 (例如 1, 2, 3...)
        self.lbl_idx = QLabel(f"{self.index}")
        self.lbl_idx.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_idx.setMinimumWidth(20)
        self.lbl_idx.setFixedHeight(18)
        self.lbl_idx.setToolTip(f"报告序号: 第 {self.index} 份")
        self.lbl_idx.setStyleSheet(
            "background-color: #f1f5f9; color: #475569; font-weight: 800; font-size: 10px; "
            "padding: 0 4px; border-radius: 4px; border: 1px solid #cbd5e1;"
        )
        top_row.addWidget(self.lbl_idx)

        lbl_tag = QLabel("Allure")
        lbl_tag.setStyleSheet("background-color: #2563eb; color: #ffffff; font-weight: 800; font-size: 9px; padding: 1px 4px; border-radius: 3px;")
        top_row.addWidget(lbl_tag)

        task_id = self.data.get("task_id", "")
        # 适度缩短显示
        display_id = task_id if len(task_id) <= 20 else (task_id[:18] + "...")
        self.lbl_id = QLabel(display_id)
        self.lbl_id.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 11px; font-family: monospace;")
        top_row.addWidget(self.lbl_id)
        top_row.addStretch()

        # 卡片快捷微型红色矢量垃圾桶删除按钮
        btn_del_item = RedTrashButton(parent=self, is_circle=True)
        btn_del_item.setFixedSize(18, 18)
        btn_del_item.setToolTip("删除此条测试报告")
        btn_del_item.clicked.connect(lambda: self.delete_requested.emit(self.data))
        top_row.addWidget(btn_del_item)

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
            if hasattr(self, "lbl_idx"):
                self.lbl_idx.setStyleSheet(
                    "background-color: #eff6ff; color: #1d4ed8; font-weight: 800; font-size: 10px; "
                    "padding: 0 4px; border-radius: 4px; border: 1px solid #93c5fd;"
                )
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
            if hasattr(self, "lbl_idx"):
                self.lbl_idx.setStyleSheet(
                    "background-color: #f1f5f9; color: #475569; font-weight: 800; font-size: 10px; "
                    "padding: 0 4px; border-radius: 4px; border: 1px solid #cbd5e1;"
                )


class ReportsPage(QWidget):
    """测试报告与质量门禁看板 (图 5 像素级复刻)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_data: List[Dict[str, Any]] = []
        self.selected_task: Dict[str, Any] = {}
        self.history_items: List[ReportHistoryItem] = []

        self.init_ui()
        # 懒加载策略：推迟至首屏呈现后异步扫描历史报告，杜绝启动期磁盘 I/O 阻塞主线程
        QTimer.singleShot(500, self.refresh_reports)

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

        card_cov, self.card_cov_val = self._create_kpi_card("自动化覆盖率", "86.4%", "门禁目标: ≥ 80% (达标)", "#059669")
        card_smoke, self.card_smoke_val = self._create_kpi_card("冒烟测试通过率", "14.3%", "门禁目标: ≥ 95% (未达标)", "#0f172a")
        card_flaky, self.card_flaky_val = self._create_kpi_card("Flaky Test 占比", "0%", "门禁目标: ≤ 2% (健康)", "#d97706")
        card_count, self.card_count_val = self._create_kpi_card("累计归档报告", "0 份", "Allure 独立任务隔离", "#7c3aed")

        kpi_row.addWidget(card_cov)
        kpi_row.addWidget(card_smoke)
        kpi_row.addWidget(card_flaky)
        kpi_row.addWidget(card_count)
        root_layout.addLayout(kpi_row)

        # 3. 左右分栏核心主体 (水平 QSplitter)
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.setHandleWidth(4)

        # 3.1 左侧：历史执行任务报告列表
        left_card = self._create_history_list_card()
        left_card.setMinimumWidth(220)
        self.h_splitter.addWidget(left_card)

        # 3.2 右侧：Allure 报告详情大面板 (与移动端执行报告 100% 统一)
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

        # 右侧药丸状态 Badge 组 (与移动IM控制中心完全公用统一通用控件)
        self.top_status_pill = TopStatusPillWidget(parent=card)
        self.lbl_rep = self.top_status_pill.lbl_report
        self.top_status_pill.refresh_clicked.connect(self.refresh_reports)
        h_layout.addWidget(self.top_status_pill)
        return card

    # ================= 2. 门禁指标 KPI 卡片 =================
    def _create_kpi_card(self, label: str, val: str, sub: str, color: str) -> tuple[QWidget, QLabel]:
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
        return card, lbl_v

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

        # 红色高亮圆形矢量垃圾桶删除操作按钮
        btn_del = RedTrashButton(parent=card, is_circle=True)
        btn_del.setFixedSize(24, 24)
        btn_del.setToolTip("删除报告 (支持删除当前 / 一键清空全部)")
        btn_del.clicked.connect(self._on_click_delete_menu)
        head_row.addWidget(btn_del)

        btn_ref = QPushButton("🔄")
        btn_ref.setFixedSize(22, 22)
        btn_ref.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ref.setToolTip("刷新报告列表")
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
            is_active = (r.get("task_id") == self.selected_task.get("task_id"))
            item = ReportHistoryItem(r, index=idx + 1, is_selected=is_active)
            item.clicked.connect(self._on_select_history)
            item.delete_requested.connect(self._delete_single_report)
            self.history_items.append(item)
            self.list_layout.insertWidget(idx, item)

    # ================= 删除测试报告业务逻辑 =================
    def _delete_single_report(self, task_data: Dict[str, Any]):
        """删除指定的一条报告及其物理磁盘数据"""
        task_id = task_data.get("task_id", "")
        if not task_id:
            return

        reply = QMessageBox.question(
            self,
            "确认删除测试报告",
            f"确定要彻底删除该测试报告吗？\n\n任务编号: {task_id}\n生成时间: {task_data.get('time', '未知')}\n\n该操作将永久从磁盘中清除本次报告的所有结果文件与截图。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._do_delete_report_files(task_id, task_data.get("path"))
            self.refresh_reports()

    def _delete_current_selected_report(self):
        """删除当前选中的报告"""
        if not self.selected_task or not self.selected_task.get("task_id"):
            QMessageBox.information(self, "提示", "当前没有选中的测试报告可删除。")
            return
        self._delete_single_report(self.selected_task)

    def _clear_all_reports(self):
        """一键清空本地所有历史测试报告"""
        if not self.history_data:
            QMessageBox.information(self, "提示", "当前历史报告列表已为空，无需清理。")
            return

        reply = QMessageBox.warning(
            self,
            "危险操作：清空全部报告",
            f"确定要一键清空本地所有的历史测试报告吗？（共 {len(self.history_data)} 份）\n\n此操作将永久清理磁盘上所有生成的测试报告、JSON 结果与失败截图，不可撤回！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for item in list(self.history_data):
                self._do_delete_report_files(item.get("task_id", ""), item.get("path"))
            self.refresh_reports()
            QMessageBox.information(self, "清理完成", "已成功清空本地所有历史测试报告！")

    def _do_delete_report_files(self, task_id: str, task_path: Optional[str] = None):
        """彻底清理单个任务在文件系统中的全部产物"""
        import shutil
        targets = set()
        if task_path and os.path.exists(task_path):
            targets.add(os.path.abspath(task_path))
        if task_id:
            targets.add(os.path.abspath(os.path.join(REPORTS_DIR, "allure_reports", task_id)))
            targets.add(os.path.abspath(os.path.join(REPORTS_DIR, "allure_results", task_id)))
            targets.add(os.path.abspath(os.path.join(REPORTS_DIR, f"html_{task_id}")))
            targets.add(os.path.abspath(os.path.join(REPORTS_DIR, f"tmp_{task_id}")))

        for p in targets:
            if os.path.exists(p):
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
                except Exception as e:
                    print(f"删除报告文件失败 ({p}): {e}")

    def _on_click_delete_menu(self):
        """点击顶栏垃圾桶按钮，弹出操作菜单（删除当前或清空全部）"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 14px;
                font-size: 11px;
                color: #334155;
                border-radius: 4px;
            }
            QMenu::item:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QMenu::item:selected {
                background-color: #fee2e2;
                color: #e11d48;
            }
        """)

        curr_id = self.selected_task.get("task_id", "")
        short_id = (curr_id[:16] + "...") if len(curr_id) > 18 else curr_id
        action_del_curr = menu.addAction(create_red_trash_icon(14), f"删除当前报告 ({short_id or '未选择'})")
        action_del_curr.triggered.connect(self._delete_current_selected_report)
        if not curr_id:
            action_del_curr.setEnabled(False)

        menu.addSeparator()

        action_clear_all = menu.addAction("🧹 清空全部历史报告")
        action_clear_all.triggered.connect(self._clear_all_reports)

        btn_sender = self.sender()
        if isinstance(btn_sender, QPushButton):
            menu.exec(btn_sender.mapToGlobal(btn_sender.rect().bottomLeft()))
        else:
            from PyQt6.QtGui import QCursor
            menu.exec(QCursor.pos())

    def _on_select_history(self, task_data: Dict[str, Any]):
        self.selected_task = task_data
        for item in self.history_items:
            item.set_selected(item.data.get("task_id") == task_data.get("task_id"))

        curr_idx = task_data.get("index", "")
        prefix = f"[#{curr_idx}] " if curr_idx else ""
        self.lbl_curr_report.setText(f"当前报告: {prefix}{task_data.get('task_id', '未选择')}   生成时间: {task_data.get('time', '')}")

        # 核心：精准动态加载并呈现该历史任务的真实测试报告
        task_id = task_data.get("task_id", "")
        task_path = task_data.get("path", "")
        report_dir = None
        results_dir = None

        if task_path and os.path.exists(task_path):
            if os.path.exists(os.path.join(task_path, "widgets", "summary.json")):
                report_dir = task_path
            else:
                results_dir = task_path

        if not report_dir:
            cand_report = os.path.join(REPORTS_DIR, "allure_reports", task_id)
            if os.path.exists(os.path.join(cand_report, "widgets", "summary.json")):
                report_dir = cand_report

        if not results_dir:
            cand_results = os.path.join(REPORTS_DIR, "allure_results", task_id)
            if os.path.exists(cand_results):
                results_dir = cand_results
            else:
                cand_tmp = os.path.join(REPORTS_DIR, f"tmp_{task_id}")
                if os.path.exists(cand_tmp):
                    results_dir = cand_tmp

        self.allure_dashboard.load_report_from_path(report_dir=report_dir, results_dir=results_dir)
        role = self.combo_role.currentData() or "business"
        self.allure_dashboard.set_role_view(role)

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

        curr_id = self.selected_task.get('task_id', '就绪')
        curr_time = self.selected_task.get('time', '')
        self.lbl_curr_report = QLabel(f"当前报告: {curr_id}   生成时间: {curr_time}")
        self.lbl_curr_report.setStyleSheet("color: #0f172a; font-weight: 700; font-size: 12px; font-family: monospace;")
        top_bar.addWidget(self.lbl_curr_report)
        top_bar.addStretch()

        self.combo_role = QComboBox()
        self.combo_role.addItem("精简视角", "business")
        self.combo_role.addItem("完整视角", "tech")
        self.combo_role.setFixedWidth(130)
        self.combo_role.setFixedHeight(28)
        self.combo_role.currentIndexChanged.connect(self._on_role_changed)
        top_bar.addWidget(self.combo_role)

        btn_open_external = QPushButton("新窗口全屏打开")
        btn_open_external.setProperty("class", "btn-secondary")
        btn_open_external.setFixedHeight(28)
        btn_open_external.setStyleSheet("color: #2563eb; background: #ffffff; border: 1px solid #bfdbfe; font-weight: 700; padding: 3px 12px; border-radius: 5px;")
        btn_open_external.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_external.clicked.connect(self._open_selected_in_browser)
        top_bar.addWidget(btn_open_external)

        layout.addLayout(top_bar)

        # 核心：直接嵌入功能完备、与实际运行完全统一的 Allure 原生看板组件
        self.allure_dashboard = AllureDashboardWidget(parent=self)
        layout.addWidget(self.allure_dashboard, stretch=1)
        self._on_role_changed()

        return panel

    def _on_role_changed(self):
        """报告中心角色视角切换响应槽"""
        role = self.combo_role.currentData() or "business"
        if hasattr(self, "allure_dashboard") and self.allure_dashboard:
            self.allure_dashboard.set_role_view(role)

    def _open_selected_in_browser(self):
        curr_task = getattr(self, "selected_task", {})
        if curr_task:
            task_id = curr_task.get("task_id", "")
            task_path = curr_task.get("path", "")
            candidates = [
                os.path.join(task_path, "index.html") if task_path else "",
                os.path.join(REPORTS_DIR, "allure_reports", task_id, "index.html"),
                os.path.join(REPORTS_DIR, f"html_{task_id}", "index.html"),
            ]
            for cand in candidates:
                if cand and os.path.exists(cand):
                    webbrowser.open(Path(cand).resolve().as_uri())
                    return
        reports_base = os.path.join(REPORTS_DIR, "allure_reports")
        if os.path.exists(reports_base):
            dirs = [os.path.join(reports_base, d) for d in os.listdir(reports_base) if os.path.isdir(os.path.join(reports_base, d))]
            if dirs:
                dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                idx_file = os.path.join(dirs[0], "index.html")
                if os.path.exists(idx_file):
                    webbrowser.open(Path(idx_file).resolve().as_uri())
                    return
        QMessageBox.information(self, "Allure 报告", "当前任务尚未生成独立 HTML 报告，可在右侧仪表盘实时预览测试数据。")

    def refresh_reports(self):
        """全自动扫描并同步本地所有测试任务报告，按时间倒序排列并渲染"""
        new_list = scan_available_reports()

        if new_list:
            self.history_data = new_list
            self.selected_task = new_list[0]
            self.card_count_val.setText(f"{len(new_list)} 份")
            self.top_status_pill.update_report_count(len(new_list))
            self._render_history_items()
            self._on_select_history(self.selected_task)
        else:
            self.history_data = []
            self.selected_task = {}
            self.card_count_val.setText("0 份")
            self.top_status_pill.update_report_count(0)
            self.lbl_curr_report.setText("当前暂无历史测试报告")
            self._render_history_items()
            if hasattr(self, 'allure_dashboard') and self.allure_dashboard:
                self.allure_dashboard.reset_to_ready_state()
