@echo off


for /f "tokens=1,2*" %%A in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v "Personal" 2^>nul') do set TARGET=%%C

echo Are you sure you want to uninstall Maya To Painter?(Y/N)
set INPUT=
set /P INPUT=%=%

If /I "%INPUT%"=="y" goto yes 
If /I "%INPUT%"=="n" goto continue

:yes
del %TARGET%\maya\plug-ins\mayaToPainter.py
del %TARGET%\maya\scripts\contextPolyToolsObjectMM.mel
del %TARGET%\maya\scripts\contextPolyToolsObjectMM.res.mel
goto version

:version
CLS
set /p VERSION="Enter Maya year (ex. "2018"): "
IF NOT EXIST %TARGET%\maya\%VERSION% (
echo Maya %VERSION% isn't installed.
goto version
)
del %TARGET%\maya\%VERSION%\prefs\icons\mayaToPainter.png
goto continue

:continue
del "%TARGET%\Allegorithmic\Substance Painter\plugins\maya-to-painter" /Q
RD "%TARGET%\Allegorithmic\Substance Painter\plugins\maya-to-painter" /Q
CLS
echo Uninstall complete: Maya To Painter successfully uninstalled.
pause
