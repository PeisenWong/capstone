from pymodbus.client import ModbusTcpClient

def main():
    # Replace with your robotic arm's IP address and port
    robot_ip = '192.168.0.2'
    robot_port = 502  # Default Modbus TCP port is 502

    # Create a Modbus TCP client
    client = ModbusTcpClient(robot_ip, port=robot_port)

    # Connect to the robot controller
    if not client.connect():
        print('Unable to connect to the robot controller.')
        return

    # Define the starting register and the count
    start_address = 31  # Starting register
    register_count = 4  # Number of registers to read (31 to 34)

    # Adjust slave ID (replace with correct value if known)
    slave_id = 2  # Default Modbus slave ID

    try:
        # Read registers
        response = client.read_holding_registers(start_address, count=register_count, slave=slave_id)
        
        if response.isError():
            print(f"Error reading registers from {start_address} to {start_address + register_count - 1}: {response}")
        else:
            # Display the values
            print(f"Register values from {start_address} to {start_address + register_count - 1}:")
            for i, value in enumerate(response.registers, start=start_address):
                print(f"Register {i}: {value}")
    except Exception as e:
        print(f"Exception during read operation: {e}")
    finally:
        # Close the client connection
        client.close()

if __name__ == '__main__':
    main()
