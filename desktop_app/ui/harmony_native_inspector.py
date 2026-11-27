# -*- coding: utf-8 -*-
"""
================================================================================
Santiao Mobile Inspector - 移动端全平台 UI 审查器兼容门面入口
================================================================================
原 12,341 行单体实现已按【功能分层 + 三端平台隔离】重构至 desktop_app/ui/inspector/：
- common/    : 图标引擎、配色、轻奢置顶弹窗与通用控件
- locator/   : XPath、iOS Predicate/ClassChain、鸿蒙 HypiumBy/HosBy 解析与校验
- platforms/ : HarmonyOS / Android / iOS 独立底层通信、抓取、WebView 自愈与服务管理
- layout/    : 跨端布局解析调度与 DOM 树遮挡聚合构建器
- workers/   : 实时投屏线程 (ScreenCastWorker) 与异步抓取线程 (CaptureWorker)
- views/     : 真机画布、DOM 树视图、元素查找器浮窗与审查器主窗口

本文件保留所有历史公共符号导出与独立运行入口，确保外部调用方 100% 零破坏兼容。
"""
import logging
import sys

# 静默 hmnextauto 冗余日志流
for _name in ("hmnextauto", "hmnextauto.hdc", "hmnextauto._client"):
    _lg = logging.getLogger(_name)
    _lg.setLevel(logging.WARNING)
    for _h in _lg.handlers:
        if hasattr(_h, "setStream"):
            _h.setStream(sys.stdout)

from desktop_app.ui.inspector.common.dialogs import (
    ModernInputDialog,
    ModernMessageBox,
    ToastNotification,
)
from desktop_app.ui.inspector.common.icons import (
    LOCAL_ICON_DIR,
    create_modern_app_icon,
    get_dom_tag_color,
    get_tech_icon,
    import_network_icon,
)
from desktop_app.ui.inspector.common.widgets import (
    AutoResizingTextEdit,
    AutoWrapStatusLabel,
    ButtonSpinner,
    DeviceComboBox,
    FlowLayout,
)
from desktop_app.ui.inspector.layout.parser import (
    get_layout_physical_size,
    parse_layout_file,
)
from desktop_app.ui.inspector.locator.harmony_hypium import (
    extract_hypium_expression,
    parse_hypium_by_expression,
    resolve_harmony_locator_input,
)
from desktop_app.ui.inspector.locator.ios_selector import (
    tokenize_ios_predicate,
    validate_ios_selector_syntax,
)
from desktop_app.ui.inspector.locator.xpath_engine import (
    _init_lxml_xpath_extensions,
    validate_xpath_syntax,
)
from desktop_app.ui.inspector.platforms.android import parse_android_node, run_adb
from desktop_app.ui.inspector.platforms.harmony import (
    HarmonyRpcLayoutClient,
    normalize_harmony_node,
    run_hdc,
)
from desktop_app.ui.inspector.platforms.ios import (
    crop_ios_dvt_image,
    extract_ios_logical_size,
    normalize_ios_screenshot_file,
    parse_ios_json_node,
    parse_ios_node,
)
from desktop_app.ui.inspector.platforms.ios_service import (
    IosServiceActionWorker,
    IosWdaManager,
    check_ios_wda_services,
    run_ios_action,
)
from desktop_app.ui.inspector.platforms.registry import (
    DeviceController,
    DeviceScanWorker,
    get_connected_devices,
)
from desktop_app.ui.inspector.views.dom_tree_view import (
    DOMTreeItemDelegate,
    DOMTreeWidget,
    extract_word_bounds,
)
from desktop_app.ui.inspector.views.main_inspector import HarmonyAppiumInspector, main
from desktop_app.ui.inspector.views.screen_canvas import AppiumScreenView, InspectorMode
from desktop_app.ui.inspector.views.search_dialog import SearchElementDialog
from desktop_app.ui.inspector.workers.capture_worker import CaptureWorker
from desktop_app.ui.inspector.workers.screencast_worker import ScreenCastWorker

# 兼容旧引用别名
QMessageBox = ModernMessageBox
QInputDialog = ModernInputDialog

__all__ = [
    "AppiumScreenView",
    "AutoResizingTextEdit",
    "AutoWrapStatusLabel",
    "ButtonSpinner",
    "CaptureWorker",
    "DOMTreeItemDelegate",
    "DOMTreeWidget",
    "DeviceComboBox",
    "DeviceController",
    "DeviceScanWorker",
    "FlowLayout",
    "HarmonyAppiumInspector",
    "HarmonyRpcLayoutClient",
    "InspectorMode",
    "IosServiceActionWorker",
    "IosWdaManager",
    "LOCAL_ICON_DIR",
    "ModernInputDialog",
    "ModernMessageBox",
    "QInputDialog",
    "QMessageBox",
    "ScreenCastWorker",
    "SearchElementDialog",
    "ToastNotification",
    "_init_lxml_xpath_extensions",
    "check_ios_wda_services",
    "create_modern_app_icon",
    "crop_ios_dvt_image",
    "extract_hypium_expression",
    "extract_ios_logical_size",
    "extract_word_bounds",
    "get_connected_devices",
    "get_dom_tag_color",
    "get_layout_physical_size",
    "get_tech_icon",
    "import_network_icon",
    "main",
    "normalize_harmony_node",
    "normalize_ios_screenshot_file",
    "parse_android_node",
    "parse_hypium_by_expression",
    "parse_ios_json_node",
    "parse_ios_node",
    "parse_layout_file",
    "resolve_harmony_locator_input",
    "run_adb",
    "run_hdc",
    "run_ios_action",
    "tokenize_ios_predicate",
    "validate_ios_selector_syntax",
    "validate_xpath_syntax",
]

if __name__ == "__main__":
    main()