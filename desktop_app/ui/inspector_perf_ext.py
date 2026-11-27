# -*- coding: utf-8 -*-
"""
=======================================================
UI 审查器 DOM 树与画布渲染性能优化扩展模块
=======================================================
独立承接对 HarmonyAppiumInspector / AppiumScreenView / DOMTreeWidget 的 5 项主线程渲染性能优化：
1. DOM 树单击去重：合并 currentItemChanged 与 itemClicked 重复触发，消除单击一次刷两遍；
2. 画布高分底图预缩放与圆角裁剪缓存：按当前视口尺寸 + DPR 缓存 QPixmap，避免每次切节点重复缩放 1224×2776 原图；
3. 右侧属性表单元格就地复用 + 按需长行测高：垂直表头改用 Interactive + 默认 28px，仅对长文本/换行值单行测高；
4. 面包屑 QSS 与输入框显隐状态缓存：避免同类节点切换时反复重解析样式表与触发布局抖动；
5. DOM 树开启等高行优化：启用 setUniformRowHeights(True)，将行高测算从 O(N) 降至 O(1)。
"""
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

import psutil
from PyQt6.QtCore import QRect, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QHeaderView, QTableWidgetItem, QTreeWidget, QTreeWidgetItem

_PATCHES_INSTALLED: bool = False


def install_inspector_perf_patches() -> None:
    """
    在实例化 HarmonyAppiumInspector 前幂等安装类级渲染与交互性能优化。
    所有优化均在类方法层生效，确保 PyQt6 C++ 虚函数（如 paintEvent）与信号连接 100% 命中优化路径。
    """
    global _PATCHES_INSTALLED
    if _PATCHES_INSTALLED:
        return

    from desktop_app.ui import harmony_native_inspector as mod

    screen_cls = mod.AppiumScreenView
    tree_cls = mod.DOMTreeWidget
    inspector_cls = mod.HarmonyAppiumInspector
    inspector_mode = mod.InspectorMode
    get_dom_tag_color = mod.get_dom_tag_color

    # ------------------------------------------------------------------
    # 1. AppiumScreenView：高分底图预缩放与圆角裁剪缓存
    # ------------------------------------------------------------------
    orig_screen_init = screen_cls.__init__
    orig_clear_screen = screen_cls.clear_screen
    orig_update_pixmap = screen_cls.update_screen_pixmap
    orig_update_image = screen_cls.update_screen_image
    orig_load_screenshot = screen_cls.load_screenshot

    def _screen_init(self: Any, parent: Any = None) -> None:
        orig_screen_init(self, parent)
        self._source_ver = 0
        self._cached_source_ver = -1
        self._cached_draw_size = QSize()
        self._cached_dpr = 1.0
        self._cached_scaled_pixmap: Optional[QPixmap] = None
        self._tag_font = QFont("Consolas", 9, QFont.Weight.Bold)

    def _invalidate_screen_cache(self: Any) -> None:
        """底图变更时递增版本号并释放缩放缓存，确保新帧/新截图即时生效"""
        self._source_ver = getattr(self, "_source_ver", 0) + 1
        self._cached_scaled_pixmap = None

    def _get_cached_rounded_pixmap(self: Any, target_size: QSize) -> Optional[QPixmap]:
        """按当前视口目标尺寸与设备像素比缓存缩放并圆角裁剪后的底图"""
        if target_size.isEmpty():
            return None
        dpr = max(1.0, float(self.devicePixelRatioF()))
        if (
            getattr(self, "_cached_scaled_pixmap", None) is not None
            and getattr(self, "_cached_source_ver", -1) == getattr(self, "_source_ver", 0)
            and getattr(self, "_cached_draw_size", QSize()) == target_size
            and abs(getattr(self, "_cached_dpr", 1.0) - dpr) < 1e-3
        ):
            return self._cached_scaled_pixmap

        phys_w = max(1, int(round(target_size.width() * dpr)))
        phys_h = max(1, int(round(target_size.height() * dpr)))
        cached = QPixmap(phys_w, phys_h)
        cached.setDevicePixelRatio(dpr)
        cached.fill(Qt.GlobalColor.transparent)

        p = QPainter(cached)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        local_rect = QRect(0, 0, target_size.width(), target_size.height())
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(local_rect), 10, 10)
        p.setClipPath(clip_path)
        if self.screen_image and not self.screen_image.isNull():
            p.drawImage(local_rect, self.screen_image)
        elif self.pixmap and not self.pixmap.isNull():
            p.drawPixmap(local_rect, self.pixmap)
        p.end()

        self._cached_scaled_pixmap = cached
        self._cached_source_ver = getattr(self, "_source_ver", 0)
        self._cached_draw_size = QSize(target_size)
        self._cached_dpr = dpr
        return cached

    def _wrapped_clear_screen(self: Any) -> None:
        self._invalidate_screen_cache()
        orig_clear_screen(self)

    def _wrapped_update_pixmap(self: Any, pix: QPixmap, keep_components: bool = True) -> None:
        if pix and not pix.isNull():
            self._invalidate_screen_cache()
        orig_update_pixmap(self, pix, keep_components=keep_components)

    def _wrapped_update_image(self: Any, img: Any, keep_components: bool = True) -> None:
        if img and not img.isNull():
            self._invalidate_screen_cache()
        orig_update_image(self, img, keep_components=keep_components)

    def _wrapped_load_screenshot(
        self: Any,
        img_path: str,
        components: List[Dict[str, Any]],
        layout_size: Optional[Tuple[int, int]] = None,
    ) -> None:
        self._invalidate_screen_cache()
        orig_load_screenshot(self, img_path, components, layout_size=layout_size)

    def _optimized_paint_event(self: Any, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        draw_rect = self.get_draw_rect()
        has_content = (self.screen_image and not self.screen_image.isNull()) or (
            self.pixmap and not self.pixmap.isNull()
        )
        if not has_content or draw_rect.isEmpty():
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(QFont("PingFang SC", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "正在连接移动设备并同步界面布局...")
            return

        # 1. 绘制拟真手机悬浮机身外壳
        phone_shell = draw_rect.adjusted(-6, -6, 6, 6)
        shell_path = QPainterPath()
        shell_path.addRoundedRect(QRectF(phone_shell), 16, 16)
        painter.fillPath(shell_path, QBrush(QColor("#0f172a")))
        painter.setPen(QPen(QColor("#cbd5e1"), 2))
        painter.drawPath(shell_path)

        # 2. 优先直接贴合当前视口尺寸的预缩放圆角缓存底图（单帧 < 1ms）
        cached_pix = self._get_cached_rounded_pixmap(draw_rect.size())
        if cached_pix is not None:
            painter.drawPixmap(draw_rect.topLeft(), cached_pix)
        else:
            screen_path = QPainterPath()
            screen_path.addRoundedRect(QRectF(draw_rect), 10, 10)
            painter.save()
            painter.setClipPath(screen_path)
            if self.screen_image and not self.screen_image.isNull():
                painter.drawImage(draw_rect, self.screen_image)
            elif self.pixmap and not self.pixmap.isNull():
                painter.drawPixmap(draw_rect, self.pixmap)
            painter.restore()

        scale_x = draw_rect.width() / self.layout_w
        scale_y = draw_rect.height() / self.layout_h
        tag_font = getattr(self, "_tag_font", None) or QFont("Consolas", 9, QFont.Weight.Bold)

        # 3. 审查模式交互高亮
        if self.mode == inspector_mode.SELECT:
            if (
                self.hover_node_id
                and self.hover_node_id in self.comp_map
                and self.hover_node_id != self.selected_node_id
            ):
                h_comp = self.comp_map[self.hover_node_id]
                h_scheme = get_dom_tag_color(h_comp.get("type", ""))
                bx = int(draw_rect.x() + h_comp["left"] * scale_x)
                by = int(draw_rect.y() + h_comp["top"] * scale_y)
                bw = max(2, int(h_comp["width"] * scale_x))
                bh = max(2, int(h_comp["height"] * scale_y))

                painter.setPen(QPen(QColor(h_scheme["border"]), 1.8, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(h_scheme["box_bg"]))
                painter.drawRect(bx, by, bw, bh)

                tag_text = f" {h_comp['type']}  {h_comp['width']}×{h_comp['height']} "
                painter.setFont(tag_font)
                fm = painter.fontMetrics()
                tag_w = fm.horizontalAdvance(tag_text) + 8
                tag_h = 20
                tag_y = max(draw_rect.y() + 4, by - tag_h - 2)
                tag_rect = QRect(bx, tag_y, tag_w, tag_h)

                painter.setPen(QPen(QColor(h_scheme["border"]), 1))
                painter.setBrush(QBrush(QColor(h_scheme["bg"])))
                painter.drawRoundedRect(tag_rect, 4, 4)
                painter.setPen(QColor(h_scheme["text"]))
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, tag_text)

            if self.selected_node_id and self.selected_node_id in self.comp_map:
                s_comp = self.comp_map[self.selected_node_id]
                s_scheme = get_dom_tag_color(s_comp.get("type", ""))
                bx = int(draw_rect.x() + s_comp["left"] * scale_x)
                by = int(draw_rect.y() + s_comp["top"] * scale_y)
                bw = max(2, int(s_comp["width"] * scale_x))
                bh = max(2, int(s_comp["height"] * scale_y))

                painter.setPen(QPen(QColor(s_scheme["border"]), 2.2, Qt.PenStyle.SolidLine))
                painter.setBrush(QBrush(s_scheme["box_bg"]))
                painter.drawRect(bx, by, bw, bh)

                s_text = s_comp.get("text", "")
                summary = f" {s_comp['type']}  {s_comp['width']}×{s_comp['height']}"
                if s_text:
                    clean_t = s_text[:14].replace("\n", " ") + ("..." if len(s_text) > 14 else "")
                    summary += f"  {clean_t}"
                summary += " "

                painter.setFont(tag_font)
                fm = painter.fontMetrics()
                tag_w = min(draw_rect.width() - 8, fm.horizontalAdvance(summary) + 10)
                tag_h = 20
                tag_y = max(draw_rect.y() + 4, by - tag_h - 2)
                tag_rect = QRect(bx, tag_y, tag_w, tag_h)

                painter.setPen(QPen(QColor(s_scheme["border"]), 1.2))
                painter.setBrush(QBrush(QColor(s_scheme["bg"])))
                painter.drawRoundedRect(tag_rect, 4, 4)
                painter.setPen(QColor(s_scheme["text"]))
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, summary)

        # 4. 滑动模式下绘制手势轨迹
        if self.mode == inspector_mode.SWIPE and self.is_dragging and self.swipe_start_pos and self.swipe_cur_pos:
            pen_arrow = QPen(QColor("#0284c7"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arrow)
            painter.drawLine(self.swipe_start_pos, self.swipe_cur_pos)
            painter.setBrush(QBrush(QColor("#0284c7")))
            painter.drawEllipse(self.swipe_start_pos, 5, 5)
            painter.drawEllipse(self.swipe_cur_pos, 7, 7)

    screen_cls.__init__ = _screen_init
    screen_cls._invalidate_screen_cache = _invalidate_screen_cache
    screen_cls._get_cached_rounded_pixmap = _get_cached_rounded_pixmap
    screen_cls.clear_screen = _wrapped_clear_screen
    screen_cls.update_screen_pixmap = _wrapped_update_pixmap
    screen_cls.update_screen_image = _wrapped_update_image
    screen_cls.load_screenshot = _wrapped_load_screenshot
    screen_cls.paintEvent = _optimized_paint_event

    # ------------------------------------------------------------------
    # 2. DOMTreeWidget：开启等高行优化（O(N) -> O(1)）
    # ------------------------------------------------------------------
    orig_tree_init = tree_cls.__init__

    def _tree_init(self: Any, parent: Any = None) -> None:
        orig_tree_init(self, parent)
        self.setUniformRowHeights(True)

    tree_cls.__init__ = _tree_init

    # ------------------------------------------------------------------
    # 3. HarmonyAppiumInspector：点击去重 + 属性表单元格复用 + 按需行高/样式缓存
    # ------------------------------------------------------------------
    def _ensure_perf_attrs(self: Any) -> None:
        if not hasattr(self, "_attr_key_bold_font"):
            self._last_panel_sig: Optional[Tuple[str, int, str]] = None
            self._last_breadcrumb_style: str = ""
            self._attr_long_rows: List[int] = []
            self._attr_key_bold_font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            self._attr_key_norm_font = QFont("Segoe UI", 9)
            self._attr_key_hl_color = QColor("#0284c7")
            self._attr_val_hl_color = QColor("#d97706")
            self._attr_key_norm_color = QColor("#64748b")
            self._attr_val_norm_color = QColor("#0f172a")

    def _resize_long_attr_rows(self: Any) -> None:
        """仅对超长/多行属性行按需测高，避免 45+ 短行全表换行排版风暴"""
        if not hasattr(self, "table_attrs"):
            return
        row_count = self.table_attrs.rowCount()
        for row in getattr(self, "_attr_long_rows", []):
            if 0 <= row < row_count:
                self.table_attrs.resizeRowToContents(row)

    def _apply_selected_node(self: Any, node_id: str, force_panel: bool = False) -> None:
        """统一节点选中联动入口：基于 (node_id, comp对象ID, text) 精确去重，避免单击跑两遍"""
        if not node_id:
            return
        _ensure_perf_attrs(self)
        comp = self.comp_map.get(node_id)
        sig = (node_id, id(comp) if comp is not None else 0, str(comp.get("text", "")) if comp else "")
        if not force_panel and node_id == self.canvas.selected_node_id and sig == self._last_panel_sig:
            return

        self.canvas.selected_node_id = node_id
        self.canvas.hover_node_id = ""
        self.canvas.update()
        self.update_selected_element_panel(node_id)

        if hasattr(self, "search_dialog") and self.search_dialog and self.search_dialog.isVisible() and comp:
            self.search_dialog.sync_element_from_main(comp)

    def _optimized_select_element_by_id(self: Any, node_id: str) -> None:
        item = self.tree_item_map.get(node_id)
        if item:
            h_bar = self.tree_widget.horizontalScrollBar()
            h_val = h_bar.value()
            self.tree_widget.blockSignals(True)
            self.tree_widget.setCurrentItem(item)
            self.tree_widget.blockSignals(False)
            self.tree_widget.scrollToItem(item, QTreeWidget.ScrollHint.EnsureVisible)
            h_bar.setValue(h_val)
        self._apply_selected_node(node_id)

    def _optimized_on_tree_item_clicked(self: Any, item: QTreeWidgetItem, column: int) -> None:
        h_bar = self.tree_widget.horizontalScrollBar()
        h_val = h_bar.value()
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self._apply_selected_node(node_id)
        h_bar.setValue(h_val)

    def _optimized_on_tree_item_double_clicked(self: Any, item: QTreeWidgetItem, column: int) -> None:
        if not item:
            return
        h_bar = self.tree_widget.horizontalScrollBar()
        h_val = h_bar.value()
        self.tree_widget.blockSignals(True)
        self.tree_widget.setCurrentItem(item)
        item.setSelected(True)
        self.tree_widget.blockSignals(False)
        h_bar.setValue(h_val)

        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self._apply_selected_node(node_id)

    def _optimized_on_tree_current_item_changed(
        self: Any,
        current: Optional[QTreeWidgetItem],
        previous: Optional[QTreeWidgetItem],
    ) -> None:
        if not current:
            return
        node_id = current.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self._apply_selected_node(node_id)

    def _optimized_update_selected_element_panel(self: Any, node_id: str) -> None:
        """就地复用表格单元格、缓存 QSS/显隐状态并仅对长文本行按需测高"""
        comp = self.comp_map.get(node_id)
        if not comp:
            return
        _ensure_perf_attrs(self)
        self._last_panel_sig = (node_id, id(comp), str(comp.get("text", "")))

        c_type = comp.get("type", "")
        c_text = comp.get("text", "")

        if self.edit_live_input.text() != c_text:
            self.edit_live_input.blockSignals(True)
            self.edit_live_input.setText(c_text)
            self.edit_live_input.blockSignals(False)

        is_input_or_text = (
            c_type in ("TextInput", "TextArea", "Search", "Text", "RichText", "Span", "TextField", "SecureTextField")
            or any(k in c_type.lower() for k in ("input", "edit", "text", "search", "field"))
            or bool(c_text and c_text.strip())
        )
        if self.input_sync_box.isVisible() != is_input_or_text:
            self.input_sync_box.setVisible(is_input_or_text)

        path_str = comp.get("xpath", "Hierarchy").replace("/", "  ›  ")
        scheme = get_dom_tag_color(c_type)
        self.lbl_breadcrumb.setText(f"📍 路径: {path_str}")
        new_bc_style = (
            f"background-color: {scheme['bg']}; color: {scheme['text']}; "
            f"border: 1px solid {scheme['border']}; border-radius: 6px; padding: 4px 8px; font-weight: 600;"
        )
        if new_bc_style != self._last_breadcrumb_style:
            self._last_breadcrumb_style = new_bc_style
            self.lbl_breadcrumb.setStyleSheet(new_bc_style)

        self.txt_loc_id.setText(comp.get("rec_id", ""))
        self.txt_loc_xpath.setText(comp.get("rec_xpath", ""))
        self.txt_loc_py.setText(comp.get("rec_py", ""))
        if hasattr(self, "txt_loc_predicate"):
            self.txt_loc_predicate.setText(comp.get("rec_predicate", ""))
            self.txt_loc_predicate.setCursorPosition(0)
        if hasattr(self, "txt_loc_class_chain"):
            self.txt_loc_class_chain.setText(comp.get("rec_class_chain", ""))
            self.txt_loc_class_chain.setCursorPosition(0)

        self.txt_loc_id.setCursorPosition(0)
        self.txt_loc_xpath.setCursorPosition(0)
        self.txt_loc_py.setCursorPosition(0)

        raw = comp.get("raw") or comp.get("raw_attributes") or {}
        real_id_val = comp.get("id", "")
        dom_path_val = raw.get("dom_path", "")
        if real_id_val:
            id_show = real_id_val
        elif dom_path_val:
            id_show = f"(未显式声明 · 虚拟层级: {dom_path_val})"
        else:
            id_show = "-"

        full_type_val = comp.get("full_type") or comp.get("rec_class") or c_type
        display_attrs = [
            ("原生全类名 (Full Type)", full_type_val),
            ("精炼类型 (Type)", c_type),
            ("id / name / key", id_show),
            ("text / label / value", comp.get("text", "-")),
            ("Predicate (iOS谓词)", comp.get("rec_predicate", "-")),
            ("Class Chain (iOS类链)", comp.get("rec_class_chain", "-")),
            ("bounds (坐标范围)", f"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]"),
            ("size (尺寸宽高)", f"{comp['width']} × {comp['height']}"),
            ("clickable (可点击)", str(raw.get("clickable", "-"))),
            ("enabled (可用状态)", str(raw.get("enabled", "-"))),
            ("focusable (可获焦点)", str(raw.get("focusable", "-"))),
            ("focused (当前聚焦)", str(raw.get("focused", "-"))),
            ("scrollable (可滚动)", str(raw.get("scrollable", "-"))),
            ("visible (可见性)", str(raw.get("visible", "-"))),
            ("xpath (完整绝对路径)", comp.get("xpath", "-")),
        ]

        known_keys = {
            "id", "key", "text", "originalText", "type", "full_type", "bounds",
            "bundleName", "clickable", "enabled", "focusable", "focused", "scrollable", "visible",
        }
        for k, v in raw.items():
            if k not in known_keys:
                display_attrs.append((f"raw: {k}", str(v)))

        hl_keywords = ("Full Type", "Type", "id", "text", "Predicate", "Class Chain", "xpath", "bounds", "size")
        long_rows: List[int] = []
        default_row_h = 28

        self.table_attrs.setUpdatesEnabled(False)
        self.table_attrs.setRowCount(len(display_attrs))
        for row, (k, v) in enumerate(display_attrs):
            k_str = str(k)
            v_str = str(v)

            k_item = self.table_attrs.item(row, 0)
            if k_item is None:
                k_item = QTableWidgetItem(k_str)
                self.table_attrs.setItem(row, 0, k_item)
            elif k_item.text() != k_str:
                k_item.setText(k_str)

            v_item = self.table_attrs.item(row, 1)
            if v_item is None:
                v_item = QTableWidgetItem(v_str)
                self.table_attrs.setItem(row, 1, v_item)
            elif v_item.text() != v_str:
                v_item.setText(v_str)
            v_item.setToolTip(v_str)

            if any(key in k_str for key in hl_keywords):
                k_item.setForeground(self._attr_key_hl_color)
                v_item.setForeground(self._attr_val_hl_color)
                k_item.setFont(self._attr_key_bold_font)
            else:
                k_item.setForeground(self._attr_key_norm_color)
                v_item.setForeground(self._attr_val_norm_color)
                k_item.setFont(self._attr_key_norm_font)

            if len(v_str) > 26 or "\n" in v_str:
                long_rows.append(row)
            else:
                if self.table_attrs.rowHeight(row) != default_row_h:
                    self.table_attrs.setRowHeight(row, default_row_h)

        self._attr_long_rows = long_rows
        for row in long_rows:
            self.table_attrs.resizeRowToContents(row)
        self.table_attrs.setUpdatesEnabled(True)

    inspector_cls._resize_long_attr_rows = _resize_long_attr_rows
    inspector_cls._apply_selected_node = _apply_selected_node
    inspector_cls.select_element_by_id = _optimized_select_element_by_id
    inspector_cls.on_tree_item_clicked = _optimized_on_tree_item_clicked
    inspector_cls.on_tree_item_double_clicked = _optimized_on_tree_item_double_clicked
    inspector_cls.on_tree_current_item_changed = _optimized_on_tree_current_item_changed
    inspector_cls.update_selected_element_panel = _optimized_update_selected_element_panel

    # ------------------------------------------------------------------
    # 4. IosServiceActionWorker：修复 Mac .dmg / Win .exe 打包态点【启动服务】失败
    #    - 打包态 (sys.frozen) 改用内置自举 [sys.executable, "--internal-wda"]，不再依赖外部系统 python3；
    #    - 补齐 --internal-wda 与 relay 8100 进程树回收，避免重启残留与端口占用；
    #    - 将守护进程输出写入系统临时目录日志，失败时提取关键报错返回界面。
    # ------------------------------------------------------------------
    ios_worker_cls = mod.IosServiceActionWorker
    check_ios_wda_services = mod.check_ios_wda_services
    orig_execute_start = ios_worker_cls._execute_start_bat
    orig_execute_stop = ios_worker_cls._execute_stop_bat

    def _wda_log_path() -> str:
        return os.path.join(tempfile.gettempdir(), "santiao_ios_wda.log")

    def _read_wda_failure_hint(log_file: str) -> str:
        """从守护日志尾部提取一条最关键的失败原因，便于在 Mac/Win 打包版界面直接提示"""
        if not os.path.isfile(log_file):
            return ""
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = [ln.strip() for ln in f.readlines()[-25:] if ln.strip()]
            for ln in reversed(lines):
                if any(tag in ln for tag in ("❌", "DTXNsError", "未检测到 USB", "Failed to launch", "ERROR", "异常")):
                    return ln[:140]
            return lines[-1][:140] if lines else ""
        except Exception:
            return ""

    def _patched_execute_stop(self: Any) -> bool:
        """兼容打包态内置 --internal-wda / --internal-tidevice / --internal-pmd3 进程的彻底清理"""
        is_frozen = bool(getattr(sys, "frozen", False))
        if not is_frozen:
            orig_execute_stop(self)

        target_kws = (
            "--internal-wda",
            "start_ios_wda",
            "usbmux forward 8100",
            "relay 8100",
            "developer dvt xcuitest",
            "webdriveragentrunner",
        )
        my_pid = os.getpid()
        for p in psutil.process_iter(["pid", "cmdline"]):
            try:
                if p.info["pid"] == my_pid:
                    continue
                cmdline = " ".join(p.info.get("cmdline") or []).lower()
                if not cmdline:
                    continue
                if any(kw in cmdline for kw in target_kws):
                    try:
                        for child in p.children(recursive=True):
                            if child.pid == my_pid:
                                continue
                            try:
                                child.kill()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        for _ in range(10):
            is_xcuitest, is_forward = check_ios_wda_services()
            if not is_xcuitest and not is_forward:
                break
            time.sleep(0.3)
        return True

    def _patched_execute_start(self: Any) -> bool:
        """打包态优先走内置 [sys.executable, '--internal-wda']，摆脱外部 python3 缺依赖导致的静默秒退"""
        self._last_wda_err = ""
        if not getattr(sys, "frozen", False):
            return orig_execute_start(self)

        log_file = _wda_log_path()
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        work_dir = os.path.dirname(self.start_bat)
        if not os.path.isdir(work_dir):
            work_dir = tempfile.gettempdir()

        log_fp = None
        proc = None
        try:
            try:
                log_fp = open(log_file, "w", encoding="utf-8", errors="replace")
            except Exception:
                log_fp = None

            popen_kwargs: Dict[str, Any] = {
                "stdin": subprocess.DEVNULL,
                "stdout": log_fp if log_fp is not None else subprocess.DEVNULL,
                "stderr": subprocess.STDOUT if log_fp is not None else subprocess.DEVNULL,
                "creationflags": creationflags,
                "cwd": work_dir,
            }
            if sys.platform != "win32":
                popen_kwargs["start_new_session"] = True

            proc = subprocess.Popen([sys.executable, "--internal-wda"], **popen_kwargs)
        except Exception as e:
            self._last_wda_err = str(e)
            if log_fp is not None:
                try:
                    log_fp.close()
                except Exception:
                    pass
            return False
        finally:
            # 父进程关闭自身文件描述符副本，子进程仍持有已继承的句柄继续写日志
            if log_fp is not None:
                try:
                    log_fp.close()
                except Exception:
                    pass

        # 轮询探测双服务是否就绪（若内置守护进程提前异常退出则立即快速失败，避免白等 30 秒）
        stable_ticks = 0
        for _ in range(60):
            time.sleep(0.5)
            is_xcuitest, is_forward = check_ios_wda_services()
            if is_xcuitest and is_forward:
                stable_ticks += 1
                if stable_ticks >= 3:
                    return True
            else:
                stable_ticks = 0
                if proc is not None and proc.poll() is not None:
                    self._last_wda_err = _read_wda_failure_hint(log_file)
                    return False

        self._last_wda_err = _read_wda_failure_hint(log_file)
        return False

    def _patched_worker_run(self: Any) -> None:
        if self.action == "stop":
            self._execute_stop_bat()
            self.finished_sig.emit(True, "服务已停止", "stop")
        else:
            self._execute_stop_bat()
            ok = self._execute_start_bat()
            if ok:
                self.finished_sig.emit(True, "服务已启动", "start_or_restart")
            else:
                hint = getattr(self, "_last_wda_err", "").strip()
                msg = f"服务启动未完全就绪: {hint}" if hint else "服务启动未完全就绪"
                self.finished_sig.emit(False, msg, "start_or_restart")

    ios_worker_cls._execute_stop_bat = _patched_execute_stop
    ios_worker_cls._execute_start_bat = _patched_execute_start
    ios_worker_cls.run = _patched_worker_run

    _PATCHES_INSTALLED = True


def optimize_inspector_instance(inspector: Any) -> None:
    """对已实例化的 HarmonyAppiumInspector 调整属性表行高模式与分隔条联动，完成全部性能优化"""
    if hasattr(inspector, "tree_widget") and inspector.tree_widget is not None:
        inspector.tree_widget.setUniformRowHeights(True)

    if hasattr(inspector, "table_attrs") and inspector.table_attrs is not None:
        v_header = inspector.table_attrs.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        v_header.setDefaultSectionSize(28)
        v_header.setMinimumSectionSize(26)

    if hasattr(inspector, "splitter") and inspector.splitter is not None:
        try:
            inspector.splitter.splitterMoved.disconnect()
        except TypeError:
            pass
        inspector.splitter.splitterMoved.connect(lambda *_: inspector._resize_long_attr_rows())
