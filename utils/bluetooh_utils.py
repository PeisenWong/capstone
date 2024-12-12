import subprocess
import time
import re

def scan_bluetooth_devices():
    """
    Scan for nearby Bluetooth devices using bluetoothctl and return their MAC addresses and names.
    """
    print("Scanning for Bluetooth devices...")

    # Start scanning
    scan_process = subprocess.Popen(['bluetoothctl', 'scan', 'on'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(5)  # Wait for 10 seconds to scan devices

    # Stop scanning
    subprocess.run(['bluetoothctl', 'scan', 'off'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    print("Scan complete.")

    # Collect and parse the output for MAC addresses and device names
    scan_process.terminate()
    scan_process.wait()
    scan_output = subprocess.run(['bluetoothctl', 'devices'], stdout=subprocess.PIPE, text=True).stdout

    devices = {}
    for line in scan_output.splitlines():
        match = re.search(r"Device ([0-9A-F:]+) (.+)", line)
        if match:
            mac_address, name = match.groups()
            devices[mac_address] = name

    for mac, name in devices.items():
        print(f"Found device: {name} ({mac})")

    return devices

def pair_bluetooth_device(device_mac):
    """
    Pair with a Bluetooth device using its MAC address.
    """
    print(f"Pairing with device {device_mac}...")
    result = subprocess.run(['bluetoothctl', 'pair', device_mac], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if "Pairing successful" in result.stdout:
        print("Pairing successful.")
        return True
    else:
        print("Pairing failed.")
        return False

def connect_bluetooth_device(device_mac):
    """
    Connect to a paired Bluetooth device using its MAC address.
    """
    print(f"Connecting to device {device_mac}...")
    result = subprocess.run(['bluetoothctl', 'connect', device_mac], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if "Connection successful" in result.stdout:
        print("Connection successful.")
        return True
    else:
        print("Connection failed.")
        return False

def check_bluetooth_connection(device_mac):
    """
    Check the connection status of a Bluetooth device using its MAC address.
    """
    print(f"Checking connection status for device {device_mac}...")
    result = subprocess.run(['bluetoothctl', 'info', device_mac], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if "Connected: yes" in result.stdout:
        print("Device is connected.")
        return True
    else:
        print("Device is not connected.")
        return False

# Demo functionality
def main():
    # Step 1: Scan for devices
    devices = scan_bluetooth_devices()
    if not devices:
        print("No devices found.")
        return

    # # Select the first device for testing
    # test_device_mac = next(iter(devices.keys()))
    # test_device_name = devices[test_device_mac]
    # print(f"Using device: {test_device_name} ({test_device_mac})")

    # # Step 2: Pair with the device
    # if pair_bluetooth_device(test_device_mac):
    #     # Step 3: Connect to the device
    #     if connect_bluetooth_device(test_device_mac):
    #         # Step 4: Periodically check connection status
    #         for _ in range(5):
    #             check_bluetooth_connection(test_device_mac)
    #             time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    main()
