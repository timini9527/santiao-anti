# 🚀 IM 核心接口高性能压测体系 (`performance/`)

## 1. 架构选型与决策说明

针对类微信 IM 产品的接口压测，截至当前行业最推崇的技术路线为 **Locust + FastHttpUser (基于 geventhttpclient 协程异步驱动)**。

### 为什么选择 Locust + FastHttpUser 而非传统方案？
1. **极限吞吐与极低开销**：传统 JMeter 依赖操作系统线程池，线程切换与内存开销巨大（1000 线程常驻消耗大量内存甚至 OOM）；而 `FastHttpUser` 底层基于 C 编写的 HTTP 解析器与轻量级 Python 协程，单台压测机可轻松承载 5,000~10,000 级并发长短连接请求，资源利用率提升 5~10 倍。
2. **代码即工程 (Code as Test)**：与本项目 Python 自动化测试体系无缝契合，无需在 XML 或 GUI 间痛苦切换，直接复用既有的配置加载、Token 轮换机制与测试数据工厂。
3. **双模自由切换**：
   - **CI/CD 无头模式 (Headless)**：毫秒级输出数据，通过退出码直接卡口阻断。
   - **Web UI 实时交互**：图形化动态调整并发量、观察实时 RPS 折线图与 P50/P95/P99 延迟分位数。

---

## 2. 目录结构规范

```text
performance/
├── config/
│   └── perf_config.yaml         # 【核心】完全配置化接口定义（想测几个接口直接在此增删改）
├── scenarios/
│   └── api_scenarios.py         # 业务场景库（供代码级深度编排使用，可选）
├── locustfile.py                # 动态配置驱动型 Locust 引擎（自动解析 YAML 并生成压测任务）
├── run_perf.py                  # 一键调度脚本（集成 Headless/Web 双模式与报告导出）
├── start_perf_batch.bat         # Windows 一键批量启动集群脚本
├── stop_perf.bat                # Windows 一键清理与释放端口脚本
└── README.md                    # 本文档
```
> **注意**：遵循项目规则，Python 3.11+ / 3.13+ 环境下无需创建 `__init__.py`。

---

## 3. 如何自定义想测的接口？（免写代码 · 想测几个配几个）

打开 [perf_config.yaml](file:///d:/projects/santiao-anti/performance/config/perf_config.yaml)，在 `interfaces` 列表中按需添加接口配置：

```yaml
target:
  host: "http://www.baidu.com"   # 被测目标服务的根地址

interfaces:
  # 接口 1：GET 接口示例
  - name: "百度首页"
    enabled: true                # true 开启，false 关闭
    method: "GET"
    path: "/"
    weight: 3                    # 流量权重比例
    params: {}

  # 接口 2：带查询参数的 GET 接口
  - name: "百度搜索接口"
    enabled: true
    method: "GET"
    path: "/s"
    weight: 1
    params:
      wd: "性能测试"

  # 接口 3：带 JSON Body 的 POST 接口
  - name: "某业务提交接口"
    enabled: true
    method: "POST"
    path: "/api/v1/submit"
    weight: 2
    headers:
      Content-Type: "application/json"
    body:
      id: 1001
      data: "负载测试"
```
> 💡 无论在 YAML 里配 1 个还是 10 个接口，引擎启动时会自动动态装载，完全不需要改动任何 Python 代码！

---

## 3. 环境准备

安装压测核心依赖库（推荐安装 `locust` 及其协程依赖）：

```bash
pip install locust pyyaml
```

---

## 4. 运行方式

### 方式 A：一键无头模式（推荐 CI/CD 流水线与日常回归使用）
直接运行调度脚本，默认以 500 并发执行 1 分钟，并自动生成 HTML / CSV 测试报告：
```bash
python performance/run_perf.py
```

指定并发数和时长：
```bash
python performance/run_perf.py -u 1000 -t 3m
```

### 方式 B：Web UI 可视化控制台模式（推荐性能调优与实时观测）
```bash
python performance/run_perf.py --web
```
- 控制台将自动在默认浏览器中弹出：`http://127.0.0.1:8089`

### 方式 C：分布式多节点“批量启动”集群模式（⭐ 榨干多核 CPU，突破万级并发）
单个 Python 进程由于 GIL 锁通常只能使用一个 CPU 核心。当并发量达到数千或上万时，需使用 Master-Worker 集群模式批量拉起：

```bash
# 批量拉起 1 个 Master 调度节点 + 4 个 Worker 施压节点 (Web UI 模式)
python performance/run_perf.py --web -w 4

# 批量拉起集群并在 CI/CD 中以无头模式压测 5000 并发：
python performance/run_perf.py -w 4 -u 5000 -t 3m
```

### 方式 D：Windows 一键批处理脚本启动（对标项目已有 batch 工具）
- **一键批量启动集群**：双击运行或命令行执行 `performance\start_perf_batch.bat`（默认一键拉起 Master + 4 个 Worker 并自动唤起浏览器）。
- **一键清理与释放端口**：若压测中断或端口被占用，双击运行 `performance\stop_perf.bat`，自动释放 8089 与 5557 端口。

### 方式 E：按场景标签批量筛选压测 (Tags 批跑)
```bash
# 仅对只读高频接口批量压测（用户资料、会话列表）
python performance/run_perf.py --tags read -u 1000 -t 2m

# 仅对高并发写接口批量压测（单聊/群聊发消息）
python performance/run_perf.py --tags write -u 500 -t 2m
```

---

## 5. 质量门禁基线 (SLA Quality Gate)

| 监控指标 | 达标阈值 | 异常级别 | 应对策略 |
| :--- | :--- | :--- | :--- |
| **错误率 (Failure Rate)** | $\le 0.1\%$ | P0 阻断 | 检查服务端 5xx、连接超时、数据库连接池耗尽 |
| **平均响应时间 (Avg RT)** | $\le 200\text{ ms}$ | P1 告警 | 排查单次请求慢查询、Redis 缓存穿透 |
| **P95 响应时间** | $\le 350\text{ ms}$ | P1 告警 | 重点优化尾部高延迟接口 |
| **P99 响应时间** | $\le 500\text{ ms}$ | P2 观察 | 系统极限压力与网络抖动边界 |
