# -*- coding: utf-8 -*-
"""
DOM 组件层级树控件 (DOMTreeWidget) 与局部单词高亮渲染委托 (DOMTreeItemDelegate)：
1. 开启 setUniformRowHeights(True)，将行高测算从 O(N) 降至 O(1)；
2. 锁定水平滚动条防止切节点横向跳动；
3. 支持双击局部单词精准高亮并自动复制到剪贴板，支持 Ctrl+C / Ctrl+F 快捷键。
"""
from typing import Optional, Tuple

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)


def extract_word_bounds(text: str, pos: int) -> Optional[Tuple[int, int, str]]:
    """给定文本与字符索引 pos，提取不含外围分隔符的完整单词区间 (start, end, word)"""
    if not text or pos < 0 or pos >= len(text):
        return None

    delimiters = {" ", "\t", "\r", "\n", "<", ">", "=", '"', "'", "“", "”"}

    if text[pos] in delimiters:
        if pos > 0 and text[pos - 1] not in delimiters:
            pos = pos - 1
        elif pos + 1 < len(text) and text[pos + 1] not in delimiters:
            pos = pos + 1
        else:
            return None

    start = pos
    while start > 0 and text[start - 1] not in delimiters:
        start -= 1

    end = pos + 1
    while end < len(text) and text[end] not in delimiters:
        end += 1

    word = text[start:end]
    if not word.strip():
        return None
    return (start, end, word)


class DOMTreeItemDelegate(QStyledItemDelegate):
    """DOM 树项目渲染委托：保留莫兰迪彩色标签并支持双击局部单词蓝底纯白高亮"""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        widget = option.widget
        if not isinstance(widget, DOMTreeWidget):
            super().paint(painter, option, index)
            return

        item = widget.itemFromIndex(index)
        if widget.selected_word_item != item or not widget.selected_word_range:
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        text_rect = widget.style().subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, widget)
        text_rect = text_rect.adjusted(2, 0, -2, 0)

        opt.state &= ~QStyle.StateFlag.State_Selected
        opt.text = ""
        super().paint(painter, opt, index)

        text = item.text(0)
        start, end = widget.selected_word_range
        if not text or start >= len(text) or end <= start:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = opt.font
        fm = opt.fontMetrics
        orig_color = (
            item.foreground(0).color()
            if item.foreground(0).style() != Qt.BrushStyle.NoBrush
            else opt.palette.text().color()
        )

        prefix_str = text[:start]
        word_str = text[start:end]
        suffix_str = text[end:]

        prefix_w = fm.horizontalAdvance(prefix_str)
        word_w = fm.horizontalAdvance(word_str)

        y_pos = text_rect.top() + (text_rect.height() - fm.height()) // 2 + fm.ascent()
        x_base = text_rect.left()

        painter.setFont(font)
        painter.setPen(orig_color)
        if prefix_str:
            painter.drawText(x_base, y_pos, prefix_str)

        word_bg_rect = QRectF(
            float(x_base + prefix_w),
            float(text_rect.top() + (text_rect.height() - fm.height()) / 2),
            float(word_w),
            float(fm.height()),
        )
        word_bg_path = QPainterPath()
        word_bg_path.addRoundedRect(word_bg_rect.adjusted(-1, 0, 1, 0), 3.0, 3.0)
        painter.fillPath(word_bg_path, QBrush(QColor("#0284c7")))

        bold_font = QFont(font)
        bold_font.setBold(True)
        painter.setFont(bold_font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(x_base + prefix_w, y_pos, word_str)

        painter.setFont(font)
        painter.setPen(orig_color)
        if suffix_str:
            painter.drawText(x_base + prefix_w + word_w, y_pos, suffix_str)

        painter.restore()


class DOMTreeWidget(QTreeWidget):
    """DOM 组件层级树控件：等高行 O(1) 渲染、锁定水平滚动条、支持双击单词复制"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setUniformRowHeights(True)
        self.setAutoScroll(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setIndentation(13)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setExpandsOnDoubleClick(False)

        self.selected_word_item: Optional[QTreeWidgetItem] = None
        self.selected_word_range: Optional[Tuple[int, int]] = None
        self.selected_word_text: str = ""

        self.setItemDelegate(DOMTreeItemDelegate(self))

    def clear(self) -> None:
        self.selected_word_item = None
        self.selected_word_range = None
        self.selected_word_text = ""
        super().clear()

    def scrollTo(self, index, hint=QAbstractItemView.ScrollHint.EnsureVisible) -> None:
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()
        super().scrollTo(index, hint)
        h_bar.setValue(h_val)

    def mousePressEvent(self, event) -> None:
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()

        click_pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        item = self.itemAt(click_pos)

        if self.selected_word_item and self.selected_word_item != item:
            self.selected_word_item = None
            self.selected_word_range = None
            self.selected_word_text = ""
            self.viewport().update()

        super().mousePressEvent(event)
        h_bar.setValue(h_val)

    def mouseDoubleClickEvent(self, event) -> None:
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()

        click_pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        item = self.itemAt(click_pos)

        if item:
            opt = QStyleOptionViewItem()
            self.initViewItemOption(opt)
            opt.rect = self.visualItemRect(item)
            text_rect = self.style().subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, self)

            rel_x = click_pos.x() - text_rect.left()
            text = item.text(0)
            if rel_x >= 0 and text:
                fm = self.fontMetrics()
                curr_x = 0
                hit_pos = len(text) - 1
                for i, ch in enumerate(text):
                    ch_w = fm.horizontalAdvance(ch)
                    if curr_x + ch_w >= rel_x:
                        hit_pos = i
                        break
                    curr_x += ch_w

                bounds = extract_word_bounds(text, hit_pos)
                if bounds:
                    start, end, word = bounds
                    self.selected_word_item = item
                    self.selected_word_range = (start, end)
                    self.selected_word_text = word
                    self.viewport().update()

                    QApplication.clipboard().setText(word)
                    win = self.window()
                    if hasattr(win, "show_toast"):
                        win.show_toast(f"✅ 已复制: {word}", duration_ms=1000)

        super().mouseDoubleClickEvent(event)
        h_bar.setValue(h_val)

    def mouseReleaseEvent(self, event) -> None:
        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()
        super().mouseReleaseEvent(event)
        h_bar.setValue(h_val)

    def keyPressEvent(self, event) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_C:
            if self.selected_word_text:
                QApplication.clipboard().setText(self.selected_word_text)
                win = self.window()
                if hasattr(win, "show_toast"):
                    win.show_toast(f"✅ 已复制: {self.selected_word_text}", duration_ms=1000)
                event.accept()
                return

        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            win = self.window()
            if hasattr(win, "toggle_dom_search"):
                win.toggle_dom_search()
                return

        h_bar = self.horizontalScrollBar()
        h_val = h_bar.value()
        super().keyPressEvent(event)
        h_bar.setValue(h_val)
