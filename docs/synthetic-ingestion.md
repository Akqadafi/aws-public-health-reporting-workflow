# Synthetic multi-program ingestion examples

This repository includes five invented staff-report profiles that demonstrate the kinds of files a
public-health reporting team may receive. Their structure was informed by broad operational patterns
such as form-response exports, monthly activity reports, participant demographic records, and
cross-program summaries. No source record, person, organization, location, narrative, or reported
figure was copied into these examples.

All examples use fictional identifiers, generic site codes, invented narratives, and invented counts.
They are portfolio fixtures only and must never be mixed with real participant information.

## Included report profiles

| Dataset key | Staff-report pattern | Cleaned output | Transformed output |
|---|---|---|---|
| `health-education-demographics` | Participant demographics and interests | Standardized internal rows plus ZIP3 | Counts by month, program, and age group |
| `case-management-activity` | Monthly home visits, participants, screenings, and referrals | Standardized monthly rows | One canonical row per metric |
| `behavioral-health-activity` | Monthly referrals, appointments, groups, and telehealth | Standardized monthly rows | One canonical row per metric |
| `outreach-activity` | Monthly events, referrals, enrollments, partners, and contacts | Standardized counts and narrative | Metrics only; narrative is excluded |
| `father-engagement-activity` | Monthly visits, referrals, enrollment, and education | Standardized counts and narratives | Metrics only; narratives are excluded |

Each profile has a `-valid.csv` and `-invalid.csv` file under
`sample-data/synthetic-staff-reports/`. Invalid examples deliberately contain problems such as
negative counts, non-numeric counts, duplicate submission IDs, invalid months, unknown codes, and
unsafe demographic values.

## What the Python cleaner changes safely

The cleaner may:

- trim extra spaces and collapse repeated whitespace;
- convert report months such as `April 2026` or `04/2026` to `2026-04`;
- convert dates to `YYYY-MM-DD`;
- standardize site, program, and category codes to uppercase underscore form;
- convert whole-number text such as `"1,025"` to `1025`;
- sort multi-select interest values into a stable order;
- derive ZIP3 for controlled internal use.

The cleaner does not guess missing identifiers, unknown categories, impossible dates, fractional
people, negative counts, or unsupported selections. Those rows produce explicit validation errors and
the file receives `QUARANTINED` status.

## What transformation removes

The transformed demographic report contains no submission ID, participant ID, full ZIP code,
submission timestamp, or exact service date. Monthly program transformations exclude submission IDs
and staff narratives. They use the shared shape:

```text
report_month,dataset,site_code,metric,value
```

These controls reduce exposure but are not a complete production privacy program. Real releases would
also need organization-approved small-cell suppression, access controls, retention rules, and disclosure
review.

## Run one valid example

From the repository root, point Python at the backend code.

PowerShell:

```powershell
$env:PYTHONPATH="$PWD/application/backend/src"
python -m health_reporting.portfolio_cli `
  outreach-activity `
  sample-data/synthetic-staff-reports/outreach-activity-valid.csv
```

macOS/Linux:

```bash
export PYTHONPATH="$PWD/application/backend/src"
python3 -m health_reporting.portfolio_cli \
  outreach-activity \
  sample-data/synthetic-staff-reports/outreach-activity-valid.csv
```

The JSON response should say `"status": "TRANSFORMED"`. Look under
`portfolio-output/outreach-activity/` for:

- a validation report;
- a cleaned CSV that keeps the internal staff-report structure;
- a transformed CSV containing canonical metrics only.

## Prove quarantine behavior

PowerShell:

```powershell
python -m health_reporting.portfolio_cli `
  outreach-activity `
  sample-data/synthetic-staff-reports/outreach-activity-invalid.csv
```

macOS/Linux:

```bash
python3 -m health_reporting.portfolio_cli \
  outreach-activity \
  sample-data/synthetic-staff-reports/outreach-activity-invalid.csv
```

The response should say `"status": "QUARANTINED"` and list the unsafe fields. A quarantined file does
not receive a transformed output.

## Run the other profiles

Replace the dataset key and filename with one of these matching pairs:

```text
health-education-demographics  health-education-demographics-valid.csv
case-management-activity       case-management-activity-valid.csv
behavioral-health-activity     behavioral-health-activity-valid.csv
father-engagement-activity     father-engagement-activity-valid.csv
```

The dataset key is explicit on purpose. The program refuses to guess a schema from a filename or from
ambiguous columns.

## Supported file format

The demonstration accepts CSV text. Real-world Excel or Google Forms workbooks should be exported to a
reviewed CSV contract before upload. A file named `.xls` may actually contain CSV text; a production
intake layer should inspect content type instead of trusting the extension. Binary `.xlsx` ingestion
would require an explicitly packaged and tested parser and is not claimed by this repository.

## Python implementation

- `portfolio_ingestion.py` defines every schema, normalization rule, validation error, and transform.
- `portfolio_cli.py` writes validation reports plus cleaned and transformed artifacts.
- `test_portfolio_ingestion.py` proves all five valid files transform, all five invalid files fail,
  identifiers and narratives do not enter transformed outputs, and unknown schemas are not guessed.
