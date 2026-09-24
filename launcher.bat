@echo off
setlocal

REM ==========================================
REM My Game Launcher
REM ==========================================

cd /d "%~dp0"

set "PYTHON_CMD=python"

echo.
echo ==========================================
echo          My Game Launcher
echo ==========================================
echo.

call :ensure_git
if errorlevel 1 (
    pause
    exit /b 1
)

call :ensure_python
if errorlevel 1 (
    pause
    exit /b 1
)

if /I "%~1"=="--skip-update" goto setup_environment

REM ------------------------------------------
REM Update the game
REM ------------------------------------------

echo Checking for game updates...
echo.

git fetch origin

if errorlevel 1 (
    echo.
    echo ERROR: Could not contact GitHub.
    echo The game cannot verify that this computer has the latest version.
    echo Please check the internet connection and try again.
    echo.
    pause
    exit /b 1
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
    %PYTHON_CMD% -m venv .venv

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
exit

:ensure_git
call :refresh_tool_paths
git --version >nul 2>&1
if not errorlevel 1 exit /b 0

echo Git is not installed. Attempting to install Git with winget...
where winget >nul 2>&1
if errorlevel 1 (
    echo ERROR: winget is not available. Install Git manually from https://git-scm.com/.
    exit /b 1
)

winget install --id Git.Git --exact --source winget --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
    echo ERROR: Git installation failed.
    exit /b 1
)

call :refresh_tool_paths
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git was installed but is not available in PATH yet.
    echo Restart this launcher and try again.
    exit /b 1
)
exit /b 0

:ensure_python
call :refresh_tool_paths
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

echo Python is not installed. Attempting to install Python with winget...
where winget >nul 2>&1
if errorlevel 1 (
    echo ERROR: winget is not available. Install Python manually from https://www.python.org/downloads/.
    exit /b 1
)

winget install --id Python.Python.3.13 --exact --source winget --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
    echo ERROR: Python installation failed.
    exit /b 1
)

call :refresh_tool_paths
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was installed but is not available in PATH yet.
    echo Restart this launcher and try again.
    exit /b 1
)
set "PYTHON_CMD=python"
exit /b 0

:refresh_tool_paths
if exist "%ProgramFiles%\Git\cmd\git.exe" set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PATH=%LocalAppData%\Programs\Python\Python313;%LocalAppData%\Programs\Python\Python313\Scripts;%PATH%"
for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%~fD\python.exe" set "PATH=%%~fD;%%~fD\Scripts;%PATH%"
)
exit /b 0