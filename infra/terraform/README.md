# Terraform deployment

This configuration has two deliberate cost tiers.

## Default data plane

With `enable_full_stack = false` (the default), Terraform creates:

- private, versioned, KMS-encrypted S3 data storage;
- S3 object events through EventBridge;
- Step Functions orchestration and two Python Lambda functions;
- an SNS operations topic and CloudWatch failure alarms;
- a multi-Region CloudTrail with S3 object data events and log validation;
- a private S3 frontend origin and CloudFront Origin Access Control when enabled.

The React build is not uploaded automatically. After `terraform apply`, build `frontend/` and sync
`frontend/dist/` to the `frontend_bucket` output. This separation avoids using Terraform as a build
or artifact-deployment tool.

## Opt-in full control plane

`enable_full_stack = true` additionally creates cost-bearing resources:

- a VPC spanning two Availability Zones;
- public ALB subnets, private Fargate subnets, and isolated RDS subnets;
- one NAT Gateway for the demo (a production availability design would normally use one per AZ);
- an HTTPS Application Load Balancer and two Fargate tasks;
- encrypted PostgreSQL RDS with backups and optional deletion protection;
- a generated database secret in Secrets Manager.

It requires `api_image_uri` and `alb_certificate_arn`. The application also requires valid
`oidc_issuer` and `oidc_audience` values before protected endpoints can be used. The certificate's
DNS name must resolve to the ALB; the raw AWS ALB hostname generally will not match it.

## Safe deployment sequence

1. Use a dedicated non-production AWS account and synthetic data only.
2. Copy `terraform.tfvars.example` to the ignored `terraform.tfvars`.
3. Run `terraform init`, `terraform fmt -check -recursive`, and `terraform validate`.
4. Save and review a plan: `terraform plan -out=portfolio.tfplan`.
5. Apply only after checking current AWS prices, quotas, naming, identity, certificate, and retention.
6. Create `configuration/cycles/<cycle-id>.json` in the data bucket before uploading files.
7. Confirm the optional SNS email subscription and test both pass and quarantine paths.

Example cycle configuration:

```json
{
  "cycle_id": "2026-Q2",
  "period_start": "2026-04-01",
  "period_end": "2026-06-30",
  "required_datasets": ["participant-outcomes"]
}
```

## Important limitations

- This is a reference environment, not a HIPAA compliance attestation.
- The RDS schema is not auto-applied and the demo API does not yet use the PostgreSQL adapter.
- A custom domain, WAF policy, enterprise IdP registration, VPC endpoints, cross-account log archive,
  AWS Backup plan, and multi-AZ database are production hardening decisions, not hidden defaults.
- Destroy may intentionally stop on protected RDS or non-empty buckets. Preserve or explicitly handle
  data before changing those safeguards.
