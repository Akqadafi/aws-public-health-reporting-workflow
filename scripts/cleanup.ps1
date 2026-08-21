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

$confirmation = Read-Host "Type DESTROY-$Environment to destroy that environment"
if ($confirmation -cne "DESTROY-$Environment") {
    throw 'Destroy cancelled.'
}

Invoke-Terraform -ArgumentList @('init', '-backend-config=backend.hcl')
Invoke-Terraform -ArgumentList @('plan', '-destroy', "-out=destroy-$Environment.tfplan")
Invoke-Terraform -ArgumentList @('apply', "destroy-$Environment.tfplan")
