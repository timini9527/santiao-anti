@echo off
chcp 65001 >nul
title Santiao iOS WDA Stop Tool

echo ======================================================================
echo   Santiao iOS WDA 8100 自动化服务停止与清理器
echo ======================================================================
echo.

python -u "%~dp0stop_ios_wda.py"

echo.
echo 按任意键退出本窗口...
pause >nul

