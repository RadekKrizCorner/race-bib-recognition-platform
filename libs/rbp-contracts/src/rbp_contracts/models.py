"""Shared domain and persistence models."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from rbp_contracts.statuses import ArtifactType, JobStatus, PipelineStage


class ContractModel(BaseModel):
    """Provide strict shared model behavior."""

    model_config = ConfigDict(extra="forbid")


class Detection(ContractModel):
    """Describe one detected bib bounding box."""

    detectionId: str
    bbox: list[int] = Field(min_length=4, max_length=4)
    confidence: float = Field(ge=0.0, le=1.0)


class Crop(ContractModel):
    """Describe one cropped bib artifact."""

    cropId: str
    detectionId: str
    artifactUri: str


class NormalizedImage(ContractModel):
    """Describe one normalized crop artifact."""

    normalizedId: str
    cropId: str
    artifactUri: str
    transformProfile: str


class OCRResult(ContractModel):
    """Describe one OCR bib number candidate."""

    ocrResultId: str
    normalizedId: str
    bibNumber: str
    confidence: float = Field(ge=0.0, le=1.0)


class FinalResult(ContractModel):
    """Describe one final bib number result."""

    bibNumber: str
    confidence: float = Field(ge=0.0, le=1.0)
    ocrResultId: str


class FailureRecord(ContractModel):
    """Describe one persisted pipeline failure."""

    stage: str
    serviceName: str
    errorCode: str
    message: str
    retryCount: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    originalEventId: str | None = None


class Artifact(ContractModel):
    """Describe a stored artifact reference."""

    artifactId: str
    jobId: str
    photoId: str
    type: ArtifactType
    stage: PipelineStage
    uri: str
    contentType: str
    width: int | None = None
    height: int | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    def as_mongo_document(self) -> dict[str, Any]:
        """Serialize the artifact as a MongoDB-style document."""
        document = self.model_dump(mode="json")
        document["_id"] = self.artifactId
        return document


class PipelineTimestamps(ContractModel):
    """Track timestamps for each pipeline stage."""

    ingestedAt: datetime | None = None
    detectedAt: datetime | None = None
    croppedAt: datetime | None = None
    normalizedAt: datetime | None = None
    ocrCompletedAt: datetime | None = None
    linkedAt: datetime | None = None


class ProcessingJob(ContractModel):
    """Represent the MongoDB processing_jobs aggregate."""

    jobId: str
    raceId: str | None = None
    photoId: str
    sourceImageUri: str
    status: JobStatus = JobStatus.RECEIVED
    currentStage: PipelineStage = PipelineStage.INGEST
    createdAt: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(UTC))
    pipeline: PipelineTimestamps = Field(default_factory=PipelineTimestamps)
    detections: list[Detection] = Field(default_factory=list)
    crops: list[Crop] = Field(default_factory=list)
    normalizedImages: list[NormalizedImage] = Field(default_factory=list)
    ocrResults: list[OCRResult] = Field(default_factory=list)
    finalResults: list[FinalResult] = Field(default_factory=list)
    errors: list[FailureRecord] = Field(default_factory=list)

    def as_mongo_document(self) -> dict[str, Any]:
        """Serialize the job as a MongoDB-style document."""
        document = self.model_dump(mode="json")
        document["_id"] = self.jobId
        return document


class JobStatusResponse(ContractModel):
    """Represent a public job status response."""

    jobId: str
    photoId: str
    status: JobStatus
    currentStage: PipelineStage
    createdAt: datetime
    updatedAt: datetime


class PhotoResults(ContractModel):
    """Represent final results for one photo."""

    photoId: str
    results: list[FinalResult]
    status: JobStatus
