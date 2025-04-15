@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Check if a file path was provided
if "%~1"=="" (
  echo Error: Please provide a file path.
  echo Usage: scripts\all.bat ^<file_path^> [options]
  exit /b 1
)

rem Run the all command
python cli.py all %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo Complete workflow completed successfully.
) else (
  echo Workflow failed. Please check the error message above.
)

endlocal