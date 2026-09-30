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

ELEMENT_PLUS_LIGHT_QSS = """
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

/* 表单输入与下拉 */
QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    selection-background-color: #eff6ff;
    selection-color: #2563eb;
    color: #0f172a;
    padding: 4px;
    border-radius: 6px;
}

/* ==================== 3. 按钮规范 (Element Plus 体系) ==================== */
QPushButton.btn-primary {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 18px;
    border: 1px solid #1d4ed8;
}

QPushButton.btn-primary:hover {
    background-color: #1d4ed8;
}

QPushButton.btn-primary:pressed {
    background-color: #1e40af;
}

QPushButton.btn-success {
    background-color: #059669;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 16px;
    border: 1px solid #047857;
}

QPushButton.btn-success:hover {
    background-color: #047857;
}

QPushButton.btn-warning {
    background-color: #d97706;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 16px;
    border: 1px solid #b45309;
}

QPushButton.btn-warning:hover {
    background-color: #b45309;
}

QPushButton.btn-danger {
    background-color: #e11d48;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 18px;
    border: 1px solid #be123c;
}

QPushButton.btn-danger:hover {
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

/* ==================== 树内操作按钮 (1:1 像素级复刻 Element Plus 胶囊药丸风格) ==================== */
QPushButton.tree-pill-btn {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 11px;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 6px;
    margin: 0px;
    text-align: center;
}
QPushButton.tree-pill-btn:hover {
    background-color: #eff6ff;
    color: #2563eb;
    border-color: #bfdbfe;
}
QPushButton.tree-pill-btn:pressed {
    background-color: #dbeafe;
    color: #1d4ed8;
    border-color: #93c5fd;
}

QPushButton.tree-pill-btn-class {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 11px;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 8px;
    margin: 0px;
    text-align: center;
}
QPushButton.tree-pill-btn-class:hover {
    background-color: #fffbeb;
    color: #d97706;
    border-color: #fde68a;
}

QPushButton.tree-pill-btn-file {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #e2e8f0;
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

QPushButton.tree-pill-btn-dir {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 11px;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 8px;
    margin: 0px;
    text-align: center;
}
QPushButton.tree-pill-btn-dir:hover {
    background-color: #fefce8;
    color: #ca8a04;
    border-color: #fef08a;
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

/* 滚动条美化 */
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
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ==================== 6. 分割器美化 (Splitter Handle) ==================== */
QSplitter::handle {
    background-color: #f1f5f9;
}
QSplitter::handle:horizontal {
    width: 6px;
}
QSplitter::handle:vertical {
    height: 7px;
}
QSplitter::handle:hover {
    background-color: #93c5fd;
}
QSplitter::handle:pressed {
    background-color: #3b82f6;
}
"""

# 保持桌面入口与历史主题名称兼容
LIGHT_LUXURY_QSS = ELEMENT_PLUS_LIGHT_QSS
