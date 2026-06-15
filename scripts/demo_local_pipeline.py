"""Run the deterministic local race bib pipeline demo."""

import json
import sys
from pathlib import Path


def bootstrap_paths() -> None:
    """Add local package paths for direct script execution."""
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "libs" / "rbp-contracts" / "src",
        root / "src",
        root / "services" / "ingest-api" / "src",
    ]
    for path in paths:
        sys.path.insert(0, str(path))


def run_demo() -> dict[str, object]:
    """Run a local in-process pipeline demo."""
    bootstrap_paths()
    from rbp_pipeline.runner import LocalPipelineRunner

    runner = LocalPipelineRunner()
    job = runner.process_photo(
        photo_bytes=b"synthetic public demo image bytes",
        filename="synthetic-race-photo.jpg",
        race_id="demo-race",
    )
    details = runner.get_job_details(job.jobId)
    results = runner.get_photo_results(job.photoId)
    return {
        "job": details.model_dump(mode="json"),
        "results": results.model_dump(mode="json"),
        "topics": {topic: len(events) for topic, events in runner.event_bus.all_topics().items()},
    }


def main() -> None:
    """Print the local demo output as JSON."""
    print(json.dumps(run_demo(), indent=2))


if __name__ == "__main__":
    main()
