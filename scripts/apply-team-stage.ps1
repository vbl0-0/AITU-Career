param(
    [Parameter(Mandatory = $true)][string]$Stage,
    [Parameter(Mandatory = $true)][string]$Repository
)
$ErrorActionPreference = 'Stop'
$taskPackage = $PSScriptRoot
$taskManifest = Join-Path $taskPackage 'manifest.json'
if (!(Test-Path -LiteralPath $taskManifest)) { throw 'Run the helper extracted from a team package, beside manifest.json.' }
$taskConfig = Get-Content -LiteralPath $taskManifest -Raw -Encoding UTF8 | ConvertFrom-Json
$taskSelected = @($taskConfig.stages | Where-Object { $_.name -eq $Stage })
if ($taskSelected.Count -ne 1) { throw 'Unknown stage. See manifest.json for this package.' }
$taskRepoRoot = (Resolve-Path -LiteralPath $Repository).Path
if (!(Test-Path -LiteralPath (Join-Path $taskRepoRoot '.git'))) { throw 'The destination must be an existing Git working copy.' }
$taskGitRoot = (& git -C $taskRepoRoot rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($taskGitRoot) -ne [IO.Path]::GetFullPath($taskRepoRoot)) { throw 'Use the root of the Git working copy.' }
$taskStaged = & git -C $taskRepoRoot diff --cached --name-only
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect the Git index.' }
if ($taskStaged) { throw 'There are already staged files. Commit or unstage them before applying a delivery stage.' }
$taskGitBranch = & git -C $taskRepoRoot symbolic-ref --quiet --short HEAD
if ($LASTEXITCODE -ne 0) { throw 'Switch to a named branch first.' }
if ($Stage -ne '00-repository' -and $taskGitBranch -in @('main', 'master')) { throw 'Create a task branch before applying module files.' }
$taskPrefix = $taskRepoRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
$taskCopies = @()
foreach ($taskEntry in $taskSelected[0].files) {
    $taskRelative = [string]$taskEntry.path
    if ([IO.Path]::IsPathRooted($taskRelative) -or $taskRelative -match '(^|[\\/])\.\.([\\/]|$)') { throw 'Unsafe relative file path.' }
    $taskParts = $taskRelative -split '[\\/]'
    if ($taskParts -contains '.git' -or $taskParts -contains '.env') { throw 'Forbidden path in package.' }
    $taskDestination = [IO.Path]::GetFullPath((Join-Path $taskRepoRoot $taskRelative))
    if (!$taskDestination.StartsWith($taskPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Destination leaves the working copy.' }
    $taskSource = Join-Path (Join-Path (Join-Path $taskPackage 'stages') $Stage) $taskRelative
    if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw "Package checksum mismatch: $taskRelative" }
    # Check parents too: a symlink or junction must not redirect a copy outside the repository.
    $taskParent = Split-Path -Parent $taskDestination
    $taskCheck = $taskDestination
    while ($taskCheck -ne $taskRepoRoot -and $taskCheck) {
        if (Test-Path -LiteralPath $taskCheck) {
            if ((Get-Item -LiteralPath $taskCheck -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Symlink/junction destination refused: $taskRelative" }
        }
        $taskCheck = Split-Path -Parent $taskCheck
    }
    if (Test-Path -LiteralPath $taskDestination) {
        if ((Get-FileHash -LiteralPath $taskDestination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw "Existing file differs; review it manually before copying: $taskRelative" }
    }
    $taskCopies += [pscustomobject]@{ Source = $taskSource; Destination = $taskDestination; Parent = $taskParent; Relative = $taskRelative }
}
foreach ($taskCopy in $taskCopies) {
    if (!(Test-Path -LiteralPath $taskCopy.Parent)) { New-Item -ItemType Directory -Path $taskCopy.Parent -Force | Out-Null }
    Copy-Item -LiteralPath $taskCopy.Source -Destination $taskCopy.Destination
    & git -C $taskRepoRoot add -- $taskCopy.Relative
    if ($LASTEXITCODE -ne 0) { throw "Git could not stage $($taskCopy.Relative). Review the index." }
}
Write-Output "Prepared $($taskCopies.Count) files for $Stage on $taskGitBranch. No commit or push was made."
& git -C $taskRepoRoot diff --cached --stat
