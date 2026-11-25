@echo off
setlocal EnableExtensions
title GhostPilot - Kaldirma
cd /d "%~dp0"
color 0F
echo.
echo   ============================================================
echo     GhostPilot - Kaldirma
echo   ============================================================
echo.
echo   Bu islem sunlari yapar:
echo     1) Sunucuyu ve bekciyi durdurur
echo     2) Otomatik baslatmayi kaldirir
echo     3) Masaustu / Baslat menusu kisayollarini siler
echo     4) "Programlar" listesi kaydini siler
echo     5) Ayarlari ve lisans bilgisini siler
echo     6) Kurulum klasorunu siler
echo.
echo   Once KAPATIN: uygulamadaki baglantiyi
echo   (Ayarlar - Baglayicilar - GhostPilot - Kaldir)
echo.
set /p ONAY="  Devam edilsin mi? (E/H): "
if /i not "%ONAY%"=="E" (
  echo   Iptal edildi.
  call "%~dp0_bitis.bat"
  exit /b 0
)
echo.

rem --- Python bul (4 yol)
set "PY="
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if not defined PY (
  py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
  python -c "import sys" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  python3 -c "import sys" >nul 2>&1 && set "PY=python3"
)
if not defined PY (
  echo   [UYARI] Python bulunamadi. Klasoru elle silebilirsiniz:
  echo           %~dp0
  echo           ve kayit defterinden su anahtari silin:
  echo           HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\GhostPilot
  call "%~dp0_bitis.bat"
  exit /b 1
)

echo   Python: %PY%
echo.
%PY% "%~dp0kaldir.py" --sessiz --tum
set "SON=%ERRORLEVEL%"

echo.
if "%SON%"=="0" (
  echo   ------------------------------------------------------------
  echo   GhostPilot kaldirildi. Bu pencereyi kapatabilirsiniz.
  echo   ------------------------------------------------------------
) else (
  echo   ------------------------------------------------------------
  echo   Kaldirma tamamlanmadi. Yukaridaki mesaja bakin.
  echo   ------------------------------------------------------------
)
echo.
call "%~dp0_bitis.bat"
exit /b %SON%
