@echo off
echo Starting DocTypeGen API server...

:: Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in your PATH. Please make sure Python is installed.
    goto end
)

:: Start the API server
start /B python api.py
if %errorlevel% neq 0 (
    echo Failed to start the API server.
    goto end
)

echo API server started successfully!
echo You can access the dashboard at http://localhost:8000
echo To stop the server, run stop.bat

:end
echo.
echo Press any key to exit...
pause > nul
