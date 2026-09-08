@echo off
setlocal

rem ================================================================
rem Appium port switches
rem Keep "rem" to disable a port; remove "rem" to enable it.
rem icacls "$env:USERPROFILE\Desktop" /grant "${env:USERNAME}:(OI)(CI)(F)" /t /c /q
rem ================================================================
set "START_4723=1"
set "START_4724=1"
rem set "START_4725=1"
rem set "START_4726=1"
set "START_4727=1"
set "START_4728=1"
set "START_4729=1"
set "START_4730=1"
set "START_4731=1"

rem Example: to disable port 4725, change its line to:
rem set "START_4725=1"

where wt.exe >nul 2>&1
if errorlevel 1 goto :fallback
set "USE_WT=1"
echo Opening one Windows Terminal window with Appium tabs...

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

if "%USE_WT%"=="1" goto :adb_tab

echo.
echo Waiting briefly for the Appium processes to start...
timeout /t 2 /nobreak >nul

echo.
echo Resetting ADB and listing connected devices...
adb kill-server
adb devices -l

echo.
echo Appium processes were started in this CMD window.
echo Keep this window open while using Appium.
pause
endlocal
exit /b 0

:adb_tab
echo Opening the final ADB tab...
wt.exe -w 0 new-tab --title "ADB devices" cmd.exe /d /k "adb kill-server & adb devices -l"
echo.
echo All enabled Appium tabs and the ADB tab were opened in one Windows Terminal window.
endlocal
exit /b 0

:launch_port
if "%USE_WT%"=="1" (
    echo Opening Appium tab on port %~1...
    wt.exe -w 0 new-tab --title "Appium %~1" cmd.exe /d /k appium -p %~1
    timeout /t 1 /nobreak >nul
) else (
    echo Starting Appium on port %~1...
    start "" /b appium -p %~1
)
exit /b 0

:fallback
set "USE_WT=0"
echo Windows Terminal wt.exe was not found.
echo Classic CMD does not support tabs.
echo Falling back to one CMD window with background Appium processes.
echo.
goto :start_ports
