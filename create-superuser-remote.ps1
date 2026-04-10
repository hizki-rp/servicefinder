# Create Superuser on Remote PostgreSQL Database

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Create Superuser - Remote Database" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[INFO] Connecting to Render PostgreSQL Database" -ForegroundColor Yellow
Write-Host "Database: addist (Oregon)" -ForegroundColor Yellow
Write-Host ""

# Set environment variable to use remote database
$env:USE_LOCAL_DB = "false"
$env:DEBUG = "True"

Write-Host "Environment set: USE_LOCAL_DB = $env:USE_LOCAL_DB" -ForegroundColor Green
Write-Host ""

Write-Host "Creating superuser on remote database..." -ForegroundColor Cyan
Write-Host ""

# Create superuser
python manage.py createsuperuser

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now login at: http://localhost:8000/admin/" -ForegroundColor Yellow
Write-Host ""
