#!/usr/bin/env bash
set -euo pipefail

environment="${1:-dev}"
if [[ "${environment}" != "dev" && "${environment}" != "prod" ]]; then
  echo "Usage: $0 [dev|prod]" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
environment_dir="${repo_root}/terraform/environments/${environment}"

read -r -p "Type DESTROY-${environment} to destroy that environment: " confirmation
if [[ "${confirmation}" != "DESTROY-${environment}" ]]; then
  echo "Destroy cancelled."
  exit 1
fi

terraform -chdir="${environment_dir}" init -backend-config=backend.hcl
terraform -chdir="${environment_dir}" plan -destroy -out="destroy-${environment}.tfplan"
terraform -chdir="${environment_dir}" apply "destroy-${environment}.tfplan"
