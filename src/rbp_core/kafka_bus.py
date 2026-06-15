"""Kafka event bus adapter."""

from typing import Any

from rbp_contracts.events import EventEnvelope

from rbp_core.worker_runtime import JsonEventCodec


def is_transient_kafka_error(error: Any) -> bool:
    """Return whether a Kafka error can be ignored during startup."""
    return error.code() in {3}


class KafkaEventBus:
    """Publish metadata-only events to Kafka."""

    def __init__(self, bootstrap_servers: str, client_id: str = "race-bib-platform") -> None:
        """Initialize the Kafka producer."""
        from confluent_kafka import Producer

        self.codec = JsonEventCodec()
        self.producer = Producer({"bootstrap.servers": bootstrap_servers, "client.id": client_id})

    def publish(self, topic: str, event: EventEnvelope) -> None:
        """Publish an event to Kafka."""
        self.producer.produce(
            topic=topic,
            key=event.photoId.encode(),
            value=self.codec.encode(event).encode(),
        )
        self.producer.flush()


class KafkaStageWorker:
    """Consume one Kafka topic and process events with a stage handler."""

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        input_topic: str,
        handler: Any,
    ) -> None:
        """Initialize the Kafka worker."""
        from confluent_kafka import Consumer

        self.codec = JsonEventCodec()
        self.input_topic = input_topic
        self.handler = handler
        self.consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )

    def run_forever(self) -> None:
        """Poll Kafka and process events forever."""
        self.consumer.subscribe([self.input_topic])
        try:
            while True:
                message = self.consumer.poll(1.0)
                if message is None:
                    continue
                if message.error():
                    if is_transient_kafka_error(message.error()):
                        continue
                    raise RuntimeError(str(message.error()))
                event = self.codec.decode(message.value())
                self.handler(event)
                self.consumer.commit(message)
        finally:
            self.consumer.close()
