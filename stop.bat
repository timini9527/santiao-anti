@echo off
:: 设置终端编码为 UTF-8，防止中文乱码
chcp 65001 >nul
title 三条自动化 - 一键关闭服务

echo ============================================================
echo   🛑 正在一键关闭并清理三条自动化测试平台的所有进程...
echo ============================================================
echo.

:: 1. 强制清理后端服务 (8000 端口)
echo 正在检测并终止 Python 后端服务 (8000端口)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
    echo  - 已成功释放 8000 端口 (PID: %%a)
)

:: 2. 强制清理前端服务 (5173 端口)
echo 正在检测并终止 Vite 前端调试服务 (5173端口)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
    echo  - 已成功释放 5173 端口 (PID: %%a)
)

:: 3. 强制清理任何残留的测试子进程
echo 正在清理可能残留的 pytest 测试进程...
taskkill /F /IM pytest.exe 2>nul >nul

echo.
echo ============================================================
echo   🎉 清理完成！所有服务端口与自动化测试子进程均已成功释放。
echo ============================================================
timeout /t 3
