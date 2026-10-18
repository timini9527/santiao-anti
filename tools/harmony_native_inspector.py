# -*- coding: utf-8 -*-
"""
=======================================================
HarmonyOS Native Inspector (纯血鸿蒙纯原生桌面审查器)
=======================================================
基于 PyQt6 原生 C++ 渲染管线，100% 纯桌面独立 GUI 应用程序，
绝不调用外部浏览器，绝不使用 WebView 壳子。
提供真机屏幕映射、DOM 组件树交互浏览、XPath / ID 实时搜索与定位代码生成。
"""
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, pyqtSignal
from PyQt6.QtGui import (
    QAction, QBrush, QColor, QFont, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap
)
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)


def get_connected_device() -> str:
    """获取当前连接的鸿蒙真机 UDID"""
    try:
        out = subprocess.check_output(["hdc", "list", "targets"], text=True, errors="ignore").strip()
        lines = [line.strip() for line in out.splitlines() if line.strip() and "empty" not in line.lower()]
        if lines:
            return lines[0]
    except Exception:
        pass
    try:
        import yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "devices.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("devices", {}).get("dev", {}).get("harmony_sender", {}).get("udid", "")
    except Exception:
        pass
    return ""


def run_hdc(cmd: List[str], udid: str = "") -> str:
    """执行 HDC 指令"""
    full_cmd = ["hdc"]
    if udid:
        full_cmd.extend(["-t", udid])
    full_cmd.extend(cmd)
    res = subprocess.run(full_cmd, capture_output=True, text=True, errors="ignore")
    return res.stdout.strip()


class ScreenCanvas(QWidget):
    """真机屏幕绘制画布：支持真实截图缩放、鼠标悬停黄色高亮、点击选中红色高亮"""
    element_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pixmap: Optional[QPixmap] = None
        self.flat_components: List[Dict[str, Any]] = []
        self.hover_node_id: str = ""
        self.selected_node_id: str = ""
        self.orig_w = 1084
        self.orig_h = 2412
        self.setStyleSheet("background-color: #0f1015; border-radius: 8px;")

    def load_data(self, img_path: str, components: List[Dict[str, Any]]):
        self.pixmap = QPixmap(img_path)
        if not self.pixmap.isNull():
            self.orig_w = self.pixmap.width()
            self.orig_h = self.pixmap.height()
        self.flat_components = components
        self.hover_node_id = ""
        self.selected_node_id = ""
        self.update()

    def get_draw_rect(self) -> QRect:
        if not self.pixmap or self.pixmap.isNull():
            return QRect()
        scaled = self.pixmap.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        return QRect(x, y, scaled.width(), scaled.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        draw_rect = self.get_draw_rect()
        if not self.pixmap or self.pixmap.isNull() or draw_rect.isEmpty():
            painter.setPen(QColor("#71717a"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "等待设备连接与刷新界面...")
            return

        # 1. 绘制设备屏幕截图
        scaled_pixmap = self.pixmap.scaled(
            draw_rect.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(draw_rect.topLeft(), scaled_pixmap)

        # 2. 绘制所有控件边界高亮
        scale_x = draw_rect.width() / self.orig_w
        scale_y = draw_rect.height() / self.orig_h

        # 绘制所有基础微弱蓝框
        pen_default = QPen(QColor(56, 189, 248, 40), 1)
        painter.setPen(pen_default)
        painter.setBrush(QBrush(QColor(56, 189, 248, 8)))
        for comp in self.flat_components:
            bx = int(draw_rect.x() + comp["left"] * scale_x)
            by = int(draw_rect.y() + comp["top"] * scale_y)
            bw = int(comp["width"] * scale_x)
            bh = int(comp["height"] * scale_y)
            painter.drawRect(bx, by, bw, bh)

        # 绘制 Hover 黄色高亮
        if self.hover_node_id:
            for comp in self.flat_components:
                if comp["node_id"] == self.hover_node_id:
                    bx = int(draw_rect.x() + comp["left"] * scale_x)
                    by = int(draw_rect.y() + comp["top"] * scale_y)
                    bw = int(comp["width"] * scale_x)
                    bh = int(comp["height"] * scale_y)
                    painter.setPen(QPen(QColor("#eab308"), 2))
                    painter.setBrush(QBrush(QColor(234, 179, 8, 50)))
                    painter.drawRect(bx, by, bw, bh)
                    break

        # 绘制 Selected 红色加粗高亮
        if self.selected_node_id:
            for comp in self.flat_components:
                if comp["node_id"] == self.selected_node_id:
                    bx = int(draw_rect.x() + comp["left"] * scale_x)
                    by = int(draw_rect.y() + comp["top"] * scale_y)
                    bw = int(comp["width"] * scale_x)
                    bh = int(comp["height"] * scale_y)
                    painter.setPen(QPen(QColor("#ef4444"), 2.5))
                    painter.setBrush(QBrush(QColor(239, 68, 68, 70)))
                    painter.drawRect(bx, by, bw, bh)
                    break

    def mouseMoveEvent(self, event):
        draw_rect = self.get_draw_rect()
        if draw_rect.isEmpty() or not draw_rect.contains(event.pos()):
            if self.hover_node_id:
                self.hover_node_id = ""
                self.update()
            return

        scale_x = draw_rect.width() / self.orig_w
        scale_y = draw_rect.height() / self.orig_h
        dev_x = int((event.pos().x() - draw_rect.x()) / scale_x)
        dev_y = int((event.pos().y() - draw_rect.y()) / scale_y)

        # 寻找命中的最小叶子控件
        hit_node = ""
        min_area = float("inf")
        for comp in self.flat_components:
            if comp["left"] <= dev_x <= comp["right"] and comp["top"] <= dev_y <= comp["bottom"]:
                area = comp["width"] * comp["height"]
                if area < min_area:
                    min_area = area
                    hit_node = comp["node_id"]

        if hit_node != self.hover_node_id:
            self.hover_node_id = hit_node
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.hover_node_id:
            self.selected_node_id = self.hover_node_id
            self.update()
            self.element_clicked.emit(self.selected_node_id)


class HarmonyNativeInspectorWindow(QMainWindow):
    """纯血鸿蒙原生桌面审查器主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HarmonyOS Native Inspector - 纯血鸿蒙原生桌面审查器")
        self.resize(1400, 900)
        self.setMinimumSize(1000, 700)
        self.flat_components: List[Dict[str, Any]] = []
        self.comp_map: Dict[str, Dict[str, Any]] = {}
        self.tree_item_map: Dict[str, QTreeWidgetItem] = {}
        self.node_counter = 0

        self.apply_dark_theme()
        self.init_ui()
        self.refresh_from_device()

    def apply_dark_theme(self):
        """应用现代轻奢黑科技桌面深色主题"""
        self.setStyleSheet("""
            QMainWindow { background-color: #141417; }
            QWidget { color: #f4f4f5; font-family: 'Segoe UI', 'PingFang SC', sans-serif; font-size: 13px; }
            QToolBar, QFrame#topBar { background-color: #1c1c21; border-bottom: 1px solid #2d2d35; }
            QLineEdit { background-color: #26262e; border: 1px solid #3f3f4e; border-radius: 6px; padding: 6px 12px; color: #ffffff; }
            QLineEdit:focus { border: 1px solid #38bdf8; }
            QPushButton { background-color: #2563eb; color: #ffffff; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 600; }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton#btnRefresh { background-color: #059669; }
            QPushButton#btnRefresh:hover { background-color: #047857; }
            QSplitter::handle { background-color: #2d2d35; }
            QTreeWidget { background-color: #18181d; border: 1px solid #27272f; border-radius: 6px; padding: 4px; }
            QTreeWidget::item:hover { background-color: #272733; }
            QTreeWidget::item:selected { background-color: #2563eb; color: #ffffff; }
            QTableWidget { background-color: #18181d; border: 1px solid #27272f; border-radius: 6px; gridline-color: #2d2d35; }
            QHeaderView::section { background-color: #22222a; color: #a1a1aa; border: none; padding: 6px; font-weight: 600; }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 顶部工具栏与实时 XPath / ID 搜索栏
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 10, 16, 10)
        top_layout.setSpacing(12)

        self.btn_refresh = QPushButton("📸 刷新界面 (Capture)")
        self.btn_refresh.setObjectName("btnRefresh")
        self.btn_refresh.clicked.connect(self.refresh_from_device)
        top_layout.addWidget(self.btn_refresh)

        self.lbl_device = QLabel("设备: 检测中...")
        self.lbl_device.setStyleSheet("color: #38bdf8; font-weight: bold;")
        top_layout.addWidget(self.lbl_device)

        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("🔍 树中搜索定位 (XPath / ID / Text):"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入如 //Text[@text='三条'] 或 ID 或关键字，回车快速在树中定位")
        self.search_input.returnPressed.connect(self.search_element)
        top_layout.addWidget(self.search_input, 1)

        btn_search = QPushButton("在树中定位")
        btn_search.clicked.connect(self.search_element)
        top_layout.addWidget(btn_search)

        self.lbl_search_res = QLabel("")
        self.lbl_search_res.setStyleSheet("color: #eab308; font-weight: 500;")
        top_layout.addWidget(self.lbl_search_res)

        main_layout.addWidget(top_bar)

        # 2. 中间三栏原生分割器 (QSplitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左栏：屏幕物理映射画布
        self.canvas = ScreenCanvas()
        self.canvas.element_clicked.connect(self.on_canvas_element_clicked)
        splitter.addWidget(self.canvas)

        # 中栏：DOM 组件层级树
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(8, 8, 8, 8)
        lbl_tree_title = QLabel("组件层次结构树 (Hierarchy Tree)")
        lbl_tree_title.setStyleSheet("color: #a1a1aa; font-weight: 600; margin-bottom: 4px;")
        tree_layout.addWidget(lbl_tree_title)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["组件类型 / 属性 (ArkUI DOM Tree)"])
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        tree_layout.addWidget(self.tree_widget)
        splitter.addWidget(tree_container)

        # 右栏：属性表格与一键复制面板
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(8, 8, 8, 8)

        lbl_attr_title = QLabel("选中组件详情与代码生成 (Selected Element)")
        lbl_attr_title.setStyleSheet("color: #a1a1aa; font-weight: 600; margin-bottom: 4px;")
        right_layout.addWidget(lbl_attr_title)

        code_box = QFrame()
        code_box.setStyleSheet("background-color: #1e1e26; border-radius: 6px; padding: 10px; border: 1px solid #2d2d38;")
        code_layout = QVBoxLayout(code_box)
        code_layout.setSpacing(8)

        # ID 定位复制栏
        id_row = QHBoxLayout()
        self.txt_id_code = QLineEdit()
        self.txt_id_code.setReadOnly(True)
        self.txt_id_code.setPlaceholderText("推荐 ID 定位代码")
        btn_copy_id = QPushButton("复制 ID")
        btn_copy_id.clicked.connect(lambda: self.copy_to_clip(self.txt_id_code.text()))
        id_row.addWidget(self.txt_id_code, 1)
        id_row.addWidget(btn_copy_id)
        code_layout.addLayout(id_row)

        # XPath 定位复制栏
        xpath_row = QHBoxLayout()
        self.txt_xpath_code = QLineEdit()
        self.txt_xpath_code.setReadOnly(True)
        self.txt_xpath_code.setPlaceholderText("推荐 XPath 定位代码")
        btn_copy_xpath = QPushButton("复制 XPath")
        btn_copy_xpath.clicked.connect(lambda: self.copy_to_clip(self.txt_xpath_code.text()))
        xpath_row.addWidget(self.txt_xpath_code, 1)
        xpath_row.addWidget(btn_copy_xpath)
        code_layout.addLayout(xpath_row)

        right_layout.addWidget(code_box)

        self.table_attrs = QTableWidget()
        self.table_attrs.setColumnCount(2)
        self.table_attrs.setHorizontalHeaderLabels(["属性名称 (Attribute)", "属性值 (Value)"])
        self.table_attrs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_attrs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.table_attrs)

        splitter.addWidget(right_container)

        # 设置三栏初始宽度比例： 40% : 35% : 25%
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 3)

        main_layout.addWidget(splitter, 1)

    def refresh_from_device(self):
        """通过 HDC 执行真机截图与 dumpLayout 刷新"""
        udid = get_connected_device()
        if not udid:
            self.lbl_device.setText("❌ 未检测到鸿蒙真机")
            QMessageBox.warning(self, "设备连接异常", "未检测到在线的鸿蒙设备，请确认已开启 USB 调试并运行 hdc list targets")
            return

        self.lbl_device.setText(f"✅ 在线设备: {udid}")
        tmp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "inspector")
        os.makedirs(tmp_dir, exist_ok=True)

        remote_png = "/data/local/tmp/native_shot.png"
        run_hdc(["shell", "uitest", "screenCap", "-p", remote_png], udid)
        local_png = os.path.join(tmp_dir, "native_shot.png")
        run_hdc(["file", "recv", remote_png, local_png], udid)
        run_hdc(["shell", "rm", "-f", remote_png], udid)

        remote_json = "/data/local/tmp/native_layout.json"
        run_hdc(["shell", "uitest", "dumpLayout", "-p", remote_json], udid)
        local_json = os.path.join(tmp_dir, "native_layout.json")
        run_hdc(["file", "recv", remote_json, local_json], udid)
        run_hdc(["shell", "rm", "-f", remote_json], udid)

        if not os.path.exists(local_png) or not os.path.exists(local_json):
            QMessageBox.critical(self, "抓取失败", "抓取手机现场失败，请确认屏幕已点亮且处于解锁状态。")
            return

        with open(local_json, "r", encoding="utf-8") as f:
            raw_tree = json.load(f)

        self.flat_components.clear()
        self.comp_map.clear()
        self.tree_item_map.clear()
        self.tree_widget.clear()
        self.node_counter = 0

        # 构建原生层级树并记录扁平化列表
        self.build_tree_recursive(raw_tree, None)
        self.canvas.load_data(local_png, self.flat_components)
        self.tree_widget.expandToDepth(3)

    def build_tree_recursive(self, raw_node: Dict[str, Any], parent_item: Optional[QTreeWidgetItem]):
        current_id = f"node_{self.node_counter}"
        self.node_counter += 1

        attrs = raw_node.get("attributes", {})
        bounds_str = attrs.get("bounds", "[0,0][0,0]")
        match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
        left, top, right, bottom = 0, 0, 0, 0
        if match:
            left, top, right, bottom = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))

        width = max(0, right - left)
        height = max(0, bottom - top)
        c_id = attrs.get("id") or attrs.get("key") or ""
        text = attrs.get("text") or attrs.get("originalText") or ""
        c_type = attrs.get("type", "Component")

        locator_id = f'(AppiumBy.ID, "{c_id}")' if c_id else ""
        if text:
            locator_xpath = f'(AppiumBy.XPATH, \'//{c_type}[@text="{text}"]\')'
        elif c_id:
            locator_xpath = f'(AppiumBy.XPATH, \'//*[@id="{c_id}"]\')'
        else:
            locator_xpath = f'(AppiumBy.XPATH, \'//{c_type}\')'

        comp_info = {
            "node_id": current_id,
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "width": width,
            "height": height,
            "type": c_type,
            "id": c_id,
            "text": text,
            "locator_id": locator_id,
            "locator_xpath": locator_xpath,
            "raw_attributes": attrs
        }

        if width > 0 and height > 0:
            self.flat_components.append(comp_info)
        self.comp_map[current_id] = comp_info

        # 构建树节点文本显示
        item_text = f"<{c_type}>"
        if c_id:
            item_text += f'  id="{c_id}"'
        if text:
            short_txt = text if len(text) <= 25 else text[:25] + "..."
            item_text += f'  text="{short_txt}"'

        item = QTreeWidgetItem([item_text])
        item.setData(0, Qt.ItemDataRole.UserRole, current_id)
        self.tree_item_map[current_id] = item

        if parent_item:
            parent_item.addChild(item)
        else:
            self.tree_widget.addTopLevelItem(item)

        for child in raw_node.get("children", []):
            self.build_tree_recursive(child, item)

    def on_canvas_element_clicked(self, node_id: str):
        """画布点击 -> 联动树形选中与滚动聚焦"""
        item = self.tree_item_map.get(node_id)
        if item:
            self.tree_widget.setCurrentItem(item)
            self.tree_widget.scrollToItem(item)
        self.update_detail_panel(node_id)

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """树形点击 -> 联动左侧画布红框锁定"""
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self.canvas.selected_node_id = node_id
            self.canvas.update()
            self.update_detail_panel(node_id)

    def update_detail_panel(self, node_id: str):
        """刷新右侧属性表格与代码生成框"""
        comp = self.comp_map.get(node_id)
        if not comp:
            return

        self.txt_id_code.setText(comp.get("locator_id", ""))
        self.txt_xpath_code.setText(comp.get("locator_xpath", ""))

        raw_attrs = comp.get("raw_attributes", {})
        self.table_attrs.setRowCount(len(raw_attrs))
        row = 0
        for k, v in raw_attrs.items():
            k_item = QTableWidgetItem(str(k))
            v_item = QTableWidgetItem(str(v))
            if k in ("id", "key", "text", "originalText", "type", "bounds"):
                k_item.setForeground(QColor("#38bdf8"))
                v_item.setForeground(QColor("#facc15"))
                k_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table_attrs.setItem(row, 0, k_item)
            self.table_attrs.setItem(row, 1, v_item)
            row += 1

    def search_element(self):
        """在树中根据 XPath / ID / 文本进行匹配高亮与定位"""
        val = self.search_input.text().strip()
        if not val:
            self.lbl_search_res.setText("")
            return

        matched_ids = []
        for c in self.flat_components:
            hit = False
            # 1. 匹配 ID
            if c["id"] and (c["id"] == val or val in c["id"]):
                hit = True
            # 2. 匹配 Text
            elif c["text"] and val in c["text"]:
                hit = True
            # 3. 匹配简易 XPath
            elif val.startswith("//"):
                if "@text=" in val:
                    exp_text = val.split("@text=")[1].strip("'\" ]")
                    if c["text"] == exp_text:
                        hit = True
                elif "contains(@text" in val:
                    m = re.search(r"contains\(@text,\s*['\"]([^'\"]+)['\"]\)", val)
                    if m and m.group(1) in c["text"]:
                        hit = True
                elif "@id=" in val:
                    exp_id = val.split("@id=")[1].strip("'\" ]")
                    if c["id"] == exp_id:
                        hit = True
                else:
                    tag = val.strip("/[]").split("[")[0].strip()
                    if tag == "*" or c["type"] == tag:
                        hit = True

            if hit:
                matched_ids.append(c["node_id"])

        self.lbl_search_res.setText(f"匹配到 {len(matched_ids)} 项")

        if matched_ids:
            first_id = matched_ids[0]
            item = self.tree_item_map.get(first_id)
            if item:
                self.tree_widget.setCurrentItem(item)
                self.tree_widget.scrollToItem(item)
            self.canvas.selected_node_id = first_id
            self.canvas.update()
            self.update_detail_panel(first_id)
        else:
            QMessageBox.information(self, "搜索结果", f"未能在当前界面组件树中匹配到符合条件的元素: '{val}'")

    def copy_to_clip(self, text: str):
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "复制成功", f"代码已复制到系统剪贴板:\n{text}")


def main():
    app = QApplication(sys.argv)
    window = HarmonyNativeInspectorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
