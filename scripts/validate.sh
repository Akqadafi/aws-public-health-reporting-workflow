#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PYTHONPATH="${repo_root}/application/backend/src"
python -m unittest discover -s "${repo_root}/application/backend/tests" -v
python -m unittest discover -s "${repo_root}/tests" -v

npm --prefix "${repo_root}/application/frontend" ci
npm --prefix "${repo_root}/application/frontend" run build

terraform -chdir="${repo_root}/terraform" fmt -check -recursive
for environment in dev prod; do
  terraform -chdir="${repo_root}/terraform/environments/${environment}" init -backend=false -input=false
  terraform -chdir="${repo_root}/terraform/environments/${environment}" validate
done
