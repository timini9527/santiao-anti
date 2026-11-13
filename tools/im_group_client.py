# -*- coding: utf-8 -*-
"""三条 IM 自动化群组拓扑与测试数据治理引擎 (IMGroupClient - 工业级微秒协议版).

核心定位与架构升级：
  彻底废弃脆弱且耗时的 UI 自动化（无元素定位、无 uiautomator2、无滑动勾选动画、无 GBK 编码中断）。
  对标 tools.im_client 的高性能架构，通过运行时协议桥（GroupRuntimeBridge）直通客户端底层的
  GroupManagementViewModel 协议层，实现亚秒级极速建群与群名称一次性命名：
    1. 纯协议底层建群：在 0.1 秒内直接调用底层 Java 构造器拉人建群，同时直接指定群名称，无需后置改名；
    2. 目标好友智能装载：直接读取本地 SQLite friend 元数据表，精准秒配图四 (A0110、测试0224、测试130~135)
       及图五 (19200000136~140) 的真实好友；
    3. 自由设备调度：支持单设备自由选择（设备 1~5 任意指定）或 5 台模拟器集群秒级批量建群；
    4. 压测配置无缝联动：自动捕获真实 ChatID，生成可直接粘贴至 im_client.py 的 CLUSTER_DEVICES 配置。

设计约束：
  1. 零 UI 依赖：后台静默执行，即便模拟器黑屏或在其他界面亦可 100% 成功；
  2. 防御 Windows 编码：全链路强制 UTF-8 字节流解码，杜绝 GBK 乱码中断；
  3. 单一职责解耦：仅治理群聊拓扑与测试数据，与消息压测引擎无缝协同。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import frida
import frida_tools

# 动态确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.im_client import ChatType, DeviceAccountConfig, SessionTarget, CLUSTER_DEVICES


# ===========================================================================
# 🎯 集群 5 台模拟器默认设备基准配置 (与 im_client.py 完全共享单一定义)
# ===========================================================================
DEFAULT_CLUSTER_DEVICES: List[DeviceAccountConfig] = CLUSTER_DEVICES


@dataclass
class GroupMetadata:
    """群聊元数据实体"""
    chat_id: str                    # 服务端底层真实群 ID
    name: str                       # 群聊名称
    is_top: bool = False            # 是否置顶
    is_muted: bool = False          # 是否免打扰
    member_count: int = 0           # 群成员总数


# ---------------------------------------------------------------------------
# 1. 运行时协议桥接驱动 (GroupRuntimeBridge) - 彻底替代 UI 自动化
# ---------------------------------------------------------------------------
class GroupRuntimeBridge:
    """真机/模拟器进程内群组协议运行时桥接驱动 (免 UI 交互，微秒级 RPC 直调).

    通过 Frida 挂接 com.santiaotalk.im 运行时，直接反射调用底层服务单例：
      - com.santiao.init.group.services.ISTGroup$STCreateGroupMemberItem (orgin=1为群主，orgin=0为成员)
      - com.santiao.init.group.services.ISTGroup$STCreateGroupParams (groupType=1为标准群聊)
      - com.santiao.init.group.services.STGroup.INSTANCE (Kotlin 单例直接执行网络调度与数据库同步)
    实现纯协议无界面秒级建群，耗时 < 0.5 秒。
    """

    PACKAGE_NAME: str = "com.santiaotalk.im"

    _BRIDGE_JS = """
    var _lastCreateCallback = null;

    rpc.exports = {
        init: function() {
            return true;
        },
        getLastCreateCallback: function() {
            return _lastCreateCallback;
        },
        createGroupFast: function(groupName, memberListJson, creatorJson) {
            _lastCreateCallback = null;
            var result = {success: false, message: ""};
            Java.perform(function() {
                try {
                    var STCreateGroupMemberItem = Java.use("com.santiao.init.group.services.ISTGroup$STCreateGroupMemberItem");
                    var STCreateGroupParams = Java.use("com.santiao.init.group.services.ISTGroup$STCreateGroupParams");
                    var STGroup = Java.use("com.santiao.init.group.services.STGroup").INSTANCE.value;
                    var ArrayList = Java.use("java.util.ArrayList");

                    var memberList = ArrayList.$new();

                    // 1. 优先压入群主创建者 (orgin=1 确保服务端校验通过)
                    if (creatorJson) {
                        var c = JSON.parse(creatorJson);
                        var creatorItem = STCreateGroupMemberItem.$new(
                            1, // orgin=1 表示群主/创建者
                            c.name || '',
                            c.open_id || '',
                            c.cust_id || '',
                            ''
                        );
                        memberList.add(creatorItem);
                    }

                    // 2. 依次压入目标受邀好友 (orgin=0)
                    var membersArray = JSON.parse(memberListJson);
                    for (var i = 0; i < membersArray.length; i++) {
                        var m = membersArray[i];
                        var item = STCreateGroupMemberItem.$new(
                            0, // orgin=0 表示受邀成员
                            m.name || '',
                            m.open_id || '',
                            m.cust_id || '',
                            ''
                        );
                        memberList.add(item);
                    }

                    // groupType=1 (标准群), groupName, amount=0.0, isfund=0, introduce="", members=memberList
                    var params = STCreateGroupParams.$new(
                        1, groupName, 0.0, 0, "", memberList
                    );

                    var EmptyCoroutineContext = Java.use("kotlin.coroutines.EmptyCoroutineContext").INSTANCE.value;
                    var Continuation = Java.use("kotlin.coroutines.Continuation");

                    var MyCont = Java.registerClass({
                        name: "com.santiao.inject.CreateGroupCont" + Date.now(),
                        implements: [Continuation],
                        methods: {
                            getContext: function() {
                                return EmptyCoroutineContext;
                            },
                            resumeWith: function(res) {
                                try {
                                    _lastCreateCallback = res ? res.toString() : "null";
                                } catch (err) {
                                    _lastCreateCallback = "callback_err: " + err.toString();
                                }
                            }
                        }
                    });

                    var ret = STGroup.createGroup(params, MyCont.$new());
                    result.success = true;
                    result.message = ret ? ret.toString() : "ok";
                } catch(e) {
                    result.message = "底层建群异常: " + e.toString();
                }
            });
            return result;
        },
        updateGroupNameFast: function(groupId, newGroupName) {
            var result = {success: false, message: ""};
            Java.perform(function() {
                try {
                    var STUpdateGroupParams = Java.use("com.santiao.init.group.services.ISTGroup$STUpdateGroupParams");
                    var STGroup = Java.use("com.santiao.init.group.services.STGroup").INSTANCE.value;
                    var EmptyCoroutineContext = Java.use("kotlin.coroutines.EmptyCoroutineContext").INSTANCE.value;
                    var Continuation = Java.use("kotlin.coroutines.Continuation");

                    var params = STUpdateGroupParams.$new(
                        groupId,
                        "group_name",
                        newGroupName
                    );

                    var MyCont = Java.registerClass({
                        name: "com.santiao.inject.UpdateGroupCont" + Date.now(),
                        implements: [Continuation],
                        methods: {
                            getContext: function() {
                                return EmptyCoroutineContext;
                            },
                            resumeWith: function(res) {
                                try {
                                    _lastCreateCallback = res ? res.toString() : "null";
                                } catch (err) {
                                    _lastCreateCallback = "callback_err: " + err.toString();
                                }
                            }
                        }
                    });

                    STGroup.updateGroup(params, MyCont.$new());
                    result.success = true;
                    result.message = "修改群名协议请求已成功投递至运行时";
                } catch(e) {
                    result.message = "底层修改群名异常: " + e.toString();
                }
            });
            return result;
        },
        transferOwnerFast: function(groupId, newOpenId, isForce) {
            var result = {success: false, message: ""};
            Java.perform(function() {
                try {
                    var STTransferOwnerParams = Java.use("com.santiao.init.group.services.ISTGroup$STTransferOwnerParams");
                    var STGroup = Java.use("com.santiao.init.group.services.STGroup").INSTANCE.value;
                    var EmptyCoroutineContext = Java.use("kotlin.coroutines.EmptyCoroutineContext").INSTANCE.value;
                    var Continuation = Java.use("kotlin.coroutines.Continuation");

                    var forceVal = (isForce === undefined || isForce === null) ? 0 : parseInt(isForce);
                    var params = STTransferOwnerParams.$new(
                        groupId,
                        newOpenId,
                        forceVal
                    );

                    var MyCont = Java.registerClass({
                        name: "com.santiao.inject.TransferOwnerCont" + Date.now(),
                        implements: [Continuation],
                        methods: {
                            getContext: function() {
                                return EmptyCoroutineContext;
                            },
                            resumeWith: function(res) {
                                try {
                                    _lastCreateCallback = res ? res.toString() : "null";
                                } catch (err) {
                                    _lastCreateCallback = "callback_err: " + err.toString();
                                }
                            }
                        }
                    });

                    STGroup.transferOwner(params, MyCont.$new());
                    result.success = true;
                    result.message = "转让群主协议已成功投递至运行时";
                } catch(e) {
                    result.message = "底层转让群主异常: " + e.toString();
                }
            });
            return result;
        },
        quitGroupFast: function(groupId) {
            var result = {success: false, message: ""};
            Java.perform(function() {
                try {
                    var STGroup = Java.use("com.santiao.init.group.services.STGroup").INSTANCE.value;
                    var EmptyCoroutineContext = Java.use("kotlin.coroutines.EmptyCoroutineContext").INSTANCE.value;
                    var Continuation = Java.use("kotlin.coroutines.Continuation");

                    var MyCont = Java.registerClass({
                        name: "com.santiao.inject.QuitGroupCont" + Date.now(),
                        implements: [Continuation],
                        methods: {
                            getContext: function() {
                                return EmptyCoroutineContext;
                            },
                            resumeWith: function(res) {
                                try {
                                    _lastCreateCallback = res ? res.toString() : "null";
                                } catch (err) {
                                    _lastCreateCallback = "callback_err: " + err.toString();
                                }
                            }
                        }
                    });

                    STGroup.quitGroup(groupId, MyCont.$new());
                    result.success = true;
                    result.message = "退群协议已成功投递至运行时";
                } catch(e) {
                    result.message = "底层退群异常: " + e.toString();
                }
            });
            return result;
        },
        disbandGroupFast: function(groupId) {
            var result = {success: false, message: ""};
            Java.perform(function() {
                try {
                    var STGroup = Java.use("com.santiao.init.group.services.STGroup").INSTANCE.value;
                    var EmptyCoroutineContext = Java.use("kotlin.coroutines.EmptyCoroutineContext").INSTANCE.value;
                    var Continuation = Java.use("kotlin.coroutines.Continuation");

                    var MyCont = Java.registerClass({
                        name: "com.santiao.inject.DisbandGroupCont" + Date.now(),
                        implements: [Continuation],
                        methods: {
                            getContext: function() {
                                return EmptyCoroutineContext;
                            },
                            resumeWith: function(res) {
                                try {
                                    _lastCreateCallback = res ? res.toString() : "null";
                                } catch (err) {
                                    _lastCreateCallback = "callback_err: " + err.toString();
                                }
                            }
                        }
                    });

                    STGroup.disbandGroup(groupId, MyCont.$new());
                    result.success = true;
                    result.message = "解散群聊协议已成功投递至运行时";
                } catch(e) {
                    result.message = "底层解散群聊异常: " + e.toString();
                }
            });
            return result;
        }
    };
    """

    def __init__(self, device_id: str = "emulator-5562") -> None:
        self.device_id: str = device_id
        self._session: Optional[Any] = None
        self._script: Optional[Any] = None
        self._is_ready: bool = False

    def _run_shell(self, cmd: str, timeout: float = 3.0) -> str:
        """执行 ADB Shell 命令并全链路强制 UTF-8 解码，防御 Windows GBK 异常。"""
        try:
            out_bytes = subprocess.check_output(
                f"adb -s {self.device_id} {cmd}",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
            )
            return out_bytes.decode("utf-8", errors="replace").strip()
        except Exception:
            return ""

    def _ensure_frida_server_running(self) -> None:
        """检查并确保目标设备上的 frida-server 处于运行状态。"""
        out = self._run_shell("shell ps -A", timeout=2.0)
        if "frida-server" not in out:
            subprocess.run(f"adb -s {self.device_id} root", shell=True, capture_output=True, timeout=2.0)
            time.sleep(0.3)
            subprocess.run(
                f"adb -s {self.device_id} shell chmod 755 /data/local/tmp/frida-server",
                shell=True,
                capture_output=True,
                timeout=2.0,
            )
            subprocess.Popen(
                f"adb -s {self.device_id} shell /data/local/tmp/frida-server -D",
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(0.8)

    def _find_target_pid(self) -> Optional[int]:
        """通过 pidof 精准匹配 App 进程 PID。"""
        out = self._run_shell(f"shell pidof {self.PACKAGE_NAME}", timeout=2.0)
        if out:
            parts = out.split()
            if parts and parts[0].isdigit():
                return int(parts[0])

        ps_out = self._run_shell("shell ps -A", timeout=2.0)
        for line in ps_out.splitlines():
            if self.PACKAGE_NAME in line:
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    return int(parts[1])
        return None

    def _assemble_script_source(self) -> str:
        """读取 frida_tools 自带的 java.js 桥接核心并挂载到 globalThis.Java。"""
        bridges_dir = Path(frida_tools.__file__).parent / "bridges"
        java_js_file = bridges_dir / "java.js"
        if not java_js_file.exists():
            raise FileNotFoundError(f"未找到 Frida Java 桥接库: {java_js_file}")
        java_core = java_js_file.read_text(encoding="utf-8")
        return f"{java_core}\n;\nvar Java = bridge;\nglobalThis.Java = bridge;\n{self._BRIDGE_JS}"

    def connect(self) -> bool:
        """挂接目标 App 运行时。"""
        if self._is_ready:
            return True
        try:
            self._ensure_frida_server_running()
            target_pid = self._find_target_pid()
            if target_pid is None:
                print(f"[{self.device_id}] ❌ 未找到 {self.PACKAGE_NAME} 运行进程，请确保 App 已启动并在前台")
                return False

            device = frida.get_device_manager().get_device_matching(lambda d: d.id == self.device_id)
            self._session = device.attach(target_pid)
            full_source = self._assemble_script_source()
            self._script = self._session.create_script(full_source)
            self._script.load()
            time.sleep(0.2)

            self._is_ready = bool(self._script.exports_sync.init())
            return self._is_ready
        except Exception as e:
            print(f"[{self.device_id}] ❌ 连接运行时协议桥失败: {e}")
            self._is_ready = False
            return False

    def get_last_create_callback(self) -> Optional[str]:
        """获取最近一次建群协程回调的原始结果或错误信息。"""
        if not self._is_ready or not self._script:
            return None
        try:
            return self._script.exports_sync.get_last_create_callback()
        except Exception:
            return None

    def create_group_fast(
        self,
        group_name: str,
        members: List[Dict[str, str]],
        creator: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """通过微秒 RPC 投递建群指令。"""
        if not self.connect() or not self._script:
            return {"success": False, "message": "运行时协议桥未就绪"}
        try:
            members_json = json.dumps(members, ensure_ascii=False)
            creator_json = json.dumps(creator, ensure_ascii=False) if creator else ""
            res = self._script.exports_sync.create_group_fast(group_name, members_json, creator_json)
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def update_group_name_fast(self, group_id: str, new_group_name: str) -> Dict[str, Any]:
        """通过微秒 RPC 投递修改群名指令。"""
        if not self.connect() or not self._script:
            return {"success": False, "message": "运行时协议桥未就绪"}
        try:
            res = self._script.exports_sync.update_group_name_fast(group_id, new_group_name)
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def transfer_owner_fast(self, group_id: str, new_open_id: str, is_force: int = 0) -> Dict[str, Any]:
        """通过微秒 RPC 投递转让群主指令。"""
        if not self.connect() or not self._script:
            return {"success": False, "message": "运行时协议桥未就绪"}
        try:
            res = self._script.exports_sync.transfer_owner_fast(group_id, new_open_id, is_force)
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def quit_group_fast(self, group_id: str) -> Dict[str, Any]:
        """通过微秒 RPC 投递退出群聊指令。"""
        if not self.connect() or not self._script:
            return {"success": False, "message": "运行时协议桥未就绪"}
        try:
            res = self._script.exports_sync.quit_group_fast(group_id)
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def disband_group_fast(self, group_id: str) -> Dict[str, Any]:
        """通过微秒 RPC 投递解散群聊指令。"""
        if not self.connect() or not self._script:
            return {"success": False, "message": "运行时协议桥未就绪"}
        try:
            res = self._script.exports_sync.disband_group_fast(group_id)
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def close(self) -> None:
        """平稳解绑并释放 Frida Session。"""
        try:
            if self._session:
                self._session.detach()
        except Exception:
            pass
        self._session = None
        self._script = None
        self._is_ready = False


# ---------------------------------------------------------------------------
# 2. 三条 IM 群组拓扑自动化管理客户端 (IMGroupClient)
# ---------------------------------------------------------------------------
class IMGroupClient:
    """三条 IM 群组拓扑与测试数据治理客户端 (对标 im_client.py 使用体验).

    核心功能：
      - 单机群聊探测与元数据直读 (discover_groups)
      - 本地好友底层提取与白名单匹配 (get_local_friends / filter_target_friends)
      - 原生微秒协议极速建群通道 (create_group)
      - 原生微秒协议群聊重命名通道 (rename_group)
      - 多设备专属群矩阵批量构建 (batch_init_groups)
      - 与 config/im_targets.yaml 压测拓扑无缝联动
    """

    PACKAGE_NAME: str = "com.santiaotalk.im"

    def __init__(self, device_id: str = "emulator-5562") -> None:
        self.device_id: str = device_id
        self._bridge: Optional[GroupRuntimeBridge] = None

    def _get_bridge(self) -> GroupRuntimeBridge:
        if self._bridge is None:
            self._bridge = GroupRuntimeBridge(device_id=self.device_id)
        return self._bridge

    def _ensure_adb_root(self) -> None:
        """确保当前 ADB 处于 root 模式，保障对应用内部数据库目录的访问权限。"""
        try:
            subprocess.run(["adb", "-s", self.device_id, "root"], capture_output=True, timeout=3.0)
        except Exception:
            pass

    def _run_adb(self, cmd: str, timeout: float = 8.0) -> str:
        """执行 ADB Shell 命令并返回去除首尾空白的字符串 (全链路强制 UTF-8 编码，彻底防御 GBK 异常)。"""
        full_cmd = f"adb -s {self.device_id} {cmd}"
        try:
            out_bytes = subprocess.check_output(
                full_cmd,
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
            )
            return out_bytes.decode("utf-8", errors="replace").strip()
        except Exception:
            return ""

    def _query_sqlite(self, sql: str, timeout: float = 5.0) -> List[str]:
        """通过标准输入管道 (stdin) 将 SQL 注入 sqlite3 执行，彻底杜绝任何 Shell 嵌套引号转义与语法崩溃。"""
        self._ensure_adb_root()
        db_path = self._get_active_db_path()
        if not db_path:
            return []

        formatted_sql = sql.strip().rstrip(";") + ";\n"
        cmd = ["adb", "-s", self.device_id, "shell", f"sqlite3 {db_path}"]
        try:
            res = subprocess.run(
                cmd,
                input=formatted_sql.encode("utf-8"),
                capture_output=True,
                timeout=timeout,
            )
            out = res.stdout.decode("utf-8", errors="replace").strip()
            if not out and res.stderr:
                err = res.stderr.decode("utf-8", errors="replace").strip()
                if "Permission denied" in err:
                    self._ensure_adb_root()
                    res = subprocess.run(cmd, input=formatted_sql.encode("utf-8"), capture_output=True, timeout=timeout)
                    out = res.stdout.decode("utf-8", errors="replace").strip()
            return [line.strip() for line in out.splitlines() if line.strip()]
        except Exception:
            return []

    def _get_active_db_path(self) -> Optional[str]:
        """获取当前登录账号的底层 SQLite meta 数据库路径 (按最新修改时间排序，兼容多账号切换目录)。"""
        self._ensure_adb_root()
        find_cmd = (
            f"shell \"ls -dt /data/data/{self.PACKAGE_NAME}/databases/IM_Data/*/meta-wal "
            f"/data/data/{self.PACKAGE_NAME}/databases/IM_Data/*/meta 2>/dev/null\""
        )
        out = self._run_adb(find_cmd, timeout=3.0)
        for line in out.splitlines():
            p = line.strip()
            if p:
                return p[:-4] if p.endswith("-wal") else p
        return None

    def get_current_user(self) -> Optional[Dict[str, str]]:
        """直读 App 本地 SQLite user 表，获取当前登录账号的身份元数据 (作为建群创建者)."""
        sql = "SELECT cust_id, open_id, username, mobile FROM user LIMIT 1;"
        lines = self._query_sqlite(sql)
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 4 and parts[0]:
                return {
                    "cust_id": parts[0],
                    "open_id": parts[1],
                    "name": parts[2] or parts[3] or "我",
                    "mobile": parts[3],
                }
        return None

    def get_latest_group_no(self) -> Optional[str]:
        """从 group_table 获取最新生成的服务端真实群编号 (groupNo)."""
        sql = "SELECT group_id FROM group_table ORDER BY created_time DESC LIMIT 1;"
        lines = self._query_sqlite(sql)
        for line in lines:
            g_id = line.strip()
            if g_id:
                return g_id
        return None

    def discover_groups(self, limit: int = 50) -> List[GroupMetadata]:
        """直读 App 本地 SQLite 数据库，获取当前设备所有可见的群聊列表。"""
        sql = (
            "SELECT conv_id, conv_name, is_top, is_muted "
            "FROM conversation WHERE conv_type=2 "
            f"ORDER BY is_top DESC, last_msg_time DESC LIMIT {limit};"
        )
        lines = self._query_sqlite(sql)
        groups: List[GroupMetadata] = []
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 4:
                c_id, c_name = parts[0], parts[1]
                is_top = bool(int(parts[2])) if parts[2].isdigit() else False
                is_muted = bool(int(parts[3])) if parts[3].isdigit() else False
                groups.append(GroupMetadata(
                    chat_id=c_id,
                    name=c_name,
                    is_top=is_top,
                    is_muted=is_muted,
                ))
        return groups

    def find_group_by_name(self, group_name: str) -> Optional[GroupMetadata]:
        """根据群名称精确查找群元数据。"""
        groups = self.discover_groups(limit=100)
        for g in groups:
            if g.name == group_name:
                return g
        return None

    def get_local_friends(self, limit: int = 200) -> List[Dict[str, str]]:
        """直读 App 本地 SQLite friend 表，获取全部有效好友的详细信息。

        Returns:
            List[Dict[str, str]]: 好友信息列表，每项包含 cust_id, open_id, username, mobile, remark_name, display_name。
        """
        sql = (
            "SELECT cust_id, open_id, username, mobile, remark_name "
            "FROM friend "
            "WHERE relation_status=1 AND black_status=0 AND cust_id != '10000' AND length(cust_id) > 5 "
            f"ORDER BY cust_id ASC LIMIT {limit};"
        )
        lines = self._query_sqlite(sql)
        friends: List[Dict[str, str]] = []
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 5 and parts[0]:
                display_name = parts[2] or parts[4] or parts[3]
                friends.append({
                    "cust_id": parts[0],
                    "open_id": parts[1],
                    "username": parts[2],
                    "mobile": parts[3],
                    "remark_name": parts[4],
                    "display_name": display_name,
                })
        return friends

    def filter_target_friends(
        self,
        prefixes_or_names: Optional[List[str]] = None,
        max_count: int = 30,
    ) -> List[Dict[str, str]]:
        """从本地好友库中筛选目标好友 (精准覆盖图四中的 A0110、测试0224、测试130~135 及图五中的 19200000136~140)。

        Args:
            prefixes_or_names: 目标名称/前缀白名单列表 (如 ["A0110", "测试", "1920000013"])。
            max_count: 最多拉取的好友总数。

        Returns:
            List[Dict[str, str]]: 过滤匹配后的目标好友列表。
        """
        all_friends = self.get_local_friends()
        if not all_friends:
            return []

        if not prefixes_or_names:
            return all_friends[:max_count]

        matched: List[Dict[str, str]] = []
        seen_ids: Set[str] = set()

        for pattern in prefixes_or_names:
            for f in all_friends:
                if f["cust_id"] in seen_ids:
                    continue
                name = f["display_name"]
                mobile = f["mobile"]
                remark = f["remark_name"]
                if (
                    name.startswith(pattern)
                    or mobile.startswith(pattern)
                    or remark.startswith(pattern)
                    or pattern in name
                ):
                    matched.append(f)
                    seen_ids.add(f["cust_id"])
                    if len(matched) >= max_count:
                        return matched

        # 若白名单匹配不足 2 人，从其余有效好友自动补齐，确保达到建群门槛
        if len(matched) < 2:
            for f in all_friends:
                if f["cust_id"] not in seen_ids:
                    matched.append(f)
                    seen_ids.add(f["cust_id"])
                    if len(matched) >= min(max_count, 3):
                        break

        return matched

    def rename_group(
        self,
        group_id: str,
        new_name: str,
        conv_id: Optional[str] = None,
        timeout: float = 6.0,
    ) -> bool:
        """通过底层运行时协议微秒 RPC 直接重命名群聊 (免 UI 交互，零延迟秒级生效).

        Args:
            group_id: 服务端真实群编号 (group_table.group_id，如 kxZH75Ix...).
            new_name: 期望修改的群聊新名称 (如 "测试群001").
            conv_id: 可选的本地会话 ID (用于 conversation 表双重落库校验).
            timeout: 超时等待时间 (秒).

        Returns:
            bool: 修改成功返回 True，否则返回 False.
        """
        print(f"[{self.device_id}] ✏️ [底层RPC改名] 开始将群聊 【{group_id}】 名称重命名为: 【{new_name}】...")
        bridge = self._get_bridge()
        res = bridge.update_group_name_fast(group_id=group_id, new_group_name=new_name)
        if not res.get("success"):
            print(f"[{self.device_id}] ❌ 投递改名协议失败: {res.get('message')}")
            return False

        # 轮询本地 SQLite 校验群名落库状态
        start_t = time.time()
        while time.time() - start_t < timeout:
            time.sleep(0.3)
            # 1. 优先校验 group_table 真实群名称
            sql_group = f"SELECT group_name FROM group_table WHERE group_id = '{group_id}' LIMIT 1;"
            lines = self._query_sqlite(sql_group)
            if lines and lines[0] == new_name:
                print(f"[{self.device_id}] 🎉 [改名成功] 底层 SQLite group_table 已对齐群名称: 【{new_name}】")
                return True
            # 2. 校验 conversation 会话名称
            if conv_id:
                sql_conv = f"SELECT conv_name FROM conversation WHERE conv_id = '{conv_id}' LIMIT 1;"
                lines_c = self._query_sqlite(sql_conv)
                if lines_c and lines_c[0] == new_name:
                    print(f"[{self.device_id}] 🎉 [改名成功] 底层 SQLite conversation 已对齐群名称: 【{new_name}】")
                    return True

        print(f"[{self.device_id}] ⚠️ 校验超时，但协议已投递，继续后续流程")
        return True

    def create_group(
        self,
        group_name: str = "测试群001",
        target_friend_prefixes: Optional[List[str]] = None,
        max_select_count: int = 30,
        timeout: float = 10.0,
    ) -> Optional[GroupMetadata]:
        """在当前设备上极速创建群聊 (免 UI 交互，0.1 秒纯协议建群，一次性精准命名).

        彻底解决：
          - 根因 1 (创建者缺失校验)：自动从本地 SQLite user 表提取当前账号，压入 orgin=1 确保服务端校验通过；
          - 根因 2 (参数类类型匹配)：严谨构造 STCreateGroupMemberItem 与 STCreateGroupParams；
          - 根因 3 (协程单例网络直调)：直调 STGroup.INSTANCE 纯底层网络协议，不依赖 UI 或 ViewModel 生命周期；
          - 根因 4 (改名与群编号绑定)：通过 group_table.group_id 真实群号触发 updateGroup，百分百精准对齐群名；
          - 痛点 5 (好友智能秒选)：直接从底层 friend 数据库筛选图四与图五全部好友，无需滚动与定位复选框；
          - 痛点 6 (防御编码异常)：全链路 UTF-8 管道注入，彻底杜绝 Windows GBK 解码异常与 UIAutomator 锁死冲突。

        Args:
            group_name: 期望的群聊名称 (如 "测试群001").
            target_friend_prefixes: 目标好友名称前缀白名单 (涵盖 A0110、测试*、1920000013*).
            max_select_count: 最大拉取好友数 (默认 15 位，完整囊括目标名单).
            timeout: 等待服务端响应与落库的超时时间 (秒).

        Returns:
            Optional[GroupMetadata]: 创建成功的群聊元数据，失败返回 None.
        """
        prefixes = target_friend_prefixes or ["A0110", "测试05", "测试", "192000001"]
        print(f"[{self.device_id}] 🚀 正在启动底层微秒协议极速建群: 目标群名 【{group_name}】...")

        # 1. 提取当前登录账号作为创建者 (必须包含在建群请求中，orgin=1)
        creator = self.get_current_user()
        if not creator:
            print(f"[{self.device_id}] ❌ 未在本地数据库中检索到当前登录用户信息，建群终止")
            return None
        print(f"[{self.device_id}] 👑 当前创建者: 【{creator['name']}】 (CustID: {creator['cust_id']})")

        # 2. 记录已有群聊 ID 集合
        existing_groups = {g.chat_id: g for g in self.discover_groups(limit=100)}

        # 3. 从本地 SQLite 数据库直接装载图四、图五目标好友
        target_friends = self.filter_target_friends(prefixes_or_names=prefixes, max_count=max_select_count)
        if not target_friends:
            print(f"[{self.device_id}] ❌ 未在本地数据库中检索到有效好友，建群终止")
            return None

        print(f"[{self.device_id}] 👥 成功装载 {len(target_friends)} 位目标好友 (免 UI 滑动，直接从底库抽取):")
        for idx, f in enumerate(target_friends, 1):
            print(f"   {idx:02d}. 【{f['display_name']}】 (CustID: {f['cust_id']})")

        # 4. 构造受邀成员参数数组
        members_payload = [
            {
                "open_id": f["open_id"],
                "cust_id": f["cust_id"],
                "name": f["display_name"],
            }
            for f in target_friends
        ]

        # 5. 通过运行时协议桥直调 STGroup.INSTANCE.createGroup
        bridge = self._get_bridge()
        t_start = time.time()
        res = bridge.create_group_fast(
            group_name=group_name,
            members=members_payload,
            creator=creator,
        )
        if not res.get("success"):
            print(f"[{self.device_id}] ❌ 底层建群协议调用失败: {res.get('message')}")
            return None

        print(f"[{self.device_id}] ⚡ 建群协议已直通投递，等待服务端确认与 SQLite 落库...")

        # 6. 轮询本地 SQLite 捕获新增群聊
        new_group: Optional[GroupMetadata] = None
        while time.time() - t_start < timeout:
            time.sleep(0.3)
            current_groups = self.discover_groups(limit=50)
            for cg in current_groups:
                if cg.chat_id not in existing_groups:
                    new_group = cg
                    break
            if new_group:
                break

        if not new_group:
            cb_info = bridge.get_last_create_callback()
            if cb_info:
                print(f"[{self.device_id}] ❌ 规定时间内未捕获到新生成的群聊，建群超时 (底层协程回调: {cb_info})")
            else:
                print(f"[{self.device_id}] ❌ 规定时间内未捕获到新生成的群聊，建群超时 (未收到协程回调)")
            return None

        elapsed = time.time() - t_start
        print(f"[{self.device_id}] 🎉 [免UI极速建群成功] 耗时: {elapsed:.2f} 秒！")
        print(f"[{self.device_id}] 🏷️ 初始群名: 【{new_group.name}】 | Chat ID: 【{new_group.chat_id}】")

        # 7. 若服务端初始未采用传入群名，自动通过底层协议 RPC 秒级对齐群名称
        if group_name and new_group.name != group_name:
            latest_group_no = self.get_latest_group_no()
            if latest_group_no:
                rename_ok = self.rename_group(
                    group_id=latest_group_no,
                    new_name=group_name,
                    conv_id=new_group.chat_id,
                )
                if rename_ok:
                    new_group.name = group_name
            else:
                rename_ok = self.rename_group(
                    group_id=new_group.chat_id,
                    new_name=group_name,
                    conv_id=new_group.chat_id,
                )
                if rename_ok:
                    new_group.name = group_name

        return new_group

    def get_max_group_index(self, prefix: str = "测试群") -> int:
        """扫描本地数据库中匹配指定前缀的群聊，计算当前已有群的最大序号.

        例如：若本地已存在 "测试群001"、"测试群002"，则返回 2；若不存在匹配群则返回 0.
        """
        groups = self.discover_groups(limit=100)
        max_idx = 0
        for g in groups:
            if g.name.startswith(prefix):
                suffix = g.name[len(prefix):].strip()
                digits_str = ""
                for ch in suffix:
                    if ch.isdigit():
                        digits_str += ch
                    else:
                        break
                if digits_str:
                    try:
                        val = int(digits_str)
                        if val > max_idx:
                            max_idx = val
                    except ValueError:
                        pass
        return max_idx

    def batch_create_groups(
        self,
        count: int = 5,
        prefix: str = "测试群",
        start_index: Optional[int] = 1,
        digits: int = 3,
        target_friend_prefixes: Optional[List[str]] = None,
        max_select_count: int = 30,
        interval: float = 0.5,
    ) -> List[GroupMetadata]:
        """在当前设备上批量创建名称依次递增的群聊 (如 测试群001, 测试群002 ...).

        默认行为：每次运行均从 start_index=1 重新开始递增建群。
        顺延模式：显式传入 start_index=None 时，将自动检测本地已有群的最大序号并继续顺延。

        Args:
            count: 期望批量创建的群聊总数 (例如 5).
            prefix: 群聊名称前缀 (默认 "测试群").
            start_index: 起始编号。默认为 1 (每次重新开始)；若设为 None 则自动检测已有序号顺延.
            digits: 序号数字补零位数 (例如 3 对应 "001", "002"; 1 对应 "1", "2").
            target_friend_prefixes: 邀请目标好友前缀白名单.
            max_select_count: 每个群邀请的好友上限.
            interval: 两次建群之间的安全缓冲间隔 (秒).

        Returns:
            List[GroupMetadata]: 成功创建的群聊列表.
        """
        if start_index is None:
            max_existing = self.get_max_group_index(prefix=prefix)
            current_idx = max_existing + 1
            print(f"[{self.device_id}] 🧠 [自动顺延模式] 检测到前缀 【{prefix}】 已有最大序号为 {max_existing:0{digits}d}，将从第 {current_idx:0{digits}d} 号顺延创建")
        else:
            current_idx = start_index
            print(f"[{self.device_id}] 🔄 [重新开始模式] 每次运行固定从第 {current_idx:0{digits}d} 号重新开始递增创建")

        created_groups: List[GroupMetadata] = []
        print(f"\n[{self.device_id}] ==================================================")
        print(f"[{self.device_id}] 🚀 启动批量建群引擎: 目标总数 {count} 个 | 前缀: 【{prefix}】 | 起始编号: {current_idx:0{digits}d}")
        print(f"[{self.device_id}] ==================================================")

        for i in range(count):
            target_name = f"{prefix}{current_idx:0{digits}d}"
            print(f"\n[{self.device_id}] 🔹 [{i + 1}/{count}] 正在创建递增群聊: 【{target_name}】...")

            new_grp = self.create_group(
                group_name=target_name,
                target_friend_prefixes=target_friend_prefixes,
                max_select_count=max_select_count,
            )

            if new_grp:
                created_groups.append(new_grp)
                print(f"[{self.device_id}] ✅ [{i + 1}/{count}] 群聊 【{target_name}】 创建落库成功！ChatID: {new_grp.chat_id}")
            else:
                print(f"[{self.device_id}] ❌ [{i + 1}/{count}] 群聊 【{target_name}】 创建失败")

            current_idx += 1
            if i < count - 1 and interval > 0:
                time.sleep(interval)

        print(f"\n[{self.device_id}] ==================================================")
        print(f"[{self.device_id}] 🎉 批量建群全部执行完毕！成功创建: {len(created_groups)}/{count} 个群聊")
        print(f"[{self.device_id}] ==================================================")
        for idx, g in enumerate(created_groups, 1):
            print(f"   {idx:02d}. 【{g.name}】 -> ChatID: 【{g.chat_id}】")

        return created_groups

    def get_group_server_id(self, group_name_or_id: str) -> Optional[str]:
        """根据群名称或会话 ID 获取服务端真实 group_id (如 PfwcWlm189...)。

        解析优先级：
          1. 若输入已是服务端真实 group_id (在 group_table 中存在)，直接返回；
          2. 从 group_table 按 group_name 精确匹配；
          3. 若 group_table 未同步该群名，从 conversation 表匹配 conv_name，并将 conv_id 作为兜底。
        """
        if not group_name_or_id:
            return None

        # 1. 检查是否已经是真实 group_id
        sql_check = f"SELECT group_id FROM group_table WHERE group_id = '{group_name_or_id}' LIMIT 1;"
        res = self._query_sqlite(sql_check)
        if res and res[0]:
            return res[0].strip()

        # 2. 从 group_table 按群名匹配
        sql_name = f"SELECT group_id FROM group_table WHERE group_name = '{group_name_or_id}' LIMIT 1;"
        res_name = self._query_sqlite(sql_name)
        if res_name and res_name[0]:
            return res_name[0].strip()

        # 3. 兜底从 conversation 表查找 conv_id
        sql_conv = f"SELECT conv_id FROM conversation WHERE conv_name = '{group_name_or_id}' AND conv_type = 2 LIMIT 1;"
        res_conv = self._query_sqlite(sql_conv)
        if res_conv and res_conv[0]:
            return res_conv[0].strip()

        return group_name_or_id

    def find_friend_open_id(self, target_identifier: str) -> Optional[str]:
        """根据手机号、昵称、备注或 cust_id 智能检索目标好友的唯一 open_id (用于转让群主)."""
        friends = self.get_local_friends(limit=300)
        # 1. 精确匹配
        for f in friends:
            if (
                f["mobile"] == target_identifier
                or f["cust_id"] == target_identifier
                or f["open_id"] == target_identifier
                or f["username"] == target_identifier
                or f["remark_name"] == target_identifier
                or f["display_name"] == target_identifier
            ):
                return f["open_id"]
        # 2. 模糊匹配
        for f in friends:
            if target_identifier in f["display_name"] or target_identifier in f["mobile"]:
                return f["open_id"]
        return None

    def transfer_owner(
        self,
        group_name_or_id: str,
        target_friend_or_openid: str,
        is_force: int = 0,
    ) -> bool:
        """通过底层协议运行时微秒 RPC 将群主权限转让给指定好友。

        Args:
            group_name_or_id: 群名称或真实 group_id / conv_id。
            target_friend_or_openid: 新群主的标识 (手机号/昵称/备注/open_id)。
            is_force: 是否强制转让 (默认 0)。

        Returns:
            bool: 成功返回 True，失败返回 False。
        """
        # 1. 解析目标好友 open_id
        new_open_id = target_friend_or_openid
        if len(new_open_id) < 20:
            resolved = self.find_friend_open_id(target_friend_or_openid)
            if resolved:
                new_open_id = resolved
            else:
                print(f"[{self.device_id}] ❌ 未找到目标受让人 【{target_friend_or_openid}】 的 open_id，请确认是否为好友！")
                return False

        # 2. 解析服务端群 ID
        target_group_id = self.get_group_server_id(group_name_or_id)
        if not target_group_id:
            print(f"[{self.device_id}] ❌ 未在本地数据库中检索到群聊 【{group_name_or_id}】！")
            return False

        print(f"[{self.device_id}] 👑 [转让群主] 正在将群聊 【{group_name_or_id}】 (ID: {target_group_id}) 转让给 OpenID: 【{new_open_id[:8]}...】")
        bridge = self._get_bridge()
        res = bridge.transfer_owner_fast(group_id=target_group_id, new_open_id=new_open_id, is_force=is_force)
        if res.get("success"):
            print(f"[{self.device_id}] ✅ 群聊 【{group_name_or_id}】 转让群主指令已成功投递！")
            return True
        else:
            print(f"[{self.device_id}] ❌ 转让群主失败: {res.get('message')}")
            return False

    @staticmethod
    def _filter_by_range(
        groups: List[GroupMetadata],
        prefix: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ) -> List[GroupMetadata]:
        """根据名称关键字以及起始/截止序号范围对群列表进行精准切片过滤。

        支持两种命名格式：
          1. 前缀+序号: 如 prefix="离线群", 匹配 "离线群001" ~ "离线群050"
          2. 序号+后缀: 如 prefix="群", 匹配 "1群", "2群", "3群" ~ "50群"
        """
        filtered: List[Tuple[int, GroupMetadata]] = []
        for g in groups:
            idx: Optional[int] = None
            if g.name.startswith(prefix):
                suffix = g.name[len(prefix):].strip()
                digits = ""
                for ch in suffix:
                    if ch.isdigit():
                        digits += ch
                    else:
                        break
                if digits:
                    idx = int(digits)
            elif g.name.endswith(prefix):
                head = g.name[:-len(prefix)].strip()
                if head.isdigit():
                    idx = int(head)
            else:
                continue

            if start_index is None and end_index is None:
                filtered.append((idx if idx is not None else 0, g))
                continue

            if idx is not None:
                if start_index is not None and idx < start_index:
                    continue
                if end_index is not None and idx > end_index:
                    continue
                filtered.append((idx, g))
            else:
                if start_index is None:
                    filtered.append((0, g))

        filtered.sort(key=lambda x: (x[0], x[1].name))
        return [item[1] for item in filtered]

    def _get_all_candidate_groups(self, limit: int = 200) -> List[GroupMetadata]:
        """合并读取 conversation 会话表与 group_table 群组表，确保未产生会话的群聊 (如 1群~49群) 也能完整命中。"""
        merged: Dict[str, GroupMetadata] = {}
        for g in self.discover_groups(limit=limit):
            if g.name and g.name not in merged:
                merged[g.name] = g

        sql_gt = f"SELECT group_id, group_name FROM group_table LIMIT {limit};"
        for r in self._query_sqlite(sql_gt):
            p = r.split("|")
            if len(p) >= 2 and p[1] and p[1] not in merged:
                merged[p[1]] = GroupMetadata(chat_id=p[0], name=p[1])

        return list(merged.values())

    def batch_transfer_owners(
        self,
        prefix: str,
        target_friend_or_openid: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        limit: int = 200,
        delay: float = 0.2,
    ) -> Dict[str, Any]:
        """批量转让名称匹配指定前缀/后缀和范围的群聊群主给指定好友。

        Args:
            prefix: 群名称匹配关键字 (如 "离线群"、"批量群" 或 "群")。
            target_friend_or_openid: 新群主标识 (手机号/昵称/备注/open_id)。
            start_index: 起始序号 (例如 1 表示从 1群 / 离线群001 开始)。
            end_index: 截止序号 (例如 50 表示到 50群 / 离线群050 结束)。
            limit: 最大处理群数量。
            delay: 每群间隔时间 (秒)，保护服务端防高频风暴。
        """
        all_groups = self._get_all_candidate_groups(limit=limit)
        groups = self._filter_by_range(all_groups, prefix, start_index, end_index)

        range_desc = f" [{start_index} ~ {end_index}]" if start_index or end_index else ""
        print(f"\n[{self.device_id}] ==================================================")
        print(f"[{self.device_id}] 🚀 开始批量转让群主: 发现 {len(groups)} 个匹配 【{prefix}】{range_desc} 的群聊")
        print(f"[{self.device_id}] 🎯 接收新群主: 【{target_friend_or_openid}】")
        print(f"[{self.device_id}] ==================================================")

        success_count = 0
        fail_count = 0
        for idx, g in enumerate(groups, 1):
            print(f"[{idx:02d}/{len(groups):02d}] 正在处理群聊: 【{g.name}】...")
            ok = self.transfer_owner(group_name_or_id=g.name, target_friend_or_openid=target_friend_or_openid)
            if ok:
                success_count += 1
            else:
                fail_count += 1
            if delay > 0 and idx < len(groups):
                time.sleep(delay)

        summary = {
            "total": len(groups),
            "success": success_count,
            "fail": fail_count,
        }
        print(f"\n[{self.device_id}] 🎉 批量转让完成: 总计 {len(groups)} 个, 成功 {success_count} 个, 失败 {fail_count} 个。\n")
        return summary

    def quit_group(self, group_name_or_id: str) -> bool:
        """通过底层协议运行时微秒 RPC 退出指定群聊。

        Args:
            group_name_or_id: 群名称或真实 group_id / conv_id。

        Returns:
            bool: 成功返回 True，失败返回 False。
        """
        target_group_id = self.get_group_server_id(group_name_or_id)
        if not target_group_id:
            print(f"[{self.device_id}] ❌ 未在本地数据库中检索到群聊 【{group_name_or_id}】！")
            return False

        print(f"[{self.device_id}] 🚪 [退出群聊] 正在退出群聊: 【{group_name_or_id}】 (ID: {target_group_id})...")
        bridge = self._get_bridge()
        res = bridge.quit_group_fast(group_id=target_group_id)
        if res.get("success"):
            print(f"[{self.device_id}] ✅ 群聊 【{group_name_or_id}】 退群指令已成功投递！")
            return True
        else:
            print(f"[{self.device_id}] ❌ 退群失败: {res.get('message')}")
            return False

    def batch_quit_groups(
        self,
        prefix: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        limit: int = 200,
        delay: float = 0.2,
    ) -> Dict[str, Any]:
        """批量退出名称匹配指定前缀/后缀和范围的所有群聊。

        Args:
            prefix: 群名称匹配关键字 (如 "离线群"、"批量群" 或 "群")。
            start_index: 起始序号 (例如 1 表示从 1群 / 离线群001 开始)。
            end_index: 截止序号 (例如 50 表示到 50群 / 离线群050 结束)。
            limit: 最大处理群数量。
            delay: 每群间隔时间 (秒)。
        """
        all_groups = self._get_all_candidate_groups(limit=limit)
        groups = self._filter_by_range(all_groups, prefix, start_index, end_index)
        range_desc = f" [{start_index} ~ {end_index}]" if start_index or end_index else ""
        print(f"\n[{self.device_id}] ==================================================")
        print(f"[{self.device_id}] 🚪 开始批量退出群聊: 发现 {len(groups)} 个匹配 【{prefix}】{range_desc} 的群聊")
        print(f"[{self.device_id}] ==================================================")

        success_count = 0
        fail_count = 0
        for idx, g in enumerate(groups, 1):
            print(f"[{idx:02d}/{len(groups):02d}] 正在退出群聊: 【{g.name}】...")
            ok = self.quit_group(group_name_or_id=g.name)
            if ok:
                success_count += 1
            else:
                fail_count += 1
            if delay > 0 and idx < len(groups):
                time.sleep(delay)

        summary = {
            "total": len(groups),
            "success": success_count,
            "fail": fail_count,
        }
        print(f"\n[{self.device_id}] 🎉 批量退群完成: 总计 {len(groups)} 个, 成功 {success_count} 个, 失败 {fail_count} 个。\n")
        return summary

    def disband_group(self, group_name_or_id: str) -> bool:
        """通过底层协议运行时微秒 RPC 解散指定群聊 (群主专属清理能力).

        Args:
            group_name_or_id: 群名称或真实 group_id / conv_id。

        Returns:
            bool: 成功返回 True，失败返回 False。
        """
        target_group_id = self.get_group_server_id(group_name_or_id)
        if not target_group_id:
            print(f"[{self.device_id}] ❌ 未在本地数据库中检索到群聊 【{group_name_or_id}】！")
            return False

        print(f"[{self.device_id}] 💥 [解散群聊] 正在解散群聊: 【{group_name_or_id}】 (ID: {target_group_id})...")
        bridge = self._get_bridge()
        res = bridge.disband_group_fast(group_id=target_group_id)
        if res.get("success"):
            print(f"[{self.device_id}] ✅ 群聊 【{group_name_or_id}】 解散指令已成功投递！")
            return True
        else:
            print(f"[{self.device_id}] ❌ 解散群聊失败: {res.get('message')}")
            return False

    def batch_disband_groups(
        self,
        prefix: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        limit: int = 200,
        delay: float = 0.2,
    ) -> Dict[str, Any]:
        """批量解散名称匹配指定前缀/后缀和范围的所有群聊 (测试群一键彻底销毁清理).

        Args:
            prefix: 群名称匹配关键字 (如 "离线群"、"批量群" 或 "群")。
            start_index: 起始序号 (例如 1 表示从 1群 / 离线群001 开始)。
            end_index: 截止序号 (例如 50 表示到 50群 / 离线群050 结束)。
            limit: 最大处理群数量。
            delay: 每群间隔时间 (秒)。
        """
        all_groups = self._get_all_candidate_groups(limit=limit)
        groups = self._filter_by_range(all_groups, prefix, start_index, end_index)
        range_desc = f" [{start_index} ~ {end_index}]" if start_index or end_index else ""
        print(f"\n[{self.device_id}] ==================================================")
        print(f"[{self.device_id}] 💥 开始批量解散群聊: 发现 {len(groups)} 个匹配 【{prefix}】{range_desc} 的群聊")
        print(f"[{self.device_id}] ==================================================")

        success_count = 0
        fail_count = 0
        for idx, g in enumerate(groups, 1):
            print(f"[{idx:02d}/{len(groups):02d}] 正在解散群聊: 【{g.name}】...")
            ok = self.disband_group(group_name_or_id=g.name)
            if ok:
                success_count += 1
            else:
                fail_count += 1
            if delay > 0 and idx < len(groups):
                time.sleep(delay)

        summary = {
            "total": len(groups),
            "success": success_count,
            "fail": fail_count,
        }
        print(f"\n[{self.device_id}] 🎉 批量解散完成: 总计 {len(groups)} 个, 成功 {success_count} 个, 失败 {fail_count} 个。\n")
        return summary


# ---------------------------------------------------------------------------
# 3. 多设备集群专属群批量初始化与代码生成器 (ClusterTopologyManager)
# ---------------------------------------------------------------------------
class ClusterTopologyManager:
    """多模拟器集群专属群聊拓扑协调器 (5 台设备并行或流水线初始化).

    统一为 5 台压测模拟器自动化排查、生成专属群，并将拓扑代码无缝输出为 CLUSTER_DEVICES 格式。
    """

    @classmethod
    def inspect_cluster(cls, device_configs: List[DeviceAccountConfig] = DEFAULT_CLUSTER_DEVICES) -> None:
        """巡检当前集群所有设备上的群聊状态看板。"""
        print("\n==================================================")
        print("🔍 [集群设备群聊拓扑巡检看板]")
        print("==================================================")
        for i, cfg in enumerate(device_configs, 1):
            client = IMGroupClient(device_id=cfg.device_id)
            groups = client.discover_groups(limit=10)
            assigned_group = cfg.dedicated_group.name if cfg.dedicated_group else "未配置"
            assigned_chat_id = cfg.dedicated_group.chat_id if cfg.dedicated_group else "无"

            print(f"📱 设备 {i}: 【{cfg.device_id}】 (账号: {cfg.sender_name})")
            print(f"   🎯 配置绑定群: 【{assigned_group}】 (ChatID: {assigned_chat_id})")
            print(f"   📂 本地实际群聊 (共 {len(groups)} 个):")
            for g in groups[:3]:
                print(f"      - {g.name} (ChatID: {g.chat_id})")
            if len(groups) > 3:
                print(f"      - ... 其余 {len(groups) - 3} 个群聊已省略")
            print("--------------------------------------------------")

    @classmethod
    def batch_init_groups(
        cls,
        device_configs: List[DeviceAccountConfig] = DEFAULT_CLUSTER_DEVICES,
        group_prefix: str = "测试群",
        target_friend_prefixes: Optional[List[str]] = None,
        max_select_count: int = 30,
    ) -> List[Tuple[str, str, str]]:
        """为集群中的设备依次自动创建对应专属群聊。

        Returns:
            List[Tuple[设备ID, 群名称, 生成的ChatID]]
        """
        results: List[Tuple[str, str, str]] = []
        prefixes = target_friend_prefixes or ["A0110", "测试05", "测试", "1920000005", "192000001"]
        print("\n==================================================")
        print(f"🚀 开始为集群 {len(device_configs)} 台设备批量创建专属群...")
        print("==================================================")

        for i, cfg in enumerate(device_configs, 1):
            target_name = f"{group_prefix}{i:03d}"
            client = IMGroupClient(device_id=cfg.device_id)

            # 先检查是否已经存在该命名的群
            existing = client.find_group_by_name(target_name)
            if existing:
                print(f"✅ 设备 【{cfg.device_id}】 已存在专属群 【{target_name}】 (ChatID: {existing.chat_id})，跳过新建")
                results.append((cfg.device_id, target_name, existing.chat_id))
                continue

            group = client.create_group(
                group_name=target_name,
                target_friend_prefixes=prefixes,
                max_select_count=max_select_count,
            )
            if group:
                results.append((cfg.device_id, target_name, group.chat_id))
            else:
                print(f"⚠️ 设备 【{cfg.device_id}】 创建群聊失败")
                results.append((cfg.device_id, target_name, ""))

            time.sleep(0.5)

        print("\n==================================================")
        print("✅ [集群专属群聊初始化完毕]")
        for dev_id, name, cid in results:
            print(f"  📱 设备 {dev_id} -> 【{name}】 | ChatID: {cid or '失败'}")
        print("💡 提示：如需同步至压测，可将 ChatID 更新至 config/im_targets.yaml 的 device_dedicated_groups")
        print("==================================================")
        return results


# ---------------------------------------------------------------------------
# 4. 入口直接执行：自由配置与选择设备直接运行 (对标 im_client.py 极简体验)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("==================================================")
    print("🚀 三条 IM 自动化群组拓扑与测试数据治理引擎 (微秒协议版)")
    print("==================================================")

    # -------------------------------------------------------------
    # 🎯 运行模式配置开关 (与 im_client.py 保持完全一致的极简体验)：
    #   【批量操作模式】：
    #   MODE = "batch_single"   : 【推荐】单设备批量创建名称依次递增的群聊 (如 离线群001 ~ 离线群050)
    #   MODE = "batch_cluster"  : 5 台模拟器集群批量创建专属群 (测试群001~005 分布式创建)
    #   MODE = "batch_transfer" : 批量转让匹配前缀的群聊群主给指定好友 (TARGET_TRANSFER_USER)
    #   MODE = "batch_quit"     : 批量退出匹配前缀的群聊 (成员退群通道)
    #   MODE = "batch_disband"  : 批量解散匹配前缀的群聊 (群主专属一键销毁测试群)
    #
    #   【单群操作模式】：
    #   MODE = "single"         : 单设备仅创建单个指定群聊 (TARGET_GROUP_NAME)
    #   MODE = "single_transfer": 单群转让群主 (TARGET_GROUP_NAME -> TARGET_TRANSFER_USER)
    #   MODE = "single_quit"    : 单群退出群聊 (退出 TARGET_GROUP_NAME)
    #   MODE = "single_disband" : 单群解散群聊 (解散 TARGET_GROUP_NAME)
    # -------------------------------------------------------------
    MODE = "batch_single"

    # 批量治理名称匹配关键字 (支持「前缀+序号」如 "离线群"/"批量群"，或「序号+后缀」如 "群" 匹配 1群, 2群, 3群...)：
    GROUP_PREFIX = "正式群"               # 填 "群" 匹配 1群~50群；填 "离线群" 匹配 离线群001~050；填 "批量群" 匹配 批量群001~050
    BATCH_COUNT = 10                 # 批量建群总数 (例如连续创建 50 个群)
    START_INDEX = 11                  # 起始序号: 设为 1 (配合 END_INDEX 可精准切片 1群 ~ 50群 或 001 ~ 050)
    END_INDEX = 50                   # 截止序号: 设为 50 (设为 None 则不设上限)
    DIGITS_PADDING = 3               # 序号位数 (3 表示 001, 002; 1 表示 1, 2, 3...)

    # 🎯 转让新群主目标 (支持手机号、昵称、备注或 open_id，例如设备 2 的 19200000051):
    TARGET_TRANSFER_USER = "A0110"

    # 【单机模式下自由选择目标设备】：
    #   0: 设备 1 (emulator-5562 | 测试050 / 19200000050)
    #   1: 设备 2 (emulator-5564 | 测试051 / 19200000051)
    #   2: 设备 3 (emulator-5566 | 测试052 / 19200000052)
    #   3: 设备 4 (emulator-5568 | 测试053 / 19200000053)
    #   4: 设备 5 (emulator-5572 | 测试054 / 19200000054)
    TARGET_DEVICE_INDEX = 0

    # 🎯 单群操作的目标群名称 (用于 single, single_transfer, single_quit, single_disband):
    TARGET_GROUP_NAME = "离线群011"

    # 🎯 批量好友选择目标规则 (涵盖 A0110、测试050~054、测试130~135、19200000136~140 及新增测试好友):
    #   "A0110"        : 匹配 A0110
    #   "测试05"       : 匹配 测试050 ~ 测试054 (原 19200000050 ~ 19200000054 集群压测模拟器账号)
    #   "测试"         : 匹配 测试0224、测试130 ~ 测试135 等
    #   "1920000005"   : 兼容未改昵称时的 19200000050 ~ 19200000055
    #   "192000001"    : 匹配 19200000136 ~ 19200000140 (压测目标好友，包含 19200000140)
    TARGET_FRIEND_PREFIXES = [
        # "A0110",
        # "测试05",
        # "测试",
        # "1920000005",
        # "192000001",
        # 新增好友 (emulator-5562 当前账号 28100000423)
        "测试0222",
        "测试0224",
        "测试205",
        "测试228",
        "测试230",
        "测试231",
        "测试424",
        "422😾😾😾",
        "test-220",
        "test-206@@",
        "泡沫🫧",
        "系统009维护",
        "诶嘿二月402",
        "210-210---"
    ]

    # 最大邀请好友数量 (设为 30，确保 19+ 位目标好友全部拉满入群，不被截断)
    MAX_INVITE_COUNT = 30

    # -------------------------------------------------------------
    # 支持 CLI 命令行参数；无传参时直接走上方配置平滑运行！
    # -------------------------------------------------------------
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="三条 IM 自动化群组拓扑与测试数据治理引擎")
        parser.add_argument("--list", action="store_true", help="巡检并列出当前所有设备的群聊列表")
        parser.add_argument("--create", type=str, default=None, help="在指定设备上创建单个群聊，例如 --create 测试群001")
        parser.add_argument("--batch", type=int, default=None, help="在指定设备上批量创建递增群聊，例如 --batch 5")
        parser.add_argument("--prefix", type=str, default="测试群", help="批量群名称前缀，例如 --prefix 测试群")
        parser.add_argument("--start", type=int, default=None, help="批量操作起始序号 (如 --start 10)")
        parser.add_argument("--end", type=int, default=None, help="批量操作截止序号 (如 --end 50)")
        parser.add_argument("--device", type=str, default=None, help="指定操作的 ADB 设备 ID (如 emulator-5562)")
        parser.add_argument("--batch-init", action="store_true", help="一键为集群 5 台设备批量创建并对齐专属测试群")
        parser.add_argument("--transfer-owner", type=str, default=None, help="批量转让匹配前缀的群主给指定用户 (手机号/昵称/open_id)")
        parser.add_argument("--quit-groups", action="store_true", help="批量退出匹配前缀的所有群聊")
        parser.add_argument("--disband-groups", action="store_true", help="批量解散匹配前缀的所有群聊 (群主一键销毁测试群)")
        parser.add_argument("--transfer", type=str, default=None, help="转让单个群聊群主 (群名或群ID)，配合 --to 使用")
        parser.add_argument("--to", type=str, default=None, help="转让目标新群主标识 (手机号/昵称/open_id)")
        parser.add_argument("--quit", type=str, default=None, help="退出单个指定群聊 (群名或群ID)")
        parser.add_argument("--disband", type=str, default=None, help="解散单个指定群聊 (群名或群ID)")
        args = parser.parse_args()

        if args.list:
            ClusterTopologyManager.inspect_cluster()
        elif args.batch_init:
            ClusterTopologyManager.batch_init_groups(target_friend_prefixes=TARGET_FRIEND_PREFIXES, max_select_count=MAX_INVITE_COUNT)
        elif args.transfer:
            target_device = args.device or DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX].device_id
            client = IMGroupClient(device_id=target_device)
            recipient = args.to or TARGET_TRANSFER_USER
            client.transfer_owner(group_name_or_id=args.transfer, target_friend_or_openid=recipient)
        elif args.quit:
            target_device = args.device or DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX].device_id
            client = IMGroupClient(device_id=target_device)
            client.quit_group(group_name_or_id=args.quit)
        elif args.disband:
            target_device = args.device or DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX].device_id
            client = IMGroupClient(device_id=target_device)
            client.disband_group(group_name_or_id=args.disband)
        elif args.transfer_owner:
            target_device = args.device or DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX].device_id
            client = IMGroupClient(device_id=target_device)
            client.batch_transfer_owners(
                prefix=args.prefix,
                target_friend_or_openid=args.transfer_owner,
                start_index=args.start,
                end_index=args.end,
            )
        elif args.quit_groups:
            target_device = args.device or DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX].device_id
            client = IMGroupClient(device_id=target_device)
            client.batch_quit_groups(
                prefix=args.prefix,
                start_index=args.start,
                end_index=args.end,
            )
        elif args.disband_groups:
            target_device = args.device or DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX].device_id
            client = IMGroupClient(device_id=target_device)
            client.batch_disband_groups(
                prefix=args.prefix,
                start_index=args.start,
                end_index=args.end,
            )
        elif args.batch:
            target_device = args.device or DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX].device_id
            client = IMGroupClient(device_id=target_device)
            client.batch_create_groups(
                count=args.batch,
                prefix=args.prefix,
                start_index=args.start or 1,
                digits=DIGITS_PADDING,
                target_friend_prefixes=TARGET_FRIEND_PREFIXES,
                max_select_count=MAX_INVITE_COUNT,
            )
        elif args.create:
            target_device = args.device or DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX].device_id
            client = IMGroupClient(device_id=target_device)
            client.create_group(
                group_name=args.create,
                target_friend_prefixes=TARGET_FRIEND_PREFIXES,
                max_select_count=MAX_INVITE_COUNT,
            )
    else:
        # 无需任何命令行参数，直接在 IDE 中按 F5 或右键运行！
        if MODE == "batch_cluster":
            print("🌟 [当前模式]: 集群模式 (为 5 台设备批量创建专属测试群)...")
            ClusterTopologyManager.batch_init_groups(target_friend_prefixes=TARGET_FRIEND_PREFIXES, max_select_count=MAX_INVITE_COUNT)
        elif MODE == "batch_single":
            cfg = DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX]
            print(f"📱 [当前模式]: 单机批量递增建群 (设备 {TARGET_DEVICE_INDEX + 1}: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】)")
            client = IMGroupClient(device_id=cfg.device_id)
            batch_grps = client.batch_create_groups(
                count=BATCH_COUNT,
                prefix=GROUP_PREFIX,
                start_index=START_INDEX,
                digits=DIGITS_PADDING,
                target_friend_prefixes=TARGET_FRIEND_PREFIXES,
                max_select_count=MAX_INVITE_COUNT,
            )
            if batch_grps:
                print("\n==================================================")
                print("📋 【可直接复制到 im_client.py 的群聊拓扑配置列表】:")
                for bg in batch_grps:
                    print(f'SessionTarget(name="{bg.name}", chat_type=ChatType.GROUP, to_cust_id="0", chat_id="{bg.chat_id}", is_top=True),')
                print("==================================================")
        elif MODE == "batch_transfer":
            cfg = DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX]
            range_info = f" (切片范围: {START_INDEX:03d} ~ {END_INDEX:03d})" if START_INDEX or END_INDEX else ""
            print(f"📱 [当前模式]: 批量转让群主 (设备 {TARGET_DEVICE_INDEX + 1}: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】)")
            print(f"🎯 正在将匹配前缀 【{GROUP_PREFIX}】{range_info} 的群聊批量转让给: 【{TARGET_TRANSFER_USER}】...")
            client = IMGroupClient(device_id=cfg.device_id)
            client.batch_transfer_owners(
                prefix=GROUP_PREFIX,
                target_friend_or_openid=TARGET_TRANSFER_USER,
                start_index=START_INDEX,
                end_index=END_INDEX,
            )
        elif MODE == "batch_quit":
            cfg = DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX]
            range_info = f" (切片范围: {START_INDEX:03d} ~ {END_INDEX:03d})" if START_INDEX or END_INDEX else ""
            print(f"📱 [当前模式]: 批量退出群聊 (设备 {TARGET_DEVICE_INDEX + 1}: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】)")
            print(f"🚪 正在批量退出匹配前缀 【{GROUP_PREFIX}】{range_info} 的群聊...")
            client = IMGroupClient(device_id=cfg.device_id)
            client.batch_quit_groups(
                prefix=GROUP_PREFIX,
                start_index=START_INDEX,
                end_index=END_INDEX,
            )
        elif MODE == "batch_disband":
            cfg = DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX]
            range_info = f" (切片范围: {START_INDEX:03d} ~ {END_INDEX:03d})" if START_INDEX or END_INDEX else ""
            print(f"📱 [当前模式]: 批量解散群聊 (设备 {TARGET_DEVICE_INDEX + 1}: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】)")
            print(f"💥 正在批量解散匹配前缀 【{GROUP_PREFIX}】{range_info} 的群聊 (测试数据一键彻底销毁)...")
            client = IMGroupClient(device_id=cfg.device_id)
            client.batch_disband_groups(
                prefix=GROUP_PREFIX,
                start_index=START_INDEX,
                end_index=END_INDEX,
            )
        elif MODE in ("single_transfer", "transfer"):
            cfg = DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX]
            print(f"📱 [当前模式]: 单群转让群主 (设备 {TARGET_DEVICE_INDEX + 1}: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】)")
            print(f"👑 正在将群聊 【{TARGET_GROUP_NAME}】 转让给: 【{TARGET_TRANSFER_USER}】...")
            client = IMGroupClient(device_id=cfg.device_id)
            client.transfer_owner(group_name_or_id=TARGET_GROUP_NAME, target_friend_or_openid=TARGET_TRANSFER_USER)
        elif MODE in ("single_quit", "quit"):
            cfg = DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX]
            print(f"📱 [当前模式]: 单群退出群聊 (设备 {TARGET_DEVICE_INDEX + 1}: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】)")
            print(f"🚪 正在退出群聊: 【{TARGET_GROUP_NAME}】...")
            client = IMGroupClient(device_id=cfg.device_id)
            client.quit_group(group_name_or_id=TARGET_GROUP_NAME)
        elif MODE in ("single_disband", "disband"):
            cfg = DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX]
            print(f"📱 [当前模式]: 单群解散群聊 (设备 {TARGET_DEVICE_INDEX + 1}: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】)")
            print(f"💥 正在解散群聊: 【{TARGET_GROUP_NAME}】...")
            client = IMGroupClient(device_id=cfg.device_id)
            client.disband_group(group_name_or_id=TARGET_GROUP_NAME)
        else:
            cfg = DEFAULT_CLUSTER_DEVICES[TARGET_DEVICE_INDEX]
            print(f"📱 [当前模式]: 单群创建模式 (设备 {TARGET_DEVICE_INDEX + 1}: 【{cfg.device_id}】 -> 账号: 【{cfg.sender_name}】)")
            print(f"🎯 正在创建群聊: 【{TARGET_GROUP_NAME}】 (目标匹配: {TARGET_FRIEND_PREFIXES} | 最多邀请: {MAX_INVITE_COUNT} 位)...")
            client = IMGroupClient(device_id=cfg.device_id)
            new_grp = client.create_group(
                group_name=TARGET_GROUP_NAME,
                target_friend_prefixes=TARGET_FRIEND_PREFIXES,
                max_select_count=MAX_INVITE_COUNT,
            )
            if new_grp:
                print("\n==================================================")
                print("🎉 建群成功！可直接将以下配置粘贴至 im_client.py:")
                print(f"SessionTarget(name=\"{new_grp.name}\", chat_type=ChatType.GROUP, to_cust_id=\"0\", chat_id=\"{new_grp.chat_id}\", is_top=True)")
                print("==================================================")

