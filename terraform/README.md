# Terraform infrastructure

```text
terraform/
├── modules/
│   └── reporting-platform/   # Reusable AWS platform module
└── environments/
    ├── dev/                  # Low-cost validation/default deployment
    └── prod/                 # Production-style values and protected data settings
```

Each environment is an independent Terraform root module and state boundary. Copy both example
configuration files before a real deployment:

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
cp backend.hcl.example backend.hcl
terraform init -backend-config=backend.hcl
terraform validate
terraform plan
```

`backend.hcl` and `terraform.tfvars` are ignored because they contain account-specific settings.
Create the state bucket separately with Versioning, encryption, restricted access, and the native S3
lockfile option. CI initializes with `-backend=false` for formatting and static validation.

## Environments

- **dev:** Frontend and event-driven workflow by default; deletion protection is off for synthetic
  demonstrations.
- **prod:** The checked-in example opts into the full stack and protected data settings, but requires
  an immutable API image, ACM certificate, enterprise OIDC values, and operations email.

The repository never applies automatically on push. `terraform-apply.yml` is manually dispatched and
targets a GitHub Environment so deployment approval and AWS OIDC permissions can be configured outside
the code.
