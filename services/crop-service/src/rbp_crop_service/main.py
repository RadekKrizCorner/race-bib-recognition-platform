"""Bib crop worker entry point."""

import os

from rbp_contracts.events import EventEnvelope, EventType

from rbp_core.kafka_bus import KafkaStageWorker
from rbp_core.observability import configure_logging
from rbp_core.reliable_processor import ReliableStageProcessor
from rbp_core.runtime_factory import (
    create_artifact_store,
    create_detector,
    create_event_bus,
    create_image_processor,
    create_ocr,
    create_repository,
)
from rbp_core.worker_runtime import idle_forever, process_stdin_event
from rbp_pipeline.runner import LocalPipelineRunner


def main() -> None:
    """Start the crop worker."""
    logger = configure_logging("crop-service")
    repository = create_repository()
    event_bus = create_event_bus()
    runner = LocalPipelineRunner(
        repository=repository,
        artifact_store=create_artifact_store(),
        event_bus=event_bus,
        detector=create_detector(),
        ocr=create_ocr(),
        image_processor=create_image_processor(),
    )
    processor = ReliableStageProcessor(
        stage="CROP",
        service_name="crop-service",
        input_topic=EventType.BIB_DETECTED.topic_name(),
        repository=repository,
        event_bus=event_bus,
    )

    def handler(event: EventEnvelope) -> EventEnvelope | None:
        """Process one crop event with reliability handling."""
        return processor.process(event, runner.crop_handler.handle)

    if process_stdin_event(handler) is None:
        bootstrap_servers = os.getenv("RBP_KAFKA_BOOTSTRAP_SERVERS")
        if bootstrap_servers:
            logger.info("Crop worker is consuming Kafka.")
            KafkaStageWorker(
                bootstrap_servers=bootstrap_servers,
                group_id="crop-service",
                input_topic=EventType.BIB_DETECTED.topic_name(),
                handler=handler,
            ).run_forever()
        else:
            logger.info("Crop worker is waiting for Kafka integration.")
            idle_forever("crop-service")


if __name__ == "__main__":
    main()
