# -*- coding: utf-8 -*-
"""
UI 审查器通用弹窗与悬浮提示组件：
1. ModernMessageBox：纯白圆角置顶消息对话框；
2. ModernInputDialog：纯白圆角置顶输入对话框；
3. ToastNotification：无阻塞透明居中悬浮提示条。
"""
import sys
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from desktop_app.ui.inspector.common.icons import create_modern_app_icon


def _apply_win32_topmost(widget: QWidget) -> None:
    """在 Windows 下调用 SetWindowPos 强化顶层 Z-Order，非 Windows 平台安全跳过"""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = int(widget.winId())
        hwnd_topmost = -1
        swp_flags = 0x0002 | 0x0001 | 0x0040
        ctypes.windll.user32.SetWindowPos(hwnd, hwnd_topmost, 0, 0, 0, 0, swp_flags)
        ctypes.windll.user32.BringWindowToTop(hwnd)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


class ModernMessageBox(QDialog):
    """
    全中文轻奢圆角置顶消息对话框，支持自动吸附活跃窗口中央与 Windows 顶层强化。
    """

    IconNone = 0
    IconInformation = 1
    IconWarning = 2
    IconCritical = 3
    IconQuestion = 4

    def __init__(
        self,
        title: str = "提示",
        text: str = "",
        icon_type: int = IconInformation,
        buttons: Optional[List[str]] = None,
        parent: Optional[QWidget] = None,
        center_align: bool = False,
    ) -> None:
        super().__init__(parent)
        self.icon_type = icon_type
        self.center_align = center_align
        self.clicked_button = ""
        self._drag_pos = None

        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(title)
        self.setWindowIcon(create_modern_app_icon())

        self.buttons = ["确定"] if buttons is None else buttons
        self._init_ui(title, text)

    def _init_ui(self, title: str, text: str) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(0)

        self.card = QFrame(self)
        self.card.setObjectName("ModernMsgCard")
        self.card.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.card.setAutoFillBackground(True)
        self.card.setStyleSheet("""
            QFrame#ModernMsgCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(15, 23, 42, 50))
        shadow.setOffset(0, 6)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 顶部标题栏
        title_bar = QWidget(self.card)
        title_bar.setFixedHeight(44)
        title_bar.setAutoFillBackground(True)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid #f1f5f9;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 12, 0)
        title_layout.setSpacing(8)

        lbl_title_icon = QLabel()
        title_icon_map = {
            self.IconCritical: "❌",
            self.IconWarning: "⚠️",
            self.IconInformation: "ℹ️",
            self.IconQuestion: "❓",
        }
        lbl_title_icon.setText(title_icon_map.get(self.icon_type, "💡"))
        lbl_title_icon.setStyleSheet("font-size: 14px; background-color: #ffffff; border: none;")
        title_layout.addWidget(lbl_title_icon)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #0f172a; background-color: #ffffff; border: none;"
        )
        title_layout.addWidget(lbl_title, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: none;
                border-radius: 4px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #ef4444;
            }
        """)
        btn_close.clicked.connect(self.reject)
        title_layout.addWidget(btn_close)
        card_layout.addWidget(title_bar)

        # 中间内容区
        content_widget = QWidget(self.card)
        content_widget.setAutoFillBackground(True)
        content_widget.setStyleSheet("background-color: #ffffff; border: none;")

        lines = text.strip().split("\n", 1)
        headline = lines[0]
        detail = lines[1].strip() if len(lines) > 1 else ""

        badge = QLabel()
        badge.setFixedSize(46, 46)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.icon_type == self.IconCritical:
            badge.setText("✕")
            badge.setStyleSheet(
                "background-color: #fee2e2; color: #dc2626; font-size: 20px; font-weight: 900; "
                "border-radius: 23px; border: 1px solid #fecaca;"
            )
        elif self.icon_type == self.IconWarning:
            badge.setText("!")
            badge.setStyleSheet(
                "background-color: #fef3c7; color: #d97706; font-size: 22px; font-weight: 900; "
                "border-radius: 23px; border: 1px solid #fde68a;"
            )
        elif self.icon_type == self.IconQuestion:
            badge.setText("?")
            badge.setStyleSheet(
                "background-color: #e0f2fe; color: #0284c7; font-size: 22px; font-weight: 900; "
                "border-radius: 23px; border: 1px solid #bae6fd;"
            )
        else:
            badge.setText("ℹ")
            badge.setStyleSheet(
                "background-color: #e0f2fe; color: #0284c7; font-size: 20px; font-weight: 900; "
                "border-radius: 23px; border: 1px solid #bae6fd;"
            )

        if self.center_align:
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(20, 16, 20, 16)
            content_layout.setSpacing(12)

            badge.setFixedSize(38, 38)
            badge.setStyleSheet(
                badge.styleSheet()
                .replace("border-radius: 23px", "border-radius: 19px")
                .replace("font-size: 22px", "font-size: 18px")
                .replace("font-size: 20px", "font-size: 17px")
            )

            header_row = QHBoxLayout()
            header_row.setContentsMargins(0, 0, 0, 0)
            header_row.setSpacing(12)
            header_row.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)

            lbl_head = QLabel(headline)
            lbl_head.setWordWrap(True)
            lbl_head.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            lbl_head.setStyleSheet(
                "color: #0f172a; font-size: 14px; font-weight: 600; line-height: 1.45; background-color: #ffffff;"
            )
            lbl_head.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            header_row.addWidget(lbl_head, 1)
            content_layout.addLayout(header_row)

            if detail:
                lbl_detail = QLabel(detail)
                lbl_detail.setWordWrap(True)
                lbl_detail.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                lbl_detail.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                lbl_detail.setStyleSheet("""
                    QLabel {
                        background-color: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        color: #334155;
                        font-size: 12.5px;
                        font-family: 'Microsoft YaHei UI', Consolas, sans-serif;
                        line-height: 1.65;
                        padding: 12px 14px;
                    }
                """)
                lbl_detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                content_layout.addWidget(lbl_detail)
        else:
            content_layout = QHBoxLayout(content_widget)
            content_layout.setContentsMargins(20, 18, 20, 16)
            content_layout.setSpacing(16)
            content_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

            right_layout = QVBoxLayout()
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(8)

            lbl_head = QLabel(headline)
            lbl_head.setWordWrap(True)
            lbl_head.setStyleSheet(
                "color: #0f172a; font-size: 14px; font-weight: 600; line-height: 1.4; background-color: #ffffff;"
            )
            lbl_head.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            right_layout.addWidget(lbl_head)

            if detail:
                txt_detail = QPlainTextEdit()
                txt_detail.setReadOnly(True)
                txt_detail.setPlainText(detail)
                txt_detail.setStyleSheet("""
                    QPlainTextEdit {
                        background-color: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 6px;
                        color: #334155;
                        font-size: 12px;
                        font-family: Consolas, 'Courier New', monospace;
                        padding: 8px;
                    }
                """)
                txt_detail.setMaximumHeight(160)
                txt_detail.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                right_layout.addWidget(txt_detail)

            content_layout.addLayout(right_layout, 1)

        card_layout.addWidget(content_widget, 1)

        # 底部按钮栏
        btn_bar = QWidget(self.card)
        btn_bar.setFixedHeight(54)
        btn_bar.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid #f1f5f9;
            }
        """)
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(16, 0, 20, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        for btn_text in self.buttons:
            btn = QPushButton(btn_text)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            is_primary = btn_text in ("确定", "OK", "是", "Yes", "保存", "立即安装")
            if is_primary:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7;
                        color: #ffffff;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: 600;
                        padding: 0 18px;
                    }
                    QPushButton:hover { background-color: #0369a1; }
                    QPushButton:pressed { background-color: #075985; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #475569;
                        border: 1px solid #cbd5e1;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: 500;
                        padding: 0 16px;
                    }
                    QPushButton:hover { background-color: #f1f5f9; color: #0f172a; border-color: #94a3b8; }
                """)
            btn.clicked.connect(lambda checked=False, val=btn_text: self._on_btn_clicked(val))
            btn_layout.addWidget(btn)

        if self.center_align:
            btn_layout.addStretch()

        card_layout.addWidget(btn_bar)
        root_layout.addWidget(self.card)

        self.setMinimumWidth(440)
        self.setMaximumWidth(580)
        self.adjustSize()

    def _on_btn_clicked(self, val: str) -> None:
        self.clicked_button = val
        if val in ("确定", "OK", "是", "Yes", "保存", "立即安装"):
            self.accept()
        else:
            self.reject()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.adjustSize()
        target_rect = None
        active_w = QApplication.activeWindow()
        if active_w and active_w.isVisible() and active_w is not self:
            target_rect = active_w.frameGeometry()
        elif self.parentWidget() and self.parentWidget().isVisible():
            target_rect = self.parentWidget().frameGeometry()
        else:
            screen = QApplication.primaryScreen()
            if screen:
                target_rect = screen.availableGeometry()

        if target_rect:
            self.move(
                target_rect.center().x() - self.width() // 2,
                target_rect.center().y() - self.height() // 2,
            )

        self.raise_()
        self.activateWindow()
        self._apply_native_topmost()

    def _apply_native_topmost(self) -> None:
        _apply_win32_topmost(self)

    @classmethod
    def critical(cls, parent: Optional[QWidget], title: str, text: str) -> None:
        dlg = cls(title=title, text=text, icon_type=cls.IconCritical, buttons=["确定"], parent=parent)
        dlg.exec()

    @classmethod
    def warning(cls, parent: Optional[QWidget], title: str, text: str) -> None:
        dlg = cls(title=title, text=text, icon_type=cls.IconWarning, buttons=["确定"], parent=parent)
        dlg.exec()

    @classmethod
    def information(cls, parent: Optional[QWidget], title: str, text: str) -> None:
        dlg = cls(title=title, text=text, icon_type=cls.IconInformation, buttons=["确定"], parent=parent)
        dlg.exec()

    @classmethod
    def question(
        cls,
        parent: Optional[QWidget],
        title: str,
        text: str,
        buttons: Optional[List[str]] = None,
    ) -> bool:
        if buttons is None:
            buttons = ["确定", "取消"]
        dlg = cls(title=title, text=text, icon_type=cls.IconQuestion, buttons=buttons, parent=parent)
        res = dlg.exec()
        return res == QDialog.DialogCode.Accepted or dlg.clicked_button in ("确定", "是", "Yes")


class ModernInputDialog(QDialog):
    """全中文轻奢圆角置顶输入弹窗"""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "输入内容",
        label: str = "请输入内容:",
        default_text: str = "",
    ) -> None:
        super().__init__(parent)
        self._drag_pos = None
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(title)
        self.setWindowIcon(create_modern_app_icon())

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)

        card = QFrame(self)
        card.setObjectName("ModernInputCard")
        card.setStyleSheet("""
            QFrame#ModernInputCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(15, 23, 42, 50))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        title_bar = QWidget(card)
        title_bar.setFixedHeight(44)
        title_bar.setStyleSheet(
            "background-color: #ffffff; border-top-left-radius: 12px; "
            "border-top-right-radius: 12px; border-bottom: 1px solid #f1f5f9;"
        )
        t_layout = QHBoxLayout(title_bar)
        t_layout.setContentsMargins(16, 0, 12, 0)
        lbl_t = QLabel(f"✏️ {title}")
        lbl_t.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f172a;")
        t_layout.addWidget(lbl_t, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #94a3b8; font-size: 13px; font-weight: bold; } "
            "QPushButton:hover { background: #fee2e2; color: #ef4444; border-radius: 4px; }"
        )
        btn_close.clicked.connect(self.reject)
        t_layout.addWidget(btn_close)
        card_layout.addWidget(title_bar)

        body = QWidget(card)
        body.setStyleSheet("background-color: #ffffff;")
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(20, 18, 20, 18)
        b_layout.setSpacing(10)

        lbl_prompt = QLabel(label)
        lbl_prompt.setStyleSheet("font-size: 13px; color: #334155; font-weight: 500;")
        b_layout.addWidget(lbl_prompt)

        self.edit_input = QLineEdit(default_text)
        self.edit_input.setFixedHeight(36)
        self.edit_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0284c7;
            }
        """)
        self.edit_input.returnPressed.connect(self.accept)
        b_layout.addWidget(self.edit_input)
        card_layout.addWidget(body)

        btn_bar = QWidget(card)
        btn_bar.setFixedHeight(52)
        btn_bar.setStyleSheet(
            "background-color: #f8fafc; border-bottom-left-radius: 12px; "
            "border-bottom-right-radius: 12px; border-top: 1px solid #f1f5f9;"
        )
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(16, 0, 20, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.setFixedHeight(32)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #ffffff; color: #475569; border: 1px solid #cbd5e1; "
            "border-radius: 6px; padding: 0 16px; font-size: 12px; } "
            "QPushButton:hover { background: #f1f5f9; }"
        )
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("确定")
        btn_ok.setFixedHeight(32)
        btn_ok.setStyleSheet(
            "QPushButton { background: #0284c7; color: #ffffff; border: none; "
            "border-radius: 6px; padding: 0 18px; font-size: 12px; font-weight: 600; } "
            "QPushButton:hover { background: #0369a1; }"
        )
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        card_layout.addWidget(btn_bar)

        root_layout.addWidget(card)
        self.setMinimumWidth(400)
        self.adjustSize()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        target_rect = None
        active_w = QApplication.activeWindow()
        if active_w and active_w.isVisible() and active_w is not self:
            target_rect = active_w.frameGeometry()
        elif self.parentWidget() and self.parentWidget().isVisible():
            target_rect = self.parentWidget().frameGeometry()
        else:
            screen = QApplication.primaryScreen()
            if screen:
                target_rect = screen.availableGeometry()

        if target_rect:
            self.move(
                target_rect.center().x() - self.width() // 2,
                target_rect.center().y() - self.height() // 2,
            )
        self.raise_()
        self.activateWindow()
        self._apply_native_topmost()
        self.edit_input.setFocus()

    def _apply_native_topmost(self) -> None:
        _apply_win32_topmost(self)

    @classmethod
    def getText(
        cls,
        parent: Optional[QWidget],
        title: str,
        label: str,
        default_text: str = "",
    ) -> Tuple[str, bool]:
        dlg = cls(parent=parent, title=title, label=label, default_text=default_text)
        res = dlg.exec()
        if res == QDialog.DialogCode.Accepted:
            return dlg.edit_input.text().strip(), True
        return "", False


class ToastNotification(QLabel):
    """无阻塞透明居中悬浮提示条"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #166534;
                font-size: 16px;
                font-weight: 700;
                padding: 10px 24px;
                border: none;
            }
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, message: str, duration_ms: int = 1500) -> None:
        self.setText(message)
        self.adjustSize()
        if self.parentWidget():
            parent_rect = self.parentWidget().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = (parent_rect.height() - self.height()) // 2
            self.move(x, y)
        self.show()
        self.raise_()
        self._timer.start(duration_ms)
