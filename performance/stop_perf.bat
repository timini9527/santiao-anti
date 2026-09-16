@echo off
chcp 65001 >nul
setlocal

rem ================================================================
rem IM 接口压测 - 一键停止与释放端口脚本
rem 强行释放 8089 (Web UI) 和 5557 (Master-Worker 调度端口)
rem ================================================================

echo ===============================================================
echo        🛑 正在终止并清理所有 Locust 压测进程...
echo ===============================================================

rem 1. 释放 8089 端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8089 ^| findstr LISTENING') do (
    echo 正在终止占用 8089 端口的进程 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

rem 2. 释放 5557 分布式调度端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5557 ^| findstr LISTENING') do (
    echo 正在终止占用 5557 端口的集群通信进程 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

echo ✅ 压测所有端口与后台节点已清理完毕！
timeout /t 2 >nul
endlocal
