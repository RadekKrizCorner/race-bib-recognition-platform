"""Run the Docker Compose end-to-end pipeline demo."""

import argparse
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DockerComposeE2EConfig:
    """Store Docker Compose E2E runner configuration."""

    repo_root: Path = REPO_ROOT
    compose_file: Path = REPO_ROOT / "infra" / "docker-compose" / "docker-compose.yml"
    api_url: str = "http://127.0.0.1:8000"
    timeout_seconds: int = 180


def build_compose_command(config: DockerComposeE2EConfig, *args: str) -> list[str]:
    """Build a Docker Compose command for the project compose file."""
    return ["docker", "compose", "-f", str(config.compose_file), *args]


def should_teardown(keep_running: bool) -> bool:
    """Return whether the runner should tear down Compose services."""
    return not keep_running


def run_command(command: list[str], cwd: Path) -> None:
    """Run a subprocess command and fail on non-zero exit."""
    subprocess.run(command, cwd=cwd, check=True)


def wait_for_api(client: httpx.Client, api_url: str, timeout_seconds: int) -> None:
    """Wait for the ingest API health endpoint."""
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = client.get(f"{api_url}/healthz", timeout=2.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(2)
    raise TimeoutError(f"API did not become healthy: {last_error}")


def upload_synthetic_photo(client: httpx.Client, api_url: str) -> dict[str, Any]:
    """Upload a synthetic photo to the ingest API."""
    response = client.post(
        f"{api_url}/v1/photos",
        files={"file": ("synthetic-e2e-photo.jpg", b"synthetic docker compose image", "image/jpeg")},
        data={"raceId": "docker-compose-e2e"},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()


def wait_for_results(
    client: httpx.Client,
    api_url: str,
    photo_id: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Wait for final photo results."""
    deadline = time.monotonic() + timeout_seconds
    last_body: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        response = client.get(f"{api_url}/v1/photos/{photo_id}/results", timeout=5.0)
        if response.status_code == 200:
            body = response.json()
            last_body = body
            if body.get("status") == "COMPLETED" and body.get("results"):
                return body
        time.sleep(2)
    raise TimeoutError(f"Pipeline did not complete. Last body: {last_body}")


def run_e2e(config: DockerComposeE2EConfig, keep_running: bool = False) -> dict[str, Any]:
    """Run Docker Compose and verify upload-to-results behavior."""
    run_command(build_compose_command(config, "up", "-d", "--build"), cwd=config.repo_root)
    try:
        with httpx.Client() as client:
            wait_for_api(client, config.api_url, config.timeout_seconds)
            upload_body = upload_synthetic_photo(client, config.api_url)
            result_body = wait_for_results(
                client=client,
                api_url=config.api_url,
                photo_id=upload_body["photoId"],
                timeout_seconds=config.timeout_seconds,
            )
            print(result_body)
            return result_body
    finally:
        if should_teardown(keep_running):
            run_command(build_compose_command(config, "down"), cwd=config.repo_root)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run Docker Compose E2E demo.")
    parser.add_argument("--keep-running", action="store_true", help="Keep containers running after the test.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="Ingest API URL.")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds.")
    return parser.parse_args()


def main() -> None:
    """Run the Docker Compose E2E command."""
    args = parse_args()
    config = DockerComposeE2EConfig(api_url=args.api_url, timeout_seconds=args.timeout)
    run_e2e(config, keep_running=args.keep_running)


if __name__ == "__main__":
    main()
