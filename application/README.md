# Application

The application is intentionally separate from Terraform:

- `backend/` contains the Python validation package, Lambda handlers, FastAPI control plane,
  standard-library test suite, and container definition.
- `frontend/` contains the React/Vite reporting portal.

The local workflow and Lambda handlers import the same validation and aggregation modules. This
keeps business rules consistent between a laptop demonstration and the AWS execution path.
