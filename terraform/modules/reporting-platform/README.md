# Reporting platform Terraform module

This cohesive module contains the portfolio platform's shared AWS resources. The `dev` and `prod`
root modules call it with environment-specific values and remote-state configuration.

## Resource groups

| File | Responsibility |
|---|---|
| `storage.tf` | KMS-encrypted, versioned workflow bucket and event notifications |
| `workflow.tf` | Lambda packaging, Step Functions, EventBridge, SNS, and IAM |
| `frontend.tf` | KMS-encrypted frontend origin, CloudFront OAC, and AWS WAF managed rules |
| `audit_monitoring.tf` | CloudTrail, audit-log bucket, CloudWatch alarms |
| `full_stack.tf` | Opt-in VPC, ALB, ECS Fargate, Secrets Manager, and PostgreSQL RDS |

The module stays cohesive because these resources share bucket, key, workflow, and identity outputs.
If separate teams or release cadences emerge, the file groups are ready to become smaller modules.

## Cost boundary

`enable_full_stack` defaults to `false`. The default path demonstrates the event-driven data plane;
NAT Gateway, ALB, Fargate, and RDS are created only after an explicit opt-in and the required image
and certificate inputs are supplied.

Do not run this directory directly. Use `terraform/environments/dev` or
`terraform/environments/prod`.
