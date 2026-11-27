# -*- coding: utf-8 -*-
"""
独立浮窗元素定位与查找器 (SearchElementDialog)：
支持 HarmonyOS (ID / Text / HypiumBy / HosBy / Description / XPath / Type)、
Android (ID / Accessibility ID / UiAutomator / XPath / Class Name) 与
iOS (Accessibility ID / Class Chain / Predicate String / XPath / Class Name) 三端检索、语法诊断与双向联动。
"""
import ast
import logging
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import QEvent, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from desktop_app.ui.inspector.common.dialogs import ModernInputDialog
from desktop_app.ui.inspector.common.icons import (
    create_modern_app_icon,
    get_dom_tag_color,
    get_tech_icon,
)
from desktop_app.ui.inspector.common.widgets import AutoResizingTextEdit, AutoWrapStatusLabel
from desktop_app.ui.inspector.locator.harmony_hypium import (
    _eval_hypium_attr_step,
    parse_hypium_by_expression,
    resolve_harmony_locator_input,
)
from desktop_app.ui.inspector.locator.ios_selector import (
    tokenize_ios_predicate,
    validate_ios_selector_syntax,
)
from desktop_app.ui.inspector.locator.xpath_engine import (
    init_lxml_xpath_extensions,
    validate_xpath_syntax,
)

logger = logging.getLogger("Inspector")


class SearchElementDialog(QDialog):
    """全中文纯白轻奢定位搜索独立浮窗（具备跨会话与平台隔离记忆）"""

    element_picked = pyqtSignal(str)
    tap_requested = pyqtSignal(str)
    send_keys_requested = pyqtSignal(str, str)

    _MEMORY_STATE: Dict[str, Dict[str, Any]] = {}

    def __init__(
        self,
        flat_components: List[Dict[str, Any]],
        xml_root: Optional[ET.Element],
        comp_map: Optional[Dict[str, Dict[str, Any]]] = None,
        platform: str = "harmony",
        parent: Any = None,
    ) -> None:
        if not isinstance(platform, str):
            parent = platform
            platform = "harmony"
        self.inspector = parent
        super().__init__(None)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowIcon(create_modern_app_icon())

        app = QApplication.instance()
        if app:
            app.applicationStateChanged.connect(self._on_app_state_changed)
        self.platform = (platform or "harmony").lower()
        plat_map = {"harmony": "HarmonyOS NEXT", "android": "Android", "ios": "iOS"}
        self.setWindowTitle(f"元素定位与查找器 ({plat_map.get(self.platform, '多端统一')})")
        self.resize(750, 560)
        self.flat_components = flat_components
        self.comp_map = comp_map or {}
        self.xml_root = xml_root
        self.matched_components: List[Dict[str, Any]] = []
        self.last_main_selected_comp: Optional[Dict[str, Any]] = None

        self.apply_theme()
        self.init_ui()
        self._load_memory()

    def apply_theme(self) -> None:
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; color: #1e293b; }
            QLabel { color: #334155; font-size: 13px; font-weight: 600; }
            QComboBox {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 4px 10px; font-size: 13px; min-height: 28px;
            }
            QComboBox:hover { border-color: #0284c7; }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 6px 10px; font-size: 13px; min-height: 28px;
                font-family: Consolas, "Segoe UI", monospace;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border: 1.5px solid #0284c7; }
            QPushButton {
                background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1;
                border-radius: 6px; padding: 0 16px; font-weight: 600; font-size: 13px; min-height: 32px;
                text-align: center;
            }
            QPushButton:hover { background-color: #f8fafc; border-color: #94a3b8; color: #0f172a; }
            QPushButton:pressed { background-color: #f1f5f9; }
            QPushButton:disabled { background-color: #f8fafc; color: #94a3b8; border: 1px solid #e2e8f0; }
            QPushButton#btnSearchExec {
                background-color: #0284c7; color: #ffffff; border: 1px solid #0284c7;
                font-size: 13px; font-weight: 600; padding: 0 18px; min-height: 32px; text-align: center;
            }
            QPushButton#btnSearchExec:hover { background-color: #0369a1; border-color: #0369a1; }
            QPushButton#btnSearchExec:pressed { background-color: #075985; }
            QPushButton#btnCancel {
                background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1;
                font-size: 13px; min-height: 32px;
            }
            QPushButton#btnCancel:hover { background-color: #f1f5f9; color: #0f172a; border-color: #94a3b8; }
            QListWidget {
                background-color: #f8fafc; border: 1px solid #e2e8f0;
                border-radius: 6px; color: #0f172a; font-family: Consolas, monospace;
            }
            QListWidget::item { padding: 9px; border-bottom: 1px solid #f1f5f9; min-height: 24px; }
            QListWidget::item:selected {
                background-color: #e0f2fe; color: #0369a1; border-radius: 4px; font-weight: bold;
            }
        """)

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        top_ctrl_bar = QHBoxLayout()
        top_ctrl_bar.addWidget(QLabel("定位策略 (Locator Strategy):"))
        top_ctrl_bar.addStretch()

        self.chk_stay_on_top = QCheckBox("保持置顶 (防遮挡)")
        self.chk_stay_on_top.setChecked(True)
        self.chk_stay_on_top.setToolTip("保持查找窗口置顶防遮挡")
        self.chk_stay_on_top.setStyleSheet("color: #0284c7; font-size: 12px; font-weight: 600;")
        self.chk_stay_on_top.toggled.connect(self._toggle_stay_on_top)
        top_ctrl_bar.addWidget(self.chk_stay_on_top)
        layout.addLayout(top_ctrl_bar)

        self.combo_strategy = QComboBox()
        self.combo_strategy.setFixedHeight(30)
        self.combo_strategy.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.combo_strategy)

        self.format_pill_layout = QHBoxLayout()
        self.format_pill_layout.setSpacing(6)
        self.format_pill_layout.setContentsMargins(0, 0, 0, 0)
        self.format_pill_buttons: Dict[str, QPushButton] = {}
        layout.addLayout(self.format_pill_layout)

        layout.addWidget(QLabel("选择器表达式 (Selector):"))
        sel_row = QHBoxLayout()
        self.edit_selector = AutoResizingTextEdit(min_height=54, max_height=180)
        self.edit_selector.textChanged.connect(self._on_selector_text_changed)
        sel_row.addWidget(self.edit_selector, 1)

        self.btn_pick_current = QPushButton("填入主视窗选中元素")
        self.btn_pick_current.setIcon(get_tech_icon("target", "#0284c7"))
        self.btn_pick_current.setIconSize(QSize(14, 14))
        self.btn_pick_current.setFixedHeight(34)
        self.btn_pick_current.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick_current.setToolTip("将当前在真机画面或 DOM 树中选中的组件表达式快速填入输入框")
        self.btn_pick_current.clicked.connect(self.pick_current_element_to_input)
        sel_row.addWidget(self.btn_pick_current, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(sel_row)

        self.chk_auto_pick = QCheckBox("主视窗点击真机或 DOM 树时，自动填充推荐定位器")
        self.chk_auto_pick.setChecked(False)
        self.chk_auto_pick.setStyleSheet("color: #475569; font-size: 12px;")
        layout.addWidget(self.chk_auto_pick)

        self.chk_only_visible = QCheckBox("仅匹配当前真实展示元素 (智能过滤被遮挡/未展开的隐藏层)")
        self.chk_only_visible.setChecked(True)
        self.chk_only_visible.setStyleSheet("color: #0284c7; font-size: 12px; font-weight: 600;")
        self.chk_only_visible.stateChanged.connect(self._on_only_visible_changed)
        layout.addWidget(self.chk_only_visible)

        self._rebuild_strategies()
        self.combo_strategy.currentIndexChanged.connect(self._on_strategy_changed)

        btn_layout = QHBoxLayout()
        self.btn_search = QPushButton("查找匹配元素 (Search)")
        self.btn_search.setIcon(get_tech_icon("search", "#ffffff"))
        self.btn_search.setIconSize(QSize(15, 15))
        self.btn_search.setObjectName("btnSearchExec")
        self.btn_search.setFixedHeight(32)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self.do_search)
        self.edit_selector.returnPressed.connect(self.do_search)
        btn_layout.addWidget(self.btn_search, 0, Qt.AlignmentFlag.AlignTop)

        self.lbl_status = AutoWrapStatusLabel("就绪，请输入表达式或点击主视窗元素后点击查找")
        self.lbl_status.setStyleSheet("color: #0284c7; font-weight: 600;")
        btn_layout.addWidget(self.lbl_status, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("匹配到的元素列表 (Elements Found):"))
        self.list_results = QListWidget()
        self.list_results.setWordWrap(True)
        self.list_results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_results.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_results, 1)

        bottom_box = QHBoxLayout()
        bottom_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.btn_tap = QPushButton("点击该元素 (Tap)")
        self.btn_tap.setIcon(get_tech_icon("tap", "#0284c7"))
        self.btn_tap.setIconSize(QSize(15, 15))
        self.btn_tap.setFixedHeight(32)
        self.btn_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tap.setEnabled(False)
        self.btn_tap.clicked.connect(self.on_tap_clicked)
        bottom_box.addWidget(self.btn_tap)

        self.btn_send_keys = QPushButton("输入文本 (Send Keys)")
        self.btn_send_keys.setIcon(get_tech_icon("send", "#0284c7"))
        self.btn_send_keys.setIconSize(QSize(15, 15))
        self.btn_send_keys.setFixedHeight(32)
        self.btn_send_keys.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_keys.setEnabled(False)
        self.btn_send_keys.clicked.connect(self.on_send_keys_clicked)
        bottom_box.addWidget(self.btn_send_keys)

        bottom_box.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setFixedHeight(32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setObjectName("btnCancel")
        btn_close.clicked.connect(self.close)
        bottom_box.addWidget(btn_close)
        layout.addLayout(bottom_box)

    def _get_platform_strategies(self) -> List[Tuple[str, str, str]]:
        if self.platform == "android":
            return [
                ("id", "Resource-ID", "id (resource-id 标识 - 推荐首选)"),
                ("accessibility id", "Accessibility ID", "accessibility id (content-desc 文本/描述)"),
                ("uiautomator", "UiAutomator", "android uiautomator (UiSelector 语法表达式)"),
                ("xpath", "XPath", "xpath (XPath 路径表达式 - 灵活兜底)"),
                ("class name", "Class Name", "class name (组件类名)"),
            ]
        if self.platform == "ios":
            return [
                ("id", "Accessibility ID", "id / accessibility id (name / label 标识 - 推荐首选)"),
                ("class chain", "Class Chain", "ios class chain (原生类链表达式 - 快速层级)"),
                ("predicate", "Predicate String", "ios predicate string (原生谓词表达式 - 复合条件)"),
                ("xpath", "XPath", "xpath (XPath 路径表达式 - 灵活兜底)"),
                ("class name", "Class Name", "class name (XCUIElementType 组件类型)"),
            ]
        return [
            ("id", "ID / Key", "id (组件 Key / ID 标识 - By.id - 推荐首选)"),
            ("text", "Text 文本", "text (文本内容 - By.text - 原生高效)"),
            ("hypium", "HypiumBy", "HypiumBy (BY.* 原生链式表达式 - 支持 isAfter/isBefore/within)"),
            ("description", "Description", "description (无障碍描述 - By.description)"),
            ("xpath", "XPath", "xpath (XPath 路径表达式 - 灵活兜底)"),
            ("type", "Type 类型", "type / class name (ArkUI 组件类型名 - By.type)"),
        ]

    def _rebuild_strategies(self) -> None:
        self.combo_strategy.blockSignals(True)
        self.combo_strategy.clear()

        if hasattr(self, "format_pill_layout"):
            while self.format_pill_layout.count():
                item = self.format_pill_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            self.format_pill_buttons.clear()

        for s_key, s_short, s_full in self._get_platform_strategies():
            self.combo_strategy.addItem(s_full, s_key)
            if hasattr(self, "format_pill_layout"):
                btn = QPushButton(s_short)
                btn.setFixedHeight(26)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setToolTip(f"一键切换至 [{s_short}] 格式并自动填入表达式")
                btn.clicked.connect(lambda checked=False, k=s_key: self._on_format_pill_clicked(k))
                self.format_pill_layout.addWidget(btn)
                self.format_pill_buttons[s_key] = btn

        if hasattr(self, "format_pill_layout"):
            self.format_pill_layout.addStretch()

        self.combo_strategy.setCurrentIndex(0)
        self.combo_strategy.blockSignals(False)
        self._update_format_pills_active_state(self.combo_strategy.currentData())
        self.update_placeholder()

    def _update_format_pills_active_state(self, active_key: str) -> None:
        if not hasattr(self, "format_pill_buttons"):
            return
        for k, btn in self.format_pill_buttons.items():
            if k == active_key:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7; color: #ffffff;
                        border: 1px solid #0284c7; border-radius: 13px;
                        padding: 0 12px; font-weight: 700; font-size: 11px; min-height: 26px;
                    }
                    QPushButton:hover { background-color: #0369a1; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8fafc; color: #475569;
                        border: 1px solid #cbd5e1; border-radius: 13px;
                        padding: 0 12px; font-weight: 600; font-size: 11px; min-height: 26px;
                    }
                    QPushButton:hover { background-color: #f1f5f9; color: #0f172a; border-color: #94a3b8; }
                """)

    def _on_format_pill_clicked(self, strategy_key: str) -> None:
        idx = self.combo_strategy.findData(strategy_key)
        if idx >= 0:
            self.combo_strategy.setCurrentIndex(idx)

    def _get_expression_for_strategy(self, strategy: str, comp: Dict[str, Any]) -> str:
        if not comp:
            return ""
        rec_xp = comp.get("rec_xpath") or comp.get("xpath") or ""
        rec_id = comp.get("rec_id") or comp.get("id") or ""
        rec_text = comp.get("text") or ""
        rec_type = comp.get("type") or ""
        rec_full_type = comp.get("full_type") or comp.get("rec_class") or rec_type
        rec_pred = comp.get("rec_predicate") or ""
        rec_chain = comp.get("rec_class_chain") or ""
        raw_attrs = comp.get("raw_attributes") or comp.get("raw") or {}

        if strategy == "xpath":
            return rec_xp
        if strategy == "predicate":
            if rec_pred:
                return rec_pred
            ios_val = raw_attrs.get("value") or ""
            if rec_id:
                return f'type == "{rec_full_type}" AND name == "{rec_id}"'
            if rec_text:
                return f'type == "{rec_full_type}" AND (label == "{rec_text}" OR name == "{rec_text}")'
            if ios_val:
                return f'type == "{rec_full_type}" AND value == "{ios_val}"'
            return f'type == "{rec_full_type}"'
        if strategy == "class chain":
            if rec_chain:
                return rec_chain
            if rec_id:
                return f'**/{rec_full_type}[`name == "{rec_id}"`]'
            if rec_text:
                return f'**/{rec_full_type}[`label == "{rec_text}"`]'
            return f"**/{rec_full_type}"
        if strategy in ("id", "accessibility id"):
            if self.platform == "ios":
                ios_name = raw_attrs.get("name") or raw_attrs.get("id") or rec_id
                ios_label = raw_attrs.get("label") or rec_text
                return ios_name or ios_label or rec_id
            return rec_id or rec_text
        if strategy in ("class name", "type"):
            return rec_full_type if self.platform in ("ios", "android") else rec_type
        if strategy == "text":
            return rec_text
        if strategy == "hypium":
            safe_type = rec_type.replace("\\", "\\\\").replace('"', '\\"') if rec_type else ""
            safe_id = rec_id.replace("\\", "\\\\").replace('"', '\\"') if rec_id else ""
            safe_text = rec_text.replace("\\", "\\\\").replace('"', '\\"') if rec_text else ""
            raw_hint = str(raw_attrs.get("hint") or raw_attrs.get("placeholder") or "")
            safe_hint = raw_hint.replace("\\", "\\\\").replace('"', '\\"') if raw_hint else ""
            if safe_type and safe_id:
                return f'BY.type("{safe_type}").id("{safe_id}")'
            if safe_id:
                return f'BY.id("{safe_id}")'
            if safe_type and safe_text:
                return f'BY.type("{safe_type}").text("{safe_text}")'
            if safe_text:
                return f'BY.text("{safe_text}")'
            if safe_type and safe_hint:
                return f'BY.type("{safe_type}").hint("{safe_hint}")'
            if safe_type:
                return f'BY.type("{safe_type}")'
            return ""
        if strategy == "description":
            return str(raw_attrs.get("description") or raw_attrs.get("content-desc") or rec_text)
        if strategy == "uiautomator":
            if rec_text:
                return f'text("{rec_text}")'
            if rec_id:
                return f'resourceId("{rec_id}")'
            if rec_full_type:
                return f'className("{rec_full_type}")'
            return ""
        return rec_xp

    def _on_strategy_changed(self) -> None:
        strat = self.combo_strategy.currentData()
        self._update_format_pills_active_state(strat)
        self.update_placeholder()
        self._save_memory()

        comp = getattr(self, "last_main_selected_comp", None)
        if comp:
            expr = self._get_expression_for_strategy(strat, comp)
            if expr:
                self.edit_selector.setText(expr)
                strat_name = self.combo_strategy.currentText().split(" (")[0]
                self.lbl_status.setText(f"已切换为 [{strat_name}] 格式表达式，点击【查找】验证")

    def _on_only_visible_changed(self) -> None:
        self._save_memory()
        if hasattr(self, "edit_selector") and self.edit_selector.text().strip():
            self.do_search()

    def _apply_native_topmost(self, on_top: bool) -> None:
        was_visible = self.isVisible()
        flags = self.windowFlags()
        if on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint

        if self.windowFlags() != flags:
            self.setWindowFlags(flags)
            if was_visible:
                self.show()

        if sys.platform == "win32":
            try:
                import ctypes

                hwnd = int(self.winId())
                target = -1 if on_top else -2
                ctypes.windll.user32.SetWindowPos(hwnd, target, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0010)
            except Exception as e:
                logger.debug(f"Win32 SetWindowPos 调度异常: {e}")

    def _update_stay_on_top_state(self) -> None:
        if not hasattr(self, "chk_stay_on_top"):
            return
        self._apply_native_topmost(self.chk_stay_on_top.isChecked() and self.isVisible())

    def _toggle_stay_on_top(self, checked: bool) -> None:
        self._save_memory()
        self._apply_native_topmost(checked)
        if checked:
            self.raise_()
            self.activateWindow()

    def _on_app_state_changed(self, state: Qt.ApplicationState) -> None:
        pass

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_stay_on_top_state()

    def _save_memory(self) -> None:
        if not hasattr(self, "combo_strategy") or not hasattr(self, "edit_selector"):
            return
        cur_node_id = None
        if hasattr(self, "list_results"):
            curr = self.list_results.currentItem()
            if curr:
                cur_node_id = curr.data(Qt.ItemDataRole.UserRole)
        self._MEMORY_STATE[self.platform] = {
            "strategy": self.combo_strategy.currentData(),
            "selector": self.edit_selector.text(),
            "selected_node_id": cur_node_id,
            "only_visible": self.chk_only_visible.isChecked() if hasattr(self, "chk_only_visible") else True,
            "stay_on_top": self.chk_stay_on_top.isChecked() if hasattr(self, "chk_stay_on_top") else True,
        }

    def _on_selector_text_changed(self) -> None:
        self._save_memory()
        if hasattr(self, "edit_selector"):
            self.edit_selector.setStyleSheet("")
        if hasattr(self, "lbl_status") and self.lbl_status.text().startswith("⚠️"):
            self.lbl_status.setText("就绪，点击查找或按回车开始匹配")
            self.lbl_status.setStyleSheet("color: #0284c7; font-weight: 600;")

    def show_syntax_error(self, err_msg: str, example: str = "") -> None:
        if hasattr(self, "lbl_status"):
            self.lbl_status.setText(f"⚠️ 语法错误: {err_msg}")
            self.lbl_status.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 13px;")
        if hasattr(self, "edit_selector"):
            self.edit_selector.setStyleSheet("border: 1.5px solid #ef4444; border-radius: 6px; background-color: #fef2f2;")

        self.list_results.clear()

        err_item = QListWidgetItem(f"❌ 表达式语法错误: {err_msg}")
        err_item.setForeground(QColor("#b91c1c"))
        err_item.setBackground(QBrush(QColor("#fee2e2")))
        err_item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.list_results.addItem(err_item)

        if example:
            tip_item = QListWidgetItem(f"💡 正确语法示例: {example}")
            tip_item.setForeground(QColor("#0369a1"))
            tip_item.setBackground(QBrush(QColor("#f0f9ff")))
            tip_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(tip_item)
        else:
            tip_item = QListWidgetItem("💡 提示: 请检查标签名、属性格式 [@attr='值']、方括号/引号是否配对闭合")
            tip_item.setForeground(QColor("#475569"))
            tip_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(tip_item)

        self.list_results.setUpdatesEnabled(True)
        self.btn_tap.setEnabled(False)
        self.btn_send_keys.setEnabled(False)

    def _load_memory(self) -> None:
        saved = self._MEMORY_STATE.get(self.platform, {})
        saved_strat = saved.get("strategy")
        if saved_strat:
            idx = self.combo_strategy.findData(saved_strat)
            if idx >= 0:
                self.combo_strategy.setCurrentIndex(idx)

        saved_sel = saved.get("selector", "")
        if saved_sel:
            self.edit_selector.setText(saved_sel)
            self.edit_selector.setCursorPosition(len(saved_sel))

        if hasattr(self, "chk_only_visible"):
            self.chk_only_visible.blockSignals(True)
            self.chk_only_visible.setChecked(saved.get("only_visible", True))
            self.chk_only_visible.blockSignals(False)

        if hasattr(self, "chk_stay_on_top"):
            self.chk_stay_on_top.blockSignals(True)
            self.chk_stay_on_top.setChecked(saved.get("stay_on_top", True))
            self.chk_stay_on_top.blockSignals(False)
            self._update_stay_on_top_state()

        self.lbl_status.setText("就绪，请输入表达式或点击主视窗元素后点击查找")

    def update_context(
        self,
        flat_components: List[Dict[str, Any]],
        xml_root: Optional[ET.Element],
        comp_map: Optional[Dict[str, Dict[str, Any]]] = None,
        platform: str = "harmony",
    ) -> None:
        new_platform = (platform or "harmony").lower()
        platform_changed = new_platform != self.platform
        self.platform = new_platform
        self.flat_components = flat_components
        if comp_map is not None:
            self.comp_map = comp_map
        self.xml_root = xml_root

        if platform_changed:
            plat_map = {"harmony": "HarmonyOS NEXT", "android": "Android", "ios": "iOS"}
            self.setWindowTitle(f"元素定位与查找器 ({plat_map.get(self.platform, '多端统一')})")
            self._rebuild_strategies()
            self._load_memory()
        else:
            self.lbl_status.setText("真机数据已同步，点击【查找】重新匹配")

    def sync_element_from_main(self, comp: Dict[str, Any]) -> None:
        self.last_main_selected_comp = comp
        if hasattr(self, "chk_auto_pick") and self.chk_auto_pick.isChecked():
            self.pick_current_element_to_input()
        else:
            c_tag = comp.get("type", "Component")
            c_bounds = f"[{comp.get('left')},{comp.get('top')}][{comp.get('right')},{comp.get('bottom')}]"
            raw_attrs = comp.get("raw_attributes") or comp.get("raw") or {}
            attr_summary = ""
            if self.platform == "ios":
                ios_name = raw_attrs.get("name") or raw_attrs.get("id") or comp.get("id") or ""
                ios_label = raw_attrs.get("label") or ""
                ios_value = raw_attrs.get("value") or comp.get("text") or ""
                if ios_value:
                    short_v = ios_value if len(ios_value) <= 20 else ios_value[:20] + "..."
                    attr_summary += f' value="{short_v}"'
                if ios_name:
                    short_n = ios_name if len(ios_name) <= 20 else ios_name[:20] + "..."
                    attr_summary += f' name="{short_n}"'
                if ios_label and ios_label != ios_value:
                    short_l = ios_label if len(ios_label) <= 20 else ios_label[:20] + "..."
                    attr_summary += f' label="{short_l}"'
            else:
                if comp.get("id"):
                    attr_summary += f' id="{comp["id"]}"'
                if comp.get("text"):
                    short_t = comp["text"] if len(comp["text"]) <= 22 else comp["text"][:22] + "..."
                    attr_summary += f' text="{short_t}"'
            self.lbl_status.setText(f'主视窗已选中: <{c_tag}{attr_summary} bounds="{c_bounds}"> (点击【填入主视窗选中元素】)')

    def pick_current_element_to_input(self) -> None:
        comp = getattr(self, "last_main_selected_comp", None)
        if not comp:
            self.lbl_status.setText("提示: 请先在主视窗点击选中任意真机或 DOM 树元素")
            return

        curr_strat = self.combo_strategy.currentData()
        target_expr = self._get_expression_for_strategy(curr_strat, comp)
        if not target_expr:
            for s_key, _, _ in self._get_platform_strategies():
                candidate_expr = self._get_expression_for_strategy(s_key, comp)
                if candidate_expr:
                    target_expr = candidate_expr
                    idx = self.combo_strategy.findData(s_key)
                    if idx >= 0:
                        self.combo_strategy.setCurrentIndex(idx)
                    break

        if target_expr:
            self.edit_selector.setText(target_expr)

        strat_title = self.combo_strategy.currentText().split(" (")[0]
        self.lbl_status.setText(f"已按 [{strat_title}] 策略填入 <{comp.get('type')}> 推荐表达式，点击【查找】验证")

    def closeEvent(self, event) -> None:
        self._save_memory()
        super().closeEvent(event)

    def accept(self) -> None:
        self._save_memory()
        super().accept()

    def update_placeholder(self) -> None:
        if not hasattr(self, "edit_selector"):
            return
        strategy = self.combo_strategy.currentData()
        if self.platform == "android":
            tips = {
                "id": "例如: com.example.app:id/btn_send 或 login_btn",
                "xpath": "例如: //android.widget.Button[@text='发送']",
                "accessibility id": "例如: 发送 (对应 content-desc 描述)",
                "class name": "例如: android.widget.Button 或 TextView",
                "uiautomator": '例如: text("发送") 或 description("返回")',
            }
        elif self.platform == "ios":
            tips = {
                "id": "例如: ic delete 48 或 login_btn (Accessibility ID / Name / Label 标识)",
                "xpath": "例如: //XCUIElementTypeButton[@name='发送']",
                "class name": "例如: XCUIElementTypeButton 或 XCUIElementTypeStaticText",
                "predicate": "例如: label == '发送' AND visible == 1",
                "class chain": "**/XCUIElementTypeButton[`name == '发送'`]",
            }
        else:
            tips = {
                "id": "例如: login_button 或 send_btn (ArkUI key/id 标识)",
                "xpath": "例如: //Button[@text='发送'] 或 //Text[@text='925']",
                "text": "例如: 发送 或 925 (匹配组件展示文本)",
                "hypium": '例如: BY.type("Text").text("手机号登录")，或直接粘贴源码 HosBy.between_texts(...) / 日志元组',
                "type": "例如: Button 或 Text 或 TextInput (ArkUI 类型)",
                "description": "例如: 无障碍描述文本",
            }
        self.edit_selector.setPlaceholderText(tips.get(strategy, "请输入定位选择器表达式"))

    def do_search(self) -> None:
        parent_win = getattr(self, "inspector", None) or self.parent()
        if parent_win and hasattr(parent_win, "xml_root") and parent_win.xml_root is not None:
            self.xml_root = parent_win.xml_root
            if hasattr(parent_win, "comp_map"):
                self.comp_map = parent_win.comp_map
            if hasattr(parent_win, "flat_components"):
                self.flat_components = parent_win.flat_components

        strategy = self.combo_strategy.currentData()
        val = self.edit_selector.text().strip()
        self.list_results.setUpdatesEnabled(False)
        self.list_results.clear()
        self.matched_components.clear()
        self.btn_tap.setEnabled(False)
        self.btn_send_keys.setEnabled(False)

        self.edit_selector.setStyleSheet("")
        self.lbl_status.setStyleSheet("color: #0284c7; font-weight: 600;")

        if not val:
            self.list_results.setUpdatesEnabled(True)
            self.lbl_status.setText("请输入有效的定位表达式")
            return

        hos_pre_err = None
        if self.platform == "harmony":
            res_strat, res_val, hos_pre_err = resolve_harmony_locator_input(val)
            if res_strat:
                if res_strat != strategy:
                    target_idx = self.combo_strategy.findData(res_strat)
                    if target_idx >= 0:
                        self.combo_strategy.blockSignals(True)
                        self.combo_strategy.setCurrentIndex(target_idx)
                        self.combo_strategy.blockSignals(False)
                        self._update_format_pills_active_state(res_strat)
                        self.update_placeholder()
                        strategy = res_strat
                if res_val is not None:
                    val = res_val

        syntax_err = hos_pre_err
        example_str = (
            'HosBy.between_texts(after_text="密码验证登录", before_text="我已阅读且同意", target_type="Image")'
            if hos_pre_err
            else ""
        )
        if syntax_err:
            pass
        elif self.platform == "ios":
            syntax_err, example_str = validate_ios_selector_syntax(strategy, val)
        elif strategy == "hypium":
            syntax_err, _ = parse_hypium_by_expression(val)
            example_str = 'BY.isAfter(BY.text("密码验证登录")).isBefore(BY.text("我已阅读且同意", 1)).type("Image") 或 HosBy.text_contains("我已阅读且同意", "Text")'
        elif strategy == "xpath":
            syntax_err = validate_xpath_syntax(val)
            example_str = "//Text[@text='会员中心'] 或 //Button[contains(@text, '发送')]"
        elif strategy == "id":
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到 XPath 路径语法特征；当前策略为 [id]，若要使用路径定位请切换策略为 [xpath]"
                example_str = "login_button 或 send_btn 或 com.santiao.im:id/btn_send"
            elif val.startswith("@"):
                syntax_err = "ID 选择器无需添加 '@' 前缀；请直接输入组件 ID 或 Key"
                example_str = val.lstrip("@")
            elif " " in val and self.platform != "ios":
                syntax_err = "组件 ID 标识通常不包含空格；若要根据展示文本匹配，请将策略切换为 [text]"
                example_str = val.replace(" ", "_")
        elif strategy == "text":
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到 XPath 表达式语法；当前策略为 [text] 纯文本匹配，请直接输入文本内容"
                m_txt = re.findall(r"['\"](.*?)['\"]", val)
                example_str = m_txt[0] if m_txt else "测试0225"
            elif val.startswith("@text="):
                syntax_err = "无需添加 '@text=' 前缀；当前策略为纯文本内容匹配，直接输入文本即可"
                example_str = val.replace("@text=", "").strip("'\"")
            elif re.match(r"^text\s*\(", val):
                syntax_err = "当前策略为纯文本匹配，无需使用 text(...) 函数包裹"
                m_txt = re.findall(r"['\"](.*?)['\"]", val)
                example_str = m_txt[0] if m_txt else "设置"
        elif strategy in ("type", "class name"):
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到路径语法；当前策略为 [type/class name] 组件类型匹配，无需斜杠或方括号"
                clean_type = re.sub(r"[^a-zA-Z0-9_]", "", val.split("/")[-1].split("[")[0])
                example_str = clean_type or "Button 或 Text 或 ListItem"
            elif any(ch in val for ch in ("@", "=", "(", ")")):
                syntax_err = "组件类型名不能包含 '@'、'=' 或括号；请输入标准的组件类型名称"
                example_str = "Button 或 TextInput 或 Column"
        elif strategy in ("description", "accessibility id"):
            if val.startswith(("//", "/", ".")) or ("[" in val and "]" in val):
                syntax_err = "检测到 XPath 语法特征；当前策略为无障碍描述匹配，请直接输入描述文本"
                example_str = "返回 或 关闭"
        elif strategy == "uiautomator":
            if val.count('"') % 2 != 0 or val.count("'") % 2 != 0 or val.count("(") != val.count(")"):
                syntax_err = "UiAutomator 表达式引号或括号未正确闭合"
                example_str = 'new UiSelector().text("设置") 或 text("设置")'
        elif strategy == "predicate":
            if val.count('"') % 2 != 0 or val.count("'") % 2 != 0:
                syntax_err = "Predicate 表达式字符串引号未闭合"
                example_str = 'label == "设置" 或 name CONTAINS "btn"'
        elif strategy == "class chain":
            if val.count("[") != val.count("]"):
                syntax_err = "Class Chain 表达式方括号 '[' 与 ']' 未正确闭合"
                example_str = '**/XCUIElementTypeButton[`label == "确定"`]'

        if syntax_err:
            self.show_syntax_error(syntax_err, example=example_str)
            return

        matched: List[Dict[str, Any]] = []
        val_lower = val.lower()

        def eval_atomic_predicate(atom_expr: str, comp: Dict[str, Any]) -> bool:
            sub = atom_expr.strip().strip("()")
            if not sub:
                return True
            is_neg = False
            if re.match(r"^(?:NOT\s+|!\s*)", sub, re.IGNORECASE):
                is_neg = True
                sub = re.sub(r"^(?:NOT\s+|!\s*)", "", sub, flags=re.IGNORECASE).strip().strip("()")

            raw_attrs = comp.get("raw_attributes", {}) or comp.get("raw", {})
            c_label = str(raw_attrs.get("label", "") or comp.get("text", "") or raw_attrs.get("value", "")).lower()
            c_name = str(raw_attrs.get("name", "") or comp.get("id", "") or raw_attrs.get("label", "")).lower()
            c_type = comp.get("type", "").lower()
            c_type_full = c_type if c_type.startswith("xcuielementtype") else f"xcuielementtype{c_type}"
            c_type_short = c_type.replace("xcuielementtype", "")
            c_val = str(raw_attrs.get("value", "")).lower()

            res = True
            in_match = re.search(r"^([A-Za-z_][A-Za-z0-9_\.]*)\s+IN(?:\s*\[[cd]+\])?\s*\{([^}]+)\}$", sub, re.IGNORECASE)
            if in_match:
                attr_key = in_match.group(1).lower()
                items = []
                for raw_s in in_match.group(2).split(","):
                    tok = raw_s.strip()
                    if not tok:
                        continue
                    if (tok.startswith("'") and tok.endswith("'")) or (tok.startswith('"') and tok.endswith('"')):
                        tok = tok[1:-1]
                    items.append(tok.lower())
                if attr_key == "type":
                    res = (c_type in items) or (c_type_full in items) or (c_type_short in items)
                else:
                    target_val = c_label if attr_key == "label" else (c_name if attr_key == "name" else c_val)
                    res = target_val in items
            else:
                cmp_m = re.search(
                    r"^([A-Za-z_][A-Za-z0-9_\.]*)\s*(==|!=|=|<>|<=|>=|<|>|\b(?:CONTAINS|BEGINSWITH|ENDSWITH|LIKE|MATCHES)\b(?:\s*\[[cd]+\])?)\s*(.+)$",
                    sub,
                    re.IGNORECASE,
                )
                if cmp_m:
                    attr_key = cmp_m.group(1).lower()
                    op = cmp_m.group(2).upper()
                    rhs = cmp_m.group(3).strip()
                    if (rhs.startswith("'") and rhs.endswith("'")) or (rhs.startswith('"') and rhs.endswith('"')):
                        rhs = rhs[1:-1]
                    rhs_lower = rhs.lower()
                    if attr_key == "type":
                        rhs_short = rhs_lower.replace("xcuielementtype", "")
                        rhs_full = rhs_lower if rhs_lower.startswith("xcuielementtype") else f"xcuielementtype{rhs_lower}"
                        is_type_eq = (
                            c_type == rhs_lower
                            or c_type == rhs_short
                            or c_type_full == rhs_full
                            or c_type_short == rhs_short
                        )
                        res = is_type_eq if op in ("==", "=") else not is_type_eq
                    else:
                        if attr_key in ("visible", "isvisible"):
                            raw_vis = raw_attrs.get("visible") if "visible" in raw_attrs else comp.get("is_visible", "")
                            lhs = str(raw_vis).lower()
                        else:
                            lhs = (
                                c_label
                                if attr_key == "label"
                                else (c_name if attr_key == "name" else (c_val if attr_key == "value" else str(raw_attrs.get(attr_key, "")).lower()))
                            )
                        bool_true = {"true", "1", "yes"}
                        bool_false = {"false", "0", "no"}
                        if op in ("==", "="):
                            if (lhs in bool_true or lhs in bool_false) and (rhs_lower in bool_true or rhs_lower in bool_false):
                                res = (lhs in bool_true) == (rhs_lower in bool_true)
                            else:
                                res = lhs == rhs_lower
                        elif op in ("!=", "<>"):
                            if (lhs in bool_true or lhs in bool_false) and (rhs_lower in bool_true or rhs_lower in bool_false):
                                res = (lhs in bool_true) != (rhs_lower in bool_true)
                            else:
                                res = lhs != rhs_lower
                        elif op.startswith("BEGINSWITH"):
                            res = lhs.startswith(rhs_lower)
                        elif op.startswith("ENDSWITH"):
                            res = lhs.endswith(rhs_lower)
                        elif op.startswith("MATCHES"):
                            try:
                                res = bool(re.search(rhs, raw_attrs.get(attr_key, "") or ""))
                            except Exception:
                                res = False
                        else:
                            res = rhs_lower in lhs
                else:
                    res = False

            return (not res) if is_neg else res

        def eval_ast_bool(node: ast.AST, c_map: Dict[str, bool]) -> bool:
            if isinstance(node, ast.Expression):
                return eval_ast_bool(node.body, c_map)
            if isinstance(node, ast.BoolOp):
                if isinstance(node.op, ast.And):
                    return all(eval_ast_bool(v, c_map) for v in node.values)
                if isinstance(node.op, ast.Or):
                    return any(eval_ast_bool(v, c_map) for v in node.values)
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                return not eval_ast_bool(node.operand, c_map)
            if isinstance(node, ast.Name):
                return c_map.get(node.id, False)
            if isinstance(node, ast.Constant):
                return bool(node.value)
            return False

        def match_ios_predicate(pred_expr: str, comps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            p_err, atom_list, py_expr = tokenize_ios_predicate(pred_expr)
            if p_err or not atom_list:
                atom_list = [pred_expr]
                py_expr = "_c_0"
            try:
                eval_tree = ast.parse(py_expr, mode="eval")
            except Exception:
                eval_tree = None
            out = []
            for comp in comps:
                if eval_tree:
                    c_map = {f"_c_{k}": eval_atomic_predicate(atom, comp) for k, atom in enumerate(atom_list)}
                    if eval_ast_bool(eval_tree, c_map):
                        out.append(comp)
                elif all(eval_atomic_predicate(atom, comp) for atom in atom_list):
                    out.append(comp)
            return out

        try:
            if strategy == "id":
                for c in self.flat_components:
                    cid = c.get("id", "")
                    raw_attrs = c.get("raw_attributes", {}) or c.get("raw", {})
                    raw_id = raw_attrs.get("resource-id", "") or raw_attrs.get("name", "") or raw_attrs.get("id", "")
                    raw_label = raw_attrs.get("label", "") if self.platform == "ios" else ""
                    raw_ident = raw_attrs.get("identifier", "") if self.platform == "ios" else ""
                    targets = [t for t in (cid, raw_id, raw_label, raw_ident) if t]
                    if any(val_lower == t.lower() or val_lower in t.lower() for t in targets):
                        matched.append(c)
            elif strategy == "accessibility id":
                for c in self.flat_components:
                    text = c.get("text", "")
                    desc = c.get("raw_attributes", {}).get("description", "") or c.get("raw_attributes", {}).get("content-desc", "")
                    name = c.get("raw_attributes", {}).get("name", "") or c.get("raw_attributes", {}).get("label", "")
                    if (text and val_lower in text.lower()) or (desc and val_lower in desc.lower()) or (name and val_lower in name.lower()):
                        matched.append(c)
            elif strategy in ("class name", "type"):
                for c in self.flat_components:
                    ctype = c.get("type", "")
                    if self.platform == "ios":
                        ctype_short = ctype.lower().replace("xcuielementtype", "")
                        val_short = val_lower.replace("xcuielementtype", "")
                        c_full_type = str(c.get("full_type", "")).lower()
                        if val_short == ctype_short or val_lower == c_full_type or val_short in ctype_short or val_lower in ctype.lower():
                            matched.append(c)
                    elif ctype.lower() == val_lower or val_lower in ctype.lower():
                        matched.append(c)
            elif strategy == "text":
                for c in self.flat_components:
                    text = c.get("text", "") or c.get("raw_attributes", {}).get("text", "") or c.get("raw_attributes", {}).get("label", "")
                    if text and (val_lower == text.lower() or val_lower in text.lower()):
                        matched.append(c)
            elif strategy == "description":
                for c in self.flat_components:
                    desc = c.get("raw_attributes", {}).get("description", "") or c.get("raw_attributes", {}).get("content-desc", "")
                    if desc and (val_lower == desc.lower() or val_lower in desc.lower()):
                        matched.append(c)
            elif strategy == "uiautomator":
                m_text = re.search(r'text(?:Contains)?\s*\(\s*["\']([^"\']+)["\']\s*\)', val, re.IGNORECASE)
                m_desc = re.search(r'description(?:Contains)?\s*\(\s*["\']([^"\']+)["\']\s*\)', val, re.IGNORECASE)
                m_id = re.search(r'resourceId(?:Matches)?\s*\(\s*["\']([^"\']+)["\']\s*\)', val, re.IGNORECASE)
                m_cls = re.search(r'className\s*\(\s*["\']([^"\']+)["\']\s*\)', val, re.IGNORECASE)
                target_t = m_text.group(1).lower() if m_text else None
                target_d = m_desc.group(1).lower() if m_desc else None
                target_i = m_id.group(1).lower() if m_id else None
                target_c = m_cls.group(1).lower() if m_cls else None
                for c in self.flat_components:
                    c_text = c.get("text", "").lower()
                    c_desc = str(c.get("raw_attributes", {}).get("content-desc", "")).lower()
                    c_id = c.get("id", "").lower()
                    c_type = c.get("type", "").lower()
                    if target_t and target_t not in c_text:
                        continue
                    if target_d and target_d not in c_desc:
                        continue
                    if target_i and target_i not in c_id:
                        continue
                    if target_c and target_c != c_type and target_c not in c_type:
                        continue
                    if not any([target_t, target_d, target_i, target_c]):
                        if val_lower not in c_text and val_lower not in c_desc and val_lower not in c_id:
                            continue
                    matched.append(c)
            elif strategy == "predicate":
                matched = match_ios_predicate(val, self.flat_components)
            elif (
                strategy == "class chain"
                and "`" not in val
                and "$" not in val
                and re.fullmatch(r"(\*\*/|/)?[\w*]+(\[-?\d+\])?(/(\*\*/)?[\w*]+(\[-?\d+\])?)*", val.strip())
            ):
                chain_xp = val.strip().replace("**/", "//")
                if not chain_xp.startswith("/"):
                    chain_xp = "/" + chain_xp
                chain_xp = re.sub(r"(?<=/)(?!XCUIElementType|\*)([A-Za-z]\w*)", r"XCUIElementType\1", chain_xp)
                chain_xp = re.sub(
                    r"\[-(\d+)\]",
                    lambda m: "[last()]" if m.group(1) == "1" else f"[last()-{int(m.group(1)) - 1}]",
                    chain_xp,
                )
                matched = self.match_xpath(chain_xp)
            elif strategy == "class chain":
                raw_chain = val.strip()
                segs = [s.strip() for s in re.split(r"/(?![^\[]*\])", raw_chain) if s.strip() and s.strip() not in ("**", "*")]
                last_seg = segs[-1] if segs else raw_chain.replace("**/", "").replace("/*", "").strip()

                pred_inner = ""
                desc_pred_inner = ""
                idx_filter = None
                chain_type = last_seg

                m_pred = re.search(r"\[`([^`]+)`\]", last_seg)
                m_desc_pred = re.search(r"\[\$([^$]+)\$\]", last_seg)
                if m_pred:
                    pred_inner = m_pred.group(1).strip()
                    chain_type = last_seg[: m_pred.start()].strip()
                elif m_desc_pred:
                    desc_pred_inner = m_desc_pred.group(1).strip()
                    chain_type = last_seg[: m_desc_pred.start()].strip()
                else:
                    m_idx = re.search(r"\[(-?\d+)\]", last_seg)
                    if m_idx:
                        idx_filter = int(m_idx.group(1))
                        chain_type = last_seg[: m_idx.start()].strip()
                    else:
                        m_plain_pred = re.search(r"\[([a-zA-Z_].+)\]", last_seg)
                        if m_plain_pred:
                            pred_inner = m_plain_pred.group(1).strip()
                            chain_type = last_seg[: m_plain_pred.start()].strip()

                chain_type_clean = chain_type.replace("**/", "").replace("/*", "").strip()
                chain_type_lower = chain_type_clean.lower()
                chain_type_short = chain_type_lower.replace("xcuielementtype", "")

                desc_matched_ids = set()
                xml_node_by_id: Dict[str, Any] = {}
                if desc_pred_inner:
                    desc_matched_ids = {
                        mc.get("node_id")
                        for mc in match_ios_predicate(desc_pred_inner, list(self.comp_map.values()) or self.flat_components)
                        if mc.get("node_id")
                    }
                    if self.xml_root is not None:
                        xml_node_by_id = {
                            el.attrib.get("node_id"): el
                            for el in self.xml_root.iter()
                            if el.attrib.get("node_id")
                        }

                cand_matched = []
                for c in self.flat_components:
                    c_type = c.get("type", "").lower()
                    c_type_short = c_type.replace("xcuielementtype", "")
                    c_full_type = str(c.get("full_type", "")).lower()

                    if chain_type_clean and chain_type_clean != "*":
                        type_matched = (
                            chain_type_short == c_type_short
                            or chain_type_lower == c_full_type
                            or chain_type_short in c_type_short
                            or chain_type_lower in c_type
                        )
                        if not type_matched:
                            continue

                    if pred_inner and not match_ios_predicate(pred_inner, [c]):
                        continue

                    if desc_pred_inner:
                        xml_el = xml_node_by_id.get(c.get("node_id"))
                        if xml_el is not None:
                            has_desc = any(
                                sub is not xml_el and sub.attrib.get("node_id") in desc_matched_ids
                                for sub in xml_el.iter()
                            )
                            if not has_desc:
                                continue
                        else:
                            continue

                    cand_matched.append(c)

                if idx_filter is not None and cand_matched:
                    if 0 < idx_filter <= len(cand_matched):
                        matched = [cand_matched[idx_filter - 1]]
                    elif idx_filter < 0 and abs(idx_filter) <= len(cand_matched):
                        matched = [cand_matched[idx_filter]]
                    else:
                        matched = []
                else:
                    matched = cand_matched
            elif strategy == "hypium":
                matched = self.match_hypium_by(val)
            elif strategy == "xpath":
                matched = self.match_xpath(val)
        except Exception as e:
            err_text = str(e)
            if err_text.startswith("XPath 语法错误:"):
                err_text = err_text.replace("XPath 语法错误:", "").strip()
            self.show_syntax_error(err_text, example=example_str)
            return

        total_matched_raw = len(matched)
        if hasattr(self, "chk_only_visible") and self.chk_only_visible.isChecked():
            matched = [c for c in matched if not c.get("is_occluded", False) and c.get("is_exposed", True)]

        self.matched_components = matched
        if total_matched_raw != len(matched):
            self.lbl_status.setText(f"匹配到 {len(matched)} 个真实展示元素 (智能过滤 {total_matched_raw - len(matched)} 个被遮挡层)")
        else:
            self.lbl_status.setText(f"匹配到 {len(matched)} 个元素")

        if not matched:
            strat_tips = {
                "id": "建议核对组件 Key/ID 属性是否存在，或切换为 [text] / [xpath] 策略重试",
                "xpath": "建议核对标签名大小写、属性值及层级，或点击【填入主视窗选中元素】获取推荐路径",
                "text": "建议核对文本大小写、去除首尾空格，或取消勾选【仅匹配当前真实展示元素】重试",
                "hypium": "建议核对 BY.text/type/isAfter/isBefore 参数与匹配模式 (0=精确, 1=包含, 4=正则)，或取消勾选【仅匹配当前真实展示元素】排查背景页命中情况",
                "type": "未找到该类型的组件，请核对组件类型拼写 (如 Button、Text、ListItem、Flex)",
                "class name": "未找到该类型的组件，请核对类型名拼写",
                "description": "未找到包含该无障碍描述的组件，请检查 accessibility 属性设置",
                "accessibility id": "未找到包含该描述的组件，请检查 content-desc / label 属性",
            }
            tip_detail = strat_tips.get(strategy, "请核对选择器表达式与当前真机画面组件是否匹配")
            strat_label = self.combo_strategy.currentText().split(" (")[0]
            item = QListWidgetItem(f"⚠️ 未找到任何符合条件的元素 (策略: {strat_label})")
            item.setForeground(QColor("#d97706"))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(item)

            tip_item = QListWidgetItem(f"💡 查找建议: {tip_detail}")
            tip_item.setForeground(QColor("#0369a1"))
            tip_item.setBackground(QBrush(QColor("#f0f9ff")))
            tip_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(tip_item)

            self.list_results.setUpdatesEnabled(True)
            return

        render_limit = 200
        for idx, comp in enumerate(matched[:render_limit]):
            c_type = comp.get("type", "Component")
            c_scheme = get_dom_tag_color(c_type)
            title = f"元素 {idx + 1} - <{c_type}"
            raw_attrs = comp.get("raw_attributes") or comp.get("raw") or {}
            if self.platform == "ios":
                ios_name = raw_attrs.get("name") or raw_attrs.get("id") or comp.get("id") or ""
                ios_label = raw_attrs.get("label") or ""
                ios_value = raw_attrs.get("value") or comp.get("text") or ""
                if ios_value:
                    short_v = ios_value if len(ios_value) <= 20 else ios_value[:20] + "..."
                    title += f' value="{short_v}"'
                if ios_name:
                    short_n = ios_name if len(ios_name) <= 20 else ios_name[:20] + "..."
                    title += f' name="{short_n}"'
                if ios_label and ios_label != ios_value:
                    short_l = ios_label if len(ios_label) <= 20 else ios_label[:20] + "..."
                    title += f' label="{short_l}"'
            else:
                if comp.get("id"):
                    title += f' id="{comp["id"]}"'
                if comp.get("text"):
                    c_text = comp["text"]
                    short_t = c_text if len(c_text) <= 22 else c_text[:22] + "..."
                    title += f' text="{short_t}"'
            title += f' bounds="[{comp["left"]},{comp["top"]}][{comp["right"]},{comp["bottom"]}]">'
            list_item = QListWidgetItem(title)
            list_item.setData(Qt.ItemDataRole.UserRole, comp["node_id"])
            list_item.setForeground(QColor(c_scheme["text"]))
            list_item.setBackground(QBrush(QColor(c_scheme["bg"])))
            self.list_results.addItem(list_item)

        if len(matched) > render_limit:
            tip_item = QListWidgetItem(f"... 已截断显示前 {render_limit} 条匹配项 (共 {len(matched)} 条)")
            tip_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_results.addItem(tip_item)

        self.list_results.setUpdatesEnabled(True)
        self.list_results.setCurrentRow(0)
        self.on_item_clicked(self.list_results.item(0))
        self._save_memory()

    def _extract_comps_from_xml_nodes(self, nodes: List[Any]) -> List[Dict[str, Any]]:
        matched = []
        matched_ids = set()
        for elem in nodes:
            if not hasattr(elem, "attrib"):
                continue
            node_id = elem.attrib.get("node_id")
            if not node_id or node_id in matched_ids:
                continue
            matched_ids.add(node_id)

            comp = self.comp_map.get(node_id) if hasattr(self, "comp_map") and self.comp_map else None
            if not comp:
                for c in self.flat_components:
                    if c.get("node_id") == node_id:
                        comp = c
                        break
            if comp:
                elem_tag = str(getattr(elem, "tag", "")).lower()
                comp_type = str(comp.get("type", "")).lower()
                comp_full = str(comp.get("full_type", "")).lower()
                if elem_tag and comp_type and elem_tag != "component":
                    elem_short = elem.attrib.get("short_type", "").lower() if hasattr(elem, "attrib") else ""
                    if not elem_short:
                        elem_short = elem_tag.replace("xcuielementtype", "").split(".")[-1]
                    type_matched = (
                        elem_tag == comp_type
                        or elem_tag == comp_full
                        or elem_short == comp_type
                        or elem_tag.endswith(comp_type)
                    )
                    if not type_matched:
                        continue
                matched.append(comp)
        return matched

    def _evaluate_xpath_natively(self, root_elem: ET.Element, xp: str) -> List[ET.Element]:
        parent_map: Dict[ET.Element, ET.Element] = {}
        for p in root_elem.iter():
            for c in p:
                parent_map[c] = p

        raw_xp = xp.strip()

        if raw_xp.startswith("("):
            p_depth = 0
            match_paren_idx = -1
            in_s = False
            in_d = False
            for idx, ch in enumerate(raw_xp):
                if ch == "'" and not in_d:
                    in_s = not in_s
                elif ch == '"' and not in_s:
                    in_d = not in_d
                elif not in_s and not in_d:
                    if ch == "(":
                        p_depth += 1
                    elif ch == ")":
                        p_depth -= 1
                        if p_depth == 0:
                            match_paren_idx = idx
                            break
            if match_paren_idx != -1:
                inner_xp = raw_xp[1:match_paren_idx].strip()
                outer_tail = raw_xp[match_paren_idx + 1 :].strip()
                if not outer_tail:
                    return self._evaluate_xpath_natively(root_elem, inner_xp)
                if outer_tail.startswith("[") and outer_tail.endswith("]"):
                    inner_nodes = self._evaluate_xpath_natively(root_elem, inner_xp)
                    pred = outer_tail[1:-1].strip()
                    if pred == "last()":
                        return [inner_nodes[-1]] if inner_nodes else []
                    if pred.isdigit():
                        idx = int(pred)
                        if 1 <= idx <= len(inner_nodes):
                            return [inner_nodes[idx - 1]]
                        return []

        clean_xp = raw_xp.strip().strip("()")
        if clean_xp.startswith(".//"):
            clean_xp = clean_xp[1:]
        elif clean_xp.startswith("./"):
            clean_xp = clean_xp[1:]

        if "|" in clean_xp:
            u_parts: List[str] = []
            u_buf: List[str] = []
            u_b_level = 0
            u_p_level = 0
            u_in_sq = False
            u_in_dq = False
            for ch in clean_xp:
                if ch == "'" and not u_in_dq:
                    u_in_sq = not u_in_sq
                    u_buf.append(ch)
                elif ch == '"' and not u_in_sq:
                    u_in_dq = not u_in_dq
                    u_buf.append(ch)
                elif not u_in_sq and not u_in_dq:
                    if ch == "[":
                        u_b_level += 1
                        u_buf.append(ch)
                    elif ch == "]":
                        u_b_level = max(0, u_b_level - 1)
                        u_buf.append(ch)
                    elif ch == "(":
                        u_p_level += 1
                        u_buf.append(ch)
                    elif ch == ")":
                        u_p_level = max(0, u_p_level - 1)
                        u_buf.append(ch)
                    elif ch == "|" and u_b_level == 0 and u_p_level == 0:
                        u_parts.append("".join(u_buf).strip())
                        u_buf = []
                    else:
                        u_buf.append(ch)
                else:
                    u_buf.append(ch)
            u_parts.append("".join(u_buf).strip())

            if len(u_parts) > 1:
                merged_nodes: List[ET.Element] = []
                seen_node_ids = set()
                for sub_xp in u_parts:
                    if sub_xp:
                        for n_elem in self._evaluate_xpath_natively(root_elem, sub_xp):
                            elem_key = id(n_elem)
                            if elem_key not in seen_node_ids:
                                seen_node_ids.add(elem_key)
                                merged_nodes.append(n_elem)
                return merged_nodes

        steps: List[Tuple[str, str]] = []
        i = 0
        n = len(clean_xp)
        current_op = "//" if clean_xp.startswith("//") else ("/" if clean_xp.startswith("/") else "//")
        if clean_xp.startswith("//"):
            i = 2
        elif clean_xp.startswith("/"):
            i = 1

        buf: List[str] = []
        bracket_level = 0
        while i < n:
            ch = clean_xp[i]
            if ch == "[":
                bracket_level += 1
                buf.append(ch)
                i += 1
            elif ch == "]":
                bracket_level = max(0, bracket_level - 1)
                buf.append(ch)
                i += 1
            elif bracket_level == 0 and clean_xp[i : i + 2] == "//":
                seg = "".join(buf).strip()
                if seg:
                    steps.append((current_op, seg))
                current_op = "//"
                buf = []
                i += 2
            elif bracket_level == 0 and clean_xp[i : i + 1] == "/":
                seg = "".join(buf).strip()
                if seg:
                    steps.append((current_op, seg))
                current_op = "/"
                buf = []
                i += 1
            else:
                buf.append(ch)
                i += 1

        last_seg = "".join(buf).strip()
        if last_seg:
            steps.append((current_op, last_seg))
        if not steps:
            return []

        current_nodes: List[ET.Element] = [root_elem]

        for op, step_str in steps:
            axis_name = ""
            tag_and_pred = step_str
            if "::" in step_str:
                axis_parts = step_str.split("::", 1)
                axis_name = axis_parts[0].strip().lower()
                tag_and_pred = axis_parts[1].strip()

            m = re.match(r"^([a-zA-Z0-9_\-\*]+|\.\.|\.|node\(\)|text\(\))(.*)$", tag_and_pred)
            if not m:
                raise ValueError(f"步进 '{step_str}' 节点名称格式非法")
            tag_name, predicate_str = m.group(1), m.group(2)
            if predicate_str and predicate_str.strip() and not predicate_str.strip().startswith("["):
                raise ValueError(f"节点 '{tag_name}' 后面存在未用方括号 '[]' 包裹的非法字符或空格: '{predicate_str.strip()}'")
            tag_lower = tag_name.lower()

            next_nodes: List[ET.Element] = []

            for node in current_nodes:
                candidates: List[ET.Element] = []
                if axis_name == "following-sibling":
                    p = parent_map.get(node)
                    if p is not None:
                        siblings = list(p)
                        try:
                            candidates = siblings[siblings.index(node) + 1 :]
                        except ValueError:
                            pass
                elif axis_name == "preceding-sibling":
                    p = parent_map.get(node)
                    if p is not None:
                        siblings = list(p)
                        try:
                            candidates = list(reversed(siblings[: siblings.index(node)]))
                        except ValueError:
                            pass
                elif axis_name == "preceding":
                    all_elems = list(root_elem.iter())
                    try:
                        candidates = list(reversed(all_elems[: all_elems.index(node)]))
                    except ValueError:
                        pass
                elif axis_name == "following":
                    all_elems = list(root_elem.iter())
                    try:
                        candidates = all_elems[all_elems.index(node) + 1 :]
                    except ValueError:
                        pass
                elif axis_name == "parent":
                    p = parent_map.get(node)
                    if p is not None:
                        candidates = [p]
                elif axis_name == "ancestor":
                    curr_p = parent_map.get(node)
                    while curr_p is not None:
                        candidates.append(curr_p)
                        curr_p = parent_map.get(curr_p)
                else:
                    if op == "/":
                        candidates = list(node)
                    else:
                        candidates = list(node.iter())
                        if node in candidates:
                            candidates.remove(node)

                filtered_by_tag: List[ET.Element] = []
                query_short_l = tag_lower.replace("xcuielementtype", "").split(".")[-1]
                for cand in candidates:
                    cand_tag_l = cand.tag.lower()
                    cand_full_l = str(cand.attrib.get("full_type", "")).lower()
                    cand_short_l = str(cand.attrib.get("short_type", "")).lower() or cand_tag_l.replace("xcuielementtype", "").split(".")[-1]
                    if (
                        tag_name == "*"
                        or cand_tag_l == tag_lower
                        or cand_full_l == tag_lower
                        or cand_short_l == query_short_l
                        or cand_short_l == tag_lower
                        or cand_tag_l.endswith(tag_lower)
                    ):
                        filtered_by_tag.append(cand)

                if predicate_str:
                    pred_list: List[str] = []
                    p_buf: List[str] = []
                    p_depth = 0
                    p_in_sq = False
                    p_in_dq = False
                    for ch in predicate_str:
                        if ch == "'" and not p_in_dq:
                            p_in_sq = not p_in_sq
                            p_buf.append(ch)
                        elif ch == '"' and not p_in_sq:
                            p_in_dq = not p_in_dq
                            p_buf.append(ch)
                        elif not p_in_sq and not p_in_dq:
                            if ch == "[":
                                if p_depth > 0:
                                    p_buf.append(ch)
                                p_depth += 1
                            elif ch == "]":
                                p_depth -= 1
                                if p_depth == 0:
                                    pred_list.append("".join(p_buf).strip())
                                    p_buf = []
                                else:
                                    p_buf.append(ch)
                            elif p_depth > 0:
                                p_buf.append(ch)
                        else:
                            p_buf.append(ch)

                    cand_results = filtered_by_tag
                    for pred in pred_list:
                        pred = pred.strip()
                        if not pred:
                            continue
                        if pred.isdigit():
                            idx = int(pred) - 1
                            cand_results = [cand_results[idx]] if 0 <= idx < len(cand_results) else []
                            continue
                        if pred == "last()":
                            cand_results = [cand_results[-1]] if cand_results else []
                            continue

                        def _eval_atomic(el_node: ET.Element, p_str: str) -> bool:
                            p_str = p_str.strip()
                            attrs = el_node.attrib
                            m_contains = re.match(
                                r"^contains\s*\(\s*(@[a-zA-Z0-9_\-]+|text\(\))\s*,\s*['\"](.*?)['\"]\s*\)$",
                                p_str,
                                re.IGNORECASE,
                            )
                            if m_contains:
                                target_k, target_v = m_contains.group(1), m_contains.group(2)
                                actual_val = (
                                    (attrs.get("text", "") or attrs.get("label", "") or (el_node.text or ""))
                                    if target_k == "text()"
                                    else attrs.get(target_k[1:], "")
                                )
                                return target_v in str(actual_val)

                            m_matches = re.match(
                                r"^matches\s*\(\s*(@[a-zA-Z0-9_\-]+|text\(\))\s*,\s*['\"](.*?)['\"](?:\s*,\s*['\"](.*?)['\"])?\s*\)$",
                                p_str,
                                re.IGNORECASE,
                            )
                            if m_matches:
                                target_k, pat, flags = m_matches.group(1), m_matches.group(2), m_matches.group(3) or ""
                                actual_val = (
                                    (attrs.get("text", "") or attrs.get("label", "") or (el_node.text or ""))
                                    if target_k == "text()"
                                    else attrs.get(target_k[1:], "")
                                )
                                py_flags = re.IGNORECASE if "i" in flags.lower() else 0
                                try:
                                    return bool(re.search(pat, str(actual_val), py_flags))
                                except Exception:
                                    return False

                            m_eq = re.match(r"^@([a-zA-Z0-9_\-]+)\s*=\s*['\"](.*?)['\"]$", p_str)
                            if m_eq:
                                attr_k, attr_v = m_eq.group(1), m_eq.group(2)
                                actual_v = attrs.get(attr_k, "")
                                if not actual_v and attr_k in ("id", "resource-id", "name"):
                                    actual_v = attrs.get("id") or attrs.get("resource-id") or attrs.get("name") or ""
                                elif not actual_v and attr_k in ("text", "label", "value"):
                                    actual_v = attrs.get("text") or attrs.get("label") or attrs.get("value") or ""
                                return str(actual_v) == attr_v

                            if p_str.startswith("@"):
                                return bool(p_str[1:] in attrs and attrs[p_str[1:]])

                            if p_str.startswith((".", "//", "/")):
                                try:
                                    return bool(self._evaluate_xpath_natively(el_node, p_str))
                                except Exception:
                                    return False

                            return any(sub.tag.lower() == p_str.lower() for sub in el_node.iter() if sub is not el_node)

                        def _eval_predicate(el_node: ET.Element, p_str: str) -> bool:
                            p_str = p_str.strip()
                            if " or " in p_str:
                                return any(_eval_predicate(el_node, b) for b in re.split(r"\s+or\s+", p_str))
                            if " and " in p_str:
                                return all(_eval_predicate(el_node, b) for b in re.split(r"\s+and\s+", p_str))
                            return _eval_atomic(el_node, p_str)

                        cand_results = [el for el in cand_results if _eval_predicate(el, pred)]
                    next_nodes.extend(cand_results)
                else:
                    next_nodes.extend(filtered_by_tag)

            seen = set()
            dedup_nodes: List[ET.Element] = []
            for n_elem in next_nodes:
                elem_id = id(n_elem)
                if elem_id not in seen:
                    seen.add(elem_id)
                    dedup_nodes.append(n_elem)
            current_nodes = dedup_nodes

        return current_nodes

    def match_hypium_by(self, expr: str) -> List[Dict[str, Any]]:
        err, steps = parse_hypium_by_expression(expr)
        if err:
            raise ValueError(err)

        parent_map: Dict[ET.Element, ET.Element] = {}
        comp_by_elem: Dict[ET.Element, Dict[str, Any]] = {}
        ordered_items: List[Tuple[Optional[ET.Element], Dict[str, Any], int]] = []

        if self.xml_root is not None:
            for p in self.xml_root.iter():
                for ch in p:
                    parent_map[ch] = p

            idx_counter = 0
            for el in self.xml_root.iter():
                node_id = el.attrib.get("node_id")
                if not node_id:
                    continue
                comp = self.comp_map.get(node_id) if self.comp_map else None
                if not comp:
                    continue
                comp_by_elem[el] = comp
                ordered_items.append((el, comp, idx_counter))
                idx_counter += 1
        else:
            for idx_counter, comp in enumerate(self.flat_components):
                ordered_items.append((None, comp, idx_counter))

        def _is_ancestor(maybe_anc: Optional[ET.Element], node: Optional[ET.Element]) -> bool:
            if maybe_anc is None or node is None or maybe_anc is node:
                return False
            cur = parent_map.get(node)
            while cur is not None:
                if cur is maybe_anc:
                    return True
                cur = parent_map.get(cur)
            return False

        def _eval_chain(chain_steps: List[Tuple[str, Tuple[Any, ...]]]) -> List[Tuple[Optional[ET.Element], Dict[str, Any], int]]:
            candidates = list(ordered_items)
            for method, args in chain_steps:
                if not candidates:
                    break
                if method == "within":
                    container_elems = {el for el, _, _ in _eval_chain(args[0]) if el is not None}
                    if not container_elems:
                        candidates = []
                        continue
                    next_cands = []
                    for el, comp, idx in candidates:
                        cur = parent_map.get(el) if el is not None else None
                        found_anc = False
                        while cur is not None:
                            if cur in container_elems:
                                found_anc = True
                                break
                            cur = parent_map.get(cur)
                        if found_anc:
                            next_cands.append((el, comp, idx))
                    candidates = next_cands
                elif method == "isBefore":
                    anchors = _eval_chain(args[0])
                    if not anchors:
                        candidates = []
                        continue
                    candidates = [
                        (el, comp, idx)
                        for el, comp, idx in candidates
                        if any(idx < a_idx and not _is_ancestor(el, a_el) for a_el, _, a_idx in anchors)
                    ]
                elif method == "isAfter":
                    anchors = _eval_chain(args[0])
                    if not anchors:
                        candidates = []
                        continue
                    candidates = [
                        (el, comp, idx)
                        for el, comp, idx in candidates
                        if any(idx > a_idx and not _is_ancestor(a_el, el) for a_el, _, a_idx in anchors)
                    ]
                elif method == "xpath":
                    xp_matched_ids = {c.get("node_id") for c in self.match_xpath(str(args[0])) if c.get("node_id")}
                    candidates = [
                        (el, comp, idx)
                        for el, comp, idx in candidates
                        if comp.get("node_id") in xp_matched_ids
                    ]
                else:
                    candidates = [
                        (el, comp, idx)
                        for el, comp, idx in candidates
                        if _eval_hypium_attr_step(method, args, comp, el, parent_map, comp_by_elem)
                    ]
            return candidates

        return [comp for _, comp, _ in _eval_chain(steps)]

    def match_xpath(self, xpath: str) -> List[Dict[str, Any]]:
        xp = xpath.strip()
        if not xp:
            return []

        syntax_err = validate_xpath_syntax(xp)
        if syntax_err:
            raise ValueError(syntax_err)

        try:
            from lxml import etree

            has_lxml = True
        except (ImportError, ModuleNotFoundError):
            has_lxml = False

        if has_lxml and self.xml_root is not None:
            try:
                init_lxml_xpath_extensions()
                xml_bytes = ET.tostring(self.xml_root, encoding="utf-8")
                ltree = etree.fromstring(xml_bytes)
                matched_nodes = ltree.xpath(xp)
                if isinstance(matched_nodes, list):
                    return self._extract_comps_from_xml_nodes(matched_nodes)
            except Exception as e:
                err_str = str(e)
                if "XPathSyntaxError" in type(e).__name__ or "XPathEvalError" in type(e).__name__ or "Invalid" in err_str:
                    raise ValueError(f"XPath 语法错误: {err_str}")
                logger.warning(f"lxml 解析异常: {e}，自动降级至内置原生 XPath 引擎")

        if self.xml_root is not None:
            try:
                et_xp = xp
                if et_xp.startswith("//"):
                    et_xp = "." + et_xp
                elif not et_xp.startswith("."):
                    et_xp = ".//" + et_xp
                nodes = self.xml_root.findall(et_xp)
                if nodes:
                    res = self._extract_comps_from_xml_nodes(nodes)
                    if res:
                        return res
            except Exception:
                pass

            try:
                custom_nodes = self._evaluate_xpath_natively(self.xml_root, xp)
                if custom_nodes:
                    return self._extract_comps_from_xml_nodes(custom_nodes)
            except Exception as e:
                raise ValueError(str(e))
            return []

        return []

    def on_item_clicked(self, item: QListWidgetItem) -> None:
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self.btn_tap.setEnabled(True)
            self.btn_send_keys.setEnabled(True)
            self.element_picked.emit(node_id)
            self._save_memory()

    def on_tap_clicked(self) -> None:
        curr = self.list_results.currentItem()
        if curr:
            node_id = curr.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.lbl_status.setText("正在真机上执行点击动作...")
                QApplication.processEvents()
                self.tap_requested.emit(node_id)
                self.lbl_status.setText("已在设备上成功执行点击动作")

    def on_send_keys_clicked(self) -> None:
        curr = self.list_results.currentItem()
        if curr:
            node_id = curr.data(Qt.ItemDataRole.UserRole)
            if node_id:
                text, ok = ModernInputDialog.getText(self, "输入文本", "请输入要发送至该元素的文本内容:")
                if ok and text:
                    self.lbl_status.setText("正在向设备下发文本内容...")
                    QApplication.processEvents()
                    self.send_keys_requested.emit(node_id, text)
                    self.lbl_status.setText("文本已成功发送至目标组件")
