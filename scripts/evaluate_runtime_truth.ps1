$ErrorActionPreference = "Stop"

python -m pytest -q
python -m py_compile bali_agent\cli.py bali_agent\capabilities.py bali_agent\readme_audit.py bali_agent\templates\runtime\bali_runtime.py

$tmp = Join-Path $env:TEMP ('bali-final-audit-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
    python -m bali_agent.cli --root $tmp init
    python -m bali_agent.cli --root $tmp verify
    python -m bali_agent.cli --root $tmp capability-report --json
    python -m bali_agent.cli --root . audit-readme --readme README.md --strict
}
finally {
    if (Test-Path -LiteralPath $tmp) {
        Remove-Item -LiteralPath $tmp -Recurse -Force
    }
}

Write-Host "Runtime truth evaluation passed."
