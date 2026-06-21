# VCDS Free

Open-source vehicle diagnostic tool for VAG (VW/Audi/Skoda/SEAT), BMW, and generic OBD-II vehicles. Inspired by Ross-Tech VCDS.

## Features

- **Fault codes (DTCs)** — read and clear from any ECU
- **Live data** — real-time sensor values (RPM, speed, temperature, etc.)
- **Auto-Scan** — automatically detect all ECUs in the vehicle
- **Multi-protocol** — OBD-II generic, KWP2000 (ISO 14230), UDS (ISO 14229)
- **Multi-manufacturer** — VAG group, BMW, any OBD-II vehicle

## Supported Hardware

| Interface | Protocols | Notes |
|-----------|-----------|-------|
| ELM327 (USB/Bluetooth) | Generic OBD-II | Cheapest option |
| FTDI VAG cable clone | KWP2000, TP2.0 | For older VAG vehicles |
| SocketCAN (Peak PCAN, Kvaser) | UDS, CAN bus | Professional, newer vehicles |

## Installation

Requires Python 3.11+.

```bash
git clone https://github.com/Brennerofhell/vcds-free.git
cd vcds-free
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Usage

```bash
cd src
python main.py
```

1. Click **Connect** in the toolbar
2. Select manufacturer (VAG / BMW / Generic OBD-II)
3. Select interface type and COM port
4. Use the tabs: **Auto-Scan**, **Fault Codes**, **Live Data**

> **No hardware?** Select *Mock (Test)* in the connect dialog to run with simulated ECU data.

## Running Tests

```bash
pytest tests/ -v
```

All tests run without physical hardware using a built-in mock ECU.

## Project Structure

```
src/
├── interfaces/     # Hardware abstraction (ELM327, SocketCAN, Mock)
├── protocols/      # OBD-II, KWP2000, UDS implementations
├── ecu/
│   ├── vag/        # VAG ECU address table + DTC database
│   └── bmw/        # BMW ECU address table
└── ui/             # PySide6 Qt GUI
data/
├── dtc_generic.json   # SAE J2012 generic fault codes
└── dtc_vag.json       # VAG-specific fault codes
```

## Roadmap

- [ ] VAG TP2.0 transport protocol (CAN)
- [ ] Long Coding / Adaptation editor
- [ ] BMW UDS full support
- [ ] Live data graph with CSV export
- [ ] VAG measuring blocks (KWP2000 groups)

## License

MIT
