$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        $command = @($Executable) + $Arguments -join ' '
        throw "Command failed with exit code ${LASTEXITCODE}: $command"
    }
}

$scriptRoot = $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$repoRoot = Split-Path -Parent $scriptRoot

Push-Location $repoRoot
try {
    Invoke-Step python @('-m', 'pytest', '-q')
    Invoke-Step python @('-m', 'py_compile', 'bali_agent\cli.py', 'bali_agent\capabilities.py', 'bali_agent\readme_audit.py', 'bali_agent\templates\runtime\bali_runtime.py')

    $tmp = Join-Path $env:TEMP ('bali-final-audit-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tmp | Out-Null

    try {
        Invoke-Step python @('-m', 'bali_agent.cli', '--root', $tmp, 'init')
        Invoke-Step python @('-m', 'bali_agent.cli', '--root', $tmp, 'verify')
        Invoke-Step python @('-m', 'bali_agent.cli', '--root', $tmp, 'capability-report', '--json')
        Invoke-Step python @('-m', 'bali_agent.cli', '--root', '.', 'audit-readme', '--readme', 'README.md', '--strict')
    }
    finally {
        if ($null -ne $tmp -and (Test-Path -LiteralPath $tmp)) {
            Remove-Item -LiteralPath $tmp -Recurse -Force
        }
    }
}
finally {
    Pop-Location
}

Write-Host "Runtime truth evaluation passed."
