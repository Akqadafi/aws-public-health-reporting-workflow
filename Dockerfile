FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

USER appuser
EXPOSE 8080
CMD ["uvicorn", "health_reporting.api:app", "--host", "0.0.0.0", "--port", "8080"]
