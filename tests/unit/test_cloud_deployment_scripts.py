from scripts.cloud_preflight import required_tools
from scripts.deploy_gcp import GcpDeploymentConfig, build_terraform_command


def test_required_tools_include_cloud_deployment_dependencies() -> None:
    """Verify cloud preflight checks the required CLIs."""
    tools = required_tools()

    assert "gcloud" in tools
    assert "terraform" in tools
    assert "kubectl" in tools


def test_build_terraform_command_targets_infra_directory() -> None:
    """Verify Terraform commands run from the infrastructure directory."""
    config = GcpDeploymentConfig(project_id="demo-project", bucket_name="demo-bucket")

    command = build_terraform_command(config, "plan")

    assert command[:2] == ["terraform", "plan"]
    assert f"-var=project_id={config.project_id}" in command
    assert f"-var=artifact_bucket_name={config.bucket_name}" in command
