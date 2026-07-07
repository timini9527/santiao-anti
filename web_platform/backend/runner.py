import os
import sys
import json
import asyncio
import subprocess
import zipfile
import urllib.request
from typing import Dict, Any, List, Callable, Optional

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
    log_file = os.path.join(os.getcwd(), "web_platform", "backend", "task_debug.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"写入 debug 日志失败: {e}")

def ensure_allure_cli() -> Optional[str]:
    """检测并确保本地环境存在 Allure 命令行工具，如果缺失则在后台自动从远程下载、解压并配置环境变量"""
    allure_dir = os.path.join(os.getcwd(), "allure-cli")
    allure_bat = os.path.join(allure_dir, "bin", "allure.bat")
    
    if os.path.exists(allure_bat):
        return allure_bat
        
    print("\n[Web Console] 检测到未安装 Allure CLI，正在自动下载 (20MB)...")
    url = "https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.27.0/allure-commandline-2.27.0.zip"
    zip_path = os.path.join(os.getcwd(), "allure.zip")
    
    try:
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.getcwd())
        
        extracted_dir = os.path.join(os.getcwd(), "allure-2.27.0")
        if os.path.exists(extracted_dir):
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

async def run_allure_generator(task_id: str):
    """子进程结束后，异步启动 Allure CLI 生成对应的可视化 HTML 测试报告"""
    try:
        allure_bat = ensure_allure_cli()
        if allure_bat:
            await broadcast_log(task_id, f"\n[Web Console] 正在生成任务 {task_id} 的 Allure 报告，请稍候...\n")
            tmp_dir = os.path.join("reports", f"tmp_{task_id}")
            html_dir = os.path.join("reports", f"html_{task_id}")
            
            # 使用 subprocess.Popen 并在 to_thread 中等待，避开 asyncio loop 限制
            def run_allure():
                p = subprocess.Popen(
                    [allure_bat, "generate", tmp_dir, "-o", html_dir, "--clean"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=True
                )
                return p.wait()
            await asyncio.to_thread(run_allure)
            
            # 自动注入中文语言配置，使其默认以中文展示并设定业务屏蔽
            html_path = os.path.join(html_dir, "index.html")
            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
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
                if "role-business" not in content:
                    content = content.replace("<head>", f"<head>{script}")
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(content)
                        
            await broadcast_log(task_id, f"\n[Web Console] ✨ 任务 {task_id} 的 Allure 报告生成完毕！\n")
        else:
            await broadcast_log(task_id, "\n[Web Console] ⚠️ Allure 引擎配置失败，无法生成报告。\n")
    except Exception as e:
        await broadcast_log(task_id, f"\n[Web Console] ⚠️ 生成 Allure 报告时出错: {e}\n")

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

    tmp_dir = os.path.join("reports", f"tmp_{task_id}")
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
            collect_cmd = [sys.executable, "templates/temp_collect.py", safe_nodeid]
            try:
                # 采用 to_thread + subprocess.run 收集用例，绕过 Windows 平台下 selector 循环的 create_subprocess 限制
                def run_collect():
                    return subprocess.run(
                        collect_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT
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
            with open(os.path.join(os.getcwd(), "web_platform", "backend", "task_debug.log"), "w", encoding="utf-8") as f:
                f.write(f"=== 任务启动: {task_id} ===\n")
        except Exception:
            pass
            
        write_task_debug_log(f"[Web Console] 准备拉起 Pytest 进程，命令: {cmd}")
        # 改用同步的 subprocess.Popen 并开启 bufsize=0 彻底消除 NotImplementedError 且保证流的无缓冲实时写入
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            env=env
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
        await run_allure_generator(task_id)
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
