"""UDS (ISO 14229) protocol — used by newer VAG (2008+) and all BMW."""
from __future__ import annotations
from dataclasses import dataclass
from ..interfaces.base import AbstractInterface

# UDS Service IDs
SID_DIAGNOSTIC_SESSION  = 0x10
SID_ECU_RESET           = 0x11
SID_CLEAR_DTC           = 0x14
SID_READ_DTC_INFO       = 0x19
SID_READ_DATA_BY_ID     = 0x22
SID_WRITE_DATA_BY_ID    = 0x2E
SID_IO_CONTROL          = 0x2F
SID_SECURITY_ACCESS     = 0x27

# Session types
SESSION_DEFAULT    = 0x01
SESSION_EXTENDED   = 0x03
SESSION_PROGRAMMING = 0x02

# DTC status masks
DTC_STATUS_TEST_FAILED   = 0x01
DTC_STATUS_CONFIRMED     = 0x08
DTC_STATUS_PENDING       = 0x04


@dataclass
class UDSResponse:
    sid: int
    data: bytes
    is_negative: bool = False
    nrc: int = 0  # negative response code


@dataclass
class UDSDTC:
    code: int       # 3-byte DTC number
    status: int     # status byte


class UDSProtocol:
    """ISO 14229-1 UDS protocol over ISOTP (via python-can or ELM327)."""

    def __init__(self, interface: AbstractInterface):
        self._iface = interface

    def start_session(self, session_type: int = SESSION_EXTENDED) -> bool:
        resp = self._request(SID_DIAGNOSTIC_SESSION, bytes([session_type]))
        return resp is not None and not resp.is_negative

    def read_dtcs(self, status_mask: int = 0xFF) -> list[UDSDTC]:
        """Service 19 subfunction 02: reportDTCByStatusMask."""
        resp = self._request(SID_READ_DTC_INFO, bytes([0x02, status_mask]))
        if resp is None or resp.is_negative or len(resp.data) < 2:
            return []
        dtcs: list[UDSDTC] = []
        data = resp.data[1:]  # skip availability mask byte
        idx = 0
        while idx + 3 < len(data):
            code = (data[idx] << 16) | (data[idx + 1] << 8) | data[idx + 2]
            status = data[idx + 3]
            dtcs.append(UDSDTC(code=code, status=status))
            idx += 4
        return dtcs

    def clear_dtcs(self, group: int = 0xFFFFFF) -> bool:
        """Service 14: ClearDiagnosticInformation."""
        group_bytes = group.to_bytes(3, "big")
        resp = self._request(SID_CLEAR_DTC, group_bytes)
        return resp is not None and not resp.is_negative

    def read_data(self, data_id: int) -> bytes | None:
        """Service 22: ReadDataByIdentifier."""
        id_bytes = data_id.to_bytes(2, "big")
        resp = self._request(SID_READ_DATA_BY_ID, id_bytes)
        if resp is None or resp.is_negative or len(resp.data) < 2:
            return None
        return resp.data[2:]  # strip echoed DID

    def write_data(self, data_id: int, value: bytes) -> bool:
        """Service 2E: WriteDataByIdentifier."""
        payload = data_id.to_bytes(2, "big") + value
        resp = self._request(SID_WRITE_DATA_BY_ID, payload)
        return resp is not None and not resp.is_negative

    def ecu_reset(self, reset_type: int = 0x01) -> bool:
        """Service 11: ECUReset. 0x01=hard, 0x02=key off/on, 0x03=soft."""
        resp = self._request(SID_ECU_RESET, bytes([reset_type]))
        return resp is not None and not resp.is_negative

    def _request(self, sid: int, data: bytes, timeout: float = 2.0) -> UDSResponse | None:
        payload = bytes([sid]) + data
        self._iface.send(payload)
        raw = self._iface.receive(timeout)
        return self._parse(raw)

    @staticmethod
    def _parse(raw: bytes) -> UDSResponse | None:
        if len(raw) < 1:
            return None
        if raw[0] == 0x7F:
            # Negative response: [7F] [requested SID] [NRC]
            nrc = raw[2] if len(raw) >= 3 else 0
            return UDSResponse(sid=raw[1] if len(raw) >= 2 else 0,
                               data=b"", is_negative=True, nrc=nrc)
        return UDSResponse(sid=raw[0], data=raw[1:])
