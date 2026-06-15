from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from rbp_contracts.events import (
    BibDetectedPayload,
    EventEnvelope,
    EventType,
    PhotoIngestedPayload,
    ResultLinkedPayload,
)
from rbp_contracts.ids import new_event_id, new_job_id, new_photo_id
from rbp_contracts.models import Detection, FinalResult, ProcessingJob
from rbp_contracts.statuses import ArtifactType, JobStatus, PipelineStage


def test_id_helpers_create_prefixed_identifiers() -> None:
    """Verify identifier helpers create expected prefixes."""
    event_id = new_event_id()
    job_id = new_job_id()
    photo_id = new_photo_id()

    assert event_id.startswith("evt-")
    assert job_id.startswith("job-")
    assert photo_id.startswith("photo-")


def test_event_envelope_keeps_metadata_separate_from_payload() -> None:
    """Verify event metadata stays outside payload data."""
    payload = PhotoIngestedPayload(imageUri="file://artifacts/jobs/job-1/raw/photo-1.jpg")
    event = EventEnvelope.new(
        eventType=EventType.PHOTO_INGESTED,
        jobId="job-1",
        photoId="photo-1",
        source="ingest-api",
        payload=payload,
        timestamp=datetime(2026, 6, 13, 10, 15, 30, tzinfo=UTC),
    )

    dumped = event.model_dump(mode="json")

    assert dumped["eventType"] == "photo.ingested"
    assert dumped["jobId"] == "job-1"
    assert dumped["photoId"] == "photo-1"
    assert dumped["payload"] == {"imageUri": "file://artifacts/jobs/job-1/raw/photo-1.jpg"}


def test_event_payload_rejects_image_bytes() -> None:
    """Verify event payloads reject unexpected image bytes."""
    with pytest.raises(ValidationError):
        PhotoIngestedPayload(imageUri="file://x.jpg", imageBytes="not-allowed")


def test_detection_payload_supports_multiple_bibs() -> None:
    """Verify detection payloads can carry multiple bibs."""
    payload = BibDetectedPayload(
        detections=[
            Detection(detectionId="det-1", bbox=[10, 20, 100, 150], confidence=0.91),
            Detection(detectionId="det-2", bbox=[110, 30, 210, 160], confidence=0.84),
        ]
    )

    assert len(payload.detections) == 2
    assert payload.detections[0].bbox == [10, 20, 100, 150]


def test_processing_job_serializes_mongo_style_document() -> None:
    """Verify processing jobs serialize to Mongo-style documents."""
    created_at = datetime(2026, 6, 13, 10, 15, 30, tzinfo=UTC)
    job = ProcessingJob(
        jobId="job-1",
        raceId="race-1",
        photoId="photo-1",
        sourceImageUri="file://artifacts/jobs/job-1/raw/photo-1.jpg",
        status=JobStatus.COMPLETED,
        currentStage=PipelineStage.LINKING,
        createdAt=created_at,
        updatedAt=created_at,
        finalResults=[FinalResult(bibNumber="1258", confidence=0.97, ocrResultId="ocr-1")],
    )

    document = job.as_mongo_document()

    assert document["_id"] == "job-1"
    assert document["status"] == "COMPLETED"
    assert document["currentStage"] == "LINKING"
    assert document["finalResults"][0]["bibNumber"] == "1258"


def test_result_linked_payload_uses_final_results_only() -> None:
    """Verify linked result payloads expose final results."""
    payload = ResultLinkedPayload(
        finalResults=[FinalResult(bibNumber="3421", confidence=0.91, ocrResultId="ocr-2")]
    )

    assert payload.finalResults[0].bibNumber == "3421"


def test_enums_match_spec_values() -> None:
    """Verify enum values match the implementation spec."""
    assert JobStatus.OCRING.value == "OCRING"
    assert PipelineStage.NORMALIZATION.value == "NORMALIZATION"
    assert ArtifactType.NORMALIZED_CROP.value == "normalized_crop"
