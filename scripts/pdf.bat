@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the pdf command
python cli.py pdf %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo PDF generation completed successfully.
  echo Processing workflow complete.
) else (
  echo PDF generation failed. Please check the error message above.
)

endlocal