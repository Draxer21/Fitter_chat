# PowerShell helper: apply idempotent DB schema on Windows
# Usage: from repo root in PowerShell:
#   .\scripts\apply_schema_windows.ps1

$venv = "$PSScriptRoot\..\.venv\Scripts\Activate.ps1"
if (-Not (Test-Path $venv)) {
    Write-Host "No se encontró el virtualenv en $venv. Asegúrate de crear .venv y activar manualmente." -ForegroundColor Yellow
    return
}

Write-Host "Activando entorno virtual..."
. $venv

# Verifica versión de Python (debe ser 3.10.x)
$pyVersion = & python --version 2>&1
Write-Host "Versión de Python detectada: $pyVersion"
if ($pyVersion -notmatch 'Python\s+3\.10') {
    Write-Host "ERROR: Se requiere Python 3.10.x para ejecutar este script. Por favor instala Python 3.10 o activa el binario adecuado." -ForegroundColor Red
    exit 1
}

# Establece PYTHONPATH al repo root y ejecuta el script de aplicación de esquema
$env:PYTHONPATH = $PSScriptRoot + "\.."
Write-Host "PYTHONPATH=$env:PYTHONPATH"
Write-Host "Ejecutando scripts/apply_schema_sql.py..."
python "$PSScriptRoot\apply_schema_sql.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Script de esquema aplicado correctamente." -ForegroundColor Green
} else {
    Write-Host "Error ejecutando el script de esquema. Revisa la salida anterior." -ForegroundColor Red
    exit $LASTEXITCODE
}
