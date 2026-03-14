@echo off
echo ========================================
echo Starting MertService Backend
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python or add it to PATH
    pause
    exit /b 1
)

echo.
echo Starting Django development server...
echo Backend will be available at: http://0.0.0.0:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python manage.py runserver 0.0.0.0:8000

pause
