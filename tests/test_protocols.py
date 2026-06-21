import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from interfaces.mock import MockInterface
from protocols.obd2 import OBD2Protocol, _decode_dtc_word


class TestDTCDecoding:
    def test_p_code(self):
        # word 0x0143 → P0143
        assert _decode_dtc_word(0x0143) == "P0143"

    def test_c_code(self):
        # bits 15-14 = 01 → C
        assert _decode_dtc_word(0x4034)[0] == "C"

    def test_b_code(self):
        # bits 15-14 = 10 → B
        assert _decode_dtc_word(0x8012)[0] == "B"

    def test_u_code(self):
        # bits 15-14 = 11 → U
        assert _decode_dtc_word(0xC001)[0] == "U"


class TestOBD2Protocol:
    @pytest.fixture
    def proto(self):
        iface = MockInterface()
        iface.connect()
        return OBD2Protocol(iface)

    def test_read_dtcs_returns_list(self, proto):
        dtcs = proto.read_dtcs()
        assert isinstance(dtcs, list)
        # Mock returns one DTC (P0143)
        assert len(dtcs) == 1
        assert dtcs[0].code == "P0143"

    def test_clear_dtcs(self, proto):
        assert proto.clear_dtcs() is True

    def test_live_data_rpm(self, proto):
        results = proto.read_live_data([0x0C])
        assert len(results) == 1
        assert results[0].name == "Engine RPM"
        assert results[0].value == pytest.approx(1726.0, abs=1.0)

    def test_live_data_speed(self, proto):
        results = proto.read_live_data([0x0D])
        assert results[0].value == 50.0
        assert results[0].unit == "km/h"

    def test_live_data_coolant(self, proto):
        results = proto.read_live_data([0x05])
        assert results[0].value == 50.0  # 0x5A - 40

    def test_unsupported_pid_returns_empty(self, proto):
        results = proto.read_live_data([0xFF])
        assert results == []

    def test_get_vin(self, proto):
        vin = proto.get_vin()
        assert vin is not None
        assert len(vin) == 17


class TestMockInterface:
    def test_connect_disconnect(self):
        iface = MockInterface()
        assert iface.connect() is True
        assert iface.is_connected is True
        iface.disconnect()
        assert iface.is_connected is False

    def test_send_receive(self):
        iface = MockInterface()
        iface.connect()
        iface.send(b"010C")
        resp = iface.receive()
        assert b"41" in resp or len(resp) > 0
