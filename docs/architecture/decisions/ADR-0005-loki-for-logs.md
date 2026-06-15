# ADR-0005: Loki for Logs

## Status

Accepted

## Context

The observability stack needs separate tools for metrics, logs, traces, and dashboards.

## Decision

Use Prometheus for metrics, Loki for logs, Tempo for traces, OpenTelemetry for instrumentation, and Grafana for dashboards.

## Consequences

- Logs are not sent through Kafka.
- Prometheus is not misused as a log store.
- Grafana can correlate metrics, logs, and traces.
