"""Artifact storage abstractions and local implementation."""

from abc import ABC, abstractmethod
from pathlib import Path

from rbp_contracts.ids import new_artifact_id
from rbp_contracts.models import Artifact
from rbp_contracts.statuses import ArtifactType, PipelineStage


class ArtifactStore(ABC):
    """Define artifact storage operations used by services."""

    @abstractmethod
    def write_artifact(
        self,
        job_id: str,
        photo_id: str,
        artifact_type: ArtifactType,
        stage: PipelineStage,
        relative_stage_dir: str,
        filename: str,
        content: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> Artifact:
        """Persist artifact bytes and return metadata."""

    @abstractmethod
    def read_uri(self, uri: str) -> bytes:
        """Read artifact bytes from a URI."""


class LocalArtifactStore(ArtifactStore):
    """Store artifacts on the local filesystem."""

    def __init__(self, root: Path | str = "artifacts") -> None:
        """Initialize the local artifact root."""
        self.root = Path(root)

    def write_artifact(
        self,
        job_id: str,
        photo_id: str,
        artifact_type: ArtifactType,
        stage: PipelineStage,
        relative_stage_dir: str,
        filename: str,
        content: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> Artifact:
        """Persist artifact bytes under a deterministic job path."""
        path = self.root / "jobs" / job_id / relative_stage_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        uri = f"file://artifacts/jobs/{job_id}/{relative_stage_dir}/{filename}"
        return Artifact(
            artifactId=new_artifact_id(),
            jobId=job_id,
            photoId=photo_id,
            type=artifact_type,
            stage=stage,
            uri=uri,
            contentType=content_type,
            metadata=metadata or {},
        )

    def read_uri(self, uri: str) -> bytes:
        """Read artifact bytes from a local artifact URI."""
        prefix = "file://artifacts/"
        if not uri.startswith(prefix):
            raise ValueError(f"Unsupported local artifact URI: {uri}")
        relative = uri.removeprefix(prefix)
        return (self.root / relative).read_bytes()
