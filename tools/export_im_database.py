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
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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
# 目标设备序列号 (若设为 None 则运行时自动探测首台在线设备)
DEFAULT_DEVICE_ID: Optional[str] = "3B65BN02GU600000"

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
UPDATE_LATEST_MIRROR: bool = False

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

        # 优先使用传入参数，其次读取全局变量，最后执行自动探测
        selected_device = device_id or DEFAULT_DEVICE_ID
        self.device_id = selected_device or self._auto_detect_device()

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

    def _auto_detect_device(self) -> str:
        """自动检测当前连接的可用设备。"""
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

        if not devices:
            raise RuntimeError(
                "❌ 未检测到任何已连接的 Android 设备，请检查 USB 调试或模拟器状态！"
            )

        # 优先匹配当前工程默认的测试真机
        preferred = "3B65BN02GU600000"
        if preferred in devices:
            return preferred
        return devices[0]

    def verify_debuggable_access(self) -> bool:
        """验证目标应用是否具备 run-as 穿透权限。"""
        print(f"🔍 检查设备 [{self.device_id}] 上应用 [{self.package_name}] 的提权通道...")
        res = self._run_adb_cmd(
            ["shell", f"run-as {self.package_name} id"], check=False
        )
        if res.returncode == 0 and "uid=" in res.stdout:
            print(f"✅ 沙盒穿透通道验证成功: {res.stdout.strip()}")
            return True

        print("❌ 无法以 run-as 身份访问该应用沙盒！")
        print("💡 排查建议: 请确保真机安装的是已破甲注入 android:debuggable='true' 的 APK 包。")
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
        # 1. 在设备端将私有沙盒数据库打包克隆至 /data/local/tmp
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
            # 2. 原生 CRC 高速直拉到本地目标时间戳目录 (无中间 rename 冲突)
            print(f"🚀 正在拉取全量数据库至本地目标路径: {self.output_dir} ...")
            source_on_device = f"{device_temp_dir}/databases/."

            pull_res = self._run_adb_cmd(
                ["pull", source_on_device, str(self.output_dir)],
                check=False,
            )
            if pull_res.returncode != 0:
                print(f"❌ ADB 数据拉取失败: {pull_res.stderr}")
                return False, self.output_dir, {}

            print("✅ 数据库拉取传输完成！")

            # 3. 补充扩展名生成副本（提升开发查看体验）
            if generate_db_alias:
                self._generate_db_extensions()

            # 4. 同步维护 local_databases/latest/ 最新镜像 (供下游工具免换路径读取)
            if UPDATE_LATEST_MIRROR:
                self._update_latest_mirror()

            # 5. 自动清理超额历史备份，保持磁盘健康
            self._cleanup_old_backups()

            # 6. 统计并打印提取产物
            stats = self._inspect_extracted_databases()
            return True, self.output_dir, stats

        finally:
            # 7. 清理真机临时目录，杜绝设备存储堆积
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


    def _generate_db_extensions(self) -> None:
        """为所有未带扩展名的 SQLite 数据库及日志自动补全 .db 扩展名。"""
        print("🛠️ 正在为数据库文件自动配置 .db 关联后缀...")
        count = 0
        for p in list(self.output_dir.rglob("*")):
            if not p.is_file():
                continue
            # 跳过已有扩展名文件或临时日志
            if p.suffix or p.name.endswith("-wal") or p.name.endswith("-shm") or p.name.endswith("-journal"):
                continue

            # 检测是否为 SQLite 数据库
            try:
                with open(p, "rb") as f:
                    magic = f.read(16)
                if magic.startswith(b"SQLite format 3"):
                    new_db = p.with_suffix(".db")
                    shutil.copy2(p, new_db)
                    count += 1

                    # 同步复制 WAL 与 SHM
                    wal = p.with_name(f"{p.name}-wal")
                    if wal.exists():
                        shutil.copy2(wal, p.with_name(f"{p.name}.db-wal"))
                    shm = p.with_name(f"{p.name}-shm")
                    if shm.exists():
                        shutil.copy2(shm, p.with_name(f"{p.name}.db-shm"))
            except Exception:
                pass
        print(f"✨ 已为 {count} 个数据库创建 .db 镜像，支持可视化工具直接双击打开。")

    def _inspect_extracted_databases(self) -> Dict[str, int]:
        """扫描并打印提取结果概要。"""
        stats: Dict[str, int] = {}
        total_size = 0
        db_files = []

        for p in self.output_dir.rglob("*"):
            if p.is_file():
                total_size += p.stat().st_size
                if p.suffix == ".db" or p.name in ["meta", "message_2026", "bugly_db_"]:
                    db_files.append(p)

        print("\n" + "=" * 80)
        print(f"📊 【数据库提取成果汇报】 (设备: {self.device_id})")
        print(f"📂 存储根目录: {self.output_dir}")
        print(f"💾 数据总容量: {round(total_size / (1024 * 1024), 2)} MB")
        print("=" * 80)

        for db in sorted(db_files, key=lambda x: str(x)):
            rel_path = db.relative_to(self.output_dir)
            size_kb = round(db.stat().st_size / 1024, 1)

            # 探测表名及行数
            extra_info = ""
            try:
                conn = sqlite3.connect(db)
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [r[0] for r in c.fetchall() if not r[0].startswith("sqlite_")]
                table_cnt = len(tables)

                if "message" in tables:
                    c.execute("SELECT count(*) FROM message;")
                    msg_cnt = c.fetchone()[0]
                    extra_info = f" | 💬 聊天记录: {msg_cnt} 条"
                elif "friend" in tables:
                    c.execute("SELECT count(*) FROM friend;")
                    friend_cnt = c.fetchone()[0]
                    extra_info = f" | 👥 好友: {friend_cnt} 人"
                else:
                    extra_info = f" | 包含表: {table_cnt} 张"
                conn.close()
            except Exception:
                extra_info = ""

            print(f"  • {str(rel_path):<50} ({size_kb:>8} KB){extra_info}")
            stats[str(rel_path)] = int(size_kb)

        print("=" * 80 + "\n")
        return stats


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


def main() -> None:
    """命令行入口函数。"""
    parser = argparse.ArgumentParser(
        description="三条 IM 客户端全量数据库导出工具 (免 Root 沙盒穿透)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
    使用示例:
    # 提取到默认目录 (使用全局变量 DEFAULT_OUTPUT_DIR: {DEFAULT_OUTPUT_DIR}):
    python tools/export_im_database.py

    # 指定目标设备与自定义输出路径:
    python tools/export_im_database.py -d 3B65BN02GU600000 -o D:/databases_backup/
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

    args = parser.parse_args()

    try:
        success, out_path, _ = export_im_database(
            device_id=args.device,
            package_name=args.package,
            output_dir=args.output,
            generate_db_alias=not args.no_alias,
        )
        if success:
            print(f"🎉 导出完成！所有数据库已就绪在: {out_path}")
            sys.exit(0)
        else:
            print("❌ 数据库导出失败，请检查上方日志。")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 运行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

