from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from ..protocols.obd2 import OBD2Protocol, DTC


class _DTCWorker(QThread):
    dtcs_ready = Signal(list)
    cleared = Signal(bool)

    def __init__(self, protocol: OBD2Protocol, mode: str):
        super().__init__()
        self._proto = protocol
        self._mode = mode

    def run(self):
        if self._mode == "read":
            self.dtcs_ready.emit(self._proto.read_dtcs())
        elif self._mode == "clear":
            self.cleared.emit(self._proto.clear_dtcs())


class DTCTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: OBD2Protocol | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_read = QPushButton("Read DTCs")
        self.btn_read.clicked.connect(self._read_dtcs)
        self.btn_clear = QPushButton("Clear DTCs")
        self.btn_clear.clicked.connect(self._clear_dtcs)
        self.btn_clear.setStyleSheet("QPushButton { color: #c0392b; }")
        self.status_label = QLabel("Not connected")
        toolbar.addWidget(self.btn_read)
        toolbar.addWidget(self.btn_clear)
        toolbar.addStretch()
        toolbar.addWidget(self.status_label)
        layout.addLayout(toolbar)

        # DTC table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Code", "Description", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def set_protocol(self, protocol: OBD2Protocol):
        self._protocol = protocol
        self.status_label.setText("Ready")
        self.btn_read.setEnabled(True)
        self.btn_clear.setEnabled(True)

    def _read_dtcs(self):
        if not self._protocol:
            return
        self.btn_read.setEnabled(False)
        self.status_label.setText("Reading DTCs...")
        self._worker = _DTCWorker(self._protocol, "read")
        self._worker.dtcs_ready.connect(self._on_dtcs)
        self._worker.start()

    def _on_dtcs(self, dtcs: list[DTC]):
        self.table.setRowCount(0)
        for dtc in dtcs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(dtc.code))
            self.table.setItem(row, 1, QTableWidgetItem(dtc.description))
            self.table.setItem(row, 2, QTableWidgetItem("Pending" if dtc.is_pending else "Confirmed"))
        count = len(dtcs)
        self.status_label.setText(f"{count} DTC{'s' if count != 1 else ''} found")
        self.btn_read.setEnabled(True)

    def _clear_dtcs(self):
        if not self._protocol:
            return
        reply = QMessageBox.question(
            self, "Clear DTCs",
            "Clear all Diagnostic Trouble Codes?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.btn_clear.setEnabled(False)
        self.status_label.setText("Clearing DTCs...")
        self._worker = _DTCWorker(self._protocol, "clear")
        self._worker.cleared.connect(self._on_cleared)
        self._worker.start()

    def _on_cleared(self, success: bool):
        if success:
            self.table.setRowCount(0)
            self.status_label.setText("DTCs cleared")
        else:
            self.status_label.setText("Clear failed")
        self.btn_clear.setEnabled(True)
