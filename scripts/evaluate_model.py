"""Evaluate model predictions from a JSON file."""

import argparse
import json
import sys
from pathlib import Path


def bootstrap_paths() -> None:
    """Add local package paths for direct script execution."""
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate race bib model predictions.")
    parser.add_argument("input", type=Path, help="JSON file containing evaluation cases.")
    return parser.parse_args()


def load_cases(path: Path) -> list[object]:
    """Load evaluation cases from a JSON file."""
    bootstrap_paths()
    from rbp_core.model_evaluation import EvaluationCase

    body = json.loads(path.read_text())
    return [EvaluationCase.model_validate(item) for item in body["cases"]]


def main() -> None:
    """Print aggregate model evaluation metrics."""
    bootstrap_paths()
    from rbp_core.model_evaluation import ModelEvaluator

    args = parse_args()
    result = ModelEvaluator().evaluate(load_cases(args.input))
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
