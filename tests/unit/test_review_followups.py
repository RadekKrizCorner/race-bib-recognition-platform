from pathlib import Path

import pytest
from rbp_contracts.events import EventEnvelope, EventType, PhotoIngestedPayload
from rbp_contracts.statuses import ArtifactType, PipelineStage

from rbp_core.artifact_store import LocalArtifactStore
from rbp_core.cloud_storage import GcsArtifactStore
from rbp_core.event_bus import InMemoryEventBus
from rbp_core.reliable_processor import ReliableStageProcessor
from rbp_core.state import InMemoryProcessingJobRepository
from rbp_core.worker_runtime import JsonEventCodec
from rbp_pipeline.handlers import IngestHandler, content_type_for_suffix


def test_ingest_handler_uses_photo_id_for_raw_artifact_name(tmp_path: Path) -> None:
    """Verify uploaded source filenames do not leak into artifact paths."""
    repository = InMemoryProcessingJobRepository()
    event_bus = InMemoryEventBus()
    handler = IngestHandler(repository, LocalArtifactStore(tmp_path), event_bus)

    job_id, photo_id = handler.handle_photo(
        photo_bytes=b"bytes",
        filename="private-runner-name-secret-photo.jpg",
        race_id=None,
    )

    job = repository.get_job(job_id)

    assert job.sourceImageUri == f"file://artifacts/jobs/{job_id}/raw/{photo_id}.jpg"
    assert "private-runner-name" not in job.sourceImageUri


def test_ingest_content_type_matches_supported_suffix() -> None:
    """Verify raw artifact content types match supported image suffixes."""
    assert content_type_for_suffix(".jpg") == "image/jpeg"
    assert content_type_for_suffix(".jpeg") == "image/jpeg"
    assert content_type_for_suffix(".png") == "image/png"
    assert content_type_for_suffix(".webp") == "image/webp"
    assert content_type_for_suffix(".unknown") == "image/jpeg"


def test_reliable_stage_processor_publishes_failed_event_and_dlq() -> None:
    """Verify stage failures publish pipeline.failed and DLQ events."""
    repository = InMemoryProcessingJobRepository()
    event_bus = InMemoryEventBus()
    repository.create_received_job(
        job_id="job-1",
        photo_id="photo-1",
        race_id=None,
        source_image_uri="file://artifacts/jobs/job-1/raw/photo-1.jpg",
    )
    incoming = EventEnvelope.new(
        eventType=EventType.PHOTO_INGESTED,
        jobId="job-1",
        photoId="photo-1",
        source="ingest-api",
        payload=PhotoIngestedPayload(imageUri="file://artifacts/jobs/job-1/raw/photo-1.jpg"),
    )
    processor = ReliableStageProcessor(
        stage="DETECTION",
        service_name="bib-detection-service",
        input_topic=EventType.PHOTO_INGESTED.topic_name(),
        repository=repository,
        event_bus=event_bus,
    )

    with pytest.raises(RuntimeError):
        processor.process(
            incoming,
            lambda _event: (_ for _ in ()).throw(RuntimeError("detector failed")),
        )

    failed_events = event_bus.topic_events(EventType.PIPELINE_FAILED.topic_name())
    dlq_events = event_bus.topic_events("photo.ingested.dlq")

    assert failed_events[0].payload.errorCode == "RuntimeError"
    assert dlq_events[0].eventId == incoming.eventId
    assert repository.get_job("job-1").status == "FAILED"


def test_json_event_codec_round_trips_typed_events() -> None:
    """Verify worker JSON codec preserves typed event payloads."""
    event = EventEnvelope.new(
        eventType=EventType.PHOTO_INGESTED,
        jobId="job-1",
        photoId="photo-1",
        source="ingest-api",
        payload=PhotoIngestedPayload(imageUri="file://artifacts/jobs/job-1/raw/photo-1.jpg"),
    )
    codec = JsonEventCodec()

    decoded = codec.decode(codec.encode(event))

    assert decoded.eventType == EventType.PHOTO_INGESTED
    assert isinstance(decoded.payload, PhotoIngestedPayload)
    assert decoded.payload.imageUri.endswith("photo-1.jpg")


def test_gcs_artifact_store_uploads_to_bucket_with_stable_uri() -> None:
    """Verify GCS artifact store writes object bytes and returns gs URI metadata."""
    uploaded: dict[str, object] = {}

    class FakeBlob:
        """Provide a fake GCS blob."""

        def __init__(self, name: str) -> None:
            """Store the blob name."""
            self.name = name

        def upload_from_string(self, data: bytes, content_type: str) -> None:
            """Capture uploaded bytes and content type."""
            uploaded["name"] = self.name
            uploaded["data"] = data
            uploaded["content_type"] = content_type

    class FakeBucket:
        """Provide a fake GCS bucket."""

        def blob(self, name: str) -> FakeBlob:
            """Return a fake blob for a name."""
            return FakeBlob(name)

    class FakeClient:
        """Provide a fake GCS client."""

        def bucket(self, name: str) -> FakeBucket:
            """Return a fake bucket."""
            uploaded["bucket"] = name
            return FakeBucket()

    store = GcsArtifactStore(bucket_name="rbp-artifacts", client=FakeClient())

    artifact = store.write_artifact(
        job_id="job-1",
        photo_id="photo-1",
        artifact_type=ArtifactType.RAW_IMAGE,
        stage=PipelineStage.INGEST,
        relative_stage_dir="raw",
        filename="photo-1.jpg",
        content=b"bytes",
        content_type="image/jpeg",
    )

    assert artifact.uri == "gs://rbp-artifacts/jobs/job-1/raw/photo-1.jpg"
    assert uploaded["name"] == "jobs/job-1/raw/photo-1.jpg"
    assert uploaded["data"] == b"bytes"
