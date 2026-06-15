from pathlib import Path

from rbp_contracts.statuses import ArtifactType, JobStatus, PipelineStage

from rbp_core.artifact_store import LocalArtifactStore
from rbp_core.state import InMemoryProcessingJobRepository


def test_local_artifact_store_writes_deterministic_job_paths(tmp_path: Path) -> None:
    """Verify local artifacts use deterministic job paths."""
    store = LocalArtifactStore(root=tmp_path)

    record = store.write_artifact(
        job_id="job-1",
        photo_id="photo-1",
        artifact_type=ArtifactType.RAW_IMAGE,
        stage=PipelineStage.INGEST,
        relative_stage_dir="raw",
        filename="photo-1.jpg",
        content=b"image-bytes",
        content_type="image/jpeg",
    )

    assert record.uri == "file://artifacts/jobs/job-1/raw/photo-1.jpg"
    assert (tmp_path / "jobs" / "job-1" / "raw" / "photo-1.jpg").read_bytes() == b"image-bytes"


def test_processing_repository_upserts_jobs_idempotently() -> None:
    """Verify creating the same received job is idempotent."""
    repository = InMemoryProcessingJobRepository()

    first = repository.create_received_job(
        job_id="job-1",
        photo_id="photo-1",
        race_id="race-1",
        source_image_uri="file://artifacts/jobs/job-1/raw/photo-1.jpg",
    )
    second = repository.create_received_job(
        job_id="job-1",
        photo_id="photo-1",
        race_id="race-1",
        source_image_uri="file://artifacts/jobs/job-1/raw/photo-1.jpg",
    )

    assert first.jobId == second.jobId
    assert len(repository.list_jobs()) == 1
    assert repository.get_job("job-1").status == JobStatus.RECEIVED


def test_processing_repository_tracks_stage_outputs_idempotently() -> None:
    """Verify repeated stage outputs do not duplicate records."""
    repository = InMemoryProcessingJobRepository()
    repository.create_received_job(
        job_id="job-1",
        photo_id="photo-1",
        race_id=None,
        source_image_uri="file://artifacts/jobs/job-1/raw/photo-1.jpg",
    )

    repository.mark_detected(
        job_id="job-1",
        detections=[{"detectionId": "det-1", "bbox": [1, 2, 3, 4], "confidence": 0.8}],
    )
    repository.mark_detected(
        job_id="job-1",
        detections=[{"detectionId": "det-1", "bbox": [1, 2, 3, 4], "confidence": 0.8}],
    )

    job = repository.get_job("job-1")

    assert job.status == JobStatus.CROPPING
    assert len(job.detections) == 1
