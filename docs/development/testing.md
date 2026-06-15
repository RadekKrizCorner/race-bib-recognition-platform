# Testing

## Unit Tests

Unit tests cover:

- ID helpers
- event envelope validation
- payload validation
- status and stage enums
- artifact path generation
- in-memory repository behavior
- local pipeline handlers
- retry, DLQ, analytics, and retraining helpers

Run:

```bash
uv run pytest tests/unit
```

## Integration Tests

Integration tests cover FastAPI upload and result retrieval using the deterministic local runner.

Run:

```bash
uv run pytest tests/integration
```

## Live Docker Compose E2E

The live E2E test starts Kafka, MongoDB, API, and workers with Docker Compose, uploads a synthetic image, waits for results, and tears the stack down.

Run:

```bash
RBP_RUN_DOCKER_E2E=1 uv run pytest tests/e2e/test_docker_compose_live.py -q
```

## Documentation Checks

```bash
uv run mkdocs build --strict
```
