# Runbook: workflow execution failure

## Trigger

The `ExecutionsFailed` or Lambda `Errors` CloudWatch alarm enters ALARM, or an expected execution does
not reach a terminal business state.

## Triage

1. Record the alarm, state-machine execution ARN, cycle, object key/version, and correlation time.
2. Distinguish a business validation failure (`QUARANTINED`) from a technical execution failure.
   Quarantine is expected workflow behavior and uses the quarantine runbook.
3. Inspect Step Functions state history. Execution input logging is disabled; access the source object
   only if your role and incident need require it.
4. Check Lambda errors/throttles/duration, S3 access-denied events, KMS key status, EventBridge target
   failures, service health, quotas, and recent deployments.
5. Contain unsafe processing by disabling the EventBridge rule if there is evidence of corruption or
   runaway execution. Record and review that operational change.

## Recovery

1. Correct the infrastructure, permissions, code, or service condition through the reviewed change path.
2. Start a new execution with the original S3 bucket, key, and version. Do not overwrite the input.
3. Verify exactly one expected validated/quarantine result and reconcile workflow metadata.
4. Confirm alarms return to OK and no later submissions were skipped.
5. Document cause, impact, recovery evidence, and any monitoring or runbook change.
