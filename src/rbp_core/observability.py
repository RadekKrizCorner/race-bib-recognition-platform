"""Observability setup helpers."""

import logging
import os


def configure_tracing(service_name: str, app: object | None = None) -> None:
    """Configure OpenTelemetry tracing for a service."""
    endpoint = os.getenv("RBP_OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)


def configure_logging(service_name: str) -> logging.Logger:
    """Configure structured baseline logging for a service."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger(service_name)


class MetricsRegistry:
    """Store lightweight local metrics counters."""

    def __init__(self) -> None:
        """Initialize empty metric counters."""
        self._counters: dict[str, int] = {}
        self._stage_completed: dict[str, int] = {}
        self._stage_latency: dict[str, float] = {}
        self._ocr_confidence_sum = 0.0
        self._ocr_confidence_count = 0

    def increment(self, name: str, amount: int = 1) -> int:
        """Increment and return a counter value."""
        self._counters[name] = self._counters.get(name, 0) + amount
        return self._counters[name]

    def snapshot(self) -> dict[str, int]:
        """Return all counters."""
        return dict(self._counters)

    def record_stage_completed(self, stage: str) -> None:
        """Record one completed pipeline stage."""
        self._stage_completed[stage] = self._stage_completed.get(stage, 0) + 1

    def record_stage_latency(self, stage: str, seconds: float) -> None:
        """Record stage latency in seconds."""
        self._stage_latency[stage] = seconds

    def record_ocr_confidence(self, confidence: float) -> None:
        """Record an OCR confidence sample."""
        self._ocr_confidence_sum += confidence
        self._ocr_confidence_count += 1

    def prometheus_text(self) -> str:
        """Render counters in Prometheus text exposition format."""
        lines = [
            "# HELP rbp_jobs_total Total jobs accepted by the local API.",
            "# TYPE rbp_jobs_total counter",
        ]
        lines.append(f"rbp_jobs_total {self._counters.get('rbp_jobs_total', 0)}")
        for name, value in sorted(self._counters.items()):
            if name == "rbp_jobs_total":
                continue
            lines.append(f"{name} {value}")
        lines.extend(
            [
                "# HELP rbp_stage_completed_total Completed pipeline stages.",
                "# TYPE rbp_stage_completed_total counter",
            ]
        )
        for stage, value in sorted(self._stage_completed.items()):
            lines.append(f'rbp_stage_completed_total{{stage="{stage}"}} {value}')
        lines.extend(
            [
                "# HELP rbp_stage_latency_seconds Last observed stage latency.",
                "# TYPE rbp_stage_latency_seconds gauge",
            ]
        )
        for stage, value in sorted(self._stage_latency.items()):
            lines.append(f'rbp_stage_latency_seconds{{stage="{stage}"}} {value}')
        lines.extend(
            [
                "# HELP rbp_ocr_confidence_sum Sum of OCR confidence values.",
                "# TYPE rbp_ocr_confidence_sum counter",
                f"rbp_ocr_confidence_sum {round(self._ocr_confidence_sum, 6)}",
                "# HELP rbp_ocr_confidence_count Count of OCR confidence values.",
                "# TYPE rbp_ocr_confidence_count counter",
                f"rbp_ocr_confidence_count {self._ocr_confidence_count}",
            ]
        )
        return "\n".join(lines) + "\n"
