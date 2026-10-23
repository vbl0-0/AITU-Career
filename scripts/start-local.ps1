param([string]$PostgresBin = 'D:\postgres\bin', [switch]$SkipInstall)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskLocal = Join-Path $taskRoot '.local'
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
Push-Location $taskRoot
try {
    python scripts/setup_env.py
    if ($LASTEXITCODE -ne 0) { throw 'Environment setup failed' }
    if (!(Test-Path -LiteralPath $taskPython)) { python -m venv .venv }
    if (!$SkipInstall) {
        & $taskPython -m pip install -r backend/requirements.lock.txt
        if ($LASTEXITCODE -ne 0) { throw 'Python dependencies failed' }
        Push-Location frontend
        try { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'Node dependencies failed' } } finally { Pop-Location }
    }
    & (Join-Path $PSScriptRoot 'local-postgres.ps1') -PostgresBin $PostgresBin
    Push-Location backend
    try {
        & $taskPython -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'Migrations failed' }
        & $taskPython -m app.database.seed
        if ($LASTEXITCODE -ne 0) { throw 'Seed failed' }
    } finally { Pop-Location }
    $taskProcesses = @{}
    $taskBackendRunning = $false
    try { $taskHealth = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 2; $taskBackendRunning = $taskHealth.service -eq 'AITU Career' } catch { }
    if (!$taskBackendRunning) {
        $taskApi = Start-Process -FilePath $taskPython -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000' -WorkingDirectory (Join-Path $taskRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLocal 'backend.log') -RedirectStandardError (Join-Path $taskLocal 'backend-error.log') -PassThru
        $taskProcesses['backend'] = $taskApi.Id
    }
    $taskFrontendRunning = $false
    try { $taskPage = Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 2; $taskFrontendRunning = $taskPage.Content -match 'AITU Career' } catch { }
    if (!$taskFrontendRunning) {
        $taskNode = (Get-Command node.exe).Source
        $taskWeb = Start-Process -FilePath $taskNode -ArgumentList 'node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '5173', '--strictPort' -WorkingDirectory (Join-Path $taskRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLocal 'frontend.log') -RedirectStandardError (Join-Path $taskLocal 'frontend-error.log') -PassThru
        $taskProcesses['frontend'] = $taskWeb.Id
    }
    $taskProcessFile = Join-Path $taskLocal 'processes.json'
    if (Test-Path -LiteralPath $taskProcessFile) {
        $taskPrevious = Get-Content -LiteralPath $taskProcessFile -Raw | ConvertFrom-Json
        foreach ($entry in $taskPrevious.PSObject.Properties) { if (!$taskProcesses.ContainsKey($entry.Name)) { $taskProcesses[$entry.Name] = $entry.Value } }
    }
    $taskProcesses | ConvertTo-Json | Set-Content -LiteralPath $taskProcessFile
    Write-Output 'Website: http://localhost:5173 | API documentation: http://localhost:8000/docs'
} finally { Pop-Location }
