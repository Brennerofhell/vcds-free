# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run from the repo root (`F:\programmieren\vcds free`).

```bash
# Setup (first time)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run the app (must be run from src/ so imports resolve)
cd src && python main.py

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_protocols.py::TestOBD2Protocol::test_read_dtcs_returns_list -v
```

## Architecture

The codebase has three layers that stack on top of each other:

**1. Interface layer** (`src/interfaces/`) — hardware abstraction  
All interfaces implement `AbstractInterface` (`base.py`) with four methods: `connect`, `disconnect`, `send(bytes)`, `receive() -> bytes`. Protocol code never talks to hardware directly — it only knows about `AbstractInterface`. `MockInterface` (`mock.py`) returns hardcoded OBD-II hex responses and is used by all tests.

**2. Protocol layer** (`src/protocols/`) — byte-level communication  
Each protocol class takes an `AbstractInterface` in its constructor and builds request/response frames on top of it:
- `OBD2Protocol` — SAE J1979 generic (AT commands via ELM327 or raw bytes)
- `KWP2000Protocol` — ISO 14230, for VAG vehicles up to ~2005
- `UDSProtocol` — ISO 14229, for VAG 2008+ and all BMW

`OBD2Protocol` speaks in ASCII hex strings (ELM327 style). `KWP2000Protocol` and `UDSProtocol` speak raw bytes (for direct CAN or serial). DTC descriptions are looked up from `data/dtc_generic.json` (or `dtc_vag.json`) at protocol init time.

**3. UI layer** (`src/ui/`) — PySide6 Qt GUI  
`MainWindow` owns the tab widget and the `ConnectDialog`. On connect it instantiates the chosen interface + `OBD2Protocol` and passes them to each tab via `set_protocol()` / `set_interface()`. Long-running operations (DTC read, ECU scan) run in `QThread` subclasses (`_DTCWorker`, `_ScanWorker`) and emit signals back to the UI thread.

## ECU databases

`src/ecu/vag/addresses.py` and `src/ecu/bmw/addresses.py` contain plain dicts mapping integer ECU addresses to human-readable names. These are consumed by `AutoScanTab` to know which addresses to probe during an auto-scan.

DTC description databases live in `data/` as JSON (`dtc_generic.json`, `dtc_vag.json`). Keys are DTC code strings (`"P0143"`). Missing codes fall back to `"Unknown"`.

## Import path note

`src/main.py` is the entry point and must be run with `src/` as the working directory — it imports `from ui.main_window import MainWindow` (no `src.` prefix). Tests work around this with `sys.path.insert(0, ".../src")` at the top of `test_protocols.py`.

## Adding a new protocol

1. Create `src/protocols/yourprotocol.py`, accept `AbstractInterface` in `__init__`
2. Add response fixtures to `MockInterface._RESPONSES` in `src/interfaces/mock.py`
3. Add tests in `tests/test_protocols.py`
4. Wire it into `MainWindow._connect()` in `src/ui/main_window.py`
