"""KWP2000 (ISO 14230) protocol — used by older VAG vehicles (up to ~2005)."""
from __future__ import annotations
import time
from dataclasses import dataclass
from ..interfaces.base import AbstractInterface

# KWP2000 Service IDs
SID_START_SESSION    = 0x10
SID_READ_DTC         = 0x18
SID_CLEAR_DTC        = 0x14
SID_READ_DATA_LOCAL  = 0x21  # VAG measuring blocks
SID_READ_DATA_BY_ID  = 0x22
SID_WRITE_DATA       = 0x2E
SID_ADAPTATION       = 0x2C
SID_ECU_RESET        = 0x11


@dataclass
class KWPFrame:
    service_id: int
    data: bytes


class KWP2000Protocol:
    """ISO 14230-4 KWP2000 over serial (fast-init)."""

    def __init__(self, interface: AbstractInterface, ecu_address: int = 0x01):
        self._iface = interface
        self._ecu_addr = ecu_address
        self._tester_addr = 0xF1

    def start_session(self, mode: int = 0x89) -> bool:
        """Open a diagnostic session. 0x89 = VAG extended session."""
        resp = self._send_recv(SID_START_SESSION, bytes([mode]))
        return resp is not None and resp.service_id == (SID_START_SESSION | 0x40)

    def read_dtcs(self) -> list[tuple[int, int]]:
        """Read DTCs. Returns list of (dtc_word, status_byte) tuples."""
        resp = self._send_recv(SID_READ_DTC, bytes([0xFF, 0xFF]))
        if resp is None or len(resp.data) < 2:
            return []
        dtcs: list[tuple[int, int]] = []
        data = resp.data
        count = data[0]
        for i in range(count):
            base = 1 + i * 3
            if base + 2 >= len(data):
                break
            word = (data[base] << 8) | data[base + 1]
            status = data[base + 2]
            dtcs.append((word, status))
        return dtcs

    def clear_dtcs(self) -> bool:
        resp = self._send_recv(SID_CLEAR_DTC, bytes([0xFF, 0xFF]))
        return resp is not None and resp.service_id == (SID_CLEAR_DTC | 0x40)

    def read_measuring_block(self, group: int) -> bytes | None:
        """Read VAG measuring block (group 001–255)."""
        resp = self._send_recv(SID_READ_DATA_LOCAL, bytes([group]))
        if resp is None:
            return None
        return resp.data

    def ecu_reset(self) -> bool:
        resp = self._send_recv(SID_ECU_RESET, bytes([0x01]))
        return resp is not None

    def _build_frame(self, sid: int, data: bytes) -> bytes:
        """Build KWP2000 frame: [len] [tester_addr] [ecu_addr] [sid] [data...] [checksum]."""
        payload = bytes([self._tester_addr, self._ecu_addr, sid]) + data
        length = len(payload)
        frame = bytes([0x80 | length]) + payload
        checksum = sum(frame) & 0xFF
        return frame + bytes([checksum])

    def _send_recv(self, sid: int, data: bytes, timeout: float = 2.0) -> KWPFrame | None:
        frame = self._build_frame(sid, data)
        self._iface.send(frame)
        raw = self._iface.receive(timeout)
        return self._parse_frame(raw)

    @staticmethod
    def _parse_frame(raw: bytes) -> KWPFrame | None:
        if len(raw) < 4:
            return None
        # strip header byte + addresses
        length = raw[0] & 0x3F
        if len(raw) < length + 2:
            return None
        sid = raw[3]
        payload = raw[4:3 + length]
        return KWPFrame(service_id=sid, data=payload)
