# -*- coding: utf-8 -*-
"""
XPath 高级扩展函数注册与跨端静态语法校验引擎：
1. 为 lxml 注册 XPath 2.0 扩展函数 (matches / lower-case / upper-case / ends-with)；
2. 提供零外部依赖 + lxml 双重兜底的 validate_xpath_syntax 中文诊断校验。
"""
import re
from typing import List, Optional

_LXML_EXTENSIONS_REGISTERED: bool = False


def init_lxml_xpath_extensions() -> None:
    """为 lxml 注册高级扩展函数 (matches 正则、lower-case、upper-case、ends-with)"""
    global _LXML_EXTENSIONS_REGISTERED
    if _LXML_EXTENSIONS_REGISTERED:
        return
    try:
        from lxml import etree

        ns = etree.FunctionNamespace(None)

        def xpath_matches(context, text_arg, pattern_arg, flags_arg=""):
            try:
                if isinstance(text_arg, list):
                    if not text_arg:
                        return False
                    first = text_arg[0]
                    target_str = str(getattr(first, "text", first) or "")
                else:
                    target_str = str(text_arg or "")
                pattern = str(pattern_arg or "")
                py_flags = 0
                f = str(flags_arg).lower()
                if "i" in f:
                    py_flags |= re.IGNORECASE
                if "s" in f:
                    py_flags |= re.DOTALL
                if "m" in f:
                    py_flags |= re.MULTILINE
                return bool(re.search(pattern, target_str, py_flags))
            except Exception:
                return False

        def xpath_lower_case(context, text_arg):
            if isinstance(text_arg, list):
                s = str(getattr(text_arg[0], "text", text_arg[0]) or "") if text_arg else ""
            else:
                s = str(text_arg or "")
            return s.lower()

        def xpath_upper_case(context, text_arg):
            if isinstance(text_arg, list):
                s = str(getattr(text_arg[0], "text", text_arg[0]) or "") if text_arg else ""
            else:
                s = str(text_arg or "")
            return s.upper()

        def xpath_ends_with(context, text_arg, sub_arg):
            if isinstance(text_arg, list):
                s = str(getattr(text_arg[0], "text", text_arg[0]) or "") if text_arg else ""
            else:
                s = str(text_arg or "")
            return s.endswith(str(sub_arg or ""))

        ns["matches"] = xpath_matches
        ns["lower-case"] = xpath_lower_case
        ns["upper-case"] = xpath_upper_case
        ns["ends-with"] = xpath_ends_with
        _LXML_EXTENSIONS_REGISTERED = True
    except Exception:
        pass


_init_lxml_xpath_extensions = init_lxml_xpath_extensions
init_lxml_xpath_extensions()


def validate_xpath_syntax(xpath_str: str) -> Optional[str]:
    """
    全方位校验 XPath 表达式语法合法性（纯 Python + lxml 双重兜底）。
    合法返回 None；若存在语法错误则返回中文诊断描述。
    """
    if not xpath_str or not xpath_str.strip():
        return "XPath 表达式不能为空"

    xp = xpath_str.strip()

    # 1. 检查单双引号闭合与方括号/圆括号配对
    in_single_quote = False
    in_double_quote = False
    bracket_stack: List[int] = []
    paren_stack: List[int] = []

    for idx, ch in enumerate(xp):
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if ch == "[":
                bracket_stack.append(idx)
            elif ch == "]":
                if not bracket_stack:
                    return f"第 {idx + 1} 个字符处方括号 ']' 提前闭合，缺少对应的 '['"
                bracket_stack.pop()
            elif ch == "(":
                paren_stack.append(idx)
            elif ch == ")":
                if not paren_stack:
                    return f"第 {idx + 1} 个字符处圆括号 ')' 提前闭合，缺少对应的 '('"
                paren_stack.pop()

    if in_single_quote:
        return "单引号 ''' 未闭合，字符串缺少结束单引号"
    if in_double_quote:
        return '双引号 \'"\' 未闭合，字符串缺少结束双引号'
    if bracket_stack:
        return f"第 {bracket_stack[-1] + 1} 个字符处方括号 '[' 未闭合，缺少对应的 ']'"
    if paren_stack:
        return f"第 {paren_stack[-1] + 1} 个字符处圆括号 '(' 未闭合，缺少对应的 ')'"

    # 2. 检查顶层联合操作符 '|'
    union_parts: List[str] = []
    u_buf: List[str] = []
    u_b_level = 0
    u_p_level = 0
    u_in_sq = False
    u_in_dq = False

    for ch in xp:
        if ch == "'" and not u_in_dq:
            u_in_sq = not u_in_sq
            u_buf.append(ch)
        elif ch == '"' and not u_in_sq:
            u_in_dq = not u_in_dq
            u_buf.append(ch)
        elif not u_in_sq and not u_in_dq:
            if ch == "[":
                u_b_level += 1
                u_buf.append(ch)
            elif ch == "]":
                u_b_level = max(0, u_b_level - 1)
                u_buf.append(ch)
            elif ch == "(":
                u_p_level += 1
                u_buf.append(ch)
            elif ch == ")":
                u_p_level = max(0, u_p_level - 1)
                u_buf.append(ch)
            elif ch == "|" and u_b_level == 0 and u_p_level == 0:
                union_parts.append("".join(u_buf).strip())
                u_buf = []
            else:
                u_buf.append(ch)
        else:
            u_buf.append(ch)

    union_parts.append("".join(u_buf).strip())

    if len(union_parts) > 1:
        for p_idx, part in enumerate(union_parts):
            if not part:
                return "联合操作符 '|' 前后缺少有效的路径表达式"
            sub_err = validate_xpath_syntax(part)
            if sub_err:
                return f"联合表达式分支 [{p_idx + 1}] 语法错误: {sub_err}"
        return None

    # 3. 检查空谓语 [] 与非法连续三个斜杠 ///
    i = 0
    in_sq = False
    in_dq = False
    while i < len(xp):
        ch = xp[i]
        if ch == "'" and not in_dq:
            in_sq = not in_sq
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
        elif not in_sq and not in_dq:
            if xp[i : i + 2] == "[]":
                return "谓语方括号 '[]' 内部不能为空"
            if xp[i : i + 3] == "///":
                return f"第 {i + 1} 个字符处存在非法的连续三个斜杠 '///'"
        i += 1

    # 4. 剥离外层圆括号包装并检查路径前缀
    base_xp = xp
    while base_xp.startswith("(") and ")" in base_xp:
        p_depth = 0
        match_paren_idx = -1
        in_s = False
        in_d = False
        for idx, ch in enumerate(base_xp):
            if ch == "'" and not in_d:
                in_s = not in_s
            elif ch == '"' and not in_s:
                in_d = not in_d
            elif not in_s and not in_d:
                if ch == "(":
                    p_depth += 1
                elif ch == ")":
                    p_depth -= 1
                    if p_depth == 0:
                        match_paren_idx = idx
                        break
        if match_paren_idx == -1:
            return "XPath 表达式圆括号 '(' 与 ')' 未正确配对闭合"
        inner_content = base_xp[1:match_paren_idx].strip()
        outer_pred = base_xp[match_paren_idx + 1 :].strip()
        if outer_pred and not (outer_pred.startswith("[") or outer_pred.startswith("/")):
            return f"圆括号表达式后存在非法字符或空格: '{outer_pred}'"
        base_xp = inner_content

    if not (base_xp.startswith("/") or base_xp.startswith(".")):
        return "XPath 必须以 '/'、'//' 或 '.' 开头 (例如: //Text 或 /root)"

    if len(base_xp) > 1 and base_xp.endswith("/"):
        return "XPath 不能以悬空斜杠 '/' 或 '//' 结尾"

    # 5. 拆分步进并逐一校验
    steps: List[str] = []
    i = 0
    n = len(base_xp)
    if base_xp.startswith("//"):
        i = 2
    elif base_xp.startswith("/"):
        i = 1

    buf: List[str] = []
    b_level = 0
    p_level = 0
    in_sq = False
    in_dq = False

    while i < n:
        ch = base_xp[i]
        if ch == "'" and not in_dq:
            in_sq = not in_sq
            buf.append(ch)
            i += 1
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
            buf.append(ch)
            i += 1
        elif not in_sq and not in_dq:
            if ch == "[":
                b_level += 1
                buf.append(ch)
                i += 1
            elif ch == "]":
                b_level = max(0, b_level - 1)
                buf.append(ch)
                i += 1
            elif ch == "(":
                p_level += 1
                buf.append(ch)
                i += 1
            elif ch == ")":
                p_level = max(0, p_level - 1)
                buf.append(ch)
                i += 1
            elif b_level == 0 and p_level == 0 and base_xp[i : i + 2] == "//":
                seg = "".join(buf).strip()
                if not seg:
                    return "连续斜杠之间缺少有效的节点测试步进"
                steps.append(seg)
                buf = []
                i += 2
            elif b_level == 0 and p_level == 0 and base_xp[i : i + 1] == "/":
                seg = "".join(buf).strip()
                if not seg:
                    return "连续斜杠之间缺少有效的节点测试步进"
                steps.append(seg)
                buf = []
                i += 1
            else:
                buf.append(ch)
                i += 1
        else:
            buf.append(ch)
            i += 1

    last_seg = "".join(buf).strip()
    if last_seg:
        steps.append(last_seg)
    elif not steps and base_xp not in ("/", "//"):
        return "XPath 缺少有效的节点测试步进"

    valid_axes = {
        "ancestor", "ancestor-or-self", "attribute", "child", "descendant",
        "descendant-or-self", "following", "following-sibling", "namespace",
        "parent", "preceding", "preceding-sibling", "self",
    }

    for step in steps:
        tag_and_pred = step
        if "::" in step:
            parts = step.split("::", 1)
            axis = parts[0].strip().lower()
            rest = parts[1].strip()
            if axis not in valid_axes:
                return f"未知的 XPath 轴名称 '{parts[0]}'，标准轴包括: following-sibling, preceding-sibling, parent, ancestor 等"
            if not rest:
                return f"轴 '{parts[0]}::' 后面缺少节点测试（如组件标签名或 '*'）"
            tag_and_pred = rest

        m = re.match(r"^([a-zA-Z0-9_\-\*]+|\.\.|\.|node\(\)|text\(\))(.*)$", tag_and_pred)
        if not m:
            return f"步进 '{step}' 的节点名格式非法，组件标签名只能包含字母、数字、下划线、中划线或通配符 '*'"

        tag_name = m.group(1)
        rest_part = m.group(2)

        if rest_part:
            rest_part_stripped = rest_part.strip()
            if rest_part_stripped and not rest_part_stripped.startswith("["):
                return f"节点 '{tag_name}' 后面存在未用方括号 '[]' 包裹的非法字符或空格: '{rest_part_stripped}'"

            pred_list: List[str] = []
            p_buf: List[str] = []
            p_depth = 0
            p_in_sq = False
            p_in_dq = False
            for ch in rest_part:
                if ch == "'" and not p_in_dq:
                    p_in_sq = not p_in_sq
                    p_buf.append(ch)
                elif ch == '"' and not p_in_sq:
                    p_in_dq = not p_in_dq
                    p_buf.append(ch)
                elif not p_in_sq and not p_in_dq:
                    if ch == "[":
                        if p_depth > 0:
                            p_buf.append(ch)
                        p_depth += 1
                    elif ch == "]":
                        p_depth -= 1
                        if p_depth == 0:
                            pred_list.append("".join(p_buf).strip())
                            p_buf = []
                        else:
                            p_buf.append(ch)
                    else:
                        if p_depth > 0:
                            p_buf.append(ch)
                        elif ch.strip():
                            return f"方括号谓语后存在非法字符 '{ch}'，谓语之间不能有孤立字符"
                else:
                    p_buf.append(ch)

            for p_content in pred_list:
                if not p_content:
                    return "谓语方括号 '[]' 内部不能为空"
                if p_content == "@":
                    return "属性选择符 '@' 后面缺少属性名，例如 [@text='...']"

                if re.match(r"^[a-zA-Z0-9_\-]+$", p_content):
                    if p_content.isdigit():
                        if int(p_content) <= 0:
                            return f"XPath 索引从 1 开始计数，不能使用 0 或负数 '[{p_content}]'"
                    elif p_content in ("last()", "position()", "true()", "false()"):
                        pass
                    elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_\-]*$", p_content):
                        pass
                    else:
                        return (
                            f"谓语 '[{p_content}]' 语法异常：'{p_content}' 格式非法，"
                            f"既非有效数字索引，也非合法子元素标签或属性过滤，请检查是否拼写错误"
                        )

                is_compound_expr = any(op in p_content for op in (" and ", " or ", ">=", "<=", "!="))
                if (
                    "=" in p_content
                    and not is_compound_expr
                    and not any(p_content.startswith(fn) for fn in ["contains", "starts-with", "not", "count"])
                ):
                    eq_parts = p_content.split("=", 1)
                    left = eq_parts[0].strip()
                    right = eq_parts[1].strip()
                    if not left:
                        return f"谓语 '{p_content}' 等号左侧缺少属性名"
                    if not right:
                        return f"谓语 '{p_content}' 等号右侧缺少对比值，例如 @text='标题'"
                    if not (
                        right.isdigit()
                        or right.startswith("'")
                        or right.startswith('"')
                        or right in ("true()", "false()", "last()")
                    ):
                        if " " in right or not re.match(r"^[a-zA-Z0-9_\-]+$", right):
                            return f"谓语属性值 '{right}' 缺少引号包裹，字符串属性值必须用单引号或双引号包裹"

                if "contains" in p_content:
                    m_c = re.search(r"contains\s*\((.*?)\)", p_content)
                    if m_c:
                        c_args = [arg.strip() for arg in m_c.group(1).split(",")]
                        if len(c_args) < 2 or not c_args[0] or not c_args[1]:
                            return "contains() 函数需要 2 个参数，格式如: contains(@text, '关键字')"

                if p_content.startswith((".", "//", "/")) and not is_compound_expr:
                    sub_err = validate_xpath_syntax(p_content)
                    if sub_err:
                        return f"嵌套谓语 '[{p_content}]' 内部语法错误: {sub_err}"

    # 6. lxml 最终深度校验
    try:
        init_lxml_xpath_extensions()
        from lxml import etree

        etree.XPath(xp)
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception as e:
        lxml_err = str(e)
        if "Invalid expression" in lxml_err:
            return "XPath 表达式语法非法 (Invalid expression)"
        if "Invalid predicate" in lxml_err:
            return "XPath 谓语语法非法 (Invalid predicate)"
        if "Undefined namespace" in lxml_err:
            return "未定义的命名空间前缀"
        if "Unregistered function" in lxml_err:
            m_fn = re.search(r"([a-zA-Z_\-]+)\s*\(", xp)
            fn_name = m_fn.group(1) if m_fn else "所调用的"
            return (
                f"不支持的 XPath 函数 '{fn_name}()' (Unregistered function)："
                f"请核对函数名拼写，当前支持 matches()、contains()、starts-with()、ends-with()、lower-case()、upper-case() 等"
            )
        return f"XPath 语法错误: {lxml_err}"

    return None
