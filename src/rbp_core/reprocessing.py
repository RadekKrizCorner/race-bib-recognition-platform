"""Reprocessing helpers for restarting jobs from persisted artifacts."""

from rbp_contracts.events import EventEnvelope, EventType, PhotoIngestedPayload


def build_photo_reprocess_event(job_id: str, photo_id: str, source_image_uri: str) -> EventEnvelope:
    """Build a photo.ingested event for reprocessing a raw artifact."""
    return EventEnvelope.new(
        eventType=EventType.PHOTO_INGESTED,
        jobId=job_id,
        photoId=photo_id,
        source="reprocessing-worker",
        payload=PhotoIngestedPayload(imageUri=source_image_uri),
    )
