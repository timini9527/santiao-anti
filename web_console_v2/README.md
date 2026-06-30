# Web Console V2

面向非开发人员的 Santiao 自动化测试 Web 控制台重构版。

此目录是独立新增工程，不替换原有 `templates/web_runner.py` 和 `templates/index.html`。

## 目录

```text
web_console_v2/
  backend/      FastAPI 后端，负责发现用例、执行 pytest、推送日志
  frontend/     Vue 3 + Vite + Element Plus 前端控制台
  runtime/      运行时产物目录，启动后自动生成
```

## 后端启动

```powershell
cd D:\projects\santiao-anti\web_console_v2\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

后端默认会把项目根目录识别为 `web_console_v2` 的上一级目录，即 `D:\projects\santiao-anti`。
如需指定其他项目根目录：

```powershell
$env:SANTIAO_PROJECT_ROOT="D:\projects\santiao-anti"
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

## 前端启动

```powershell
cd D:\projects\santiao-anti\web_console_v2\frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

浏览器访问：

```text
http://localhost:5173
```

局域网访问时，把 `localhost` 换成运行机器的 IP。

## 主要能力

- 自动扫描 `tests/` 下的 pytest 用例。
- 以模块/文件/类/函数展示用例树。
- 支持搜索用例名、nodeid、文件路径。
- 支持配置环境、Appium 地址、设备 UDID、聊天对象等运行参数。
- 单条用例执行。
- 实时日志推送。
- 执行中停止任务。
- 查看最近执行历史。

## 注意事项

- 当前版本先做可运行骨架，不内置登录和权限。
- 同一台设备/Appium 通常不适合多人同时执行；后端默认同一时间只允许一个任务运行。
- pytest、Appium、设备连接和项目依赖仍沿用原项目环境。
- Allure 结果默认输出到 `web_console_v2/runtime/reports/<task_id>/allure-results`。
- 项目现有 hook 仍可能写入原项目的 `logs/`、`screenshots/`、`.pytest_cache` 等目录。
