import os
import sys
import ast
import json
import socket
import threading
import subprocess
import time
import re
import urllib.request
import importlib.util
import io
import contextlib
from types import SimpleNamespace
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 8000
AGENT_DIR = os.path.join(os.getcwd(), ".agents", "test-runner-agent")
AGENT_SCRIPT = os.path.join(AGENT_DIR, "test_agent_runner.py")
AGENT_PAGE = os.path.join(AGENT_DIR, "web_console.html")
_agent_module = None

# 任务并发管理系统数据结构
# active_tasks 的结构为：
# {
#     "task_id": {
#         "process": subprocess.Popen,
#         "log_buffer": [list_of_lines],
#         "status": "running" | "finished" | "idle",
#         "current_test": "test_node_id",
#         "exit_code": exit_code,
#         "listeners": [list_of_callbacks]
#     }
# }
active_tasks = {}
tasks_lock = threading.Lock()

def load_test_runner_agent():
    """加载独立测试执行 Agent 模块，供 Web Runner 复用其匹配与参数化选择逻辑。"""
    global _agent_module
    if _agent_module is not None:
        return _agent_module
    if not os.path.exists(AGENT_SCRIPT):
        raise FileNotFoundError(f"未找到测试执行 Agent 脚本: {AGENT_SCRIPT}")
    spec = importlib.util.spec_from_file_location("test_runner_agent", AGENT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _agent_module = module
    return module

def agent_entry_to_dict(entry):
    return {
        "file": entry.file,
        "class_name": entry.class_name,
        "test_name": entry.test_name,
        "display_name": entry.display_name,
        "params": entry.params,
        "markers": sorted(entry.markers),
        "nodeid": entry.nodeid,
    }

def resolve_agent_target(data):
    agent = load_test_runner_agent()
    query = (data.get("query") or "").strip()
    allow_destructive = bool(data.get("allow_destructive", False))
    case_value = data.get("case")
    case_index = int(case_value) if str(case_value or "").strip() else None
    param = (data.get("param") or "").strip()
    entries = agent.collect_tests()
    target, candidates, mode = agent.resolve_target(query, entries, allow_destructive)
    if mode == "ambiguous":
        return {
            "success": False,
            "reason": "ambiguous",
            "message": "匹配到多个候选，请选择更精确的用例。",
            "candidates": [agent_entry_to_dict(entry) for entry in candidates],
        }
    if not target:
        return {
            "success": False,
            "reason": "not_found",
            "message": "未匹配到测试目标。",
            "candidates": [],
        }
    destructive = agent.filter_destructive(candidates)
    if destructive and not allow_destructive:
        return {
            "success": False,
            "reason": "destructive",
            "message": "匹配目标包含 destructive 用例，默认不执行。",
            "candidates": [agent_entry_to_dict(entry) for entry in destructive],
        }
    args = SimpleNamespace(case=case_index, param=param)
    try:
        target = agent.select_param_case(target, args)
    except Exception as exc:
        return {
            "success": False,
            "reason": "case_error",
            "message": str(exc),
            "candidates": [agent_entry_to_dict(entry) for entry in candidates],
        }
    command_args = SimpleNamespace(
        allow_destructive=allow_destructive,
        env=(data.get("env") or "").strip(),
        allure_dir=(data.get("allure_dir") or "reports/allure-results"),
    )
    cmd = agent.build_pytest_command(target, command_args)
    return {
        "success": True,
        "mode": mode,
        "target": target,
        "command": agent.command_to_text(cmd),
        "candidates": [agent_entry_to_dict(entry) for entry in candidates],
    }

def get_host_ip():
    """获取本机局域网 IP (智能过滤虚拟机与代理网卡)"""
    try:
        hostname = socket.gethostname()
        _, _, ips = socket.gethostbyname_ex(hostname)
        valid_ips = []
        for ip in ips:
            # 过滤回环、APIPA 自动分配的无效 IP，以及通常作为网关/宿主机的 .1 结尾 IP
            if ip.startswith("127.") or ip.startswith("169.254.") or ip.endswith(".1"):
                continue
            valid_ips.append(ip)
        
        if valid_ips:
            # 优先返回 192.168 开头的常规家用/办公内网 IP
            for ip in valid_ips:
                if ip.startswith("192.168."):
                    return ip
            return valid_ips[-1]

        # 降级方案：如果没有选出合适的，再尝试直连探测
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

class TestCollector(ast.NodeVisitor):
    """使用 AST 静态解析 Python 文件中的测试类和测试函数"""
    
    def __init__(self):
        """初始化 AST 解析收集器，用于存放解析到的测试类和函数节点列表"""
        self.classes = []
        self.functions = []

    def _parse_parametrize(self, node):
        """从 AST 函数节点中，递归解析并提取 @pytest.mark.parametrize 携带的参数列表或自定义 ids"""
        params = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                func = dec.func
                is_param = False
                if isinstance(func, ast.Attribute) and func.attr == 'parametrize':
                    if isinstance(func.value, ast.Attribute) and func.value.attr == 'mark':
                        if hasattr(func.value.value, 'id') and func.value.value.id == 'pytest':
                            is_param = True
                
                if is_param and len(dec.args) >= 2:
                    # 1. 优先尝试从 keyword `ids` 中获取人为定义的中文描述
                    ids_values = []
                    for kw in dec.keywords:
                        if kw.arg == 'ids' and (isinstance(kw.value, ast.List) or isinstance(kw.value, ast.Tuple)):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant):
                                    ids_values.append(str(elt.value))
                    
                    if ids_values:
                        params.extend(ids_values)
                    else:
                        # 2. 如果没有 ids，则回退到解析实际传参的值
                        arg_values = dec.args[1]
                        if isinstance(arg_values, ast.List) or isinstance(arg_values, ast.Tuple):
                            for elt in arg_values.elts:
                                if isinstance(elt, ast.Constant): params.append(str(elt.value))
                                elif isinstance(elt, ast.Name): params.append(elt.id)
                                elif isinstance(elt, ast.Tuple) or isinstance(elt, ast.List):
                                    sub_vals = []
                                    for sub_elt in elt.elts:
                                        if isinstance(sub_elt, ast.Constant): sub_vals.append(str(sub_elt.value))
                                        elif isinstance(sub_elt, ast.Name): sub_vals.append(sub_elt.id)
                                        else: sub_vals.append("?")
                                    params.append("-".join(sub_vals))
                                else: params.append("?")
        return params

    def _process_func(self, node):
        """处理单个测试函数节点，提取 Allure 的 title 或 story 装饰器以及用例参数，组装成带有中文名称的数据字典"""
        params = self._parse_parametrize(node)
        
        title = ""
        story = ""
        # 1. 尝试提取 @allure.title() 与 @allure.story()
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and getattr(dec.func, 'value', None) and getattr(dec.func.value, 'id', '') == 'allure':
                attr = getattr(dec.func, 'attr', '')
                if attr == 'title' and dec.args and hasattr(dec.args[0], 'value'):
                    title = str(dec.args[0].value)
                elif attr == 'story' and dec.args and hasattr(dec.args[0], 'value'):
                    story = str(dec.args[0].value)
        
        # 优先以 @allure.title 展示，没有则以 @allure.story 展示
        name_desc = title or story
        
        # 2. 如果都没有，尝试提取 docstring 注释 (第一行)
        if not name_desc:
            doc = ast.get_docstring(node)
            if doc:
                name_desc = doc.strip().split('\n')[0].strip()
        
        display_name = f"{name_desc} ({node.name})" if name_desc else node.name
        
        return {"name": node.name, "display_name": display_name, "params": params}

    def visit_ClassDef(self, node):
        """访问类节点，若类名以 Test 开头，则遍历其内部所有以 test_ 开头的方法，并加入收集结果集"""
        if node.name.startswith("Test"):
            feature = ""
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and getattr(dec.func, 'value', None) and getattr(dec.func.value, 'id', '') == 'allure':
                    if getattr(dec.func, 'attr', '') == 'feature' and dec.args and hasattr(dec.args[0], 'value'):
                        feature = str(dec.args[0].value)
            
            if not feature:
                doc = ast.get_docstring(node)
                if doc:
                    feature = doc.strip().split('\n')[0].strip()
            
            display_name = f"{feature} ({node.name})" if feature else node.name
            
            class_tests = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    class_tests.append(self._process_func(item))
            self.classes.append({"name": node.name, "display_name": display_name, "tests": class_tests})
            return  # 修复Bug: 避免向下继续遍历内部的函数导致重复收集为独立的函数
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """访问独立函数节点，若函数名以 test_ 开头，则提取并加入收集结果集"""
        if node.name.startswith("test_"):
            self.functions.append(self._process_func(node))

def collect_all_tests(tests_dir="tests"):
    """递归遍历测试目录收集测试用例"""
    catalog = []
    if not os.path.exists(tests_dir):
        return catalog

    for root, dirs, files in os.walk(tests_dir):
        # 排除 pycache 等目录
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.pytest_cache')]
        for file in files:
            if (file.startswith("test_") or file.endswith("_test.py")) and file.endswith(".py"):
                filepath = os.path.join(root, file).replace("\\", "/")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=filepath)
                    collector = TestCollector()
                    collector.visit(tree)
                    
                    if collector.classes or collector.functions:
                        doc = ast.get_docstring(tree)
                        file_desc = ""
                        if doc:
                            lines = [l.strip() for l in doc.splitlines() if l.strip()]
                            if lines:
                                file_desc = lines[0]
                        if not file_desc and collector.classes:
                            first_cls = collector.classes[0]
                            if " (" in first_cls["display_name"]:
                                file_desc = first_cls["display_name"].split(" (")[0]
                            else:
                                file_desc = first_cls["display_name"]
                        if not file_desc and collector.functions:
                            first_func = collector.functions[0]
                            if " (" in first_func["display_name"]:
                                file_desc = first_func["display_name"].split(" (")[0]
                            else:
                                file_desc = first_func["display_name"]
                        
                        display_name = f"{file_desc} ({file})" if file_desc else file
                        catalog.append({
                            "file": filepath,
                            "display_name": display_name,
                            "classes": collector.classes,
                            "tests": collector.functions
                        })
                except Exception as e:
                    print(f"解析文件失败 {filepath}: {e}")
    # --- 动态合并真实的 Pytest 参数化 ID ---
    try:
        import subprocess, sys, json
        raw_out = subprocess.check_output([sys.executable, "templates/temp_collect.py"], stderr=subprocess.STDOUT)
        try:
            out = raw_out.decode('utf-8')
        except UnicodeDecodeError:
            out = raw_out.decode('gbk', errors='ignore')
            
        real_nodes = {}
        if "JSON_START" in out and "JSON_END" in out:
            json_str = out.split("JSON_START")[1].split("JSON_END")[0].strip()
            nodeids = json.loads(json_str)
            for nodeid in nodeids:
                if "[" in nodeid and nodeid.endswith("]"):
                    parent, param = nodeid.rsplit("[", 1)
                    param = param[:-1]
                    parent = parent.replace("\\", "/")
                    if parent not in real_nodes:
                        real_nodes[parent] = []
                    real_nodes[parent].append(param)
                
        for file_obj in catalog:
            file_path = file_obj["file"]
            for cls in file_obj.get("classes", []):
                for test in cls.get("tests", []):
                    parent_nodeid = f"{file_path}::{cls['name']}::{test['name']}"
                    if parent_nodeid in real_nodes:
                        test["params"] = real_nodes[parent_nodeid]
            for test in file_obj.get("tests", []):
                parent_nodeid = f"{file_path}::{test['name']}"
                if parent_nodeid in real_nodes:
                    test["params"] = real_nodes[parent_nodeid]
    except Exception as e:
        print(f"动态收集参数化用例失败: {e}")
        
    return catalog

def ensure_allure_cli():
    """检测并确保本地环境存在 Allure 命令行工具，如果缺失则在后台自动从远程下载、解压并配置环境变量"""
    import urllib.request
    import zipfile
    
    allure_dir = os.path.join(os.getcwd(), "allure-cli")
    allure_bat = os.path.join(allure_dir, "bin", "allure.bat")
    
    if os.path.exists(allure_bat):
        return allure_bat
        
    print("\n[Web Runner] 检测到未安装 Allure CLI，正在后台自动下载 (20MB)...")
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
            
        print("[Web Runner] Allure CLI 下载并配置成功！")
        return allure_bat
    except Exception as e:
        print(f"[Web Runner] Allure 下载失败: {e}")
        return None

def stream_process_output(task_id, proc):
    """
    工作线程：实时读取指定 task_id 的 pytest 测试子进程的标准输出流，并通过 SSE 将日志推送给网页客户端。
    在测试进程完全结束后，自动调用 allure 命令行生成该任务专属的可视化 HTML 报告。
    """
    global active_tasks
    exit_code = -1
    
    def broadcast(msg):
        with tasks_lock:
            if task_id in active_tasks:
                task_info = active_tasks[task_id]
                task_info["log_buffer"].append(msg)
                for listener in list(task_info["listeners"]):
                    try: listener(msg)
                    except:
                        if listener in task_info["listeners"]:
                            task_info["listeners"].remove(listener)

    try:
        # 逐行读取输出并推送到前端
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                decoded_line = line.decode('utf-8', errors='replace')
                broadcast(decoded_line)
                           
        exit_code = proc.wait()
        
        # 自动生成 Allure 报告
        try:
            allure_bat = ensure_allure_cli()
            if allure_bat:
                broadcast(f"\n[Web Runner] 正在生成任务 {task_id} 的 Allure 报告，请稍候...\n")
                tmp_dir = os.path.join("reports", f"tmp_{task_id}")
                html_dir = os.path.join("reports", f"html_{task_id}")
                # 隐藏命令行窗口静默执行
                subprocess.run([allure_bat, "generate", tmp_dir, "-o", html_dir, "--clean"], shell=True)
                
                # 自动注入中文语言配置，使其默认以中文展示
                html_path = os.path.join(html_dir, "index.html")
                if os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # 注入脚本，修改 localStorage 并注入权限沙盒控制
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
                            
                broadcast(f"\n[Web Runner] ✨ 任务 {task_id} 的 Allure 报告生成完毕！\n")
            else:
                broadcast("\n[Web Runner] ⚠️ Allure 引擎配置失败，无法生成报告。\n")
        except Exception as e:
            broadcast(f"\n[Web Runner] ⚠️ 生成 Allure 报告时出错: {e}\n")
    finally:
        with tasks_lock:
            if task_id in active_tasks:
                active_tasks[task_id]["status"] = "finished"
                active_tasks[task_id]["exit_code"] = exit_code
                active_tasks[task_id]["process"] = None
            
        broadcast(f"\n[Web Runner] 测试执行流程全部结束，退出码: {exit_code}\n")
        
        # 限制完成的任务缓存数量，防内存泄漏，仅保留最近 50 个已结束任务的内存数据
        with tasks_lock:
            finished_tasks = [tid for tid, info in active_tasks.items() if info["status"] == "finished"]
            if len(finished_tasks) > 50:
                for tid in finished_tasks[:len(finished_tasks)-50]:
                    active_tasks.pop(tid, None)

def run_pytest_node(task_id, nodeid, param_index=None, remote_appium=None, remote_udid=None, debug_mode=False, private_chat_name=None, group_chat_name=None, web_receipt_data=None, env_name=None):
    """构建并发起新的 Pytest 子进程执行特定的测试节点 (nodeid)"""
    global active_tasks
    
    # 设定当前任务为运行状态并更新/初始化其专属数据结构，必须保留已由 SSE 创建并挂载的 listeners 数组
    with tasks_lock:
        if task_id in active_tasks:
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
        
    # 区分专属临时文件夹，实现多任务并发的报告隔离
    tmp_dir = os.path.join("reports", f"tmp_{task_id}")
    if os.path.exists(tmp_dir):
        import shutil
        try: shutil.rmtree(tmp_dir)
        except: pass
        
    import re
    nodeid_to_run = nodeid
    if "[" in nodeid and "]" in nodeid:
        safe_nodeid = re.sub(r'\[.*?\]$', '', nodeid)
        if param_index is not None:
            # 动态获取底层的真实子用例 ID (以防静态解析拿不到真实名字)
            collect_cmd = [sys.executable, "templates/temp_collect.py", safe_nodeid]
            try:
                # 设定 5 秒超时时间，防止因未知导入阻塞导致主服务进程无限卡死
                raw_out = subprocess.check_output(collect_cmd, stderr=subprocess.STDOUT, timeout=5.0)
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
            except Exception as e:
                nodeid_to_run = safe_nodeid
        
    cmd = [sys.executable, "-m", "pytest", nodeid_to_run, "-vs", "--color=yes", f"--alluredir={tmp_dir}"]
    if env_name:
        cmd.extend(["--env", env_name])
    if debug_mode:
        cmd.append("--pdb")
        
    # 强制 Python 无缓冲输出，避免日志卡住
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    
    if remote_appium:
        env["REMOTE_APPIUM_URL"] = remote_appium
    if remote_udid:
        env["REMOTE_UDID"] = remote_udid
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
    
    # 启动子进程
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            env=env
        )
        with tasks_lock:
            if task_id in active_tasks:
                active_tasks[task_id]["process"] = proc
                
        # 启动工作线程读取输出
        t = threading.Thread(target=stream_process_output, args=(task_id, proc))
        t.daemon = True
        t.start()
        return True, "测试已启动"
    except Exception as e:
        with tasks_lock:
            if task_id in active_tasks:
                active_tasks[task_id]["status"] = "idle"
        return False, f"启动测试失败: {str(e)}"

class WebRunnerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """重写底层 HTTP 请求日志方法，静默前端发来的心跳与轮询请求，保持终端的清爽干净"""
        pass

    def do_GET(self):
        """处理 Web 控制台所有的 GET 请求：包含主页渲染、Allure 报告静态代理分发、用例解析数据分发及 SSE 日志流建立"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            else:
                html_content = "<h3>未找到 templates/index.html 模板文件</h3>"
            self.wfile.write(html_content.encode("utf-8"))

        elif path == "/agent":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if os.path.exists(AGENT_PAGE):
                with open(AGENT_PAGE, "r", encoding="utf-8") as f:
                    html_content = f.read()
            else:
                html_content = "<h3>未找到 .agents/test-runner-agent/web_console.html</h3>"
            self.wfile.write(html_content.encode("utf-8"))
            
        elif path.startswith("/allure/"):
            # 简单静态文件服务，根据 task_id 代理专属的 allure 测试报告
            rel_path = path.replace("/allure/", "", 1)
            parts = rel_path.split("/", 1)
            if len(parts) == 2:
                task_id, file_rel = parts
                file_path = os.path.join("reports", f"html_{task_id}", file_rel)
            elif len(parts) == 1 and parts[0]:
                task_id = parts[0]
                file_path = os.path.join("reports", f"html_{task_id}", "index.html")
            else:
                # 兜底访问默认全局报告
                file_path = os.path.join("reports", "html", rel_path)
                
            if file_path and os.path.isdir(file_path): 
                file_path = os.path.join(file_path, "index.html")
                
            if file_path and os.path.exists(file_path):
                self.send_response(200)
                ext = file_path.split('.')[-1]
                content_type = {"html": "text/html", "css": "text/css", "js": "application/javascript", "svg": "image/svg+xml", "json": "application/json"}.get(ext, "application/octet-stream")
                self.send_header("Content-Type", content_type)
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Report not generated yet for this task")
            
        elif path == "/api/tests":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            tests = collect_all_tests()
            self.wfile.write(json.dumps(tests, ensure_ascii=False).encode("utf-8"))
            
        elif path == "/api/status":
            query_params = parse_qs(parsed_url.query)
            task_id = query_params.get("task_id", [None])[0]
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            
            with tasks_lock:
                if task_id and task_id in active_tasks:
                    task_info = active_tasks[task_id]
                    res_data = {
                        "status": task_info["status"],
                        "current_test": task_info["current_test"],
                        "exit_code": task_info["exit_code"]
                    }
                else:
                    res_data = {
                        "status": "idle",
                        "current_test": None,
                        "exit_code": None
                    }
            self.wfile.write(json.dumps(res_data, ensure_ascii=False).encode("utf-8"))
            
        elif path == "/api/logs/stream":
            # Server-Sent Events (SSE) 协议，实现特定 task_id 的日志实时推送到特定浏览器客户端
            query_params = parse_qs(parsed_url.query)
            task_id = query_params.get("task_id", [None])[0]
            if not task_id:
                self.send_error(400, "Missing task_id")
                return
                
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            
            # 定义事件监听器并在 tasks_lock 保护下注册/拉取历史日志
            event_queue = []
            def listener(msg):
                event_queue.append(msg)
                
            with tasks_lock:
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
                # 发送历史日志
                for log in task_info["log_buffer"]:
                    try:
                        self.wfile.write(f"data: {json.dumps(log)}\n\n".encode("utf-8"))
                    except Exception:
                        pass
                try:
                    self.wfile.flush()
                except Exception:
                    pass
                # 挂载监听器以监听后续产生的日志
                task_info["listeners"].append(listener)
            
            try:
                while True:
                    if event_queue:
                        msg = event_queue.pop(0)
                        self.wfile.write(f"data: {json.dumps(msg)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    else:
                        # 保持连接活跃
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
                        threading.Event().wait(0.2)
            except Exception:
                with tasks_lock:
                    task_info = active_tasks.get(task_id)
                    if task_info and listener in task_info["listeners"]:
                        task_info["listeners"].remove(listener)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """处理 Web 控制台所有的 POST 请求：包含测试任务的下发启动、调试参数透传以及对当前运行测试任务的主动终止"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == "/api/run":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                task_id = data.get("task_id")
                nodeid = data.get("nodeid")
                remote_appium = data.get("remote_appium", "").strip()
                remote_udid = data.get("remote_udid", "").strip()
                debug_mode = data.get("debug_mode", False)
                private_chat_name = data.get("private_chat_name", "").strip()
                group_chat_name = data.get("group_chat_name", "").strip()
                web_receipt_data = data.get("web_receipt_data", "").strip()
                param_index = data.get("param_index")
                env_name = data.get("env", "").strip()
                
                if not task_id:
                    self.send_json_response(400, {"success": False, "message": "缺少参数 task_id"})
                    return
                if not nodeid:
                    self.send_json_response(400, {"success": False, "message": "缺少参数 nodeid"})
                    return
                
                success, msg = run_pytest_node(task_id, nodeid, param_index, remote_appium, remote_udid, debug_mode, private_chat_name, group_chat_name, web_receipt_data, env_name)
                if success:
                    self.send_json_response(200, {"success": True, "message": msg})
                else:
                    self.send_json_response(400, {"success": False, "message": msg})
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": f"服务器错误: {str(e)}"})
                
        elif path == "/api/agent/self_check":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length else "{}"
            try:
                data = json.loads(post_data)
                agent = load_test_runner_agent()
                args = SimpleNamespace(env=(data.get("env") or "").strip(), remote_appium=(data.get("remote_appium") or "").strip())
                entries = agent.collect_tests()
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    exit_code = agent.self_check(args, entries)
                self.send_json_response(200, {"success": exit_code == 0, "exit_code": exit_code, "output": buffer.getvalue()})
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": str(e)})

        elif path == "/api/agent/list":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length else "{}"
            try:
                data = json.loads(post_data)
                agent = load_test_runner_agent()
                query = (data.get("query") or "").strip()
                allow_destructive = bool(data.get("allow_destructive", False))
                limit = int(data.get("limit") or 80)
                entries = agent.collect_tests()
                if query:
                    target, candidates, mode = agent.resolve_target(query, entries, allow_destructive)
                    if candidates:
                        entries = candidates
                    elif target:
                        entries = [entry for entry in entries if entry.nodeid.startswith(target) or entry.file == target]
                    else:
                        entries = agent.action_candidates(query, entries)
                if not allow_destructive:
                    entries = [entry for entry in entries if "destructive" not in entry.markers]
                self.send_json_response(200, {
                    "success": True,
                    "count": len(entries),
                    "items": [agent_entry_to_dict(entry) for entry in entries[:limit]],
                })
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": str(e)})

        elif path == "/api/agent/resolve":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length else "{}"
            try:
                data = json.loads(post_data)
                result = resolve_agent_target(data)
                self.send_json_response(200 if result.get("success") else 400, result)
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": str(e)})

        elif path == "/api/agent/cases":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length else "{}"
            try:
                data = json.loads(post_data)
                result = resolve_agent_target({**data, "case": "", "param": ""})
                if not result.get("success"):
                    self.send_json_response(400, result)
                    return
                agent = load_test_runner_agent()
                cases = agent.collect_param_nodeids(result["target"])
                self.send_json_response(200, {"success": True, "target": result["target"], "cases": cases})
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": str(e)})

        elif path == "/api/agent/run":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length else "{}"
            try:
                data = json.loads(post_data)
                task_id = data.get("task_id")
                if not task_id:
                    self.send_json_response(400, {"success": False, "message": "缺少参数 task_id"})
                    return
                result = resolve_agent_target(data)
                if not result.get("success"):
                    self.send_json_response(400, result)
                    return
                success, msg = run_pytest_node(
                    task_id,
                    result["target"],
                    None,
                    data.get("remote_appium", "").strip(),
                    data.get("remote_udid", "").strip(),
                    bool(data.get("debug_mode", False)),
                    data.get("private_chat_name", "").strip(),
                    data.get("group_chat_name", "").strip(),
                    data.get("web_receipt_data", "").strip(),
                    data.get("env", "").strip(),
                )
                self.send_json_response(200 if success else 400, {
                    "success": success,
                    "message": msg,
                    "target": result["target"],
                    "command": result.get("command", ""),
                })
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": str(e)})

        elif path == "/api/agent/analyze_report":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length else "{}"
            try:
                data = json.loads(post_data)
                agent = load_test_runner_agent()
                report_dir = (data.get("allure_dir") or "reports/allure-results").strip()
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    exit_code = agent.analyze_allure_report(report_dir)
                self.send_json_response(200, {"success": exit_code == 0, "exit_code": exit_code, "output": buffer.getvalue()})
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": str(e)})

        elif path == "/api/detect_appium":
            appium_url = ""
            try:
                req = urllib.request.Request("http://127.0.0.1:4723/status")
                with urllib.request.urlopen(req, timeout=1) as response:
                    if response.status == 200:
                        appium_url = "127.0.0.1:4723"
            except Exception:
                pass
            self.send_json_response(200, {"success": True, "appium": appium_url})
            
        elif path == "/api/detect_udid":
            udid = ""
            # 1. 尝试检测 Android 设备 (adb)
            try:
                subprocess.run(["adb", "kill-server"], timeout=5)
                out = subprocess.check_output(["adb", "devices"], timeout=10).decode('utf-8')
                lines = out.strip().split('\n')
                for line in lines[1:]:
                    if '\tdevice' in line or '\toffline' in line:
                        udid = line.split('\t')[0].strip()
                        break
            except Exception:
                pass
            
            # 2. 如果未发现安卓，尝试检测 鸿蒙 HarmonyOS NEXT 设备 (hdc)
            if not udid:
                try:
                    subprocess.run(["hdc", "kill"], timeout=5)
                    out = subprocess.check_output(["hdc", "list", "targets"], timeout=10).decode('utf-8')
                    lines = out.strip().split('\n')
                    for line in lines:
                        # hdc 的正常输出是一行一个 UDID，或者提示无设备
                        if line.strip() and "Empty" not in line and "Error" not in line and "not found" not in line:
                            udid = line.strip()
                            break
                except Exception:
                    pass
                    
            self.send_json_response(200, {"success": True, "udid": udid})
                
        elif path == "/api/start_appium":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                os_type = "windows"
                if content_length > 0:
                    post_data = self.rfile.read(content_length).decode('utf-8')
                    try:
                        data = json.loads(post_data)
                        os_type = data.get("os", "windows")
                    except Exception:
                        pass
                        
                if os_type == "windows":
                    subprocess.Popen(["cmd.exe", "/c", "start", "appium", "-a", "0.0.0.0"])
                elif os_type == "mac":
                    # Mac: 使用 osascript 唤起 Terminal 应用程序并执行命令
                    subprocess.Popen(["osascript", "-e", 'tell application "Terminal" to do script "appium -a 0.0.0.0"'])
                else:
                    # Linux 或其他 Unix
                    subprocess.Popen(["appium", "-a", "0.0.0.0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                self.send_json_response(200, {"success": True})
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": str(e)})
                
        elif path == "/api/stop":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                task_id = data.get("task_id")
                if not task_id:
                    self.send_json_response(400, {"success": False, "message": "缺少参数 task_id"})
                    return
                
                with tasks_lock:
                    task_info = active_tasks.get(task_id)
                    if task_info and task_info["process"]:
                        proc = task_info["process"]
                        try:
                            if os.name == 'nt':
                                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            else:
                                proc.terminate()
                            self.send_json_response(200, {"success": True, "message": "测试已手动终止"})
                        except Exception as e:
                            self.send_json_response(500, {"success": False, "message": f"终止测试失败: {str(e)}"})
                    else:
                        self.send_json_response(400, {"success": False, "message": "当前没有正在运行的测试任务"})
            except Exception as e:
                self.send_json_response(500, {"success": False, "message": f"参数解析错误: {str(e)}"})
        else:
            self.send_error(404, "Not Found")

    def send_json_response(self, status, data):
        """快捷封装方法：向客户端发送标准的 JSON 响应头与数据"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

class QuietThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        import sys
        exc_class, exc, tb = sys.exc_info()
        # 忽略客户端强行断开连接的报错 (WinError 10053, BrokenPipeError 等)
        if exc_class in (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            return
        super().handle_error(request, client_address)

def main():
    ip = get_host_ip()
    # server = ThreadingHTTPServer(('0.0.0.0', PORT), WebRunnerHandler)
    server = QuietThreadingHTTPServer(('0.0.0.0', PORT), WebRunnerHandler)
    print("=" * 60)
    print("         IM 自动化测试局域网 Web 控制台服务已启动")
    print("=" * 60)
    print(f" 本机地址: http://localhost:{PORT}")
    print(f" 局域网内新电脑访问地址: http://{ip}:{PORT}")
    print(f" (请确保防火墙已允许 Python 访问网络，或开放 {PORT} 端口)")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务关闭中...")
        server.server_close()

if __name__ == '__main__':
    main()
