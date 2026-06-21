from .base import AbstractInterface


# Pre-defined OBD-II responses for testing without hardware
_RESPONSES: dict[bytes, bytes] = {
    b"0100": b"4100BE3EA813",  # supported PIDs 01-20
    b"0120": b"4120801FB010",  # supported PIDs 21-40
    b"010C": b"41 0C 1A F8",  # RPM = 6904 / 4 = 1726 rpm
    b"010D": b"41 0D 32",      # speed = 50 km/h
    b"0105": b"41 05 5A",      # coolant temp = 90-40 = 50 °C
    b"03":   b"43 01 43 00 00 00 00",  # 1 DTC: P0143
    b"04":   b"44",             # clear DTCs OK
    b"0902": b"49 02 01 31 47 31 42 41 35 38 30 32 4C 37 32 30 30 30 30 31",  # VIN
}


class MockInterface(AbstractInterface):
    """Simulated ECU interface for testing without real hardware."""

    def __init__(self):
        self._connected = False
        self._last_sent: bytes = b""

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def send(self, data: bytes) -> None:
        self._last_sent = data.strip().upper()

    def receive(self, timeout: float = 2.0) -> bytes:
        return _RESPONSES.get(self._last_sent, b"NO DATA")

    @property
    def is_connected(self) -> bool:
        return self._connected
