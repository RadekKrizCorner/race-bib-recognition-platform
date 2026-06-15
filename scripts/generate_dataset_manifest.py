"""Generate a sample low-confidence dataset manifest."""

import json
import sys
from pathlib import Path


def bootstrap_paths() -> None:
    """Add local package paths for direct script execution."""
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "libs" / "rbp-contracts" / "src"))
    sys.path.insert(0, str(root / "src"))


def build_manifest() -> dict[str, object]:
    """Build a sample dataset manifest."""
    bootstrap_paths()
    from rbp_core.training import DatasetManifestBuilder

    builder = DatasetManifestBuilder(model_version="fake-ocr-v1")
    return builder.build(
        [
            {
                "jobId": "job-demo",
                "photoId": "photo-demo",
                "artifactUri": "file://artifacts/jobs/job-demo/normalized/norm-1.jpg",
                "bibNumber": "1258",
                "confidence": 0.42,
            }
        ]
    )


def main() -> None:
    """Print a sample dataset manifest."""
    print(json.dumps(build_manifest(), indent=2))


if __name__ == "__main__":
    main()
