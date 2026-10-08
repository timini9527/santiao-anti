# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 用例扫描与解析
=======================================================
"""
import os
import sys
from typing import List, Dict, Any

from desktop_app.config import PROJECT_ROOT

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web_platform.backend.collector import collect_all_tests

import json

class TestCollectorService:
    """提供用例目录树扫描服务"""

    @staticmethod
    def _get_catalog_data() -> List[Dict[str, Any]]:
        """
        自适应获取测试用例目录清单：
        1. 优先加载 tests/tests_catalog.json (方案4深度加密发布包专用的预提取索引，0 源码依赖，毫秒级响应)
        2. 源码开发状态下动态实时扫描 tests/
        """
        cached_json = os.path.join(PROJECT_ROOT, "tests", "tests_catalog.json")
        if os.path.exists(cached_json):
            try:
                with open(cached_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        return data
            except Exception:
                pass
        return collect_all_tests(os.path.join(PROJECT_ROOT, "tests"))

    @staticmethod
    def get_test_hierarchy(category: str = "mobile") -> List[Dict[str, Any]]:
        """
        按 一级目录(Category) -> 二级文件(File) -> 三级类(Class) -> 四级用例(Test) -> 五级参数(Param)
        组织全量多级测试用例树结构
        """
        all_catalog = TestCollectorService._get_catalog_data()
        categories: Dict[str, List[Dict[str, Any]]] = {}
        direct_files: List[Dict[str, Any]] = []

        for file_obj in all_catalog:
            file_path = file_obj["file"].replace("\\", "/")
            if category == "mobile" and (file_path.startswith("tests/web") or file_path.startswith("tests/api")):
                continue
            elif category == "web" and not file_path.startswith("tests/web"):
                continue
            elif category == "api" and not file_path.startswith("tests/api"):
                continue

            rel = file_path[6:] if file_path.startswith("tests/") else file_path
            parts = rel.split("/")

            # 统计当前文件用例总数
            file_count = 0
            for cls in file_obj.get("classes", []):
                for t in cls.get("tests", []):
                    params = t.get("params", [])
                    file_count += len(params) if params else 1
            for t in file_obj.get("tests", []):
                params = t.get("params", [])
                file_count += len(params) if params else 1

            file_copy = dict(file_obj)
            file_copy["count"] = file_count

            if len(parts) > 1:
                cat_name = parts[0]
                if cat_name not in categories:
                    categories[cat_name] = []
                categories[cat_name].append(file_copy)
            else:
                direct_files.append(file_copy)

        final_hierarchy = []
        # 一级目录排序：smoke_test 必须置顶排在最前，其余按字母排序
        sorted_cat_names = sorted(categories.keys(), key=lambda x: (0 if "smoke" in x.lower() else 1, x))
        for cat_name in sorted_cat_names:
            file_list = categories[cat_name]
            # 文件排序：单聊基础等核心文件排在最前
            file_list.sort(key=lambda x: (0 if "smoke_chat" in x["file"].lower() or "test_chat" in x["file"].lower() else 1, x["file"]))
            cat_count = sum(f["count"] for f in file_list)
            final_hierarchy.append({
                "type": "category",
                "name": cat_name,
                "display_name": cat_name,
                "target": f"tests/{cat_name}",
                "count": cat_count,
                "files": file_list
            })

        if direct_files:
            final_hierarchy.append({
                "type": "category",
                "name": "root",
                "display_name": "独立测试用例",
                "target": "tests",
                "count": sum(f["count"] for f in direct_files),
                "files": direct_files
            })

        return final_hierarchy

    @staticmethod
    def get_test_catalog(category: str = "mobile") -> List[Dict[str, Any]]:
        """保留扁平文件列表兼容接口"""
        all_catalog = TestCollectorService._get_catalog_data()
        if category == "mobile":
            mobile_catalog = []
            for item in all_catalog:
                rel = item["file"].replace("\\", "/")
                if not rel.startswith("tests/web") and not rel.startswith("tests/api"):
                    mobile_catalog.append(item)
            mobile_catalog.sort(key=lambda x: (0 if "smoke" in x["file"].lower() else 1, x["file"]))
            return mobile_catalog
        elif category == "web":
            return [item for item in all_catalog if item["file"].replace("\\", "/").startswith("tests/web")]
        elif category == "api":
            return [item for item in all_catalog if item["file"].replace("\\", "/").startswith("tests/api")]
        else:
            return all_catalog
