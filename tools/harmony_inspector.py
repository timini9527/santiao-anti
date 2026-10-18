import base64
import json
import os
import re
import subprocess
import sys
import webbrowser
from typing import Any, Dict, List, Tuple


def get_connected_device() -> str:
    """动态获取当前连接的鸿蒙设备 UDID"""
    try:
        out = subprocess.check_output(["hdc", "list", "targets"], text=True, errors="ignore").strip()
        lines = [line.strip() for line in out.splitlines() if line.strip() and "empty" not in line.lower()]
        if lines:
            return lines[0]
    except Exception:
        pass
    # 兜底读取 devices.yaml
    try:
        import yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "devices.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("devices", {}).get("dev", {}).get("harmony_sender", {}).get("udid", "")
    except Exception:
        pass
    return ""


def run_hdc(cmd: List[str], udid: str = "") -> str:
    """执行 HDC 指令"""
    full_cmd = ["hdc"]
    if udid:
        full_cmd.extend(["-t", udid])
    full_cmd.extend(cmd)
    res = subprocess.run(full_cmd, capture_output=True, text=True, errors="ignore")
    return res.stdout.strip()


_node_counter = 0


def build_dom_tree(raw_node: Dict[str, Any], depth: int = 0) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    为鸿蒙 ArkUI 节点递归赋予唯一 node_id，同时生成嵌套 DOM 树和扁平化坐标索引
    """
    global _node_counter
    current_id = f"node_{_node_counter}"
    _node_counter += 1

    attrs = raw_node.get("attributes", {})
    bounds_str = attrs.get("bounds", "[0,0][0,0]")
    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    left, top, right, bottom = 0, 0, 0, 0
    if match:
        left, top, right, bottom = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))

    width = max(0, right - left)
    height = max(0, bottom - top)

    c_id = attrs.get("id") or attrs.get("key") or ""
    text = attrs.get("text") or attrs.get("originalText") or ""
    c_type = attrs.get("type", "Component")

    # 生成推荐定位代码
    locator_id = f'(AppiumBy.ID, "{c_id}")' if c_id else ""
    if text:
        locator_xpath = f'(AppiumBy.XPATH, \'//{c_type}[@text="{text}"]\')'
    elif c_id:
        locator_xpath = f'(AppiumBy.XPATH, \'//*[@id="{c_id}"]\')'
    else:
        locator_xpath = f'(AppiumBy.XPATH, \'//{c_type}\')'

    comp_info = {
        "node_id": current_id,
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": width,
        "height": height,
        "type": c_type,
        "id": c_id,
        "text": text,
        "depth": depth,
        "visible": attrs.get("visible", "true"),
        "enabled": attrs.get("enabled", "true"),
        "clickable": attrs.get("clickable", "false"),
        "locator_id": locator_id,
        "locator_xpath": locator_xpath,
        "raw_attributes": attrs
    }

    flat_list = []
    if width > 0 and height > 0:
        flat_list.append(comp_info)

    tree_node = {
        "node_id": current_id,
        "type": c_type,
        "id": c_id,
        "text": text,
        "comp_info": comp_info,
        "children": []
    }

    for child in raw_node.get("children", []):
        sub_tree, sub_flats = build_dom_tree(child, depth + 1)
        tree_node["children"].append(sub_tree)
        flat_list.extend(sub_flats)

    return tree_node, flat_list


def generate_inspector_html(img_b64: str, dom_tree: Dict[str, Any], flat_components: List[Dict[str, Any]],
                            width: int, height: int, out_html: str) -> None:
    """生成具备三栏联动、DOM 层级树折叠与 XPath / ID 实时搜索匹配的 Inspector 页面"""
    dom_tree_json = json.dumps(dom_tree, ensure_ascii=False)
    flat_json = json.dumps(flat_components, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>HarmonyOS Appium Inspector - 鸿蒙层级树与元素审查器</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #141417;
            color: #e4e4e7;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }}
        /* 顶部工具栏与搜索区 */
        .topbar {{
            height: 52px;
            background: #1c1c21;
            border-bottom: 1px solid #2d2d35;
            display: flex;
            align-items: center;
            padding: 0 16px;
            gap: 12px;
            flex-shrink: 0;
        }}
        .brand {{
            font-weight: 700;
            font-size: 15px;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-right: 12px;
        }}
        .search-container {{
            display: flex;
            align-items: center;
            background: #27272f;
            border: 1px solid #3f3f4e;
            border-radius: 6px;
            padding: 2px 8px;
            flex: 1;
            max-width: 650px;
        }}
        .search-select {{
            background: transparent;
            border: none;
            color: #a1a1aa;
            font-size: 12px;
            padding: 4px 6px;
            outline: none;
            cursor: pointer;
            border-right: 1px solid #3f3f4e;
            margin-right: 6px;
        }}
        .search-input {{
            background: transparent;
            border: none;
            color: #fafafa;
            font-size: 13px;
            font-family: monospace;
            padding: 4px 8px;
            flex: 1;
            outline: none;
        }}
        .search-btn {{
            background: #2563eb;
            color: #fff;
            border: none;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s;
        }}
        .search-btn:hover {{ background: #1d4ed8; }}
        .search-count {{
            font-size: 12px;
            color: #eab308;
            margin-left: 8px;
            font-weight: 500;
        }}

        /* 主体三栏布局 */
        .main-container {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}

        /* 左栏：截图区域 */
        .pane-screen {{
            flex: 1.1;
            background: #0d0d11;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
            overflow: auto;
            border-right: 1px solid #2d2d35;
        }}
        .phone-wrapper {{
            position: relative;
            box-shadow: 0 8px 32px rgba(0,0,0,0.8);
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid #27272e;
        }}
        .phone-img {{
            display: block;
            max-height: 86vh;
            width: auto;
            user-select: none;
        }}
        .overlay-layer {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }}
        .element-box {{
            position: absolute;
            border: 1px solid rgba(56, 189, 248, 0.4);
            background: rgba(56, 189, 248, 0.05);
            pointer-events: auto;
            cursor: pointer;
            transition: all 0.1s ease;
        }}
        .element-box:hover {{
            background: rgba(234, 179, 8, 0.25);
            border: 2px solid #eab308;
            z-index: 10;
        }}
        .element-box.selected {{
            background: rgba(239, 68, 68, 0.35);
            border: 2px solid #ef4444;
            z-index: 20;
        }}
        .element-box.search-match {{
            border: 2px dashed #22c55e !important;
            background: rgba(34, 197, 94, 0.25) !important;
            z-index: 15;
        }}

        /* 中栏：DOM 层级树 (App Source) */
        .pane-tree {{
            flex: 1.2;
            background: #18181d;
            border-right: 1px solid #2d2d35;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        .pane-header {{
            padding: 12px 16px;
            font-size: 13px;
            font-weight: 600;
            color: #a1a1aa;
            border-bottom: 1px solid #27272e;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .tree-scroll {{
            padding: 12px 8px;
            overflow-y: auto;
            flex: 1;
            font-family: monospace;
            font-size: 12px;
        }}
        .tree-node {{
            margin-left: 14px;
            user-select: none;
        }}
        .node-row {{
            display: flex;
            align-items: center;
            padding: 3px 6px;
            border-radius: 4px;
            cursor: pointer;
            white-space: nowrap;
        }}
        .node-row:hover {{ background: #26262f; }}
        .node-row.selected {{
            background: #3b82f6 !important;
            color: #ffffff !important;
        }}
        .node-row.search-hit {{
            background: #14532d;
            border: 1px solid #22c55e;
            color: #86efac;
        }}
        .toggle-arrow {{
            width: 14px;
            display: inline-block;
            cursor: pointer;
            color: #71717a;
            font-size: 10px;
        }}
        .tag-name {{ color: #38bdf8; font-weight: 600; }}
        .tag-attr-id {{ color: #a78bfa; margin-left: 6px; }}
        .tag-attr-text {{ color: #fbbf24; margin-left: 6px; }}

        /* 右栏：属性与代码生成 */
        .pane-attr {{
            width: 420px;
            background: #1c1c21;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        .attr-scroll {{
            padding: 16px;
            overflow-y: auto;
            flex: 1;
        }}
        .card {{
            background: #24242c;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 14px;
            border: 1px solid #32323d;
        }}
        .card-title {{
            font-size: 12px;
            font-weight: 600;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        .code-row {{ margin-bottom: 8px; }}
        .code-label {{ font-size: 11px; color: #a1a1aa; margin-bottom: 4px; }}
        .code-box {{
            background: #131316;
            padding: 8px 10px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 12px;
            color: #38bdf8;
            border: 1px solid #27272a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            word-break: break-all;
        }}
        .copy-btn {{
            background: #3f3f46;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
            margin-left: 8px;
            flex-shrink: 0;
        }}
        .copy-btn:hover {{ background: #2563eb; }}
        .attr-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}
        .attr-table td {{
            padding: 6px 4px;
            border-bottom: 1px solid #2d2d35;
        }}
        .attr-k {{ color: #9ca3af; width: 100px; }}
        .attr-v {{ color: #e4e4e7; font-family: monospace; word-break: break-all; }}
        .empty-hint {{
            color: #71717a;
            font-size: 13px;
            text-align: center;
            margin-top: 60px;
        }}
    </style>
</head>
<body>
    <!-- 顶部定位器调试与搜索 -->
    <div class="topbar">
        <div class="brand">
            <span>鸿蒙 Appium Inspector</span>
        </div>
        <div class="search-container">
            <select class="search-select" id="searchType">
                <option value="xpath">XPath 表达式</option>
                <option value="id">ID / Key 定位</option>
                <option value="text">Text 文本内容</option>
            </select>
            <input type="text" class="search-input" id="searchInput" placeholder="例: //Text[@text='三条'] 或 //List/ListItem 或 rooter" />
            <button class="search-btn" onclick="doSearch()">在树中定位</button>
        </div>
        <div class="search-count" id="searchCount"></div>
    </div>

    <div class="main-container">
        <!-- 左栏：设备屏幕画面 -->
        <div class="pane-screen">
            <div class="phone-wrapper" id="phoneWrapper">
                <img src="{img_b64}" class="phone-img" id="phoneImg" alt="Device Screen">
                <div class="overlay-layer" id="overlay"></div>
            </div>
        </div>

        <!-- 中栏：组件层级树 (Hierarchy Tree) -->
        <div class="pane-tree">
            <div class="pane-header">
                <span>组件层次树 (App Source / Hierarchy)</span>
                <div>
                    <button class="copy-btn" onclick="expandAll(true)">展开全部</button>
                    <button class="copy-btn" onclick="expandAll(false)">折叠全部</button>
                </div>
            </div>
            <div class="tree-scroll" id="treeContainer"></div>
        </div>

        <!-- 右栏：元素属性详情与代码生成 -->
        <div class="pane-attr">
            <div class="pane-header">
                <span>选中元素详情 (Selected Element)</span>
            </div>
            <div class="attr-scroll" id="detailPanel">
                <div class="empty-hint">👈 请在中间树形结构或左侧截图中点击选中元素</div>
            </div>
        </div>
    </div>

    <script>
        const domTree = {dom_tree_json};
        const flatComponents = {flat_json};
        const origWidth = {width};
        const origHeight = {height};

        const overlay = document.getElementById("overlay");
        const phoneImg = document.getElementById("phoneImg");
        const treeContainer = document.getElementById("treeContainer");
        const detailPanel = document.getElementById("detailPanel");
        const searchInput = document.getElementById("searchInput");
        const searchType = document.getElementById("searchType");
        const searchCount = document.getElementById("searchCount");

        // 建立 node_id 快速索引字典
        const compMap = {{}};
        flatComponents.forEach(c => compMap[c.node_id] = c);

        phoneImg.onload = () => renderScreenBoxes();
        if (phoneImg.complete) renderScreenBoxes();
        window.onresize = renderScreenBoxes;

        // 1. 渲染截图上的半透明遮罩框
        function renderScreenBoxes() {{
            overlay.innerHTML = "";
            const rect = phoneImg.getBoundingClientRect();
            const scaleX = rect.width / origWidth;
            const scaleY = rect.height / origHeight;

            flatComponents.forEach(comp => {{
                const box = document.createElement("div");
                box.className = "element-box";
                box.id = "box_" + comp.node_id;
                box.style.left = (comp.left * scaleX) + "px";
                box.style.top = (comp.top * scaleY) + "px";
                box.style.width = (comp.width * scaleX) + "px";
                box.style.height = (comp.height * scaleY) + "px";
                box.title = comp.type + (comp.id ? ` #${{comp.id}}` : "") + (comp.text ? ` "${{comp.text}}"` : "");

                box.onclick = (e) => {{
                    e.stopPropagation();
                    selectElement(comp.node_id, true);
                }};

                overlay.appendChild(box);
            }});
        }}

        // 2. 递归构建中间的 DOM 树 HTML
        function renderTreeItem(node) {{
            const div = document.createElement("div");
            div.className = "tree-node";
            div.id = "tree_" + node.node_id;

            const row = document.createElement("div");
            row.className = "node-row";
            row.id = "row_" + node.node_id;

            const hasChildren = node.children && node.children.length > 0;
            const arrow = document.createElement("span");
            arrow.className = "toggle-arrow";
            arrow.innerHTML = hasChildren ? "▼ " : "&nbsp;&nbsp;";
            row.appendChild(arrow);

            const tag = document.createElement("span");
            tag.className = "tag-name";
            tag.textContent = `<${{node.type}}>`;
            row.appendChild(tag);

            if (node.id) {{
                const idSpan = document.createElement("span");
                idSpan.className = "tag-attr-id";
                idSpan.textContent = `id="${{node.id}}"`;
                row.appendChild(idSpan);
            }}

            if (node.text) {{
                const textSpan = document.createElement("span");
                textSpan.className = "tag-attr-text";
                textSpan.textContent = `text="${{node.text.length > 20 ? node.text.substring(0, 20) + '...' : node.text}}"`;
                row.appendChild(textSpan);
            }}

            div.appendChild(row);

            const childContainer = document.createElement("div");
            childContainer.className = "node-children";

            arrow.onclick = (e) => {{
                e.stopPropagation();
                if (childContainer.style.display === "none") {{
                    childContainer.style.display = "block";
                    arrow.innerHTML = "▼ ";
                }} else {{
                    childContainer.style.display = "none";
                    arrow.innerHTML = "▶ ";
                }}
            }};

            row.onclick = (e) => {{
                selectElement(node.node_id, false);
            }};

            if (hasChildren) {{
                node.children.forEach(c => childContainer.appendChild(renderTreeItem(c)));
            }}
            div.appendChild(childContainer);
            return div;
        }}

        // 初始化渲染 DOM 树
        treeContainer.appendChild(renderTreeItem(domTree));

        // 3. 核心双向联动选择逻辑
        function selectElement(nodeId, fromScreen = false) {{
            // 高亮截图红框
            document.querySelectorAll(".element-box").forEach(b => b.classList.remove("selected"));
            const targetBox = document.getElementById("box_" + nodeId);
            if (targetBox) targetBox.classList.add("selected");

            // 高亮树形行
            document.querySelectorAll(".node-row").forEach(r => r.classList.remove("selected"));
            const targetRow = document.getElementById("row_" + nodeId);
            if (targetRow) {{
                targetRow.classList.add("selected");
                // 自动展开祖先节点并滚动到当前行
                let parent = targetRow.parentElement;
                while (parent && parent !== treeContainer) {{
                    if (parent.className === "node-children") parent.style.display = "block";
                    parent = parent.parentElement;
                }}
                targetRow.scrollIntoView({{ behavior: "smooth", block: "center" }});
            }}

            // 渲染右侧属性面板
            const comp = compMap[nodeId];
            if (comp) showAttributes(comp);
        }}

        function showAttributes(comp) {{
            let codeHtml = "";
            if (comp.locator_id) {{
                codeHtml += `
                    <div class="code-row">
                        <div class="code-label">推荐 ID 定位:</div>
                        <div class="code-box">
                            <span>${{comp.locator_id}}</span>
                            <button class="copy-btn" onclick="copyCode('${{comp.locator_id}}')">复制</button>
                        </div>
                    </div>`;
            }}
            codeHtml += `
                <div class="code-row">
                    <div class="code-label">推荐 XPath 定位:</div>
                    <div class="code-box">
                        <span>${{comp.locator_xpath}}</span>
                        <button class="copy-btn" onclick="copyCode('${{comp.locator_xpath}}')">复制</button>
                    </div>
                </div>`;

            let tableHtml = "";
            for (let [k, v] of Object.entries(comp.raw_attributes)) {{
                tableHtml += `<tr><td class="attr-k">${{k}}</td><td class="attr-v">${{v}}</td></tr>`;
            }}

            detailPanel.innerHTML = `
                <div class="card">
                    <div class="card-title">🚀 自动化代码生成 (直接粘贴到 Page Object)</div>
                    ${{codeHtml}}
                </div>
                <div class="card">
                    <div class="card-title">📌 关键属性概览</div>
                    <table class="attr-table">
                        <tr><td class="attr-k">Component Type</td><td class="attr-v">${{comp.type}}</td></tr>
                        <tr><td class="attr-k">id / key</td><td class="attr-v">${{comp.id || '-'}}</td></tr>
                        <tr><td class="attr-k">text / originalText</td><td class="attr-v">${{comp.text || '-'}}</td></tr>
                        <tr><td class="attr-k">bounds</td><td class="attr-v">[${{comp.left}},${{comp.top}}][${{comp.right}},${{comp.bottom}}]</td></tr>
                        <tr><td class="attr-k">size</td><td class="attr-v">${{comp.width}} × ${{comp.height}}</td></tr>
                        <tr><td class="attr-k">clickable</td><td class="attr-v">${{comp.clickable}}</td></tr>
                    </table>
                </div>
                <div class="card">
                    <div class="card-title">🔍 全部原始属性 (Raw Attributes)</div>
                    <table class="attr-table">${{tableHtml}}</table>
                </div>
            `;
        }}

        // 4. 树展开/折叠
        function expandAll(expanded) {{
            document.querySelectorAll(".node-children").forEach(c => {{
                c.style.display = expanded ? "block" : "none";
            }});
            document.querySelectorAll(".toggle-arrow").forEach(a => {{
                if (a.textContent.trim()) a.innerHTML = expanded ? "▼ " : "▶ ";
            }});
        }}

        // 5. XPath / ID 实时定位与树中搜索
        function doSearch() {{
            const val = searchInput.value.trim();
            const mode = searchType.value;
            // 清理旧搜索高亮
            document.querySelectorAll(".node-row").forEach(r => r.classList.remove("search-hit"));
            document.querySelectorAll(".element-box").forEach(b => b.classList.remove("search-match"));
            searchCount.textContent = "";

            if (!val) return;

            let matches = [];

            flatComponents.forEach(comp => {{
                let hit = false;
                if (mode === "id") {{
                    if (comp.id && (comp.id.includes(val) || val.includes(comp.id))) hit = true;
                }} else if (mode === "text") {{
                    if (comp.text && comp.text.includes(val)) hit = true;
                }} else if (mode === "xpath") {{
                    // 简易前端 XPath 解析引擎
                    if (val.includes("@text=")) {{
                        let expText = val.split("@text=")[1].replace(/['"\\]\\]/g, "");
                        if (comp.text === expText) hit = true;
                    }} else if (val.includes("contains(@text")) {{
                        let expSub = val.match(/contains\\(@text,\\s*['"]([^'"]+)['"]\\)/);
                        if (expSub && comp.text && comp.text.includes(expSub[1])) hit = true;
                    }} else if (val.includes("@id=")) {{
                        let expId = val.split("@id=")[1].replace(/['"\\]\\]/g, "");
                        if (comp.id === expId) hit = true;
                    }} else if (val.startsWith("//")) {{
                        let tag = val.replace(/\\/\\//g, "").split("[")[0].trim();
                        if (tag === "*" || comp.type === tag) hit = true;
                    }}
                }}

                if (hit) matches.push(comp);
            }});

            searchCount.textContent = `匹配到 ${{matches.length}} 个元素`;

            if (matches.length > 0) {{
                expandAll(true);
                matches.forEach(m => {{
                    const row = document.getElementById("row_" + m.node_id);
                    if (row) row.classList.add("search-hit");
                    const box = document.getElementById("box_" + m.node_id);
                    if (box) box.classList.add("search-match");
                }});
                // 自动选中第 1 个匹配项
                selectElement(matches[0].node_id);
            }} else {{
                alert("未匹配到符合条件的元素，请检查表达式是否正确");
            }}
        }}

        searchInput.addEventListener("keyup", (e) => {{
            if (e.key === "Enter") doSearch();
        }});

        function copyCode(text) {{
            navigator.clipboard.writeText(text).then(() => alert("已复制到剪贴板:\\n" + text));
        }}
    </script>
</body>
</html>"""
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    print("=" * 60)
    print(" 🚀 HarmonyOS UI Inspector (鸿蒙应用元素审查工具 - 完整版)")
    print("=" * 60)

    udid = get_connected_device()
    if not udid:
        print("❌ 未检测到在线的鸿蒙设备，请确认已开启 USB 调试且已执行 hdc list targets")
        sys.exit(1)

    print(f"✅ 目标鸿蒙设备: {udid}")
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "inspector")
    os.makedirs(tmp_dir, exist_ok=True)

    # 1. 抓取截图与 DOM 树
    print("📸 正在抓取屏幕物理截图...")
    remote_png = "/data/local/tmp/inspector_shot.png"
    run_hdc(["shell", "uitest", "screenCap", "-p", remote_png], udid)
    local_png = os.path.join(tmp_dir, "screen.png")
    run_hdc(["file", "recv", remote_png, local_png], udid)
    run_hdc(["shell", "rm", "-f", remote_png], udid)

    print("🌳 正在抓取 ArkUI 组件树 (dumpLayout)...")
    remote_json = "/data/local/tmp/inspector_layout.json"
    run_hdc(["shell", "uitest", "dumpLayout", "-p", remote_json], udid)
    local_json = os.path.join(tmp_dir, "layout.json")
    run_hdc(["file", "recv", remote_json, local_json], udid)
    run_hdc(["shell", "rm", "-f", remote_json], udid)

    if not os.path.exists(local_png) or not os.path.exists(local_json):
        print("❌ 抓取设备现场失败，请检查手机屏幕是否点亮")
        sys.exit(1)

    # 2. 读取图片 base64
    with open(local_png, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")
    img_uri = f"data:image/png;base64,{b64_data}"

    # 3. 屏幕分辨率与 DOM 层次树构建
    screen_w, screen_h = 1084, 2412
    try:
        from PIL import Image
        with Image.open(local_png) as im:
            screen_w, screen_h = im.size
    except Exception:
        pass

    with open(local_json, "r", encoding="utf-8") as f:
        layout_data = json.load(f)

    dom_tree, flat_components = build_dom_tree(layout_data)
    print(f"🔍 成功构建完整 DOM 层次树，解析出 {len(flat_components)} 个可交互组件节点")

    # 4. 生成三栏联动审查网页并自动打开
    out_html = os.path.join(tmp_dir, "harmony_inspector.html")
    generate_inspector_html(img_uri, dom_tree, flat_components, screen_w, screen_h, out_html)

    print(f"✨ 审查页面生成成功: {out_html}")
    print("🌐 正在自动为您打开可视化审查器...")
    webbrowser.open(f"file:///{os.path.abspath(out_html).replace(os.sep, '/')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
