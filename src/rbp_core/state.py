"""Processing job state repository implementations."""

from datetime import UTC, datetime
from typing import Any

from rbp_contracts.models import (
    Artifact,
    Crop,
    Detection,
    FailureRecord,
    FinalResult,
    JobStatusResponse,
    NormalizedImage,
    OCRResult,
    PhotoResults,
    ProcessingJob,
)
from rbp_contracts.statuses import JobStatus, PipelineStage


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(UTC)


class InMemoryProcessingJobRepository:
    """Keep processing jobs and artifacts in memory for local execution."""

    def __init__(self) -> None:
        """Initialize empty in-memory collections."""
        self._jobs: dict[str, ProcessingJob] = {}
        self._artifacts: dict[str, Artifact] = {}

    def create_received_job(
        self,
        job_id: str,
        photo_id: str,
        race_id: str | None,
        source_image_uri: str,
    ) -> ProcessingJob:
        """Create a received job if it does not already exist."""
        if job_id not in self._jobs:
            now = utc_now()
            job = ProcessingJob(
                jobId=job_id,
                raceId=race_id,
                photoId=photo_id,
                sourceImageUri=source_image_uri,
                status=JobStatus.RECEIVED,
                currentStage=PipelineStage.INGEST,
                createdAt=now,
                updatedAt=now,
            )
            job.pipeline.ingestedAt = now
            self._jobs[job_id] = job
        return self._copy_job(self._jobs[job_id])

    def add_artifact(self, artifact: Artifact) -> Artifact:
        """Persist artifact metadata idempotently by URI."""
        for existing in self._artifacts.values():
            if existing.uri == artifact.uri:
                return existing.model_copy(deep=True)
        self._artifacts[artifact.artifactId] = artifact
        return artifact.model_copy(deep=True)

    def get_job(self, job_id: str) -> ProcessingJob:
        """Return a processing job by identifier."""
        return self._copy_job(self._jobs[job_id])

    def get_job_by_photo(self, photo_id: str) -> ProcessingJob:
        """Return the newest processing job for a photo."""
        jobs = [job for job in self._jobs.values() if job.photoId == photo_id]
        if not jobs:
            raise KeyError(photo_id)
        return self._copy_job(sorted(jobs, key=lambda job: job.createdAt)[-1])

    def list_jobs(self) -> list[ProcessingJob]:
        """Return all processing jobs."""
        return [self._copy_job(job) for job in self._jobs.values()]

    def list_job_documents(self) -> list[dict[str, Any]]:
        """Return jobs as Mongo-style dictionaries."""
        return [job.as_mongo_document() for job in self._jobs.values()]

    def job_status(self, job_id: str) -> JobStatusResponse:
        """Return the public job status view."""
        job = self._jobs[job_id]
        return JobStatusResponse(
            jobId=job.jobId,
            photoId=job.photoId,
            status=job.status,
            currentStage=job.currentStage,
            createdAt=job.createdAt,
            updatedAt=job.updatedAt,
        )

    def photo_results(self, photo_id: str) -> PhotoResults:
        """Return final results for a photo."""
        job = self.get_job_by_photo(photo_id)
        return PhotoResults(photoId=job.photoId, results=job.finalResults, status=job.status)

    def mark_detecting(self, job_id: str) -> ProcessingJob:
        """Mark a job as running detection."""
        return self._advance(job_id, JobStatus.DETECTING, PipelineStage.DETECTION)

    def mark_detected(self, job_id: str, detections: list[dict[str, Any] | Detection]) -> ProcessingJob:
        """Persist detection results idempotently."""
        job = self._jobs[job_id]
        existing = {item.detectionId for item in job.detections}
        for detection in detections:
            model = detection if isinstance(detection, Detection) else Detection(**detection)
            if model.detectionId not in existing:
                job.detections.append(model)
                existing.add(model.detectionId)
        job.status = JobStatus.CROPPING
        job.currentStage = PipelineStage.DETECTION
        job.pipeline.detectedAt = job.pipeline.detectedAt or utc_now()
        job.updatedAt = utc_now()
        return self._copy_job(job)

    def mark_cropped(self, job_id: str, crops: list[Crop]) -> ProcessingJob:
        """Persist crop results idempotently."""
        job = self._jobs[job_id]
        existing = {item.cropId for item in job.crops}
        for crop in crops:
            if crop.cropId not in existing:
                job.crops.append(crop)
                existing.add(crop.cropId)
        job.status = JobStatus.NORMALIZING
        job.currentStage = PipelineStage.CROP
        job.pipeline.croppedAt = job.pipeline.croppedAt or utc_now()
        job.updatedAt = utc_now()
        return self._copy_job(job)

    def mark_normalized(self, job_id: str, normalized_images: list[NormalizedImage]) -> ProcessingJob:
        """Persist normalized image results idempotently."""
        job = self._jobs[job_id]
        existing = {item.normalizedId for item in job.normalizedImages}
        for image in normalized_images:
            if image.normalizedId not in existing:
                job.normalizedImages.append(image)
                existing.add(image.normalizedId)
        job.status = JobStatus.OCRING
        job.currentStage = PipelineStage.NORMALIZATION
        job.pipeline.normalizedAt = job.pipeline.normalizedAt or utc_now()
        job.updatedAt = utc_now()
        return self._copy_job(job)

    def mark_ocr_completed(self, job_id: str, results: list[OCRResult]) -> ProcessingJob:
        """Persist OCR results idempotently."""
        job = self._jobs[job_id]
        existing = {item.ocrResultId for item in job.ocrResults}
        for result in results:
            if result.ocrResultId not in existing:
                job.ocrResults.append(result)
                existing.add(result.ocrResultId)
        job.status = JobStatus.LINKING
        job.currentStage = PipelineStage.OCR
        job.pipeline.ocrCompletedAt = job.pipeline.ocrCompletedAt or utc_now()
        job.updatedAt = utc_now()
        return self._copy_job(job)

    def mark_linked(self, job_id: str, final_results: list[FinalResult]) -> ProcessingJob:
        """Persist final linked results idempotently."""
        job = self._jobs[job_id]
        existing = {item.ocrResultId for item in job.finalResults}
        for result in final_results:
            if result.ocrResultId not in existing:
                job.finalResults.append(result)
                existing.add(result.ocrResultId)
        job.status = JobStatus.COMPLETED
        job.currentStage = PipelineStage.LINKING
        job.pipeline.linkedAt = job.pipeline.linkedAt or utc_now()
        job.updatedAt = utc_now()
        return self._copy_job(job)

    def mark_failed(self, job_id: str, failure: FailureRecord) -> ProcessingJob:
        """Persist a failure record and mark the job failed."""
        job = self._jobs[job_id]
        job.errors.append(failure)
        job.status = JobStatus.FAILED
        job.updatedAt = utc_now()
        return self._copy_job(job)

    def _advance(self, job_id: str, status: JobStatus, stage: PipelineStage) -> ProcessingJob:
        """Advance a job status and stage."""
        job = self._jobs[job_id]
        job.status = status
        job.currentStage = stage
        job.updatedAt = utc_now()
        return self._copy_job(job)

    def _copy_job(self, job: ProcessingJob) -> ProcessingJob:
        """Return a deep copy of a job."""
        return job.model_copy(deep=True)
