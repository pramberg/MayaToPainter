@echo off

echo Are you sure you want to install Maya To Painter?(Y/N)
set INPUT=
set /P INPUT=%=%

If /I "%INPUT%"=="n" goto cancel

for /f "tokens=1,2*" %%A in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v "Personal" 2^>nul') do set TARGET=%%C
IF NOT EXIST %TARGET%\maya\plug-ins\ (
mkdir %TARGET%\maya\plug-ins
)

copy .\Content\mayaToPainter.py %TARGET%\maya\plug-ins
CLS
echo Would you like to install marking menu?(Y/N)
set INPUT=
set /P INPUT=%=%

If /I "%INPUT%"=="y" goto yes 
If /I "%INPUT%"=="n" goto continue

:yes
IF NOT EXIST %TARGET%\maya\scripts (
mkdir %TARGET%\maya\scripts
)
copy .\Content\scripts\contextPolyToolsObjectMM.mel %TARGET%\maya\scripts
copy .\Content\scripts\contextPolyToolsObjectMM.res.mel %TARGET%\maya\scripts
goto version

:version
CLS
set /p VERSION="Enter Maya year (ex. "2018"): "
IF NOT EXIST %TARGET%\maya\%VERSION% (
echo Maya %VERSION% isn't installed. %TARGET%\maya\%VERSION%
goto version
)
robocopy ".\Content\prefs" %TARGET%\maya\%VERSION%\prefs /E
CLS
goto continue

:continue
robocopy ".\Content\maya-to-painter" "%TARGET%\Allegorithmic\Substance Painter\plugins\maya-to-painter" /E
CLS
echo Installation complete: Maya To Painter successfully installed.
pause
goto end

:cancel
CLS
echo Installation cancelled.
pause

:end