# Portfolio walkthrough

## 60-second version

Staff use a portal and receive a short-lived S3 upload URL, so participant files do not pass through
the application server. S3 sends the upload event through EventBridge to Step Functions. Python checks
schema, missing or duplicate identifiers, dates, reporting-window boundaries, codes, and controlled
values. Only deterministic formatting issues are corrected. Questionable data and a precise error
report go to quarantine; passing rows are standardized and reduced to a de-identified aggregate.
Operational status is separate from file content. IAM, KMS, private networking, secrets, audit,
monitoring, versioning, backups, Terraform, and runbooks support the workflow around that core.

## What to demonstrate live

1. Run the valid synthetic CSV and open its curated report and lineage manifest.
2. Run the invalid CSV and show the error codes and lack of curated output.
3. Query or describe `local-data/workflow.db` to show state is not stored in a person's memory.
4. Show that local execution and Lambda import the same validator.
5. Walk through the Step Functions Choice branch and prefix-scoped IAM policy.
6. Explain why `enable_full_stack` is off by default and what remains environment-specific.

## Defensible language

Say “I reconstructed this portfolio repository from the architecture and operating model I worked
on.” Do not imply that employer code, production Terraform, data, screenshots, account configuration,
or compliance evidence are present. Be specific about which parts run locally, which are validated
Terraform, and which are extension points.
