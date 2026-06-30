@echo off
:: 设置终端编码为 UTF-8，防止中文乱码
chcp 65001 >nul
title 三条自动化 - 一键联调启动器

echo ============================================================
echo   🚀 三条自动化测试平台 - 前后端联调一键启动工具 (同窗版)
echo ============================================================
echo.

:: 启动前置防御性清理，防止端口冲突
echo [0/2] 正在执行前置端口清理，确保运行环境纯净...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
taskkill /F /IM pytest.exe 2>nul >nul
echo 前置环境清理完毕！
echo.

:: 1. 在当前控制台后台拉起 Python 后端，不弹出新窗口，与前端共享同一个进程组
echo [1/2] 正在当前终端后台拉起后端服务 (8000端口)...
start /B "" python web_platform/start.py

:: 稍微等待 2 秒以确保后端网络端口初始化完毕
timeout /t 2 /nobreak >nul

:: 2. 在当前窗口直接启动前端 Vite 调试服务器
echo [2/2] 正在拉起前端调试服务 (5173/5174端口)...
echo ------------------------------------------------------------
cd web_platform/frontend
npm run dev
