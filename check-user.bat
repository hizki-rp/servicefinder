@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Checking user status...
python check-user-status.py %1

pause
