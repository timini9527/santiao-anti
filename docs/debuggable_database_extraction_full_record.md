# 📱 三条 IM 客户端真机沙盒破甲与数据库全流程技术复盘文档

> **项目背景**：在未 Root 的 Android 11+ 真机设备（`3B65BN02GU600000`）上，对类微信 IM 客户端“三条”（`com.santiaotalk.im`）进行数据层穿透，提取并解析本地 SQLite 聊天记录、好友 CustId/OpenId 以及系统元数据。  
> **核心破局策略**：路线 A —— AXML 二进制原地破甲注入 `android:debuggable="true"` 属性，建立免 Root `run-as` 官方合法提权通道。

---

## 目录
1. [阶段一：方案决策与路线 A 确立](#阶段一方案决策与路线-a-确立)
2. [阶段二：灰度包提取与 AXML 二进制破甲尝试（第 1 代流水线）](#阶段二灰度包提取与-axml-二进制破甲尝试第-1-代流水线)
3. [阶段三：正式环境官方包切换与破甲修复（解决灰度问题与目录为空疑虑）](#阶段三正式环境官方包切换与破甲修复解决灰度问题与目录为空疑虑)
4. [阶段四：真机代操作，穿透并进入 databases 目录](#阶段四真机代操作穿透并进入-databases-目录)
5. [阶段五：聊天记录数据库深度解析与提取](#阶段五聊天记录数据库深度解析与提取)
6. [阶段六：解决 MT 管理器“无数据库选项”与文本打开“乱码”问题](#阶段六解决-mt-管理器无数据库选项与文本打开乱码问题)
7. [阶段七：全量数据库架构职责与数据内容全景梳理](#阶段七全量数据库架构职责与数据内容全景梳理)
8. [阶段八：好友 CustId 与 OpenId 数据表定位与明文导出](#阶段八好友-custid-与-openid-数据表定位与明文导出)
9. [阶段九：电脑端 SQLite 可视化工具推荐与本地环境就绪](#阶段九电脑端-sqlite-可视化工具推荐与本地环境就绪)
10. [产出文件资产清单](#产出文件资产清单)

---

## 阶段一：方案决策与路线 A 确立

### 1. 用户诉求
* 用户提问：“使用.agent目中的 dsh-purge-archive-pr-115-merge 和rea-rea-agents-6.7.0工具，分析如何才能看到数据库内容”。
* 目标设备：真机 `3B65BN02GU600000`（未 Root）。

### 2. 技术瓶颈分析
* 在 Android 11+（API 30+）内核中，`/data/data/com.santiaotalk.im` 受到 Linux DAC（所有者权限 `0700`）和 SELinux 严格隔离保护。普通 `adb shell` 或常规应用（包括 MT 管理器直接访问）均返回 `Permission Denied`。

### 3. 架构决策推演
架构师对比了三套技术方案：
* **路线 A（最完美、零门槛推荐）**：对安装包的 `AndroidManifest.xml` 进行二进制注入 `android:debuggable="true"` 并重签名安装，打通系统底层的 `run-as com.santiaotalk.im` 官方穿透能力。
* **路线 B**：使用 Shizuku + ADB shell 脚本流式导出备份。
* **路线 C**：Frida hook 动态导出。

### 4. 执行决策
用户确认 `yes` 并选择 `1`，正式启动**路线 A**。

---

## 阶段二：灰度包提取与 AXML 二进制破甲尝试（第 1 代流水线）

### 1. 详细步骤与执行动作
1. **提取安装包**：从运行中的 MuMu 模拟器提取已安装的 `base.apk`（大小约 148MB）；
2. **研发 AXML 原地破甲脚本**（`build_debug_apk.py`）：
   * 采用二进制原地修改策略，避免使用 apktool 反编译导致资源 ID 错乱或 Dex 签名破坏；
   * 读取 AXML StringPool，将 11 字符的 `allowBackup` 原地替换为 10 字符的 `debuggable\0`（补 4 字节保持结构对齐）；
   * 将属性 ResourceId 由 `0x01010280`（allowBackup）修改为 `0x0101000f`（debuggable）；
   * 将属性值修改为 `0xFFFFFFFF`（布尔值 `true`）；
3. **对齐与签名**：
   * 使用 `zipalign -p -f 4` 对齐 APK；
   * 使用 JDK `keytool` 生成 debug 证书，通过 `apksigner` 完成 V1+V2 签名；
4. **安装验证**：将生成的 `base_debug_aligned.apk` 推送并安装到真机设备 `3B65BN02GU600000`。

---

## 阶段三：正式环境官方包切换与破甲修复（解决灰度问题与目录为空疑虑）

### 1. 用户反馈
1. “你怎么给我弄成灰度环境的debug，我需要的是正式环境的debug包;”
2. “你打的这个包根部没有这个目录 /data/data/com.santiaotalk.im/databases/”

### 2. 技术排查与成因分析
* **灰度包成因**：第一阶段从模拟器提取时，模拟器上运行的是灰度包（`versionCode: 11129, versionName: 11.1.29`）。
* **为何“根本没有 databases 目录”？（底层原理）**：
  * **原理 1（按需懒加载机制）**：APK 安装包本身仅包含代码和静态资源，私有目录由系统在设备端按需生成。全新安装 App 后，系统仅分配 `cache/` 与 `code_cache/`。`databases/` 目录只有在 App 首次运行并调用 `openOrCreateDatabase`（或登录账号初始化数据库）时才会由底层 `mkdirs()` 创建！未启动应用前该目录客观上**不存在**。
  * **原理 2（MT 管理器访问姿势限制）**：在 Android 11+ 上，未 Root 手机直接在 MT 管理器文件路径栏点 `/data/data` 会被系统 SELinux 拦截显示为空，必须通过 MT 管理器的【应用】$\rightarrow$【三条】$\rightarrow$【数据目录】入口跳转挂载。

### 3. 正式环境破甲流水线实施（`build_official_debug.py`）
1. 定位本地正式环境官方原版安装包：
   `SanTiaoTalk_official_release_11.1.21_20260908_143857—无限制.apk`（版本：`11.1.21`，versionCode: `11121`）；
2. 执行自动化脚本将 AXML 破甲为 `debuggable="true"`；
3. 执行 `zipalign` 4 字节对齐，并使用 `apksigner` 重新签名；
4. 通过 `aapt.exe dump badging` 校验，确认存在 `application-debuggable`；
5. 卸载真机旧的灰度包：`adb -s 3B65BN02GU600000 uninstall com.santiaotalk.im`；
6. 安装正式环境 Debug 包：`adb -s 3B65BN02GU600000 install official_debug_aligned.apk`；
7. 执行命令验证权限穿透生效：`adb -s 3B65BN02GU600000 shell "run-as com.santiaotalk.im id"` 返回 `uid=10422(u0_a422)`。

---

## 阶段四：真机代操作，穿透并进入 databases 目录

### 1. 用户诉求
* “你帮我操作，进入databases目录”。

### 2. 自动化代操作完整步骤
1. **唤醒三条 App 触发初始化**：
   * 执行 `adb -s 3B65BN02GU600000 shell monkey -p com.santiaotalk.im -c android.intent.category.LAUNCHER 1`；
   * 触发底层 SQLite 数据库引擎启动，确证生成了 `databases/`、`files/`、`shared_prefs/` 等目录。
2. **全量流式导出到公共存储**：
   * 将私有数据库通过 tar 管道流式克隆至真机外部共享下载目录：
     `adb shell "mkdir -p /sdcard/Download/santiao_databases && run-as com.santiaotalk.im tar -cf - -C /data/data/com.santiaotalk.im databases | tar -xf - -C /sdcard/Download/santiao_databases"`
   * 赋予全局读写权限：`chmod -R 777 /sdcard/Download/santiao_databases`。
3. **控制 MT 管理器自动化导航**：
   * 启动 MT 管理器：`adb shell monkey -p bin.mt.plus ...`；
   * 通过 `uiautomator dump` 获取屏幕控件坐标，定位到三条应用条目并点击 `(500, 560)`；
   * 识别弹窗中的数据目录选项，精准点击 `(687, 1302)`；
   * 通过 Intent 将 MT 管理器直达定位到目标路径：
     `adb shell am start -n bin.mt.plus/.Main -d "file:///sdcard/Download/santiao_databases/databases"`；
   * 成功使用户真机前台屏幕直接停留在 `databases` 目录！

---

## 阶段五：聊天记录数据库深度解析与提取

### 1. 用户诉求
* “帮我查看聊天记录”。

### 2. 数据拉取与技术验证
1. **无损拉取数据**：通过原生 CRC 校验通道将 `databases/IM_Data` 完整 pull 到本地开发环境；
2. **SQLite 结构探查（`read_chat_records.py`）**：
   * 读取 `messages/message_2026` 头部 Magic 为 `b'SQLite format 3\x00'`；
   * 确认核心消息库为**标准的 SQLite 数据库，完全未加密**（并非 SQLCipher 或自定义加密）；
   * 单表 `message` 记录总数达 **5,551 条**；
   * `meta` 库中包含 `conversation`（89个会话）、`friend`（27位好友）、`group_table`（110个群）。
3. **数据关联与格式化输出（`export_utf8_chat.py`）**：
   * 跨库联合查询 `message_2026` 与 `meta`，将 `from_cust_id`、`conv_id` 转换为真实的群名、好友备注和“我”；
   * 将毫秒时间戳转换人类可读时间（YYYY-MM-DD HH:MM:SS）；
   * 提取纯文本内容与 `msg_body` JSON 富媒体结构；
   * 在当前工作区根目录生成纯文本文件 [`chat_records.txt`](file:///d:/projects/santiao-anti/chat_records.txt)。

---

## 阶段六：解决 MT 管理器“无数据库选项”与文本打开“乱码”问题

### 1. 用户反馈
1. “这是哪一个目录文件中的，我怎么看到是乱码的”
2. “没有 选择 【数据库】（或 【SQLite 查看器】）；这两个选项”

### 2. 根因技术剖析
* **乱码成因**：`message_2026` 与 `meta` 是标准的 SQLite 二进制文件（内部由 B-Tree 页、数据槽、十六进制索引组成）。若直接用手机“文本编辑器”或记事本打开，软件会强行将二进制数据按字符渲染，呈现为大量问号和乱码。
* **无选项成因**：
  1. 用户真机上的 MT 管理器属于基础版本，没有集成 SQLite 专有图形化查看插件；
  2. 原生数据库文件名没有 `.db` 后缀（就叫 `message_2026` 和 `meta`），系统文件管理器无法根据 MIME/扩展名自动关联数据库。

### 3. 双端解决方案落地
1. **自动补充扩展名**：在真机目录与本地目录中，将 `message_2026`、`meta` 及其 WAL/SHM 文件完整复制生成对应的 `.db`、`.db-wal`、`.db-shm` 文件；
2. **手机端极简可视化方案（HTML查看）**：
   * 编写 `generate_chat_html.py`，将 5551 条聊天记录生成为带气泡样式的独立离线网页 `chat_history.html`；
   * 推送至真机当前目录：`/sdcard/Download/santiao_databases/chat_history.html`；
   * 用户在 MT 管理器中点击它，直接使用内置的 **【HTML查看】** 即可像微信一样看聊天记录！
3. **电脑端就绪**：在项目根目录生成 [`chat_records.txt`](file:///d:/projects/santiao-anti/chat_records.txt) 与 [`chat_history.html`](file:///d:/projects/santiao-anti/chat_history.html)。

---

## 阶段七：全量数据库架构职责与数据内容全景梳理

### 1. 用户诉求
* “databases 这些数据库对应哪些数据内容”。

### 2. 深度分析（`analyze_all_dbs.py`）
全量扫描真机 31 个数据库文件，系统化梳理出四大架构域：

```text
databases/
├── IM_Data/                          [IM 核心业务域]
│   └── {用户UID}/
│       ├── messages/message_2026.db  --> 消息库 (message 表：msg_id, conv_id, content, msg_body, is_read 等 5551条)
│       ├── meta.db                   --> 元数据库 (user, conversation, friend, group_table, keywords 等 17张表)
│       ├── global_search.db          --> SQLite FTS 全文检索引擎库 (search, search_idx)
│       └── {用户UID} (16KB)          --> MMKV 内存映射高频 Key-Value 缓存
├── bugly_db_                         [异常排查域] 腾讯 Bugly SDK，记录 Java Crash/Native 崩溃/ANR
├── monitor.db                        [性能监控域] 阿里系监控组件，记录网络请求与耗时 (alitx_monitor)
├── msre.db / msvolcano.db            [安全风控域] 字节跳动火山引擎 SDK，负责设备指纹与风控环境检测
└── tbsbeacon_db_*                    [浏览服务域] 腾讯 TBS X5 内核信标库，记录内置网页渲染与指标
```

---

## 阶段八：好友 CustId 与 OpenId 数据表定位与明文导出

### 1. 用户诉求
1. “如果要查看好友的CustId和OpenId，是在哪个数据库里面”
2. “为什么我打开后还是加密乱码状态”

### 2. 核心结论与排查
* **目标定位**：`IM_Data/{用户UID}/meta` 数据库中的 **`friend`** 数据表。
* **乱码解释**：`meta` 本身也是 SQLite 二进制文件，直接用文本方式打开必然呈现假性“加密乱码”。
* **自动化导出实施（`export_friends.py`）**：
  * 连接 `meta` 库，提取全部 27 位好友的 `cust_id`、`open_id`、`remark_name`、`username`、`mobile`；
  * 生成电脑端格式化对齐文件：[`friends_list.txt`](file:///d:/projects/santiao-anti/friends_list.txt)；
  * 生成手机端卡片网页 `friends.html` 并推送到真机 MT 管理器目录；
  * 明确提示用户：压测脚本 `im_client.py:L105` 的 `to_cust_id` 参数直接填入该清单中的 `cust_id`。

---

## 阶段九：电脑端 SQLite 可视化工具推荐与本地环境就绪

### 1. 用户诉求
* “电脑上使用什么工具，可以直接查看呢”。

### 2. 架构级工具选型推荐
1. **方案一：VS Code 扩展 `SQLite Viewer`（最推荐）**：
   * 在编辑器内一键安装插件，无需跳出当前开发窗口；
   * 点击 `.db` 文件直接像 Excel 一样浏览、搜索、排序各表数据。
2. **方案二：DB Browser for SQLite（专业独立利器）**：
   * 官方开源免费，支持拖拽文件直接秒开（即使没有 `.db` 后缀也能识别）；
   * 支持强大的 SQL 自定义查询能力。
3. **方案三：DBeaver / Navicat**：通用数据库管理客户端。

### 3. 本地资产自动化同步
* 将真机全套数据库同步至本地工作区：[`local_databases/`](file:///d:/projects/santiao-anti/local_databases/)；
* 编写脚本为所有数据库无损复制一份 `.db` 扩展名文件，确保任何工具双击即开。

---

## 产出文件资产清单

| 资产路径 | 类型 | 内容描述 |
| :--- | :--- | :--- |
| [`friends_list.txt`](file:///d:/projects/santiao-anti/friends_list.txt) | 纯文本 | **全量 27 位好友名单**（包含昵称、手机、CustId、OpenId 表格对齐） |
| [`chat_records.txt`](file:///d:/projects/santiao-anti/chat_records.txt) | 纯文本 | **最新聊天记录提取报告**（包含发送方、时间、会话、消息内容明细） |
| [`chat_history.html`](file:///d:/projects/santiao-anti/chat_history.html) | 网页 | **聊天记录可视化页面**（手机/电脑双端均可双击直接查看） |
| [`local_databases/.../meta.db`](file:///d:/projects/santiao-anti/local_databases/IM_Data/zCWf_C98sQbn466xnFK8BfBwBocgVfAd/meta.db) | 数据库 | **好友与会话元数据库**（可用 SQLite 工具直接打开） |
| [`local_databases/.../message_2026.db`](file:///d:/projects/santiao-anti/local_databases/IM_Data/zCWf_C98sQbn466xnFK8BfBwBocgVfAd/messages/message_2026.db) | 数据库 | **聊天记录原始数据库**（可用 SQLite 工具直接打开） |
