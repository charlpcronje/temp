@echo off
echo Stopping DocTypeGen API server...

:: Find the Python process running api.py
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /NH ^| findstr "python"') do (
    echo Checking PID: %%i
    taskkill /F /PID %%i
    echo Stopped Python process with PID: %%i
)

echo API server stopped.
echo.
echo Press any key to exit...
pause > nul
