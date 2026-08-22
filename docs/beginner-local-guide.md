# Complete beginner guide: run locally and deploy with Terraform

This guide starts at the very beginning. Part 1 runs entirely on your computer and does not need an
AWS account. Part 2 creates the portfolio environment in a real AWS account with Terraform and then
uses the AWS command-line interface (CLI) to prove that the deployed workflow works. Always use
invented records, never real health or participant data.

## What you are about to do

Think of the repository as a project folder containing instructions, Python code, test data, and
documentation. You will:

1. Copy the repository from GitHub onto your computer.
2. Open a terminal inside the copied folder.
3. Tell Python where the project code lives.
4. Run the original good and bad participant samples.
5. Inspect the folders created by the original workflow.
6. Run five different kinds of invented staff reports.
7. Inspect cleaned, de-identified, and quarantined results.
8. Run the automated tests.
9. Optionally create the AWS environment with Terraform.
10. Use AWS CLI commands to prove the cloud workflow works.
11. Destroy the practice environment when you are finished.

The local demonstration is free. It does not contact AWS, create cloud resources, or contain real
participant information.

## A few useful words

- **Repository, or repo:** the complete project folder.
- **Terminal:** a window where you type commands. Windows users can use PowerShell. macOS and Linux
  users can use Terminal.
- **Command:** one instruction typed into the terminal.
- **Current folder:** the folder the terminal is working inside right now.
- **CSV:** a plain-text spreadsheet file whose values are separated by commas.
- **Synthetic data:** invented information that does not describe real people.

## Step 1: install the two required tools

### Git

Git downloads the repository and helps you get future updates.

1. Download Git from [git-scm.com/downloads](https://git-scm.com/downloads).
2. Run the installer.
3. The normal default choices are fine for this project.

You can skip Git if you plan to use the ZIP download method in Step 2.

### Python

This project requires Python 3.11 or newer.

1. Download Python from [python.org/downloads](https://www.python.org/downloads/).
2. On Windows, select **Add Python to PATH** when the installer offers that choice.
3. Finish the installation.

Open PowerShell or Terminal and check the installation:

```text
python --version
```

You should see Python 3.11 or a larger number, such as Python 3.13. On Windows, try this if the first
command is not recognized:

```powershell
py --version
```

If `py` works but `python` does not, replace `python` with `py` in the Windows commands below.

## Step 2: copy the repository to your computer

Choose either the Git method or the ZIP method. You do not need to do both.

### Choice A: clone with Git

Open PowerShell or Terminal. Move to a place where you keep projects. This example uses the Documents
folder:

```text
cd "$HOME/Documents"
```

Clone the repository:

```text
git clone https://github.com/Akqadafi/aws-public-health-reporting-workflow.git
```

If the repository is private, GitHub may open a browser and ask you to sign in. Your GitHub account
must have permission to view the repository.

Enter the new project folder:

```text
cd aws-public-health-reporting-workflow
```

### Choice B: download a ZIP file

1. Open the repository page in GitHub.
2. Select the green **Code** button.
3. Select **Download ZIP**.
4. Find the downloaded ZIP file.
5. Extract it into your Documents folder.
6. Open PowerShell or Terminal inside the extracted folder.

ZIP downloads are snapshots. They do not support `git pull`; download a new ZIP when you want a newer
copy.

## Step 3: make sure the terminal is in the project root

The **project root** is the folder containing `README.md`, `application`, `docs`, and `sample-data`.

On Windows PowerShell, list the current folder:

```powershell
Get-ChildItem
```

On macOS or Linux:

```bash
ls
```

If you do not see `README.md`, you are probably in the wrong folder. Use `cd` to move into
`aws-public-health-reporting-workflow` before continuing.

## Step 4: point Python at the project code

This setting lasts only for the current terminal window.

Windows PowerShell:

```powershell
$env:PYTHONPATH="$PWD/application/backend/src"
```

macOS or Linux:

```bash
export PYTHONPATH="$PWD/application/backend/src"
```

Keep this terminal open. If you close it and come back later, repeat this step.

## Step 5: run the good sample file

Windows PowerShell:

```powershell
python -m health_reporting.cli sample-data/valid-participants.csv
```

macOS or Linux:

```bash
python3 -m health_reporting.cli sample-data/valid-participants.csv
```

Python prints a JSON result. JSON is simply a structured way to display names and values. The most
important line will look like this:

```json
"status": "AWAITING_APPROVAL"
```

That status means the file passed validation, a de-identified summary was created, and the result is
ready for a manager decision. The long file paths in the result tell you where each output was saved.
Your run ID will be different each time; that is expected.

## Step 6: run the intentionally bad sample file

Windows PowerShell:

```powershell
python -m health_reporting.cli sample-data/invalid-participants.csv
```

macOS or Linux:

```bash
python3 -m health_reporting.cli sample-data/invalid-participants.csv
```

This time, the important line should be:

```json
"status": "QUARANTINED"
```

This is also a successful demonstration. The workflow noticed unsafe or confusing data and stopped
it instead of guessing how to fix it.

## Step 7: inspect what the workflow created

Look inside the `local-data` folder. It now acts like a tiny version of the AWS storage design:

```text
local-data/
├── incoming/     original copies received by the workflow
├── validated/    normalized files and validation reports that passed
├── curated/      de-identified summary reports
├── quarantine/   rejected files and explanations of their problems
├── archive/      final manifests for successful runs
└── workflow.db   local workflow status stored in SQLite
```

Open the folder from Windows PowerShell:

```powershell
explorer .\local-data
```

Open it from macOS:

```bash
open local-data
```

Most Linux desktop systems can use:

```bash
xdg-open local-data
```

Do not place real health or participant data in this demonstration.

## Step 8: run the automated tests

Tests are small automatic checks that ask, “Does the code still behave the way we expect?”

Run the twelve backend workflow tests:

```text
python scripts/run_backend_tests.py
```

On macOS or Linux, use `python3` if that is your Python command:

```bash
python3 scripts/run_backend_tests.py
```

Run the two repository-structure checks:

```text
python -m unittest discover -s tests -v
```

Successful output ends with `OK`. Seeing several lines containing `... ok` is also a good sign.

## Step 9: run all five synthetic staff-report examples

The first demonstration used one small participant-outcomes table. The repository also includes five
different kinds of invented staff reports so you can see how the cleaner handles files that arrive in
different shapes. These examples are made-up portfolio data. They do not copy any real person,
organization, location, story, or result.

| Dataset key you type | What the invented report represents |
|---|---|
| `health-education-demographics` | Participant demographics and health-education interests |
| `case-management-activity` | Monthly visits, participants, screenings, and referrals |
| `behavioral-health-activity` | Monthly referrals, appointments, groups, and telehealth activity |
| `outreach-activity` | Monthly events, referrals, enrollments, partners, and contacts |
| `father-engagement-activity` | Monthly visits, referrals, enrollment, and education activity |

Each type has two files in `sample-data/synthetic-staff-reports`:

- a `-valid.csv` file that should pass; and
- an `-invalid.csv` file that should be safely rejected.

The dataset key and the filename must match. The program makes you name the dataset because guessing
a schema from a filename or a few columns could silently process a report incorrectly.

### Run every valid staff report

Make sure you are still in the repository root and that you completed Step 4. Windows PowerShell
users can copy and run these commands one at a time:

```powershell
python -m health_reporting.portfolio_cli health-education-demographics sample-data/synthetic-staff-reports/health-education-demographics-valid.csv
python -m health_reporting.portfolio_cli case-management-activity sample-data/synthetic-staff-reports/case-management-activity-valid.csv
python -m health_reporting.portfolio_cli behavioral-health-activity sample-data/synthetic-staff-reports/behavioral-health-activity-valid.csv
python -m health_reporting.portfolio_cli outreach-activity sample-data/synthetic-staff-reports/outreach-activity-valid.csv
python -m health_reporting.portfolio_cli father-engagement-activity sample-data/synthetic-staff-reports/father-engagement-activity-valid.csv
```

On macOS or Linux, use the same commands with `python3`:

```bash
python3 -m health_reporting.portfolio_cli health-education-demographics sample-data/synthetic-staff-reports/health-education-demographics-valid.csv
python3 -m health_reporting.portfolio_cli case-management-activity sample-data/synthetic-staff-reports/case-management-activity-valid.csv
python3 -m health_reporting.portfolio_cli behavioral-health-activity sample-data/synthetic-staff-reports/behavioral-health-activity-valid.csv
python3 -m health_reporting.portfolio_cli outreach-activity sample-data/synthetic-staff-reports/outreach-activity-valid.csv
python3 -m health_reporting.portfolio_cli father-engagement-activity sample-data/synthetic-staff-reports/father-engagement-activity-valid.csv
```

Each command prints JSON. Every valid example should include:

```json
"status": "TRANSFORMED"
```

The program creates one folder per dataset under `portfolio-output`. Open the main folder in Windows:

```powershell
explorer .\portfolio-output
```

Or list every output in the terminal:

```powershell
Get-ChildItem -Recurse .\portfolio-output
```

On macOS use `open portfolio-output`; on most Linux desktops use `xdg-open portfolio-output`. Each
successful dataset folder contains three useful files:

- `*.validation.json` says whether the file passed, lists safe corrections, and records any issues;
- `*.cleaned.csv` contains standardized internal rows; and
- `*.transformed.csv` contains the smaller reporting output.

The transformed files leave out direct participant and submission identifiers, full ZIP codes, exact
dates, and staff narratives. De-identification in this demonstration is useful, but it is not a
replacement for your organization's privacy review, access rules, retention rules, or small-number
suppression policy.

### Run every invalid staff report

Now run the matching bad examples. They intentionally contain problems such as negative counts,
letters where a number belongs, repeated submission IDs, impossible months, or unsupported choices.

Windows PowerShell:

```powershell
python -m health_reporting.portfolio_cli health-education-demographics sample-data/synthetic-staff-reports/health-education-demographics-invalid.csv
python -m health_reporting.portfolio_cli case-management-activity sample-data/synthetic-staff-reports/case-management-activity-invalid.csv
python -m health_reporting.portfolio_cli behavioral-health-activity sample-data/synthetic-staff-reports/behavioral-health-activity-invalid.csv
python -m health_reporting.portfolio_cli outreach-activity sample-data/synthetic-staff-reports/outreach-activity-invalid.csv
python -m health_reporting.portfolio_cli father-engagement-activity sample-data/synthetic-staff-reports/father-engagement-activity-invalid.csv
```

macOS or Linux:

```bash
python3 -m health_reporting.portfolio_cli health-education-demographics sample-data/synthetic-staff-reports/health-education-demographics-invalid.csv
python3 -m health_reporting.portfolio_cli case-management-activity sample-data/synthetic-staff-reports/case-management-activity-invalid.csv
python3 -m health_reporting.portfolio_cli behavioral-health-activity sample-data/synthetic-staff-reports/behavioral-health-activity-invalid.csv
python3 -m health_reporting.portfolio_cli outreach-activity sample-data/synthetic-staff-reports/outreach-activity-invalid.csv
python3 -m health_reporting.portfolio_cli father-engagement-activity sample-data/synthetic-staff-reports/father-engagement-activity-invalid.csv
```

Every bad example should say:

```json
"status": "QUARANTINED"
```

That result is a success: it proves the program found unsafe input and refused to create cleaned or
transformed output. Read the matching `.validation.json` file to see the exact row, column, error
code, and explanation.

The cleaner only makes safe, predictable corrections. For example, it can remove extra spaces,
standardize a month, capitalize a known code, or convert a whole-number string to a number. It will
not invent a missing ID, guess an unknown category, change a negative count, repair an impossible
date, or guess what a person meant.

To keep another set of outputs separate, add an output folder to any command:

```powershell
python -m health_reporting.portfolio_cli outreach-activity sample-data/synthetic-staff-reports/outreach-activity-valid.csv --output-dir practice-portfolio-output
```

For the exact columns and cleaning rules for each report, see the
[synthetic ingestion guide](synthetic-ingestion.md).

## Optional: use a separate practice folder for output

You do not have to erase old results. Give a run a different output folder instead:

```text
python -m health_reporting.cli sample-data/valid-participants.csv --data-root practice-data
```

The workflow will create `practice-data` and leave `local-data` alone.

## Optional: try your own invented CSV

For the original participant-outcomes workflow, copy `sample-data/valid-participants.csv`, give the
copy a new name, and edit only invented values. Keep these column headings:

```text
participant_id,program_code,service_date,outcome_achieved,age_group
```

Run the copy by replacing the sample path in the command:

```text
python -m health_reporting.cli path/to/your-invented-file.csv
```

The default reporting period is April 1 through June 30, 2026. To use another period:

```text
python -m health_reporting.cli path/to/your-invented-file.csv --cycle 2026-Q3 --start 2026-07-01 --end 2026-09-30
```

Dates use `YYYY-MM-DD`: year, month, then day.

For one of the five staff-report workflows, copy the matching `-valid.csv` example from
`sample-data/synthetic-staff-reports`, keep its exact headings, and change only invented values. Then
run it with `health_reporting.portfolio_cli`, using the matching dataset key from Step 9.

This demonstration reads CSV files. If your invented practice data starts in Excel or Google Sheets,
export or download a copy as **Comma-separated values (.csv)** first. Do not merely rename `.xlsx` to
`.csv`; those are different file formats. Never put real work documents, names, email addresses,
phone numbers, birth dates, medical details, or identifying stories in this public repository.

## Optional: preview the React portal

The portal preview requires Node.js 22 and npm. Install Node.js from
[nodejs.org](https://nodejs.org/en/download), then check it:

```text
node --version
npm --version
```

From the repository root:

```text
cd application/frontend
npm ci
npm run dev
```

The terminal displays a local address, usually `http://localhost:5173`. Open that address in a web
browser. Press `Ctrl+C` in the terminal when you want to stop the preview.

The screen is a portfolio demonstration. Its secure upload button needs the AWS API, bucket, identity,
and browser-origin configuration before it can upload a file. The Python commands in Steps 5 and 6
are the complete no-AWS demonstration.

## Optional: run every local project check

The complete validation script also requires Node.js, npm, and Terraform. It tests Python, builds the
portal, formats Terraform, downloads Terraform providers, and validates both environments.

Windows PowerShell:

```powershell
.\scripts\validate.ps1
```

macOS or Linux:

```bash
./scripts/validate.sh
```

This takes longer than the Python-only tests and requires an internet connection for package and
provider downloads.

## Get newer repository changes later

If you cloned with Git, open a terminal in the repository and first check whether you changed files:

```text
git status
```

If the output says the working tree is clean, download the newest `main` branch:

```text
git switch main
git pull origin main
```

Do not force a pull over work you want to keep. Commit, copy, or ask for help with your changes first.

## Common problems

### “python is not recognized” or “command not found”

Python is missing or is not on your PATH. Reinstall Python and, on Windows, select **Add Python to
PATH**. Windows users can also try `py` instead of `python`.

### `No module named health_reporting`

You probably skipped Step 4, opened a new terminal, or are not in the repository root. Return to the
project folder and set `PYTHONPATH` again.

### `No such file or directory` or `cannot find the path`

Check your current folder. You must run the commands from the folder containing `README.md`.

### The bad sample says `QUARANTINED`

That is correct. The bad file exists to prove the workflow refuses unsafe data.

### `invalid choice` appears after `portfolio_cli`

The dataset key was typed incorrectly. Copy one of the five keys from the table in Step 9. Do not use
the filename as the key, and do not include `.csv` in the key.

### A staff-report file is quarantined even though you expected it to pass

First check that the dataset key matches the file. For example, use `outreach-activity` with
`outreach-activity-valid.csv`. Then open the generated `.validation.json` file under
`portfolio-output/<dataset-key>/`; its `issues` list explains the exact problem.

### I cannot find the cleaned or transformed staff-report files

They are written under `portfolio-output/<dataset-key>/`, not under `local-data`. A quarantined file
only gets a validation report because the program deliberately refuses to transform unsafe rows.

### The run IDs or filenames do not match this guide

That is normal. The program creates a new random run ID each time so different runs do not overwrite
one another.

### The portal opens, but its upload fails

The visual portal can run locally, but direct upload requires deployed AWS resources and configuration.
Use the Python workflow for the no-AWS demonstration.

## Part 2: deploy the dev environment to AWS with Terraform

Stop here unless Part 1 works. The AWS steps create real cloud resources and can cost money. The
default dev configuration leaves the expensive VPC, NAT Gateway, load balancer, Fargate, and RDS
control plane turned off. It still creates services such as S3, Lambda, Step Functions, EventBridge,
CloudFront, WAF, CloudTrail, CloudWatch, SNS, and KMS. Check current prices and use a dedicated
non-production AWS account with a budget alarm.

The instructions below are written for Windows PowerShell. A macOS/Linux command table appears near
the end of the guide.

### What Terraform does

Terraform reads the `.tf` files and compares them with your AWS account. Its main commands are:

- `terraform init`: prepares the folder and downloads providers.
- `terraform validate`: checks whether the Terraform code makes sense.
- `terraform plan`: shows what Terraform wants to change without making the changes.
- `terraform apply`: makes the reviewed changes in AWS.
- `terraform destroy`: removes resources tracked in the Terraform state.

HashiCorp's official [Terraform CLI documentation](https://developer.hashicorp.com/terraform/cli/commands)
describes each command. Never skip the plan review.

### AWS Step 1: install the additional tools

Install these tools before continuing:

1. [Terraform](https://developer.hashicorp.com/terraform/install), version 1.10 or newer but below 2.0.
2. [AWS CLI version 2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
3. [Node.js 22](https://nodejs.org/en/download), which includes npm.

Open a new PowerShell window in the repository root and check them:

```powershell
terraform version
aws --version
node --version
npm.cmd --version
```

Every command should print a version number. Do not continue if one says it is not recognized.

### AWS Step 2: sign in safely

Ask the AWS account administrator for an approved non-production role. Prefer short-lived AWS IAM
Identity Center credentials instead of permanent access keys. The administrator must grant the role
permission to create the resources shown in the Terraform plan and to use the separate state bucket.

Create a profile. This example names it `health-demo`:

```powershell
aws configure sso --profile health-demo
aws sso login --profile health-demo
```

Tell the AWS CLI and Terraform to use that profile and the repo's example Region:

```powershell
$Profile = "health-demo"
$Region = "us-west-2"
$env:AWS_PROFILE = $Profile
$env:AWS_REGION = $Region
```

Confirm the identity before creating anything:

```powershell
aws sts get-caller-identity
```

Read the returned account number and role ARN. Stop if they are not the intended sandbox account and
role. AWS documents this check in the
[get-caller-identity reference](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html).

These PowerShell variables last only until you close the window. Set them again in a new window.

### AWS Step 3: create the remote Terraform state bucket once

Terraform state is its memory of what it created. This project keeps that state in a separate private
S3 bucket. The bucket must exist before Terraform can manage the application.

Create a globally unique, lowercase name using your AWS account number:

```powershell
$AccountId = aws sts get-caller-identity --query Account --output text
$StateBucket = "health-reporting-tfstate-$AccountId-$Region"
$StateBucket
```

The last line prints the exact bucket name. Create and secure it:

```powershell
aws s3api create-bucket `
  --bucket $StateBucket `
  --region $Region `
  --create-bucket-configuration LocationConstraint=$Region

aws s3api put-bucket-versioning `
  --bucket $StateBucket `
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption `
  --bucket $StateBucket `
  --server-side-encryption-configuration 'Rules=[{ApplyServerSideEncryptionByDefault={SSEAlgorithm=AES256}}]'

aws s3api put-public-access-block `
  --bucket $StateBucket `
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

If `create-bucket` says the bucket already exists and belongs to you, do not create another one. Keep
using that same state bucket. If it belongs to somebody else, choose another unique name.

Confirm all three protections:

```powershell
aws s3api get-bucket-versioning --bucket $StateBucket
aws s3api get-bucket-encryption --bucket $StateBucket
aws s3api get-public-access-block --bucket $StateBucket
```

Look for `Enabled`, `AES256`, and four `true` values. HashiCorp recommends Versioning for state
recovery and supports S3 lockfiles through `use_lockfile = true`; see the official
[S3 backend documentation](https://developer.hashicorp.com/terraform/language/backend/s3).

The `us-east-1` Region is a special case: its `create-bucket` command must omit
`--create-bucket-configuration`. This guide uses `us-west-2`, so the displayed command is correct as
written.

### AWS Step 4: make private configuration copies

Run these commands from the repository root:

```powershell
Copy-Item .\terraform\environments\dev\backend.hcl.example .\terraform\environments\dev\backend.hcl
Copy-Item .\terraform\environments\dev\terraform.tfvars.example .\terraform\environments\dev\terraform.tfvars
notepad .\terraform\environments\dev\backend.hcl
```

In `backend.hcl`, replace `replace-with-terraform-state-bucket` with the value printed by
`$StateBucket`. Keep the key, Region, encryption, and lockfile lines. Save and close Notepad.

Open the variable file:

```powershell
notepad .\terraform\environments\dev\terraform.tfvars
```

For the least expensive working demo, keep these important values:

```hcl
aws_region        = "us-west-2"
enable_frontend   = true
enable_full_stack = false
protect_data      = false
```

`protect_data = false` allows the disposable dev buckets to be removed during teardown. Production
uses `true`. The full-stack-only values may remain empty because `enable_full_stack` is false.

Both private files are ignored by Git. Confirm that they are not being offered for commit:

```powershell
git status --short
```

You should not see `backend.hcl` or `terraform.tfvars` in the output.

### AWS Step 5: run every local check

This command runs the Python tests, repository tests, frontend build, Terraform formatting, and
Terraform validation for dev and prod:

```powershell
.\scripts\validate.ps1
```

The successful ending contains Python `OK`, a successful Vite build, and `Success! The configuration
is valid.` for both Terraform environments.

You can also run only Terraform's safe static checks:

```powershell
terraform -chdir=terraform/environments/dev init -backend=false -input=false
terraform -chdir=terraform/environments/dev fmt -check
terraform -chdir=terraform/environments/dev validate
```

`validate` checks the code but does not prove that your AWS role has enough permission. The next step
does that more completely.

### AWS Step 6: connect the backend and create a plan

Set a short variable so the commands are easier to read:

```powershell
$TfDir = "terraform/environments/dev"
```

Connect Terraform to the state bucket:

```powershell
terraform -chdir=$TfDir init -reconfigure -backend-config=backend.hcl
```

Create a saved plan:

```powershell
terraform -chdir=$TfDir fmt -check
terraform -chdir=$TfDir validate
terraform -chdir=$TfDir plan -out=dev.tfplan
```

`plan` reads AWS but does not create the proposed resources. Read the entire output. Check that:

- the account and Region are correct;
- the plan contains additions, not surprise deletions;
- `enable_full_stack` is false;
- names begin with `health-reporting-demo-dev`;
- no real data, passwords, tokens, or access keys appear.

For an easier second look at the saved plan:

```powershell
terraform -chdir=$TfDir show dev.tfplan
```

Stop here and ask the account administrator if the plan is surprising or an authorization error
appears.

### AWS Step 7: apply the reviewed plan

The repository script repeats the safety checks, saves a fresh plan, and waits for a deliberate
confirmation:

```powershell
.\scripts\deploy.ps1 dev
```

Read the new plan. Only when you are satisfied, type exactly:

```text
APPLY-dev
```

Terraform now creates resources. This can take several minutes because CloudFront and WAF are global
services. Success ends with `Apply complete!` and a list of outputs. Do not close the terminal while
an apply is running.

### AWS Step 8: collect Terraform's answers

Do not guess resource names. Ask Terraform:

```powershell
$DataBucket = terraform -chdir=$TfDir output -raw data_bucket
$AuditBucket = terraform -chdir=$TfDir output -raw audit_bucket
$FrontendBucket = terraform -chdir=$TfDir output -raw frontend_bucket
$DistributionId = terraform -chdir=$TfDir output -raw frontend_distribution_id
$FrontendUrl = terraform -chdir=$TfDir output -raw frontend_url
$WorkflowArn = terraform -chdir=$TfDir output -raw workflow_arn

terraform -chdir=$TfDir output
```

The final command displays the non-secret outputs together. Keep these variables in the same
PowerShell window for the remaining checks.

### AWS Step 9: prove the basic AWS controls exist

Run these read-only checks:

```powershell
aws s3api head-bucket --bucket $DataBucket
aws s3api get-bucket-versioning --bucket $DataBucket
aws s3api get-bucket-encryption --bucket $DataBucket
aws s3api get-public-access-block --bucket $DataBucket
aws stepfunctions describe-state-machine --state-machine-arn $WorkflowArn --query status --output text
```

Expected results:

- `head-bucket` prints nothing and exits without a red error;
- bucket Versioning says `Enabled`;
- encryption says `aws:kms`;
- all four public-access settings are `true`;
- the state machine says `ACTIVE`.

If any command fails with `AccessDenied`, the role needs the missing read permission. Do not work
around that by creating permanent administrator keys.

### AWS Step 10: publish and check the visual portal

Terraform creates a private frontend bucket and CloudFront distribution, but application files must
still be built and copied into that bucket:

```powershell
npm.cmd --prefix .\application\frontend ci
npm.cmd --prefix .\application\frontend run build
aws s3 sync .\application\frontend\dist "s3://$FrontendBucket"
aws cloudfront create-invalidation --distribution-id $DistributionId --paths "/*"
```

Check the web response:

```powershell
$FrontendUrl
curl.exe -I $FrontendUrl
```

Expect an HTTP `200` response. If you briefly see `403`, wait a few minutes for CloudFront and the
invalidation to finish, then try again.

The page is a visual portfolio demo. Its Upload button will not work in the default deployment because
the API/Fargate control plane is intentionally off. The next step tests the real event-driven data
plane directly with the AWS CLI.

### AWS Step 11: run a real end-to-end AWS smoke test

#### Use the AWS-compatible sample

The deployed validation and transformation Lambdas currently implement the original
participant-outcomes contract with these columns:

```text
participant_id,program_code,service_date,outcome_achieved,age_group
```

Therefore, use `sample-data/valid-participants.csv` and `sample-data/invalid-participants.csv` for
this AWS test. The five report types under `sample-data/synthetic-staff-reports` are fully runnable
with the local `portfolio_cli` commands in Step 9, but they are not connected to the deployed Lambda
yet. Uploading one of those files to the AWS `incoming/` prefix would not prove its profile works; the
current Lambda would reject it because its columns do not match the participant-outcomes contract.

Connecting the five-profile dispatcher to Lambda and Step Functions would be a future extension. This
guide keeps the test honest by using only the data contract the Terraform deployment actually runs.

#### Upload the reporting-period configuration

First upload the reporting-period configuration. This does not start the workflow:

```powershell
aws s3 cp .\sample-data\cycle-2026-Q2.json "s3://$DataBucket/configuration/cycles/2026-Q2.json" --content-type application/json
```

This JSON file tells the workflow which reporting dates belong to `2026-Q2`. It is configuration,
not a participant record.

#### Upload a valid CSV and wait for the workflow

Remember the most recent execution, if there is one:

```powershell
$PreviousExecution = aws stepfunctions list-executions `
  --state-machine-arn $WorkflowArn `
  --max-results 1 `
  --query "executions[0].executionArn" `
  --output text `
  --no-paginate
```

Upload the invented valid CSV under the required `incoming/<cycle>/` path:

```powershell
$RunTag = Get-Date -Format "yyyyMMdd-HHmmss"
$IncomingKey = "incoming/2026-Q2/cli-$RunTag-valid-participants.csv"
aws s3 cp .\sample-data\valid-participants.csv "s3://$DataBucket/$IncomingKey" --content-type text/csv
```

S3 sends an event to EventBridge, which starts Step Functions. The following loop waits for the new
execution instead of guessing how fast AWS will be:

```powershell
$ExecutionArn = $null
for ($Try = 1; $Try -le 24; $Try++) {
  Start-Sleep -Seconds 5
  $Candidate = aws stepfunctions list-executions `
    --state-machine-arn $WorkflowArn `
    --max-results 1 `
    --query "executions[0].executionArn" `
    --output text `
    --no-paginate

  if ($Candidate -and $Candidate -ne "None" -and $Candidate -ne $PreviousExecution) {
    $ExecutionArn = $Candidate
    break
  }
}

if (-not $ExecutionArn) {
  throw "No new Step Functions execution appeared within two minutes."
}
```

Wait for that execution to finish:

```powershell
do {
  Start-Sleep -Seconds 5
  $WorkflowStatus = aws stepfunctions describe-execution `
    --execution-arn $ExecutionArn `
    --query status `
    --output text
  Write-Host "Workflow status: $WorkflowStatus"
} while ($WorkflowStatus -eq "RUNNING")

if ($WorkflowStatus -ne "SUCCEEDED") {
  throw "The workflow ended with status $WorkflowStatus."
}
```

Display the workflow result and list the encrypted artifacts:

```powershell
aws stepfunctions describe-execution --execution-arn $ExecutionArn --query output --output text
aws s3 ls "s3://$DataBucket/validated/2026-Q2/" --recursive
aws s3 ls "s3://$DataBucket/curated/2026-Q2/" --recursive
```

The execution output should contain `"status":"AWAITING_APPROVAL"`. The two S3 listings should show
a normalized CSV, a validation JSON report, and a de-identified summary CSV. That combination proves
the real S3 → EventBridge → Step Functions → validation Lambda → transform Lambda path worked.

To prove the failure path too, upload the intentionally bad sample:

```powershell
$BadRunTag = Get-Date -Format "yyyyMMdd-HHmmss"
aws s3 cp .\sample-data\invalid-participants.csv "s3://$DataBucket/incoming/2026-Q2/cli-$BadRunTag-invalid-participants.csv" --content-type text/csv
Start-Sleep -Seconds 30
aws s3 ls "s3://$DataBucket/quarantine/2026-Q2/" --recursive
```

Seeing the original bad CSV and a `validation-report.json` under `quarantine` means the safety branch
worked. The Step Functions API is eventually consistent, so a short wait is normal.

### AWS Step 12: confirm Terraform sees no unexplained changes

After the deployment and smoke test, run another plan:

```powershell
terraform -chdir=$TfDir plan -detailed-exitcode
$PlanExitCode = $LASTEXITCODE

if ($PlanExitCode -eq 0) {
  Write-Host "PASS: Terraform found no infrastructure changes."
} elseif ($PlanExitCode -eq 2) {
  Write-Warning "Terraform found changes. Read the plan before doing anything."
} else {
  throw "Terraform plan failed with exit code $PlanExitCode."
}
```

Exit code `0` means the deployed infrastructure matches the Terraform configuration. Exit code `2`
means Terraform found a difference; it does not automatically mean something is broken, but you must
read the plan.

### AWS Step 13: destroy the disposable dev environment

Leaving the environment running may continue to cost money. Confirm that the copied
`terraform.tfvars` still has `protect_data = false`, then run:

```powershell
.\scripts\cleanup.ps1 dev
```

Read the destroy plan. If it names only this dev environment, type exactly:

```text
DESTROY-dev
```

The dev setting allows Terraform to empty and remove its data, audit, and frontend buckets. This
permanently deletes the synthetic smoke-test objects. KMS key deletion is scheduled with a 30-day
waiting period, which is normal AWS behavior.

Confirm Terraform no longer tracks application resources:

```powershell
terraform -chdir=$TfDir state list
```

No output means the application state is empty. The separate Terraform state bucket remains because
Terraform did not create it. Keep it for future deployments. Delete it only when no environment uses
it and after deliberately emptying all object versions.

## macOS and Linux command differences

The order and safety rules are the same. Use these replacements:

| Windows PowerShell | macOS/Linux shell |
|---|---|
| `$env:AWS_PROFILE = "health-demo"` | `export AWS_PROFILE="health-demo"` |
| `$env:AWS_REGION = "us-west-2"` | `export AWS_REGION="us-west-2"` |
| `Copy-Item source destination` | `cp source destination` |
| `notepad file` | open the file in your text editor |
| `.\scripts\validate.ps1` | `./scripts/validate.sh` |
| `.\scripts\deploy.ps1 dev` | `./scripts/deploy.sh dev` |
| `.\scripts\cleanup.ps1 dev` | `./scripts/cleanup.sh dev` |
| `npm.cmd` | `npm` |
| `curl.exe -I` | `curl -I` |

The PowerShell waiting loop in AWS Step 11 can be replaced with repeated `aws stepfunctions
list-executions` and `aws stepfunctions describe-execution` commands. Wait until the newest execution
says `SUCCEEDED` before checking S3.

## About the optional full stack

`enable_full_stack = true` adds the API control plane: VPC networking, NAT Gateway, HTTPS load
balancer, two Fargate tasks, PostgreSQL RDS, and Secrets Manager. It costs considerably more and is
not a one-click demo. Before enabling it, you must provide:

- an immutable container image already pushed to Amazon ECR;
- an ACM certificate valid for the API hostname;
- a real enterprise OIDC issuer and audience;
- approved DNS, IAM, database, backup, and security choices.

Fake placeholder values do not make a safe or working deployment. The CLI smoke test above proves the
default event-driven portfolio architecture without pretending those organization-owned dependencies
exist.

## AWS troubleshooting

### `ExpiredToken` or an SSO login error

Sign in again and reset the profile variables:

```powershell
aws sso login --profile health-demo
$env:AWS_PROFILE = "health-demo"
$env:AWS_REGION = "us-west-2"
```

### Terraform says the backend changed

Make sure `backend.hcl` points to the intended state bucket, then run:

```powershell
terraform -chdir=terraform/environments/dev init -reconfigure -backend-config=backend.hcl
```

Do not use `-migrate-state` unless you intentionally want to move existing state.

### `AccessDenied`

Copy the exact denied AWS action and resource ARN for the account administrator. Ask for the smallest
role change that permits the reviewed deployment. Do not paste credentials into Terraform files.

### The state bucket creation command fails in `us-east-1`

Create it again without the location line:

```powershell
aws s3api create-bucket --bucket $StateBucket --region us-east-1
```

### The workflow never starts

Check that the key begins with `incoming/`, the cycle file exists, and EventBridge is enabled:

```powershell
aws s3 ls "s3://$DataBucket/configuration/cycles/"
aws s3 ls "s3://$DataBucket/incoming/2026-Q2/"
aws stepfunctions list-executions --state-machine-arn $WorkflowArn --max-results 5
```

### The workflow fails

Display its error details and follow the workflow failure runbook:

```powershell
aws stepfunctions describe-execution --execution-arn $ExecutionArn
```

See [Workflow failure response](runbooks/workflow-failure.md).

### Destroy says a protected resource cannot be deleted

Stop and check which environment you selected. For disposable dev only, set `protect_data = false`,
run a normal plan and apply so AWS records the protection change, and then run cleanup. Never weaken
production protection just to make an error disappear.
