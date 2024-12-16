import sys
import subprocess
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit
)

class BluetoothManager(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Bluetooth Manager")
        self.setGeometry(100, 100, 500, 400)

        # Layout
        self.layout = QVBoxLayout()

        # Output display
        self.output_display = QTextEdit(self)
        self.output_display.setReadOnly(True)
        self.layout.addWidget(self.output_display)

        # Input for MAC address
        self.mac_input = QLineEdit(self)
        self.mac_input.setPlaceholderText("Enter MAC Address")
        self.layout.addWidget(self.mac_input)

        # Buttons
        self.scan_button = QPushButton("Scan for Devices")
        self.scan_button.clicked.connect(self.scan_devices)
        self.layout.addWidget(self.scan_button)

        self.pair_button = QPushButton("Pair Device")
        self.pair_button.clicked.connect(self.pair_device)
        self.layout.addWidget(self.pair_button)

        self.connect_button = QPushButton("Connect Device")
        self.connect_button.clicked.connect(self.connect_device)
        self.layout.addWidget(self.connect_button)

        # Set layout
        self.setLayout(self.layout)

    def append_output(self, text):
        """Append text to the output display."""
        self.output_display.append(text)

    def scan_devices(self):
        """Scan for nearby Bluetooth devices."""
        self.append_output("Scanning for devices...")
        try:
            result = subprocess.run(
                ['bluetoothctl', 'scan', 'on'], stdout=subprocess.PIPE, text=True, timeout=10
            )
            subprocess.run(['bluetoothctl', 'scan', 'off'], stdout=subprocess.PIPE, text=True)

            devices_output = subprocess.run(
                ['bluetoothctl', 'devices'], stdout=subprocess.PIPE, text=True
            ).stdout
            devices = []
            for line in devices_output.splitlines():
                match = re.search(r"Device ([0-9A-F:]+) (.+)", line)
                if match:
                    mac, name = match.groups()
                    devices.append(f"{name} ({mac})")
            if devices:
                self.append_output("\n".join(devices))
            else:
                self.append_output("No devices found.")
        except Exception as e:
            self.append_output(f"Error scanning devices: {e}")

    def pair_device(self):
        """Pair with the entered MAC address."""
        mac_address = self.mac_input.text()
        if not mac_address:
            self.append_output("Please enter a MAC address.")
            return

        self.append_output(f"Pairing with {mac_address}...")
        try:
            result = subprocess.run(
                ['bluetoothctl', 'pair', mac_address], stdout=subprocess.PIPE, text=True
            ).stdout
            self.append_output(result)
        except Exception as e:
            self.append_output(f"Error pairing device: {e}")

    def connect_device(self):
        """Connect to the entered MAC address."""
        mac_address = self.mac_input.text()
        if not mac_address:
            self.append_output("Please enter a MAC address.")
            return

        self.append_output(f"Connecting to {mac_address}...")
        try:
            result = subprocess.run(
                ['bluetoothctl', 'connect', mac_address], stdout=subprocess.PIPE, text=True
            ).stdout
            self.append_output(result)
        except Exception as e:
            self.append_output(f"Error connecting to device: {e}")

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BluetoothManager()
    window.show()
    sys.exit(app.exec_())
