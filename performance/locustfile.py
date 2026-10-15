from core.logger_utils import logger, LogIcon
"""
配置驱动型 Locust 接口性能压测主入口 (locustfile.py)
架构特性：
1. 100% 配置驱动 (Declarative Performance Testing)：不再硬编码任何接口
2. 动态加载：想测几个接口，只需在 perf_config.yaml 中配置几个，实时读取并生成并发任务
3. 高性能引擎：采用 FastHttpUser (geventhttpclient) 协程并发模型
4. 自由权重分配：不同接口支持独立配置流量权重 (weight) 与启用开关 (enabled)
"""

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List
import yaml

# 将项目根目录与 performance 目录加入 Python 搜索路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from locust import between, events
try:
    from locust import FastHttpUser
except ImportError:
    from locust.contrib.fasthttp import FastHttpUser

CONFIG_FILE = CURRENT_DIR / "config" / "perf_config.yaml"


def load_perf_interfaces() -> List[Dict[str, Any]]:
    """从 perf_config.yaml 中加载用户自定义的接口列表"""
    if not CONFIG_FILE.exists():
        logger.warning(f"{LogIcon.WARN} [配置未找到] 未检测到配置文件: {CONFIG_FILE}")
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("interfaces", [])
    except Exception as e:
        logger.error(f"{LogIcon.FAIL} [配置解析失败] 读取 interfaces 出现异常: {e}")
        return []


def generate_dynamic_tasks() -> Dict[Callable, int]:
    """
    根据配置文件动态生成 Locust 任务字典
    返回格式: {任务执行函数: 流量权重}
    """
    interface_list = load_perf_interfaces()
    task_map: Dict[Callable, int] = {}
    active_count = 0

    for index, iface in enumerate(interface_list):
        # 仅加载开启的接口 (enabled: true)
        if not iface.get("enabled", True):
            continue

        name: str = iface.get("name", f"接口_{index + 1}")
        method: str = iface.get("method", "GET").upper()
        path: str = iface.get("path", "/")
        weight: int = int(iface.get("weight", 1))
        headers: Dict[str, Any] = iface.get("headers") or {}
        params: Dict[str, Any] = iface.get("params") or {}
        body: Dict[str, Any] = iface.get("body") or {}

        # 利用闭包固定当前接口的所有上下文参数
        def create_task_closure(
            req_method: str = method,
            req_path: str = path,
            req_name: str = name,
            req_headers: Dict[str, Any] = headers,
            req_params: Dict[str, Any] = params,
            req_body: Dict[str, Any] = body,
        ) -> Callable:
            def single_api_task(user: FastHttpUser) -> None:
                display_name = f"[{req_method}] {req_name}"
                kwargs: Dict[str, Any] = {
                    "name": display_name,
                    "catch_response": True,
                }
                if req_headers:
                    kwargs["headers"] = req_headers
                if req_params:
                    kwargs["params"] = req_params
                if req_method in ("POST", "PUT", "PATCH") and req_body:
                    kwargs["json"] = req_body

                with user.client.request(req_method, req_path, **kwargs) as response:
                    # 状态码校验 (2xx 与 3xx 判定为请求成功)
                    if 200 <= response.status_code < 400:
                        response.success()
                    elif response.status_code == 0:
                        response.failure("网络连接拒绝或超时 (Connection Refused/Timeout)")
                    else:
                        response.failure(f"HTTP错误码: {response.status_code}")

            single_api_task.__name__ = f"task_{index}_{req_method}_{req_name}"
            return single_api_task

        task_func = create_task_closure()
        task_map[task_func] = weight
        active_count += 1

    # 兜底保障：若配置文件中没有任何启用的接口
    if not task_map:
        def fallback_task(user: FastHttpUser) -> None:
            with user.client.get("/", name="[GET] 默认根路径 (未配置启用接口)", catch_response=True) as resp:
                if resp.status_code < 400:
                    resp.success()
                else:
                    resp.failure(f"状态码: {resp.status_code}")
        task_map[fallback_task] = 1

    return task_map


class DynamicApiPerformanceUser(FastHttpUser):
    """
    配置驱动型动态压测用户
    所测试的接口完全由 perf_config.yaml 中的 interfaces 列表动态生成，配几个测几个
    """
    # 请求思考时间：0.1 ~ 0.5 秒
    wait_time = between(0.1, 0.5)

    # 动态装载从配置文件生成的任务与权重
    tasks = generate_dynamic_tasks()


# ================================================================
# 🌐 官方级 Web UI 地道中文汉化补丁 (自动消除英文与浏览器生硬机翻)
# ================================================================
ZH_CN_INJECT_SCRIPT = """
<script>
(function() {
    const zhMap = {
        // 顶部操作栏与状态
        "Start swarming": "开始高并发压测",
        "Start": "开始测试",
        "Stop": "停止压测",
        "New test": "新建测试",
        "Edit": "动态调速/编辑",
        "Reset Stats": "重置统计",
        "Download Data": "导出报表与数据",
        "Download Report": "下载 HTML 报告",
        "Download CSV": "下载 CSV 数据明细",
        "Statistics": "接口性能统计",
        "Charts": "实时性能图表",
        "Failures": "失败请求明细",
        "Exceptions": "后端异常记录",
        "Current RPS": "当前每秒吞吐量 (RPS)",
        "Current Failures/s": "实时错误率 (次/秒)",
        "Peak concurrency": "峰值并发",
        "Total Requests per Second": "每秒总请求吞吐量 (RPS)",
        "Response Times (ms)": "响应延迟分布 (毫秒)",
        "Number of Users": "实时并发用户数",
        
        // 启动/编辑弹窗配置项
        "Number of users (peak concurrency)": "并发用户数 (峰值并发)",
        "Number of users": "并发用户数",
        "Ramp up (users started/second)": "爬坡速率 (每秒启动用户数)",
        "Spawn rate (users started/second)": "爬坡速率 (每秒启动用户数)",
        "Spawn rate": "爬坡速率 (用户/秒)",
        "Host": "目标服务器根地址 (Host)",
        "Advanced options": "高级参数选项",
        "Run time": "压测持续时间 (例如 1m, 5m, 1h)",
        "Description": "测试描述/备注",
        
        // 数据表格表头
        "Type": "请求方法",
        "Name": "接口名称",
        "Requests": "总请求量",
        "Fails": "失败数",
        "Median": "中位数 (P50)",
        "90%ile": "90% 分位数",
        "95%ile": "95% 分位数",
        "98%ile": "98% 分位数",
        "99%ile": "99% 分位数",
        "99.9%ile": "99.9% 分位数",
        "99.99%ile": "99.99% 分位数",
        "Average": "平均响应耗时",
        "Min": "最小耗时",
        "Max": "最大耗时",
        "Content Size": "平均包体体积",
        "Aggregated": "全接口综合汇总 (Total)",
        "Status": "状态",
        "Error": "错误详情",
        "Occurrences": "发生频次"
    };

    function walkAndTranslate(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            const val = node.nodeValue.trim();
            if (zhMap[val]) {
                node.nodeValue = node.nodeValue.replace(val, zhMap[val]);
            }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            if (node.placeholder && zhMap[node.placeholder]) {
                node.placeholder = zhMap[node.placeholder];
            }
            if (node.title && zhMap[node.title]) {
                node.title = zhMap[node.title];
            }
            for (let child of node.childNodes) {
                walkAndTranslate(child);
            }
        }
    }

    function triggerI18n() {
        if (document.body) {
            walkAndTranslate(document.body);
        }
    }

    // 页面加载完成与动态异步组件渲染监听
    window.addEventListener('DOMContentLoaded', triggerI18n);
    const observer = new MutationObserver(triggerI18n);
    observer.observe(document.documentElement, { childList: true, subtree: true });
    setInterval(triggerI18n, 500);
})();
</script>
"""


# @events.init.add_listener
# def on_init_localization(environment, **kwargs) -> None:
#     """初始化事件：向 Locust WebUI 动态注入地道中文汉化补丁"""
#     if not environment.web_ui:
#         return

#     @environment.web_ui.app.after_request
#     def inject_chinese_i18n(response):
#         content_type = response.headers.get("Content-Type", "")
#         if response.status_code == 200 and "text/html" in content_type:
#             try:
#                 html_text = response.get_data(as_text=True)
#                 if "</body>" in html_text:
#                     html_text = html_text.replace("</body>", f"{ZH_CN_INJECT_SCRIPT}</body>")
#                 elif "</html>" in html_text:
#                     html_text = html_text.replace("</html>", f"{ZH_CN_INJECT_SCRIPT}</html>")
#                 response.set_data(html_text)
#             except Exception:
#                 pass
#         return response


@events.test_start.add_listener
def on_test_start(environment, **kwargs) -> None:
    """压测启动前事件：输出当前已生效的自定义接口矩阵"""
    ifaces = [i for i in load_perf_interfaces() if i.get("enabled", True)]
    # 分隔线日志
    logger.info(f"{LogIcon.SETUP} [配置驱动压测引擎] 启动就绪！")
    logger.info(f"{LogIcon.SETUP} 当前生效的自定义接口数量: {len(ifaces)} 个")
    for idx, item in enumerate(ifaces, 1):
        logger.info(f"{LogIcon.ACTION} {idx}. [{item.get('method', 'GET').upper()}] {item.get('name')} -> {item.get('path')} (权重: {item.get('weight', 1)})")
    logger.info(f"{LogIcon.SETUP} 引擎核心: FastHttpUser (基于 C 解析器极速并发)")
    logger.info(f"{LogIcon.ACTION} 🇨🇳 界面语言: 已注入地道中文专业汉化补丁")
    # 分隔线日志


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:
    """压测结束事件：打印质量门禁统计摘要"""
    stats = environment.stats.total
    # 分隔线日志
    logger.info(f"{LogIcon.ACTION} 🏁 [自定义接口压测] 压测执行完毕，指标汇总统计：")
    logger.info(f"{LogIcon.ACTION} 📊 总请求数: {stats.num_requests}")
    logger.error(f"{LogIcon.FAIL} 失败请求数: {stats.num_failures}")
    failure_rate = (stats.num_failures / stats.num_requests * 100) if stats.num_requests > 0 else 0.0
    logger.error(f"{LogIcon.FAIL} 📉 失败率: {failure_rate:.2f}%")
    logger.info(f"{LogIcon.SETUP} 平均响应时间: {stats.avg_response_time:.2f} ms")
    logger.info(f"{LogIcon.SETUP} 中位数 (P50): {stats.median_response_time} ms")
    logger.info(f"{LogIcon.SETUP} 95% 分位数 (P95): {stats.get_response_time_percentile(0.95)} ms")
    logger.info(f"{LogIcon.SETUP} 99% 分位数 (P99): {stats.get_response_time_percentile(0.99)} ms")
    logger.info(f"{LogIcon.SETUP} 当前吞吐量 (RPS): {stats.current_rps:.2f}")
    # 分隔线日志

