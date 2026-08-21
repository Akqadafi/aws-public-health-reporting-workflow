# Backend and processing package

## Local workflow

From the repository root:

```powershell
$env:PYTHONPATH="$PWD/application/backend/src"
python -m health_reporting.cli sample-data/valid-participants.csv
python -m health_reporting.cli sample-data/invalid-participants.csv
python -m unittest discover -s application/backend/tests -v
```

The package has no runtime dependency for local validation. Installing the project adds FastAPI,
OIDC/JWT support, and the AWS SDK for API development:

```bash
python -m pip install -e "application/backend[dev]"
uvicorn health_reporting.api:app --reload --port 8080
```

Build the API container with:

```bash
docker build -t health-reporting-api application/backend
```
