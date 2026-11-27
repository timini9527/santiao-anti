# -*- coding: utf-8 -*-
"""
鸿蒙 HypiumBy (BY.* 原生链式表达式) 与 HosBy 源码调用静态解析及属性求值引擎。
"""
import ast
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from desktop_app.ui.inspector.locator.xpath_engine import validate_xpath_syntax

_HYPIUM_MATCH_PATTERNS: Dict[str, int] = {
    "EQUALS": 0,
    "CONTAINS": 1,
    "STARTS_WITH": 2,
    "ENDS_WITH": 3,
    "REGEXP": 4,
    "REGEXP_ICASE": 5,
}

_HYPIUM_STR_METHODS = frozenset({
    "text", "type", "id", "key", "hint", "description", "inWindow",
    "originalText", "bundleName", "accessibilityId",
})
_HYPIUM_XPATH_METHODS = frozenset({"xpath"})
_HYPIUM_BOOL_METHODS = frozenset({
    "clickable", "longClickable", "scrollable", "enabled",
    "focused", "selected", "checked", "checkable",
})
_HYPIUM_REL_METHODS = frozenset({"within", "isBefore", "isAfter"})

_HARMONY_TUPLE_STRATEGY_MAP: Dict[str, str] = {
    "hypiumby": "hypium",
    "byexpression": "hypium",
    "hypium": "hypium",
    "xpath": "xpath",
    "text": "text",
    "type": "type",
    "class name": "type",
    "id": "id",
    "key": "id",
    "description": "description",
    "accessibility id": "description",
}


def _eval_hosby_ast_arg(node: ast.AST) -> Tuple[Optional[str], Any]:
    """安全静态求值 HosBy.xxx(...) 调用中的字面量与常量参数（零 eval 风险）。"""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (str, int, float, bool)) or node.value is None:
            return None, node.value
        return f"不支持的常量参数类型: {type(node.value).__name__}", None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        if (
            isinstance(node.operand, ast.Constant)
            and isinstance(node.operand.value, (int, float))
            and not isinstance(node.operand.value, bool)
        ):
            return None, -node.operand.value
    if isinstance(node, ast.Name):
        low = node.id.lower()
        if low == "true":
            return None, True
        if low == "false":
            return None, False
        if low in ("none", "null"):
            return None, None
        return f"不支持的变量引用 '{node.id}'，请替换为具体字面量字符串或 HosBy.MATCH_* 常量", None
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        if node.value.id in ("HosBy", "MatchPattern"):
            attr_name = node.attr.upper()
            if attr_name.startswith("MATCH_"):
                attr_name = attr_name[6:]
            if attr_name in _HYPIUM_MATCH_PATTERNS:
                return None, _HYPIUM_MATCH_PATTERNS[attr_name]
        return f"不支持的属性引用 '{node.value.id}.{node.attr}'", None
    return "HosBy 参数仅支持字符串、数字、布尔值、None 及 HosBy.MATCH_* 常量", None


def _convert_hosby_call_to_by_expr(raw: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    安全静态解析从源码直接复制的 HosBy.<method>(...) 调用。
    返回 (是否识别为 HosBy 调用, 转换后的标准 BY.* 表达式, 错误提示信息)。
    """
    cleaned = (raw or "").strip()
    if not cleaned:
        return False, None, None

    cleaned = re.sub(r"^(?:return\s+|[A-Za-z_][A-Za-z0-9_]*\s*=\s*)", "", cleaned).strip()
    if not re.match(r"^HosBy\.", cleaned):
        return False, None, None

    if cleaned.endswith(","):
        cleaned = cleaned[:-1].strip()

    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError as e:
        return True, None, f"HosBy 调用语法错误（请检查引号与括号是否闭合）: {e.msg}"

    call_node = tree.body
    if (
        not isinstance(call_node, ast.Call)
        or not isinstance(call_node.func, ast.Attribute)
        or not isinstance(call_node.func.value, ast.Name)
        or call_node.func.value.id != "HosBy"
    ):
        return True, None, '请输入完整的 HosBy.<方法>(...) 调用，例如 HosBy.text_contains("我已阅读且同意", "Text")'

    method_name = call_node.func.attr
    if method_name.startswith("_"):
        return True, None, f"不允许调用私有方法 HosBy.{method_name}"

    try:
        from locators.common.hos_by import HosBy as _ProjectHosBy
    except Exception as imp_err:
        return True, None, f"无法加载 locators.common.hos_by.HosBy: {imp_err}"

    target_fn = getattr(_ProjectHosBy, method_name, None)
    if not callable(target_fn):
        return True, None, f"HosBy 中不存在方法 '{method_name}'，请核对 locators/common/hos_by.py 中的方法名"

    pos_args: List[Any] = []
    for arg in call_node.args:
        a_err, a_val = _eval_hosby_ast_arg(arg)
        if a_err:
            return True, None, f"HosBy.{method_name}() 参数错误: {a_err}"
        pos_args.append(a_val)

    kw_args: Dict[str, Any] = {}
    for kw in call_node.keywords:
        if not kw.arg:
            return True, None, f"HosBy.{method_name}() 不支持 **kwargs 展开"
        a_err, a_val = _eval_hosby_ast_arg(kw.value)
        if a_err:
            return True, None, f"HosBy.{method_name}({kw.arg}=...) 参数错误: {a_err}"
        kw_args[kw.arg] = a_val

    try:
        res = target_fn(*pos_args, **kw_args)
    except Exception as call_err:
        return True, None, f"HosBy.{method_name}() 参数校验失败: {call_err}"

    if not (isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], str) and isinstance(res[1], str)):
        return True, None, f"HosBy.{method_name}() 返回值不是标准 (strategy, value) 二元组"

    strat_raw, val_raw = res[0].strip(), res[1].strip()
    strat_low = strat_raw.lower()
    if strat_low in ("hypiumby", "byexpression", "hypium"):
        return True, val_raw, None

    safe_v = _ProjectHosBy._escape(val_raw)
    if strat_low == "text":
        return True, f'BY.text("{safe_v}")', None
    if strat_low == "type":
        return True, f'BY.type("{safe_v}")', None
    if strat_low == "key":
        return True, f'BY.key("{safe_v}")', None
    if strat_low == "id":
        return True, f'BY.id("{safe_v}")', None
    return True, val_raw, None


def resolve_harmony_locator_input(raw: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    统一识别鸿蒙端粘贴的 HosBy 调用、日志/代码二元组与纯 BY.* 表达式。
    返回 (目标策略键或 None, 解包后的表达式值或 None, 语法错误信息或 None)。
    """
    text = (raw or "").strip()
    if not text:
        return None, None, None

    is_hosby, by_expr, hosby_err = _convert_hosby_call_to_by_expr(text)
    if is_hosby:
        if hosby_err:
            return "hypium", None, hosby_err
        return "hypium", by_expr, None

    def _try_parse_locator_tuple(candidate: str) -> Optional[Tuple[str, str]]:
        cand_norm = re.sub(
            r"^\(\s*(?:AppiumBy|By)\.([A-Za-z_]+)\s*,",
            lambda m: f"('{m.group(1).lower().replace('_', ' ')}',",
            candidate.strip(),
        )
        try:
            parsed = ast.literal_eval(cand_norm)
        except Exception:
            return None
        if (
            isinstance(parsed, (tuple, list))
            and len(parsed) == 2
            and isinstance(parsed[0], str)
            and isinstance(parsed[1], str)
        ):
            mapped = _HARMONY_TUPLE_STRATEGY_MAP.get(parsed[0].strip().lower())
            if mapped:
                return mapped, parsed[1].strip()
        if isinstance(parsed, str) and re.match(r"^(?:BY|By|by)\.", parsed.strip()):
            return "hypium", parsed.strip()
        return None

    direct_tuple = _try_parse_locator_tuple(text)
    if direct_tuple is not None:
        return direct_tuple[0], direct_tuple[1], None

    no_assign = re.sub(r"^(?:return\s+|[A-Za-z_][A-Za-z0-9_]*\s*=\s*)", "", text).strip().rstrip(",").strip()
    if no_assign != text:
        assign_tuple = _try_parse_locator_tuple(no_assign)
        if assign_tuple is not None:
            return assign_tuple[0], assign_tuple[1], None

    strat_keys_pat = "|".join(re.escape(k) for k in _HARMONY_TUPLE_STRATEGY_MAP)
    m_tuple = re.search(
        rf"\(\s*(?:['\"](?:{strat_keys_pat})['\"]|(?:AppiumBy|By)\.[A-Za-z_]+)\s*,",
        text,
        re.IGNORECASE,
    )
    if m_tuple:
        start_idx = m_tuple.start()
        depth = 0
        in_sq = False
        in_dq = False
        escaped = False
        for i in range(start_idx, len(text)):
            ch = text[i]
            if escaped:
                escaped = False
                continue
            if ch == "\\" and (in_sq or in_dq):
                escaped = True
                continue
            if ch == "'" and not in_dq:
                in_sq = not in_sq
            elif ch == '"' and not in_sq:
                in_dq = not in_dq
            elif not in_sq and not in_dq:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        extracted = _try_parse_locator_tuple(text[start_idx : i + 1])
                        if extracted is not None:
                            return extracted[0], extracted[1], None
                        break

    if re.match(r"^(?:BY|By|by)\.", text):
        return "hypium", text, None

    return None, None, None


def extract_hypium_expression(raw: str) -> str:
    """规范化用户粘贴的 HypiumBy 表达式（兼容 HosBy 调用与日志元组）"""
    resolved_strat, resolved_val, err = resolve_harmony_locator_input(raw)
    if err is None and resolved_strat == "hypium" and resolved_val:
        return resolved_val
    return (raw or "").strip()


def _eval_hypium_match_pattern(arg_node: ast.AST) -> Tuple[Optional[str], int]:
    """解析 HypiumBy 字符串方法的第 2 个匹配模式参数（支持 0~5 整型或 MatchPattern.XXX）。"""
    if isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, int) and not isinstance(arg_node.value, bool):
        mode = int(arg_node.value)
        if 0 <= mode <= 5:
            return None, mode
        return f"匹配模式数值 {mode} 超出有效范围 (0=精确, 1=包含, 2=前缀, 3=后缀, 4=正则, 5=正则忽略大小写)", 0
    if isinstance(arg_node, ast.Attribute) and isinstance(arg_node.value, ast.Name):
        if arg_node.value.id in ("MatchPattern", "HosBy"):
            attr_name = arg_node.attr.upper()
            if attr_name.startswith("MATCH_"):
                attr_name = attr_name[6:]
            if attr_name in _HYPIUM_MATCH_PATTERNS:
                return None, _HYPIUM_MATCH_PATTERNS[attr_name]
    return "匹配模式参数非法，请传入 0~5 整数或 MatchPattern.CONTAINS / MatchPattern.REGEXP", 0


def _eval_hypium_bool_arg(arg_node: ast.AST) -> Tuple[Optional[str], bool]:
    """解析 HypiumBy 布尔参数（兼容 JS true/false 与 Python True/False）。"""
    if isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, bool):
        return None, bool(arg_node.value)
    if isinstance(arg_node, ast.Name):
        low = arg_node.id.lower()
        if low == "true":
            return None, True
        if low == "false":
            return None, False
    return "布尔状态方法参数必须为 true / false (或 True / False)", True


def _parse_hypium_ast_chain(node: ast.AST) -> Tuple[Optional[str], List[Tuple[str, Tuple[Any, ...]]]]:
    """递归解析单条 BY.xxx(...).yyy(...) 链式调用 AST 为有序条件步骤列表。"""
    if isinstance(node, ast.Name):
        if node.id in ("BY", "By", "by"):
            return None, []
        return f"HypiumBy 表达式必须以 'BY.' 开头，不能以 '{node.id}' 开头", []

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return 'HypiumBy 表达式必须为标准链式方法调用，如 BY.type("Text").text("确定")', []

    if node.keywords:
        return f"方法 .{node.func.attr}() 不支持关键字参数，请使用位置参数", []

    err, prev_steps = _parse_hypium_ast_chain(node.func.value)
    if err:
        return err, []

    method = node.func.attr
    args = node.args

    if method in _HYPIUM_STR_METHODS:
        if len(args) not in (1, 2):
            return f"方法 .{method}() 需要 1~2 个参数，当前传入了 {len(args)} 个", []
        if not (isinstance(args[0], ast.Constant) and isinstance(args[0].value, str)):
            return f"方法 .{method}() 第 1 个参数必须为字符串字面量", []
        val_str = str(args[0].value)
        mode = 0
        if len(args) == 2:
            m_err, mode = _eval_hypium_match_pattern(args[1])
            if m_err:
                return f"方法 .{method}() {m_err}", []
        if mode in (4, 5):
            try:
                re.compile(val_str, re.IGNORECASE if mode == 5 else 0)
            except re.error as re_err:
                return f"方法 .{method}() 中的正则表达式语法无效: {re_err}", []
        prev_steps.append((method, (val_str, mode)))
        return None, prev_steps

    if method in _HYPIUM_XPATH_METHODS:
        if len(args) != 1:
            return f"方法 .{method}() 必须且只能传入 1 个 XPath 字符串参数", []
        if not (isinstance(args[0], ast.Constant) and isinstance(args[0].value, str)):
            return f"方法 .{method}() 参数必须为 XPath 字符串字面量", []
        xp_str = str(args[0].value).strip()
        xp_err = validate_xpath_syntax(xp_str)
        if xp_err:
            return f".xpath(...) 内部 XPath 语法错误: {xp_err}", []
        prev_steps.append((method, (xp_str,)))
        return None, prev_steps

    if method in _HYPIUM_BOOL_METHODS:
        if len(args) == 0:
            prev_steps.append((method, (True,)))
            return None, prev_steps
        if len(args) == 1:
            b_err, flag = _eval_hypium_bool_arg(args[0])
            if b_err:
                return f"方法 .{method}() {b_err}", []
            prev_steps.append((method, (flag,)))
            return None, prev_steps
        return f"方法 .{method}() 最多接受 1 个布尔参数，当前传入了 {len(args)} 个", []

    if method in _HYPIUM_REL_METHODS:
        if len(args) != 1:
            return f"关系定位方法 .{method}() 必须且只能传入 1 个子 BY 表达式", []
        sub_err, sub_steps = _parse_hypium_ast_chain(args[0])
        if sub_err:
            return f".{method}(...) 内部子表达式错误: {sub_err}", []
        if not sub_steps:
            return f".{method}(...) 内部不能仅传入空的 BY，请补充至少一个过滤条件", []
        prev_steps.append((method, (sub_steps,)))
        return None, prev_steps

    supported_list = (
        "text / originalText / type / id / key / hint / description / accessibilityId / "
        "inWindow / bundleName / xpath / checked / clickable / within / isBefore / isAfter"
    )
    return f"暂不支持的 HypiumBy 方法 '.{method}()'；当前支持: {supported_list}", []


def parse_hypium_by_expression(raw: str) -> Tuple[Optional[str], List[Tuple[str, Tuple[Any, ...]]]]:
    """
    校验并解析鸿蒙 HypiumBy (BY.*) 表达式（兼容直接粘贴 HosBy.xxx(...) 源码调用与日志元组）。
    返回 (错误提示信息或 None, 解析后的链式条件列表)。
    """
    is_hosby, by_expr, hosby_err = _convert_hosby_call_to_by_expr(raw)
    if is_hosby:
        if hosby_err:
            return hosby_err, []
        expr = by_expr or ""
    else:
        expr = extract_hypium_expression(raw)

    if not expr:
        return "HypiumBy 表达式不能为空", []

    if not re.match(r"^(?:BY|By|by)\.", expr):
        return (
            "HypiumBy 表达式必须以 'BY.' 开头（也可直接粘贴 HosBy.xxx(...) 源码或日志中的 ('HypiumBy', 'BY....') 元组）",
            [],
        )

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        return f"HypiumBy 表达式语法错误（请检查引号与括号是否闭合）: {e.msg}", []

    err, steps = _parse_hypium_ast_chain(tree.body)
    if err:
        return err, []
    if not steps:
        return "HypiumBy 表达式缺少条件方法，请至少追加一个如 .text(...) 或 .type(...)", []
    return None, steps


def _match_hypium_str(actual: str, pattern: str, mode: int) -> bool:
    """按鸿蒙 uitest MatchPattern (0~5) 规则执行字符串匹配。"""
    if mode == 0:
        return actual == pattern
    if mode == 1:
        return pattern in actual
    if mode == 2:
        return actual.startswith(pattern)
    if mode == 3:
        return actual.endswith(pattern)
    if mode == 4:
        return bool(re.search(pattern, actual))
    if mode == 5:
        return bool(re.search(pattern, actual, re.IGNORECASE))
    return actual == pattern


def _eval_hypium_attr_step(
    method: str,
    args: Tuple[Any, ...],
    comp: Dict[str, Any],
    elem: Optional[ET.Element],
    parent_map: Dict[ET.Element, ET.Element],
    comp_by_elem: Dict[ET.Element, Dict[str, Any]],
) -> bool:
    """求值单条非关系型 HypiumBy 属性/状态过滤步骤。"""
    raw_attrs = comp.get("raw_attributes") or comp.get("raw") or {}

    if method == "text":
        pat, mode = args
        val = str(comp.get("text") or raw_attrs.get("text") or raw_attrs.get("originalText") or "")
        return _match_hypium_str(val, pat, mode)

    if method == "originalText":
        pat, mode = args
        val = str(raw_attrs.get("originalText") or comp.get("text") or raw_attrs.get("text") or "")
        return _match_hypium_str(val, pat, mode)

    if method == "type":
        pat, mode = args
        c_type = str(comp.get("type") or raw_attrs.get("type") or "")
        c_full = str(comp.get("full_type") or "")
        return _match_hypium_str(c_type, pat, mode) or (bool(c_full) and _match_hypium_str(c_full, pat, mode))

    if method == "id":
        pat, mode = args
        candidates = [
            str(comp.get("id") or ""),
            str(raw_attrs.get("id") or ""),
            str(raw_attrs.get("key") or ""),
        ]
        return any(_match_hypium_str(c, pat, mode) for c in candidates if c or pat == "")

    if method == "key":
        pat, mode = args
        candidates = [
            str(raw_attrs.get("key") or ""),
            str(comp.get("id") or ""),
            str(raw_attrs.get("id") or ""),
        ]
        return any(_match_hypium_str(c, pat, mode) for c in candidates if c or pat == "")

    if method == "accessibilityId":
        pat, mode = args
        val = str(raw_attrs.get("accessibilityId") or raw_attrs.get("accessibility-id") or comp.get("id") or "")
        return _match_hypium_str(val, pat, mode)

    if method == "hint":
        pat, mode = args
        val = str(raw_attrs.get("hint") or raw_attrs.get("placeholder") or "")
        return _match_hypium_str(val, pat, mode)

    if method == "description":
        pat, mode = args
        val = str(
            raw_attrs.get("description")
            or raw_attrs.get("accessibilityDescription")
            or raw_attrs.get("content-desc")
            or ""
        )
        return _match_hypium_str(val, pat, mode)

    if method in ("inWindow", "bundleName"):
        pat, mode = args
        cur_el = elem
        while cur_el is not None:
            cur_comp = comp_by_elem.get(cur_el) or {}
            cur_attrs = cur_comp.get("raw_attributes") or cur_comp.get("raw") or {}
            bundle = str(cur_attrs.get("bundleName") or cur_attrs.get("package") or "")
            if bundle:
                return _match_hypium_str(bundle, pat, mode)
            cur_el = parent_map.get(cur_el)
        bundle = str(raw_attrs.get("bundleName") or raw_attrs.get("package") or "")
        return _match_hypium_str(bundle, pat, mode)

    if method in _HYPIUM_BOOL_METHODS:
        expected_flag = bool(args[0])
        kebab_key = re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), method)
        raw_val = None
        for k in (method, method.lower(), kebab_key):
            if k in raw_attrs:
                raw_val = raw_attrs.get(k)
                break
        if isinstance(raw_val, bool):
            actual_flag = raw_val
        else:
            actual_flag = str(raw_val or "").strip().lower() in ("true", "1", "yes")
        return actual_flag == expected_flag

    return False
