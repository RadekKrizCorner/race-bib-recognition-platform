# ADR-0004: Local-First Development

## Status

Accepted

## Context

The project should be easy to review and run by recruiters, engineers, and architects without requiring cloud credentials.

## Decision

Build a local deterministic path first, then add Docker Compose, local Kubernetes, observability, reliability, ML maturity, and cloud deployment scaffolding.

## Consequences

- Tests can run without external services.
- Cloud deployment remains reproducible but credential-free.
- Real production integrations can replace local adapters behind stable interfaces.
