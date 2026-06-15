# Kafka

Kafka is the asynchronous backbone of the platform.

## Topics

| Topic | Produced By | Consumed By |
|---|---|---|
| `photo.ingested` | Ingest API | Bib Detection Service |
| `bib.detected` | Bib Detection Service | Crop Service |
| `bib.cropped` | Crop Service | Normalization Service |
| `bib.normalized` | Normalization Service | OCR Service |
| `bib.ocr.completed` | OCR Service | Linking Service, analytics, retraining collectors |
| `result.linked` | Linking Service | Optional downstream consumers |
| `pipeline.failed` | Any service | Diagnostics workflows |

## Rules

- Partition by `photoId`.
- Keep image bytes out of Kafka.
- Store artifacts before publishing downstream events.
- Use separate consumer groups for fan-out consumers.
- Use DLQ topics for poison messages.

## Replay

Replay can use a new consumer group, reset offsets for an existing group, or reprocess jobs from stored artifacts and MongoDB metadata.
