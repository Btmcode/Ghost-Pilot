@echo off
setlocal EnableDelayedExpansion
rem ===========================================================================
rem  GhostPilot - _bitis.bat  -  Turkce "devam etmek icin bir tusa basin"
rem
rem  NEDEN VAR: Windows'un kendi "pause" komutu INGILIZCE yazar
rem  ("Press any key to continue . . ."). Bu dosya onun yerine gecer.
rem
rem  Kullanim:  call "%~dp0_bitis.bat"          (secili dili okur)
rem             call "%~dp0_bitis.bat" en       (dili zorla)
rem ===========================================================================

set "ARG="
if not "%~1"=="" (
  if /i "%~1"=="en" set "ARG=en"
  if /i "%~1"=="de" set "ARG=de"
  if /i "%~1"=="es" set "ARG=es"
  if /i "%~1"=="tr" set "ARG=tr"
)
if defined ARG goto %ARG%

rem --- dil belirtilmedi: ~/.ghostpilot/dil.json icinden oku ---
set "DIL=tr"
if exist "%USERPROFILE%\.ghostpilot\dil.json" (
  for /f "tokens=2 delims=:\"" %%a in ('findstr /i "dil" "%USERPROFILE%\.ghostpilot\dil.json"') do set "DIL=%%a"
)
if /i "!DIL!"=="en" goto en
if /i "!DIL!"=="de" goto de
if /i "!DIL!"=="es" goto es
goto tr

:tr
echo.
echo   Devam etmek icin bir tusa basin . . .
goto bekle

:en
echo.
echo   Press any key to continue . . .
goto bekle

:de
echo.
echo   Beliebige Taste drucken, um fortzufahren . . .
goto bekle

:es
echo.
echo   Pulse cualquier tecla para continuar . . .
goto bekle

:bekle
pause >nul
exit /b 0
