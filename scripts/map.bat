@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the map command
python cli.py map %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo Mapping completed successfully.
  echo You can now run html.bat to continue.
) else (
  echo Mapping failed. Please check the error message above.
)

endlocal