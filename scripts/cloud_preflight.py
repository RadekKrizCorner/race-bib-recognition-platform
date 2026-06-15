"""Check local tools required for Google Cloud deployment."""

import shutil
from pathlib import Path


def required_tools() -> list[str]:
    """Return required command-line tools for cloud deployment."""
    return ["gcloud", "terraform", "kubectl", "docker"]


def missing_tools() -> list[str]:
    """Return required tools that are not installed."""
    return [tool for tool in required_tools() if shutil.which(tool) is None]


def main() -> None:
    """Run cloud deployment preflight checks."""
    missing = missing_tools()
    if missing:
        raise SystemExit(f"Missing tools: {', '.join(missing)}")
    terraform_dir = Path(__file__).resolve().parents[1] / "infra" / "terraform"
    tfvars = terraform_dir / "terraform.tfvars"
    if not tfvars.exists():
        raise SystemExit(f"Create {tfvars} from terraform.tfvars.example before deployment.")
    print("Cloud deployment preflight passed.")


if __name__ == "__main__":
    main()
