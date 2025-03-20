@echo off
echo [Webserver Proxy] Starting Proxy

:: Enable Ctrl+C handling
setlocal ENABLEDELAYEDEXPANSION
set "ctrl_c_pressed=0"

:: Define Ctrl+C behavior
:: This prevents the "Terminate batch job (Y/N)?" prompt and allows clean exit.
:: Requires running in an interactive session.
if "%1" neq "fromTrap" (
    start "" /b cmd /c "%~f0 fromTrap"
    exit /b
)

:retry
echo [Webserver Proxy] Web Server Available at : 171.22.173.112:33000
ssh -N -R 0.0.0.0:33000:127.0.0.1:33000 -p 51821 evo@171.22.173.112

:: Check if exited due to Ctrl+C
if %ERRORLEVEL% equ 130 (
    echo [Webserver Proxy] Ctrl+C detected, stopping script.
    exit /b
)

:: If error occurs, retry after 5 seconds
echo [Webserver Proxy] Proxy disconnected. Retrying in 5 seconds...
timeout /t 5 /nobreak >nul
goto retry

