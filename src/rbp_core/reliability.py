"""Retry and failure handling helpers."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from rbp_contracts.events import EventEnvelope, EventType, PipelineFailedPayload


class RetryPolicy:
    """Represent a simple bounded retry policy."""

    def __init__(self, max_attempts: int = 3) -> None:
        """Initialize the retry policy."""
        self.max_attempts = max_attempts

    def should_retry(self, attempt: int) -> bool:
        """Return whether another retry should be attempted."""
        return attempt < self.max_attempts

    def dead_letter_topic(self, topic: str) -> str:
        """Return the DLQ topic for an input topic."""
        return f"{topic}.dlq"


class FailureMetadata(BaseModel):
    """Represent failure metadata for DLQ and pipeline.failed events."""

    model_config = ConfigDict(extra="forbid")

    jobId: str
    photoId: str
    stage: str
    serviceName: str
    errorCode: str
    message: str
    retryCount: int
    timestamp: datetime
    originalEventId: str | None = None

    def to_event(self) -> EventEnvelope:
        """Convert failure metadata to a pipeline.failed event."""
        return EventEnvelope.new(
            eventType=EventType.PIPELINE_FAILED,
            jobId=self.jobId,
            photoId=self.photoId,
            source=self.serviceName,
            timestamp=self.timestamp,
            payload=PipelineFailedPayload(
                stage=self.stage,
                serviceName=self.serviceName,
                errorCode=self.errorCode,
                message=self.message,
                retryCount=self.retryCount,
                originalEventId=self.originalEventId,
            ),
        )
