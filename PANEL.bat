@echo off
rem ===========================================================================
rem  GhostPilot - PANEL.bat  -  program arayuzunu acar (BASLA.bat ile ayni)
rem  Hata olursa pencere KAPANMAZ, hata sebebi ekranda ve hata.log'da gorunur.
rem ===========================================================================
setlocal EnableExtensions
cd /d "%~dp0"

set "LOGDIR=%USERPROFILE%\.ghostpilot"
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1
set "LOG=%LOGDIR%\hata.log"

rem ---- 1) Sanal ortam Python'u (kurulumla gelen)
set "PY="
if exist "%~dp0.venv\Scripts\pythonw.exe" set "PYW=%~dp0.venv\Scripts\pythonw.exe"
if exist "%~dp0.venv\Scripts\python.exe"  set "PY=%~dp0.venv\Scripts\python.exe"
if defined PYW if not defined PY set "PY=%PYW%"

rem ---- 2) Sanal ortam yoksa sistem Python'u
if not defined PY (
  py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
  python -c "import sys" >nul 2>&1 && set "PY=python"
)

if not defined PY (
  echo.
  echo   [HATA] Python bulunamadi.
  echo   Cozum: KURULUM.bat dosyasini calistirin.
  echo.
  call "%~dp0_bitis.bat"
  exit /b 1
)

rem ---- 3) ui.py var mi
if not exist "%~dp0ui.py" (
  echo.
  echo   [HATA] ui.py bulunamadi: %~dp0ui.py
  echo   Cozum: KURULUM.bat dosyasini yeniden calistirin.
  echo.
  call "%~dp0_bitis.bat"
  exit /b 1
)

rem ---- 4) Baslat: hata cikisini gecici dosyaya yaz
set "CIKTI=%TEMP%\ghostpilot_cikti.txt"
del /q "%CIKTI%" >nul 2>&1
start "" /wait "%PY%" "%~dp0ui.py" %* > "%CIKTI%" 2>&1

rem ---- 5) Hata var mi? (cikti doluysa bir sorun olmus)
for %%A in ("%CIKTI%") do set "BOYUT=%%~zA"
if not defined BOYUT set "BOYUT=0"

if "%BOYUT%"=="0" (
  del /q "%CIKTI%" >nul 2>&1
  exit /b 0
)

echo. >> "%LOG%"
echo ============================================================ >> "%LOG%"
echo [%DATE% %TIME%] ARAYUZ HATA VERDI >> "%LOG%"
type "%CIKTI%" >> "%LOG%"
echo. >> "%LOG%"

echo.
echo   ============================================================
echo    [!] GhostPilot acilirken hata verdi.
echo   ============================================================
echo.
type "%CIKTI%"
echo.
echo   Bu bilgi su dosyaya da yazildi:
echo     %LOG%
echo.
echo   Bu dosyayi gelistiriciye gonderirseniz sorun hizlica bulunur.
echo.
del /q "%CIKTI%" >nul 2>&1
call "%~dp0_bitis.bat"
exit /b 1
