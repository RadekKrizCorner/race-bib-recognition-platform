# ADR-0001: Event-Driven Kafka

## Status

Accepted

## Context

Computer vision and OCR stages take different amounts of time. Synchronous service chaining would couple latency and failure behavior across all services.

## Decision

Use Kafka as the event backbone. Each stage consumes one event, persists state or artifacts, and emits the next event.

## Consequences

- Services can scale independently.
- Replay and fan-out become natural.
- Consumers must be idempotent.
- Kafka events must stay metadata-only.
