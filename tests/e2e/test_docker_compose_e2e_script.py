from scripts.run_docker_compose_e2e import (
    DockerComposeE2EConfig,
    build_compose_command,
    should_teardown,
)


def test_build_compose_command_uses_project_compose_file() -> None:
    """Verify Docker Compose commands target the repository compose file."""
    config = DockerComposeE2EConfig()

    command = build_compose_command(config, "up", "-d")

    assert command[:3] == ["docker", "compose", "-f"]
    assert str(config.compose_file) in command
    assert command[-2:] == ["up", "-d"]


def test_should_teardown_honors_keep_running_flag() -> None:
    """Verify teardown can be disabled for debugging."""
    assert should_teardown(keep_running=False) is True
    assert should_teardown(keep_running=True) is False
