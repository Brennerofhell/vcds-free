from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt


class ConnectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Vehicle")
        self.setMinimumWidth(380)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Manufacturer selection
        mfr_box = QGroupBox("Vehicle Manufacturer")
        mfr_layout = QFormLayout(mfr_box)
        self.mfr_combo = QComboBox()
        self.mfr_combo.addItems(["Generic OBD-II", "VAG (VW/Audi/Skoda/SEAT)", "BMW"])
        mfr_layout.addRow("Manufacturer:", self.mfr_combo)
        layout.addWidget(mfr_box)

        # Interface selection
        iface_box = QGroupBox("Interface")
        iface_layout = QFormLayout(iface_box)

        self.iface_combo = QComboBox()
        self.iface_combo.addItems(["ELM327 (Serial)", "SocketCAN", "Mock (Test)"])
        iface_layout.addRow("Interface Type:", self.iface_combo)

        self.port_edit = QLineEdit("COM3")
        iface_layout.addRow("Port / Device:", self.port_edit)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["38400", "115200", "9600", "57600"])
        iface_layout.addRow("Baudrate:", self.baud_combo)

        layout.addWidget(iface_box)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setDefault(True)
        self.btn_connect.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_connect)
        layout.addLayout(btn_layout)

        self.iface_combo.currentIndexChanged.connect(self._on_iface_changed)

    def _on_iface_changed(self, index: int):
        is_serial = index == 0
        self.port_edit.setEnabled(is_serial)
        self.baud_combo.setEnabled(is_serial)

    @property
    def manufacturer(self) -> str:
        return self.mfr_combo.currentText()

    @property
    def interface_type(self) -> str:
        return self.iface_combo.currentText()

    @property
    def port(self) -> str:
        return self.port_edit.text()

    @property
    def baudrate(self) -> int:
        return int(self.baud_combo.currentText())
