# Ensure we are in the right directory
Set-Location "d:\MMC\Documents\fyp\parvarish-be"

# Activate environment just in case (though should be run from activated env)
# ./venv/Scripts/Activate.ps1

Write-Host "Checking Database..." -ForegroundColor Cyan
python check_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Database check failed."
    exit 1
}

Write-Host "Running Migrations..." -ForegroundColor Cyan

$migrations = @(
    "migrations/001_add_parent_child_support.py",
    "migrations/002_add_behavior_tracking.py",
    "migrations/003_add_age_group_to_questions.py",
    "migrations/004_add_child_tasks.py",
    "migrations/005_add_extended_behavior_categories.py",
    "migrations/006_add_chat_child_context.py",
    "migrations/007_add_child_game_results.py",
    "migrations/008_add_game_questions.py",
    "migrations/008_add_roman_urdu_fields.py"
)

foreach ($migration in $migrations) {
    Write-Host "Running $migration..." -ForegroundColor Yellow
    python $migration
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Migration $migration failed."
        exit 1
    }
}

Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "You can now run the server with:" -ForegroundColor White
Write-Host "uvicorn main:app --reload" -ForegroundColor Cyan
