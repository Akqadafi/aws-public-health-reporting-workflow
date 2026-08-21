# Operations runbook index

Use the procedure that matches the observed condition:

| Condition | Runbook |
|---|---|
| A file fails business validation and is intentionally quarantined | [Quarantined file](runbooks/quarantined-file.md) |
| Step Functions or Lambda fails unexpectedly | [Workflow failure](runbooks/workflow-failure.md) |
| A file version or workflow database state must be restored | [Recovery](runbooks/recovery.md) |

## Incident priorities

1. Protect participant data and preserve evidence.
2. Distinguish expected business-rule rejection from technical failure.
3. Stop unsafe or duplicate processing when integrity is uncertain.
4. Recover from immutable source versions and approved backups.
5. Reconcile workflow state, document decisions, and improve the control that failed.

All exercises in this portfolio repository must use synthetic data. Do not copy validation reports,
participant rows, credentials, or production screenshots into tickets or this repository.
