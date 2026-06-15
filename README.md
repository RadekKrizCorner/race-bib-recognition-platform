# Race Bib Recognition Platform

![Python](https://img.shields.io/badge/Python-latest%20stable-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688)
![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-Event%20Streaming-black)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestration-326CE5)
![Docker](https://img.shields.io/badge/Docker-Containers-2496ED)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-GCP-4285F4)
![MongoDB](https://img.shields.io/badge/MongoDB-Database-47A248)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8)
![YOLO](https://img.shields.io/badge/YOLO-Object%20Detection-red)
![PaddleOCR](https://img.shields.io/badge/PaddleOCR-OCR-orange)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Tracing-000000)
![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C)
![Loki](https://img.shields.io/badge/Loki-Logs-F46800)
![Grafana](https://img.shields.io/badge/Grafana-Dashboards-F46800)
![MkDocs](https://img.shields.io/badge/MkDocs-Documentation-blue)
![uv](https://img.shields.io/badge/uv-Python%20Packaging-purple)

## Overview

Race Bib Recognition Platform is an event-driven computer vision platform that automatically detects and recognizes race bib numbers from running event photos.

The system processes uploaded race photos through independent asynchronous stages: bib detection, cropping, image normalization, OCR, and result linking.

The final output is a list of recognized bib numbers for each photo.

## Technology Stack

| Category | Technology |
|---|---|
| Language | Python latest stable |
| API Framework | FastAPI |
| Packaging | uv |
| Messaging | Apache Kafka |
| Local Runtime | Docker Compose |
| Local Kubernetes | kind or minikube |
| Container Platform | Kubernetes |
| Cloud Platform | Google Cloud Platform |
| Object Storage | Local storage for MVP, Google Cloud Storage for cloud deployment |
| Database | MongoDB |
| Computer Vision | OpenCV-compatible adapters |
| Object Detection | YOLO-compatible adapter |
| OCR | PaddleOCR-compatible adapter |
| Batch / Backfill Processing | Apache Beam / Google Dataflow |
| Observability | OpenTelemetry, Prometheus, Loki, Tempo, Grafana |
| Infrastructure as Code | Terraform |
| Documentation | MkDocs |

## Architecture Highlights

- Event-driven microservices architecture
- Metadata-only Kafka events
- Image artifacts stored outside Kafka
- Independent scaling of each processing stage
- Idempotent consumers
- Retry and Dead Letter Queue support
- End-to-end traceability using `jobId`
- Local-first development workflow
- Cloud deployment as a later phase
- Documentation-first project structure

## System Architecture

```mermaid
flowchart TB

    User[Photographer Upload]

    LB[Load Balancer]

    API[Ingest API]

    Kafka[(Apache Kafka)]

    Detect[Bib Detection Service]
    Crop[Bib Crop Service]
    Normalize[Normalization Service]
    OCR[OCR Service]
    Link[Linking Service]

    Mongo[(MongoDB)]

    Storage[(Artifact Storage)]

    User --> LB
    LB --> API

    API --> Storage
    API --> Kafka

    Kafka --> Detect
    Detect --> Crop
    Crop --> Normalize
    Normalize --> OCR
    OCR --> Link

    Detect --> Mongo
    Crop --> Mongo
    Normalize --> Mongo
    OCR --> Mongo
    Link --> Mongo

    Detect --> Storage
    Crop --> Storage
    Normalize --> Storage
```

## Processing Pipeline

```mermaid
flowchart LR
    subgraph Input[Ingestion]
        A[Race Photo]
        B[Ingest API]
        A --> B
    end

    subgraph Processing[Asynchronous Processing]
        C[Kafka]
        D[Bib Detection]
        E[Bib Crop]
        F[Normalization]
        G[OCR]
        C --> D --> E --> F --> G
    end

    subgraph Output[Results]
        H[Linking Service]
        I[(MongoDB)]
        J[(Artifacts)]
        G --> H --> I
        D --> J
        E --> J
        F --> J
    end

    B --> C
```

## Local Demo

Run the deterministic in-process demo:

```bash
uv run python scripts/demo_local_pipeline.py
```

Run the API locally:

```bash
uv run uvicorn rbp_ingest_api.app:app --reload --app-dir services/ingest-api/src
```

Run the async Docker path with Kafka and MongoDB:

```bash
uv run python scripts/run_docker_compose_e2e.py
```

Run tests:

```bash
uv run pytest
```

Validate local Kubernetes manifests:

```bash
uv run python scripts/validate_local_kubernetes.py
```

Run cloud deployment preflight:

```bash
uv run python scripts/cloud_preflight.py
```

## Documentation

Full documentation is available in the MkDocs site under `docs/`.

```bash
uv run mkdocs serve
```

## Roadmap

The roadmap progresses from local MVP to local orchestration, local Kubernetes, observability, reliability, model retraining, near-real-time processing, and final Google Cloud deployment.
