$env:USE_LOCAL_DB = "false"
$env:DATABASE_URL = "postgresql://servicefinder_oexm_user:ZFyo92pkSqbmbC0Abt3MHNTNZfVtEZns@dpg-d6qjfqlm5p6s73e4cb9g-a.oregon-postgres.render.com/servicefinder_oexm"

Write-Host "Step 1: Adding missing columns via direct psycopg2 connection..." -ForegroundColor Yellow
python fix_remote_db.py

Write-Host "Step 2: Run remaining migrations..." -ForegroundColor Cyan
python manage.py migrate

Write-Host "Step 3: Seeding 2 providers per category (24 total)..." -ForegroundColor Cyan
python manage.py seed_test_providers --providers-per-category 2

Write-Host "Step 4: Admin superuser..." -ForegroundColor Cyan
$env:DJANGO_SUPERUSER_USERNAME = "admin"
$env:DJANGO_SUPERUSER_EMAIL = "admin@mertservice.com"
$env:DJANGO_SUPERUSER_PASSWORD = "admin123456"
python manage.py create_superuser

Write-Host "All done! Remote DB is seeded." -ForegroundColor Green

Remove-Item Env:USE_LOCAL_DB
Remove-Item Env:DATABASE_URL
Remove-Item Env:DJANGO_SUPERUSER_USERNAME
Remove-Item Env:DJANGO_SUPERUSER_EMAIL
Remove-Item Env:DJANGO_SUPERUSER_PASSWORD
