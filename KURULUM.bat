@echo off
rem ===========================================================================
rem  GhostPilot - KURULUM.bat
rem  Bu dosya SADECE Python'u bulup kurulum.py'yi acar.
rem  Butun kurulum mantigi Python tarafinda (kurulum.py) - boylece .bat
rem  yuzunden cikan hatalar ortadan kalkar.
rem ===========================================================================
setlocal EnableExtensions EnableDelayedExpansion
title GhostPilot - Kurulum
cd /d "%~dp0"
color 0F
echo.
echo   ============================================================
echo     GhostPilot - Kurulum
echo   ============================================================
echo.

rem ---------- 0) Dosyalar yerinde mi? (zip'in icinden calistirilmissa) ----------
if not exist "ghostpilot.py" goto eksik
if not exist "kurulum.py" goto eksik
if not exist "lisans.py" goto eksik
goto python_bul

:eksik
echo   [HATA] Kurulum dosyalari bulunamadi.
echo.
echo   Sebep: Dosyalar bir ZIP arsivinin icinde olabilir.
echo.
echo   YAPILACAK:
echo     1) ZIP dosyasina SAG TIK - "Tumunu ayikla" - "Ayikla"
echo     2) Cikan klasore girin
echo     3) Klasorun ICINDEKI KURULUM.bat dosyasina cift tiklayin
echo.
call "%~dp0_bitis.bat"
exit /b 1

rem ---------- 1) Python ara ----------
:python_bul
set "PY="
set "PYW="

rem 1a) Sanal ortam zaten varsa onu kullan (onarim/guncelleme)
if exist "%~dp0.venv\Scripts\python.exe" (
  set "PY=%~dp0.venv\Scripts\python.exe"
  goto python_var
)

rem 1b) py launcher (python.org kurulumuyla gelir - en guvenilir)
py -3 -c "import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
if not errorlevel 1 (
  set "PY=py -3"
  goto python_var
)

rem 1c) PATH'teki python / python3
python -c "import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
if not errorlevel 1 (
  set "PY=python"
  goto python_var
)
python3 -c "import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
if not errorlevel 1 (
  set "PY=python3"
  goto python_var
)

rem 1d) Bilinen kurulum yerleri (PATH bozuksa)
for %%V in (313 312 311 310 39) do (
  if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
)
for %%V in (313 312 311 310 39) do (
  if not defined PY if exist "%ProgramFiles%\Python%%V\python.exe" set "PY=%ProgramFiles%\Python%%V\python.exe"
)
if defined PY goto python_var

rem ---------- 2) Python yok - otomatik indir ----------
echo   Python bulunamadi. Otomatik indirilip kurulacak.
echo   (Pencere cikarsa "Evet" / "Install Now" deyin)
echo.
set "PYVER=3.13.7"
set "PYEXE=%TEMP%\gpython-%RANDOM%.exe"
echo   Indiriliyor... lutfen bekleyin.
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{$ProgressPreference='SilentlyContinue';Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe' -OutFile '%PYEXE%' -UseBasicParsing}catch{exit 1}"
if not exist "%PYEXE%" goto indirme_hata
for %%A in ("%PYEXE%") do if %%~zA LSS 1000000 goto indirme_hata

echo   Kuruluyor... (5-10 dakika surebilir, kapatmayin)
start /wait "" "%PYEXE%" /passive InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0 Shortcuts=0 Include_venv=1
del /q "%PYEXE%" >nul 2>nul

rem PATH tazele
set "PATH=%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;%LOCALAPPDATA%\Programs\Python\Launcher;%PATH%"
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
  set "PY=py -3"
  goto python_var
)
for %%V in (313 312) do (
  if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
)
if defined PY goto python_var

echo.
echo   [HATA] Python kuruldu ama bulunamiyor.
echo   Cozum: Bilgisayari YENIDEN BASLATIN, sonra bu dosyaya tekrar cift tiklayin.
echo.
call "%~dp0_bitis.bat"
exit /b 1

:indirme_hata
echo.
echo   [HATA] Python indirilemedi.
echo   Sebep: internet yok, guvenlik duvari veya antivirus engeli.
echo.
echo   Cozum A: Interneti kontrol edip tekrar deneyin.
echo   Cozum B: https://python.org/downloads adresinden indirip kurun.
echo            Kurulum ekraninda "Add python.exe to PATH" kutusunu isaretleyin.
echo            Sonra bu dosyaya tekrar cift tiklayin.
echo.
call "%~dp0_bitis.bat"
exit /b 1

rem ---------- 3) Kurulumu baslat ----------
:python_var
echo   Python: !PY!
echo.
echo   Kurulum penceresi aciliyor...
echo.
!PY! "%~dp0kurulum.py"
set "SON=%ERRORLEVEL%"

echo.
if "%SON%"=="0" (
  echo   ------------------------------------------------------------
  echo   Bitti. Bu pencereyi kapatabilirsiniz.
  echo   Programi acmak icin: masaustundeki GhostPilot kisayolu.
  echo   ------------------------------------------------------------
) else (
  echo   ------------------------------------------------------------
  echo   Kurulum TAMAMLANMADI. Yukaridaki mesaja bakin.
  echo   Tekrar denemek icin bu dosyaya cift tiklayin.
  echo   Ayrintili menu icin: BASLA.bat
  echo   ------------------------------------------------------------
)
echo.
call "%~dp0_bitis.bat"
exit /b %SON%
