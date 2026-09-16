@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem ================================================================
rem IM 接口高并发性能压测 - 分布式多节点批量一键启动器
rem 架构: 1 个 Master 调度节点 + N 个 Worker 施压节点 (充分榨干多核 CPU)
rem ================================================================

title IM 接口压测 - 分布式集群控制台

set "WORKERS=4"
set "WEB_PORT=8089"
set "PYTHON_EXE=python"

echo ===============================================================
echo        🚀 [IM 性能压测] 分布式集群多节点批量启动器
echo ===============================================================
echo  当前配置:
echo   - 调度节点 (Master): 1 个 (负责协调、聚合数据与 Web UI)
echo   - 施压节点 (Worker): %WORKERS% 个 (多进程独立跑满 CPU 核心)
echo   - 控制台端口: %WEB_PORT%
echo ===============================================================
echo.

rem 调用 Python 封装的集群批量调度器
%PYTHON_EXE% performance\run_perf.py --web -w %WORKERS%

echo.
echo 压测进程已结束。
pause
endlocal
