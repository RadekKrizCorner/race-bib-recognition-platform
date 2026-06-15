"""Run Google Cloud deployment commands."""

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GcpDeploymentConfig:
    """Store Google Cloud deployment configuration."""

    project_id: str
    bucket_name: str
    region: str = "europe-west3"
    cluster_name: str = "race-bib-platform"
    terraform_dir: Path = REPO_ROOT / "infra" / "terraform"


def build_terraform_command(config: GcpDeploymentConfig, action: str) -> list[str]:
    """Build a Terraform command with required variables."""
    return [
        "terraform",
        action,
        f"-var=project_id={config.project_id}",
        f"-var=region={config.region}",
        f"-var=cluster_name={config.cluster_name}",
        f"-var=artifact_bucket_name={config.bucket_name}",
    ]


def build_get_credentials_command(config: GcpDeploymentConfig) -> list[str]:
    """Build the gcloud command for fetching GKE credentials."""
    return [
        "gcloud",
        "container",
        "clusters",
        "get-credentials",
        config.cluster_name,
        "--region",
        config.region,
        "--project",
        config.project_id,
    ]


def run_command(command: list[str], cwd: Path) -> None:
    """Run a deployment command."""
    subprocess.run(command, cwd=cwd, check=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Deploy Race Bib Recognition Platform to GCP.")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--bucket-name", required=True)
    parser.add_argument("--region", default="europe-west3")
    parser.add_argument("--cluster-name", default="race-bib-platform")
    parser.add_argument("--apply", action="store_true", help="Apply Terraform instead of planning.")
    return parser.parse_args()


def main() -> None:
    """Run Terraform plan or apply for GCP deployment."""
    args = parse_args()
    config = GcpDeploymentConfig(
        project_id=args.project_id,
        bucket_name=args.bucket_name,
        region=args.region,
        cluster_name=args.cluster_name,
    )
    action = "apply" if args.apply else "plan"
    command = build_terraform_command(config, action)
    if args.apply:
        command.append("-auto-approve")
    run_command(command, cwd=config.terraform_dir)
    if args.apply:
        run_command(build_get_credentials_command(config), cwd=REPO_ROOT)


if __name__ == "__main__":
    main()
