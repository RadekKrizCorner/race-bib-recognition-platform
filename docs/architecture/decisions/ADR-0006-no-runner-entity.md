# ADR-0006: No Runner Entity

## Status

Accepted

## Context

The platform recognizes race bib numbers in photos. It does not identify people or track runners across images.

## Decision

Do not create a `Runner` entity. Store final outputs as recognized bib numbers linked to a `photoId`.

## Consequences

- The domain model stays focused on photo processing.
- Privacy and identity scope remain limited.
- Future identity features would require a separate product decision.
