# ServiceFinder Backend Setup Script
# Run this script to setup the backend automatically

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ServiceFinder Backend Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "⚠️  IMPORTANT: This setup uses SQLite (local database)" -ForegroundColor Yellow
Write-Host "   Remote PostgreSQL will NOT be affected`n" -ForegroundColor Yellow

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Ensure SQLite is used (not remote PostgreSQL)
Write-Host "`nConfiguring database settings..." -ForegroundColor Yellow
$env:USE_LOCAL_DB = "true"
Write-Host "✅ Configured to use SQLite (local database)" -ForegroundColor Green

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create migrations
Write-Host "`nCreating migrations for providers app..." -ForegroundColor Yellow
python manage.py makemigrations providers
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migrations created" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create migrations" -ForegroundColor Red
    exit 1
}

# Run migrations
Write-Host "`nRunning migrations..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migrations applied" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to apply migrations" -ForegroundColor Red
    exit 1
}

# Run test script
Write-Host "`nRunning setup tests..." -ForegroundColor Yellow
python test_setup.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Please review the output above." -ForegroundColor Yellow
}

# Prompt for superuser creation
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$createSuperuser = Read-Host "Do you want to create a superuser now? (y/n)"
if ($createSuperuser -eq "y" -or $createSuperuser -eq "Y") {
    Write-Host "`nCreating superuser..." -ForegroundColor Yellow
    python manage.py createsuperuser
}

# Final instructions
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "1. Start the server:" -ForegroundColor White
Write-Host "   python manage.py runserver`n" -ForegroundColor Gray
Write-Host "2. Access admin interface:" -ForegroundColor White
Write-Host "   http://localhost:8000/admin/`n" -ForegroundColor Gray
Write-Host "3. Test API endpoints:" -ForegroundColor White
Write-Host "   http://localhost:8000/api/`n" -ForegroundColor Gray
Write-Host "4. View documentation:" -ForegroundColor White
Write-Host "   - API-DOCUMENTATION.md" -ForegroundColor Gray
Write-Host "   - ADMIN-SETUP-GUIDE.md" -ForegroundColor Gray
Write-Host "   - BACKEND-TO-FRONTEND-HANDOFF.md`n" -ForegroundColor Gray

Write-Host "🎉 ServiceFinder backend is ready!" -ForegroundColor Green
Write-Host ""
