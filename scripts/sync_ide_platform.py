# -*- coding: utf-8 -*-
"""根据当前测试平台自动同步跨端 Locator 代理类的继承顺序，使 IDE Ctrl+左键跳转到对应平台定义文件。"""
import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# 平台名称标准化映射
_PLATFORM_ALIASES: Dict[str, str] = {
    "android": "android",
    "harmonyos": "harmonyos",
    "harmony": "harmonyos",
    "hos": "harmonyos",
    "openharmony": "harmonyos",
    "ios": "ios",
    "apple": "ios",
}

# 平台对应的类属性标记名称
_PLATFORM_ATTR_MAP: Dict[str, str] = {
    "android": "_android_cls",
    "harmonyos": "_harmony_cls",
    "ios": "_ios_cls",
}

# 默认平台优先级顺序：安卓 -> iOS -> 鸿蒙
_DEFAULT_PLATFORM_ORDER: List[str] = ["android", "ios", "harmonyos"]

_CLASS_DEF_PATTERN = re.compile(
    r"(class\s+\w+\()([^)]*?)(,\s*metaclass=DynamicLocatorMeta\):)"
)


def normalize_platform(platform: Optional[str]) -> str:
    """将输入平台名标准化为 android / harmonyos / ios。"""
    raw = (platform or "android").strip().lower()
    return _PLATFORM_ALIASES.get(raw, "android")


def read_current_platform(project_root: Path) -> str:
    """从 config/devices.yaml 读取 current_platform。"""
    devices_yaml = project_root / "config" / "devices.yaml"
    if not devices_yaml.exists():
        return "android"
    try:
        with open(devices_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return normalize_platform(data.get("current_platform", "android"))
    except Exception:
        return "android"


def _extract_platform_classes(content: str) -> Dict[str, str]:
    """从 Locator 文件中解析 _android_cls / _harmony_cls / _ios_cls 对应的类名。"""
    mapping: Dict[str, str] = {}
    for plat, attr_name in _PLATFORM_ATTR_MAP.items():
        match = re.search(rf"^\s*{attr_name}\s*=\s*(\w+)\s*$", content, re.MULTILINE)
        if match:
            mapping[plat] = match.group(1)
    return mapping


def _reorder_bases(
    bases_str: str,
    plat_classes: Dict[str, str],
    target_platform: str,
) -> str:
    """将目标平台基类置顶，其余基类按 安卓 -> iOS -> 鸿蒙 优先级排列。"""
    bases: List[str] = [item.strip() for item in bases_str.split(",") if item.strip()]
    ordered_platforms = [target_platform] + [p for p in _DEFAULT_PLATFORM_ORDER if p != target_platform]

    reordered: List[str] = []
    for plat in ordered_platforms:
        cls_name = plat_classes.get(plat)
        if cls_name and cls_name in bases and cls_name not in reordered:
            reordered.append(cls_name)

    for base in bases:
        if base not in reordered:
            reordered.append(base)

    return ", ".join(reordered)


def sync_ide_platform(
    target_platform: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> List[Path]:
    """同步 locators 目录下所有跨端代理类的继承顺序，返回实际发生变更的文件路径列表。"""
    root = project_root or Path(__file__).resolve().parent.parent
    locators_dir = root / "locators"
    if not locators_dir.exists():
        return []

    platform = normalize_platform(target_platform) if target_platform else read_current_platform(root)
    changed_files: List[Path] = []

    for py_file in sorted(locators_dir.rglob("*.py")):
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        if "metaclass=DynamicLocatorMeta" not in content:
            continue

        plat_classes = _extract_platform_classes(content)
        preferred_cls = plat_classes.get(platform)
        if not preferred_cls:
            continue

        def _replace_match(m: re.Match[str]) -> str:
            new_bases = _reorder_bases(m.group(2), plat_classes, platform)
            return f"{m.group(1)}{new_bases}{m.group(3)}"

        new_content, count = _CLASS_DEF_PATTERN.subn(_replace_match, content, count=1)
        if count > 0 and new_content != content:
            py_file.write_text(new_content, encoding="utf-8")
            changed_files.append(py_file)

    return changed_files


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="同步跨端 Locator 的 IDE 静态跳转目标平台")
    parser.add_argument(
        "--platform",
        "-p",
        type=str,
        default=None,
        help="目标平台 (android / harmonyos / ios)，不传则读取 config/devices.yaml",
    )
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    active_platform = normalize_platform(args.platform) if args.platform else read_current_platform(root_dir)
    updated = sync_ide_platform(target_platform=active_platform, project_root=root_dir)

    if updated:
        print(f"[IDE跳转同步] 已切换为 {active_platform}，更新 {len(updated)} 个定位器文件：")
        for path in updated:
            print(f"  - {path.relative_to(root_dir).as_posix()}")
    else:
        print(f"[IDE跳转同步] 当前已是 {active_platform}，无需修改。")
