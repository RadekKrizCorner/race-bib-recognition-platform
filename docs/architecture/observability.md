# Observability

Grafana visualizes metrics, logs, and traces.

```mermaid
flowchart TB
    subgraph Apps[Application Services]
        direction LR
        API[Ingest API]
        D[Bib Detection Service]
        C[Crop Service]
        N[Normalization Service]
        O[OCR Service]
        L[Linking Service]
    end

    subgraph Signals[Telemetry Signals]
        direction LR
        LOG[Logs]
        MET[Metrics]
        TR[Traces]
    end

    COL[OpenTelemetry Collector / Log Agent]

    subgraph Backends[Observability Backends]
        direction LR
        PR[Prometheus]
        LK[Loki]
        TP[Tempo]
    end

    GR[Grafana]

    Apps --> COL
    Signals --> COL
    COL --> PR
    COL --> LK
    COL --> TP
    PR --> GR
    LK --> GR
    TP --> GR
```

## Required Dashboards

- Pipeline throughput
- End-to-end processing latency
- Per-stage latency
- Kafka consumer lag
- OCR confidence distribution
- Failed jobs
- DLQ message count
- Service health

## Instrumentation

The API exposes Prometheus text metrics at `/metrics`. Services can enable OpenTelemetry export with `RBP_OTEL_EXPORTER_OTLP_ENDPOINT`.
