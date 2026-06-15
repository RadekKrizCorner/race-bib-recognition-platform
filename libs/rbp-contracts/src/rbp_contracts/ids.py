"""Identifier helpers for pipeline entities."""

from uuid import uuid4


def new_id(prefix: str) -> str:
    """Create a compact prefixed identifier."""
    return f"{prefix}-{uuid4().hex[:12]}"


def new_event_id() -> str:
    """Create an event identifier."""
    return new_id("evt")


def new_job_id() -> str:
    """Create a processing job identifier."""
    return new_id("job")


def new_photo_id() -> str:
    """Create a photo identifier."""
    return new_id("photo")


def new_artifact_id() -> str:
    """Create an artifact identifier."""
    return new_id("art")


def new_detection_id(index: int) -> str:
    """Create a deterministic detection identifier for a stage output."""
    return f"det-{index}"


def new_crop_id(index: int) -> str:
    """Create a deterministic crop identifier for a stage output."""
    return f"crop-{index}"


def new_normalized_id(index: int) -> str:
    """Create a deterministic normalized image identifier for a stage output."""
    return f"norm-{index}"


def new_ocr_result_id(index: int) -> str:
    """Create a deterministic OCR result identifier for a stage output."""
    return f"ocr-{index}"
