# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 品牌轻奢启动画面
=======================================================
提供 1:1 白金轻奢、极速感应的 Native Splash Screen：
1. 居中自适应：严格对齐软件主窗口即将呈现的几何区域黄金正中心
2. 尺寸自适应：根据主窗口记忆尺寸及当前显示器工作区按黄金比例动态缩放
3. 矢量高精度响应式排版：Logo、字号、进度条位置随窗口尺寸全自适应缩放
4. 毫秒级极速响应，并在主界面渲染完成后平滑移交前台焦点
"""
import os
import sys
from typing import Optional

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QFont, QPainterPath, QPixmap, QGuiApplication
)

from desktop_app.config import desktop_config


class AppSplashScreen(QSplashScreen):
    """
    轻量高质感原生启动加载窗口 (支持全自动屏幕与主窗口居中及尺寸自适应)。
    """

    def __init__(self):
        super().__init__()
        # 设置无边框、置顶与半透明底衬支持
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._progress = 10
        self._message = "正在初始化自动化引擎与运行时环境..."
        self._logo_pixmap: Optional[QPixmap] = self._load_logo()
        # 绑定应用专属图标，防止 Windows 任务栏注册默认空占位符
        from PyQt6.QtGui import QIcon
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for ic_name in ["app_icon.ico", "app_icon.png", "sant_logo_hd.png"]:
            for d in [
                os.path.join(base_dir, "desktop_app", "resources"),
                os.path.join(base_dir, "resources"),
                os.path.join(os.path.dirname(__file__), "..", "resources"),
            ]:
                p = os.path.join(d, ic_name)
                if os.path.isfile(p):
                    self.setWindowIcon(QIcon(p))
                    break

        # 核心：自动根据软件窗口目标几何区域计算自适应尺寸并严格居中
        self.auto_fit_and_center()

    def _load_logo(self) -> Optional[QPixmap]:
        """按优先级加载高清品牌 Logo 资源"""
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidates = [
            os.path.join(base_dir, "desktop_app", "resources", "sant_logo_hd.png"),
            os.path.join(base_dir, "desktop_app", "resources", "sant_logo.png"),
            os.path.join(base_dir, "resources", "sant_logo_hd.png"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "sant_logo_hd.png"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "sant_logo.png"),
        ]
        for path in candidates:
            abs_p = os.path.abspath(path)
            if os.path.exists(abs_p):
                pm = QPixmap(abs_p)
                if not pm.isNull():
                    return pm
        return None

    def auto_fit_and_center(self) -> None:
        """
        核心算法：
        1. 读取主窗口记忆配置（位置、宽高、最大化状态）
        2. 定位目标活动屏幕工作区
        3. 依据软件主窗口尺寸按黄金比例自适应计算 Splash 尺寸
        4. 严格将 Loading 窗口对齐至软件主窗口正中心 (水平 + 垂直绝对居中)
        """
        # 1. 获取软件主窗口的目标尺寸与坐标记忆
        cfg_w = int(desktop_config.get("window", "width", 1440))
        cfg_h = int(desktop_config.get("window", "height", 920))
        cfg_x = desktop_config.get("window", "x", None)
        cfg_y = desktop_config.get("window", "y", None)
        is_maximized = bool(desktop_config.get("window", "maximized", False))

        # 2. 定位当前活动的物理显示器
        screens = QGuiApplication.screens()
        primary_screen = QGuiApplication.primaryScreen()
        active_screen = primary_screen

        if screens and cfg_x is not None and cfg_y is not None:
            for s in screens:
                if s.geometry().contains(int(cfg_x), int(cfg_y)):
                    active_screen = s
                    break

        screen_geom = active_screen.availableGeometry() if active_screen else QRect(0, 0, 1920, 1080)

        # 3. 计算软件主窗口的实际目标矩形 (Target Window Geometry)
        if is_maximized:
            target_rect = screen_geom
        else:
            win_w = min(cfg_w, screen_geom.width())
            win_h = min(cfg_h, screen_geom.height())
            if cfg_x is not None and cfg_y is not None:
                win_x = int(cfg_x)
                win_y = int(cfg_y)
                # 校验坐标是否落在屏幕内，避免飞出屏幕
                if not screen_geom.contains(win_x, win_y):
                    win_x = screen_geom.x() + (screen_geom.width() - win_w) // 2
                    win_y = screen_geom.y() + (screen_geom.height() - win_h) // 2
            else:
                win_x = screen_geom.x() + (screen_geom.width() - win_w) // 2
                win_y = screen_geom.y() + (screen_geom.height() - win_h) // 2
            target_rect = QRect(win_x, win_y, win_w, win_h)

        # 4. 依据软件主窗口尺寸自适应计算 Loading 卡片宽高 (黄金视觉占比 36% 左右)
        splash_w = int(target_rect.width() * 0.36)
        splash_w = max(460, min(680, splash_w))
        # 高宽比维持在 0.618 黄金分割比附近
        splash_h = int(splash_w * 0.61)
        splash_h = max(280, min(420, splash_h))

        # 5. 严格将 Loading 窗口对齐至软件主窗口的几何正中心
        center_point = target_rect.center()
        splash_x = center_point.x() - splash_w // 2
        splash_y = center_point.y() - splash_h // 2

        self.setGeometry(splash_x, splash_y, splash_w, splash_h)

    def update_progress(self, value: int, message: str) -> None:
        """更新启动进度百分比与阶段说明信息，并强制刷新界面事件"""
        self._progress = max(0, min(100, value))
        self._message = message
        self.repaint()
        QApplication.processEvents()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        w = float(self.width())
        h = float(self.height())
        radius = max(12.0, min(18.0, h * 0.045))

        # 1. 绘制白金轻奢卡片背景 (纯白 + 1.2px 浅灰精致描边)
        path = QPainterPath()
        path.addRoundedRect(QRectF(1.0, 1.0, w - 2.0, h - 2.0), radius, radius)

        painter.fillPath(path, QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#e2e8f0"), 1.2))
        painter.drawPath(path)

        # 2. 居中绘制 SanT 品牌 Logo (动态按高度自适应缩放)
        logo_size = max(42.0, min(60.0, h * 0.18))
        logo_y = h * 0.11
        logo_x = (w - logo_size) / 2.0
        if self._logo_pixmap and not self._logo_pixmap.isNull():
            painter.drawPixmap(
                QRectF(logo_x, logo_y, logo_size, logo_size).toRect(),
                self._logo_pixmap
            )
        else:
            font_logo = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif", int(logo_size * 0.35))
            font_logo.setWeight(QFont.Weight.Black)
            font_logo.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.6)
            painter.setFont(font_logo)
            painter.setPen(QColor("#0f172a"))
            painter.drawText(QRectF(0, logo_y, w, logo_size * 0.6), Qt.AlignmentFlag.AlignCenter, "SanT")

            dot_r = max(2.8, logo_size * 0.065)
            dot_x = w / 2.0 - dot_r
            dot_y = logo_y - 2.0
            painter.setBrush(QBrush(QColor("#22c55e")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(dot_x, dot_y, dot_r * 2.0, dot_r * 2.0))

        # 3. 动态响应式绘制主标题与副标题
        title_y = logo_y + logo_size + h * 0.04
        title_font_size = max(12, min(16, int(h * 0.048)))
        title_font = QFont("Segoe UI", title_font_size)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#0f172a"))
        title_h = float(title_font_size + 10)
        painter.drawText(QRectF(0, title_y, w, title_h), Qt.AlignmentFlag.AlignCenter, "三条 IM 自动化测试控制台")

        sub_y = title_y + title_h + 2.0
        sub_font_size = max(9, min(11, int(h * 0.032)))
        sub_font = QFont("Segoe UI", sub_font_size)
        painter.setFont(sub_font)
        painter.setPen(QColor("#64748b"))
        sub_h = float(sub_font_size + 8)
        painter.drawText(QRectF(0, sub_y, w, sub_h), Qt.AlignmentFlag.AlignCenter, "全端一体化自动化测试架构平台 · v0.9.9")

        # 4. 绘制底部胶囊进度条底槽与动态翡翠绿进度
        bar_w = w * 0.74
        bar_h = max(3.5, min(5.0, h * 0.015))
        bar_x = (w - bar_w) / 2.0
        bar_y = h * 0.67

        # 底槽
        bg_bar_path = QPainterPath()
        bg_bar_path.addRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), bar_h / 2.0, bar_h / 2.0)
        painter.fillPath(bg_bar_path, QBrush(QColor("#f1f5f9")))

        # 活跃进度 (翡翠绿渐变 #10b981 -> #059669)
        fill_w = max(4.0, bar_w * (self._progress / 100.0))
        fill_bar_path = QPainterPath()
        fill_bar_path.addRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), bar_h / 2.0, bar_h / 2.0)

        grad = QLinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
        grad.setColorAt(0.0, QColor("#34d399"))
        grad.setColorAt(1.0, QColor("#059669"))
        painter.fillPath(fill_bar_path, QBrush(grad))

        # 5. 绘制当前状态阶段提示文本
        msg_y = bar_y + bar_h + 10.0
        msg_font_size = max(8, min(10, int(h * 0.030)))
        msg_font = QFont("Segoe UI", msg_font_size)
        painter.setFont(msg_font)
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(QRectF(0, msg_y, w, float(msg_font_size + 8)), Qt.AlignmentFlag.AlignCenter, self._message)

        # 6. 底部品牌标语
        footer_y = h - 26.0
        footer_font = QFont("Segoe UI", max(7, min(9, int(h * 0.026))))
        painter.setFont(footer_font)
        painter.setPen(QColor("#cbd5e1"))
        painter.drawText(QRectF(0, footer_y, w, 18.0), Qt.AlignmentFlag.AlignCenter, "Santiao IM Quality Engineering · Powered by PyQt6")
