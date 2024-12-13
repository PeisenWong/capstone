from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("192.168.0.2", port=502)

while True:
    command = input("Enter command: ").strip().lower()

    if command == 's':
        print("Starting the robot...")
        response = client.write_register(60*2+1, 0, slave=2)
    elif command == 'p':
        print("Stopping the robot...")
        response = client.write_register(60*2+1, 1, slave=2)
    elif command == 'f':
        print("Setting speed to fast...")
        response = client.write_register(16*2+1, 70, slave=2)
    elif command == 'l':
        print("Setting speed to slow...")
        response = client.write_register(16*2+1, 20, slave=2)
    elif command == 'q':
        print("Exiting the program...")
        break
    else:
        print("Invalid command. Please enter s, p, f, l, or q.")
    