# Crop Service

## Responsibility

Consume `bib.detected`, crop detected bib regions, store crop artifacts, update job state, and publish `bib.cropped`.

## Input Event

`bib.detected`

## Output Event

`bib.cropped`

## Configuration

- `RBP_ARTIFACT_ROOT`
- `RBP_MONGODB_URI`
- `RBP_KAFKA_BOOTSTRAP_SERVERS`
- `RBP_IMAGE_PROCESSOR=opencv` to use OpenCV crop operations

## Local Run

```bash
uv run python -m rbp_crop_service.main
```

## Test Strategy

Validate deterministic crop paths, metadata persistence, and idempotent replay behavior.
