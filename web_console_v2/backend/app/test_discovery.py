from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from .config import PROJECT_ROOT, TESTS_DIR
from .schemas import TestCase, TestParam, TestTreeNode


SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "allure-results"}


def _relative_posix(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def _decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _decorator_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return ""


def _literal_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Name):
        return node.id
    return None


def _list_values(node: ast.AST) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    values: list[str] = []
    for item in node.elts:
        text = _literal_text(item)
        if text is not None:
            values.append(text)
            continue
        if isinstance(item, (ast.List, ast.Tuple)):
            nested = [_literal_text(child) or "?" for child in item.elts]
            values.append("-".join(nested))
            continue
        values.append("?")
    return values


def _extract_markers(node: ast.FunctionDef) -> list[str]:
    markers: list[str] = []
    for dec in node.decorator_list:
        name = _decorator_name(dec)
        if name.startswith("pytest.mark."):
            markers.append(name.removeprefix("pytest.mark.").split(".")[0])
    return sorted(set(markers))


def _extract_title(node: ast.FunctionDef) -> str:
    title = ""
    story = ""
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        name = _decorator_name(dec.func)
        if name == "allure.title" and dec.args:
            title = _literal_text(dec.args[0]) or ""
        elif name == "allure.story" and dec.args:
            story = _literal_text(dec.args[0]) or ""
    if title or story:
        return title or story
    doc = ast.get_docstring(node)
    if doc:
        return doc.strip().splitlines()[0].strip()
    return ""


def _extract_param_labels(node: ast.FunctionDef) -> list[str]:
    labels: list[str] = []
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        if _decorator_name(dec.func) != "pytest.mark.parametrize":
            continue
        ids_keyword = next((kw for kw in dec.keywords if kw.arg == "ids"), None)
        if ids_keyword is not None:
            ids_values = _list_values(ids_keyword.value)
            if ids_values:
                labels.extend(ids_values)
                continue
        if len(dec.args) >= 2:
            labels.extend(_list_values(dec.args[1]))
    return labels


def _iter_test_files() -> list[Path]:
    if not TESTS_DIR.exists():
        return []
    files: list[Path] = []
    for path in TESTS_DIR.rglob("test_*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def _case_from_function(path: Path, node: ast.FunctionDef, class_name: str | None = None) -> TestCase:
    rel_file = _relative_posix(path)
    module = str(path.parent.relative_to(TESTS_DIR)).replace("\\", "/")
    module = "" if module == "." else module
    base_nodeid = f"{rel_file}::{class_name}::{node.name}" if class_name else f"{rel_file}::{node.name}"
    title = _extract_title(node)
    display_name = f"{title} ({node.name})" if title else node.name
    markers = _extract_markers(node)
    params = [
        TestParam(index=index, label=label, nodeid=f"{base_nodeid}[{label}]")
        for index, label in enumerate(_extract_param_labels(node))
    ]
    return TestCase(
        id=_stable_id(base_nodeid),
        nodeid=base_nodeid,
        display_name=display_name,
        file=rel_file,
        module=module or "tests",
        class_name=class_name,
        function_name=node.name,
        params=params,
        markers=markers,
        destructive="destructive" in markers,
    )


def collect_tests() -> list[TestCase]:
    cases: list[TestCase] = []
    for path in _iter_test_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            tree = ast.parse(path.read_text(encoding="gbk", errors="ignore"))
        except SyntaxError:
            continue

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                cases.append(_case_from_function(path, node))
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name.startswith("test_"):
                        cases.append(_case_from_function(path, child, node.name))
    return cases


def build_test_tree(cases: list[TestCase]) -> list[TestTreeNode]:
    roots: dict[str, TestTreeNode] = {}

    def get_child(parent: TestTreeNode, node_id: str, label: str, node_type: str) -> TestTreeNode:
        for child in parent.children:
            if child.id == node_id:
                return child
        child = TestTreeNode(id=node_id, label=label, type=node_type)
        parent.children.append(child)
        return child

    for case in cases:
        parts = Path(case.file).parts
        if not parts:
            continue
        root_key = parts[0]
        root = roots.setdefault(root_key, TestTreeNode(id=root_key, label=root_key, type="folder"))
        parent = root
        for part in parts[1:-1]:
            folder_id = f"{parent.id}/{part}"
            parent = get_child(parent, folder_id, part, "folder")

        file_id = f"{case.file}"
        file_node = get_child(parent, file_id, parts[-1], "file")
        case_parent = file_node
        if case.class_name:
            case_parent = get_child(file_node, f"{case.file}::{case.class_name}", case.class_name, "class")
        case_parent.children.append(TestTreeNode(id=case.id, label=case.display_name, type="case", case=case))

    return list(roots.values())
