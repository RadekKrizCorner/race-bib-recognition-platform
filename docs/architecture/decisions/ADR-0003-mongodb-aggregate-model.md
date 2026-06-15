# ADR-0003: MongoDB Aggregate Model

## Status

Accepted

## Context

The platform needs fast job status reads and debugging visibility across detections, crops, OCR results, final results, and errors.

## Decision

Use a `processing_jobs` aggregate document for pipeline state and an `artifacts` collection for artifact references.

## Consequences

- API reads are straightforward.
- Debugging views can fetch one aggregate document.
- Stage handlers must update only their owned sections idempotently.
