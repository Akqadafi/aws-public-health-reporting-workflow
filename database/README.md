# Workflow metadata database

`schema.sql` models reporting cycles, required datasets, submissions, validation runs, artifacts,
approvals, and audit events in PostgreSQL. It intentionally stores S3 references and workflow facts,
not participant rows.

The Terraform full-stack option creates an encrypted private RDS instance and stores its generated
credentials in Secrets Manager. Schema migration is intentionally a separate, reviewed deployment
step; Terraform does not execute SQL. For a real deployment, use a migration tool, give its role
time-limited access, and create separate least-privilege application and migration database roles.
