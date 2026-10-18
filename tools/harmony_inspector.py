import base64
import json
import os
import re
import subprocess
import sys
import time
import webbrowser
from typing import Any, Dict, List, Optional


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


def flatten_components(node: Dict[str, Any], result: List[Dict[str, Any]], depth: int = 0) -> None:
    """递归展开布局树所有节点，解析物理坐标"""
    attrs = node.get("attributes", {})
    bounds_str = attrs.get("bounds", "[0,0][0,0]")
    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    left, top, right, bottom = 0, 0, 0, 0
    if match:
        left, top, right, bottom = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))

    width = max(0, right - left)
    height = max(0, bottom - top)

    # 过滤无效或全屏不可交互容器
    if width > 0 and height > 0:
        c_id = attrs.get("id") or attrs.get("key") or ""
        text = attrs.get("text") or attrs.get("originalText") or ""
        c_type = attrs.get("type", "Component")

        # 生成推荐的 Python 自动化定位器
        locator_id = f'(AppiumBy.ID, "{c_id}")' if c_id else ""
        if text:
            locator_xpath = f'(AppiumBy.XPATH, \'//{c_type}[@text="{text}"]\')'
        elif c_id:
            locator_xpath = f'(AppiumBy.XPATH, \'//*[@id="{c_id}"]\')'
        else:
            locator_xpath = f'(AppiumBy.XPATH, \'//{c_type}\')'

        result.append({
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "width": width,
            "height": height,
            "type": c_type,
            "id": c_id,
            "text": text,
            "visible": attrs.get("visible", "true"),
            "enabled": attrs.get("enabled", "true"),
            "locator_id": locator_id,
            "locator_xpath": locator_xpath,
            "raw_attributes": attrs
        })

    for child in node.get("children", []):
        flatten_components(child, result, depth + 1)


def generate_inspector_html(img_b64: str, components: List[Dict[str, Any]], width: int, height: int, out_html: str) -> None:
    """生成完全媲美 Appium Inspector 的现代化交互式审查网页"""
    components_json = json.dumps(components, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>HarmonyOS UI Inspector - 鸿蒙元素审查器</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #18181c;
            color: #efefef;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        /* 左侧截图区 */
        .preview-pane {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            background: #101014;
            overflow: auto;
        }}
        .phone-wrapper {{
            position: relative;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8);
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid #2d2d35;
        }}
        .phone-img {{
            display: block;
            max-height: 88vh;
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
            border: 1px solid rgba(59, 130, 246, 0.5);
            background: rgba(59, 130, 246, 0.08);
            pointer-events: auto;
            cursor: pointer;
            transition: all 0.15s ease;
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

        /* 右侧面板 */
        .info-pane {{
            width: 440px;
            background: #1e1e24;
            border-left: 1px solid #2d2d35;
            display: flex;
            flex-direction: column;
        }}
        .header {{
            padding: 16px 20px;
            border-bottom: 1px solid #2d2d35;
            font-size: 15px;
            font-weight: 600;
            color: #60a5fa;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .tag {{
            background: #2563eb;
            color: white;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .content {{
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        }}
        .card {{
            background: #26262f;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 16px;
            border: 1px solid #33333f;
        }}
        .card-title {{
            font-size: 12px;
            font-weight: 600;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        .code-row {{
            margin-bottom: 10px;
        }}
        .code-label {{
            font-size: 12px;
            color: #a1a1aa;
            margin-bottom: 4px;
        }}
        .code-box {{
            background: #141418;
            padding: 8px 10px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 13px;
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
            border-bottom: 1px solid #33333f;
        }}
        .attr-name {{
            color: #9ca3af;
            width: 90px;
            word-break: break-word;
        }}
        .attr-val {{
            color: #e4e4e7;
            font-family: monospace;
            word-break: break-all;
        }}
        .hint {{
            color: #71717a;
            font-size: 13px;
            text-align: center;
            margin-top: 50px;
        }}
    </style>
</head>
<body>
    <div class="preview-pane">
        <div class="phone-wrapper" id="phoneWrapper">
            <img src="{img_b64}" class="phone-img" id="phoneImg" alt="Device Screen">
            <div class="overlay-layer" id="overlay"></div>
        </div>
    </div>
    <div class="info-pane">
        <div class="header">
            <span>鸿蒙元素审查器 (Inspector)</span>
            <span class="tag">HarmonyOS NEXT</span>
        </div>
        <div class="content" id="detailContent">
            <div class="hint">👈 请在左侧手机截图中点击任意元素进行检视</div>
        </div>
    </div>

    <script>
        const components = {components_json};
        const origWidth = {width};
        const origHeight = {height};
        const overlay = document.getElementById("overlay");
        const phoneImg = document.getElementById("phoneImg");
        const detailContent = document.getElementById("detailContent");

        phoneImg.onload = function() {{
            renderBoxes();
        }};
        if (phoneImg.complete) {{
            renderBoxes();
        }}
        window.onresize = renderBoxes;

        function renderBoxes() {{
            overlay.innerHTML = "";
            const rect = phoneImg.getBoundingClientRect();
            const scaleX = rect.width / origWidth;
            const scaleY = rect.height / origHeight;

            components.forEach((comp, idx) => {{
                const box = document.createElement("div");
                box.className = "element-box";
                box.style.left = (comp.left * scaleX) + "px";
                box.style.top = (comp.top * scaleY) + "px";
                box.style.width = (comp.width * scaleX) + "px";
                box.style.height = (comp.height * scaleY) + "px";
                box.title = comp.type + (comp.text ? `: "${{comp.text}}"` : "");

                box.onclick = (e) => {{
                    e.stopPropagation();
                    document.querySelectorAll(".element-box").forEach(b => b.classList.remove("selected"));
                    box.classList.add("selected");
                    showDetail(comp);
                }};

                overlay.appendChild(box);
            }});
        }}

        function copyToClip(text) {{
            navigator.clipboard.writeText(text).then(() => {{
                alert("已复制到剪贴板: " + text);
            }});
        }}

        function showDetail(comp) {{
            let codeHtml = "";
            if (comp.locator_id) {{
                codeHtml += `
                    <div class="code-row">
                        <div class="code-label">推荐 ID 定位:</div>
                        <div class="code-box">
                            <span>${{comp.locator_id}}</span>
                            <button class="copy-btn" onclick="copyToClip('${{comp.locator_id}}')">复制</button>
                        </div>
                    </div>`;
            }}
            codeHtml += `
                <div class="code-row">
                    <div class="code-label">推荐 XPath 定位:</div>
                    <div class="code-box">
                        <span>${{comp.locator_xpath}}</span>
                        <button class="copy-btn" onclick="copyToClip('${{comp.locator_xpath}}')">复制</button>
                    </div>
                </div>`;

            let attrHtml = "";
            for (let [k, v] of Object.entries(comp.raw_attributes)) {{
                attrHtml += `<tr><td class="attr-name">${{k}}</td><td class="attr-val">${{v}}</td></tr>`;
            }}

            detailContent.innerHTML = `
                <div class="card">
                    <div class="card-title">🚀 自动化测试代码生成</div>
                    ${{codeHtml}}
                </div>
                <div class="card">
                    <div class="card-title">📌 组件基础属性</div>
                    <table class="attr-table">
                        <tr><td class="attr-name">Component Type</td><td class="attr-val">${{comp.type}}</td></tr>
                        <tr><td class="attr-name">ID / Key</td><td class="attr-val">${{comp.id || '-'}}</td></tr>
                        <tr><td class="attr-name">Text</td><td class="attr-val">${{comp.text || '-'}}</td></tr>
                        <tr><td class="attr-name">Bounds</td><td class="attr-val">[${{comp.left}},${{comp.top}}][${{comp.right}},${{comp.bottom}}]</td></tr>
                        <tr><td class="attr-name">Size</td><td class="attr-val">${{comp.width}} × ${{comp.height}}</td></tr>
                    </table>
                </div>
                <div class="card">
                    <div class="card-title">🔍 全部原始属性 (Raw Attributes)</div>
                    <table class="attr-table">
                        ${{attrHtml}}
                    </table>
                </div>
            `;
        }}
    </script>
</body>
</html>"""
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    print("=" * 60)
    print(" 🚀 HarmonyOS UI Inspector (鸿蒙应用元素审查工具)")
    print("=" * 60)

    udid = get_connected_device()
    if not udid:
        print("❌ 未检测到在线的鸿蒙设备，请确认已开启 USB 调试且已执行 hdc list targets")
        sys.exit(1)

    print(f"✅ 目标鸿蒙设备: {udid}")
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "inspector")
    os.makedirs(tmp_dir, exist_ok=True)

    # 1. 设备端抓取截图与 DOM 树
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

    # 3. 读取屏幕分辨率与组件信息
    try:
        from PIL import Image
        with Image.open(local_png) as im:
            screen_w, screen_h = im.size
    except Exception:
        screen_w, screen_h = 1080, 2400

    with open(local_json, "r", encoding="utf-8") as f:
        layout_data = json.load(f)

    flat_components = []
    flatten_components(layout_data, flat_components)
    print(f"🔍 成功解析出 {len(flat_components)} 个可交互 UI 组件节点")

    # 4. 生成可视化审查网页并自动打开
    out_html = os.path.join(tmp_dir, "harmony_inspector.html")
    generate_inspector_html(img_uri, flat_components, screen_w, screen_h, out_html)

    print(f"✨ 审查页面生成成功: {out_html}")
    print("🌐 正在自动为您打开可视化审查器...")
    webbrowser.open(f"file:///{os.path.abspath(out_html).replace(os.sep, '/')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
