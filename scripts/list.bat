@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the list command
python cli.py list

echo Use the scripts in the 'scripts' folder to run these commands.

endlocal