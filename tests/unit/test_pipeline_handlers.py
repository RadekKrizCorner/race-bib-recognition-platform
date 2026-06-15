from pathlib import Path

from rbp_contracts.events import EventType
from rbp_contracts.statuses import JobStatus

from rbp_core.artifact_store import LocalArtifactStore
from rbp_core.event_bus import InMemoryEventBus
from rbp_core.state import InMemoryProcessingJobRepository
from rbp_pipeline.adapters import FakeOcrAdapter, HeuristicBibDetector
from rbp_pipeline.runner import LocalPipelineRunner


def test_local_pipeline_processes_multiple_bib_results(tmp_path: Path) -> None:
    """Verify the local pipeline emits multiple final bib results."""
    runner = LocalPipelineRunner(
        repository=InMemoryProcessingJobRepository(),
        artifact_store=LocalArtifactStore(root=tmp_path),
        event_bus=InMemoryEventBus(),
        detector=HeuristicBibDetector(),
        ocr=FakeOcrAdapter(default_numbers=["1258", "3421"]),
    )

    job = runner.process_photo(
        photo_bytes=b"synthetic image bytes",
        filename="photo-abc123.jpg",
        race_id="race-1",
    )

    details = runner.get_job_details(job.jobId)
    results = runner.get_photo_results(job.photoId)

    assert job.status == JobStatus.COMPLETED
    assert details.status == JobStatus.COMPLETED
    assert [result.bibNumber for result in results.results] == ["1258", "3421"]
    assert runner.event_bus.topic_events(EventType.PHOTO_INGESTED.topic_name())
    assert runner.event_bus.topic_events(EventType.RESULT_LINKED.topic_name())


def test_pipeline_is_idempotent_for_replayed_events(tmp_path: Path) -> None:
    """Verify replayed events do not duplicate stage outputs."""
    runner = LocalPipelineRunner(
        repository=InMemoryProcessingJobRepository(),
        artifact_store=LocalArtifactStore(root=tmp_path),
        event_bus=InMemoryEventBus(),
        detector=HeuristicBibDetector(),
        ocr=FakeOcrAdapter(default_numbers=["1258"]),
    )
    job = runner.process_photo(photo_bytes=b"bytes", filename="photo.jpg", race_id=None)
    ingested_event = runner.event_bus.topic_events(EventType.PHOTO_INGESTED.topic_name())[0]

    runner.detection_handler.handle(ingested_event)

    details = runner.get_job_details(job.jobId)

    assert len(details.detections) == 2
    assert len(runner.event_bus.topic_events(EventType.BIB_DETECTED.topic_name())) == 1
