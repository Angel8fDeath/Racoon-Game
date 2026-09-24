@echo off
setlocal

cd /d "%~dp0"

set "LAUNCHER=%~dp0launcher.bat"

if not exist "%LAUNCHER%" (
    echo ERROR: launcher.bat was not found.
    pause
    exit /b 1
)

call :ensure_git
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo ==========================================
echo          Updating Racoon Game
echo ==========================================
echo.

echo Checking for game updates...
git fetch origin
if errorlevel 1 (
    echo.
    echo ERROR: Could not contact GitHub.
    echo Check the internet connection and try again.
    pause
    exit /b 1
)

git pull --ff-only origin main
if errorlevel 1 (
    echo.
    echo ERROR: Game update failed.
    echo The local copy may contain uncommitted changes.
    pause
    exit /b 1
)

echo.
echo Update successful. Starting the refreshed launcher...
echo.

call "%LAUNCHER%" --skip-update
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%

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
    echo Restart this bootstrap launcher and try again.
    exit /b 1
)
exit /b 0

:refresh_tool_paths
if exist "%ProgramFiles%\Git\cmd\git.exe" set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
exit /b 0
