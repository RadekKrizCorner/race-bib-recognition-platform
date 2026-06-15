from scripts.validate_local_kubernetes import KubernetesValidationConfig, build_kubectl_command


def test_build_kubectl_command_uses_k8s_directory() -> None:
    """Verify kubectl validation targets the project manifests."""
    config = KubernetesValidationConfig(dry_run=True)

    command = build_kubectl_command(config)

    assert command[:2] == ["kubectl", "apply"]
    assert "--dry-run=client" in command
    assert str(config.manifest_dir) in command


def test_build_kubectl_command_can_run_live_apply() -> None:
    """Verify live apply omits dry-run mode."""
    config = KubernetesValidationConfig(dry_run=False)

    command = build_kubectl_command(config)

    assert "--dry-run=client" not in command
