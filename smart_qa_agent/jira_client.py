import os
import json
import requests
import datetime
from typing import Dict, Any

class JiraClient:
    """自动创建 Bug 票据的 Jira 客户端"""

    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_user = os.getenv("JIRA_USER")
        self.jira_token = os.getenv("JIRA_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "IM")

    def create_bug(self, failure_detail: Dict[str, Any], rca_report: str) -> str:
        """
        创建一个 Bug。若没有配置真实 Jira 环境，将以 Mock 模式输出 JSON 文件到本地
        :param failure_detail: 失败用例详情
        :param rca_report: AI/本地生成的根因分析报告
        :return: Jira Bug 键值 (如 IM-101) 或 Mock 本地文件路径
        """
        # 构建 Bug 内容
        summary = f"[Auto-Bug] 测试用例 {failure_detail.get('name')} 执行失败 - {failure_detail.get('error_class')}"
        
        description = (
            f"h2. 🔴 自动化测试失败自动提单\n\n"
            f"*失败用例*: {failure_detail.get('file')}::{failure_detail.get('name')} (第 {failure_detail.get('line')} 行)\n"
            f"*异常类别*: {failure_detail.get('error_class')}\n"
            f"*执行耗时*: {failure_detail.get('duration', 0.0)} 秒\n\n"
            f"h3. 🤖 AI 智能诊断分析:\n"
            f"{rca_report}\n\n"
            f"h3. 📋 Traceback 报错日志:\n"
            f"{{code:python}}\n"
            f"{failure_detail.get('traceback', '').strip()}\n"
            f"{{code}}\n"
        )

        # 检查是否配置了 Jira 凭证
        if not all([self.jira_url, self.jira_user, self.jira_token]):
            # 运行在 Mock 模式，输出本地 JSON 文件
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            bug_dir = os.path.join(os.getcwd(), "reports", "jira_bugs")
            os.makedirs(bug_dir, exist_ok=True)
            
            mock_bug_data = {
                "summary": summary,
                "description": description,
                "project": {"key": self.project_key},
                "issuetype": {"name": "Bug"},
                "priority": {"name": "High"},
                "labels": ["autotest-failure", failure_detail.get("error_class", "unknown")]
            }
            
            file_path = os.path.join(bug_dir, f"bug_{failure_detail.get('name')}_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(mock_bug_data, f, indent=4, ensure_ascii=False)
            
            print(f"[提示]: 未检测到完整 Jira 环境变量。Bug 数据已输出到本地 file: {file_path}")
            return f"LOCAL_MOCK_FILE: {file_path}"

        # 真实 Jira 创建请求
        headers = {
            "Content-Type": "application/json"
        }
        
        # Jira REST API 负载结构
        payload = {
            "fields": {
                "project": {
                    "key": self.project_key
                },
                "summary": summary,
                "description": description,
                "issuetype": {
                    "name": "Bug"
                },
                "priority": {
                    "name": "Medium"
                },
                "labels": ["autotest-failure", "smart-triage"]
            }
        }

        # 调用 Jira API 创建票据 (通常使用 Basic 鉴权：邮箱/用户名 和 API Token)
        try:
            api_endpoint = f"{self.jira_url.rstrip('/')}/rest/api/2/issue"
            response = requests.post(
                api_endpoint,
                headers=headers,
                auth=(self.jira_user, self.jira_token),
                json=payload,
                timeout=10
            )
            if response.status_code in [200, 201]:
                issue_key = response.json().get("key")
                print(f"[Jira] 成功在 Jira 创建 Bug 单: {issue_key}")
                return issue_key
            else:
                print(f"[Jira] Jira 创建失败 (HTTP {response.status_code}): {response.text}")
                # 失败时做个兜底保存
                return f"ERROR_FALLBACK: {response.text}"
        except Exception as e:
            print(f"[Jira] 连接 Jira 发生网络异常: {e}")
            return f"ERROR_FALLBACK_EXCEPTION: {e}"
