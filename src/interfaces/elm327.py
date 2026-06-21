import serial
import time
from .base import AbstractInterface


class ELM327Interface(AbstractInterface):
    """ELM327-based OBD-II interface via serial (USB/Bluetooth)."""

    def __init__(self, port: str, baudrate: int = 38400):
        self._port = port
        self._baudrate = baudrate
        self._serial: serial.Serial | None = None

    def connect(self) -> bool:
        try:
            self._serial = serial.Serial(
                self._port, self._baudrate, timeout=2.0
            )
            self._init_elm327()
            return True
        except serial.SerialException:
            return False

    def _init_elm327(self) -> None:
        cmds = [
            b"ATZ\r",    # reset
            b"ATE0\r",   # echo off
            b"ATL0\r",   # linefeeds off
            b"ATS0\r",   # spaces off
            b"ATH1\r",   # headers on
            b"ATSP0\r",  # auto protocol
        ]
        for cmd in cmds:
            self._serial.write(cmd)
            time.sleep(0.1)
            self._serial.read_all()

    def disconnect(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def send(self, data: bytes) -> None:
        if not self._serial:
            raise RuntimeError("Not connected")
        self._serial.write(data + b"\r")

    def receive(self, timeout: float = 2.0) -> bytes:
        if not self._serial:
            raise RuntimeError("Not connected")
        self._serial.timeout = timeout
        buf = b""
        while True:
            chunk = self._serial.read(64)
            if not chunk:
                break
            buf += chunk
            if b">" in buf:
                break
        return buf.replace(b">", b"").strip()

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open
