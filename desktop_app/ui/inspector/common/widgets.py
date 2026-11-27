# -*- coding: utf-8 -*-
"""
UI 审查器通用基础控件：
1. ButtonSpinner：按钮 Loading 转圈动画控制器；
2. FlowLayout：自适应折行流式布局；
3. AutoResizingTextEdit：随内容自动调高的纯文本选择器输入框；
4. AutoWrapStatusLabel：不撑宽父容器的自适应换行状态标签；
5. DeviceComboBox：基于 QMenu 的零残影设备下拉选择框。
"""
from typing import List, Optional

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QLayout,
    QMenu,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QWidget,
)

from desktop_app.ui.inspector.common.icons import get_tech_icon


class ButtonSpinner:
    """通用按钮 Loading 转圈控制器，任务结束后自动恢复原图标与原文字"""

    def __init__(self, button: QPushButton, orig_icon_name: str = "refresh", icon_color: str = "#0284c7") -> None:
        self.button = button
        self.orig_icon_name = orig_icon_name
        self.icon_color = icon_color
        self.loading_icon_name = "spinner"
        self.angle = 0
        self.timer = QTimer(button)
        self.timer.timeout.connect(self._on_tick)
        self._orig_text = button.text()

    def start(self, loading_text: Optional[str] = None) -> None:
        self._orig_text = self.button.text()
        if loading_text is not None:
            self.button.setText(loading_text)
        self.angle = 0
        self.button.setIcon(get_tech_icon(self.loading_icon_name, self.icon_color, rotation=0.0))
        self.timer.start(35)

    def _on_tick(self) -> None:
        self.angle = (self.angle + 30) % 360
        self.button.setIcon(get_tech_icon(self.loading_icon_name, self.icon_color, rotation=self.angle))

    def stop(self, restore_text: bool = True) -> None:
        self.timer.stop()
        if restore_text and self._orig_text:
            self.button.setText(self._orig_text)
        self.button.setIcon(get_tech_icon(self.orig_icon_name, self.icon_color, rotation=0.0))
        self.button.setEnabled(True)


class FlowLayout(QLayout):
    """自适应流式换行布局：宽屏单行排布，窄屏自动折行，支持单行末尾控件右对齐"""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        margin: int = 0,
        h_spacing: int = 8,
        v_spacing: int = 6,
    ) -> None:
        super().__init__(parent)
        self._items: List = []
        self._h_space = h_spacing
        self._v_space = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self) -> None:
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item) -> None:
        self._items.append(item)

    def addWidgetRight(self, widget: QWidget) -> None:
        """添加标记为靠右对齐的控件（单行时推至行尾最右侧，折行后正常顺排）"""
        widget.setProperty("_flow_align_right", True)
        self.addWidget(widget)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        total_w = 0
        max_h = 0
        visible_count = 0
        for item in self._items:
            wid = item.widget()
            if wid is not None and wid.isHidden():
                continue
            hint = item.sizeHint()
            total_w += hint.width()
            max_h = max(max_h, hint.height())
            visible_count += 1
        if visible_count > 1:
            total_w += self._h_space * (visible_count - 1)
        m = self.contentsMargins()
        return QSize(total_w + m.left() + m.right(), max_h + m.top() + m.bottom())

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            wid = item.widget()
            if wid is not None and wid.isHidden():
                continue
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0
        row_items: List = []

        def _flush_row(items_in_row: List, row_y: int, row_h: int) -> None:
            if test_only or not items_in_row:
                return
            right_indices = [
                i for i, (it, _, _) in enumerate(items_in_row)
                if it.widget() is not None and bool(it.widget().property("_flow_align_right"))
            ]
            if right_indices and right_indices[0] > 0:
                split_idx = right_indices[0]
                right_chunk = items_in_row[split_idx:]
                right_total_w = sum(h.width() for _, _, h in right_chunk) + self._h_space * (len(right_chunk) - 1)
                _, prev_x, prev_h = items_in_row[split_idx - 1]
                left_end = prev_x + prev_h.width() + self._h_space
                target_start = effective.right() + 1 - right_total_w
                if target_start > left_end:
                    cur_rx = target_start
                    for i in range(split_idx, len(items_in_row)):
                        it, _, h = items_in_row[i]
                        items_in_row[i] = (it, cur_rx, h)
                        cur_rx += h.width() + self._h_space

            for r_item, r_x, r_hint in items_in_row:
                offset_y = max(0, (row_h - r_hint.height()) // 2)
                r_item.setGeometry(QRect(QPoint(r_x, row_y + offset_y), r_hint))

        for item in self._items:
            wid = item.widget()
            if wid is not None and wid.isHidden():
                continue
            hint = item.sizeHint()
            next_x = x + hint.width() + self._h_space
            if next_x - self._h_space > effective.right() + 1 and line_height > 0:
                _flush_row(row_items, y, line_height)
                row_items = []
                x = effective.x()
                y = y + line_height + self._v_space
                next_x = x + hint.width() + self._h_space
                line_height = 0

            row_items.append((item, x, hint))
            x = next_x
            line_height = max(line_height, hint.height())

        _flush_row(row_items, y, line_height)
        total_h = y + line_height - rect.y() + m.bottom() + 2
        if not test_only:
            p = self.parentWidget()
            if p is not None and p.objectName() == "topBar" and p.minimumHeight() != total_h:
                p.setMinimumHeight(total_h)
        return total_h


class AutoResizingTextEdit(QTextEdit):
    """自适应内容高度的多行纯文本选择器输入框，兼容 QLineEdit 常用接口"""

    returnPressed = pyqtSignal()

    def __init__(self, min_height: int = 54, max_height: int = 180, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.min_height = min_height
        self.max_height = max_height
        self.setAcceptRichText(False)

        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        doc = self.document()
        doc.setDocumentMargin(4)

        self.textChanged.connect(self.adjust_height)
        self.setFixedHeight(self.min_height)

    def text(self) -> str:
        return self.toPlainText()

    def setText(self, text: str) -> None:
        self.setPlainText(text or "")
        self.adjust_height()

    def setCursorPosition(self, pos: int) -> None:
        cursor = self.textCursor()
        cursor.setPosition(min(max(0, pos), len(self.toPlainText())))
        self.setTextCursor(cursor)

    def cursorPosition(self) -> int:
        return self.textCursor().position()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.returnPressed.emit()
                event.accept()
                return
        super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.adjust_height()

    def adjust_height(self) -> None:
        vw = self.viewport().width()
        if vw <= 0:
            vw = max(300, self.width() - 16)
        doc = self.document()
        doc.setTextWidth(float(vw))
        doc_height = doc.size().height()
        target_height = int(doc_height + 14)
        target_height = max(self.min_height, min(target_height, self.max_height))
        if self.height() != target_height:
            self.setFixedHeight(target_height)


class AutoWrapStatusLabel(QLabel):
    """自适应内容换行的状态标签，避免单行长文本撑宽父窗口"""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self) -> QSize:
        w = self.width() if self.width() > 50 else 300
        h = self.heightForWidth(w)
        return QSize(w, max(24, h))


class DeviceComboBox(QComboBox):
    """基于一次性 QMenu 的零残影设备选择下拉框，消除 Windows DWM 透明幽灵方框"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._active_menu: Optional[QMenu] = None
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def showPopup(self) -> None:
        self.hidePopup()
        if self.count() <= 0:
            return

        menu = QMenu(self)
        self._active_menu = menu
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        menu.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        menu.setMinimumWidth(self.width())
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                padding: 4px;
                font-family: 'Segoe UI', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
                background-color: #ffffff;
                color: #0f172a;
            }
            QMenu::item:selected {
                background-color: #e0f2fe;
                color: #0284c7;
                font-weight: 600;
            }
        """)

        actions_map = {}
        curr_idx = self.currentIndex()
        for i in range(self.count()):
            act = menu.addAction(self.itemText(i))
            if i == curr_idx:
                font = act.font()
                font.setBold(True)
                act.setFont(font)
            actions_map[act] = i

        popup_pos = self.mapToGlobal(QPoint(0, self.height() + 2))
        chosen_act = menu.exec(popup_pos)
        self.hidePopup()

        if chosen_act is not None and chosen_act in actions_map:
            target_idx = actions_map[chosen_act]
            if target_idx != self.currentIndex():
                QTimer.singleShot(0, lambda idx=target_idx: self.setCurrentIndex(idx))

    def hidePopup(self) -> None:
        if self._active_menu is not None:
            try:
                self._active_menu.hide()
                self._active_menu.close()
                self._active_menu.deleteLater()
            except Exception:
                pass
            self._active_menu = None
        super().hidePopup()
