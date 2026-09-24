@echo off
setlocal

REM ==========================================
REM My Game Launcher
REM ==========================================

cd /d "%~dp0"

echo.
echo ==========================================
echo          My Game Launcher
echo ==========================================
echo.

REM ------------------------------------------
REM Check that Git is installed
REM ------------------------------------------

where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed.
    echo Please install Git and try again.
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------
REM Check that Python is installed
REM ------------------------------------------

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo Please install Python and try again.
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------
REM Update the game
REM ------------------------------------------

echo Checking for game updates...
echo.

git fetch origin

if errorlevel 1 (
    echo.
    echo WARNING: Could not contact GitHub.
    echo The game will use the current local version.
    echo.
    goto setup_environment
)

echo Updating game files...

git pull --ff-only origin main

if errorlevel 1 (
    echo.
    echo ERROR: Game update failed.
    echo.
    echo This may mean the local copy has been modified.
    echo Please contact the game developer.
    echo.
    pause
    exit /b 1
)

echo.
echo Game files are up to date.

REM ------------------------------------------
REM Set up Python environment
REM ------------------------------------------

:setup_environment

echo.
echo Checking Python environment...

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    python -m venv .venv

    if errorlevel 1 (
        echo.
        echo ERROR: Could not create Python environment.
        pause
        exit /b 1
    )
)

if not exist ".venv\Scripts\python.exe" (
     echo.
     echo ERROR: Python virtual environment was not created.
     pause
     exit /b 1
)

REM ------------------------------------------
REM Install/update dependencies
REM ------------------------------------------

echo.
echo Checking dependencies...

".venv\Scripts\python.exe" -m pip --version >nul 2>&1

if errorlevel 1 (
     echo pip is missing. Installing pip...
     ".venv\Scripts\python.exe" -m ensurepip --upgrade

     if errorlevel 1 (
         echo.
         echo ERROR: Could not install pip in the virtual environment.
         pause
         exit /b 1
     )
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt --disable-pip-version-check

if errorlevel 1 (
    echo.
    echo ERROR: Could not install game dependencies.
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------
REM Start the game
REM ----------  --------------------------------

echo.
echo Starting game...
echo.

".venv\Scripts\python.exe" game\Main.py

if errorlevel 1 (
    echo.
    echo ==========================================
    echo The game exited with an error.
    echo ==========================================
    echo.
    pause
)

endlocal