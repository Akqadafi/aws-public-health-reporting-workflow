# AWS Public Health Reporting Workflow

> **One-sentence summary:** A portfolio-safe AWS workflow that replaces manual public-health file
> handling with secure direct uploads, deterministic validation, human review, de-identified
> reporting, and traceable operations.

[![Application CI](https://github.com/Akqadafi/aws-public-health-reporting-workflow/actions/workflows/application-ci.yml/badge.svg)](https://github.com/Akqadafi/aws-public-health-reporting-workflow/actions/workflows/application-ci.yml)
[![Terraform Plan](https://github.com/Akqadafi/aws-public-health-reporting-workflow/actions/workflows/terraform-plan.yml/badge.svg)](https://github.com/Akqadafi/aws-public-health-reporting-workflow/actions/workflows/terraform-plan.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![AWS public health reporting architecture](docs/architecture-diagram.png)

## Overview

Public-health reporting teams often work against recurring deadlines while receiving sensitive files
from several sources. Manual quality checks, shared folders, email approvals, and staff memory make it
difficult to answer basic operational questions: Which file version passed? What still needs review?
Who approved the output? Can the process recover from an overwrite or failed workflow?

This project reconstructs that operating model as a controlled AWS workflow:

- Staff use a simple internal portal instead of the AWS console.
- The browser uploads CSV files directly to encrypted S3 using a short-lived presigned URL.
- EventBridge and Step Functions coordinate validation, quarantine, transformation, and notification.
- Python applies deterministic cleanup rules but never guesses missing or contradictory identifiers.
- Passing records become de-identified aggregate reports; questionable records remain quarantined.
- Workflow metadata is separated from file content through a relational state model.
- Terraform, GitHub Actions, CloudWatch, CloudTrail, Versioning, backups, and runbooks make the process
  reviewable and recoverable.

### Portfolio reconstruction notice

This repository was created from a description of work completed in a former role. It contains no
employer source code, AWS state, credentials, screenshots, or participant data. Every sample record is
invented. It demonstrates the architecture and operating principles; it does not claim that this exact
repository was deployed by the former employer or that it constitutes a compliance certification.

### Outcomes demonstrated

- Repeatable pass/quarantine decisions with row-level error codes
- Safe normalization separated from human-owned data correction
- De-identified report output with a source-to-artifact lineage manifest
- Workflow state stored outside email threads and staff memory
- One validation contract shared by the local simulator and Lambda handlers
- Cost-bearing infrastructure disabled until explicitly requested

## Architecture

### High-Level Design

```text
Staff → React / CloudFront → FastAPI / Fargate → presigned S3 upload
                                                    ↓
S3 incoming → EventBridge → Step Functions → validation Lambda
                                                ├─ FAIL → S3 quarantine + error report
                                                └─ PASS → S3 validated → transform Lambda
                                                                            ↓
                                                                  S3 curated aggregate
                                                                            ↓
                                                           manager approval → archive
```

RDS tracks reporting-cycle and approval metadata. IAM/OIDC, private networking, KMS, Secrets Manager,
CloudWatch, SNS, CloudTrail, S3 Versioning, database backups, and runbooks support the workflow around
the data path. See [Architecture and design decisions](docs/architecture.md) and the editable
[diagram source](docs/architecture-diagram.svg).

### AWS Services Used

| Service | Purpose |
|---|---|
| IAM and OIDC | Role-based staff access and separated workload identities |
| VPC and security groups | Private Fargate/database tiers and explicit network paths |
| S3 | Incoming, quarantine, validated, curated, archive, frontend, and audit objects |
| CloudFront | HTTPS delivery from a private frontend bucket using Origin Access Control |
| AWS WAF | AWS-managed common protections for the CloudFront frontend |
| Application Load Balancer | HTTPS entry point for the API control plane |
| ECS Fargate | Containerized FastAPI service without host management |
| EventBridge | Starts processing when an object arrives under `incoming/` |
| Step Functions | Retry, failure handling, and pass/quarantine branching |
| Lambda | Python validation, normalization, and de-identified aggregation |
| RDS for PostgreSQL | Reporting-cycle, submission, validation, artifact, and approval metadata |
| KMS and Secrets Manager | Encryption keys and generated database credentials |
| CloudWatch and SNS | Technical failure alarms and operational notifications |
| CloudTrail | Multi-Region management events and S3 object data events |

## Repository Structure

```text
aws-public-health-reporting-workflow/
├── README.md
├── LICENSE
├── .pre-commit-config.yaml
├── application/
│   ├── backend/
│   │   ├── src/health_reporting/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── frontend/
│       ├── src/
│       └── package.json
├── database/
│   └── schema.sql
├── docs/
│   ├── architecture.md
│   ├── architecture-diagram.png
│   ├── architecture-diagram.svg
│   ├── security-and-privacy.md
│   ├── runbook.md
│   └── runbooks/
├── terraform/
│   ├── modules/reporting-platform/
│   └── environments/
│       ├── dev/
│       └── prod/
├── scripts/
│   ├── validate.sh / validate.ps1
│   ├── deploy.sh / deploy.ps1
│   └── cleanup.sh / cleanup.ps1
├── sample-data/
├── local-data/
├── tests/
└── .github/workflows/
    ├── application-ci.yml
    ├── terraform-plan.yml
    └── terraform-apply.yml
```

## Infrastructure as Code

Infrastructure is managed with Terraform `>= 1.10, < 2.0` and HashiCorp AWS provider `~> 6.0`.

- `terraform/modules/reporting-platform` is the reusable platform module.
- `terraform/environments/dev` and `prod` are separate root modules and state boundaries.
- Environment wrappers supply naming, tagging, cost, and data-protection defaults.
- Example S3 backend files use encryption and native state lockfiles; real backend settings stay ignored.
- Names combine project, environment, account, and Region where global uniqueness is required.
- Default tags identify project, environment, Terraform ownership, and synthetic data classification.

```text
terraform fmt → terraform validate → security scan → terraform plan → review → manual apply
```

The cohesive platform module is deliberately not split into tiny modules with dense cross-dependencies.
Its storage, workflow, frontend, monitoring, and optional control-plane files form clear future module
boundaries if ownership or release schedules diverge.

## CI/CD

GitHub Actions separates verification from deployment:

| Workflow | Trigger | Responsibility |
|---|---|---|
| `application-ci.yml` | Pull request, `main`, manual | Python lint/tests, structure contract, React build, API image build |
| `terraform-plan.yml` | Terraform-related pull request, manual | Format, validate dev/prod, Trivy IaC scan, optional authenticated dev plan |
| `terraform-apply.yml` | Manual only | OIDC authentication, reviewed plan, environment-gated apply |

The plan job runs when repository variable `AWS_ROLE_ARN` is configured. Apply additionally requires
`TF_STATE_BUCKET` and environment-specific application/identity variables. Configure `dev` and `prod`
as GitHub Environments and add required reviewers before enabling deployment.

## Security

- Least-privilege roles for EventBridge, Step Functions, Lambda, and ECS tasks
- OIDC token verification and analyst/manager role checks in protected API routes
- Short-lived presigned URLs scoped to a generated S3 key
- S3 Block Public Access, TLS-only bucket policies, Versioning, and KMS encryption
- CloudFront Origin Access Control for the private frontend origin
- AWS WAF managed common rules on the CloudFront distribution
- Fargate tasks in private application subnets and RDS in isolated database subnets
- Database ingress permitted only from the API security group
- Generated database credentials stored in Secrets Manager
- Step Functions execution payload logging disabled to reduce sensitive-data exposure
- GitHub-to-AWS authentication designed for OIDC rather than stored access keys
- Trivy configuration scanning and dependency lockfiles in CI

This is a control demonstration, not a HIPAA or regulatory attestation. Review
[Security and privacy notes](docs/security-and-privacy.md) before considering any real workload.

## Monitoring and Logging

- CloudWatch alarms detect Step Functions failures and unhandled Lambda errors.
- SNS provides the operations notification path and quarantine notices.
- Step Functions state history identifies the failed technical step without logging execution payloads.
- CloudTrail records multi-Region management activity and S3 object-level data events.
- CloudTrail log-file validation helps identify altered audit files.
- RDS backups, S3 Versioning, lineage manifests, and runbooks support recovery and reconciliation.

Deadline-risk evaluation and application-level service metrics are documented future additions; the
repository does not present them as already implemented.

## Deployment

### Prerequisites

- Git
- Python 3.11 or newer
- Node.js 22 and npm
- Terraform 1.10 or newer
- AWS CLI v2 with an approved AWS account/role
- Docker for the optional Fargate API image
- pre-commit (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/Akqadafi/aws-public-health-reporting-workflow.git
cd aws-public-health-reporting-workflow
```

### 2. Run the Zero-Cloud Demonstration

PowerShell:

```powershell
$env:PYTHONPATH="$PWD/application/backend/src"
python -m health_reporting.cli sample-data/valid-participants.csv
python -m health_reporting.cli sample-data/invalid-participants.csv
```

macOS/Linux:

```bash
export PYTHONPATH="$PWD/application/backend/src"
python -m health_reporting.cli sample-data/valid-participants.csv
python -m health_reporting.cli sample-data/invalid-participants.csv
```

Valid input reaches `validated`, `curated`, and `archive`; bad input stops in `quarantine`.
`local-data/workflow.db` holds operational state separately from the CSV content.

### 3. Configure AWS Authentication

Use a dedicated non-production account and synthetic data. Prefer IAM Identity Center:

```bash
aws configure sso
aws sts get-caller-identity
```

### 4. Configure Terraform State and Values

```bash
cd terraform/environments/dev
cp backend.hcl.example backend.hcl
cp terraform.tfvars.example terraform.tfvars
```

Replace all placeholders. The state bucket must already exist with Versioning, encryption, and
restricted access. Never commit `backend.hcl`, `terraform.tfvars`, state, plans, or credentials.

### 5. Initialize, Validate, and Plan

```bash
terraform init -backend-config=backend.hcl
terraform fmt -check
terraform validate
terraform plan -out=dev.tfplan
```

### 6. Deploy After Review

```bash
terraform apply dev.tfplan
```

The cross-platform scripts under `scripts/` wrap this flow with explicit confirmation. The full stack
requires an immutable API image URI, matching ACM certificate/custom DNS, and enterprise OIDC values.

## Testing

The test suite covers validation rules, safe normalization, duplicate and missing identifiers,
reporting-period checks, quarantine behavior, de-identified aggregation, lineage/state behavior, and
the professional repository structure contract.

Run the complete local verification:

```powershell
./scripts/validate.ps1
```

```bash
./scripts/validate.sh
```

Focused backend tests require no AWS account:

```bash
PYTHONPATH=application/backend/src python -m unittest discover -s application/backend/tests -v
python -m unittest discover -s tests -v
```

Install pre-commit hooks with `pre-commit install`; hooks run Python tests, the structure contract, and
Terraform formatting before commits.

## Failure Recovery and Operations

- Business-rule failures follow the [quarantined file runbook](docs/runbooks/quarantined-file.md).
- Unexpected Lambda or Step Functions failures follow the
  [workflow failure runbook](docs/runbooks/workflow-failure.md).
- S3 version or PostgreSQL recovery follows the [recovery runbook](docs/runbooks/recovery.md).
- [The runbook index](docs/runbook.md) defines incident priorities and evidence handling.

Recovery preserves the original object/version and restores to a new database instance before a
reviewed cutover. A backup is not considered reliable until restore and application reconciliation are
tested with synthetic data.

## Design Decisions

### Why AWS?

S3 event notifications, EventBridge, Step Functions, Lambda, Fargate, RDS, KMS, and CloudTrail map
directly to the required storage, coordination, compute, metadata, encryption, and audit boundaries.
Managed services reduce host administration while preserving explicit operational controls.

### Why Terraform?

Terraform makes networking, identities, encryption, retention, monitoring, and recovery settings
reviewable together. Separate environment roots reduce state blast radius and prevent manual console
configuration from becoming the undocumented source of truth.

### Why direct-to-S3 upload?

Presigned uploads avoid proxying entire participant files through the API container. The API controls
identity, authorization, key naming, and URL lifetime while S3 handles the data transfer.

### Why Lambda plus Fargate?

Short, event-driven file checks fit Lambda. The API needs longer-lived HTTP behavior, identity
integration, and database access, which fit Fargate. The full Fargate/RDS tier is opt-in because it is
also the major portfolio cost boundary.

### Why quarantine instead of automatic correction?

Whitespace, date representation, casing, and explicit yes/no variants are deterministic. Missing IDs,
duplicates, and contradictions require an authoritative human decision. Preserving the failed original
supports audit and reproducibility.

## Cost Considerations

Major cost drivers are NAT Gateway hours/data processing, the ALB, two Fargate tasks, RDS, CloudTrail
S3 data events, CloudWatch logs, KMS requests, and data transfer. The default dev configuration leaves
NAT, ALB, Fargate, and RDS disabled; validate with synthetic files before opting into the full stack.

Always check the current AWS Pricing Calculator and the Terraform plan. For teardown:

```bash
./scripts/cleanup.sh dev
```

Protected RDS and non-empty buckets intentionally prevent casual destruction. Review retention,
snapshots, and object versions before changing those safeguards.

## Future Improvements

- Implement PostgreSQL migrations and connect the API repository adapter to the included schema
- Complete enterprise OIDC login in the React portal and manager approval screens
- Add malware/content scanning, upload-size enforcement, and application rate limits
- Evaluate deadlines and unresolved errors as custom operational metrics
- Add integration tests using an isolated AWS account and synthetic fixtures
- Add policy-as-code, automated cost estimation, and drift detection to pull requests
- Use separate AWS accounts for dev/prod and a centralized organization audit archive
- Add cross-Region disaster recovery only after defined RPO/RTO justify the added cost

## What This Project Demonstrates

- AWS event-driven architecture and managed-service tradeoffs
- Terraform modules, environment separation, remote-state design, and tagging
- GitHub Actions validation, security scanning, planning, approval, and deployment design
- IAM least privilege, OIDC federation, private networking, encryption, and secrets management
- Python data validation, safe normalization, testing, and de-identification
- CloudWatch monitoring, CloudTrail audit, S3 recovery, RDS backups, and operational runbooks
- Clear separation of production claims, implemented controls, and documented extension points

## Documentation

- [Architecture](docs/architecture.md)
- [Architecture diagram](docs/architecture-diagram.png)
- [Security and privacy](docs/security-and-privacy.md)
- [Runbook index](docs/runbook.md)
- [Portfolio walkthrough](docs/portfolio-walkthrough.md)
- [Terraform guide](terraform/README.md)

## Author

**Ahmad Qadafi** — Cloud / DevOps Engineer

- GitHub: [@Akqadafi](https://github.com/Akqadafi)
