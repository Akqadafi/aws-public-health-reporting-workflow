#!/usr/bin/env bash
set -euo pipefail

environment="${1:-dev}"
if [[ "${environment}" != "dev" && "${environment}" != "prod" ]]; then
  echo "Usage: $0 [dev|prod]" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
environment_dir="${repo_root}/terraform/environments/${environment}"

terraform -chdir="${environment_dir}" init -backend-config=backend.hcl
terraform -chdir="${environment_dir}" fmt -check
terraform -chdir="${environment_dir}" validate
terraform -chdir="${environment_dir}" plan -out="${environment}.tfplan"

read -r -p "Type APPLY-${environment} to apply the reviewed plan: " confirmation
if [[ "${confirmation}" != "APPLY-${environment}" ]]; then
  echo "Apply cancelled."
  exit 1
fi

terraform -chdir="${environment_dir}" apply "${environment}.tfplan"
