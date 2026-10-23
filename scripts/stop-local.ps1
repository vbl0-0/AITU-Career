$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskFile = Join-Path $taskRoot '.local\processes.json'
if (Test-Path -LiteralPath $taskFile) {
    $taskProcesses = Get-Content -LiteralPath $taskFile -Raw | ConvertFrom-Json
    foreach ($entry in $taskProcesses.PSObject.Properties) {
        $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($entry.Value)" -ErrorAction SilentlyContinue
        if ($taskProcess -and (($taskProcess.ExecutablePath -like "$taskRoot\*") -or ($taskProcess.CommandLine -match 'node_modules/vite/bin/vite.js'))) {
            foreach ($taskChild in Get-CimInstance Win32_Process -Filter "ParentProcessId=$($entry.Value)") {
                if ($taskChild.CommandLine -match '-m uvicorn app.main:app') { Stop-Process -Id $taskChild.ProcessId -ErrorAction SilentlyContinue }
            }
            Stop-Process -Id $entry.Value -ErrorAction SilentlyContinue
        }
    }
    Remove-Item -LiteralPath $taskFile
}
Write-Output 'Project web processes stopped. PostgreSQL remains running to preserve other local work.'
