@echo off
echo Attempting to kill matlab.exe...
taskkill /F /IM "matlab.exe"

echo Waiting for 10 seconds before deleting the directory...
timeout /t 10 /nobreak >nul


echo Deleting directory...
rd /s /q "C:\Users\exam\soft-robots-studio-3d"

:: Confirm completion
echo Operation complete.
REM pause

shutdown /s /t 0
