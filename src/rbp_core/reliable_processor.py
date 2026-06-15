"""Reliable stage processing wrapper."""

from collections.abc import Callable
from datetime import UTC, datetime
from time import sleep

from rbp_contracts.events import EventEnvelope, EventType
from rbp_contracts.models import FailureRecord

from rbp_core.event_bus import InMemoryEventBus
from rbp_core.reliability import FailureMetadata, RetryPolicy
from rbp_core.state import InMemoryProcessingJobRepository


class ReliableStageProcessor:
    """Wrap stage handlers with failure event and DLQ publishing."""

    def __init__(
        self,
        stage: str,
        service_name: str,
        input_topic: str,
        repository: InMemoryProcessingJobRepository,
        event_bus: InMemoryEventBus,
        retry_policy: RetryPolicy | None = None,
        retry_backoff_seconds: float = 0.0,
    ) -> None:
        """Initialize reliable processing dependencies."""
        self.stage = stage
        self.service_name = service_name
        self.input_topic = input_topic
        self.repository = repository
        self.event_bus = event_bus
        self.retry_policy = retry_policy or RetryPolicy()
        self.retry_backoff_seconds = retry_backoff_seconds

    def process(
        self,
        event: EventEnvelope,
        handler: Callable[[EventEnvelope], EventEnvelope | None],
        retry_count: int = 0,
    ) -> EventEnvelope | None:
        """Run a handler and publish failure metadata on exceptions."""
        attempt = retry_count
        while True:
            try:
                return handler(event)
            except Exception as exc:
                attempt += 1
                if self.retry_policy.should_retry(attempt):
                    if self.retry_backoff_seconds > 0:
                        sleep(self.retry_backoff_seconds)
                    continue
                self._publish_failure(event, exc, attempt)
                raise

    def _publish_failure(self, event: EventEnvelope, exc: Exception, retry_count: int) -> None:
        """Publish pipeline.failed and DLQ events for a failed event."""
        metadata = FailureMetadata(
            jobId=event.jobId,
            photoId=event.photoId,
            stage=self.stage,
            serviceName=self.service_name,
            errorCode=type(exc).__name__,
            message=str(exc),
            retryCount=retry_count,
            timestamp=datetime.now(UTC),
            originalEventId=event.eventId,
        )
        failed_event = metadata.to_event()
        self.event_bus.publish(EventType.PIPELINE_FAILED.topic_name(), failed_event)
        self.event_bus.publish(self.retry_policy.dead_letter_topic(self.input_topic), event)
        failure = FailureRecord(
            stage=self.stage,
            serviceName=self.service_name,
            errorCode=type(exc).__name__,
            message=str(exc),
            retryCount=retry_count,
            timestamp=metadata.timestamp,
            originalEventId=event.eventId,
        )
        try:
            self.repository.mark_failed(event.jobId, failure)
        except KeyError:
            return
