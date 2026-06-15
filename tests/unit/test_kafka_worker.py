from rbp_core.kafka_bus import is_transient_kafka_error


class FakeKafkaError:
    """Provide a fake Kafka error object."""

    def __init__(self, code_value: int) -> None:
        """Store the fake error code."""
        self.code_value = code_value

    def code(self) -> int:
        """Return the fake Kafka error code."""
        return self.code_value


def test_unknown_topic_error_is_transient_during_worker_startup() -> None:
    """Verify missing topics are treated as transient startup errors."""
    assert is_transient_kafka_error(FakeKafkaError(3)) is True


def test_non_transient_kafka_error_is_not_ignored() -> None:
    """Verify unrelated Kafka errors are not ignored."""
    assert is_transient_kafka_error(FakeKafkaError(99)) is False
