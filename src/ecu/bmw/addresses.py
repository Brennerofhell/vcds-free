"""BMW ECU address map for UDS-based scan."""

BMW_ECU_ADDRESSES: dict[int, str] = {
    0x12: "DME (Engine)",
    0x18: "EGS (Transmission)",
    0x19: "VTG (Transfer Case)",
    0x1E: "DSC (Stability Control)",
    0x28: "Instrument Cluster",
    0x2F: "Airbag",
    0x36: "CAS (Car Access System / Immobilizer)",
    0x40: "Light Control Module (LCM)",
    0x44: "Roof Function Centre",
    0x45: "Convertible Top",
    0x50: "EPS (Power Steering)",
    0x56: "LWR (Headlight Range)",
    0x60: "PDC (Park Distance Control)",
    0x70: "Radio / Head Unit",
    0x76: "Navigation",
    0x80: "Comfort Access",
}
