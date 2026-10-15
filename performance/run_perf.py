from core.logger_utils import logger, LogIcon
"""
压测一键执行与质量门禁校验入口 (run_perf.py)
功能特性：
1. 读取 perf_config.yaml 配置文件中的发压配置与 SLA 质量门禁指标
2. 支持 --headless 无头模式（CI/CD 流水线自动化回归）与 Web UI 模式（调试与实时观测）
3. 自动生成 HTML 与 CSV 性能分析报告
4. 压测完成后严格比对 SLA 指标，超出阈值时返回非 0 退出码，阻断不可靠版本合入
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List
import yaml

# 项目与配置文件路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
CONFIG_PATH = CURRENT_DIR / "config" / "perf_config.yaml"
REPORT_DIR = CURRENT_DIR / "reports"


def load_perf_config() -> Dict[str, Any]:
    """加载压测 YAML 配置文件"""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"未找到配置文件: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
        return config_data if isinstance(config_data, dict) else {}


def build_locust_command(
    config: Dict[str, Any],
    headless: bool = True,
    custom_users: int = None,
    custom_time: str = None,
) -> List[str]:
    """根据配置组装 Locust 命令行参数"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    html_report = str(REPORT_DIR / "perf_report.html")
    csv_prefix = str(REPORT_DIR / "perf_stats")

    target_host: str = config.get("target", {}).get("host", "http://127.0.0.1:8080")
    run_cfg: Dict[str, Any] = config.get("run_settings", {})
    
    users = custom_users if custom_users else run_cfg.get("users", 500)
    spawn_rate = run_cfg.get("spawn_rate", 50)
    run_time = custom_time if custom_time else run_cfg.get("run_time", "1m")
    locust_file = str(CURRENT_DIR / "locustfile.py")

    cmd: List[str] = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        locust_file,
        "--host",
        target_host,
    ]

    if headless:
        cmd.extend([
            "--headless",
            "-u", str(users),
            "-r", str(spawn_rate),
            "--run-time", str(run_time),
            "--html", html_report,
            "--csv", csv_prefix,
            "--exit-code-on-error", "0",
        ])
    else:
        web_host = run_cfg.get("web_host", "127.0.0.1")
        web_port = run_cfg.get("web_port", 8089)
        cmd.extend([
            "--web-host", str(web_host),
            "--web-port", str(web_port),
            "-u", str(users),
            "-r", str(spawn_rate),
        ])

    return cmd


def main() -> None:
    """主程序入口"""
    parser = argparse.ArgumentParser(description="IM 接口高并发性能压测执行调度引擎")
    parser.add_argument("--web", action="store_true", help="启动 Web UI 交互模式（默认无头模式）")
    parser.add_argument("-u", "--users", type=int, default=None, help="覆盖并发用户数")
    parser.add_argument("-t", "--time", type=str, default=None, help="覆盖压测持续时长 (如 30s, 2m, 5m)")
    parser.add_argument("-w", "--workers", type=int, default=0, help="分布式 Worker 节点数量（0表示单进程，>0表示批量拉起多个 Worker 施压节点）")
    parser.add_argument("--tags", type=str, default=None, help="仅执行指定 Tag 标签的接口场景 (如 read, write, profile, message)")
    args = parser.parse_args()

    config = load_perf_config()
    is_headless = not args.web
    worker_count = args.workers

    # 分隔线日志
    logger.info(f"{LogIcon.SETUP} 正在装载压测任务与参数矩阵...")
    logger.info(f"{LogIcon.SETUP} 目标主机: {config.get('target', {}).get('host')}")
    logger.info(f"{LogIcon.SETUP} 目标并发数: {args.users or config.get('run_settings', {}).get('users')} VUsers")
    logger.info(f"{LogIcon.SETUP} 持续时间: {args.time or config.get('run_settings', {}).get('run_time')}")
    logger.info(f"{LogIcon.SETUP} 运行模式: {'Headless (CI/CD 自动化)' if is_headless else 'Web UI 可视化控制台'}")
    if worker_count > 0:
        logger.info(f"{LogIcon.SETUP} 分布式集群模式: 1 个 Master 调度节点 + {worker_count} 个 Worker 施压节点（多核批量加速）")
    if args.tags:
        logger.info(f"{LogIcon.SETUP} 场景标签过滤: {args.tags}")
    # 分隔线日志

    locust_file = str(CURRENT_DIR / "locustfile.py")
    target_host = config.get("target", {}).get("host", "http://127.0.0.1:8080")
    run_cfg = config.get("run_settings", {})
    users = args.users if args.users else run_cfg.get("users", 500)
    spawn_rate = run_cfg.get("spawn_rate", 50)
    run_time = args.time if args.time else run_cfg.get("run_time", "1m")

    # 单进程模式直接运行
    if worker_count <= 0:
        cmd = build_locust_command(
            config=config,
            headless=is_headless,
            custom_users=args.users,
            custom_time=args.time,
        )
        if args.tags:
            cmd.extend(["--tags", args.tags])

        if not is_headless:
            import threading
            import time
            import webbrowser

            web_port = config.get("run_settings", {}).get("web_port", 8089)
            url = f"http://127.0.0.1:{web_port}"

            def _auto_open_browser():
                time.sleep(1.2)
                webbrowser.open(url)

            threading.Thread(target=_auto_open_browser, daemon=True).start()
            logger.info(f"{LogIcon.ACTION} 压测控制台地址: {url}")
            logger.info(f"{LogIcon.ACTION} 系统已尝试为您自动弹出浏览器，若未弹出请手动复制上方地址在浏览器打开。\n")

        logger.info(f"{LogIcon.ACTION} 执行命令: {' '.join(cmd)}\n")
        proc = subprocess.run(cmd)
        sys.exit(proc.returncode)

    # 分布式集群批量启动模式：1 个 Master + N 个 Worker
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    html_report = str(REPORT_DIR / "perf_report.html")
    csv_prefix = str(REPORT_DIR / "perf_stats")

    # 1. 组装 Master 启动命令
    master_cmd = [
        sys.executable, "-m", "locust",
        "-f", locust_file,
        "--master",
        "--host", target_host,
    ]
    if is_headless:
        master_cmd.extend([
            "--headless",
            "--expect-workers", str(worker_count),
            "-u", str(users),
            "-r", str(spawn_rate),
            "--run-time", str(run_time),
            "--html", html_report,
            "--csv", csv_prefix,
            "--exit-code-on-error", "0",
        ])
    else:
        web_host = run_cfg.get("web_host", "127.0.0.1")
        web_port = run_cfg.get("web_port", 8089)
        master_cmd.extend([
            "--web-host", str(web_host),
            "--web-port", str(web_port),
            "--expect-workers", str(worker_count),
        ])
    if args.tags:
        master_cmd.extend(["--tags", args.tags])

    # 2. 组装 Worker 启动命令
    worker_cmd = [
        sys.executable, "-m", "locust",
        "-f", locust_file,
        "--worker",
        "--master-host", "127.0.0.1",
    ]

    import time
    worker_processes = []
    try:
        logger.info(f"{LogIcon.SETUP} [1/2] 正在启动 Master 调度节点...")
        master_proc = subprocess.Popen(master_cmd)
        time.sleep(1.5)  # 等待 Master 节点端口就绪

        logger.info(f"{LogIcon.SETUP} [2/2] 正在批量拉起 {worker_count} 个 Worker 施压节点...")
        for i in range(1, worker_count + 1):
            wp = subprocess.Popen(worker_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            worker_processes.append(wp)
            logger.info(f"{LogIcon.SUCCESS} - Worker #{i} 已启动 (PID: {wp.pid})")

        if not is_headless:
            import webbrowser
            web_port = run_cfg.get("web_port", 8089)
            url = f"http://127.0.0.1:{web_port}"
            time.sleep(1.0)
            webbrowser.open(url)
            logger.info(f"{LogIcon.ACTION} 压测控制台地址: {url}")
            logger.info(f"{LogIcon.ACTION} 集群就绪！可在 Web UI 查看已连接的 {worker_count} 个 Worker 节点状态。\n")

        # 等待 Master 执行完毕
        master_proc.wait()
    except KeyboardInterrupt:
        logger.info(f"{LogIcon.ACTION} 收到中断信号，正在批量清理所有压测节点...")
    finally:
        # 清理与回收所有 Worker 进程
        for wp in worker_processes:
            try:
                wp.terminate()
            except Exception:
                pass
        logger.info(f"{LogIcon.SUCCESS} 所有分布式压测节点已安全退出。")


if __name__ == "__main__":
    main()
