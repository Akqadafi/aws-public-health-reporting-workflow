# Runbook: quarantined reporting file

## Trigger

An analyst receives a quarantine notification or sees a submission in `QUARANTINED` state.

## Procedure

1. Confirm the reporting cycle, dataset, run ID, S3 object version, and validation timestamp.
2. Open the JSON error report through the authorized application path; do not paste it into email,
   chat, tickets, or an unapproved workstation location.
3. Group errors by rule and row. Determine whether the source system or export process owns each fix.
4. Correct the authoritative source. Do not edit the quarantined copy or silently patch curated data.
5. Export a new file and upload it as a new submission. Preserve the failed version for lineage.
6. Confirm the new Step Functions execution completes and the submission becomes validated.
7. If the same systematic error repeats, open a controlled rule/export defect with non-sensitive
   evidence and assess whether other cycles are affected.

## Escalate when

- The error report or notification contains more participant data than needed.
- A missing identifier, duplicate, or contradiction cannot be resolved from an authoritative source.
- The deadline is at risk, the rule appears incorrect, or repeated uploads fail unexpectedly.
- An object is absent, unreadable, or appears to have been changed outside the normal workflow.

## Evidence to retain

Run ID, cycle, dataset, S3 version IDs, rule-set version, error counts, correction owner, resubmission
run ID, decision timestamps, and links to approved incident/change records. Do not duplicate row data.
