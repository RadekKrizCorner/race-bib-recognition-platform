"""Validate local Kubernetes manifests."""

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class KubernetesValidationConfig:
    """Store Kubernetes validation configuration."""

    manifest_dir: Path = REPO_ROOT / "infra" / "k8s"
    dry_run: bool = True


def build_kubectl_command(config: KubernetesValidationConfig) -> list[str]:
    """Build the kubectl apply validation command."""
    command = ["kubectl", "apply", "-f", str(config.manifest_dir)]
    if config.dry_run:
        command.extend(["--dry-run=client", "--validate=false"])
    return command


def run_validation(config: KubernetesValidationConfig) -> None:
    """Run Kubernetes manifest validation."""
    subprocess.run(build_kubectl_command(config), cwd=REPO_ROOT, check=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Validate local Kubernetes manifests.")
    parser.add_argument("--apply", action="store_true", help="Apply manifests to the current cluster.")
    return parser.parse_args()


def main() -> None:
    """Run the Kubernetes validation command."""
    args = parse_args()
    run_validation(KubernetesValidationConfig(dry_run=not args.apply))


if __name__ == "__main__":
    main()
