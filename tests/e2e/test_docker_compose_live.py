import os

import pytest

from scripts.run_docker_compose_e2e import DockerComposeE2EConfig, run_e2e


@pytest.mark.skipif(
    os.getenv("RBP_RUN_DOCKER_E2E") != "1",
    reason="Set RBP_RUN_DOCKER_E2E=1 to run the live Docker Compose E2E test.",
)
def test_docker_compose_pipeline_reaches_completed_results() -> None:
    """Verify Docker Compose runs the full async pipeline."""
    result = run_e2e(DockerComposeE2EConfig(timeout_seconds=240), keep_running=False)

    assert result["status"] == "COMPLETED"
    assert result["results"]
