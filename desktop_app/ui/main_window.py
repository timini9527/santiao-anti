# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 主窗口
=======================================================
1:1 像素级复刻图 2 高定纯白侧边栏导航：
1. 宽度 68px，高雅纯白底色 #ffffff，右侧边缘 1px solid #e2e8f0 精致浅灰分割线
2. 顶部图 2 品牌 Logo：艺术字 SanT + 字母 a 正上方鲜翠灵动翡翠绿呼吸光球 (● #22c55e)
3. 5 大高级科技线框矢量按键 (未激活冷灰石板色、悬停微灰、激活浅天蓝柔光底)
4. 右上角精确贴合的微型彩色胶囊 Badge (Core 蓝、UI 天蓝、IM 翡翠绿、Grid 极客紫、Allure 琥珀金)
5. 底部白底高质感浅灰边框状态药丸 (● 8000)
"""
import os
import sys
from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QLineF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient,
    QFont, QPainterPath, QMouseEvent, QPixmap, QIcon
)

from ..config import desktop_config
from .mobile_page import MobilePage
from .web_page import WebPage
from .api_page import ApiPage
from .devices_page import DevicesPage
from .reports_page import ReportsPage

class BrandLogoWidget(QWidget):
    """
    1:1 精确呈现图 2 品牌 Logo：
    1. 艺术品牌字 SanT (S大写、a小写、n小写、T大写)，高定曜石墨黑 #0f172a
    2. 字母 a 正上方悬浮一颗鲜明灵动的翡翠绿呼吸光球 (● #22c55e)
    3. 支持高保真无损 Pixmap 绘制，并在缺失时支持纯原生 QPainter 矢量抗锯齿平滑兜底
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(68, 48)
        self.pixmap = None
        self._load_logo()

    def _load_logo(self):
        # 探测内置提取的高保真图 2 Logo 图片 (兼容源码运行与 PyInstaller 打包环境)
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidates = [
            os.path.join(base_dir, "desktop_app", "resources", "sant_logo_hd.png"),
            os.path.join(base_dir, "desktop_app", "resources", "sant_logo.png"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "sant_logo_hd.png"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "sant_logo.png"),
            os.path.join(os.path.dirname(__file__), "..", "logo_crop.png"),
        ]
        for path in candidates:
            abs_p = os.path.abspath(path)
            if os.path.exists(abs_p):
                pm = QPixmap(abs_p)
                if not pm.isNull():
                    self.pixmap = pm
                    break

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        w = float(self.width())
        h = float(self.height())

        # 1. 优先使用提取的高保真无损图 2 样式
        if self.pixmap and not self.pixmap.isNull():
            # 居中等比绘制图 2 Logo，呈现极简轻奢质感
            target_size = 38.0
            x = (w - target_size) / 2.0
            y = (h - target_size) / 2.0 + 1.0
            target_rect = QRectF(x, y, target_size, target_size)
            painter.drawPixmap(target_rect.toRect(), self.pixmap)
            return

        # 2. 兜底高精度矢量自绘图 2：SanT + 字母 a 顶部翡翠绿呼吸光球
        font = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif", 13)
        font.setWeight(QFont.Weight.Black)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.6)
        painter.setFont(font)
        painter.setPen(QColor("#0f172a"))

        # 居中绘制艺术字 SanT
        text = "SanT"
        text_rect = QRectF(0, 14.0, w, 22.0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

        # 绘制字母 a 顶部的翡翠绿灵动光球
        dot_x = w / 2.0 - 2.8
        dot_y = 12.0
        dot_r = 3.2

        rad_grad = QRadialGradient(dot_x - 0.8, dot_y - 0.8, dot_r)
        rad_grad.setColorAt(0.0, QColor("#4ade80"))
        rad_grad.setColorAt(0.7, QColor("#22c55e"))
        rad_grad.setColorAt(1.0, QColor("#16a34a"))

        painter.setBrush(QBrush(rad_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(dot_x, dot_y), dot_r, dot_r)


class HighEndNavButton(QWidget):
    """
    1:1 纯原生 QPainter 矢量自绘科技导航按键 (白底高定版)：
    精致矢量线框 + 悬浮贴合微型胶囊 Badge，完美适配纯白底色
    """
    clicked = pyqtSignal(int)

    def __init__(self, index: int, icon_type: str, title: str, tag: str, parent=None):
        super().__init__(parent)
        self.index = index
        self.icon_type = icon_type  # 'core', 'ui', 'im', 'grid', 'allure'
        self.title = title
        self.tag = tag
        self.is_active = False
        self.is_hovered = False

        self.setFixedSize(58, 68 if index in (2, 3, 4) else 58)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, active: bool):
        if self.is_active != active:
            self.is_active = active
            self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        w = float(self.width())
        h = float(self.height())
        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)

        # 1. 绘制背景与外边框 (白底专属高定配色)
        if self.is_active:
            # 激活态：浅天蓝柔光底色 + 精致科技蓝描边
            painter.setBrush(QColor("#eff6ff"))
            painter.setPen(QPen(QColor("#bfdbfe"), 1.2))
            painter.drawRoundedRect(rect, 10.0, 10.0)
        elif self.is_hovered:
            # 悬停态：浅淡高级冷灰
            painter.setBrush(QColor("#f1f5f9"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 10.0, 10.0)
        else:
            # 未激活态：通透白底无背景
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(Qt.PenStyle.NoPen)

        # 2. 确定主题色 (白底专属)
        if self.is_active:
            main_color = QColor("#2563eb")   # 皇家科技亮蓝
            text_color = QColor("#2563eb")
        elif self.is_hovered:
            main_color = QColor("#1e293b")   # 悬停深石板色
            text_color = QColor("#1e293b")
        else:
            main_color = QColor("#64748b")   # 未激活高雅冷灰
            text_color = QColor("#64748b")

        # 3. 绘制上方高精密矢量线框图标 (中心位于 cx, cy_icon)
        cx = w / 2.0
        cy_icon = 24.0 if self.index in (2, 3, 4) else 20.0
        icon_pen = QPen(main_color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(icon_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        self._draw_vector_icon(painter, cx, cy_icon, main_color)

        # 4. 绘制右上角微型药丸胶囊 Badge
        self._draw_badge(painter, cx, cy_icon)

        # 5. 绘制下方中文标题
        font_text = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif", 8)
        font_text.setWeight(QFont.Weight.Bold if self.is_active else QFont.Weight.DemiBold)
        painter.setFont(font_text)
        painter.setPen(text_color)
        text_y = 42.0 if self.index in (2, 3, 4) else 36.0
        text_rect = QRectF(0, text_y, w, 18.0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.title)

    def _draw_vector_icon(self, painter: QPainter, cx: float, cy: float, color: QColor):
        """绘制 5 大高级科技线框矢量图标"""
        t = self.icon_type

        if t == "core":
            # 移动 IM：纤细圆角手机外框 + 听筒横线 + 底部圆点
            phone_rect = QRectF(cx - 6.5, cy - 9.5, 13.0, 19.0)
            painter.drawRoundedRect(phone_rect, 2.2, 2.2)
            # 听筒横线
            painter.drawLine(QPointF(cx - 2.5, cy - 7.0), QPointF(cx + 2.5, cy - 7.0))
            # 底部 Home 点
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(cx, cy + 6.5), 0.9, 0.9)
            painter.setBrush(Qt.BrushStyle.NoBrush)

        elif t == "ui":
            # Web 测试：现代显示器外框 (激活态屏幕内部带半透明微光) + 支架底座
            screen_rect = QRectF(cx - 9.5, cy - 9.0, 19.0, 13.0)
            if self.is_active:
                painter.setBrush(QColor(37, 99, 235, 24))
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(screen_rect, 1.8, 1.8)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # 底座立柱与底板横线
            painter.drawLine(QPointF(cx, cy + 4.0), QPointF(cx, cy + 7.5))
            painter.drawLine(QPointF(cx - 4.5, cy + 7.5), QPointF(cx + 4.5, cy + 7.5))

        elif t == "im":
            # 接口压测：两个交错穿插扣合的圆角胶囊链条环
            # 左环
            left_rect = QRectF(cx - 7.5, cy - 6.0, 9.5, 7.0)
            painter.drawRoundedRect(left_rect, 2.5, 2.5)
            # 右环
            right_rect = QRectF(cx - 1.5, cy - 2.0, 9.5, 7.0)
            painter.drawRoundedRect(right_rect, 2.5, 2.5)

        elif t == "grid":
            # 设备矩阵：精密正方形芯片主体 + 四周 8 根微型金属引脚
            chip_rect = QRectF(cx - 5.5, cy - 5.5, 11.0, 11.0)
            painter.drawRoundedRect(chip_rect, 2.0, 2.0)

            # 上引脚
            painter.drawLine(QPointF(cx - 2.5, cy - 8.5), QPointF(cx - 2.5, cy - 5.5))
            painter.drawLine(QPointF(cx + 2.5, cy - 8.5), QPointF(cx + 2.5, cy - 5.5))
            # 下引脚
            painter.drawLine(QPointF(cx - 2.5, cy + 5.5), QPointF(cx - 2.5, cy + 8.5))
            painter.drawLine(QPointF(cx + 2.5, cy + 5.5), QPointF(cx + 2.5, cy + 8.5))
            # 左引脚
            painter.drawLine(QPointF(cx - 8.5, cy - 2.5), QPointF(cx - 5.5, cy - 2.5))
            painter.drawLine(QPointF(cx - 8.5, cy + 2.5), QPointF(cx - 5.5, cy + 2.5))
            # 右引脚
            painter.drawLine(QPointF(cx + 5.5, cy - 2.5), QPointF(cx + 8.5, cy - 2.5))
            painter.drawLine(QPointF(cx + 5.5, cy + 2.5), QPointF(cx + 8.5, cy + 2.5))

        elif t == "allure":
            # 报告中心：数据展板三脚架 (展板外框 + 内部柱状数据线 + 三脚架)
            board_rect = QRectF(cx - 7.5, cy - 8.5, 15.0, 10.5)
            painter.drawRoundedRect(board_rect, 1.5, 1.5)

            # 内部柱状线条 (低、中、高)
            painter.drawLine(QPointF(cx - 4.0, cy - 0.5), QPointF(cx - 4.0, cy - 3.0))
            painter.drawLine(QPointF(cx, cy - 0.5), QPointF(cx, cy - 5.0))
            painter.drawLine(QPointF(cx + 4.0, cy - 0.5), QPointF(cx + 4.0, cy - 7.0))

            # 下方支架
            painter.drawLine(QPointF(cx, cy + 2.0), QPointF(cx, cy + 4.0))
            painter.drawLine(QPointF(cx, cy + 4.0), QPointF(cx - 4.5, cy + 8.5))
            painter.drawLine(QPointF(cx, cy + 4.0), QPointF(cx + 4.5, cy + 8.5))

    def _draw_badge(self, painter: QPainter, cx: float, cy: float):
        """精准贴合在图标右上角的彩色微型胶囊 Badge (白底高清晰版)"""
        tag_text = self.tag
        tag_lower = tag_text.lower()

        # 根据 tag 赋予辨识度极佳的科技点缀色
        if tag_lower == "core":
            bg_color = QColor("#2563eb")     # 皇家科技蓝
            badge_w = 21.0
        elif tag_lower == "ui":
            bg_color = QColor("#0284c7")     # 亮天蓝
            badge_w = 14.0
        elif tag_lower == "im":
            bg_color = QColor("#059669")     # 翡翠绿
            badge_w = 15.0
        elif tag_lower == "grid":
            bg_color = QColor("#7c3aed")     # 极客紫
            badge_w = 20.0
        else:
            bg_color = QColor("#d97706")     # 琥珀金
            badge_w = 23.0

        badge_h = 10.5
        badge_x = cx + 3.0
        badge_y = cy - 12.0
        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(badge_rect, 3.2, 3.2)

        # 徽标纯白文字
        font_badge = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", 6)
        font_badge.setBold(True)
        painter.setFont(font_badge)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, tag_text)


class ModernSidebar(QFrame):
    """
    纯白高定奢华侧边栏导航：
    1. 纯白底色 #ffffff，右侧边缘 1px solid #e2e8f0 精致分割线
    2. 顶部图 2 品牌 Logo (SanT 艺术字 + 字母 a 顶部翡翠绿呼吸光球)
    3. 5 大高定线框按键 (未激活冷灰石板色、悬停微灰、激活浅天蓝柔光底)
    4. 底部精致浅灰边框端口胶囊 (● 8000)
    """
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(68)
        self.setObjectName("modernSidebar")
        self.current_index = 0
        self.items: List[HighEndNavButton] = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 14, 0, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # 1. 顶部品牌标识：全面升级为图 2 样式 (SanT 艺术字 + 翡翠绿光球)
        self.brand_logo = BrandLogoWidget(self)
        layout.addWidget(self.brand_logo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(4)

        # 2. 导航按键组 (严格对齐：移动 IM, Web 测试, 接口压测, 设备矩阵, 报告中心)
        nav_defs = [
            {"title": "移动 IM", "tag": "Core", "icon": "core", "index": 0},
            {"title": "Web 测试", "tag": "UI", "icon": "ui", "index": 1},
            {"title": "接口压测", "tag": "IM", "icon": "im", "index": 2},
            {"title": "设备矩阵", "tag": "Grid", "icon": "grid", "index": 3},
            {"title": "报告中心", "tag": "Allure", "icon": "allure", "index": 4},
        ]

        for item in nav_defs:
            if item["index"] in (3, 4):
                layout.addSpacing(4)
            btn = HighEndNavButton(item["index"], item["icon"], item["title"], item["tag"])
            btn.clicked.connect(self._on_item_clicked)
            if item["index"] == 0:
                btn.set_active(True)
            self.items.append(btn)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        # 3. 底部状态指示药丸 (白底专属精致胶囊 ● 8000)
        footer_pill = QFrame()
        footer_pill.setFixedSize(54, 22)
        footer_pill.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 11px;
            }
            QFrame:hover {
                background: #f1f5f9;
                border-color: #cbd5e1;
            }
        """)
        f_layout = QHBoxLayout(footer_pill)
        f_layout.setContentsMargins(6, 0, 6, 0)
        f_layout.setSpacing(4)
        f_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dot = QLabel("●")
        dot.setStyleSheet("color: #10b981; font-size: 9px;")
        f_layout.addWidget(dot)

        port_lbl = QLabel("8000")
        port_lbl.setStyleSheet("color: #475569; font-size: 10px; font-weight: 700; font-family: monospace;")
        f_layout.addWidget(port_lbl)

        layout.addWidget(footer_pill, alignment=Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        # 绘制纯白底色与右边缘极细浅灰分割线
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = float(self.width())
        h = float(self.height())

        # 纯净白底背景
        painter.fillRect(QRectF(0, 0, w, h), QColor("#ffffff"))

        # 右边缘极细浅灰分割线
        painter.setPen(QPen(QColor("#e2e8f0"), 1.0))
        painter.drawLine(QPointF(w - 1.0, 0), QPointF(w - 1.0, h))

    def _on_item_clicked(self, index: int):
        self.current_index = index
        for item in self.items:
            item.set_active(item.index == index)
        self.page_changed.emit(index)


class MainWindow(QMainWindow):
    """原生 Windows 独立桌面端主窗体"""

    def __init__(self):
        super().__init__()
        # 优化主窗口标题：简洁大气、专业高端
        self.setWindowTitle("三条 IM 自动化测试控制台")

        # 绑定专属高清品牌窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(
            desktop_config.get("window", "width", 1440),
            desktop_config.get("window", "height", 920)
        )
        if desktop_config.get("window", "maximized", False):
            self.showMaximized()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. 纯白高雅主侧边栏导航 (严格对齐图 2 与白色底色)
        self.sidebar = ModernSidebar(self)
        self.sidebar.page_changed.connect(self._switch_page)
        root_layout.addWidget(self.sidebar)

        # 2. 右侧主体工作区 (Platform Workspace)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #f1f5f9;")

        self.page_mobile = MobilePage()
        self.page_web = WebPage()
        self.page_api = ApiPage()
        self.page_devices = DevicesPage()
        self.page_reports = ReportsPage()

        self.stacked_widget.addWidget(self.page_mobile)   # index 0
        self.stacked_widget.addWidget(self.page_web)      # index 1
        self.stacked_widget.addWidget(self.page_api)      # index 2
        self.stacked_widget.addWidget(self.page_devices)  # index 3
        self.stacked_widget.addWidget(self.page_reports)  # index 4

        root_layout.addWidget(self.stacked_widget, stretch=1)

    def _switch_page(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        if index == 3 and hasattr(self.page_devices, "refresh_devices"):
            self.page_devices.refresh_devices()
        elif index == 4 and hasattr(self.page_reports, "refresh_reports"):
            self.page_reports.refresh_reports()

    def closeEvent(self, event):
        desktop_config.set("window", "width", self.width())
        desktop_config.set("window", "height", self.height())
        desktop_config.set("window", "maximized", self.isMaximized())
        super().closeEvent(event)
