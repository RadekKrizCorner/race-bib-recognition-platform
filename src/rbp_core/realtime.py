"""Live status notification helpers."""

from collections.abc import Callable

from rbp_contracts.models import JobStatusResponse


class JobStatusBroadcaster:
    """Broadcast job status updates to local subscribers."""

    def __init__(self) -> None:
        """Initialize the subscriber list."""
        self._subscribers: list[Callable[[JobStatusResponse], None]] = []

    def subscribe(self, callback: Callable[[JobStatusResponse], None]) -> None:
        """Add a status subscriber."""
        self._subscribers.append(callback)

    def publish(self, status: JobStatusResponse) -> None:
        """Publish a status update to all subscribers."""
        for callback in self._subscribers:
            callback(status)
