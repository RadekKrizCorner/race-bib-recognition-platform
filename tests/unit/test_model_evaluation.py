from rbp_core.model_evaluation import EvaluationCase, ModelEvaluator, ModelRegistry, ModelVersion


def test_model_evaluator_calculates_accuracy_and_confidence() -> None:
    """Verify model evaluator compares expected and predicted bib numbers."""
    evaluator = ModelEvaluator()

    result = evaluator.evaluate(
        [
            EvaluationCase(
                photoId="photo-1",
                expectedBibNumber="1258",
                predictedBibNumber="1258",
                confidence=0.9,
            ),
            EvaluationCase(
                photoId="photo-2",
                expectedBibNumber="3421",
                predictedBibNumber="1234",
                confidence=0.5,
            ),
        ]
    )

    assert result.totalSamples == 2
    assert result.correctSamples == 1
    assert result.accuracy == 0.5
    assert result.averageConfidence == 0.7


def test_model_registry_tracks_latest_version() -> None:
    """Verify model registry returns the newest registered version."""
    registry = ModelRegistry()

    registry.register(ModelVersion(name="ocr", version="v1", artifactUri="gs://bucket/models/ocr-v1"))
    registry.register(ModelVersion(name="ocr", version="v2", artifactUri="gs://bucket/models/ocr-v2"))

    assert registry.latest("ocr").version == "v2"
