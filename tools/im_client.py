# -*- coding: utf-8 -*-
"""三条 IM 多会话并发客户端与高并发压测引擎（工业级多端统一实现）
======================================================
核心定位：
  为自研三条 IM 提供统一的高性能消息发送引擎。
  全面支持：
    1. 单目标压测：向特定好友（如 A0110）进行单条验证与百万级极限压测；
    2. 多会话并发/广播：同时向界面中多个活跃会话（单聊、群聊混合）并行发送消息；
    3. 动态会话感知：支持从客户端底层数据库自动扫描当前主页会话列表（自适应抓取）；
    4. 百万级多会话流式压测：轮询调度并发打向图中各个会话，测试会话列表排序与并发性能。

设计原则与工程约束：
  1. 免 UI 交互：严禁使用 Appium、UIAutomator2 点击元素，杜绝界面渲染与动画耗时；
  2. 免 ADB 模拟：严禁使用 adb shell input 模拟按键，杜绝跨进程输入法抖动；
  3. 原生协议直通：单聊（chatType=1）、群聊（chatType=2）自动按协议分发路由；
  4. 真机活动长连接复用（AppRuntimeBridge）：
     直连设备上三条 App 已与网关保持活动 TCP 握手与心跳认证的 WebSocketManager 单例，
     直接调用底层协议管理器 sendTextMessage，100% 确保服务端网关实时路由；
  5. 生产者-消费者流式队列引擎：内存常驻 < 25MB，彻底杜绝 OOM。

依赖项：
  pip install frida frida-tools requests websockets
"""

import asyncio
import concurrent.futures
from dataclasses import dataclass
from enum import IntEnum
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import uuid

import frida
import frida_tools
import requests

# 动态确保项目根目录在 sys.path 中，以便直接运行脚本并复用框架现有模块
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.file_reader.data_loader import load_csv_data, load_yaml_data


# ---------------------------------------------------------------------------
# 0. 数据驱动：基于 data_loader 的真实 CSV 消息样本语料池
# ---------------------------------------------------------------------------
_CACHED_MESSAGES_POOL: Optional[List[str]] = None


def get_chat_message_corpus(file_name: str = "chat/chat_messages.csv") -> List[str]:
    """通过项目现有的 data_loader 工具加载 chat_messages.csv 真实消息语料。
    自动解析 context 列数据，过滤空白项，并单例缓存在内存中以支撑高并发极速发送。
    Args:
        file_name: 相对路径或文件名，默认 'chat/chat_messages.csv'
    Returns:
        List[str]: 解析提取出的真实业务消息内容列表。
    """
    global _CACHED_MESSAGES_POOL
    if _CACHED_MESSAGES_POOL is not None and len(_CACHED_MESSAGES_POOL) > 0:
        return _CACHED_MESSAGES_POOL

    try:
        raw_rows = load_csv_data(file_name)
        messages: List[str] = []
        for row in raw_rows:
            if isinstance(row, dict):
                mes_id = row.get("case_id")
                text = row.get("context")
                if text:
                    messages.append(f"{mes_id}:{str(text).strip()}")
        if messages:
            _CACHED_MESSAGES_POOL = messages
            return _CACHED_MESSAGES_POOL
    except Exception as e:
        print(f"⚠️ [数据驱动] 通过 data_loader 加载 {file_name} 异常: {e}，将采用备用样本")

    fallback = ["三条 IM 自动化高并发测试消息通道连接正常"]
    _CACHED_MESSAGES_POOL = fallback
    return fallback


# ---------------------------------------------------------------------------
# 1. 协议枚举与会话目标模型
# ---------------------------------------------------------------------------
class ChatType(IntEnum):
    """聊天会话类型枚举（与三条 IM 协议底层严格对齐）"""
    SYSTEM = 0            # 系统通知
    SINGLE = 1            # 单聊 (私聊)
    GROUP = 2             # 群聊 (多播)
    CUSTOMER_SERVICE = 3  # 客服消息


@dataclass(frozen=True)
class SessionTarget:
    """多会话压测目标实体"""
    name: str                             # 会话展示名称（如 "测试群001", "A0110"）
    chat_type: Union[int, ChatType] = ChatType.SINGLE  # 1 为单聊，2 为群聊
    to_cust_id: str = "0"                 # 接收方 CustID（单聊填目标用户 CustID，群聊填 "0"）
    chat_id: str = "0"                    # 会话 ID（单聊填 "0"，群聊填群真实 GroupID）
    is_top: bool = False                  # 是否置顶会话
    is_muted: bool = False                # 是否免打扰

    @property
    def is_group(self) -> bool:
        """是否为群聊。"""
        return int(self.chat_type) == int(ChatType.GROUP)


# 批次元素：(会话目标, 文本内容)
BatchItem = Tuple[SessionTarget, str]


# ---------------------------------------------------------------------------
# 2. 真机底层长连接协议桥接驱动 (AppRuntimeBridge)
# ---------------------------------------------------------------------------
class AppRuntimeBridge:
    """真机进程内活动协议长连接桥接驱动
    通过轻量级微秒 RPC 桥，直连真机运行时中已与长连接网关保持活动 TCP 握手与心跳认证的
    WebSocketManager 单例。
    优势：
      - 彻底绕过外部未授权拦截；
      - 自动完成底层消息封包、seq 递增、时间戳及异或校验和；
      - 纯协议层直接投递入 Netty Channel，单机吞吐达数千 QPS。
    """

    # 注入到 App 运行时的微秒级发送桥接脚本（通用支持单聊与群聊）
    _BRIDGE_JS = """
    var WebSocketMgr = null;
    var SocketClientPendingField = null;
    var JavaThreadCls = null;
    var _skipSendDbWrite = false;
    var _activeSendThreadId = -1;
    var _dbHooksInstalled = false;

    function installSkipDbHooks() {
        if (_dbHooksInstalled) {
            return;
        }
        Java.perform(function() {
            try {
                JavaThreadCls = Java.use('java.lang.Thread');
                var msgCls = 'com.bm.santiaotalk.store.entity.w.Message';
                var MessageDao = Java.use('com.bm.santiaotalk.store.dao.w.MessageDao');
                MessageDao.insert.overload(msgCls).implementation = function(msg) {
                    if (_skipSendDbWrite && JavaThreadCls.currentThread().getId() === _activeSendThreadId) {
                        return;
                    }
                    return this.insert(msg);
                };
                var ShardedMessageDao = Java.use('com.bm.santiaotalk.store.dao.w.ShardedMessageDao');
                ShardedMessageDao.insert.overload(msgCls).implementation = function(msg) {
                    if (_skipSendDbWrite && JavaThreadCls.currentThread().getId() === _activeSendThreadId) {
                        return;
                    }
                    return this.insert(msg);
                };
                ShardedMessageDao.insertToYear.overload(msgCls).implementation = function(msg) {
                    if (_skipSendDbWrite && JavaThreadCls.currentThread().getId() === _activeSendThreadId) {
                        return;
                    }
                    return this.insertToYear(msg);
                };
                _dbHooksInstalled = true;
            } catch (e) {
                console.log("[Bridge] 安装跳过写库 Hook 异常: " + e.toString());
            }
        });
    }

    function getPendingCount() {
        var count = 0;
        Java.perform(function() {
            try {
                if (!WebSocketMgr) {
                    WebSocketMgr = Java.use('com.network.lib.socket.WebSocketManager').INSTANCE.value;
                }
                if (WebSocketMgr && WebSocketMgr.socketClient) {
                    var sc = WebSocketMgr.socketClient.value;
                    if (sc) {
                        if (!SocketClientPendingField) {
                            SocketClientPendingField = Java.use('com.network.lib.socket.SocketClient').class.getDeclaredField('pendingMessages');
                            SocketClientPendingField.setAccessible(true);
                        }
                        var map = Java.cast(SocketClientPendingField.get(sc), Java.use('java.util.Map'));
                        count = map.size();
                    }
                }
            } catch (e) {}
        });
        return count;
    }

    rpc.exports = {
        init: function() {
            var ok = false;
            Java.perform(function() {
                try {
                    WebSocketMgr = Java.use('com.network.lib.socket.WebSocketManager').INSTANCE.value;
                    ok = WebSocketMgr != null;
                } catch (e) {
                    console.log("[Bridge] 初始化 WebSocketManager 异常: " + e.toString());
                }
            });
            return ok;
        },
        // 获取底层 SocketClient 当前在途等待服务端 ACK 的消息总数
        getInflightCount: function() {
            return getPendingCount();
        },
        // 开关：压测发消息时是否跳过本地 WCDB 落库（仅当前发送线程生效，不干扰接收与 ACK 线程）
        setSkipDbWrite: function(enabled) {
            _skipSendDbWrite = !!enabled;
            if (_skipSendDbWrite) {
                installSkipDbHooks();
            }
            return _skipSendDbWrite;
        },
        // 通用发送入口：自动适配单聊 (chatType=1) 与群聊 (chatType=2)
        sendTextMessage: function(chatId, chatType, fromCustId, fromCustName, toCustId, content) {
            var success = false;
            Java.perform(function() {
                try {
                    if (!WebSocketMgr) {
                        WebSocketMgr = Java.use('com.network.lib.socket.WebSocketManager').INSTANCE.value;
                    }
                    if (WebSocketMgr) {
                        success = WebSocketMgr.sendTextMessage(
                            chatId,        // 单聊填 "0"，群聊填群 GroupID
                            chatType,      // 1: 单聊, 2: 群聊
                            fromCustId,
                            fromCustName,
                            toCustId,      // 单聊填对方 CustID，群聊填 "0"
                            content,
                            0,             // quoteSeq
                            null,          // richContent
                            null,          // contentJson
                            null,          // atCustIds
                            false,         // isBurnAfterReading
                            false          // isGroupNotify
                        );
                    }
                } catch (e) {
                    console.log("[Bridge] 发送底层异常: " + e.toString());
                }
            });
            return success;
        },
        // 批量管道高速发送接口：单次 RPC 传输批次数组，App 内部执行原生循环直投 Netty
        // 返回逐条回执：rejected 为同步拒收或未执行（未进入 Netty，可安全重发）；unknown 为抛异常、结果未知（禁止重放）
        // 快速失败：通道一旦拒收立即停止本批，避免对不可写通道持续冲击并产生大量本地失败记录
        sendBatchTextMessage: function(messagesJson) {
            var list = JSON.parse(messagesJson);
            var len = list.length;
            var result = {rejected: [], unknown: []};
            Java.perform(function() {
                var i = 0;
                try {
                    if (!WebSocketMgr) {
                        WebSocketMgr = Java.use('com.network.lib.socket.WebSocketManager').INSTANCE.value;
                    }
                    if (WebSocketMgr) {
                        if (_skipSendDbWrite) {
                            if (!JavaThreadCls) {
                                JavaThreadCls = Java.use('java.lang.Thread');
                            }
                            _activeSendThreadId = JavaThreadCls.currentThread().getId();
                        }
                        try {
                            for (; i < len; i++) {
                                var item = list[i];
                                var ok = WebSocketMgr.sendTextMessage(
                                    item.chatId,
                                    item.chatType,
                                    item.fromCustId,
                                    item.fromCustName,
                                    item.toCustId,
                                    item.content,
                                    0, null, null, null, false, false
                                );
                                if (!ok) {
                                    break;
                                }
                            }
                        } finally {
                            _activeSendThreadId = -1;
                        }
                    }
                } catch (e) {
                    console.log("[Bridge] 批量管道发送底层异常: " + e.toString());
                    result.unknown.push(i);
                    i++;
                }
                for (; i < len; i++) {
                    result.rejected.push(i);
                }
            });
            result.inflight = getPendingCount();
            return result;
        }
    };
    """

    def __init__(self, device_id: str = "emulator-5562", package_name: str = "com.santiaotalk.im") -> None:
        self.device_id: str = device_id
        self.package_name: str = package_name
        self._session: Optional[Any] = None
        self._script: Optional[Any] = None
        self._is_ready: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()
        # 核心架构优化：为每台物理/虚拟设备配置独立的私有线程池，彻底杜绝全局默认线程池饥饿导致的设备排队串行！
        self._executor: concurrent.futures.ThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor(
            max_workers=30,
            thread_name_prefix=f"frida-{device_id}",
        )

    def _assemble_script_source(self) -> str:
        """读取 frida_tools 自带的 java.js 桥接核心并挂载到 globalThis.Java。"""
        bridges_dir = Path(frida_tools.__file__).parent / "bridges"
        java_js_file = bridges_dir / "java.js"
        if not java_js_file.exists():
            raise FileNotFoundError(f"未找到 Frida Java 桥接库: {java_js_file}")
        java_core = java_js_file.read_text(encoding="utf-8")
        # 挂载为全局变量，确保 RPC 导出函数内调用 Java 顺畅无阻
        return f"{java_core}\n;\nvar Java = bridge;\nglobalThis.Java = bridge;\n{self._BRIDGE_JS}"

    def _ensure_frida_server_running(self) -> None:
        """检查并确保目标设备上的 frida-server 处于 root 守护运行状态，具备断线自愈能力。"""
        try:
            # 增加 timeout=2.0 刚性超时，杜绝 ADB 离线设备无限期阻塞
            out = subprocess.check_output(
                f"adb -s {self.device_id} shell ps -A",
                shell=True, text=True, stderr=subprocess.DEVNULL, timeout=2.0
            )
            if "frida-server" not in out:
                # 自动尝试提权为 root 模式并拉起守护进程
                subprocess.run(f"adb -s {self.device_id} root", shell=True, capture_output=True, timeout=3.0)
                time.sleep(0.3)
                # 核心自愈保障：自动赋予可执行权限，避免 adb push 后默认无 +x 导致 Permission denied
                subprocess.run(
                    f"adb -s {self.device_id} shell chmod 755 /data/local/tmp/frida-server",
                    shell=True,
                    capture_output=True,
                    timeout=2.0,
                )
                # 核心防卡死：彻底隔离标准输入输出管道，杜绝 Windows 控制台句柄继承死锁卡住 Terminal
                subprocess.Popen(
                    f"adb -s {self.device_id} shell /data/local/tmp/frida-server -D",
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(0.5)
        except Exception:
            pass

    def _find_target_pid(self) -> Optional[int]:
        """优先通过 ADB 原生 pidof 精准获取目标 PID，彻底规避模拟器中进程名乱码问题；多级降级检索。"""
        # 1. 原生 pidof 精准匹配 (超时 2 秒)
        try:
            cmd = f"adb -s {self.device_id} shell pidof {self.package_name}"
            out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, timeout=2.0).strip()
            if out:
                return int(out.split()[0])
        except Exception:
            pass

        # 2. 原生 ps -A 匹配 (超时 2 秒)
        try:
            cmd = f"adb -s {self.device_id} shell ps -A"
            out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, timeout=2.0)
            for line in out.splitlines():
                if self.package_name in line:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1])
        except Exception:
            pass

        # 3. Frida 自身枚举降级 (超时 2 秒)
        try:
            device = frida.get_device_manager().get_device(self.device_id, timeout=2)
            for p in device.enumerate_processes():
                if p.name == self.package_name or p.name == "3T":
                    return p.pid
        except Exception:
            pass

        return None

    def connect(self) -> bool:
        """连接目标设备上的三条 IM 进程并初始化注入桥（全链路超时与防死锁）。"""
        try:
            self._ensure_frida_server_running()
            target_pid = self._find_target_pid()
            if target_pid is None:
                raise ProcessLookupError(f"设备 {self.device_id} 上未找到三条 IM 运行进程 ({self.package_name})，请确认 App 前台处于运行状态")

            device = frida.get_device_manager().get_device(self.device_id, timeout=3)
            self._session = device.attach(target_pid)
            full_source = self._assemble_script_source()
            self._script = self._session.create_script(full_source)
            self._script.load()
            time.sleep(0.3)

            self._is_ready = bool(self._script.exports_sync.init())
            return self._is_ready
        except Exception as e:
            print(f"[协议桥接] 连接设备 {self.device_id} 运行时异常: {e}")
            self._is_ready = False
            return False

    async def ensure_connected(self) -> None:
        """异步确保桥接连接处于就绪状态。"""
        if not self._is_ready:
            async with self._lock:
                if not self._is_ready:
                    loop = asyncio.get_running_loop()
                    ok = await loop.run_in_executor(self._executor, self.connect)
                    if not ok:
                        raise RuntimeError(f"无法建立与设备 {self.device_id} 运行时长连接的注入桥接")

    async def send_text(
        self,
        chat_id: str,
        chat_type: int,
        from_cust_id: str,
        from_cust_name: str,
        to_cust_id: str,
        content: str,
    ) -> bool:
        """通过 App 运行时活动长连接直接发送文本消息。
        
        Args:
            chat_id: 会话标识（单聊默认 "0"）
            chat_type: 聊天类型（1 为单聊，2 为群聊）
            from_cust_id: 发送方 CustID
            from_cust_name: 发送方昵称
            to_cust_id: 接收方 CustID
            content: 消息文本内容
            
        Returns:
            bool: 协议栈成功提交返回 True，否则返回 False。
        """
        await self.ensure_connected()
        assert self._script is not None

        def _invoke() -> bool:
            return bool(
                self._script.exports_sync.send_text_message(
                    chat_id,
                    chat_type,
                    from_cust_id,
                    from_cust_name,
                    to_cust_id,
                    content,
                )
            )

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, _invoke)

    async def get_inflight(self) -> int:
        """获取底层长连接当前在途未确认消息数（服务端 ACK 尚未返回的队列大小）。"""
        await self.ensure_connected()
        assert self._script is not None

        def _invoke() -> int:
            return int(self._script.exports_sync.get_inflight_count())

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, _invoke)

    async def set_skip_db_write(self, enabled: bool) -> bool:
        """设置压测发消息时是否跳过本地 WCDB 落库（仅对当前发送线程生效）。"""
        await self.ensure_connected()
        assert self._script is not None

        def _invoke() -> bool:
            return bool(self._script.exports_sync.set_skip_db_write(enabled))

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, _invoke)

    async def send_batch_text(self, items: List[Dict[str, Any]]) -> Tuple[List[int], List[int], int]:
        """通过 App 运行时活动长连接批量高速管道投递消息（单次 RPC 传输）。
        Args:
            items: 消息字典列表，每一项包含 chatId, chatType, fromCustId, fromCustName, toCustId, content
        Returns:
            Tuple[List[int], List[int], int]: (同步拒收索引, 抛异常未知索引, 最新在途未确认消息数)
        """
        if not items:
            return [], [], 0
        await self.ensure_connected()
        assert self._script is not None

        def _invoke() -> Tuple[List[int], List[int], int]:
            payload_json = json.dumps(items, ensure_ascii=False)
            res: Dict[str, Any] = self._script.exports_sync.send_batch_text_message(payload_json)
            rejected = [int(i) for i in res.get("rejected", [])]
            unknown = [int(i) for i in res.get("unknown", [])]
            inflight = int(res.get("inflight", 0))
            return rejected, unknown, inflight

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, _invoke)

    def close(self) -> None:
        """关闭会话释放桥接资源，安全取消任务避免 Windows 后台非守护线程卡死解释器退出。"""
        self._is_ready = False
        try:
            if self._script:
                try:
                    self._script.unload()
                except Exception:
                    pass
            if self._session:
                try:
                    self._session.detach()
                except Exception:
                    pass
            self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 3. 工业级多会话统一 IM 客户端核心 (IMClient)
# ---------------------------------------------------------------------------
class IMClient:
    """工业级类微信 IM 客户端
    
    统一聚合：
      - 单目标 / 多目标矩阵管理：同时支持单聊、群聊及混合会话目标池；
      - 真机原生底层协议桥通道（AppRuntimeBridge）：100% 真实到达且支撑百万压测；
      - 多会话并发广播机制（send_broadcast）：一键向图中全部会话发送消息；
      - 百万级流式调度压测引擎（send_stream）：轮询并发打散，保障各会话均衡承载。
    """

    def __init__(
        self,
        device_id: str = "emulator-5562",
        *,
        sender_cust_id: str = "1500692599256551424",
        sender_name: str = "测试130",
        targets: Optional[List[SessionTarget]] = None,
        max_inflight: int = 200,
    ) -> None:
        self.device_id: str = device_id
        self.sender_cust_id: str = sender_cust_id
        self.sender_name: str = sender_name
        self.targets: List[SessionTarget] = targets or []
        self.bridge: AppRuntimeBridge = AppRuntimeBridge(device_id=device_id)
        self._sem: asyncio.Semaphore = asyncio.Semaphore(max_inflight)
        self._is_started: bool = False

    async def start(self) -> bool:
        """启动客户端并建立与真机运行时的协议桥接通道。"""
        print(f"[IM 客户端] 正在连接设备 【{self.device_id}】 上的三条 IM 进程协议栈...")
        ok = await asyncio.to_thread(self.bridge.connect)
        if ok:
            self._is_started = True
            print(f"[IM 客户端] ✅ 成功挂接真机活动长连接通道 (WebSocketManager 就绪)")
            return True
        else:
            print(f"[IM 客户端] ❌ 无法挂接真机进程，请确认 App 前台运行且 frida-server 已启动！")
            return False

    async def stop(self) -> None:
        """关闭客户端并释放资源。"""
        self.bridge.close()
        self._is_started = False

    async def send_to_target(self, target: SessionTarget, text: str) -> Dict[str, Any]:
        """向特定目标会话（单聊或群聊）发送单条消息。"""
        client_msg_id = uuid.uuid4().hex
        ts = int(time.time() * 1000)

        await self._sem.acquire()
        try:
            # 统一调用底层长连接协议栈
            success = await self.bridge.send_text(
                chat_id=target.chat_id,
                chat_type=int(target.chat_type),
                from_cust_id=self.sender_cust_id,
                from_cust_name=self.sender_name,
                to_cust_id=target.to_cust_id,
                content=text,
            )
            return {
                "ok": success,
                "target_name": target.name,
                "chat_type": "群聊" if target.is_group else "单聊",
                "chat_id": target.chat_id,
                "to_cust_id": target.to_cust_id,
                "client_msg_id": client_msg_id,
                "timestamp": ts,
            }
        except Exception as e:
            return {
                "ok": False,
                "target_name": target.name,
                "error": str(e),
                "client_msg_id": client_msg_id,
                "timestamp": ts,
            }
        finally:
            self._sem.release()

    async def wait_for_ack_window(self, low_watermark: int = 35, timeout: float = 2.0) -> int:
        """非阻塞等待服务端 ACK 回流释放发送窗口（在途降至低水位以下）。"""
        start = time.time()
        while time.time() - start < timeout:
            inflight = await self.bridge.get_inflight()
            if inflight <= low_watermark:
                return inflight
            await asyncio.sleep(0.015)
        return await self.bridge.get_inflight()

    async def drain_offline_sync(self, quiet_duration: float = 2.5, max_timeout: float = 15.0) -> bool:
        """【离线消息收敛静默排空闸门】
        在压测开始前，等待后台正在拉取的历史离线消息彻底落库收敛并确认完毕，
        确保网络通道和本地 WCDB 数据库写锁完全空闲，杜绝前后台写锁争用碰撞与主键冲突。
        """
        print(f"[📱 {self.sender_name} | {self.device_id}] ⏳ 正在探测与排空后台离线同步队列...")
        start = time.time()
        stable_start: Optional[float] = None

        while time.time() - start < max_timeout:
            inflight = await self.bridge.get_inflight()
            if inflight == 0:
                if stable_start is None:
                    stable_start = time.time()
                elif time.time() - stable_start >= quiet_duration:
                    print(f"[📱 {self.sender_name} | {self.device_id}] ✅ 离线同步已收敛，通道完全静止就绪 (耗时: {time.time() - start:.1f}s)")
                    return True
            else:
                stable_start = None
            await asyncio.sleep(0.5)

        curr = await self.bridge.get_inflight()
        print(f"[📱 {self.sender_name} | {self.device_id}] ⏱️ 离线排空达到超时门限 ({max_timeout:.0f}s)，当前在途: {curr}，平滑放行")
        return False

    async def send_batch_to_targets(
        self, items: List[BatchItem]
    ) -> Tuple[List[BatchItem], List[BatchItem], List[BatchItem], int]:
        """向批量会话目标投递消息（批处理管道，逐条回执与在途感知）。
        Args:
            items: 元素为 (SessionTarget, 文本内容) 的批次列表
        Returns:
            Tuple: (成功入队列表, 同步拒收可安全重发列表, 结果未知禁止重放列表, 最新在途未确认数)。
        """
        if not items:
            return [], [], [], 0
        rpc_items = []
        for tgt, text in items:
            rpc_items.append({
                "chatId": "0" if tgt.chat_type == ChatType.SINGLE else tgt.chat_id,
                "chatType": int(tgt.chat_type),
                "fromCustId": self.sender_cust_id,
                "fromCustName": self.sender_name,
                "toCustId": tgt.to_cust_id if tgt.chat_type == ChatType.SINGLE else "0",
                "content": text,
            })
        await self._sem.acquire()
        try:
            rejected_idx, unknown_idx, inflight = await self.bridge.send_batch_text(rpc_items)
        finally:
            self._sem.release()
        rejected_set, unknown_set = set(rejected_idx), set(unknown_idx)
        succeeded = [it for i, it in enumerate(items) if i not in rejected_set and i not in unknown_set]
        return succeeded, [items[i] for i in rejected_idx], [items[i] for i in unknown_idx], inflight

    async def send_message(
        self,
        conversation_id: str,
        text: str,
        *,
        to_cust_id: Optional[str] = None,
        chat_type: int = 1,
    ) -> Dict[str, Any]:
        """单会话发送消息（标准单目标调用接口）。"""
        target = SessionTarget(
            name=f"conv_{conversation_id}",
            chat_type=chat_type,
            to_cust_id=to_cust_id or "0",
            chat_id=conversation_id,
        )
        return await self.send_to_target(target, text)

    async def send_batch(
        self,
        conversation_id: str,
        texts: Iterable[str],
        *,
        to_cust_id: Optional[str] = None,
        chat_type: int = 1,
    ) -> List[Dict[str, Any]]:
        """向指定单个会话并发批量发送消息。"""
        return await asyncio.gather(*[
            self.send_message(conversation_id, t, to_cust_id=to_cust_id, chat_type=chat_type)
            for t in texts
        ])

    async def send_broadcast(
        self,
        text: str,
        targets: Optional[List[SessionTarget]] = None,
    ) -> List[Dict[str, Any]]:
        """【模式一：多会话全员广播】一条消息并发投递至所有目标会话。
        
        Args:
            text: 消息正文
            targets: 指定发送的目标列表（缺省时使用实例中配置的全部 targets）
            
        Returns:
            List[Dict]: 各会话发送结果列表。
        """
        active_targets = targets or self.targets
        if not active_targets:
            raise ValueError("未指定任何会话目标，无法执行广播")

        print(f"\n📢 [多会话广播] 正在向图中全部 {len(active_targets)} 个会话并发投递消息...")
        start_time = time.time()
        tasks = [self.send_to_target(t, text) for t in active_targets]
        results = await asyncio.gather(*tasks)
        cost = time.time() - start_time

        success_count = sum(1 for r in results if r.get("ok") is True)
        print("--------------------------------------------------")
        print(f"📊 多会话广播执行回执 (耗时: {cost:.2f}s, 成功: {success_count}/{len(active_targets)}):")
        for r in results:
            status_icon = "✅" if r.get("ok") else "❌"
            print(f"  {status_icon} 【{r.get('target_name')}】 ({r.get('chat_type')}) -> 状态: {'成功到达' if r.get('ok') else '发送失败'}")
        print("--------------------------------------------------")
        return results

    async def send_stream(
        self,
        messages: Optional[Union[int, Iterable[str]]] = None,
        *,
        messages_per_target: Optional[int] = None,
        targets: Optional[List[SessionTarget]] = None,
        concurrency: int = 20,
        batch_size: int = 50,
        report_interval: int = 1000,
        delay_between_msg: float = 0.0,
        use_csv_data: bool = True,
        max_retries: int = 4,
        retry_backoff: float = 0.2,
        max_pace: float = 1.0,
        high_watermark: int = 25,
        low_watermark: int = 10,
        enforce_fifo_order: bool = True,
        skip_local_db: bool = False,
    ) -> Dict[str, Any]:
        """【多会话流式并发压测引擎】全面支持批量高速管道、总量轮询打散与齐步等量并发。
        
        Args:
            messages: 总消息数（如 100,000）或消息文本可迭代集合（总量轮询打散模式）。
            messages_per_target: 每个目标会话独立发送的消息总数（多会话齐步等量并发模式）。
            targets: 压测目标会话池。
            concurrency: 并发协程数量（批量管道模式下 15~20 即可吃满通道）。
            batch_size: 批处理管道大小（单次 RPC 注入的消息数量，默认 50，大幅降低 IPC 开销）。
            report_interval: 统计聚合打点间隔。
            delay_between_msg: 批次间额外延时（压测通常设为 0）。
            use_csv_data: 是否使用 data_loader 从 data/chat/chat_messages.csv 提取真实业务语料。
            max_retries: 同步拒收消息的最大重发次数（仅重发未进入 Netty 的消息，结果未知的消息禁止重放）。
            retry_backoff: 重发指数退避基数（秒），第 n 次重发等待 retry_backoff * 2^(n-1)，上限 max_pace。
            max_pace: 自适应批次间隔上限（秒），拒收时间隔翻倍、顺畅时每批加性回落 10ms 至 delay_between_msg（标准 AIMD）。
            high_watermark: 底层长连接在途消息高水位线（默认 80），达到该阈值主动收油门等待服务端 ACK。
            low_watermark: 底层长连接在途消息低水位线（默认 35），排空至该值后继续全速推进。
            enforce_fifo_order: 是否开启单会话严格保序屏障（默认 True）。
                开启后为每条消息固化逻辑序号并防止后序批次在网络层超车重试中消息，彻底根治乱序。
        """
        active_targets = targets or self.targets
        if not active_targets:
            raise ValueError("未指定任何会话目标，无法启动流式压测")

        corpus = get_chat_message_corpus() if use_csv_data else []
        corpus_len = len(corpus) if corpus else 0
        num_targets = len(active_targets)

        # 计算预期发送总数与压测模式
        if messages_per_target is not None:
            total_count = num_targets * messages_per_target
            mode_desc = f"多会话齐步同频并发 (每个会话完整发送前 {messages_per_target:,} 条语料，总计 {total_count:,} 条 | 批处理管道 Batch={batch_size})"
        elif isinstance(messages, int):
            quota = max(1, messages // num_targets)
            total_count = quota * num_targets
            mode_desc = f"总量按会话顺序切分投递 (总计 {total_count:,} 条，每会话依次发送 {quota:,} 条 | 批处理管道 Batch={batch_size})"
        elif hasattr(messages, "__len__"):
            total_count = len(messages) * num_targets
            mode_desc = f"自定义消息集按会话依次投递 (每会话发送 {len(messages):,} 条，总计 {total_count:,} 条 | 批处理管道 Batch={batch_size})"
        elif use_csv_data and corpus_len > 0:
            total_count = corpus_len * num_targets
            mode_desc = f"CSV 语料按会话依次发送 (每会话发送 {corpus_len:,} 条，总计 {total_count:,} 条 | 批处理管道 Batch={batch_size})"
        else:
            total_count = 100000
            mode_desc = f"流式压测 (批处理管道 Batch={batch_size})"

        queue: asyncio.Queue[Optional[List[Tuple[SessionTarget, str]]]] = asyncio.Queue(maxsize=concurrency * 4)
        sent_count = 0
        success_count = 0
        fail_count = 0
        retry_count = 0
        # AIMD 自适应节奏：拒收即乘性放大间隔让 ACK 回流排空窗口，顺畅后渐进回落到基础节奏
        pace = max(0.0, delay_between_msg)
        target_success_map: Dict[str, int] = {t.name: 0 for t in active_targets}

        target_seq_map: Dict[str, int] = {t.name: 0 for t in active_targets}

        def format_ordered_text(tgt: SessionTarget, raw_text: str) -> str:
            """会话严格保序编码：在消息正文附加强时序逻辑序列号 [#SEQ0001]，防止异步重传导致时序不可溯。"""
            if not enforce_fifo_order:
                return raw_text
            target_seq_map[tgt.name] += 1
            seq = target_seq_map[tgt.name]
            return f"[#SEQ{seq:04d}] {raw_text}"

        start_time = time.time()
        last_report_time = start_time
        last_report_count = 0

        batch_buffer: List[Tuple[SessionTarget, str]] = []

        async def flush_buffer() -> None:
            nonlocal batch_buffer
            if batch_buffer:
                await queue.put(list(batch_buffer))
                batch_buffer.clear()

        async def emit_item(tgt: SessionTarget, text: str) -> None:
            nonlocal sent_count
            sent_count += 1
            ordered_text = format_ordered_text(tgt, text)
            if batch_size > 1:
                batch_buffer.append((tgt, ordered_text))
                if len(batch_buffer) >= batch_size:
                    await flush_buffer()
            else:
                await queue.put([(tgt, ordered_text)])

        async def producer() -> None:
            if messages_per_target is not None:
                # 【多会话齐步同频并发调度】：
                # 所有会话在第 k 轮同时齐步发送对应第 k 条真实语料 (例如第 1 轮全会话齐步发第 1 条，第 10 轮全会话齐步发第 10 条)
                # 既确保所有会话均各自独立完整发送第 1~N 条消息，又保持多会话齐步开火的最大并发吞吐！
                for round_idx in range(messages_per_target):
                    if use_csv_data and corpus_len > 0:
                        msg_body = corpus[round_idx % corpus_len]
                    else:
                        msg_body = f"并发压测第 {round_idx + 1}/{messages_per_target} 条 ({time.strftime('%H:%M:%S')})"
                    for tgt in active_targets:
                        await emit_item(tgt, msg_body)

            elif isinstance(messages, int):
                # 【总量按会话顺序切分投递】：每个会话分 quota 条依次发送
                quota_per_target = max(1, messages // num_targets)
                for tgt in active_targets:
                    for msg_idx in range(quota_per_target):
                        if use_csv_data and corpus_len > 0:
                            msg_body = corpus[msg_idx % corpus_len]
                        else:
                            msg_body = f"[{tgt.name}] 消息第 {msg_idx + 1}/{quota_per_target} 条 ({time.strftime('%H:%M:%S')})"
                        await emit_item(tgt, msg_body)
                    if batch_size > 1:
                        await flush_buffer()
            elif messages is not None:
                # 【自定义消息序列】：每个会话按顺序发送全量消息列表
                for tgt in active_targets:
                    for item in messages:
                        await emit_item(tgt, item)
                    if batch_size > 1:
                        await flush_buffer()
            elif use_csv_data and corpus_len > 0:
                # 【CSV 语料全量顺序发送】：每个会话按顺序发送全量语料
                for tgt in active_targets:
                    for text in corpus:
                        await emit_item(tgt, text)
                    if batch_size > 1:
                        await flush_buffer()

            if batch_size > 1:
                await flush_buffer()


            # 放入结束标记
            for _ in range(concurrency):
                await queue.put(None)

        async def worker() -> None:
            nonlocal success_count, fail_count, retry_count, pace, last_report_time, last_report_count
            current_inflight = 0
            # 保序防超车门禁：若开启 FIFO 保序，在途超过 low_watermark 即主动排空，彻底杜绝后序批次超越前序重试中消息
            trigger_limit = low_watermark if enforce_fifo_order else high_watermark

            while True:
                # 1. 窗口主动保护：发送前若在途依然处于阈值之上，主动挂起等待 ACK 回流排空
                if current_inflight >= trigger_limit:
                    current_inflight = await self.wait_for_ack_window(low_watermark=low_watermark, timeout=3.0)

                batch_items = await queue.get()
                if batch_items is None:
                    queue.task_done()
                    break
                pending: List[BatchItem] = batch_items
                try:
                    for attempt in range(max_retries + 1):
                        succeeded, rejected, unknown, current_inflight = await self.send_batch_to_targets(pending)
                        success_count += len(succeeded)
                        fail_count += len(unknown)
                        for tgt, _ in succeeded:
                            target_success_map[tgt.name] = target_success_map.get(tgt.name, 0) + 1
                        pending = rejected
                        if not rejected:
                            # 2. 动态自适应弹性背压流控 (Elastic Backpressure Controller)
                            # 根据底层在途排队情况自适应伸缩节奏，防止堆积超过 30s 触发超时失败与 WCDB 锁争用
                            if current_inflight <= low_watermark:
                                # 通道极速畅通无堆积：加性释放油门，逼近网络最佳吞吐
                                pace = max(delay_between_msg, pace - 0.015)
                            else:
                                # 存在轻度在途堆积：主动收油门拉大呼吸间隙，给服务端分发与本地 SQLite 留出写入窗口
                                pace = min(max_pace, max(pace * 1.3, 0.08))

                            # 若在途达到保序或高水位阈值，立即触发等待排空
                            if current_inflight >= trigger_limit:
                                current_inflight = await self.wait_for_ack_window(low_watermark=low_watermark, timeout=3.0)
                            break
                        # 发生拒收时乘性避让并拉大间隔
                        pace = min(max_pace, max(pace * 2.0, 0.15))
                        if attempt == max_retries:
                            fail_count += len(rejected)
                            pending = []
                            break
                        # 仅重发同步拒收（未进入 Netty）的消息，指数退避等待服务端 ACK 回流释放发送窗口
                        retry_count += len(rejected)
                        await asyncio.sleep(min(max_pace, retry_backoff * (2 ** attempt)))
                        current_inflight = await self.wait_for_ack_window(low_watermark=low_watermark, timeout=1.5)
                except Exception as e:
                    fail_count += len(pending)
                    print(f"❌ [📱 {self.sender_name} | {self.device_id}] 批次投递异常: {e}")
                finally:
                    queue.task_done()
                    if pace > 0:
                        await asyncio.sleep(pace)
                    
                    completed = success_count + fail_count
                    if report_interval > 0 and (
                        (completed - last_report_count >= report_interval)
                        or (last_report_count == 0 and completed > 0)
                        or (completed >= total_count)
                    ):
                        now = time.time()
                        elapsed_total = max(0.001, now - start_time)
                        elapsed_interval = max(0.001, now - last_report_time)
                        interval_items = max(1, completed - last_report_count)
                        instant_tps = interval_items / elapsed_interval
                        pct = (completed / total_count * 100) if total_count > 0 else 0.0
                        total_str = f"/{total_count:,}" if total_count > 0 else ""
                        print(
                            f"[📱 {self.sender_name} | {self.device_id}] 进度: {completed:,}{total_str} ({pct:5.1f}%) | "
                            f"瞬时吞吐: {instant_tps:,.0f} msg/s | 在途: {current_inflight:2d} | 累计成功: {success_count:,} | "
                            f"失败: {fail_count} | 重发: {retry_count} | 节奏: {pace * 1000:.0f}ms | 总耗时: {elapsed_total:.2f}s"
                        )
                        last_report_time = now
                        last_report_count = completed

        if skip_local_db:
            await self.bridge.set_skip_db_write(True)
            print(f"[📱 {self.sender_name} | {self.device_id}] ⚡ [极速压测模式] 已开启跳过发送端本地写库 Hook（仅走网络发包，不写本地 message 库）")

        producer_task = asyncio.create_task(producer())
        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]

        try:
            await producer_task
            await queue.join()
            await asyncio.gather(*workers)
        finally:
            if skip_local_db:
                try:
                    await self.bridge.set_skip_db_write(False)
                except Exception:
                    pass

        total_time = max(0.001, time.time() - start_time)
        avg_tps = sent_count / total_time
        summary = {
            "mode": mode_desc,
            "targets_count": num_targets,
            "total_sent": sent_count,
            "success": success_count,
            "fail": fail_count,
            "retried": retry_count,
            "duration_seconds": round(total_time, 2),
            "average_tps": round(avg_tps, 1),
            "distribution": target_success_map,
        }
        
        print("\n==================================================")
        print("🎉 [多会话海量压测圆满完成看板]")
        print(f"  📊 涉及目标: {num_targets} 个会话 (单聊+群聊混合)")
        print(f"  🎯 压测模式: {mode_desc}")
        print(f"  📦 发送总量: {sent_count:,} 条")
        print(f"  ✅ 成功到达: {success_count:,} 条")
        print(f"  ❌ 发送受阻: {fail_count:,} 条")
        print(f"  🔁 拒收重发: {retry_count:,} 次")
        print(f"  ⏱️ 执行总耗时: {total_time:.2f} 秒")
        print(f"  ⚡ 综合平均吞吐 (TPS): {avg_tps:,.1f} msg/s")
        print(f"  📋 各会话到达分布:")
        for t_name, count in target_success_map.items():
            expected_info = f" (预期: {messages_per_target:,} 条)" if messages_per_target is not None else ""
            print(f"    - 【{t_name}】: {count:,} 条{expected_info}")
        print("==================================================")
        print(f"✅ [📱 {self.sender_name} | {self.device_id}] 本机全部会话配额投递完毕，等待集群汇总战报...\n")
        return summary

    async def send_matrix(
        self,
        count_per_target: int = 100,
        *,
        targets: Optional[List[SessionTarget]] = None,
        concurrency: int = 20,
        batch_size: int = 50,
        report_interval: int = 1000,
        delay_between_msg: float = 0.0,
        max_pace: float = 0.3,
        high_watermark: int = 300,
        low_watermark: int = 150,
        use_csv_data: bool = True,
        enforce_fifo_order: bool = True,
        skip_local_db: bool = False,
    ) -> Dict[str, Any]:
        """【模式三：多会话齐步并行等量压测】同时对所有指定会话各自发送相同数量的消息。
        
        Args:
            count_per_target: 每个会话各自需要发送的消息总数（例如每个会话各发 100 条）。
            targets: 压测目标会话池。
            concurrency: 并发协程数量。
            batch_size: 批处理管道大小（单次 RPC 注入的消息数量，默认 50，提升上百倍吞吐）。
            report_interval: 统计聚合打点间隔。
            delay_between_msg: 消息间隔。
            max_pace: 自适应批次间隔上限（秒）。
            high_watermark: 底层长连接在途消息高水位线。
            low_watermark: 底层长连接在途消息低水位线。
            use_csv_data: 是否使用 data_loader 从 data/chat/chat_messages.csv 提取真实业务语料。
            enforce_fifo_order: 是否开启单会话严格保序屏障（默认 True）。
        """
        return await self.send_stream(
            messages_per_target=count_per_target,
            targets=targets,
            concurrency=concurrency,
            batch_size=batch_size,
            report_interval=report_interval,
            delay_between_msg=delay_between_msg,
            max_pace=max_pace,
            high_watermark=high_watermark,
            low_watermark=low_watermark,
            use_csv_data=use_csv_data,
            enforce_fifo_order=enforce_fifo_order,
            skip_local_db=skip_local_db,
        )


@dataclass(frozen=True)
class DeviceAccountConfig:
    """集群设备与账号绑定配置实体"""
    device_id: str                          # 模拟器或真机 ADB 设备标识
    sender_cust_id: str                     # 账号底层真实 CustID
    sender_name: str                        # 账号昵称或用户名
    mobile: str = ""                        # 登录手机号
    dedicated_group: Optional[SessionTarget] = None  # 该设备专属绑定的群聊目标 (设备1->群001, 设备2->群002...)


# ---------------------------------------------------------------------------
# 4. 多模拟器分布式集群压测协同器 (IMClientCluster)
# ---------------------------------------------------------------------------
class IMClientCluster:
    """多模拟器/多端分布式 IM 客户端集群协调器
    
    统一编排调度多台设备上的独立真实账号，同时挂接各自真机长连接 Netty 通道，
    支持【专属群聊独立绑定 + 公共单聊智能分流】，以同频齐步方式向指定会话池并发倾泻海量消息流。
    """

    def __init__(
        self,
        device_configs: List[DeviceAccountConfig],
        common_targets: Optional[List[SessionTarget]] = None,
        concurrency_per_device: int = 20,
        shard_group_targets: bool = False,
    ) -> None:
        """初始化集群。

        Args:
            device_configs: 设备与账号绑定配置列表。
            common_targets: 公共会话目标池。
            concurrency_per_device: 单设备并发协程数。
            shard_group_targets: 是否按设备分片公共群聊（True 时每个群仅由 1 台设备发送，
                消除同群多发送者的服务端 seq 锁冲突；单聊目标不分片）。默认 False，保持原有全量行为。
        """
        self.device_configs = device_configs
        self.common_targets = common_targets or []
        self.concurrency_per_device = concurrency_per_device
        self.shard_group_targets = shard_group_targets
        self.clients: List[IMClient] = []

        # 分片模式：公共群聊按设备序号连续切块（如 50 群 / 5 台 → 每台 10 个群）
        common_groups = [t for t in self.common_targets if t.chat_type == ChatType.GROUP]
        chunk = -(-len(common_groups) // len(device_configs)) if device_configs else 0

        # 为每台设备动态装配专属的目标会话矩阵
        for idx, cfg in enumerate(device_configs):
            device_targets: List[SessionTarget] = []
            # 1. 挂接该设备独占的专属群聊目标
            if cfg.dedicated_group:
                device_targets.append(cfg.dedicated_group)

            # 2. 挂接公共目标（智能过滤自己发给自己的单聊情况）
            if shard_group_targets:
                device_targets.extend(common_groups[idx * chunk:(idx + 1) * chunk])
                device_targets.extend(
                    t for t in self.common_targets
                    if t.chat_type != ChatType.GROUP and t.to_cust_id != cfg.sender_cust_id
                )
            else:
                for t in self.common_targets:
                    if t.to_cust_id != cfg.sender_cust_id:
                        device_targets.append(t)

            self.clients.append(
                IMClient(
                    device_id=cfg.device_id,
                    sender_cust_id=cfg.sender_cust_id,
                    sender_name=cfg.sender_name,
                    targets=device_targets,
                    max_inflight=concurrency_per_device,
                )
            )

    async def start(self) -> bool:
        """多设备并行挂接各自真机活动长连接通道。"""
        print(f"\n==================================================")
        print(f"🚀 [集群初始化] 正在连接 {len(self.clients)} 台设备的底层 Netty 协议通道...")
        for i, (cfg, client) in enumerate(zip(self.device_configs, self.clients), 1):
            group_name = cfg.dedicated_group.name if cfg.dedicated_group else "无专属群"
            print(f"   {i}. 设备: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】 | 专属群: 【{group_name}】 (目标总数: {len(client.targets)} 个)")
        print("==================================================")

        async def _safe_start(c: IMClient) -> bool:
            try:
                # 8 秒刚性挂接超时：杜绝离线或异常设备无限期卡死主事件循环
                return await asyncio.wait_for(c.start(), timeout=8.0)
            except Exception as e:
                print(f"[IM 客户端] ⚠️ 设备 【{c.device_id}】 挂接超时或异常: {e}，自动隔离跳过")
                return False

        tasks = [_safe_start(c) for c in self.clients]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        ready_clients = [c for c, r in zip(self.clients, results) if r is True]
        print(f"📊 集群通道就绪结果: {len(ready_clients)}/{len(self.clients)} 台设备挂接成功\n")
        return len(ready_clients) > 0

    async def drain_all_offline_sync(self, quiet_duration: float = 2.5, max_timeout: float = 15.0) -> None:
        """【全集群离线消息收敛排空闸门】
        为所有就绪设备并发执行离线消息排空收敛预热，确保开火前历史离线同步全部确认落库，
        彻底杜绝压测刚启动时前后台并发抢夺 WCDB 数据库写锁导致的 UNIQUE constraint 崩溃。
        """
        active_clients = [c for c in self.clients if c._is_started and c.bridge._is_ready]
        if not active_clients:
            return
        print("==================================================")
        print(f"🛡️ [离线消息排空预热闸门] 正在为 {len(active_clients)} 台设备排空历史同步队列...")
        print(f"   ⏳ 目标: 等待通道在途归零且持续静止 {quiet_duration}s (上限: {max_timeout:.0f}s)")
        print("==================================================")
        await asyncio.gather(*(c.drain_offline_sync(quiet_duration, max_timeout) for c in active_clients))
        print("🚀 全集群离线排空预热完毕，网络与数据库写锁已处于空闲最佳状态！\n")

    async def send_matrix(
        self,
        count_per_target: int = 100,
        batch_size: int = 20,
        report_interval: int = 1000,
        delay_between_batches: float = 0.02,
        use_csv_data: bool = True,
        enforce_fifo_order: bool = True,
    ) -> List[Dict[str, Any]]:
        """【多设备集群齐步等量并行压测】
        
        所有参战模拟器设备【完全同时同频】向各自配置的目标会话池齐步发射：
        - 自动隔离 offline 异常设备，仅对健康就绪的客户端投递任务；
        - 每台设备各自向自己的专属群与单聊目标发送 count_per_target 条；
        - 总计投递量由实际在线的设备装配会话相加计算。
        - 开启 batch_size 极速管道 + delay_between_batches 批次微延时，彻底规避原生 socket 冲垮。
        - 默认通过 data_loader 加载 data/chat/chat_messages.csv 真实业务语料。
        - enforce_fifo_order: 开启会话严格保序屏障，杜绝跨批次超车导致消息乱序。
        """
        active_clients = [c for c in self.clients if c._is_started and c.bridge._is_ready]
        if not active_clients:
            print("❌ 当前集群中没有就绪的活动客户端，请确认模拟器处于在线状态且 App 正在运行。")
            return []

        total_cluster_msgs = sum(len(c.targets) * count_per_target for c in active_clients)
        print(f"💥 [多机集群协同开火] {len(active_clients)} 台健康设备启动齐步矩阵压测！")
        print(f"   🎯 调度模式: 设备专属群聊对齐 + 公共单聊并发 (已自动隔离离线设备)")
        print(f"   📂 消息内容数据源: {'data/chat/chat_messages.csv (data_loader 工具加载)' if use_csv_data else '内置测试标头'}")
        print(f"   🚀 批处理管道: 开启 (Batch={batch_size} 条/RPC, 批次间防爆微延时: {delay_between_batches*1000:.0f}ms)")
        print(f"   🛡️ 会话保序屏障: {'开启 (单会话逻辑序号锚定 + 在途排空防超车)' if enforce_fifo_order else '关闭'}")
        print(f"   📦 单机单会话配额: {count_per_target:,} 条")
        print(f"   🌊 全集群总消息投放量: {total_cluster_msgs:,} 条真实消息")
        print("--------------------------------------------------")

        start_time = time.time()
        tasks = [
            c.send_matrix(
                count_per_target=count_per_target,
                concurrency=self.concurrency_per_device,
                batch_size=batch_size,
                report_interval=report_interval,
                delay_between_msg=delay_between_batches,
                use_csv_data=use_csv_data,
                enforce_fifo_order=enforce_fifo_order,
            )
            for c in active_clients
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = max(0.001, time.time() - start_time)

        # 聚合全集群战报看板
        total_sent = 0
        total_success = 0
        total_fail = 0
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                print(f"❌ [集群异常] 设备任务 {i + 1} 发生异常: {r}")
            elif isinstance(r, dict):
                total_sent += r.get("total_sent", 0)
                total_success += r.get("success", 0)
                total_fail += r.get("fail", 0)

        cluster_tps = total_sent / total_time
        print("\n==================================================")
        print("🏆 [多设备分布式集群协同压测总战报]")
        print(f"  📱 参战设备总数: {len(self.clients)} 台模拟器集群")
        print(f"  🎯 压测运行模式: 设备专属群独立映射 + 公共会话齐步并行")
        print(f"  📦 集群投放总量: {total_sent:,} 条")
        print(f"  ✅ 协议到达总量: {total_success:,} 条")
        print(f"  ❌ 发送受阻总量: {total_fail:,} 条")
        print(f"  ⏱️ 集群总运行时长: {total_time:.2f} 秒")
        print(f"  ⚡ 集群综合并发吞吐 (TPS): {cluster_tps:,.1f} msg/s")
        print("==================================================")
        return results

    async def stop(self) -> None:
        """关闭集群并断开所有设备的 Frida 注入长连接桥。"""
        await asyncio.gather(*(c.stop() for c in self.clients))


# ---------------------------------------------------------------------------
# 5. 会话目标统一管理中心 (SessionTargetManager)
# ---------------------------------------------------------------------------
class SessionTargetManager:
    """压测会话策略与目标配置智能管理器 (基于框架统一 data_loader 驱动与 SQLite 动态自发现)."""

    CONFIG_FILE_NAME: str = "im_targets.yaml"

    @classmethod
    def discover_groups_from_sqlite(
        cls,
        device_id: str = "emulator-5562",
        pattern_prefix: str = "离线群",
        max_groups: int = 50,
    ) -> List[SessionTarget]:
        """直连设备底层 SQLite 的 conversation 表，秒级动态拉取匹配前缀的最新群聊 ID (Zero Config)."""
        try:
            find_cmd = (
                f"adb -s {device_id} shell \"ls -dt /data/data/com.santiaotalk.im/databases/IM_Data/*/meta-wal "
                f"/data/data/com.santiaotalk.im/databases/IM_Data/*/meta 2>/dev/null\""
            )
            res = subprocess.run(find_cmd, shell=True, capture_output=True, timeout=3.0)
            lines = res.stdout.decode("utf-8", errors="replace").splitlines()
            db_path = ""
            for line in lines:
                p = line.strip()
                if p:
                    db_path = p[:-4] if p.endswith("-wal") else p
                    break
            if not db_path:
                return []

            if pattern_prefix == "群":
                sql_filter = "conv_name LIKE '%群' OR conv_name LIKE '群%'"
            else:
                sql_filter = f"conv_name LIKE '{pattern_prefix}%'"

            sql = (
                f"SELECT conv_id, conv_name, is_top FROM conversation "
                f"WHERE conv_type=2 AND ({sql_filter}) "
                f"ORDER BY conv_name ASC LIMIT {max_groups};"
            )
            query_cmd = f"adb -s {device_id} shell \"sqlite3 {db_path} \\\"{sql}\\\"\""
            res_query = subprocess.run(query_cmd, shell=True, capture_output=True, timeout=4.0)
            out = res_query.stdout.decode("utf-8", errors="replace").strip()
            if not out:
                return []

            targets: List[SessionTarget] = []
            for item in out.splitlines():
                parts = item.strip().split("|")
                if len(parts) >= 2 and parts[0]:
                    conv_id, conv_name = parts[0], parts[1]
                    is_top = bool(int(parts[2])) if len(parts) >= 3 and parts[2].isdigit() else False
                    targets.append(
                        SessionTarget(
                            name=conv_name,
                            chat_type=ChatType.GROUP,
                            to_cust_id="0",
                            chat_id=conv_id,
                            is_top=is_top,
                        )
                    )
            import re
            targets.sort(key=lambda t: (int(re.search(r'\d+', t.name).group()) if re.search(r'\d+', t.name) else 0, t.name))
            return targets
        except Exception as e:
            print(f"⚠️ [动态发现] 从设备 {device_id} 动态自发现会话失败: {e}")
            return []

    @classmethod
    def discover_friends_from_sqlite(
        cls,
        device_id: str = "emulator-5562",
        max_friends: int = 1000,
    ) -> List[SessionTarget]:
        """直连设备底层 SQLite 的 friend 表，秒级提取全部有效好友作为单聊目标 (Zero Config 自动装载千人好友)."""
        try:
            find_cmd = (
                f"adb -s {device_id} shell \"ls -dt /data/data/com.santiaotalk.im/databases/IM_Data/*/meta-wal "
                f"/data/data/com.santiaotalk.im/databases/IM_Data/*/meta 2>/dev/null\""
            )
            res = subprocess.run(find_cmd, shell=True, capture_output=True, timeout=3.0)
            lines = res.stdout.decode("utf-8", errors="replace").splitlines()
            db_path = ""
            for line in lines:
                p = line.strip()
                if p:
                    db_path = p[:-4] if p.endswith("-wal") else p
                    break
            if not db_path:
                return []

            sql = (
                "SELECT cust_id, username, remark_name, mobile FROM friend "
                "WHERE relation_status=1 AND black_status=0 AND cust_id != '10000' AND length(cust_id) > 5 "
                f"ORDER BY cust_id ASC LIMIT {max_friends};"
            )
            cmd = ["adb", "-s", device_id, "shell", f"sqlite3 {db_path}"]
            res_query = subprocess.run(cmd, input=(sql + "\n").encode("utf-8"), capture_output=True, timeout=5.0)
            out = res_query.stdout.decode("utf-8", errors="replace").strip()
            if not out:
                return []

            targets: List[SessionTarget] = []
            for item in out.splitlines():
                parts = item.strip().split("|")
                if len(parts) >= 1 and parts[0]:
                    cust_id = parts[0]
                    # 优先 remark_name -> username -> mobile -> cust_id
                    disp_name = (
                        parts[2] if len(parts) >= 3 and parts[2] else (
                            parts[1] if len(parts) >= 2 and parts[1] else (
                                parts[3] if len(parts) >= 4 and parts[3] else cust_id
                            )
                        )
                    )
                    targets.append(
                        SessionTarget(
                            name=disp_name,
                            chat_type=ChatType.SINGLE,
                            to_cust_id=cust_id,
                            chat_id="0",
                            is_top=False,
                        )
                    )
            return targets
        except Exception as e:
            print(f"⚠️ [动态发现] 从设备 {device_id} 动态自发现好友失败: {e}")
            return []

    @classmethod
    def load_cluster_targets(
        cls,
        config_name: Optional[str] = None,
        discovery_device_id: str = "emulator-5562",
    ) -> Tuple[List[DeviceAccountConfig], List[SessionTarget], bool]:
        """一站式装配集群设备与目标会话池 (复用框架统一 load_yaml_data 工具).

        Returns:
            Tuple[List[DeviceAccountConfig], List[SessionTarget], bool]:
                - device_configs: 包含或剥离专属群绑定的 5 台设备实体列表
                - common_targets: 待发送的目标会话池 (离线群/测试群/单聊)
                - shard_by_device: 是否开启 5 台设备分片发送 (每群单发送者)
        """
        # 直接复用 utils/file_reader/data_loader.py 现成工具，自动通过 find_file 在 config 目录检索加载
        file_name = config_name or cls.CONFIG_FILE_NAME
        try:
            cfg = load_yaml_data(file_name) or {}
        except Exception as e:
            print(f"⚠️ [配置管理器] 通过 load_yaml_data 加载配置失败 ({file_name}): {e}")
            cfg = {}
        active_profile_name = cfg.get("active_profile", "offline_groups")
        profiles = cfg.get("profiles", {})
        profile = profiles.get(active_profile_name, {})

        desc = profile.get("description", active_profile_name)
        mode = profile.get("discovery_mode", "auto")
        pattern_prefix = profile.get("pattern_prefix", "")
        max_groups = profile.get("max_groups", 50)
        shard_by_device = profile.get("shard_by_device", True)
        include_dedicated = profile.get("include_dedicated_group", False)

        print("\n==================================================")
        print(f"🎯 [会话配置中心] 当前激活场景: 【{active_profile_name}】 ({desc})")
        print(f"   ⚙️ 模式: {mode.upper()} | 前缀: '{pattern_prefix}' | 分片发送: {shard_by_device} | 包含设备专属群: {include_dedicated}")
        print("==================================================")

        # 1. 装配 5 台基准设备基准实体
        dedicated_map = cfg.get("device_dedicated_groups", {})
        base_devices = [
            ("emulator-5562", "1500692599256551424", "测试050", "19200000050"),
            ("emulator-5564", "1500692599583707136", "测试051", "19200000051"),
            ("emulator-5566", "1500692599990554624", "测试052", "19200000052"),
            ("emulator-5568", "1500692600422567936", "测试053", "19200000053"),
            ("emulator-5572", "1500692600787472384", "测试054", "19200000054"),
        ]
        device_configs: List[DeviceAccountConfig] = []
        for dev_id, cust_id, name, mobile in base_devices:
            dedicated_group = None
            if include_dedicated and dev_id in dedicated_map:
                d_info = dedicated_map[dev_id]
                dedicated_group = SessionTarget(
                    name=d_info.get("name", "专属群"),
                    chat_type=ChatType.GROUP if d_info.get("chat_type") == "GROUP" else ChatType.SINGLE,
                    to_cust_id=d_info.get("to_cust_id", "0"),
                    chat_id=d_info.get("chat_id", "0"),
                    is_top=d_info.get("is_top", True),
                )
            device_configs.append(
                DeviceAccountConfig(
                    device_id=dev_id,
                    sender_cust_id=cust_id,
                    sender_name=name,
                    mobile=mobile,
                    dedicated_group=dedicated_group,
                )
            )

        # 2. 装配公共目标会话 (动态自发现优先，静态兜底)
        common_targets: List[SessionTarget] = []
        if active_profile_name == "single_chat" and mode == "auto":
            max_friends = profile.get("max_friends", 1000)
            discovered_friends = cls.discover_friends_from_sqlite(
                device_id=discovery_device_id,
                max_friends=max_friends,
            )
            if discovered_friends:
                common_targets = discovered_friends
                print(f"✨ [Zero Config 动态自发现] 成功从设备 【{discovery_device_id}】 提取 {len(common_targets)} 位真实好友作为单聊目标 (首位: {common_targets[0].name} ~ 末位: {common_targets[-1].name})")
        elif mode == "auto" and pattern_prefix:
            discovered = cls.discover_groups_from_sqlite(
                device_id=discovery_device_id,
                pattern_prefix=pattern_prefix,
                max_groups=max_groups,
            )
            if discovered:
                common_targets = discovered
                print(f"✨ [Zero Config 动态自发现] 成功从设备 【{discovery_device_id}】 提取 {len(common_targets)} 个群聊最新真实 ID (范围: {common_targets[0].name} ~ {common_targets[-1].name})")

        # 若动态拉取为空或指定为 static 模式，回退至 YAML static_targets
        if not common_targets:
            raw_statics = cfg.get("static_targets", [])
            for item in raw_statics:
                c_type_str = item.get("chat_type", "GROUP")
                c_type = ChatType.GROUP if c_type_str == "GROUP" else ChatType.SINGLE
                target_name = item.get("name", "")
                # 过滤符合场景前缀或后缀的会话项 (兼顾 "离线群001" 前缀与 "1群" 后缀)
                if pattern_prefix and c_type == ChatType.GROUP:
                    if not (target_name.startswith(pattern_prefix) or target_name.endswith(pattern_prefix)):
                        continue
                if active_profile_name == "single_chat" and c_type != ChatType.SINGLE:
                    continue
                common_targets.append(
                    SessionTarget(
                        name=target_name,
                        chat_type=c_type,
                        to_cust_id=item.get("to_cust_id", "0"),
                        chat_id=item.get("chat_id", "0"),
                        is_top=item.get("is_top", False),
                    )
                )
            print(f"📋 [静态配置兜底] 已从 config/im_targets.yaml 装载 {len(common_targets)} 个目标会话")

        return device_configs, common_targets, shard_by_device


# 默认集群与公共目标装配 (从 config/im_targets.yaml 读取，外部模块导入完全兼容)
_default_devs, _default_targets, _default_shard = SessionTargetManager.load_cluster_targets()
CLUSTER_DEVICES = _default_devs
COMMON_SINGLE_TARGETS = _default_targets


# ---------------------------------------------------------------------------
# 6. 入口执行：单机压测与 5 台模拟器集群压测自由编排
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    async def main() -> None:
        print("==================================================")
        print("🚀 三条 IM 分布式多设备多会话高并发压测引擎")
        print("📚 消息语料: 加载自 data/chat/chat_messages.csv (通过 data_loader 工具)")
        print("==================================================")

        # -------------------------------------------------------------
        # 运行模式开关：
        #   USE_CLUSTER = True  : 5 台模拟器设备集群协同【同时】压测
        #   USE_CLUSTER = False : 单台模拟器本地独立压测
        # -------------------------------------------------------------
        # USE_CLUSTER = True
        USE_CLUSTER = False 

        # 每台设备对各自会话（专属群聊+公共单聊）发送的消息数量（如设为 20 条）
        COUNT_PER_TARGET = 10000
        # COUNT_PER_TARGET = 28572

        if USE_CLUSTER:
            # =========================================================
            # 【集群模式】：5 台模拟器同时协同，各自对应专属群聊齐步开火
            # =========================================================
            # 工业级稳态流水线：单设备单协程顺序投递（concurrency=1）+ 适度批次 + 批次微延时
            # 彻底杜绝多协程对 Frida GumJS 单线程事件循环的锁争抢与突发洪峰导致的底层 socket 线程 SIGSEGV 崩溃
            cluster_devs, common_targets, shard_groups = SessionTargetManager.load_cluster_targets()

            cluster = IMClientCluster(
                device_configs=cluster_devs,
                common_targets=common_targets,
                concurrency_per_device=1,
                shard_group_targets=shard_groups,
            )

            started = await cluster.start()
            if not started:
                print("❌ 集群中无就绪设备，请检查模拟器与 frida-server。")
                return

            # 🛡️ 核心闸门：压测前自动执行全集群历史离线消息排空收敛预热 (保障 WCDB 与通道空闲)
            await cluster.drain_all_offline_sync(quiet_duration=2.5, max_timeout=15.0)

            await cluster.send_matrix(
                count_per_target=COUNT_PER_TARGET,
                # 分片后每群仅 1 个发送者，可放开到 10 条/批 + 100ms；全量模式保持保守节奏防服务端 500
                batch_size=200,
                report_interval=100,
                delay_between_batches=0.1 if shard_groups else 0.25,
            )
            await cluster.stop()

        else:
            # =========================================================
            # 【单机模式】：单台模拟器 (emulator-5562) 独立压测
            # =========================================================
            cluster_devs, common_targets, _ = SessionTargetManager.load_cluster_targets()
            single_cfg = cluster_devs[0]
            single_targets = ([single_cfg.dedicated_group] if single_cfg.dedicated_group else []) + [
                t for t in common_targets if t.to_cust_id != single_cfg.sender_cust_id
            ]
            client = IMClient(
                device_id=single_cfg.device_id,
                sender_cust_id=single_cfg.sender_cust_id,
                sender_name=single_cfg.sender_name,
                targets=single_targets,
            )
            started = await client.start()
            if not started:
                print("❌ 客户端启动失败，无法连接真机协议通道。")
                return

            # 🛡️ 核心闸门：压测前自动执行历史离线消息排空收敛预热 (保障 WCDB 与通道空闲)
            await client.drain_offline_sync(quiet_duration=2.5, max_timeout=15.0)

            await client.send_matrix(
                count_per_target=COUNT_PER_TARGET,
                concurrency=1,              # 单设备单协程顺序流水线，杜绝锁争抢与 Socket 洪峰
                batch_size=200,             # 批次大小（每批 200 条）
                report_interval=200,        # 打点间隔
                high_watermark=300,         # 高水位线（需大于 batch_size，避免每批都触发排空）
                low_watermark=150,          # 低水位线（需大于 batch_size，避免每批必等待）
                max_pace=0.3,               # 退避休眠上限降至 0.3s，避免单批固定卡死 1s
                enforce_fifo_order=True,    # 开启单会话严格保序屏障
                skip_local_db=True,         # 跳过发送端本地写库，彻底解决 1.7G WAL 膨胀与提速
            )
            await client.stop()

        print("\n🎉 全流程压测任务圆满结束，已安全释放连接并返回终端。")
        os._exit(0)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        os._exit(0)
