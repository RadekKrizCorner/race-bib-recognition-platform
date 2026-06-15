"""Kafka event envelopes and payload models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from rbp_contracts.ids import new_event_id
from rbp_contracts.models import ContractModel, Crop, Detection, FinalResult, NormalizedImage, OCRResult


class EventType(StrEnum):
    """Represent supported Kafka event types."""

    PHOTO_INGESTED = "photo.ingested"
    BIB_DETECTED = "bib.detected"
    BIB_CROPPED = "bib.cropped"
    BIB_NORMALIZED = "bib.normalized"
    BIB_OCR_COMPLETED = "bib.ocr.completed"
    RESULT_LINKED = "result.linked"
    PIPELINE_FAILED = "pipeline.failed"

    def topic_name(self) -> str:
        """Return the Kafka topic name for the event."""
        return self.value


class PhotoIngestedPayload(ContractModel):
    """Describe metadata for an uploaded photo."""

    imageUri: str


class BibDetectedPayload(ContractModel):
    """Describe detected bib regions."""

    detections: list[Detection]


class BibCroppedPayload(ContractModel):
    """Describe crop artifacts produced from detections."""

    crops: list[Crop]


class BibNormalizedPayload(ContractModel):
    """Describe normalized image artifacts produced from crops."""

    normalizedImages: list[NormalizedImage]


class OcrCompletedPayload(ContractModel):
    """Describe OCR results produced from normalized images."""

    results: list[OCRResult]


class ResultLinkedPayload(ContractModel):
    """Describe final linked results for a photo."""

    finalResults: list[FinalResult]


class PipelineFailedPayload(ContractModel):
    """Describe metadata for a failed pipeline stage."""

    stage: str
    errorCode: str
    message: str
    serviceName: str
    retryCount: int = 0
    originalEventId: str | None = None


EventPayload = (
    PhotoIngestedPayload
    | BibDetectedPayload
    | BibCroppedPayload
    | BibNormalizedPayload
    | OcrCompletedPayload
    | ResultLinkedPayload
    | PipelineFailedPayload
)


class EventEnvelope(ContractModel):
    """Wrap metadata around a metadata-only Kafka payload."""

    eventId: str
    eventType: EventType
    jobId: str
    photoId: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str
    payload: EventPayload | dict[str, Any]

    @classmethod
    def new(
        cls,
        eventType: EventType,
        jobId: str,
        photoId: str,
        source: str,
        payload: EventPayload,
        timestamp: datetime | None = None,
    ) -> EventEnvelope:
        """Create a new event envelope with generated metadata."""
        return cls(
            eventId=new_event_id(),
            eventType=eventType,
            jobId=jobId,
            photoId=photoId,
            timestamp=timestamp or datetime.now(UTC),
            source=source,
            payload=payload,
        )
