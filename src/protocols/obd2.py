from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Optional
from ..interfaces.base import AbstractInterface


@dataclass
class DTC:
    code: str
    description: str
    is_pending: bool = False


@dataclass
class LiveDataPID:
    pid: int
    name: str
    value: float
    unit: str


_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _load_dtc_db(filename: str) -> dict[str, str]:
    path = os.path.join(_DATA_DIR, filename)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


class OBD2Protocol:
    """Generic OBD-II (SAE J1979) protocol implementation."""

    def __init__(self, interface: AbstractInterface):
        self._iface = interface
        self._dtc_db: dict[str, str] = _load_dtc_db("dtc_generic.json")

    def _query(self, command: str) -> str:
        self._iface.send(command.encode())
        raw = self._iface.receive()
        return raw.decode(errors="replace").strip()

    def get_vin(self) -> Optional[str]:
        raw = self._query("0902")
        if "49 02" not in raw and "4902" not in raw:
            return None
        hex_data = raw.replace(" ", "").replace("\r", "").replace("\n", "")
        # strip header bytes (49 02 01) and decode ASCII
        try:
            idx = hex_data.index("490201") + 6
            vin_hex = hex_data[idx:idx + 34]
            return bytes.fromhex(vin_hex).decode("ascii", errors="replace")
        except (ValueError, UnicodeDecodeError):
            return None

    def read_dtcs(self) -> list[DTC]:
        raw = self._query("03")
        dtcs: list[DTC] = []
        hex_str = raw.replace(" ", "").replace("\r", "").replace("\n", "")
        # response: 43 [pair1_hi pair1_lo] [pair2_hi pair2_lo] ...
        try:
            idx = hex_str.index("43") + 2
            while idx + 3 < len(hex_str):
                word = int(hex_str[idx:idx + 4], 16)
                idx += 4
                if word == 0:
                    continue
                code = _decode_dtc_word(word)
                dtcs.append(DTC(code=code, description=self._dtc_db.get(code, "Unknown")))
        except (ValueError, IndexError):
            pass
        return dtcs

    def clear_dtcs(self) -> bool:
        raw = self._query("04")
        return "44" in raw.replace(" ", "")

    def read_live_data(self, pids: list[int]) -> list[LiveDataPID]:
        results: list[LiveDataPID] = []
        for pid in pids:
            cmd = f"01{pid:02X}"
            raw = self._query(cmd)
            parsed = _parse_pid(pid, raw)
            if parsed:
                results.append(parsed)
        return results

    def get_supported_pids(self) -> list[int]:
        supported: list[int] = []
        for group_start in [0x00, 0x20, 0x40, 0x60]:
            cmd = f"01{group_start:02X}"
            raw = self._query(cmd)
            mask = _extract_support_mask(raw, group_start)
            supported.extend(mask)
            if not mask:
                break
        return supported


def _decode_dtc_word(word: int) -> str:
    prefix_map = {0: "P", 1: "C", 2: "B", 3: "U"}
    prefix = prefix_map[(word >> 14) & 0x03]
    digit1 = (word >> 12) & 0x03
    rest = word & 0x0FFF
    return f"{prefix}{digit1}{rest:03X}"


def _extract_support_mask(raw: str, group_start: int) -> list[int]:
    hex_str = raw.replace(" ", "").replace("\r", "").replace("\n", "")
    expected = f"41{group_start:02X}"
    try:
        idx = hex_str.index(expected) + len(expected)
        mask_hex = hex_str[idx:idx + 8]
        mask = int(mask_hex, 16)
    except (ValueError, IndexError):
        return []
    return [group_start + i + 1 for i in range(32) if mask & (0x80000000 >> i)]


def _parse_pid(pid: int, raw: str) -> Optional[LiveDataPID]:
    hex_str = raw.replace(" ", "").replace("\r", "").replace("\n", "")
    expected = f"41{pid:02X}"
    try:
        idx = hex_str.index(expected) + len(expected)
        data = bytes.fromhex(hex_str[idx:idx + 8])
    except (ValueError, IndexError):
        return None

    pid_table: dict[int, tuple[str, str, object]] = {
        0x0C: ("Engine RPM",    "rpm",  lambda d: ((d[0] * 256 + d[1]) / 4)),
        0x0D: ("Vehicle Speed", "km/h", lambda d: d[0]),
        0x05: ("Coolant Temp",  "°C",   lambda d: d[0] - 40),
        0x0F: ("Intake Temp",   "°C",   lambda d: d[0] - 40),
        0x11: ("Throttle Pos",  "%",    lambda d: (d[0] / 255) * 100),
        0x04: ("Engine Load",   "%",    lambda d: (d[0] / 255) * 100),
        0x0A: ("Fuel Pressure", "kPa",  lambda d: d[0] * 3),
        0x10: ("MAF Rate",      "g/s",  lambda d: (d[0] * 256 + d[1]) / 100),
    }

    if pid not in pid_table:
        return None
    name, unit, calc = pid_table[pid]
    try:
        value = calc(data)
        return LiveDataPID(pid=pid, name=name, value=round(value, 2), unit=unit)
    except (IndexError, ZeroDivisionError):
        return None
