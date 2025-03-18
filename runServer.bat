@echo off
for /f "tokens=3 delims=: " %%A in ('sc query ssh-agent ^| findstr "STATE"') do set "ServiceState=%%A"


if "%ServiceState%"=="RUNNING" (
    echo ssh-agent is running. Continuing.
) else (
    echo sshd is not running. Starting the service...
    powershell -Command "Start-Service -Name ssh-agent"
    echo ssh-agent service started.
)

set "CMD1=wsl -u ozan python3 server.py"
set "CMD2=wsl -u ozan php -S 0.0.0.0:33000"
set "CMD3=ssh -N -R 0.0.0.0:33000:127.0.0.1:33000 -p 51821 evo@171.22.173.112"
set "CMD4=ssh -N -R 0.0.0.0:3753:127.0.0.1:3753 -p 51821 evo@171.22.173.112"



set "CMD1=pause"
set "CMD2=pause"
REM set "CMD3=pause"
REM set "CMD4=pause"

timeout /t 3 >nul

REM Launch Windows Terminal with all panes
start "" wt new-tab powershell -Command "%CMD1%" ^
; split-pane -H powershell -Command "%CMD2%" ^
; split-pane -V powershell -Command "%CMD3%" ^
; split-pane -V powershell -Command "%CMD4%"

