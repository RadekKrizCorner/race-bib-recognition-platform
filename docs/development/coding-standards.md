# Coding Standards

## Python

- Use typed Python.
- Prefer clear, boring code.
- Keep services small and focused.
- Use Pydantic models for public contracts.
- Keep service-specific behavior out of shared contracts.
- Add a simple docstring to every Python function or method.

## Events

- Use `EventEnvelope`.
- Include `jobId` and `photoId`.
- Keep payloads metadata-only.
- Persist artifacts before publishing downstream events.

## Tests

- Use deterministic fake adapters for local tests.
- Cover idempotency for replayed events.
- Add integration tests for public API behavior.
