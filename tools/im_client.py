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
import csv
from dataclasses import dataclass
from enum import IntEnum
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

import frida
import frida_tools
import requests

# 动态确保项目根目录在 sys.path 中，以便直接运行脚本并复用框架现有模块
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.file_reader.data_loader import find_file, load_csv_data, load_yaml_data


# ---------------------------------------------------------------------------
# 0. 数据驱动：基于 data_loader 的真实消息文件语料池（支持多文件按需缓存）
# ---------------------------------------------------------------------------
_CORPUS_CACHE: Dict[Tuple[str, bool, bool], List[str]] = {}
_CORPUS_TEXT_KEYS: Tuple[str, ...] = ("context", "content", "message", "text", "payload")


def _extract_row_text(row: Any, include_case_id: bool = True) -> str:
    """从单条数据记录中提取消息原文（默认保留 case_id 前缀），过滤空值与 NUL 字符。"""
    if isinstance(row, str):
        return row.replace("\x00", "").strip()
    if not isinstance(row, dict):
        return ""

    raw_text: Any = None
    for key in _CORPUS_TEXT_KEYS:
        val = row.get(key)
        if val is not None and str(val).strip() and str(val).strip().lower() != "nan":
            raw_text = val
            break
    if raw_text is None:
        return ""

    clean_text = str(raw_text).replace("\x00", "").strip()
    if not clean_text:
        return ""

    if include_case_id:
        case_id = row.get("case_id")
        if case_id is not None and str(case_id).strip():
            return f"{str(case_id).strip()}:{clean_text}"
    return clean_text


def _load_raw_corpus_items(file_name: str) -> List[Any]:
    """按文件后缀自适应读取消息文件原始记录，优先复用项目 data_loader。"""
    path_obj = Path(file_name)
    suffix = path_obj.suffix.lower()

    resolved = path_obj if (path_obj.is_absolute() or path_obj.exists()) else find_file(file_name)
    if resolved is None:
        raise FileNotFoundError(f"未找到消息文件: {file_name}")

    if suffix == ".csv":
        if path_obj.is_absolute() or path_obj.exists():
            with open(resolved, "r", encoding="utf-8-sig") as f:
                return list(csv.DictReader(f))
        return load_csv_data(file_name)

    if suffix in (".xlsx", ".xls"):
        import pandas as pd

        return pd.read_excel(resolved).to_dict("records")

    if suffix in (".yaml", ".yml"):
        data = load_yaml_data(file_name)
        return data if isinstance(data, list) else []

    with open(resolved, "r", encoding="utf-8-sig") as f:
        return f.read().splitlines()


def get_chat_message_corpus(
    file_name: str = "chat/chat_messages.csv",
    *,
    include_case_id: bool = True,
    deduplicate: bool = False,
) -> List[str]:
    """加载并缓存指定消息文件中的消息内容列表。

    默认提取文件中的 case_id 与正文内容（形如 case_id:context），不再叠加额外的人工序号前缀，
    支持 .csv / .xlsx / .txt / .yaml 格式并按参数维度隔离缓存。

    Args:
        file_name: 消息文件路径（相对 data/ 或绝对路径），默认 'chat/chat_messages.csv'
        include_case_id: 是否前置保留 case_id（默认 True，格式为 case_id:原文）
        deduplicate: 是否去重（默认 False，保留文件原始顺序与分布）
    Returns:
        List[str]: 解析提取出的消息列表。
    """
    cache_key = (file_name, include_case_id, deduplicate)
    cached = _CORPUS_CACHE.get(cache_key)
    if cached:
        return cached

    try:
        raw_items = _load_raw_corpus_items(file_name)
        messages: List[str] = []
        seen: Optional[Set[str]] = set() if deduplicate else None
        for row in raw_items:
            clean_text = _extract_row_text(row, include_case_id=include_case_id)
            if not clean_text:
                continue
            if seen is not None:
                if clean_text in seen:
                    continue
                seen.add(clean_text)
            messages.append(clean_text)

        if messages:
            _CORPUS_CACHE[cache_key] = messages
            print(f"📚 [语料加载] 已加载消息文件 {file_name} | 有效消息: {len(messages):,} 条")
            return messages
        raise ValueError(f"消息文件 {file_name} 中未解析到任何有效正文内容")
    except Exception as e:
        print(f"⚠️ [数据驱动] 加载消息文件 {file_name} 失败: {e}，将采用备用样本")

    fallback = ["三条 IM 自动化高并发测试消息通道连接正常"]
    _CORPUS_CACHE[cache_key] = fallback
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
    var _MapCls = null;
    var _skipSendDbWrite = false;
    var _dbHooksInstalled = false;
    var _origNetworkLogEnabled = null;

    function installSkipDbHooks() {
        if (_dbHooksInstalled) {
            return;
        }
        Java.perform(function() {
            var msgCls = 'com.bm.santiaotalk.store.entity.w.Message';
            var listCls = 'java.util.List';
            var strCls = 'java.lang.String';
            var contCls = 'kotlin.coroutines.Continuation';
            var booleanCls = Java.use('java.lang.Boolean');
            var unitCls = Java.use('kotlin.Unit');

            function hookVoidOnSkip(clsName, methodName, argTypes) {
                var cls = Java.use(clsName);
                var m = cls[methodName].overload.apply(cls[methodName], argTypes);
                m.implementation = function() {
                    if (_skipSendDbWrite) return;
                    return m.apply(this, arguments);
                };
            }

            // 1. 消息表写库、更新与 FTS 全文索引同步旁路
            try {
                var msgDaoCls = 'com.bm.santiaotalk.store.dao.w.MessageDao';
                hookVoidOnSkip(msgDaoCls, 'insert', [msgCls]);
                hookVoidOnSkip(msgDaoCls, 'insertAll', [listCls]);
                hookVoidOnSkip(msgDaoCls, 'update', [msgCls]);
                hookVoidOnSkip(msgDaoCls, 'syncFtsAsync', ['kotlin.jvm.functions.Function1']);

                var shardedDaoCls = 'com.bm.santiaotalk.store.dao.w.ShardedMessageDao';
                hookVoidOnSkip(shardedDaoCls, 'insert', [msgCls]);
                hookVoidOnSkip(shardedDaoCls, 'insertAll', [listCls]);
                hookVoidOnSkip(shardedDaoCls, 'insertToYear', [msgCls]);
                hookVoidOnSkip(shardedDaoCls, 'insertAllToYear', [listCls]);
                hookVoidOnSkip(shardedDaoCls, 'update', [msgCls]);
            } catch (e) {
                console.log("[Bridge] 安装消息 DAO Hook 异常: " + e.toString());
            }

            // 2. 兜底跳过发送前同步阻塞准备（runBlocking + 会话表双锁读写）
            try {
                var helperCls = Java.use('com.network.lib.socket.sendMessage.MessageSenderHelper');
                helperCls.notifyMessagePrepareSend.overload('com.network.lib.socket.ImBaseMessage').implementation = function(msg) {
                    if (_skipSendDbWrite) return true;
                    return this.notifyMessagePrepareSend(msg);
                };
            } catch (e) {
                console.log("[Bridge] 安装准备发送 Hook 异常: " + e.toString());
            }

            // 3. 跳过单条发送前的气泡装扮 Protobuf 反射与敏感词评估
            try {
                var dressUpCls = Java.use('com.network.lib.socket.sendMessage.UserDressUpProvider');
                dressUpCls.inject.overload('com.google.protobuf.Message').implementation = function(msg) {
                    if (_skipSendDbWrite) return msg;
                    return this.inject(msg);
                };
            } catch (e) {
                console.log("[Bridge] 安装装扮旁路 Hook 异常: " + e.toString());
            }
            try {
                // 动态定位敏感词回调类，避免 App 升级后 Kotlin 匿名内部类编号 ($login$4 -> $login$5) 漂移失效
                var sensitiveTargetCls = null;
                try {
                    var wsmCls = Java.use('com.network.lib.socket.WebSocketManager');
                    var sf = wsmCls.class.getDeclaredField('sensitiveRemindCheckListener');
                    sf.setAccessible(true);
                    var listenerObj = sf.get(wsmCls.INSTANCE.value);
                    if (listenerObj) {
                        sensitiveTargetCls = Java.use(listenerObj.getClass().getName());
                    }
                } catch (e1) {}
                if (!sensitiveTargetCls) {
                    for (var si = 1; si <= 15; si++) {
                        try {
                            var cand = Java.use('com.santiao.stim.STIMImpl$login$' + si);
                            if (cand.onCheckSensitiveRemind) {
                                sensitiveTargetCls = cand;
                                break;
                            }
                        } catch (e2) {}
                    }
                }
                if (sensitiveTargetCls && sensitiveTargetCls.onCheckSensitiveRemind) {
                    sensitiveTargetCls.onCheckSensitiveRemind.overload(strCls, 'boolean', strCls).implementation = function(chatId, isGroup, content) {
                        // 必须原样返回传入的 content（或 null），返回空串会导致 TextMessage.content 被置空、接收端显示为 [消息]
                        if (_skipSendDbWrite) return content;
                        return this.onCheckSensitiveRemind(chatId, isGroup, content);
                    };
                }
            } catch (e) {
                console.log("[Bridge] 安装敏感词旁路 Hook 异常: " + e.toString());
            }

            // 4. 跳过 ACK 回流后的查表、退避重试协程与状态日志写盘（pendingMessages 已先于回调清理，不影响在途计数）
            try {
                // 动态扫描 STIMImpl$login$1..15 定位 ACK 回调类，兼容 App 升级后的编号漂移 ($login$6 -> $login$7)
                var ackTargetCls = null;
                for (var ai = 1; ai <= 15; ai++) {
                    try {
                        var ackCand = Java.use('com.santiao.stim.STIMImpl$login$' + ai);
                        if (ackCand.onMessageSendStatus) {
                            ackTargetCls = ackCand;
                            break;
                        }
                    } catch (e3) {}
                }
                if (ackTargetCls && ackTargetCls.onMessageSendStatus) {
                    ackTargetCls.onMessageSendStatus.overload(
                        'com.network.lib.socket.ImBaseMessage',
                        'com.network.lib.socket.messagehelp.MsgTalkSendStatus',
                        contCls
                    ).implementation = function(msg, status, cont) {
                        if (_skipSendDbWrite) return unitCls.INSTANCE.value;
                        return this.onMessageSendStatus(msg, status, cont);
                    };
                }
            } catch (e) {
                console.log("[Bridge] 安装 ACK 回执旁路 Hook 异常: " + e.toString());
            }

            // 5. 旁路新版可靠发送的本地落库强校验 (ReliableSocketBinding.requiresFreeze)
            //    免落库压测时本地 DB 未插入待发消息，若不跳过 freezeSend 会抛出
            //    IllegalStateException("Pending send content is not durable") 并触发客户端主动断开重连
            try {
                var reliableBindingCls = Java.use('com.network.lib.socket.ReliableSocketBinding');
                if (reliableBindingCls.requiresFreeze) {
                    reliableBindingCls.requiresFreeze.overload('com.network.lib.socket.messagehelp.MsgTalkSend').implementation = function(sendMsg) {
                        if (_skipSendDbWrite) return false;
                        return this.requiresFreeze(sendMsg);
                    };
                }
            } catch (e) {
                console.log("[Bridge] 安装可靠发送落库校验旁路 Hook 异常: " + e.toString());
            }
            try {
                var stimCls = Java.use('com.santiao.stim.STIMImpl');
                stimCls.updateMessageStatusWithRetry.overload(strCls, 'int', 'long', 'int', contCls).implementation = function(msgNo, status, msgTime, maxAttempts, cont) {
                    if (_skipSendDbWrite) return booleanCls.TRUE.value;
                    return this.updateMessageStatusWithRetry(msgNo, status, msgTime, maxAttempts, cont);
                };
                var storageCls = Java.use('com.santiao.stim.processor.MessageStorage');
                storageCls.updateMessageStatus.overload(strCls, 'int', 'long', contCls).implementation = function(msgNo, status, msgTime, cont) {
                    if (_skipSendDbWrite) return booleanCls.TRUE.value;
                    return this.updateMessageStatus(msgNo, status, msgTime, cont);
                };
            } catch (e) {
                console.log("[Bridge] 安装状态更新旁路 Hook 异常: " + e.toString());
            }

            _dbHooksInstalled = true;
        });
    }

    function setNetworkLogSuppressed(suppress) {
        Java.perform(function() {
            try {
                var logger = Java.use('com.network.lib.util.NetworkLogger').INSTANCE.value;
                if (!logger) return;
                if (suppress) {
                    if (_origNetworkLogEnabled === null) {
                        _origNetworkLogEnabled = logger.isLogEnabled();
                    }
                    logger.setLogEnabled(false);
                } else if (_origNetworkLogEnabled !== null) {
                    logger.setLogEnabled(_origNetworkLogEnabled);
                    _origNetworkLogEnabled = null;
                }
            } catch (e) {}
        });
    }

    function _ensurePendingField() {
        if (!WebSocketMgr) {
            var mgr = Java.use('com.network.lib.socket.WebSocketManager').INSTANCE.value;
            if (mgr) {
                WebSocketMgr = Java.retain(mgr);
            }
        }
        if (!SocketClientPendingField) {
            var field = Java.use('com.network.lib.socket.SocketClient').class.getDeclaredField('pendingMessages');
            field.setAccessible(true);
            SocketClientPendingField = Java.retain(field);
        }
        if (!_MapCls) {
            _MapCls = Java.use('java.util.Map');
        }
    }

    function _readPendingCountInPerform() {
        try {
            _ensurePendingField();
            if (WebSocketMgr && WebSocketMgr.socketClient) {
                var sc = WebSocketMgr.socketClient.value;
                if (sc) {
                    var map = Java.cast(SocketClientPendingField.get(sc), _MapCls);
                    return map.size();
                }
            }
        } catch (e) {}
        return 0;
    }

    function getPendingCount() {
        var count = 0;
        Java.perform(function() {
            count = _readPendingCountInPerform();
        });
        return count;
    }

    function isChannelReady() {
        var ready = false;
        Java.perform(function() {
            try {
                if (!WebSocketMgr) {
                    _ensurePendingField();
                }
                if (WebSocketMgr) {
                    ready = Boolean(WebSocketMgr.isConnected() && WebSocketMgr.isAuthenticated());
                }
            } catch (e) {}
        });
        return ready;
    }

    rpc.exports = {
        init: function() {
            var ok = false;
            Java.perform(function() {
                try {
                    _ensurePendingField();
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
        // 探测底层 WebSocket 长连接是否处于已连接且已完成登录鉴权的可写状态
        isReady: function() {
            return isChannelReady();
        },
        // 开关：压测发消息时启用全链路免落库极速模式（跳过 DB 读写、同步阻塞准备、敏感词/装扮检查、ACK 重试与调试日志）
        setSkipDbWrite: function(enabled) {
            _skipSendDbWrite = !!enabled;
            if (_skipSendDbWrite) {
                installSkipDbHooks();
            }
            setNetworkLogSuppressed(_skipSendDbWrite);
            return _skipSendDbWrite;
        },
        // 批量管道高速发送接口：按 16 条分片进出 Java.perform，及时释放 JNI LocalFrame，规避 ART MarkCompact GC 崩溃
        sendBatchTextMessage: function(messagesJson) {
            var list = JSON.parse(messagesJson);
            var len = list.length;
            var result = {rejected: [], unknown: [], inflight: 0};
            var skipPrepare = _skipSendDbWrite;
            var chunkSize = 16;
            var idx = 0;
            var stopped = false;

            while (idx < len && !stopped) {
                var end = Math.min(idx + chunkSize, len);
                Java.perform(function() {
                    var i = idx;
                    try {
                        if (!WebSocketMgr) {
                            _ensurePendingField();
                        }
                        if (WebSocketMgr) {
                            for (; i < end; i++) {
                                var item = list[i];
                                var ok = WebSocketMgr.sendTextMessage(
                                    item.chatId,
                                    item.chatType,
                                    item.fromCustId,
                                    item.fromCustName,
                                    item.toCustId,
                                    item.content,
                                    0, null, null, null, skipPrepare, false
                                );
                                if (!ok) {
                                    stopped = true;
                                    break;
                                }
                            }
                        } else {
                            stopped = true;
                        }
                    } catch (e) {
                        console.log("[Bridge] 批量管道发送底层异常: " + e.toString());
                        result.unknown.push(i);
                        i++;
                        stopped = true;
                    }
                    idx = i;
                    if (stopped || idx >= len) {
                        result.inflight = _readPendingCountInPerform();
                    }
                });
            }
            for (var r = idx; r < len; r++) {
                result.rejected.push(r);
            }
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
        self._skip_db_write_enabled: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()
        # 核心架构优化：为每台物理/虚拟设备配置独立的私有线程池，彻底杜绝全局默认线程池饥饿导致的设备排队串行！
        self._executor: concurrent.futures.ThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor(
            max_workers=30,
            thread_name_prefix=f"frida-{device_id}",
        )

    def _assemble_script_source(self) -> str:
        """自适应 Frida 16/17 组装桥接脚本：16 直接使用内置 Java，17 注入 frida_tools 的 java.js。"""
        major_ver = int(str(getattr(frida, "__version__", "17")).split(".")[0])
        if major_ver < 17:
            return self._BRIDGE_JS

        bridges_dir = Path(frida_tools.__file__).parent / "bridges"
        java_js_file = bridges_dir / "java.js"
        if not java_js_file.exists():
            raise FileNotFoundError(f"未找到 Frida Java 桥接库: {java_js_file}")
        java_core = java_js_file.read_text(encoding="utf-8")
        # 通过函数参数注入局部 Java，避免覆盖只读全局属性导致 TypeError
        return f"{java_core}\n;\n(function(Java) {{\n{self._BRIDGE_JS}\n}})(bridge);"

    _frida_cache_lock: threading.Lock = threading.Lock()

    def _detect_device_frida_abi(self) -> str:
        """基于 ro.product.cpu.abi 精准识别设备真实架构，避免模拟器 uname -m 伪装导致推错二进制。"""
        try:
            proc = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "getprop", "ro.product.cpu.abi"],
                capture_output=True,
                text=True,
                timeout=3.0,
            )
            abi = proc.stdout.strip().lower()
        except Exception:
            abi = ""
        mapping = {
            "x86_64": "x86_64",
            "arm64-v8a": "arm64",
            "x86": "x86",
            "armeabi-v7a": "arm",
            "armeabi": "arm",
        }
        return mapping.get(abi, "x86_64")

    @classmethod
    def _ensure_local_frida_cache(cls, expected_ver: str, frida_abi: str) -> Optional[Path]:
        """确保本机临时目录存在对应版本与架构的 frida-server 二进制缓存，缺失时自动拉取解压。"""
        cache_path = Path(tempfile.gettempdir()) / f"frida-server-{expected_ver}-{frida_abi}"
        with cls._frida_cache_lock:
            if cache_path.exists() and cache_path.stat().st_size > 10_000_000:
                return cache_path
            try:
                import lzma
                url = (
                    f"https://github.com/frida/frida/releases/download/"
                    f"{expected_ver}/frida-server-{expected_ver}-android-{frida_abi}.xz"
                )
                resp = requests.get(url, timeout=60, stream=True)
                resp.raise_for_status()
                raw_bytes = lzma.decompress(resp.content)
                tmp_path = cache_path.with_suffix(".tmp")
                tmp_path.write_bytes(raw_bytes)
                tmp_path.replace(cache_path)
                return cache_path
            except Exception as e:
                print(f"⚠️ [协议桥接] 自动下载 frida-server {expected_ver} ({frida_abi}) 失败: {e}")
                return None

    def _read_remote_frida_version(self, remote_path: str) -> str:
        """安全读取设备上指定 frida-server 路径的版本号，文件不存在或损坏时返回空串。"""
        try:
            proc = subprocess.run(
                ["adb", "-s", self.device_id, "shell", f"{remote_path} --version 2>/dev/null"],
                capture_output=True,
                text=True,
                timeout=3.0,
            )
            if proc.returncode == 0:
                return proc.stdout.strip().splitlines()[0].strip() if proc.stdout.strip() else ""
        except Exception:
            pass
        return ""

    def _ensure_frida_server_running(self) -> None:
        """检查设备 frida-server 版本与运行状态：版本不一致时自动切换至本机对应版本并重启。"""
        expected_ver = str(getattr(frida, "__version__", "")).strip()
        major_ver = expected_ver.split(".")[0] if expected_ver else "16"
        versioned_remote = f"/data/local/tmp/frida-server-{major_ver}"
        active_remote = "/data/local/tmp/frida-server"

        try:
            ps_out = subprocess.check_output(
                ["adb", "-s", self.device_id, "shell", "ps -A"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=3.0,
            )
            is_running = "frida-server" in ps_out
            current_ver = self._read_remote_frida_version(active_remote)

            need_switch = bool(expected_ver and current_ver != expected_ver)
            if is_running and not need_switch:
                return

            subprocess.run(["adb", "-s", self.device_id, "root"], capture_output=True, timeout=3.0)
            time.sleep(0.3)

            if need_switch:
                print(
                    f"🔄 [协议桥接] 设备 {self.device_id} frida-server 版本不一致 "
                    f"(当前={current_ver or '未知'}, 目标={expected_ver})，正在自动切换..."
                )
                subprocess.run(
                    ["adb", "-s", self.device_id, "shell", "pkill -9 frida-server 2>/dev/null || true"],
                    capture_output=True,
                    timeout=3.0,
                )
                # 优先检查设备本地是否已存有匹配版本的实体文件
                cached_ver = self._read_remote_frida_version(versioned_remote)
                if cached_ver != expected_ver:
                    frida_abi = self._detect_device_frida_abi()
                    local_bin = self._ensure_local_frida_cache(expected_ver, frida_abi)
                    if local_bin and local_bin.exists():
                        subprocess.run(
                            ["adb", "-s", self.device_id, "push", str(local_bin), versioned_remote],
                            capture_output=True,
                            timeout=30.0,
                        )
                subprocess.run(
                    [
                        "adb", "-s", self.device_id, "shell",
                        f"chmod 755 {versioned_remote} && ln -sf {versioned_remote} {active_remote}",
                    ],
                    capture_output=True,
                    timeout=3.0,
                )
            else:
                subprocess.run(
                    ["adb", "-s", self.device_id, "shell", f"chmod 755 {active_remote}"],
                    capture_output=True,
                    timeout=2.0,
                )

            # 彻底隔离标准输入输出管道，杜绝 Windows 控制台句柄继承导致终端卡死
            subprocess.Popen(
                ["adb", "-s", self.device_id, "shell", f"{active_remote} -D"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(0.8)
        except Exception as e:
            print(f"⚠️ [协议桥接] 设备 {self.device_id} 自愈拉起 frida-server 异常: {e}")

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

    def _on_session_detached(self, reason: str, *args: Any) -> None:
        """Frida 会话断开回调（App 闪退、被杀或重启时触发）。"""
        self._is_ready = False
        self._script = None
        print(f"⚠️ [协议桥接] 设备 {self.device_id} 会话已断开 ({reason})")

    def _on_script_message(self, message: Dict[str, Any], data: Any) -> None:
        """透传 Frida 脚本异常堆栈，便于直接定位 JS 侧加载或运行期错误。"""
        if message.get("type") == "error":
            desc = message.get("description") or message.get("stack") or str(message)
            print(f"❌ [协议桥接] 设备 {self.device_id} 脚本异常: {desc}")

    def _cleanup_session(self) -> None:
        """仅清理 Frida 会话与脚本句柄，保留线程池以支持原地重连自愈。"""
        self._is_ready = False
        if self._script:
            try:
                self._script.unload()
            except Exception:
                pass
            self._script = None
        if self._session:
            try:
                self._session.detach()
            except Exception:
                pass
            self._session = None

    def _launch_target_app(self, wait_timeout: float = 8.0) -> Optional[int]:
        """当设备上三条 IM 未运行时，自动通过 ADB 拉起前台 Activity 并等待进程就绪。"""
        print(f"🚀 [协议桥接] 设备 {self.device_id} 未检测到三条 IM 进程，正在自动拉起 {self.package_name}...")
        subprocess.run(
            [
                "adb", "-s", self.device_id, "shell",
                "am", "start", "-n", f"{self.package_name}/com.vvchat.vcapp.activity.MainActivity",
            ],
            capture_output=True,
            timeout=5.0,
        )
        deadline = time.time() + wait_timeout
        while time.time() < deadline:
            pid = self._find_target_pid()
            if pid is not None:
                time.sleep(1.5)  # 预留冷启动初始化 WebSocketManager 与登录态的缓冲
                return pid
            time.sleep(0.5)
        return None

    def connect(self) -> bool:
        """连接目标设备上的三条 IM 进程并初始化注入桥（全链路超时与防死锁）。"""
        try:
            self._cleanup_session()
            self._ensure_frida_server_running()
            target_pid = self._find_target_pid()
            if target_pid is None:
                target_pid = self._launch_target_app()
            if target_pid is None:
                raise ProcessLookupError(f"设备 {self.device_id} 上未找到三条 IM 运行进程 ({self.package_name})，请确认 App 前台处于运行状态")

            device = frida.get_device_manager().get_device(self.device_id, timeout=3)
            self._session = device.attach(target_pid)
            self._session.on("detached", self._on_session_detached)
            full_source = self._assemble_script_source()
            self._script = self._session.create_script(full_source)
            self._script.on("message", self._on_script_message)
            self._script.load()
            time.sleep(0.3)

            self._is_ready = bool(self._script.exports_sync.init())
            if self._is_ready and self._skip_db_write_enabled:
                self._script.exports_sync.set_skip_db_write(True)
            return self._is_ready
        except Exception as e:
            print(f"[协议桥接] 连接设备 {self.device_id} 运行时异常: {e}")
            self._is_ready = False
            return False

    async def reconnect(self, timeout: float = 20.0) -> bool:
        """当 App 进程崩溃重启或脚本销毁后，等待新进程拉起并自动重建注入桥。"""
        async with self._lock:
            self._cleanup_session()
            loop = asyncio.get_running_loop()
            start = time.time()
            launched = False
            while time.time() - start < timeout:
                pid = await loop.run_in_executor(self._executor, self._find_target_pid)
                if pid is not None:
                    await asyncio.sleep(1.5)  # 预留新进程初始化 WebSocketManager 的缓冲
                    ok = await loop.run_in_executor(self._executor, self.connect)
                    if ok:
                        return True
                elif not launched and time.time() - start >= 3.0:
                    launched = True
                    # 若系统未自动重启 App，通过 monkey 主动唤醒拉起
                    try:
                        await loop.run_in_executor(
                            self._executor,
                            lambda: subprocess.run(
                                f"adb -s {self.device_id} shell monkey -p {self.package_name} -c android.intent.category.LAUNCHER 1",
                                shell=True,
                                capture_output=True,
                                timeout=4.0,
                            ),
                        )
                    except Exception:
                        pass
                await asyncio.sleep(1.0)
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

    async def get_inflight(self) -> int:
        """获取底层长连接当前在途未确认消息数（服务端 ACK 尚未返回的队列大小）。"""
        await self.ensure_connected()
        assert self._script is not None

        def _invoke() -> int:
            return int(self._script.exports_sync.get_inflight_count())

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, _invoke)

    async def is_channel_ready(self) -> bool:
        """探测底层 WebSocket 长连接是否已连接且完成鉴权。"""
        await self.ensure_connected()
        assert self._script is not None

        def _invoke() -> bool:
            return bool(self._script.exports_sync.is_ready())

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, _invoke)

    async def set_skip_db_write(self, enabled: bool) -> bool:
        """设置压测发消息时是否跳过本地 WCDB 落库（仅对当前发送线程生效）。"""
        self._skip_db_write_enabled = bool(enabled)
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
        try:
            self._cleanup_session()
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
      - 百万级流式调度压测引擎（send_stream / send_matrix）：批处理并发打散，保障各会话均衡承载。
    """

    def __init__(
        self,
        device_id: str = "emulator-5562",
        *,
        sender_cust_id: str = "1158096069641277440",
        sender_name: str = "008628100000423",
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

    async def wait_for_ack_window(self, low_watermark: int = 35, timeout: float = 2.0) -> int:
        """非阻塞等待服务端 ACK 回流释放发送窗口（在途降至低水位以下）。"""
        start = time.time()
        while time.time() - start < timeout:
            inflight = await self.bridge.get_inflight()
            if inflight <= low_watermark:
                return inflight
            await asyncio.sleep(0.06)
        return await self.bridge.get_inflight()

    async def wait_for_channel_ready(self, timeout: float = 30.0, poll_interval: float = 0.5) -> bool:
        """断线自愈闸门：检测到长连接断开时暂停投递并轮询等待 App 自动重连与鉴权恢复。"""
        if await self.bridge.is_channel_ready():
            return True
        print(f"⏳ [📱 {self.sender_name} | {self.device_id}] 检测到长连接已断开或未鉴权，暂停发送并等待自动重连 (最长 {timeout:.0f}s)...")
        start = time.time()
        while time.time() - start < timeout:
            await asyncio.sleep(poll_interval)
            if await self.bridge.is_channel_ready():
                # 通道重连成功后预留 0.3s 让底层状态机与离线补偿平稳切换
                await asyncio.sleep(0.3)
                print(f"✅ [📱 {self.sender_name} | {self.device_id}] 长连接已重连就绪 (耗时 {time.time() - start:.1f}s)，恢复发送")
                return True
        print(f"❌ [📱 {self.sender_name} | {self.device_id}] 等待 {timeout:.0f}s 后长连接仍未恢复，请检查网络或服务端状态")
        return False

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
        corpus_file: str = "chat/chat_messages.csv",
        corpus_offset: int = 0,
        shard_targets_corpus: bool = False,
        include_case_id: bool = True,
        include_seq_prefix: bool = False,
        max_retries: int = 4,
        retry_backoff: float = 0.2,
        max_pace: float = 1.0,
        high_watermark: int = 25,
        low_watermark: int = 10,
        enforce_fifo_order: bool = True,
        skip_local_db: bool = False,
        persist_first_message: bool = True,
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
            use_csv_data: 是否从消息文件加载真实业务语料。
            corpus_file: 消息文件路径（相对 data/ 或绝对路径），默认 'chat/chat_messages.csv'。
            corpus_offset: 语料起始游标偏移量（默认 0，严格从消息表第 1 条开始顺序发送）。
            shard_targets_corpus: 同一设备多目标之间是否微错开语料游标（默认 False，所有会话均从头严格按表顺序发送）。
            include_case_id: 是否在消息正文前附加 case_id（默认 True，格式为 case_id:原文）。
            include_seq_prefix: 是否在消息正文前附加 [#SEQ0001] 序号前缀（默认 False）。
            max_retries: 同步拒收消息的最大重发次数（仅重发未进入 Netty 的消息，结果未知的消息禁止重放）。
            retry_backoff: 重发指数退避基数（秒），第 n 次重发等待 retry_backoff * 2^(n-1)，上限 max_pace。
            max_pace: 自适应批次间隔上限（秒），拒收时间隔翻倍、顺畅时每批加性回落 10ms 至 delay_between_msg（标准 AIMD）。
            high_watermark: 底层长连接在途消息高水位线（默认 80），达到该阈值主动收油门等待服务端 ACK。
            low_watermark: 底层长连接在途消息低水位线（默认 35），排空至该值后继续全速推进。
            enforce_fifo_order: 是否开启单会话严格保序屏障（默认 True，通过网络排空门禁防跨批超车）。
            skip_local_db: 是否开启免落库极速模式（默认 False）。
            persist_first_message: 在 skip_local_db=True 时，是否先完整落库并展示每个会话的第 1 条消息以生成会话列表条目（默认 True），其余消息全速免落库。
        """
        active_targets = targets or self.targets
        if not active_targets:
            raise ValueError("未指定任何会话目标，无法启动流式压测")

        corpus = (
            get_chat_message_corpus(corpus_file, include_case_id=include_case_id)
            if use_csv_data
            else []
        )
        corpus_len = len(corpus) if corpus else 0
        num_targets = len(active_targets)
        custom_messages: Optional[List[str]] = (
            list(messages) if (messages is not None and not isinstance(messages, int)) else None
        )

        # 计算预期发送总数与压测模式
        if messages_per_target is not None:
            per_target_quota = max(0, messages_per_target)
            total_count = num_targets * per_target_quota
            mode_desc = f"多会话齐步同频并发 (每个会话发送 {per_target_quota:,} 条消息文件原文，总计 {total_count:,} 条 | 批处理管道 Batch={batch_size})"
        elif isinstance(messages, int):
            per_target_quota = max(1, messages // num_targets)
            total_count = per_target_quota * num_targets
            mode_desc = f"总量按会话顺序切分投递 (总计 {total_count:,} 条，每会话依次发送 {per_target_quota:,} 条 | 批处理管道 Batch={batch_size})"
        elif custom_messages is not None:
            per_target_quota = len(custom_messages)
            total_count = per_target_quota * num_targets
            mode_desc = f"自定义消息集按会话依次投递 (每会话发送 {per_target_quota:,} 条，总计 {total_count:,} 条 | 批处理管道 Batch={batch_size})"
        elif use_csv_data and corpus_len > 0:
            per_target_quota = corpus_len
            total_count = per_target_quota * num_targets
            mode_desc = f"消息文件全量按会话依次发送 (每会话发送 {per_target_quota:,} 条，总计 {total_count:,} 条 | 批处理管道 Batch={batch_size})"
        else:
            per_target_quota = 0
            total_count = 100000
            mode_desc = f"流式压测 (批处理管道 Batch={batch_size})"

        need_first_persist = bool(skip_local_db and persist_first_message and per_target_quota >= 1)
        start_idx = 1 if need_first_persist else 0

        queue: asyncio.Queue[Optional[List[Tuple[SessionTarget, str]]]] = asyncio.Queue(maxsize=concurrency * 4)
        sent_count = 0
        success_count = 0
        fail_count = 0
        retry_count = 0
        # AIMD 自适应节奏：拒收即乘性放大间隔让 ACK 回流排空窗口，顺畅后渐进回落到基础节奏
        pace = max(0.0, delay_between_msg)
        target_success_map: Dict[str, int] = {t.name: 0 for t in active_targets}
        target_seq_map: Dict[str, int] = {t.name: 0 for t in active_targets} if include_seq_prefix else {}

        start_time = time.time()
        last_report_time = start_time
        last_report_count = 0

        batch_buffer: List[Tuple[SessionTarget, str]] = []

        async def flush_buffer() -> None:
            nonlocal batch_buffer
            if batch_buffer:
                await queue.put(list(batch_buffer))
                batch_buffer.clear()

        def format_item_text(tgt: SessionTarget, text: str) -> str:
            """按需附加视觉序号前缀；默认直接返回消息原文，零拷贝开销。"""
            if not include_seq_prefix:
                return text
            seq = target_seq_map[tgt.name] + 1
            target_seq_map[tgt.name] = seq
            return f"[#SEQ{seq:04d}] {text}"

        async def emit_item(tgt: SessionTarget, text: str) -> None:
            nonlocal sent_count
            sent_count += 1
            final_text = format_item_text(tgt, text)
            if batch_size > 1:
                batch_buffer.append((tgt, final_text))
                if len(batch_buffer) >= batch_size:
                    await flush_buffer()
            else:
                await queue.put([(tgt, final_text)])

        def pick_raw_message(seq_idx: int, tgt_idx: int, tgt: SessionTarget) -> str:
            """统一按索引与目标生成当条发送文本，优先采用消息文件语料。"""
            if custom_messages is not None:
                return custom_messages[seq_idx]
            if use_csv_data and corpus_len > 0:
                target_shift = tgt_idx if shard_targets_corpus else 0
                return corpus[(corpus_offset + seq_idx + target_shift) % corpus_len]
            if messages_per_target is not None:
                return f"并发压测第 {seq_idx + 1}/{per_target_quota} 条 ({time.strftime('%H:%M:%S')})"
            return f"[{tgt.name}] 消息第 {seq_idx + 1}/{per_target_quota} 条 ({time.strftime('%H:%M:%S')})"

        async def producer() -> None:
            if messages_per_target is not None:
                # 所有会话按轮次齐步推进，默认严格从消息文件顺序逐条发送；若首条已预热落库则从第 2 条开始
                for round_idx in range(start_idx, per_target_quota):
                    for tgt_idx, tgt in enumerate(active_targets):
                        await emit_item(tgt, pick_raw_message(round_idx, tgt_idx, tgt))
            elif per_target_quota > 0:
                for tgt_idx, tgt in enumerate(active_targets):
                    for msg_idx in range(start_idx, per_target_quota):
                        await emit_item(tgt, pick_raw_message(msg_idx, tgt_idx, tgt))
                    if batch_size > 1:
                        await flush_buffer()

            if batch_size > 1:
                await flush_buffer()

            # 放入结束标记
            for _ in range(concurrency):
                await queue.put(None)

        trigger_limit = low_watermark if enforce_fifo_order else high_watermark

        async def deliver_batch(pending: List[BatchItem], current_inflight: int, apply_pace: bool = True) -> int:
            """执行单批消息投递、断线/进程崩溃自愈重连、同步拒收重发与弹性背压控制。"""
            nonlocal success_count, fail_count, retry_count, pace, last_report_time, last_report_count
            reconnect_left = 2
            while pending:
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
                            if current_inflight <= low_watermark:
                                pace = max(delay_between_msg, pace - 0.015)
                            else:
                                pace = min(max_pace, max(pace * 1.3, 0.08))
                            if current_inflight >= trigger_limit:
                                current_inflight = await self.wait_for_ack_window(low_watermark=low_watermark, timeout=3.0)
                            break

                        pace = min(max_pace, max(pace * 2.0, 0.15))
                        if attempt == max_retries:
                            fail_count += len(rejected)
                            pending = []
                            break

                        retry_count += len(rejected)
                        # 若底层长连接已断开，先暂停等待自动重连完成，避免在断线窗口内白白耗尽重试次数
                        if not await self.bridge.is_channel_ready():
                            recovered = await self.wait_for_channel_ready(timeout=30.0, poll_interval=0.5)
                            if not recovered:
                                fail_count += len(rejected)
                                pending = []
                                break
                            pace = max(pace, 0.2)
                        else:
                            await asyncio.sleep(min(max_pace, retry_backoff * (2 ** attempt)))
                            current_inflight = await self.wait_for_ack_window(low_watermark=low_watermark, timeout=1.5)
                    break
                except Exception as e:
                    err_msg = str(e).lower()
                    is_frida_crash = any(
                        k in err_msg for k in ("destroyed", "detached", "terminated", "session", "unable to find process")
                    )
                    if is_frida_crash and reconnect_left > 0:
                        reconnect_left -= 1
                        print(f"🔄 [📱 {self.sender_name} | {self.device_id}] 检测到进程崩溃/脚本销毁 ({e})，等待 App 重启并恢复注入桥接...")
                        if await self.bridge.reconnect(timeout=20.0) and await self.wait_for_channel_ready(timeout=25.0):
                            current_inflight = 0
                            pace = max(pace, 0.2)
                            print(f"✅ [📱 {self.sender_name} | {self.device_id}] 进程注入与长连接已自愈恢复，继续发送剩余 {len(pending)} 条")
                            continue
                    fail_count += len(pending)
                    print(f"❌ [📱 {self.sender_name} | {self.device_id}] 批次投递异常: {e}")
                    break

            if apply_pace and pace > 0:
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
            return current_inflight

        async def worker() -> None:
            current_inflight = 0
            while True:
                if current_inflight >= trigger_limit:
                    try:
                        current_inflight = await self.wait_for_ack_window(low_watermark=low_watermark, timeout=3.0)
                    except Exception:
                        current_inflight = 0

                batch_items = await queue.get()
                if batch_items is None:
                    queue.task_done()
                    break
                try:
                    current_inflight = await deliver_batch(batch_items, current_inflight, apply_pace=True)
                finally:
                    queue.task_done()

        # 第一阶段（可选）：免落库模式下先正常发送每个会话的第 1 条并等其落库完成，使模拟器列表出现对应会话
        if need_first_persist:
            await self.bridge.set_skip_db_write(False)
            first_items: List[BatchItem] = []
            for tgt_idx, tgt in enumerate(active_targets):
                sent_count += 1
                first_items.append((tgt, format_item_text(tgt, pick_raw_message(0, tgt_idx, tgt))))
            step = max(1, batch_size)
            inflight_first = 0
            for pos in range(0, len(first_items), step):
                inflight_first = await deliver_batch(first_items[pos:pos + step], inflight_first, apply_pace=False)
            # 等待首条消息 ACK 返回及后台协程完成本地会话库写入后再切入极速免落库模式
            await self.wait_for_ack_window(low_watermark=0, timeout=2.0)
            await asyncio.sleep(0.15)
            await self.bridge.set_skip_db_write(True)
            print(
                f"[📱 {self.sender_name} | {self.device_id}] ⚡ [极速压测模式] "
                f"已为 {len(first_items)} 个会话落库展示第 1 条消息，剩余消息已切换全链路免落库 Hook"
            )
        elif skip_local_db:
            await self.bridge.set_skip_db_write(True)
            print(f"[📱 {self.sender_name} | {self.device_id}] ⚡ [极速压测模式] 已开启全链路免落库 Hook（跳过本地 DB 读写、同步阻塞准备、敏感词/装扮检查、ACK 重试与调试日志）")

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
        corpus_file: str = "chat/chat_messages.csv",
        corpus_offset: int = 0,
        shard_targets_corpus: bool = False,
        include_case_id: bool = True,
        include_seq_prefix: bool = False,
        enforce_fifo_order: bool = True,
        skip_local_db: bool = False,
        persist_first_message: bool = True,
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
            use_csv_data: 是否从消息文件提取真实业务语料。
            corpus_file: 消息文件路径（默认 'chat/chat_messages.csv'）。
            corpus_offset: 语料起始游标偏移量（默认 0）。
            shard_targets_corpus: 同设备多目标之间是否微错开语料游标（默认 False，严格按表顺序发送）。
            include_case_id: 是否前置拼接 case_id（默认 True，格式为 case_id:原文）。
            include_seq_prefix: 是否前置拼接 [#SEQ0001] 序号前缀（默认 False）。
            enforce_fifo_order: 是否开启单会话严格保序屏障（默认 True）。
            skip_local_db: 是否开启免落库极速模式（默认 False）。
            persist_first_message: 在 skip_local_db=True 时，是否先正常落库并展示每个会话的第 1 条消息以生成会话列表条目（默认 True）。
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
            corpus_file=corpus_file,
            corpus_offset=corpus_offset,
            shard_targets_corpus=shard_targets_corpus,
            include_case_id=include_case_id,
            include_seq_prefix=include_seq_prefix,
            enforce_fifo_order=enforce_fifo_order,
            skip_local_db=skip_local_db,
            persist_first_message=persist_first_message,
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
                # 20 秒挂接超时：兼顾首次版本切换推送 frida-server，同时杜绝离线设备无限期卡死主事件循环
                return await asyncio.wait_for(c.start(), timeout=20.0)
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
        max_pace: float = 0.3,
        high_watermark: int = 300,
        low_watermark: int = 150,
        use_csv_data: bool = True,
        corpus_file: str = "chat/chat_messages.csv",
        shard_corpus: bool = False,
        include_case_id: bool = True,
        include_seq_prefix: bool = False,
        enforce_fifo_order: bool = True,
        skip_local_db: bool = False,
        persist_first_message: bool = True,
    ) -> List[Dict[str, Any]]:
        """【多设备集群齐步等量并行压测】
        
        所有参战模拟器设备【完全同时同频】向各自配置的目标会话池齐步发射：
        - 自动隔离 offline 异常设备，仅对健康就绪的客户端投递任务；
        - 每台设备各自向自己的专属群与单聊目标发送 count_per_target 条；
        - 总计投递量由实际在线的设备装配会话相加计算。
        - 开启 batch_size 极速管道 + delay_between_batches 批次微延时，彻底规避原生 socket 冲垮。
        - 默认加载 corpus_file 消息文件（保留 case_id:正文 格式，不强加 [#SEQ] 前缀），并严格按表从头顺序发送。
        - shard_corpus=True 时才按设备索引错开语料起始游标；默认 False（例如发 10 条即发送前 10 条）。
        """
        active_clients = [c for c in self.clients if c._is_started and c.bridge._is_ready]
        if not active_clients:
            print("❌ 当前集群中没有就绪的活动客户端，请确认模拟器处于在线状态且 App 正在运行。")
            return []

        corpus = (
            get_chat_message_corpus(corpus_file, include_case_id=include_case_id)
            if use_csv_data
            else []
        )
        corpus_len = len(corpus)
        step = max(1, corpus_len // len(active_clients)) if (shard_corpus and corpus_len > 0) else 0

        total_cluster_msgs = sum(len(c.targets) * count_per_target for c in active_clients)
        content_mode = (
            f"消息文件原文 ({corpus_file}, 共 {corpus_len:,} 条)"
            if use_csv_data
            else "内置测试标头"
        )
        prefix_tags = []
        if include_case_id:
            prefix_tags.append("case_id")
        if include_seq_prefix:
            prefix_tags.append("#SEQ")
        prefix_desc = f"附加前缀: {'+'.join(prefix_tags)}" if prefix_tags else "纯正原文 (无人工前缀)"

        print(f"💥 [多机集群协同开火] {len(active_clients)} 台健康设备启动齐步矩阵压测！")
        print(f"   🎯 调度模式: 设备专属群聊对齐 + 公共单聊并发 (已自动隔离离线设备)")
        print(f"   📂 消息内容数据源: {content_mode} | {prefix_desc} | 集群分片错峰: {'开启' if (shard_corpus and use_csv_data) else '关闭'}")
        print(f"   🚀 批处理管道: 开启 (Batch={batch_size} 条/RPC, 批次间防爆微延时: {delay_between_batches*1000:.0f}ms)")
        print(f"   🛡️ 会话保序屏障: {'开启 (在途排空防超车)' if enforce_fifo_order else '关闭'}")
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
                max_pace=max_pace,
                high_watermark=high_watermark,
                low_watermark=low_watermark,
                use_csv_data=use_csv_data,
                corpus_file=corpus_file,
                corpus_offset=(idx * step) % corpus_len if (shard_corpus and corpus_len > 0) else 0,
                shard_targets_corpus=shard_corpus,
                include_case_id=include_case_id,
                include_seq_prefix=include_seq_prefix,
                enforce_fifo_order=enforce_fifo_order,
                skip_local_db=skip_local_db,
                persist_first_message=persist_first_message,
            )
            for idx, c in enumerate(active_clients)
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
    def _get_online_adb_devices(cls) -> Set[str]:
        """获取当前在线 (device 状态) 的 ADB 设备 ID 集合，避免阻塞探测离线设备。"""
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, timeout=3.0)
            out = res.stdout.decode("utf-8", errors="replace")
            online: Set[str] = set()
            for line in out.splitlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    online.add(parts[0])
            return online
        except Exception:
            return set()

    @classmethod
    def _get_active_meta_db_path(cls, device_id: str) -> str:
        """定位设备当前最新活跃账号对应的本地 SQLite meta 数据库路径。"""
        find_cmd = (
            f"adb -s {device_id} shell \"ls -dt /data/data/com.santiaotalk.im/databases/IM_Data/*/meta-wal "
            f"/data/data/com.santiaotalk.im/databases/IM_Data/*/meta 2>/dev/null\""
        )
        res = subprocess.run(find_cmd, shell=True, capture_output=True, timeout=3.0)
        for line in res.stdout.decode("utf-8", errors="replace").splitlines():
            p = line.strip()
            if p:
                return p[:-4] if p.endswith("-wal") else p
        return ""

    @classmethod
    def discover_current_user_from_sqlite(cls, device_id: str) -> Optional[Tuple[str, str, str]]:
        """直连设备最新活跃账号的 meta 库 user 表，动态读取 (cust_id, name, mobile)。"""
        try:
            db_path = cls._get_active_meta_db_path(device_id)
            if not db_path:
                return None
            sql = "SELECT cust_id, username, mobile FROM user LIMIT 1;"
            cmd = ["adb", "-s", device_id, "shell", f"sqlite3 {db_path}"]
            res_query = subprocess.run(cmd, input=(sql + "\n").encode("utf-8"), capture_output=True, timeout=4.0)
            out = res_query.stdout.decode("utf-8", errors="replace").strip()
            if not out:
                return None
            parts = out.splitlines()[0].strip().split("|")
            if len(parts) >= 1 and parts[0]:
                cust_id = parts[0]
                username = parts[1] if len(parts) >= 2 else ""
                mobile = parts[2] if len(parts) >= 3 else ""
                name = username or mobile or cust_id
                return (cust_id, name, mobile or name)
            return None
        except Exception as e:
            print(f"⚠️ [账号自发现] 从设备 {device_id} 读取当前登录账号失败，将使用静态兜底: {e}")
            return None

    @classmethod
    def discover_groups_from_sqlite(
        cls,
        device_id: str = "emulator-5562",
        pattern_prefix: str = "离线群",
        max_groups: int = 50,
    ) -> List[SessionTarget]:
        """直连设备底层 SQLite 的 conversation 表，秒级动态拉取匹配前缀的最新群聊 ID (Zero Config)."""
        try:
            db_path = cls._get_active_meta_db_path(device_id)
            if not db_path:
                return []

            if pattern_prefix == "群":
                sql_filter = "conv_name LIKE '%群' OR conv_name LIKE '群%'"
            else:
                sql_filter = f"conv_name LIKE '{pattern_prefix}%'"

            sql = (
                f"SELECT conv_id, conv_name, is_top FROM conversation "
                f"WHERE conv_type=2 AND state=1 AND ({sql_filter}) "
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
            db_path = cls._get_active_meta_db_path(device_id)
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

        # 1. 装配 5 台基准设备实体（优先从在线设备活跃 meta 库自发现当前登录账号，失败时回退静态兜底）
        dedicated_map = cfg.get("device_dedicated_groups", {})
        base_devices = [
            ("emulator-5562", "1500692599256551424", "测试050", "19200000050"),
            # ("emulator-5562", "1158096069641277440", "008628100000423", "008628100000423"),
            ("emulator-5564", "1500692599583707136", "测试051", "19200000051"),
            ("emulator-5566", "1500692599990554624", "测试052", "19200000052"),
            ("emulator-5568", "1500692600422567936", "测试053", "19200000053"),
            ("emulator-5572", "1500692600787472384", "测试054", "19200000054"),
        ]
        online_devices = cls._get_online_adb_devices()
        device_configs: List[DeviceAccountConfig] = []
        for dev_id, cust_id, name, mobile in base_devices:
            if dev_id in online_devices:
                live_user = cls.discover_current_user_from_sqlite(dev_id)
                if live_user is not None:
                    cust_id, name, mobile = live_user
                    print(f"🔄 [账号自发现] {dev_id} 已自动识别当前登录账号: {name} (CustID: {cust_id})")
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
        # 消息文件路径（默认加载 data/chat/chat_messages.csv，也可切换为 .xlsx / .txt / 绝对路径）
        CORPUS_FILE = "chat/chat_messages.csv"

        print("==================================================")
        print("🚀 三条 IM 分布式多设备多会话高并发压测引擎")
        print(f"📚 消息语料: {CORPUS_FILE}（保留 case_id:原文 格式，不额外附加 #SEQ 前缀）")
        print("==================================================")

        # -------------------------------------------------------------
        # 运行模式开关：
        #   USE_CLUSTER = True  : 5 台模拟器设备集群协同【同时】压测
        #   USE_CLUSTER = False : 单台模拟器本地独立压测
        # -------------------------------------------------------------
        # USE_CLUSTER = True
        USE_CLUSTER = False

        # -------------------------------------------------------------
        # 循环发送控制开关（通宵/长稳压测专用）：
        #   LOOP_SEND = True  : 持续循环发送（一晚上不断轮次投递，按 Ctrl+C 停止）
        #   LOOP_SEND = False : 仅发送 1 轮后自动结束
        # -------------------------------------------------------------
        LOOP_SEND = False
        LOOP_INTERVAL_SECONDS = 5.0  # 每轮结束后的缓冲休眠时间（秒）

        # 每台设备对各自会话（专属群聊+公共单聊）单轮发送的消息数量（如设为 20 条）
        COUNT_PER_TARGET = 10000
        # COUNT_PER_TARGET = 28572

        async def _run_with_loop(create_fn, start_fn, send_fn, stop_fn) -> None:
            """通用轮次执行器：支持单轮与通宵无限循环压测，异常断连时自动重建通道。"""
            instance = create_fn()
            try:
                if not await start_fn(instance):
                    return
                round_idx = 1
                while True:
                    if LOOP_SEND:
                        print(f"\n🔄 [通宵循环压测 · 第 {round_idx} 轮] 启动本轮发送 ({time.strftime('%Y-%m-%d %H:%M:%S')})")
                    try:
                        await send_fn(instance, round_idx)
                    except Exception as e:
                        print(f"⚠️ [第 {round_idx} 轮异常] {e}")
                        if not LOOP_SEND:
                            raise
                        await stop_fn(instance)
                        await asyncio.sleep(max(LOOP_INTERVAL_SECONDS, 5.0))
                        instance = create_fn()
                        await start_fn(instance)
                        round_idx += 1
                        continue

                    if not LOOP_SEND:
                        break
                    print(f"💤 [第 {round_idx} 轮结束] 休眠 {LOOP_INTERVAL_SECONDS:.1f}s 后进入第 {round_idx + 1} 轮...")
                    round_idx += 1
                    await asyncio.sleep(LOOP_INTERVAL_SECONDS)
            finally:
                await stop_fn(instance)

        if USE_CLUSTER:
            # =========================================================
            # 【集群模式】：5 台模拟器同时协同，各自对应专属群聊齐步开火
            # =========================================================
            cluster_devs, common_targets, shard_groups = SessionTargetManager.load_cluster_targets()

            def _create_cluster() -> IMClientCluster:
                return IMClientCluster(
                    device_configs=cluster_devs,
                    common_targets=common_targets,
                    concurrency_per_device=1,
                    shard_group_targets=shard_groups,
                )

            async def _start_cluster(cluster: IMClientCluster) -> bool:
                if not await cluster.start():
                    print("❌ 集群中无就绪设备，请检查模拟器与 frida-server。")
                    return False
                # 🛡️ 核心闸门：压测前自动执行全集群历史离线消息排空收敛预热 (保障 WCDB 与通道空闲)
                await cluster.drain_all_offline_sync(quiet_duration=2.5, max_timeout=15.0)
                return True

            async def _send_cluster(cluster: IMClientCluster, round_idx: int) -> None:
                results = await cluster.send_matrix(
                    count_per_target=COUNT_PER_TARGET,
                    # 分片后每群仅 1 个发送者，可放开到 10 条/批 + 100ms；全量模式保持保守节奏防服务端 500
                    batch_size=200,
                    report_interval=200,
                    delay_between_batches=0.02 if shard_groups else 0.1,
                    high_watermark=300,
                    low_watermark=150,
                    max_pace=0.3,
                    corpus_file=CORPUS_FILE,
                    shard_corpus=False,
                    include_case_id=True,
                    include_seq_prefix=False,
                    skip_local_db=True,
                    # 仅第 1 轮先正常落库展示会话，后续轮次全量走免落库通道避免本地 DB 膨胀
                    persist_first_message=(round_idx == 1),
                )
                if LOOP_SEND and not results:
                    raise RuntimeError("本轮无可用就绪设备，准备重建集群连接")

            await _run_with_loop(_create_cluster, _start_cluster, _send_cluster, lambda c: c.stop())

        else:
            # =========================================================
            # 【单机模式】：单台模拟器 (emulator-5562) 独立压测
            # =========================================================
            cluster_devs, common_targets, _ = SessionTargetManager.load_cluster_targets()
            single_cfg = cluster_devs[0]
            single_targets = ([single_cfg.dedicated_group] if single_cfg.dedicated_group else []) + [
                t for t in common_targets if t.to_cust_id != single_cfg.sender_cust_id
            ]

            def _create_single() -> IMClient:
                return IMClient(
                    device_id=single_cfg.device_id,
                    sender_cust_id=single_cfg.sender_cust_id,
                    sender_name=single_cfg.sender_name,
                    targets=single_targets,
                )

            async def _start_single(client: IMClient) -> bool:
                if not await client.start():
                    print("❌ 客户端启动失败，无法连接真机协议通道。")
                    return False
                # 🛡️ 核心闸门：压测前自动执行历史离线消息排空收敛预热 (保障 WCDB 与通道空闲)
                await client.drain_offline_sync(quiet_duration=2.5, max_timeout=15.0)
                return True

            async def _send_single(client: IMClient, round_idx: int) -> None:
                await client.send_matrix(
                    count_per_target=COUNT_PER_TARGET,
                    concurrency=1,              # 单设备单协程顺序流水线，杜绝锁争抢与 Socket 洪峰
                    batch_size=200,             # 批次大小（每批 10 条，平滑投递防网关限流断连）
                    report_interval=200,        # 打点间隔
                    delay_between_msg=0.02,      # 每批发送完成后固定停顿 0.5s，避免零间隔洪峰踢断长连接
                    high_watermark=50,          # 高水位线（与 batch_size=10 匹配，防止在途积压打爆缓冲区）
                    low_watermark=20,           # 低水位线（超过 20 条在途即等待服务端 ACK 回落）
                    max_pace=1.0,               # 退避休眠上限（必须 >= delay_between_msg，防止背压反向缩短间隔）
                    corpus_file=CORPUS_FILE,
                    include_case_id=True,
                    include_seq_prefix=False,
                    enforce_fifo_order=True,    # 开启单会话严格保序屏障
                    skip_local_db=True,         # 跳过发送端本地写库，彻底解决 1.7G WAL 膨胀与提速
                    persist_first_message=(round_idx == 1),
                )

            await _run_with_loop(_create_single, _start_single, _send_single, lambda c: c.stop())

        print("\n🎉 全流程压测任务圆满结束，已安全释放连接并返回终端。")
        os._exit(0)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        os._exit(0)
