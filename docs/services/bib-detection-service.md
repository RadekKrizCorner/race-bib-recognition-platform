# Bib Detection Service

## Responsibility

Consume `photo.ingested`, load the source image artifact, detect candidate bib regions, persist detection metadata, and publish `bib.detected`.

## Input Event

`photo.ingested`

## Output Event

`bib.detected`

## Configuration

- `RBP_ARTIFACT_ROOT`
- `RBP_MONGODB_URI`
- `RBP_KAFKA_BOOTSTRAP_SERVERS`
- `RBP_DETECTOR_ADAPTER=yolo` to use the YOLO-compatible adapter
- `RBP_YOLO_MODEL_PATH` for the YOLO model artifact

For the current private local detector, use:

```bash
RBP_DETECTOR_ADAPTER=yolo
RBP_YOLO_MODEL_PATH=$RBP_PRIVATE_DATA_ROOT/runs/yolo/bib-yolo-v3-mps-2/weights/best.pt
```

The `bib-yolo-v3-mps-2` artifact is the selected detector for local OCR integration work. It detects bib regions well enough to feed crop generation and OCR tests.

The model registry metadata is stored in:

```text
models/registry/bib-yolo-v3-mps-2.yaml
```

Do not commit model weights to Git. Keep private detector artifacts under `data/private/` or another ignored local artifact directory. If a model artifact must be shared across machines, publish it through an artifact store, release asset, or model registry and document the checksum and download location.

## Local Run

```bash
uv run python -m rbp_bib_detection_service.main
```

## Test Strategy

Use fake or heuristic detector adapters for deterministic tests. Validate idempotency with replayed events.
