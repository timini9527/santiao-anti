# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 通用高级 UI 组件库
=======================================================
提供白金轻奢现代科技风格的专属矢量 UI 控件：
1. RedTrashButton: 高定纯原生矢量红色垃圾桶删除按键 (彻底杜绝系统 Emoji 灰色铁丝网问题)
2. create_red_trash_icon: 矢量红色垃圾桶 QIcon 生成器
"""
import sys
from typing import Optional

from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush,
    QPainterPath, QPixmap, QIcon, QMouseEvent
)


def create_red_trash_icon(size: int = 16, color: str = "#ef4444") -> QIcon:
    """
    生成高精度抗锯齿矢量纯正红色垃圾桶 QIcon。
    """
    scale = 2  # 2x 超采样
    px_size = size * scale
    pixmap = QPixmap(px_size, px_size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    c = QColor(color)
    pen = QPen(c, 1.2 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    brush = QBrush(c)

    w = float(px_size)
    h = float(px_size)

    # 1. 把手
    hw = w * 0.28
    hh = h * 0.10
    hx = (w - hw) / 2.0
    hy = h * 0.12
    h_path = QPainterPath()
    h_path.addRoundedRect(QRectF(hx, hy, hw, hh), 1.0 * scale, 1.0 * scale)
    painter.strokePath(h_path, pen)

    # 2. 盖子
    lw = w * 0.72
    lh = h * 0.08
    lx = (w - lw) / 2.0
    ly = hy + hh + 1.0 * scale
    l_path = QPainterPath()
    l_path.addRoundedRect(QRectF(lx, ly, lw, lh), 1.0 * scale, 1.0 * scale)
    painter.fillPath(l_path, brush)

    # 3. 桶身
    bw_top = w * 0.58
    bw_bot = w * 0.46
    by1 = ly + lh + 1.2 * scale
    by2 = h * 0.88

    b_path = QPainterPath()
    b_path.moveTo(QPointF((w - bw_top) / 2.0, by1))
    b_path.lineTo(QPointF((w + bw_top) / 2.0, by1))
    b_path.lineTo(QPointF((w + bw_bot) / 2.0, by2))
    b_path.lineTo(QPointF((w - bw_bot) / 2.0, by2))
    b_path.closeSubpath()
    painter.strokePath(b_path, pen)

    # 4. 桶身竖条纹
    ly1 = by1 + h * 0.12
    ly2 = by2 - h * 0.12
    sp = w * 0.12
    painter.drawLine(QPointF(w / 2.0 - sp / 2.0, ly1), QPointF(w / 2.0 - sp / 2.0, ly2))
    painter.drawLine(QPointF(w / 2.0 + sp / 2.0, ly1), QPointF(w / 2.0 + sp / 2.0, ly2))

    painter.end()
    return QIcon(pixmap)


class RedTrashButton(QPushButton):
    """
    高定纯原生矢量红色垃圾桶删除按钮：
    1. 彻底摆脱 Windows Segoe UI Emoji 默认灰色铁丝网限制
    2. 无论 16px、22px 还是 30px，高分屏下始终纯正鲜艳、锐利平滑
    3. 支持 Normal/Hover/Pressed 三态柔和交互与高质感淡粉红微光圆角底槽
    """

    def __init__(self, parent: Optional[QWidget] = None, is_circle: bool = True):
        super().__init__(parent)
        self.is_circle = is_circle
        self.is_hovered = False
        self.is_pressed = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = False
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = float(self.width())
        h = float(self.height())
        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)

        # 1. 动态配色状态机
        if self.is_pressed:
            bg_color = QColor("#fecdd3")       # 按下：深粉底
            border_color = QColor("#f87171")   # 按下：鲜红细边
            trash_color = QColor("#b91c1c")    # 按下：暗宝红
        elif self.is_hovered:
            bg_color = QColor("#fee2e2")       # 悬停：柔光淡粉
            border_color = QColor("#fca5a5")   # 悬停：珊瑚粉红边
            trash_color = QColor("#dc2626")    # 悬停：绯红加深
        else:
            bg_color = QColor("#fef2f2")       # 常态：高定轻透极浅粉
            border_color = QColor("#fecdd3")   # 常态：精致极浅边
            trash_color = QColor("#ef4444")    # 常态：鲜明珊瑚红

        # 2. 绘制背景圆角/圆形底槽
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.0))
        if self.is_circle:
            radius = min(w, h) / 2.0 - 1.0
            painter.drawRoundedRect(rect, radius, radius)
        else:
            painter.drawRoundedRect(rect, 6.0, 6.0)

        # 3. 居中绘制高保真红色垃圾桶矢量图标
        # 图标参考尺寸约为按钮自身短边的 50%~55%
        icon_dim = max(10.0, min(w, h) * 0.52)
        cx = w / 2.0
        cy = h / 2.0

        pen_width = max(1.1, icon_dim * 0.08)
        pen = QPen(trash_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        brush = QBrush(trash_color)
        painter.setPen(pen)

        # 3.1 垃圾桶顶盖把手
        hw = icon_dim * 0.32
        hh = icon_dim * 0.12
        hx = cx - hw / 2.0
        hy = cy - icon_dim / 2.0 + 1.0
        h_path = QPainterPath()
        h_path.addRoundedRect(QRectF(hx, hy, hw, hh), 1.0, 1.0)
        painter.strokePath(h_path, pen)

        # 3.2 垃圾桶顶盖横板 (实心填色)
        lw = icon_dim * 0.86
        lh = max(1.5, icon_dim * 0.10)
        lx = cx - lw / 2.0
        ly = hy + hh + 0.8
        l_path = QPainterPath()
        l_path.addRoundedRect(QRectF(lx, ly, lw, lh), 1.0, 1.0)
        painter.fillPath(l_path, brush)

        # 3.3 桶身外轮廓 (微收梯形线框)
        bw_top = icon_dim * 0.70
        bw_bot = icon_dim * 0.56
        by1 = ly + lh + 1.2
        by2 = cy + icon_dim / 2.0 - 0.5

        b_path = QPainterPath()
        b_path.moveTo(QPointF(cx - bw_top / 2.0, by1))
        b_path.lineTo(QPointF(cx + bw_top / 2.0, by1))
        b_path.lineTo(QPointF(cx + bw_bot / 2.0, by2))
        b_path.lineTo(QPointF(cx - bw_bot / 2.0, by2))
        b_path.closeSubpath()
        painter.strokePath(b_path, pen)

        # 3.4 桶身内部 2 条垂直镂空竖肋线
        ly1 = by1 + icon_dim * 0.10
        ly2 = by2 - icon_dim * 0.10
        spacing = icon_dim * 0.18
        painter.drawLine(QPointF(cx - spacing / 2.0, ly1), QPointF(cx - spacing / 2.0, ly2))
        painter.drawLine(QPointF(cx + spacing / 2.0, ly1), QPointF(cx + spacing / 2.0, ly2))
