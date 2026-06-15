from datetime import UTC, datetime

from rbp_contracts.events import EventEnvelope, EventType, OcrCompletedPayload
from rbp_contracts.models import OCRResult

from rbp_core.analytics import PipelineAnalytics
from rbp_core.event_bus import InMemoryEventBus
from rbp_core.reliability import FailureMetadata, RetryPolicy
from rbp_core.reliable_processor import ReliableStageProcessor
from rbp_core.reprocessing import build_photo_reprocess_event
from rbp_core.state import InMemoryProcessingJobRepository
from rbp_core.training import DatasetManifestBuilder, LowConfidenceCollector


def test_retry_policy_routes_to_dlq_after_max_attempts() -> None:
    """Verify retry policy stops at the configured attempt limit."""
    policy = RetryPolicy(max_attempts=3)

    assert policy.should_retry(1) is True
    assert policy.should_retry(3) is False
    assert policy.dead_letter_topic("bib.normalized") == "bib.normalized.dlq"


def test_failure_metadata_creates_pipeline_failed_event() -> None:
    """Verify failure metadata converts to pipeline.failed events."""
    metadata = FailureMetadata(
        jobId="job-1",
        photoId="photo-1",
        stage="OCR",
        serviceName="ocr-service",
        errorCode="OCR_EMPTY_RESULT",
        message="No readable bib number found",
        retryCount=3,
        timestamp=datetime(2026, 6, 13, 10, 16, 10, tzinfo=UTC),
        originalEventId="evt-1",
    )

    event = metadata.to_event()

    assert event.eventType == EventType.PIPELINE_FAILED
    assert event.payload.stage == "OCR"
    assert event.payload.retryCount == 3


def test_low_confidence_collector_filters_ocr_results() -> None:
    """Verify low-confidence OCR results become training samples."""
    event = EventEnvelope.new(
        eventType=EventType.BIB_OCR_COMPLETED,
        jobId="job-1",
        photoId="photo-1",
        source="ocr-service",
        payload=OcrCompletedPayload(
            results=[
                OCRResult(ocrResultId="ocr-1", normalizedId="norm-1", bibNumber="1258", confidence=0.97),
                OCRResult(ocrResultId="ocr-2", normalizedId="norm-2", bibNumber="3421", confidence=0.41),
            ]
        ),
    )
    collector = LowConfidenceCollector(threshold=0.5)

    samples = collector.collect(event)

    assert len(samples) == 1
    assert samples[0].bibNumber == "3421"


def test_dataset_manifest_builder_outputs_training_manifest() -> None:
    """Verify dataset manifests include model versions and samples."""
    builder = DatasetManifestBuilder(model_version="fake-ocr-v1")

    manifest = builder.build(
        samples=[
            {
                "jobId": "job-1",
                "photoId": "photo-1",
                "artifactUri": "file://artifacts/jobs/job-1/normalized/norm-2.jpg",
                "bibNumber": "3421",
                "confidence": 0.41,
            }
        ]
    )

    assert manifest["modelVersion"] == "fake-ocr-v1"
    assert manifest["samples"][0]["artifactUri"].endswith("norm-2.jpg")


def test_pipeline_analytics_summarizes_completed_jobs() -> None:
    """Verify analytics summarize jobs and OCR confidence."""
    analytics = PipelineAnalytics()

    summary = analytics.summarize_jobs(
        [
            {"status": "COMPLETED", "finalResults": [{"confidence": 0.9}, {"confidence": 0.7}]},
            {"status": "FAILED", "finalResults": []},
        ]
    )

    assert summary["completedJobs"] == 1
    assert summary["failedJobs"] == 1
    assert summary["averageOcrConfidence"] == 0.8


def test_reliable_processor_retries_transient_failures_before_success() -> None:
    """Verify reliable processor retries a handler before DLQ routing."""
    repository = InMemoryProcessingJobRepository()
    event_bus = InMemoryEventBus()
    repository.create_received_job(
        job_id="job-1",
        photo_id="photo-1",
        race_id=None,
        source_image_uri="file://artifacts/jobs/job-1/raw/photo-1.jpg",
    )
    event = EventEnvelope.new(
        eventType=EventType.PHOTO_INGESTED,
        jobId="job-1",
        photoId="photo-1",
        source="ingest-api",
        payload={"imageUri": "file://artifacts/jobs/job-1/raw/photo-1.jpg"},
    )
    attempts = {"count": 0}

    def flaky_handler(_event: EventEnvelope) -> None:
        """Fail twice before succeeding."""
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary failure")

    processor = ReliableStageProcessor(
        stage="DETECTION",
        service_name="bib-detection-service",
        input_topic="photo.ingested",
        repository=repository,
        event_bus=event_bus,
        retry_policy=RetryPolicy(max_attempts=3),
    )

    processor.process(event, flaky_handler)

    assert attempts["count"] == 3
    assert event_bus.topic_events(EventType.PIPELINE_FAILED.topic_name()) == []
    assert event_bus.topic_events("photo.ingested.dlq") == []


def test_build_photo_reprocess_event_restarts_from_source_artifact() -> None:
    """Verify reprocessing can restart from a persisted raw artifact."""
    event = build_photo_reprocess_event(
        job_id="job-1",
        photo_id="photo-1",
        source_image_uri="file://artifacts/jobs/job-1/raw/photo-1.jpg",
    )

    assert event.eventType == EventType.PHOTO_INGESTED
    assert event.source == "reprocessing-worker"
    assert event.payload.imageUri.endswith("photo-1.jpg")
