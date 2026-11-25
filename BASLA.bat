@echo off
rem GhostPilot - program arayuzunu acar (konsol penceresi acilmaz)
setlocal EnableExtensions
cd /d "%~dp0"

set "PY="
if exist "%~dp0.venv\Scripts\pythonw.exe" set "PY=%~dp0.venv\Scripts\pythonw.exe"
if not defined PY if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"

if defined PY (
  start "" "%PY%" "%~dp0ui.py" %*
  exit /b 0
)

py -3 -c "import sys" >nul 2>&1 && (start "" py -3 "%~dp0ui.py" %* & exit /b 0)
python -c "import sys" >nul 2>&1 && (start "" python "%~dp0ui.py" %* & exit /b 0)

echo.
echo   [HATA] Python bulunamadi.
echo   Cozum: KURULUM.bat dosyasini calistirin.
echo.
call "%~dp0_bitis.bat"
exit /b 1
