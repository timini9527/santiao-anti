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
from .devices import detect_appium_status, detect_connected_devices, start_appium_server
from .runner import start_pytest_task, terminate_pytest_task, active_tasks, tasks_lock

app = FastAPI(title="IM 自动化测试控制台 REST API")

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

# ==================== REST API 接口 ====================

@app.get("/api/tests")
async def api_get_tests():
    """获取所有解析到的用例树"""
    catalog = collect_all_tests("tests")
    return catalog

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
async def api_detect_appium():
    """探测本机 Appium 服务状态"""
    url = detect_appium_status()
    return {"success": True, "appium": url}

@app.post("/api/detect_udid")
async def api_detect_udid():
    """探测连接的手机 UDID 标识"""
    devices = detect_connected_devices()
    udid = devices[0] if devices else ""
    return {"success": True, "udid": udid, "devices": devices}

@app.post("/api/start_appium")
async def api_start_appium(params: StartAppiumParams):
    """自动调起服务端的 Appium"""
    success = start_appium_server(params.os)
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
                    log_data = await asyncio.wait_for(log_queue.get(), timeout=2.0)
                    yield {"data": json.dumps(log_data)}
                except asyncio.TimeoutError:
                    # 发送空心跳包
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
        
    file_path = os.path.join("reports", f"html_{task_id}", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
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
    
    raise HTTPException(status_code=404, detail="测试报告资源未找到，可能测试尚未运行结束")

# ==================== 静态网页托管 ====================

# 先挂载前端静态文件目录
static_dir = os.path.join("web_platform", "backend", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    def index_fallback():
        return HTMLResponse("<h3>未找到 Web 端前端静态资源文件，请确认 web_platform/backend/static 存在。</h3>")
