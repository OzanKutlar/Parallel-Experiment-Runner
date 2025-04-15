@echo off
setlocal

:: Save the current directory
set "TARGET_DIR=%CD%"

echo Attempting to kill matlab.exe...
taskkill /F /IM "matlab.exe"

echo Changing to a temporary directory to allow deletion...
cd /d "%TEMP%"

echo Waiting for 10 seconds before deleting the directory: %TARGET_DIR%
timeout /t 10 /nobreak >nul

echo Deleting directory...
REM rd /s /q "%TARGET_DIR%"

echo Operation complete.
shutdown /s /t 360
