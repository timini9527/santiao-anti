# -*- coding: utf-8 -*-
"""
Pytest 运行时状态收集插件
用于在用例执行完毕时，通过 stdout 打印固定格式的状态日志，供控制台解析。
"""
import pytest

def pytest_runtest_logreport(report):
    # 过滤 setup / call / teardown 的结果
    # 只有在 call 阶段（用例执行完）我们才报告 passed/failed
    # 如果 setup 阶段失败了（例如 Error 或是环境崩溃），我们需要在 setup 阶段记录失败或跳过
    if report.when == 'call':
        status = report.outcome  # 'passed' | 'failed' | 'skipped'
        print(f"\n[TEST_RESULT] nodeid={report.nodeid} status={status}")
    elif report.when == 'setup':
        if report.failed:
            print(f"\n[TEST_RESULT] nodeid={report.nodeid} status=failed")
        elif report.skipped:
            print(f"\n[TEST_RESULT] nodeid={report.nodeid} status=skipped")
