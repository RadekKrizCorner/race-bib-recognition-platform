# Agent Instructions

## Project Rules

- Keep all public text and documentation in English.
- Keep Kafka events metadata-only. Never include image bytes in events.
- Use `jobId` and `photoId` across the full pipeline.
- Do not create a `Runner` entity. The domain output is recognized bib numbers per photo.
- Keep services small, typed, and focused.
- Add tests for every production behavior change.
- Every Python function or method must have a simple docstring.
- Do not commit secrets, private race photos, or generated local artifacts.

## Development Workflow

- Use `uv run pytest` for the Python test suite.
- Use `uv run mkdocs build --strict` for documentation checks.
- Use `uv run ruff check .` for lint checks.
- Keep local data under ignored `artifacts/`, `.docker-data/`, `tmp/`, or `data/`.
- Use fake detector and OCR adapters for deterministic local tests.
- Replace fake adapters with YOLO-compatible and PaddleOCR-compatible implementations behind the existing protocols.

## Commit Format

When commits are requested, use:

```text
RBP-0001: short imperative commit description
```

Increase the numeric identifier by one for each new commit.
