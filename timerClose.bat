@echo off
:loop
:: Get the current date and time
for /f "tokens=2 delims==" %%I in ('"wmic OS Get localdatetime /value"') do set datetime=%%I
set year=%datetime:~0,4%
set month=%datetime:~4,2%
set day=%datetime:~6,2%
set hour=%datetime:~8,2%
set minute=%datetime:~10,2%

:: Check if the current date is 23rd December 2024
if "%year%"=="2024" if "%month%"=="12" if "%day%"=="23" (
    :: Check if the current time is 8:30 AM
    if "%hour%"=="08" if "%minute%"=="20" (
        :: Taskkill MATLAB process
        taskkill /f /im matlab.exe
        :: Shutdown the computer
        shutdown /s /f /t 0
    )
)

echo "Checked data and didnt shut down"

:: Wait for 15 seconds before checking again
timeout /t 15 >nul

:: Loop back to check again
goto loop
