from pathlib import Path

import anyio
import httpx
from rbp_ingest_api.app import create_app


def test_ingest_api_accepts_photo_and_returns_results(tmp_path: Path) -> None:
    """Verify the API accepts an upload and returns final bib results."""

    async def scenario() -> None:
        """Run the API scenario through an ASGI transport."""
        app = create_app(artifact_root=tmp_path)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            upload_response = await client.post(
                "/v1/photos",
                files={"file": ("race-photo.jpg", b"synthetic-image", "image/jpeg")},
                data={"raceId": "race-1"},
            )
            upload_body = upload_response.json()

            result_response = await client.get(f"/v1/photos/{upload_body['photoId']}/results")
            result_body = result_response.json()

        assert upload_response.status_code == 201
        assert upload_body["status"] == "RECEIVED"
        assert result_response.status_code == 200
        assert result_body["status"] == "COMPLETED"
        assert result_body["results"][0]["bibNumber"] == "1258"

    anyio.run(scenario)


def test_ingest_api_exposes_prometheus_metrics(tmp_path: Path) -> None:
    """Verify the API exposes Prometheus-compatible metrics."""

    async def scenario() -> None:
        """Run the metrics scenario through an ASGI transport."""
        app = create_app(artifact_root=tmp_path)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/metrics")

        assert response.status_code == 200
        assert "rbp_jobs_total" in response.text
        assert "text/plain" in response.headers["content-type"]

    anyio.run(scenario)
