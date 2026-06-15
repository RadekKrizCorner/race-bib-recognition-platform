# Ingest API

## Responsibility

Accept photo uploads, store raw image artifacts, create processing jobs, and publish `photo.ingested`.

## Input Event

None. This is the public HTTP entry point.

## Output Event

`photo.ingested`

## Configuration

- `RBP_ARTIFACT_ROOT`
- `RBP_MONGODB_URI`
- `RBP_KAFKA_BOOTSTRAP_SERVERS`

## Local Run

```bash
uv run uvicorn rbp_ingest_api.app:app --reload --app-dir services/ingest-api/src
```

Set `RBP_API_MODE=async` when running with Kafka and MongoDB. Local mode processes the deterministic demo in process for tests and quick portfolio review.

## Test Strategy

Use FastAPI integration tests with deterministic local pipeline dependencies.
