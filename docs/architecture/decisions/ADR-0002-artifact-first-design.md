# ADR-0002: Artifact-First Design

## Status

Accepted

## Context

Race photos and intermediate crops can be large. Sending image bytes through Kafka would increase broker storage, network cost, and replay risk.

## Decision

Store raw images and intermediate files in artifact storage. Kafka events carry only artifact URIs and metadata.

## Consequences

- Events remain small and stable.
- Debugging and retraining can reuse persisted artifacts.
- Services must persist artifacts before publishing downstream events.
