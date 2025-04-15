@echo off
setlocal enabledelayedExpansion

set "scanFolder=%~1"
set "extensions=%~2"
set "exclusions=%~3"

if "%scanFolder%"=="" set "scanFolder=."
if "%scanFolder%"=="." set "scanFolder=%cd%"

set "baseFile=combined_project_files"
set "outputFile=%baseFile%.md"

if exist "%outputFile%" (
    set /p "overwrite=File %outputFile% already exists. Overwrite? (Y/N): "
    if /i "!overwrite!"=="n" (
        set "outputFile=%baseFile%_1.md"
        set /a counter=1
        :findFileName
        if exist "!outputFile!" (
            set /a counter+=1
            set "outputFile=%baseFile%_!counter!.md"
            goto :findFileName
        )
        echo Will use !outputFile! instead.
    ) else (
        echo Will overwrite %outputFile%
    )
)

echo # Combined Project Files>"%outputFile%"

rem Add a blank line after the title
(echo()>>"%outputFile%"

set "fileCount=0"

for %%x in (%extensions%) do (
    for /r "%scanFolder%" %%f in (*.%%x) do (
        set "includeFile=true"
        set "relativePath=%%~ff"
        set "relativePath=!relativePath:%scanFolder%=!"
        if "!relativePath:~0,1!"=="\" set "relativePath=!relativePath:~1!"
        
        echo.!relativePath! | findstr /i /L /c:"%baseFile%" >nul
        if not errorlevel 1 (
            set "includeFile=false"
        ) else if not "%exclusions%"=="" (
            echo.!relativePath! | findstr /i /L /c:"%exclusions%" >nul
            if not errorlevel 1 (
                set "includeFile=false"
            )
        )

        if "!includeFile!"=="true" (
            echo Adding: !relativePath!
            echo ## !relativePath!>>"%outputFile%"
            echo ```%%x>>"%outputFile%"
            type "%%f">>"%outputFile%"
            (echo()>>"%outputFile%"
            echo ```>>"%outputFile%"
            (echo()>>"%outputFile%"
            set /a "fileCount+=1"
        )
    )
)

echo Finished! Added %fileCount% files to %outputFile%
endlocal