"""Worker runtime helpers for Kafka-compatible JSON event processing."""

import json
import signal
import sys
import time
from collections.abc import Callable
from typing import Any

from rbp_contracts.events import (
    BibCroppedPayload,
    BibDetectedPayload,
    BibNormalizedPayload,
    EventEnvelope,
    EventType,
    OcrCompletedPayload,
    PhotoIngestedPayload,
    PipelineFailedPayload,
    ResultLinkedPayload,
)

PayloadModel = (
    type[PhotoIngestedPayload]
    | type[BibDetectedPayload]
    | type[BibCroppedPayload]
    | type[BibNormalizedPayload]
    | type[OcrCompletedPayload]
    | type[ResultLinkedPayload]
    | type[PipelineFailedPayload]
)


class JsonEventCodec:
    """Encode and decode metadata-only event JSON."""

    payload_models: dict[EventType, PayloadModel] = {
        EventType.PHOTO_INGESTED: PhotoIngestedPayload,
        EventType.BIB_DETECTED: BibDetectedPayload,
        EventType.BIB_CROPPED: BibCroppedPayload,
        EventType.BIB_NORMALIZED: BibNormalizedPayload,
        EventType.BIB_OCR_COMPLETED: OcrCompletedPayload,
        EventType.RESULT_LINKED: ResultLinkedPayload,
        EventType.PIPELINE_FAILED: PipelineFailedPayload,
    }

    def encode(self, event: EventEnvelope) -> str:
        """Encode an event envelope as JSON."""
        return event.model_dump_json()

    def decode(self, raw_event: str | bytes) -> EventEnvelope:
        """Decode JSON into a typed event envelope."""
        body = json.loads(raw_event)
        event_type = EventType(body["eventType"])
        payload_model = self.payload_models[event_type]
        body["payload"] = payload_model.model_validate(body["payload"])
        return EventEnvelope.model_validate(body)


def process_stdin_event(handler: Callable[[EventEnvelope], EventEnvelope | None]) -> EventEnvelope | None:
    """Process a single event from stdin and write any output event to stdout."""
    if sys.stdin.isatty():
        return None
    raw_event = sys.stdin.read().strip()
    if not raw_event:
        return None
    codec = JsonEventCodec()
    outgoing = handler(codec.decode(raw_event))
    if outgoing is not None:
        print(codec.encode(outgoing))
    return outgoing


def idle_forever(service_name: str) -> None:
    """Keep a container worker process alive until it receives a stop signal."""
    running = True

    def stop(_signum: int, _frame: Any) -> None:
        """Stop the worker loop."""
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while running:
        time.sleep(5)
    print(f"{service_name} stopped")
