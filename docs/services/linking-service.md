# Linking Service

## Responsibility

Consume `bib.ocr.completed`, build final result lists, update `processing_jobs.finalResults`, set final status, and publish `result.linked`.

## Input Event

`bib.ocr.completed`

## Output Event

`result.linked`

## Configuration

- `RBP_MONGODB_URI`
- `RBP_KAFKA_BOOTSTRAP_SERVERS`

## Local Run

```bash
uv run python -m rbp_linking_service.main
```

## Test Strategy

Validate final results preserve bib numbers, confidence values, and OCR result references.
