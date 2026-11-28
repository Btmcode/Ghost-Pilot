@echo off
REM ===========================================================================
REM  GhostPilot NEX — Windows kurulum EXE'si üretir
REM  Copyright (c) 2026 BTM Code — MIT License
REM
REM  NE YAPAR
REM    dist\GhostPilot-Kurulum.exe  → tek dosya, çift tıkla çalışır
REM
REM  ÖNEMLİ
REM    Çapraz derleme YOKTUR. Windows .exe yalnızca Windows'ta üretilebilir.
REM    Bu yüzden bu dosyayı KENDİ Windows makinenizde çalıştırın.
REM
REM  KULLANIM
REM    1) Python 3.9+ kurulu olmalı (python.org, "Add to PATH" işaretli)
REM    2) Bu dosyaya çift tıkla  (ya da:  yap_exe.bat)
REM    3) Bittiğinde: dist\GhostPilot-Kurulum.exe
REM ===========================================================================
setlocal
cd /d "%~dp0"

echo.
echo   ============================================
echo    GhostPilot NEX - kurulum EXE'si uretiliyor
echo   ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo   [HATA] Python bulunamadi.
  echo          https://python.org adresinden kurun ve "Add Python to PATH" isaretleyin.
  pause
  exit /b 1
)

echo   1/4  PyInstaller denetleniyor...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
  echo        kuruluyor...
  python -m pip install --upgrade pyinstaller
  if errorlevel 1 (
    echo   [HATA] PyInstaller kurulamadi. Internet baglantisini denetleyin.
    pause
    exit /b 1
  )
)

echo   2/4  Araclar deneniyor (derleme oncesi)...
python -m py_compile ghostpilot.py oturum.py arama.py dosya.py gui.py izleme.py cihaz.py guvenlik.py moduller.py pty_yardimci.py
if errorlevel 1 (
  echo   [HATA] Kaynak dosyalarda sozdizimi hatasi var.
  pause
  exit /b 1
)

echo   3/4  EXE uretiliyor (birkac dakika surer)...
python exe_yap.py
if errorlevel 1 (
  echo   [HATA] Derleme basarisiz. Yukaridaki ciktiyi inceleyin.
  pause
  exit /b 1
)

echo   4/4  Sonuc:
if exist "dist\GhostPilot-Kurulum.exe" (
  for %%F in ("dist\GhostPilot-Kurulum.exe") do echo        dist\GhostPilot-Kurulum.exe  (%%~zF bayt)
  echo.
  echo   Hazir. Bu dosyaya cift tiklayarak kurabilirsiniz.
) else (
  echo        [UYARI] dist\GhostPilot-Kurulum.exe olusmadi.
  echo        exe_yap.py ciktisini inceleyin.
)

echo.
pause
endlocal
