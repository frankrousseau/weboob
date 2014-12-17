@echo off
setlocal enableextensions enabledelayedexpansion

call settings.cmd

echo.
echo 0.Set proxy
set/P HTTP_PROXY=Enter HTTP_PROXY if needed :
set/P HTTPS_PROXY=Enter HTTPS_PROXY if needed :

echo.
echo 1.GNU/WGET Init

set WGET=wget-%ARCHITECTURE%.exe

echo.
echo 2.Check Python Installation

rem check first possible key
set KEY_NAME=HKLM\Software\Python\PythonCore\2.7\InstallPath
if %ARCHITECTURE% == x64 (
	set KEY_NAME=HKLM\SOFTWARE\Python\PythonCore\2.7\InstallPath
)

set IsPythonInstalled=0

REG QUERY !KEY_NAME! >NUL 2>NUL
if %ERRORLEVEL% EQU 0 (
  set IsPythonInstalled=1
) else (
  rem first key doesn't exist, test the second possible key
  set KEY_NAME=HKCU\Software\Python\PythonCore\2.7\InstallPath
  REG QUERY !KEY_NAME! >NUL 2>NUL
  if %ERRORLEVEL% EQU 0 (
    set IsPythonInstalled=1
  )
)

if %IsPythonInstalled% EQU 1 (
  rem check installed python version
  for /F "tokens=4" %%A IN ('REG QUERY !KEY_NAME!') do (
    set PythonPath=%%A
  )

  !PythonPath!python.exe --version 2>&1 | find /i "!PYTHON_VERSION!" > tmp.txt
  if %ERRORLEVEL% EQU 1 (
    set IsPythonInstalled=0
  ) else (
    FOR /F "eol=; tokens=3 delims=." %%i in (tmp.txt) do set minor_version=%%i
    if !minor_version! LSS !PYTHON_MINOR_VERSION! (
      set IsPythonInstalled=0
    )
  )

  del tmp.txt
)

if %IsPythonInstalled% EQU 0 (
  rem Python is not installed
  set PYTHON_MSI=python-!PYTHON_VERSION!.msi
  if %ARCHITECTURE% == x64 (
    set PYTHON_MSI=python-!PYTHON_VERSION!.amd64.msi
  )

  echo 2.1 Download !PYTHON_MSI!
  "%WGET%" -o python_donwload --no-check-certificate "http://www.python.org/ftp/python/!PYTHON_VERSION!/!PYTHON_MSI!"

  echo 2.2 Setup !PYTHON_MSI!
  !PYTHON_MSI!

  del !PYTHON_MSI!
  del python_donwload
)

for /F "tokens=4" %%A IN ('REG QUERY !KEY_NAME!') do (
  set PythonPath=%%A
)

echo.
echo 3.Check PyQt4 Installation
set KEY_NAME=HKLM\Software\PyQt4\Py2.7\InstallPath
REG QUERY %KEY_NAME% > nul || (

  echo 3.1 Download PyQt4
  "%WGET%" -o qt_download http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.3/PyQt4-4.11.3-gpl-Py2.7-Qt4.8.6-%ARCHITECTURE%.exe

  echo 3.2 Setup PyQt4
  PyQt4-4.11.3-gpl-Py2.7-Qt4.8.6-%ARCHITECTURE%.exe

  del PyQt4-4.11.3-gpl-Py2.7-Qt4.8.6-%ARCHITECTURE%.exe
  del qt_download
)

echo.
echo 4.Check Gpg4win Installation
set ShouldReboot=0
set KEY_NAME=HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\GPG4Win
REG QUERY %KEY_NAME% > nul || (

  echo 4.1 Download Gpg4win
  "%WGET%" -o gpg4win_download http://files.gpg4win.org/gpg4win-2.2.2.exe

  echo 4.2 Setup Gpg4win
  gpg4win-2.2.2.exe

  set ShouldReboot=1

  del gpg4win-2.2.2.exe
  del gpg4win_download
)

echo.
echo 5.Check EasyInstall
if exist "%PythonPath%Scripts\easy_install.exe" (
	goto :InstallWeboobDependances
) else (

	echo 5.1 Setup setuptools
	%PythonPath%python.exe ez_setup.py || goto :InstallFailed

	del setuptools-1.1.6.tar.gz

	goto :InstallWeboobDependances
)

:InstallWeboobDependances
echo.
echo 6.Install Weboob Dependances
echo.
echo -- cssselect
%PythonPath%Scripts\easy_install.exe cssselect || goto :InstallFailed
echo.
echo -- lxml
%PythonPath%Scripts\easy_install.exe lxml==3.2.5 || goto :InstallFailed
echo.
echo -- dateutils
%PythonPath%Scripts\easy_install.exe dateutils || goto :InstallFailed
echo.
echo -- pyyaml
%PythonPath%Scripts\easy_install.exe pyyaml || goto :InstallFailed
echo.
echo -- html2text
%PythonPath%Scripts\easy_install.exe html2text || goto :InstallFailed
echo.
echo -- mechanize
%PythonPath%Scripts\easy_install.exe mechanize || goto :InstallFailed
echo.
echo -- gdata
%PythonPath%Scripts\easy_install.exe gdata || goto :InstallFailed
echo.
echo -- feedparser
%PythonPath%Scripts\easy_install.exe feedparser || goto :InstallFailed
echo.
echo -- pillow
%PythonPath%Scripts\easy_install.exe pillow==2.3.0 || goto :InstallFailed
echo.
echo -- requests
%PythonPath%Scripts\easy_install.exe requests==2.3.0 || goto :InstallFailed

echo.
echo 6.Install WeBoob
%PythonPath%Scripts\easy_install.exe %WEBOOB% || goto :InstallFailed

set StartupFolder=%AppData%\Microsoft\Windows\Start Menu\Programs
if exist "%StartupFolder%" Goto :FoundStartup
set StartupFolder=%UserProfile%\Start Menu\Programs
if exist "%StartupFolder%" Goto :FoundStartup
echo Cannot find Startup folder.
echo do not create launchers
goto :InstallSucceed

:FoundStartup
if exist "%StartupFolder%\Weboob" (
	goto :CreateLauncher
) else (
	md "%StartupFolder%\Weboob"
	goto :CreateLauncher
)

:CreateLauncher
for %%i in (%LIST_APPLIQUATIONS_QT%) do (
	echo Process %%i

	(
	  echo @echo off
	  echo start %PythonPath%pythonw.exe %PythonPath%Scripts\%%i
	) > %%i.bat

	%PythonPath%python.exe convertPNG2ICO.py "%PythonPath%\Lib\site-packages\%WEBOOB%\share\icons\hicolor\64x64\apps\%%i.png" > nul

	if exist "%StartupFolder%\Weboob\%%i.exe" (
		del "%StartupFolder%\Weboob\%%i.exe"
	)

	"Bat_To_Exe_Converter_%ARCHITECTURE%.exe" -bat "%%i.bat" -save "%StartupFolder%\Weboob\%%i.exe" -icon "%PythonPath%\Lib\site-packages\%WEBOOB%\share\icons\hicolor\64x64\apps\%%i.ico" "%%i"
	del "%%i.bat"
	del "%PythonPath%\Lib\site-packages\%WEBOOB%\share\icons\hicolor\64x64\apps\%%i.ico"
)

goto :InstallSucceed

:InstallSucceed

echo.
echo INSTALLATION PROCESS SUCCEED
if %ShouldReboot% EQU 1 (
  echo.
  echo YOU SHOULD REBOOT BEFORE USING WEBOOB
)
goto :Quit

:InstallFailed
echo.
echo INSTALLATION PROCESS FAILED
goto :Quit

:Quit

del "%WEBOOB%"
del ez_setup.py
del convertPNG2ICO.py
del settings.cmd

pause

