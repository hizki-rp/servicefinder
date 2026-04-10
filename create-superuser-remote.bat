@echo off
title Create Superuser on Remote Database
color 0E

echo.
echo ========================================
echo   Create Superuser - Remote Database
echo ========================================
echo.

echo [INFO] Connecting to Render PostgreSQL Database
echo Database: addist (Oregon)
echo.

set USE_LOCAL_DB=false
set DEBUG=True

echo [Step 1/2] Checking database connection...
python -c "import os; os.environ['USE_LOCAL_DB'] = 'false'; import django; django.setup(); from django.db import connection; connection.ensure_connection(); print('✅ Connected to remote database')" 2>nul

if errorlevel 1 (
    echo ❌ Failed to connect to remote database
    echo Check your internet connection and backend/.env file
    pause
    exit /b 1
)

echo.
echo [Step 2/2] Creating superuser on remote database...
echo.
echo Please enter the following information:
echo.

python manage.py createsuperuser

echo.
echo ========================================
echo   Superuser Created Successfully!
echo ========================================
echo.
echo You can now login at:
echo http://localhost:8000/admin/
echo.
echo (Using remote PostgreSQL database)
echo.
pause
