$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory)]
        [string]$Executable,
        [string[]]$ArgumentList
    )

    & $Executable @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable failed with exit code $LASTEXITCODE."
    }
}

$env:PYTHONPATH = Join-Path $repoRoot 'application/backend/src'
Invoke-CheckedCommand -Executable 'python' -ArgumentList @(
    '-m', 'unittest', 'discover', '-s',
    (Join-Path $repoRoot 'application/backend/tests'), '-v'
)
Invoke-CheckedCommand -Executable 'python' -ArgumentList @(
    '-m', 'unittest', 'discover', '-s', (Join-Path $repoRoot 'tests'), '-v'
)

$frontendRoot = Join-Path $repoRoot 'application/frontend'
Invoke-CheckedCommand -Executable 'npm.cmd' -ArgumentList @('--prefix', $frontendRoot, 'ci')
Invoke-CheckedCommand -Executable 'npm.cmd' -ArgumentList @('--prefix', $frontendRoot, 'run', 'build')

$terraformRoot = Join-Path $repoRoot 'terraform'
Invoke-CheckedCommand -Executable 'terraform' -ArgumentList @(
    "-chdir=$terraformRoot", 'fmt', '-check', '-recursive'
)
foreach ($environment in @('dev', 'prod')) {
    $directory = Join-Path $repoRoot "terraform/environments/$environment"
    Invoke-CheckedCommand -Executable 'terraform' -ArgumentList @(
        "-chdir=$directory", 'init', '-backend=false', '-input=false'
    )
    Invoke-CheckedCommand -Executable 'terraform' -ArgumentList @(
        "-chdir=$directory", 'validate'
    )
}
