import os
import sys
import ast
import json
import subprocess
from typing import List, Dict, Any

from .paths import PROJECT_ROOT, TEMP_COLLECT_SCRIPT, TESTS_DIR

class TestCollector(ast.NodeVisitor):
    """使用 AST 静态解析 Python 文件中的测试类和测试函数"""
    
    def __init__(self):
        self.classes = []
        self.functions = []

    def _parse_parametrize(self, node: ast.FunctionDef) -> List[str]:
        """解析函数节点中 pytest.mark.parametrize 携带的 ids 或参数"""
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
                    # 1. 优先尝试从 keyword `ids` 中获取自定义中文描述
                    ids_values = []
                    for kw in dec.keywords:
                        if kw.arg == 'ids' and (isinstance(kw.value, ast.List) or isinstance(kw.value, ast.Tuple)):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant):
                                    ids_values.append(str(elt.value))
                    
                    if ids_values:
                        params.extend(ids_values)
                    else:
                        # 2. 回退至实际传参的值解析
                        arg_values = dec.args[1]
                        if isinstance(arg_values, (ast.List, ast.Tuple)):
                            for elt in arg_values.elts:
                                if isinstance(elt, ast.Constant):
                                    params.append(str(elt.value))
                                elif isinstance(elt, ast.Name):
                                    params.append(elt.id)
                                elif isinstance(elt, (ast.Tuple, ast.List)):
                                    sub_vals = []
                                    for sub_elt in elt.elts:
                                        if isinstance(sub_elt, ast.Constant):
                                            sub_vals.append(str(sub_elt.value))
                                        elif isinstance(sub_elt, ast.Name):
                                            sub_vals.append(sub_elt.id)
                                        else:
                                            sub_vals.append("?")
                                    params.append("-".join(sub_vals))
                                else:
                                    params.append("?")
        return params

    def _process_func(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """提取 Allure 描述或 Docstring 并组装测试用例结构"""
        params = self._parse_parametrize(node)
        title = ""
        story = ""
        
        # 更加健壮地提取 @allure.title() 与 @allure.story()
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                func = dec.func
                is_allure = False
                attr = ""
                if isinstance(func, ast.Attribute):
                    if isinstance(func.value, ast.Name) and func.value.id == 'allure':
                        is_allure = True
                        attr = func.attr
                elif isinstance(func, ast.Name):
                    if func.id in ('title', 'story'):
                        is_allure = True
                        attr = func.id
                
                if is_allure and dec.args:
                    arg = dec.args[0]
                    val_str = ""
                    if isinstance(arg, ast.Constant):
                        val_str = str(arg.value)
                    elif isinstance(arg, ast.Str):
                        val_str = arg.s
                    elif isinstance(arg, ast.JoinedStr):
                        parts = []
                        for val_node in arg.values:
                            if isinstance(val_node, ast.Constant):
                                parts.append(str(val_node.value))
                            elif isinstance(val_node, ast.FormattedValue):
                                parts.append("{var}")
                        val_str = "".join(parts)
                    
                    if val_str:
                        if attr == 'title':
                            title = val_str
                        elif attr == 'story':
                            story = val_str
        
        # 优先使用 allure title，其次 allure story，再次使用函数 docstring 的首行
        name_desc = title or story
        if not name_desc:
            doc = ast.get_docstring(node)
            if doc:
                name_desc = doc.strip().split('\n')[0].strip()
        
        display_name = name_desc if name_desc else node.name
        return {"name": node.name, "display_name": display_name, "params": params}

    def visit_ClassDef(self, node: ast.ClassDef):
        """如果类以 Test 开头，则收集其内部的方法"""
        if node.name.startswith("Test"):
            feature = ""
            story = ""
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    func = dec.func
                    is_allure = False
                    attr = ""
                    if isinstance(func, ast.Attribute):
                        if isinstance(func.value, ast.Name) and func.value.id == 'allure':
                            is_allure = True
                            attr = func.attr
                    elif isinstance(func, ast.Name):
                        if func.id in ('feature', 'story'):
                            is_allure = True
                            attr = func.id
                    
                    if is_allure and dec.args:
                        arg = dec.args[0]
                        val_str = ""
                        if isinstance(arg, ast.Constant):
                            val_str = str(arg.value)
                        elif isinstance(arg, ast.Str):
                            val_str = arg.s
                        elif isinstance(arg, ast.JoinedStr):
                            parts = []
                            for val_node in arg.values:
                                if isinstance(val_node, ast.Constant):
                                    parts.append(str(val_node.value))
                                elif isinstance(val_node, ast.FormattedValue):
                                    parts.append("{var}")
                            val_str = "".join(parts)
                        
                        if val_str:
                            if attr == 'feature':
                                feature = val_str
                            elif attr == 'story':
                                story = val_str
            
            # 类展示优先使用 feature，其次 story，再次使用类 docstring 的首行
            class_desc = feature or story
            if not class_desc:
                doc = ast.get_docstring(node)
                if doc:
                    class_desc = doc.strip().split('\n')[0].strip()
            
            display_name = class_desc if class_desc else node.name
            
            class_tests = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    class_tests.append(self._process_func(item))
            self.classes.append({"name": node.name, "display_name": display_name, "tests": class_tests})
            return
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """如果函数以 test_ 开头且是独立的，则收集"""
        if node.name.startswith("test_"):
            self.functions.append(self._process_func(node))

def collect_all_tests(tests_dir: str = "tests") -> List[Dict[str, Any]]:
    """
    递归遍历目录，静态及动态融合解析测试用例。
    参数: tests_dir - 测试代码的根目录名称。
    返回: 含有用例分级结构的目录树列表。
    """
    catalog = []
    # 动态支持绝对路径或基于项目根目录的相对路径
    abs_tests_dir = tests_dir if os.path.isabs(tests_dir) else os.path.join(PROJECT_ROOT, tests_dir)
    if not os.path.exists(abs_tests_dir):
        return catalog

    for root, dirs, files in os.walk(abs_tests_dir):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.pytest_cache')]
        for file in files:
            if (file.startswith("test_") or file.endswith("_test.py")) and file.endswith(".py"):
                full_path = os.path.join(root, file)
                # 统一为相对于项目根目录的跨平台标准 posix 路径 (如 tests/smoke_test/xxx.py)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT).replace("\\", "/")
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=full_path)
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
                            file_desc = first_cls["display_name"].split(" (")[0] if " (" in first_cls["display_name"] else first_cls["display_name"]
                        if not file_desc and collector.functions:
                            first_func = collector.functions[0]
                            file_desc = first_func["display_name"].split(" (")[0] if " (" in first_func["display_name"] else first_func["display_name"]
                        
                        display_name = file_desc if file_desc else file
                        catalog.append({
                            "file": rel_path,
                            "display_name": display_name,
                            "classes": collector.classes,
                            "tests": collector.functions
                        })
                except Exception as e:
                    print(f"解析文件失败 {full_path}: {e}", file=sys.stderr)

    # 动态匹配真实的 Pytest 参数化 ID (如 ids_values)
    try:
        try:
            from desktop_app.core.path_resolver import SmartPathResolver
            py_exec = SmartPathResolver.discover_python_runtime().get("executable")
        except Exception:
            py_exec = sys.executable if not getattr(sys, 'frozen', False) else None
            if not py_exec:
                import shutil
                py_exec = shutil.which("python") or shutil.which("python3")

        # 使用动态绝对路径定位辅助收集脚本，并指定工作目录为项目根目录
        if py_exec and os.path.exists(TEMP_COLLECT_SCRIPT):
            no_window = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            raw_out = subprocess.check_output(
                [py_exec, TEMP_COLLECT_SCRIPT],
                stderr=subprocess.STDOUT,
                cwd=PROJECT_ROOT,
                creationflags=no_window
            )
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
        print(f"动态匹配用例参数失败: {e}", file=sys.stderr)
        
    return catalog
