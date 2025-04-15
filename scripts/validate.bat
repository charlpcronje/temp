@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the validate command
python cli.py validate %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo Validation completed successfully.
  echo You can now run map.bat to continue.
) else (
  echo Validation failed. Please check the error message above.
)

endlocal