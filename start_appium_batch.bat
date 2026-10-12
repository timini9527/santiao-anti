@echo off
setlocal
cd /d "%~dp0"

rem ================================================================
rem Appium 端口开关配置 (静默后台无窗运行版)
rem 保留 set 开启端口；在行首增加 rem 即可禁用该端口
rem ================================================================
set "START_4723=1"
set "START_4724=1"
rem set "START_4725=1"
rem set "START_4726=1"
rem set "START_4727=1"
rem set "START_4728=1"
rem set "START_4729=1"
rem set "START_4730=1"
rem set "START_4731=1"

if not exist "logs" mkdir "logs"

echo ================================================================
echo  正在后台静默启动 Appium 服务集群 (完全隐藏控制台窗口)...
echo ================================================================

:start_ports
if defined START_4723 call :launch_port 4723
if defined START_4724 call :launch_port 4724
if defined START_4725 call :launch_port 4725
if defined START_4726 call :launch_port 4726
if defined START_4727 call :launch_port 4727
if defined START_4728 call :launch_port 4728
if defined START_4729 call :launch_port 4729
if defined START_4730 call :launch_port 4730
if defined START_4731 call :launch_port 4731

echo.
echo [ADB] 正在确保 ADB 守护服务就绪...
adb start-server >nul 2>&1
adb devices

echo.
echo ================================================================
echo  ✅ 所有启用的 Appium 服务已在后台静默运行！
echo  📁 详细日志请查看: logs\appium_4723.log / logs\appium_4724.log 等
echo  ⏹ 停止服务可使用桌面端【停止服务】或执行 taskkill /F /IM node.exe
echo ================================================================

endlocal
exit /b 0

:launch_port
echo  - [端口 %~1] 正在后台启动 (日志重定向至: %~dp0logs\appium_%~1.log)...
start "" /B cmd /c "appium.cmd -p %~1 -a 0.0.0.0 --log "%~dp0logs\appium_%~1.log""
exit /b 0
