# -*- coding: utf-8 -*-
"""三条 IM 客户端全量数据库导出工具 (免 Root 沙盒穿透版)。

本模块专用于自动化提取类微信 IM 客户端在真机/模拟器私有沙盒目录
(/data/data/com.santiaotalk.im/databases/) 下的全部 SQLite 数据库文件。
基于 AXML debuggable 原地破甲能力，通过合法 run-as 通道无损提取包括：
1. 核心聊天记录库 (messages/message_*)
2. 用户与会话元数据库 (meta)
3. 全文检索 FTS 数据库 (global_search)
4. 异常监控及性能数据库 (bugly_db_, monitor.db, msre.db 等)
"""

import argparse
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# 适配 Windows 控制台编码
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass



# ---------------------------------------------------------------------------
# 全局控制变量 (支持在三条 IM 控制台或上层调用方直接修改或传入)
# ---------------------------------------------------------------------------
# 目标设备序列号 (设为 None 则运行时自动智能探测并匹配当前在线且安装了目标应用的设备)
DEFAULT_DEVICE_ID: Optional[str] = None

# 数据库存储根目录基准路径 (即 ./local_databases/)
BASE_DATABASES_DIR: Path = (
    Path(__file__).resolve().parent.parent / "local_databases"
).resolve()


def get_timestamp_output_dir() -> Path:
    """动态生成当前精确时刻的时间戳导出目录路径。"""
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (BASE_DATABASES_DIR / timestamp_str).resolve()


# 本地数据库导出的目标路径 (若设为 None 则每次执行时自动调用 get_timestamp_output_dir() 动态生成隔离目录)
DEFAULT_OUTPUT_DIR: Optional[str] = None

# 目标应用包名
DEFAULT_PACKAGE_NAME: str = "com.santiaotalk.im"

# 是否自动为缺少后缀的库补全 .db 扩展名镜像
GENERATE_DB_ALIAS: bool = True

# 是否自动在 local_databases/latest/ 同步维护最新一份数据的镜像
UPDATE_LATEST_MIRROR: bool = True

# 当检测到多台在线可用设备且未显式指定某台设备时，是否默认全量导出所有设备数据库
AUTO_EXPORT_ALL_DEVICES: bool = True

# 最多保留的历史时间戳备份文件夹数量 (超过则自动轮转回收最旧目录，防止磁盘爆满)
MAX_HISTORY_BACKUPS: int = 20



class IMDatabaseExtractor:
    """IM 客户端数据库导出器。"""

    def __init__(
        self,
        device_id: Optional[str] = None,
        package_name: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> None:
        """初始化导出器。

        Args:
            device_id: ADB 目标设备序列号，若为 None 则使用全局变量 DEFAULT_DEVICE_ID
            package_name: 目标应用包名，若为 None 则使用全局变量 DEFAULT_PACKAGE_NAME
            output_dir: 本地导出目标目录路径，若为 None 则使用全局变量 DEFAULT_OUTPUT_DIR 或动态生成时间戳目录
        """
        self.package_name = package_name or DEFAULT_PACKAGE_NAME
        self.access_mode: str = "run-as"  # 提权通道: 'run-as' (免root) 或 'root'/'su' (root模式)

        # 动态智能解析目标设备：优先指定参数 -> 全局变量 -> 自动多设备智能嗅探
        online_devices = self.list_online_devices()
        if not online_devices:
            raise RuntimeError(
                "❌ 未检测到任何已连接且处于 online/device 状态的 Android 设备，请检查 USB 调试或模拟器状态！"
            )

        target_dev = device_id or DEFAULT_DEVICE_ID
        if target_dev:
            if target_dev in online_devices:
                self.device_id = target_dev
            else:
                print(f"⚠️ 指定的目标设备 [{target_dev}] 当前未连接或离线！当前在线设备列表: {online_devices}")
                self.device_id = self._select_best_device(online_devices)
        else:
            self.device_id = self._select_best_device(online_devices)

        # 动态解析目标输出目录：优先传入 -> 全局静态指定 -> 动态生成当前时间戳子目录
        target_dir = output_dir or DEFAULT_OUTPUT_DIR
        if target_dir:
            self.output_dir = Path(target_dir).resolve()
        else:
            self.output_dir = get_timestamp_output_dir()

    def _run_adb_cmd(
        self, cmd_args: List[str], check: bool = True
    ) -> subprocess.CompletedProcess:
        """执行 ADB 命令行指令。"""
        base_cmd = ["adb"]
        if self.device_id:
            base_cmd.extend(["-s", self.device_id])
        full_cmd = base_cmd + cmd_args
        return subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=check,
        )

    @staticmethod
    def list_online_devices() -> List[str]:
        """获取当前已连接并在线的所有 Android 设备列表。"""
        try:
            res = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            devices: List[str] = []
            for line in res.stdout.splitlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            return devices
        except Exception:
            return []

    def _select_best_device(self, online_devices: List[str]) -> str:
        """在多个在线设备中智能推导并选定已安装目标应用的设备。"""
        if len(online_devices) == 1:
            return online_devices[0]

        installed_devices: List[str] = []
        for dev in online_devices:
            try:
                chk = subprocess.run(
                    ["adb", "-s", dev, "shell", f"pm list packages {self.package_name}"],
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=3,
                )
                if self.package_name in chk.stdout:
                    installed_devices.append(dev)
            except Exception:
                pass

        print(f"\n📱 当前检测到 {len(online_devices)} 台在线设备:")
        for idx, dev in enumerate(online_devices, 1):
            is_installed = dev in installed_devices
            tag = "✅ 已安装目标应用" if is_installed else "❌ 未安装目标应用"
            print(f"  [{idx}] {dev} - {tag}")

        if installed_devices:
            chosen = installed_devices[0]
            print(f"🎯 自动选定首台已安装目标应用的可用设备: [{chosen}]")
            if len(installed_devices) > 1:
                print(f"💡 提示: 存在多台安装了应用的设备，如需指定导出某台，请加参数: -d <设备ID>\n")
            return chosen

        fallback = online_devices[0]
        print(f"⚠️ 在线设备中均未检索到 [{self.package_name}] 包名，默认回退尝试首台设备: [{fallback}]\n")
        return fallback

    def verify_debuggable_access(self) -> bool:
        """验证目标应用是否具备提权通道 (优先 run-as 免 Root 穿透，备选 Root 通道)。"""
        print(f"🔍 检查设备 [{self.device_id}] 上应用 [{self.package_name}] 的提权通道...")
        # 1. 优先尝试合法 run-as 免 Root 穿透 (适用于已注入 debuggable 的包)
        res = self._run_adb_cmd(
            ["shell", f"run-as {self.package_name} id"], check=False
        )
        if res.returncode == 0 and "uid=" in res.stdout:
            print(f"✅ 沙盒穿透通道验证成功 (run-as 模式): {res.stdout.strip()}")
            self.access_mode = "run-as"
            return True

        # 2. 备选尝试原生 Root 穿透 (适用于模拟器、开发固件或已 root 测试真机)
        res_root = self._run_adb_cmd(["shell", "id"], check=False)
        if res_root.returncode == 0 and "uid=0" in res_root.stdout:
            print(f"✅ 检测到当前设备具备 Root 权限通道，自动启用 Root 极速导出模式！")
            self.access_mode = "root"
            return True

        res_su = self._run_adb_cmd(["shell", "su 0 id"], check=False)
        if res_su.returncode == 0 and "uid=0" in res_su.stdout:
            print(f"✅ 检测到当前设备具备 su 0 提权通道，自动启用 Root 极速导出模式！")
            self.access_mode = "su"
            return True

        print("❌ 无法以提权通道访问该应用沙盒数据库！")
        print("💡 排查建议: 请确保真机安装的是已破甲注入 android:debuggable='true' 的 APK 包，或在具备 Root 权限的设备/模拟器上运行。")
        return False

    def export_all(
        self, generate_db_alias: bool = True
    ) -> Tuple[bool, Path, Dict[str, int]]:
        """执行全量数据库提取流程。

        Args:
            generate_db_alias: 是否自动为缺少扩展名的数据库文件（如 meta, message_2026）
                               创建带有 .db 后缀的镜像副本，方便直接双击查看。

        Returns:
            (是否成功, 最终输出路径, 提取文件概览统计字典)
        """
        if not self.verify_debuggable_access():
            return False, self.output_dir, {}

        self.output_dir.mkdir(parents=True, exist_ok=True)
        device_temp_dir = f"/data/local/tmp/im_db_export_{os.getpid()}"

        print(f"\n📦 正在从设备沙盒流式克隆全部数据库至设备暂存区: {device_temp_dir} ...")
        # 1. 在设备端根据提权模式将私有沙盒数据库打包克隆至 /data/local/tmp
        if self.access_mode == "root":
            clone_sh = (
                f"mkdir -p {device_temp_dir} && "
                f"cp -r /data/data/{self.package_name}/databases {device_temp_dir}/ && "
                f"chmod -R 777 {device_temp_dir}"
            )
        elif self.access_mode == "su":
            clone_sh = (
                f"su 0 mkdir -p {device_temp_dir} && "
                f"su 0 cp -r /data/data/{self.package_name}/databases {device_temp_dir}/ && "
                f"su 0 chmod -R 777 {device_temp_dir}"
            )
        else:
            clone_sh = (
                f"mkdir -p {device_temp_dir} && "
                f"run-as {self.package_name} tar -cf - -C /data/data/{self.package_name} databases | "
                f"tar -xf - -C {device_temp_dir} && "
                f"chmod -R 777 {device_temp_dir}"
            )
        clone_res = self._run_adb_cmd(["shell", clone_sh], check=False)
        if clone_res.returncode != 0:
            print(f"❌ 设备端打包暂存失败: {clone_res.stderr}")
            return False, self.output_dir, {}

        try:
            # 2. 原生 CRC 高速直拉到本地独立纯 ASCII 暂存区 (彻底规避 Windows 下 ADB 遭遇 Emoji/中文路径抛 Illegal byte sequence 的底层缺陷)
            safe_dev_tag = re.sub(r'[^a-zA-Z0-9_]', '_', self.device_id or "device")
            temp_staging_dir = BASE_DATABASES_DIR / f"_staging_{safe_dev_tag}_{os.getpid()}"
            if temp_staging_dir.exists():
                shutil.rmtree(temp_staging_dir, ignore_errors=True)
            temp_staging_dir.mkdir(parents=True, exist_ok=True)

            print(f"🚀 正在拉取沙盒数据库至安全中转区: {temp_staging_dir.name} ...")
            source_on_device = f"{device_temp_dir}/databases/."

            pull_res = self._run_adb_cmd(
                ["pull", source_on_device, str(temp_staging_dir)],
                check=False,
            )
            if pull_res.returncode != 0:
                print(f"❌ ADB 数据拉取失败: {pull_res.stderr}")
                shutil.rmtree(temp_staging_dir, ignore_errors=True)
                return False, self.output_dir, {}

            print("✅ 数据库底层数据传输完成，正在迁移入库...")

            # 3. 将中转数据迁移至目标目录并由 Python 原生支持的 Unicode 引擎接管
            self.output_dir.mkdir(parents=True, exist_ok=True)
            raw_sandbox_dir = self.output_dir / "raw_databases"
            if raw_sandbox_dir.exists():
                shutil.rmtree(raw_sandbox_dir, ignore_errors=True)
            shutil.move(str(temp_staging_dir), str(raw_sandbox_dir))

            # 4. 智能解析账号身份、重构清晰目录结构并生成全景索引清单
            stats = self._organize_and_index_databases(raw_sandbox_dir)

            # 4. 同步维护 local_databases/latest/ 最新镜像 (供下游工具免换路径读取)
            if UPDATE_LATEST_MIRROR:
                self._update_latest_mirror()

            # 5. 自动清理超额历史备份，保持磁盘健康
            self._cleanup_old_backups()

            return True, self.output_dir, stats

        finally:
            # 6. 清理真机临时目录，杜绝设备存储堆积
            self._run_adb_cmd(["shell", f"rm -rf {device_temp_dir}"], check=False)

    def _update_latest_mirror(self) -> None:
        """在 local_databases/latest/ 维护最新一次导出的镜像副本与指针。"""
        latest_dir = BASE_DATABASES_DIR / "latest"
        try:
            if latest_dir.exists():
                shutil.rmtree(latest_dir, ignore_errors=True)
            shutil.copytree(self.output_dir, latest_dir)
            # 写入指针说明文件
            pointer_file = BASE_DATABASES_DIR / "latest_backup_path.txt"
            pointer_file.write_text(str(self.output_dir), encoding="utf-8")
            print(f"📌 已同步更新快捷镜像至: {latest_dir}")
        except Exception as e:
            print(f"⚠️ 更新 latest 镜像提示: {e}")

    def _cleanup_old_backups(self) -> None:
        """自动清理超过 MAX_HISTORY_BACKUPS 的历史时间戳目录，防止磁盘爆满。"""
        if not BASE_DATABASES_DIR.exists():
            return
        # 扫描形如 20261023_153326 的时间戳目录
        history_dirs: List[Path] = []
        for d in BASE_DATABASES_DIR.iterdir():
            if d.is_dir() and d.name != "latest" and "_" in d.name and len(d.name) >= 15:
                history_dirs.append(d)

        # 按目录名称（时间戳）倒序排序
        history_dirs.sort(key=lambda x: x.name, reverse=True)
        if len(history_dirs) > MAX_HISTORY_BACKUPS:
            expired_dirs = history_dirs[MAX_HISTORY_BACKUPS:]
            print(f"🧹 检测到历史备份超过 {MAX_HISTORY_BACKUPS} 个，自动清理最旧的 {len(expired_dirs)} 个备份...")
            for exp in expired_dirs:
                try:
                    shutil.rmtree(exp, ignore_errors=True)
                    print(f"   🗑️ 已清理: {exp.name}")
                except Exception:
                    pass

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """清洗字符串中影响 Windows/Linux 目录命名的非法与不可见字符。"""
        if not name:
            return ""
        # 移除非法字符 \ / : * ? " < > | 以及不可见字符
        sanitized = re.sub(r'[\x00-\x1f\\/:*?"<>|\r\n\t]+', '_', str(name)).strip(' ._')
        return sanitized[:40] if sanitized else ""

    def _extract_account_details(self, acc_dir: Path) -> Dict[str, Any]:
        """深度探测并提取单个账号目录的核心身份与业务数据。"""
        open_id = acc_dir.name
        details: Dict[str, Any] = {
            "open_id": open_id,
            "mobile": "",
            "nickname": "",
            "short_no": "",
            "msg_count": 0,
            "friend_count": 0,
            "conv_count": 0,
            "meta_file": None,
            "msg_file": None,
            "search_file": None,
            "raw_dir": acc_dir,
        }

        # 1. 解析 meta 数据库 (获取用户信息、好友数、会话数)
        meta_candidates = [
            acc_dir / "meta",
            acc_dir / "meta.db",
        ]
        meta_file = next((f for f in meta_candidates if f.is_file()), None)
        if meta_file:
            details["meta_file"] = meta_file
            try:
                conn = sqlite3.connect(f"file:{meta_file.resolve()}?mode=ro", uri=True)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = {r[0] for r in cursor.fetchall()}

                # 读取用户信息
                if "user" in tables:
                    cursor.execute("PRAGMA table_info(user);")
                    cols = [c[1] for c in cursor.fetchall()]

                    # 优先精确匹配当前账号 open_id
                    matched_row = None
                    if "open_id" in cols:
                        cursor.execute("SELECT * FROM user WHERE open_id = ? LIMIT 1;", (open_id,))
                        matched_row = cursor.fetchone()

                    # 若未精确匹配，取包含 token/mobile 的有效行
                    if not matched_row:
                        where_clause = " WHERE mobile IS NOT NULL AND mobile != ''" if "mobile" in cols else ""
                        cursor.execute(f"SELECT * FROM user{where_clause} LIMIT 1;")
                        matched_row = cursor.fetchone()

                    if matched_row:
                        row_dict = dict(zip(cols, matched_row))
                        raw_mobile = str(row_dict.get("mobile") or "").strip()
                        # 剥离国家码 0086 / +86
                        if raw_mobile.startswith("0086"):
                            raw_mobile = raw_mobile[4:]
                        elif raw_mobile.startswith("+86"):
                            raw_mobile = raw_mobile[3:]
                        details["mobile"] = raw_mobile

                        raw_nick = str(row_dict.get("nickname") or "").strip()
                        details["nickname"] = self._sanitize_filename(raw_nick)
                        details["short_no"] = str(row_dict.get("default_short_no") or row_dict.get("short_no") or "").strip()

                # 读取好友总数
                if "friend" in tables:
                    try:
                        cursor.execute("SELECT count(*) FROM friend;")
                        details["friend_count"] = cursor.fetchone()[0]
                    except Exception:
                        pass

                # 读取会话总数
                if "conversation" in tables:
                    try:
                        cursor.execute("SELECT count(*) FROM conversation;")
                        details["conv_count"] = cursor.fetchone()[0]
                    except Exception:
                        pass

                conn.close()
            except Exception:
                pass

        # 2. 解析 messages 目录 (统计聊天记录条数)
        msg_dir = acc_dir / "messages"
        candidate_msg_files: List[Path] = []
        if msg_dir.is_dir():
            for p in msg_dir.iterdir():
                if p.is_file() and not p.name.endswith(("-wal", "-shm", "-journal")):
                    candidate_msg_files.append(p)
        for p in acc_dir.iterdir():
            if p.is_file() and p.name.startswith("message_") and not p.name.endswith(("-wal", "-shm", "-journal")):
                candidate_msg_files.append(p)

        total_msgs = 0
        primary_msg_file: Optional[Path] = None
        for mf in candidate_msg_files:
            try:
                conn = sqlite3.connect(f"file:{mf.resolve()}?mode=ro", uri=True)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message';")
                if cursor.fetchone():
                    cursor.execute("SELECT count(*) FROM message;")
                    cnt = cursor.fetchone()[0]
                    total_msgs += cnt
                    if primary_msg_file is None or cnt > 0:
                        primary_msg_file = mf
                conn.close()
            except Exception:
                pass

        details["msg_count"] = total_msgs
        details["msg_file"] = primary_msg_file or (candidate_msg_files[0] if candidate_msg_files else None)

        # 3. 检索 global_search 数据库
        search_candidates = [acc_dir / "global_search", acc_dir / "global_search.db"]
        details["search_file"] = next((f for f in search_candidates if f.is_file()), None)

        return details

    def _copy_with_wal(self, src_file: Path, dest_file: Path) -> None:
        """完整拷贝 SQLite 数据库文件及其 WAL、SHM 伴生日志，确保事务数据零丢失。"""
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)

        wal_src = src_file.with_name(f"{src_file.name}-wal")
        if wal_src.exists():
            shutil.copy2(wal_src, dest_file.with_name(f"{dest_file.name}-wal"))

        shm_src = src_file.with_name(f"{src_file.name}-shm")
        if shm_src.exists():
            shutil.copy2(shm_src, dest_file.with_name(f"{dest_file.name}-shm"))

    def _organize_and_index_databases(self, raw_sandbox_dir: Path) -> Dict[str, int]:
        """将从设备拉取的原始数据库进行智能业务分类、语义化命名，并生成可视化全景索引清单。"""
        print("🧠 正在启动智能分析引擎：解析账号手机号、昵称与聊天数据全景...")

        im_data_dir = raw_sandbox_dir / "IM_Data"
        accounts: List[Dict[str, Any]] = []

        if im_data_dir.is_dir():
            for sub_dir in im_data_dir.iterdir():
                if sub_dir.is_dir():
                    info = self._extract_account_details(sub_dir)
                    accounts.append(info)

        # 按消息总量 > 好友数 > 是否有手机号 倒序排序
        accounts.sort(
            key=lambda x: (x["msg_count"], x["friend_count"], bool(x["mobile"])),
            reverse=True,
        )

        user_data_root = self.output_dir / "用户账号数据"
        sys_db_root = self.output_dir / "系统与监控数据库"
        backup_archive_dir = self.output_dir / "原始沙盒全量备份"

        user_data_root.mkdir(parents=True, exist_ok=True)
        sys_db_root.mkdir(parents=True, exist_ok=True)

        active_account_found = False
        empty_accounts_dir = user_data_root / "其他历史空壳残留"
        stats: Dict[str, int] = {}

        # 1. 整理各账号业务数据
        for idx, acc in enumerate(accounts):
            msg_cnt = acc["msg_count"]
            friend_cnt = acc["friend_count"]
            phone_tag = acc["mobile"] or (f"UID_{acc['open_id'][:8]}" if not acc["short_no"] else acc["short_no"])
            nick_tag = f"_{acc['nickname']}" if acc["nickname"] else ""

            # 判断是否为当前主活跃账号
            is_active = False
            if not active_account_found and (msg_cnt > 0 or len(accounts) == 1):
                is_active = True
                active_account_found = True
                acc["category"] = "⭐ 当前主活跃账号"
                folder_name = f"当前活跃账号_[{phone_tag}{nick_tag}]_消息{msg_cnt}条"
            elif msg_cnt > 0 or friend_cnt > 0:
                acc["category"] = "📁 历史有效账号"
                folder_name = f"历史账号_[{phone_tag}{nick_tag}]_消息{msg_cnt}条"
            else:
                acc["category"] = "⭕ 历史空壳残留"
                folder_name = f"账号_[{phone_tag}{nick_tag}]"

            # 目标归档目录
            if acc["category"] == "⭕ 历史空壳残留":
                target_acc_dir = empty_accounts_dir / folder_name
            else:
                target_acc_dir = user_data_root / folder_name

            target_acc_dir.mkdir(parents=True, exist_ok=True)
            acc["dest_dir"] = target_acc_dir

            # 复制并语义化重命名核心数据库
            if acc["msg_file"] and acc["msg_file"].exists():
                dest_msg_db = target_acc_dir / f"聊天记录_{msg_cnt}条.db"
                self._copy_with_wal(acc["msg_file"], dest_msg_db)
                stats[str(dest_msg_db.relative_to(self.output_dir))] = int(dest_msg_db.stat().st_size / 1024)

            if acc["meta_file"] and acc["meta_file"].exists():
                dest_meta_db = target_acc_dir / "通讯录与好友会话.db"
                self._copy_with_wal(acc["meta_file"], dest_meta_db)
                stats[str(dest_meta_db.relative_to(self.output_dir))] = int(dest_meta_db.stat().st_size / 1024)

            if acc["search_file"] and acc["search_file"].exists():
                dest_search_db = target_acc_dir / "全局全文检索.db"
                self._copy_with_wal(acc["search_file"], dest_search_db)
                stats[str(dest_search_db.relative_to(self.output_dir))] = int(dest_search_db.stat().st_size / 1024)

            # 保留一份原生命名的 .db 副本 (供已有脚本或第三方自动化工具直接使用)
            raw_mirror_dir = target_acc_dir / "原始命名库"
            if acc["meta_file"] and acc["meta_file"].exists():
                self._copy_with_wal(acc["meta_file"], raw_mirror_dir / "meta.db")
            if acc["msg_file"] and acc["msg_file"].exists():
                self._copy_with_wal(acc["msg_file"], raw_mirror_dir / "messages" / f"{acc['msg_file'].name}.db")
            if acc["search_file"] and acc["search_file"].exists():
                self._copy_with_wal(acc["search_file"], raw_mirror_dir / "global_search.db")

        # 2. 收集系统与 SDK 监控库 (Bugly, APM, 火山引擎等)
        sys_prefixes = ("bugly", "monitor", "msre", "msvolcano", "tbsbeacon")
        for p in raw_sandbox_dir.iterdir():
            if p.is_file() and not p.name.endswith(("-wal", "-shm", "-journal")):
                if any(p.name.lower().startswith(prefix) for prefix in sys_prefixes):
                    dest_sys_file = sys_db_root / (p.name if p.name.endswith(".db") else f"{p.name}.db")
                    self._copy_with_wal(p, dest_sys_file)
                    stats[str(dest_sys_file.relative_to(self.output_dir))] = int(dest_sys_file.stat().st_size / 1024)

        # 3. 将原始拉取目录重命名为清晰的原始备份归档
        if backup_archive_dir.exists():
            shutil.rmtree(backup_archive_dir, ignore_errors=True)
        try:
            raw_sandbox_dir.rename(backup_archive_dir)
        except Exception:
            try:
                shutil.move(str(raw_sandbox_dir), str(backup_archive_dir))
            except Exception:
                pass

        # 4. 生成专业可视化全景索引清单 Markdown 报告
        markdown_path = self.output_dir / "📋_账号与数据库全量索引清单.md"
        self._write_markdown_index(markdown_path, accounts)

        # 5. 打印终端高颜值汇报
        self._print_executive_summary(accounts, markdown_path)

        return stats

    def _write_markdown_index(self, md_path: Path, accounts: List[Dict[str, Any]]) -> None:
        """生成专业可视化全景索引清单 Markdown 报告。"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_msgs = sum(a.get("msg_count", 0) for a in accounts)

        lines: List[str] = [
            "# 📋 三条 IM 客户端全量数据库架构与账号透视报告",
            "",
            "> ⚡ **系统说明**：本报告由 `export_im_database.py` 自动化架构引擎自动生成。系统已对提取的沙盒全量数据库完成智能语义化解构，提取核心手机号、昵称与聊天数据，告别无序的哈希乱码目录。",
            "",
            "## 📌 导出摘要",
            "",
            f"- **设备序列号**：`{self.device_id}`",
            f"- **目标应用包名**：`{self.package_name}`",
            f"- **导出执行时间**：`{now_str}`",
            f"- **检测到历史账号总数**：`{len(accounts)}` 个",
            f"- **累计聊天消息总量**：`{total_msgs:,}` 条",
            f"- **存储根目录绝对路径**：`{self.output_dir}`",
            "",
            "---",
            "",
            "## 👤 账号数据全景透视表",
            "",
            "| 状态分类 | 绑定手机号 | 用户昵称 | 账号短号 / UID | 聊天记录数 | 好友数 | 最近会话 | 对应数据目录 |",
            "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |",
        ]

        for a in accounts:
            status = a.get("category", "未知")
            phone = a.get("mobile") or "`未绑定`"
            nick = a.get("nickname") or "`未设置`"
            short_no = a.get("short_no") or f"`{a.get('open_id', '')[:10]}...`"
            msg_cnt = f"**{a.get('msg_count', 0):,}** 条" if a.get("msg_count", 0) > 0 else "0 条"
            friend_cnt = f"{a.get('friend_count', 0)} 人"
            conv_cnt = f"{a.get('conv_count', 0)} 个"
            dest_dir = a.get("dest_dir")
            rel_dir = dest_dir.relative_to(self.output_dir).as_posix() if dest_dir else ""
            link_text = f"[`{Path(rel_dir).name}`](./{rel_dir})" if rel_dir else "-"
            lines.append(f"| {status} | **{phone}** | {nick} | {short_no} | {msg_cnt} | {friend_cnt} | {conv_cnt} | {link_text} |")

        lines.extend([
            "",
            "---",
            "",
            "## 🗂️ 目录分层架构说明",
            "",
            "```text",
            f"{self.output_dir.name}/",
            "├── 📋_账号与数据库全量索引清单.md          # 🌟 [当前文档] 账号与数据库全景导航报告",
            "├── 👤_用户账号数据/                        # 🌟 核心业务数据库归档目录",
            "│   ├── ⭐_当前活跃账号_[手机号_昵称]_消息xx条/  # 当前设备主要登录活跃账号 (重点排查目标)",
            "│   │   ├── 💬_聊天记录_*.db               # 核心消息库 (包含单聊/群聊全部记录，支持直接双击查看)",
            "│   │   ├── 👥_通讯录与好友会话.db         # 用户信息、好友关系、最近会话、群聊成员表",
            "│   │   ├── 🔍_全局全文检索.db             # FTS 倒排索引全文搜索库",
            "│   │   └── 📂_原始命名库/                 # 保持 meta.db 等原生命名的镜像，兼容自动化测试用例",
            "│   ├── 📁_历史账号_[手机号_昵称]_消息xx条/  # 设备历史上登录过的其他有效测试账号",
            "│   └── 📁_其他历史空壳残留/                 # 消息与好友为 0 的空壳残留目录收纳，不占主视线",
            "├── ⚙️_系统与监控数据库/                     # 🌟 Bugly 异常上报、火山引擎 APM 等系统监控库",
            "└── 📦_原始沙盒全量备份/                     # 🌟 还原原生沙盒目录与原名文件的全量备份 (安全留底)",
            "```",
            "",
            "## 📖 核心数据库表结构指引",
            "",
            "### 1. `💬_聊天记录_*.db` (即原 `message_2026`)",
            "- **`message` 表**：存储所有即时通讯聊天记录，包含字段：",
            "  - `msg_id`：全局唯一消息 ID",
            "  - `conv_id`：会话 ID (与哪个好友或群聊)",
            "  - `from_user` / `to_user`：发送方与接收方 UID",
            "  - `content`：消息加密/明文正文 (文本/卡片/系统提示)",
            "  - `msg_type`：消息类型编码 (1: 文本, 2: 图片, 3: 语音, 4: 视频, 5: 文件, 6: 名片, 等)",
            "  - `create_time`：消息毫秒时间戳",
            "  - `send_status`：发送状态 (0: 发送中, 1: 成功, 2: 失败)",
            "",
            "### 2. `👥_通讯录与好友会话.db` (即原 `meta`)",
            "- **`user` 表**：账号基本信息（手机号 `mobile`、昵称 `nickname`、短号 `default_short_no`、OpenID `open_id` 等）",
            "- **`friend` 表**：好友关系列表及备注名",
            "- **`conversation` 表**：首页会话列表、未读消息计数、置顶状态、最后一条消息预览",
            "- **`group_table` & `group_member` 表**：加入的群聊详情及群成员花名册",
            "",
            "### 3. `🔍_全局全文检索.db` (即原 `global_search`)",
            "- 采用 SQLite FTS 虚拟表技术，支持在客户端对百万级历史消息与联系人进行毫秒级全文分词检索。",
            "",
        ])

        try:
            md_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"📄 已生成全景可视化索引清单: {md_path}")
        except Exception as e:
            print(f"⚠️ 生成 Markdown 索引清单提示: {e}")

    def _print_executive_summary(self, accounts: List[Dict[str, Any]], md_path: Path) -> None:
        """在控制台打印资深架构级执行成果汇报。"""
        total_msgs = sum(a.get("msg_count", 0) for a in accounts)
        primary = next((a for a in accounts if a.get("category") == "⭐ 当前主活跃账号"), None)

        print("\n" + "=" * 80)
        print("🎉 【三条 IM 数据库智能规整与提权导出报告】")
        print("=" * 80)
        print(f"📱 目标设备 : {self.device_id}")
        print(f"📂 产物路径 : {self.output_dir}")
        print(f"📑 索引报告 : {md_path.name}")
        print(f"👥 账号总数 : 检测到 {len(accounts)} 个账号，累计聊天记录: {total_msgs:,} 条")
        if primary:
            phone = primary.get("mobile") or "未绑定"
            nick = primary.get("nickname") or "未设置"
            msgs = primary.get("msg_count", 0)
            friends = primary.get("friend_count", 0)
            print("-" * 80)
            print(f"⭐ 【当前主活跃账号识别成功】")
            print(f"   • 手机号   : {phone}")
            print(f"   • 昵称     : {nick}")
            print(f"   • 聊天记录 : {msgs:,} 条")
            print(f"   • 好友总数 : {friends} 人")
            print(f"   • 存储目录 : {primary.get('dest_dir', '').name}")
        print("=" * 80)
        print(f"💡 提示: 目录已按业务彻底理顺！已将系统监控库隔离，并为您生成了 Markdown 清单与 .db 直读镜像。")
        print("=" * 80 + "\n")



def export_im_database(
    device_id: Optional[str] = None,
    output_dir: Optional[str] = None,
    package_name: Optional[str] = None,
    generate_db_alias: Optional[bool] = None,
) -> Tuple[bool, Path, Dict[str, int]]:
    """全局便捷导出函数，专供三条 IM 控制台、自动化用例直接调用传入数据执行。

    使用示例:
        from tools.export_im_database import export_im_database
        # 1. 直接按全局默认配置执行 (设备 3B65BN02GU600000，路径 ./local_databases/):
        export_im_database()

        # 2. 动态传入设备序列号和目标路径执行:
        export_im_database(device_id="3B65BN02GU600000", output_dir="D:/backup_im")

    Args:
        device_id: 目标设备序列号（不传则读取全局变量 DEFAULT_DEVICE_ID）
        output_dir: 本地存储路径（不传则读取全局变量 DEFAULT_OUTPUT_DIR）
        package_name: 目标包名（不传则读取全局变量 DEFAULT_PACKAGE_NAME）
        generate_db_alias: 是否自动补全 .db 扩展名镜像（不传则读取 GENERATE_DB_ALIAS）

    Returns:
        (是否成功, 最终本地存储路径, 提取文件概览统计字典)
    """
    extractor = IMDatabaseExtractor(
        device_id=device_id,
        package_name=package_name,
        output_dir=output_dir,
    )
    need_alias = GENERATE_DB_ALIAS if generate_db_alias is None else generate_db_alias
    return extractor.export_all(generate_db_alias=need_alias)


def export_cluster_databases(
    device_ids: List[str],
    package_name: str = DEFAULT_PACKAGE_NAME,
    base_output_dir: Optional[Path] = None,
    generate_db_alias: bool = True,
) -> Tuple[bool, Path]:
    """批量导出多台设备数据库至同一集群批次目录下，并生成集群全景汇总报告。"""
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    cluster_root = base_output_dir or (BASE_DATABASES_DIR / f"{timestamp_str}_集群全量导出_{len(device_ids)}台设备")
    cluster_root.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print(f"🚀 开始执行集群多设备全量数据库导出 (共 {len(device_ids)} 台设备)")
    print(f"📂 批次汇总目录: {cluster_root}")
    print("=" * 80)

    device_results: List[Dict[str, Any]] = []
    overall_ok = True

    for idx, dev in enumerate(device_ids, 1):
        safe_dev_name = dev.replace(":", "_").replace("-", "_")
        dev_out_dir = cluster_root / f"设备_{safe_dev_name}"
        print(f"\n[{idx}/{len(device_ids)}] 正在导出设备: {dev} -> {dev_out_dir.name} ...")

        try:
            extractor = IMDatabaseExtractor(
                device_id=dev,
                package_name=package_name,
                output_dir=str(dev_out_dir),
            )
            ok, out_path, stats = extractor.export_all(generate_db_alias=generate_db_alias)
            if not ok:
                overall_ok = False
                device_results.append({
                    "device": dev,
                    "status": "❌ 失败 (拉取异常)",
                    "dir_name": dev_out_dir.name,
                    "primary_info": "未提取到有效数据库",
                    "file_count": 0,
                })
                print(f"⚠️ 设备 [{dev}] 导出未成功，已记录状态，自动继续下一台设备！")
                continue

            md_index = dev_out_dir / "📋_账号与数据库全量索引清单.md"
            primary_info = "已导出"
            if md_index.exists():
                for line in md_index.read_text(encoding="utf-8").splitlines():
                    if "当前主活跃账号" in line:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 6:
                            primary_info = f"主账号: {parts[2].replace('**', '')} | 消息: {parts[5]} | 好友: {parts[6]}"
                        break

            device_results.append({
                "device": dev,
                "status": "✅ 成功",
                "dir_name": dev_out_dir.name,
                "primary_info": primary_info,
                "file_count": len(stats),
            })
        except Exception as e:
            print(f"❌ 设备 [{dev}] 导出过程出现异常: {e}")
            overall_ok = False
            device_results.append({
                "device": dev,
                "status": f"❌ 异常: {e}",
                "dir_name": dev_out_dir.name,
                "primary_info": "执行异常",
                "file_count": 0,
            })
            print(f"⚠️ 设备 [{dev}] 发生异常，已隔离保护，继续下一台设备！")
            continue

    # 生成集群多设备全景汇总清单
    cluster_md = cluster_root / "📋_集群多设备全量汇总报告.md"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_lines = [
        "# 🌐 三条 IM 集群多设备全量数据库导出汇总报告",
        "",
        "> ⚡ **系统说明**：当前系统处于多设备集群测试模式，已将所有在线测试设备的私有数据库完整拉取、结构化规整并归集于本目录。",
        "",
        "## 📌 集群导出概览",
        "",
        f"- **导出执行时间**：`{now_str}`",
        f"- **集群设备总数**：`{len(device_ids)}` 台",
        f"- **目标应用包名**：`{package_name}`",
        f"- **存储批次根目录**：`{cluster_root}`",
        "",
        "---",
        "",
        "## 📱 各设备导出成果对照表",
        "",
        "| 序号 | 设备序列号 | 导出状态 | 主要活跃账号与业务指标 | 对应设备数据库目录 |",
        "| :---: | :--- | :---: | :--- | :--- |",
    ]

    for idx, r in enumerate(device_results, 1):
        rel_link = f"[`{r['dir_name']}`](./{r['dir_name']})"
        md_lines.append(f"| {idx} | `{r['device']}` | {r['status']} | {r['primary_info']} | {rel_link} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 💡 快速浏览指引",
        "- 点击上方表格中对应的设备目录链接，即可直接进入该设备的独立数据库空间；",
        "- 每个设备目录下均包含专属的 `📋_账号与数据库全量索引清单.md` 以及重命名后的 `💬_聊天记录_*.db` 和 `👥_通讯录与好友会话.db`。",
    ])

    try:
        cluster_md.write_text("\n".join(md_lines), encoding="utf-8")
        print(f"\n📑 已生成集群多设备全景汇总清单: {cluster_md}")
    except Exception as e:
        print(f"⚠️ 生成集群报告提示: {e}")

    # 同步维护 latest 镜像为整个集群目录
    if UPDATE_LATEST_MIRROR:
        latest_dir = BASE_DATABASES_DIR / "latest"
        try:
            if latest_dir.exists():
                shutil.rmtree(latest_dir, ignore_errors=True)
            shutil.copytree(cluster_root, latest_dir)
            pointer_file = BASE_DATABASES_DIR / "latest_backup_path.txt"
            pointer_file.write_text(str(cluster_root), encoding="utf-8")
            print(f"📌 已同步将整个集群导出镜像更新至: {latest_dir}")
        except Exception as e:
            print(f"⚠️ 更新 latest 镜像提示: {e}")

    print("\n" + "=" * 80)
    print(f"🎉 集群多设备全量导出完毕！所有产物已集中就绪在: {cluster_root}")
    print("=" * 80 + "\n")
    return overall_ok, cluster_root


def main() -> None:
    """命令行入口函数。"""
    parser = argparse.ArgumentParser(
        description="三条 IM 客户端全量数据库导出工具 (免 Root 沙盒穿透 & 多设备集群支持)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
    使用示例:
    # 1. 默认执行 (自动探测多设备，若多台在线默认全量导出集群所有设备):
    python tools/export_im_database.py

    # 2. 即使连着多台设备，也仅导出首台设备:
    python tools/export_im_database.py --single

    # 3. 指定特定设备导出:
    python tools/export_im_database.py -d emulator-5562
        """,
    )
    parser.add_argument(
        "-d",
        "--device",
        type=str,
        default=DEFAULT_DEVICE_ID,
        help=f"目标设备序列号 (默认使用全局变量: {DEFAULT_DEVICE_ID})",
    )
    parser.add_argument(
        "-p",
        "--package",
        type=str,
        default=DEFAULT_PACKAGE_NAME,
        help=f"目标包名 (默认使用全局变量: {DEFAULT_PACKAGE_NAME})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"目标输出目录 (默认使用全局变量: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--no-alias",
        action="store_true",
        help="不自动生成 .db 扩展名副本 (默认会自动生成)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="显式声明批量全量导出所有在线可用设备",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="仅导出首台可用设备 (多设备时不进行集群批量导出)",
    )

    args = parser.parse_args()

    try:
        # 获取当前所有在线且安装了目标应用的设备
        online_devices = IMDatabaseExtractor.list_online_devices()
        installed_devices: List[str] = []
        for dev in online_devices:
            try:
                chk = subprocess.run(
                    ["adb", "-s", dev, "shell", f"pm list packages {args.package}"],
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=3,
                )
                if args.package in chk.stdout:
                    installed_devices.append(dev)
            except Exception:
                pass

        if not installed_devices:
            print(f"❌ 当前在线设备中没有检测到安装了 [{args.package}] 的设备！")
            sys.exit(1)

        # 智能判定是否采用集群多设备全量导出模式:
        # 条件: 未显式通过 -d 指定单一设备，且 (显式传了 --all 或 开启了 AUTO_EXPORT_ALL_DEVICES 且未指定 --single) 且在线安装设备 > 1
        is_cluster_mode = (
            args.device is None
            and not args.single
            and (args.all or AUTO_EXPORT_ALL_DEVICES)
            and len(installed_devices) > 1
        )

        if is_cluster_mode:
            print(f"🌐 检测到当前系统连接了 {len(installed_devices)} 台集群设备: {installed_devices}")
            print("🚀 已自动开启【多设备集群全量导出模式】！")
            success, cluster_path = export_cluster_databases(
                device_ids=installed_devices,
                package_name=args.package,
                generate_db_alias=not args.no_alias,
            )
            sys.exit(0 if success else 1)

        # 单设备模式执行
        target_dev = args.device or installed_devices[0]
        success, out_path, _ = export_im_database(
            device_id=target_dev,
            package_name=args.package,
            output_dir=args.output,
            generate_db_alias=not args.no_alias,
        )
        if success:
            print(f"🎉 导出完成！数据库已就绪在: {out_path}")
            sys.exit(0)
        else:
            print("❌ 数据库导出失败，请检查上方日志。")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 运行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


