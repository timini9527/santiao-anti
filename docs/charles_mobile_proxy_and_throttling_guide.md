# 📱 Charles 移动端抓包与弱网测试实战新手教程

---

## 一、 核心基础信息与环境自检

在配置手机前，必须首先明确电脑端的真实 IP 与 Charles 当前监听的代理端口。

### 1. 获取电脑局域网 IPv4 地址
* 打开终端（PowerShell 或 CMD）执行：
  ```cmd
  ipconfig
  ```
* 找到当前正在使用的网卡（无线局域网适配器 WLAN 或 以太网适配器）：
  * 记下 **IPv4 地址**（例如：`192.168.1.110`）。
  * 避开虚拟机网卡（如 VMware、VirtualBox、vEthernet 等虚拟 IP）。

### 2. 确认 Charles 监听端口
* 打开 Charles，顶部菜单选择 **Proxy** $\rightarrow$ **Proxy Settings...**。
* 查看 **HTTP Proxy Port**：
  * **注意**：本项目环境下已自定义为 **`8899`**（默认通常为 `8888`，以当前 Charles 配置为准）。

### 3. Windows 防火墙与访问控制放行
1. **Windows 防火墙**：确保 Windows Defender 防火墙允许 `Charles.exe` 访问「专用网络」与「公用网络」（若手机连入后断网，可临时关闭防火墙排查）。
2. **Charles 授权白名单**：
   * 顶部菜单：**Proxy** $\rightarrow$ **Access Control Settings...**。
   * 点击 **Add** 添加 `0.0.0.0/0`，点击 **OK**（允许局域网内所有手机 IP 连入，避免被误拦截）。

---

## 二、 手机端配置 HTTP 代理

> **前置条件**：手机与电脑必须连接**同一个 Wi-Fi 网络**。

### 1. iOS 端配置
1. 进入手机「设置」 $\rightarrow$ 「无线局域网（Wi-Fi）」。
2. 点击当前连接 Wi-Fi 右侧的 **(i)** 图标。
3. 滑到底部，点击 **配置代理** $\rightarrow$ 选择 **手动**。
4. 填写参数：
   * **服务器**：电脑局域网 IP（如 `192.168.1.110`）
   * **端口**：`8899`
   * **认证**：关闭
5. 点击右上角「存储」。

### 2. Android 端配置
1. 进入手机「设置」 $\rightarrow$ 「WLAN / Wi-Fi」。
2. 长按或点击当前连接的 Wi-Fi 详情 / 高级选项。
3. 找到 **代理** $\rightarrow$ 选择 **手动**。
4. 填写参数：
   * **代理主机名**：电脑局域网 IP（如 `192.168.1.110`）
   * **代理端口**：`8899`
5. 点击保存。

---

## 三、 SSL 证书下载、安装与完全信任

未安装并信任证书前，所有 HTTPS / WSS 请求都会提示连接不安全或直接阻断。

### 途径 A：手机在线下载（标准流程）
1. 手机连上代理后，打开自带浏览器（iOS 必须使用 Safari，Android 使用 Chrome 或系统浏览器）。
2. 地址栏输入：`chls.pro/ssl` 回车。
3. 手机会自动触发证书描述文件下载。

### 途径 B：电脑本地导出推送（推荐，离线最稳定）
若手机浏览器打不开下载页，直接从电脑导出：
1. 电脑 Charles 菜单：**Help** $\rightarrow$ **SSL Proxying** $\rightarrow$ **Save Charles Root Certificate...**。
2. 保存文件为 `charles.cer`。
3. 传输至手机：
   * **iOS**：通过 AirDrop 直接发送到手机，立即弹出安装提示；或通过系统文件分享。
   * **Android**：执行命令推送至手机存储：
     ```bash
     adb push charles.cer /sdcard/charles.cer
     ```

### 关键步骤：各端安装与信任激活

![image-20261112140811226](C:\Users\OiO\AppData\Roaming\Typora\typora-user-images\image-20261112140811226.png)

#### 1. iOS 启用完全信任（关键，漏掉则全是未知错误）
* 第一步：进入「设置」 $\rightarrow$ 「已下载描述文件」 $\rightarrow$ 点击右上角「安装」。
* 第二步：进入「设置」 $\rightarrow$ 「通用」 $\rightarrow$ 「关于本机」 $\rightarrow$ 滑到最底部「**证书信任设置**」。
* 第三步：在“针对根证书启用完全信任”列表中找到 **Charles Proxy CA**，打开右侧开关，弹出警告点击「继续」。

#### 2. Android 安装 CA 证书
* 进入「设置」 $\rightarrow$ 「安全」 $\rightarrow$ 「更多安全设置」 $\rightarrow$ 「加密与凭据」 $\rightarrow$ 「从存储设备安装（安装证书）」 $\rightarrow$ 选择 **CA 证书**。
* 选择刚推送的 `charles.cer` 文件完成安装。
* **注意**：Android 7.0+ 系统默认不信任用户 CA。开发/测试环境必须确保 App 开启了 `networkSecurityConfig` 允许 `user` 证书；生产包需依赖 Root 手机推入系统目录或使用 Frida/LSPosed 模块。

---

## 四、 Charles 抓包核心配置（避坑指南）

### 1. 开启全局 SSL 抓包（SSL Proxying）
* 顶部菜单：**Proxy** $\rightarrow$ **SSL Proxying Settings...**。
* 勾选 **Enable SSL Proxying**。
* 在 **Include** 列表中点击 **Add**：
  * **Host**：`*`（通配符表示解密所有域名）
  * **Port**：`*` 或 `443`
* 点击 **OK** 保存。

### 2. 检查录制过滤白名单（解决界面一片空白）
* 顶部菜单：**Proxy** $\rightarrow$ **Recording Settings...**。
  ![image-20261112140953777](C:\Users\OiO\AppData\Roaming\Typora\typora-user-images\image-20261112140953777.png)
* 切换到 **Include** 标签页：
  * **若想捕获所有流量（包括百度等外部网站）**：勾选 `*` 通配符，或清空 Include 列表中的条目。
  * **若想专注特定业务**：仅添加被测域名（如 `api.3tiao.top`、`api.3tai.vip`）。
* 确保顶部工具栏的录制开关（`Ctrl + R`）处于开启状态。

---

## 五、 弱网环境模拟配置（Throttle Settings）

### 1. 开启限速功能
* 顶部菜单：**Proxy** $\rightarrow$ **Throttle Settings...**（快捷键 `Ctrl + T`）。
* 勾选 **Enable Throttling**。

### 2. 配置定向限速（强烈推荐架构实践）
切勿开启全局无差别限速，否则会导致手机系统后台进程频繁超时奔溃。
* 勾选 **Only for selected hosts**。
* 点击 **Add**，添加被测 IM 服务端域名（如 `api.3tiao.top`，端口 `443`）。

### 3. 常见弱网测试场景参数模板

| 测试场景 | 带宽 (Bandwidth) | 往返延迟 (Latency) | 可靠性 (Reliability / 丢包率) | 业务验证重点 |
| :--- | :--- | :--- | :--- | :--- |
| **高延迟网络** | 500 kbps | 2000 ~ 3000 ms | 100% | 消息发送转圈状态机、请求防重复点击、超时提示 |
| **高丢包网络** | 200 kbps | 200 ms | 70%（制造 30% 丢包） | 消息自动重发、Seq 序号保序、幂等去重（无重复消息） |
| **极端恶劣弱网** | 20 kbps | 3000 ms | 60%（制造 40% 丢包） | 心跳包保活超时、自动重连机制、大文件/图片断点续传 |

* 配置完成后点击 **OK**。
* 确认主界面工具栏顶部的**乌龟图标（Throttle）**点亮变绿，即弱网生效。

---

## 六、 常见问题自检清单（FAQ）

| 异常现象 | 可能原因 | 快速解决措施 |
| :--- | :--- | :--- |
| **手机连上代理后断网，打不开网页** | 1. 电脑防火墙拦截入站连接<br>2. 电脑端口不正确（填了 8888 而非 8899） | 1. 临时关闭 Windows 防火墙或添加 8899 端口入站规则<br>2. 检查手机填写的端口是否与 Charles 一致 |
| **Charles 界面一片空白，没有任何请求** | 1. Recording Settings 设置了 Include 域名白名单<br>2. Charles 停止了录制（快捷键 `Ctrl + R` 未开启） | 1. 在 `Proxy -> Recording Settings -> Include` 勾选 `*` 通配符<br>2. 按 `Ctrl + R` 开始捕获 |
| **接口带锁头，显示 `<unknown>`** | 未开启 SSL Proxying 或未通配域名 | 在 `Proxy -> SSL Proxying Settings` 勾选 Enable，并添加 `*:*` |
| **提示证书不安全 / SSL 握手失败** | 1. iOS 未开启「针对根证书启用完全信任」<br>2. Android 未安装为 CA 证书 | 1. 进入 iOS「设置 - 通用 - 关于本机 - 证书信任设置」打开开关<br>2. Android 重新从凭据存储安装为 CA 证书 |
| **发消息、收消息接口在 Charles 里抓不到** | IM 核心通信采用原生 TCP Socket / Protobuf 长连接协议，不走系统 HTTP 代理 | 需改用链路层工具抓包（电脑开启热点后用 **Wireshark** 抓取网卡流量，或 Android `tcpdump`） |

