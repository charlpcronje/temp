@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Check if a file path was provided
if "%~1"=="" (
  echo Error: Please provide a file path.
  echo Usage: scripts\import.bat ^<file_path^> [options]
  exit /b 1
)

rem Run the import command
python cli.py import %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo Import completed successfully.
  echo You can now run validate.bat to continue.
) else (
  echo Import failed. Please check the error message above.
)

endlocal