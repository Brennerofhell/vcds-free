from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QToolBar, QLabel
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from .connect_dialog import ConnectDialog
from .dtc_tab import DTCTab
from .live_data_tab import LiveDataTab
from .autoscan_tab import AutoScanTab
from ..interfaces.elm327 import ELM327Interface
from ..interfaces.mock import MockInterface
from ..protocols.obd2 import OBD2Protocol


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VCDS Free — Open Diagnostic Tool")
        self.resize(900, 600)
        self._protocol: OBD2Protocol | None = None
        self._build_ui()

    def _build_ui(self):
        # Toolbar
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        act_connect = QAction("Connect", self)
        act_connect.triggered.connect(self._connect)
        toolbar.addAction(act_connect)

        act_disconnect = QAction("Disconnect", self)
        act_disconnect.triggered.connect(self._disconnect)
        toolbar.addAction(act_disconnect)

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.dtc_tab = DTCTab()
        self.live_tab = LiveDataTab()
        self.scan_tab = AutoScanTab()

        self.tabs.addTab(self.scan_tab, "Auto-Scan")
        self.tabs.addTab(self.dtc_tab, "Fault Codes (DTCs)")
        self.tabs.addTab(self.live_tab, "Live Data")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._conn_label = QLabel("Disconnected")
        self.status_bar.addPermanentWidget(self._conn_label)
        self.status_bar.showMessage("Ready")

    def _connect(self):
        dlg = ConnectDialog(self)
        if dlg.exec() != ConnectDialog.DialogCode.Accepted:
            return

        iface_type = dlg.interface_type
        manufacturer = dlg.manufacturer

        if "Mock" in iface_type:
            iface = MockInterface()
        else:
            iface = ELM327Interface(dlg.port, dlg.baudrate)

        if not iface.connect():
            self.status_bar.showMessage("Connection failed — check port/device")
            return

        self._protocol = OBD2Protocol(iface)
        self.dtc_tab.set_protocol(self._protocol)
        self.live_tab.set_protocol(self._protocol)
        self.scan_tab.set_interface(iface, manufacturer)

        self._conn_label.setText(f"Connected  |  {manufacturer}  |  {iface_type}")
        self.status_bar.showMessage("Connected successfully")

    def _disconnect(self):
        self._protocol = None
        self._conn_label.setText("Disconnected")
        self.status_bar.showMessage("Disconnected")
