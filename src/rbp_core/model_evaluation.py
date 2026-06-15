"""Model versioning and evaluation helpers."""

from pydantic import BaseModel, ConfigDict


class EvaluationCase(BaseModel):
    """Represent one labeled model evaluation case."""

    model_config = ConfigDict(extra="forbid")

    photoId: str
    expectedBibNumber: str
    predictedBibNumber: str
    confidence: float


class EvaluationResult(BaseModel):
    """Represent aggregate model evaluation metrics."""

    model_config = ConfigDict(extra="forbid")

    totalSamples: int
    correctSamples: int
    accuracy: float
    averageConfidence: float


class ModelVersion(BaseModel):
    """Represent one model version artifact."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    artifactUri: str


class ModelEvaluator:
    """Evaluate predicted bib numbers against expected labels."""

    def evaluate(self, cases: list[EvaluationCase]) -> EvaluationResult:
        """Calculate accuracy and average confidence."""
        total = len(cases)
        correct = sum(1 for case in cases if case.expectedBibNumber == case.predictedBibNumber)
        average_confidence = round(sum(case.confidence for case in cases) / total, 4) if total else 0.0
        accuracy = round(correct / total, 4) if total else 0.0
        return EvaluationResult(
            totalSamples=total,
            correctSamples=correct,
            accuracy=accuracy,
            averageConfidence=average_confidence,
        )


class ModelRegistry:
    """Track model versions in memory for local experiments."""

    def __init__(self) -> None:
        """Initialize an empty model registry."""
        self._versions: dict[str, list[ModelVersion]] = {}

    def register(self, version: ModelVersion) -> None:
        """Register one model version."""
        self._versions.setdefault(version.name, []).append(version)

    def latest(self, name: str) -> ModelVersion:
        """Return the latest registered version for a model name."""
        versions = self._versions.get(name, [])
        if not versions:
            raise KeyError(name)
        return versions[-1]
