@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the html command
python cli.py html %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo HTML generation completed successfully.
  echo You can now run pdf.bat to continue.
) else (
  echo HTML generation failed. Please check the error message above.
)

endlocal