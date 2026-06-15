from rbp_core.observability import MetricsRegistry


def test_metrics_registry_renders_stage_and_confidence_metrics() -> None:
    """Verify metrics registry exposes pipeline stage and confidence metrics."""
    metrics = MetricsRegistry()

    metrics.increment("rbp_jobs_total")
    metrics.record_stage_completed("OCR")
    metrics.record_stage_latency("OCR", 1.25)
    metrics.record_ocr_confidence(0.91)
    rendered = metrics.prometheus_text()

    assert 'rbp_stage_completed_total{stage="OCR"} 1' in rendered
    assert 'rbp_stage_latency_seconds{stage="OCR"} 1.25' in rendered
    assert "rbp_ocr_confidence_sum 0.91" in rendered
    assert "rbp_ocr_confidence_count 1" in rendered
