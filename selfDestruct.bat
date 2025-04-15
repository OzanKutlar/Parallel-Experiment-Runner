@echo off
echo Attempting to kill matlab.exe...
taskkill /F /IM "matlab.exe"
echo Waiting for 10 seconds before deleting the directory...
echo Directory to be deleted: %CD%
timeout /t 10 /nobreak >nul
echo Deleting directory...
REM rd /s /q "%CD%"
:: Confirm completion
echo Operation complete.
REM pause
shutdown /s /t 0