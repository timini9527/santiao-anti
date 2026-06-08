import os
py_path = 'templates/web_runner.py'
with open(py_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''def run_pytest_node(nodeid, remote_appium=None, remote_udid=None, debug_mode=False, private_chat_name=None, group_chat_name=None, web_receipt_data=None):
    """构建并发起新的 Pytest 子进程执行特定的测试节点 (nodeid)，支持远程设备环境注入与 Inspector 调试保活模式"""
    global running_process, log_buffer, status_data
    with process_lock:
        if running_process is not None:
            return False, "当前有正在运行的测试任务"
        
        log_buffer.clear()
        status_data["status"] = "running"
        status_data["current_test"] = nodeid
        status_data["exit_code"] = None
        
        # 构建执行命令，生成 allure 数据
        tmp_dir = os.path.join("reports", "tmp")
        if os.path.exists(tmp_dir):
            import shutil
            try: shutil.rmtree(tmp_dir)
            except: pass
            
        import re
        # 针对 AST 静态解析无法算出 lambda 动态参数名的问题：
        # 如果前端传来的 nodeid 包含方括号（如 test_enter_chat[PRIVATE_USER1]）
        # 我们在这里强行把它剥离，退化为运行整个测试方法（test_enter_chat）
        # 这样就能完美兼容所有使用了动态 lambda 参数化的测试用例！
        safe_nodeid = re.sub(r'\[.*?\]$', '', nodeid)
        
        cmd = [sys.executable, "-m", "pytest", safe_nodeid, "-vs", "--color=yes", f"--alluredir={tmp_dir}"]'''

new_func = '''def run_pytest_node(nodeid, param_index=None, remote_appium=None, remote_udid=None, debug_mode=False, private_chat_name=None, group_chat_name=None, web_receipt_data=None):
    """构建并发起新的 Pytest 子进程执行特定的测试节点 (nodeid)，支持动态探测子用例 ID"""
    global running_process, log_buffer, status_data
    with process_lock:
        if running_process is not None:
            return False, "当前有正在运行的测试任务"
        
        log_buffer.clear()
        status_data["status"] = "running"
        status_data["current_test"] = nodeid
        status_data["exit_code"] = None
        
        tmp_dir = os.path.join("reports", "tmp")
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
                collect_cmd = [sys.executable, "-m", "pytest", safe_nodeid, "--collect-only", "-q"]
                try:
                    import subprocess
                    out = subprocess.check_output(collect_cmd, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
                    real_nodes = []
                    for line in out.splitlines():
                        line = line.strip()
                        if line and "::" in line and "[" in line:
                            real_nodes.append(line)
                    if 0 <= param_index < len(real_nodes):
                        nodeid_to_run = real_nodes[param_index]
                    else:
                        nodeid_to_run = safe_nodeid
                except Exception as e:
                    nodeid_to_run = safe_nodeid
            else:
                nodeid_to_run = safe_nodeid
        
        cmd = [sys.executable, "-m", "pytest", nodeid_to_run, "-vs", "--color=yes", f"--alluredir={tmp_dir}"]'''

if old_func in content:
    content = content.replace(old_func, new_func)
    
    # Now update JS in HTML_TEMPLATE
    content = content.replace('runSubBtn.onclick = () => runNode(`${fileObj.file}::${cls.name}::${test.name}[${param}]`);', 'runSubBtn.onclick = () => runNode(`${fileObj.file}::${cls.name}::${test.name}[${param}]`, index);')
    content = content.replace('test.params.forEach(param => {', 'test.params.forEach((param, index) => {')
    
    content = content.replace('runSubBtn.onclick = () => runNode(`${fileObj.file}::${test.name}[${param}]`);', 'runSubBtn.onclick = () => runNode(`${fileObj.file}::${test.name}[${param}]`, index);')
    
    content = content.replace('function runNode(nodeid) {', 'function runNode(nodeid, paramIndex = null) {')
    content = content.replace('body: JSON.stringify({', 'body: JSON.stringify({ param_index: paramIndex,')
    
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Update successful')
else:
    print('Failed to find target string')
