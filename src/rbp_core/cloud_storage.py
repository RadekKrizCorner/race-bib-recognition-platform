"""Cloud artifact storage adapter implementation."""

from typing import Any

from rbp_contracts.ids import new_artifact_id
from rbp_contracts.models import Artifact
from rbp_contracts.statuses import ArtifactType, PipelineStage

from rbp_core.artifact_store import ArtifactStore


class GcsArtifactStore(ArtifactStore):
    """Store artifacts in Google Cloud Storage."""

    def __init__(self, bucket_name: str, client: Any | None = None) -> None:
        """Initialize the GCS bucket target."""
        self.bucket_name = bucket_name
        self.client = client or self._create_default_client()

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
        """Persist artifact bytes to a deterministic GCS object path."""
        object_name = f"jobs/{job_id}/{relative_stage_dir}/{filename}"
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(content, content_type=content_type)
        return Artifact(
            artifactId=new_artifact_id(),
            jobId=job_id,
            photoId=photo_id,
            type=artifact_type,
            stage=stage,
            uri=f"gs://{self.bucket_name}/{object_name}",
            contentType=content_type,
            metadata=metadata or {},
        )

    def read_uri(self, uri: str) -> bytes:
        """Read artifact bytes from a GCS URI."""
        bucket_name, object_name = self._parse_gcs_uri(uri)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        return blob.download_as_bytes()

    def _parse_gcs_uri(self, uri: str) -> tuple[str, str]:
        """Parse a GCS URI into bucket and object name."""
        prefix = "gs://"
        if not uri.startswith(prefix):
            raise ValueError(f"Unsupported GCS URI: {uri}")
        bucket_name, object_name = uri.removeprefix(prefix).split("/", 1)
        return bucket_name, object_name

    def _create_default_client(self) -> Any:
        """Create the default Google Cloud Storage client."""
        from google.cloud import storage

        return storage.Client()
