# Beginner guide: run the project on your computer

This guide starts at the very beginning. You do not need an AWS account to follow the main steps.
You will use invented CSV records, run the reporting workflow on your own computer, and see one file
pass validation while another file is safely quarantined.

## What you are about to do

Think of the repository as a project folder containing instructions, Python code, test data, and
documentation. You will:

1. Copy the repository from GitHub onto your computer.
2. Open a terminal inside the copied folder.
3. Tell Python where the project code lives.
4. Run a good sample file.
5. Run a bad sample file.
6. Inspect the folders created by the workflow.
7. Run the automated tests.

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

Run the seven backend workflow tests:

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

## Optional: use a separate practice folder for output

You do not have to erase old results. Give a run a different output folder instead:

```text
python -m health_reporting.cli sample-data/valid-participants.csv --data-root practice-data
```

The workflow will create `practice-data` and leave `local-data` alone.

## Optional: try your own invented CSV

Copy `sample-data/valid-participants.csv`, give the copy a new name, and edit only invented values.
Keep these column headings:

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

### The run IDs or filenames do not match this guide

That is normal. The program creates a new random run ID each time so different runs do not overwrite
one another.

### The portal opens, but its upload fails

The visual portal can run locally, but direct upload requires deployed AWS resources and configuration.
Use the Python workflow for the no-AWS demonstration.

## About the AWS deployment

Deploying the cloud version is an advanced step. It can create resources that cost money, including
NAT Gateway, load balancer, Fargate, RDS, CloudTrail data events, KMS, and storage. It also requires
an AWS account, approved credentials, remote Terraform state, identity-provider settings, a container
image, and deliberate security review.

Start with this local guide. When you are ready for AWS, follow the main
[deployment instructions](../README.md#deployment) with a dedicated non-production account and only
synthetic data. Never run `terraform apply` just to see what happens; read and understand the plan
first.
