-- Workflow metadata only. Participant-level rows remain in encrypted S3 objects.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE cycle_status AS ENUM (
  'DRAFT', 'ACCEPTING_FILES', 'VALIDATION_BLOCKED', 'READY_FOR_APPROVAL',
  'APPROVED', 'SUBMITTED', 'CLOSED'
);
CREATE TYPE submission_status AS ENUM (
  'RECEIVED', 'VALIDATING', 'QUARANTINED', 'VALIDATED', 'SUPERSEDED'
);

CREATE TABLE reporting_cycles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_code varchar(40) UNIQUE NOT NULL,
  period_start date NOT NULL,
  period_end date NOT NULL,
  due_at timestamptz NOT NULL,
  status cycle_status NOT NULL DEFAULT 'DRAFT',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (period_start <= period_end)
);

CREATE TABLE required_datasets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_id uuid NOT NULL REFERENCES reporting_cycles(id) ON DELETE RESTRICT,
  dataset_code varchar(40) NOT NULL,
  display_name varchar(120) NOT NULL,
  UNIQUE (cycle_id, dataset_code)
);

CREATE TABLE file_submissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  required_dataset_id uuid NOT NULL REFERENCES required_datasets(id) ON DELETE RESTRICT,
  s3_bucket text NOT NULL,
  s3_object_key text NOT NULL,
  s3_version_id text,
  submitted_by text NOT NULL,
  submitted_at timestamptz NOT NULL DEFAULT now(),
  status submission_status NOT NULL DEFAULT 'RECEIVED',
  UNIQUE (s3_bucket, s3_object_key, s3_version_id)
);

CREATE TABLE validation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id uuid NOT NULL REFERENCES file_submissions(id) ON DELETE RESTRICT,
  step_functions_execution_arn text UNIQUE NOT NULL,
  rule_set_version varchar(40) NOT NULL,
  error_count integer NOT NULL DEFAULT 0 CHECK (error_count >= 0),
  warning_count integer NOT NULL DEFAULT 0 CHECK (warning_count >= 0),
  safe_correction_count integer NOT NULL DEFAULT 0 CHECK (safe_correction_count >= 0),
  error_report_key text,
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE TABLE report_artifacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_id uuid NOT NULL REFERENCES reporting_cycles(id) ON DELETE RESTRICT,
  s3_object_key text NOT NULL,
  source_manifest_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE approvals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  report_artifact_id uuid NOT NULL REFERENCES report_artifacts(id) ON DELETE RESTRICT,
  decision varchar(20) NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED')),
  decided_by text NOT NULL,
  decided_at timestamptz NOT NULL DEFAULT now(),
  comment text
);

CREATE TABLE workflow_audit_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cycle_id uuid REFERENCES reporting_cycles(id) ON DELETE RESTRICT,
  actor_subject text NOT NULL,
  event_type varchar(80) NOT NULL,
  resource_type varchar(80) NOT NULL,
  resource_id text NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  correlation_id uuid NOT NULL DEFAULT gen_random_uuid(),
  details jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX file_submissions_dataset_status_idx
  ON file_submissions (required_dataset_id, status, submitted_at DESC);
CREATE INDEX workflow_audit_cycle_time_idx
  ON workflow_audit_events (cycle_id, occurred_at DESC);

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
