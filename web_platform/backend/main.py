import os
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from sse_starlette.sse import EventSourceResponse

from .collector import collect_all_tests
from .devices import detect_appium_status, detect_connected_devices, detect_device_details, start_appium_server, get_configured_devices, get_local_ip
from .runner import start_pytest_task, terminate_pytest_task, active_tasks, tasks_lock
from .paths import PROJECT_ROOT, REPORTS_DIR, TESTS_DIR, STATIC_DIR

app = FastAPI(title="IM 自动化测试控制台 REST API")

# 跨域资源共享配置
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义数据传输模型 (Pydantic Validation)
class RunParams(BaseModel):
    task_id: str
    nodeid: str
    param_index: Optional[int] = None
    remote_appium: Optional[str] = None
    remote_appium2: Optional[str] = None
    remote_udid: Optional[str] = None
    remote_udid2: Optional[str] = None
    debug_mode: Optional[bool] = False
    private_chat_name: Optional[str] = None
    group_chat_name: Optional[str] = None
    web_receipt_data: Optional[str] = None
    env: Optional[str] = None

class StopParams(BaseModel):
    task_id: str

class StartAppiumParams(BaseModel):
    os: Optional[str] = "windows"
    port: Optional[int] = 4723

class DetectAppiumParams(BaseModel):
    port: Optional[int] = 4723

# ==================== REST API 接口 ====================

# 用例树与真实用例统计全局缓存
_cases_summary_cache = None

def _calculate_cases_summary(catalog: list) -> dict:
    func_count = 0
    total_cases = 0
    for file_obj in catalog:
        for cls in file_obj.get("classes", []):
            for test in cls.get("tests", []):
                func_count += 1
                params = test.get("params", [])
                total_cases += len(params) if params else 1
        for test in file_obj.get("tests", []):
            func_count += 1
            params = test.get("params", [])
            total_cases += len(params) if params else 1

    return {
        "total_cases": total_cases,
        "total_functions": func_count
    }

@app.get("/api/tests")
async def api_get_tests():
    """获取所有解析到的用例树并更新统计缓存"""
    global _cases_summary_cache
    catalog = collect_all_tests(TESTS_DIR)
    _cases_summary_cache = _calculate_cases_summary(catalog)
    return catalog

@app.get("/api/overview")
async def api_get_overview():
    """获取多端平台全局概览统计（真实展开参数化用例数，兼具毫秒级缓存响应）"""
    global _cases_summary_cache
    if not _cases_summary_cache:
        catalog = collect_all_tests("tests")
        _cases_summary_cache = _calculate_cases_summary(catalog)
        
    summary = _cases_summary_cache

    def _compute_devices():
        devices = detect_connected_devices()
        reports_count = 0
        if os.path.exists(REPORTS_DIR):
            reports_count = len([d for d in os.listdir(REPORTS_DIR) if d.startswith("html_task_")])

        return {
            "success": True,
            "total_cases": summary["total_cases"],
            "total_functions": summary["total_functions"],
            "connected_devices": len(devices),
            "device_list": devices,
            "history_reports": reports_count,
            "appium_port_4723": bool(detect_appium_status(4723)),
            "appium_port_4724": bool(detect_appium_status(4724))
        }
    
    return await asyncio.to_thread(_compute_devices)

def calculate_quality_gate_metrics() -> dict:
    """
    全自动、动态计算质量门禁三大核心指标：
    1. 自动化覆盖率: 基于工程扫描的真实用例数与基准功能矩阵动态计算；
    2. 冒烟测试通过率: 遍历并解析所有已归档 Allure 报告统计 passed / total；
    3. Flaky Test 占比: 解析重试趋势统计 retry / total。
    """
    global _cases_summary_cache
    if not _cases_summary_cache:
        catalog = collect_all_tests(TESTS_DIR)
        _cases_summary_cache = _calculate_cases_summary(catalog)
    
    total_cases = _cases_summary_cache.get("total_cases", 0)
    # 对标类微信 IM 完整自动化业务矩阵规划基线（三端功能 + 协议 + 弱网 + 异常共 1600 场景点）
    baseline_cases = 1600.0
    coverage_rate = round(min(100.0, (total_cases / baseline_cases) * 100), 1) if baseline_cases > 0 else 0.0

    total_executed = 0
    total_passed = 0
    total_failed = 0
    total_retried = 0

    if os.path.exists(REPORTS_DIR):
        for item in os.listdir(REPORTS_DIR):
            if item.startswith("html_task_"):
                summary_file = os.path.join(REPORTS_DIR, item, "widgets", "summary.json")
                if os.path.exists(summary_file):
                    try:
                        with open(summary_file, "r", encoding="utf-8") as f:
                            s_data = json.load(f)
                            stat = s_data.get("statistic", {})
                            p = stat.get("passed", 0)
                            f_cnt = stat.get("failed", 0) + stat.get("broken", 0)
                            tot = stat.get("total", 0)
                            total_passed += p
                            total_failed += f_cnt
                            total_executed += tot
                    except Exception:
                        pass
                
                retry_file = os.path.join(REPORTS_DIR, item, "widgets", "retry-trend.json")
                if os.path.exists(retry_file):
                    try:
                        with open(retry_file, "r", encoding="utf-8") as f:
                            r_data = json.load(f)
                            if isinstance(r_data, list) and len(r_data) > 0:
                                retry_cnt = r_data[0].get("data", {}).get("retry", 0)
                                total_retried += retry_cnt
                    except Exception:
                        pass

    # 冒烟测试通过率 (若无执行记录则默认 100.0%)
    if total_executed > 0:
        smoke_pass_rate = round((total_passed / total_executed) * 100, 1)
        flaky_rate = round((total_retried / total_executed) * 100, 1)
    else:
        smoke_pass_rate = 100.0
        flaky_rate = 0.0

    return {
        "coverage_rate": coverage_rate,
        "coverage_target": 80.0,
        "coverage_is_passed": coverage_rate >= 80.0,
        "smoke_pass_rate": smoke_pass_rate,
        "smoke_target": 95.0,
        "smoke_is_passed": smoke_pass_rate >= 95.0,
        "flaky_rate": flaky_rate,
        "flaky_target": 2.0,
        "flaky_is_healthy": flaky_rate <= 2.0,
        "total_cases": total_cases,
        "total_executed": total_executed,
        "total_passed": total_passed,
        "total_failed": total_failed
    }

@app.get("/api/reports/metrics")
async def api_get_reports_metrics():
    """动态获取质量门禁核心指标"""
    metrics = await asyncio.to_thread(calculate_quality_gate_metrics)
    return {"success": True, "metrics": metrics}

@app.get("/api/reports/history")
async def api_get_reports_history():
    """获取所有历史执行生成的 Allure 报告列表及动态质量门禁指标"""
    history = []
    if os.path.exists(REPORTS_DIR):
        import datetime
        for item in sorted(os.listdir(REPORTS_DIR), reverse=True):
            if item.startswith("html_task_"):
                task_id = item.replace("html_", "")
                dir_path = os.path.join(REPORTS_DIR, item)
                index_path = os.path.join(dir_path, "index.html")
                if os.path.exists(index_path):
                    mtime = os.path.getmtime(index_path)
                    time_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    history.append({
                        "task_id": task_id,
                        "time": time_str,
                        "report_url": f"/allure/{task_id}/index.html",
                        "size": os.path.getsize(index_path)
                    })
    metrics = await asyncio.to_thread(calculate_quality_gate_metrics)
    return {"success": True, "history": history, "metrics": metrics}

@app.get("/api/status")
async def api_get_status(task_id: str):
    """获取指定任务的执行状态"""
    async with tasks_lock:
        task = active_tasks.get(task_id)
        if task:
            return {
                "status": task["status"],
                "current_test": task["current_test"],
                "exit_code": task["exit_code"]
            }
        return {
            "status": "idle",
            "current_test": None,
            "exit_code": None
        }

@app.post("/api/run")
async def api_run_test(params: RunParams):
    """启动自动化测试"""
    success, msg = await start_pytest_task(
        task_id=params.task_id,
        nodeid=params.nodeid,
        param_index=params.param_index,
        remote_appium=params.remote_appium,
        remote_appium2=params.remote_appium2,
        remote_udid=params.remote_udid,
        remote_udid2=params.remote_udid2,
        debug_mode=bool(params.debug_mode),
        private_chat_name=params.private_chat_name,
        group_chat_name=params.group_chat_name,
        web_receipt_data=params.web_receipt_data,
        env_name=params.env
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@app.post("/api/stop")
async def api_stop_test(params: StopParams):
    """手动终止正在进行的测试任务"""
    success, msg = await terminate_pytest_task(params.task_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@app.post("/api/detect_appium")
async def api_detect_appium(params: Optional[DetectAppiumParams] = None):
    """探测本机 Appium 服务状态及当前电脑真实有效局域网 IP"""
    port = params.port if params else 4723
    url = detect_appium_status(port)
    local_ip = get_local_ip()
    return {"success": True, "appium": url, "local_ip": local_ip, "port": port}

@app.post("/api/detect_udid")
async def api_detect_udid():
    """探测当前 USB 物理连接的手机真机与所有在线设备"""
    details = detect_device_details()
    real_devices = details["real_devices"]
    all_devices = details["all_devices"]
    default_sender = details["sender_default"]
    default_receiver = details["receiver_default"]

    # 优先识别真实 USB 物理连接的真机
    sender_detected = real_devices[0] if len(real_devices) > 0 else (all_devices[0] if len(all_devices) > 0 else None)
    receiver_detected = real_devices[1] if len(real_devices) > 1 else (all_devices[1] if len(all_devices) > 1 else None)

    return {
        "success": True,
        "udid": sender_detected or default_sender,
        "sender_udid": default_sender,
        "receiver_udid": default_receiver,
        "sender_detected": sender_detected,
        "receiver_detected": receiver_detected,
        "real_devices": real_devices,
        "emulator_devices": details["emulator_devices"],
        "all_devices": all_devices,
        "device_items": details["device_items"],
        "devices": details["legacy_devices"]
    }

@app.post("/api/start_appium")
async def api_start_appium(params: StartAppiumParams):
    """自动调起服务端的 Appium"""
    success = start_appium_server(params.os, params.port)
    if not success:
        raise HTTPException(status_code=500, detail="调起 Appium 失败")
    return {"success": True}

# ==================== SSE 实时日志流 ====================

@app.get("/api/logs/stream")
async def api_logs_stream(task_id: str, request: Request):
    """Server-Sent Events (SSE) 协议，实现日志的无缓冲非阻塞实时分发"""
    if not task_id:
        raise HTTPException(status_code=400, detail="Missing task_id")

    log_queue = asyncio.Queue()

    # 日志钩子监听器
    async def listener(msg: str):
        await log_queue.put(msg)

    async with tasks_lock:
        if task_id not in active_tasks:
            active_tasks[task_id] = {
                "process": None,
                "log_buffer": [],
                "status": "idle",
                "current_test": None,
                "exit_code": None,
                "listeners": []
            }
        task_info = active_tasks[task_id]
        
        # 将已有的历史日志先放入队列，避免前端刷新丢失
        for history_log in task_info["log_buffer"]:
            await log_queue.put(history_log)
            
        task_info["listeners"].append(listener)

    async def log_generator():
        try:
            while True:
                # 检查连接是否断开
                if await request.is_disconnected():
                    break
                try:
                    # 等待新日志产生，加入超时机制以维持连接心跳
                    log_data = await asyncio.wait_for(log_queue.get(), timeout=1.2)
                    yield {"data": json.dumps(log_data)}
                except asyncio.TimeoutError:
                    # 检查当前任务是否已进入 finished 状态并且日志队列已消费完毕
                    async with tasks_lock:
                        task = active_tasks.get(task_id)
                        if task and task.get("status") == "finished" and log_queue.empty():
                            # 下发结构化完成事件并优雅退出流
                            yield {
                                "event": "finished",
                                "data": json.dumps({
                                    "status": "finished",
                                    "exit_code": task.get("exit_code")
                                })
                            }
                            break
                    # 发送空心跳包维持连接
                    yield {"comment": "keep-alive"}
        finally:
            # 链接断开后彻底移除监听器，防内存泄漏
            async with tasks_lock:
                if task_id in active_tasks:
                    if listener in active_tasks[task_id]["listeners"]:
                        active_tasks[task_id]["listeners"].remove(listener)

    return EventSourceResponse(log_generator())

# ==================== Allure 静态报告路由分发 ====================

@app.get("/allure/{task_id}/{path:path}")
async def proxy_allure_report(task_id: str, path: str):
    """
    静态代理路由：智能加载每个 Task 隔离目录下的 Allure HTML 资源。
    例如访问 /allure/task_123/index.html -> 自动定位并读取 reports/html_task_123/index.html 并分发。
    """
    if not path or path == "/":
        path = "index.html"
        
    file_path = os.path.join(REPORTS_DIR, f"html_{task_id}", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # 如果是 index.html，动态注入视角切换核心脚本与 CSS 规则，确保即时生效
        if path == "index.html":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                injection = """<script>
(function() {
    try {
        window.localStorage.setItem('allure2Settings', JSON.stringify({ language: 'zh' }));
    } catch(e) {}

    function applyRole(role) {
        if (!role) return;
        try {
            window.localStorage.setItem('allure_active_role', role);
        } catch(e) {}
        
        var isBusiness = (role === 'business');
        if (isBusiness) {
            document.documentElement.classList.add('role-business');
            if (document.body) document.body.classList.add('role-business');
        } else {
            document.documentElement.classList.remove('role-business');
            if (document.body) document.body.classList.remove('role-business');
        }
    }

    var savedRole = 'business';
    try {
        savedRole = window.localStorage.getItem('allure_active_role') || 'business';
    } catch(e) {}
    applyRole(savedRole);

    window.addEventListener('DOMContentLoaded', function() {
        applyRole(savedRole);
    });

    window.addEventListener('message', function(event) {
        if (!event || !event.data) return;
        var msg = event.data;
        if (typeof msg === 'string') {
            if (msg.indexOf('role:') === 0) {
                applyRole(msg.split('role:')[1].trim());
            }
        } else if (typeof msg === 'object' && msg.role) {
            applyRole(msg.role);
        }
    });
})();
</script>
<style>
/* 精简视角模式：智能隐藏底层开发维度的 Suites(套件)、Packages(包)、Timeline(时间线) */
.role-business .side-nav__item:has([href*="suites"]),
.role-business .side-nav__item:has([href*="packages"]),
.role-business .side-nav__item:has([href*="timeline"]),
.role-business .side-nav__link[href*="suites"],
.role-business .side-nav__link[href*="packages"],
.role-business .side-nav__link[href*="timeline"],
.role-business li[data-tooltip*="Packages"],
.role-business li[data-tooltip*="Suites"],
.role-business li[data-tooltip*="Timeline"],
.role-business li[data-tooltip*="套件"],
.role-business li[data-tooltip*="包"],
.role-business li[data-tooltip*="时间线"] {
    display: none !important;
}
</style>
"""
                if "role-business" not in content:
                    content = content.replace("<head>", f"<head>{injection}")

                return HTMLResponse(content)
            except Exception:
                pass

        # 智能匹配 Content-Type，确保网页资源正常解析，防止 Allure 静态报错
        ext = path.split('.')[-1]
        media_types = {
            "html": "text/html",
            "css": "text/css",
            "js": "application/javascript",
            "svg": "image/svg+xml",
            "json": "application/json",
            "png": "image/png",
            "jpg": "image/jpeg"
        }
        media_type = media_types.get(ext, "application/octet-stream")
        return FileResponse(file_path, media_type=media_type)
    
    # 终极守护：如果请求的是 index.html 但由于任何偶发原因未找到，立即动态生成兜底诊断报告返回，彻底消除 404！
    if path == "index.html":
        from .runner import generate_fallback_report
        generate_fallback_report(task_id)
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="text/html")

    raise HTTPException(status_code=404, detail="测试报告资源未找到，可能测试尚未运行结束")

# ==================== 静态网页托管 ====================

# 动态挂载前端静态文件目录
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/")
    def index_fallback():
        return HTMLResponse("<h3>未找到 Web 端前端静态资源文件，请确认 static 目录存在。</h3>")
