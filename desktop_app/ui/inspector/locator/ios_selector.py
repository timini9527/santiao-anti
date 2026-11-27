# -*- coding: utf-8 -*-
"""
iOS 专属元素定位语法分词与静态校验器：
1. tokenize_ios_predicate：将 NSPredicate 表达式拆解为原子条件与布尔逻辑树；
2. validate_ios_selector_syntax：校验 iOS 五大策略 (id / xpath / class name / predicate / class chain)。
"""
import ast
import re
from typing import List, Optional, Tuple

from desktop_app.ui.inspector.locator.xpath_engine import validate_xpath_syntax


def tokenize_ios_predicate(raw: str) -> Tuple[Optional[str], List[str], str]:
    """
    将 iOS NSPredicate 表达式解析为原子条件列表与纯布尔逻辑表达式。
    返回: (错误信息, 原子条件列表, Python布尔表达式字符串)。
    """
    raw_s = raw.strip()
    if not raw_s:
        return ("定位表达式不能为空", [], "")

    in_sq = False
    in_dq = False
    in_brace = False
    tokens: List[Tuple[str, str]] = []
    buf: List[str] = []

    def flush_atom() -> None:
        nonlocal buf
        s = "".join(buf).strip()
        if s:
            tokens.append(("atom", s))
        buf = []

    i = 0
    n = len(raw_s)
    while i < n:
        ch = raw_s[i]
        if ch == "\\":
            buf.append(ch)
            if i + 1 < n:
                buf.append(raw_s[i + 1])
                i += 2
            else:
                i += 1
            continue

        if ch == "'" and not in_dq:
            in_sq = not in_sq
            buf.append(ch)
            i += 1
            continue
        if ch == '"' and not in_sq:
            in_dq = not in_dq
            buf.append(ch)
            i += 1
            continue

        if not in_sq and not in_dq:
            if ch == "{":
                in_brace = True
                buf.append(ch)
                i += 1
                continue
            if ch == "}":
                in_brace = False
                buf.append(ch)
                i += 1
                continue

            if not in_brace:
                if ch in ("(", ")"):
                    flush_atom()
                    tokens.append(("paren", ch))
                    i += 1
                    continue

                sub = raw_s[i:]
                and_m = re.match(r"^(?:AND\b|&&)", sub, re.IGNORECASE)
                or_m = re.match(r"^(?:OR\b|\|\|)", sub, re.IGNORECASE)
                not_m = re.match(r"^(?:NOT\b|!)", sub, re.IGNORECASE)

                if and_m:
                    flush_atom()
                    tokens.append(("op", "and"))
                    i += and_m.end()
                    continue
                if or_m:
                    flush_atom()
                    tokens.append(("op", "or"))
                    i += or_m.end()
                    continue
                if not_m and not "".join(buf).strip():
                    flush_atom()
                    tokens.append(("op", "not"))
                    i += not_m.end()
                    continue

        buf.append(ch)
        i += 1

    flush_atom()

    if in_sq:
        return ("单引号 ''' 未闭合，字符串缺少结束单引号", [], "")
    if in_dq:
        return ('双引号 \'"\' 未闭合，字符串缺少结束双引号', [], "")
    if in_brace:
        return ("集合花括号 '{{' 未闭合，缺少结束 '}}'", [], "")

    atom_list: List[str] = []
    py_parts: List[str] = []
    for t_type, t_val in tokens:
        if t_type == "atom":
            atom_idx = len(atom_list)
            atom_list.append(t_val)
            py_parts.append(f"_c_{atom_idx}")
        elif t_type in ("op", "paren"):
            py_parts.append(t_val)

    py_expr = " ".join(py_parts).strip()
    if not py_expr:
        return ("Predicate 表达式不能为空", [], "")

    try:
        ast.parse(py_expr, mode="eval")
    except SyntaxError:
        if py_parts and py_parts[-1] in ("and", "or", "not"):
            return (f"Predicate 表达式不完整，不能以逻辑运算符 '{py_parts[-1].upper()}' 结尾", [], "")
        if py_parts and py_parts[0] in ("and", "or"):
            return (f"Predicate 表达式逻辑结构错误: 不能以逻辑运算符 '{py_parts[0].upper()}' 开头", [], "")
        if "()" in py_expr or "( )" in py_expr:
            return ("Predicate 括号内部不能为空", [], "")
        return ("Predicate 表达式布尔逻辑结构非法，请检查 AND / OR 及括号连接", [], "")

    return (None, atom_list, py_expr)


def validate_ios_selector_syntax(strategy: str, val: str) -> Tuple[Optional[str], str]:
    """
    iOS 五大定位策略静态语法校验器 (id / xpath / class name / predicate / class chain)。
    返回 (错误提示信息, 推荐标准示例)；合法返回 (None, "")。
    """
    if not val or not val.strip():
        return "定位表达式不能为空", ""

    raw = val.strip()

    py_prefix_match = re.match(r'^([fFrRuUbB]{1,2})(["\'])(.*)$', raw, re.DOTALL)
    if py_prefix_match:
        prefix_str = py_prefix_match.group(1)
        quote_ch = py_prefix_match.group(2)
        rest_str = py_prefix_match.group(3)
        clean_example = rest_str[:-1].strip() if rest_str.endswith(quote_ch) else rest_str.strip()
        clean_example = clean_example.replace("{_TAP_TYPES}", "{'XCUIElementTypeButton', 'XCUIElementTypeStaticText'}")
        clean_example = clean_example.replace("{_TEXT_TYPES}", "{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}")
        return (
            f"检测到 Python 格式化字符串前缀 '{prefix_str}{quote_ch}...'；请移除外部的 {prefix_str}{quote_ch}...{quote_ch} 代码包装，直接输入纯定位表达式",
            clean_example,
        )

    first_ch = raw[0]
    if first_ch in ('"', "'"):
        match_idx = -1
        i = 1
        n = len(raw)
        while i < n:
            ch = raw[i]
            if ch == "\\":
                i += 2
                continue
            if ch == first_ch:
                match_idx = i
                break
            i += 1
        if match_idx != -1:
            trailing = raw[match_idx + 1 :].strip()
            inner_content = raw[1:match_idx].strip()
            if trailing:
                return (
                    f"引号在第 {match_idx + 1} 位提前闭合，引号后存在非法游离字符 '{trailing}'；请移除外部包裹的引号与尾部残留字符",
                    inner_content,
                )
            return (
                f"表达式无需在最外层包裹多余的代码引号 ({first_ch}...{first_ch})；请直接输入表达式内容",
                inner_content,
            )

    py_var_match = re.search(r"\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}", raw)
    if py_var_match:
        var_name = py_var_match.group(1)
        clean_example = raw.replace("{_TAP_TYPES}", "{'XCUIElementTypeButton', 'XCUIElementTypeStaticText'}")
        clean_example = clean_example.replace("{_TEXT_TYPES}", "{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}")
        if clean_example == raw:
            clean_example = re.sub(r"\{\s*" + re.escape(var_name) + r"\s*\}", "{'XCUIElementTypeButton'}", raw)
        return (
            f"检测到未展开的 Python 变量占位符 '{{{var_name}}}'；查找器仅接收纯定位表达式（集合内字符串必须加引号）",
            clean_example,
        )

    if strategy == "id":
        if raw.startswith(("//", "/", ".")) or ("[" in raw and "]" in raw):
            return (
                "检测到 XPath 路径语法特征；当前策略为 [id]，若要使用路径定位请切换策略为 [xpath]",
                "login_button 或 ic delete 48",
            )
        if raw.startswith("**/"):
            return (
                "检测到 Class Chain 语法特征；当前策略为 [id]，请切换策略为 [ios class chain]",
                "**/XCUIElementTypeButton[`name == '确定'`]",
            )
        if raw.startswith("@"):
            return ("ID 选择器无需添加 '@' 前缀，请直接输入组件名称或标识", raw.lstrip("@"))
        if re.search(r"\b(OR|AND|NOT|IN)\b|[=!<>]=?", raw, re.IGNORECASE):
            return (
                "ID / Accessibility ID 仅支持单一标识精确匹配，不支持 'OR'/'AND'/'==' 等逻辑运算符；若需多条件二选一，请切换策略为 [ios predicate string] 或 [xpath]",
                "name IN {'密码验证登录', '短信验证登录'}",
            )
        return None, ""

    if strategy == "xpath":
        if not (raw.startswith("/") or raw.startswith("./") or raw.startswith("(")):
            return (
                "XPath 表达式必须以 '//' 或 '/' 开头",
                "//XCUIElementTypeButton[@name='确定'] 或 //Button",
            )
        if re.search(r"\[\s*(name|label|value|type|enabled|visible)\s*=", raw):
            return ("XPath 属性过滤必须以 '@' 开头，请勿漏写 '@' 符号", "//Button[@name='确定']")
        xp_err = validate_xpath_syntax(raw)
        if xp_err:
            return f"XPath 语法错误: {xp_err}", "//XCUIElementTypeButton[@name='登录']"
        return None, ""

    if strategy in ("class name", "type"):
        if any(ch in raw for ch in ("/", "\\", "[", "]", "@", "=", "(", ")", "'", '"')):
            return (
                "Class Name 仅为单一组件类型名称，无需包含斜杠、方括号或属性条件；若要按层级查找请使用 [xpath] 或 [ios class chain]",
                "XCUIElementTypeButton 或 Button",
            )
        if " " in raw:
            return ("组件类名不能包含空格，请输入合法的类名标识符", "XCUIElementTypeButton")
        if raw.startswith("android.") or "widget." in raw:
            return (
                "当前为 iOS 平台，不能使用 Android 控件类名 (android.widget.*)；请输入 iOS 的 XCUIElementType* 类名",
                "XCUIElementTypeButton 或 XCUIElementTypeStaticText",
            )
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", raw):
            return ("组件类名必须由英文字母、数字或下划线组成", "XCUIElementTypeButton")
        return None, ""

    if strategy == "predicate":
        in_sq = False
        in_dq = False
        paren_stack: List[int] = []
        brace_stack: List[int] = []
        bracket_stack: List[int] = []
        i = 0
        n = len(raw)
        while i < n:
            ch = raw[i]
            if ch == "\\":
                i += 2
                continue
            if ch == "'" and not in_dq:
                in_sq = not in_sq
            elif ch == '"' and not in_sq:
                in_dq = not in_dq
            elif not in_sq and not in_dq:
                if ch == "(":
                    paren_stack.append(i)
                elif ch == ")":
                    if not paren_stack:
                        return f"第 {i + 1} 个字符处圆括号 ')' 提前闭合，缺少对应的 '('", "label == '设置'"
                    paren_stack.pop()
                elif ch == "{":
                    brace_stack.append(i)
                elif ch == "}":
                    if not brace_stack:
                        return f"第 {i + 1} 个字符处花括号 '}}' 提前闭合，缺少对应的 '{{'", "name IN {'A', 'B'}"
                    brace_stack.pop()
                elif ch == "[":
                    bracket_stack.append(i)
                elif ch == "]":
                    if not bracket_stack:
                        return f"第 {i + 1} 个字符处方括号 ']' 提前闭合，缺少对应的 '['", "name == '确定'"
                    bracket_stack.pop()
            i += 1

        if in_sq:
            return "单引号 ''' 未闭合，字符串字面量缺少结束单引号", "name == '登录'"
        if in_dq:
            return '双引号 \'"\' 未闭合，字符串字面量缺少结束双引号', 'name == "登录"'
        if paren_stack:
            return f"第 {paren_stack[-1] + 1} 个字符处圆括号 '(' 未闭合，缺少对应的 ')'", "(name == 'A' OR name == 'B')"
        if brace_stack:
            return f"第 {brace_stack[-1] + 1} 个字符处集合花括号 '{{' 未闭合，缺少对应的 '}}'", "name IN {'A', 'B'}"
        if bracket_stack:
            return f"第 {bracket_stack[-1] + 1} 个字符处方括号 '[' 未闭合，缺少对应的 ']'", "name == '确定'"

        if raw.startswith(("//", "/", "./", "**/")):
            return (
                "检测到路径语法特征；Predicate 为属性比较表达式，无需斜杠；例如: name == '确定' 或 label CONTAINS '登录'",
                "name == '确定' OR label == '确定'",
            )
        if re.search(r"@(name|label|value|type)\b", raw):
            return (
                "Predicate 表达式属性名无需添加 '@' 前缀；请直接书写属性名 (例如: name == '确定' 而非 @name)",
                "name == '确定'",
            )
        if re.search(r"\bIN\s*\(", raw, re.IGNORECASE):
            return (
                "NSPredicate 的集合语法必须使用花括号 {}，不能使用圆括号 ()",
                "name IN {'密码验证登录', '短信验证登录'}",
            )
        for set_m in re.finditer(r"\bIN\s*\{([^}]*)\}", raw, re.IGNORECASE):
            set_body = set_m.group(1).strip()
            if not set_body:
                return "IN 集合花括号 '{}' 内部不能为空", "name IN {'密码验证登录', '短信验证登录'}"
            for raw_item in set_body.split(","):
                it = raw_item.strip()
                if not it:
                    continue
                if not (
                    (it.startswith("'") and it.endswith("'"))
                    or (it.startswith('"') and it.endswith('"'))
                    or it.isdigit()
                ):
                    return (
                        f"IN 集合内部的字符串元素 '{it}' 缺少引号包裹；集合元素必须使用单引号或双引号包裹",
                        "type IN {'XCUIElementTypeButton', 'XCUIElementTypeStaticText'}",
                    )
        if re.search(
            r"\b(AND|OR|NOT|IN|LIKE|CONTAINS|BEGINSWITH|ENDSWITH|MATCHES)\s*$|[=!<>]=?\s*$",
            raw,
            re.IGNORECASE,
        ):
            return (
                "Predicate 表达式不完整，不能以运算符 (如 '==', 'AND', 'OR', 'IN') 结尾",
                "label == '确定' AND visible == 1",
            )
        has_cmp = re.search(
            r"==|!=|<=|>=|<|>|<>|\b(CONTAINS|BEGINSWITH|ENDSWITH|LIKE|MATCHES|IN|BETWEEN)\b",
            raw,
            re.IGNORECASE,
        )
        if not has_cmp:
            return (
                "Predicate 表达式必须包含比较运算符 (如 ==, CONTAINS, IN 等)；若仅按 ID 匹配请切换为 [id] 策略",
                "label == '设置' 或 name IN {'密码验证登录', '短信验证登录'}",
            )

        err_msg, atom_list, _ = tokenize_ios_predicate(raw)
        if err_msg:
            return (err_msg, "type == 'Link' AND (label == '注册' OR name == '注册')")

        valid_pred_attrs = {
            "name", "label", "value", "type", "enabled", "visible", "accessible",
            "selected", "focused", "hittable", "wdtype", "wdname", "wdlabel",
            "wdvalue", "wdrect", "wdvisible", "wdenabled", "wdaccessible", "wduid",
            "rect", "frame", "placeholdervalue", "title", "identifier", "traits", "index",
        }

        for atom in atom_list:
            c_str_no_not = re.sub(r"^(?:NOT\s+|!\s*)", "", atom, flags=re.IGNORECASE).strip()
            in_clause_m = re.match(
                r"^([A-Za-z_][A-Za-z0-9_\.]*)\s+IN(?:\s*\[[cd]+\])?\s*\{([^}]*)\}(.*)$",
                c_str_no_not,
                re.IGNORECASE | re.DOTALL,
            )
            if in_clause_m:
                attr_name = in_clause_m.group(1)
                set_inner = in_clause_m.group(2)
                trailing_after_brace = in_clause_m.group(3).strip()
                if attr_name.lower().split(".")[0] not in valid_pred_attrs:
                    return (
                        f"未知的 iOS Predicate 属性名 '{attr_name}'；常用属性包括: name, label, value, type, enabled, visible",
                        f"name IN {{{set_inner}}}",
                    )
                if trailing_after_brace:
                    return (
                        f"集合表达式 '}}' 闭合后存在非法多余内容 '{trailing_after_brace}'；条件之间必须使用 AND / OR 连接，请移除尾部多余字符",
                        f"{attr_name} IN {{{set_inner}}}",
                    )
                continue

            in_missing_brace_m = re.match(
                r"^([A-Za-z_][A-Za-z0-9_\.]*)\s+IN(?:\s*\[[cd]+\])?\s+([^{].*)$",
                c_str_no_not,
                re.IGNORECASE | re.DOTALL,
            )
            if in_missing_brace_m:
                attr_name = in_missing_brace_m.group(1)
                rhs_raw = in_missing_brace_m.group(2).strip()
                clean_rhs = rhs_raw.strip("'\"[]() ")
                sample_val = clean_rhs if clean_rhs else "XCUIElementTypeStaticText"
                return (
                    f"运算符 'IN' 右侧 '{rhs_raw}' 缺少集合花括号 '{{}}' 与引号包裹；NSPredicate 集合必须写作 {attr_name} IN {{'{sample_val}'}}（单个值也可改用 {attr_name} == '{sample_val}'）",
                    f"{attr_name} IN {{'{sample_val}'}}",
                )

            cmp_clause_m = re.match(
                r"^([A-Za-z_][A-Za-z0-9_\.]*)\s*(==|!=|=|<>|<=|>=|<|>|\b(?:CONTAINS|BEGINSWITH|ENDSWITH|LIKE|MATCHES)\b(?:\s*\[[cd]+\])?)\s*(.+)$",
                c_str_no_not,
                re.IGNORECASE | re.DOTALL,
            )
            if cmp_clause_m:
                attr_name = cmp_clause_m.group(1)
                op_str = cmp_clause_m.group(2).strip()
                rhs_str = cmp_clause_m.group(3).strip()
                if attr_name.lower().split(".")[0] not in valid_pred_attrs:
                    return (
                        f"未知的 iOS Predicate 属性名 '{attr_name}'；常用属性包括: name, label, value, type, enabled, visible",
                        f"name {op_str} {rhs_str}",
                    )
                if rhs_str[0] in ("'", '"'):
                    q_ch = rhs_str[0]
                    q_end = -1
                    k = 1
                    while k < len(rhs_str):
                        if rhs_str[k] == "\\":
                            k += 2
                            continue
                        if rhs_str[k] == q_ch:
                            q_end = k
                            break
                        k += 1
                    if q_end != -1:
                        rhs_trailing = rhs_str[q_end + 1 :].strip()
                        if rhs_trailing:
                            clean_rhs = rhs_str[: q_end + 1]
                            return (
                                f"字符串字面量 {clean_rhs} 闭合引号后存在非法多余内容 '{rhs_trailing}'；请移除多余字符或使用 AND / OR 连接新条件",
                                f"{attr_name} {op_str} {clean_rhs}",
                            )
                else:
                    if not re.match(r"^(?:true|false|yes|no|nil|null|\d+(?:\.\d+)?)$", rhs_str, re.IGNORECASE):
                        return (
                            f"比较运算符 '{op_str}' 右侧的字符串值 '{rhs_str}' 缺少引号包裹，或包含多余字符",
                            f"{attr_name} {op_str} '{rhs_str}'",
                        )
                continue

            if re.match(
                r"^(?:TRUEPREDICATE|FALSEPREDICATE|1|0|true|false|enabled|visible|accessible|selected|hittable)$",
                c_str_no_not,
                re.IGNORECASE,
            ):
                continue

            return (
                f"Predicate 子表达式 '{atom}' 语法格式非法；每个条件子句必须为 '属性 运算符 值' 格式 (如 name == '确定' 或 name IN {{'A', 'B'}})",
                "type == 'Link' AND (label == '注册' OR name == '注册')",
            )

        return None, ""

    if strategy == "class chain":
        if not (raw.startswith("**/") or raw.startswith("/*") or raw.startswith("/")):
            return (
                "Class Chain 表达式必须以 '**/' 或 '/' 开头",
                "**/XCUIElementTypeButton[`name == '确定'`]",
            )
        if raw.count("[") != raw.count("]"):
            return "Class Chain 表达式方括号 '[' 与 ']' 未成对闭合", "**/XCUIElementTypeButton[`name == '确定'`]"
        if raw.count("`") % 2 != 0:
            return "Class Chain 嵌套谓词反引号 '`' 未成对闭合", "**/XCUIElementTypeButton[`label == '确定'`]"
        if raw.count('"') % 2 != 0 or raw.count("'") % 2 != 0:
            return "Class Chain 内部字符串引号未成对闭合", "**/XCUIElementTypeButton[`name == '确定'`]"
        if re.search(r"\[\s*@(name|label|text)", raw):
            return (
                "Class Chain 中的属性过滤需使用反引号包裹 Predicate 语法，如 [`name == '确定'`]，无需使用 XPath 的 '@' 属性语法",
                "**/XCUIElementTypeButton[`name == '确定'`]",
            )
        if "//" in raw and not raw.startswith("**/"):
            return (
                "Class Chain 使用 '**/' 表示任意深度后代遍历，不能使用 XPath 的 '//'",
                "**/XCUIElementTypeButton[`name == '确定'`]",
            )

        cc_segs: List[str] = []
        cc_buf: List[str] = []
        cc_bt = False
        cc_sq = False
        cc_dq = False
        for ch in raw:
            if ch == "`" and not cc_sq and not cc_dq:
                cc_bt = not cc_bt
                cc_buf.append(ch)
            elif ch == "'" and not cc_dq:
                cc_sq = not cc_sq
                cc_buf.append(ch)
            elif ch == '"' and not cc_sq:
                cc_dq = not cc_dq
                cc_buf.append(ch)
            elif ch == "/" and not cc_bt and not cc_sq and not cc_dq:
                cc_segs.append("".join(cc_buf))
                cc_buf = []
            else:
                cc_buf.append(ch)
        cc_segs.append("".join(cc_buf))

        for seg in cc_segs:
            seg_s = seg.strip()
            if not seg_s or seg_s in ("**", "*"):
                continue
            seg_m = re.match(r"^(\*|[A-Za-z_][A-Za-z0-9_]*)(.*)$", seg_s, re.DOTALL)
            if not seg_m:
                return f"Class Chain 节点段 '{seg_s}' 类名格式非法", "**/XCUIElementTypeButton[`name == '确定'`]"
            seg_rest = seg_m.group(2).strip()
            if seg_rest:
                if not seg_rest.startswith("[") or not seg_rest.endswith("]"):
                    return (
                        f"Class Chain 节点 '{seg_m.group(1)}' 后存在未包裹在方括号 '[]' 内的非法多余字符: '{seg_rest}'",
                        f"**/{seg_m.group(1)}[`name == '确定'`]",
                    )
                for bt_m in re.finditer(r"\[\s*[`$]([^`$]*)[`$]\s*\]", seg_rest):
                    inner_p_err, inner_p_ex = validate_ios_selector_syntax("predicate", bt_m.group(1))
                    if inner_p_err:
                        inner_fallback = inner_p_ex if inner_p_ex else "name == '确定'"
                        return (
                            f"Class Chain 嵌套 Predicate 语法错误: {inner_p_err}",
                            f"**/{seg_m.group(1)}[`{inner_fallback}`]",
                        )
        return None, ""

    return None, ""
