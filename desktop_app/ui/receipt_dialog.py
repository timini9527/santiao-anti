# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 - 填写测试结果 Web 回执模态对话框
=======================================================
1:1 像素级复刻 Web 端 (MobilePlatform.vue) 的【📝 填写测试结果 Web 回执】：
1. 顶部标题栏：📝 填写测试结果 Web 回执 + 说明文案
2. 动态表单项列表 (带滚动)：
   - 键名输入框 (如 设备1, 私聊用户1) + 值输入框 (占位提示: 值...) + 红色圆形删除按钮 (🗑️)
3. 3 大快捷插入按键：
   - ＋ 添加测试设备 (浅蓝胶囊)
   - ＋ 添加测试账号 (浅绿胶囊)
   - ＋ 增加普通项 (浅灰胶囊)
4. 底部操作栏：取消 + 保存配置 (高定科技蓝)
"""
import json
from typing import List, Dict, Any, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor


class WebReceiptDialog(QDialog):
    """填写测试结果 Web 回执模态对话框"""

    def __init__(self, current_fields: List[Dict[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("填写测试结果 Web 回执")
        self.resize(540, 500)
        self.setMinimumSize(480, 420)
        
        # 深度复制一份原始数据，防止用户点击取消时污染原数据
        self.fields_data = [dict(f) for f in current_fields] if current_fields else [
            {"key": "设备1", "val": ""},
            {"key": "私聊用户1", "val": ""},
            {"key": "私聊用户2", "val": ""},
            {"key": "群聊名称1", "val": ""},
            {"key": "群聊名称2", "val": ""},
        ]
        
        self.row_widgets: List[Tuple[QLineEdit, QLineEdit, QWidget]] = []
        self.init_ui()

    def init_ui(self):
        # 对话框全局高阶极简白金样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 18)
        main_layout.setSpacing(12)

        # 1. 顶部标题栏：带图标的粗体标题
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        lbl_title = QLabel("📝 填写测试结果 Web 回执")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a;")
        title_row.addWidget(lbl_title)
        title_row.addStretch()
        main_layout.addLayout(title_row)

        # 2. 副标题说明文案
        lbl_desc = QLabel("配置本次回归测试结束后自动生成的归档报告回执单内容（可用于通知非开发团队汇报）。")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 12px; color: #64748b; line-height: 1.4;")
        main_layout.addWidget(lbl_desc)

        main_layout.addSpacing(2)

        # 3. 动态表单项列表区 (外层包裹平滑滚动条)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f8fafc;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
        """)

        self.rows_container = QWidget()
        self.rows_container.setStyleSheet("background: transparent;")
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 6, 0)
        self.rows_layout.setSpacing(10)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 初始化渲染已有表单项
        for item in self.fields_data:
            self._add_row_ui(item.get("key", ""), item.get("val", ""))

        self.scroll_area.setWidget(self.rows_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # 4. 快捷增加按键组 (添加测试设备 / 添加测试账号 / 增加普通项)
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 4, 0, 8)
        btn_bar.setSpacing(10)

        # 4.1 + 添加测试设备 (浅蓝底)
        btn_add_device = QPushButton("＋ 添加测试设备")
        btn_add_device.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_device.setStyleSheet("""
            QPushButton {
                background-color: #eff6ff;
                color: #2563eb;
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #dbeafe;
                border-color: #93c5fd;
            }
            QPushButton:pressed {
                background-color: #bfdbfe;
            }
        """)
        btn_add_device.clicked.connect(self._on_add_device)
        btn_bar.addWidget(btn_add_device)

        # 4.2 + 添加测试账号 (浅绿底)
        btn_add_user = QPushButton("＋ 添加测试账号")
        btn_add_user.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_user.setStyleSheet("""
            QPushButton {
                background-color: #f0fdf4;
                color: #16a34a;
                border: 1px solid #bbf7d0;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #dcfce7;
                border-color: #86efac;
            }
            QPushButton:pressed {
                background-color: #bbf7d0;
            }
        """)
        btn_add_user.clicked.connect(self._on_add_user)
        btn_bar.addWidget(btn_add_user)

        # 4.3 + 增加普通项 (浅灰底)
        btn_add_custom = QPushButton("＋ 增加普通项")
        btn_add_custom.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_custom.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                color: #475569;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #cbd5e1;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        btn_add_custom.clicked.connect(self._on_add_custom)
        btn_bar.addWidget(btn_add_custom)

        btn_bar.addStretch()
        main_layout.addLayout(btn_bar)

        # 5. 底部操作按钮栏 (取消 / 保存配置)
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 6, 0, 0)
        footer_row.setSpacing(12)
        footer_row.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.setFixedSize(76, 32)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f8fafc;
                border-color: #94a3b8;
            }
            QPushButton:pressed {
                background-color: #f1f5f9;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        footer_row.addWidget(btn_cancel)

        btn_save = QPushButton("保存配置")
        btn_save.setFixedSize(86, 32)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        btn_save.clicked.connect(self._on_save)
        footer_row.addWidget(btn_save)

        main_layout.addLayout(footer_row)

    def _add_row_ui(self, key_text: str = "", val_text: str = ""):
        """动态增加单条键值对表单行"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        # 1. 键名输入框
        edit_key = QLineEdit(key_text)
        edit_key.setPlaceholderText("项目")
        edit_key.setFixedWidth(136)
        edit_key.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: #0f172a;
                font-weight: 600;
            }
            QLineEdit:focus {
                border-color: #2563eb;
                background-color: #ffffff;
            }
        """)

        # 2. 键值输入框
        edit_val = QLineEdit(val_text)
        edit_val.setPlaceholderText("值...")
        edit_val.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border-color: #2563eb;
                background-color: #ffffff;
            }
        """)

        # 3. 红色高亮圆形垃圾桶删除按钮
        btn_delete = QPushButton("🗑️")
        btn_delete.setFixedSize(30, 30)
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setToolTip("删除该项配置")
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #fef2f2;
                color: #ef4444;
                border: 1px solid #fecdd3;
                border-radius: 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                border-color: #fca5a5;
                color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #fecdd3;
            }
        """)

        tuple_ref = (edit_key, edit_val, row_widget)
        self.row_widgets.append(tuple_ref)

        # 绑定删除事件
        btn_delete.clicked.connect(lambda: self._on_delete_row(tuple_ref))

        row_layout.addWidget(edit_key)
        row_layout.addWidget(edit_val, stretch=1)
        row_layout.addWidget(btn_delete)

        self.rows_layout.addWidget(row_widget)

    def _on_delete_row(self, tuple_ref: Tuple[QLineEdit, QLineEdit, QWidget]):
        """从界面与记录中移除对应行"""
        if tuple_ref in self.row_widgets:
            self.row_widgets.remove(tuple_ref)
            _, _, row_widget = tuple_ref
            self.rows_layout.removeWidget(row_widget)
            row_widget.deleteLater()

    def _on_add_device(self):
        """自动计算已有设备数并追加『设备N』"""
        dev_count = sum(1 for k, _, _ in self.row_widgets if k.text().strip().startswith("设备")) + 1
        self._add_row_ui(f"设备{dev_count}", "")
        # 自动滚屏到底部
        self._scroll_to_bottom()

    def _on_add_user(self):
        """自动计算已有用户数并追加『私聊用户N』"""
        user_count = sum(1 for k, _, _ in self.row_widgets if k.text().strip().startswith("私聊用户")) + 1
        self._add_row_ui(f"私聊用户{user_count}", "")
        self._scroll_to_bottom()

    def _on_add_custom(self):
        """增加空白普通项"""
        self._add_row_ui("", "")
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """平滑滚动到底部"""
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def _on_save(self):
        """收集所有有效字段数据并保存"""
        collected = []
        for edit_key, edit_val, _ in self.row_widgets:
            k = edit_key.text().strip()
            v = edit_val.text().strip()
            if k:  # 只保留有 key 的项
                collected.append({"key": k, "val": v})
        self.fields_data = collected
        self.accept()

    def get_receipt_fields(self) -> List[Dict[str, str]]:
        """获取结构化字段列表"""
        return self.fields_data

    def get_receipt_dict(self) -> Dict[str, str]:
        """获取扁平键值对映射字典"""
        return {item["key"]: item["val"] for item in self.fields_data if item.get("key")}
