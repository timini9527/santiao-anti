import os
import re
import requests
from typing import Dict, Any

class AIAnalyzer:
    """自动化测试错误根因分析 (RCA) 智能体"""

    def __init__(self):
        # 优先读取系统环境变量，支持灵活配置
        self.api_key = os.getenv("sk-MalT0UWMS4qKOhWlKeSqnrgR36DMAKBXO4qL5xE0ZKjOT41P")
        self.base_url = os.getenv("AI_BASE_URL", "sk-MalT0UWMS4qKOhWlKeSqnrgR36DMAKBXO4qL5xE0ZKjOT41P")
        self.model = os.getenv("AI_MODEL", "gpt-5.5")

    def _get_mock_analysis(self, failure_detail: Dict[str, Any]) -> str:
        """规则兜底：在未配置 API_KEY 时提供本地的规则匹配诊断"""
        name = failure_detail.get("name", "")
        error_class = failure_detail.get("error_class", "")
        message = failure_detail.get("message", "")
        traceback = failure_detail.get("traceback", "")

        analysis_template = (
            "📌 【故障大意】:\n"
            "{summary}\n\n"
            "🔍 【可能原因】:\n"
            "{reasons}\n\n"
            "🛠️ 【排查与修复建议】:\n"
            "{suggestions}\n\n"
            "⚠️ [提示]: 当前运行在本地规则诊断(Mock)模式。配置环境变量 AI_API_KEY 后可启用完整的 LLM 智能诊断。"
        )

        # 规则匹配 1：元素定位失败 (NoSuchElementException)
        if "NoSuchElementException" in error_class or "NoSuchElementException" in traceback:
            summary = f"在用例 {name} 中定位 UI 元素失败。详细信息: {message}"
            reasons = (
                "- 定位器失效/DOM 改变：被测应用 (IM 软件) 进行了版本更新，导致目标元素的 XPath、ID 或 ClassName 发生了改变。\n"
                "- 元素加载延迟：页面渲染过慢，当前脚本尚未等该元素渲染完毕即执行了定位操作。"
            )
            suggestions = (
                "1. 查看错误截图，核对报错发生时页面是否处于预期状态。\n"
                "2. 使用 Appium Inspector/Chrome DevTools 重新定位该元素，核对 XPath 表达式。\n"
                "3. 将直接定位修改为显式等待，例如使用 WebDriverWait + ExpectedConditions。"
            )
        # 规则匹配 2：超时 (TimeoutException)
        elif "TimeoutException" in error_class or "TimeoutException" in traceback:
            summary = f"用例 {name} 执行时，等待特定 UI 状态或事件超时。详细信息: {message}"
            reasons = (
                "- 超时与网络问题：IM 长连接 (WebSocket) 在弱网/丢包环境下握手过慢或断开，导致未能及时收到离线消息。\n"
                "- 前置步骤卡死：App 当前处于异常弹窗或崩溃状态，导致后续元素一直未能出现。"
            )
            suggestions = (
                "1. 确认前置步骤是否成功，检查是否有未关闭的系统权限弹窗。\n"
                "2. 检查网络代理或 mitmproxy 的设置，观察 WebSocket 长连接心跳是否正常。\n"
                "3. 酌情增加 WebDriverWait 的 timeout 阈值。"
            )
        # 规则匹配 3：断言失败 (AssertionError)
        elif "AssertionError" in error_class or "AssertionError" in traceback:
            summary = f"用例 {name} 的业务逻辑断言失败。详细信息: {message}"
            reasons = (
                "- 业务 Bug：类微信 IM 软件的消息状态机、联系人同步或朋友圈模块存在真实的逻辑 Bug，系统表现与预期不符。\n"
                "- 测试数据污染：多端并发测试中，被测账号受到其他用例的并发干扰，导致未读数、好友列表不符合预期。"
            )
            suggestions = (
                "1. 根据断言信息核对实际输出与期望值，确认该业务功能在当前版本是否正常。\n"
                "2. 检查测试数据隔离，确保该用例使用的账号不与其他并发用例冲突。\n"
                "3. 检查后端接口日志，确认此断言背后的 API 返回是否正确。"
            )
        # 兜底通用规则
        else:
            summary = f"用例 {name} 抛出了未预料的异常 {error_class}。详细信息: {message}"
            reasons = (
                "- 脚本本身 Bug：可能存在 Python 代码逻辑错误或空值引用。\n"
                "- 环境崩溃：测试执行环境（设备离线、App 进程闪退）导致异常中断。"
            )
            suggestions = (
                "1. 仔细查阅下方 Traceback 堆栈定位到具体的报错代码行。\n"
                "2. 确认测试设备 (如 Android/iOS) 是否在线，App 是否发生了 Crash (闪退)。"
            )

        return analysis_template.format(summary=summary, reasons=reasons, suggestions=suggestions)

    def analyze_failure(self, failure_detail: Dict[str, Any]) -> str:
        """
        核心分析接口。若配置了 API_KEY 则调用大模型；否则使用 Mock 诊断
        :param failure_detail: 包含用例信息、错误类和 traceback 的字典
        :return: 中文分析报告
        """
        if not self.api_key:
            return self._get_mock_analysis(failure_detail)

        # 构造 prompt
        system_prompt = (
            "你是一名拥有 10 年以上经验的资深测试开发架构师。现在需要你对自动化测试中挂掉的测试用例进行根因分析（RCA）。\n\n"
            "请按如下结构输出中文分析结果，不要包含 Markdown 的 ``` 包装，只返回以下格式 of 文本：\n"
            "📌 【故障大意】:\n"
            "[简短清晰地说明在什么地方、执行什么操作时发生了什么错误，通俗易懂，避免直接堆砌堆栈]\n\n"
            "🔍 【可能原因】:\n"
            "[给出可能导致该错误发生的具体原因。需结合你的自动化测试经验，区分以下类别并给出诊断：\n"
            " - 业务 Bug\n"
            " - 定位器失效/DOM 改变\n"
            " - 超时与网络\n"
            " - 数据/环境问题\n"
            " - 脚本本身 Bug]\n\n"
            "🛠️ 【排查与修复建议】:\n"
            "[提供下一步的排查方案、需要检查的日志、或具体的代码修改思路]"
        )

        user_content = (
            f"测试用例: {failure_detail.get('file')}::{failure_detail.get('name')}\n"
            f"错误类型: {failure_detail.get('error_class')}\n"
            f"异常信息: {failure_detail.get('message')}\n"
            f"Traceback 堆栈信息:\n{failure_detail.get('traceback')}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2
        }

        try:
            # 设置 15 秒超时防止卡死执行流程
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data, timeout=15)
            if response.status_code == 200:
                result_json = response.json()
                return result_json["choices"][0]["message"]["content"].strip()
            else:
                # HTTP 报错时退回到本地 Mock 诊断
                err_msg = f"API 响应错误 (HTTP {response.status_code}): {response.text}"
                print(f"警告: 大模型接口请求失败，将使用本地诊断。{err_msg}")
                return self._get_mock_analysis(failure_detail)
        except Exception as e:
            print(f"警告: 大模型接口请求发生异常，将使用本地诊断。错误: {e}")
            return self._get_mock_analysis(failure_detail)
