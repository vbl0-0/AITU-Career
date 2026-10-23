param([string]$PostgresBin = 'D:\postgres\bin', [int]$Port = 55432)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskLocal = Join-Path $taskRoot '.local'
$taskData = Join-Path $taskLocal 'postgres'
if (!(Test-Path -LiteralPath (Join-Path $PostgresBin 'initdb.exe'))) { throw 'Set -PostgresBin to your PostgreSQL bin directory.' }
if (!(Test-Path -LiteralPath (Join-Path $taskRoot '.env'))) { throw 'Run python scripts/setup_env.py first.' }
$taskEnv = @{}
foreach ($line in Get-Content -LiteralPath (Join-Path $taskRoot '.env')) {
    if ($line -match '^([A-Z_]+)=(.*)$') { $taskEnv[$Matches[1]] = $Matches[2] }
}
New-Item -ItemType Directory -Path $taskLocal -Force | Out-Null
if (!(Test-Path -LiteralPath (Join-Path $taskData 'PG_VERSION'))) {
    $taskPw = Join-Path $taskLocal 'pg-init-password'
    [System.IO.File]::WriteAllText($taskPw, $taskEnv['POSTGRES_PASSWORD'])
    try {
        & (Join-Path $PostgresBin 'initdb.exe') -D $taskData -U $taskEnv['POSTGRES_USER'] --pwfile=$taskPw --auth-host=scram-sha-256 --auth-local=scram-sha-256 --encoding=UTF8 --locale=C
        if ($LASTEXITCODE -ne 0) { throw 'initdb failed' }
    } finally { Remove-Item -LiteralPath $taskPw -ErrorAction SilentlyContinue }
}
& (Join-Path $PostgresBin 'pg_ctl.exe') status -D $taskData 2>$null
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $PostgresBin 'pg_ctl.exe') start -D $taskData -l (Join-Path $taskLocal 'postgres.log') -o "-p $Port -h 127.0.0.1" -w
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL start failed' }
}
$taskOldPassword = $env:PGPASSWORD
try {
    $env:PGPASSWORD = $taskEnv['POSTGRES_PASSWORD']
    $taskExists = & (Join-Path $PostgresBin 'psql.exe') -h 127.0.0.1 -p $Port -U $taskEnv['POSTGRES_USER'] -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='aitu_career'"
    if ($taskExists -ne '1') {
        & (Join-Path $PostgresBin 'createdb.exe') -h 127.0.0.1 -p $Port -U $taskEnv['POSTGRES_USER'] aitu_career
        if ($LASTEXITCODE -ne 0) { throw 'Database creation failed' }
    }
} finally { $env:PGPASSWORD = $taskOldPassword }
Write-Output "Project PostgreSQL is available at 127.0.0.1:$Port. Data: $taskData"
