# Race Bib Recognition Platform

Race Bib Recognition Platform detects and recognizes race bib numbers from running event photos using an event-driven pipeline.

The platform is designed as a portfolio-ready monorepo with local-first execution, clear service boundaries, metadata-only Kafka events, artifact-first image storage, and a staged path to Google Cloud deployment.

## Core Flow

1. Upload a race photo.
2. Store the raw image as an artifact.
3. Publish `photo.ingested`.
4. Detect candidate bib regions.
5. Crop detected bib regions.
6. Normalize crops for OCR.
7. Run OCR.
8. Link recognized bib numbers back to the photo.

## Local Verification

```bash
uv run pytest
uv run python scripts/demo_local_pipeline.py
uv run mkdocs serve
```
