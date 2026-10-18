# -*- coding: utf-8 -*-
"""
================================================================================
HarmonyOS Appium Inspector (纯血鸿蒙专属高颜值桌面审查器 - 实时输入同步增强版)
================================================================================
1. 遇到输入框与编辑框时，提供专属实时输入同步控制台 (Live Input Sync Console)。
2. 支持输入文本即时同步至鸿蒙真机，零延迟同步更新 DOM 树、属性表、XPath 代码推荐与真机原画。
3. 彻底解决高 DPI 缩放下标签截断 (th:, on:) 与输入框文本压扁被裁剪的问题。
4. 面包屑开启 setWordWrap 自动换行，属性表格行高优化 (34px)，消除所有文本溢出。
5. DOM 树增加底部横向拖动条，超宽超深层级组件与完整属性尽收眼底。
6. 全局按钮悬浮小手光标，后台 QThread 异步抓取，60 帧丝滑不卡顿。
================================================================================
"""
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize, QRectF, QThread
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QFont, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap
)
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)


# ==============================================================================
# 鸿蒙 HDC 驱动通信层
# ==============================================================================

def get_connected_devices() -> List[str]:
    """获取所有当前在线的鸿蒙设备列表"""
    devices = []
    try:
        out = subprocess.check_output(["hdc", "list", "targets"], text=True, errors="ignore").strip()
        for line in out.splitlines():
            line = line.strip()
            if line and "empty" not in line.lower() and "[Empty]" not in line:
                devices.append(line)
    except Exception:
        pass
    if not devices:
        try:
            import yaml
            cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "devices.yaml")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                    udid = cfg.get("devices", {}).get("dev", {}).get("harmony_sender", {}).get("udid", "")
                    if udid:
                        devices.append(udid)
        except Exception:
            pass
    return devices


def run_hdc(cmd: List[str], udid: str = "") -> str:
    """执行 HDC 指令"""
    full_cmd = ["hdc"]
    if udid:
        full_cmd.extend(["-t", udid])
    full_cmd.extend(cmd)
    try:
        res = subprocess.run(full_cmd, capture_output=True, text=True, errors="ignore", timeout=25)
        return res.stdout.strip()
    except Exception:
        return ""


# ==============================================================================
# 异步后台抓取线程 (彻底根治主界面卡顿)
# ==============================================================================

class CaptureWorker(QThread):
    """后台异步抓取线程：在独立线程中执行截图与 dumpLayout，主线程绝不卡死"""
    finished = pyqtSignal(str, str)
    failed = pyqtSignal(str)

    def __init__(self, udid: str, tmp_dir: str):
        super().__init__()
        self.udid = udid
        self.tmp_dir = tmp_dir

    def run(self):
        try:
            remote_png = "/data/local/tmp/appium_shot.png"
            local_png = os.path.join(self.tmp_dir, "appium_shot.png")
            remote_json = "/data/local/tmp/appium_layout.json"
            local_json = os.path.join(self.tmp_dir, "appium_layout.json")

            # 1. 执行真机截图并拉取
            run_hdc(["shell", "uitest", "screenCap", "-p", remote_png], self.udid)
            run_hdc(["file", "recv", remote_png, local_png], self.udid)

            # 2. 执行真机 dumpLayout 布局并拉取
            run_hdc(["shell", "uitest", "dumpLayout", "-p", remote_json], self.udid)
            run_hdc(["file", "recv", remote_json, local_json], self.udid)

            # 3. 校验产物
            if os.path.exists(local_png) and os.path.exists(local_json):
                self.finished.emit(local_png, local_json)
            else:
                self.failed.emit("抓取现场数据失败，请确认屏幕已点亮且处于解锁状态。")
        except Exception as e:
            self.failed.emit(str(e))


# ==============================================================================
# 左栏：纯净真机屏幕视窗 (纯白画布 + 拟真机身外壳，无任何方格干扰)
# ==============================================================================

class InspectorMode:
    SELECT = "select"  # 审查选择模式
    TAP = "tap"        # 坐标点击模式
    SWIPE = "swipe"    # 坐标滑动模式


class AppiumScreenView(QWidget):
    """
    真机屏幕映射视窗：
    - 纯净真实画面，默认不绘制任何杂乱的全局方格；
    - 鼠标悬停 (Hover)：单个组件细腻光晕框 + 顶部浮动类型尺寸小气泡；
    - 鼠标点击选中 (Selected)：单个组件鲜亮克莱因蓝高亮实线框；
    - 自适应缩放居中绘制，拖拽调整窗口大小时平滑流畅。
    """
    element_selected = pyqtSignal(str)
    coordinate_tapped = pyqtSignal(int, int)
    coordinate_swiped = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.mode = InspectorMode.SELECT
        self.pixmap: Optional[QPixmap] = None
        self.flat_components: List[Dict[str, Any]] = []
        self.comp_map: Dict[str, Dict[str, Any]] = {}
        self.hover_node_id: str = ""
        self.selected_node_id: str = ""
        self.orig_w = 1084
        self.orig_h = 2412

        # 拖拽滑动状态
        self.is_dragging = False
        self.swipe_start_pos: Optional[QPoint] = None
        self.swipe_cur_pos: Optional[QPoint] = None

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: transparent;")

    def set_mode(self, mode: str):
        self.mode = mode
        if mode == InspectorMode.SELECT:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif mode == InspectorMode.TAP:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == InspectorMode.SWIPE:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.update()

    def load_screenshot(self, img_path: str, components: List[Dict[str, Any]]):
        self.pixmap = QPixmap(img_path)
        if not self.pixmap.isNull():
            self.orig_w = self.pixmap.width()
            self.orig_h = self.pixmap.height()
        self.flat_components = components
        self.comp_map = {c["node_id"]: c for c in components}
        self.hover_node_id = ""
        self.update()

    def get_draw_rect(self) -> QRect:
        if not self.pixmap or self.pixmap.isNull():
            return QRect()
        avail_w = max(50, self.width() - 24)
        avail_h = max(50, self.height() - 24)
        scaled = self.pixmap.scaled(
            QSize(avail_w, avail_h),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        return QRect(x, y, scaled.width(), scaled.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        draw_rect = self.get_draw_rect()
        if not self.pixmap or self.pixmap.isNull() or draw_rect.isEmpty():
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(QFont("PingFang SC", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "正在连接鸿蒙真机并同步界面布局...")
            return

        # 1. 绘制拟真手机深灰/银黑悬浮机身外壳与圆角投影
        phone_shell = draw_rect.adjusted(-6, -6, 6, 6)
        shell_path = QPainterPath()
        shell_path.addRoundedRect(QRectF(phone_shell), 16, 16)
        painter.fillPath(shell_path, QBrush(QColor("#0f172a")))
        painter.setPen(QPen(QColor("#cbd5e1"), 2))
        painter.drawPath(shell_path)

        # 2. 绘制实际真机屏幕原画截图 (绝对无满屏方格)
        screen_path = QPainterPath()
        screen_path.addRoundedRect(QRectF(draw_rect), 10, 10)
        painter.save()
        painter.setClipPath(screen_path)
        scaled_pixmap = self.pixmap.scaled(
            draw_rect.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(draw_rect.topLeft(), scaled_pixmap)
        painter.restore()

        scale_x = draw_rect.width() / self.orig_w
        scale_y = draw_rect.height() / self.orig_h

        # 3. 审查模式交互高亮：仅高亮 Hover 与选中的单个目标元素
        if self.mode == InspectorMode.SELECT:
            # 鼠标悬停 (Hover) 单个组件
            if self.hover_node_id and self.hover_node_id in self.comp_map:
                h_comp = self.comp_map[self.hover_node_id]
                bx = int(draw_rect.x() + h_comp["left"] * scale_x)
                by = int(draw_rect.y() + h_comp["top"] * scale_y)
                bw = int(h_comp["width"] * scale_x)
                bh = int(h_comp["height"] * scale_y)

                painter.setPen(QPen(QColor("#0284c7"), 2, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(2, 132, 199, 35)))
                painter.drawRect(bx, by, bw, bh)

                # 顶部浮动类型标签小气泡
                tag_text = f" {h_comp['type']}  {h_comp['width']}×{h_comp['height']} "
                painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
                fm = painter.fontMetrics()
                tag_w = fm.horizontalAdvance(tag_text) + 8
                tag_h = 20
                tag_y = max(draw_rect.y() + 4, by - tag_h - 2)
                tag_rect = QRect(bx, tag_y, tag_w, tag_h)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor("#0284c7")))
                painter.drawRoundedRect(tag_rect, 4, 4)
                painter.setPen(QColor("#ffffff"))
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, tag_text)

            # 鼠标选中 (Selected) 单个组件
            if self.selected_node_id and self.selected_node_id in self.comp_map:
                s_comp = self.comp_map[self.selected_node_id]
                bx = int(draw_rect.x() + s_comp["left"] * scale_x)
                by = int(draw_rect.y() + s_comp["top"] * scale_y)
                bw = int(s_comp["width"] * scale_x)
                bh = int(s_comp["height"] * scale_y)

                painter.setPen(QPen(QColor("#ef4444"), 2.5))
                painter.setBrush(QBrush(QColor(239, 68, 68, 45)))
                painter.drawRect(bx, by, bw, bh)

        # 4. 滑动模式下绘制交互手势轨迹
        if self.mode == InspectorMode.SWIPE and self.is_dragging and self.swipe_start_pos and self.swipe_cur_pos:
            pen_arrow = QPen(QColor("#0284c7"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arrow)
            painter.drawLine(self.swipe_start_pos, self.swipe_cur_pos)
            painter.setBrush(QBrush(QColor("#0284c7")))
            painter.drawEllipse(self.swipe_start_pos, 5, 5)
            painter.drawEllipse(self.swipe_cur_pos, 7, 7)

    def mouseMoveEvent(self, event):
        draw_rect = self.get_draw_rect()
        if draw_rect.isEmpty() or not draw_rect.contains(event.pos()):
            if self.hover_node_id:
                self.hover_node_id = ""
                self.update()
            return

        if self.mode == InspectorMode.SWIPE and self.is_dragging:
            self.swipe_cur_pos = event.pos()
            self.update()
            return

        if self.mode == InspectorMode.SELECT:
            scale_x = draw_rect.width() / self.orig_w
            scale_y = draw_rect.height() / self.orig_h
            dev_x = int((event.pos().x() - draw_rect.x()) / scale_x)
            dev_y = int((event.pos().y() - draw_rect.y()) / scale_y)

            # 寻找命中叶子组件（最小面积）
            hit_id = ""
            min_area = float("inf")
            for comp in self.flat_components:
                if comp["left"] <= dev_x <= comp["right"] and comp["top"] <= dev_y <= comp["bottom"]:
                    area = comp["width"] * comp["height"]
                    if area < min_area:
                        min_area = area
                        hit_id = comp["node_id"]

            if hit_id != self.hover_node_id:
                self.hover_node_id = hit_id
                self.update()

    def mousePressEvent(self, event):
        draw_rect = self.get_draw_rect()
        if draw_rect.isEmpty() or not draw_rect.contains(event.pos()):
            return

        scale_x = draw_rect.width() / self.orig_w
        scale_y = draw_rect.height() / self.orig_h
        dev_x = int((event.pos().x() - draw_rect.x()) / scale_x)
        dev_y = int((event.pos().y() - draw_rect.y()) / scale_y)

        if self.mode == InspectorMode.SELECT:
            if event.button() == Qt.MouseButton.LeftButton and self.hover_node_id:
                if self.selected_node_id != self.hover_node_id:
                    self.selected_node_id = self.hover_node_id
                    self.update()
                    self.element_selected.emit(self.selected_node_id)

        elif self.mode == InspectorMode.TAP:
            if event.button() == Qt.MouseButton.LeftButton:
                self.coordinate_tapped.emit(dev_x, dev_y)

        elif self.mode == InspectorMode.SWIPE:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = True
                self.swipe_start_pos = event.pos()
                self.swipe_cur_pos = event.pos()
                self.update()

    def mouseReleaseEvent(self, event):
        if self.mode == InspectorMode.SWIPE and self.is_dragging:
            self.is_dragging = False
            draw_rect = self.get_draw_rect()
            if self.swipe_start_pos and self.swipe_cur_pos and not draw_rect.isEmpty():
                scale_x = draw_rect.width() / self.orig_w
                scale_y = draw_rect.height() / self.orig_h
                x1 = int((self.swipe_start_pos.x() - draw_rect.x()) / scale_x)
                y1 = int((self.swipe_start_pos.y() - draw_rect.y()) / scale_y)
                x2 = int((self.swipe_cur_pos.x() - draw_rect.x()) / scale_x)
                y2 = int((self.swipe_cur_pos.y() - draw_rect.y()) / scale_y)
                self.swipe_start_pos = None
                self.swipe_cur_pos = None
                self.update()
                self.coordinate_swiped.emit(x1, y1, x2, y2)


# ==============================================================================
# 现代浅色高级感：Search for element 对话框
# ==============================================================================

class SearchElementDialog(QDialog):
    """
    全中文纯白轻奢定位搜索弹窗
    """
    element_picked = pyqtSignal(str)
    tap_requested = pyqtSignal(str)
    send_keys_requested = pyqtSignal(str, str)

    def __init__(self, flat_components: List[Dict[str, Any]], xml_root: Optional[ET.Element], parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔎 元素定位与查找器 (Search for element)")
        self.resize(720, 540)
        self.flat_components = flat_components
        self.xml_root = xml_root
        self.matched_components: List[Dict[str, Any]] = []

        self.apply_theme()
        self.init_ui()

    def apply_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; color: #1e293b; }
            QLabel { color: #334155; font-size: 13px; font-weight: 600; }
            QComboBox {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 7px 12px; font-size: 13px; min-height: 24px;
            }
            QComboBox:hover { border-color: #0284c7; }
            QLineEdit {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 4px 10px; font-size: 13px; min-height: 28px;
            }
            QLineEdit:focus { border: 1px solid #0284c7; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
                color: #ffffff; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 600; font-size: 13px; min-height: 22px;
            }
            QPushButton:hover { opacity: 0.9; }
            QPushButton#btnCancel { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
            QPushButton#btnCancel:hover { background: #e2e8f0; color: #0f172a; }
            QListWidget {
                background-color: #f8fafc; border: 1px solid #e2e8f0;
                border-radius: 6px; color: #0f172a; font-family: Consolas, monospace;
            }
            QListWidget::item { padding: 9px; border-bottom: 1px solid #f1f5f9; min-height: 24px; }
            QListWidget::item:selected {
                background-color: #e0f2fe; color: #0369a1; border-radius: 4px; font-weight: bold;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        layout.addWidget(QLabel("定位策略 (Locator Strategy):"))
        self.combo_strategy = QComboBox()
        self.combo_strategy.addItem("xpath (XPath 路径表达式)", "xpath")
        self.combo_strategy.addItem("id (组件 Key / ID 标识)", "id")
        self.combo_strategy.addItem("accessibility id (文本或无障碍描述)", "accessibility id")
        self.combo_strategy.addItem("class name (ArkUI 组件类型名)", "class name")
        layout.addWidget(self.combo_strategy)

        layout.addWidget(QLabel("选择器表达式 (Selector):"))
        self.edit_selector = QLineEdit()
        self.edit_selector.setPlaceholderText("例如: //Button[@text='发送'] 或组件 ID")
        layout.addWidget(self.edit_selector)

        btn_layout = QHBoxLayout()
        self.btn_search = QPushButton("🔍 查找匹配元素 (Search)")
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self.do_search)
        self.edit_selector.returnPressed.connect(self.do_search)
        btn_layout.addWidget(self.btn_search)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #0284c7; font-weight: 600;")
        btn_layout.addWidget(self.lbl_status, 1)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("匹配到的元素列表 (Elements Found):"))
        self.list_results = QListWidget()
        self.list_results.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_results, 1)

        bottom_box = QHBoxLayout()
        self.btn_tap = QPushButton("👆 点击该元素 (Tap)")
        self.btn_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tap.setEnabled(False)
        self.btn_tap.clicked.connect(self.on_tap_clicked)
        bottom_box.addWidget(self.btn_tap)

        self.btn_send_keys = QPushButton("⌨️ 输入文本内容 (Send Keys)")
        self.btn_send_keys.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_keys.setEnabled(False)
        self.btn_send_keys.clicked.connect(self.on_send_keys_clicked)
        bottom_box.addWidget(self.btn_send_keys)

        bottom_box.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setObjectName("btnCancel")
        btn_close.clicked.connect(self.accept)
        bottom_box.addWidget(btn_close)
        layout.addLayout(bottom_box)

    def do_search(self):
        strategy = self.combo_strategy.currentData()
        val = self.edit_selector.text().strip()
        self.list_results.clear()
        self.matched_components.clear()
        self.btn_tap.setEnabled(False)
        self.btn_send_keys.setEnabled(False)

        if not val:
            self.lbl_status.setText("请输入有效的定位表达式")
            return

        matched = []
        if strategy == "id":
            for c in self.flat_components:
                cid = c.get("id", "")
                if cid and (cid == val or val in cid):
                    matched.append(c)
        elif strategy == "accessibility id":
            for c in self.flat_components:
                text = c.get("text", "")
                desc = c.get("raw_attributes", {}).get("description", "")
                if (text and val in text) or (desc and val in desc):
                    matched.append(c)
        elif strategy == "class name":
            for c in self.flat_components:
                ctype = c.get("type", "")
                if ctype.lower() == val.lower():
                    matched.append(c)
        elif strategy == "xpath":
            matched = self.match_xpath(val)

        self.matched_components = matched
        self.lbl_status.setText(f"匹配到 {len(matched)} 个元素")

        if not matched:
            item = QListWidgetItem("未找到任何符合条件的元素")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(item)
            return

        for idx, comp in enumerate(matched):
            title = f"元素 {idx + 1} - <{comp['type']}"
            if comp['id']:
                title += f" id=\"{comp['id']}\""
            if comp['text']:
                title += f" text=\"{comp['text']}\""
            title += f" bounds=\"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]\">"
            list_item = QListWidgetItem(title)
            list_item.setData(Qt.ItemDataRole.UserRole, comp["node_id"])
            self.list_results.addItem(list_item)

        self.list_results.setCurrentRow(0)
        self.on_item_clicked(self.list_results.item(0))

    def match_xpath(self, xpath: str) -> List[Dict[str, Any]]:
        matched = []
        matched_node_ids = set()

        if self.xml_root is not None:
            try:
                xp = xpath
                if xp.startswith("//"):
                    xp = ".//" + xp[2:]
                elements = self.xml_root.findall(xp)
                for el in elements:
                    nid = el.get("node_id")
                    if nid:
                        matched_node_ids.add(nid)
            except Exception:
                pass

        if not matched_node_ids:
            for c in self.flat_components:
                hit = False
                c_text = c.get("text", "")
                c_id = c.get("id", "")
                c_type = c.get("type", "")

                if "@text=" in xpath:
                    exp_text = xpath.split("@text=")[1].strip("'\" ]")
                    if c_text == exp_text:
                        hit = True
                elif "contains(@text" in xpath:
                    m = re.search(r"contains\(@text,\s*['\"]([^'\"]+)['\"]\)", xpath)
                    if m and m.group(1) in c_text:
                        hit = True
                elif "@id=" in xpath:
                    exp_id = xpath.split("@id=")[1].strip("'\" ]")
                    if c_id == exp_id:
                        hit = True
                elif "contains(@id" in xpath:
                    m = re.search(r"contains\(@id,\s*['\"]([^'\"]+)['\"]\)", xpath)
                    if m and m.group(1) in c_id:
                        hit = True
                elif xpath.startswith("//") or xpath.startswith(".//"):
                    tag = xpath.replace(".//", "").replace("//", "").split("[")[0].strip()
                    if tag == "*" or c_type == tag:
                        hit = True

                if hit:
                    matched_node_ids.add(c["node_id"])

        for c in self.flat_components:
            if c["node_id"] in matched_node_ids:
                matched.append(c)
        return matched

    def on_item_clicked(self, item: QListWidgetItem):
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self.btn_tap.setEnabled(True)
            self.btn_send_keys.setEnabled(True)
            self.element_picked.emit(node_id)

    def on_tap_clicked(self):
        curr = self.list_results.currentItem()
        if curr:
            node_id = curr.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.tap_requested.emit(node_id)

    def on_send_keys_clicked(self):
        curr = self.list_results.currentItem()
        if curr:
            node_id = curr.data(Qt.ItemDataRole.UserRole)
            if node_id:
                text, ok = QInputDialog.getText(self, "输入文本", "请输入要发送至该元素的文本内容:")
                if ok and text:
                    self.send_keys_requested.emit(node_id, text)


# ==============================================================================
# 主窗口：现代纯白轻奢 UI 鸿蒙 Appium Inspector (实时输入同步增强版)
# ==============================================================================

class HarmonyAppiumInspector(QMainWindow):
    """纯血鸿蒙专属高颜值纯白桌面审查器"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HarmonyOS Appium Inspector - 鸿蒙专属桌面端元素审查器")
        self.resize(1560, 960)
        self.setMinimumSize(950, 650)

        self.current_udid: str = ""
        self.flat_components: List[Dict[str, Any]] = []
        self.comp_map: Dict[str, Dict[str, Any]] = {}
        self.tree_item_map: Dict[str, QTreeWidgetItem] = {}
        self.xml_root: Optional[ET.Element] = None
        self.node_counter = 0

        # 后台抓取线程
        self.capture_worker: Optional[CaptureWorker] = None

        self.apply_white_luxury_theme()
        self.init_ui()
        self.load_device_list()

    def apply_white_luxury_theme(self):
        """采用现代高级纯白 + 浅灰科技感设计系统 (全面杜绝文本被截断)"""
        self.setStyleSheet("""
            /* 全局基础背景与字体设置 */
            QMainWindow { background-color: #f1f5f9; }
            QWidget {
                color: #0f172a; font-family: 'Segoe UI', 'PingFang SC', sans-serif; font-size: 13px;
            }
            
            /* 顶部纯白卡片操作栏 */
            QFrame#topBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }
            QLabel#topBrand {
                font-weight: 800; color: #0284c7; font-size: 16px; margin-right: 6px;
            }
            
            /* 设备选择下拉框 */
            QComboBox {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 6px 14px; font-weight: 500; min-height: 22px;
            }
            QComboBox:hover { border-color: #0284c7; }
            
            /* 模式切换按钮 (审查 / 点击 / 滑动) */
            QPushButton.mode-btn {
                background-color: #ffffff; color: #334155; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 7px 15px; font-weight: 600; min-height: 22px;
            }
            QPushButton.mode-btn:hover {
                background-color: #f8fafc; border-color: #0284c7; color: #0284c7;
            }
            QPushButton.mode-btn:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
                color: #ffffff; border: 1px solid #0284c7; font-weight: bold;
            }
            
            /* 功能动作按钮 */
            QPushButton.action-btn {
                background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 7px 14px; font-weight: 600; min-height: 22px;
            }
            QPushButton.action-btn:hover {
                background-color: #f8fafc; border-color: #94a3b8;
            }
            QPushButton.action-btn#btnRefresh {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                border: none; color: #ffffff;
            }
            QPushButton.action-btn#btnRefresh:hover { opacity: 0.9; }
            
            QPushButton.action-btn#btnSearch {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #8b5cf6);
                border: none; color: #ffffff;
            }
            QPushButton.action-btn#btnSearch:hover { opacity: 0.9; }
            
            /* 分割线与三栏背景容器 (自由拖拽手柄) */
            QSplitter::handle:horizontal {
                background-color: #e2e8f0; width: 6px; margin: 0px 1px; border-radius: 3px;
            }
            QSplitter::handle:horizontal:hover {
                background-color: #0ea5e9;
            }
            QFrame.panel-card {
                background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
            }
            
            /* App Source DOM 树形视图 (充足行高 + 底部横向拖动条) */
            QTreeWidget {
                background-color: #ffffff; border: 1px solid #e2e8f0;
                border-radius: 8px; padding: 6px; color: #0f172a; font-family: Consolas, monospace;
            }
            QTreeWidget::item {
                min-height: 28px; padding: 4px 6px; border-radius: 4px; margin-bottom: 2px;
            }
            QTreeWidget::item:hover {
                background-color: #f1f5f9;
            }
            QTreeWidget::item:selected {
                background-color: #e0f2fe; color: #0369a1; font-weight: bold;
            }
            
            /* 精致横向与纵向滚动拖动条 */
            QScrollBar:horizontal {
                background: #f1f5f9; height: 10px; margin: 0px; border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #cbd5e1; min-width: 30px; border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #0284c7;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px; height: 0px;
            }
            QScrollBar:vertical {
                background: #f1f5f9; width: 10px; margin: 0px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1; min-height: 30px; border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0284c7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                width: 0px; height: 0px;
            }
            
            /* 属性表格 */
            QTableWidget {
                background-color: #ffffff; border: 1px solid #e2e8f0;
                border-radius: 8px; gridline-color: #f1f5f9; color: #0f172a;
            }
            QHeaderView::section {
                background-color: #f8fafc; color: #475569; border: none;
                border-bottom: 1px solid #e2e8f0; padding: 8px 10px; font-weight: 700;
            }
            
            /* 定位器复制输入框：去除过大垂直 padding，提供充足垂直渲染高度 */
            QLineEdit {
                background-color: #ffffff; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 2px 10px; color: #0f172a;
                font-family: 'Segoe UI', 'PingFang SC', Consolas, sans-serif; font-size: 13px;
                selection-background-color: #0284c7; selection-color: #ffffff;
            }
            QLineEdit:focus { border: 1px solid #0284c7; }
            
            /* 面包屑导航栏：支持多行舒展展示 */
            QLabel#breadcrumb {
                background-color: #f8fafc; border: 1px solid #e2e8f0;
                border-radius: 6px; padding: 8px 12px; color: #0284c7;
                font-family: 'Segoe UI', 'PingFang SC', Consolas, sans-serif; font-size: 12px;
                line-height: 1.4;
            }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------------------------------------------------------------
        # 1. 顶部操作栏 (全中文高质感按钮，悬停均带小手形态)
        # ----------------------------------------------------------------------
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 10, 16, 10)
        top_layout.setSpacing(10)

        lbl_brand = QLabel("鸿蒙 UI 审查器")
        lbl_brand.setObjectName("topBrand")
        top_layout.addWidget(lbl_brand)

        top_layout.addWidget(QLabel("当前设备:"))
        self.combo_devices = QComboBox()
        self.combo_devices.setMinimumWidth(220)
        self.combo_devices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_devices.currentIndexChanged.connect(self.on_device_changed)
        top_layout.addWidget(self.combo_devices)

        top_layout.addSpacing(16)

        # 模式切换按钮 (全中文)
        self.btn_mode_select = QPushButton("🎯 元素审查")
        self.btn_mode_select.setProperty("class", "mode-btn")
        self.btn_mode_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_select.setCheckable(True)
        self.btn_mode_select.setChecked(True)
        self.btn_mode_select.clicked.connect(lambda: self.switch_mode(InspectorMode.SELECT))
        top_layout.addWidget(self.btn_mode_select)

        self.btn_mode_tap = QPushButton("👆 坐标点击")
        self.btn_mode_tap.setProperty("class", "mode-btn")
        self.btn_mode_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_tap.setCheckable(True)
        self.btn_mode_tap.clicked.connect(lambda: self.switch_mode(InspectorMode.TAP))
        top_layout.addWidget(self.btn_mode_tap)

        self.btn_mode_swipe = QPushButton("🖐 滑动模拟")
        self.btn_mode_swipe.setProperty("class", "mode-btn")
        self.btn_mode_swipe.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_swipe.setCheckable(True)
        self.btn_mode_swipe.clicked.connect(lambda: self.switch_mode(InspectorMode.SWIPE))
        top_layout.addWidget(self.btn_mode_swipe)

        top_layout.addSpacing(16)

        # 核心动作按钮 (全部加上小手光标)
        btn_back = QPushButton("🔙 返回")
        btn_back.setProperty("class", "action-btn")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self.action_back)
        top_layout.addWidget(btn_back)

        btn_home = QPushButton("🏠 桌面")
        btn_home.setProperty("class", "action-btn")
        btn_home.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_home.clicked.connect(self.action_home)
        top_layout.addWidget(btn_home)

        self.btn_refresh = QPushButton("🔄 刷新界面")
        self.btn_refresh.setProperty("class", "action-btn")
        self.btn_refresh.setObjectName("btnRefresh")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_screen_and_dom)
        top_layout.addWidget(self.btn_refresh)

        btn_search_modal = QPushButton("🔎 定位元素")
        btn_search_modal.setProperty("class", "action-btn")
        btn_search_modal.setObjectName("btnSearch")
        btn_search_modal.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_modal.clicked.connect(self.open_search_dialog)
        top_layout.addWidget(btn_search_modal)

        top_layout.addStretch()

        btn_copy_xml = QPushButton("📋 复制源码")
        btn_copy_xml.setProperty("class", "action-btn")
        btn_copy_xml.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy_xml.clicked.connect(self.copy_xml_source)
        top_layout.addWidget(btn_copy_xml)

        btn_save_shot = QPushButton("💾 保存截图")
        btn_save_shot.setProperty("class", "action-btn")
        btn_save_shot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save_shot.clicked.connect(self.save_screenshot)
        top_layout.addWidget(btn_save_shot)

        main_layout.addWidget(top_bar)

        # ----------------------------------------------------------------------
        # 2. 核心三栏布局 (支持自由调整大小，绝对不隐藏)
        # ----------------------------------------------------------------------
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # ------------------ 左栏：真机屏幕画面 ------------------
        left_container = QFrame()
        left_container.setProperty("class", "panel-card")
        left_container.setMinimumWidth(220)
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        lbl_left_title = QLabel("📱 设备真机画面 (Device Screen)")
        lbl_left_title.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px;")
        left_layout.addWidget(lbl_left_title)

        self.canvas = AppiumScreenView()
        self.canvas.element_selected.connect(self.on_canvas_element_selected)
        self.canvas.coordinate_tapped.connect(self.on_canvas_coordinate_tapped)
        self.canvas.coordinate_swiped.connect(self.on_canvas_coordinate_swiped)
        left_layout.addWidget(self.canvas, 1)

        self.splitter.addWidget(left_container)

        # ------------------ 中栏：DOM 组件层级树 (支持横向拖动条) ------------------
        mid_container = QFrame()
        mid_container.setProperty("class", "panel-card")
        mid_container.setMinimumWidth(240)
        mid_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mid_layout = QVBoxLayout(mid_container)
        mid_layout.setContentsMargins(14, 14, 14, 14)
        mid_layout.setSpacing(10)

        tree_header = QHBoxLayout()
        lbl_mid_title = QLabel("🌳 DOM 组件层级树 (App Source)")
        lbl_mid_title.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px;")
        tree_header.addWidget(lbl_mid_title)
        tree_header.addStretch()

        btn_expand = QPushButton("展开全部")
        btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_expand.setStyleSheet("padding: 4px 10px; font-size: 11px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; color: #334155;")
        btn_expand.clicked.connect(lambda: self.tree_widget.expandAll())
        tree_header.addWidget(btn_expand)

        btn_collapse = QPushButton("折叠全部")
        btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_collapse.setStyleSheet("padding: 4px 10px; font-size: 11px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; color: #334155;")
        btn_collapse.clicked.connect(lambda: self.tree_widget.collapseAll())
        tree_header.addWidget(btn_collapse)
        mid_layout.addLayout(tree_header)

        # 面包屑路径 (开启自动换行，绝不单行截断溢出)
        self.lbl_breadcrumb = QLabel("📍 路径: Hierarchy (根节点)")
        self.lbl_breadcrumb.setObjectName("breadcrumb")
        self.lbl_breadcrumb.setWordWrap(True)
        mid_layout.addWidget(self.lbl_breadcrumb)

        # 树视图：开启横向与纵向平滑滚动条，解除截断
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["ArkUI 组件层次结构"])
        self.tree_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_widget.header().setStretchLastSection(False)
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        mid_layout.addWidget(self.tree_widget, 1)

        self.splitter.addWidget(mid_container)

        # ------------------ 右栏：Selected Element 面板 ------------------
        right_container = QFrame()
        right_container.setProperty("class", "panel-card")
        right_container.setMinimumWidth(300)
        right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(12)

        lbl_right_title = QLabel("🔍 选中组件属性与定位器 (Selected Element)")
        lbl_right_title.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px;")
        right_layout.addWidget(lbl_right_title)

        # 动作工具箱 (悬浮小手)
        act_box = QFrame()
        act_box.setStyleSheet("background-color: #f8fafc; border-radius: 6px; padding: 6px; border: 1px solid #e2e8f0;")
        act_layout = QHBoxLayout(act_box)
        act_layout.setContentsMargins(8, 6, 8, 6)
        act_layout.setSpacing(10)

        self.btn_elem_tap = QPushButton("👆 点击该元素")
        self.btn_elem_tap.setEnabled(False)
        self.btn_elem_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_elem_tap.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981); color: #fff; font-weight: 600; padding: 7px 14px; border-radius: 4px; border: none; min-height: 22px;")
        self.btn_elem_tap.clicked.connect(self.action_element_tap)
        act_layout.addWidget(self.btn_elem_tap)

        self.btn_elem_send_keys = QPushButton("⌨️ 向元素输入")
        self.btn_elem_send_keys.setEnabled(False)
        self.btn_elem_send_keys.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_elem_send_keys.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9); color: #fff; font-weight: 600; padding: 7px 14px; border-radius: 4px; border: none; min-height: 22px;")
        self.btn_elem_send_keys.clicked.connect(self.action_element_send_keys)
        act_layout.addWidget(self.btn_elem_send_keys)

        self.btn_elem_clear = QPushButton("🧹 清空文本")
        self.btn_elem_clear.setEnabled(False)
        self.btn_elem_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_elem_clear.setStyleSheet("background: #64748b; color: #fff; font-weight: 600; padding: 7px 14px; border-radius: 4px; border: none; min-height: 22px;")
        self.btn_elem_clear.clicked.connect(self.action_element_clear)
        act_layout.addWidget(self.btn_elem_clear)

        act_layout.addStretch()
        right_layout.addWidget(act_box)

        # ----------------------------------------------------------------------
        # 新增：输入框/编辑框专属【实时输入同步控制台】 (Live Input Sync)
        # ----------------------------------------------------------------------
        self.input_sync_box = QFrame()
        self.input_sync_box.setStyleSheet("background-color: #f0fdf4; border-radius: 8px; padding: 12px; border: 1px solid #bbf7d0;")
        sync_layout = QVBoxLayout(self.input_sync_box)
        sync_layout.setContentsMargins(10, 8, 10, 8)
        sync_layout.setSpacing(8)

        lbl_sync_title = QLabel("✍️ 输入框内容实时同步编辑框 (实时同步至真机与 DOM)")
        lbl_sync_title.setStyleSheet("color: #166534; font-weight: 700; font-size: 13px;")
        sync_layout.addWidget(lbl_sync_title)

        row_sync = QHBoxLayout()
        row_sync.setSpacing(8)

        self.edit_live_input = QLineEdit()
        self.edit_live_input.setMinimumHeight(38)
        self.edit_live_input.setPlaceholderText("在此输入文字，按回车或点同步即刻下发真机并更新界面...")
        self.edit_live_input.returnPressed.connect(self.sync_live_input)
        row_sync.addWidget(self.edit_live_input, 1)

        self.btn_sync_send = QPushButton("🚀 实时同步")
        self.btn_sync_send.setMinimumHeight(38)
        self.btn_sync_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_send.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16a34a, stop:1 #22c55e); color: #fff; font-weight: 700; border: none; border-radius: 6px; padding: 0 16px; font-size: 13px;")
        self.btn_sync_send.clicked.connect(self.sync_live_input)
        row_sync.addWidget(self.btn_sync_send)

        self.btn_sync_clear = QPushButton("🧹 清空")
        self.btn_sync_clear.setMinimumHeight(38)
        self.btn_sync_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_clear.setStyleSheet("background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1; border-radius: 6px; padding: 0 12px; font-weight: 600; font-size: 13px;")
        self.btn_sync_clear.clicked.connect(self.action_element_clear)
        row_sync.addWidget(self.btn_sync_clear)

        sync_layout.addLayout(row_sync)
        right_layout.addWidget(self.input_sync_box)

        # 定位器推荐与一键复制卡片 (使用 QGridLayout 像素级网格严格对齐，彻底消除文字截断)
        loc_box = QFrame()
        loc_box.setStyleSheet("background-color: #f8fafc; border-radius: 8px; padding: 14px; border: 1px solid #e2e8f0;")
        loc_layout = QVBoxLayout(loc_box)
        loc_layout.setSpacing(10)

        lbl_loc_title = QLabel("🚀 自动化定位代码推荐 (一键复制到 Page Object)")
        lbl_loc_title.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 13px;")
        loc_layout.addWidget(lbl_loc_title)

        grid_loc = QGridLayout()
        grid_loc.setContentsMargins(0, 4, 0, 4)
        grid_loc.setHorizontalSpacing(10)
        grid_loc.setVerticalSpacing(10)

        # 1. ID 行：宽度扩充为 82px，绝不截断标签
        lbl_id = QLabel("id:")
        lbl_id.setFixedWidth(82)
        lbl_id.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_id.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px; font-family: Consolas, monospace;")
        self.txt_loc_id = QLineEdit()
        self.txt_loc_id.setMinimumHeight(38)
        self.txt_loc_id.setReadOnly(True)
        self.txt_loc_id.setPlaceholderText("ID 定位代码: (该元素无 ID)")
        btn_cp_id = QPushButton("复制")
        btn_cp_id.setMinimumHeight(38)
        btn_cp_id.setFixedWidth(68)
        btn_cp_id.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cp_id.setStyleSheet("background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; border-radius: 6px; font-weight: 700; font-size: 13px;")
        btn_cp_id.clicked.connect(lambda: self.copy_to_clip(self.txt_loc_id.text()))
        grid_loc.addWidget(lbl_id, 0, 0)
        grid_loc.addWidget(self.txt_loc_id, 0, 1)
        grid_loc.addWidget(btn_cp_id, 0, 2)

        # 2. XPath 行：宽度扩充为 82px，完整呈现 xpath:
        lbl_xp = QLabel("xpath:")
        lbl_xp.setFixedWidth(82)
        lbl_xp.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_xp.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px; font-family: Consolas, monospace;")
        self.txt_loc_xpath = QLineEdit()
        self.txt_loc_xpath.setMinimumHeight(38)
        self.txt_loc_xpath.setReadOnly(True)
        self.txt_loc_xpath.setPlaceholderText("XPath 表达式")
        btn_cp_xp = QPushButton("复制")
        btn_cp_xp.setMinimumHeight(38)
        btn_cp_xp.setFixedWidth(68)
        btn_cp_xp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cp_xp.setStyleSheet("background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; border-radius: 6px; font-weight: 700; font-size: 13px;")
        btn_cp_xp.clicked.connect(lambda: self.copy_to_clip(self.txt_loc_xpath.text()))
        grid_loc.addWidget(lbl_xp, 1, 0)
        grid_loc.addWidget(self.txt_loc_xpath, 1, 1)
        grid_loc.addWidget(btn_cp_xp, 1, 2)

        # 3. Python 行：宽度扩充为 82px，完整呈现 python:
        lbl_py = QLabel("python:")
        lbl_py.setFixedWidth(82)
        lbl_py.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_py.setStyleSheet("color: #475569; font-weight: 700; font-size: 13px; font-family: Consolas, monospace;")
        self.txt_loc_py = QLineEdit()
        self.txt_loc_py.setMinimumHeight(38)
        self.txt_loc_py.setReadOnly(True)
        self.txt_loc_py.setPlaceholderText("Python 语句")
        btn_cp_py = QPushButton("复制")
        btn_cp_py.setMinimumHeight(38)
        btn_cp_py.setFixedWidth(68)
        btn_cp_py.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cp_py.setStyleSheet("background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; border-radius: 6px; font-weight: 700; font-size: 13px;")
        btn_cp_py.clicked.connect(lambda: self.copy_to_clip(self.txt_loc_py.text()))
        grid_loc.addWidget(lbl_py, 2, 0)
        grid_loc.addWidget(self.txt_loc_py, 2, 1)
        grid_loc.addWidget(btn_cp_py, 2, 2)

        loc_layout.addLayout(grid_loc)
        right_layout.addWidget(loc_box)

        # 详细属性表 (优化默认行高与文本展示，消除上下截断)
        lbl_attr_header = QLabel("📋 详细属性清单 (Attributes)")
        lbl_attr_header.setStyleSheet("color: #475569; font-weight: 700; margin-top: 4px;")
        right_layout.addWidget(lbl_attr_header)

        self.table_attrs = QTableWidget()
        self.table_attrs.setColumnCount(2)
        self.table_attrs.setHorizontalHeaderLabels(["属性名称 (Attribute)", "属性值 (Value)"])
        self.table_attrs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_attrs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_attrs.verticalHeader().setDefaultSectionSize(34)
        self.table_attrs.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right_layout.addWidget(self.table_attrs, 1)

        self.splitter.addWidget(right_container)

        # 初始分配比例：4 : 4 : 3
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setStretchFactor(2, 3)

        main_layout.addWidget(self.splitter, 1)

    # --------------------------------------------------------------------------
    # 设备与界面刷新 (使用异步多线程，绝不卡死主界面)
    # --------------------------------------------------------------------------

    def load_device_list(self):
        devices = get_connected_devices()
        self.combo_devices.clear()
        if devices:
            for dev in devices:
                self.combo_devices.addItem(f"鸿蒙真机: {dev}", dev)
            self.current_udid = devices[0]
            self.refresh_screen_and_dom()
        else:
            self.combo_devices.addItem("未检测到在线鸿蒙设备", "")
            self.current_udid = ""

    def on_device_changed(self, index: int):
        udid = self.combo_devices.currentData()
        if udid and udid != self.current_udid:
            self.current_udid = udid
            self.refresh_screen_and_dom()

    def refresh_screen_and_dom(self):
        """核心：通过后台异步线程执行真机截图与 dumpLayout 构建"""
        if not self.current_udid:
            QMessageBox.warning(self, "设备未连接", "未检测到在线的鸿蒙真机，请确认已开启 USB 调试并运行 hdc list targets 确认设备状态。")
            return

        if self.capture_worker and self.capture_worker.isRunning():
            return

        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("⏳ 正在刷新...")

        tmp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "inspector")
        os.makedirs(tmp_dir, exist_ok=True)

        self.capture_worker = CaptureWorker(self.current_udid, tmp_dir)
        self.capture_worker.finished.connect(self.on_capture_success)
        self.capture_worker.failed.connect(self.on_capture_failed)
        self.capture_worker.start()

    def on_capture_success(self, local_png: str, local_json: str):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("🔄 刷新界面")

        prev_selected_id = self.canvas.selected_node_id

        with open(local_json, "r", encoding="utf-8") as f:
            raw_tree = json.load(f)

        self.flat_components.clear()
        self.comp_map.clear()
        self.tree_item_map.clear()
        self.tree_widget.clear()
        self.node_counter = 0

        self.xml_root = ET.Element("Hierarchy", {"platform": "HarmonyOS", "udid": self.current_udid})
        self.build_dom_tree(raw_tree, None, self.xml_root, "/Hierarchy")

        # 加载到左栏视窗
        self.canvas.load_screenshot(local_png, self.flat_components)
        self.tree_widget.expandToDepth(2)

        # 重新锁定原先选中的节点，保持状态连贯
        if prev_selected_id and prev_selected_id in self.comp_map:
            self.select_element_by_id(prev_selected_id)

    def on_capture_failed(self, err_msg: str):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("🔄 刷新界面")
        QMessageBox.critical(self, "抓取失败", f"无法获取鸿蒙真机界面与布局:\n{err_msg}")

    def build_dom_tree(self, node: Dict[str, Any], parent_item: Optional[QTreeWidgetItem], xml_parent: ET.Element, current_xpath: str):
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1

        attrs = node.get("attributes", {})
        bounds_str = attrs.get("bounds", "[0,0][0,0]")
        match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
        left, top, right, bottom = 0, 0, 0, 0
        if match:
            left, top, right, bottom = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))

        width = max(0, right - left)
        height = max(0, bottom - top)
        c_type = attrs.get("type", "Component")
        c_id = attrs.get("id") or attrs.get("key") or ""
        c_text = attrs.get("text") or attrs.get("originalText") or ""

        node_xpath = f"{current_xpath}/{c_type}"
        
        # 推荐定位器
        rec_id = c_id if c_id else ""
        if c_id:
            rec_xpath = f"//{c_type}[@id='{c_id}']"
            rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
        elif c_text:
            rec_xpath = f"//{c_type}[@text='{c_text}']"
            rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{c_type}[@text='{c_text}']\")"
        else:
            rec_xpath = node_xpath
            rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"

        comp = {
            "node_id": node_id,
            "type": c_type,
            "id": c_id,
            "text": c_text,
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "width": width,
            "height": height,
            "center_x": left + width // 2,
            "center_y": top + height // 2,
            "xpath": node_xpath,
            "rec_xpath": rec_xpath,
            "rec_id": rec_id,
            "rec_py": rec_py,
            "rec_class": c_type,
            "raw_attributes": attrs
        }

        if width > 0 and height > 0:
            self.flat_components.append(comp)
        self.comp_map[node_id] = comp

        xml_elem = ET.SubElement(xml_parent, c_type, {
            "node_id": node_id,
            "id": c_id,
            "text": c_text,
            "type": c_type,
            "bounds": bounds_str,
            "clickable": str(attrs.get("clickable", "")),
            "enabled": str(attrs.get("enabled", ""))
        })

        # 高颜值彩色节点标签渲染
        type_badge = f"<{c_type}"
        attrs_str = ""
        if c_id:
            attrs_str += f' id="{c_id}"'
        if c_text:
            short_t = c_text if len(c_text) <= 22 else c_text[:22] + "..."
            attrs_str += f' text="{short_t}"'
        attrs_str += f' bounds="{bounds_str}">'

        item = QTreeWidgetItem([f"{type_badge}{attrs_str}"])
        item.setData(0, Qt.ItemDataRole.UserRole, node_id)

        # 浅色背景下的优雅层次着色
        if c_type in ("Button", "Toggle"):
            item.setForeground(0, QColor("#0284c7"))  # 蓝
        elif c_type in ("Text", "Span"):
            item.setForeground(0, QColor("#d97706"))  # 暖金
        elif c_type in ("TextInput", "TextArea"):
            item.setForeground(0, QColor("#16a34a"))  # 翠绿
        elif c_type in ("Image", "QRCode"):
            item.setForeground(0, QColor("#e11d48"))  # 珊瑚红
        elif c_type in ("Column", "Row", "Scroll", "List", "Flex"):
            item.setForeground(0, QColor("#7c3aed"))  # 优雅紫
        else:
            item.setForeground(0, QColor("#475569"))  # 深灰

        self.tree_item_map[node_id] = item

        if parent_item:
            parent_item.addChild(item)
        else:
            self.tree_widget.addTopLevelItem(item)

        for child in node.get("children", []):
            self.build_dom_tree(child, item, xml_elem, node_xpath)

    # --------------------------------------------------------------------------
    # 模式切换与工具栏动作
    # --------------------------------------------------------------------------

    def switch_mode(self, mode: str):
        self.btn_mode_select.setChecked(mode == InspectorMode.SELECT)
        self.btn_mode_tap.setChecked(mode == InspectorMode.TAP)
        self.btn_mode_swipe.setChecked(mode == InspectorMode.SWIPE)
        self.canvas.set_mode(mode)

    def action_back(self):
        if self.current_udid:
            run_hdc(["shell", "uitest", "uiInput", "keyEvent", "Back"], self.current_udid)
            self.refresh_screen_and_dom()

    def action_home(self):
        if self.current_udid:
            run_hdc(["shell", "uitest", "uiInput", "keyEvent", "Home"], self.current_udid)
            self.refresh_screen_and_dom()

    def copy_xml_source(self):
        if self.xml_root is not None:
            xml_str = ET.tostring(self.xml_root, encoding="utf-8").decode("utf-8")
            QApplication.clipboard().setText(xml_str)
            QMessageBox.information(self, "复制成功", "当前界面的完整 XML 层次源码已成功复制到系统剪贴板！")

    def save_screenshot(self):
        if not self.canvas.pixmap or self.canvas.pixmap.isNull():
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存真机截图", "harmony_screen.png", "PNG Images (*.png)")
        if path:
            self.canvas.pixmap.save(path, "PNG")
            QMessageBox.information(self, "保存成功", f"截图已保存至:\n{path}")

    def open_search_dialog(self):
        dlg = SearchElementDialog(self.flat_components, self.xml_root, self)
        dlg.element_picked.connect(self.select_element_by_id)
        dlg.tap_requested.connect(self.direct_tap_element)
        dlg.send_keys_requested.connect(self.direct_send_keys_to_element)
        dlg.exec()

    # --------------------------------------------------------------------------
    # 核心：点击元素时 DOM 树窗口不改变展开折叠状态，极速定位
    # --------------------------------------------------------------------------

    def select_element_by_id(self, node_id: str):
        self.canvas.selected_node_id = node_id
        self.canvas.update()

        item = self.tree_item_map.get(node_id)
        if item:
            self.tree_widget.setCurrentItem(item)
            self.tree_widget.scrollToItem(item, QTreeWidget.ScrollHint.EnsureVisible)

        self.update_selected_element_panel(node_id)

    def on_canvas_element_selected(self, node_id: str):
        self.select_element_by_id(node_id)

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self.canvas.selected_node_id = node_id
            self.canvas.update()
            self.update_selected_element_panel(node_id)

    def on_canvas_coordinate_tapped(self, x: int, y: int):
        if self.current_udid:
            run_hdc(["shell", "uitest", "uiInput", "click", str(x), str(y)], self.current_udid)
            self.refresh_screen_and_dom()

    def on_canvas_coordinate_swiped(self, x1: int, y1: int, x2: int, y2: int):
        if self.current_udid:
            run_hdc(["shell", "uitest", "uiInput", "swipe", str(x1), str(y1), str(x2), str(y2), "600"], self.current_udid)
            self.refresh_screen_and_dom()

    def update_selected_element_panel(self, node_id: str):
        """刷新右侧 Selected Element 面板与实时输入同步栏"""
        comp = self.comp_map.get(node_id)
        if not comp:
            return

        self.btn_elem_tap.setEnabled(True)
        self.btn_elem_send_keys.setEnabled(True)
        self.btn_elem_clear.setEnabled(True)

        c_type = comp.get("type", "")
        c_text = comp.get("text", "")

        # 实时输入框预填当前组件现有文字
        self.edit_live_input.blockSignals(True)
        self.edit_live_input.setText(c_text)
        self.edit_live_input.blockSignals(False)

        # 智能感知：如果是输入/编辑框组件，高亮提示
        if c_type in ("TextInput", "TextArea", "Search") or "input" in c_type.lower():
            self.input_sync_box.setStyleSheet(
                "background-color: #ecfdf5; border-radius: 8px; padding: 12px; border: 1.5px solid #10b981;"
            )
        else:
            self.input_sync_box.setStyleSheet(
                "background-color: #f8fafc; border-radius: 8px; padding: 12px; border: 1px solid #e2e8f0;"
            )

        path_str = comp.get("xpath", "Hierarchy").replace("/", "  ›  ")
        self.lbl_breadcrumb.setText(f"📍 路径: {path_str}")

        # 推荐定位器
        self.txt_loc_id.setText(comp.get("rec_id", ""))
        self.txt_loc_xpath.setText(comp.get("rec_xpath", ""))
        self.txt_loc_py.setText(comp.get("rec_py", ""))

        self.txt_loc_id.setCursorPosition(0)
        self.txt_loc_xpath.setCursorPosition(0)
        self.txt_loc_py.setCursorPosition(0)

        # 快速填充属性列表
        raw = comp.get("raw_attributes", {})
        display_attrs = [
            ("id / key", comp.get("id", "-")),
            ("text / originalText", comp.get("text", "-")),
            ("class / type", comp.get("type", "-")),
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

        known_keys = {"id", "key", "text", "originalText", "type", "bounds", "bundleName", "clickable", "enabled", "focusable", "focused", "scrollable", "visible"}
        for k, v in raw.items():
            if k not in known_keys:
                display_attrs.append((f"raw: {k}", str(v)))

        self.table_attrs.setUpdatesEnabled(False)
        self.table_attrs.setRowCount(len(display_attrs))
        for row, (k, v) in enumerate(display_attrs):
            k_item = QTableWidgetItem(str(k))
            v_item = QTableWidgetItem(str(v))
            v_item.setToolTip(str(v))
            if any(key in k for key in ("id", "text", "class", "xpath", "bounds", "size")):
                k_item.setForeground(QColor("#0284c7"))
                v_item.setForeground(QColor("#d97706"))
                k_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            else:
                k_item.setForeground(QColor("#64748b"))
                v_item.setForeground(QColor("#0f172a"))
            self.table_attrs.setItem(row, 0, k_item)
            self.table_attrs.setItem(row, 1, v_item)
        self.table_attrs.setUpdatesEnabled(True)

    # --------------------------------------------------------------------------
    # 核心新增：实时输入同步 (Live Input & Device Sync)
    # --------------------------------------------------------------------------

    def sync_live_input(self):
        """将实时输入框中的文字下发到鸿蒙真机，并即时同步全量视图"""
        curr_id = self.canvas.selected_node_id
        if not curr_id:
            QMessageBox.information(self, "提示", "请先在左侧或 DOM 树中选择目标输入框/编辑框组件！")
            return

        text = self.edit_live_input.text()
        self.direct_send_keys_to_element(curr_id, text)

    def action_element_tap(self):
        curr_id = self.canvas.selected_node_id
        if curr_id:
            self.direct_tap_element(curr_id)

    def direct_tap_element(self, node_id: str):
        comp = self.comp_map.get(node_id)
        if comp and self.current_udid:
            cx, cy = comp["center_x"], comp["center_y"]
            run_hdc(["shell", "uitest", "uiInput", "click", str(cx), str(cy)], self.current_udid)
            self.refresh_screen_and_dom()

    def action_element_send_keys(self):
        curr_id = self.canvas.selected_node_id
        if curr_id:
            comp = self.comp_map.get(curr_id, {})
            curr_text = comp.get("text", "")
            text, ok = QInputDialog.getText(self, "输入文本", "请输入要发送至该元素的文本内容:", text=curr_text)
            if ok:
                self.direct_send_keys_to_element(curr_id, text)

    def direct_send_keys_to_element(self, node_id: str, text: str):
        """
        向目标组件下发文本，并实现零延迟的视图与真机双向实时同步：
        1. 下发 HDC 指令到真机执行物理输入
        2. 立即就地更新内存中该节点的 text 与 XPath 表达式
        3. 即时刷新 DOM 树、属性表格、实时输入框
        4. 异步刷新真机原画截图并重新锚定当前节点
        """
        comp = self.comp_map.get(node_id)
        if not comp or not self.current_udid:
            return

        cx, cy = comp["center_x"], comp["center_y"]
        # 先下发点击聚焦，再注入文本
        run_hdc(["shell", "uitest", "uiInput", "click", str(cx), str(cy)], self.current_udid)
        run_hdc(["shell", "uitest", "uiInput", "inputText", str(cx), str(cy), text], self.current_udid)

        # 1. 立即就地同步内存对象中的属性
        comp["text"] = text
        comp["raw_attributes"]["text"] = text
        comp["raw_attributes"]["originalText"] = text

        # 2. 立即更新推荐定位代码
        c_type = comp.get("type", "Component")
        c_id = comp.get("id", "")
        if c_id:
            rec_xpath = f"//{c_type}[@id='{c_id}']"
            rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
        elif text:
            rec_xpath = f"//{c_type}[@text='{text}']"
            rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{c_type}[@text='{text}']\")"
        else:
            rec_xpath = comp.get("xpath", "")
            rec_py = f"driver.find_element(AppiumBy.XPATH, \"{rec_xpath}\")"

        comp["rec_xpath"] = rec_xpath
        comp["rec_py"] = rec_py

        # 3. 立即就地更新 DOM 树该节点标签
        item = self.tree_item_map.get(node_id)
        if item:
            bounds_str = f"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]"
            short_t = text if len(text) <= 22 else text[:22] + "..."
            id_attr = f' id="{c_id}"' if c_id else ""
            txt_attr = f' text="{short_t}"' if text else ""
            item.setText(0, f"<{c_type}{id_attr}{txt_attr} bounds=\"{bounds_str}\">")

        # 4. 立即更新右侧属性表与实时输入框
        self.update_selected_element_panel(node_id)

        # 5. 后台异步捕获真机输入后的真实截图，同步左侧真机视窗
        self.refresh_screen_and_dom()

    def action_element_clear(self):
        """清空该输入框/编辑框内容并即时同步"""
        curr_id = self.canvas.selected_node_id
        comp = self.comp_map.get(curr_id)
        if comp and self.current_udid:
            cx, cy = comp["center_x"], comp["center_y"]
            run_hdc(["shell", "uitest", "uiInput", "click", str(cx), str(cy)], self.current_udid)
            # 发送退格删除
            for _ in range(35):
                run_hdc(["shell", "uitest", "uiInput", "keyEvent", "2055"], self.current_udid)
            
            # 本地属性立即同步清空
            comp["text"] = ""
            comp["raw_attributes"]["text"] = ""
            comp["raw_attributes"]["originalText"] = ""
            self.edit_live_input.setText("")
            self.update_selected_element_panel(curr_id)
            
            # 后台刷新最新画面
            self.refresh_screen_and_dom()

    def copy_to_clip(self, text: str):
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "复制成功", f"内容已复制到剪贴板:\n{text}")


def main():
    app = QApplication(sys.argv)
    window = HarmonyAppiumInspector()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
