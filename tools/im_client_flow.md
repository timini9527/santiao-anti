# 🚀 三条 IM 分布式并发压测引擎架构与全流程规范 (im_client.py)

> **定位**：本文档详细阐述三条 IM 自动化测试体系中，高并发消息压测引擎 [`tools/im_client.py`](file:///d:/projects/santiao-anti/tools/im_client.py) 的系统架构、设计理念、多模拟器集群协同机制及端到端执行全流程。该引擎彻底抛弃了脆弱缓慢的 UI 操作，采用 Frida 微秒级 RPC 直通真机底层 Netty 长连接协议栈，支撑百万级消息的高保真、保序并发投递。

---

## 🏛️ 一、整体系统架构

整个压测引擎采用**「配置数据驱动 (DDT) + 分布式集群调度 + 运行时协议直通」**的三层工业化架构：

```mermaid
flowchart TD
    subgraph Layer1["1. 配置与数据驱动层 (DDT)"]
        CFG["config/im_targets.yaml<br/>(会话策略/场景矩阵/静态兜底)"]
        CSV["data/chat/chat_messages.csv<br/>(真实压测语料池)"]
    end

    subgraph Layer2["2. 会话管理与集群调度中心"]
        STM["SessionTargetManager<br/>(动态自发现 / 静态切片 / 自然数排序)"]
        CLUSTER["IMClientCluster<br/>(5 台模拟器集群协同编排器)"]
    end

    subgraph Layer3["3. 单机并发控制核心 (IMClient)"]
        QUEUE["Asyncio 并发任务池"]
        BP["Elastic Backpressure Controller<br/>(自适应高低水位在途流控)"]
        FIFO["Session Sequencer Barrier<br/>(单会话严格保序屏障)"]
    end

    subgraph Layer4["4. 运行时协议桥接层 (AppRuntimeBridge)"]
        DAEMON["Frida 守护自愈与 PID 探测"]
        RPC["Frida JS RPC Bridge<br/>(Java.perform 注入)"]
    end

    subgraph Layer5["5. 真机端协议栈与服务端"]
        NETTY["com.zkj.common.core.network.NettyTransceiver<br/>(sendTextMessage 原生直发通道)"]
        WCDB["本地 WCDB 消息持久化"]
        SERVER["服务端 Netty 长连接网关"]
    end

    CFG --> STM
    CSV --> QUEUE
    STM -->|分片切块 10群/机| CLUSTER
    CLUSTER -->|分发设备实例| QUEUE
    QUEUE --> BP --> FIFO --> RPC
    DAEMON -.->|守护运行| RPC
    RPC -->|微秒级直接调用| NETTY
    NETTY -->|TCP Socket / Protobuf| SERVER
    NETTY -->|异步写入| WCDB
```

---

## 🔄 二、端到端执行全流程时序

压测从启动到聚合输出战报，涵盖五个严密生命周期阶段：

```mermaid
sequenceDiagram
    autonumber
    participant Main as 执行入口 (main)
    participant STM as SessionTargetManager
    participant Cluster as IMClientCluster
    participant Client as IMClient (各设备)
    participant Bridge as AppRuntimeBridge
    participant Netty as 真机 Netty 协议栈

    Note over Main,STM: 【阶段一：会话策略加载与分片】
    Main->>STM: load_cluster_targets()
    STM->>STM: 解析 active_profile (如 offline_groups)
    alt 动态发现 (auto)
        STM->>STM: 查询各设备 SQLite conversation 表
    else 静态配置 (static)
        STM->>STM: 从 YAML 读取 50 个群聊静态 ID 并自然数排序
    end
    STM-->>Main: 返回 5 台设备实例与分配的目标会话 (每机 10 群)

    Note over Main,Bridge: 【阶段二：集群初始化与守护唤醒】
    Main->>Cluster: start()
    loop 每台已连接设备
        Cluster->>Client: start()
        Client->>Bridge: connect()
        Bridge->>Bridge: 检查/拉起 frida-server 守护进程
        Bridge->>Bridge: pidof 动态探测 App 主进程
        Bridge->>Bridge: 注入 JS 桥接脚本并获取 RPC Exports
    end

    Note over Main,Netty: 【阶段三：离线消息积压排空 (可选)】
    opt drain_offline=True
        Main->>Cluster: drain_all_offline_sync()
        Cluster->>Netty: 轮询并等待在途历史消息同步完成
    end

    Note over Main,Netty: 【阶段四：多机集群协同矩阵压测】
    Main->>Cluster: send_matrix(count_per_target, batch_size, ...)
    par 5 台模拟器并行执行
        loop 目标会话列表 (每设备 10 个群)
            Client->>Client: 弹性背压检测 (在途数 >= trigger_limit 则等待)
            Client->>Bridge: send_batch_text(targets, contents, batch_id)
            Bridge->>Netty: Java 反射调用 sendTextMessage()
            Netty-->>Bridge: 立即返回入队状态 (耗时 < 1ms)
            Bridge-->>Client: 批次提交成功确认
            Client->>Client: 动态微延时控制 (自适应平滑发送)
        end
    end

    Note over Main,Cluster: 【阶段五：战报聚合与安全释放】
    Cluster-->>Main: 汇总 5 台设备 TPS、成功量、耗时
    Main->>Cluster: stop() (注销 RPC，释放资源)
```

---

## ⚙️ 三、核心关键机制深度剖析

### 1. 弹性自适应背压流控 (Elastic Backpressure Controller)
* **痛点**：端侧 SQLite/WCDB 数据库写入性能有限。若以万级 TPS 无限推送，真机底层消息队列严重堆积，将导致内存泄露、WCDB 锁争用崩溃，以及触发 30s 协议超时。
* **机制**：
  - **动态监控**：通过 `get_inflight()` 实时读取 NettyTransceiver 中排队待发与待 ACK 的在途消息数。
  - **双水位线控制**：
    - `trigger_limit (高水位，默认 50 条)`：在途消息达到此阈值时，自动挂起后续批次，进入异步等待状态。
    - `low_watermark (低水位，默认 20 条)`：等待真机网络与数据库消费回流，在途数降至低水位时平滑恢复发送。

### 2. 单会话严格保序屏障 (Session Sequencer Barrier)
* **痛点**：在异步并发下，若同一会话的多条消息被多协程乱序投递，会导致服务端记录的聊天时序错乱。
* **机制**：
  - 对同一 `chat_id` 的批次打上严格递增的本地时序序号。
  - 采用会话维度锁屏障，确保前一批次被 Netty 成功受理前，后续批次严禁超车，保障消息在服务端 seq 的绝对单调递增。

### 3. 多模拟器自然数均分分片算法 (Natural Cluster Sharding)
* **机制**：
  - 针对 `1群` ~ `50群` 或 `离线群001` ~ `050`，系统内置自然数正则解析引擎 `re.findall(r'\d+', name)`。
  - 彻底规避字典序排序陷阱（防止排成 `1群, 10群, 11群, 2群...`）。
  - 将 50 个群按序号整齐切块：
    - **设备 1 (`emulator-5562`)**：分得第 `1群 ~ 10群`
    - **设备 2 (`emulator-5564`)**：分得第 `11群 ~ 20群`
    - **设备 3 (`emulator-5566`)**：分得第 `21群 ~ 30群`
    - **设备 4 (`emulator-5568`)**：分得第 `31群 ~ 40群`
    - **设备 5 (`emulator-5572`)**：分得第 `41群 ~ 50群`

---

## 📋 四、实战配置与运行指南

### 1. 压测场景切换（修改 [`config/im_targets.yaml`](file:///d:/projects/santiao-anti/config/im_targets.yaml)）

```yaml
# 切换全局压测场景：
active_profile: "offline_groups"  # 1-50群 集群分片压测
# active_profile: "dedicated_groups" # 设备专属测试群压测
# active_profile: "single_chat"      # 好友单聊压测
```

### 2. 压测参数调整（在 [`tools/im_client.py`](file:///d:/projects/santiao-anti/tools/im_client.py#L1435) 的 main 函数中）

```python
# 核心压测参数配置：
USE_CLUSTER = True            # True: 5 台设备集群协同; False: 单设备运行
TARGET_DEVICE_INDEX = 0       # 单机模式下指定的设备编号 (0~4)

COUNT_PER_TARGET = 100        # 每个会话目标发送的消息配额 (例: 10个群各发100条 = 单机1000条)
BATCH_SIZE = 5                # 每批次聚合发送消息条数 (推荐 1~10)
DELAY_BETWEEN_BATCHES = 0.05  # 批次之间的缓冲微延时 (50ms，保护端侧数据库)
ENFORCE_FIFO = True           # 是否开启会话保序屏障
USE_CSV_DATA = True           # 是否使用真实语料库 (data/chat/chat_messages.csv)
```

### 3. 一键启动
直接在终端或 IDE 中执行：
```bash
python tools/im_client.py
```
终端将自动输出多机各节点的发送进度条与全集群综合 TPS 战报。
