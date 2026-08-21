"""Small FastAPI control plane for reporting cycles and direct-to-S3 uploads."""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import PurePath
from typing import Annotated
from uuid import uuid4

import boto3
import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from pydantic import BaseModel, Field

CYCLE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,39}$")
DATASET_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,39}$")
ALLOWED_EXTENSIONS = {".csv"}

app = FastAPI(title="Public Health Reporting API", version="0.1.0")
bearer = HTTPBearer(auto_error=False)


class Actor(BaseModel):
    subject: str
    roles: set[str]


class CycleConfiguration(BaseModel):
    cycle_id: str = Field(pattern=CYCLE_PATTERN.pattern)
    period_start: date
    period_end: date
    required_datasets: list[str] = Field(min_length=1)


class UploadRequest(BaseModel):
    cycle_id: str = Field(pattern=CYCLE_PATTERN.pattern)
    dataset: str = Field(pattern=DATASET_PATTERN.pattern)
    filename: str = Field(min_length=1, max_length=120)


def _local_actor(role: str | None) -> Actor:
    if os.environ.get("APP_ENV", "local") != "local":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
    return Actor(subject="local-demo-user", roles={role or "analyst"})


def current_actor(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    x_demo_role: Annotated[str | None, Header()] = None,
) -> Actor:
    issuer = os.environ.get("OIDC_ISSUER")
    audience = os.environ.get("OIDC_AUDIENCE")
    if not credentials:
        return _local_actor(x_demo_role)
    if not issuer or not audience:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "OIDC is not configured")
    try:
        jwks = PyJWKClient(f"{issuer.rstrip('/')}/.well-known/jwks.json")
        signing_key = jwks.get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid access token") from exc
    roles_claim = claims.get("roles", claims.get("cognito:groups", []))
    roles = {roles_claim} if isinstance(roles_claim, str) else set(roles_claim)
    return Actor(subject=str(claims["sub"]), roles=roles)


def require_any(*allowed_roles: str):
    def authorize(actor: Annotated[Actor, Depends(current_actor)]) -> Actor:
        if actor.roles.isdisjoint(allowed_roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Role is not authorized")
        return actor

    return authorize


def _data_bucket() -> str:
    bucket = os.environ.get("DATA_BUCKET")
    if not bucket:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "DATA_BUCKET is not configured")
    return bucket


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.put("/cycles/{cycle_id}")
def configure_cycle(
    cycle_id: str,
    configuration: CycleConfiguration,
    actor: Annotated[Actor, Depends(require_any("manager", "administrator"))],
) -> dict[str, str]:
    if cycle_id != configuration.cycle_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cycle IDs must match")
    if configuration.period_start > configuration.period_end:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reporting period is invalid")
    if any(not DATASET_PATTERN.fullmatch(item) for item in configuration.required_datasets):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A required dataset name is invalid")
    boto3.client("s3").put_object(
        Bucket=_data_bucket(),
        Key=f"configuration/cycles/{cycle_id}.json",
        Body=configuration.model_dump_json(indent=2).encode(),
        ContentType="application/json",
        ServerSideEncryption="aws:kms",
        SSEKMSKeyId=os.environ["KMS_KEY_ARN"],
        Metadata={"configured-by": actor.subject},
    )
    return {"cycle_id": cycle_id, "status": "CONFIGURED"}


@app.post("/uploads")
def create_upload(
    request: UploadRequest,
    actor: Annotated[Actor, Depends(require_any("analyst", "manager"))],
) -> dict[str, str | int]:
    file_name = PurePath(request.filename).name
    is_supported_extension = PurePath(file_name).suffix.lower() in ALLOWED_EXTENSIONS
    if file_name != request.filename or not is_supported_extension:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only plain CSV filenames are accepted")
    object_key = f"incoming/{request.cycle_id}/{request.dataset}/{uuid4()}-{file_name}"
    expires_in = int(os.environ.get("UPLOAD_URL_TTL_SECONDS", "900"))
    upload_url = boto3.client("s3").generate_presigned_url(
        "put_object",
        Params={
            "Bucket": _data_bucket(),
            "Key": object_key,
            "ContentType": "text/csv",
        },
        ExpiresIn=expires_in,
    )
    return {"object_key": object_key, "upload_url": upload_url, "expires_in": expires_in}
