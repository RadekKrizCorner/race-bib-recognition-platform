"""Event bus abstractions for Kafka and local tests."""

from collections import defaultdict

from rbp_contracts.events import EventEnvelope


class InMemoryEventBus:
    """Store events by topic for deterministic local execution."""

    def __init__(self) -> None:
        """Initialize an empty in-memory event bus."""
        self._topics: dict[str, list[EventEnvelope]] = defaultdict(list)

    def publish(self, topic: str, event: EventEnvelope) -> None:
        """Publish an event unless the same event already exists."""
        if all(existing.eventId != event.eventId for existing in self._topics[topic]):
            self._topics[topic].append(event)

    def topic_events(self, topic: str) -> list[EventEnvelope]:
        """Return events published to one topic."""
        return list(self._topics.get(topic, []))

    def all_topics(self) -> dict[str, list[EventEnvelope]]:
        """Return all topic events."""
        return {topic: list(events) for topic, events in self._topics.items()}
