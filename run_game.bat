@echo off
rem ---------------------------------------------------------------------------
rem  Flappy Bird - one-click launcher (Windows)
rem
rem  Uses a project-local virtual environment so the system Python is never
rem  modified.  If .venv is missing this script creates it and installs Pygame.
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto :run

echo.
echo  Creating the virtual environment (one time only)...
where py >nul 2>nul
if not errorlevel 1 py -3.13 -m venv .venv
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if not exist ".venv\Scripts\python.exe" goto :fail

echo  Installing Pygame...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

:run
".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
goto :eof

:fail
echo.
echo  Setup failed.  Install Python 3.13 from python.org, then run:
echo.
echo      py -3.13 -m venv .venv
echo      .venv\Scripts\python.exe -m pip install -r requirements.txt
echo      .venv\Scripts\python.exe main.py
echo.
pause
