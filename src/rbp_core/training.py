"""Model improvement helpers for low-confidence OCR outputs."""

from typing import Any

from pydantic import BaseModel, ConfigDict
from rbp_contracts.events import EventEnvelope, OcrCompletedPayload


class LowConfidenceSample(BaseModel):
    """Represent a candidate sample for annotation or retraining."""

    model_config = ConfigDict(extra="forbid")

    jobId: str
    photoId: str
    normalizedId: str
    bibNumber: str
    confidence: float
    artifactUri: str | None = None


class LowConfidenceCollector:
    """Collect OCR results below a confidence threshold."""

    def __init__(self, threshold: float = 0.6) -> None:
        """Initialize the collector threshold."""
        self.threshold = threshold

    def collect(self, event: EventEnvelope) -> list[LowConfidenceSample]:
        """Collect low-confidence OCR samples from an event."""
        payload = event.payload
        if not isinstance(payload, OcrCompletedPayload):
            return []
        return [
            LowConfidenceSample(
                jobId=event.jobId,
                photoId=event.photoId,
                normalizedId=result.normalizedId,
                bibNumber=result.bibNumber,
                confidence=result.confidence,
            )
            for result in payload.results
            if result.confidence < self.threshold
        ]


class DatasetManifestBuilder:
    """Build dataset manifests for retraining experiments."""

    def __init__(self, model_version: str) -> None:
        """Initialize the manifest builder."""
        self.model_version = model_version

    def build(self, samples: list[dict[str, Any] | LowConfidenceSample]) -> dict[str, Any]:
        """Build a serializable dataset manifest."""
        normalized_samples = [
            sample.model_dump(mode="json")
            if isinstance(sample, LowConfidenceSample)
            else sample
            for sample in samples
        ]
        return {"modelVersion": self.model_version, "samples": normalized_samples}
