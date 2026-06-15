# Normalization Service

## Responsibility

Consume `bib.cropped`, normalize crop images for OCR, store normalized artifacts, and publish `bib.normalized`.

## Input Event

`bib.cropped`

## Output Event

`bib.normalized`

## Configuration

- `RBP_ARTIFACT_ROOT`
- `RBP_MONGODB_URI`
- `RBP_KAFKA_BOOTSTRAP_SERVERS`
- `RBP_IMAGE_PROCESSOR=opencv` to use OpenCV normalization
- transform profile

## Local Run

```bash
uv run python -m rbp_normalization_service.main
```

## Test Strategy

Validate normalized artifact creation and transform profile metadata.
