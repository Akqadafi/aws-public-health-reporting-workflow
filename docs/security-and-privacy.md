# Security and privacy notes

This repository demonstrates security controls; it does not by itself make a workload compliant with
HIPAA, 42 CFR Part 2, a state privacy law, or an organization's policy. Compliance depends on account
configuration, contracts, risk analysis, operations, people, and evidence in addition to code.

## Demonstrated controls

- Synthetic-only committed data and de-identified aggregate output
- KMS encryption with rotation for workflow data and RDS
- S3 Block Public Access, Bucket Owner Enforced, TLS-only bucket policy, and Versioning
- Private Fargate and database subnets with security-group-to-security-group rules
- OIDC token verification and role checks on protected API actions
- Short-lived, key-specific presigned upload URLs
- Secrets Manager resource for generated database credentials
- Step Functions execution data excluded from logs
- CloudTrail management events, S3 object data events, and log-file validation
- Least-privilege roles separated for Lambda, Step Functions, EventBridge, and ECS tasks

## Before any real use

- Execute a formal data classification and threat model.
- Use an eligible account and services under the required agreements.
- Replace synthetic validation rules with reviewed business rules and test fixtures.
- Register the enterprise IdP, constrain token claims, and test revocation and role changes.
- Add WAF/rate limits, organization log archive, GuardDuty/Security Hub controls as appropriate.
- Decide retention, legal hold, deletion, key administration, break-glass access, and evidence handling.
- Add malware/content scanning and enforce upload size limits before processing untrusted files.
- Keep identifiers out of metrics, traces, exception messages, SNS messages, and support tickets.
- Exercise restore procedures and measure recovery time and recovery point objectives.

## Repository hygiene

Never commit `.env`, `terraform.tfvars`, state files, provider caches, generated Lambda ZIPs, real
exports, credentials, screenshots containing records, or copied employer materials. Run a secret
scanner in the GitHub repository and require pull-request review for infrastructure changes.
