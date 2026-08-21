# Runbook: data or state recovery

## S3 object recovery

1. Identify bucket, key, expected version, last known good time, and business owner.
2. Review CloudTrail object events and S3 versions; do not delete the current version during diagnosis.
3. Restore by copying the approved prior version to a new version of the intended key, preserving both.
4. Re-run validation and compare the new lineage manifest with the recovery request.

## PostgreSQL recovery

1. Declare the incident and stop state-changing application actions if consistency is uncertain.
2. Select a point before the unwanted change using RDS automated backups/PITR evidence.
3. Restore to a **new** RDS instance; never restore over the only copy.
4. Validate schema, cycle counts, submission state, approval history, and references to existing S3
   versions with authorized business and technical reviewers.
5. Cut over through a reviewed secret/endpoint change or extract only the approved records.
6. Retain incident evidence and remove temporary recovery resources under the retention procedure.

## Exercise expectations

Run a synthetic restore exercise on a schedule. Record measured RPO/RTO, gaps, owners, and follow-up
changes. A backup is not considered reliable until restore and application reconciliation are tested.
