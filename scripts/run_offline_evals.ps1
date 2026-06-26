$ErrorActionPreference = "Stop"

function Test-PythonCandidate {
    param([string] $Path)

    if (-not $Path) {
        return $false
    }
    if (-not (Test-Path $Path)) {
        return $false
    }

    & $Path "--version" *> $null
    return $LASTEXITCODE -eq 0
}

$candidates = @()

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $candidates += $pythonCommand.Source
}

$codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$candidates += $codexPython

$pyCommand = Get-Command py -ErrorAction SilentlyContinue
if ($pyCommand) {
    $candidates += $pyCommand.Source
}

$selected = $null
foreach ($candidate in $candidates) {
    if (Test-PythonCandidate $candidate) {
        $selected = $candidate
        break
    }
}

if (-not $selected) {
    throw "Could not find a working Python runtime."
}

& $selected ".\evals\run_evals.py" "--offline"
