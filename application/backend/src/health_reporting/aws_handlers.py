"""AWS Lambda entry points for the event-driven data plane."""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import date
from urllib.parse import unquote_plus

import boto3

from health_reporting.reporting import aggregate_rows, aggregate_to_csv
from health_reporting.validation import rows_to_csv, validate_csv


def _s3():
    return boto3.client("s3")


def _event_location(event: dict) -> tuple[str, str]:
    detail = event.get("detail", event)
    bucket = detail.get("bucket", {})
    object_detail = detail.get("object", {})
    bucket_name = bucket.get("name") if isinstance(bucket, dict) else bucket
    object_key = object_detail.get("key") if isinstance(object_detail, dict) else object_detail
    if not bucket_name or not object_key:
        raise ValueError("Event must contain detail.bucket.name and detail.object.key")
    return str(bucket_name), unquote_plus(str(object_key))


def _cycle_id_from_key(key: str) -> str:
    parts = key.split("/")
    if len(parts) < 3 or parts[0] != "incoming":
        raise ValueError("Incoming key must use incoming/{cycle_id}/{filename}")
    return parts[1]


def _reporting_period(client, bucket: str, cycle_id: str) -> tuple[date, date]:
    try:
        response = client.get_object(Bucket=bucket, Key=f"configuration/cycles/{cycle_id}.json")
        configuration = json.loads(response["Body"].read())
        return date.fromisoformat(configuration["period_start"]), date.fromisoformat(
            configuration["period_end"]
        )
    except client.exceptions.NoSuchKey:
        start = os.environ.get("DEFAULT_PERIOD_START")
        end = os.environ.get("DEFAULT_PERIOD_END")
        if not start or not end:
            raise ValueError(
                f"No reporting-period configuration found for cycle '{cycle_id}'"
            ) from None
        return date.fromisoformat(start), date.fromisoformat(end)


def validate_handler(event: dict, _context: object) -> dict:
    """Validate an incoming object and route failures to quarantine."""
    client = _s3()
    bucket, key = _event_location(event)
    cycle_id = _cycle_id_from_key(key)
    period_start, period_end = _reporting_period(client, bucket, cycle_id)
    response = client.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8-sig")
    result = validate_csv(content, period_start, period_end)
    file_name = key.rsplit("/", 1)[-1]
    run_id = response.get("VersionId") or response.get("ETag", "run").strip('"')
    base_output = {
        "bucket": bucket,
        "cycle_id": cycle_id,
        "run_id": run_id,
        "source_key": key,
        "error_count": result.error_count,
        "safe_corrections": result.corrections,
    }
    report = {
        **base_output,
        "status": "PASS" if result.passed else "FAIL",
        "issues": [issue.as_dict() for issue in result.issues],
    }

    if not result.passed:
        prefix = f"quarantine/{cycle_id}/{run_id}"
        quarantine_key = f"{prefix}/{file_name}"
        client.copy_object(
            Bucket=bucket,
            Key=quarantine_key,
            CopySource={"Bucket": bucket, "Key": key},
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId=os.environ["KMS_KEY_ARN"],
        )
        report_key = f"{prefix}/validation-report.json"
        client.put_object(
            Bucket=bucket,
            Key=report_key,
            Body=(json.dumps(report, indent=2) + "\n").encode(),
            ContentType="application/json",
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId=os.environ["KMS_KEY_ARN"],
        )
        return {**base_output, "status": "FAIL", "report_key": report_key}

    validated_key = f"validated/{cycle_id}/{run_id}.csv"
    client.put_object(
        Bucket=bucket,
        Key=validated_key,
        Body=rows_to_csv(result.cleaned_rows).encode(),
        ContentType="text/csv",
        ServerSideEncryption="aws:kms",
        SSEKMSKeyId=os.environ["KMS_KEY_ARN"],
    )
    report_key = f"validated/{cycle_id}/{run_id}.validation.json"
    client.put_object(
        Bucket=bucket,
        Key=report_key,
        Body=(json.dumps(report, indent=2) + "\n").encode(),
        ContentType="application/json",
        ServerSideEncryption="aws:kms",
        SSEKMSKeyId=os.environ["KMS_KEY_ARN"],
    )
    return {
        **base_output,
        "status": "PASS",
        "validated_key": validated_key,
        "report_key": report_key,
    }


def transform_handler(event: dict, _context: object) -> dict:
    """Transform validated participant rows into a de-identified aggregate."""
    client = _s3()
    bucket = event["bucket"]
    validated_key = event["validated_key"]
    response = client.get_object(Bucket=bucket, Key=validated_key)
    rows = list(csv.DictReader(io.StringIO(response["Body"].read().decode("utf-8-sig"))))
    aggregate = aggregate_rows(rows)
    curated_key = f"curated/{event['cycle_id']}/{event['run_id']}-summary.csv"
    client.put_object(
        Bucket=bucket,
        Key=curated_key,
        Body=aggregate_to_csv(aggregate).encode(),
        ContentType="text/csv",
        ServerSideEncryption="aws:kms",
        SSEKMSKeyId=os.environ["KMS_KEY_ARN"],
    )
    return {
        **event,
        "status": "AWAITING_APPROVAL",
        "curated_key": curated_key,
        "aggregate_row_count": len(aggregate),
        "contains_participant_identifiers": False,
    }
