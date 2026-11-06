# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 现代白金轻奢主题
=======================================================
与 Web 端 Element Plus 视觉体系 1:1 像素级复刻：
1. 太空银/珍珠白底色 (#f1f5f9) 与纯白高雅毛玻璃卡片 (#ffffff)
2. 皇家典雅睿智蓝 (#2563eb)、极光翡翠绿 (#059669)、焦糖琥珀橙 (#d97706)、胭脂霓虹红 (#e11d48)
3. 细致圆角、精美表单阴影与高对比度极客终端
"""
import os
import sys

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_RESOURCES_DIR = os.path.join(_CURRENT_DIR, "resources")


def _get_or_create_arrow_icons() -> tuple[str, str]:
    """获取或自愈生成下拉箭头高清图标绝对路径 (支持 Windows 正斜杠标准 URL 规范)"""
    os.makedirs(_RESOURCES_DIR, exist_ok=True)
    icon_normal = os.path.join(_RESOURCES_DIR, "chevron_down.png").replace("\\", "/")
    icon_hover = os.path.join(_RESOURCES_DIR, "chevron_down_hover.png").replace("\\", "/")

    # 若资源文件缺失，执行极速自愈生成 (确保打包及各环境下 100% 可用)
    if not (os.path.exists(icon_normal) and os.path.exists(icon_hover)):
        try:
            from PyQt6.QtGui import QImage, QPainter, QPen, QColor, QPainterPath
            from PyQt6.QtCore import Qt, QPointF
            for path, hex_col in [(icon_normal, "#64748b"), (icon_hover, "#2563eb")]:
                img = QImage(32, 32, QImage.Format.Format_ARGB32_Premultiplied)
                img.fill(Qt.GlobalColor.transparent)
                p = QPainter(img)
                p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                pen = QPen(QColor(hex_col))
                pen.setWidthF(3.2)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                p.setPen(pen)
                pth = QPainterPath()
                pth.moveTo(QPointF(9.0, 12.5))
                pth.lineTo(QPointF(16.0, 20.0))
                pth.lineTo(QPointF(23.0, 12.5))
                p.drawPath(pth)
                p.end()
                img.save(path, "PNG")
        except Exception:
            pass

    return icon_normal, icon_hover


_ARROW_ICON, _ARROW_HOVER_ICON = _get_or_create_arrow_icons()

ELEMENT_PLUS_LIGHT_QSS_RAW = """
/* 全局基础设置 */
QWidget {
    background-color: #f1f5f9;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    outline: none;
}

/* ==================== 1. 全球导航 Rail (与 Web 端 1:1) ==================== */
#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
    min-width: 220px;
    max-width: 220px;
}

#sidebarHeader {
    background-color: #ffffff;
    padding: 20px 16px 16px 16px;
    border-bottom: 1px solid #f1f5f9;
}

#brandBadge {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563eb, stop:0.5 #7c3aed, stop:1 #059669);
    color: #ffffff;
    font-size: 14px;
    font-weight: 900;
    border-radius: 8px;
    padding: 4px 10px;
    margin-right: 8px;
    letter-spacing: 1px;
}

#brandTitle {
    font-size: 16px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: 0.5px;
}

#brandSubtitle {
    font-size: 11px;
    color: #64748b;
    margin-top: 4px;
}

/* 侧边栏按钮 */
QPushButton.rail-btn {
    background-color: transparent;
    color: #475569;
    text-align: left;
    padding: 12px 18px;
    border-radius: 8px;
    margin: 3px 12px;
    font-size: 13px;
    font-weight: 500;
    border: none;
}

QPushButton.rail-btn:hover {
    background-color: #f8fafc;
    color: #0f172a;
}

QPushButton.rail-btn:checked {
    background-color: #eff6ff;
    color: #2563eb;
    font-weight: 700;
    border-left: 3px solid #2563eb;
    border-radius: 4px 8px 8px 4px;
}

/* ==================== 2. 卡片与布局容器 ==================== */
QFrame.panel-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}

/* 顶部状态条卡片 */
QFrame.status-header-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 16px;
}

/* 状态药丸 Badge */
QLabel.status-pill-idle {
    background-color: #f1f5f9;
    color: #64748b;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 12px;
}

QLabel.status-pill-running {
    background-color: #eff6ff;
    color: #2563eb;
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 12px;
}

QLabel.status-pill-success {
    background-color: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 12px;
}

QLabel.status-pill-danger {
    background-color: #fef2f2;
    color: #e11d48;
    border: 1px solid #fecdd3;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 12px;
}

/* 视角切换胶囊栏 */
QFrame.segmented-box {
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 2px 4px;
}

/* 表单基础输入与微调框 */
QLineEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}

/* ==================== 2.2 下拉选择框 QComboBox 深度美化 (Element Plus 原生级质感) ==================== */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px 28px 5px 10px;
    color: #0f172a;
    font-size: 13px;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #94a3b8;
}

QComboBox:focus, QComboBox:on {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}

/* 可编辑模式适配：清除内部 QLineEdit 重叠边框并保障文字清晰展示 */
QComboBox:editable {
    background-color: #ffffff;
}

QComboBox:editable QLineEdit {
    background: transparent;
    border: none;
    color: #0f172a;
    padding: 0px 4px;
    font-size: 13px;
}

/* 下拉按钮触发区：高辨识度独立按钮区块，自带精致左分割线与浅灰背景 */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid #e2e8f0;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    background-color: #f8fafc;
}

QComboBox::drop-down:hover {
    background-color: #e2e8f0;
}

QComboBox::drop-down:pressed, QComboBox::drop-down:on {
    background-color: #dbeafe;
}

/* 下拉核心箭头：高清矢量向下 Chevron，悬停/展开时主色蓝高亮反馈 */
QComboBox::down-arrow {
    image: url("__ARROW_ICON__");
    width: 14px;
    height: 14px;
}

QComboBox::down-arrow:hover, QComboBox::down-arrow:on {
    image: url("__ARROW_HOVER_ICON__");
    width: 14px;
    height: 14px;
}

/* 下拉菜单浮层 (Element Plus 浮层卡片设计) */
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    selection-background-color: #eff6ff;
    selection-color: #2563eb;
    color: #0f172a;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 4px 8px;
    border-radius: 4px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #f1f5f9;
    color: #2563eb;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #eff6ff;
    color: #2563eb;
    font-weight: 600;
}

/* ==================== 3. 按钮规范 (Element Plus 体系) ==================== */
QPushButton.btn-primary, QPushButton[class="btn-primary"] {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 18px;
    border: 1px solid #1d4ed8;
}

QPushButton.btn-primary:hover, QPushButton[class="btn-primary"]:hover {
    background-color: #1d4ed8;
}

QPushButton.btn-primary:pressed, QPushButton[class="btn-primary"]:pressed {
    background-color: #1e40af;
}

QPushButton.btn-success, QPushButton[class="btn-success"] {
    background-color: #059669;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 16px;
    border: 1px solid #047857;
}

QPushButton.btn-success:hover, QPushButton[class="btn-success"]:hover {
    background-color: #047857;
}

QPushButton.btn-warning, QPushButton[class="btn-warning"] {
    background-color: #d97706;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 16px;
    border: 1px solid #b45309;
}

QPushButton.btn-warning:hover, QPushButton[class="btn-warning"]:hover {
    background-color: #b45309;
}

QPushButton.btn-danger, QPushButton[class="btn-danger"] {
    background-color: #e11d48;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 18px;
    border: 1px solid #be123c;
}

QPushButton.btn-danger:hover, QPushButton[class="btn-danger"]:hover {
    background-color: #be123c;
}

QPushButton.btn-secondary {
    background-color: #ffffff;
    color: #334155;
    font-weight: 500;
    border-radius: 6px;
    padding: 6px 12px;
    border: 1px solid #cbd5e1;
}

QPushButton.btn-secondary:hover {
    background-color: #f8fafc;
    color: #0f172a;
    border-color: #94a3b8;
}

/* 微型快捷操作按键 */
QPushButton.btn-mini {
    background-color: #f8fafc;
    color: #475569;
    font-size: 11px;
    font-weight: 500;
    border-radius: 4px;
    padding: 3px 8px;
    border: 1px solid #e2e8f0;
}

QPushButton.btn-mini:hover {
    background-color: #eff6ff;
    color: #2563eb;
    border-color: #bfdbfe;
}

/* ==================== 树内操作按钮 (保留空心透明，悬浮统一高亮翡翠绿) ==================== */
QPushButton.tree-pill-btn {
    background-color: transparent;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 11px;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 6px;
    margin: 0px;
    text-align: center;
}
QPushButton.tree-pill-btn:hover {
    background-color: #ecfdf5;
    color: #059669;
    border-color: #a7f3d0;
}
QPushButton.tree-pill-btn:pressed {
    background-color: #d1fae5;
    color: #047857;
    border-color: #6ee7b7;
}

QPushButton.tree-pill-btn-class {
    background-color: transparent;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 11px;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 8px;
    margin: 0px;
    text-align: center;
}
QPushButton.tree-pill-btn-class:hover {
    background-color: #ecfdf5;
    color: #059669;
    border-color: #a7f3d0;
}
QPushButton.tree-pill-btn-class:pressed {
    background-color: #d1fae5;
    color: #047857;
    border-color: #6ee7b7;
}

QPushButton.tree-pill-btn-doc {
    background-color: transparent;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 11px;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 6px;
    margin: 0px;
    text-align: center;
}
QPushButton.tree-pill-btn-doc:hover {
    background-color: #ecfdf5;
    color: #059669;
    border-color: #a7f3d0;
}
QPushButton.tree-pill-btn-doc:pressed {
    background-color: #d1fae5;
    color: #047857;
    border-color: #6ee7b7;
}

QPushButton.tree-pill-btn-file {
    background-color: transparent;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 11px;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 8px;
    margin: 0px;
    text-align: center;
}
QPushButton.tree-pill-btn-file:hover {
    background-color: #ecfdf5;
    color: #059669;
    border-color: #a7f3d0;
}
QPushButton.tree-pill-btn-file:pressed {
    background-color: #d1fae5;
    color: #047857;
    border-color: #6ee7b7;
}

QPushButton.tree-pill-btn-dir {
    background-color: transparent;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 11px;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 8px;
    margin: 0px;
    text-align: center;
}
QPushButton.tree-pill-btn-dir:hover {
    background-color: #ecfdf5;
    color: #059669;
    border-color: #a7f3d0;
}
QPushButton.tree-pill-btn-dir:pressed {
    background-color: #d1fae5;
    color: #047857;
    border-color: #6ee7b7;
}

/* ==================== 4. 树状列表控件 ==================== */
QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
    color: #334155;
}

QTreeWidget::item {
    min-height: 32px;
    height: 34px;
    border-radius: 6px;
    padding-left: 4px;
    padding-right: 4px;
}

QTreeWidget::item:hover {
    background-color: #f8fafc;
    color: #0f172a;
}

QTreeWidget::item:selected {
    background-color: #eff6ff;
    color: #2563eb;
    font-weight: 600;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #64748b;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: 600;
    font-size: 12px;
}

/* ==================== 5. 高性能极客控制台 ==================== */
QPlainTextEdit.console-log {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 12px;
    color: #38bdf8;
    line-height: 1.45;
    padding: 14px;
}

/* 滚动条美化 (精致细条、极简无边框、现代浅灰胶囊配色) */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 24px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::handle:vertical:pressed {
    background: #64748b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    width: 0px;
    background: transparent;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 24px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}
QScrollBar::handle:horizontal:pressed {
    background: #64748b;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    height: 0px;
    background: transparent;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* ==================== 6. 分割器美化 (极窄精致，告别粗厚视觉负担) ==================== */
QSplitter::handle {
    background-color: transparent;
}
QSplitter::handle:horizontal {
    width: 3px;
    background-color: #e2e8f0;
    border-radius: 1px;
}
QSplitter::handle:vertical {
    height: 3px;
    background-color: #e2e8f0;
    border-radius: 1px;
}
QSplitter::handle:hover {
    background-color: #3b82f6;
}
QSplitter::handle:pressed {
    background-color: #1d4ed8;
}
"""

# 动态编译渲染样式表，注入高清矢量箭头图标
ELEMENT_PLUS_LIGHT_QSS = ELEMENT_PLUS_LIGHT_QSS_RAW.replace(
    "__ARROW_ICON__", _ARROW_ICON
).replace(
    "__ARROW_HOVER_ICON__", _ARROW_HOVER_ICON
)

# 保持桌面入口与历史主题名称兼容
LIGHT_LUXURY_QSS = ELEMENT_PLUS_LIGHT_QSS
