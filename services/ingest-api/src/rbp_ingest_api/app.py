"""FastAPI application for photo ingestion and result retrieval."""

import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile

from rbp_core.observability import MetricsRegistry, configure_tracing
from rbp_core.runtime_factory import create_artifact_store, create_event_bus, create_repository
from rbp_pipeline.handlers import IngestHandler
from rbp_pipeline.runner import LocalPipelineRunner


def create_app(artifact_root: Path | str = "artifacts", mode: str | None = None) -> FastAPI:
    """Create and configure the ingest API application."""
    app = FastAPI(title="Race Bib Recognition Platform", version="0.1.0")
    configure_tracing("ingest-api", app)
    runtime_mode = mode or os.getenv("RBP_API_MODE", "local")
    runner = LocalPipelineRunner(artifact_store=None) if runtime_mode == "local" else None
    repository = runner.repository if runner is not None else create_repository()
    artifact_store = runner.artifact_store if runner is not None else create_artifact_store()
    event_bus = runner.event_bus if runner is not None else create_event_bus()
    if hasattr(artifact_store, "root") and runtime_mode == "local":
        artifact_store.root = Path(artifact_root)
    ingest_handler = IngestHandler(repository, artifact_store, event_bus)
    metrics = MetricsRegistry()

    @app.post("/v1/photos", status_code=201)
    async def upload_photo(
        file: Annotated[UploadFile, File()],
        raceId: Annotated[str | None, Form()] = None,
    ) -> dict[str, str]:
        """Accept a photo upload and start local processing."""
        photo_bytes = await file.read()
        if runner is not None:
            job = runner.process_photo(
                photo_bytes=photo_bytes,
                filename=file.filename or "photo.jpg",
                race_id=raceId,
            )
        else:
            job_id, _photo_id = ingest_handler.handle_photo(
                photo_bytes=photo_bytes,
                filename=file.filename or "photo.jpg",
                race_id=raceId,
            )
            job = repository.get_job(job_id)
        metrics.increment("rbp_jobs_total")
        return {"jobId": job.jobId, "photoId": job.photoId, "status": "RECEIVED"}

    @app.get("/v1/jobs/{job_id}")
    async def get_job_status(job_id: str) -> dict[str, object]:
        """Return current job status."""
        try:
            return repository.job_status(job_id).model_dump(mode="json")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @app.get("/v1/jobs/{job_id}/details")
    async def get_job_details(job_id: str) -> dict[str, object]:
        """Return detailed job state for debugging."""
        try:
            return repository.get_job(job_id).model_dump(mode="json")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @app.get("/v1/photos/{photo_id}/results")
    async def get_photo_results(photo_id: str) -> dict[str, object]:
        """Return final results for one photo."""
        try:
            return repository.photo_results(photo_id).model_dump(mode="json")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Photo not found") from exc

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """Return service health."""
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics_endpoint() -> Response:
        """Return Prometheus-compatible metrics."""
        return Response(content=metrics.prometheus_text(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()
