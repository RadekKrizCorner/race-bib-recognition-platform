# Processing Pipeline

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

## Stage Contracts

| Stage | Input Topic | Output Topic | Artifact Output |
|---|---|---|---|
| Ingest | HTTP upload | `photo.ingested` | raw image |
| Detection | `photo.ingested` | `bib.detected` | optional debug overlays |
| Crop | `bib.detected` | `bib.cropped` | bib crops |
| Normalization | `bib.cropped` | `bib.normalized` | normalized crops |
| OCR | `bib.normalized` | `bib.ocr.completed` | OCR metadata |
| Linking | `bib.ocr.completed` | `result.linked` | final results |

## Idempotency

Consumers check persisted job state before creating duplicate stage outputs. Replayed events reuse existing records where possible.
