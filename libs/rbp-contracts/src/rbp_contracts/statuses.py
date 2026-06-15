"""Status enums used across all services."""

from enum import StrEnum


class JobStatus(StrEnum):
    """Represent the processing status of a job."""

    RECEIVED = "RECEIVED"
    DETECTING = "DETECTING"
    CROPPING = "CROPPING"
    NORMALIZING = "NORMALIZING"
    OCRING = "OCRING"
    LINKING = "LINKING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PipelineStage(StrEnum):
    """Represent the current pipeline stage."""

    INGEST = "INGEST"
    DETECTION = "DETECTION"
    CROP = "CROP"
    NORMALIZATION = "NORMALIZATION"
    OCR = "OCR"
    LINKING = "LINKING"


class ArtifactType(StrEnum):
    """Represent the persisted artifact type."""

    RAW_IMAGE = "raw_image"
    BIB_CROP = "bib_crop"
    NORMALIZED_CROP = "normalized_crop"
    OCR_INPUT = "ocr_input"
    DEBUG_OVERLAY = "debug_overlay"
