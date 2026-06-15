# Local Setup

## Prerequisites

- Python 3.14+
- uv
- Docker and Docker Compose for local dependencies
- kind or minikube for local Kubernetes

## Install Dependencies

```bash
uv sync --dev
```

## Run Tests

```bash
uv run pytest
```

## Run In-Process Demo

```bash
uv run python scripts/demo_local_pipeline.py
```

## Run API Locally

```bash
uv run uvicorn rbp_ingest_api.app:app --reload --app-dir services/ingest-api/src
```

## Run Docker Compose

```bash
uv run python scripts/run_docker_compose_e2e.py
```

Docker Compose runs the API in async mode. The API stores raw artifacts, creates MongoDB job state, publishes `photo.ingested`, and worker containers consume Kafka topics through their service consumer groups.

## Optional Production Adapters

Install optional CV dependencies when validating real image processing locally:

```bash
uv sync --extra cv
```

Then configure:

```bash
RBP_DETECTOR_ADAPTER=yolo
RBP_YOLO_MODEL_PATH=/models/bib-detector.pt
RBP_IMAGE_PROCESSOR=opencv
RBP_OCR_ADAPTER=paddle
```

For the current private local detector, point the YOLO adapter at:

```bash
RBP_DETECTOR_ADAPTER=yolo
RBP_YOLO_MODEL_PATH=$RBP_PRIVATE_DATA_ROOT/runs/yolo/bib-yolo-v3-mps-2/weights/best.pt
RBP_IMAGE_PROCESSOR=opencv
RBP_OCR_ADAPTER=paddle
```

The `bib-yolo-v3-mps-2` model is a local private artifact and must stay out of Git. The repository ignores `data/`, `models/`, and common model weight formats such as `*.pt`.
