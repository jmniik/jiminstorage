# llm-local -> GitHub (jiminstorage) auto sync
# Runs from: Claude Code hook (after Claude edits) + Windows Task Scheduler (every 10 min)
# Log: %LOCALAPPDATA%\llm-local-sync.log
# Turn off: delete the hook in .claude/settings.json and the "llm-local auto-sync" scheduled task

$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$log  = Join-Path $env:LOCALAPPDATA 'llm-local-sync.log'
$git  = 'C:\Program Files\Git\cmd\git.exe'

function Write-Log($text) {
    Add-Content -LiteralPath $log -Encoding UTF8 -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $text)
}

# Only one sync at a time (hook and scheduler can overlap)
$mutex = New-Object System.Threading.Mutex($false, 'Local\llm-local-auto-sync')
if (-not $mutex.WaitOne(0)) { exit 0 }

try {
    Set-Location -LiteralPath $repo
    $changes = & $git status --porcelain
    if (-not $changes) { exit 0 }

    & $git add -A 2>&1 | Out-Null
    $msg = 'Auto-sync: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    & $git commit -q -m $msg 2>&1 | Out-Null
    $out = & $git push -q origin main 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Write-Log "pushed ($(@($changes).Count) files)"
    } else {
        Write-Log "push FAILED: $out"
    }
}
catch {
    Write-Log "error: $_"
}
finally {
    $mutex.ReleaseMutex()
}
