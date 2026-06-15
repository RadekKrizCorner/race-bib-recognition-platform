"""MongoDB processing job repository."""

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

from rbp_core.state import utc_now


class MongoProcessingJobRepository:
    """Persist processing jobs and artifacts in MongoDB."""

    def __init__(self, mongo_uri: str, database_name: str = "rbp") -> None:
        """Initialize MongoDB collections."""
        from pymongo import MongoClient

        self.client = MongoClient(mongo_uri)
        database = self.client[database_name]
        self.jobs = database["processing_jobs"]
        self.artifacts = database["artifacts"]

    def create_received_job(
        self,
        job_id: str,
        photo_id: str,
        race_id: str | None,
        source_image_uri: str,
    ) -> ProcessingJob:
        """Create a received job if it does not already exist."""
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
        self.jobs.update_one(
            {"jobId": job_id},
            {"$setOnInsert": job.as_mongo_document()},
            upsert=True,
        )
        return self.get_job(job_id)

    def add_artifact(self, artifact: Artifact) -> Artifact:
        """Persist artifact metadata idempotently by URI."""
        self.artifacts.update_one(
            {"uri": artifact.uri},
            {"$setOnInsert": artifact.as_mongo_document()},
            upsert=True,
        )
        document = self.artifacts.find_one({"uri": artifact.uri})
        if document is None:
            raise KeyError(artifact.uri)
        return Artifact.model_validate(self._strip_mongo_id(document))

    def get_job(self, job_id: str) -> ProcessingJob:
        """Return a processing job by identifier."""
        document = self.jobs.find_one({"jobId": job_id})
        if document is None:
            raise KeyError(job_id)
        return ProcessingJob.model_validate(self._strip_mongo_id(document))

    def get_job_by_photo(self, photo_id: str) -> ProcessingJob:
        """Return the newest processing job for a photo."""
        document = self.jobs.find_one({"photoId": photo_id}, sort=[("createdAt", -1)])
        if document is None:
            raise KeyError(photo_id)
        return ProcessingJob.model_validate(self._strip_mongo_id(document))

    def list_jobs(self) -> list[ProcessingJob]:
        """Return all processing jobs."""
        return [ProcessingJob.model_validate(self._strip_mongo_id(document)) for document in self.jobs.find()]

    def list_job_documents(self) -> list[dict[str, Any]]:
        """Return jobs as Mongo-style dictionaries."""
        return [job.as_mongo_document() for job in self.list_jobs()]

    def job_status(self, job_id: str) -> JobStatusResponse:
        """Return the public job status view."""
        job = self.get_job(job_id)
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
        return self._replace_job(self._advanced_job(job_id, JobStatus.DETECTING, PipelineStage.DETECTION))

    def mark_detected(self, job_id: str, detections: list[dict[str, Any] | Detection]) -> ProcessingJob:
        """Persist detection results idempotently."""
        job = self.get_job(job_id)
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
        return self._replace_job(job)

    def mark_cropped(self, job_id: str, crops: list[Crop]) -> ProcessingJob:
        """Persist crop results idempotently."""
        job = self.get_job(job_id)
        existing = {item.cropId for item in job.crops}
        for crop in crops:
            if crop.cropId not in existing:
                job.crops.append(crop)
                existing.add(crop.cropId)
        job.status = JobStatus.NORMALIZING
        job.currentStage = PipelineStage.CROP
        job.pipeline.croppedAt = job.pipeline.croppedAt or utc_now()
        job.updatedAt = utc_now()
        return self._replace_job(job)

    def mark_normalized(self, job_id: str, normalized_images: list[NormalizedImage]) -> ProcessingJob:
        """Persist normalized image results idempotently."""
        job = self.get_job(job_id)
        existing = {item.normalizedId for item in job.normalizedImages}
        for image in normalized_images:
            if image.normalizedId not in existing:
                job.normalizedImages.append(image)
                existing.add(image.normalizedId)
        job.status = JobStatus.OCRING
        job.currentStage = PipelineStage.NORMALIZATION
        job.pipeline.normalizedAt = job.pipeline.normalizedAt or utc_now()
        job.updatedAt = utc_now()
        return self._replace_job(job)

    def mark_ocr_completed(self, job_id: str, results: list[OCRResult]) -> ProcessingJob:
        """Persist OCR results idempotently."""
        job = self.get_job(job_id)
        existing = {item.ocrResultId for item in job.ocrResults}
        for result in results:
            if result.ocrResultId not in existing:
                job.ocrResults.append(result)
                existing.add(result.ocrResultId)
        job.status = JobStatus.LINKING
        job.currentStage = PipelineStage.OCR
        job.pipeline.ocrCompletedAt = job.pipeline.ocrCompletedAt or utc_now()
        job.updatedAt = utc_now()
        return self._replace_job(job)

    def mark_linked(self, job_id: str, final_results: list[FinalResult]) -> ProcessingJob:
        """Persist final linked results idempotently."""
        job = self.get_job(job_id)
        existing = {item.ocrResultId for item in job.finalResults}
        for result in final_results:
            if result.ocrResultId not in existing:
                job.finalResults.append(result)
                existing.add(result.ocrResultId)
        job.status = JobStatus.COMPLETED
        job.currentStage = PipelineStage.LINKING
        job.pipeline.linkedAt = job.pipeline.linkedAt or utc_now()
        job.updatedAt = utc_now()
        return self._replace_job(job)

    def mark_failed(self, job_id: str, failure: FailureRecord) -> ProcessingJob:
        """Persist a failure record and mark the job failed."""
        job = self.get_job(job_id)
        job.errors.append(failure)
        job.status = JobStatus.FAILED
        job.updatedAt = utc_now()
        return self._replace_job(job)

    def _advanced_job(self, job_id: str, status: JobStatus, stage: PipelineStage) -> ProcessingJob:
        """Return a job advanced to a status and stage."""
        job = self.get_job(job_id)
        job.status = status
        job.currentStage = stage
        job.updatedAt = utc_now()
        return job

    def _replace_job(self, job: ProcessingJob) -> ProcessingJob:
        """Replace one MongoDB job document."""
        self.jobs.replace_one({"jobId": job.jobId}, job.as_mongo_document(), upsert=True)
        return self.get_job(job.jobId)

    def _strip_mongo_id(self, document: dict[str, Any]) -> dict[str, Any]:
        """Remove MongoDB internal identifier before Pydantic validation."""
        cleaned = dict(document)
        cleaned.pop("_id", None)
        return cleaned
