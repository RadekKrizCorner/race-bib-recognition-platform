FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY libs ./libs
COPY src ./src
COPY services ./services
COPY scripts ./scripts

RUN pip install --no-cache-dir uv && uv sync --no-dev

ENV PYTHONPATH=/app/libs/rbp-contracts/src:/app/src:/app/services/ingest-api/src:/app/services/bib-detection-service/src:/app/services/crop-service/src:/app/services/normalization-service/src:/app/services/ocr-service/src:/app/services/linking-service/src
ENV RBP_ARTIFACT_ROOT=/app/artifacts

CMD ["uv", "run", "uvicorn", "rbp_ingest_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
