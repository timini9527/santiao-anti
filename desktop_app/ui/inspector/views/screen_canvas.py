# -*- coding: utf-8 -*-
"""
真机屏幕映射视窗 (AppiumScreenView) 与交互模式枚举 (InspectorMode)：
1. 高分底图按视口尺寸 + DPR 预缩放圆角缓存（避免切节点重绘重复缩放 1224×2776 原图，单帧 < 1ms）；
2. 鸿蒙 ArkUI <Web> / <rootWebArea> / 大型 <genericContainer> 容器透传与小驼峰内部控件识别；
3. 悬停虚线框 + 选中实线框 + 滑动手势轨迹绘制。
"""
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import QPoint, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QSizePolicy, QWidget

from desktop_app.ui.inspector.common.icons import get_dom_tag_color

_WEB_INNER_CONTENT_TYPES = frozenset({
    "staticText", "image", "labelText", "button", "link",
    "textField", "searchBox", "checkBox", "radioButton", "heading",
})


class InspectorMode:
    """审查器左栏画布交互模式"""

    SELECT = "select"  # 审查选择模式
    TAP = "tap"        # 坐标点击模式
    SWIPE = "swipe"    # 坐标滑动模式


class AppiumScreenView(QWidget):
    """真机屏幕映射视窗，支持高分底图预缩放圆角缓存与三端精准拾取"""

    element_selected = pyqtSignal(str)
    coordinate_tapped = pyqtSignal(int, int)
    coordinate_swiped = pyqtSignal(int, int, int, int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.mode = InspectorMode.SELECT
        self.pixmap: Optional[QPixmap] = None
        self.screen_image: Optional[QImage] = None
        self.flat_components: List[Dict[str, Any]] = []
        self.comp_map: Dict[str, Dict[str, Any]] = {}
        self.hover_node_id: str = ""
        self.selected_node_id: str = ""
        self.orig_w = 1084
        self.orig_h = 2412
        self.layout_w = 1084
        self.layout_h = 2412

        # 拖拽滑动状态
        self.is_dragging = False
        self.swipe_start_pos: Optional[QPoint] = None
        self.swipe_cur_pos: Optional[QPoint] = None

        # 底图圆角预缩放缓存状态
        self._source_ver: int = 0
        self._cached_source_ver: int = -1
        self._cached_draw_size: QSize = QSize()
        self._cached_dpr: float = 1.0
        self._cached_scaled_pixmap: Optional[QPixmap] = None
        self._tag_font = QFont("Consolas", 9, QFont.Weight.Bold)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: transparent;")

    def _invalidate_screen_cache(self) -> None:
        """底图变更时递增版本号并释放缩放缓存"""
        self._source_ver += 1
        self._cached_scaled_pixmap = None

    def _get_cached_rounded_pixmap(self, target_size: QSize) -> Optional[QPixmap]:
        """按当前视口尺寸与 DPR 缓存缩放并圆角裁剪后的底图"""
        if target_size.isEmpty():
            return None
        dpr = max(1.0, float(self.devicePixelRatioF()))
        if (
            self._cached_scaled_pixmap is not None
            and self._cached_source_ver == self._source_ver
            and self._cached_draw_size == target_size
            and abs(self._cached_dpr - dpr) < 1e-3
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
        self._cached_source_ver = self._source_ver
        self._cached_draw_size = QSize(target_size)
        self._cached_dpr = dpr
        return cached

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        if mode == InspectorMode.SELECT:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif mode == InspectorMode.TAP:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == InspectorMode.SWIPE:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.update()

    def clear_screen(self) -> None:
        """清空当前屏幕图像与组件映射，杜绝切换设备残影"""
        self._invalidate_screen_cache()
        self.pixmap = None
        self.screen_image = None
        self.flat_components.clear()
        self.comp_map.clear()
        self.hover_node_id = ""
        self.selected_node_id = ""
        self.update()

    def update_screen_pixmap(self, pix: QPixmap, keep_components: bool = True) -> None:
        if not pix or pix.isNull():
            return
        self._invalidate_screen_cache()
        self.pixmap = pix
        self.screen_image = None
        self.orig_w = pix.width()
        self.orig_h = pix.height()
        if self.layout_w <= 0 or self.layout_h <= 0:
            self.layout_w = self.orig_w
            self.layout_h = self.orig_h
        if not keep_components:
            self.hover_node_id = ""
            self.selected_node_id = ""
        self.update()

    def update_screen_image(self, img: QImage, keep_components: bool = True) -> None:
        if not img or img.isNull():
            return
        self._invalidate_screen_cache()
        self.screen_image = img
        self.orig_w = img.width()
        self.orig_h = img.height()
        if self.layout_w <= 0 or self.layout_h <= 0:
            self.layout_w = self.orig_w
            self.layout_h = self.orig_h
        if not keep_components:
            self.hover_node_id = ""
            self.selected_node_id = ""
        self.update()

    def update_components_only(
        self,
        components: List[Dict[str, Any]],
        layout_size: Optional[Tuple[int, int]] = None,
    ) -> None:
        self.flat_components = components
        self.comp_map = {c["node_id"]: c for c in components}
        self.hover_node_id = ""
        if self.selected_node_id not in self.comp_map:
            self.selected_node_id = ""
        if layout_size and layout_size[0] > 0 and layout_size[1] > 0:
            self.layout_w, self.layout_h = int(layout_size[0]), int(layout_size[1])
        else:
            max_r = max((c.get("right", 0) for c in components if c.get("right", 0) > 0), default=0)
            max_b = max((c.get("bottom", 0) for c in components if c.get("bottom", 0) > 0), default=0)
            if max_r >= 800 and max_b >= 1200:
                self.layout_w = max_r
                self.layout_h = max_b
        self.update()

    def load_screenshot(
        self,
        img_path: str,
        components: List[Dict[str, Any]],
        layout_size: Optional[Tuple[int, int]] = None,
    ) -> None:
        self._invalidate_screen_cache()
        self.screen_image = None
        self.pixmap = QPixmap(img_path)
        if not self.pixmap.isNull():
            self.orig_w = self.pixmap.width()
            self.orig_h = self.pixmap.height()
        else:
            self.orig_w = 1084
            self.orig_h = 2412

        self.flat_components = components
        self.comp_map = {c["node_id"]: c for c in components}
        self.hover_node_id = ""
        if self.selected_node_id not in self.comp_map:
            self.selected_node_id = ""

        if layout_size and layout_size[0] > 0 and layout_size[1] > 0:
            self.layout_w, self.layout_h = int(layout_size[0]), int(layout_size[1])
            self.update()
            return

        max_r = max((c.get("right", 0) for c in components if c.get("right", 0) > 0), default=0)
        max_b = max((c.get("bottom", 0) for c in components if c.get("bottom", 0) > 0), default=0)

        if max_r > 0 and max_b > 0 and max_r > self.orig_w * 1.25:
            self.layout_w = max_r
            self.layout_h = max_b
        elif self.orig_w > 0 and self.orig_h > 0:
            is_ios_points = (
                max_r > 0
                and max_b > 0
                and max_r <= self.orig_w * 0.75
                and max_b <= self.orig_h * 0.75
            )
            if is_ios_points:
                self.layout_w = max_r
                self.layout_h = max_b
            else:
                self.layout_w = self.orig_w
                self.layout_h = self.orig_h
        elif max_r > 0 and max_b > 0:
            self.layout_w = max_r
            self.layout_h = max_b
        else:
            self.layout_w = 1084
            self.layout_h = 2412

        self.update()

    def get_draw_rect(self) -> QRect:
        img_size = None
        if self.screen_image and not self.screen_image.isNull():
            img_size = self.screen_image.size()
        elif self.pixmap and not self.pixmap.isNull():
            img_size = self.pixmap.size()

        if not img_size or img_size.isEmpty():
            return QRect()
        avail_w = max(50, self.width() - 24)
        avail_h = max(50, self.height() - 24)
        target_size = img_size.scaled(QSize(avail_w, avail_h), Qt.AspectRatioMode.KeepAspectRatio)
        x = (self.width() - target_size.width()) // 2
        y = (self.height() - target_size.height()) // 2
        return QRect(x, y, target_size.width(), target_size.height())

    @staticmethod
    def is_content_component(comp: Dict[str, Any]) -> bool:
        """
        判断组件是否为具体有效内容或交互元素（含鸿蒙 <Web> 容器透传与小驼峰 Web 内部标签识别）。
        """
        if comp.get("is_interactive") is False:
            return False
        w = int(comp.get("width", 0) or 0)
        h = int(comp.get("height", 0) or 0)
        if w <= 3 or h <= 3:
            return False

        c_type = str(comp.get("type", "") or "")
        # 全屏/大尺寸 <Web>、<rootWebArea> 与大 <genericContainer> 视为容器，避免拦截网页内部节点拾取
        if c_type in ("Web", "rootWebArea"):
            return False
        if c_type == "genericContainer" and (w >= 600 or h >= 600):
            return False
        if c_type in _WEB_INNER_CONTENT_TYPES:
            return True

        c_text = (comp.get("text") or "").strip()
        c_id = (comp.get("id") or "").strip()
        raw = comp.get("raw_attributes", {})

        if c_text:
            return True

        content_types = {
            "Text", "Span", "StaticText", "TextClock", "Marquee", "Badge", "Divider",
            "SymbolGlyph", "Image", "Icon", "QRCode", "ImageView", "Video", "XComponent", "Canvas",
            "Button", "Toggle", "Checkbox", "Radio", "Switch", "ImageButton", "Slider", "Rating", "LoadingProgress",
            "TextInput", "TextArea", "Search", "SearchField", "RichEditor", "RichEditorContent",
            "TextField", "TextView", "EditText",
            "Select", "MenuItem", "Menu", "DatePicker", "TimePicker", "TextPicker",
            "XCUIElementTypeButton", "XCUIElementTypeImage", "XCUIElementTypeStaticText",
            "XCUIElementTypeTextField", "XCUIElementTypeSecureTextField", "XCUIElementTypeTextView",
            "XCUIElementTypeSearchField", "XCUIElementTypeIcon", "XCUIElementTypeLink", "XCUIElementTypeCell",
        }
        full_t = comp.get("full_type", "")
        if c_type in content_types or full_t in content_types or c_type.endswith("Input") or c_type.endswith("Field"):
            return True

        container_types = {
            "Hierarchy", "root", "WindowScene", "Stack", "Navigation", "NavigationContent",
            "NavDestination", "NavDestinationContent", "Column", "Row", "List", "ListItem",
            "Refresh", "Scroll", "RelativeContainer", "Flex", "Grid", "GridItem", "Swiper",
            "__Common__", "ViewGroup", "FrameLayout", "LinearLayout", "RelativeLayout",
            "XCUIElementTypeWindow", "XCUIElementTypeOther", "XCUIElementTypeScrollView",
        }
        if c_id and c_type not in container_types:
            return True

        clickable = raw.get("clickable") in ("true", True, "True")
        if clickable and w < 600 and h < 260 and c_type not in container_types:
            return True

        return False

    def find_component_at(self, dev_x: int, dev_y: int, for_hover: bool = False) -> str:
        """在设备坐标处精准拾取最内层有效组件"""
        matched = []
        for comp in self.flat_components:
            if comp.get("is_occluded", False) or not comp.get("is_exposed", True):
                continue
            if comp["left"] <= dev_x <= comp["right"] and comp["top"] <= dev_y <= comp["bottom"]:
                if comp["width"] > 0 and comp["height"] > 0:
                    matched.append(comp)

        if not matched:
            return ""

        content_matches = [c for c in matched if self.is_content_component(c)]
        if for_hover:
            if not content_matches:
                return ""
            candidates = content_matches
        else:
            candidates = content_matches if content_matches else matched

        candidates.sort(
            key=lambda c: (
                0 if self.is_content_component(c) else 1,
                c["width"] * c["height"],
                -c.get("depth", 0),
            )
        )
        return candidates[0]["node_id"]

    def paintEvent(self, event) -> None:
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

        # 1. 拟真手机悬浮机身外壳
        phone_shell = draw_rect.adjusted(-6, -6, 6, 6)
        shell_path = QPainterPath()
        shell_path.addRoundedRect(QRectF(phone_shell), 16, 16)
        painter.fillPath(shell_path, QBrush(QColor("#0f172a")))
        painter.setPen(QPen(QColor("#cbd5e1"), 2))
        painter.drawPath(shell_path)

        # 2. 直接绘制当前视口尺寸的预缩放圆角缓存底图
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

        scale_x = draw_rect.width() / max(1, self.layout_w)
        scale_y = draw_rect.height() / max(1, self.layout_h)

        # 3. 审查模式交互高亮
        if self.mode == InspectorMode.SELECT:
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
                painter.setFont(self._tag_font)
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

                painter.setFont(self._tag_font)
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

        # 4. 滑动手势轨迹
        if self.mode == InspectorMode.SWIPE and self.is_dragging and self.swipe_start_pos and self.swipe_cur_pos:
            pen_arrow = QPen(QColor("#0284c7"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arrow)
            painter.drawLine(self.swipe_start_pos, self.swipe_cur_pos)
            painter.setBrush(QBrush(QColor("#0284c7")))
            painter.drawEllipse(self.swipe_start_pos, 5, 5)
            painter.drawEllipse(self.swipe_cur_pos, 7, 7)

    def mouseMoveEvent(self, event) -> None:
        draw_rect = self.get_draw_rect()
        if draw_rect.isEmpty() or not draw_rect.contains(event.pos()):
            if self.hover_node_id:
                self.hover_node_id = ""
                self.update()
            return

        if self.mode == InspectorMode.SWIPE and self.is_dragging:
            self.swipe_cur_pos = event.pos()
            self.update()
            return

        if self.mode == InspectorMode.SELECT:
            scale_x = draw_rect.width() / max(1, self.layout_w)
            scale_y = draw_rect.height() / max(1, self.layout_h)
            dev_x = int((event.pos().x() - draw_rect.x()) / scale_x)
            dev_y = int((event.pos().y() - draw_rect.y()) / scale_y)

            hit_id = self.find_component_at(dev_x, dev_y, for_hover=True)
            if hit_id != self.hover_node_id:
                self.hover_node_id = hit_id
                self.update()

    def mousePressEvent(self, event) -> None:
        draw_rect = self.get_draw_rect()
        if draw_rect.isEmpty() or not draw_rect.contains(event.pos()):
            return

        scale_x = draw_rect.width() / max(1, self.layout_w)
        scale_y = draw_rect.height() / max(1, self.layout_h)
        dev_x = int((event.pos().x() - draw_rect.x()) / scale_x)
        dev_y = int((event.pos().y() - draw_rect.y()) / scale_y)

        if self.mode == InspectorMode.SELECT:
            if event.button() == Qt.MouseButton.LeftButton:
                target_id = self.find_component_at(dev_x, dev_y, for_hover=False)
                if target_id:
                    self.selected_node_id = target_id
                    self.hover_node_id = ""
                    self.update()
                    self.element_selected.emit(self.selected_node_id)
        elif self.mode == InspectorMode.TAP:
            if event.button() == Qt.MouseButton.LeftButton:
                self.coordinate_tapped.emit(dev_x, dev_y)
        elif self.mode == InspectorMode.SWIPE:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = True
                self.swipe_start_pos = event.pos()
                self.swipe_cur_pos = event.pos()
                self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self.mode == InspectorMode.SWIPE and self.is_dragging:
            self.is_dragging = False
            draw_rect = self.get_draw_rect()
            if self.swipe_start_pos and self.swipe_cur_pos and not draw_rect.isEmpty():
                scale_x = draw_rect.width() / max(1, self.layout_w)
                scale_y = draw_rect.height() / max(1, self.layout_h)
                x1 = int((self.swipe_start_pos.x() - draw_rect.x()) / scale_x)
                y1 = int((self.swipe_start_pos.y() - draw_rect.y()) / scale_y)
                x2 = int((self.swipe_cur_pos.x() - draw_rect.x()) / scale_x)
                y2 = int((self.swipe_cur_pos.y() - draw_rect.y()) / scale_y)
                self.swipe_start_pos = None
                self.swipe_cur_pos = None
                self.update()
                self.coordinate_swiped.emit(x1, y1, x2, y2)
