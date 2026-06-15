"""Describe a local reprocessing request for a job."""

import argparse
import json
import sys
from pathlib import Path


def bootstrap_paths() -> None:
    """Add local package paths for direct script execution."""
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "libs" / "rbp-contracts" / "src"))
    sys.path.insert(0, str(root / "src"))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Create a reprocessing request payload.")
    parser.add_argument("job_id", help="Processing job identifier.")
    parser.add_argument("--photo-id", help="Photo identifier.")
    parser.add_argument("--source-image-uri", help="Persisted raw image URI.")
    parser.add_argument("--stage", default="DETECTION", help="Stage to restart from.")
    return parser.parse_args()


def build_request(job_id: str, stage: str) -> dict[str, str]:
    """Build a reprocessing request payload."""
    return {"jobId": job_id, "restartStage": stage, "action": "reprocess"}


def main() -> None:
    """Print a reprocessing request payload."""
    args = parse_args()
    if args.photo_id and args.source_image_uri:
        bootstrap_paths()
        from rbp_core.reprocessing import build_photo_reprocess_event

        event = build_photo_reprocess_event(args.job_id, args.photo_id, args.source_image_uri)
        print(event.model_dump_json(indent=2))
        return
    print(json.dumps(build_request(args.job_id, args.stage), indent=2))


if __name__ == "__main__":
    main()
