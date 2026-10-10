# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 - 报告中心统一扫描与管理核心
=======================================================
提供全局统一的测试报告扫描、有效性验证、元数据解析与报告计数能力，
确保 移动控制中心、报告中心、设备矩阵 等各页面显示的报告份数 100% 动态实时对齐，
彻底杜绝页面间数据不同步或硬编码假数据。
"""
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# 环境自愈：确保项目根目录在 sys.path 中
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from web_platform.backend.paths import REPORTS_DIR
except Exception:
    try:
        from ..config import PROJECT_ROOT
        REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
    except (ImportError, ValueError):
        try:
            from desktop_app.config import PROJECT_ROOT
            REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
        except Exception:
            REPORTS_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, "reports"))


def scan_available_reports() -> List[Dict[str, Any]]:
    """
    全自动扫描本地所有有效测试任务报告（与报告中心 ReportsPage 逻辑完全一致）：
    1. 扫描 REPORTS_DIR/allure_reports/ 下的编译报告
    2. 扫描 REPORTS_DIR/html_task_* (Web 平台生成的报告)
    3. 扫描 REPORTS_DIR/allure_results/ 下未生成 HTML 的原始 JSON 结果
    返回按修改时间倒序排列的有效报告元数据列表
    """
    new_list: List[Dict[str, Any]] = []
    found_ids = set()

    if not os.path.exists(REPORTS_DIR):
        return new_list

    # 1. 扫描 REPORTS_DIR/allure_reports/ 下的编译报告
    allure_reports_dir = os.path.join(REPORTS_DIR, "allure_reports")
    if os.path.exists(allure_reports_dir):
        for name in os.listdir(allure_reports_dir):
            sp = os.path.join(allure_reports_dir, name)
            if not os.path.isdir(sp):
                continue

            # 自动清理完全为空的异常残留目录
            if not os.listdir(sp):
                try:
                    os.rmdir(sp)
                except Exception:
                    pass
                continue

            sum_sub = os.path.join(sp, "widgets", "summary.json")
            tot = 0
            t_str = ""
            if os.path.exists(sum_sub):
                try:
                    with open(sum_sub, "r", encoding="utf-8") as f:
                        s_data = json.load(f)
                    tot = s_data.get("statistic", {}).get("total", 0)
                    st = s_data.get("time", {}).get("start", 0)
                    if st:
                        t_str = datetime.fromtimestamp(st / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

            # 检查同名 allure_results 是否有结果
            cand_res = os.path.join(REPORTS_DIR, "allure_results", name)
            res_count = len([f for f in os.listdir(cand_res) if f.endswith("-result.json")]) if os.path.exists(cand_res) else 0

            # 防御性过滤：若既无统计数据也无任何结果文件（如执行时被强行终止），则不列入有效报告列表
            if tot == 0 and res_count == 0:
                continue

            if not t_str:
                mtime = os.path.getmtime(sp)
                t_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

            new_list.append({
                "task_id": name,
                "time": t_str,
                "cases": max(tot, res_count),
                "path": sp,
                "mtime": os.path.getmtime(sp)
            })
            found_ids.add(name)

    # 2. 扫描 REPORTS_DIR/html_task_* (Web 平台生成的报告)
    if os.path.exists(REPORTS_DIR):
        for name in os.listdir(REPORTS_DIR):
            if name.startswith("html_task_"):
                raw_id = name.replace("html_", "")
                if raw_id in found_ids:
                    continue
                sp = os.path.join(REPORTS_DIR, name)
                if not os.path.isdir(sp):
                    continue
                if not os.listdir(sp):
                    try:
                        os.rmdir(sp)
                    except Exception:
                        pass
                    continue
                sum_sub = os.path.join(sp, "widgets", "summary.json")
                tot = 0
                t_str = ""
                if os.path.exists(sum_sub):
                    try:
                        with open(sum_sub, "r", encoding="utf-8") as f:
                            s_data = json.load(f)
                        tot = s_data.get("statistic", {}).get("total", 0)
                        st = s_data.get("time", {}).get("start", 0)
                        if st:
                            t_str = datetime.fromtimestamp(st / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
                if tot == 0:
                    continue
                if not t_str:
                    mtime = os.path.getmtime(sp)
                    t_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                new_list.append({
                    "task_id": raw_id,
                    "time": t_str,
                    "cases": tot,
                    "path": sp,
                    "mtime": os.path.getmtime(sp)
                })
                found_ids.add(raw_id)

    # 3. 扫描 REPORTS_DIR/allure_results/ 下未生成 HTML 的原始 JSON 结果
    allure_results_dir = os.path.join(REPORTS_DIR, "allure_results")
    if os.path.exists(allure_results_dir):
        for name in os.listdir(allure_results_dir):
            if name in found_ids:
                continue
            sp = os.path.join(allure_results_dir, name)
            if not os.path.isdir(sp):
                continue
            if not os.listdir(sp):
                try:
                    os.rmdir(sp)
                except Exception:
                    pass
                continue
            json_files = [f for f in os.listdir(sp) if f.endswith("-result.json")]
            if not json_files:
                continue
            mtime = os.path.getmtime(sp)
            t_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            new_list.append({
                "task_id": name,
                "time": t_str,
                "cases": len(json_files),
                "path": sp,
                "mtime": mtime
            })
            found_ids.add(name)

    new_list.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return new_list


def get_reports_count() -> int:
    """获取报告中心当前实际存在的有效测试报告总份数"""
    try:
        reports = scan_available_reports()
        return len(reports)
    except Exception:
        return 0
