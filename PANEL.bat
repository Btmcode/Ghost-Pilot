@echo off
setlocal
title GhostPilot - Panel
cd /d "%~dp0"
set "PY=py -3"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\pythonw.exe"
start "" %PY% "%~dp0ui.py" %*
exit /b 0
