"""Pipeline stage handlers used by workers and local runner."""

from pathlib import Path

from rbp_contracts.events import (
    BibCroppedPayload,
    BibDetectedPayload,
    BibNormalizedPayload,
    EventEnvelope,
    EventType,
    OcrCompletedPayload,
    PhotoIngestedPayload,
    ResultLinkedPayload,
)
from rbp_contracts.ids import new_crop_id, new_job_id, new_normalized_id, new_photo_id
from rbp_contracts.models import Crop, FinalResult, NormalizedImage
from rbp_contracts.statuses import ArtifactType, PipelineStage

from rbp_core.artifact_store import ArtifactStore
from rbp_core.event_bus import InMemoryEventBus
from rbp_core.state import InMemoryProcessingJobRepository
from rbp_pipeline.adapters import ByteImageProcessor, DetectorAdapter, ImageProcessor, OcrAdapter


def content_type_for_suffix(suffix: str) -> str:
    """Return image content type for a filename suffix."""
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(suffix.lower(), "image/jpeg")


class IngestHandler:
    """Handle photo uploads and publish photo.ingested events."""

    def __init__(
        self,
        repository: InMemoryProcessingJobRepository,
        artifact_store: ArtifactStore,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Initialize the ingest handler dependencies."""
        self.repository = repository
        self.artifact_store = artifact_store
        self.event_bus = event_bus

    def handle_photo(self, photo_bytes: bytes, filename: str, race_id: str | None = None) -> tuple[str, str]:
        """Store a photo, create a job, and publish ingestion metadata."""
        job_id = new_job_id()
        photo_id = new_photo_id()
        suffix = Path(filename).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"
        content_type = content_type_for_suffix(suffix)
        safe_filename = f"{photo_id}{suffix}"
        raw_artifact = self.artifact_store.write_artifact(
            job_id=job_id,
            photo_id=photo_id,
            artifact_type=ArtifactType.RAW_IMAGE,
            stage=PipelineStage.INGEST,
            relative_stage_dir="raw",
            filename=safe_filename,
            content=photo_bytes,
            content_type=content_type,
        )
        self.repository.add_artifact(raw_artifact)
        self.repository.create_received_job(
            job_id=job_id,
            photo_id=photo_id,
            race_id=race_id,
            source_image_uri=raw_artifact.uri,
        )
        event = EventEnvelope.new(
            eventType=EventType.PHOTO_INGESTED,
            jobId=job_id,
            photoId=photo_id,
            source="ingest-api",
            payload=PhotoIngestedPayload(imageUri=raw_artifact.uri),
        )
        self.event_bus.publish(EventType.PHOTO_INGESTED.topic_name(), event)
        return job_id, photo_id


class BibDetectionHandler:
    """Handle photo.ingested events."""

    def __init__(
        self,
        repository: InMemoryProcessingJobRepository,
        event_bus: InMemoryEventBus,
        detector: DetectorAdapter,
    ) -> None:
        """Initialize the detection handler dependencies."""
        self.repository = repository
        self.event_bus = event_bus
        self.detector = detector

    def handle(self, event: EventEnvelope) -> EventEnvelope | None:
        """Detect bib regions and publish bib.detected."""
        payload = event.payload
        if not isinstance(payload, PhotoIngestedPayload):
            raise TypeError("photo.ingested payload expected")
        try:
            job = self.repository.get_job(event.jobId)
        except KeyError:
            job = self.repository.create_received_job(
                job_id=event.jobId,
                photo_id=event.photoId,
                race_id=None,
                source_image_uri=payload.imageUri,
            )
        if job.detections:
            return None
        self.repository.mark_detecting(event.jobId)
        detections = self.detector.detect(payload.imageUri)
        self.repository.mark_detected(event.jobId, detections)
        outgoing = EventEnvelope.new(
            eventType=EventType.BIB_DETECTED,
            jobId=event.jobId,
            photoId=event.photoId,
            source="bib-detection-service",
            payload=BibDetectedPayload(detections=detections),
        )
        self.event_bus.publish(EventType.BIB_DETECTED.topic_name(), outgoing)
        return outgoing


class CropHandler:
    """Handle bib.detected events."""

    def __init__(
        self,
        repository: InMemoryProcessingJobRepository,
        artifact_store: ArtifactStore,
        event_bus: InMemoryEventBus,
        image_processor: ImageProcessor | None = None,
    ) -> None:
        """Initialize the crop handler dependencies."""
        self.repository = repository
        self.artifact_store = artifact_store
        self.event_bus = event_bus
        self.image_processor = image_processor or ByteImageProcessor()

    def handle(self, event: EventEnvelope) -> EventEnvelope | None:
        """Create crop artifacts and publish bib.cropped."""
        job = self.repository.get_job(event.jobId)
        if job.crops:
            return None
        payload = event.payload
        if not isinstance(payload, BibDetectedPayload):
            raise TypeError("bib.detected payload expected")
        source_bytes = self.artifact_store.read_uri(job.sourceImageUri)
        crops: list[Crop] = []
        for index, detection in enumerate(payload.detections, start=1):
            crop_id = new_crop_id(index)
            artifact = self.artifact_store.write_artifact(
                job_id=event.jobId,
                photo_id=event.photoId,
                artifact_type=ArtifactType.BIB_CROP,
                stage=PipelineStage.CROP,
                relative_stage_dir="crops",
                filename=f"{crop_id}.jpg",
                content=self.image_processor.crop(source_bytes, detection.bbox, detection.detectionId),
                content_type="image/jpeg",
                metadata={"detectionId": detection.detectionId},
            )
            self.repository.add_artifact(artifact)
            crops.append(Crop(cropId=crop_id, detectionId=detection.detectionId, artifactUri=artifact.uri))
        self.repository.mark_cropped(event.jobId, crops)
        outgoing = EventEnvelope.new(
            eventType=EventType.BIB_CROPPED,
            jobId=event.jobId,
            photoId=event.photoId,
            source="crop-service",
            payload=BibCroppedPayload(crops=crops),
        )
        self.event_bus.publish(EventType.BIB_CROPPED.topic_name(), outgoing)
        return outgoing


class NormalizationHandler:
    """Handle bib.cropped events."""

    def __init__(
        self,
        repository: InMemoryProcessingJobRepository,
        artifact_store: ArtifactStore,
        event_bus: InMemoryEventBus,
        image_processor: ImageProcessor | None = None,
    ) -> None:
        """Initialize the normalization handler dependencies."""
        self.repository = repository
        self.artifact_store = artifact_store
        self.event_bus = event_bus
        self.image_processor = image_processor or ByteImageProcessor()

    def handle(self, event: EventEnvelope) -> EventEnvelope | None:
        """Create normalized artifacts and publish bib.normalized."""
        job = self.repository.get_job(event.jobId)
        if job.normalizedImages:
            return None
        payload = event.payload
        if not isinstance(payload, BibCroppedPayload):
            raise TypeError("bib.cropped payload expected")
        normalized_images: list[NormalizedImage] = []
        for index, crop in enumerate(payload.crops, start=1):
            normalized_id = new_normalized_id(index)
            crop_bytes = self.artifact_store.read_uri(crop.artifactUri)
            artifact = self.artifact_store.write_artifact(
                job_id=event.jobId,
                photo_id=event.photoId,
                artifact_type=ArtifactType.NORMALIZED_CROP,
                stage=PipelineStage.NORMALIZATION,
                relative_stage_dir="normalized",
                filename=f"{normalized_id}.jpg",
                content=self.image_processor.normalize(crop_bytes, "default-v1"),
                content_type="image/jpeg",
                metadata={"cropId": crop.cropId, "transformProfile": "default-v1"},
            )
            self.repository.add_artifact(artifact)
            normalized_images.append(
                NormalizedImage(
                    normalizedId=normalized_id,
                    cropId=crop.cropId,
                    artifactUri=artifact.uri,
                    transformProfile="default-v1",
                )
            )
        self.repository.mark_normalized(event.jobId, normalized_images)
        outgoing = EventEnvelope.new(
            eventType=EventType.BIB_NORMALIZED,
            jobId=event.jobId,
            photoId=event.photoId,
            source="normalization-service",
            payload=BibNormalizedPayload(normalizedImages=normalized_images),
        )
        self.event_bus.publish(EventType.BIB_NORMALIZED.topic_name(), outgoing)
        return outgoing


class OcrHandler:
    """Handle bib.normalized events."""

    def __init__(
        self,
        repository: InMemoryProcessingJobRepository,
        event_bus: InMemoryEventBus,
        ocr: OcrAdapter,
    ) -> None:
        """Initialize the OCR handler dependencies."""
        self.repository = repository
        self.event_bus = event_bus
        self.ocr = ocr

    def handle(self, event: EventEnvelope) -> EventEnvelope | None:
        """Run OCR and publish bib.ocr.completed."""
        job = self.repository.get_job(event.jobId)
        if job.ocrResults:
            return None
        payload = event.payload
        if not isinstance(payload, BibNormalizedPayload):
            raise TypeError("bib.normalized payload expected")
        results = self.ocr.recognize(payload.normalizedImages)
        self.repository.mark_ocr_completed(event.jobId, results)
        outgoing = EventEnvelope.new(
            eventType=EventType.BIB_OCR_COMPLETED,
            jobId=event.jobId,
            photoId=event.photoId,
            source="ocr-service",
            payload=OcrCompletedPayload(results=results),
        )
        self.event_bus.publish(EventType.BIB_OCR_COMPLETED.topic_name(), outgoing)
        return outgoing


class LinkingHandler:
    """Handle bib.ocr.completed events."""

    def __init__(self, repository: InMemoryProcessingJobRepository, event_bus: InMemoryEventBus) -> None:
        """Initialize the linking handler dependencies."""
        self.repository = repository
        self.event_bus = event_bus

    def handle(self, event: EventEnvelope) -> EventEnvelope | None:
        """Link OCR outputs to final photo results."""
        job = self.repository.get_job(event.jobId)
        if job.finalResults:
            return None
        payload = event.payload
        if not isinstance(payload, OcrCompletedPayload):
            raise TypeError("bib.ocr.completed payload expected")
        final_results = [
            FinalResult(
                bibNumber=result.bibNumber,
                confidence=result.confidence,
                ocrResultId=result.ocrResultId,
            )
            for result in payload.results
        ]
        self.repository.mark_linked(event.jobId, final_results)
        outgoing = EventEnvelope.new(
            eventType=EventType.RESULT_LINKED,
            jobId=event.jobId,
            photoId=event.photoId,
            source="linking-service",
            payload=ResultLinkedPayload(finalResults=final_results),
        )
        self.event_bus.publish(EventType.RESULT_LINKED.topic_name(), outgoing)
        return outgoing
