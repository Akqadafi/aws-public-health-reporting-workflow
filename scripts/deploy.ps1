param(
    [ValidateSet('dev', 'prod')]
    [string]$Environment = 'dev'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$environmentDirectory = Join-Path $repoRoot "terraform/environments/$Environment"

function Invoke-Terraform {
    param([string[]]$ArgumentList)

    terraform "-chdir=$environmentDirectory" @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Terraform failed with exit code $LASTEXITCODE."
    }
}

Invoke-Terraform -ArgumentList @('init', '-backend-config=backend.hcl')
Invoke-Terraform -ArgumentList @('fmt', '-check')
Invoke-Terraform -ArgumentList @('validate')
Invoke-Terraform -ArgumentList @('plan', "-out=$Environment.tfplan")

$confirmation = Read-Host "Type APPLY-$Environment to apply the reviewed plan"
if ($confirmation -cne "APPLY-$Environment") {
    throw 'Apply cancelled.'
}

Invoke-Terraform -ArgumentList @('apply', "$Environment.tfplan")
