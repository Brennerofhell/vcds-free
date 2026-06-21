from abc import ABC, abstractmethod


class AbstractInterface(ABC):
    """Base class for all hardware communication interfaces."""

    @abstractmethod
    def connect(self) -> bool:
        """Open the connection. Returns True on success."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection."""

    @abstractmethod
    def send(self, data: bytes) -> None:
        """Send raw bytes to the interface."""

    @abstractmethod
    def receive(self, timeout: float = 2.0) -> bytes:
        """Receive raw bytes. Blocks up to timeout seconds."""

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """True if currently connected."""
