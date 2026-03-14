@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Fixing provider status...
python fix-provider-status.py %1

pause
