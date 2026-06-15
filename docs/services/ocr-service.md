# OCR Service

## Responsibility

Consume `bib.normalized`, run OCR, produce bib number candidates with confidence, update job state, and publish `bib.ocr.completed`.

## Input Event

`bib.normalized`

## Output Event

`bib.ocr.completed`

## Configuration

- `RBP_ARTIFACT_ROOT`
- `RBP_MONGODB_URI`
- `RBP_KAFKA_BOOTSTRAP_SERVERS`
- `RBP_OCR_ADAPTER=paddle` to use the PaddleOCR-compatible adapter
- OCR model configuration

## Local Run

```bash
uv run python -m rbp_ocr_service.main
```

## Test Strategy

Use fake OCR for deterministic tests and benchmark real PaddleOCR-compatible adapters with `scripts/evaluate_model.py`.
