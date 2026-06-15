"""Runtime factory helpers for local, Docker, and cloud modes."""

import os
from typing import Any

from rbp_core.artifact_store import ArtifactStore, LocalArtifactStore
from rbp_core.cloud_storage import GcsArtifactStore
from rbp_core.event_bus import InMemoryEventBus
from rbp_core.kafka_bus import KafkaEventBus
from rbp_core.mongo_state import MongoProcessingJobRepository
from rbp_core.state import InMemoryProcessingJobRepository
from rbp_pipeline.adapters import (
    ByteImageProcessor,
    FakeOcrAdapter,
    HeuristicBibDetector,
    OpenCvImageProcessor,
    PaddleOcrCompatibleAdapter,
    YoloCompatibleBibDetector,
)


def create_repository() -> Any:
    """Create the configured processing job repository."""
    mongo_uri = os.getenv("RBP_MONGODB_URI")
    if mongo_uri:
        return MongoProcessingJobRepository(mongo_uri=mongo_uri)
    return InMemoryProcessingJobRepository()


def create_artifact_store() -> ArtifactStore:
    """Create the configured artifact store."""
    gcs_bucket = os.getenv("RBP_GCS_BUCKET")
    if gcs_bucket:
        return GcsArtifactStore(bucket_name=gcs_bucket)
    return LocalArtifactStore(root=os.getenv("RBP_ARTIFACT_ROOT", "artifacts"))


def create_event_bus() -> Any:
    """Create the configured event bus."""
    bootstrap_servers = os.getenv("RBP_KAFKA_BOOTSTRAP_SERVERS")
    if bootstrap_servers:
        return KafkaEventBus(
            bootstrap_servers=bootstrap_servers,
            client_id=os.getenv("RBP_KAFKA_CLIENT_ID", "race-bib-platform"),
        )
    return InMemoryEventBus()


def create_detector() -> Any:
    """Create the configured bib detector adapter."""
    if os.getenv("RBP_DETECTOR_ADAPTER") == "yolo":
        return YoloCompatibleBibDetector(model_path=os.environ["RBP_YOLO_MODEL_PATH"])
    return HeuristicBibDetector()


def create_ocr() -> Any:
    """Create the configured OCR adapter."""
    if os.getenv("RBP_OCR_ADAPTER") == "paddle":
        return PaddleOcrCompatibleAdapter()
    return FakeOcrAdapter()


def create_image_processor() -> Any:
    """Create the configured crop and normalization processor."""
    if os.getenv("RBP_IMAGE_PROCESSOR") == "opencv":
        return OpenCvImageProcessor()
    return ByteImageProcessor()
