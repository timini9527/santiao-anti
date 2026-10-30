@echo off
chcp 65001 >nul
title Apple 官方底层通信驱动一键安装程序

echo ==============================================================================
echo   Apple 官方底层通信驱动一键静默安装 (Apple Mobile Device Service)
echo ==============================================================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [提示] 正在获取管理员权限以注册系统驱动服务...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo [1/2] 正在静默安装 Apple 官方底层驱动组件 (AppleMobileDeviceSupport64.msi)...
msiexec /i "%~dp0AppleMobileDeviceSupport64.msi" /qn /norestart

:: 验证服务状态
echo [2/2] 正在启动并检查 Apple Mobile Device Service 后台服务...
sc query "Apple Mobile Device Service" >nul 2>&1
if %errorLevel% equ 0 (
    net start "Apple Mobile Device Service" >nul 2>&1
    echo.
    echo ==============================================================================
    echo  [SUCCESS] 驱动安装成功！Apple Mobile Device Service 服务已就绪并启动。
    echo ==============================================================================
    echo.
    echo 现在您可以：
    echo 1. 用 USB 数据线将 iPhone 连接到当前电脑；
    echo 2. 在手机屏幕上点击【信任此电脑】并输入锁屏密码；
    echo 3. 运行 python -m desktop_app.ui.harmony_native_inspector 即可享受 60 FPS 极速投屏。
) else (
    echo.
    echo [WARNING] 未能直接检测到服务，可能需要手动双击运行 AppleMobileDeviceSupport64.msi 完成安装。
)

echo.
pause

