@echo off
setlocal

start "MuMu v0" "D:\Program Files\MuMu\nx_main\MuMuNxMain.exe" -p com.santiaotalk.im -v 0
start "MuMu v3" "D:\Program Files\MuMu\nx_main\MuMuNxMain.exe" -p com.santiaotalk.im -v 3

where wt.exe >nul 2>&1
if not errorlevel 1 (
    wt.exe -w 0 new-tab --title "Appium 4723" cmd.exe /k appium ; new-tab --title "Appium 4724" cmd.exe /k "appium -p 4724" ; new-tab --title "ADB" cmd.exe /k "adb kill-server && adb devices"
    goto :done
)

start "Appium 4723" cmd.exe /k appium
start "Appium 4724" cmd.exe /k appium -p 4724
start "ADB" cmd.exe /k "adb kill-server && adb devices"

:done
endlocal
