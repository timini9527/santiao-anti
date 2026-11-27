# -*- coding: utf-8 -*-
"""
DOM 树构建与遮挡可见性计算引擎：
1. find_active_dialogs：检测整机是否存在有效几何尺寸的活跃模态弹窗；
2. build_dom_tree_into_widget：递归构建 QTreeWidget 节点、XML ElementTree、平铺组件与三端推荐定位器；
3. apply_occluded_visibility_to_tree：自底向上防连坐可见性保护与根骨架保底。
"""
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from desktop_app.ui.inspector.common.icons import get_dom_tag_color

_ARKUI_CONTAINER_TYPES = frozenset({
    "Row", "Column", "Stack", "Flex", "RelativeContainer", "__Common__",
    "List", "ListItem", "ListItemGroup", "Scroll", "Grid", "GridRow", "GridCol", "GridItem",
    "Swiper", "WaterFlow", "FlowItem", "Refresh", "Navigation", "NavDestination",
    "NavDestinationContent", "NavRouter", "Tabs", "TabContent", "SideBarContainer", "Panel",
    "root", "Component", "Page", "Window", "Stage", "Ability", "Hierarchy", "UIComponent",
    "View", "ViewGroup", "FrameLayout", "LinearLayout", "RelativeLayout",
    "XCUIElementTypeWindow", "XCUIElementTypeOther", "XCUIElementTypeApplication", "Other",
})

_NON_TRANSPARENT_TYPES = frozenset({
    "Text", "Button", "TextInput", "Image", "TextArea", "Toggle", "Checkbox",
    "Radio", "Slider", "Progress", "LoadingProgress", "DatePicker", "TimePicker",
    "TextView", "TextField",
})


def find_active_dialogs(node: Dict[str, Any]) -> bool:
    """检查布局树中是否存在具备真实几何尺寸 (>=100x100) 且非空的活跃模态弹窗"""
    attrs = node.get("attributes", {})
    n_type = attrs.get("type", "")
    vis = str(attrs.get("visible", "true")).lower() != "false"
    if n_type in ("Dialog", "CustomDialog", "ActionSheet", "AlertDialog", "Popup") and vis:
        b_str = attrs.get("bounds", "")
        m_b = re.match(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", b_str)
        if m_b:
            w = int(m_b.group(3)) - int(m_b.group(1))
            h = int(m_b.group(4)) - int(m_b.group(2))
            if w >= 100 and h >= 100 and len(node.get("children", [])) > 0:
                return True
    for ch in node.get("children", []):
        if find_active_dialogs(ch):
            return True
    return False


def _collect_solid_leaf_bounds(node: Dict[str, Any]) -> List[Tuple[int, int, int, int]]:
    """收集节点子树中真正具有视觉/交互实体的叶子边界（穿透纯透明布局容器与 Blank）"""
    res: List[Tuple[int, int, int, int]] = []
    attrs = node.get("attributes", {})
    n_type = attrs.get("type", "")
    try:
        op = float(attrs.get("opacity", "1.0"))
    except Exception:
        op = 1.0
    if op <= 0.05 or str(attrs.get("visible", "true")).lower() == "false":
        return res

    c_list = node.get("children", [])
    if n_type == "Blank":
        return res

    is_trans_container = (
        n_type in ("Row", "Column", "Stack", "Flex", "RelativeContainer", "__Common__", "List", "ListItem", "Scroll", "Grid")
        and len(c_list) > 0
    )
    if not is_trans_container:
        b_str = attrs.get("bounds", "")
        m = re.match(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", b_str)
        if m:
            b_w = int(m.group(3)) - int(m.group(1))
            b_h = int(m.group(4)) - int(m.group(2))
            if b_w > 0 and b_h > 0:
                res.append((int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))))
    else:
        for c in c_list:
            res.extend(_collect_solid_leaf_bounds(c))
    return res


def format_dom_node_label(
    platform: str,
    comp: Dict[str, Any],
    is_full_type: bool = False,
) -> str:
    """生成 DOM 树节点的标准标签文本"""
    full_t = comp.get("full_type") or comp.get("type", "Component")
    short_t = comp.get("type", "Component")
    disp_t = full_t if is_full_type else short_t
    raw_attrs = comp.get("raw") or comp.get("raw_attributes") or {}
    c_id = comp.get("id", "")
    c_text = comp.get("text", "")
    bounds_str = f"[{comp['left']},{comp['top']}][{comp['right']},{comp['bottom']}]"
    is_occluded = comp.get("is_occluded", False)

    attrs_str = ""
    if platform == "ios":
        ios_name = raw_attrs.get("name") or c_id
        ios_label = raw_attrs.get("label") or ""
        ios_value = raw_attrs.get("value") or ""
        if ios_value:
            attrs_str += f' value="{ios_value}"'
        if ios_name:
            attrs_str += f' name="{ios_name}"'
        if ios_label and ios_label != ios_value:
            attrs_str += f' label="{ios_label}"'
    else:
        if c_id:
            attrs_str += f' id="{c_id}"'
        if c_text:
            attrs_str += f' text="{c_text}"'
    attrs_str += f' bounds="{bounds_str}"'
    if is_occluded:
        attrs_str += ' occluded="true"'
    return f"<{disp_t}{attrs_str}>"


def build_dom_tree_into_inspector(
    inspector: Any,
    node: Dict[str, Any],
    parent_item: Optional[QTreeWidgetItem],
    xml_parent: ET.Element,
    current_xpath: str,
    depth: int = 0,
    parent_visible: bool = True,
    is_in_active_page: bool = True,
    screen_w: int = 1084,
    screen_h: int = 2412,
    is_parent_occluded: bool = False,
    has_active_dialog: bool = False,
    is_in_dialog: bool = False,
    covering_rects: Optional[List[Tuple[int, int, int, int]]] = None,
) -> bool:
    """
    递归构建 DOM 树条目、XML 元素树及平铺交互组件列表，并计算几何遮挡与自底向上容器聚合。
    返回当前子树是否至少包含一个实质可见暴露节点。
    """
    platform = inspector.current_platform
    node_id = f"node_{inspector.node_counter}"
    inspector.node_counter += 1

    attrs = node.get("attributes", {})
    bounds_str = attrs.get("bounds", "[0,0][0,0]")
    match = re.match(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", bounds_str)
    left, top, right, bottom = 0, 0, 0, 0
    if match:
        left, top, right, bottom = (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4)),
        )

    width = max(0, right - left)
    height = max(0, bottom - top)
    c_type = attrs.get("type") or ("Hierarchy" if depth == 0 else "Component")
    full_type = attrs.get("full_type") or attrs.get("class") or c_type
    if platform == "ios" and not full_type.startswith("XCUIElementType"):
        full_type = f"XCUIElementType{c_type}"
    elif platform == "android" and "." not in full_type and attrs.get("class"):
        full_type = attrs.get("class")

    c_id = attrs.get("id") or attrs.get("resource-id") or attrs.get("key") or ""
    if platform == "ios" and not c_id:
        c_id = attrs.get("name") or attrs.get("label") or ""
    c_text = attrs.get("text") or attrs.get("label") or attrs.get("originalText") or ""

    # 1. 可见性判定
    raw_visible = str(attrs.get("visible", "")).strip().lower()
    raw_visibility = str(attrs.get("visibility", "")).strip().lower()
    is_hidden_attr = str(attrs.get("hidden", "")).lower() in ("true", "1") or str(attrs.get("isHidden", "")).lower() in ("true", "1")
    is_visibility_hidden = raw_visibility in ("none", "hidden", "2", "1")
    is_explicitly_invisible = raw_visible in ("false", "0") or is_visibility_hidden or is_hidden_attr

    is_visible = not is_explicitly_invisible
    try:
        opacity = float(attrs.get("opacity", attrs.get("alpha", "1.0")))
    except Exception:
        opacity = 1.0

    node_in_active_page = is_in_active_page
    if c_type in ("NavDestination", "NavigationContent"):
        if (width <= 0 and height <= 0) or not is_visible:
            node_in_active_page = False

    ctrl_min = 8 if platform == "ios" else 15
    is_transparent_input = (
        c_type in ("TextInput", "TextArea", "SearchField", "TextField", "TextView", "EditText")
        or full_type in (
            "XCUIElementTypeTextView", "XCUIElementTypeTextField",
            "XCUIElementTypeSecureTextField", "XCUIElementTypeSearchField",
        )
        or c_type.endswith("Input")
        or c_type.endswith("Field")
    ) and is_visible and width >= ctrl_min and height >= ctrl_min

    node_visible = parent_visible and is_visible and (opacity > 0.05 or is_transparent_input)
    if not node_in_active_page:
        node_visible = False

    has_child_nodes = len(node.get("children", [])) > 0
    is_transparent_container = (
        c_type in _ARKUI_CONTAINER_TYPES
        or c_type.lower() in ("root", "component", "page", "window", "stage", "ability", "hierarchy", "uicomponent")
        or c_type.endswith("Container")
        or c_type.endswith("Layout")
        or c_type.endswith("Group")
        or (has_child_nodes and c_type not in _NON_TRANSPARENT_TYPES)
    ) and has_child_nodes

    is_dialog_root = c_type in ("Dialog", "CustomDialog", "ActionSheet", "AlertDialog", "Popup")
    current_is_dialog = is_in_dialog or is_dialog_root
    is_top_level_skeleton = depth <= 1 or c_type in ("Hierarchy", "root", "Component", "Page", "WindowScene", "XCUIElementTypeWindow")

    if is_top_level_skeleton or is_dialog_root:
        is_node_occluded = False
    elif has_active_dialog and not current_is_dialog:
        is_node_occluded = True
    elif is_parent_occluded:
        is_node_occluded = True
    else:
        is_node_occluded = False

    # 2. 实心节点几何遮挡测试
    if not is_node_occluded and not is_transparent_container and covering_rects and width > 0 and height > 0:
        center_x = left + width // 2
        center_y = top + height // 2
        node_area = width * height
        total_inter_area = 0
        for c_l, c_t, c_r, c_b in covering_rects:
            if c_l <= center_x <= c_r and c_t <= center_y <= c_b:
                is_node_occluded = True
                break
            inter_l = max(left, c_l)
            inter_t = max(top, c_t)
            inter_r = min(right, c_r)
            inter_b = min(bottom, c_b)
            if inter_r > inter_l and inter_b > inter_t:
                inter_area = (inter_r - inter_l) * (inter_b - inter_t)
                total_inter_area += inter_area
                if inter_area / node_area >= 0.50:
                    is_node_occluded = True
                    break
        if not is_node_occluded and node_area > 0 and (total_inter_area / node_area >= 0.40):
            is_node_occluded = True

    is_clickable_comp = (
        str(attrs.get("clickable", "false")).lower() in ("true", "1")
        or str(attrs.get("longClickable", "false")).lower() in ("true", "1")
    )
    has_content = bool(c_text or c_id or attrs.get("description") or attrs.get("content-desc") or is_clickable_comp)

    gap_min = 3 if platform == "ios" else 8
    if (width <= gap_min or height <= gap_min) and not has_content and depth > 0:
        is_node_occluded = True

    if c_type == "Image" and not has_content and covering_rects:
        is_node_occluded = True

    is_interactive_form_control = (
        c_type in ("TextView", "TextField", "TextInput", "TextArea", "SearchField", "EditText", "Button")
        or full_type in (
            "XCUIElementTypeTextView", "XCUIElementTypeTextField",
            "XCUIElementTypeSecureTextField", "XCUIElementTypeButton", "XCUIElementTypeSearchField",
        )
        or c_type.endswith("Input")
        or c_type.endswith("Field")
    )
    if is_interactive_form_control and width >= ctrl_min and height >= ctrl_min and is_visible:
        is_node_occluded = False

    is_exposed = node_visible and (not is_node_occluded)
    is_node_exposed = is_exposed and node_in_active_page
    is_occluded_node = (not is_node_exposed) and depth > 0

    if platform == "ios":
        vw = screen_w if screen_w >= 250 else 390
        vh = screen_h if screen_h >= 400 else 844
        plain_min, content_min = 4, 2
    else:
        vw = screen_w if screen_w >= 800 else 1084
        vh = screen_h if screen_h >= 1200 else 2412
        plain_min, content_min = 10, 4
    is_in_viewport = not (right <= 0 or left >= vw or bottom <= 0 or top >= vh)
    is_valid_size = (width >= plain_min and height >= plain_min) if not has_content else (width >= content_min and height >= content_min)
    if is_interactive_form_control and width >= ctrl_min and height >= ctrl_min:
        is_interactive = node_in_active_page and (not is_node_occluded) and is_in_viewport
    else:
        is_interactive = node_in_active_page and is_exposed and is_in_viewport and is_valid_size

    node_xpath = f"{current_xpath}/{c_type}"

    # 3. 平台推荐定位器生成
    rec_id = c_id if c_id else ""
    rec_predicate = ""
    rec_class_chain = ""
    if platform == "android":
        if c_id:
            rec_xpath = f"//*[@resource-id='{c_id}']"
            rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
        elif c_text:
            rec_xpath = f"//{full_type}[@text='{c_text}']"
            rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{full_type}[@text='{c_text}']\")"
        else:
            rec_xpath = node_xpath
            rec_py = f'driver.find_element(AppiumBy.XPATH, "{rec_xpath}")'
        rec_predicate = f'text == "{c_text}"' if c_text else ""
    elif platform == "ios":
        ios_val = attrs.get("value") or ""
        if c_id:
            rec_xpath = f"//{full_type}[@name='{c_id}']"
            rec_predicate = f'type == "{full_type}" AND name == "{c_id}"'
            rec_class_chain = f'**/{full_type}[`name == "{c_id}"`]'
            rec_py = f"driver.find_element(AppiumBy.ACCESSIBILITY_ID, '{c_id}')"
        elif c_text:
            rec_xpath = f"//{full_type}[@label='{c_text}']"
            rec_predicate = f'type == "{full_type}" AND (label == "{c_text}" OR name == "{c_text}")'
            rec_class_chain = f'**/{full_type}[`label == "{c_text}"`]'
            rec_py = f"driver.find_element(AppiumBy.IOS_PREDICATE, '{rec_predicate}')"
        elif ios_val:
            rec_xpath = f"//{full_type}[@value='{ios_val}']"
            rec_predicate = f'type == "{full_type}" AND value == "{ios_val}"'
            rec_class_chain = f'**/{full_type}[`value == "{ios_val}"`]'
            rec_py = f"driver.find_element(AppiumBy.IOS_PREDICATE, '{rec_predicate}')"
        else:
            rec_xpath = f"//{full_type}" if full_type else node_xpath
            rec_predicate = f'type == "{full_type}"'
            rec_class_chain = f"**/{full_type}"
            rec_py = f'driver.find_element(AppiumBy.XPATH, "{rec_xpath}")'
    else:
        if c_id:
            rec_xpath = f"//{c_type}[@id='{c_id}']"
            rec_py = f"driver.find_element(AppiumBy.ID, '{c_id}')"
        elif c_text:
            rec_xpath = f"//{c_type}[@text='{c_text}']"
            rec_py = f"driver.find_element(AppiumBy.XPATH, \"//{c_type}[@text='{c_text}']\")"
        else:
            rec_xpath = node_xpath
            rec_py = f'driver.find_element(AppiumBy.XPATH, "{rec_xpath}")'

    comp: Dict[str, Any] = {
        "node_id": node_id,
        "type": c_type,
        "full_type": full_type,
        "id": c_id,
        "text": c_text,
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": width,
        "height": height,
        "center_x": left + width // 2,
        "center_y": top + height // 2,
        "depth": depth,
        "xpath": node_xpath,
        "rec_xpath": rec_xpath,
        "rec_predicate": rec_predicate,
        "rec_class_chain": rec_class_chain,
        "rec_id": rec_id,
        "rec_py": rec_py,
        "rec_class": full_type,
        "is_visible": is_visible,
        "opacity": opacity,
        "is_occluded": is_node_occluded,
        "is_exposed": is_exposed,
        "is_interactive": is_interactive,
        "is_in_active_page": node_in_active_page,
        "raw_attributes": attrs,
        "raw": attrs,
    }

    if is_interactive:
        inspector.flat_components.append(comp)
    inspector.comp_map[node_id] = comp

    # 4. XML 元素节点构造
    target_tag = full_type if (platform == "ios" or (platform == "android" and "." not in full_type)) else c_type
    safe_tag = re.sub(r"[^a-zA-Z0-9_\-]", "", target_tag) or "Component"
    if safe_tag[0].isdigit() or safe_tag[0] == "-":
        safe_tag = f"comp_{safe_tag}"

    clean_xml_attrs: Dict[str, str] = {
        "node_id": node_id,
        "id": c_id,
        "text": c_text,
        "type": c_type,
        "full_type": full_type,
        "short_type": c_type,
        "bounds": bounds_str,
        "clickable": str(attrs.get("clickable", "")),
        "enabled": str(attrs.get("enabled", "")),
        "occluded": str(is_node_occluded).lower(),
        "exposed": str(is_exposed).lower(),
    }
    for k, v in attrs.items():
        if v is None:
            continue
        k_safe = re.sub(r"[^a-zA-Z0-9_\-]", "", str(k))
        if not k_safe:
            continue
        if k_safe[0].isdigit() or k_safe[0] == "-":
            k_safe = f"attr_{k_safe}"
        clean_xml_attrs.setdefault(k_safe, str(v))

    if c_id:
        clean_xml_attrs.setdefault("resource-id", c_id)
        clean_xml_attrs.setdefault("name", c_id)
    if c_text:
        clean_xml_attrs.setdefault("label", c_text)
        clean_xml_attrs.setdefault("value", c_text)
    desc = attrs.get("description", "") or attrs.get("content-desc", "")
    if desc:
        clean_xml_attrs.setdefault("content-desc", str(desc))
        clean_xml_attrs.setdefault("description", str(desc))

    xml_elem = ET.SubElement(xml_parent, safe_tag, clean_xml_attrs)

    # 5. QTreeWidgetItem 渲染
    is_full_mode = inspector.chk_show_full_type.isChecked() if hasattr(inspector, "chk_show_full_type") else False
    display_type = full_type if is_full_mode else c_type
    type_badge = f"<{display_type}"
    attrs_str = ""
    if platform == "ios":
        ios_name = attrs.get("name") or attrs.get("id") or ""
        ios_label = attrs.get("label") or ""
        ios_value = attrs.get("value") or ""
        if ios_value:
            attrs_str += f' value="{ios_value}"'
        if ios_name:
            attrs_str += f' name="{ios_name}"'
        if ios_label and ios_label != ios_value:
            attrs_str += f' label="{ios_label}"'
    else:
        if c_id:
            attrs_str += f' id="{c_id}"'
        if c_text:
            attrs_str += f' text="{c_text}"'
    attrs_str += f' bounds="{bounds_str}"'
    if is_occluded_node:
        attrs_str += ' occluded="true"'
    attrs_str += ">"

    item = QTreeWidgetItem([f"{type_badge}{attrs_str}"])
    item.setData(0, Qt.ItemDataRole.UserRole, node_id)
    item.setData(0, Qt.ItemDataRole.UserRole + 1, bool(is_occluded_node))
    item.setToolTip(0, f"原生全类名: {full_type}\n精炼类型: {c_type}\n边界范围: {bounds_str}")

    if is_occluded_node:
        item.setForeground(0, QColor("#94a3b8"))
        item.setBackground(0, QBrush(QColor("#f8fafc")))
    else:
        scheme = get_dom_tag_color(c_type)
        item.setForeground(0, QColor(scheme["text"]))
        item.setBackground(0, QBrush(QColor(scheme["bg"])))

    show_occluded = inspector.chk_show_occluded.isChecked() if hasattr(inspector, "chk_show_occluded") else False
    if is_occluded_node and not show_occluded and not has_child_nodes:
        item.setHidden(True)

    inspector.tree_item_map[node_id] = item
    if parent_item:
        parent_item.addChild(item)
    else:
        inspector.tree_widget.addTopLevelItem(item)

    # 6. 子节点递归与 Stack 层叠覆盖计算
    children = node.get("children", [])
    dialog_indices = [
        idx for idx, ch in enumerate(children)
        if ch.get("attributes", {}).get("type") in ("Dialog", "ActionSheet", "CustomDialog", "Popup")
    ]
    modal_occluded_indices = set()
    if dialog_indices:
        min_dlg_idx = min(dialog_indices)
        for prev_i in range(min_dlg_idx):
            modal_occluded_indices.add(prev_i)

    stack_covering_map: Dict[int, List[Tuple[int, int, int, int]]] = {}
    if c_type in ("Stack", "RelativeContainer") and len(children) > 1:
        for i in range(len(children)):
            accumulated_covers: List[Tuple[int, int, int, int]] = []
            for k in range(i + 1, len(children)):
                accumulated_covers.extend(_collect_solid_leaf_bounds(children[k]))
            if accumulated_covers:
                stack_covering_map[i] = accumulated_covers

    effective_parent_item = item if item is not None else parent_item
    has_any_exposed_child = False

    for idx, child in enumerate(children):
        child_covers = list(covering_rects or [])
        if idx in stack_covering_map:
            child_covers.extend(stack_covering_map[idx])
        child_parent_occluded = (idx in modal_occluded_indices) or (is_node_occluded and not is_transparent_container)

        child_has_exposed = build_dom_tree_into_inspector(
            inspector,
            child,
            effective_parent_item,
            xml_elem,
            node_xpath,
            depth=depth + 1,
            parent_visible=node_visible,
            is_in_active_page=node_in_active_page,
            screen_w=screen_w,
            screen_h=screen_h,
            is_parent_occluded=child_parent_occluded,
            has_active_dialog=has_active_dialog,
            is_in_dialog=current_is_dialog,
            covering_rects=child_covers,
        )
        if child_has_exposed:
            has_any_exposed_child = True

    # 7. 自底向上透明容器聚合
    if is_transparent_container:
        if has_any_exposed_child:
            comp["is_occluded"] = False
            comp["is_exposed"] = True
            xml_elem.attrib["occluded"] = "false"
            xml_elem.attrib["exposed"] = "true"
            scheme = get_dom_tag_color(c_type)
            item.setForeground(0, QColor(scheme["text"]))
            item.setBackground(0, QBrush(QColor(scheme["bg"])))
            attrs_str_clean = re.sub(r'\s+occluded="[^"]*"', "", attrs_str)
            if not attrs_str_clean.endswith(">"):
                attrs_str_clean += ">"
            item.setText(0, f"{type_badge}{attrs_str_clean}")
            item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
            item.setHidden(False)
        else:
            comp["is_occluded"] = True
            comp["is_exposed"] = False
            comp["is_interactive"] = False
            xml_elem.attrib["occluded"] = "true"
            xml_elem.attrib["exposed"] = "false"
            item.setForeground(0, QColor("#94a3b8"))
            item.setBackground(0, QBrush(QColor("#f8fafc")))
            base_txt = re.sub(r'\s+occluded="[^"]*"', "", attrs_str)
            if base_txt.endswith(">"):
                base_txt = base_txt[:-1]
            item.setText(0, f'{type_badge}{base_txt} occluded="true">')
            item.setData(0, Qt.ItemDataRole.UserRole + 1, True)
            if comp in inspector.flat_components:
                inspector.flat_components.remove(comp)
            if not show_occluded:
                item.setHidden(True)
        return has_any_exposed_child

    return bool(is_node_exposed)


def apply_occluded_visibility_to_tree(tree_widget: QTreeWidget, show_occluded: bool) -> None:
    """自底向上更新 DOM 树节点可见性：含可见子孙的容器绝不连坐隐藏，顶层骨架永不消失"""

    def update_item_visibility(item: QTreeWidgetItem) -> bool:
        has_visible_child = False
        for i in range(item.childCount()):
            if update_item_visibility(item.child(i)):
                has_visible_child = True

        is_self_occluded = bool(item.data(0, Qt.ItemDataRole.UserRole + 1))
        if show_occluded:
            item.setHidden(False)
            return True
        if has_visible_child:
            item.setHidden(False)
            return True
        if is_self_occluded:
            item.setHidden(True)
            return False
        item.setHidden(False)
        return True

    visible_top_count = 0
    for idx in range(tree_widget.topLevelItemCount()):
        top = tree_widget.topLevelItem(idx)
        if top:
            has_vis = update_item_visibility(top)
            top.setHidden(False)
            if has_vis:
                visible_top_count += 1

    if not show_occluded and visible_top_count == 0 and tree_widget.topLevelItemCount() > 0:
        for idx in range(tree_widget.topLevelItemCount()):
            top = tree_widget.topLevelItem(idx)
            if top:
                top.setHidden(False)
                for c_idx in range(top.childCount()):
                    top.child(c_idx).setHidden(False)
