import os
import ast
import shutil
import zipfile
from pathlib import Path
import sys

def get_imports(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return set(), set()
            
    local_imports = set()
    external_imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                name = n.name.split('.')[0]
                external_imports.add(name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                parts = node.module.split('.')
                # 尝试解析为本地文件
                # 比如 from pages.chat import chat_page
                # 本地路径可能为 pages/chat/chat_page.py 或者 pages/chat.py
                possible_path_1 = os.path.join(*parts) + '.py'
                possible_path_2 = os.path.join(*parts, '__init__.py')
                
                # Check if it's a local module
                if os.path.exists(possible_path_1):
                    local_imports.add(possible_path_1)
                elif os.path.exists(possible_path_2):
                    local_imports.add(possible_path_2)
                else:
                    # 也可能是 from pages.chat.core.chat_page import ChatPage
                    for name_node in node.names:
                        possible_path_3 = os.path.join(*parts, name_node.name) + '.py'
                        possible_path_4 = os.path.join(*parts, name_node.name, '__init__.py')
                        if os.path.exists(possible_path_3):
                            local_imports.add(possible_path_3)
                        elif os.path.exists(possible_path_4):
                            local_imports.add(possible_path_4)
                    
                    # 外部依赖
                    external_imports.add(parts[0])
            else:
                # 相对导入 from . import xxx
                pass # 暂未处理复杂相对导入，假设项目用绝对导入
                
    return local_imports, external_imports

def build_dependency_graph(root_dir):
    used_py_files = set()
    external_deps = set()
    
    queue = []
    
    # 把 tests 和 templates 目录下的所有 .py 和根目录的重要 .py 作为起点
    for target_dir in ['tests', 'templates']:
        if os.path.exists(target_dir):
            for r, ds, fs in os.walk(target_dir):
                for f in fs:
                    if f.endswith('.py'):
                        queue.append(os.path.join(r, f).replace('\\', '/'))
                    
    # 将根目录下的所有 py 文件（除打包脚本自身）作为起点
    for f in os.listdir('.'):
        if os.path.isfile(f) and f.endswith('.py') and f not in ['packager.py', 'pack.py']:
            queue.append(f)
            
    while queue:
        current = queue.pop(0)
        current_norm = os.path.normpath(current).replace('\\', '/')
        if current_norm in used_py_files:
            continue
            
        used_py_files.add(current_norm)
        
        local_imp, ext_imp = get_imports(current_norm)
        external_deps.update(ext_imp)
        
        for imp in local_imp:
            imp_norm = os.path.normpath(imp).replace('\\', '/')
            if imp_norm not in used_py_files:
                queue.append(imp_norm)
                
    return used_py_files, external_deps

from core.logger_utils import logger, LogIcon

def main():
    print("开始分析依赖...")
    used_py_files, external_deps = build_dependency_graph('.')
    
    print(f"找到 {len(used_py_files)} 个被引用的 .py 文件。")
    print(f"外部包导入: {external_deps}")
    
    # 强制包含的文件后缀或目录
    ALWAYS_INCLUDE_EXTS = {'.yml', '.yaml', '.ini', '.md', '.txt', '.env', '.json', '.spec', '.html', '.css', '.js'}
    # EXCLUDE_DIRS = {'__pycache__', '.git', 'venv', 'env', 'allure-results', '.pytest_cache', 'logs', 'reports', 'packager'}
    EXCLUDE_DIRS = {'__pycache__', '.git', 'venv', 'allure-results', '.pytest_cache', 'logs', 'reports', 'packager'}
    
    zip_filename = 'santiao-anti.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. 写入引用的 py 文件
        for py_file in used_py_files:
            zipf.write(py_file)
            # 把中间路径的 __init__.py 也加进去，防止包结构破坏
            parts = py_file.split('/')
            for i in range(1, len(parts)):
                init_file = '/'.join(parts[:i]) + '/__init__.py'
                if os.path.exists(init_file) and init_file not in used_py_files:
                    zipf.write(init_file)
                    used_py_files.add(init_file)
                    
        # 2. 写入数据文件和配置文件
        for root, dirs, files in os.walk('.'):
            # 过滤目录
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                filepath = os.path.join(root, file).replace('\\', '/')
                if file == zip_filename or file == 'packager.py' or file == 'requirements_filtered.txt':
                    continue
                    
                ext = os.path.splitext(file)[1].lower()
                if ext in ALWAYS_INCLUDE_EXTS:
                    zipf.write(filepath)
                    
        # 3. 动态生成 requirements.txt （简单映射）
        # 过滤掉 Python 内置库
        import sys
        stdlib = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()
        actual_deps = [d for d in external_deps if d not in stdlib and d not in {'appium', 'selenium', 'allure'}]
        # 手动映射一些常用的别名
        req_lines = []
        if 'appium' in external_deps: req_lines.append('Appium-Python-Client')
        if 'selenium' in external_deps: req_lines.append('selenium')
        if 'pytest' in external_deps: req_lines.append('pytest')
        if 'allure' in external_deps: req_lines.append('allure-pytest')
        if 'yaml' in external_deps: req_lines.append('PyYAML')
        if 'pytest_check' in external_deps: req_lines.append('pytest-check')
        
        for dep in actual_deps:
            if dep not in ['time', 'os', 'sys', 're', 'subprocess', 'threading', 'json', 'typing', 'contextlib']:
                req_lines.append(dep)
                
        # 去重
        req_lines = list(set(req_lines))
        
        # 写入压缩包
        zipf.writestr('requirements_filtered.txt', '\n'.join(req_lines))
        
    print(f"打包成功！文件已保存为 {zip_filename}")

if __name__ == '__main__':
    main()
