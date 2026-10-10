import os
import sys
import json
import asyncio
import subprocess
import zipfile
import urllib.request
from typing import Dict, Any, List, Callable, Optional

from .paths import PROJECT_ROOT, REPORTS_DIR, ALLURE_CLI_DIR, TEMP_COLLECT_SCRIPT, TASK_DEBUG_LOG

# 并发任务状态池
# active_tasks 的结构为：
# {
#     "task_id": {
#         "status": "running" | "finished" | "idle",
#         "current_test": "test_node_id",
#         "exit_code": int | None,
#         "log_buffer": List[str],
#         "process": asyncio.subprocess.Process | None,
#         "listeners": List[Callable[[str], None]]
#     }
# }
active_tasks: Dict[str, Dict[str, Any]] = {}
tasks_lock = asyncio.Lock()

def write_task_debug_log(message: str):
    try:
        with open(TASK_DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"写入 debug 日志失败: {e}")

def ensure_allure_cli() -> Optional[str]:
    """检测并确保本地环境存在 Allure 命令行工具，如果缺失则在后台自动从远程下载、解压并配置环境变量"""
    allure_dir = ALLURE_CLI_DIR
    allure_bat = os.path.join(ALLURE_CLI_DIR, "bin", "allure.bat")
    
    if os.path.exists(allure_bat):
        return allure_bat
        
    print("\n[Web Console] 检测到未安装 Allure CLI，正在自动下载 (20MB)...")
    url = "https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.27.0/allure-commandline-2.27.0.zip"
    zip_path = os.path.join(PROJECT_ROOT, "allure.zip")
    
    try:
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(PROJECT_ROOT)
        
        extracted_dir = os.path.join(PROJECT_ROOT, "allure-2.27.0")
        if os.path.exists(extracted_dir):
            if os.path.exists(allure_dir):
                import shutil
                shutil.rmtree(allure_dir, ignore_errors=True)
            os.rename(extracted_dir, allure_dir)
            
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        print("[Web Console] Allure CLI 下载并配置成功！")
        return allure_bat
    except Exception as e:
        print(f"[Web Console] Allure 下载失败: {e}", file=sys.stderr)
        return None

async def broadcast_log(task_id: str, message: str):
    """向当前任务的所有 SSE 客户端分发日志"""
    async with tasks_lock:
        if task_id in active_tasks:
            task_info = active_tasks[task_id]
            task_info["log_buffer"].append(message)
            # 复制一份以防遍历时被修改
            active_listeners = list(task_info["listeners"])
            for listener in active_listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(message)
                    else:
                        listener(message)
                except Exception:
                    if listener in task_info["listeners"]:
                        task_info["listeners"].remove(listener)

def auto_detect_system_java_home() -> Optional[str]:
    """
    通过系统标准环境变量 JAVA_HOME 与 cmd 命令 (where java) 解析 Java 根目录。
    找不到直接返回 None，不再进行任何磁盘扫描与注册表查询。
    """
    try:
        from desktop_app.core.path_resolver import SmartPathResolver
        return SmartPathResolver.discover_java_home()
    except Exception:
        home = os.environ.get("JAVA_HOME", "").strip()
        if home and os.path.isdir(home):
            return home
        import shutil
        which_java = shutil.which("java")
        if which_java:
            real_java = os.path.realpath(which_java)
            cand = os.path.dirname(os.path.dirname(real_java))
            if os.path.isdir(cand):
                return cand
        return None

def get_valid_java_env() -> dict:
    """
    智能检测并动态注入当前电脑真实的 Java 环境，保证 Allure CLI 跨机器无缝运行。
    """
    env = os.environ.copy()
    detected_home = auto_detect_system_java_home()
    if detected_home:
        env["JAVA_HOME"] = detected_home
        os.environ["JAVA_HOME"] = detected_home
        write_task_debug_log(f"[Java自适应] 成功动态定位电脑 Java 根目录: {detected_home}")
    return env

def generate_fallback_report(task_id: str, exit_code: Optional[int] = None, extra_err: str = ""):
    """
    当测试发生异常或 Allure 未产出结果数据时，自动生成美观规范的轻量 HTML 诊断报告，防止前端 404。
    """
    html_dir = os.path.join(REPORTS_DIR, f"html_{task_id}")
    os.makedirs(html_dir, exist_ok=True)
    html_path = os.path.join(html_dir, "index.html")
    
    recent_logs = ""
    task_info = active_tasks.get(task_id)
    if task_info and task_info.get("log_buffer"):
        recent_logs = "".join(task_info["log_buffer"][-150:])
    if extra_err:
        recent_logs = f"{extra_err}\n\n{recent_logs}"
    
    safe_logs = (recent_logs or "（暂无详细控制台日志）").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    status_badge = f"测试执行失败 (退出码: {exit_code})" if (exit_code is not None and exit_code != 0) else "测试执行异常中断"
    badge_color = "#e11d48" if (exit_code != 0) else "#059669"
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试执行诊断与日志报告 - {task_id}</title>
    <style>
        body {{
            margin: 0;
            padding: 24px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
        }}
        .report-card {{
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            padding: 24px;
            max-width: 1200px;
            margin: 0 auto;
            border: 1px solid #e2e8f0;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 16px;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 20px;
            font-weight: 600;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            color: #ffffff;
            background-color: {badge_color};
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
            background: #f8fafc;
            padding: 16px;
            border-radius: 8px;
        }}
        .meta-item {{
            font-size: 13px;
        }}
        .meta-label {{
            color: #64748b;
            margin-bottom: 4px;
        }}
        .meta-val {{
            font-weight: 600;
            color: #334155;
            font-family: monospace;
        }}
        .terminal-box {{
            background: #0f172a;
            color: #f8fafc;
            border-radius: 8px;
            padding: 16px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 13px;
            line-height: 1.6;
            max-height: 550px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        .tips {{
            margin-top: 16px;
            padding: 12px 16px;
            background: #fffbeb;
            border: 1px solid #fef3c7;
            border-radius: 6px;
            color: #92400e;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <div class="header">
            <div class="title">
                <span>📊 测试执行诊断与异常分析报告</span>
            </div>
            <span class="badge">{status_badge}</span>
        </div>
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">任务编号 (Task ID)</div>
                <div class="meta-val">{task_id}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">退出代码 (Exit Code)</div>
                <div class="meta-val">{exit_code}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">诊断分析</div>
                <div class="meta-val">{'用例断言失败 / 运行时异常' if exit_code != 0 else '正常结束'}</div>
            </div>
        </div>
        <div class="title" style="font-size: 16px; margin-bottom: 12px;">🖥️ 执行日志与调用堆栈 Traceback</div>
        <div class="terminal-box">{safe_logs}</div>
        <div class="tips">
            💡 <strong>架构师提示：</strong>本任务执行过程中由于失败或异常中断，系统已自动捕获并汇总终端全量日志与 Traceback 供诊断定位。
        </div>
    </div>
</body>
</html>"""
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        write_task_debug_log(f"[Fallback Report] 已成功写入兜底诊断报告: {html_path}")
    except Exception as e:
        write_task_debug_log(f"[Fallback Report] 写入兜底报告失败: {e}")

async def run_allure_generator(task_id: str, exit_code: Optional[int] = None):
    """子进程结束后，异步启动 Allure CLI 生成对应的可视化 HTML 测试报告；若失败则自动生成诊断兜底报告"""
    try:
        allure_bat = ensure_allure_cli()
        tmp_dir = os.path.join(REPORTS_DIR, f"tmp_{task_id}")
        html_dir = os.path.join(REPORTS_DIR, f"html_{task_id}")
        html_path = os.path.join(html_dir, "index.html")

        # 检查是否有 allure 产生的测试结果文件
        has_results = os.path.exists(tmp_dir) and any(
            f.endswith("-result.json") or f.endswith("-container.json") or f.endswith(".json")
            for f in os.listdir(tmp_dir)
        )

        if allure_bat and has_results:
            await broadcast_log(task_id, f"\n[Web Console] 正在生成任务 {task_id} 的 Allure 报告，请稍候...\n")
            target_env = get_valid_java_env()
            
            def run_allure():
                res = subprocess.run(
                    [allure_bat, "generate", tmp_dir, "-o", html_dir, "--clean"],
                    capture_output=True,
                    text=True,
                    shell=True,
                    env=target_env,
                    cwd=PROJECT_ROOT
                )
                write_task_debug_log(f"[run_allure] code={res.returncode}, out={res.stdout}, err={res.stderr}")
                return res.returncode, res.stdout, res.stderr

            ret_code, out_str, err_str = await asyncio.to_thread(run_allure)
            
            if ret_code == 0 and os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    html_c = f.read()
                
                script = """<script>
                    window.localStorage.setItem('allure2Settings', '{"language":"zh"}');
                    window.addEventListener("message", function(e) {
                        if(e.data === 'role:business') { document.body.classList.add('role-business'); }
                        else if(e.data === 'role:tech') { document.body.classList.remove('role-business'); }
                    });
                    </script>
                    <style>
                    body.role-business .side-nav__item:has([href="#suites"]),
                    body.role-business .side-nav__item:has([href="#packages"]),
                    body.role-business .side-nav__item:has([href="#timeline"]),
                    body.role-business [href="#suites"],
                    body.role-business [href="#packages"],
                    body.role-business [href="#timeline"] { display: none !important; }
                    </style>"""
                if "role-business" not in html_c:
                    html_c = html_c.replace("<head>", f"<head>{script}")
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_c)
                        
                await broadcast_log(task_id, f"\n[Web Console] ✨ 任务 {task_id} 的 Allure 报告生成完毕！\n")
                return
            else:
                write_task_debug_log(f"[run_allure] Allure CLI 生成返回码异常 ({ret_code})，转入生成诊断兜底报告。err={err_str}")
        
        await asyncio.to_thread(generate_fallback_report, task_id, exit_code)
        await broadcast_log(task_id, f"\n[Web Console] ✨ 任务 {task_id} 的测试执行与异常诊断报告生成完毕！\n")

    except Exception as e:
        write_task_debug_log(f"[run_allure_generator] 异常: {e}")
        try:
            await asyncio.to_thread(generate_fallback_report, task_id, exit_code, f"生成报告时发生内部异常: {e}")
        except Exception:
            pass
        await broadcast_log(task_id, f"\n[Web Console] ⚠️ 生成测试报告完成（已启用异常日志诊断兜底）\n")

async def read_stream_and_broadcast(task_id: str, stream: asyncio.StreamReader):
    """从子进程的输出流中读取每一行并广播"""
    while True:
        line = await stream.readline()
        if not line:
            break
        try:
            decoded_line = line.decode('utf-8')
        except UnicodeDecodeError:
            decoded_line = line.decode('gbk', errors='replace')
        await broadcast_log(task_id, decoded_line)

async def start_pytest_task(
    task_id: str,
    nodeid: str,
    param_index: Optional[int] = None,
    remote_appium: Optional[str] = None,
    remote_appium2: Optional[str] = None,
    remote_udid: Optional[str] = None,
    remote_udid2: Optional[str] = None,
    debug_mode: bool = False,
    private_chat_name: Optional[str] = None,
    group_chat_name: Optional[str] = None,
    web_receipt_data: Optional[str] = None,
    env_name: Optional[str] = None
) -> tuple[bool, str]:
    """构建并发起异步的 Pytest 子进程执行特定的测试节点 (nodeid)"""
    async with tasks_lock:
        if task_id in active_tasks:
            # 清理历史的日志和进程
            active_tasks[task_id]["status"] = "running"
            active_tasks[task_id]["current_test"] = nodeid
            active_tasks[task_id]["exit_code"] = None
            active_tasks[task_id]["log_buffer"] = []
            active_tasks[task_id]["process"] = None
        else:
            active_tasks[task_id] = {
                "process": None,
                "log_buffer": [],
                "status": "running",
                "current_test": nodeid,
                "exit_code": None,
                "listeners": []
            }

    tmp_dir = os.path.join(REPORTS_DIR, f"tmp_{task_id}")
    if os.path.exists(tmp_dir):
        import shutil
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass

    # 处理动态 pytest 参数索引定位
    nodeid_to_run = nodeid
    if "[" in nodeid and "]" in nodeid:
        import re
        safe_nodeid = re.sub(r'\[.*?\]$', '', nodeid)
        if param_index is not None:
            collect_cmd = [sys.executable, TEMP_COLLECT_SCRIPT, safe_nodeid]
            try:
                # 采用 to_thread + subprocess.run 收集用例，显式指定 cwd 为项目根目录
                def run_collect():
                    return subprocess.run(
                        collect_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        cwd=PROJECT_ROOT
                    )
                res = await asyncio.to_thread(run_collect)
                raw_out = res.stdout
                try:
                    out = raw_out.decode('utf-8')
                except UnicodeDecodeError:
                    out = raw_out.decode('gbk', errors='ignore')
                
                real_nodes = []
                if "JSON_START" in out and "JSON_END" in out:
                    json_str = out.split("JSON_START")[1].split("JSON_END")[0].strip()
                    real_nodes = json.loads(json_str)
                if 0 <= param_index < len(real_nodes):
                    nodeid_to_run = real_nodes[param_index]
                else:
                    nodeid_to_run = safe_nodeid
            except Exception:
                nodeid_to_run = safe_nodeid

    # 组装命令参数，添加 -u 强制 Python 无缓冲运行，以确保输出流即时性
    cmd = [sys.executable, "-u", "-m", "pytest", nodeid_to_run, "-vs", "--color=yes", "-p", "web_platform.backend.pytest_status_plugin", f"--alluredir={tmp_dir}"]
    if env_name:
        cmd.extend(["--env", env_name])
    if debug_mode:
        cmd.append("--pdb")

    # 配置进程环境变量，强制无缓冲输出
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    
    if remote_appium:
        env["REMOTE_APPIUM_URL"] = remote_appium
    if remote_appium2:
        env["REMOTE_APPIUM_URL2"] = remote_appium2
    if remote_udid:
        env["REMOTE_UDID"] = remote_udid
    if remote_udid2:
        env["REMOTE_UDID2"] = remote_udid2
    if env_name:
        env["ENV"] = env_name
        env["TEST_ENV"] = env_name
    if debug_mode:
        env["DEBUG_MODE"] = "1"
    if private_chat_name:
        env["PRIVATE_CHAT_NAME"] = private_chat_name
    if group_chat_name:
        env["GROUP_CHAT_NAME"] = group_chat_name
    if web_receipt_data:
        env["WEB_RECEIPT_DATA"] = web_receipt_data

    try:
        # 启动时清空或新建 task_debug.log 文件
        try:
            with open(TASK_DEBUG_LOG, "w", encoding="utf-8") as f:
                f.write(f"=== 任务启动: {task_id} ===\n")
        except Exception:
            pass
            
        write_task_debug_log(f"[Web Console] 准备拉起 Pytest 进程，命令: {cmd}")
        # 改用同步的 subprocess.Popen 并开启 bufsize=0 且绑定 cwd=PROJECT_ROOT，保证工作目录与流的无缓冲实时写入
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            env=env,
            cwd=PROJECT_ROOT
        )
        write_task_debug_log(f"[Web Console] Pytest 进程拉起成功，PID: {proc.pid}")
        
        async with tasks_lock:
            if task_id in active_tasks:
                active_tasks[task_id]["process"] = proc

        # 启动后台协程，以 to_thread 在多线程下读取输出并驱动生命周期
        asyncio.create_task(run_task_lifecycle(task_id, proc))
        write_task_debug_log("[Web Console] 后台生命周期协程已触发创建")
        return True, "测试任务已成功启动"
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        write_task_debug_log(f"[Web Console] 启动异常:\n{err_msg}")
        async with tasks_lock:
            if task_id in active_tasks:
                active_tasks[task_id]["status"] = "idle"
        return False, f"测试进程拉起失败:\n{err_msg}"

async def run_task_lifecycle(task_id: str, proc: subprocess.Popen):
    """管理测试任务的生命周期：在后台线程中读取日志、等待结束、触发 Allure 生成"""
    # 采用 asyncio.Queue 作为纯异步事件队列，用 loop.call_soon_threadsafe 实现极速且无锁的跨线程入队
    loop = asyncio.get_running_loop()
    async_queue = asyncio.Queue()
    write_task_debug_log(f"[Web Console] 开始任务 {task_id} 的生命周期监听流程")
    
    def read_to_queue():
        # 同步读取流并塞入队列，避免在线程中直接操作协程
        write_task_debug_log("[read_to_queue] 线程读取开始...")
        for line in iter(proc.stdout.readline, b''):
            try:
                decoded = line.decode('utf-8')
            except UnicodeDecodeError:
                decoded = line.decode('gbk', errors='replace')
            # 记录每一行输出到调试日志
            write_task_debug_log(f"[Pytest Process Out] {decoded.strip()}")
            # 跨线程安全地将数据放入异步队列
            loop.call_soon_threadsafe(async_queue.put_nowait, decoded)
        proc.stdout.close()
        write_task_debug_log("[read_to_queue] 线程读取结束，放置 None 哨兵")
        loop.call_soon_threadsafe(async_queue.put_nowait, None) # 放置结束标识

    async def consume_queue():
        # 纯异步非阻塞消费队列并分发广播，不占用线程池资源
        write_task_debug_log("[consume_queue] 异步消费协程启动...")
        while True:
            line = await async_queue.get()
            if line is None:
                write_task_debug_log("[consume_queue] 收到 None 哨兵，退出消费循环")
                break
            # 广播并写入日志
            write_task_debug_log(f"[consume_queue] 消费并准备广播: {line.strip()}")
            await broadcast_log(task_id, line)

    try:
        if proc.stdout:
            # 生产者与消费者并发进行
            write_task_debug_log("[run_task_lifecycle] 启动 gather 并发监听")
            await asyncio.gather(
                asyncio.to_thread(read_to_queue),
                consume_queue()
            )
        
        write_task_debug_log("[run_task_lifecycle] gather 结束，等待子进程退出状态...")
        exit_code = await asyncio.to_thread(proc.wait)
        write_task_debug_log(f"[run_task_lifecycle] 子进程已退出，退出码: {exit_code}")
        await broadcast_log(task_id, f"\n[Web Console] 测试进程已退出，退出码: {exit_code}\n")
        
        # 触发 Allure 报告生成
        write_task_debug_log("[run_task_lifecycle] 准备触发 Allure 生成")
        await run_allure_generator(task_id, exit_code)
        write_task_debug_log("[run_task_lifecycle] Allure 报告生成完毕")
        
        async with tasks_lock:
            if task_id in active_tasks:
                active_tasks[task_id]["status"] = "finished"
                active_tasks[task_id]["exit_code"] = exit_code
                active_tasks[task_id]["process"] = None
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        await broadcast_log(task_id, f"\n[Web Console] 任务执行时遭遇非预期异常:\n{err_msg}\n")
        async with tasks_lock:
            if task_id in active_tasks:
                active_tasks[task_id]["status"] = "finished"
                active_tasks[task_id]["process"] = None
    finally:
        # 清理超期完成的任务
        async with tasks_lock:
            finished = [tid for tid, info in active_tasks.items() if info["status"] == "finished"]
            if len(finished) > 50:
                for tid in finished[:len(finished)-50]:
                    active_tasks.pop(tid, None)

async def terminate_pytest_task(task_id: str) -> tuple[bool, str]:
    """强行终止当前正在运行的测试任务及其所有子孙进程"""
    async with tasks_lock:
        task_info = active_tasks.get(task_id)
        if not task_info or not task_info["process"]:
            return False, "当前无正在运行的该测试任务"
        
        proc = task_info["process"]
        try:
            pid = proc.pid
            if os.name == 'nt':
                # Windows 使用 taskkill 强行终止进程树
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Unix/Mac 强行挂起进程树
                proc.terminate()
            
            task_info["status"] = "finished"
            task_info["exit_code"] = -9
            task_info["process"] = None
            return True, "测试任务已手动强行终止"
        except Exception as e:
            return False, f"终止任务失败: {e}"
