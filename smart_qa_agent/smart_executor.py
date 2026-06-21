import os
import subprocess
import xml.etree.ElementTree as ET
import re
import sys
from typing import List, Dict, Any

# 动态将当前包目录和项目根目录加入 sys.path 防止导包失败
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ai_analyzer import AIAnalyzer
from healer import TestHealer
# from jira_client import JiraClient

def safe_print(text: str):
    """防止控制台打印非当前编码字符时崩溃"""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        clean_text = text.encode(encoding, errors='replace').decode(encoding)
        print(clean_text)

class SmartExecutor:
    """智能测试执行器，负责调用 pytest 并解析执行生成的 JUnit XML 报告"""

    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or os.getcwd()

    def run_tests(self, test_target: str, xml_path: str = "reports/junit_report.xml") -> int:
        """
        调用 pytest 运行测试目标，并导出 XML 报告
        :param test_target: 测试文件或目录路径
        :param xml_path: junit XML 报表存放路径
        :return: pytest 的退出状态码
        """
        # 确保报告目录存在
        abs_xml_path = os.path.join(self.workspace_dir, xml_path)
        os.makedirs(os.path.dirname(abs_xml_path), exist_ok=True)

        cmd = [
            "pytest",
            test_target,
            f"--junitxml={abs_xml_path}",
            "-vs"
        ]
        
        safe_print(f"开始运行测试命令: {' '.join(cmd)}")
        # 运行 pytest，捕获控制台输出，指定 errors="ignore" 防止 GBK/UTF-8 解码崩溃
        result = subprocess.run(
            cmd, 
            cwd=self.workspace_dir, 
            capture_output=True, 
            text=True, 
            encoding="utf-8", 
            errors="ignore"
        )
        
        safe_print("====== Pytest 控制台输出 ======")
        safe_print(result.stdout)
        if result.stderr:
            safe_print("====== Pytest 错误输出 ======")
            safe_print(result.stderr)
            
        return result.returncode

    def parse_xml_report(self, xml_path: str = "reports/junit_report.xml") -> Dict[str, Any]:
        """
        解析 JUnit XML 报告，提取通过、失败、跳过等统计数据
        :param xml_path: junit XML 报表路径
        :return: 包含统计结果及失败详情的字典
        """
        abs_xml_path = os.path.join(self.workspace_dir, xml_path)
        if not os.path.exists(abs_xml_path):
            raise FileNotFoundError(f"找不到 XML 报告文件: {abs_xml_path}")

        tree = ET.parse(abs_xml_path)
        root = tree.getroot()

        summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "failures_details": []
        }

        # 遍历所有的 testcase
        for testcase in root.iter("testcase"):
            summary["total"] += 1
            name = testcase.get("name")
            classname = testcase.get("classname")
            file_path = testcase.get("file")
            line = testcase.get("line")
            duration = float(testcase.get("time", 0.0))

            failure_node = testcase.find("failure")
            error_node = testcase.find("error")
            skipped_node = testcase.find("skipped")

            tb_text = ""
            if failure_node is not None:
                tb_text = failure_node.text or ""
            elif error_node is not None:
                tb_text = error_node.text or ""

            # 若 XML 未直接提供 file_path / line，则尝试从 traceback 和 classname 中提取
            if tb_text:
                # 优先匹配 pytest 输出末尾形式: tests\test_mock_failures.py:14: AssertionError
                match = re.search(r"([\w\\/\.\-]+\.py):(\d+): \w+", tb_text)
                if match:
                    file_path = match.group(1).replace("\\", "/")
                    line = match.group(2)
                else:
                    # 其次匹配标准的 Python Traceback 行: File "xxx", line 123
                    tb_lines = tb_text.strip().split("\n")
                    for tb_line in reversed(tb_lines):
                        tb_match = re.search(r'File "([^"]+)", line (\d+)', tb_line)
                        if tb_match:
                            file_path = tb_match.group(1).replace("\\", "/")
                            line = tb_match.group(2)
                            break

            # 兜底：若仍未获取到文件名，根据 classname 进行推导
            if file_path is None and classname:
                parts = classname.split(".")
                possible_path = "/".join(parts) + ".py"
                file_path = possible_path

            if failure_node is not None:
                summary["failed"] += 1
                summary["failures_details"].append({
                    "name": name,
                    "classname": classname,
                    "file": file_path,
                    "line": line,
                    "duration": duration,
                    "type": "failure",
                    "error_class": failure_node.get("message", "").split(":")[0],
                    "message": failure_node.get("message", ""),
                    "traceback": tb_text
                })
            elif error_node is not None:
                summary["failed"] += 1
                summary["failures_details"].append({
                    "name": name,
                    "classname": classname,
                    "file": file_path,
                    "line": line,
                    "duration": duration,
                    "type": "error",
                    "error_class": error_node.get("message", "").split(":")[0],
                    "message": error_node.get("message", ""),
                    "traceback": tb_text
                })
            elif skipped_node is not None:
                summary["skipped"] += 1
            else:
                summary["passed"] += 1

        return summary

    def run_smart_workflow(self, test_target: str) -> Dict[str, Any]:
        """运行智能测试闭环工作流：执行 -> 根因分析 -> 定位自愈 -> 重跑 -> Jira 提单"""
        # 1. 运行初始测试
        self.run_tests(test_target)
        
        # 2. 解析报告
        report_data = self.parse_xml_report()
        safe_print("\n====== [1/4] 测试结果统计 ======")
        safe_print(f"总用例数: {report_data['total']}")
        safe_print(f"通过数  : {report_data['passed']}")
        safe_print(f"失败数  : {report_data['failed']}")
        
        if report_data["failed"] == 0:
            safe_print("[OK] 所有用例全部通过，测试结束。")
            return {
                "total": report_data["total"],
                "passed": report_data["passed"],
                "failed": 0,
                "failures_details": []
            }

        safe_print("\n====== [2/4] 进入 AI 根因分析 (RCA) & 自愈决策 ======")
        analyzer = AIAnalyzer()
        healer = TestHealer(self.workspace_dir)

        # 存放需要恢复的文件列表
        healed_files = set()
        
        # 构建返回结果
        workflow_result = {
            "total": report_data["total"],
            "passed": report_data["passed"],
            "failed": report_data["failed"],
            "failures_details": []
        }

        for fail in report_data["failures_details"]:
            safe_print(f"\n[FAIL] 失败用例: {fail['file']}::{fail['name']} (第 {fail['line']} 行)")
            
            # 生成 AI 报告
            rca_report = analyzer.analyze_failure(fail)
            fail["rca_report"] = rca_report
            
            safe_print("[AI 诊断报告]:")
            for line_text in rca_report.split("\n"):
                safe_print(f"  {line_text}")

            # 3. 尝试定位自愈
            healed = False
            # 只有 NoSuchElementException 类型的异常才尝试自愈
            if "NoSuchElementException" in fail["error_class"] and fail["file"] and fail["line"]:
                safe_print(f"\n[自愈尝试] 检测到定位失败，开始自动修复 (Self-Healing)...")
                try:
                    line_num = int(fail["line"])
                    if healer.attempt_heal(fail["file"], line_num):
                        healed_files.add(fail["file"])
                        
                        # 重新运行这一个特定的用例
                        specific_target = f"{fail['file']}::{fail['name']}"
                        safe_print(f"[重跑验证] 重新运行用例以验证修复: {specific_target}")
                        
                        # 使用一个临时的 xml 报告来装重跑结果
                        retry_xml = "reports/junit_retry_report.xml"
                        self.run_tests(specific_target, xml_path=retry_xml)
                        retry_data = self.parse_xml_report(xml_path=retry_xml)
                        
                        if retry_data["failed"] == 0:
                            safe_print(f"[自愈成功] 用例 {fail['name']} 已通过修复重跑成功！")
                            healed = True
                        else:
                            safe_print(f"[自愈失败] 重跑仍旧失败。")
                except Exception as ex:
                    safe_print(f"[警告] 自愈尝试过程发生异常: {ex}")

            fail["healed"] = healed

            # 4. 如果无法自愈或自愈失败，自动提单 (已注释暂不执行)
            if not healed:
                safe_print(f"\n[提示] 用例最终执行失败，无法执行自愈。")
            
            workflow_result["failures_details"].append(fail)
            safe_print("-" * 60)

        # 5. 还原修改的代码文件
        if healed_files:
            safe_print("\n====== [3/4] 清理自愈临时修改并还原代码 ======")
            for file_path in healed_files:
                healer.restore_file(file_path)


if __name__ == "__main__":
    # 本地调试入口
    executor = SmartExecutor()
    
    # 支持从命令行参数接收测试目标文件或目录
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = "smart_qa_agent/tests/test_mock_failures.py"
        
    executor.run_smart_workflow(test_file)
