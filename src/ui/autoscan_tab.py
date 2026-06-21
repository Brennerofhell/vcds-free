from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QLabel
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from ..interfaces.base import AbstractInterface
from ..protocols.obd2 import OBD2Protocol
from ..ecu.vag.addresses import VAG_ECU_ADDRESSES
from ..ecu.bmw.addresses import BMW_ECU_ADDRESSES


class _ScanWorker(QThread):
    ecu_found = Signal(int, str)   # address, name
    ecu_tested = Signal(int)       # address (even if not found)
    finished = Signal()

    def __init__(self, interface: AbstractInterface, addresses: dict[int, str]):
        super().__init__()
        self._iface = interface
        self._addresses = addresses

    def run(self):
        for addr, name in self._addresses.items():
            # Try a generic ping via UDS DiagnosticSessionControl
            try:
                self._iface.send(bytes([0x10, 0x01]))
                resp = self._iface.receive(timeout=0.5)
                if resp and len(resp) > 1 and resp[0] != 0x7F:
                    self.ecu_found.emit(addr, name)
            except Exception:
                pass
            self.ecu_tested.emit(addr)
        self.finished.emit()


class AutoScanTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._interface: AbstractInterface | None = None
        self._manufacturer = "Generic OBD-II"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.btn_scan = QPushButton("Start Auto-Scan")
        self.btn_scan.clicked.connect(self._start_scan)
        self.status_label = QLabel("Not connected")
        toolbar.addWidget(self.btn_scan)
        toolbar.addStretch()
        toolbar.addWidget(self.status_label)
        layout.addLayout(toolbar)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Address", "Module", "Status"])
        self.tree.setColumnWidth(0, 80)
        self.tree.setColumnWidth(1, 280)
        layout.addWidget(self.tree)

    def set_interface(self, interface: AbstractInterface, manufacturer: str):
        self._interface = interface
        self._manufacturer = manufacturer
        self.btn_scan.setEnabled(True)
        self.status_label.setText("Ready to scan")

    def _start_scan(self):
        if not self._interface:
            return

        addresses = self._get_addresses()
        if not addresses:
            self.status_label.setText("No address table for this manufacturer")
            return

        self.tree.clear()
        self.progress.setMaximum(len(addresses))
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.btn_scan.setEnabled(False)
        self.status_label.setText("Scanning...")

        self._worker = _ScanWorker(self._interface, addresses)
        self._worker.ecu_found.connect(self._on_found)
        self._worker.ecu_tested.connect(self._on_tested)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _get_addresses(self) -> dict[int, str]:
        if "VAG" in self._manufacturer:
            return VAG_ECU_ADDRESSES
        if "BMW" in self._manufacturer:
            return BMW_ECU_ADDRESSES
        return {}

    def _on_found(self, address: int, name: str):
        item = QTreeWidgetItem(self.tree, [f"0x{address:02X}", name, "Found"])
        item.setForeground(2, QColor("#27ae60"))

    def _on_tested(self, _address: int):
        self.progress.setValue(self.progress.value() + 1)

    def _on_finished(self):
        count = self.tree.topLevelItemCount()
        self.status_label.setText(f"Scan complete — {count} module{'s' if count != 1 else ''} found")
        self.progress.setVisible(False)
        self.btn_scan.setEnabled(True)
