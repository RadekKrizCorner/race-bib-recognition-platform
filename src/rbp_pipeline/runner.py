"""Local in-process pipeline runner for tests and demos."""

from pathlib import Path

from rbp_contracts.models import JobStatusResponse, PhotoResults, ProcessingJob

from rbp_core.artifact_store import LocalArtifactStore
from rbp_core.event_bus import InMemoryEventBus
from rbp_core.state import InMemoryProcessingJobRepository
from rbp_pipeline.adapters import (
    DetectorAdapter,
    FakeOcrAdapter,
    HeuristicBibDetector,
    ImageProcessor,
    OcrAdapter,
)
from rbp_pipeline.handlers import (
    BibDetectionHandler,
    CropHandler,
    IngestHandler,
    LinkingHandler,
    NormalizationHandler,
    OcrHandler,
)


class LocalPipelineRunner:
    """Run the full pipeline in process without Kafka or MongoDB."""

    def __init__(
        self,
        repository: InMemoryProcessingJobRepository | None = None,
        artifact_store: LocalArtifactStore | None = None,
        event_bus: InMemoryEventBus | None = None,
        detector: DetectorAdapter | None = None,
        ocr: OcrAdapter | None = None,
        image_processor: ImageProcessor | None = None,
    ) -> None:
        """Initialize the runner and all stage handlers."""
        self.repository = repository or InMemoryProcessingJobRepository()
        self.artifact_store = artifact_store or LocalArtifactStore(Path("artifacts"))
        self.event_bus = event_bus or InMemoryEventBus()
        self.ingest_handler = IngestHandler(self.repository, self.artifact_store, self.event_bus)
        self.detection_handler = BibDetectionHandler(
            self.repository,
            self.event_bus,
            detector or HeuristicBibDetector(),
        )
        self.crop_handler = CropHandler(
            self.repository,
            self.artifact_store,
            self.event_bus,
            image_processor=image_processor,
        )
        self.normalization_handler = NormalizationHandler(
            self.repository,
            self.artifact_store,
            self.event_bus,
            image_processor=image_processor,
        )
        self.ocr_handler = OcrHandler(self.repository, self.event_bus, ocr or FakeOcrAdapter())
        self.linking_handler = LinkingHandler(self.repository, self.event_bus)

    def process_photo(self, photo_bytes: bytes, filename: str, race_id: str | None = None) -> ProcessingJob:
        """Process one uploaded photo through all local stages."""
        job_id, _photo_id = self.ingest_handler.handle_photo(photo_bytes, filename, race_id)
        ingested = self.event_bus.topic_events("photo.ingested")[-1]
        detected = self.detection_handler.handle(ingested)
        if detected is None:
            return self.repository.get_job(job_id)
        cropped = self.crop_handler.handle(detected)
        if cropped is None:
            return self.repository.get_job(job_id)
        normalized = self.normalization_handler.handle(cropped)
        if normalized is None:
            return self.repository.get_job(job_id)
        ocr_completed = self.ocr_handler.handle(normalized)
        if ocr_completed is None:
            return self.repository.get_job(job_id)
        self.linking_handler.handle(ocr_completed)
        return self.repository.get_job(job_id)

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        """Return current job status."""
        return self.repository.job_status(job_id)

    def get_job_details(self, job_id: str) -> ProcessingJob:
        """Return detailed job state."""
        return self.repository.get_job(job_id)

    def get_photo_results(self, photo_id: str) -> PhotoResults:
        """Return final photo results."""
        return self.repository.photo_results(photo_id)
