from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from ..protocols.obd2 import OBD2Protocol, LiveDataPID

AVAILABLE_PIDS = [0x0C, 0x0D, 0x05, 0x0F, 0x11, 0x04, 0x0A, 0x10]
PID_NAMES = {
    0x0C: "Engine RPM",
    0x0D: "Vehicle Speed",
    0x05: "Coolant Temp",
    0x0F: "Intake Temp",
    0x11: "Throttle Position",
    0x04: "Engine Load",
    0x0A: "Fuel Pressure",
    0x10: "MAF Air Rate",
}


class LiveDataTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: OBD2Protocol | None = None
        self._active_pids: list[int] = [0x0C, 0x0D, 0x05]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._build_ui()

    def _build_ui(self):
        main = QHBoxLayout(self)

        # PID selector panel
        selector_box = QGroupBox("PID Selection")
        selector_layout = QVBoxLayout(selector_box)
        self._checkboxes: dict[int, QCheckBox] = {}
        for pid in AVAILABLE_PIDS:
            cb = QCheckBox(PID_NAMES[pid])
            cb.setChecked(pid in self._active_pids)
            cb.stateChanged.connect(self._update_active_pids)
            selector_layout.addWidget(cb)
            self._checkboxes[pid] = cb
        selector_layout.addStretch()
        selector_box.setMaximumWidth(180)
        main.addWidget(selector_box)

        # Data table + controls
        right = QVBoxLayout()

        toolbar = QHBoxLayout()
        self.btn_start = QPushButton("Start Polling")
        self.btn_start.clicked.connect(self._toggle_polling)
        self.interval_label = QLabel("Interval: 500ms")
        toolbar.addWidget(self.btn_start)
        toolbar.addStretch()
        toolbar.addWidget(self.interval_label)
        right.addLayout(toolbar)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["PID", "Value", "Unit"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right.addWidget(self.table)
        main.addLayout(right)

    def set_protocol(self, protocol: OBD2Protocol):
        self._protocol = protocol
        self.btn_start.setEnabled(True)

    def _update_active_pids(self):
        self._active_pids = [pid for pid, cb in self._checkboxes.items() if cb.isChecked()]

    def _toggle_polling(self):
        if self._timer.isActive():
            self._timer.stop()
            self.btn_start.setText("Start Polling")
        else:
            self._timer.start(500)
            self.btn_start.setText("Stop Polling")

    def _poll(self):
        if not self._protocol or not self._active_pids:
            return
        results = self._protocol.read_live_data(self._active_pids)
        self.table.setRowCount(0)
        for item in results:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.value)))
            self.table.setItem(row, 2, QTableWidgetItem(item.unit))

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)
