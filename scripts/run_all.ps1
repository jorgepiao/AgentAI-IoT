$ErrorActionPreference = "Stop"

$root = $PSScriptRoot | Split-Path -Parent
$venv = Join-Path $root ".venv" "Scripts" "Activate.ps1"

if (-not (Test-Path $venv)) {
    Write-Host "❌ No se encontró .venv en $venv" -ForegroundColor Red
    exit 1
}

$apiCmd  = "& '$venv'; uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
$sensCmd = "& '$venv'; python -m simulation.mock_sensors --dry-run --interval 5"
$actCmd  = "& '$venv'; python -m simulation.mock_actuadores --dry-run"

Write-Host "🔧 Iniciando AgentAI IoT..." -ForegroundColor Cyan
Write-Host "   Abriendo 3 ventanas — cada una corre independientemente.`n" -ForegroundColor Cyan

Start-Process powershell -WindowStyle Normal -WorkingDirectory $root `
    -ArgumentList "-NoExit", "-Command", $apiCmd

Start-Process powershell -WindowStyle Normal -WorkingDirectory $root `
    -ArgumentList "-NoExit", "-Command", $sensCmd

Start-Process powershell -WindowStyle Normal -WorkingDirectory $root `
    -ArgumentList "-NoExit", "-Command", $actCmd

Write-Host "✅ Ventanas lanzadas. Abre dashboard.html en el navegador." -ForegroundColor Green
Write-Host "   Cierra cada ventana con Ctrl+C individualmente." -ForegroundColor Yellow
